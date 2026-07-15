# Plan B — Candidate Ledger + Failure Handoff + Case File + Specialists Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.
>
> **Supersedes** `2026-07-07-plan-b-casefile-blackboard.md` (written before run_1.2 completed;
> re-grounded here against `docs/version_architecture/v1/v1.2_improvement_plans.md` as updated
> by commit `17f38db`, `docs/scoreboard_result/v1/v1.2.md`, and the 8 landed v1.3 code-review
> fixes).

**Goal:** Make every delegation's answer durable and auditable (candidate ledger — the joiner copies verbatim, never re-types), stop failed/cap-hit delegations from triggering blind fresh-context replans (failure handoff — the single biggest cost lever: 62 failed delegations burned $26.53 of run_1.2's $31.36), and turn 56 isolated solves into one investigation (case file + recon + specialists + hints).

**Architecture:** Pure helpers in `case_file.py` build a per-question **candidate ledger** from `ctx.q_delegations`; the joiner must choose FROM it and a deterministic snap restores the ledger's verbatim byte form. A **failure-handoff digest** (sourcetypes tried, SPL already run, where the trail went cold) is built from every failed/too_big/cap-hit delegation record and injected into replan planning and replacement-worker subquestions. A JSON-backed `CaseFile` (entities + findings, `status ∈ {verified, hypothesis, refuted}`) is the SH's cross-question substrate; Phase-0 recon seeds it; the Verifier promotes/refutes findings. The planner tags tasks `[HUNTER]`/`[CONTENT]`/`[METRICS]` and the pool selects a matching worker graph. `HintBook` buys official hints on low-confidence ≥500-pt questions.

**Tech Stack:** Python 3.11, pytest, LangGraph, existing v0 worker graph (`agent/splunk_agent.py`), CSV hint data (`botsv3content/ctf_hints.csv`).

**Depends on:** Plan A (merged), observability foundation (merged), and the 8 v1.3 code-review fixes (merged, `246d444`→`5bd3283`; suite baseline **77 passing**). Build ON TOP of origin/jy HEAD `17f38db`. **The Mac working copy is behind origin/jy with rewritten history — sync it (`git fetch && git reset --hard origin/jy`, old history stays reachable via `judge`) before executing any task.**

## Global Constraints

- Every code change gets a same-turn changelog line in `docs/version_architecture/v1/v1.3.md` (per project CLAUDE.md — v1.3 is the in-progress version; no full run has closed it).
- Commit prefix: `feat(v1.3-planB): …`.
- Test runs (`--ids`) auto-land in `log/temp/` — never `log/v1/`, never cost-tracked.
- **Validation policy (5-question smoke):** per-task micro-smokes use 1–2 questions; before declaring Plan B done, ONE combined 5-question smoke: `--ids Q216,Q303,Q329,Q330,Q331` (case-file cascade, content-inspector, recon, hunter-scope, metrics+ledger). The human triggers the full 56-Q run.
- Selection/ranking between grounded candidates is **Plan C's job** — this plan only makes candidates durable, verbatim, and auditable. No adjudicator logic here.
- Flags: ledger, handoff, case file default ON (they are the v1.3 fix under measurement, vs run_1.2 baseline via `compare.py`); `--recon` and `--hints` default OFF.
- No new dependencies. No change to the scoring/submit path except the explicit hint-cost deduction.
- Success metrics for the eventual full run: `failed_delegations` trending toward v1.1's ~0 (run_1.2: 62), Senior input tokens cut >50% (run_1.2: 28.2M), run cost back under ~$5 (run_1.2: $31.36).

---

## What changed vs the 2026-07-07 plan (read this before executing)

| Change | Why |
|---|---|
| **NEW Tasks 1–3: candidate ledger + joiner copy-contract + failure handoff** — now the highest-priority items | run_1.2: 9 questions / **5,100 pts** lost with a correct grounded candidate already sitting in a delegation while the joiner picked (or re-typed) something else (Q215 `BSTOLL-L.froth.ly`→`BSTOLL-L`, Q221 `nullweb_admin`→`web_admin`, Q331 `1367.875`→`1499.25`); 103/204 delegations cap-hit, 62 failed, each failure → blind fresh-context replan = **$26.53** of Senior input tokens |
| **Dropped `python_calc` tool** | run_1.2 Q331: the worker doing *manual* arithmetic beat out the worker using SPL `perc25()/perc75()` — despite "using Splunk commands only" in the question. A calculator tool encourages exactly that violation. Metrics-Analyst now mandates SPL-native computation instead |
| Specialist evidence updated | Q303 (password in cloud-init raw events; workers ID'd the sourcetype then capped before reading), Q330 (3 VPN users ranked, `mkraeusen` never enumerated — scope-first), replacing v1.1-era citations |
| Changelog target `v1.2.md` → `v1.3.md` | v1.3 is the in-progress version |
| Verifier references updated | Verifier now runs on a dedicated `pool.verifier_graph` (`VERIFIER_MAX_ITER=8` baked in, lives in `splunk_subagent.py`); `verifier_node` has explicit `verifier_failed` paths — hypothesis promotion (Task 8) hooks only the success path |
| Validation policy: "2–4 Q smokes" → 5-question smoke set | current policy |
| Hint policy evidence updated | run_1.2's honest-refusal profile (Q328: no evidence after 5 delegations; Q303) is exactly where a 10–25 pt hint converts a 0 into 475–990 |

Task order = priority order. If execution is cut short, Tasks 1–3 alone are worth landing.

---

## File Structure

| File | Responsibility | Change |
|------|----------------|--------|
| `agent/v1/case_file.py` | `CaseFile` store; candidate-ledger builders (`extract_candidate`, `build_ledger`, `snap_to_ledger`); `CASE UPDATES:` parser | **Create** |
| `agent/v1/orchestrator.py` | Joiner renders ledger + copy contract + snap; `build_handoff_digest` + handoff wiring; planner digest; specialist task tags; verifier promotes findings | Modify |
| `agent/v1/specialists.py` | Specialist prompt configs + `parse_specialist_tag` | **Create** |
| `agent/v1/splunk_subagent.py` | Per-specialist worker graphs; select by tag | Modify |
| `agent/v1/recon.py` | Phase-0 recon pass | **Create** |
| `agent/v1/hint_client.py` | `HintBook` — load hints CSV | **Create** |
| `agent/v1/run_all_v1.py` | Init case file; record ledger per question; recon + hint flags | Modify |
| `agent/v1/tests/` | pytest per task | add files |

Run all commands from project root. The case file lives at `<run_dir>/case_file.json` (survives resume, like `metrics.json`). Tests import bare module names — `agent/v1/tests/conftest.py` already puts `agent/` and `agent/v1/` on `sys.path`.

---

## Task 1: Candidate ledger (pure functions, the Plan-C substrate)

**Files:**
- Create: `agent/v1/case_file.py` (ledger half; `CaseFile` class arrives in Task 4)
- Create: `agent/v1/tests/test_ledger.py`

**Interfaces:**
- Consumes: delegation record dicts as built in `executor_node` (`orchestrator.py:380` — keys `answer`, `status`, `worker`, `spl_used`, `sourcetypes`, `iterations`, `cap_hit`).
- Produces: `extract_candidate(delegation: dict) -> dict | None`, `build_ledger(delegations: list) -> list[dict]`, `snap_to_ledger(answer: str, ledger: list) -> str` — used by Task 2's joiner wiring and recorded by the runner for Plan C.

**Context:** run_1.2 lost 5,100 pts to selection/re-typing after the correct value was already in a delegation's answer. The ledger records each delegation's **verbatim** FINAL/PARTIAL value + evidence + SPL at capture time. The joiner then copies, never re-types. Snap is deliberately narrow: it restores byte-exact form only when the joiner's pick case-insensitively equals a ledger value — it never *changes* which value was picked (prefix/superset arbitration like Q215's FQDN-vs-short-hostname is a ranking judgment, i.e. Plan C).

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_ledger.py`:

```python
from case_file import extract_candidate, build_ledger, snap_to_ledger


def _deleg(answer, status="solved", spl=None, worker="senior#1"):
    return {"answer": answer, "status": status, "worker": worker,
            "spl_used": spl or [], "sourcetypes": [], "iterations": 3,
            "cap_hit": False}


def test_extract_final_answer_value_verbatim():
    d = _deleg("Ran stats.\nFINAL ANSWER: BSTOLL-L.froth.ly\nSPL: search ...",
               spl=["search index=botsv3 | stats count by host"])
    c = extract_candidate(d)
    assert c["value"] == "BSTOLL-L.froth.ly"
    assert c["status"] == "solved"
    assert c["spl"] == ["search index=botsv3 | stats count by host"]


def test_extract_partial_answer_value():
    c = extract_candidate(_deleg("PARTIAL ANSWER: nullweb_admin\nUNCERTAINTY: ...",
                                 status="partial"))
    assert c["value"] == "nullweb_admin"


def test_extract_none_when_no_tag():
    assert extract_candidate(_deleg("ESCALATE: nothing found", status="too_big")) is None
    assert extract_candidate(_deleg("")) is None


def test_build_ledger_dedupes_case_insensitively_keeps_first_form():
    ledger = build_ledger([_deleg("FINAL ANSWER: NullWeb_Admin"),
                           _deleg("FINAL ANSWER: nullweb_admin"),
                           _deleg("FINAL ANSWER: 1367.875", status="partial")])
    assert [c["value"] for c in ledger] == ["NullWeb_Admin", "1367.875"]


def test_snap_restores_verbatim_ledger_form():
    ledger = build_ledger([_deleg("FINAL ANSWER: BSTOLL-L.froth.ly")])
    assert snap_to_ledger("bstoll-l.froth.ly", ledger) == "BSTOLL-L.froth.ly"


def test_snap_never_changes_a_different_value():
    ledger = build_ledger([_deleg("FINAL ANSWER: BSTOLL-L.froth.ly")])
    # A truncation is a DIFFERENT pick, not a casing slip — snap must not "fix" it.
    assert snap_to_ledger("BSTOLL-L", ledger) == "BSTOLL-L"
    assert snap_to_ledger("mkraeusen", ledger) == "mkraeusen"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_ledger.py -v`
Expected: FAIL — no `case_file` module.

- [ ] **Step 3: Implement the ledger half of `case_file.py`**

Create `agent/v1/case_file.py`:

```python
#!/usr/bin/env python3
"""
Candidate ledger + (Task 4) case-file store for the v1 SH.

Ledger: every delegation's FINAL/PARTIAL ANSWER value is captured VERBATIM at
delegation time, with its evidence and SPL. The joiner chooses FROM the ledger
and copies — never re-types. run_1.2 lost 5,100 pts to values that existed in
a worker's answer and were mangled or bypassed at synthesis time (Q215
BSTOLL-L.froth.ly -> BSTOLL-L, Q221 nullweb_admin -> web_admin, Q331
1367.875 -> 1499.25). The ledger is also Plan C's adjudication input.
"""

from __future__ import annotations

import re

_ANSWER_TAG = re.compile(r'(?:FINAL|PARTIAL)\s+ANSWER:\s*(.+)', re.IGNORECASE)


def extract_candidate(delegation: dict) -> dict | None:
    """Verbatim candidate from one delegation record; None if it never committed
    to a value (ESCALATE / empty / crashed)."""
    text = delegation.get("answer") or ""
    m = _ANSWER_TAG.search(text)
    if not m:
        return None
    value = m.group(1).strip().splitlines()[0].strip()
    if not value:
        return None
    spl = delegation.get("spl_used") or []
    return {
        "value":    value,                       # verbatim — the joiner copies this
        "status":   delegation.get("status", "?"),
        "worker":   delegation.get("worker", ""),
        "spl":      spl[-1:],                    # the query that produced it
        "evidence": text[:400],
    }


def build_ledger(delegations: list) -> list[dict]:
    """One entry per distinct value (case-insensitive), first-seen form wins."""
    seen: set = set()
    out = []
    for d in delegations:
        c = extract_candidate(d)
        if c and c["value"].lower() not in seen:
            seen.add(c["value"].lower())
            out.append(c)
    return out


def snap_to_ledger(answer: str, ledger: list) -> str:
    """Byte-exact fidelity: if the answer case-insensitively equals a ledger
    value, return the ledger's verbatim form. Never substitutes a different
    value — truncations/supersets are a selection judgment (Plan C), not a
    casing slip."""
    a = (answer or "").strip().lower()
    for c in ledger:
        if c["value"].strip().lower() == a:
            return c["value"]
    return answer


def render_ledger(ledger: list) -> str:
    """Joiner-facing candidate block."""
    if not ledger:
        return ""
    lines = ["CANDIDATES (each captured verbatim from a worker — your FINAL ANSWER "
             "must be copied character-for-character from one of these, or from "
             "the question text):"]
    for i, c in enumerate(ledger, 1):
        spl = f"  SPL: {c['spl'][0][:160]}" if c["spl"] else ""
        lines.append(f"  {i}. `{c['value']}`  [{c['status']}, {c['worker']}]{spl}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_ledger.py -v`
Expected: 6 passed.

- [ ] **Step 5: Changelog + commit**

Add to `docs/version_architecture/v1/v1.3.md` changelog: "Plan B Task 1: candidate ledger (`case_file.py`) — verbatim per-delegation value + evidence + SPL, dedupe, narrow snap-to-verbatim."

```bash
git add agent/v1/case_file.py agent/v1/tests/test_ledger.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): candidate ledger — verbatim capture, dedupe, snap-to-verbatim"
```

---

## Task 2: Joiner chooses FROM the ledger (copy, never re-type)

**Files:**
- Modify: `agent/v1/orchestrator.py` (`JOINER_SYSTEM_PROMPT`, `joiner_node`)
- Modify: `agent/v1/run_all_v1.py` (record ledger per question)
- Create: `agent/v1/tests/test_joiner_ledger.py`

**Interfaces:**
- Consumes: `build_ledger`, `render_ledger`, `snap_to_ledger` from Task 1; `ctx.q_delegations` (all rounds' delegation records).
- Produces: `candidate_ledger` key in each `questions/<qid>.json` record (Plan C reads this); ledger block inside the joiner's HumanMessage; snapped `final_answer`.

**Context:** wiring. The ledger is rendered into the joiner message (so the LLM sees exact strings to copy), the copy contract goes into the prompt, and the deterministic snap runs right after the FINAL ANSWER parse — before the existing grounding gate at `orchestrator.py:453-460` (a snapped value is by construction grounded, so no interaction).

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_joiner_ledger.py`:

```python
from case_file import build_ledger, render_ledger, snap_to_ledger


def test_render_contains_verbatim_values_and_contract():
    ledger = build_ledger([{"answer": "FINAL ANSWER: 1367.875", "status": "solved",
                            "worker": "senior#2", "spl_used": ["| stats perc25(x)"],
                            "sourcetypes": [], "iterations": 5, "cap_hit": False}])
    r = render_ledger(ledger)
    assert "1367.875" in r and "character-for-character" in r


def test_snap_pipeline_restores_worker_form():
    delegs = [{"answer": "FINAL ANSWER: nullweb_admin", "status": "solved",
               "worker": "senior#1", "spl_used": [], "sourcetypes": [],
               "iterations": 2, "cap_hit": False}]
    ledger = build_ledger(delegs)
    assert snap_to_ledger("NULLWEB_ADMIN", ledger) == "nullweb_admin"


def test_empty_delegations_render_empty():
    assert render_ledger(build_ledger([])) == ""
```

- [ ] **Step 2: Run tests** (these exercise Task-1 code plus `render_ledger`; if all pass immediately, proceed)

Run: `python -m pytest agent/v1/tests/test_joiner_ledger.py -v`

- [ ] **Step 3: Wire into `joiner_node`**

In `agent/v1/orchestrator.py`:

1. Import at top (with the other local imports, after `from grounding import ...`):

```python
from case_file import build_ledger, render_ledger, snap_to_ledger
```

2. In `joiner_node`, after `findings = "\n\n".join(parts)` (line ~423), build and append the ledger block:

```python
        ledger = build_ledger(ctx.q_delegations)
        ledger_block = render_ledger(ledger)

        joiner_msg_text = (
            f"All delegated tasks are complete (round {plan_round}).\n\n"
            f"=== Task Results ===\n{findings}\n\n"
            + (ledger_block + "\n\n" if ledger_block else "")
            + "Synthesize the above and give your FINAL ANSWER, "
              "or request a focused REPLAN if a critical datum is missing."
        )
```

3. In the FINAL ANSWER branch, immediately after `answer = fa_m.group(1).strip().split('\n')[0].strip()` (line ~442):

```python
            snapped = snap_to_ledger(answer, ledger)
            if snapped != answer:
                print(f"[SH JOINER] ledger snap: {answer!r} -> {snapped!r}")
                answer = snapped
```

4. Append to `JOINER_SYSTEM_PROMPT` (after the GROUNDING RULE block):

```
LEDGER RULE — when a CANDIDATES list is provided, your FINAL ANSWER must be one
of those values copied character-for-character (or a value from the question
text). Do not re-type, trim, expand, or reformat a candidate: no dropping
domain suffixes, no rounding numbers, no removing prefixes. If two candidates
conflict, prefer the one whose SPL and status best satisfy the question's own
constraints, and copy it exactly.
```

- [ ] **Step 4: Record the ledger for Plan C**

In `agent/v1/run_all_v1.py`, import `from case_file import build_ledger` and add one key to the per-question results dict (line ~407, next to `"delegations"`):

```python
            "candidate_ledger": build_ledger(ctx.q_delegations),
```

- [ ] **Step 5: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -q` — expect 77 + new, all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import orchestrator; print('ok')"`

- [ ] **Step 6: Micro-smoke — the re-typing class**

Run: `python agent/v1/run_all_v1.py --ids Q221`
Expected: completes; `log/temp/<ts>/questions/Q221.json` contains `candidate_ledger`; report whether the joiner message showed a CANDIDATES block and whether the submitted value is byte-identical to a ledger entry.

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Plan B Task 2: joiner renders candidate ledger, copy contract in prompt, deterministic snap-to-verbatim before the grounding gate; runner records `candidate_ledger` per question."

```bash
git add agent/v1/orchestrator.py agent/v1/run_all_v1.py agent/v1/tests/test_joiner_ledger.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): joiner copies from candidate ledger, never re-types"
```

---

## Task 3: Failure handoff (the cost lever)

**Files:**
- Modify: `agent/v1/orchestrator.py` (`build_handoff_digest`, `DelegationContext`, `executor_node`, `joiner_node`)
- Create: `agent/v1/tests/test_handoff.py`

**Interfaces:**
- Consumes: delegation record dicts (same shape as Task 1).
- Produces: `build_handoff_digest(record: dict) -> str`; `ctx.q_handoffs: list[str]` (reset per question); handoff text appended to replacement-worker subquestions and to the joiner message.

**Context:** run_1.2's $26.53 Senior burn: 62 failed + 103 cap-hit delegations, each triggering a REPLAN whose fresh workers re-ran the same discovery searches from zero. The handoff digest tells worker #2 what was already tried (sourcetypes, SPL) and where the trail went cold, so it resumes the hunt instead of restarting it. Target: `failed_delegations` → ~0, Senior input tokens −50%.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_handoff.py`:

```python
from orchestrator import build_handoff_digest


def _rec(status="failed", cap_hit=False):
    return {"status": status, "cap_hit": cap_hit, "iterations": 25,
            "answer": "Searched cloudwatch logs... found the cloud-init sourcetype "
                      "but ran out of iterations before reading raw events.",
            "spl_used": ["search index=botsv3 sourcetype=aws:cloudwatchlogs | stats count",
                         "search index=botsv3 sourcetype=lastlog | head 5"],
            "sourcetypes": ["aws:cloudwatchlogs", "lastlog"],
            "worker": "senior#7", "subquestion": "Find the Tomcat password"}


def test_digest_names_sourcetypes_spl_and_trail():
    d = build_handoff_digest(_rec())
    assert "aws:cloudwatchlogs" in d
    assert "sourcetype=lastlog" in d
    assert "do NOT repeat" in d
    assert "ran out of iterations" in d


def test_digest_is_bounded():
    rec = _rec()
    rec["answer"] = "x" * 10000
    rec["spl_used"] = [f"search very long query number {i} " + "y" * 300
                      for i in range(40)]
    assert len(build_handoff_digest(rec)) <= 1500


def test_digest_labels_cap_hit():
    d = build_handoff_digest(_rec(status="solved", cap_hit=True))
    assert "cap-hit" in d.lower()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_handoff.py -v`
Expected: FAIL — no `build_handoff_digest`.

- [ ] **Step 3: Implement digest + context plumbing**

In `agent/v1/orchestrator.py`, add module-level (near `substitute_deps`):

```python
HANDOFF_MAX_CHARS = 1500
HANDOFF_KEEP      = 3      # most recent digests injected per question


def build_handoff_digest(record: dict) -> str:
    """Structured handoff for the worker that replaces a failed/too_big/cap-hit
    delegation: what was tried, what to not repeat, where the trail went cold.
    run_1.2 burned $26.53 on replacement workers re-running discovery from zero.
    """
    label = record.get("status", "?")
    if record.get("cap_hit"):
        label += ", cap-hit"
    lines = [f"PRIOR ATTEMPT ({label}, {record.get('iterations', 0)} iterations) "
             f"by {record.get('worker', '?')}:"]
    sts = record.get("sourcetypes") or []
    if sts:
        lines.append(f"- sourcetypes already examined: {', '.join(sts)}")
    spl = record.get("spl_used") or []
    if spl:
        lines.append("- SPL already run (do NOT repeat these; go one step further):")
        lines += [f"    {q[:200]}" for q in spl[-6:]]
    tail = (record.get("answer") or "").strip()
    if tail:
        lines.append(f"- where the trail went cold: {tail[-400:]}")
    out = "\n".join(lines)
    # ponytail: char truncation, not token-aware; upgrade if digests start clipping SPL
    return out[:HANDOFF_MAX_CHARS]
```

In `DelegationContext.__init__` add `self.q_handoffs = []`; in `reset_question` add `self.q_handoffs = []`.

- [ ] **Step 4: Emit on failure, inject on dispatch and replan**

In `executor_node`, replace the existing block

```python
                    if result["status"] in ("too_big", "failed"):
                        ctx.failed_delegations += 1
```

with (increment semantics identical — cap-hit alone does not count as failed):

```python
                    if (result["status"] in ("too_big", "failed")
                            or result.get("cap_hit")):
                        if result["status"] in ("too_big", "failed"):
                            ctx.failed_delegations += 1
                        ctx.q_handoffs.append(build_handoff_digest(
                            {**result, "worker": f"senior#{worker_idx}"}))
```

In `executor_node`, where the subquestion is prepared (line ~360, `subq = substitute_deps(...)`), append handoffs for replacement rounds:

```python
                    subq = substitute_deps(t.subquestion, completed)
                    if ctx.q_handoffs:
                        subq += ("\n\nCONTEXT FROM PRIOR ATTEMPTS ON THIS QUESTION "
                                 "(resume the hunt, do not restart it):\n"
                                 + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]))
```

In `joiner_node`, so a REPLAN decision is informed, build:

```python
        handoff_block = ""
        if ctx.q_handoffs:
            handoff_block = ("=== Failed-Attempt Digests ===\n"
                             + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]) + "\n\n")
```

and include `handoff_block` in `joiner_msg_text` between the ledger block and the closing instruction.

- [ ] **Step 5: Full suite**

Run: `python -m pytest agent/v1/tests/ -q` — all green.

- [ ] **Step 6: Micro-smoke — the cap-out-then-replan class**

Run: `python agent/v1/run_all_v1.py --ids Q303`
Expected: completes. In the log, if any delegation fails/caps: report whether the next round's worker subquestion contained "CONTEXT FROM PRIOR ATTEMPTS" and whether its SPL avoided repeating the digest's queries. (Correctness on Q303 not required — the handoff appearing and changing worker behavior is the signal.)

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Plan B Task 3: failure handoff — failed/too_big/cap-hit delegations emit a bounded digest (sourcetypes, SPL-do-not-repeat, trail tail) injected into replacement-worker subquestions and the joiner's replan context."

```bash
git add agent/v1/orchestrator.py agent/v1/tests/test_handoff.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): failure handoff — replacement workers resume, not restart"
```

---

## Task 4: CaseFile store + planner digest + CASE UPDATES

**Files:**
- Modify: `agent/v1/case_file.py` (add the `CaseFile` class + `parse_case_updates`)
- Modify: `agent/v1/orchestrator.py`, `agent/v1/run_all_v1.py`
- Create: `agent/v1/tests/test_case_file.py`, `agent/v1/tests/test_case_integration.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `CaseFile(path)` with `.add_entity(etype, value, *, qid="")`, `.add_finding(claim, *, evidence="", source_qid="", status="hypothesis", confidence=0.5) -> int`, `.get_finding(fid) -> dict`, `.iter_findings() -> list`, `.set_status(fid, status)`, `.render_digest(*, max_chars=4000) -> str`; `parse_case_updates(text) -> list[dict]`; `apply_case_updates(case_file, joiner_text, *, source_qid) -> int` in orchestrator; `DelegationContext(pool, logger, case_file=None, use_case_file=True)`.

**Context:** cross-question memory today is the SH's chat thread, windowed to `MAX_HISTORY_MSGS=24` (~3–5 questions visible) — older findings silently fall out, and wrong verdicts propagate untagged (v1.1: Q210→Q216 cascade). The case file is a compact, confidence-tagged store injected into the planner; carried-forward claims arrive as `hypothesis` until the Verifier promotes them (Task 8).

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_case_file.py`:

```python
from case_file import CaseFile, parse_case_updates


def test_add_and_render_entity_and_finding(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    cf.add_entity("host", "BSTOLL-L.froth.ly", qid="Q210")
    cf.add_finding("BSTOLL-L mined Monero", evidence="cisco:asa flow",
                   source_qid="Q210", status="hypothesis", confidence=0.6)
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d
    assert "[?]" in d          # hypothesis marker


def test_finding_status_promote_and_refute(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    fid = cf.add_finding("miner is FYODOR-L", evidence="tcp connect",
                         source_qid="Q210", status="hypothesis", confidence=0.5)
    cf.set_status(fid, "refuted")
    assert cf.get_finding(fid)["status"] == "refuted"
    assert "[X]" in cf.render_digest()


def test_persist_and_reload(tmp_path):
    p = str(tmp_path / "case.json")
    CaseFile(p).add_entity("user", "mkraeusen", qid="Q330")
    assert "mkraeusen" in CaseFile(p).render_digest()


def test_digest_is_bounded(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    for i in range(500):
        cf.add_finding(f"finding number {i} with some text", evidence="x",
                       source_qid=f"Q{i}", status="verified", confidence=0.9)
    assert len(cf.render_digest(max_chars=4000)) <= 4000


def test_parse_case_updates_block():
    text = '''FINAL ANSWER: BSTOLL-L
CASE UPDATES:
- entity host BSTOLL-L.froth.ly
- finding [verified] BSTOLL-L is the Monero miner | evidence: cisco:asa message_id 113019
'''
    updates = parse_case_updates(text)
    assert any(u["kind"] == "entity" and "BSTOLL-L" in u["value"] for u in updates)
    assert any(u["kind"] == "finding" and u["status"] == "verified" for u in updates)


def test_parse_case_updates_absent_returns_empty():
    assert parse_case_updates("FINAL ANSWER: x\n(no updates)") == []
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_case_file.py -v`
Expected: FAIL — no `CaseFile` in `case_file`.

- [ ] **Step 3: Add `CaseFile` + parser to `case_file.py`**

Append to `agent/v1/case_file.py`:

```python
import json
import os
import threading

_STATUSES    = ("verified", "hypothesis", "refuted")
_STATUS_MARK = {"verified": "[OK]", "hypothesis": "[?]", "refuted": "[X]"}


class CaseFile:
    """Cross-question incident store: entities + confidence-tagged findings.
    JSON-backed so it survives process resume (same run_dir, like metrics.json).
    Thread-locked: parallel Senior threads report via the joiner (main thread)
    today, but the lock makes direct worker writes safe if that changes."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._data = {"entities": [], "findings": []}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def add_entity(self, etype: str, value: str, *, qid: str = "") -> None:
        with self._lock:
            if not any(e["value"].lower() == value.lower()
                       for e in self._data["entities"]):
                self._data["entities"].append(
                    {"type": etype, "value": value, "qid": qid})
                self._save()

    def add_finding(self, claim: str, *, evidence: str = "", source_qid: str = "",
                    status: str = "hypothesis", confidence: float = 0.5) -> int:
        if status not in _STATUSES:
            status = "hypothesis"
        with self._lock:
            fid = len(self._data["findings"])
            self._data["findings"].append({
                "id": fid, "claim": claim, "evidence": evidence,
                "source_qid": source_qid, "status": status,
                "confidence": confidence,
            })
            self._save()
            return fid

    def get_finding(self, fid: int) -> dict:
        return self._data["findings"][fid]

    def iter_findings(self):
        return list(self._data["findings"])

    def set_status(self, fid: int, status: str) -> None:
        if status not in _STATUSES:
            return
        with self._lock:
            self._data["findings"][fid]["status"] = status
            self._save()

    def render_digest(self, *, max_chars: int = 4000) -> str:
        """Planner-facing view: verified first, hypotheses next, refuted last
        with a warning marker so the planner distrusts them."""
        ents = self._data["entities"]
        ent_line = ("ENTITIES: " + ", ".join(f"{e['type']}={e['value']}"
                                             for e in ents)) if ents else ""
        order = {"verified": 0, "hypothesis": 1, "refuted": 2}
        finds = sorted(self._data["findings"],
                       key=lambda f: order.get(f["status"], 3))
        lines = [ent_line, "", "FINDINGS:"]
        for f in finds:
            lines.append(f"  {_STATUS_MARK.get(f['status'], '[?]')} "
                         f"{f['claim']} (src {f['source_qid']}"
                         f"{'; ' + f['evidence'] if f['evidence'] else ''})")
        out = "\n".join(lines)
        if len(out) > max_chars:
            out = out[:max_chars - 24].rstrip() + "\n  ...[digest truncated]"
        return out


def parse_case_updates(text: str) -> list[dict]:
    """Parse a `CASE UPDATES:` block. Grammar (one per line under the header):
      - entity <type> <value>
      - finding [<status>] <claim> | evidence: <evidence>
    """
    m = re.search(r'CASE UPDATES:\s*(.+)$', text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    updates = []
    for raw in m.group(1).splitlines():
        line = raw.strip().lstrip("-").strip()
        if not line:
            continue
        em = re.match(r'entity\s+(\S+)\s+(.+)$', line, re.IGNORECASE)
        if em:
            updates.append({"kind": "entity", "etype": em.group(1),
                            "value": em.group(2).strip()})
            continue
        fm = re.match(r'finding\s+\[(\w+)\]\s+(.+)$', line, re.IGNORECASE)
        if fm:
            claim, evidence = fm.group(2).strip(), ""
            if "|" in claim:
                claim, _, tail = claim.partition("|")
                claim = claim.strip()
                evidence = re.sub(r'^\s*evidence:\s*', '', tail.strip(),
                                  flags=re.IGNORECASE)
            updates.append({"kind": "finding", "status": fm.group(1).lower(),
                            "claim": claim, "evidence": evidence})
    return updates
```

Run: `python -m pytest agent/v1/tests/test_case_file.py -v` — 6 passed.

- [ ] **Step 4: Integration — `apply_case_updates`, planner digest, context, runner**

Create `agent/v1/tests/test_case_integration.py`:

```python
from case_file import CaseFile
from orchestrator import apply_case_updates


def test_apply_case_updates_writes_entities_and_findings(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    joiner_text = ("FINAL ANSWER: BSTOLL-L\n"
                   "CASE UPDATES:\n"
                   "- entity host BSTOLL-L.froth.ly\n"
                   "- finding [verified] BSTOLL-L is the miner | evidence: cisco:asa")
    n = apply_case_updates(cf, joiner_text, source_qid="Q210")
    assert n == 2
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d and "miner" in d


def test_apply_case_updates_noop_when_absent(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    assert apply_case_updates(cf, "FINAL ANSWER: x", source_qid="Q1") == 0
```

Run it, verify FAIL (no `apply_case_updates`). Then in `agent/v1/orchestrator.py`:

1. Extend the Task-2 import line: `from case_file import build_ledger, render_ledger, snap_to_ledger, CaseFile, parse_case_updates`.

2. Add module-level:

```python
def apply_case_updates(case_file, joiner_text: str, *, source_qid: str) -> int:
    """Parse a CASE UPDATES block and write it into the case file. Returns count."""
    n = 0
    for u in parse_case_updates(joiner_text):
        if u["kind"] == "entity":
            case_file.add_entity(u["etype"], u["value"], qid=source_qid)
            n += 1
        elif u["kind"] == "finding":
            case_file.add_finding(u["claim"], evidence=u.get("evidence", ""),
                                  source_qid=source_qid, status=u["status"])
            n += 1
    return n
```

3. `DelegationContext.__init__(self, pool, logger, case_file=None, use_case_file=True)` — store both; leave `reset_question` unchanged (the case file is cross-question by design).

4. In `joiner_node`'s FINAL ANSWER branch, in the `action == "final"` path right before the `return` (line ~478), add:

```python
            if ctx.case_file and ctx.use_case_file:
                apply_case_updates(ctx.case_file, jtext, source_qid=ctx.current_qid)
```

5. In `planner_node`, replace `msgs = [sys_planner] + _window(state["messages"])` with:

```python
        extra = []
        if ctx.case_file and ctx.use_case_file:
            digest = ctx.case_file.render_digest()
            if digest.strip():
                extra = [SystemMessage(content=(
                    "CASE FILE (known incident state — verified [OK], "
                    "hypothesis [?], refuted [X]; re-verify [?]/[X] findings "
                    "before relying on them):\n" + digest))]
        msgs = [sys_planner] + extra + _window(state["messages"])
```

6. Append to `PLANNER_SYSTEM_PROMPT`: "A CASE FILE block may precede this conversation — treat `[?]`/`[X]` findings as unproven; re-verify before building a plan on them." Append to `JOINER_SYSTEM_PROMPT`:

```
CASE UPDATES — after your FINAL ANSWER line, record durable incident facts:
CASE UPDATES:
- entity <host|user|ip|domain|file|hash|bucket|cve> <value>
- finding [verified|hypothesis] <one-sentence claim> | evidence: <sourcetype/SPL fragment>
Only include facts a future question could reuse. Mark [verified] only if a
worker proved it with a query this round.
```

7. In `agent/v1/run_all_v1.py`, after `logger = RunLogger(...)` (line ~243):

```python
    case_file = CaseFile(os.path.join(logger.run_dir, "case_file.json"))
```

with `from case_file import CaseFile, build_ledger` at the top, and change `ctx = DelegationContext(pool, logger)` → `ctx = DelegationContext(pool, logger, case_file=case_file)`.

- [ ] **Step 5: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import orchestrator; print('ok')"`

- [ ] **Step 6: Micro-smoke — the cascade pair**

Run: `python agent/v1/run_all_v1.py --ids Q210,Q216`
Expected: `log/temp/<ts>/case_file.json` exists with entities/findings after Q210; report whether Q216's planner context contained the CASE FILE block and with which status markers.

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Plan B Task 4: CaseFile store (entities + confidence-tagged findings, bounded digest) injected into planner; joiner emits CASE UPDATES; persisted at `<run_dir>/case_file.json`."

```bash
git add agent/v1/case_file.py agent/v1/orchestrator.py agent/v1/run_all_v1.py agent/v1/tests/test_case_file.py agent/v1/tests/test_case_integration.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): case-file digest in planner + CASE UPDATES from joiner"
```

---

## Task 5: Specialist workers (HUNTER / CONTENT / METRICS)

**Files:**
- Create: `agent/v1/specialists.py`
- Modify: `agent/v1/splunk_subagent.py`, `agent/v1/orchestrator.py`
- Create: `agent/v1/tests/test_specialists.py`

**Interfaces:**
- Consumes: `agent_mod.create_agent(...)` (existing), `ESCALATE_INSTRUCTIONS`, `web_lookup`, `iter_budget`/`MAX_ITER`/`HIGH_VALUE_THRESHOLD`.
- Produces: `SPECIALISTS: dict[str, str]`, `parse_specialist_tag(subquestion: str) -> str`; `SplunkWorkerPool.run_senior` selects the specialist graph from the task tag.

**Context (run_1.2 evidence, one row per specialist):**

| Specialist | Config delta | run_1.2 evidence |
|---|---|---|
| **Hunter** (default) | scope-first rule: enumerate ALL hosts/users with `stats by` before filtering | Q208 (`chrome#5` never found — searched one host), Q211 (1 of 6 mining destinations), Q330 (3 VPN users ranked, `mkraeusen` never enumerated) — 1,200 pts |
| **Content-Inspector** | drill to raw events FIRST, map sourcetypes second (`get_raw_events` is already a first-class tool from Plan A) | Q303 (password `ilovedavidverve` in cloud-init raw events; workers ID'd the sourcetype then capped), Q315, Q321, Q322, Q328 — 2,600 pts |
| **Metrics-Analyst** | SPL-native stats (`perc25/perc75`, `eval`) mandatory; show formula + inputs; obey "using Splunk commands only" literally | Q206 (2.9348 mis-rounded), Q216 (duration eval chain never completed), Q224 (avg over wrong set), Q331 (manual Tukey beat the SPL `perc` worker) — 2,600 pts |

**Deliberate deviation from the 2026-07-07 plan: no `python_calc` tool.** run_1.2's Q331 loss was caused by a worker computing fences manually instead of with SPL — a calculator invites exactly that. Metrics-Analyst mandates SPL-native computation instead.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_specialists.py`:

```python
from specialists import parse_specialist_tag, SPECIALISTS


def test_parse_tag_defaults_to_hunter():
    assert parse_specialist_tag("Search dns for the C2 domain") == "hunter"


def test_parse_content_tag():
    assert parse_specialist_tag("[CONTENT] Read the phishing email body") == "content"


def test_parse_metrics_tag_case_insensitive():
    assert parse_specialist_tag("  [metrics] Average subdomain length") == "metrics"


def test_all_specialists_have_prompt_text():
    assert set(SPECIALISTS) == {"hunter", "content", "metrics"}
    for name in ("content", "metrics"):
        assert SPECIALISTS[name].strip()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_specialists.py -v`
Expected: FAIL — no `specialists` module.

- [ ] **Step 3: Implement `specialists.py`**

Create `agent/v1/specialists.py`:

```python
#!/usr/bin/env python3
"""
Specialist worker roles: same v0 graph, different prompt emphasis. The planner
tags each task [HUNTER]/[CONTENT]/[METRICS]; the pool picks the matching graph.
run_1.2 evidence per role: docs/version_architecture/v1/v1.2_improvement_plans.md (B3).
"""

import re

SPECIALISTS = {
    # Hunter is the default Senior + scope-first: Q208/Q211/Q330 all died by
    # filtering to one host/user before enumerating the population.
    "hunter": (
        "SCOPE-FIRST RULE: before filtering to any single host/user/IP, run one "
        "`stats count by <entity>` over the WHOLE population so you see every "
        "candidate. Never conclude from the first entity you inspected."
    ),
    # Q303: the password sat in cloud-init raw events; workers found the
    # sourcetype and capped out before ever reading an event.
    "content": (
        "You are a Content-Inspector. The answer is INSIDE raw event text "
        "(email bodies, scripts, cloud-init logs, bash history, HTTP payloads). "
        "Drill to raw events FIRST with get_raw_events, map sourcetypes second. "
        "Do not spend iterations on aggregations when the task is to read content."
    ),
    # Q331: a worker computed Tukey's fences by hand and beat the SPL worker's
    # correct perc25/perc75 value. Q206/Q216/Q224 are the same class.
    "metrics": (
        "You are a Metrics-Analyst. Compute EVERY number with SPL "
        "(eval, stats, perc25()/perc75(), avg()) and show the exact SPL formula "
        "and its inputs in your answer. If the question says 'using Splunk "
        "commands only', the computation MUST happen inside SPL — never do the "
        "arithmetic yourself, never round beyond what the question asks."
    ),
}


def parse_specialist_tag(subquestion: str) -> str:
    m = re.match(r'\s*\[(hunter|content|metrics)\]', subquestion or "", re.IGNORECASE)
    return m.group(1).lower() if m else "hunter"
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_specialists.py -v`
Expected: 4 passed.

- [ ] **Step 5: Build specialist graphs + select by tag**

In `agent/v1/splunk_subagent.py`:

1. Import: `from specialists import SPECIALISTS, parse_specialist_tag`.

2. In `SplunkWorkerPool.__init__`, replace the two `senior_graph`/`senior_graph_hi` builds with a dict keyed `(role, hi)` — 3 specialists × 2 budgets, built once offline (keep `verifier_graph` exactly as is):

```python
        self._graphs = {}
        for name, extra in SPECIALISTS.items():
            instructions = ESCALATE_INSTRUCTIONS + ("\n\n" + extra if extra else "")
            for hi, cap in ((False, MAX_ITER),
                            (True, iter_budget(HIGH_VALUE_THRESHOLD))):
                self._graphs[(name, hi)], _ = agent_mod.create_agent(
                    senior_api_key, splunk,
                    model=senior_model, base_url=senior_base_url,
                    extra_instructions=instructions,
                    extra_tools=[web_lookup],
                    max_iter=cap,
                )
```

3. In `run_senior`, replace the graph selection (keep the `max_iter is not None` verifier branch first, unchanged):

```python
        budget = iter_budget(points)
        role   = parse_specialist_tag(subquestion)
        graph  = self._graphs[(role, budget > MAX_ITER)]
        return self._run("senior", graph, self.senior_model,
                         subquestion, parent_qid, idx, max_iter=budget)
```

4. In `agent/v1/orchestrator.py`, append to `PLANNER_SYSTEM_PROMPT` RULES:

```
- Prefix every task with a specialist tag: [HUNTER] for entity hunts across
  hosts/users/IPs, [CONTENT] when the answer is inside raw event text (emails,
  scripts, logs to READ), [METRICS] for any computed number (averages,
  percentiles, durations, counts with arithmetic). Untagged tasks default to
  [HUNTER].
```

- [ ] **Step 6: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import splunk_subagent, specialists; print('ok')"`

- [ ] **Step 7: Micro-smoke — a metrics question**

Run: `python agent/v1/run_all_v1.py --ids Q331`
Expected: completes; report whether the planner tagged a `[METRICS]` task, whether the worker's answer shows an SPL formula (`perc25`/`perc75`), and whether the ledger captured the SPL worker's value verbatim.

- [ ] **Step 8: Changelog + commit**

v1.3.md changelog: "Plan B Task 5: specialist workers — hunter (scope-first) / content-inspector (raw-events-first) / metrics-analyst (SPL-native arithmetic, no python_calc by design); planner tags tasks, pool selects graph."

```bash
git add agent/v1/specialists.py agent/v1/splunk_subagent.py agent/v1/orchestrator.py agent/v1/tests/test_specialists.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): specialist workers (hunter/content/metrics) selected by task tag"
```

---

## Task 6: Phase-0 recon pass (`--recon`, default off)

**Files:**
- Create: `agent/v1/recon.py`
- Modify: `agent/v1/run_all_v1.py`
- Create: `agent/v1/tests/test_recon.py`

**Interfaces:**
- Consumes: `CaseFile` (Task 4), `orchestrator.MAX_WORKERS` and `orchestrator._run_senior`, `ctx.logger.next_worker`.
- Produces: `RECON_TASKS: list[str]`, `seed_case_from_recon(case_file, results) -> int`, `run_recon(ctx) -> list[dict]`.

**Context:** build the incident skeleton once before the question loop. run_1.2 re-confirmed the need: Q310 (500) chased the wave-2 `.lnk` artifact instead of the wave-1 `Frothly-Brewery-Financial-Planning-FY2019-Draft.xlsm` phishing attachment (wave confusion), Q329 (1000) answered `Beer` from the wrong uploaded file (no "which files were uploaded, by whom, what's in them" narrative). ~$0.10 at GLM pricing.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_recon.py`:

```python
from case_file import CaseFile
from recon import RECON_TASKS, seed_case_from_recon


def test_recon_task_set_nonempty():
    assert len(RECON_TASKS) >= 4
    assert all(isinstance(t, str) and t.strip() for t in RECON_TASKS)


def test_seed_writes_verified_findings_and_entities(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fake = [{"subquestion": RECON_TASKS[0], "status": "solved",
             "answer": "FINAL ANSWER: key hosts are BSTOLL-L, FYODOR-L and ABUNGST-L"}]
    n = seed_case_from_recon(cf, fake)
    assert n >= 1
    d = cf.render_digest()
    assert "[OK]" in d                      # seeded as verified baseline
    assert "BSTOLL-L" in d                  # entity regex caught the hostname


def test_seed_skips_failed_results(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    assert seed_case_from_recon(cf, [{"subquestion": "x", "status": "failed",
                                      "answer": ""}]) == 0
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_recon.py -v`
Expected: FAIL — no `recon` module.

- [ ] **Step 3: Implement `recon.py`**

Create `agent/v1/recon.py`:

```python
#!/usr/bin/env python3
"""
Phase-0 recon: build the incident skeleton once, before the question loop,
and seed the case file as verified baseline. run_1.2: Q310 chased the wrong
phishing wave, Q329 read the wrong uploaded file — both are scoping errors a
one-time incident narrative prevents.
"""

import concurrent.futures
import re

RECON_TASKS = [
    "[HUNTER] Inventory the BOTSv3 dataset: list every sourcetype in "
    "index=botsv3 with its event count and earliest/latest event time "
    "(| metadata or | tstats). Name the 10 highest-volume sourcetypes.",
    "[HUNTER] Enumerate the key Frothly endpoint hosts and their users: "
    "stats count by host over the Windows/endpoint sourcetypes; for each of "
    "the top hosts name the primary user account seen on it.",
    "[CONTENT] Map the phishing story: find every inbound email with an "
    "attachment in the email sourcetype(s); for EACH wave give the send time, "
    "sender, recipients, attachment filename and type.",
    "[HUNTER] Map external attack infrastructure: suspicious/repeated external "
    "IPs and domains in web, firewall and DNS sourcetypes (scanning, C2 "
    "beaconing, cryptomining pools), each with its role and time window.",
    "[HUNTER] Summarize the AWS/cloud story: which IAM users and access keys "
    "appear in aws:cloudtrail, which S3 buckets are touched (esp. public "
    "access/policy changes), and any EC2 activity worth noting.",
]

_HOSTLIKE = re.compile(r'\b[A-Z][A-Z0-9]+-L\b')          # BSTOLL-L, FYODOR-L, ...


def seed_case_from_recon(case_file, results: list) -> int:
    """Write usable recon answers into the case file as verified baseline.
    Returns number of findings written."""
    n = 0
    for r in results:
        answer = (r.get("answer") or "").strip()
        if not answer or r.get("status") in ("failed", "too_big"):
            continue
        case_file.add_finding(answer[:600], evidence="recon",
                              source_qid="RECON", status="verified",
                              confidence=0.8)
        n += 1
        for host in set(_HOSTLIKE.findall(answer)):
            case_file.add_entity("host", host, qid="RECON")
    return n


def run_recon(ctx) -> list[dict]:
    """Dispatch RECON_TASKS in parallel through the existing pool (mirrors
    executor_node's ThreadPoolExecutor pattern; qid label 'RECON')."""
    from orchestrator import MAX_WORKERS, _run_senior
    from langsmith.run_helpers import get_current_run_tree

    ctx.reset_question("RECON", points=0, question="Phase-0 incident recon")
    parent = get_current_run_tree()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futs = {}
        for t in RECON_TASKS:
            widx = ctx.logger.next_worker("senior", "RECON")
            futs[exe.submit(_run_senior, ctx, t, widx, parent)] = t
        for fut, t in futs.items():
            try:
                r = fut.result()
            except Exception as exc:
                r = {"status": "failed", "answer": f"recon worker crashed: {exc}"}
            r["subquestion"] = t
            results.append(r)
    return results
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_recon.py -v`
Expected: 3 passed.

- [ ] **Step 5: Wire `--recon` into the runner**

In `agent/v1/run_all_v1.py`:

1. Add the flag: `parser.add_argument("--recon", action="store_true", help="Run the Phase-0 recon pass before the question loop (seeds the case file).")`
2. After `ctx = DelegationContext(...)` and the case-file init, before the question loop:

```python
    if args.recon:
        already = any(f.get("source_qid") == "RECON"
                      for f in case_file.iter_findings())
        if already:
            print("[RECON] case file already seeded — skipping (resume).")
        else:
            from recon import run_recon, seed_case_from_recon
            print("[RECON] Phase-0 incident recon ...")
            recon_results = run_recon(ctx)
            seeded = seed_case_from_recon(case_file, recon_results)
            logger.events.emit("recon_done", findings=seeded,
                               tasks=len(recon_results))
            print(f"[RECON] seeded {seeded} verified finding(s).")
```

- [ ] **Step 6: Full suite + micro-smoke**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python agent/v1/run_all_v1.py --ids Q329 --recon`
Expected: recon runs first (report seeded count), then Q329; report whether Q329's planner CASE FILE block contained recon findings. (Slow — best effort; unit tests are the gate.)

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Plan B Task 6: Phase-0 recon (`--recon`, default off) — 5 parallel skeleton tasks seed the case file as verified baseline; resume-safe (skips if RECON findings exist)."

```bash
git add agent/v1/recon.py agent/v1/run_all_v1.py agent/v1/tests/test_recon.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): phase-0 recon pass seeds verified case-file baseline (--recon)"
```

---

## Task 7: Hint economy (`--hints`, default off)

**Files:**
- Create: `agent/v1/hint_client.py`
- Modify: `agent/v1/run_all_v1.py`
- Create: `agent/v1/tests/test_hint_client.py`

**Interfaces:**
- Consumes: `botsv3content/ctf_hints.csv` (97 hints, columns `Hint,HintCost,HintNumber,Number`), `is_grounded` (existing import in the runner), `run_sh` (existing).
- Produces: `HintBook(hints_csv)` with `.get_hint(number, hint_number) -> dict | None` (`{"number", "hint_number", "text", "cost"}`), `.count_for(number) -> int`; `hint_cost` recorded in the results record + metrics row and deducted from `pts_earned`.

**Context:** 97 official hints unused after three full runs. Hint cost 10–25 pts vs 100–1000-pt questions; a wrong answer scores 0, a hint-assisted correct one scores 75–990. run_1.2's honest-refusal questions (Q328: no evidence after 5 delegations; Q303 refusal) are exactly the profile where a hint converts a 0 into 475–990. Policy: ungrounded answer AND ≥500 pts → buy hint 1 (one hint max per question), one extra `run_sh` pass with the hint embedded, deduct cost honestly.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_hint_client.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_hint_client.py -v`
Expected: FAIL — no `hint_client`.

- [ ] **Step 3: Implement `hint_client.py`**

Create `agent/v1/hint_client.py`:

```python
#!/usr/bin/env python3
"""
Official BOTSv3 hint book. A hint costs HintCost points; a hint-assisted
correct answer scores base - cost (75-990) — strictly better than a wrong 0.
97 hints sat unused through runs 1.0-1.2.
"""

from __future__ import annotations

import csv
from collections import defaultdict


class HintBook:
    def __init__(self, hints_csv: str) -> None:
        self._by_q: dict[int, list[dict]] = defaultdict(list)
        with open(hints_csv, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    num  = int(row["Number"])
                    hnum = int(row["HintNumber"])
                    cost = int(row["HintCost"])
                except (ValueError, KeyError, TypeError):
                    continue
                self._by_q[num].append(
                    {"number": num, "hint_number": hnum,
                     "text": (row.get("Hint") or "").strip(), "cost": cost})
        for lst in self._by_q.values():
            lst.sort(key=lambda h: h["hint_number"])

    def get_hint(self, number: int, hint_number: int) -> dict | None:
        for h in self._by_q.get(number, []):
            if h["hint_number"] == hint_number:
                return h
        return None

    def count_for(self, number: int) -> int:
        return len(self._by_q.get(number, []))
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_hint_client.py -v`
Expected: 3 passed.

- [ ] **Step 5: Hint policy in the runner**

In `agent/v1/run_all_v1.py`:

1. Flag: `parser.add_argument("--hints", action="store_true", help="Buy official hint 1 on ungrounded >=500pt answers (cost deducted from earned points).")`
2. Import `from hint_client import HintBook` at the top; init after the scoreboard: `hint_book = HintBook(os.path.join(PROJECT_ROOT, "botsv3content", "ctf_hints.csv")) if args.hints else None`.
3. Between the extractor and the scoreboard submit (after `print(f"[EXTRACTOR] clean={clean!r}")`):

```python
        hint_cost = 0
        if hint_book and points >= 500:
            tr = {i: {"answer": d.get("answer")} for i, d in enumerate(ctx.q_delegations)}
            if not is_grounded(clean, tr, qtext):
                hint = hint_book.get_hint(q_number, 1)
                if hint:
                    hint_cost = hint["cost"]
                    print(f"[HINT] buying hint 1 for {qid} (cost {hint_cost}): {hint['text']!r}")
                    logger.events.emit("hint_bought", qid=qid, cost=hint_cost)
                    with logger.events.timer() as t_hint:
                        sh_answer, _ = run_sh(
                            sh_graph,
                            (f"OFFICIAL HINT for {qid} (cost {hint_cost} pts, already "
                             f"paid): {hint['text']}\nRe-investigate with this hint "
                             f"and give a corrected FINAL ANSWER."),
                            run_thread, qid=qid, run_name=f"SH-{qid}-hint",
                            tracker=tracker)
                    stage_ms["hint"] = t_hint.ms
                    try:
                        clean = extractor.extract(qtext, guidance, sh_answer,
                                                  qid=qid, expected_shape=guidance)
                    except Exception:
                        clean = extractor_fallback_answer(sh_answer, ctx.q_delegations)
                    print(f"[HINT] post-hint clean={clean!r}")
```

4. Deduct honestly: inside the submit `try`, after `pts_earned = sb.earned`, add `pts_earned = max(0, pts_earned - hint_cost)` **before** `earned_pts += pts_earned`. Add `"hint_cost": hint_cost,` to the results dict, add a `hint_cost=0` keyword to `build_metrics_row`'s signature, include it in the returned row, and pass `hint_cost=hint_cost` at the call site.

- [ ] **Step 6: Full suite + micro-smoke**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python agent/v1/run_all_v1.py --ids Q328 --hints`
Expected: if the answer comes back ungrounded/refused, a `hint_bought` event fires and the cost deduction lands; report bought-or-not, cost, and net earned.

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Plan B Task 7: hint economy (`--hints`, default off) — ungrounded ≥500pt answer buys official hint 1, one re-plan pass, cost deducted from earned points and recorded in metrics."

```bash
git add agent/v1/hint_client.py agent/v1/run_all_v1.py agent/v1/tests/test_hint_client.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): hint economy — buy hint 1 on ungrounded >=500pt answers (--hints)"
```

---

## Task 8: Verifier promotes/refutes case-file findings

**Files:**
- Modify: `agent/v1/orchestrator.py` (`promote_from_verdict` + call in `verifier_node`)
- Create: `agent/v1/tests/test_verifier_promotes.py`

**Interfaces:**
- Consumes: `CaseFile.iter_findings()` / `.set_status()` (Task 4), `parse_verifier_verdict` output (`{"verdict": "confirmed"|"refuted", "correction": str}`).
- Produces: `promote_from_verdict(case_file, answer: str, verdict: dict) -> None`.

**Context:** closes the cascade loop — when the Verifier (now on its dedicated `verifier_graph`, cap actually enforced since v1.3 Task 1) confirms/refutes a ≥500-pt answer, reflect that into the case file so later questions inherit the corrected status. Hook ONLY the success path of `verifier_node` — the `verifier_failed` paths (crash, failed/too_big/cap-hit) must not touch the case file.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_verifier_promotes.py`:

```python
from case_file import CaseFile
from orchestrator import promote_from_verdict


def test_confirmed_promotes_to_verified(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("BSTOLL-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "BSTOLL-L", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "verified"


def test_refuted_marks_refuted(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("FYODOR-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "FYODOR-L",
                         {"verdict": "refuted", "correction": "BSTOLL-L"})
    assert cf.get_finding(fid)["status"] == "refuted"


def test_empty_answer_is_noop(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("something", source_qid="Q1", status="hypothesis")
    promote_from_verdict(cf, "", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "hypothesis"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_verifier_promotes.py -v`
Expected: FAIL — no `promote_from_verdict`.

- [ ] **Step 3: Implement + wire**

Add to `agent/v1/orchestrator.py` (module level):

```python
def promote_from_verdict(case_file, answer: str, verdict: dict) -> None:
    """Reflect a Verifier verdict into the case file: findings whose claim
    contains the checked answer flip to verified/refuted accordingly."""
    a = (answer or "").strip().lower()
    if not a:
        return
    for f in case_file.iter_findings():
        if a in f["claim"].lower():
            if verdict["verdict"] == "confirmed":
                case_file.set_status(f["id"], "verified")
            elif verdict["verdict"] == "refuted":
                case_file.set_status(f["id"], "refuted")
```

In `verifier_node`, right after `verdict = parse_verifier_verdict(result.get("answer", ""))` (line ~559 — i.e. on the success path only, after both `verifier_failed` early returns):

```python
        if ctx.case_file and ctx.use_case_file:
            promote_from_verdict(ctx.case_file, answer, verdict)
```

- [ ] **Step 4: Run tests, verify they pass; full suite**

Run: `python -m pytest agent/v1/tests/test_verifier_promotes.py -v` — 3 passed.
Run: `python -m pytest agent/v1/tests/ -q` — all green.

- [ ] **Step 5: Changelog + commit**

v1.3.md changelog: "Plan B Task 8: Verifier promotes/refutes case-file findings on its success path (verifier_failed paths untouched) — closes the Q210→Q216 cascade loop."

```bash
git add agent/v1/orchestrator.py agent/v1/tests/test_verifier_promotes.py docs/version_architecture/v1/v1.3.md
git commit -m "feat(v1.3-planB): verifier promotes/refutes case-file findings"
```

---

## Task 9: Combined 5-question smoke (gate before the full run)

**Files:** none created — this is the integration gate.

- [ ] **Step 1: Full unit suite**

Run: `python -m pytest agent/v1/tests/ -q`
Expected: 77 baseline + all Plan-B tests, zero failures.

- [ ] **Step 2: The 5-question smoke**

Run: `python agent/v1/run_all_v1.py --ids Q216,Q303,Q329,Q330,Q331 --recon --hints`

Report, per feature (correctness is a bonus, mechanism-firing is the gate):

| Question | Feature under test | Signal to report |
|---|---|---|
| Q216 (1000) | case file + cascade | planner CASE FILE block present; findings arrive tagged `[?]`/`[OK]`/`[X]` |
| Q303 (100) | content-inspector + failure handoff | `[CONTENT]` tag; on any cap-hit, next worker's subquestion contains "CONTEXT FROM PRIOR ATTEMPTS" |
| Q329 (1000) | recon | recon seeded findings; Q329's plan references the uploaded-files narrative |
| Q330 (1000) | hunter scope-first | worker ran an unfiltered `stats ... by <user>` enumeration before filtering |
| Q331 (1000) | metrics + ledger | `[METRICS]` tag; SPL `perc` formula shown; submitted value byte-identical to a ledger entry |

Also report from the run summary: `failed_delegations`, per-role token usage, and whether any handoff digests fired.

- [ ] **Step 3: Hand off to the human**

Per CLAUDE.md: the human triggers the full 56-Q run and provides the dollar cost afterward. On full-run completion: fold the v1.3.md changelog into a "What changed vs v1.2" section, write `docs/scoreboard_result/v1/v1.3.md` (including wrong questions), compare against run_1.2 with `compare.py` — success = `failed_delegations` near 0, Senior input tokens < 14M (−50%), cost < ~$5, score ≥ 26/56 with the 5,100-pt selection block now auditable in `candidate_ledger` for Plan C.

---

## Done criteria

- All tasks committed with per-task changelog lines in `docs/version_architecture/v1/v1.3.md`.
- `python -m pytest agent/v1/tests/ -q` fully green.
- Ledger + handoff + case file default ON; `--recon`/`--hints` opt-in; no scoring-path change except the explicit hint-cost deduction.
- `candidate_ledger` present in every `questions/<qid>.json` — Plan C's adjudicator input exists.
- Whole-implementation review focus: (a) joiner/planner context stays bounded (ledger block + handoff digests + case digest are all char-capped); (b) case-file thread safety; (c) recon/hints resume-safe; (d) snap never substitutes a different value — only restores byte form.
- The human runs the full 56-Q run; Plan B is declared a win on cost + auditability metrics, not score alone (selection recovery is Plan C's claim).
