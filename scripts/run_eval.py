#!/usr/bin/env python3
"""Offline scorer for BOTSv3 agent runs.

Reads artifacts that are already in the repo — no API key, no Splunk, no LLM
calls. Verdicts are recomputed from the submitted/official answer pair using
the same exact-match rule as the live scoreboard, so this is a real
re-scoring, not a replay of a cached boolean.

Source-of-truth note: `run_summary.json`'s `score`/`correct`/`results` keys are
NOT trustworthy — run_1.1's were overwritten by a later partial re-run. Only
`scoreboard_submissions.json` (verdicts) and `run_summary["token_usage"]`
(cost) are used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG_ROOT = REPO / "log" / "v1"
TIERS = (100, 500, 1000)


def is_correct(submitted: str | None, official: str | None) -> bool:
    """The scoreboard's rule, mirrored from agent/scoreboard_client.py:9."""
    if submitted is None or official is None:
        return False
    return submitted.lower().strip() == official.lower().strip()


def load_rows(run_dir: Path) -> list[dict]:
    path = run_dir / "scoreboard_submissions.json"
    if not path.exists():
        sys.exit(
            f"{path} not found. Only runs with a submissions file can be scored "
            f"(run_1.0 predates it)."
        )
    return json.loads(path.read_text())


def filter_rows(rows: list[dict], tier: int | None, ids: list[str] | None) -> list[dict]:
    selected = rows
    if tier is not None:
        selected = [r for r in selected if r["base_points"] == tier]
    if ids:
        wanted = {i.strip().upper().lstrip("Q") for i in ids}
        selected = [r for r in selected if str(r["number"]) in wanted]
        found = {str(r["number"]) for r in selected}
        missing = sorted(wanted - found)
        if missing:
            sys.exit(f"No such question(s) in this run: {', '.join('Q' + m for m in missing)}")
    if not selected:
        sys.exit("Filter matched no questions.")
    return selected


def summarize(rows: list[dict]) -> dict:
    tiers = {t: {"correct": 0, "total": 0} for t in TIERS}
    correct = points_earned = points_possible = 0
    for row in rows:
        hit = is_correct(row["submitted"], row["official"])
        points = row["base_points"]
        points_possible += points
        if hit:
            correct += 1
            points_earned += points
        if points in tiers:
            tiers[points]["total"] += 1
            tiers[points]["correct"] += int(hit)
    return {
        "tiers": {t: v for t, v in tiers.items() if v["total"]},
        "correct": correct,
        "total": len(rows),
        "points_earned": points_earned,
        "points_possible": points_possible,
    }
