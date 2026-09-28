# Premise Ledger Implementation Plan (spec 1, v0.5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the senior's prose `## Assumptions` section, and every regex that reads it, with one runner-owned structured premise ledger that a senior cannot drop a premise from.

**Architecture:** A new `agent/v0/premise.py` owns the models, the ledger, the status transitions and the rendering. The senior emits only *new premises* and *id-keyed updates* through `submit_finding` — never the list — so omission cannot remove a premise. A status moving to VERIFIED or REFUTED requires a quote that the runner finds in a tool result the author actually received. SH's `premise_audit` folds into the same ledger as `author="sh"`. `AuditLine` and the whole regex layer in `senior_report.py` are deleted.

**Tech Stack:** Python 3, pydantic v2, pytest. No new dependencies. Tests live in `agent/v0/tests/` and import modules bare (`from premise import ...`) because `conftest.py` puts `agent/` and `agent/v0/` on `sys.path`.

**Spec:** `docs/superpowers/specs/2026-09-20-premise-ledger-design.md`

**Baseline before starting:** `pytest agent/v0/tests/ -q` → 498 passed, 5 skipped.

---

## File Structure

| File | Responsibility |
|---|---|
| `agent/v0/premise.py` | **new.** Models (`PremiseDraft`, `PremiseUpdate`, `Premise`, `OpenQuestion`), the `PremiseLedger`, transition rules, the tool-output quote check, all rendering, and the `premise_ledger.json` dump. Owns `_norm` and `MIN_QUOTE_CHARS`, which move here from `conversation.py` so `conversation.py` can import from `premise.py` without a cycle |
| `agent/v0/finding.py` | `submit_finding` gains `new_premises`, `premise_updates`, `open_questions`; `parse_finding` extracts them. Accepts either a real list or a JSON string, so Task 0's outcome changes one type annotation and nothing else |
| `agent/v0/senior_session.py` | Accumulates the per-senior tool-output corpus across rounds; applies the round's updates to the ledger; injects the carry-forward block into the next round's message |
| `agent/v0/conversation.py` | `AuditLine` deleted. `SeniorDirective` gains `new_premises`, `premise_updates`, `answer_premise_ids`. Gates read the ledger |
| `agent/v0/sh_loop.py` | Owns one `PremiseLedger` per question; wires it through the wave; `render_wave` prints the table; the `doubts` dict is deleted; prompt updated |
| `agent/v0/senior_report.py` | Regex layer deleted; open questions leave the report entirely |

**Build order:** new code first (Tasks 1–7), swap the callers over (Tasks 8–9), delete the old layer last (Task 10). The suite stays green at every commit except where a task explicitly says otherwise.

---

## Task 0: Probe — can GLM-5.3 fill a nested tool parameter?

**This is a decision gate, not code.** Spec §5: `submit_finding` takes flat primitives today. If GLM-5.3 on AI& cannot fill a `list[object]` parameter, the whole shape changes. Find out before writing anything.

**Files:**
- Create: `<scratchpad>/probe_nested_tool.py` (scratchpad, not the repo — this is a one-off)

- [ ] **Step 1: Write the probe**

```python
"""One-off: does GLM-5.3 on AI& fill a list-of-objects tool parameter?"""
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv(os.path.join("agent", ".env"))


@tool
def submit_probe(summary: str, new_premises: list[dict], open_questions: list[str]) -> str:
    """Report findings.

    - summary: one sentence.
    - new_premises: list of objects, each {"text": str, "kind": str, "load_bearing": bool}.
    - open_questions: list of plain strings.
    """
    return "ok"


llm = ChatOpenAI(model="glm-5.3", base_url="https://api.aiand.com/v1",
                 api_key=os.environ["AI_AND_API_KEY"], temperature=0)
msg = llm.bind_tools([submit_probe]).invoke(
    "Call submit_probe. summary: 'chrome.exe reached 45.77.53.176 on port 3333'. "
    "Record two premises: that the flow is inbound-heavy (load-bearing, kind 'other'), "
    "and that port 3333 alone does not prove the activity (not load-bearing, kind "
    "'definition'). Ask one open question: which feed owns the byte counts.")

calls = getattr(msg, "tool_calls", None) or []
print("tool_calls:", len(calls))
for c in calls:
    print("args:", c["args"])
    np = c["args"].get("new_premises")
    print("new_premises type:", type(np).__name__)
    if isinstance(np, list) and np and isinstance(np[0], dict):
        print("VERDICT: nested objects OK")
    elif isinstance(np, str):
        print("VERDICT: returned as STRING - use the JSON-string fallback")
    else:
        print("VERDICT: unusable -", repr(np)[:200])
```

- [ ] **Step 2: Run it**

Run: `python <scratchpad>/probe_nested_tool.py`

Expected: one of the three VERDICT lines. Cost is a single short completion.

- [ ] **Step 3: Record the outcome**

Append to `docs/version_architecture/v0/v0.5.md` under `## Changelog` (create the file with that heading if absent):

```markdown
- Probed GLM-5.3 on AI& for nested tool arguments (2026-09-20): a `list[dict]` parameter
  came back as <OBSERVED RESULT>. `submit_finding` therefore types `new_premises` and
  `premise_updates` as <list | str parsed by the runner>.
```

- [ ] **Step 4: Commit the record**

```bash
git add docs/version_architecture/v0/v0.5.md
git commit -m "docs(v0.5): record the GLM-5.3 nested-tool-argument probe

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

**Effect on the rest of the plan:** none, except one type annotation in Task 6. `_coerce_objects()` there accepts a list *or* a JSON string either way, so both outcomes run the same code path.

---

## Task 1: `premise.py` — the models

**Files:**
- Create: `agent/v0/premise.py`
- Test: `agent/v0/tests/test_premise.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from premise import MIN_QUOTE_CHARS, Premise, PremiseDraft, PremiseUpdate, _norm
from pydantic import ValidationError


def test_a_draft_carries_only_what_the_senior_decides():
    d = PremiseDraft(text="The 3333 flow is inbound-heavy", kind="other",
                     load_bearing=True)
    assert d.load_bearing and d.kind == "other"


def test_a_draft_rejects_a_kind_outside_the_four():
    with pytest.raises(ValidationError):
        PremiseDraft(text="x", kind="guesswork", load_bearing=False)


def test_an_update_rejects_a_status_outside_the_three():
    with pytest.raises(ValidationError):
        PremiseUpdate(id="p1", status="PROBABLY", quote="", evidence="")


def test_a_premise_starts_unverified_with_nothing_behind_it():
    p = Premise(id="p1", author="s1", kind="coverage", text="Mining could surface as...",
                load_bearing=True, round_first_seen=1)
    assert p.status == "UNVERIFIED" and p.verified_by == "" and p.quote == ""


def test_norm_ignores_markdown_case_and_whitespace():
    assert _norm("  **ibc=5782875**\n obc=177 ") == _norm("ibc=5782875 obc=177")


def test_min_quote_chars_is_defined_here_now():
    assert MIN_QUOTE_CHARS == 12
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'premise'`

- [ ] **Step 3: Write the module**

```python
#!/usr/bin/env python3
"""
The premise ledger (spec 1, v0.5).

A senior's premises used to live in its report's "## Assumptions" section as
prose, read by five regexes. v0.4.2's Q216 was lost to that: s1 flagged the 3333
flow's byte profile as download-like and UNVERIFIED in rounds 1 and 2, SH
commanded a restate-only round, and round 3 came back all-VERIFIED with the line
simply gone. A regex cannot tell a premise that was settled from one that was
dropped, and `carry_doubts`/`_label` matched premises by their first four words.

So the RUNNER owns the list. The senior emits new premises and id-keyed updates
and never the list itself, which makes dropping one structurally impossible
rather than merely discouraged, and makes the premise text immutable once filed.

A status only reaches VERIFIED or REFUTED with a quote the runner finds in a
tool result the author actually received (`quote_supported`) - the senior-side
equivalent of the rule that stops SH citing itself.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field

STATUSES = ("UNVERIFIED", "VERIFIED", "REFUTED")
KINDS = ("coverage", "selection", "definition", "other")

# Shorter than this and a "quote" matches almost any text. Moved here from
# conversation.py so conversation can import from premise without a cycle.
MIN_QUOTE_CHARS = 12


def _norm(text: str) -> str:
    """Whitespace-, case- and markdown-insensitive form, so a faithful quote matches."""
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", text or "")).strip().lower()


class PremiseDraft(BaseModel):
    """A premise as its author files it. No id and no status: both are the runner's."""

    text: str = Field(description="The premise, in one sentence. Immutable once filed.")
    kind: Literal["coverage", "selection", "definition", "other"] = Field(
        description="'coverage': the ways the question's concept could show up in the "
                    "data. 'selection': why this entity and not another candidate. "
                    "'definition': what the question's words mean for the measurement. "
                    "'other': anything else your conclusion or next step rests on.")
    load_bearing: bool = Field(
        description="True when the answer breaks if this premise is false. Be honest: "
                    "marking everything load-bearing is the same as marking nothing.")


class PremiseUpdate(BaseModel):
    """A settled (or unsettled) verdict on a premise already in the ledger."""

    id: str = Field(description="The premise id, e.g. 'p3'. Copy it exactly.")
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"] = Field(
        description="VERIFIED: a result you ran shows it holds. REFUTED: a result you "
                    "ran shows it is false. UNVERIFIED: you are withdrawing a previous "
                    "verdict.")
    quote: str = Field(description="VERIFIED/REFUTED: the query output that settles it, "
                                   "copied word for word. The runner checks it against "
                                   "results you actually received.")
    evidence: str = Field(description="Why that quote settles it. For UNVERIFIED, what "
                                      "would test it.")


class Premise(BaseModel):
    """One premise in the ledger. `text` never changes after it is filed."""

    id: str
    author: str
    kind: Literal["coverage", "selection", "definition", "other"]
    text: str
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"] = "UNVERIFIED"
    load_bearing: bool = False
    round_first_seen: int = 0
    verified_by: str = ""
    quote: str = ""
    evidence: str = ""
    history: list[dict] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    """A senior's question for SH, addressable by id so an answer cannot be miscounted."""

    id: str
    author: str
    text: str
    answer: str = ""
    round_asked: int = 0
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add agent/v0/premise.py agent/v0/tests/test_premise.py
git commit -m "feat(v0.5): premise ledger models

PremiseDraft (what an author files), PremiseUpdate (an id-keyed verdict),
Premise (the ledger entry, text immutable) and OpenQuestion. _norm and
MIN_QUOTE_CHARS move here from conversation.py so conversation can import
premise without a cycle.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 2: `premise.py` — the ledger holds and carries premises

**Files:**
- Modify: `agent/v0/premise.py` (append `PremiseLedger`)
- Test: `agent/v0/tests/test_premise.py` (append)

- [ ] **Step 1: Write the failing test**

```python
from premise import PremiseLedger


def _draft(text, kind="other", lb=True):
    return PremiseDraft(text=text, kind=kind, load_bearing=lb)


def test_the_runner_assigns_ids_the_author_never_picks_one():
    led = PremiseLedger()
    added = led.add([_draft("a"), _draft("b")], author="s1", round_n=1)
    assert [p.id for p in added] == ["p1", "p2"]


def test_ids_keep_counting_across_authors_and_rounds():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    added = led.add([_draft("b")], author="s2", round_n=1)
    assert added[0].id == "p2"


def test_a_premise_the_senior_stops_mentioning_is_still_there():
    """The Q216 bug: s1 filed the byte-profile premise in round 1, wrote a cleaner
    report in round 3, and the doubt vanished. It cannot vanish now."""
    led = PremiseLedger()
    led.add([_draft("The 3333 flow's byte profile is download-like")],
            author="s1", round_n=1)
    led.add([_draft("chrome.exe is the process")], author="s1", round_n=3)
    open_ids = [p.id for p in led.unresolved_for("s1")]
    assert "p1" in open_ids


def test_unresolved_is_per_author():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    led.add([_draft("b")], author="s2", round_n=1)
    assert [p.id for p in led.unresolved_for("s2")] == ["p2"]


def test_load_bearing_open_premises_are_the_ones_that_block():
    led = PremiseLedger()
    led.add([_draft("heavy", lb=True), _draft("light", lb=False)],
            author="s1", round_n=1)
    assert [p.id for p in led.blocking()] == ["p1"]


def test_a_candidate_is_recorded_per_round_for_later_calibration():
    led = PremiseLedger()
    led.record_candidate("s1", 1, "112")
    led.record_candidate("s1", 2, "112")
    assert led.candidates["s1"] == {1: "112", 2: "112"}
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: FAIL — `ImportError: cannot import name 'PremiseLedger'`

- [ ] **Step 3: Append the ledger to `agent/v0/premise.py`**

```python
class PremiseLedger:
    """Every premise on one question, for every author. One instance per question.

    Ids are global to the question, not per senior: cross-author verification is
    allowed (a sibling senior may settle a premise another filed), so an id has
    to mean the same thing to everyone reading it.
    """

    def __init__(self):
        self.premises: dict[str, Premise] = {}
        self.questions: dict[str, OpenQuestion] = {}
        self.candidates: dict[str, dict[int, str]] = {}   # author -> round -> value
        self._n = 0
        self._qn = 0

    # -- filing ---------------------------------------------------------------
    def add(self, drafts: list, author: str, round_n: int) -> list[Premise]:
        """File new premises. The runner assigns ids and stamps the round."""
        out = []
        for d in drafts or []:
            self._n += 1
            p = Premise(id=f"p{self._n}", author=author, kind=d.kind, text=d.text,
                        load_bearing=bool(d.load_bearing), round_first_seen=round_n,
                        history=[{"round": round_n, "status": "UNVERIFIED",
                                  "by": author, "quote": ""}])
            self.premises[p.id] = p
            out.append(p)
        return out

    def ask(self, texts: list, author: str, round_n: int) -> list[OpenQuestion]:
        """File a senior's open questions, each addressable by id."""
        out = []
        for t in texts or []:
            if not str(t).strip():
                continue
            self._qn += 1
            q = OpenQuestion(id=f"q{self._qn}", author=author, text=str(t).strip(),
                             round_asked=round_n)
            self.questions[q.id] = q
            out.append(q)
        return out

    def record_candidate(self, author: str, round_n: int, value: str) -> None:
        """What this author's candidate was at this round.

        Spec 2's trigger is "load-bearing premise unverified for N rounds AND the
        candidate unchanged", which is unrecoverable from the reports afterwards.
        Recorded here so the ledger dump can answer it.
        """
        self.candidates.setdefault(author, {})[round_n] = value or ""

    # -- reading --------------------------------------------------------------
    def unresolved_for(self, author: str) -> list[Premise]:
        """This author's premises that are not VERIFIED, oldest first."""
        return [p for p in self.premises.values()
                if p.author == author and p.status != "VERIFIED"]

    def blocking(self) -> list[Premise]:
        """Load-bearing premises that are not VERIFIED - the ones that gate an ANSWER."""
        return [p for p in self.premises.values()
                if p.load_bearing and p.status != "VERIFIED"]

    def refuted(self) -> list[Premise]:
        return [p for p in self.premises.values() if p.status == "REFUTED"]

    def open_questions_for(self, author: str) -> list[OpenQuestion]:
        return [q for q in self.questions.values()
                if q.author == author and not q.answer.strip()]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add agent/v0/premise.py agent/v0/tests/test_premise.py
git commit -m "feat(v0.5): PremiseLedger holds and carries premises

Ids are global to the question because cross-author verification is allowed.
record_candidate() captures the per-round candidate, which spec 2's trigger
needs and which the reports cannot recover afterwards.

The test that matters: a premise the senior stops mentioning is still in
unresolved_for() - the Q216 bug, now impossible by construction.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 3: `premise.py` — transitions and the tool-output quote check

**Files:**
- Modify: `agent/v0/premise.py`
- Test: `agent/v0/tests/test_premise.py` (append)

- [ ] **Step 1: Write the failing test**

```python
from premise import PremiseUpdate, quote_supported

CORPUS = ["sourcetype=cisco:nvm | 1 result: ibc=5782875 obc=177 dest_port=3333"]


def _upd(pid, status, quote="", evidence="because"):
    return PremiseUpdate(id=pid, status=status, quote=quote, evidence=evidence)


def _led():
    led = PremiseLedger()
    led.add([_draft("The 3333 flow is submission, not download")],
            author="s1", round_n=1)
    return led


def test_quote_supported_matches_across_markdown_and_whitespace():
    assert quote_supported("**ibc=5782875**   obc=177", CORPUS)


def test_quote_supported_rejects_a_quote_nobody_received():
    assert not quote_supported("obc=5782875 ibc=177", CORPUS)


def test_quote_supported_rejects_a_quote_too_short_to_mean_anything():
    assert not quote_supported("ibc=57", CORPUS)


def test_verified_needs_a_quote_from_a_result_the_author_received():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert notes == [] and led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].verified_by == "s1"


def test_verified_without_a_real_quote_is_dropped_and_reported():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "the flow is clearly mining traffic")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert len(notes) == 1 and "p1" in notes[0]


def test_refuted_is_terminal():
    led = _led()
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=3)
    assert led.premises["p1"].status == "REFUTED"
    assert len(notes) == 1 and "REFUTED" in notes[0]


def test_withdrawing_a_verdict_needs_no_quote():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    notes = led.apply([_upd("p1", "UNVERIFIED", "")], author="s1",
                      corpus=CORPUS, round_n=3)
    assert notes == [] and led.premises["p1"].status == "UNVERIFIED"


def test_a_sibling_senior_may_settle_another_seniors_premise():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s2", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].verified_by == "s2"
    assert led.premises["p1"].author == "s1"


def test_an_update_naming_an_unknown_id_is_reported_not_crashed():
    led = _led()
    notes = led.apply([_upd("p99", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert len(notes) == 1 and "p99" in notes[0]


def test_every_transition_is_recorded_in_history():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED", "VERIFIED"]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: FAIL — `ImportError: cannot import name 'quote_supported'`

- [ ] **Step 3: Append `quote_supported` to `agent/v0/premise.py`**

Place it above `class PremiseLedger`:

```python
def quote_supported(quote: str, corpus: list) -> bool:
    """Does this quote appear, word for word, in something the author actually received?

    The senior-side equivalent of the rule that stops SH citing its own instruction
    as evidence. Without it a senior can assert VERIFIED with nothing behind it and
    only SH's judgement stands between that and an answer - which is what happened
    on Q216.
    """
    q = _norm(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return False
    return any(q in _norm(chunk) for chunk in corpus or [])
```

- [ ] **Step 4: Add `apply` and `answer` to `PremiseLedger`**

```python
    def apply(self, updates: list, author: str, corpus: list, round_n: int) -> list[str]:
        """Apply this round's verdicts. Returns a note per REJECTED update.

        A senior round cannot be rejected mid-flight the way an SH turn can, so a
        bad update is dropped rather than raised: the premise keeps its old status
        and the note goes into the report SH reads. The effect on the gates is the
        same as if the update had never been sent.
        """
        notes = []
        for u in updates or []:
            p = self.premises.get(u.id)
            if p is None:
                notes.append(f"update ignored: {u.id} is not a premise on this question")
                continue
            if p.status == "REFUTED":
                notes.append(f"update ignored: {u.id} is REFUTED, which is final")
                continue
            if u.status in ("VERIFIED", "REFUTED") and not quote_supported(u.quote, corpus):
                notes.append(
                    f"{u.id} stays {p.status}: its quote is in no result you ran - "
                    "copy the query output that shows it word for word")
                continue
            p.status = u.status
            p.evidence = u.evidence
            if u.status == "UNVERIFIED":
                p.verified_by, p.quote = "", ""
            else:
                p.verified_by, p.quote = author, u.quote
            p.history.append({"round": round_n, "status": u.status,
                              "by": author, "quote": u.quote})
        return notes

    def answer(self, question_id: str, text: str) -> bool:
        """Record SH's answer to one open question. False when the id is unknown."""
        q = self.questions.get(question_id)
        if q is None:
            return False
        q.answer = text
        return True
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: 22 passed

- [ ] **Step 6: Commit**

```bash
git add agent/v0/premise.py agent/v0/tests/test_premise.py
git commit -m "feat(v0.5): premise transitions and the tool-output quote check

VERIFIED and REFUTED require a quote the runner finds in a result the author
actually received. REFUTED is terminal. Withdrawing a verdict needs no quote -
a senior finding a problem with its own premise is the honest path.

A bad update is dropped with a note rather than raised: a senior round cannot
be rejected mid-flight, and the gate outcome is identical either way.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 4: `premise.py` — rendering for the senior and for SH

**Files:**
- Modify: `agent/v0/premise.py`
- Test: `agent/v0/tests/test_premise.py` (append)

- [ ] **Step 1: Write the failing test**

```python
def test_the_carry_forward_block_quotes_the_premise_word_for_word():
    led = PremiseLedger()
    text = "The 3333 record's byte profile (5.7MB in / 177B out) is download-like"
    led.add([_draft(text)], author="s1", round_n=1)
    block = led.render_for_senior("s1")
    assert text in block and "[p1]" in block and "open since round 1" in block


def test_the_carry_forward_block_is_empty_when_nothing_is_open():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    assert led.render_for_senior("s1") == ""


def test_a_senior_is_not_handed_another_seniors_premises():
    led = PremiseLedger()
    led.add([_draft("s1 only")], author="s1", round_n=1)
    assert led.render_for_senior("s2") == ""


def test_the_sh_table_shows_status_load_bearing_and_who_settled_it():
    led = PremiseLedger()
    led.add([_draft("mining could surface as stratum", kind="coverage")],
            author="s1", round_n=1)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s2", corpus=CORPUS, round_n=2)
    table = led.render_table()
    assert "p1" in table and "coverage" in table and "VERIFIED" in table and "s2" in table


def test_the_sh_table_says_so_when_there_are_no_premises():
    assert "no premises" in PremiseLedger().render_table().lower()


def test_the_refuted_block_carries_the_evidence_that_killed_it():
    led = PremiseLedger()
    led.add([_draft("the flow is submission")], author="s1", round_n=1)
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177",
                    evidence="inbound bytes dwarf outbound")],
              author="s2", corpus=CORPUS, round_n=2)
    block = led.render_refuted()
    assert "the flow is submission" in block and "ibc=5782875" in block
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: FAIL — `AttributeError: 'PremiseLedger' object has no attribute 'render_for_senior'`

- [ ] **Step 3: Append the renderers to `PremiseLedger`**

```python
    # -- rendering ------------------------------------------------------------
    def render_for_senior(self, author: str) -> str:
        """The unresolved premises this author owns, verbatim, for its next round.

        Carried by the runner unconditionally. The v0.4.2 equivalent fired only
        when SH graded R4 WEAK or FAIL - and SH grades all-PASS when it wants to
        answer. The runner has no candidate and no preference.
        """
        open_ = self.unresolved_for(author)
        if not open_:
            return ""
        lines = ["YOUR UNRESOLVED PREMISES - carried forward by the runner, "
                 "in your own words:"]
        for p in open_:
            tag = "load-bearing, " if p.load_bearing else ""
            state = ", REFUTED" if p.status == "REFUTED" else ""
            lines.append(f'[{p.id}] {tag}open since round {p.round_first_seen}'
                         f'{state} - "{p.text}"')
        lines.append("\nSettle each with `premise_updates`: a status, and a quote from "
                     "a result you actually ran. Not mentioning one does not remove it.")
        return "\n".join(lines)

    def render_table(self) -> str:
        """The whole ledger, for SH. Replaces the three '!!' warning blocks - a
        missing Coverage row is visible as absence."""
        if not self.premises:
            return "PREMISE LEDGER - no premises filed yet."
        rows = ["PREMISE LEDGER",
                f"{'id':<4} {'kind':<11} {'status':<11} {'LB':<3} {'since':<6} text"]
        for p in self.premises.values():
            by = f"  [{p.verified_by}]" if p.verified_by else ""
            rows.append(f"{p.id:<4} {p.kind:<11} {p.status:<11} "
                        f"{'Y' if p.load_bearing else 'n':<3} r{p.round_first_seen:<5} "
                        f"{p.author}: {p.text[:70]}{by}")
        return "\n".join(rows)

    def render_refuted(self) -> str:
        """What a replacement senior must not rebuild on. Empty when nothing is refuted.

        ponytail: no caller until spec 2's alternative-agent brief. Four lines, and
        the ledger already holds everything it needs - delete it if spec 2 slips.
        """
        dead = self.refuted()
        if not dead:
            return ""
        lines = ["PREMISES ALREADY DISPROVEN - do not rebuild on these:"]
        for p in dead:
            lines.append(f'[{p.id}] REFUTED by {p.verified_by} - "{p.text}"')
            lines.append(f'     disproven by: {p.quote}')
        lines.append("\nA line of reasoning that needs one of these to be true is "
                     "already known wrong.")
        return "\n".join(lines)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: 28 passed

- [ ] **Step 5: Commit**

```bash
git add agent/v0/premise.py agent/v0/tests/test_premise.py
git commit -m "feat(v0.5): ledger rendering for the senior, for SH, and for a replacement

render_for_senior() is the carry-forward block, emitted unconditionally rather
than on SH's R4 grade. render_table() replaces the three '!!' warning blocks in
render_wave. render_refuted() is spec 2's AA brief, built now because the
ledger already holds everything it needs.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 5: `premise.py` — the `premise_ledger.json` dump

Spec §7: the Q216 run must emit each premise's full status history plus the per-round candidate. Spec 2 §8 calibrates five parameters from this file and says to re-run rather than estimate if it is absent.

**Files:**
- Modify: `agent/v0/premise.py`
- Test: `agent/v0/tests/test_premise.py` (append)

- [ ] **Step 1: Write the failing test**

```python
import json


def test_the_dump_carries_history_and_the_per_round_candidate():
    led = PremiseLedger()
    led.add([_draft("The 3333 flow is submission")], author="s1", round_n=1)
    led.record_candidate("s1", 1, "112")
    led.record_candidate("s1", 2, "112")
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)

    rec = led.to_records("216")[0]
    assert rec["qid"] == "216" and rec["id"] == "p1" and rec["load_bearing"] is True
    assert [h["status"] for h in rec["history"]] == ["UNVERIFIED", "REFUTED"]
    assert rec["candidate_at_each_round"] == {"1": "112", "2": "112"}
    json.dumps(rec)   # must be serialisable


def test_the_dump_is_empty_for_an_empty_ledger():
    assert PremiseLedger().to_records("216") == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: FAIL — `AttributeError: 'PremiseLedger' object has no attribute 'to_records'`

- [ ] **Step 3: Append `to_records` to `PremiseLedger`, and `dump_ledgers` at module level**

```python
    def to_records(self, qid: str) -> list[dict]:
        """One JSON-serialisable record per premise, for `premise_ledger.json`.

        The HISTORY is the point, not the end state. Spec 2's validation-agent
        trigger is "load-bearing, UNVERIFIED for N rounds, candidate unchanged" -
        a report shows only where a premise finished, so without this the single
        reading that decides whether that trigger is aimed correctly is lost.
        """
        return [{
            "qid": qid,
            "senior": p.author,
            "id": p.id,
            "kind": p.kind,
            "text": p.text,
            "load_bearing": p.load_bearing,
            "round_first_seen": p.round_first_seen,
            "status": p.status,
            "verified_by": p.verified_by,
            "history": list(p.history),
            "candidate_at_each_round": {str(r): v for r, v
                                        in sorted(self.candidates
                                                  .get(p.author, {}).items())},
        } for p in self.premises.values()]
```

At module level, after the class:

```python
def dump_ledgers(path: str, ledgers: dict) -> None:
    """Write every question's ledger to one file. `ledgers` maps qid -> PremiseLedger."""
    records = [r for qid, led in ledgers.items() for r in led.to_records(qid)]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest agent/v0/tests/test_premise.py -q`
Expected: 30 passed

- [ ] **Step 5: Commit**

```bash
git add agent/v0/premise.py agent/v0/tests/test_premise.py
git commit -m "feat(v0.5): premise_ledger.json dump with history and per-round candidate

Spec 1 S7. The history is what spec 2 S8 calibrates against: its trigger asks
how long a premise sat UNVERIFIED while the candidate held still, which a
report's end state cannot answer.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 6: `finding.py` — the senior emits drafts, updates and questions

**Files:**
- Modify: `agent/v0/finding.py` — imports (28-30), `submit_finding` (85-133), `_split` area (136-137), `empty_finding` (174-189), `parse_finding` return (259-274)
- Test: `agent/v0/tests/test_finding_premises.py` (new)

- [ ] **Step 1: Write the failing test**

```python
from finding import empty_finding, parse_finding


class _Call:
    """A message carrying one submit_finding tool call, as parse_finding scans for."""

    def __init__(self, args):
        self.tool_calls = [{"name": "submit_finding", "args": args}]


def _parse(**args):
    return parse_finding([_Call({"insight": "FOUND", "value": "112", **args})], "")


def test_premise_drafts_come_back_as_objects():
    f = _parse(new_premises=[{"text": "the flow is inbound-heavy", "kind": "other",
                              "load_bearing": True}])
    assert f["new_premises"][0].text == "the flow is inbound-heavy"
    assert f["new_premises"][0].load_bearing is True


def test_premise_drafts_survive_arriving_as_a_json_string():
    """Some providers flatten a list[object] tool argument to a string (Task 0)."""
    f = _parse(new_premises='[{"text": "the flow is inbound-heavy", '
                            '"kind": "other", "load_bearing": true}]')
    assert f["new_premises"][0].kind == "other"


def test_a_draft_missing_a_field_gets_a_safe_default_not_a_crash():
    f = _parse(new_premises=[{"text": "no kind given"}])
    assert f["new_premises"][0].kind == "other"
    assert f["new_premises"][0].load_bearing is False


def test_a_malformed_draft_is_dropped_not_fatal():
    f = _parse(new_premises=[{"kind": "other"}, "just a string",
                             {"text": "kept", "kind": "other", "load_bearing": False}])
    assert [p.text for p in f["new_premises"]] == ["just a string", "kept"]


def test_updates_come_back_as_objects():
    f = _parse(premise_updates=[{"id": "p1", "status": "VERIFIED",
                                 "quote": "ibc=5782875", "evidence": "why"}])
    assert f["premise_updates"][0].id == "p1"
    assert f["premise_updates"][0].status == "VERIFIED"


def test_an_update_with_an_illegal_status_is_dropped():
    f = _parse(premise_updates=[{"id": "p1", "status": "MAYBE", "quote": "x",
                                 "evidence": "y"}])
    assert f["premise_updates"] == []


def test_open_questions_come_back_as_plain_strings():
    f = _parse(open_questions=["which feed owns the byte counts?", "  ", "and this?"])
    assert f["open_questions"] == ["which feed owns the byte counts?", "and this?"]


def test_a_finding_with_no_premise_fields_is_still_valid():
    f = _parse()
    assert f["new_premises"] == [] and f["premise_updates"] == []
    assert f["open_questions"] == []


def test_empty_finding_carries_the_new_keys():
    e = empty_finding("failed")
    assert e["new_premises"] == [] and e["premise_updates"] == []
    assert e["open_questions"] == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_finding_premises.py -q`
Expected: FAIL — `KeyError: 'new_premises'`

- [ ] **Step 3: Update the imports**

Replace `finding.py`'s import block (lines 28-30) with:

```python
import json
import re

from langchain_core.tools import tool
from premise import KINDS, PremiseDraft, PremiseUpdate
from pydantic import ValidationError
```

- [ ] **Step 4: Add the coercion helpers after `_split` (line 137)**

```python
def _coerce_objects(value) -> list:
    """A list of dicts (or strings) from whatever the provider actually sent.

    Task 0 probed GLM-5.3 on AI& for nested tool arguments. This accepts a real
    list OR a JSON string either way, so the probe's outcome changes one type
    annotation on the tool and no logic at all - and a provider that changes its
    mind later costs nothing.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    if isinstance(value, dict):
        value = [value]
    return [v for v in (value or []) if isinstance(v, (dict, str))]


def _drafts(value) -> list:
    """PremiseDrafts from the tool's `new_premises`. A malformed one is dropped, not
    fatal: a round that filed four good premises and one bad is worth four."""
    out = []
    for d in _coerce_objects(value):
        if isinstance(d, str):
            d = {"text": d}
        text = str(d.get("text", "")).strip()
        if not text:
            continue
        kind = str(d.get("kind", "") or "other").strip().lower()
        try:
            out.append(PremiseDraft(text=text,
                                    kind=kind if kind in KINDS else "other",
                                    load_bearing=bool(d.get("load_bearing", False))))
        except ValidationError:
            continue
    return out


def _updates(value) -> list:
    """PremiseUpdates from the tool's `premise_updates`. An illegal status is dropped -
    the premise then keeps its old status, which is the safe direction."""
    out = []
    for u in _coerce_objects(value):
        if not isinstance(u, dict):
            continue
        try:
            out.append(PremiseUpdate(id=str(u.get("id", "")).strip(),
                                     status=str(u.get("status", "")).strip().upper(),
                                     quote=str(u.get("quote", "") or ""),
                                     evidence=str(u.get("evidence", "") or "")))
        except ValidationError:
            continue
    return out
```

- [ ] **Step 5: Extend the `submit_finding` tool**

Replace the signature (lines 86-90) with:

```python
@tool
def submit_finding(insight: str, value: str = "", value_kind: str = "",
                   evidence: str = "", confidence: int = 50,
                   sourcetypes_used: str = "", sources_used: str = "",
                   ruled_out: str = "", notes: str = "",
                   report: str = "", new_premises: list = None,
                   premise_updates: list = None,
                   open_questions: list = None) -> str:
```

> **Task 0 applies here and nowhere else.** If the probe said nested objects work,
> leave `new_premises: list` and `premise_updates: list` as written. If it said the
> provider flattens them to a string, change those two annotations to `str` and say
> so in the docstring. `_coerce_objects` handles both without another change.

Insert into the docstring, after the `notes:` bullet and before `report:`:

```
    - new_premises: the premises you are filing THIS round, each an object
      {"text": ..., "kind": "coverage"|"selection"|"definition"|"other",
       "load_bearing": true|false}. Do NOT re-send premises you filed earlier -
      the runner holds them and shows them back to you every round. `text` is
      immutable once filed, so write it as you want it read in five rounds' time.
      `load_bearing` is true only when the answer breaks if this premise is false;
      marking everything load-bearing is the same as marking nothing.
    - premise_updates: verdicts on premises ALREADY in your ledger, each
      {"id": "p3", "status": "VERIFIED"|"REFUTED"|"UNVERIFIED",
       "quote": ..., "evidence": ...}. VERIFIED and REFUTED need a quote copied
      word for word from a query output you actually received - the runner checks
      it and keeps the old status if it is not there. UNVERIFIED withdraws a
      verdict and needs no quote.
    - open_questions: what you need SH to answer, one plain string each. SH must
      answer every one before your next round, so ask only what SH can settle:
      which entity is in scope, whether a prior finding applies, which scope to
      try next. Never an SPL question.
```

- [ ] **Step 6: Extend `empty_finding` and `parse_finding`**

In `empty_finding`'s dict (lines 177-189), add:

```python
        "new_premises":      [],
        "premise_updates":   [],
        "open_questions":    [],
```

In `parse_finding`'s return dict (lines 259-274), add:

```python
        "new_premises":    _drafts(args.get("new_premises")),
        "premise_updates": _updates(args.get("premise_updates")),
        "open_questions":  [str(q).strip() for q in (args.get("open_questions") or [])
                            if str(q).strip()],
```

- [ ] **Step 7: Run the tests**

Run: `pytest agent/v0/tests/test_finding_premises.py agent/v0/tests/test_finding.py agent/v0/tests/test_finding_value_shape.py agent/v0/tests/test_finding_report_fields.py -q`
Expected: all pass, 9 new

- [ ] **Step 8: Commit**

```bash
git add agent/v0/finding.py agent/v0/tests/test_finding_premises.py
git commit -m "feat(v0.5): submit_finding files premise drafts, updates and questions

_coerce_objects accepts a real list or a JSON string, so Task 0's probe outcome
changes one type annotation and no logic. A malformed draft is dropped rather
than fatal: a round that filed four good premises and one bad is worth four.
An illegal status is dropped too, which leaves the premise at its old status -
the safe direction.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 7: `senior_session.py` — corpus, updates, carry-forward

**Files:**
- Modify: `agent/v0/senior_session.py` — after `unseen_rows_note` (line 43), `__init__` (57-99), `work` (101-159), `_message_for` (168-191)
- Test: `agent/v0/tests/test_senior_session_premises.py` (new)

- [ ] **Step 1: Write the failing test**

```python
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from senior_session import SeniorSession, tool_outputs

FULL_STATE = [
    {"type": "HumanMessage", "content": "go"},
    {"type": "ToolMessage", "name": "run_splunk_search",
     "content": "1 result: ibc=5782875 obc=177 dest_port=3333"},
    {"type": "AIMessage", "content": "done"},
]


def test_tool_outputs_picks_only_what_the_tools_returned():
    assert tool_outputs(FULL_STATE) == ["1 result: ibc=5782875 obc=177 dest_port=3333"]


def test_tool_outputs_survives_a_missing_full_state():
    assert tool_outputs(None) == []


class _Pool:
    senior_model = "glm-5.3"

    def __init__(self, result):
        self.result = result
        self.messages = []

    def run_round(self, *, thread_id, message, qid, idx, technique, max_iter):
        self.messages.append(message)
        return dict(self.result)


def _session(pool, ledger):
    return SeniorSession(sid="s1", pool=pool, qid="216", technique="senior",
                         subquestion="find it", brief="BRIEF", window=200_000,
                         rounds_granted=8, idx=1, ledger=ledger)


def _result(**kw):
    base = {"report": "## This round\nx", "status": "ok", "iterations": 3,
            "spl_used": ["search a"], "full_state": FULL_STATE, "value": "112",
            "new_premises": [], "premise_updates": [], "open_questions": []}
    return {**base, **kw}


def test_a_filed_premise_lands_in_the_ledger_with_a_runner_id():
    led = PremiseLedger()
    pool = _Pool(_result(new_premises=[
        PremiseDraft(text="the flow is inbound-heavy", kind="other", load_bearing=True)]))
    _session(pool, led).work("go", rounds_remaining=7)
    assert [p.id for p in led.unresolved_for("s1")] == ["p1"]


def test_the_candidate_is_recorded_for_the_round():
    led = PremiseLedger()
    _session(_Pool(_result(value="112")), led).work("go", rounds_remaining=7)
    assert led.candidates["s1"] == {1: "112"}


def test_the_next_round_carries_the_unresolved_premise_verbatim():
    led = PremiseLedger()
    pool = _Pool(_result(new_premises=[
        PremiseDraft(text="the flow is inbound-heavy", kind="other", load_bearing=True)]))
    sess = _session(pool, led)
    sess.work("round one", rounds_remaining=7)
    pool.result = _result()
    sess.work("round two", rounds_remaining=6)
    assert "the flow is inbound-heavy" in pool.messages[-1]
    assert "[p1]" in pool.messages[-1]


def test_a_rejected_update_is_reported_into_the_report_sh_reads():
    led = PremiseLedger()
    led.add([PremiseDraft(text="a premise", kind="other", load_bearing=True)],
            author="s1", round_n=1)
    pool = _Pool(_result(premise_updates=[
        PremiseUpdate(id="p1", status="VERIFIED", quote="a quote nobody ran ever",
                      evidence="because")]))
    out = _session(pool, led).work("go", rounds_remaining=7)
    assert "p1 stays UNVERIFIED" in out["report"]
    assert led.premises["p1"].status == "UNVERIFIED"


def test_open_questions_are_filed_with_ids():
    led = PremiseLedger()
    _session(_Pool(_result(open_questions=["which feed owns the byte counts?"])),
             led).work("go", rounds_remaining=7)
    assert [q.id for q in led.open_questions_for("s1")] == ["q1"]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_senior_session_premises.py -q`
Expected: FAIL — `ImportError: cannot import name 'tool_outputs'`

- [ ] **Step 3: Add `tool_outputs` after `unseen_rows_note` (line 43)**

```python
def tool_outputs(full_state) -> list:
    """The text every tool returned this round.

    `full_state` is the ROUND's messages, not the thread's (splunk_subagent._run
    slices `all_msgs[before:]`), so the session accumulates these across rounds to
    hold everything this senior has actually seen. That corpus is what a VERIFIED
    premise's quote is checked against.
    """
    return [str(m.get("content") or "") for m in (full_state or [])
            if m.get("type") == "ToolMessage" and str(m.get("content") or "").strip()]
```

- [ ] **Step 4: Thread the ledger through `__init__`**

Add `ledger=None` to the signature (after `iters: int = ROUND_ITERS`), and to the body:

```python
        self.ledger = ledger
        self.tool_corpus: list = []
```

- [ ] **Step 5: Apply the round's ledger writes in `work`**

Immediately after `count, self.prior_spl = novel_spl(...)` (line 123), insert:

```python
        # The ledger: this round's filings, then its verdicts. Order matters - a
        # senior may file a premise and settle it in the same round.
        ledger_notes = []
        if self.ledger is not None:
            self.tool_corpus += tool_outputs(result.get("full_state"))
            self.ledger.add(result.get("new_premises") or [],
                            author=self.sid, round_n=self.rounds_used)
            ledger_notes = self.ledger.apply(result.get("premise_updates") or [],
                                             author=self.sid, corpus=self.tool_corpus,
                                             round_n=self.rounds_used)
            self.ledger.ask(result.get("open_questions") or [],
                            author=self.sid, round_n=self.rounds_used)
            self.ledger.record_candidate(self.sid, self.rounds_used,
                                         result.get("value", ""))
```

After the iteration-cap note is appended to `body` (ends line 137) and before `note = ...`, insert:

```python
        if ledger_notes:
            # The senior claimed a verdict the runner could not support. SH must see
            # it: keeping the old status silently would look like it never tried.
            body = (body.rstrip() + "\n\n_Premise updates refused by the runner:_\n"
                    + "\n".join(f"- {n}" for n in ledger_notes) + "\n")
```

- [ ] **Step 6: Inject the carry-forward block in `_message_for`**

Replace `_message_for` (168-191) with:

```python
    def _message_for(self, directive: str) -> str:
        """The round's input: the brief on round one, a compaction seed when the
        projection says so, otherwise the bare directive - always preceded by the
        premises this senior has left open."""
        carried = (self.ledger.render_for_senior(self.sid)
                   if self.ledger is not None else "")
        head = f"{carried}\n\n" if carried else ""

        if not self.briefed:
            self.briefed = True
            return (f"{self.brief}\n\n## Your task\n{self.subquestion}\n\n"
                    f"{head}## This round\n{directive}")

        if should_compact(self.last_prompt_tokens,
                          mean_per_iter=self.mean_tokens_per_iteration,
                          window=self.window, iters=self.iters):
            mean = self.mean_tokens_per_iteration
            self.thread_id = self._new_thread()
            self.thread_iterations = 0
            self.compactions += 1
            print(f"[{self.sid}] compacting: context {self.last_prompt_tokens:,} + "
                  f"{self.iters}x{mean:,} projected past "
                  f"{int(COMPACT_AT * 100)}% of {self.window:,}")
            spl_section = f"## SPL you already ran - do not repeat, go one step further\n{self._render_spl_list()}\n\n"
            return (f"{self.brief}\n\n## Your task\n{self.subquestion}\n\n"
                    f"## Where you got to (your own last report)\n{self.last_report}\n\n"
                    f"{spl_section}{head}## This round\n{directive}")

        return f"{head}{directive}"
```

- [ ] **Step 7: Run the tests**

Run: `pytest agent/v0/tests/test_senior_session_premises.py agent/v0/tests/test_senior_session.py -q`
Expected: all pass, 7 new

- [ ] **Step 8: Commit**

```bash
git add agent/v0/senior_session.py agent/v0/tests/test_senior_session_premises.py
git commit -m "feat(v0.5): the session carries the ledger through every round

tool_outputs() accumulates what this senior's tools actually returned across
rounds - full_state is per-round, so the corpus has to be built up. That corpus
is what a VERIFIED quote is checked against.

_message_for prepends the unresolved premises to every round unconditionally,
replacing the R4-conditional reminder. A refused update is written into the
report so SH sees the senior tried and failed, rather than nothing at all.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 8: `conversation.py` — gates read the ledger, `AuditLine` goes

**Files:**
- Modify: `agent/v0/conversation.py` — imports (26-28); delete `AuditLine` (58-77), `_norm` (80-82), `MIN_QUOTE_CHARS` (85), `_AUDIT_TEXT` (88), `_audit_from_text` (197-213); rewrite `open_question_answers` (114-119), `premise_audit` (175-182), `premise_audit_violations` (330-346), `unverified_audit` (349-351), `evidence_violations` (381-423), `open_question_violations` (426-439); edit `directive_violations` (513-518)
- Test: `agent/v0/tests/test_conversation_routes.py` (modify)

- [ ] **Step 1: Write the failing test**

Update `BLANK` at the top of `agent/v0/tests/test_conversation_routes.py`: replace the
`"open_question_answers": []` and `"premise_audit": []` entries with

```python
    "open_question_answers": [], "new_premises": [], "premise_updates": [],
    "answer_premise_ids": [],
```

Add `ledger_violations` and `premise_audit_violations` to the `from conversation import`
block, then append:

```python
from premise import PremiseDraft, PremiseLedger, PremiseUpdate

CORPUS = ["1 result: ibc=5782875 obc=177 dest_port=3333"]


def _ledger_with(*, status="UNVERIFIED", lb=True, kind="coverage"):
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining could surface as stratum or DNS", kind=kind,
                          load_bearing=lb)], author="s1", round_n=1)
    if status != "UNVERIFIED":
        led.apply([PremiseUpdate(id="p1", status=status, quote="ibc=5782875 obc=177",
                                 evidence="why")], author="s1", corpus=CORPUS, round_n=2)
    return led


def _answer(**kw):
    kw.setdefault("answer_premise_ids", ["p1"])
    return entry(route="ANSWER", value="112", value_kind="count", source_senior="s1",
                 justification="the NVM flow", r1_scope_alignment="PASS",
                 r2_progress="PASS", r3_answer_readiness="PASS",
                 r4_premise_verification="PASS", **kw)


def _spent_state():
    """Every senior slot used, s1's rounds gone - unsure_remedy has nothing to offer."""
    state = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        state.open_senior(sid)
    for _ in range(state.budget["rounds"]):
        state.record_round("s1", capped=False)
    state.retire("s2")
    state.retire("s3")
    return state


def test_an_answer_must_cite_the_premises_it_rests_on():
    e = _answer(answer_premise_ids=[])
    assert any("premise" in v for v in premise_audit_violations([e], _ledger_with()))


def test_an_answer_must_rest_on_a_coverage_premise():
    led = _ledger_with(kind="other", status="VERIFIED")
    assert any("Coverage" in v for v in premise_audit_violations([_answer()], led))


def test_a_clean_verified_coverage_premise_passes():
    led = _ledger_with(status="VERIFIED")
    assert premise_audit_violations([_answer()], led) == []


def test_an_answer_citing_an_unknown_premise_id_is_rejected():
    e = _answer(answer_premise_ids=["p99"])
    assert any("p99" in v for v in premise_audit_violations([e], _ledger_with()))


def test_a_load_bearing_unverified_premise_blocks_while_a_remedy_exists():
    state = QuestionState(points=1000)
    state.open_senior("s1")
    assert any("UNVERIFIED" in v
               for v in ledger_violations([_answer()], _ledger_with(), state))


def test_it_stops_blocking_once_rounds_and_slots_are_spent():
    out = ledger_violations([_answer()], _ledger_with(), _spent_state())
    assert not any("UNVERIFIED" in v for v in out)


def test_a_refuted_premise_blocks_even_with_nothing_left_to_try():
    out = ledger_violations([_answer()], _ledger_with(status="REFUTED"), _spent_state())
    assert any("REFUTED" in v for v in out)


def test_an_unanswered_open_question_is_named_by_its_id():
    led = PremiseLedger()
    led.ask(["which feed owns the byte counts?"], author="s1", round_n=1)
    e = entry(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
              directive="d", r1_scope_alignment="PASS", r2_progress="PASS",
              r3_answer_readiness="WEAK", r4_premise_verification="PASS")
    out = open_question_violations([e], led)
    assert len(out) == 1 and "q1" in out[0]


def test_answering_by_id_clears_it():
    led = PremiseLedger()
    led.ask(["which feed owns the byte counts?"], author="s1", round_n=1)
    e = entry(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
              directive="d", r1_scope_alignment="PASS", r2_progress="PASS",
              r3_answer_readiness="WEAK", r4_premise_verification="PASS",
              open_question_answers=[{"id": "q1", "answer": "cisco:nvm holds them"}])
    assert open_question_violations([e], led) == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_conversation_routes.py -q`
Expected: FAIL — `ImportError: cannot import name 'ledger_violations'`

- [ ] **Step 3: Update `conversation.py`'s imports and delete the dead pieces**

Replace lines 26-28 with:

```python
from premise import PremiseDraft, PremiseUpdate, quote_supported
from pydantic import BaseModel, Field, model_validator
from question_state import MAX_EXPLORATIONS, QuestionState
```

Delete: `class AuditLine` (58-77), `_norm` (80-82), `MIN_QUOTE_CHARS` (85), `_AUDIT_TEXT`
(88), and the `_audit_from_text` validator (197-213). `field_validator` and
`senior_report`'s `open_doubts` re-export go with them.

> **Note (post-review correction).** Do NOT import `_norm` or `MIN_QUOTE_CHARS` from
> `premise`. `premise._norm` was deleted during the Tasks 1-5 review: a senior's tool
> output is JSON (`splunk_agent._format_result` returns `json.dumps(...)`) while a
> senior restates it as `dest_port=3333`, so markdown-only normalization matched
> nothing and would have rejected every honest VERIFIED. `quote_supported` now uses
> `premise._match_form` (alphanumeric runs only) internally, and it is the only entry
> point you need — `conversation.py` never normalizes a quote itself.

- [ ] **Step 4: Add `QuestionAnswer` and rewrite the three fields**

Beside `Scope`:

```python
class QuestionAnswer(BaseModel):
    """SH's answer to one open question, addressed by id.

    A bare list matched by index let SH answer question 2 twice and pass the count
    check, which is what `open_question_violations` used to do."""

    id: str = Field(description="The question id, e.g. 'q2'. Copy it exactly.")
    answer: str = Field(description="Your answer. If you cannot settle it, say what would.")
```

Replace the `open_question_answers` field (114-119):

```python
    open_question_answers: list[QuestionAnswer] = Field(
        description="One entry per OPEN question the senior you are addressing has "
                    "asked (for ANSWER: the source senior's). Each names the question's "
                    "id and your answer. Answer from the case, the question text and "
                    "sibling reports; if you cannot, say what would settle it - that is "
                    "still an answer. Empty only when it has asked nothing.")
```

Replace the `premise_audit` field (175-182):

```python
    new_premises: list[PremiseDraft] = Field(
        description="Premises YOU are adding to the ledger - the ones the chain from "
                    "the question's words to the value rests on that the senior never "
                    "filed. Before any ANSWER, trace that chain and file what is "
                    "missing, opening with a 'coverage' premise: every way the "
                    "question's key concept could show up in the data, and whether the "
                    "seniors searched each. Then a 'selection' premise: why this entity "
                    "and not another that could fit. Empty on other routes unless you "
                    "have a premise to add.")
    premise_updates: list[PremiseUpdate] = Field(
        description="Verdicts you are recording on premises already in the ledger. "
                    "VERIFIED needs `quote` copied WORD FOR WORD from a senior's "
                    "report - any senior's, since a premise established by a sibling "
                    "is still evidence. Your own instruction is never evidence.")
    answer_premise_ids: list[str] = Field(
        description="ANSWER only. Every premise id the value rests on. The runner "
                    "checks each is VERIFIED, and refuses an answer resting on a "
                    "REFUTED one however little budget is left.")
```

- [ ] **Step 5: Rewrite the gates**

Replace `premise_audit_violations` (330-346), `unverified_audit` (349-351) and
`evidence_violations` (381-423) with:

```python
def premise_audit_violations(entries: list, ledger) -> list[str]:
    """An ANSWER must name the premises it rests on, and one of them must be the
    Coverage premise - every way the question's concept could show up in the data.
    A candidate can only win against candidates that were looked for."""
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        cited = [ledger.premises.get(i) for i in e.answer_premise_ids]
        missing = [i for i, p in zip(e.answer_premise_ids, cited) if p is None]
        if missing:
            out.append(f"ANSWER cites {', '.join(missing)}, which is not a premise on "
                       "this question - cite ids from the ledger, or file the premise "
                       "in new_premises first")
        found = [p for p in cited if p is not None]
        if not found:
            out.append(f"ANSWER from {e.source_senior} names no premises - trace the "
                       "chain from the question to the value and cite every premise "
                       "it rests on in answer_premise_ids")
        elif not any(p.kind == "coverage" for p in found):
            out.append(f"ANSWER from {e.source_senior} rests on no Coverage premise - "
                       "list every way the question's concept could show up in the "
                       "data and whether each was searched")
    return out


def ledger_violations(entries: list, ledger, state: QuestionState) -> list[str]:
    """The ANSWER gate, read off the ledger.

    Two blocks with different force:
      * a load-bearing premise still UNVERIFIED blocks while there is a remedy -
        a round left on the source senior, or a free slot for an alternative;
      * a REFUTED premise blocks FULL STOP. It is not "unsettled", it is known
        false, and an answer resting on it scores zero and poisons the case file
        for every later question. There is deliberately no escape here.
    """
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        cited = [ledger.premises[i] for i in e.answer_premise_ids
                 if i in ledger.premises]
        dead = [p for p in cited if p.status == "REFUTED"]
        if dead:
            out.append("ANSWER is blocked: it rests on REFUTED premise(s) - "
                       + "; ".join(f'{p.id} "{p.text[:80]}"' for p in dead)
                       + ". A refuted premise is not unsettled, it is false: this "
                       "value cannot be answered from. RETIRE and work a direction "
                       "that does not need it.")
        open_ = [p for p in cited if p.load_bearing and p.status == "UNVERIFIED"]
        fix = unsure_remedy(state, e.source_senior) if open_ else ""
        if fix:
            out.append(f"ANSWER is blocked: {len(open_)} load-bearing premise(s) it "
                       f"rests on are still UNVERIFIED - {fix}: "
                       + " | ".join(f'{p.id} "{p.text[:80]}"' for p in open_))
    return out


def sh_update_violations(entries: list, ledger, reports_of) -> list[str]:
    """SH settles a premise from a senior's REPORT, not from a tool result it never
    saw. The quote is checked against every senior's reports (a premise established
    by a sibling is still evidence - v0.4.2 Q216 was blocked three turns for quoting
    s1 under s2), and may not cite SH itself."""
    out = []
    for e in entries:
        for u in e.premise_updates:
            if u.status == "UNVERIFIED":
                continue
            if u.id not in ledger.premises:
                out.append(f"premise_update names {u.id}, which is not on this question")
            elif _CIRCULAR.search(u.quote or ""):
                out.append(f"premise_update {u.id} quotes SH as the authority - your "
                           "own instruction is not evidence. Quote the senior's query "
                           "or result that shows it.")
            elif not quote_supported(u.quote, [reports_of(None)]):
                out.append(f"premise_update {u.id} is {u.status} but its quote is in no "
                           "senior's report - copy the query, result or finding that "
                           "shows it word for word.")
    return out
```

Replace `open_question_violations` (426-439):

```python
def open_question_violations(entries: list[SeniorDirective], ledger) -> list[str]:
    """SH answers every OPEN question, by id. The entry that owes the answers is the
    route addressed to that senior, or the ANSWER built on its report."""
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        if not sid:
            continue
        owed = {q.id for q in ledger.open_questions_for(sid)}
        got = {a.id for a in e.open_question_answers if a.answer.strip()}
        missing = sorted(owed - got)
        if missing:
            out.append(f"{sid} is waiting on {', '.join(missing)} - answer each by id "
                       "in open_question_answers")
    return out
```

In `directive_violations`, delete the `unverified_audit` block (513-518). `ledger_violations`
replaces it. Leave the cut-off block (519-523) untouched.

- [ ] **Step 6: Run the tests and fix the fallout**

Run: `pytest agent/v0/tests/test_conversation_routes.py -q`

Roughly a dozen existing tests reference `premise_audit=[...]`, `AuditLine` or
`evidence_violations`. Convert each: build a `PremiseLedger`, file the premise with
`add()`, settle it with `apply()` where the old test passed a VERIFIED audit line, and
pass `answer_premise_ids=["p1"]` on the ANSWER entry. Delete tests that only checked
the legacy `"<premise> - VERIFIED: <where>"` string parsing — that path is gone.

Expected when done: all pass.

- [ ] **Step 7: Commit**

```bash
git add agent/v0/conversation.py agent/v0/tests/test_conversation_routes.py
git commit -m "feat(v0.5): SH's gates read the ledger; AuditLine deleted

SH now files premises into the same ledger (new_premises) and settles them from
report quotes (premise_updates), instead of keeping a parallel audit list.
ANSWER cites premise ids.

ledger_violations splits the old single block in two: a load-bearing UNVERIFIED
premise blocks while a remedy exists, as before; a REFUTED one blocks with no
escape at all. A refuted premise is not unsettled, it is false.

open_question_violations matches by id, so SH can no longer answer one question
twice and pass a count check.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 9: `sh_loop.py` — wire the ledger, delete the doubts

**Files:**
- Modify: `agent/v0/sh_loop.py` — imports (28-48), `SH_SYSTEM_PROMPT` + `SENIOR_BRIEF` (69-205), `render_wave` (250-291), `_render_turn` (~318), `_answers_note` (~330), `_directive_text` (~375), `_route_directive` (~382), `run_question` (437-740)
- Test: `agent/v0/tests/test_sh_loop.py`, `agent/v0/tests/test_sh_prompts.py` (modify)

- [ ] **Step 1: Write the failing test**

Append to `agent/v0/tests/test_sh_loop.py`:

```python
from premise import PremiseDraft, PremiseLedger
from sh_loop import render_wave


def test_render_wave_prints_the_ledger_table():
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining could surface as stratum", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    out = render_wave({"s1": {"report": "## This round\nx", "insight": "FOUND",
                              "novel_spl_count": 2, "rounds_left": 5}},
                      slots_remaining=2, turns_remaining=10, ledger=led)
    assert "PREMISE LEDGER" in out and "p1" in out and "coverage" in out


def test_render_wave_still_works_with_an_empty_ledger():
    out = render_wave({"s1": {"report": "x", "insight": "FOUND",
                              "novel_spl_count": 1, "rounds_left": 3}},
                      slots_remaining=1, turns_remaining=4, ledger=PremiseLedger())
    assert "no premises filed yet" in out.lower()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest agent/v0/tests/test_sh_loop.py -q`
Expected: FAIL — `TypeError: render_wave() got an unexpected keyword argument 'ledger'`

- [ ] **Step 3: Update the imports**

Replace the `conversation` and `senior_report` import blocks with:

```python
from conversation import (
    SHTurn,
    directive_violations,
    effective_r2,
    grade_violations,
    ledger_violations,
    open_question_violations,
    premise_audit_violations,
    sh_update_violations,
    spawn_overlap_violations,
    unsure_remedy,
)
from premise import PremiseLedger
from senior_report import report_violations, truncate_words
```

Drop `carry_doubts`, `has_coverage_premise`, `has_selection_premise`, `open_doubts`,
`open_questions`, `unverified_premises` and `evidence_violations`.

- [ ] **Step 4: Rewrite `render_wave`**

```python
def render_wave(reports: dict, *, slots_remaining: int, turns_remaining: int,
                ledger) -> str:
    """What SH reads at the top of a turn: every report from the wave just finished,
    then the whole premise ledger.

    The ledger table replaces the three '!!' warnings this used to print (unverified
    count, missing Coverage, missing Selection). All three were regexes over the
    report's prose; the table shows the same facts as typed data, and a missing
    Coverage row is visible as absence.
    """
    blocks = []
    for sid, r in reports.items():
        novel = int(r.get("novel_spl_count", 0))
        head = (f"--- {sid} | round report | insight={r.get('insight', '?')} "
                f"| status={r.get('status', '?')} "
                f"| candidate={r.get('value') or 'none'} "
                f"| confidence={r.get('confidence')} "
                f"| novel_spl={novel} "
                f"| rounds_left={r.get('rounds_left', 0)}")
        if novel == 0:
            head += "\n!! This round ran NO new query. R2 = FAIL for it, by code, " \
                    "and you cannot grade it otherwise."
        blocks.append(head + "\n" + (r.get("report") or "").strip())

    return (_budget_line(slots_remaining, turns_remaining) + "\n\n"
            + "\n\n".join(blocks)
            + "\n\n" + ledger.render_table()
            + "\n\nReview every report above as a senior threat hunter, grade it "
              "(R1/R2/R3/R4), answer every open question by id in "
              "open_question_answers, and emit exactly one route per senior. ANSWER "
              "only when the value appears literally in one of these reports or in "
              "the question text.")
```

- [ ] **Step 5: Update the three open-question renderers**

`_answers_note`:

```python
def _answers_note(e) -> str:
    """SH's answers to the senior's open questions, as the senior will read them."""
    answers = [a for a in e.open_question_answers if a.answer.strip()]
    if not answers:
        return ""
    return ("SH's answers to your open questions:\n"
            + "\n".join(f"[{a.id}] {a.answer}" for a in answers) + "\n\n")
```

In `_route_directive`, replace the two `answers = ...` lines with:

```python
    answers = [a for a in e.open_question_answers if a.answer.strip()]
    answers = ("\n\nOn your open questions:\n"
               + "\n".join(f"[{a.id}] {a.answer}" for a in answers)) if answers else ""
```

In `_render_turn`, replace the `answered:` line with:

```python
        rows += [f"    answered {a.id}: {a.answer}"
                 for a in e.open_question_answers if a.answer.strip()]
```

In `_route_body`'s ANSWER branch, replace the `audit` lines with:

```python
    cited = ", ".join(e.answer_premise_ids) or "(none)"
    return (f"**{e.value}** ({e.value_kind}) from {e.source_senior}\n\n{e.justification}"
            f"\n\n**Premises it rests on:** {cited}")
```

- [ ] **Step 6: Delete `_directive_text`'s R4 prefix**

```python
def _directive_text(e) -> str:
    """What a senior is actually told this round: SH's answers, then the route.

    The verify-first prefix this used to add on a WEAK/FAIL R4 is gone: the runner
    now prepends the senior's unresolved premises to EVERY round
    (SeniorSession._message_for), unconditionally. The old prefix fired on SH's own
    grade, and SH grades all-PASS when it wants to answer.
    """
    return _route_directive(e)
```

- [ ] **Step 7: Wire the ledger into `run_question`**

After `state = QuestionState(points=points)`:

```python
    ledger = PremiseLedger()
```

Delete `doubts: dict = {}` and its comment.

Replace the gate-assembly expression with:

```python
        problems = grade_violations(
            turn.entries, graded=set(unread),
            exploration={s for s, k in kinds.items() if k == "exploration"},
        ) + directive_violations(turn.entries, state) + open_question_violations(
            turn.entries, ledger
        ) + spawn_overlap_violations(
            turn.entries, {sid: s.constraints for sid, s in sessions.items()
                           if state.is_active(sid)}
        ) + sh_update_violations(
            turn.entries, ledger,
            # A premise established by a sibling is still evidence, so the quote is
            # checked against every senior's reports and clarify replies.
            reports_of=lambda sid: "\n".join(
                [r.get("report", "") for r in all_reports]
                + sum(clarify_text.values(), [])),
        ) + premise_audit_violations(
            turn.entries, ledger
        ) + ledger_violations(turn.entries, ledger, state)
```

Immediately after `grades.extend(rows)` / `unread = {}` (so SH's writes land only on a
turn that passed every gate):

```python
        # SH's own ledger writes. Its quotes come from reports, not tool output - it
        # has no Splunk access and never will.
        sh_corpus = ([r.get("report", "") for r in all_reports]
                     + sum(clarify_text.values(), []))
        for e in turn.entries:
            ledger.add(e.new_premises, author="sh", round_n=state.turns_used)
            ledger.apply(e.premise_updates, author="sh", corpus=sh_corpus,
                         round_n=state.turns_used)
            for a in e.open_question_answers:
                if a.answer.strip():
                    ledger.answer(a.id, a.answer)
```

Add `ledger=ledger,` to the `SeniorSession(...)` constructor call.

Delete the `doubts[sid] = carry_doubts(...)` line in the wave loop.

Update the `render_wave(...)` call to pass `ledger=ledger`.

Add `"ledger": ledger,` to `run_question`'s returned dict.

- [ ] **Step 8: Update the prompts**

In `SH_SYSTEM_PROMPT`, replace the `ANSWER EVERY OPEN QUESTION` and
`AUDIT THE CHAIN BEFORE ANY ANSWER` paragraphs with:

```
ANSWER EVERY OPEN QUESTION, BY ID. A senior's open questions reach you with an id (q1, q2...). Put one entry per open question in `open_question_answers`, naming its id and your answer. They reach the senior with its next instruction. Answer from the case, the question text and sibling reports; if you cannot, say what would settle it - that is still an answer. A turn that leaves one unanswered is rejected. Keep each to a line or two.

THE PREMISE LEDGER. Every premise on this question lives in one ledger, shown to you in full each turn. The seniors file their own; you file the ones they missed, in `new_premises`. A premise is VERIFIED only when a result someone actually ran shows it - you settle one in `premise_updates`, quoting the senior's query, result or finding WORD FOR WORD from any senior's report. Your own instruction is never evidence, however faithfully a senior wrote it down: the runner rejects a quote that cites you.

BEFORE ANY ANSWER, trace the chain yourself from the question's words to the value, and file in `new_premises` every premise it rests on that no one has. Open with a `coverage` premise: the key concept the question asks about, every way it could show up in the data, and whether the seniors' searches covered each - checked against the feed's own fields, not against a senior's list drawn from memory. Then a `selection` premise: why this entity and not another that could fit. When the answer is a measurement, a `definition` premise: its meaning taken from the question's verbatim words, not your framing and not a rule a senior states - a senior citing a rule is not a result. Mark `load_bearing` true on any premise the answer breaks without. Then cite every premise the value rests on in `answer_premise_ids`.

A candidate is never answerable because no rival turned up. A way nobody searched is UNVERIFIED however well the chosen candidate is verified, and a candidate can only win against candidates that were looked for. Every result a runner "Partial results" note lists was only partly read - a claim resting on one is UNVERIFIED.
```

In `THE GATES YOU MUST RESPECT`, replace the `Premise audit`, `Unverified premises`,
`Quoted evidence` and `The senior's own doubts` bullets with:

```
  * Premise ledger: an ANSWER must cite its premises in `answer_premise_ids`, and one of them must be a `coverage` premise, or the turn is rejected.
  * Unverified premises: an ANSWER resting on a load-bearing UNVERIFIED premise is rejected while the source senior has rounds left OR a senior slot is free.
  * Refuted premises: an ANSWER resting on a REFUTED premise is rejected outright - there is no budget state that lets it through. A refuted premise is not unsettled, it is false.
  * Quoted evidence: a `premise_updates` verdict must quote a senior's report word for word, and may not cite you.
```

In `SENIOR_BRIEF`, delete the `## Assumptions` and `## Open questions for SH` blocks from
the report template (leaving `## Ruled out` as the template's last section), and replace
the closing sentences of `NO UNTESTED ASSUMPTIONS` with:

```
Your premises do not go in the report. File them in `submit_finding`'s `new_premises`, each with a kind and whether the answer breaks without it. The runner holds them and shows every unsettled one back to you at the start of each round, with its id - settle them in `premise_updates`, quoting the query output that does it. A premise you stop mentioning does not go away.
Your first premise each round is a `coverage` one: the ways the question's concept could show up in your scope, and for each, the query that searched it and what came back. Your second is `selection`: why this entity and not the other candidates coverage found.
Your questions for SH do not go in the report either - put them in `open_questions`, one per string. SH must answer every one before your next round.
```

- [ ] **Step 9: Run the full suite**

Run: `pytest agent/v0/tests/ -q`

`test_sh_prompts.py` asserts on prompt text and `test_sh_loop.py` on `render_wave`'s
arity and the old `open_question_answers` shape. Update each assertion to the new
wording and shapes.

Expected when done: green.

- [ ] **Step 10: Commit**

```bash
git add agent/v0/sh_loop.py agent/v0/tests/
git commit -m "feat(v0.5): sh_loop owns one ledger per question

The doubts dict is gone - a premise that is not VERIFIED is the same thing, and
the ledger already carries it. render_wave prints the table instead of the three
regex '!!' warnings. Open questions are answered by id.

_directive_text no longer prepends a verify-first reminder on a WEAK/FAIL R4:
SeniorSession prepends the unresolved premises to every round unconditionally.
The old one fired on SH's own grade, and SH grades all-PASS when it wants to
answer.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 10: `senior_report.py` — delete the regex layer

**Files:**
- Modify: `agent/v0/senior_report.py` — `REQUIRED_SECTIONS` (24-32), `_TRIM_ORDER` comment (52-53), delete 98-188
- Test: `agent/v0/tests/test_senior_report.py`

- [ ] **Step 1: Delete the dead functions**

Remove `_NOT_A_QUESTION`, `open_questions`, `_DOUBT`, `open_doubts`, `_label`,
`carry_doubts`, `unverified_premises`, `_has_assumption`, `has_selection_premise` and
`has_coverage_premise`.

Shorten `REQUIRED_SECTIONS`:

```python
REQUIRED_SECTIONS = (
    "## Prior rounds",
    "## This round",
    "### What I ran",
    "### What it means",
    "## Ruled out",
)
```

Update the `_TRIM_ORDER` comment:

```python
# Trimmed first when a report is over the cap: narrative SH can do without. Premises
# and open questions left the report in v0.5 (they are schema fields on the ledger
# now), so a tail cut can no longer eat the sections SH grades on.
_TRIM_ORDER = ("### What I ran", "### What it means", "## Prior rounds")
```

- [ ] **Step 2: Confirm nothing still imports them**

Run: `grep -rn "open_doubts\|carry_doubts\|unverified_premises\|has_coverage_premise\|has_selection_premise\|_has_assumption" agent/`
Expected: no matches outside `docs/`.

- [ ] **Step 3: Delete the obsolete tests**

In `agent/v0/tests/test_senior_report.py`, delete every test for the removed functions
(`test_a_doubt_survives_a_report_that_simply_stops_mentioning_it`, the `open_questions`
tests, the Coverage/Selection premise tests, the `unverified_premises` tests). Keep the
`truncate_words`, `novel_spl`, `stamp_header` and `report_violations` tests, and update
`report_violations` expectations for the shortened `REQUIRED_SECTIONS`.

- [ ] **Step 4: Run the full suite**

Run: `pytest agent/v0/tests/ -q`
Expected: green

- [ ] **Step 5: Commit**

```bash
git add agent/v0/senior_report.py agent/v0/tests/test_senior_report.py
git commit -m "refactor(v0.5): delete the regex layer over the report's prose

Gone: open_doubts, carry_doubts, _DOUBT, _label, unverified_premises,
has_coverage_premise, has_selection_premise, _has_assumption, and the markdown
open_questions parser. The ledger holds all of it as typed data.

REQUIRED_SECTIONS drops Assumptions and Open questions - both are schema fields
now, which also stops them competing with narrative for the 600-word cap.

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 11: One ledger file per run, and the version doc

**Files:**
- Modify: `agent/v0/run_all_v0.py`
- Create/modify: `docs/version_architecture/v0/v0.5.md`

- [ ] **Step 1: Collect and dump in the runner**

In `agent/v0/run_all_v0.py`, add `from premise import dump_ledgers` to the imports and
a `ledgers: dict = {}` beside the other per-run accumulators. Where each question's
result is collected, add:

```python
        ledgers[qid] = result["ledger"]
```

After the question loop, before the scoreboard print:

```python
    dump_ledgers(os.path.join(run_dir, "premise_ledger.json"), ledgers)
    print(f"[ledger] wrote {sum(len(l.premises) for l in ledgers.values())} premises "
          f"to {os.path.join(run_dir, 'premise_ledger.json')}")
```

- [ ] **Step 2: Run the full suite**

Run: `pytest agent/v0/tests/ -q`
Expected: green

- [ ] **Step 3: Write the version doc**

Create `docs/version_architecture/v0/v0.5.md` following `v0.4.2.md`'s shape: a
`## Changelog` section with one entry per commit from Tasks 0–11 (the Task 0 probe
result first), then a `## What changed vs v0.4.2` section naming the deleted regex
layer, the runner-owned ledger, the REFUTED status and the per-round carry-forward.

- [ ] **Step 4: Commit**

```bash
git add agent/v0/run_all_v0.py docs/version_architecture/v0/v0.5.md
git commit -m "feat(v0.5): one premise_ledger.json per run; v0.5 version doc

Claude-Session: https://claude.ai/code/session_016qD8L48LFgQFzy1ZzNgZuE"
```

---

## Task 12: Q216 smoke run

**Requires the user's go-ahead.** `CLAUDE.md`'s cost-limited-runs policy makes every
run a smoke test on named questions, and escalating needs explicit approval. Do not
launch this without being asked.

- [ ] **Step 1: Run Q216 alone**

```bash
python agent/v0/run_all_v0.py --ids 216 --run-name v0.5_glm-5.3_Q216
```

Output goes to `log/temp/v0.5_glm-5.3_Q216/`.

- [ ] **Step 2: Read the three things that decide whether spec 1 worked**

1. `log/temp/v0.5_glm-5.3_Q216/premise_ledger.json` exists and holds premises whose
   `history` arrays have more than one entry.
2. The byte-profile premise ("download-like", "inbound", or similar wording) is
   present, and its history shows it either settled with a real quote or still
   UNVERIFIED at the end — **not** absent.
3. No ANSWER was accepted while a load-bearing premise it cites was UNVERIFIED.

- [ ] **Step 3: Read spec 2's calibration numbers**

From the same file, per spec 2 §8.1:
- premises per report, and the share with `load_bearing: true` → §7.1, §7.5
- how many load-bearing premises sat UNVERIFIED for ≥2 rounds with
  `candidate_at_each_round` unchanged — i.e. how often spec 2's trigger would have
  fired → §7.1, §7.5
- whether the byte-profile premise is among them. If it is not, spec 2 §3.1's trigger
  is aimed at the wrong thing and must be rewritten before spec 2 is built

- [ ] **Step 4: Record**

Add a smoke-run section to `docs/version_architecture/v0/v0.5.md` with the score, cost
by role (SH vs senior), latency and the three readings. Write the measured values into
spec 2's §7 table **alongside** the provisional ones, per spec 2 §8.3 — do not replace
them silently.

---

## Self-review

**Spec coverage:**

| Spec section | Task |
|---|---|
| §3.1 runner-owned ledger | 2 |
| §3.2 models | 1 |
| §3.3 senior emits drafts / updates / questions | 6 |
| §3.4 transitions, REFUTED terminal | 3 |
| §3.5 tool-output quote check | 3, 7 |
| §3.6 carry-forward into every round | 7 |
| §3.7 one ledger, `author="sh"` | 8, 9 |
| §3.8 gates | 8 |
| §3.9 open questions by id | 6, 8 |
| §3.10 ledger table for SH | 4, 9 |
| §4 deletions | 8, 9, 10 |
| §5 nested-tool-arg risk | 0, 6 |
| §6 tests | every task |
| §7 `premise_ledger.json` + spec 2 calibration | 5, 9, 11, 12 |
| §8 files | all |

**Type consistency:** `PremiseDraft(text, kind, load_bearing)`, `PremiseUpdate(id,
status, quote, evidence)` and `QuestionAnswer(id, answer)` keep the same field names
everywhere. Ledger methods used across Tasks 2–11: `add(drafts, author, round_n)`,
`ask(texts, author, round_n)`, `apply(updates, author, corpus, round_n)`,
`answer(question_id, text)`, `record_candidate(author, round_n, value)`,
`unresolved_for(author)`, `blocking()`, `refuted()`, `open_questions_for(author)`,
`render_for_senior(author)`, `render_table()`, `render_refuted()`, `to_records(qid)`.
`quote_supported(quote, corpus)` takes a list at every call site —
`sh_update_violations` wraps its single report string in one.

**Known loose end:** `render_refuted()` (Task 4) has no caller until spec 2's
alternative-agent brief. It is four lines over data the ledger already holds; delete it
and restore it in spec 2 if a reviewer objects.
