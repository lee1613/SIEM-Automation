"""Tests for the offline scorer.

The v1.2 run is the fixture: its numbers are published in the README, so if
these tests drift from the run artifacts, the storefront is lying.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import run_eval  # noqa: E402


def test_is_correct_ignores_case_and_surrounding_whitespace():
    assert run_eval.is_correct("  CVE-2017-16995 ", "cve-2017-16995")


def test_is_correct_rejects_substring_match():
    # "E5-2676 v3" vs "E5-2676" was a real v1.1 miss (Q202). Exact match only.
    assert not run_eval.is_correct("E5-2676 v3", "E5-2676")


def test_is_correct_handles_missing_values():
    assert not run_eval.is_correct(None, "splunk")
    assert not run_eval.is_correct("splunk", None)


def test_recomputed_verdicts_match_the_recorded_ones():
    rows = run_eval.load_rows(REPO / "log" / "v1" / "run_1.2")
    assert len(rows) == 56
    for row in rows:
        assert run_eval.is_correct(row["submitted"], row["official"]) is bool(row["correct"]), row["number"]


def test_summarize_reproduces_the_published_v12_leaderboard():
    rows = run_eval.load_rows(REPO / "log" / "v1" / "run_1.2")
    summary = run_eval.summarize(rows)
    assert summary["correct"] == 26
    assert summary["total"] == 56
    assert summary["points_earned"] == 8000
    assert summary["points_possible"] == 22900
    assert summary["tiers"][100] == {"correct": 15, "total": 24}
    assert summary["tiers"][500] == {"correct": 9, "total": 23}
    assert summary["tiers"][1000] == {"correct": 2, "total": 9}


def test_filter_by_tier_selects_only_that_tier():
    rows = run_eval.load_rows(REPO / "log" / "v1" / "run_1.2")
    summary = run_eval.summarize(run_eval.filter_rows(rows, tier=1000, ids=None))
    assert (summary["correct"], summary["total"]) == (2, 9)


def test_filter_by_ids_is_case_insensitive_and_order_independent():
    rows = run_eval.load_rows(REPO / "log" / "v1" / "run_1.2")
    summary = run_eval.summarize(run_eval.filter_rows(rows, tier=None, ids=["q333", "Q332"]))
    assert (summary["correct"], summary["total"]) == (2, 2)


def test_filter_by_unknown_id_raises():
    rows = run_eval.load_rows(REPO / "log" / "v1" / "run_1.2")
    with pytest.raises(SystemExit):
        run_eval.filter_rows(rows, tier=None, ids=["Q999"])
