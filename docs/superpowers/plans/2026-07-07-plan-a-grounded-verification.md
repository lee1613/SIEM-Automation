# Plan A — Grounded Verification Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Stop the v1 pipeline from dropping, mangling, or fabricating answers that a worker already found — the single biggest fixable point loss in v1.1 (JOINER fabrication 2,300 pts + EXTRACTOR 500 + REASONING 800) — and open the two structurally-blocked classes (raw content, external knowledge).

**Architecture:** All changes sit in the existing LLMCompiler SH graph (`agent/v1/orchestrator.py`), the reused v0 worker graph (`agent/splunk_agent.py`), and the extractor. The load-bearing idea is a **deterministic grounding guard**: the SH's final answer must appear verbatim in some worker's evidence or the question text, or it is rejected and replanned — LLM prompt compliance is a helper, the Python guard is the enforcement. New capabilities (raw-content reads, web lookup) are added as tools; a Verifier node re-checks high-value answers.

**Tech Stack:** Python 3.11, pytest 9.1, LangGraph, LangChain tools, requests.

**Validation policy:** Every task ends with unit tests (green) + an import/parse check. Live behavior is validated with **cheap `--ids` smoke runs (2–4 questions)** only — NO full 56-question run in this plan. The human triggers the full scoring run.

**Depends on:** the observability foundation (2026-07-07-observability-foundation.md) — already merged. `metrics.json`/`events.jsonl` let each smoke run be inspected without reading raw logs.

---

## File Structure

| File | Responsibility | Change |
|------|----------------|--------|
| `agent/v1/grounding.py` | Pure grounding predicate + candidate fallback | **Create** |
| `agent/v1/orchestrator.py` | Grounded joiner guard; answer-shape in planner; Verifier node; points-aware rounds | Modify |
| `agent/splunk_agent.py` | `get_raw_events` tool; noise-filter prompt patch; points-aware MAX_ITER; cap→PARTIAL discipline | Modify |
| `agent/v1/web_tool.py` | `web_lookup` tool (DuckDuckGo HTML, no API key) | **Create** |
| `agent/v1/splunk_subagent.py` | Give workers the web tool; pass points through | Modify |
| `agent/v1/extractor.py` | Accept `expected_shape` hint | Modify |
| `agent/v1/run_all_v1.py` | Thread question points + expected_shape through | Modify |
| `agent/v1/tests/` | pytest for all of the above | add files |

Run all commands from project root. Tests rely on the existing `agent/v1/tests/conftest.py`.

---

## Task 1: Grounding predicate (pure, the enforcement core)

**Files:**
- Create: `agent/v1/grounding.py`
- Create: `agent/v1/tests/test_grounding.py`

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_grounding.py`:

```python
from grounding import is_grounded, best_candidate


def test_grounded_when_answer_in_a_task_result():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253"}}
    assert is_grounded("199.66.91.253", tr, "What is the C2 IP?") is True


def test_grounded_is_case_insensitive():
    tr = {1: {"status": "solved", "answer": "found host BSTOLL-L.froth.ly"}}
    assert is_grounded("bstoll-l.froth.ly", tr, "") is True


def test_grounded_when_answer_in_question_text():
    # some answers legitimately echo the question (e.g. a term to confirm)
    assert is_grounded("column chart", {}, "Which chart type: column chart or bar?") is True


def test_ungrounded_when_answer_appears_nowhere():
    tr = {1: {"status": "partial", "answer": "candidates: /images/index1.jpeg"}}
    assert is_grounded("taedonggang.jpeg", tr, "Name the defacement image") is False


def test_empty_answer_is_ungrounded():
    assert is_grounded("", {1: {"answer": "x"}}, "q") is False


def test_best_candidate_prefers_solved_over_partial():
    tr = {
        1: {"status": "partial", "answer": "maybe FYODOR-L"},
        2: {"status": "solved", "answer": "FINAL ANSWER: BSTOLL-L"},
    }
    # returns the answer text of the highest-confidence non-empty task
    assert "BSTOLL-L" in best_candidate(tr)


def test_best_candidate_none_when_all_empty():
    assert best_candidate({1: {"status": "failed", "answer": ""}}) is None
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_grounding.py -v`
Expected: FAIL — no `grounding` module.

- [ ] **Step 3: Implement `grounding.py`**

Create `agent/v1/grounding.py`:

```python
#!/usr/bin/env python3
"""
Deterministic grounding check for the SH's final answer.

The joiner's FINAL ANSWER must appear verbatim (case-insensitive substring) in
at least one worker's answer text or in the question itself. If it doesn't, the
SH invented a value no delegate produced — the v1.1 fabrication failure mode
(Q221 'glacier', Q303 'tomcat7:Summer2018!', Q330 'james', Q333 'cve-2018-7600').
This module is pure so the guard is unit-testable without a live run.
"""

from __future__ import annotations

_STATUS_RANK = {"solved": 3, "partial": 2, "too_big": 1, "failed": 0}


def is_grounded(answer: str, task_results: dict, question_text: str = "") -> bool:
    a = (answer or "").strip().lower()
    if not a:
        return False
    if a in (question_text or "").lower():
        return True
    for r in task_results.values():
        if a in (r.get("answer") or "").lower():
            return True
    return False


def best_candidate(task_results: dict) -> str | None:
    """Highest-confidence non-empty worker answer, for the ungrounded fallback."""
    best = None
    best_rank = -1
    for r in task_results.values():
        ans = (r.get("answer") or "").strip()
        if not ans:
            continue
        rank = _STATUS_RANK.get(r.get("status", "failed"), 0)
        if rank > best_rank:
            best, best_rank = ans, rank
    return best
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_grounding.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/v1/grounding.py agent/v1/tests/test_grounding.py
git commit -m "feat(v1.2): grounding predicate + best-candidate fallback"
```

---

## Task 2: Wire the grounding guard into the joiner

**Files:**
- Modify: `agent/v1/orchestrator.py` (`joiner_node`, `JOINER_SYSTEM_PROMPT`)
- Create: `agent/v1/tests/test_joiner_guard.py`

**Context:** `joiner_node` currently extracts `FINAL ANSWER:` and returns it done. Add: after extracting the answer, if it is NOT grounded and replan rounds remain, force a REPLAN with a pointed message; if ungrounded and no rounds remain, fall back to `best_candidate` (the highest-confidence worker answer) rather than submitting the fabrication. The joiner already has access to `state["tasks"]`, `state["task_results"]`, and the question (last HumanMessage in `state["messages"]`).

- [ ] **Step 1: Write failing tests for the pure guard decision**

Extract the decision into a pure helper so it is testable without the LLM. Create `agent/v1/tests/test_joiner_guard.py`:

```python
from orchestrator import decide_joiner_answer


def test_grounded_answer_is_kept():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253"}}
    out = decide_joiner_answer("199.66.91.253", tr, "C2 IP?", plan_round=1, max_rounds=3)
    assert out["action"] == "final"
    assert out["answer"] == "199.66.91.253"


def test_ungrounded_with_rounds_left_replans():
    tr = {1: {"status": "partial", "answer": "candidates: /images/index1.jpeg"}}
    out = decide_joiner_answer("taedonggang.jpeg", tr, "defacement image",
                               plan_round=1, max_rounds=3)
    assert out["action"] == "replan"
    assert "not found" in out["reason"].lower()


def test_ungrounded_no_rounds_left_falls_back_to_best_candidate():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: /images/index1.jpeg"}}
    out = decide_joiner_answer("taedonggang.jpeg", tr, "defacement image",
                               plan_round=3, max_rounds=3)
    assert out["action"] == "final"
    assert "/images/index1.jpeg" in out["answer"]


def test_ungrounded_no_candidate_keeps_original():
    out = decide_joiner_answer("glacier", {1: {"status": "failed", "answer": ""}},
                               "iam resource", plan_round=3, max_rounds=3)
    assert out["action"] == "final"
    assert out["answer"] == "glacier"   # nothing better to offer
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_joiner_guard.py -v`
Expected: FAIL — no `decide_joiner_answer`.

- [ ] **Step 3: Implement `decide_joiner_answer` in orchestrator.py**

Add this module-level function to `agent/v1/orchestrator.py` (near `parse_plan`), importing the grounding helpers at the top (`from grounding import is_grounded, best_candidate`):

```python
def decide_joiner_answer(answer: str, task_results: dict, question_text: str,
                         *, plan_round: int, max_rounds: int) -> dict:
    """Grounding gate for the joiner's FINAL ANSWER.

    - grounded            -> keep it ('final')
    - ungrounded, rounds  -> 'replan' with a pointed reason
    - ungrounded, no rnds -> fall back to best worker candidate, else keep
    """
    if is_grounded(answer, task_results, question_text):
        return {"action": "final", "answer": answer}
    if plan_round < max_rounds:
        return {"action": "replan",
                "reason": (f"Your proposed answer {answer!r} was NOT found in any "
                           f"task result or the question. Either run a task that "
                           f"produces it as an exact value, or choose a value that "
                           f"DOES appear in the evidence.")}
    cand = best_candidate(task_results)
    return {"action": "final", "answer": cand if cand else answer}
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_joiner_guard.py -v`
Expected: 4 passed.

- [ ] **Step 5: Call the guard inside `joiner_node`**

In `joiner_node`, after the `FINAL ANSWER` regex match extracts `answer` (the `fa_m` branch), before returning `done=True`, run the guard. You need the question text — extract the most recent HumanMessage that isn't the joiner's own task-results message; simplest: capture the original question from the first HumanMessage in `state["messages"]` for this question. Use:

```python
        if fa_m:
            answer = fa_m.group(1).strip().split('\n')[0].strip()
            qtext = next((m.content for m in state["messages"]
                          if isinstance(m, HumanMessage)), "")
            decision = decide_joiner_answer(
                answer, task_results, qtext,
                plan_round=plan_round, max_rounds=MAX_PLAN_ROUNDS)
            if decision["action"] == "replan":
                replan_hm = HumanMessage(content=(
                    "GROUNDING CHECK FAILED. " + decision["reason"] +
                    "\nProduce a REPLAN with 1-2 targeted tasks, or a corrected "
                    "FINAL ANSWER that is present in the evidence."))
                return {
                    "messages":     [joiner_hm, response, replan_hm],
                    "plan_text":    jtext,
                    "tasks":        [],            # force planner? no—executor needs tasks
                    "task_results": task_results,
                    "plan_round":   plan_round + 1,
                    "done":         False,
                }
            answer = decision["answer"]
            return {
                "messages":     [joiner_hm, response],
                "plan_text":    jtext,
                "final_answer": answer,
                "done":         True,
            }
```

**Important routing note:** the replan branch above sets `tasks=[]`, but `route_joiner` sends to `executor` only when `state["tasks"]` is truthy. For a grounding-triggered replan we want the PLANNER to generate fresh tasks from the failure message. Add a new state key `needs_replan: bool` and update routing: in `route_joiner`, `return "planner" if state.get("needs_replan") else (...)`. Set `needs_replan=True` in the replan return above and add `"planner"` to the joiner's conditional edge map. Add `needs_replan` to `SHState` (default False) and clear it in `planner_node`'s returns. Wire the edge:

```python
    g.add_conditional_edges("joiner", route_joiner,
                            {"executor": "executor", "planner": "planner", END: END})
```

and in `route_joiner`:

```python
    def route_joiner(state: SHState) -> str:
        if state.get("needs_replan"):
            return "planner"
        if state.get("done") or state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):
            return "executor"
        return END
```

- [ ] **Step 6: Strengthen the joiner prompt (helper, not enforcement)**

Append to `JOINER_SYSTEM_PROMPT`:

```
GROUNDING RULE — CRITICAL:
- Your FINAL ANSWER must be a value that literally appears in one of the task
  results above (or the question). Never invent, guess, or synthesize a value
  no worker reported. If the tasks did not produce the needed value, prefer a
  focused REPLAN. If you must answer without it, use the closest value a worker
  actually reported, not a plausible-sounding fabrication.
```

- [ ] **Step 7: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -v`
Expected: all green (previous 27 + new).
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import orchestrator; print('ok')"`
Expected: `ok`.

- [ ] **Step 8: Cheap smoke run on two fabrication-class questions**

Run (scratch log root off OneDrive):
`SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q225,Q301`
Expected: completes; inspect `metrics.json` — Q225's `grounded` should now be `true` if the guard forced the joiner onto the real `/images/index1.jpeg` candidate (or at least it did not submit `taedonggang.jpeg`). Report the actual submitted answers and grounded flags. (Q301 is a control — a normal grounded question must still work.)

- [ ] **Step 9: Commit**

```bash
git add agent/v1/orchestrator.py agent/v1/tests/test_joiner_guard.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): grounding guard in joiner (anti-fabrication) + replan routing"
```

(Add a changelog line to `docs/version_architecture/v1/v1.2.md` in this commit.)

---

## Task 3: Answer-shape contract (planner → extractor)

**Files:**
- Modify: `agent/v1/orchestrator.py` (`PLANNER_SYSTEM_PROMPT`)
- Modify: `agent/v1/extractor.py` (accept `expected_shape`)
- Modify: `agent/v1/run_all_v1.py` (pass guidance as shape hint — already have `guidance`)
- Create: `agent/v1/tests/test_extractor_shape.py`

**Context:** Q202 submitted `E5-2676 v3` for official `E5-2676`. The extractor already gets `guidance`; add an explicit shape hint so it strips vendor/version suffixes and normalizes list format. Keep it minimal — the scoreboard compares `lower().strip()`, so casing is already safe; ordering/spacing/suffix are the real risks.

- [ ] **Step 1: Write failing test**

Create `agent/v1/tests/test_extractor_shape.py`:

```python
from extractor import build_extract_prompt


def test_prompt_includes_shape_when_given():
    p = build_extract_prompt("What processor?", "bare model number, no suffix",
                             "The CPU is Intel Xeon E5-2676 v3 @ 2.40GHz",
                             expected_shape="bare processor model like E5-XXXX, drop ' vN' suffix")
    assert "drop ' vN' suffix" in p
    assert "E5-2676 v3" in p  # the analysis is included


def test_prompt_without_shape_still_valid():
    p = build_extract_prompt("q", "", "answer text", expected_shape="")
    assert "answer text" in p
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_extractor_shape.py -v`
Expected: FAIL — no `build_extract_prompt`.

- [ ] **Step 3: Extract the prompt builder + add shape**

In `agent/v1/extractor.py`, refactor the inline prompt construction in `extract` into a module-level pure function and add the shape hint:

```python
def build_extract_prompt(question: str, guidance: str, verbose_answer: str,
                         expected_shape: str = "") -> str:
    guidance_line = f"Answer format guidance: {guidance}" if guidance else ""
    shape_line = f"Required answer shape: {expected_shape}" if expected_shape else ""
    return (
        f"Question: {question}\n\n"
        f"{guidance_line}\n{shape_line}\n\n"
        f"Agent's analysis: {verbose_answer}\n\n"
        "Based on the analysis above, state ONLY the exact answer with no "
        "explanation, no punctuation beyond what the format requires, and no "
        "surrounding text. Strip any vendor/version suffix not asked for. "
        "If the answer is a list, use comma-separated values with no spaces. "
        "If a number, give only the number. Output nothing else."
    )
```

Change `extract` to accept `expected_shape: str = ""` and call `build_extract_prompt(question, guidance, verbose_answer, expected_shape)` instead of the inline string. Keep `qid` param and token tracking.

- [ ] **Step 4: Planner emits an EXPECTED SHAPE line**

Append to `PLANNER_SYSTEM_PROMPT` (after the PLAN block spec):

```
- Also output one line:  EXPECTED SHAPE: <the exact form the scoreboard wants —
  e.g. "bare MAC address lowercase", "integer only", "comma-separated lowercase
  list no spaces", "filename with extension". Derive it from the answer guidance.>
```

Parse it in the runner and pass to the extractor. In `run_all_v1.py`, after `sh_answer` is produced, the shape is not in the answer — simplest reliable source is `guidance` itself. For now pass `expected_shape=guidance` (the guidance already carries format hints), i.e. `extractor.extract(qtext, guidance, sh_answer, qid=qid, expected_shape=guidance)`. (A later iteration can parse the planner's EXPECTED SHAPE line from the SH state; keep this task minimal.)

- [ ] **Step 5: Run tests + full suite**

Run: `python -m pytest agent/v1/tests/test_extractor_shape.py agent/v1/tests/ -v`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add agent/v1/extractor.py agent/v1/orchestrator.py agent/v1/run_all_v1.py agent/v1/tests/test_extractor_shape.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): answer-shape hint through planner->extractor"
```

---

## Task 4: Raw-content tool + noise-filter prompt patch

**Files:**
- Modify: `agent/splunk_agent.py` (`make_tools`, `SYSTEM_PROMPT`)
- Create: `agent/v1/tests/test_raw_events_tool.py`

**Context:** Q306/Q310/Q315/Q321/Q322 need to READ raw event content (email bodies, bash history, HTTP payloads), but the verify gate rejects any `run_splunk_search` without `| stats/top/rare`. Add a separate `get_raw_events` tool that returns raw events with a hard `limit`. Because `_verify_call`'s aggregation rule only applies to `run_splunk_search`, a new tool name is automatically exempt — but bound the result size to avoid blowing context. Also patch the prompt so workers stop excluding suspicious files by benign-name blocklists (Q317 excluded `HxTsr.exe` by regex).

- [ ] **Step 1: Write failing test (tool exists, is bounded, registered)**

Create `agent/v1/tests/test_raw_events_tool.py`:

```python
from unittest.mock import MagicMock
import splunk_agent


def test_get_raw_events_registered_and_bounded():
    fake = MagicMock()
    fake.sample_events.return_value = {"results": [{"_raw": "x"} for _ in range(50)]}
    tools = {t.name: t for t in splunk_agent.make_tools(fake)}
    assert "get_raw_events" in tools
    # limit is clamped to <= 20
    tools["get_raw_events"].invoke({"sourcetype": "stream:smtp",
                                    "keyword": "financial", "limit": 999})
    # the clamp happens before the splunk call; assert splunk got count<=20
    _, kwargs = fake.sample_events.call_args
    called_count = kwargs.get("count", (fake.sample_events.call_args[0] or [None]*5))
    assert True  # presence + no exception is the contract; clamp asserted below


def test_get_raw_events_clamps_limit(monkeypatch):
    fake = MagicMock()
    fake.sample_events.return_value = {"results": []}
    tools = {t.name: t for t in splunk_agent.make_tools(fake)}
    tools["get_raw_events"].invoke({"sourcetype": "stream:smtp", "limit": 999})
    call = fake.sample_events.call_args
    passed = call.kwargs.get("count")
    assert passed is not None and passed <= 20
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_raw_events_tool.py -v`
Expected: FAIL — `get_raw_events` not in tools.

- [ ] **Step 3: Add the tool**

In `agent/splunk_agent.py` `make_tools`, add (before the `return [...]`):

```python
    @tool
    def get_raw_events(sourcetype: str, keyword: str = "", index: str = "botsv3",
                       limit: int = 10) -> str:
        """Return RAW event content (not aggregated) from a sourcetype, to read
        the actual text of emails, scripts, bash history, HTTP payloads, etc.
        Use when the answer is INSIDE the event content rather than a field value.
        `limit` is capped at 20 to protect context. Prefer a specific `keyword`."""
        n = max(1, min(int(limit), 20))
        result = splunk.sample_events(sourcetype=sourcetype, index=index,
                                      keyword=keyword, count=n)
        return _format_result(result, keep_raw=True)
```

and add `get_raw_events` to the returned tool list.

- [ ] **Step 4: Patch the prompt (noise-filter discipline)**

Append to `SYSTEM_PROMPT` (before the example flow):

```
Reading content: when the answer is text inside an event (an email body, a
command line, a script, an uploaded file's content), use get_raw_events to read
the raw events rather than forcing an aggregation.

Never exclude a process, file, or host from suspicion just because its name looks
benign or "known-good". Suspicion comes from behavior (unusual parent, network,
timing), not from a name blocklist. Do not add NOT match(...) filters that drop
candidate answers by name.
```

- [ ] **Step 5: Run tests + full suite**

Run: `python -m pytest agent/v1/tests/test_raw_events_tool.py agent/v1/tests/ -v`
Expected: all green.

- [ ] **Step 6: Cheap smoke run on a content question**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q315`
Expected: completes; report whether any worker called `get_raw_events` (check the question's `questions/Q315.json` delegations `full_state` for the tool call) and the submitted answer. (Correctness not required for the smoke — tool usage + no crash is the bar.)

- [ ] **Step 7: Commit**

```bash
git add agent/splunk_agent.py agent/v1/tests/test_raw_events_tool.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): get_raw_events content-read tool + noise-filter prompt patch"
```

---

## Task 5: Web-knowledge tool

**Files:**
- Create: `agent/v1/web_tool.py`
- Modify: `agent/v1/splunk_subagent.py` (add the tool to worker graphs)
- Create: `agent/v1/tests/test_web_tool.py`

**Context:** Q213/Q302 (Symantec severity/date) and Q332/Q333 (CVE mapping) need external knowledge. Add a keyless `web_lookup` using DuckDuckGo's HTML endpoint; parse the top result snippets. Must degrade gracefully (return a clear "no network" string, never raise) so offline unit tests and Splunk-only runs don't break.

- [ ] **Step 1: Write failing tests (mock the HTTP layer)**

Create `agent/v1/tests/test_web_tool.py`:

```python
from unittest.mock import patch
import web_tool


SAMPLE_HTML = '''
<div class="result__snippet">Symantec rates Backdoor.PsEmpire severity: Medium.</div>
<div class="result__snippet">Second snippet about the threat.</div>
'''


def test_web_lookup_returns_snippets():
    with patch("web_tool._fetch", return_value=SAMPLE_HTML):
        out = web_tool.web_lookup.invoke({"query": "Backdoor.PsEmpire severity"})
    assert "Medium" in out


def test_web_lookup_network_failure_is_graceful():
    with patch("web_tool._fetch", side_effect=Exception("no network")):
        out = web_tool.web_lookup.invoke({"query": "anything"})
    assert "unavailable" in out.lower() or "no result" in out.lower()
    # must not raise
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_web_tool.py -v`
Expected: FAIL — no `web_tool`.

- [ ] **Step 3: Implement `web_tool.py`**

Create `agent/v1/web_tool.py`:

```python
#!/usr/bin/env python3
"""
Keyless web lookup tool for external knowledge the BOTSv3 dataset can't answer
(vendor threat severity/dates, CVE identification). Uses DuckDuckGo's HTML
endpoint and returns the top result snippets as plain text.

Degrades gracefully: any network/parse failure returns a clear string rather
than raising, so offline runs and unit tests never break the worker graph.
"""

from __future__ import annotations

import re
import html

import requests
from langchain_core.tools import tool

_DDG = "https://html.duckduckgo.com/html/"
_SNIPPET = re.compile(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
                      re.IGNORECASE | re.DOTALL)


def _fetch(query: str) -> str:
    resp = requests.post(_DDG, data={"q": query},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    return resp.text


def _clean(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


@tool
def web_lookup(query: str) -> str:
    """Look up EXTERNAL knowledge not in the Splunk dataset — e.g. a vendor's
    published threat severity/date, or which CVE matches an exploit technique.
    Returns the top web result snippets. Use ONLY for facts outside BOTSv3."""
    try:
        raw = _fetch(query)
    except Exception as exc:
        return f"web_lookup unavailable ({exc}); answer from dataset evidence instead."
    snippets = [_clean(m) for m in _SNIPPET.findall(raw)]
    snippets = [s for s in snippets if s][:5]
    if not snippets:
        return "web_lookup: no result snippets found."
    return " | ".join(snippets)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_web_tool.py -v`
Expected: 2 passed.

- [ ] **Step 5: Give workers the tool**

In `agent/v1/splunk_subagent.py`, the worker graph is built by `agent_mod.create_agent(...)`. Rather than change v0's tool list globally, extend the worker after creation is awkward — instead pass the extra tool through. Simplest: in `create_agent` (`agent/splunk_agent.py`), accept an optional `extra_tools: list | None = None` param, and if provided, append to `tools` before `tool_map`/`bind_tools`. Then in `SplunkWorkerPool.__init__`, import `from web_tool import web_lookup` and pass `extra_tools=[web_lookup]` into `create_agent`. Add a one-line mention to the ESCALATE/worker instructions that a `web_lookup` tool exists for external facts.

- [ ] **Step 6: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -v`
Expected: all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import splunk_subagent; print('ok')"`
Expected: `ok`.

- [ ] **Step 7: Cheap smoke run on a knowledge question**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q213`
Expected: completes; report whether `web_lookup` was called and the submitted answer.

- [ ] **Step 8: Commit**

```bash
git add agent/v1/web_tool.py agent/splunk_agent.py agent/v1/splunk_subagent.py agent/v1/tests/test_web_tool.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): keyless web_lookup tool for external knowledge questions"
```

---

## Task 6: Points-aware budget + cap→PARTIAL discipline

**Files:**
- Modify: `agent/splunk_agent.py` (`create_agent`/`agent_node` — dynamic MAX_ITER, forced-final message)
- Modify: `agent/v1/splunk_subagent.py` (`run_senior` accepts points)
- Modify: `agent/v1/orchestrator.py` (pass question points to workers)
- Modify: `agent/v1/run_all_v1.py` (thread points in)
- Create: `agent/v1/tests/test_budget.py`

**Context:** 46/56 questions got identical effort in v1.1; five of eight 1000-pt questions were wrong. Give ≥500-pt questions a larger iteration budget. And when the cap IS hit, force the worker's final message to be a PARTIAL-with-evidence, never a bare guess (Q328/Q332/Q333 guessed at the cap).

- [ ] **Step 1: Write failing test for the budget function**

Create `agent/v1/tests/test_budget.py`:

```python
from splunk_agent import iter_budget


def test_high_value_gets_more_iterations():
    assert iter_budget(1000) >= 25
    assert iter_budget(500) >= 25


def test_low_value_gets_base():
    assert iter_budget(100) == 15
    assert iter_budget(0) == 15
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_budget.py -v`
Expected: FAIL — no `iter_budget`.

- [ ] **Step 3: Implement `iter_budget` + use it**

In `agent/splunk_agent.py` add module-level:

```python
def iter_budget(points: int) -> int:
    """Iteration cap scaled by question value."""
    return 25 if (points or 0) >= 500 else MAX_ITER
```

Thread an optional `max_iter` through: `create_agent(..., max_iter: int = MAX_ITER)`, store it in a closure var used by `agent_node` and `should_continue` in place of the module `MAX_ITER`. Update the forced-final message branch so that when the cap is reached it instructs a PARTIAL-with-evidence:

```python
            msgs = msgs + [HumanMessage(
                "You have reached the maximum number of tool calls. Do NOT invent a "
                "value. Reply with PARTIAL ANSWER: <your best evidence-backed "
                "candidate>, UNCERTAINTY: <what is unconfirmed>, and the SPL you ran. "
                "If you have nothing concrete, reply ESCALATE with what you searched.")]
```

- [ ] **Step 4: Thread points from runner → orchestrator → worker**

- `run_all_v1.py`: the SH message already knows `points`; pass it into `run_sh(... , points=points)` and store on `ctx` (`ctx.current_points = points` in `reset_question`).
- `orchestrator.py`: `DelegationContext.reset_question(qid, points=0)` stores `self.current_points`. In `_run_senior`/`ctx.pool.run_senior`, pass `ctx.current_points`.
- `splunk_subagent.py`: `run_senior(self, subquestion, parent_qid, idx, points=0)`; build/select a graph with `max_iter=iter_budget(points)`. Since the graph is built once in `__init__`, instead build the LLM per-call is expensive — simplest: build TWO graphs at init, `self.senior_graph` (base) and `self.senior_graph_hi` (max_iter=25), and pick by `points>=500`. Document this.

Add `iter_budget` import in `splunk_subagent.py`.

- [ ] **Step 5: Run tests + full suite**

Run: `python -m pytest agent/v1/tests/ -v`
Expected: all green.

- [ ] **Step 6: Cheap smoke run on a 1000-pt question**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q330`
Expected: completes; report the max `iterations` seen across Q330's delegations in `questions/Q330.json` (should be allowed up to 25) and whether any delegation hit the cap with a PARTIAL (not a bare guess).

- [ ] **Step 7: Commit**

```bash
git add agent/splunk_agent.py agent/v1/splunk_subagent.py agent/v1/orchestrator.py agent/v1/run_all_v1.py agent/v1/tests/test_budget.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): points-aware iteration budget + cap->PARTIAL discipline"
```

---

## Task 7: Verifier node (highest-value, needs full-run tuning)

**Files:**
- Modify: `agent/v1/orchestrator.py` (new `verifier_node`, routing, prompt)
- Create: `agent/v1/tests/test_verifier.py`

**Context:** For ≥500-pt questions, after the joiner produces a grounded FINAL ANSWER, run one Verifier pass: a Senior worker in "prove-or-refute" mode runs ≤3 confirmation queries. Refuted → one targeted replan. This catches SENIOR-REASONING errors (Q212 wrong-timestamp "first", Q210 connection≠mining). This is the piece most needing full-run tuning, so keep the node behind a points gate and make its decision logic pure+tested; the human tunes the prompt against a full run.

- [ ] **Step 1: Write failing test for the pure verifier decision**

Create `agent/v1/tests/test_verifier.py`:

```python
from orchestrator import parse_verifier_verdict


def test_confirm_verdict():
    v = parse_verifier_verdict("Checked event order by _time. CONFIRMED: 30358")
    assert v["verdict"] == "confirmed"


def test_refute_verdict_with_correction():
    v = parse_verifier_verdict("The earliest by _time is 30358, not 30356. "
                               "REFUTED. CORRECTION: 30358")
    assert v["verdict"] == "refuted"
    assert v["correction"] == "30358"


def test_unknown_defaults_to_confirmed():
    # if the verifier is inconclusive, don't block the pipeline
    v = parse_verifier_verdict("could not run additional queries")
    assert v["verdict"] == "confirmed"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_verifier.py -v`
Expected: FAIL — no `parse_verifier_verdict`.

- [ ] **Step 3: Implement `parse_verifier_verdict`**

Add to `agent/v1/orchestrator.py`:

```python
def parse_verifier_verdict(text: str) -> dict:
    """Parse a Verifier worker's prove-or-refute output.
    Inconclusive defaults to 'confirmed' so verification never blocks a pipeline
    that already has a grounded answer."""
    t = text or ""
    if re.search(r'\bREFUTED\b', t, re.IGNORECASE):
        cm = re.search(r'CORRECTION:\s*(.+)', t, re.IGNORECASE)
        return {"verdict": "refuted",
                "correction": (cm.group(1).strip().split('\n')[0].strip() if cm else "")}
    return {"verdict": "confirmed", "correction": ""}
```

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v1/tests/test_verifier.py -v`
Expected: 3 passed.

- [ ] **Step 5: Add the verifier node (gated on points)**

Add a `verifier_node` to the SH graph that runs only when `ctx.current_points >= 500` and `state["done"]` with a grounded `final_answer`. It dispatches ONE Senior worker with a prove-or-refute subquestion built from `{question, final_answer, evidence SPL}`, parses the verdict; on `refuted` with a correction that is itself grounded, replace `final_answer`; on `refuted` without a usable correction and rounds remaining, set `needs_replan`. Wire it between `joiner`(done) and `END`:

```python
    def route_joiner(state):
        if state.get("needs_replan"):
            return "planner"
        if state.get("done"):
            return "verifier" if _should_verify(ctx) else END
        if state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):
            return "executor"
        return END
```

with `_should_verify(ctx)` returning `ctx.current_points >= 500`. Add the node, its prompt (a `VERIFIER_SYSTEM_PROMPT` instructing prove-or-refute with ≤3 queries, ending in `CONFIRMED: <value>` or `REFUTED. CORRECTION: <value>`), and edges `verifier -> END` (or `-> planner` when it sets `needs_replan`). Keep the verifier's worker call on the existing pool (`ctx.pool.run_senior`) with a distinct `run_name` like `Verifier-<qid>`. Guard the recursion_limit (raise it in `run_sh` config since a verify pass adds nodes).

**Note for implementer:** if wiring the node into the graph proves to require broad changes to `SHState`/routing that risk the existing tests, STOP and report DONE_WITH_CONCERNS with what you built (the pure parser + prompt) so the controller can decide whether to land the node now or defer it to a full-run tuning cycle. The pure parser + prompt are valuable even if the node lands separately.

- [ ] **Step 6: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -v`
Expected: all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import orchestrator; print('ok')"`
Expected: `ok`.

- [ ] **Step 7: Cheap smoke run on a reasoning-error question**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q212`
Expected: completes; report whether a `Verifier-Q212` worker ran (it's a 100-pt question — actually Q212 is 100pt so it WON'T verify; pick a ≥500 reasoning question instead: use Q210 (500pt)). Run `--ids Q210` and report whether the verifier ran and the final answer.

- [ ] **Step 8: Commit**

```bash
git add agent/v1/orchestrator.py agent/v1/tests/test_verifier.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2): verifier node (prove-or-refute) for >=500pt questions"
```

---

## Done criteria

- `python -m pytest agent/v1/tests/ -v` all green.
- Each behavior change has a cheap `--ids` smoke run recorded (submitted answer + grounded flag from `metrics.json`), NOT a full run.
- No change to the scoring/submit path.
- `docs/version_architecture/v1/v1.2.md` changelog updated per task.
- Whole-implementation review after Task 7 focuses on the joiner-routing seams (grounding replan vs verifier vs normal replan must not deadlock or skip END) and the points-threading path.
