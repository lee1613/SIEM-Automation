# Observability Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the v0 multi-agent runner complete, machine-first observability — a canonical event stream, per-question/per-role cost+latency attribution, truthful worker-status labels, and an auto-rendered report — plus the P0 bugfixes that currently crash the next full run.

**Architecture:** Add a thin append-only `EventLog` (JSONL) owned by `RunLogger`; extend `UsageTracker` to bucket usage by `(qid, role, model)` and expose stage timers; fix the status classifier and the `ext[...]` NameError in the runner; wrap the raw-SDK Extractor call so LangSmith sees it and restore per-run LangSmith project naming; add `make_report.py` that turns the event stream + metrics into human views. All changes are instrumentation only — no agent decision logic changes, so behavior on the scoreboard is unchanged and each task is smoke-testable with `--ids Q200,Q210`.

**Tech Stack:** Python 3.11, pytest 9.1, langsmith 0.8.17, langgraph, LangChain callbacks.

---

## File Structure

| File | Responsibility | Change |
|------|----------------|--------|
| `agent/v0/event_log.py` | Append-only JSONL event stream + schema | **Create** |
| `agent/v0/agent_logger.py` | Run dir mgmt; owns the `EventLog`; honor `SIEM_LOG_ROOT` | Modify |
| `agent/v0/usage_tracker.py` | Bucket usage by `(qid, role, model)`; stage timers | Modify |
| `agent/v0/splunk_subagent.py` | Truthful `_classify`; return `iterations`/`cap_hit` | Modify |
| `agent/v0/run_all_v0.py` | Fix `ext` NameError; emit events; write `metrics.json`; split summary; LangSmith project name | Modify |
| `agent/v0/extractor.py` | `@traceable` wrap so extractor shows in LangSmith | Modify |
| `agent/v0/make_report.py` | Render `report.md` from `events.jsonl` + `metrics.json` | **Create** |
| `agent/v0/tests/` | pytest tests for the above | **Create** |

Run all commands from the project root:
`C:/Users/Lee023/OneDrive - National University of Singapore/Desktop/Project/SIEM Automation`
Tests import modules from `agent/v0/`; add a `conftest.py` that puts `agent/` and `agent/v0/` on `sys.path` (mirrors how `run_all_v0.py` does it).

---

## Task 1: Test harness + P0 bugfixes (unblock the next run)

**Why first:** `run_all_v0.py` currently references `ext["valid"]`/`ext["reason"]` (lines ~262-263) which were deleted when the extractor-validation node was removed — the next full run throws `NameError` on the first question. And `_classify` in `splunk_subagent.py` marks a delegation `solved` whenever the answer string is non-empty, even when the transcript ended mid-tool-call with no `FINAL ANSWER` (confirmed on Q330). Both must be fixed before any instrumentation is meaningful.

**Files:**
- Create: `agent/v0/tests/conftest.py`
- Create: `agent/v0/tests/test_classify.py`
- Modify: `agent/v0/splunk_subagent.py` (`_classify`, `_run` return dict)
- Modify: `agent/v0/run_all_v0.py` (remove `ext[...]` references)

- [ ] **Step 1: Create the test conftest**

Create `agent/v0/tests/conftest.py`:

```python
import os
import sys

AGENT_V1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent/v0
AGENT    = os.path.dirname(AGENT_V1)                                    # agent
for p in (AGENT, AGENT_V1):
    if p not in sys.path:
        sys.path.insert(0, p)
```

- [ ] **Step 2: Write failing tests for the truthful classifier**

Create `agent/v0/tests/test_classify.py`:

```python
from splunk_subagent import _classify


def test_final_answer_is_solved():
    assert _classify("Here is the result.\nFINAL ANSWER: 199.66.91.253") == "solved"

def test_partial_answer_is_partial():
    assert _classify("PARTIAL ANSWER: FYODOR-L\nUNCERTAINTY: not confirmed") == "partial"

def test_escalate_is_too_big():
    assert _classify("ESCALATE: searched dns, found nothing, narrow the window") == "too_big"

def test_empty_is_failed():
    assert _classify("") == "failed"

def test_prose_without_final_answer_tag_is_failed():
    # Q330 case: non-empty transcript tail but no FINAL ANSWER committed
    assert _classify("I was still looking at cisco:asa message_id 113019 when") == "failed"
```

- [ ] **Step 3: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_classify.py -v`
Expected: `test_prose_without_final_answer_tag_is_failed` FAILS (current code returns "solved"); the others may pass.

- [ ] **Step 4: Fix `_classify`**

In `agent/v0/splunk_subagent.py` replace the `_classify` function with:

```python
def _classify(answer: str) -> str:
    """Status from the worker's terminal message.

    'solved' requires an explicit FINAL ANSWER commitment — a non-empty tail
    with no tag means the worker never actually answered (e.g. ran out of
    iterations mid-tool-call), which must read as 'failed', not 'solved'.
    """
    a = (answer or "").strip()
    if not a:
        return "failed"
    upper = a.upper()
    if "ESCALATE:" in upper or upper.startswith("ESCALATE"):
        return "too_big"
    if "PARTIAL ANSWER" in upper:
        return "partial"
    if "FINAL ANSWER" in upper:
        return "solved"
    return "failed"
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_classify.py -v`
Expected: 5 passed.

- [ ] **Step 6: Add `iterations`/`cap_hit` to the worker result**

In `agent/v0/splunk_subagent.py`, at the top add the MAX_ITER import:

```python
from splunk_agent import MAX_ITER
```

In `SplunkWorkerPool._run`, after `answer, state = agent_mod.run_agent_traced(...)` (inside the try) and its except clause, compute iteration info from the returned state and include it in the returned dict. Change the `except` branch to also set `state = {"messages": [], "step_count": 0}`, then before the `return`:

```python
        steps   = int(state.get("step_count", 0)) if isinstance(state, dict) else 0
        cap_hit = steps > MAX_ITER
```

and add these two keys to the returned dict:

```python
            "iterations":  steps,
            "cap_hit":     cap_hit,
```

- [ ] **Step 7: Fix the `ext[...]` NameError in the runner**

In `agent/v0/run_all_v0.py`, in the `results.append({...})` block, delete these two lines:

```python
            "extractor_valid":  ext["valid"],
            "extractor_reason": ext["reason"],
```

(The extractor no longer validates; `clean` is submitted directly. No replacement keys needed.)

- [ ] **Step 8: Smoke-check the runner imports and parses**

Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v0'); import run_all_v0; import splunk_subagent; print('import ok')"`
Expected: `import ok` (no NameError, no ImportError).

- [ ] **Step 9: Commit**

```bash
git add agent/v0/tests/conftest.py agent/v0/tests/test_classify.py agent/v0/splunk_subagent.py agent/v0/run_all_v0.py
git commit -m "fix(v0): truthful worker status classifier + remove dead ext[] refs"
```

---

## Task 2: EventLog — canonical append-only JSONL event stream

**Files:**
- Create: `agent/v0/event_log.py`
- Create: `agent/v0/tests/test_event_log.py`

- [ ] **Step 1: Write failing tests**

Create `agent/v0/tests/test_event_log.py`:

```python
import json
import os

from event_log import EventLog, SCHEMA_VERSION


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
    for t in threads: t.start()
    for t in threads: t.join()
    rows = _read(tmp_path / "events.jsonl")     # every line must be valid JSON
    assert len(rows) == 120
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_event_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'event_log'`.

- [ ] **Step 3: Implement `EventLog`**

Create `agent/v0/event_log.py`:

```python
#!/usr/bin/env python3
"""
Canonical append-only event stream for a v0 multi-agent run.

One JSON object per line (JSONL). This is the machine-first system of record:
timeline.md and report.md are rendered views of it. Every event shares an
envelope (schema version, ISO-8601 local timestamp, run name, event type) plus
event-specific keys passed as kwargs.

Thread-safe: up to 6 Senior workers emit task_end events concurrently, so a
single lock serializes the write of each complete line.
"""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA_VERSION = 1


class _Timer:
    __slots__ = ("ms",)
    def __init__(self) -> None:
        self.ms = 0


class EventLog:
    """Append-only JSONL writer. All events go through emit()."""

    def __init__(self, path: str, *, run: str) -> None:
        self.path = path
        self.run  = run
        self._lock = threading.Lock()

    def emit(self, event: str, **fields) -> None:
        row = {
            "v":     SCHEMA_VERSION,
            "ts":    datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
            "run":   self.run,
            "event": event,
        }
        row.update(fields)
        line = json.dumps(row, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    @contextmanager
    def timer(self):
        """Measure wall-clock ms for a block: `with log.timer() as t: ...; t.ms`."""
        t = _Timer()
        start = time.perf_counter()
        try:
            yield t
        finally:
            t.ms = int((time.perf_counter() - start) * 1000)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_event_log.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/v0/event_log.py agent/v0/tests/test_event_log.py
git commit -m "feat(v0): add EventLog canonical JSONL event stream"
```

---

## Task 3: RunLogger owns the EventLog + honor SIEM_LOG_ROOT

**Why:** the ~30-min periodic crashes during run_0.1 were consistent with OneDrive syncing the run dir (logs + `sh_checkpoints.sqlite`) and locking files. Allow redirecting the log root to a non-synced path via env var, defaulting to today's behavior so nothing breaks if unset.

**Files:**
- Modify: `agent/v0/agent_logger.py`
- Create: `agent/v0/tests/test_run_logger.py`

- [ ] **Step 1: Write failing tests**

Create `agent/v0/tests/test_run_logger.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_run_logger.py -v`
Expected: FAIL — `RunLogger` has no `events` attr and ignores `SIEM_LOG_ROOT`.

- [ ] **Step 3: Implement the override + EventLog wiring**

In `agent/v0/agent_logger.py`:

Replace the `log_root` line in `__init__`:

```python
        log_root = os.environ.get("SIEM_LOG_ROOT") or os.path.join(PROJECT_ROOT, "log")
```

After `self._counters = {"senior": 0, "junior": 0}` add:

```python
        from event_log import EventLog
        self.events = EventLog(os.path.join(self.run_dir, "events.jsonl"),
                               run=self.run_name)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_run_logger.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/v0/agent_logger.py agent/v0/tests/test_run_logger.py
git commit -m "feat(v0): RunLogger owns EventLog + SIEM_LOG_ROOT override"
```

---

## Task 4: Per-(qid, role, model) usage attribution + stage timers

**Why:** today only SH tokens are broken out per question; Senior and Extractor cost cannot be attributed to a question. The callback already receives `tags=["senior", qid]` / `["SH", qid]`, so the qid+role are available — bucket by them.

**Files:**
- Modify: `agent/v0/usage_tracker.py`
- Modify: `agent/v0/extractor.py` (pass qid+role into `add_nim_usage`)
- Create: `agent/v0/tests/test_usage_attribution.py`

- [ ] **Step 1: Write failing tests**

Create `agent/v0/tests/test_usage_attribution.py`:

```python
from types import SimpleNamespace

from usage_tracker import UsageTracker


def _fake_llm_result(model, prompt, completion):
    gen = SimpleNamespace(usage_metadata={"input_tokens": prompt, "output_tokens": completion})
    return SimpleNamespace(
        llm_output={"model_name": model, "token_usage":
                    {"prompt_tokens": prompt, "completion_tokens": completion}},
        generations=[[gen]],
    )


def test_by_question_buckets_sh_and_senior_separately():
    t = UsageTracker()
    t.on_llm_end(_fake_llm_result("gpt-5.4", 1000, 100), tags=["SH", "Q200"])
    t.on_llm_end(_fake_llm_result("GLM-5.2-fp8", 5000, 400), tags=["senior", "Q200"])
    bq = t.by_question()
    assert bq["Q200"]["sh"]["input_tokens"] == 1000
    assert bq["Q200"]["senior"]["input_tokens"] == 5000
    assert bq["Q200"]["senior"]["output_tokens"] == 400


def test_extractor_usage_attributed_to_question():
    t = UsageTracker()
    t.add_nim_usage("deepseek-ai/DeepSeek-V4-Flash", inp=200, cached=0, out=10,
                    qid="Q200", role="extractor")
    bq = t.by_question()
    assert bq["Q200"]["extractor"]["input_tokens"] == 200


def test_totals_still_work():
    t = UsageTracker()
    t.on_llm_end(_fake_llm_result("gpt-5.4", 1000, 100), tags=["SH", "Q200"])
    tot = t.totals()
    assert tot["__total__"]["input_tokens"] == 1000
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_usage_attribution.py -v`
Expected: FAIL — no `by_question`; `add_nim_usage` has no `qid`/`role` params.

- [ ] **Step 3: Implement per-question buckets**

In `agent/v0/usage_tracker.py`:

In `__init__` add:

```python
        self._by_q: dict[tuple[str, str], dict] = {}   # (qid, role) -> bucket
```

Add a private helper (module-level or method) to record a per-(qid,role) bucket:

```python
    def _add_by_q(self, qid: str, role: str, inp: int, cached: int, out: int, usd: float) -> None:
        if not qid:
            return
        b = self._by_q.setdefault((qid, role), _empty_bucket())
        b["input_tokens"]  += inp
        b["cached_tokens"] += cached
        b["output_tokens"] += out
        b["estimated_usd"] += usd
```

In `on_llm_end`, after computing `usd` and inside the `with self._lock:` block, derive qid/role from tags and call the helper:

```python
            role = "sh" if "SH" in tags else ("senior" if "senior" in tags else "other")
            qid  = next((tg for tg in tags if isinstance(tg, str) and tg.startswith("Q")), "")
            self._add_by_q(qid, role, inp, cached, out, usd)
```

Change `add_nim_usage` signature and body to accept qid/role:

```python
    def add_nim_usage(self, model: str, inp: int, cached: int, out: int,
                      qid: str = "", role: str = "extractor") -> None:
        if not (inp or out):
            return
        usd = _call_cost(model, inp, cached, out)
        with self._lock:
            b = self._nim.setdefault(model, _empty_bucket())
            b["input_tokens"]  += inp
            b["cached_tokens"] += cached
            b["output_tokens"] += out
            b["estimated_usd"] += usd
            self._add_by_q(qid, role, inp, cached, out, usd)
```

Add a `by_question()` method:

```python
    def by_question(self) -> dict:
        """Return {qid: {role: bucket}} with per-question, per-role usage."""
        out: dict[str, dict] = {}
        with self._lock:
            for (qid, role), b in self._by_q.items():
                out.setdefault(qid, {})[role] = {
                    "input_tokens":  b["input_tokens"],
                    "cached_tokens": b["cached_tokens"],
                    "output_tokens": b["output_tokens"],
                    "estimated_usd": round(b["estimated_usd"], 6),
                }
        return out
```

- [ ] **Step 4: Update the Extractor call site**

In `agent/v0/extractor.py`, change `extract` to accept an optional `qid` and forward it:

- Change signature: `def extract(self, question: str, guidance: str, verbose_answer: str, qid: str = "") -> str:`
- In the `self.tracker.add_nim_usage(...)` call add `qid=qid, role="extractor"`.

In `agent/v0/run_all_v0.py` update the call: `clean = extractor.extract(qtext, guidance, sh_answer, qid=qid)`.

- [ ] **Step 5: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_usage_attribution.py -v`
Expected: 3 passed.

- [ ] **Step 6: Run the full test suite (no regressions)**

Run: `python -m pytest agent/v0/tests/ -v`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add agent/v0/usage_tracker.py agent/v0/extractor.py agent/v0/run_all_v0.py agent/v0/tests/test_usage_attribution.py
git commit -m "feat(v0): per-question per-role token/cost attribution"
```

---

## Task 5: Wire events into the runner + write metrics.json + split summary

**Files:**
- Modify: `agent/v0/run_all_v0.py`
- Create: `agent/v0/tests/test_metrics_row.py`

The per-question metric row is pure data assembly — extract it into a small testable helper so it doesn't require a live run to verify.

- [ ] **Step 1: Write failing test for the metrics-row builder**

Create `agent/v0/tests/test_metrics_row.py`:

```python
from run_all_v0 import build_metrics_row


def test_metrics_row_flags_ungrounded_and_verdict():
    row = build_metrics_row(
        qid="Q225", points=500, verdict="wrong", earned=0,
        clean_answer="taedonggang.jpeg",
        delegations=[
            {"status": "partial", "answer": "candidates: /images/index1.jpeg",
             "iterations": 9, "cap_hit": False},
            {"status": "partial", "answer": "no result", "iterations": 4, "cap_hit": False},
        ],
        stage_ms={"plan": 12000, "exec": 900000, "join": 30000, "extract": 2000},
        usage_by_role={"sh": {"estimated_usd": 0.002}, "senior": {"estimated_usd": 0.04}},
    )
    assert row["qid"] == "Q225"
    assert row["verdict"] == "wrong"
    assert row["delegations"] == 2
    assert row["statuses"] == ["partial", "partial"]
    assert row["cap_hits"] == 0
    # "taedonggang.jpeg" never appears verbatim in any worker answer -> ungrounded
    assert row["grounded"] is False
    assert row["latency_s"]["total"] == round((12000+900000+30000+2000)/1000, 1)


def test_metrics_row_grounded_true_when_answer_in_worker_text():
    row = build_metrics_row(
        qid="Q301", points=100, verdict="correct", earned=100,
        clean_answer="199.66.91.253",
        delegations=[{"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253",
                      "iterations": 6, "cap_hit": False}],
        stage_ms={"plan": 5000, "exec": 60000, "join": 8000, "extract": 1000},
        usage_by_role={},
    )
    assert row["grounded"] is True
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v0/tests/test_metrics_row.py -v`
Expected: FAIL — `build_metrics_row` not defined.

- [ ] **Step 3: Implement `build_metrics_row` in run_all_v0.py**

Add this module-level function to `agent/v0/run_all_v0.py` (above `main`):

```python
def build_metrics_row(*, qid, points, verdict, earned, clean_answer, delegations,
                      stage_ms, usage_by_role):
    """Assemble one per-question metrics row (pure data — unit-testable).

    `grounded` = the submitted answer appears verbatim (case-insensitive) in at
    least one worker's answer text. False here is the fabrication signal: the
    SH invented a value no delegate ever produced (Q221/Q303/Q330/Q333 class).
    """
    ca = (clean_answer or "").strip().lower()
    grounded = bool(ca) and any(
        ca in (d.get("answer") or "").lower() for d in delegations
    )
    statuses = [d.get("status", "?") for d in delegations]
    cap_hits = sum(1 for d in delegations if d.get("cap_hit"))
    total_ms = sum(stage_ms.values())
    return {
        "qid": qid,
        "points": points,
        "verdict": verdict,
        "earned": earned,
        "clean_answer": clean_answer,
        "grounded": grounded,
        "delegations": len(delegations),
        "statuses": statuses,
        "cap_hits": cap_hits,
        "latency_s": {
            "total": round(total_ms / 1000, 1),
            **{k: round(v / 1000, 1) for k, v in stage_ms.items()},
        },
        "cost_by_role": {r: round(v.get("estimated_usd", 0.0), 6)
                         for r, v in usage_by_role.items()},
    }
```

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v0/tests/test_metrics_row.py -v`
Expected: 2 passed.

- [ ] **Step 5: Emit events + metrics in the question loop**

In `agent/v0/run_all_v0.py` `main()`, integrate (do NOT change any scoring logic):

- After building `logger`, emit run manifest:
  ```python
  import subprocess
  try:
      git_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                        cwd=PROJECT_ROOT, text=True).strip()
  except Exception:
      git_sha = "unknown"
  logger.events.emit("run_start", git_sha=git_sha, full_run=full_run,
                     models={"sh": SH_MODEL, "senior": senior_model,
                             "extractor": extractor.model},
                     langsmith_project=ls_project, questions=len(selected))
  ```
  (Move this emit to after `extractor` and `ls_project` are defined.)

- At the top of the per-question loop, after `logger.timeline_question_header(...)`:
  ```python
  logger.events.emit("question_start", qid=qid, points=points)
  stage_ms = {}
  ```

- Wrap the SH call and extractor call in timers:
  ```python
  with logger.events.timer() as t_sh:
      sh_answer, _ = run_sh(sh_graph, build_sh_message(qid, qtext, guidance),
                            run_thread, qid=qid, run_name=f"SH-{qid}", tracker=tracker)
  stage_ms["sh"] = t_sh.ms

  with logger.events.timer() as t_ext:
      clean = extractor.extract(qtext, guidance, sh_answer, qid=qid)
  stage_ms["extract"] = t_ext.ms
  ```

- After the scoreboard submit + verdict is known, build and record the row:
  ```python
  verdict_str = "correct" if sb_correct else "wrong"
  ubr = tracker.by_question().get(qid, {})
  row = build_metrics_row(
      qid=qid, points=points, verdict=verdict_str, earned=pts_earned,
      clean_answer=clean, delegations=ctx.q_delegations,
      stage_ms=stage_ms, usage_by_role=ubr,
  )
  logger.events.emit("submit", qid=qid, verdict=verdict_str, earned=pts_earned,
                     grounded=row["grounded"], clean=clean)
  logger.events.emit("question_end", qid=qid, **{k: row[k] for k in
                     ("latency_s", "delegations", "statuses", "cap_hits", "cost_by_role")})
  metrics_rows.append(row)
  with open(os.path.join(logger.run_dir, "metrics.json"), "w", encoding="utf-8") as f:
      json.dump(metrics_rows, f, indent=2, ensure_ascii=False)
  ```
  Initialize `metrics_rows = []` next to `results = []` (and seed it from an existing
  `metrics.json` on resume, mirroring the `run_summary.json` resume logic).

- After the loop, emit `run_end`:
  ```python
  logger.events.emit("run_end", correct=correct_n, attempted=att,
                     score=earned_pts, total=total_points,
                     estimated_usd=tok_total.get("estimated_usd", 0))
  ```

- [ ] **Step 6: Split the heavy payload out of run_summary.json**

In the per-question `with open(summary_path...)` block, stop writing the full `results`
array into `run_summary.json`. Instead:
- Write each question's heavy record to `logger.run_dir/questions/<qid>.json`
  (create the `questions/` dir once at startup with `os.makedirs(..., exist_ok=True)`).
- Keep `run_summary.json` as a light rollup: add `"schema_version": 1`, keep
  `score/total/correct/attempted/failed_delegations/token_usage/models`, and replace
  `"results": results` with `"questions_dir": "questions"` plus a compact index list
  `[{"id", "verdict", "earned", "grounded"} ...]`.

Write the per-question file right after `results.append(...)`:
```python
os.makedirs(os.path.join(logger.run_dir, "questions"), exist_ok=True)
with open(os.path.join(logger.run_dir, "questions", f"{qid}.json"), "w",
          encoding="utf-8") as f:
    json.dump(results[-1], f, indent=2, ensure_ascii=False)
```

- [ ] **Step 7: Smoke-test the runner end-to-end on two questions**

Run: `python agent/v0/run_all_v0.py --ids Q200,Q301`
Expected: completes without error; `log/temp/<ts>/` (or `$SIEM_LOG_ROOT/temp/...`) contains
`events.jsonl` (with run_start/question_start/submit/question_end/run_end rows), `metrics.json`
(2 rows, each with `grounded`, `latency_s.total` > 0), `questions/Q200.json`, and a light
`run_summary.json`. Report the actual file contents.

- [ ] **Step 8: Commit**

```bash
git add agent/v0/run_all_v0.py agent/v0/tests/test_metrics_row.py
git commit -m "feat(v0): emit event stream + per-question metrics.json + split summary"
```

---

## Task 6: LangSmith hygiene — traceable extractor + per-run project + resume metadata

**Files:**
- Modify: `agent/v0/extractor.py`
- Modify: `agent/v0/run_all_v0.py`

- [ ] **Step 1: Make the Extractor visible in LangSmith**

In `agent/v0/extractor.py`, import and wrap the network call with the langsmith decorator so it appears as a span:

```python
from langsmith import traceable
```

Wrap the body of `extract` (or an inner `_complete` method that does the `create` call) with `@traceable(run_type="llm", name="Extractor")`. Keep the existing token-tracking; the decorator only adds a trace span. If `langsmith` import fails, fall back to a no-op decorator so the module still runs offline:

```python
try:
    from langsmith import traceable
except Exception:
    def traceable(*a, **k):
        def _wrap(fn): return fn
        return _wrap if not (len(a) == 1 and callable(a[0])) else a[0]
```

- [ ] **Step 2: Restore per-run LangSmith project naming**

In `agent/v0/run_all_v0.py`, replace the hardcoded line
`os.environ["LANGSMITH_PROJECT"] = "V1.1"` with:

```python
    os.environ["LANGSMITH_PROJECT"] = (
        f"botsv3-{logger.run_name}" if full_run else f"botsv3-{logger.run_name}"
    )
```

(Both branches use the run name — full runs give `botsv3-run_1.x`, test runs
`botsv3-test_<ts>` — matching the v0.1 architecture doc's stated behavior. Set it
**after** `logger` is created and **before** the first `run_sh`.)

- [ ] **Step 3: Tag resumed attempts**

Where the SH config is built (`run_sh` in `orchestrator.py` sets `config["metadata"]`),
pass an `attempt`/`resumed` flag through. Minimal approach: in `run_all_v0.py`, when the
resume branch fires (`if os.path.exists(summary_path)`), set a module/local
`resumed = True` (default `False`) and include it in the `run_start` event
(`logger.events.emit("run_start", ..., resumed=resumed)`). Full per-trace metadata
tagging can stay in the event log; do not over-engineer the LangSmith side.

- [ ] **Step 4: Smoke-test tracing still works**

Run: `python agent/v0/run_all_v0.py --ids Q200`
Expected: run completes; console prints `LangSmith project: botsv3-test_<ts>`; no tracing
exceptions. (Actual span visibility is verified in LangSmith UI, out of scope for the test.)

- [ ] **Step 5: Commit**

```bash
git add agent/v0/extractor.py agent/v0/run_all_v0.py
git commit -m "feat(v0): traceable extractor + per-run LangSmith project + resume flag"
```

---

## Task 7: make_report.py — render human views from the event stream

**Files:**
- Create: `agent/v0/make_report.py`
- Create: `agent/v0/tests/test_make_report.py`

- [ ] **Step 1: Write failing tests**

Create `agent/v0/tests/test_make_report.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_make_report.py -v`
Expected: FAIL — no `make_report` module.

- [ ] **Step 3: Implement `make_report.py`**

Create `agent/v0/make_report.py`:

```python
#!/usr/bin/env python3
"""
Render human-readable views from a run's canonical event stream + metrics.json.

    python agent/v0/make_report.py <run_dir>

Writes <run_dir>/report.md. Pure rendering — reads events.jsonl and metrics.json,
computes score/cost/latency rollups, ranks slowest & most expensive questions,
and surfaces the ungrounded-answer list (the fabrication signal) and cap-hit list.
"""

from __future__ import annotations

import json
import os
import sys


def load_events(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_metrics(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100) * (len(s) - 1)))))
    return s[k]


def render_report(events: list[dict], metrics: list[dict]) -> str:
    run_end = next((e for e in events if e.get("event") == "run_end"), {})
    run_start = next((e for e in events if e.get("event") == "run_start"), {})
    correct = run_end.get("correct", sum(1 for m in metrics if m.get("verdict") == "correct"))
    attempted = run_end.get("attempted", len(metrics))
    score = run_end.get("score", sum(m.get("earned", 0) for m in metrics))
    total = run_end.get("total", sum(m.get("points", 0) for m in metrics))

    lats = [m["latency_s"]["total"] for m in metrics if m.get("latency_s")]
    lines = []
    lines.append(f"# Run report — {run_start.get('run', '?')}")
    if run_start.get("git_sha"):
        lines.append(f"\n_git {run_start['git_sha']}, "
                     f"models {run_start.get('models', {})}_")
    lines.append(f"\n## Score\n\n**{correct}/{attempted}** correct — "
                 f"{score}/{total} pts\n")

    lines.append("## Latency (per question, s)\n")
    lines.append(f"- p50 {_pct(lats,50):.0f} · p95 {_pct(lats,95):.0f} · "
                 f"max {max(lats) if lats else 0:.0f}\n")

    slow = sorted(metrics, key=lambda m: m.get("latency_s", {}).get("total", 0), reverse=True)[:5]
    lines.append("### Slowest questions\n")
    lines.append("| qid | s | verdict |\n|---|---|---|")
    for m in slow:
        lines.append(f"| {m['qid']} | {m['latency_s']['total']:.0f} | {m['verdict']} |")
    lines.append("")

    exp = sorted(metrics, key=lambda m: sum(m.get("cost_by_role", {}).values()), reverse=True)[:5]
    lines.append("### Most expensive questions\n")
    lines.append("| qid | $ | verdict |\n|---|---|---|")
    for m in exp:
        lines.append(f"| {m['qid']} | {sum(m.get('cost_by_role', {}).values()):.4f} | {m['verdict']} |")
    lines.append("")

    ungrounded = [m for m in metrics if m.get("verdict") == "wrong" and not m.get("grounded")]
    lines.append(f"## Ungrounded wrong answers ({len(ungrounded)})\n")
    lines.append("_Submitted a value no worker produced — fabrication signal._\n")
    lines.append("| qid | pts | submitted |\n|---|---|---|")
    for m in ungrounded:
        lines.append(f"| {m['qid']} | {m['points']} | `{m.get('clean_answer','')}` |")
    lines.append("")

    caps = [m for m in metrics if m.get("cap_hits")]
    lines.append(f"## Questions that hit the iteration cap ({len(caps)})\n")
    lines.append("| qid | cap_hits | verdict |\n|---|---|---|")
    for m in caps:
        lines.append(f"| {m['qid']} | {m['cap_hits']} | {m['verdict']} |")
    lines.append("")

    lines.append("## Wrong / Not Answered\n")
    lines.append("| qid | pts | submitted | grounded |\n|---|---|---|---|")
    for m in metrics:
        if m.get("verdict") == "wrong":
            lines.append(f"| {m['qid']} | {m['points']} | `{m.get('clean_answer','')}` "
                         f"| {m.get('grounded')} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python make_report.py <run_dir>")
    run_dir = sys.argv[1]
    events = load_events(os.path.join(run_dir, "events.jsonl"))
    metrics = load_metrics(os.path.join(run_dir, "metrics.json"))
    md = render_report(events, metrics)
    out = os.path.join(run_dir, "report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_make_report.py -v`
Expected: 2 passed.

- [ ] **Step 5: Render a report from the Task 5 smoke-run dir**

Run: `python agent/v0/make_report.py <the log/temp/... dir from Task 5>`
Expected: `wrote .../report.md`; open it and confirm score/latency/ungrounded sections populate.

- [ ] **Step 6: Full suite + commit**

Run: `python -m pytest agent/v0/tests/ -v`
Expected: all green.

```bash
git add agent/v0/make_report.py agent/v0/tests/test_make_report.py
git commit -m "feat(v0): make_report.py renders report.md from event stream"
```

---

## Done criteria

- `python -m pytest agent/v0/tests/ -v` all green.
- `python agent/v0/run_all_v0.py --ids Q200,Q301` produces `events.jsonl`, `metrics.json`
  (with `grounded` + `latency_s`), `questions/*.json`, light `run_summary.json`, and
  `make_report.py` renders `report.md`.
- No change to scoring logic — score on the two smoke questions matches pre-change behavior.
