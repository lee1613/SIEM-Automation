import csv
from hint_client import HintBook


def _write_hints(path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["_key", "Hint", "HintCost", "HintNumber", "Number"])
        w.writerow(["", "Use aws:cloudtrail.", "10", "1", "200"])
        w.writerow(["", "Look at user_type.", "25", "2", "200"])


def test_get_hint_by_number_and_index(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    h = HintBook(str(p)).get_hint(200, 1)
    assert h["text"] == "Use aws:cloudtrail." and h["cost"] == 10


def test_total_hint_count(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    assert HintBook(str(p)).count_for(200) == 2


def test_missing_hint_returns_none(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    assert HintBook(str(p)).get_hint(999, 1) is None
