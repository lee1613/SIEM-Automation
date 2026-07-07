from make_report import progress_line, load_metrics
import json


def test_progress_line_counts_and_cost(tmp_path):
    m = tmp_path / "metrics.json"
    m.write_text(json.dumps([
        {"qid": "Q1", "verdict": "correct", "earned": 100, "points": 100,
         "grounded": True, "latency_s": {"total": 60.0}, "cost_by_role": {"senior": 0.01}},
        {"qid": "Q2", "verdict": "wrong", "earned": 0, "points": 500,
         "grounded": False, "latency_s": {"total": 200.0}, "cost_by_role": {"senior": 0.05}},
    ]), encoding="utf-8")
    line = progress_line(load_metrics(str(m)))
    assert "1/2" in line          # correct/attempted
    assert "100" in line          # points earned
    assert "0.06" in line or "0.0600" in line  # cumulative cost
