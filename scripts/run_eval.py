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
    return str(submitted).lower().strip() == str(official).lower().strip()


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
    if ids:
        wanted = {i.strip().upper().removeprefix("Q") for i in ids}
        # Check id existence against full rows before tier narrowing
        found_in_all = {str(r["number"]) for r in rows}
        missing = sorted(wanted - found_in_all)
        if missing:
            sys.exit(f"No such question(s) in this run: {', '.join('Q' + m for m in missing)}")
        # Now narrow by ids
        selected = [r for r in selected if str(r["number"]) in wanted]
    if tier is not None:
        selected = [r for r in selected if r["base_points"] == tier]
    if not selected:
        sys.exit("Filter matched no questions.")
    return selected


def summarize(rows: list[dict]) -> dict:
    correct = points_earned = points_possible = 0
    tiers = {}
    for row in rows:
        hit = is_correct(row["submitted"], row["official"])
        points = row["base_points"]
        points_possible += points
        if hit:
            correct += 1
            points_earned += points
        if points not in tiers:
            tiers[points] = {"correct": 0, "total": 0}
        tiers[points]["total"] += 1
        tiers[points]["correct"] += int(hit)
    return {
        "tiers": {t: tiers[t] for t in sorted(tiers.keys())},
        "correct": correct,
        "total": len(rows),
        "points_earned": points_earned,
        "points_possible": points_possible,
    }
