# Observability P2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Finish the two remaining "nice-to-have" observability items from `docs/observability_plan.md` §P2 — a cross-run comparison tool (`compare.py`) and a live-tail mode for the report — now that P0/P1 (event stream, metrics.json, make_report) are merged.

**Architecture:** Both are pure readers over the artifacts a run already produces (`metrics.json`, `run_summary.json`, `events.jsonl`). `compare.py` diffs two run dirs into a verdict-flip / cost / latency table; `make_report.py --watch` re-renders `report.md` as `events.jsonl` grows. No runner or agent changes.

**Tech Stack:** Python 3.11, pytest 9.1.

**Depends on:** observability foundation (merged). Note: old runs (`run_1.0`, `run_1.1`) predate `metrics.json` — they only have a `run_summary.json` with an inline `results` array (old schema). `compare.py` MUST read from `metrics.json` when present and fall back to `run_summary.json`'s `results`/`index` otherwise, so a new run can be compared against `run_1.1`.

Run all commands from project root.

---

## Task 1: compare.py — cross-run verdict / cost / latency diff

**Files:**
- Create: `agent/v1/compare.py`
- Create: `agent/v1/tests/test_compare.py`

**Context:** the version docs require a per-question fixes/regressions table when comparing two versions (today hand-assembled). `compare.py <run_dir_a> <run_dir_b>` produces it: per-qid verdict flip (fixed = wrong→correct, regressed = correct→wrong), plus score/cost/latency deltas.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_compare.py`:

```python
import json

from compare import load_run, diff_runs, render_comparison


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
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    _old_schema(a)     # Q1 wrong, Q2 correct
    _new_schema(b)     # Q1 correct, Q2 wrong
    d = diff_runs(load_run(str(a)), load_run(str(b)))
    assert "Q1" in [x["qid"] for x in d["fixed"]]        # wrong -> correct
    assert "Q2" in [x["qid"] for x in d["regressed"]]    # correct -> wrong


def test_render_includes_both_sections(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    _old_schema(a); _new_schema(b)
    md = render_comparison("a", "b", diff_runs(load_run(str(a)), load_run(str(b))))
    assert "Fixed" in md and "Regressed" in md
    assert "Q1" in md and "Q2" in md
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_compare.py -v`
Expected: FAIL — no `compare` module.

- [ ] **Step 3: Implement `compare.py`**

Create `agent/v1/compare.py` with:
- `load_run(run_dir) -> dict[qid -> {"verdict","points","earned","latency_s","cost"}]`:
  read `metrics.json` if it exists (verdict/points/earned/latency_s.total/sum(cost_by_role)); ELSE read `run_summary.json` and use its `results` array (`sb_correct`→verdict, `base_points`→points, `earned`) or its `index` if that's all that's present. Latency/cost default to 0 when unavailable (old runs).
- `diff_runs(a, b) -> {"fixed": [...], "regressed": [...], "same": [...], "score_a", "score_b", "cost_a", "cost_b"}`: over the union of qids; `fixed` = a wrong/absent & b correct; `regressed` = a correct & b wrong; totals summed.
- `render_comparison(name_a, name_b, diff) -> str`: markdown — headline score/cost/latency deltas, a "Fixed (a→b)" table, a "Regressed (a→b)" table, each `| qid | pts |`.
- `main()`: `python compare.py <dir_a> <dir_b>` → writes `<dir_b>/comparison_vs_<basename(dir_a)>.md` and prints the path.

Keep it pure and defensive (missing files → empty run, never raise).

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_compare.py -v`
Expected: 4 passed.

- [ ] **Step 5: Real-data check against run_1.1**

Run: `python agent/v1/compare.py log/v1/run_1.0 log/v1/run_1.1`
Expected: writes a comparison markdown; open it and confirm the fixed/regressed lists are populated (run_1.1's result doc lists 11 fixes and 4 regressions vs v1.0 — the tool should surface a consistent set). Report the counts it produced.

- [ ] **Step 6: Commit**

```bash
git add agent/v1/compare.py agent/v1/tests/test_compare.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1): compare.py cross-run verdict/cost/latency diff"
```

---

## Task 2: make_report.py --watch (live tail)

**Files:**
- Modify: `agent/v1/make_report.py`
- Create: `agent/v1/tests/test_make_report_watch.py`

**Context:** during a long full run, re-render `report.md` periodically so progress is visible without waiting for the run to end. Pure addition to the existing `make_report.py`.

- [ ] **Step 1: Write failing test for the pure progress summary**

Extract the per-tick summary into a pure function so it's testable without a real loop. Create `agent/v1/tests/test_make_report_watch.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_make_report_watch.py -v`
Expected: FAIL — no `progress_line`.

- [ ] **Step 3: Implement `progress_line` + `--watch`**

In `agent/v1/make_report.py`:
- Add pure `progress_line(metrics) -> str`: `"<correct>/<attempted> correct · <earned> pts · $<cost> · p50 <lat>s"`.
- In `main()`, support `python make_report.py <run_dir> --watch [interval]`: loop every `interval` seconds (default 20), re-run `render_report` → `report.md`, and print `progress_line(...)`; stop on KeyboardInterrupt. Without `--watch`, behavior is unchanged (render once and exit). Use `argparse` or a minimal `sys.argv` check consistent with the current `main()`.

- [ ] **Step 4: Run test + full suite**

Run: `python -m pytest agent/v1/tests/test_make_report_watch.py agent/v1/tests/ -v`
Expected: all green.

- [ ] **Step 5: Smoke the CLI (no live run needed)**

Run: `python agent/v1/make_report.py <any existing run dir with metrics.json>` (once, no --watch)
Expected: still writes report.md as before (regression check). Then optionally `--watch 2` for a few seconds and Ctrl-C — confirm it prints progress lines and exits cleanly. Report what you saw.

- [ ] **Step 6: Commit**

```bash
git add agent/v1/make_report.py agent/v1/tests/test_make_report_watch.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1): make_report --watch live tail + progress_line"
```

---

## Done criteria

- `python -m pytest agent/v1/tests/ -v` all green.
- `compare.py` produces a fixed/regressed table across an old-schema and a new-schema run dir.
- `make_report.py --watch` re-renders on an interval; default (no flag) behavior unchanged.
- `docs/observability_plan.md` §P2 items are struck through / marked done.
