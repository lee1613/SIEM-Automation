# Plan C — Evidence-Ranked Adjudication + Dual-Track + Escalation: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the joiner's fluency-driven candidate selection with a rule-based adjudicator over the Plan B candidate ledger, add dual-track planning + gpt-5.4 escalation for 1000-pt questions, and 3× self-consistency sampling for metrics questions — attacking run_0.2's 5,100-pt SELECTION losses and the 7,000-pt 1000-pt residue.

**Architecture:** A new `adjudicator` LangGraph node sits between the joiner and the verifier in `build_sh_agent_compiler`. It ranks the candidate ledger (Plan B's verbatim per-delegation values) by explicit rules — constraint compliance, byte-exact fidelity, cardinality/shape, evidence strength — with a deterministic post-guard so it can never emit a value outside the ledger or question text. It may dispatch ONE bounded follow-up worker (a targeted tiebreak query; escalated to a gpt-5.4 Senior on ≥1000-pt questions) and re-adjudicate once. Dual-track is a planner-prompt instruction on ≥1000-pt questions (the executor already runs independent tasks in parallel). Self-consistency runs `[METRICS]` tasks 3× at temperature 0.3 on ≥500-pt questions and majority-votes the extracted value. The verifier is untouched — per the spec its only remaining job (confirm/refute the single chosen answer) is exactly what it already does since the v0.3 Task 1 dedicated-graph fix.

**Tech Stack:** Python 3.12, LangGraph, LangChain `ChatOpenAI`, pytest. Models: SH + adjudicator + escalation = `gpt-5.4` (OpenAI), Senior = `gpt-5.4-mini` (OpenAI), Extractor = `meta/llama-3.3-70b-instruct` (NIM).

**Spec:** `docs/version_architecture/v0/v0.2_improvement_plans.md` § "Plan C — Evidence-Ranked Adjudication + Dual-Track + Escalation" (lines 185–240).

## Global Constraints

- **Python invocation is `python3` / `python -m pytest` from the project root** (`/Users/june/Desktop/Project/SIEM-Automation`); test suite lives at `agent/v0/tests/` (its `conftest.py` handles sys.path).
- **NO full 56-question runs.** Verification runs are smoke tests only: `python agent/v0/run_all_v0.py --ids <ids>` (≤5 questions, output to `log/temp/`, not versioned, not cost-tracked). Escalating to a full run requires explicit user go-ahead.
- **Every code change gets a same-turn changelog entry** in `docs/version_architecture/v0/v0.3.md` under a `## Plan C Tasks` section (v0.3 is still the in-progress version — no full run has closed it; same precedent as the `## Plan B Tasks` section).
- **Never add `Co-Authored-By: Claude` to commits.**
- Commit scope prefix: `feat(v0.3-planC):` / `fix(v0.3-planC):` / `test(v0.3-planC):`.
- Model ids exactly as spelled: `gpt-5.4`, `gpt-5.4-mini` (both already priced in `usage_tracker.PRICES_PER_1M`).
- Hard rule inherited from run_0.2's Q321 (spec item 1): the pipeline must **never submit a synthesized value** — every adjudicator output is deterministically validated against the ledger / question text before it can replace the answer.
- Existing baseline: `python -m pytest agent/v0/tests/ -q` → **125 passed**. Every task ends with the full suite green.

---

### Task 1: Adjudicator module — prompt, parser, deterministic choice guard

**Files:**
- Create: `agent/v0/adjudicator.py`
- Test: `agent/v0/tests/test_adjudicator.py`
- Modify: `docs/version_architecture/v0/v0.3.md` (add `## Plan C Tasks` section + entry)

**Interfaces:**
- Consumes: `case_file.build_ledger(delegations) -> list[dict]` — each entry `{"value": str, "status": str, "worker": str, "spl": list, "evidence": str}` (already exists).
- Produces (later tasks rely on these exact names):
  - `ADJUDICATOR_SYSTEM_PROMPT: str`
  - `parse_adjudication(text: str) -> dict` — `{"choice": str, "confidence": "high"|"medium"|"low", "tiebreak": str}`; `choice`/`tiebreak` are `""` when absent or `UNKNOWN`.
  - `resolve_choice(choice: str, ledger: list, question_text: str = "") -> str | None` — verbatim ledger form on case-insensitive match, the choice itself if it appears in the question text, else `None`.
  - `fallback_choice(ledger: list) -> str | None` — best honest candidate by status rank (`solved` > `partial` > `too_big` > `failed`).
  - `render_adjudication_input(question: str, guidance: str, ledger: list) -> str`
  - `adjudicate_once(invoke, question: str, guidance: str, ledger: list) -> dict` — `invoke: Callable[[str], str]` (injectable for tests); returns `{"answer": str|None, "confidence": str, "tiebreak": str, "raw": str}`.

- [ ] **Step 1: Write the failing tests**

Create `agent/v0/tests/test_adjudicator.py`:

```python
from adjudicator import (parse_adjudication, resolve_choice, fallback_choice,
                         render_adjudication_input, adjudicate_once)

LEDGER = [
    {"value": "1367.875", "status": "solved",  "worker": "senior#2",
     "spl": ["| stats perc25(x) perc75(x)"], "evidence": "FINAL ANSWER: 1367.875"},
    {"value": "1499.25",  "status": "partial", "worker": "senior#4",
     "spl": [], "evidence": "PARTIAL ANSWER: 1499.25 (manual Tukey fences)"},
]


def test_parse_full_block():
    out = parse_adjudication(
        "CHOICE: 1367.875\nCONFIDENCE: HIGH\nREASON: SPL-native perc75\n"
        "TIEBREAK: re-run perc75 with exact filter")
    assert out == {"choice": "1367.875", "confidence": "high",
                   "tiebreak": "re-run perc75 with exact filter"}


def test_parse_unknown_choice_is_empty():
    out = parse_adjudication("CHOICE: UNKNOWN\nCONFIDENCE: LOW")
    assert out["choice"] == "" and out["confidence"] == "low"


def test_parse_garbage_defaults():
    out = parse_adjudication("I think the answer is probably 42.")
    assert out == {"choice": "", "confidence": "low", "tiebreak": ""}


def test_resolve_choice_snaps_to_verbatim_ledger_form():
    assert resolve_choice("1367.875", LEDGER) == "1367.875"
    assert resolve_choice("  1499.25 ", LEDGER) == "1499.25"


def test_resolve_choice_case_insensitive_returns_ledger_casing():
    ledger = [{"value": "nullweb_admin", "status": "solved", "worker": "s#1",
               "spl": [], "evidence": ""}]
    assert resolve_choice("NULLWEB_ADMIN", ledger) == "nullweb_admin"


def test_resolve_choice_accepts_question_text_value():
    assert resolve_choice("Frothly", LEDGER, "Which host at Frothly?") == "Frothly"


def test_resolve_choice_rejects_synthesized_value():
    assert resolve_choice("2085", LEDGER, "what is the fence?") is None
    assert resolve_choice("", LEDGER) is None


def test_fallback_choice_prefers_solved_over_partial():
    assert fallback_choice(LEDGER) == "1367.875"
    assert fallback_choice([]) is None


def test_render_input_contains_values_and_constraints():
    r = render_adjudication_input("Using Splunk commands only, find the fence.",
                                  "number only", LEDGER)
    assert "1367.875" in r and "1499.25" in r
    assert "Using Splunk commands only" in r and "number only" in r
    assert "perc25" in r          # SPL method visible to rule (a)
    assert "partial" in r         # status visible to rule (d)


def test_adjudicate_once_resolves_choice():
    def fake_invoke(prompt):
        return "CHOICE: 1367.875\nCONFIDENCE: HIGH\nREASON: SPL-native"
    v = adjudicate_once(fake_invoke, "q?", "", LEDGER)
    assert v["answer"] == "1367.875" and v["confidence"] == "high"


def test_adjudicate_once_synthesized_choice_yields_none():
    def fake_invoke(prompt):
        return "CHOICE: 9999\nCONFIDENCE: HIGH"
    v = adjudicate_once(fake_invoke, "q?", "", LEDGER)
    assert v["answer"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agent/v0/tests/test_adjudicator.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adjudicator'`

- [ ] **Step 3: Write the module**

Create `agent/v0/adjudicator.py`:

```python
#!/usr/bin/env python3
"""
Plan C adjudicator: evidence-ranked candidate selection over the Plan B ledger.

run_0.2 lost 5,100 pts on questions where a correct candidate existed in some
delegation and the joiner picked a different grounded-but-wrong one by
recency/fluency (Q318 Canada-over-Russia, Q331 manual-Tukey-over-SPL, Q324
T-Mobile, Q323 superset). The adjudicator ranks candidates by explicit rules;
a deterministic guard (resolve_choice) makes it impossible for the pipeline to
submit a value the adjudicator invented — Q321's `1000`-from-nowhere class.
"""

from __future__ import annotations

import re

_STATUS_RANK = {"solved": 3, "partial": 2, "too_big": 1, "failed": 0}


ADJUDICATOR_SYSTEM_PROMPT = """You are the ADJUDICATOR for a BOTSv3 security \
investigation. Splunk workers produced candidate answers to one question. Pick \
the ONE candidate that best answers it — by the explicit rules below, never by \
fluency, recency, or which worker sounded most confident.

RANKING RULES, in priority order:
(a) CONSTRAINT COMPLIANCE — the winning candidate's METHOD must satisfy the
    question's own constraints. "using Splunk commands only" -> the SPL shown
    must do the computation (perc25()/perc75()/avg()), never hand arithmetic.
    "first/earliest/last by event order" -> ordering must come from the data.
(b) FIELD-VALUE FIDELITY — prefer the candidate that is a verbatim field value
    over a re-typed, trimmed, or expanded variant (keep domain suffixes,
    prefixes, exact casing).
(c) CARDINALITY/SHAPE — match the answer guidance. "at least two short
    hostnames" -> the minimal consistent set, never a superset.
(d) EVIDENCE STRENGTH — direct measurement > inference; sustained behaviour >
    a single connection; status solved > partial > too_big/failed.

HARD RULE: your CHOICE must be one of the listed candidates copied
character-for-character (or a value that appears in the question text). If no
candidate satisfies the question, output the best honest candidate — or
UNKNOWN if none is defensible. NEVER synthesize a new value or number.

OUTPUT FORMAT — exactly these lines:
CHOICE: <one candidate value copied character-for-character, or UNKNOWN>
CONFIDENCE: HIGH|MEDIUM|LOW
REASON: <one line citing the rule(s) that decided it>
TIEBREAK: <one fully self-contained Splunk subquestion that would settle it>
The TIEBREAK line is optional — include it ONLY when two candidates genuinely
conflict and one targeted query would resolve which is right."""


def parse_adjudication(text: str) -> dict:
    """Parse the adjudicator LLM's output. Missing/garbage fields degrade to
    empty choice + low confidence so the caller falls back deterministically."""
    t = text or ""
    cm = re.search(r'CHOICE:\s*(.+)', t, re.IGNORECASE)
    choice = cm.group(1).strip().splitlines()[0].strip() if cm else ""
    if choice.upper() == "UNKNOWN":
        choice = ""
    conf_m = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', t, re.IGNORECASE)
    confidence = conf_m.group(1).lower() if conf_m else "low"
    tb_m = re.search(r'TIEBREAK:\s*(.+)', t, re.IGNORECASE)
    tiebreak = tb_m.group(1).strip().splitlines()[0].strip() if tb_m else ""
    return {"choice": choice, "confidence": confidence, "tiebreak": tiebreak}


def resolve_choice(choice: str, ledger: list, question_text: str = "") -> str | None:
    """Deterministic guard: the choice is only usable if it case-insensitively
    equals a ledger value (returned in the ledger's verbatim form) or appears
    in the question text. Anything else is a synthesized value -> None."""
    c = (choice or "").strip()
    if not c:
        return None
    cl = c.lower()
    for entry in ledger:
        if entry["value"].strip().lower() == cl:
            return entry["value"]
    if question_text and cl in question_text.lower():
        return c
    return None


def fallback_choice(ledger: list) -> str | None:
    """Best honest candidate by status rank — the Q321 hard-rule fallback."""
    best, best_rank = None, -1
    for e in ledger:
        rank = _STATUS_RANK.get(e.get("status", "failed"), 0)
        if rank > best_rank:
            best, best_rank = e["value"], rank
    return best


def render_adjudication_input(question: str, guidance: str, ledger: list) -> str:
    """Adjudicator-facing digest: question + guidance + every candidate with
    its status, worker, SPL method, and evidence excerpt. KB-scale by design."""
    lines = [f"QUESTION: {question}"]
    if guidance:
        lines.append(f"ANSWER GUIDANCE: {guidance}")
    lines.append("\nCANDIDATES:")
    for i, c in enumerate(ledger, 1):
        lines.append(f"{i}. `{c['value']}`  [status={c['status']}, {c['worker']}]")
        if c.get("spl"):
            lines.append(f"   SPL: {c['spl'][0][:200]}")
        if c.get("evidence"):
            lines.append(f"   evidence: {c['evidence'][:300]}")
    lines.append("\nApply the ranking rules and output CHOICE / CONFIDENCE / "
                 "REASON (and TIEBREAK only if one query would settle a "
                 "genuine conflict).")
    return "\n".join(lines)


def adjudicate_once(invoke, question: str, guidance: str, ledger: list) -> dict:
    """One adjudication pass. `invoke` is Callable[[str], str] so tests inject
    a fake and the orchestrator injects the real gpt-5.4 call."""
    raw = invoke(render_adjudication_input(question, guidance, ledger))
    parsed = parse_adjudication(raw)
    answer = resolve_choice(parsed["choice"], ledger, question)
    return {"answer": answer, "confidence": parsed["confidence"],
            "tiebreak": parsed["tiebreak"], "raw": raw}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_adjudicator.py -q`
Expected: 11 passed

Run: `python -m pytest agent/v0/tests/ -q`
Expected: 136 passed (125 baseline + 11 new)

- [ ] **Step 5: Changelog entry**

In `docs/version_architecture/v0/v0.3.md`, after the `## Plan B Tasks` section's final bullet list (before `## Plan B combined smoke`), add:

```markdown
## Plan C Tasks

- Plan C Task 1: `adjudicator.py` — evidence-ranked candidate selection over the
  Plan B ledger. Rules (a) constraint compliance, (b) field-value fidelity,
  (c) cardinality/shape, (d) evidence strength; deterministic `resolve_choice`
  guard means a synthesized value can never replace the answer (Q321 class).
```

- [ ] **Step 6: Commit**

```bash
git add agent/v0/adjudicator.py agent/v0/tests/test_adjudicator.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): adjudicator module — rule-ranked ledger selection with deterministic choice guard"
```

---

### Task 2: Majority vote for metrics self-consistency (C4)

**Files:**
- Modify: `agent/v0/adjudicator.py` (append function)
- Test: `agent/v0/tests/test_majority.py`
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Consumes: `case_file.extract_candidate(delegation: dict) -> dict | None` (existing) — pulls the verbatim FINAL/PARTIAL ANSWER value from a delegation record.
- Produces: `adjudicator.majority_answer(records: list) -> dict | None` — given ≥2 delegation-result dicts (same shape as `SplunkWorkerPool._run` returns: has `"answer"`, `"status"`), returns the record whose extracted value holds a strict majority (≥2 votes), best status among holders; `None` when no majority.

- [ ] **Step 1: Write the failing tests**

Create `agent/v0/tests/test_majority.py`:

```python
from adjudicator import majority_answer


def _rec(value_line, status):
    return {"answer": value_line, "status": status, "spl_used": [],
            "sourcetypes": [], "iterations": 3, "cap_hit": False}


def test_two_of_three_majority_wins():
    recs = [_rec("FINAL ANSWER: 2.94", "solved"),
            _rec("PARTIAL ANSWER: 2.94", "partial"),
            _rec("FINAL ANSWER: 2.9348", "solved")]
    win = majority_answer(recs)
    assert win is recs[0]          # 2.94 majority; solved beats partial


def test_all_distinct_returns_none():
    recs = [_rec("FINAL ANSWER: 1", "solved"),
            _rec("FINAL ANSWER: 2", "solved"),
            _rec("FINAL ANSWER: 3", "solved")]
    assert majority_answer(recs) is None


def test_votes_are_case_and_space_insensitive():
    recs = [_rec("FINAL ANSWER: BSTOLL-L", "partial"),
            _rec("FINAL ANSWER:  bstoll-l ", "solved"),
            _rec("FINAL ANSWER: FYODOR-L", "solved")]
    win = majority_answer(recs)
    assert win is recs[1]          # majority value, solved holder wins


def test_records_without_answer_tag_dont_vote():
    recs = [_rec("ESCALATE: nothing found", "too_big"),
            _rec("ESCALATE: nope", "too_big"),
            _rec("FINAL ANSWER: 42", "solved")]
    assert majority_answer(recs) is None   # 1 vote is not a majority
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agent/v0/tests/test_majority.py -q`
Expected: FAIL with `ImportError: cannot import name 'majority_answer'`

- [ ] **Step 3: Implement**

Append to `agent/v0/adjudicator.py` (and add `from case_file import extract_candidate` to the imports, below `import re`):

```python
def majority_answer(records: list) -> dict | None:
    """C4 self-consistency: metrics tasks are sampled 3x (temperature 0.3);
    the value extracted from a strict majority (>=2) of records wins. Returns
    the winning record (best status among the majority's holders) so the
    executor can use it verbatim as the task result; None when no majority —
    caller falls back to its first result. Q206's 2.9348->2.94 rounding slip
    and Q331's manual-vs-SPL method split are both caught by a 3-sample vote."""
    votes: dict[str, list] = {}
    for r in records:
        c = extract_candidate(r)
        if not c:
            continue
        votes.setdefault(c["value"].strip().lower(), []).append(r)
    if not votes:
        return None
    holders = max(votes.values(), key=len)
    if len(holders) < 2:
        return None
    return max(holders, key=lambda r: _STATUS_RANK.get(r.get("status"), 0))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_majority.py agent/v0/tests/test_adjudicator.py -q`
Expected: 15 passed

- [ ] **Step 5: Changelog entry**

Append to the `## Plan C Tasks` list in `docs/version_architecture/v0/v0.3.md`:

```markdown
- Plan C Task 2: `majority_answer` — strict-majority (>=2 of 3) vote over sampled
  metrics-task records, keyed on the extracted verbatim value; ties/no-majority
  return None so the executor keeps its first result.
```

- [ ] **Step 6: Commit**

```bash
git add agent/v0/adjudicator.py agent/v0/tests/test_majority.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): majority_answer — 3-sample self-consistency vote for metrics tasks"
```

---

### Task 3: Worker pool — temperature param, sampled metrics graphs, escalation graph (C3/C4 plumbing)

**Files:**
- Modify: `agent/splunk_agent.py:392-395` (signature) and `agent/splunk_agent.py:431` (temperature)
- Modify: `agent/v0/splunk_subagent.py` (pool init, `run_senior`, new `graph_key`)
- Test: `agent/v0/tests/test_graph_key.py`
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Produces:
  - `splunk_agent.create_agent(..., temperature: float = 0)` — new keyword, default preserves v0.0.0 behaviour exactly.
  - `splunk_subagent.SAMPLE_TEMPERATURE = 0.3`
  - `splunk_subagent.graph_key(role: str, high: bool, sample: bool) -> tuple` — pure graph-selection key; sampled graphs exist only for the metrics role.
  - `SplunkWorkerPool.__init__(..., escalation_api_key: str | None = None, escalation_model: str | None = None)` — when `escalation_model` is set, builds `self.escalation_graph` (high budget, plain ESCALATE instructions) on that model.
  - `SplunkWorkerPool.run_senior(..., sample: bool = False, escalate: bool = False)` — `sample` routes metrics tasks to the temperature-0.3 graph; `escalate` routes to the escalation graph (falls back to normal senior when no escalation graph was built).

- [ ] **Step 1: Write the failing test**

Create `agent/v0/tests/test_graph_key.py`:

```python
from splunk_subagent import graph_key


def test_sampled_key_only_for_metrics_role():
    assert graph_key("metrics", True, True) == ("metrics_sampled", True)
    assert graph_key("metrics", False, True) == ("metrics_sampled", False)


def test_sample_flag_ignored_for_other_roles():
    assert graph_key("hunter", True, True) == ("hunter", True)
    assert graph_key("content", False, True) == ("content", False)


def test_unsampled_is_identity():
    assert graph_key("metrics", False, False) == ("metrics", False)
    assert graph_key("hunter", True, False) == ("hunter", True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest agent/v0/tests/test_graph_key.py -q`
Expected: FAIL with `ImportError: cannot import name 'graph_key'`

- [ ] **Step 3: Add `temperature` to `create_agent`**

In `agent/splunk_agent.py`, change the signature (line 392):

```python
def create_agent(api_key: str, splunk: SplunkClient, *,
                 model: str = MODEL, base_url: str | None = None,
                 extra_instructions: str = "", extra_tools: list | None = None,
                 max_iter: int = MAX_ITER, temperature: float = 0):
```

and where the LLM is constructed (line 431), change `temperature=0,` to:

```python
        temperature=temperature,
```

Add one line to the docstring's Args block:

```python
        temperature:        sampling temperature (default 0 — deterministic;
                            the v0 pool passes 0.3 for self-consistency
                            sampling of metrics tasks).
```

- [ ] **Step 4: Add graphs + routing to the pool**

In `agent/v0/splunk_subagent.py`:

Below `VERIFIER_MAX_ITER = 8` add:

```python
SAMPLE_TEMPERATURE = 0.3   # C4 self-consistency sampling for metrics tasks


def graph_key(role: str, high: bool, sample: bool) -> tuple:
    """Pure graph-selection key: sampled (temperature 0.3) graphs exist only
    for the metrics role; the sample flag is a no-op for hunter/content."""
    if sample and role == "metrics":
        return ("metrics_sampled", high)
    return (role, high)
```

Change `SplunkWorkerPool.__init__` signature to:

```python
    def __init__(self, splunk, *, senior_api_key: str, senior_model: str = "gpt-5.4",
                 senior_base_url: str | None = None, tracker=None,
                 escalation_api_key: str | None = None,
                 escalation_model: str | None = None):
```

After the existing `self.verifier_graph` construction, add:

```python
        # C4: metrics graphs at temperature 0.3, both budgets — used only when
        # the executor samples a [METRICS] task 3x for a majority vote.
        metrics_instr = ESCALATE_INSTRUCTIONS + "\n\n" + SPECIALISTS["metrics"]
        for hi, cap in ((False, MAX_ITER),
                        (True, iter_budget(HIGH_VALUE_THRESHOLD))):
            self._graphs[("metrics_sampled", hi)], _ = agent_mod.create_agent(
                senior_api_key, splunk,
                model=senior_model, base_url=senior_base_url,
                extra_instructions=metrics_instr,
                extra_tools=[web_lookup],
                max_iter=cap,
                temperature=SAMPLE_TEMPERATURE,
            )
        # C3: escalation graph — the strong model (gpt-5.4) at the high budget,
        # dispatched by the adjudicator on low-confidence 1000-pt questions.
        self.escalation_graph = None
        self.escalation_model = escalation_model
        if escalation_model:
            self.escalation_graph, _ = agent_mod.create_agent(
                escalation_api_key or senior_api_key, splunk,
                model=escalation_model,
                extra_instructions=ESCALATE_INSTRUCTIONS,
                extra_tools=[web_lookup],
                max_iter=iter_budget(HIGH_VALUE_THRESHOLD),
            )
```

Replace `run_senior` with:

```python
    def run_senior(self, subquestion: str, parent_qid: str, idx: int,
                   points: int = 0, max_iter: int | None = None,
                   sample: bool = False, escalate: bool = False) -> dict:
        """`max_iter` overrides the points-based budget for the one caller that
        needs a different real graph cap (the Verifier's <=3-query pass) —
        routed to a dedicated pre-built graph so the override actually reaches
        the LangGraph step-cap check baked in at create_agent() build time.
        `escalate` routes to the strong-model escalation graph (C3); `sample`
        routes metrics tasks to the temperature-0.3 graph (C4)."""
        if max_iter is not None:
            return self._run("senior", self.verifier_graph, self.senior_model,
                             subquestion, parent_qid, idx, max_iter=max_iter)
        if escalate and self.escalation_graph is not None:
            cap = iter_budget(HIGH_VALUE_THRESHOLD)
            return self._run("senior", self.escalation_graph,
                             self.escalation_model,
                             subquestion, parent_qid, idx, max_iter=cap)
        budget = iter_budget(points)
        role   = parse_specialist_tag(subquestion)
        graph  = self._graphs[graph_key(role, budget > MAX_ITER, sample)]
        return self._run("senior", graph, self.senior_model,
                         subquestion, parent_qid, idx, max_iter=budget)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_graph_key.py -q`
Expected: 3 passed

Run: `python -m pytest agent/v0/tests/ -q`
Expected: 143 passed — existing pool behaviour unchanged (defaults `sample=False, escalate=False, escalation_model=None`).

Also verify v0.0.0 default is untouched:

```bash
python -c "import sys; sys.path.insert(0, 'agent'); import inspect, splunk_agent; assert inspect.signature(splunk_agent.create_agent).parameters['temperature'].default == 0; print('ok')"
```
Expected: `ok`

- [ ] **Step 6: Changelog entry**

Append to `## Plan C Tasks` in `docs/version_architecture/v0/v0.3.md`:

```markdown
- Plan C Task 3: pool plumbing — `create_agent` gains a `temperature` param
  (default 0, v0.0.0 behaviour unchanged); pool builds temperature-0.3 metrics
  graphs (`graph_key` selects them when sampling) and an opt-in gpt-5.4
  escalation graph; `run_senior(..., sample=, escalate=)` routes to them.
```

- [ ] **Step 7: Commit**

```bash
git add agent/splunk_agent.py agent/v0/splunk_subagent.py agent/v0/tests/test_graph_key.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): sampled metrics graphs + gpt-5.4 escalation graph in worker pool"
```

---

### Task 4: Adjudicator node wired into the SH graph (C1 + C3 dispatch)

**Files:**
- Modify: `agent/v0/orchestrator.py` — imports (line 34), constants (below line 41), `SHState` (lines 318–328), `DelegationContext` (lines 330–352), new `adjudicator_node` + routing (lines 724–760), `_run_senior` (lines 763–775), `run_sh` initial state (lines 797–810)
- Test: `agent/v0/tests/test_adjudicator_wiring.py`
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Consumes: `adjudicator.adjudicate_once / resolve_choice / fallback_choice / ADJUDICATOR_SYSTEM_PROMPT` (Task 1); `SplunkWorkerPool.run_senior(..., escalate=)` (Task 3); existing `case_file.build_ledger / render_ledger`.
- Produces:
  - `DelegationContext.current_guidance: str` — set via `reset_question(qid, points=0, question="", guidance="")` (new keyword; Task 7's runner passes it).
  - `SHState` gains `adjudicated: bool`.
  - Graph node named `"adjudicator"` between joiner-done and verifier.
  - Module constants `ADJUDICATE_MIN_CANDIDATES = 2`, `ESCALATE_MIN_POINTS = 1000`.
  - `_run_senior(ctx, subquestion, idx, parent_run_tree, max_iter=None, sample=False, escalate=False)` — passthrough kwargs (Task 6 uses `sample`).

- [ ] **Step 1: Write the failing tests**

Create `agent/v0/tests/test_adjudicator_wiring.py`:

```python
from orchestrator import build_sh_agent_compiler, DelegationContext


def test_reset_question_records_guidance():
    ctx = DelegationContext(pool=None, logger=None)
    ctx.reset_question("Q331", points=1000, question="fence?",
                       guidance="number only")
    assert ctx.current_guidance == "number only"
    ctx.reset_question("Q1", points=100, question="next?")
    assert ctx.current_guidance == ""      # resets between questions


def test_graph_contains_adjudicator_node():
    ctx = DelegationContext(pool=None, logger=None)
    graph, _ = build_sh_agent_compiler("sk-fake-key", "gpt-5.4", ctx)
    nodes = graph.get_graph().nodes
    assert "adjudicator" in nodes and "verifier" in nodes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agent/v0/tests/test_adjudicator_wiring.py -q`
Expected: 2 FAILED — `TypeError: reset_question() got an unexpected keyword argument 'guidance'` and `AssertionError` (no adjudicator node).

- [ ] **Step 3: Implement in `orchestrator.py`**

**3a — imports.** Extend the import block (line 34):

```python
from case_file import build_ledger, render_ledger, snap_to_ledger, CaseFile, parse_case_updates
from adjudicator import (adjudicate_once, resolve_choice, fallback_choice,
                         ADJUDICATOR_SYSTEM_PROMPT)
```

**3b — constants.** Below `MAX_HISTORY_MSGS` add:

```python
ADJUDICATE_MIN_CANDIDATES = 2     # adjudication only when selection is a real choice
ESCALATE_MIN_POINTS       = 1000  # C3: low-confidence 1000-pt questions escalate to gpt-5.4
```

**3c — `SHState`.** Add one field after `verified: bool`:

```python
    adjudicated:  bool                           # True once the adjudicator pass has run
```

**3d — `DelegationContext`.** In `__init__` add `self.current_guidance = ""` after `self.current_question = ""`. Replace `reset_question` with:

```python
    def reset_question(self, qid: str, points: int = 0, question: str = "",
                       guidance: str = "") -> None:
        self.current_qid      = qid
        self.current_points   = points
        self.current_question = question
        self.current_guidance = guidance
        self.q_delegations    = []
        self.q_handoffs       = []
```

**3e — `_run_senior` passthrough.** Change its signature and pool call:

```python
def _run_senior(ctx: DelegationContext, subquestion: str, idx: int, parent_run_tree,
                max_iter: int | None = None, sample: bool = False,
                escalate: bool = False) -> dict:
```

```python
        return ctx.pool.run_senior(subquestion, ctx.current_qid, idx,
                                   points=ctx.current_points, max_iter=max_iter,
                                   sample=sample, escalate=escalate)
```

**3f — the node.** Inside `build_sh_agent_compiler`, after `verifier_node`, add:

```python
    # ── Adjudicator (Plan C: rule-ranked selection over the candidate ledger) ─
    def adjudicator_node(state: SHState) -> dict:
        answer = state.get("final_answer", "")
        ledger = build_ledger(ctx.q_delegations)
        if len(ledger) < ADJUDICATE_MIN_CANDIDATES:
            return {"adjudicated": True}   # nothing to select between

        def _invoke(prompt_text: str) -> str:
            resp = llm.invoke([SystemMessage(content=ADJUDICATOR_SYSTEM_PROMPT),
                               HumanMessage(content=prompt_text)])
            return (resp.content or "").strip()

        print(f"\n[SH ADJUDICATOR]  {len(ledger)} candidate(s), joiner pick={answer!r}")
        verdict = adjudicate_once(_invoke, ctx.current_question,
                                  ctx.current_guidance, ledger)

        # One bounded follow-up per question: a targeted tiebreak query, or —
        # on low-confidence 1000-pt questions — a strong-model escalation run.
        escalate = ctx.current_points >= ESCALATE_MIN_POINTS
        needs_followup = bool(verdict["tiebreak"]) or (
            verdict["confidence"] == "low" and escalate)
        if needs_followup:
            subq = verdict["tiebreak"] or (
                f"{ctx.current_question}\n\nPrior workers produced conflicting "
                f"candidates (below). Independently determine the answer using "
                f"a DIFFERENT approach or sourcetype family — do not just "
                f"re-run their queries.\n\n{render_ledger(ledger)}")
            worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
            label = "ESCALATION" if escalate else "TIEBREAK"
            print(f"[SH ADJUDICATOR] {label} -> senior#{worker_idx}: {subq[:200]}")
            try:
                result = _run_senior(ctx, subq, worker_idx,
                                     get_current_run_tree(), escalate=escalate)
            except Exception as exc:
                result = None
                print(f"[SH ADJUDICATOR] {label} worker crashed: {exc} — "
                      f"adjudicating on the existing ledger")
            if result is not None:
                record = {
                    "worker":      f"senior#{worker_idx}",
                    "qid":         ctx.current_qid,
                    "subquestion": subq,
                    "status":      result.get("status", "?"),
                    "answer":      result.get("answer", ""),
                    "spl_used":    result.get("spl_used", []),
                    "sourcetypes": result.get("sourcetypes", []),
                    "full_state":  result.get("full_state", []),
                    "iterations":  result.get("iterations", 0),
                    "cap_hit":     result.get("cap_hit", False),
                }
                ctx.q_delegations.append(record)
                ctx.all_delegations.append(record)
                ctx.logger.timeline(
                    f"- **Adjudicator {label.lower()} #{worker_idx}**  "
                    f"_[{record['status']}]_\n"
                    f"    - answer: {(record['answer'] or '').strip()[:400]}")
                ledger = build_ledger(ctx.q_delegations)
                verdict = adjudicate_once(_invoke, ctx.current_question,
                                          ctx.current_guidance, ledger)

        chosen = verdict["answer"]
        if not chosen:
            # UNKNOWN / synthesized choice. Q321 hard rule: keep the joiner's
            # answer if it is itself an honest ledger/question value, else take
            # the best honest candidate — never a value from nowhere.
            if resolve_choice(answer, ledger, ctx.current_question):
                chosen = answer
            else:
                chosen = fallback_choice(ledger) or answer
        changed = (chosen != answer)
        print(f"[SH ADJUDICATOR] choice={chosen!r} "
              f"confidence={verdict['confidence']} changed={changed}")
        _emit = getattr(ctx.logger, "events", None)
        if _emit:
            _emit.emit("adjudication", qid=ctx.current_qid, chosen=chosen,
                       confidence=verdict["confidence"], changed=changed,
                       candidates=len(ledger))
        ctx.logger.timeline(
            f"- **Adjudicator**  confidence={verdict['confidence']} "
            f"candidates={len(ledger)}\n"
            f"    - joiner pick: {answer!r}\n"
            f"    - adjudicated: {chosen!r}{'  (CHANGED)' if changed else ''}")
        out: dict = {"adjudicated": True}
        if changed:
            out["final_answer"] = chosen
        return out
```

**3g — routing.** Replace `route_joiner`'s done branch and add `route_adjudicator`:

```python
    def route_joiner(state: SHState) -> str:
        if state.get("needs_replan"):
            return "planner"
        if state.get("done"):
            return "adjudicator"
        if state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):      # replan set new tasks
            return "executor"
        return END

    def route_adjudicator(state: SHState) -> str:
        if _should_verify(ctx) and not state.get("verified"):
            return "verifier"
        return END
```

Rewire the graph block:

```python
    g = StateGraph(SHState)
    g.add_node("planner",     planner_node)
    g.add_node("executor",    executor_node)
    g.add_node("joiner",      joiner_node)
    g.add_node("adjudicator", adjudicator_node)
    g.add_node("verifier",    verifier_node)
    g.set_entry_point("planner")
    g.add_conditional_edges("planner",  route_planner,
                            {"executor": "executor", END: END})
    g.add_edge("executor", "joiner")
    g.add_conditional_edges("joiner",   route_joiner,
                            {"executor": "executor", "planner": "planner",
                             "adjudicator": "adjudicator", END: END})
    g.add_conditional_edges("adjudicator", route_adjudicator,
                            {"verifier": "verifier", END: END})
    g.add_edge("verifier", END)
```

Note: the planner's DIRECT ANSWER path still routes straight to END (`route_planner`) — with zero delegations the ledger is empty and adjudication would no-op anyway.

**3h — `run_sh` initial state.** Add to the `graph.invoke({...})` dict:

```python
            "adjudicated":  False,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_adjudicator_wiring.py -q`
Expected: 2 passed

Run: `python -m pytest agent/v0/tests/ -q`
Expected: 145 passed

- [ ] **Step 5: Changelog entry**

Append to `## Plan C Tasks`:

```markdown
- Plan C Task 4: adjudicator node wired between joiner and verifier — runs when
  the ledger has >=2 candidates; may dispatch ONE follow-up worker (tiebreak
  query; gpt-5.4 escalation on low-confidence 1000-pt questions) then
  re-adjudicates once; verifier now confirms/refutes the adjudicated answer.
  `DelegationContext` carries `current_guidance` for rule (c).
```

- [ ] **Step 6: Commit**

```bash
git add agent/v0/orchestrator.py agent/v0/tests/test_adjudicator_wiring.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): adjudicator node between joiner and verifier with bounded tiebreak/escalation"
```

---

### Task 5: Dual-track planning for 1000-pt questions (C2)

**Files:**
- Modify: `agent/v0/run_all_v0.py:90-99` (`build_sh_message`)
- Modify: `agent/v0/orchestrator.py:52-99` (`PLANNER_SYSTEM_PROMPT`)
- Test: `agent/v0/tests/test_dual_track.py`
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Produces: `run_all_v0.build_sh_message(qid, qtext, guidance, points=0) -> str` — new optional `points`; emits a `DUAL-TRACK:` instruction line when `points >= DUAL_TRACK_MIN_POINTS`. `run_all_v0.DUAL_TRACK_MIN_POINTS = 1000`.

- [ ] **Step 1: Write the failing tests**

Create `agent/v0/tests/test_dual_track.py`:

```python
from run_all_v0 import build_sh_message, DUAL_TRACK_MIN_POINTS


def test_dual_track_line_for_1000pt():
    msg = build_sh_message("Q331", "What is the fence?", "number", points=1000)
    assert "DUAL-TRACK" in msg


def test_no_dual_track_below_threshold():
    msg = build_sh_message("Q209", "Which host?", "", points=500)
    assert "DUAL-TRACK" not in msg


def test_points_default_keeps_old_behaviour():
    msg = build_sh_message("Q1", "Which host?", "")
    assert "DUAL-TRACK" not in msg and "Q1" in msg


def test_threshold_is_1000():
    assert DUAL_TRACK_MIN_POINTS == 1000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agent/v0/tests/test_dual_track.py -q`
Expected: FAIL with `ImportError: cannot import name 'DUAL_TRACK_MIN_POINTS'`

- [ ] **Step 3: Implement**

In `agent/v0/run_all_v0.py`, below the `SENIOR_MODEL` constant add:

```python
DUAL_TRACK_MIN_POINTS = 1000   # C2: 1000-pt questions get two orthogonal plan tracks
```

Replace `build_sh_message`:

```python
def build_sh_message(qid, qtext, guidance, points=0):
    lines = [f"New question — {qid}.", f"Question: {qtext}"]
    if guidance:
        lines.append(f"Answer format guidance: {guidance}")
    if points >= DUAL_TRACK_MIN_POINTS:
        lines.append(
            "DUAL-TRACK: this is a 1000-point question. Produce TWO orthogonal "
            "task tracks that attack it via DIFFERENT sourcetype families or "
            "approaches (2-3 tasks each). At least one task must enumerate the "
            "whole candidate population UNFILTERED (e.g. `stats count by "
            "<entity>` / `stats sum(bytes) by Username`) before any track "
            "narrows to a specific lead. Keep tracks $N-independent so they "
            "run in parallel."
        )
    lines.append(
        "Write your PLAN block, then produce your TASKS list. "
        "Scan your memory for relevant prior findings (hosts, IPs, usernames, bucket names, "
        "time windows, sourcetypes) and embed that context in every task you write."
    )
    return "\n".join(lines)
```

In `agent/v0/orchestrator.py`, add one rule bullet to `PLANNER_SYSTEM_PROMPT`'s `RULES:` list (after the specialist-tag bullet, before the CASE FILE bullet):

```
- If the question message contains a DUAL-TRACK instruction: your TASKS must
  form two clearly orthogonal approaches (different sourcetype families or
  methods), 2-3 tasks each within the 6-task cap, and at least one task must
  enumerate the whole population unfiltered before narrowing.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_dual_track.py -q`
Expected: 4 passed

- [ ] **Step 5: Changelog entry**

Append to `## Plan C Tasks`:

```markdown
- Plan C Task 5: dual-track planning — `build_sh_message` adds a DUAL-TRACK
  instruction on >=1000-pt questions; planner prompt rule requires two
  orthogonal tracks with one unfiltered population-enumeration task (Q330 class).
```

- [ ] **Step 6: Commit**

```bash
git add agent/v0/run_all_v0.py agent/v0/orchestrator.py agent/v0/tests/test_dual_track.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): dual-track planner instruction for 1000-pt questions"
```

---

### Task 6: Executor 3× sampling of metrics tasks with majority vote (C4)

**Files:**
- Modify: `agent/v0/orchestrator.py` — imports, constants, `executor_node` (lines 432–508)
- Test: `agent/v0/tests/test_plan_samples.py`
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Consumes: `adjudicator.majority_answer` (Task 2), `specialists.parse_specialist_tag` (existing), `_run_senior(..., sample=)` (Task 4).
- Produces: `orchestrator.plan_samples(subquestion: str, points: int) -> int`; constants `METRICS_SAMPLES = 3`, `SAMPLE_MIN_POINTS = 500`.

- [ ] **Step 1: Write the failing tests**

Create `agent/v0/tests/test_plan_samples.py`:

```python
from orchestrator import plan_samples, METRICS_SAMPLES


def test_metrics_high_value_sampled_3x():
    assert plan_samples("[METRICS] average duration of x", 1000) == METRICS_SAMPLES
    assert plan_samples("[METRICS] perc75 of bytes", 500) == METRICS_SAMPLES


def test_low_value_metrics_not_sampled():
    assert plan_samples("[METRICS] count events", 100) == 1


def test_non_metrics_never_sampled():
    assert plan_samples("[HUNTER] find the host", 1000) == 1
    assert plan_samples("[CONTENT] read the email body", 1000) == 1
    assert plan_samples("untagged task", 1000) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agent/v0/tests/test_plan_samples.py -q`
Expected: FAIL with `ImportError: cannot import name 'plan_samples'`

- [ ] **Step 3: Implement**

In `agent/v0/orchestrator.py`:

Add import:

```python
from specialists import parse_specialist_tag
```

and extend the adjudicator import with `majority_answer`:

```python
from adjudicator import (adjudicate_once, resolve_choice, fallback_choice,
                         ADJUDICATOR_SYSTEM_PROMPT, majority_answer)
```

Add constants below `ESCALATE_MIN_POINTS`:

```python
METRICS_SAMPLES   = 3     # C4: samples per metrics task (majority vote)
SAMPLE_MIN_POINTS = 500   # only high-value questions pay the 3x metrics cost
```

Add a module-level function (near `substitute_deps`):

```python
def plan_samples(subquestion: str, points: int) -> int:
    """C4 self-consistency: [METRICS] tasks on high-value questions run 3x
    (temperature 0.3) and the majority extracted value wins. Everything else
    runs once. Gated at >=500pt as a cost guard — the spec samples all metrics
    questions, but low-value ones can't recoup the 3x spend."""
    if (parse_specialist_tag(subquestion) == "metrics"
            and (points or 0) >= SAMPLE_MIN_POINTS):
        return METRICS_SAMPLES
    return 1
```

Rework the dispatch/collect section of `executor_node`. Replace from the `n_workers = min(...)` line through the end of the `with concurrent.futures.ThreadPoolExecutor` block (the `ready` computation above and the `remaining = ...` line below stay exactly as they are):

```python
            submissions = sum(plan_samples(t.subquestion, ctx.current_points)
                              for t in ready)
            n_workers = min(submissions, MAX_WORKERS)
            print(f"\n[SH EXECUTOR] dispatching {len(ready)} task(s), "
                  f"{submissions} worker run(s) ({n_workers} parallel slot(s))")

            parent_run_tree = get_current_run_tree()
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as exe:
                futures: dict = {}
                for t in ready:
                    subq = substitute_deps(t.subquestion, completed)
                    if ctx.q_handoffs:
                        subq += ("\n\nCONTEXT FROM PRIOR ATTEMPTS ON THIS QUESTION "
                                 "(resume the hunt, do not restart it):\n"
                                 + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]))
                    n = plan_samples(t.subquestion, ctx.current_points)
                    if n > 1:
                        print(f"[SH EXECUTOR] metrics task {t.idx}: sampling {n}x "
                              f"(temperature 0.3, majority vote)")
                    for _s in range(n):
                        worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
                        print(f"\n[SH -> SENIOR #{worker_idx}  task={t.idx}]\n{subq[:300]}")
                        futures[exe.submit(_run_senior, ctx, subq, worker_idx,
                                           parent_run_tree,
                                           sample=(n > 1))] = (t, worker_idx, subq)

                per_task: dict[int, list] = {}
                for fut, (t, worker_idx, subq) in futures.items():
                    try:
                        result = fut.result()
                    except Exception as exc:
                        result = {
                            "status": "failed",
                            "answer": f"worker crashed: {exc}",
                            "spl_used": [], "sourcetypes": [], "full_state": [],
                            "iterations": 0, "cap_hit": False,
                        }
                    per_task.setdefault(t.idx, []).append(result)

                    if (result["status"] in ("too_big", "failed")
                            or result.get("cap_hit")):
                        if result["status"] in ("too_big", "failed"):
                            ctx.failed_delegations += 1
                        ctx.q_handoffs.append(build_handoff_digest(
                            {**result, "worker": f"senior#{worker_idx}"}))

                    record = {
                        "worker":      f"senior#{worker_idx}",
                        "qid":         ctx.current_qid,
                        "subquestion": subq,
                        "status":      result["status"],
                        "answer":      result["answer"],
                        "spl_used":    result["spl_used"],
                        "sourcetypes": result["sourcetypes"],
                        "full_state":  result["full_state"],
                        "iterations":  result.get("iterations", 0),
                        "cap_hit":     result.get("cap_hit", False),
                    }
                    ctx.q_delegations.append(record)
                    ctx.all_delegations.append(record)

                    ctx.logger.timeline(
                        f"- **Senior #{worker_idx}**  _[{result['status']}]_  task={t.idx}\n"
                        f"    - subquestion: {subq[:200]}\n"
                        f"    - answer: {(result['answer'] or '').strip()[:400]}\n"
                        f"    - SPL: {result['spl_used']}"
                    )

                for idx_, res_list in per_task.items():
                    if len(res_list) > 1:
                        winner = majority_answer(res_list)
                        if winner is not None:
                            print(f"[SH EXECUTOR] task {idx_}: majority vote -> "
                                  f"{(winner.get('answer') or '')[:120]!r}")
                        completed[idx_] = winner or res_list[0]
                    else:
                        completed[idx_] = res_list[0]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agent/v0/tests/test_plan_samples.py -q`
Expected: 3 passed

Run: `python -m pytest agent/v0/tests/ -q`
Expected: 152 passed (single-sample path is behaviour-identical: `per_task` has one entry per task, `completed[t.idx] = res_list[0]`)

- [ ] **Step 5: Changelog entry**

Append to `## Plan C Tasks`:

```markdown
- Plan C Task 6: executor samples [METRICS] tasks 3x at temperature 0.3 on
  >=500pt questions; `majority_answer` picks the task result (all samples still
  land in the ledger/delegations). `plan_samples` gates it; single-sample path
  behaviour-identical. Deviation from spec noted: gated at >=500pt as a cost
  guard rather than sampling every metrics question.
```

- [ ] **Step 6: Commit**

```bash
git add agent/v0/orchestrator.py agent/v0/tests/test_plan_samples.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): 3x self-consistency sampling for high-value metrics tasks"
```

---

### Task 7: Runner wiring + live verification smoke

**Files:**
- Modify: `agent/v0/run_all_v0.py` — constants, pool construction (lines 275–278), banner (line 291), `reset_question` call (line 368), `build_sh_message` call (line 380)
- Modify: `docs/version_architecture/v0/v0.3.md`

**Interfaces:**
- Consumes: `SplunkWorkerPool(..., escalation_api_key=, escalation_model=)` (Task 3); `ctx.reset_question(..., guidance=)` (Task 4); `build_sh_message(..., points=)` (Task 5).
- Produces: `run_all_v0.ESCALATION_MODEL = "gpt-5.4"`; a fully wired Plan C pipeline.

- [ ] **Step 1: Wire the runner**

In `agent/v0/run_all_v0.py`:

Below `SENIOR_MODEL` add:

```python
ESCALATION_MODEL = "gpt-5.4"   # C3: adjudicator's strong-model track B
```

Change the pool construction (lines 275–278) to:

```python
    pool      = SplunkWorkerPool(splunk, senior_api_key=senior_api_key,
                                 senior_model=senior_model,
                                 senior_base_url=senior_base_url,
                                 tracker=tracker,
                                 escalation_api_key=OPENAI_API_KEY,
                                 escalation_model=ESCALATION_MODEL)
```

Change the reset call (line 368) to:

```python
        ctx.reset_question(qid, points=points, question=qtext, guidance=guidance)
```

Change the SH invocation (line 380) to pass points:

```python
                build_sh_message(qid, qtext, guidance, points=points),
```

Update the runner banner (line 291) to show the escalation model:

```python
    print(f"  SH={SH_MODEL}  Senior={senior_model} ({senior_provider})  "
          f"Escalation={ESCALATION_MODEL}  Extractor={extractor.model}(NIM)")
```

- [ ] **Step 2: Full test suite + syntax check**

Run: `python -m pytest agent/v0/tests/ -q`
Expected: 152 passed

Run: `python -c "import ast; ast.parse(open('agent/v0/run_all_v0.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Changelog entry**

Append to `## Plan C Tasks`:

```markdown
- Plan C Task 7: runner wiring — pool built with the gpt-5.4 escalation graph,
  `reset_question` carries answer guidance to the adjudicator, `build_sh_message`
  gets points for the dual-track gate.
```

- [ ] **Step 4: Commit**

```bash
git add agent/v0/run_all_v0.py docs/version_architecture/v0/v0.3.md
git commit -m "feat(v0.3-planC): wire escalation model, guidance, and dual-track gate into the runner"
```

- [ ] **Step 5: Live combined smoke (cost-policy compliant — NOT a full run)**

Per the cost policy and the standing smoke shape (4 hard 1000-pt + 1 simple):

```bash
python agent/v0/run_all_v0.py --ids Q216,Q329,Q330,Q331,Q303 --recon --hints
```

Output lands in `log/temp/test_<ts>/`. Expected cost: **~$1.5–3** (Plan B smoke was $1.09; add gpt-5.4 escalation workers on up to 4 questions + 3× metrics sampling on Q216/Q331-class tasks). **Confirm with the user before launching.**

Verify in the run dir / console:
- `[SH ADJUDICATOR]` fires on every question whose ledger has ≥2 candidates; `adjudication` events in `events.jsonl` carry `chosen/confidence/changed/candidates`.
- Dual-track: the 1000-pt questions' plans show two orthogonal tracks (planner output in `timeline.md`), including one unfiltered enumeration task.
- Escalation: any low-confidence 1000-pt adjudication logs an `ESCALATION -> senior#N` dispatch and an `Adjudicator escalation` timeline entry.
- Metrics sampling: a `[METRICS]` task on Q216/Q331 logs `sampling 3x` and a `majority vote ->` line.
- No regression on Plan B mechanics: `finalize_answer` still snaps both extract sites; `reconcile_findings` still demotes on WRONG.
- The submitted answer for every question is a ledger value or question-text value (spot-check `questions/*.json` `clean_answer` against `candidate_ledger`).

- [ ] **Step 6: Record the smoke in the version doc**

Add a `## Plan C combined smoke — test_<ts> (2026-MM-DD)` section to `docs/version_architecture/v0/v0.3.md` (same shape as the Plan B smoke section): command, score, tokens/cost estimate, which mechanisms fired, defects found. Commit:

```bash
git add docs/version_architecture/v0/v0.3.md
git commit -m "docs(v0.3-planC): record Plan C combined smoke result"
```

---

## Spec coverage self-check

| Spec item (v0.2_improvement_plans.md §Plan C) | Task |
|---|---|
| 1. Adjudicator node, rules (a)–(d), tiebreak query, Q321 hard rule | Tasks 1, 4 |
| 2. Dual-track solve for 1000-pt questions | Task 5 |
| 3. Model escalation ladder (cheap track A, gpt-5.4 track B on low confidence) | Tasks 3, 4, 7 |
| 4. Self-consistency arithmetic (3× @ temp 0.3, majority) | Tasks 2, 3, 6 |
| 5. Prerequisite verifier plumbing fix | Already landed (v0.3 Task 1) — verifier untouched, now confirms/refutes the adjudicated answer |

Known deliberate deviations (both flagged in changelog entries):
- Metrics sampling gated at ≥500pt (cost guard; spec samples all metrics questions).
- "Adjudicator model gpt-5.4" is satisfied by reusing the SH's existing `llm` client (same model, temp 0) — no separate client.
