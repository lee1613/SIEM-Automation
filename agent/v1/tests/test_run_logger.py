import os

from agent_logger import RunLogger


def test_log_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    lg = RunLogger(full_run=False, version_major=1)
    assert str(tmp_path) in lg.run_dir
    assert os.path.isdir(lg.run_dir)


def test_event_log_created_in_run_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    lg = RunLogger(full_run=False, version_major=1)
    lg.events.emit("run_start", models={"sh": "gpt-5.4"})
    assert os.path.exists(os.path.join(lg.run_dir, "events.jsonl"))
