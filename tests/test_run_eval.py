"""Tests for the offline scorer.

The v0.2 run is the fixture: its numbers are published in the README, so if
these tests drift from the run artifacts, the storefront is lying.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import run_eval  # noqa: E402


@pytest.fixture
def isolated_artifacts(tmp_path, monkeypatch):
    """A complete on-disk run + generated-artifact workspace for CLI checks."""
    log_root = tmp_path / "log" / "v0"
    run_dir = log_root / "v0.9" / "v0.9_full_r1"
    run_dir.mkdir(parents=True)
    (run_dir / "scoreboard_submissions.json").write_text(
        json.dumps(
            [
                {
                    "number": 200,
                    "submitted": "right",
                    "official": "right",
                    "base_points": 100,
                }
            ]
        )
    )
    (run_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "token_usage": {
                    "fixture-model": {"estimated_usd": 1.25},
                    "__total__": {"estimated_usd": 1.25},
                }
            }
        )
    )

    eval_dir = tmp_path / "datasets" / "evaluation"
    eval_dir.mkdir(parents=True)
    (eval_dir / "versions.json").write_text('{"versions": []}\n')
    doc = tmp_path / "leaderboard.md"
    doc.write_text(
        "intro\n<!-- LEADERBOARD:START -->\nold\n<!-- LEADERBOARD:END -->\noutro\n"
    )

    monkeypatch.setattr(run_eval, "LOG_ROOT", log_root)
    monkeypatch.setattr(run_eval, "EVAL_DIR", eval_dir)
    monkeypatch.setattr(run_eval, "LEADERBOARD_DOC", doc)
    assert run_eval.main(["--run", "v0.9/v0.9_full_r1", "--write"]) == 0
    return eval_dir / "leaderboard.json"


def test_is_correct_ignores_case_and_surrounding_whitespace():
    assert run_eval.is_correct("  CVE-2017-16995 ", "cve-2017-16995")


def test_is_correct_rejects_substring_match():
    # "E5-2676 v3" vs "E5-2676" was a real v0.1 miss (Q202). Exact match only.
    assert not run_eval.is_correct("E5-2676 v3", "E5-2676")


def test_is_correct_handles_missing_values():
    assert not run_eval.is_correct(None, "splunk")
    assert not run_eval.is_correct("splunk", None)


def test_recomputed_verdicts_match_the_recorded_ones():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    assert len(rows) == 56
    for row in rows:
        assert run_eval.is_correct(row["submitted"], row["official"]) is bool(row["correct"]), row["number"]


def test_summarize_reproduces_the_published_v12_leaderboard():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    summary = run_eval.summarize(rows)
    assert summary["correct"] == 26
    assert summary["total"] == 56
    assert summary["points_earned"] == 8000
    assert summary["points_possible"] == 22900
    assert summary["tiers"][100] == {"correct": 15, "total": 24}
    assert summary["tiers"][500] == {"correct": 9, "total": 23}
    assert summary["tiers"][1000] == {"correct": 2, "total": 9}


def test_filter_by_tier_selects_only_that_tier():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    summary = run_eval.summarize(run_eval.filter_rows(rows, tier=1000, ids=None))
    assert (summary["correct"], summary["total"]) == (2, 9)


def test_filter_by_ids_is_case_insensitive_and_order_independent():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    summary = run_eval.summarize(run_eval.filter_rows(rows, tier=None, ids=["q333", "Q332"]))
    assert (summary["correct"], summary["total"]) == (2, 2)


def test_filter_by_unknown_id_raises():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    with pytest.raises(SystemExit):
        run_eval.filter_rows(rows, tier=None, ids=["Q999"])


def test_summarize_counts_a_tier_outside_the_standard_three():
    """Test that summarize derives tiers from data, so divergence is impossible."""
    rows = [
        {"number": 1, "submitted": "a", "official": "a", "base_points": 50},
        {"number": 2, "submitted": "b", "official": "b", "base_points": 100},
        {"number": 3, "submitted": "c", "official": "x", "base_points": 100},
    ]
    summary = run_eval.summarize(rows)
    assert 50 in summary["tiers"]
    assert 100 in summary["tiers"]
    # The sum of all tier totals must equal the overall total.
    tier_total = sum(v["total"] for v in summary["tiers"].values())
    assert tier_total == summary["total"]


def test_is_correct_handles_non_string_values():
    """Test that is_correct coerces non-string JSON values instead of crashing."""
    assert run_eval.is_correct(10, "10")
    assert run_eval.is_correct("10", 10)
    assert not run_eval.is_correct(10, "11")


def test_filter_by_tier_and_ids_together_does_not_claim_a_real_question_is_missing():
    """Test that missing-id check runs against full rows before tier narrowing."""
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    # Q200 is a real question but has base_points=100, not 1000.
    # When filtering by tier=1000 and ids=["Q200"], the combined filter matches
    # nothing, but the id error should NOT fire because the id truly exists in
    # the run. The correct error is "Filter matched no questions."
    with pytest.raises(SystemExit) as exc_info:
        run_eval.filter_rows(rows, tier=1000, ids=["Q200"])
    assert "No such question" not in str(exc_info.value)


def test_filter_by_ids_rejects_a_doubled_prefix():
    """Test that removeprefix doesn't strip characters in place of prefix."""
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    # "QQ332" is not a real question id; it should not resolve to 332.
    with pytest.raises(SystemExit):
        run_eval.filter_rows(rows, tier=None, ids=["QQ332"])


def test_load_cost_matches_the_published_v12_total():
    cost = run_eval.load_cost(REPO / "log" / "v0" / "run_0.2")
    assert round(cost["total_usd"], 2) == 31.36
    assert "gpt-5.4-2026-03-05" in cost["models"]
    # Bookkeeping keys must not be reported as if they were models.
    assert "__total__" not in cost["models"]
    assert "__sh_cumulative__" not in cost["models"]


def test_load_cost_tolerates_a_run_without_token_usage():
    # v0.0 predates cost tracking; the scorer must degrade, not crash.
    cost = run_eval.load_cost(REPO / "log" / "v0" / "v0.0" / "v0.0_full_r1")
    assert cost["total_usd"] is None
    assert cost["models"] == {}


def test_load_cost_returns_none_when_cost_was_never_tracked():
    cost = run_eval.load_cost(REPO / "log" / "v0" / "v0.0" / "v0.0_full_r1")
    assert cost["total_usd"] is None
    assert cost["models"] == {}


def test_render_report_says_not_tracked_when_cost_is_unknown():
    run_dir = REPO / "log" / "v0" / "run_0.2"
    summary = run_eval.summarize(run_eval.load_rows(run_dir))
    text = run_eval.render_report(run_dir, summary, {"models": {}, "total_usd": None})
    assert "not tracked" in text
    assert "$0.00" not in text


def test_historical_versions_match_every_parseable_run_artifact():
    expected = {
        "v0.1": (26, 56, 8300, 0.63),
        "v0.2": (26, 56, 8000, 31.36),
    }
    checked = set()
    for version in run_eval.load_versions()["versions"]:
        run_dir = REPO / "log" / "v0" / ("run_" + version["version"].removeprefix("v"))
        if not (run_dir / "scoreboard_submissions.json").exists():
            continue
        summary = run_eval.summarize(run_eval.load_rows(run_dir))
        cost = run_eval.load_cost(run_dir)
        artifact_values = (
            summary["correct"],
            summary["total"],
            summary["points_earned"],
            round(cost["total_usd"], 2),
        )
        curated_values = (
            version["correct"],
            version["questions"],
            version["points"],
            version["cost_usd"],
        )
        assert artifact_values == expected[version["version"]]
        assert curated_values == artifact_values
        checked.add(version["version"])
    assert checked >= {"v0.1", "v0.2"}


def test_latest_run_is_the_newest_complete_full_run_by_version(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "LOG_ROOT", tmp_path)
    complete = json.dumps([{}] * run_eval.COMPLETE_RUN_QUESTIONS)
    runs = {"v0.9/v0.9_full_r1": complete, "v0.10/v0.10_full_r1": complete,
            "v0.10/v0.10.1_glm_full_r1": "[{}]",          # stopped early: not complete
            "v0.10/v0.10_full_backup": complete}          # not a full-run folder
    for rel, rows in runs.items():
        (tmp_path / rel).mkdir(parents=True)
        (tmp_path / rel / "scoreboard_submissions.json").write_text(rows)
    assert run_eval.latest_run().name == "v0.10_full_r1", "0.10 > 0.9 numerically, partial run skipped"


def test_render_report_states_accuracy_points_and_cost():
    run_dir = REPO / "log" / "v0" / "run_0.2"
    text = run_eval.render_report(
        run_dir,
        run_eval.summarize(run_eval.load_rows(run_dir)),
        run_eval.load_cost(run_dir),
    )
    assert "26/56" in text
    assert "46.4%" in text
    assert "8000" in text
    assert "$31.36" in text


def test_render_leaderboard_contains_both_tables_and_real_numbers():
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    markdown = run_eval.render_leaderboard_markdown(
        run_eval.summarize(rows), run_eval.load_versions()["versions"]
    )
    assert "| 1000 pt | 2 / 9 | 22.2% |" in markdown
    assert "| 100 pt | 15 / 24 | 62.5% |" in markdown
    assert "46.4%" in markdown
    assert "$0.63" not in markdown and "$31.36" not in markdown  # untraced rows hide cost
    assert "| v0.2 | full 56 | 26 / 56 | 8000 | n/a¹ | n/a¹ |" in markdown
    assert "| $44.95 | 11.3 h |" in markdown  # v0.4.5 row


def test_traced_versions_match_their_run_logs():
    for version in run_eval.load_versions()["versions"]:
        if not version.get("traced"):
            continue
        rows, usd, seconds = [], 0.0, 0.0
        for log in version["logs"]:
            run_dir = REPO / log
            rows += run_eval.load_rows(run_dir)
            usd += run_eval.load_cost(run_dir)["total_usd"]
            metrics = json.loads((run_dir / "metrics.json").read_text())
            seconds += sum(m["latency_s"]["total"] for m in metrics)
        summary = run_eval.summarize(rows)
        assert (summary["correct"], summary["total"], summary["points_earned"]) == (
            version["correct"], version["questions"], version["points"]), version["version"]
        assert round(usd, 2) == version["cost_usd"], version["version"]
        assert round(seconds / 60) == version["latency_min"], version["version"]


def test_leaderboard_doc_block_is_in_sync():
    # Guards the exact invariant CI enforces with --check.
    rows = run_eval.load_rows(REPO / "log" / "v0" / "run_0.2")
    expected = run_eval.render_leaderboard_markdown(
        run_eval.summarize(rows), run_eval.load_versions()["versions"]
    )
    doc = REPO / "docs" / "leaderboard.md"
    assert run_eval.extract_block(doc.read_text(encoding="utf-8")) == expected.strip()


def test_check_rejects_a_missing_leaderboard_json(isolated_artifacts, capsys):
    isolated_artifacts.unlink()
    assert run_eval.main(["--run", "v0.9/v0.9_full_r1", "--check"]) == 1
    assert "leaderboard.json is missing" in capsys.readouterr().err


def test_check_rejects_a_malformed_leaderboard_json(isolated_artifacts, capsys):
    isolated_artifacts.write_text("{not json")
    assert run_eval.main(["--run", "v0.9/v0.9_full_r1", "--check"]) == 1
    assert "leaderboard.json is malformed" in capsys.readouterr().err


def test_check_rejects_a_stale_leaderboard_json(isolated_artifacts, capsys):
    payload = json.loads(isolated_artifacts.read_text())
    payload["points"]["earned"] = 0
    isolated_artifacts.write_text(json.dumps(payload))
    assert run_eval.main(["--run", "v0.9/v0.9_full_r1", "--check"]) == 1
    assert "leaderboard.json is stale" in capsys.readouterr().err


def test_check_rejects_a_stale_leaderboard_block(isolated_artifacts, capsys):
    doc = isolated_artifacts.parents[2] / "leaderboard.md"
    doc.write_text(doc.read_text().replace("100 / 100", "0 / 100"))
    assert run_eval.main(["--run", "v0.9/v0.9_full_r1", "--check"]) == 1
    assert "leaderboard table is stale" in capsys.readouterr().err


def test_write_artifacts_writes_nothing_when_markers_are_missing(tmp_path, monkeypatch):
    eval_dir = tmp_path / "evaluation"  # deliberately not created
    doc = tmp_path / "leaderboard.md"
    doc.write_text("no markers here\n")

    monkeypatch.setattr(run_eval, "EVAL_DIR", eval_dir)
    monkeypatch.setattr(run_eval, "LEADERBOARD_DOC", doc)
    monkeypatch.setattr(run_eval, "load_versions", lambda: {"versions": []})

    run_dir = tmp_path / "log" / "v0" / "v0.9" / "v0.9_full_r1"
    run_dir.mkdir(parents=True)
    summary = run_eval.summarize(
        [{"number": 1, "submitted": "a", "official": "a", "base_points": 100}]
    )
    cost = {"models": {}, "total_usd": None}

    with pytest.raises(SystemExit):
        run_eval.write_artifacts(run_dir, summary, cost)

    assert not eval_dir.exists()
    assert not (eval_dir / "leaderboard.json").exists()


def test_replace_block_is_idempotent():
    original = "intro\n<!-- LEADERBOARD:START -->\nold\n<!-- LEADERBOARD:END -->\noutro\n"
    once = run_eval.replace_block(original, "new")
    assert run_eval.replace_block(once, "new") == once
    assert "old" not in once
    assert "intro" in once and "outro" in once


def test_latest_run_finds_the_pre_v0_3_run_folders(tmp_path, monkeypatch):
    # Full runs before v0.3 keep their original folder names (run_0.0 to run_0.2).
    monkeypatch.setattr(run_eval, "LOG_ROOT", tmp_path)
    complete = json.dumps([{}] * run_eval.COMPLETE_RUN_QUESTIONS)
    runs = {"run_0.1": complete, "run_0.2": complete,
            "v0.4/v0.4.5_full_r1": "[{}]"}                # stopped early: not complete
    for rel, rows in runs.items():
        (tmp_path / rel).mkdir(parents=True)
        (tmp_path / rel / "scoreboard_submissions.json").write_text(rows)
    assert run_eval.latest_run().name == "run_0.2"
