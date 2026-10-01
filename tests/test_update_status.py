"""The README status badges are derived from the docs folders, not typed by hand."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_status  # noqa: E402

README_BEFORE = (
    "[released-shield]: https://img.shields.io/badge/old-old-2ea44f?style=for-the-badge\n"
    "[progress-shield]: https://img.shields.io/badge/old-old-d29922?style=for-the-badge\n"
    "[next-shield]: https://img.shields.io/badge/old-old-6e7781?style=for-the-badge\n"
)


def make_repo(tmp_path, results, architectures, versions):
    result_dir = tmp_path / "docs" / "scoreboard_result" / "v0"
    arch_dir = tmp_path / "docs" / "version_architecture" / "v0"
    eval_dir = tmp_path / "datasets" / "evaluation"
    for folder in (result_dir, arch_dir, eval_dir):
        folder.mkdir(parents=True)
    for name in results:
        (result_dir / name).write_text("result")
    for name in architectures:
        (arch_dir / name).write_text("design")
    (eval_dir / "versions.json").write_text(json.dumps({"versions": versions}))
    (tmp_path / "README.md").write_text(README_BEFORE)
    return tmp_path


VERSIONS = [{"version": "v0.4.5", "correct": 24, "questions": 50}]


def test_released_is_the_highest_version_with_a_result_doc_numerically(tmp_path):
    repo = make_repo(tmp_path, ["v0.2.md", "v0.10.md", "v0.9.md", "v0.0.0_full_run.json"],
                     ["v0.2.md"], [{"version": "v0.10", "correct": 30, "questions": 56}])
    assert update_status.derive(repo)["released"] == ("v0.10", "30/56")


def test_in_progress_and_next_are_the_architecture_docs_newer_than_released(tmp_path):
    repo = make_repo(tmp_path, ["v0.4.5.md"],
                     ["v0.4.5.md", "v0.5.1.md", "v0.5.0.md", "v0.2_improvement_plans.md"], VERSIONS)
    status = update_status.derive(repo)
    assert (status["in_progress"], status["next"]) == ("v0.5.0", "v0.5.1")


def test_missing_versions_are_reported_as_none(tmp_path):
    repo = make_repo(tmp_path, ["v0.4.5.md"], ["v0.4.5.md"], VERSIONS)
    status = update_status.derive(repo)
    assert (status["in_progress"], status["next"]) == (None, None)


def test_released_without_a_versions_row_shows_the_version_only(tmp_path):
    repo = make_repo(tmp_path, ["v0.7.md"], ["v0.7.md"], VERSIONS)
    assert update_status.derive(repo)["released"] == ("v0.7", None)


def test_write_rewrites_only_the_three_shield_lines_and_check_agrees(tmp_path):
    repo = make_repo(tmp_path, ["v0.4.5.md"], ["v0.4.5.md", "v0.5.0.md", "v0.5.1.md"], VERSIONS)
    assert update_status.main(["--check"], repo) == 1
    assert update_status.main(["--write"], repo) == 0
    text = (repo / "README.md").read_text()
    assert "released-v0.4.5%20%C2%B7%2024%2F50-2ea44f" in text
    assert "in%20progress-v0.5.0-d29922" in text and "next-v0.5.1-6e7781" in text
    assert update_status.main(["--check"], repo) == 0


def test_write_is_idempotent(tmp_path):
    repo = make_repo(tmp_path, ["v0.4.5.md"], ["v0.4.5.md", "v0.5.0.md"], VERSIONS)
    update_status.main(["--write"], repo)
    once = (repo / "README.md").read_text()
    update_status.main(["--write"], repo)
    assert (repo / "README.md").read_text() == once


def test_write_fails_loudly_when_a_shield_line_is_missing(tmp_path):
    repo = make_repo(tmp_path, ["v0.4.5.md"], ["v0.4.5.md"], VERSIONS)
    (repo / "README.md").write_text("no shields here\n")
    with pytest.raises(SystemExit):
        update_status.main(["--write"], repo)
