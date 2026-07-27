import json

from compare import diff_runs, load_run, render_comparison


def _new_schema(dirp):
    (dirp / "metrics.json").write_text(json.dumps([
        {"qid": "Q1", "points": 100, "verdict": "correct", "earned": 100,
         "grounded": True, "latency_s": {"total": 60.0}, "cost_by_role": {"senior": 0.01}},
        {"qid": "Q2", "points": 500, "verdict": "wrong", "earned": 0,
         "grounded": False, "latency_s": {"total": 200.0}, "cost_by_role": {"senior": 0.05}},
    ]), encoding="utf-8")


def _old_schema(dirp):
    (dirp / "run_summary.json").write_text(json.dumps({
        "results": [
            {"id": "Q1", "base_points": 100, "sb_correct": False, "earned": 0},
            {"id": "Q2", "base_points": 500, "sb_correct": True, "earned": 500},
        ]
    }), encoding="utf-8")


def test_load_new_schema(tmp_path):
    _new_schema(tmp_path)
    run = load_run(str(tmp_path))
    assert run["Q1"]["verdict"] == "correct"
    assert run["Q2"]["verdict"] == "wrong"


def test_load_old_schema_fallback(tmp_path):
    _old_schema(tmp_path)
    run = load_run(str(tmp_path))
    assert run["Q1"]["verdict"] == "wrong"      # sb_correct False -> wrong
    assert run["Q2"]["verdict"] == "correct"


def test_diff_identifies_fixes_and_regressions(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _old_schema(a)     # Q1 wrong, Q2 correct
    _new_schema(b)     # Q1 correct, Q2 wrong
    d = diff_runs(load_run(str(a)), load_run(str(b)))
    assert "Q1" in [x["qid"] for x in d["fixed"]]        # wrong -> correct
    assert "Q2" in [x["qid"] for x in d["regressed"]]    # correct -> wrong


def test_render_includes_both_sections(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _old_schema(a)
    _new_schema(b)
    md = render_comparison("a", "b", diff_runs(load_run(str(a)), load_run(str(b))))
    assert "Fixed" in md and "Regressed" in md
    assert "Q1" in md and "Q2" in md
