#!/usr/bin/env python3
"""
Query Planner Agent v1 — Splunk Search Executor

Stateless tool executor: receives SPL queries from the Judge Agent
and runs them against the Splunk REST API. Handles all low-level
search mechanics and result formatting. Does not reason about what
to search — that is the Judge's responsibility.

Exposes a clean Python API:
    qp = QueryPlannerV1(splunk_client, manifest_path)
    results = qp.execute_search("index=botsv3 sourcetype=... | stats ...")
    sourcetypes = qp.list_sourcetypes()
    sample = qp.sample_events("aws:cloudtrail", keyword="PutBucketAcl")

Version: v1
"""

import json
import os
import re
import sys
from typing import Optional

# Add parent to path when run from agent/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from splunk_client import SplunkClient

# ── Fields to strip from results ───────────────────────────────────────────────

_STRIP_FIELDS = frozenset({
    "_bkt", "_cd", "_indextime", "_kv", "_si", "_sourcetype",
    "_serial", "_subsecond", "punct", "linecount", "splunk_server",
    "splunk_server_group", "timestartpos", "timeendpos",
})

_MAX_RESULT_CHARS = 14_000


class QueryPlannerV1:
    """
    Stateless Splunk search executor for the multi-agent SIEM system.

    Responsibilities:
    - Validate that queries target index=botsv3
    - Execute SPL via SplunkClient
    - Format and truncate results for LLM consumption
    - Provide sourcetype discovery via the local manifest

    Does NOT:
    - Reason about what to search
    - Track investigation state
    - Select or suggest sourcetypes (that is the Judge's job)
    """

    def __init__(self, splunk_client: SplunkClient, manifest_path: Optional[str] = None):
        self.splunk = splunk_client
        self.manifest_path = manifest_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "botsv3_fields.json"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def execute_search(self, spl_query: str, max_results: int = 100) -> str:
        """
        Execute any SPL query against the botsv3 index and return JSON results.

        Requirements enforced:
        - Query must reference index=botsv3

        Returns JSON string with 'results' array and 'meta' block, or 'error'.
        """
        validation_error = self._validate_query(spl_query)
        if validation_error:
            return json.dumps({"error": validation_error})

        try:
            raw = self.splunk.search(
                query=spl_query,
                earliest="0",
                latest="now",
                max_results=max_results,
            )
            return self._format(raw, keep_raw=False)
        except Exception as exc:
            return json.dumps({"error": f"Splunk execution error: {exc}"})

    def sample_events(self, sourcetype: str, keyword: str = "", count: int = 5) -> str:
        """
        Return raw event content (including _raw) from a sourcetype.
        Useful for discovering field names and log structure.
        """
        try:
            raw = self.splunk.sample_events(
                sourcetype=sourcetype,
                index="botsv3",
                keyword=keyword,
                count=min(count, 8),
            )
            return self._format(raw, keep_raw=True)
        except Exception as exc:
            return json.dumps({"error": f"sample_events error: {exc}"})

    def get_field_values(self, field: str, sourcetype: str = "", top_n: int = 25) -> str:
        """Return top distinct values for a field, optionally scoped to a sourcetype."""
        try:
            raw = self.splunk.get_field_values(
                field=field, index="botsv3", top_n=top_n, sourcetype=sourcetype
            )
            return self._format(raw, keep_raw=False)
        except Exception as exc:
            return json.dumps({"error": f"get_field_values error: {exc}"})

    def get_sourcetype_fields(self, sourcetype: str) -> str:
        """Return all fields in a sourcetype with coverage stats and sample values."""
        try:
            raw = self.splunk.get_sourcetype_fields(sourcetype=sourcetype, index="botsv3")
            return self._format(raw, keep_raw=False)
        except Exception as exc:
            return json.dumps({"error": f"get_sourcetype_fields error: {exc}"})

    def list_sourcetypes(self) -> str:
        """Return all known sourcetypes from the local manifest (fast, no Splunk call)."""
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            sts = list(manifest.get("source_types", {}).keys())
            return json.dumps({"sourcetypes": sts, "count": len(sts)})
        except Exception as exc:
            return json.dumps({"error": f"Manifest read error: {exc}"})

    def search_manifest_fields(self, pattern: str) -> str:
        """Search the manifest for fields or sourcetypes matching a pattern."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return json.dumps({"error": f"Invalid regex: {e}"})
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            return json.dumps({"error": f"Manifest read error: {exc}"})

        matches = []
        for st, entry in manifest.get("source_types", {}).items():
            if regex.search(st):
                matches.append({"sourcetype": st, "match_type": "sourcetype"})
            for field in entry.get("fields", []):
                if regex.search(field):
                    matches.append({"sourcetype": st, "match_type": "field", "field": field})
        return json.dumps({"matches": matches[:60], "total": len(matches)})

    # ── Internals ──────────────────────────────────────────────────────────────

    def _validate_query(self, spl: str) -> Optional[str]:
        """Return error string or None if query is acceptable."""
        if not re.search(r'\bindex\s*=\s*botsv3\b', spl, re.IGNORECASE):
            return (
                "Query must include 'index=botsv3'. "
                "All BOTSv3 data lives in this index. Prepend it to your query."
            )
        return None

    def _format(self, raw: dict, keep_raw: bool) -> str:
        """Strip noisy fields and truncate large payloads."""
        if "error" in raw:
            return json.dumps({"error": raw["error"]})

        strip = _STRIP_FIELDS if keep_raw else (_STRIP_FIELDS | {"_raw"})
        if "results" in raw:
            cleaned = [
                {k: v for k, v in row.items() if k not in strip}
                for row in raw["results"]
            ]
            payload = json.dumps({
                "results": cleaned,
                "meta": raw.get("_meta", {}),
            })
        else:
            payload = json.dumps(raw)

        if len(payload) > _MAX_RESULT_CHARS:
            payload = payload[:_MAX_RESULT_CHARS] + '...[truncated — refine query]"}'
        return payload
