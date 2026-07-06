#!/usr/bin/env python3
"""
Canonical append-only event stream for a v1 multi-agent run.

One JSON object per line (JSONL). This is the machine-first system of record:
timeline.md and report.md are rendered views of it. Every event shares an
envelope (schema version, ISO-8601 local timestamp, run name, event type) plus
event-specific keys passed as kwargs.

Thread-safe: up to 6 Senior workers emit task_end events concurrently, so a
single lock serializes the write of each complete line.
"""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA_VERSION = 1


class _Timer:
    __slots__ = ("ms",)
    def __init__(self) -> None:
        self.ms = 0


class EventLog:
    """Append-only JSONL writer. All events go through emit()."""

    def __init__(self, path: str, *, run: str) -> None:
        self.path = path
        self.run  = run
        self._lock = threading.Lock()

    def emit(self, event: str, **fields) -> None:
        row = {
            "v":     SCHEMA_VERSION,
            "ts":    datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
            "run":   self.run,
            "event": event,
        }
        row.update(fields)
        line = json.dumps(row, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    @contextmanager
    def timer(self):
        """Measure wall-clock ms for a block: `with log.timer() as t: ...; t.ms`."""
        t = _Timer()
        start = time.perf_counter()
        try:
            yield t
        finally:
            t.ms = int((time.perf_counter() - start) * 1000)
