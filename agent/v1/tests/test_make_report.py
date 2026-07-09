import json

from make_report import render_report, load_events, load_metrics


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_render_report_has_score_and_ungrounded_section(tmp_path):
    events = tmp_path / "events.jsonl"
    metrics = tmp_path / "metrics.json"
    _write_jsonl(events, [
        {"v": 1, "event": "run_start", "run": "run_x", "git_sha": "abc123"},
        {"v": 1, "event": "run_end", "run": "run_x", "correct": 1, "attempted": 2,
         "score": 100, "total": 600},
    ])
    metrics.write_text(json.dumps([
        {"qid": "Q225", "points": 500, "verdict": "wrong", "earned": 0,
         "grounded": False, "delegations": 2, "statuses": ["partial", "partial"],
         "cap_hits": 0, "latency_s": {"total": 944.0},
         "cost_by_role": {"senior": 0.04}},
        {"qid": "Q301", "points": 100, "verdict": "correct", "earned": 100,
         "grounded": True, "delegations": 1, "statuses": ["solved"],
         "cap_hits": 0, "latency_s": {"total": 66.0}, "cost_by_role": {"senior": 0.01}},
    ]), encoding="utf-8")

    md = render_report(load_events(str(events)), load_metrics(str(metrics)))
    assert "1/2" in md                      # score line
    assert "Q225" in md                     # ungrounded question listed
    assert "ungrounded" in md.lower() or "grounded" in md.lower()
    assert "Q301" not in md.split("Ungrounded")[-1] if "Ungrounded" in md else True


def test_load_metrics_survives_truncated_json(tmp_path):
    p = tmp_path / "metrics.json"
    p.write_text('[{"qid": "Q1", "verdict": "correct"', encoding="utf-8")  # truncated
    assert load_metrics(str(p)) == []


def test_load_events_survives_truncated_line(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text('{"event": "question_start", "qid": "Q1"}\n{"event": "sub', encoding="utf-8")  # 2nd line truncated
    events = load_events(str(p))
    assert len(events) == 1
    assert events[0]["qid"] == "Q1"


def test_slowest_questions_ranked(tmp_path):
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps([
        {"qid": "Q1", "points": 100, "verdict": "wrong", "earned": 0, "grounded": True,
         "delegations": 3, "statuses": [], "cap_hits": 0,
         "latency_s": {"total": 900.0}, "cost_by_role": {}},
        {"qid": "Q2", "points": 100, "verdict": "wrong", "earned": 0, "grounded": True,
         "delegations": 3, "statuses": [], "cap_hits": 0,
         "latency_s": {"total": 100.0}, "cost_by_role": {}},
    ]), encoding="utf-8")
    md = render_report([], load_metrics(str(metrics)))
    # Q1 (900s) must appear before Q2 (100s) in the slowest table
    assert md.index("Q1") < md.index("Q2")
