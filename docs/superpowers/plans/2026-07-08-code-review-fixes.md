# Code Review Fixes (v0.2 post-run review) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Ponytail discipline:** every task below is the smallest correct fix — reuse
> `grounding.is_grounded`/`best_candidate` and `compare.py`'s try/except pattern
> instead of inventing new helpers. Do not add abstractions beyond what each
> task's fix needs.

**Goal:** Fix the 8 findings from the `/code-review` pass on the v0.2 diff
(`docs/version_architecture/v0/v0.2.md`), none of which changed run_0.2's score —
they're bugs in verification, reporting, and retry-budget machinery.

**Architecture:** Eight independent, small fixes across `agent/v0/`. No new
files, no new abstractions. Each task is TDD'd and independently committable.

**Tech Stack:** Python 3.11, pytest 9.x.

---

## Task 1: Verifier max_iter never reaches the graph's real step-cap

**Files:**
- Modify: `agent/v0/splunk_subagent.py:105-141` (`SplunkWorkerPool.__init__`, `run_senior`)
- Modify: `agent/v0/orchestrator.py:37` (remove local `VERIFIER_MAX_ITER`, import from splunk_subagent)
- Test: `agent/v0/tests/test_verifier.py`

**Context:** `create_agent(max_iter=...)` in `agent/splunk_agent.py` closes over
`max_iter` inside `agent_node`/`should_continue` at graph-BUILD time (lines 437,
548) — it is NOT read per-call. `SplunkWorkerPool` pre-builds two graphs at
`__init__`: `self.senior_graph` (`max_iter=MAX_ITER=15`) and
`self.senior_graph_hi` (`max_iter=iter_budget(500)=25`). `run_senior`'s
`max_iter` parameter only picks between these two pre-built graphs
(`budget > MAX_ITER`) and sets `run_agent_traced`'s `recursion_limit` — it never
changes which graph's internal cap applies. The verifier calls
`run_senior(..., max_iter=VERIFIER_MAX_ITER=8)`; since `8 <= MAX_ITER(15)` it
gets `self.senior_graph`, whose real cap is 15, not 8. Fix: give the verifier
its own pre-built graph with the real cap baked in.

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_verifier.py`:

```python
def test_pool_builds_dedicated_verifier_graph():
    from splunk_subagent import SplunkWorkerPool, VERIFIER_MAX_ITER

    calls = []

    def fake_create_agent(*a, **kw):
        calls.append(kw.get("max_iter"))
        return (f"graph_maxiter_{kw.get('max_iter')}", None)

    import splunk_subagent
    orig = splunk_subagent.agent_mod.create_agent
    splunk_subagent.agent_mod.create_agent = fake_create_agent
    try:
        pool = SplunkWorkerPool(splunk=None, senior_api_key="x")
    finally:
        splunk_subagent.agent_mod.create_agent = orig

    assert VERIFIER_MAX_ITER in calls
    assert pool.verifier_graph == f"graph_maxiter_{VERIFIER_MAX_ITER}"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v0/tests/test_verifier.py::test_pool_builds_dedicated_verifier_graph -v`
Expected: FAIL — `AttributeError: 'SplunkWorkerPool' object has no attribute 'verifier_graph'` (or `VERIFIER_MAX_ITER` not importable from `splunk_subagent`).

- [ ] **Step 3: Move `VERIFIER_MAX_ITER` to splunk_subagent.py and build the dedicated graph**

In `agent/v0/splunk_subagent.py`, near the top-level constants (find `MAX_ITER`
import and `HIGH_VALUE_THRESHOLD` — add alongside them):

```python
VERIFIER_MAX_ITER = 8  # verifier runs <=3 targeted queries; no 25-iter wandering
```

In `SplunkWorkerPool.__init__`, right after `self.senior_graph_hi` is built
(currently the last statement in `__init__`), add a third pre-built graph:

```python
        self.verifier_graph, _ = agent_mod.create_agent(
            senior_api_key, splunk,
            model=senior_model, base_url=senior_base_url,
            extra_instructions=ESCALATE_INSTRUCTIONS,
            extra_tools=[web_lookup],
            max_iter=VERIFIER_MAX_ITER,
        )
```

Change `run_senior`'s graph-selection so an explicit `max_iter` override uses
the dedicated verifier graph instead of being budget-matched against the two
points-based graphs:

```python
    def run_senior(self, subquestion: str, parent_qid: str, idx: int,
                   points: int = 0, max_iter: int | None = None) -> dict:
        """`max_iter` overrides the points-based budget for the one caller that
        needs a different real graph cap (the Verifier's <=3-query pass) —
        routed to a dedicated pre-built graph so the override actually reaches
        the LangGraph step-cap check baked in at create_agent() build time."""
        if max_iter is not None:
            return self._run("senior", self.verifier_graph, self.senior_model,
                             subquestion, parent_qid, idx, max_iter=max_iter)
        budget = iter_budget(points)
        graph  = self.senior_graph_hi if budget > MAX_ITER else self.senior_graph
        return self._run("senior", graph, self.senior_model,
                         subquestion, parent_qid, idx, max_iter=budget)
```

In `agent/v0/orchestrator.py`, remove the local constant definition:

```python
VERIFIER_MAX_ITER = 8  # verifier runs <=3 targeted queries; no 25-iter wandering
```

and add a new import line near the other `from ... import ...` lines at the
top of `agent/v0/orchestrator.py` (after `from grounding import is_grounded,
best_candidate`) instead:

```python
from splunk_subagent import VERIFIER_MAX_ITER
```

so there is one definition of `VERIFIER_MAX_ITER`, not two.

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v0/tests/test_verifier.py -v`
Expected: all PASS.

- [ ] **Step 5: Run full suite + smoke a >=500pt question**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green (66+ tests).

Run: `python agent/v0/run_all_v0.py --ids Q209` (a 500pt question — triggers
the verifier). Check the console for `[SH VERIFIER OUTPUT] verdict=...` instead
of `VERIFIER FAILED (status=too_big...)` on a normal-length verifier run.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/splunk_subagent.py agent/v0/orchestrator.py agent/v0/tests/test_verifier.py
git commit -m "fix(v0): verifier gets a dedicated 8-iter graph, not a mismatched cap"
```

---

## Task 2: metrics.json grounded-check duplicates pre-fix naive logic

**Files:**
- Modify: `agent/v0/run_all_v0.py` (`build_metrics_row`, its call site)
- Test: `agent/v0/tests/test_metrics_row.py`

**Context:** `build_metrics_row`'s `grounded` field does
`ca in (d.get("answer") or "").lower()` on the WHOLE `clean_answer` string —
the exact naive check `grounding.is_grounded` replaced with component-wise
comma-list matching. Reuse `is_grounded` instead of a second, stale copy.

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_metrics_row.py` (check existing imports/fixtures in
that file first and match its style):

```python
def test_grounded_uses_component_wise_check_for_list_answers():
    delegations = [
        {"answer": "Users seen: bstoll, btun, also splunk_access and web_admin.",
         "status": "solved", "cap_hit": False},
    ]
    row = build_metrics_row(
        qid="Q200", points=100, verdict="correct", earned=100,
        clean_answer="bstoll,btun,splunk_access,web_admin",
        delegations=delegations, stage_ms={}, usage_by_role={},
        question_text="",
    )
    assert row["grounded"] is True
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v0/tests/test_metrics_row.py::test_grounded_uses_component_wise_check_for_list_answers -v`
Expected: FAIL — either `TypeError: unexpected keyword argument 'question_text'`
or `assert False is True` (naive check rejects the list answer).

- [ ] **Step 3: Reuse `is_grounded` in `build_metrics_row`**

In `agent/v0/run_all_v0.py`, find the existing import line for extractor/etc.
near the top and add:

```python
from grounding import is_grounded
```

Replace `build_metrics_row`'s signature and body (currently lines ~99-110):

```python
def build_metrics_row(*, qid, points, verdict, earned, clean_answer, delegations,
                      stage_ms, usage_by_role, question_text=""):
    """Assemble one per-question metrics row (pure data — unit-testable).

    `grounded` reuses grounding.is_grounded (component-wise for comma-joined
    list answers) so this diagnostic agrees with the actual gate the joiner
    used to accept the answer — a second, naive whole-string copy of this
    check previously reported every correct list answer as "ungrounded".
    """
    task_results = {i: {"answer": d.get("answer")} for i, d in enumerate(delegations)}
    grounded = is_grounded(clean_answer, task_results, question_text)
    statuses = [d.get("status", "?") for d in delegations]
    cap_hits = sum(1 for d in delegations if d.get("cap_hit"))
    total_ms = sum(stage_ms.values())
```

(Leave the rest of the function — the `return {...}` block — unchanged.)

Update the call site in `main()` (currently around line 396-399):

```python
        row = build_metrics_row(
            qid=qid, points=points, verdict=verdict_str, earned=pts_earned,
            clean_answer=clean, delegations=ctx.q_delegations,
            stage_ms=stage_ms, usage_by_role=ubr, question_text=qtext,
        )
```

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v0/tests/test_metrics_row.py -v`
Expected: all PASS.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/run_all_v0.py agent/v0/tests/test_metrics_row.py
git commit -m "fix(v0): metrics.json grounded field reuses is_grounded (was naive whole-string check)"
```

---

## Task 3: plan_round double-increments on grounding-forced replan

**Files:**
- Modify: `agent/v0/orchestrator.py:451-459` (`joiner_node`'s grounding-replan branch)
- Test: `agent/v0/tests/test_joiner_guard.py`

**Context:** When `decide_joiner_answer` returns `action="replan"`, `joiner_node`
sets `plan_round: plan_round + 1` and `needs_replan: True`; `route_joiner`
routes `needs_replan` straight to `"planner"`. `planner_node` independently
computes `round_n = state.get("plan_round", 0) + 1` — a SECOND increment for
the same replan. One grounding failure burns 2 of the 3 allowed rounds. The
Option-B `REPLAN` tag path (a few lines below) increments `plan_round` too but
routes to `"executor"` (skips `planner_node`), so it does NOT double-count —
only this path needs the fix: don't increment here, let `planner_node` do it.

- [ ] **Step 1: Write the failing test**

Check `agent/v0/tests/test_joiner_guard.py` for existing fixtures/imports and
match its style. Add:

```python
def test_grounding_replan_increments_plan_round_only_once():
    """joiner_node's grounding-forced-replan branch must NOT increment
    plan_round itself — route_joiner sends it to planner_node, which does its
    own +1. Double-incrementing here burns 2 of 3 replan rounds per failure."""
    from orchestrator import decide_joiner_answer

    decision = decide_joiner_answer(
        "fabricated_value", {}, "question text",
        plan_round=1, max_rounds=3,
    )
    assert decision["action"] == "replan"
    # This test documents the contract joiner_node must follow: when
    # decision["action"] == "replan", the returned state dict's "plan_round"
    # must equal the CURRENT plan_round (unchanged), not plan_round + 1 —
    # planner_node is the sole incrementer for this path.
```

This test alone can't exercise `joiner_node` in isolation (it's a closure
inside `build_sh_agent_compiler`), so it documents the contract via
`decide_joiner_answer`. The real regression check is the full-suite run in
Step 4 plus the manual trace in Step 5.

- [ ] **Step 2: Run test, verify it passes (it's a contract-documentation test, not a failing-first one)**

Run: `python -m pytest agent/v0/tests/test_joiner_guard.py -v`
Expected: PASS (this step just confirms `decide_joiner_answer` still returns
`action="replan"` for an ungrounded answer with rounds remaining — the actual
bug is in `joiner_node`'s handling of that decision, fixed in Step 3).

- [ ] **Step 3: Remove the double-increment**

In `agent/v0/orchestrator.py`, find the grounding-forced-replan return block
(currently around lines 451-459):

```python
                return {
                    "messages":     [joiner_hm, response, replan_hm],
                    "plan_text":    jtext,
                    "tasks":        [],
                    "task_results": task_results,
                    "plan_round":   plan_round + 1,
                    "done":         False,
                    "needs_replan": True,
                }
```

Change `"plan_round": plan_round + 1,` to `"plan_round": plan_round,`:

```python
                return {
                    "messages":     [joiner_hm, response, replan_hm],
                    "plan_text":    jtext,
                    "tasks":        [],
                    "task_results": task_results,
                    "plan_round":   plan_round,
                    "done":         False,
                    "needs_replan": True,
                }
```

(`planner_node`'s `round_n = state.get("plan_round", 0) + 1` now performs the
one-and-only increment for this path, matching the Option-B REPLAN path's
single-increment behavior.)

- [ ] **Step 4: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 5: Manual trace check**

Read `agent/v0/orchestrator.py`'s `planner_node` (line ~275) and `joiner_node`'s
grounding branch again side by side; confirm: starting at `plan_round=1`, one
grounding failure now produces `plan_round=2` after `planner_node` runs (not 3).

- [ ] **Step 6: Commit**

```bash
git add agent/v0/orchestrator.py agent/v0/tests/test_joiner_guard.py
git commit -m "fix(v0): grounding-forced replan no longer double-increments plan_round"
```

---

## Task 4: is_grounded whole-string check should run before component split

**Files:**
- Modify: `agent/v0/grounding.py`
- Test: `agent/v0/tests/test_grounding.py`

**Context:** `is_grounded` always splits on `,` and checks each component
independently. For a non-list value like `"1,234"`, this can vacuously ground
a fabricated composite if short fragments (e.g. a bare `"1"`) happen to appear
somewhere in unrelated evidence. Fix: try the whole string as a substring
FIRST (covers both real single values and any list whose full joined form
happens to appear verbatim); only fall back to per-component matching when the
whole-string check fails AND there's more than one component (i.e. it's
plausibly a real list).

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_grounding.py`:

```python
def test_short_numeric_value_not_vacuously_grounded_by_stray_digit():
    """'1,234' must not ground just because a bare '1' and a bare '234'
    each appear somewhere unrelated — the literal value must be traceable."""
    tr = {1: {"answer": "host count is 1 across all regions", "status": "solved"},
          2: {"answer": "port 234 was scanned", "status": "solved"}}
    assert not is_grounded("1,234", tr)


def test_whole_string_match_checked_before_split():
    """A value containing a comma that DOES appear verbatim should still
    ground via the whole-string path, even with only one worker mentioning it."""
    tr = {1: {"answer": "the total is 1,234 units", "status": "solved"}}
    assert is_grounded("1,234", tr)
```

- [ ] **Step 2: Run tests, verify the first one fails**

Run: `python -m pytest agent/v0/tests/test_grounding.py -v`
Expected: `test_short_numeric_value_not_vacuously_grounded_by_stray_digit` FAILS
(current code splits and vacuously grounds); `test_whole_string_match_checked_before_split`
already PASSES (whole string also passes the current split logic since both
fragments happen to be present together).

- [ ] **Step 3: Reorder the check — whole string first, split only as fallback**

In `agent/v0/grounding.py`, replace `is_grounded`'s body:

```python
def is_grounded(answer: str, task_results: dict, question_text: str = "") -> bool:
    """Whole answer must appear in some worker's answer text or the question.

    For comma-joined lists whose full joined string doesn't appear verbatim
    (scoreboard list answers are comma-joined while worker evidence lists the
    same values as prose/bullets — 'bstoll,btun,...' never appears joined),
    fall back to requiring EVERY component present instead. The whole-string
    check runs first so a single value that happens to contain a comma (e.g.
    '1,234') isn't vacuously grounded by unrelated short fragments matching
    elsewhere — it only degrades to per-component matching when it looks like
    a genuine multi-value list (2+ non-empty comma-separated parts) AND the
    joined form itself isn't directly traceable."""
    a = (answer or "").strip().lower()
    if not a:
        return False
    haystacks = [(question_text or "").lower()]
    haystacks += [(r.get("answer") or "").lower() for r in task_results.values()]
    if any(a in h for h in haystacks):
        return True
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) <= 1:
        return False
    return all(any(p in h for h in haystacks) for p in parts)
```

- [ ] **Step 4: Run tests, verify all pass**

Run: `python -m pytest agent/v0/tests/test_grounding.py -v`
Expected: all PASS (including the pre-existing list-answer tests from Plan A —
`bstoll,btun,splunk_access,web_admin` still grounds via the component fallback
since its whole joined string won't appear verbatim, exactly as before).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/grounding.py agent/v0/tests/test_grounding.py
git commit -m "fix(v0): is_grounded checks whole-string before comma-split (prevents vacuous digit matches)"
```

---

## Task 5: Grounding check loses evidence from earlier replan rounds

**Files:**
- Modify: `agent/v0/orchestrator.py` (`joiner_node`'s FINAL ANSWER branch)
- Test: `agent/v0/tests/test_joiner_guard.py`

**Context:** `task_results` resets to `{}` on every `REPLAN` (both the
grounding-forced path and the Option-B path). If a correct value was proven in
round 1 and the joiner restates it (from persistent chat history) as the
`FINAL ANSWER` in round 2, `decide_joiner_answer`'s grounding check only sees
round 2's (unrelated) `task_results` — the value isn't there, so a genuinely
correct answer gets rejected as "ungrounded". Fix: reuse `ctx.q_delegations`
(the orchestrator's own running list of every delegation across every round of
the current question — already used by the rounds-exhausted fallback a few
lines below) as additional grounding evidence, not just the current round's
`task_results`.

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_joiner_guard.py`:

```python
def test_decide_joiner_answer_grounds_against_prior_round_evidence():
    """A value proven in an earlier round and restated in a later round's
    FINAL ANSWER must still ground, using accumulated (not just current-round)
    evidence — this is what orchestrator.py's joiner_node must pass in."""
    from orchestrator import decide_joiner_answer

    # Simulates joiner_node merging ctx.q_delegations (prior rounds) into the
    # task_results dict passed to decide_joiner_answer.
    current_round_results = {1: {"answer": "checked an unrelated field", "status": "solved"}}
    prior_round_delegation = {"answer": "the MD5 is d41d8cd98f00b204e9800998ecf8427e"}
    combined = dict(current_round_results)
    combined["prior_0"] = prior_round_delegation

    decision = decide_joiner_answer(
        "d41d8cd98f00b204e9800998ecf8427e", combined, "question text",
        plan_round=2, max_rounds=3,
    )
    assert decision["action"] == "final"
```

- [ ] **Step 2: Run test, verify it passes (documents the expected merged-dict shape)**

Run: `python -m pytest agent/v0/tests/test_joiner_guard.py::test_decide_joiner_answer_grounds_against_prior_round_evidence -v`
Expected: PASS (`decide_joiner_answer`/`is_grounded` already handle any dict
shape correctly — the bug is that `joiner_node` doesn't build this merged dict
today; Step 3 fixes that).

- [ ] **Step 3: Merge `ctx.q_delegations` into the grounding check in `joiner_node`**

In `agent/v0/orchestrator.py`, find the FINAL ANSWER branch in `joiner_node`
(around line 438-443, right before the `decide_joiner_answer` call):

```python
            answer = fa_m.group(1).strip().split('\n')[0].strip()
            # ctx.current_question, NOT a scan of state["messages"]: the persistent
            # cross-question thread's first HumanMessage is always the run's first
            # question, and later HumanMessages are joiner/replan scaffolding.
            # run_0.2 ground-checked (and verifier-refuted) answers against Q200's
            # question text because of this.
            qtext = ctx.current_question
            decision = decide_joiner_answer(
                answer, task_results, qtext,
                plan_round=plan_round, max_rounds=MAX_PLAN_ROUNDS)
```

Replace the `decide_joiner_answer` call to ground against accumulated
evidence, not just the current round's `task_results`:

```python
            answer = fa_m.group(1).strip().split('\n')[0].strip()
            # ctx.current_question, NOT a scan of state["messages"]: the persistent
            # cross-question thread's first HumanMessage is always the run's first
            # question, and later HumanMessages are joiner/replan scaffolding.
            # run_0.2 ground-checked (and verifier-refuted) answers against Q200's
            # question text because of this.
            qtext = ctx.current_question
            # task_results resets to {} on every REPLAN, but a value proven in
            # an earlier round can still be the correct restated FINAL ANSWER —
            # ground against every delegation this question has produced so far
            # (ctx.q_delegations), not just this round's.
            grounding_evidence = dict(task_results)
            grounding_evidence.update({
                f"prior_{i}": {"answer": d.get("answer")}
                for i, d in enumerate(ctx.q_delegations)
            })
            decision = decide_joiner_answer(
                answer, grounding_evidence, qtext,
                plan_round=plan_round, max_rounds=MAX_PLAN_ROUNDS)
```

- [ ] **Step 4: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add agent/v0/orchestrator.py agent/v0/tests/test_joiner_guard.py
git commit -m "fix(v0): joiner grounding check includes prior-round delegations, not just current round"
```

---

## Task 6: make_report.py crashes on a truncated metrics.json/events.jsonl during --watch

**Files:**
- Modify: `agent/v0/make_report.py` (`load_events`, `load_metrics`)
- Test: `agent/v0/tests/test_make_report.py`

**Context:** `run_all_v0.py` fully rewrites `metrics.json` with `json.dump` on
every question (not append), and appends `events.jsonl` line-by-line.
`make_report.py --watch`'s entire purpose is polling these files WHILE a run
is in progress — a poll landing mid-write raises `JSONDecodeError` with no
guard anywhere, killing the watch loop. `compare.py`'s `load_run` already has
the right defensive pattern (return empty on read failure) — reuse it.

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_make_report.py` (check existing imports/style first):

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_make_report.py -v`
Expected: both FAIL with `json.decoder.JSONDecodeError` (uncaught).

- [ ] **Step 3: Guard both loaders**

In `agent/v0/make_report.py`, replace `load_events` and `load_metrics`:

```python
def load_events(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                break  # last line is mid-write; stop here, keep what parsed
    return out


def load_metrics(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []  # mid-write full-file rewrite; --watch will pick it up next poll
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_make_report.py -v`
Expected: all PASS.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/make_report.py agent/v0/tests/test_make_report.py
git commit -m "fix(v0): make_report --watch survives mid-write truncated JSON"
```

---

## Task 7: Extractor-outage fallback should reuse best_candidate, not raw last-line

**Files:**
- Modify: `agent/v0/run_all_v0.py` (extractor try/except block)
- Test: `agent/v0/tests/test_extractor_shape.py`

**Context:** `decide_joiner_answer`'s ungrounded-rounds-exhausted path assigns
`best_candidate(task_results)` — the FULL raw multi-line worker answer —
directly as `final_answer` (not forced to one line like the FINAL-ANSWER-tag
path is). If the extractor then fails all retries on that specific question,
`run_all_v0.py`'s crash-fallback takes `.splitlines()[-1]` of that raw prose
instead of reusing `best_candidate` (imported already, `ctx.q_delegations`
available at that point in the loop) — this is the exact class of bug
`grounding.best_candidate` exists to avoid (see the `docs/version_architecture/v0/v0.2.md`
Q200 changelog entry for the original last-line-submission bug).

- [ ] **Step 1: Write the failing test**

Check `agent/v0/tests/test_extractor_shape.py` for existing style/imports.
This fix touches `run_all_v0.py`'s inline try/except, which isn't a standalone
function — extract the fallback logic into a small pure function first so it's
testable, then call it from the try/except.

In `agent/v0/run_all_v0.py`, this pure helper does not exist yet. Add the test
first (it will fail with an import error, which is correct TDD sequencing):

```python
def test_extractor_fallback_prefers_best_candidate_over_raw_last_line():
    from run_all_v0 import extractor_fallback_answer

    delegations = [
        {"answer": "here is a lot of unrelated prose\nthe real answer is FYODOR-L",
         "status": "solved"},
    ]
    sh_answer = "here is a lot of unrelated prose\nthe real answer is FYODOR-L"
    result = extractor_fallback_answer(sh_answer, delegations)
    assert result == "here is a lot of unrelated prose\nthe real answer is FYODOR-L"
    # best_candidate returns the full worker answer (status=solved, highest rank) —
    # this documents that the fallback no longer blindly takes .splitlines()[-1]
    # of sh_answer when a real worker answer is available.


def test_extractor_fallback_uses_last_line_when_no_delegations():
    from run_all_v0 import extractor_fallback_answer

    result = extractor_fallback_answer("line one\nFYODOR-L", [])
    assert result == "FYODOR-L"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v0/tests/test_extractor_shape.py -v`
Expected: FAIL — `ImportError: cannot import name 'extractor_fallback_answer'`.

- [ ] **Step 3: Extract the fallback into a pure function, reuse best_candidate**

In `agent/v0/run_all_v0.py`, add near `build_metrics_row` (both are pure
helpers usable outside the main loop) — check the existing import line for
`from grounding import is_grounded` added in Task 2 and extend it:

```python
from grounding import is_grounded, best_candidate
```

Add the new function:

```python
def extractor_fallback_answer(sh_answer: str, delegations: list) -> str:
    """Used when the extractor fails all retries — prefer a real worker's
    answer (best_candidate, same ranking the joiner's own ungrounded-fallback
    uses) over blindly taking the last line of sh_answer, which can be raw
    multi-line prose when sh_answer came from decide_joiner_answer's
    best_candidate fallback rather than a single-line FINAL ANSWER tag."""
    task_results = {i: {"answer": d.get("answer"), "status": d.get("status")}
                    for i, d in enumerate(delegations)}
    cand = best_candidate(task_results)
    if cand:
        return cand
    stripped = (sh_answer or "").strip()
    return stripped.splitlines()[-1].strip() if stripped else ""
```

Update the extractor try/except (currently ~line 336-343):

```python
        with logger.events.timer() as t_ext:
            try:
                clean = extractor.extract(qtext, guidance, sh_answer, qid=qid, expected_shape=guidance)
            except Exception as exc:
                clean = extractor_fallback_answer(sh_answer, ctx.q_delegations)
                print(f"[EXTRACTOR] FAILED after retries ({exc}); falling back to best worker answer")
                logger.events.emit("extract_failed", qid=qid, error=str(exc)[:200])
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v0/tests/test_extractor_shape.py -v`
Expected: all PASS.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/run_all_v0.py agent/v0/tests/test_extractor_shape.py
git commit -m "fix(v0): extractor-outage fallback reuses best_candidate instead of raw last line"
```

---

## Task 8: _classify checks PARTIAL ANSWER before FINAL ANSWER

**Files:**
- Modify: `agent/v0/splunk_subagent.py:85-102` (`_classify`)
- Test: `agent/v0/tests/test_classify.py`

**Context:** The worker system prompt says "If in doubt, use PARTIAL ANSWER" —
if a model's free-form response contains BOTH phrases (e.g. "No partial answer
needed here — FINAL ANSWER: 42"), `_classify` matches `"PARTIAL ANSWER"` first
and returns `"partial"` even though a firm answer is present. Swap the check
order so a genuine `FINAL ANSWER` commitment always wins.

- [ ] **Step 1: Write the failing test**

Add to `agent/v0/tests/test_classify.py` (check existing style first):

```python
def test_final_answer_wins_when_partial_phrase_also_present():
    """A response that mentions 'partial answer' in passing but commits to a
    FINAL ANSWER must classify as solved, not partial."""
    answer = "No partial answer is needed here — FINAL ANSWER: 42"
    assert _classify(answer) == "solved"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v0/tests/test_classify.py::test_final_answer_wins_when_partial_phrase_also_present -v`
Expected: FAIL — `assert 'partial' == 'solved'`.

- [ ] **Step 3: Swap the check order**

In `agent/v0/splunk_subagent.py`, `_classify` currently:

```python
    if "PARTIAL ANSWER" in upper:
        return "partial"
    if "FINAL ANSWER" in upper:
        return "solved"
    return "failed"
```

Swap to check `FINAL ANSWER` first:

```python
    if "FINAL ANSWER" in upper:
        return "solved"
    if "PARTIAL ANSWER" in upper:
        return "partial"
    return "failed"
```

- [ ] **Step 4: Run tests, verify all pass**

Run: `python -m pytest agent/v0/tests/test_classify.py -v`
Expected: all PASS (including the pre-existing test that a genuine partial-only
response — no FINAL ANSWER tag — still classifies as `"partial"`).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v0/splunk_subagent.py agent/v0/tests/test_classify.py
git commit -m "fix(v0): _classify checks FINAL ANSWER before PARTIAL ANSWER"
```

---

## Done criteria

- `python -m pytest agent/v0/tests/ -v` all green (66 + ~12 new = ~78 tests).
- `docs/version_architecture/v0/v0.2.md` (or a fresh `v0.3.md` changelog, per
  CLAUDE.md's in-progress-version rule — check which version is "in progress"
  when this plan is executed) gets a one-line entry per task in the same turn
  as each fix.
- Smoke-test at least one >=500pt question (`--ids Q209` or similar) after
  Task 1 to visually confirm the verifier no longer reports spurious
  `VERIFIER FAILED (cap_hit=True)` on normal-length runs.
- No task adds a new file, new class, or new abstraction beyond what's shown
  above — every fix reuses an existing helper (`is_grounded`, `best_candidate`,
  `compare.py`'s try/except pattern) or is a same-file minimal edit.
