"""The demo's smoke comparison must match its committed rows (CI also runs --check)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import smoke_eval  # noqa: E402


def test_committed_smoke_comparison_is_in_sync():
    assert smoke_eval.main(["--check"]) == 0


def test_insights_follow_the_numbers():
    spec = {
        "questions": ["Q216"], "baseline_run": "run_1.2",
        "same_senior": ["old", "new"], "best": "new",
        "arms": [{"id": i, "version": i, "loop": i, "senior": "m"} for i in ("old", "new")],
    }

    def row(verdict, cost, secs):
        return [{"qid": "Q216", "verdict": verdict, "answer": "x", "latency_s": secs,
                 "cost_by_role": {"sh": cost / 2, "senior": cost / 2}}]

    out = smoke_eval.build(spec, {"old": row("wrong", 2.0, 600), "new": row("correct", 1.0, 1200)})
    cost, acc, lat = out["insights"]
    assert "50% less" in cost
    assert "solved 1/1 (Q216)" in acc
    assert "2.0×" in lat and "10.0 → 20.0 min" in lat
