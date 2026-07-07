#!/usr/bin/env python3
"""
One-time script: populate botsv3_fields.json with real fields for every sourcetype.

Runs fieldsummary against Splunk for each sourcetype that has no fields yet,
then writes the results back to the manifest. Safe to re-run — already-populated
sourcetypes are skipped.

Usage (from agent/ directory):
    python build_manifest.py
"""

import os
import sys
import json
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
