import json

from event_log import SCHEMA_VERSION, EventLog


def _read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_emit_writes_one_json_line_per_event(tmp_path):
    log = EventLog(str(tmp_path / "events.jsonl"), run="run_test")
    log.emit("question_start", qid="Q200", points=100)
    log.emit("submit", qid="Q200", verdict="correct", earned=100)
    rows = _read(tmp_path / "events.jsonl")
    assert len(rows) == 2
    assert rows[0]["event"] == "question_start"
    assert rows[1]["event"] == "submit"


def test_every_event_has_envelope_fields(tmp_path):
    log = EventLog(str(tmp_path / "events.jsonl"), run="run_test")
    log.emit("plan", qid="Q210", round=1)
    row = _read(tmp_path / "events.jsonl")[0]
    assert row["v"] == SCHEMA_VERSION
    assert row["run"] == "run_test"
    assert row["event"] == "plan"
    assert "ts" in row and row["ts"].endswith(("+08:00", "Z")) or "T" in row["ts"]
    assert row["qid"] == "Q210"
    assert row["round"] == 1


def test_append_survives_reopen(tmp_path):
    p = str(tmp_path / "events.jsonl")
    EventLog(p, run="r").emit("run_start")
    EventLog(p, run="r").emit("run_end")          # reopen, must append not truncate
    rows = _read(p)
    assert [r["event"] for r in rows] == ["run_start", "run_end"]


def test_timer_returns_elapsed_ms(tmp_path):
    log = EventLog(str(tmp_path / "events.jsonl"), run="r")
    with log.timer() as t:
        pass
    assert isinstance(t.ms, int) and t.ms >= 0


def test_concurrent_emit_is_line_safe(tmp_path):
    import threading
    log = EventLog(str(tmp_path / "events.jsonl"), run="r")
    def worker(i):
        for j in range(20):
            log.emit("task_end", qid=f"Q{i}", task_idx=j)
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    rows = _read(tmp_path / "events.jsonl")     # every line must be valid JSON
    assert len(rows) == 120
