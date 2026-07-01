"""
SplunkConnectionPool — thread-safe pool of authenticated Splunk sessions.

Drop-in replacement for SplunkClient: identical public API (.search,
.get_field_values, .get_sourcetype_fields, .sample_events).

Each slot in the pool is one fully-authenticated SplunkClient (its own
requests.Session + session key). Callers check out a client for the
duration of a search, then return it. If every slot is busy the caller
blocks until one is available (up to `timeout` seconds).

Why this matters
─────────────────
requests.Session is not safe for concurrent writes. In the current v1
architecture workers are serial (SH waits for each Senior to finish), so
a single shared session has worked — but any move toward parallel Senior
workers would cause race conditions on the session headers. The pool
provides:
  • Thread safety    — each concurrent search gets its own session.
  • Bounded load     — pool size is a hard cap on simultaneous Splunk jobs.
  • Auto re-auth     — a 401 triggers silent re-login and one retry.
  • Zero code change — callers just swap SplunkClient → SplunkConnectionPool.

Usage
─────
    from splunk_pool import SplunkConnectionPool

    pool = SplunkConnectionPool(host, user, password, size=5)

    # Use anywhere you previously used SplunkClient:
    results = pool.search("index=botsv3 | head 10")

    # Explicit checkout (rare — for lower-level use):
    with pool.checkout() as client:
        client.search(...)

Sizing — measured on this machine (2026-07-01)
────────────────────────────────────────────
Query: index=botsv3 sourcetype="stream:http" | stats count by src_ip | head 20
Baseline (serial): 3.37s/call

  Concur │ Per-job │ Slowdown │ Jobs/s
  ───────┼─────────┼──────────┼───────
       1 │   3.18s │    0.9x  │  0.31      ← same as serial
       2 │   3.20s │    0.9x  │  0.62      ← free gain, no slowdown
       4 │   4.33s │    1.3x  │  0.92
       6 │   5.66s │    1.7x  │  1.03  ◄── throughput peak
       7 │   6.09s │    1.8x  │  1.03  ◄── throughput peak
       8 │   7.57s │    2.2x  │  0.98
      12 │  13.95s │    4.1x  │  0.83      ← degradation starts
      20 │  15.43s │    4.6x  │  0.91  (2 failures)

Default size=6: throughput peak (1.03 jobs/s = 3.3× faster than serial)
with only 1.7× per-job slowdown. Beyond 8 slots Splunk's scheduler
starts queuing jobs and throughput actually drops.
"""

from __future__ import annotations

import queue
import time
from contextlib import contextmanager

import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from splunk_client import SplunkClient

disable_warnings(InsecureRequestWarning)

_RETRY_ON_401 = True   # re-authenticate and retry once on session expiry


class SplunkConnectionPool:
    """Thread-safe pool of authenticated Splunk sessions.

    Public API is identical to SplunkClient so it can be used as a drop-in
    replacement without touching any call site.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        size: int = 6,
        checkout_timeout: int = 60,
    ) -> None:
        self.host     = host.rstrip("/")
        self._user    = username
        self._pass    = password
        self._size    = size
        self._timeout = checkout_timeout

        self._pool: queue.Queue[SplunkClient] = queue.Queue(maxsize=size)
        for _ in range(size):
            self._pool.put(SplunkClient(host, username, password))

    # ── Context manager checkout ──────────────────────────────────────────────
    @contextmanager
    def checkout(self):
        """Check out a client for the lifetime of the with-block."""
        client = self._acquire()
        try:
            yield client
        finally:
            self._pool.put(client)

    def _acquire(self) -> SplunkClient:
        try:
            return self._pool.get(block=True, timeout=self._timeout)
        except queue.Empty:
            raise TimeoutError(
                f"SplunkConnectionPool: no free connection after {self._timeout}s "
                f"(pool size={self._size}). Increase size or checkout_timeout."
            )

    # ── Internal dispatcher with 401-retry ───────────────────────────────────
    def _call(self, method_name: str, *args, **kwargs):
        """Check out a client, call method_name, re-auth and retry once on 401."""
        client = self._acquire()
        try:
            return getattr(client, method_name)(*args, **kwargs)
        except requests.HTTPError as exc:
            if _RETRY_ON_401 and exc.response is not None and exc.response.status_code == 401:
                # Session expired — re-authenticate and try once more
                client._login(self._user, self._pass)
                result = getattr(client, method_name)(*args, **kwargs)
                return result
            raise
        finally:
            self._pool.put(client)

    # ── Public API (mirrors SplunkClient exactly) ─────────────────────────────
    def search(
        self,
        query: str,
        earliest: str = "0",
        latest: str = "now",
        max_results: int = 100,
    ) -> dict:
        return self._call("search", query, earliest, latest, max_results)

    def get_field_values(
        self,
        field: str,
        index: str = "botsv3",
        top_n: int = 20,
        sourcetype: str = "",
    ) -> dict:
        return self._call("get_field_values", field, index, top_n, sourcetype)

    def get_sourcetype_fields(
        self,
        sourcetype: str,
        index: str = "botsv3",
        min_count: int = 1,
    ) -> dict:
        return self._call("get_sourcetype_fields", sourcetype, index, min_count)

    def sample_events(
        self,
        sourcetype: str,
        index: str = "botsv3",
        keyword: str = "",
        count: int = 3,
    ) -> dict:
        return self._call("sample_events", sourcetype, index, keyword, count)

    # ── Pool introspection ────────────────────────────────────────────────────
    @property
    def available(self) -> int:
        """Number of connections currently idle in the pool."""
        return self._pool.qsize()

    @property
    def in_use(self) -> int:
        return self._size - self.available

    def __repr__(self) -> str:
        return (
            f"SplunkConnectionPool(host={self.host!r}, size={self._size}, "
            f"available={self.available})"
        )
