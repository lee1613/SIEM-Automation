#!/usr/bin/env python3
"""
One-time script: populate botsv3_fields.json with real fields for every sourcetype.

Runs fieldsummary against Splunk for each sourcetype that has no fields yet,
then writes the results back to the manifest. Safe to re-run — already-populated
sourcetypes are skipped.

Usage (from agent/ directory):
    python build_manifest.py
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from splunk_client import SplunkClient

load_dotenv()

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "botsv3_fields.json")


def load_manifest() -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict) -> None:
    # tmp + rename: a mid-write kill must not leave a truncated manifest
    # (every agent run depends on this file parsing).
    tmp = MANIFEST_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp, MANIFEST_PATH)


def sync_sourcetypes(splunk, manifest, index: str) -> tuple[int, int]:
    """Reconcile the manifest's sourcetype list against the live index.

    Returns (added, removed). The field-scan loop below only refreshes
    sourcetypes the manifest already lists, so one that was never in the file
    stayed invisible forever, and one that stopped carrying data was never
    dropped - the manifest held 104 names while the index carried 102, and the
    two sets differed by more than their sizes suggest. `| metadata` reads the
    bucket catalogue instead of scanning events, so this costs ~1s regardless
    of index size.
    """
    result = splunk.search(
        f"| metadata type=sourcetypes index={index} | table sourcetype",
        earliest="0", max_results=5000)
    live    = {r["sourcetype"] for r in (result.get("results") or []) if r.get("sourcetype")}
    entries = manifest.setdefault("source_types", {})
    added   = [st for st in sorted(live) if st not in entries]
    for st in added:
        entries[st] = {"fields": []}
    # Drop entries naming a sourcetype that carries no data in this index. They
    # are worse than absent: SH plans searches against them and every such
    # delegation is dead on arrival.
    stale = [st for st in entries if st not in live]
    for st in stale:
        del entries[st]
    return len(added), len(stale)


def sync_sources(splunk, manifest, index: str) -> int:
    """Persist the `source` axis: every source with its sourcetype, volume and
    time coverage, busiest first.

    Two axes address this data, not one - sourcetype=syslog hides 78,459 Cisco
    NVM flow events reachable only as source="cisconvmflowdata". The SH briefing
    renders the top slice of this list, and holding the whole tail locally means
    enumerating it costs a dict lookup rather than a Splunk round-trip.

    first/last come free from `| metadata` and are the cheapest way to rule out
    a feed that does not span the window a question asks about.
    """
    # Counts come from stats, NOT from metadata. `| metadata`'s totalCount is
    # bucket-derived and wrong by orders of magnitude - it reports source=lsof at
    # 103 events where stats counts 322,336 - so ranking on it would put the
    # busiest feeds nowhere near the top of the briefing. metadata is still the
    # only cheap source of first/last, so each command supplies what it is good at.
    pairs = splunk.search(f"index={index} | stats count by source, sourcetype",
                          earliest="0", max_results=20000)
    meta = splunk.search(
        f"| metadata type=sources index={index} | table source firstTime lastTime",
        earliest="0", max_results=20000)
    times = {r["source"]: r for r in (meta.get("results") or []) if r.get("source")}

    rows = []
    for r in (pairs.get("results") or []):
        src = r.get("source")
        if not src:
            continue
        t = times.get(src, {})
        rows.append({
            "source":     src,
            "sourcetype": r.get("sourcetype", ""),
            "count":      int(float(r.get("count") or 0)),
            "first":      int(float(t.get("firstTime") or 0)),
            "last":       int(float(t.get("lastTime") or 0)),
        })
    rows.sort(key=lambda x: -x["count"])
    manifest["sources"] = rows
    return len(rows)


def main():
    host = os.getenv("SPLUNK_HOST", "https://localhost:8089")
    user = os.getenv("SPLUNK_USER", "admin")
    pwd  = os.getenv("SPLUNK_PASS", "")

    if not pwd:
        sys.exit("SPLUNK_PASS not set in .env")

    print(f"Connecting to Splunk at {host} as '{user}' ...")
    splunk = SplunkClient(host, user, pwd)
    print("Connected.\n")

    manifest = load_manifest()
    index    = manifest.get("meta", {}).get("index", "botsv3")

    added, stale = sync_sourcetypes(splunk, manifest, index)
    print(f"  sourcetypes: +{added} new, -{stale} stale "
          f"({len(manifest.get('source_types', {}))} total)")
    n_src = sync_sources(splunk, manifest, index)
    print(f"  sources:     {n_src} recorded\n")
    save_manifest(manifest)

    source_types = manifest.get("source_types", {})

    total      = len(source_types)
    populated  = 0
    skipped    = 0
    empty      = 0
    failed     = 0

    for i, (st_name, entry) in enumerate(source_types.items(), start=1):
        prefix = f"[{i:>3}/{total}] {st_name}"

        if entry.get("fields"):
            print(f"  SKIP  {prefix}  ({len(entry['fields'])} fields already)")
            skipped += 1
            continue

        print(f"  SCAN  {prefix} ...", end=" ", flush=True)
        t0 = time.time()

        try:
            result = splunk.get_sourcetype_fields(st_name)
            elapsed = time.time() - t0
            rows = result.get("results", [])

            if not rows:
                print(f"no data  ({elapsed:.1f}s)")
                empty += 1
            else:
                fields = [r["field"] for r in rows]
                entry["fields"] = fields
                save_manifest(manifest)
                print(f"{len(fields)} fields  ({elapsed:.1f}s)")
                populated += 1

        except Exception as e:
            elapsed = time.time() - t0
            print(f"ERROR: {e}  ({elapsed:.1f}s)")
            failed += 1

    print(f"\nDone. populated={populated}  skipped={skipped}  empty={empty}  failed={failed}")


if __name__ == "__main__":
    main()
