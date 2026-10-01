import os

import pytest
from agent_logger import RunLogger


def test_log_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    lg = RunLogger(full_run=False, version_major=0)
    assert str(tmp_path) in lg.run_dir
    assert os.path.isdir(lg.run_dir)


def test_a_full_run_lands_in_its_version_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    lg = RunLogger(full_run=True, version="0.5.0", senior_model="zai-org/GLM-5.3")
    assert lg.run_name == "v0.5/v0.5.0_glm-5.3_full_r1", "same shape --run-name takes to resume it"
    assert lg.run_dir == os.path.join(str(tmp_path), "v0", "v0.5", "v0.5.0_glm-5.3_full_r1")


def test_a_second_full_run_of_the_same_version_is_r2(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    RunLogger(full_run=True, version="0.5.0", senior_model="zai-org/GLM-5.3")
    lg = RunLogger(full_run=True, version="0.5.0", senior_model="zai-org/GLM-5.3")
    assert lg.run_name.endswith("_full_r2")


def test_a_full_run_without_a_version_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    with pytest.raises(ValueError):
        RunLogger(full_run=True, senior_model="zai-org/GLM-5.3")


def test_resume_by_run_name_reopens_the_version_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    first = RunLogger(full_run=True, version="0.5.0", senior_model="zai-org/GLM-5.3")
    again = RunLogger(full_run=True, run_name=first.run_name)
    assert again.run_dir == first.run_dir


def test_event_log_created_in_run_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SIEM_LOG_ROOT", str(tmp_path))
    lg = RunLogger(full_run=False, version_major=0)
    lg.events.emit("run_start", models={"sh": "gpt-5.4"})
    assert os.path.exists(os.path.join(lg.run_dir, "events.jsonl"))
