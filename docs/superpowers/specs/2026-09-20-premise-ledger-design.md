# Premise Ledger — design (spec 1 of 2)

**Date:** 2026-09-20
**Status:** approved, not implemented
**Target version:** v1.5
**Successor spec:** `2026-09-20-validation-agent-design.md` (spec 2) — written, blocked on this one

---

## 1. The problem

v1.4.2's Q216 run lost the question to a premise that was never settled and never
rejected — it was simply written out of the record.

s1's round 1 Assumptions said:

> Definition premise: … The 3333 record's byte profile (5.7MB in / 177B out) is
> download-like, so the record does not positively show the act - UNVERIFIED

Round 2 still carried it. SH then issued a restate-only COMMAND —
*"make the Cisco NVM chain answer-ready… Do not reopen non-NVM validation"* — and
round 3 came back all-VERIFIED with that line gone, replaced by:

> External premise (45.77.53.176:3333 = Monero pool) — established by SH outside
> this feed; not re-tested in NVM per instruction

SH then quoted that sentence as the evidence for its own VERIFIED audit line. The
chain was circular and the doubt had vanished, so no gate fired.

Two v1.4.2 patches addressed the symptoms: `carry_doubts` (a doubt persists across
rounds) and `_CIRCULAR` (a VERIFIED quote may not cite SH). Both are regexes over
markdown, and both are working around the same root cause:

**The senior's premises are prose. Everything that reads them is a regex.**

- `unverified_premises()` counts `"UNVERIFIED"` substrings
- `has_coverage_premise()` / `has_selection_premise()` match a bullet prefix
- `open_doubts()` keyword-scans for UNVERIFIED|not verifiable|partial|unreturned
- `carry_doubts()` matches premises by `_label()` — text before the first colon,
  else the first four words
- `_AUDIT_TEXT` parses `"<premise> - VERIFIED: <where>"` back out of a string

A reworded premise is a new premise. A premise stated without the magic word is
settled. A premise that is simply omitted is gone. The laundering path is open by
construction.

Meanwhile SH's side of the same problem was solved a version ago: `AuditLine` is a
pydantic model with `premise / status / source / quote / evidence`, and
`evidence_violations` enforces a verbatim quote against real report text. The fix
is to give the senior the same treatment, and to stop keeping two lists.

## 2. What this spec changes

One structured premise ledger per senior, owned by the runner, shared by the senior
and SH. The regex layer is deleted. Open questions become addressable by id.

Explicitly **not** in this spec (they are spec 2):

- the validation agent
- the alternative-agent hand-over template
- any new agent type or spawn rule

## 3. Design

### 3.1 Ownership: the runner holds the ledger

Three options were considered:

| | How | Verdict |
|---|---|---|
| A | Senior re-emits the full list each round | Dropping a premise is one omission away — this *is* the Q216 bug, just typed |
| B | Runner owns the list; senior emits new premises + status updates keyed by id | **Chosen.** You cannot drop what you never re-emit |
| C | Senior re-emits, runner diffs and rejects drops | Catches it, but costs a round to reject and re-sends the whole list every round |

Under B the premise text is **immutable once filed**. The runner stores the string
and replays it verbatim into every subsequent round. Rewording is impossible rather
than discouraged, and `_label()`-style fuzzy matching is unnecessary.

### 3.2 The models

```python
class Premise(BaseModel):
    id: str                 # runner-assigned: p1, p2...  the senior never picks one
    author: str             # "s1" | "sh" | "v2"
    kind: Literal["coverage", "selection", "definition", "other"]
    text: str               # immutable after filing
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"]
    load_bearing: bool      # does the answer break without it?
    round_first_seen: int   # runner-stamped
    verified_by: str        # who settled it; "" while UNVERIFIED
    quote: str              # verbatim tool output that settles it
    evidence: str           # why that quote settles it


class OpenQuestion(BaseModel):
    id: str                 # runner-assigned: q1, q2...
    text: str
    answer: str             # SH fills it; "" while open
```

`kind` replaces `has_coverage_premise` / `has_selection_premise`.
`load_bearing` and `round_first_seen` exist to serve spec 2's trigger (see §7) and
are inert in this spec beyond gating (§3.8).

### 3.3 What the senior emits

`submit_finding` gains three fields. It does **not** emit the ledger:

- `new_premises` — premises added this round; no ids, the runner assigns them
- `premise_updates` — `[{id, status, quote, evidence}]` for premises being resolved
- `open_questions` — `list[str]`; the runner assigns ids

The `## Assumptions` section is removed from the report template. The ledger
replaces it, which also stops the premise list competing with narrative for the
600-word cap.

### 3.4 Status transitions, enforced in code

| From | To | Rule |
|---|---|---|
| UNVERIFIED | VERIFIED | Requires a quote. By the owning senior, **another senior**, or (spec 2) a validation agent |
| UNVERIFIED | REFUTED | Requires a quote |
| VERIFIED | UNVERIFIED | Allowed, no quote. A senior finding a problem with its own premise is the honest path |
| VERIFIED | REFUTED | Requires a quote |
| REFUTED | anything | **Refused.** Terminal |

An update naming an unknown id is ignored and logged. A senior round cannot be
rejected mid-flight the way an SH turn can, and the effect is identical: the premise
stays unresolved and the gate still blocks.

### 3.5 The quote is checked against real tool output

This is the teeth of the spec and the senior-side analogue of `_CIRCULAR`.

Today a senior can write `- Foo: VERIFIED` with nothing behind it, and only SH's
judgement stands between that and an answer.

`_record()` already retains `full_state` — the message list including tool results.
A `premise_updates` entry setting VERIFIED or REFUTED must carry a quote that
appears, word for word after `_norm()` normalization and at least `MIN_QUOTE_CHARS`
long, in a Splunk result that senior actually received during this question.

On failure the **update is dropped**, the status stays as it was, and the reason is
printed into the report SH reads. No LLM judgement is involved.

### 3.6 The runner carries unresolved premises into every round

Prepended to the senior's directive, unconditionally:

```
YOUR UNRESOLVED PREMISES — carried forward by the runner, in your own words:
[p1] load-bearing, open since round 1 — "The 3333 record's byte profile
     (5.7MB in / 177B out) is download-like, so the record does not
     positively show the act"
[p4] open since round 2 — "..."

Settle each with `premise_updates`: a status, and a quote from a result you
actually ran. Not mentioning one does not remove it.
```

This replaces the R4-triggered prefix in `_directive_text()`
(*"FIRST, before anything else this round: verify the UNVERIFIED premises…"*), which
only fires when SH grades R4 WEAK or FAIL — and SH grades all-PASS when it wants to
answer. The runner has no such incentive. R4 survives as a grade because it is
useful data; it stops being load-bearing.

### 3.7 One ledger, not two

SH's `premise_audit` folds into the same ledger with `author="sh"`. SH's traced
premises — Coverage, Selection, the measurement definition — are historically the
ones that go untested, and as ledger entries they become carryable across rounds
and (spec 2) routable to a validation agent.

`AuditLine` is deleted. SH's ANSWER cites premise ids.

Preserved from v1.4.2: SH's audit quote may come from **any** senior's report.
That was a deliberate fix — Q216 was blocked for three turns for quoting s1's
finding under s2 — and it must not regress.

### 3.8 Gates

| Gate | Change |
|---|---|
| `evidence_violations` | Loses the `doubts_of` parameter; reads the ledger |
| ANSWER + load-bearing UNVERIFIED | Blocked while `unsure_remedy()` returns a remedy — unchanged behaviour |
| ANSWER + load-bearing REFUTED | **Blocked with no remedy, ever.** The existing escape — answer anyway once rounds and slots are spent — does not apply |
| `premise_audit_violations` | ANSWER must cite premise ids; a `kind="coverage"` premise must exist |
| `open_question_violations` | Matched by id, not by count |

REFUTED having no escape hatch is deliberate. A question can now end `NO_ANSWER`
where today it would submit something. That is the correct trade: a known-refuted
answer scores zero anyway and poisons the case file for every later question in the
run.

### 3.9 Open questions become addressable

Today `open_question_violations` checks `got >= need` over a bare `list[str]` zipped
by index. SH can answer question 2 twice and pass the gate.

`SeniorDirective.open_question_answers` becomes `list[QuestionAnswer]` — `{id,
answer}`. A rejection names the id it is missing. An answered question closes and is
not carried; unlike a premise, a question is done once answered.

### 3.10 What SH sees

`render_wave` prints a ledger table per senior, replacing the three `!!` warning
blocks:

```
PREMISE LEDGER — s1
 id  kind       status      LB  since  text
 p1  coverage   UNVERIFIED  Y   r1     Mining could surface as stratum, DNS to a pool...
 p2  selection  VERIFIED    Y   r1     chrome.exe is the only process...      [s1 r2]
 p5  other      REFUTED     Y   r3     The 3333 flow shows submission...      [v1]
```

A missing Coverage row is visible as absence, so the warning blocks stop earning
their keep.

## 4. Deleted

- `senior_report.open_doubts`, `carry_doubts`, `_DOUBT`, `_label`
- `senior_report.unverified_premises`, `has_coverage_premise`, `has_selection_premise`,
  `_has_assumption`
- `conversation.AuditLine`, `_AUDIT_TEXT`, the `_audit_from_text` legacy validator
- the `doubts` dict in `sh_loop.run_question` and `evidence_violations(doubts_of=…)`
- the `## Assumptions` section of the report template, and its entry in
  `_TRIM_ORDER`'s protected set
- the R4-conditional verify-first prefix in `_directive_text`

Retained in `senior_report.py`: `truncate_words`, `novel_spl`, `stamp_header`,
`open_questions` (rewritten to read the schema field, not markdown),
`report_violations`.

## 5. Risks

**Nested tool arguments may not work on GLM-5.3 via AI&.** `submit_finding` takes
flat primitives today, and `finding.py`'s docstring records why it is a tool call
rather than `response_format`: the senior is a ReAct loop whose terminal turn is not
a single constrained completion.

This is the one thing that could invalidate the shape, so **the first
implementation step is a probe, not code**: send GLM-5.3 on AI& a tool with a
`list[object]` parameter and see whether it fills it correctly. If it does not, fall
back to a `premises_json: str` parameter parsed by the runner — uglier, but it
cannot fail. Decide by evidence.

**A senior that skips `submit_finding` files no premises.** The ledger is unchanged
and everything unresolved stays unresolved, which matches how a round that produced
nothing is already treated.

**REFUTED could fire too readily** and cost answers that would have scored. The
Q216 re-run is the measurement; if it does, the remedy is to require `load_bearing`
for the hard block, which is already the design.

## 6. Testing

Behavioural tests that must exist:

- a premise the senior stops mentioning is still in the ledger next round — the Q216 bug
- a VERIFIED update whose quote is in no tool result is refused; status stays UNVERIFIED
- `REFUTED → VERIFIED` is refused
- a load-bearing REFUTED premise blocks ANSWER with rounds *and* slots exhausted
- a load-bearing UNVERIFIED premise blocks ANSWER while a remedy exists, and does not once spent
- an unanswered open question names its id in the rejection
- a sibling senior takes a premise UNVERIFIED → VERIFIED
- SH's audit quote may come from a senior other than `source_senior` (v1.4.2 regression guard)

Acceptance: the existing suite (498 passed, 5 skipped) stays green, and a Q216
smoke run under the cost-limited-runs policy shows the laundered premise either
settled with evidence or still blocking the answer.

## 7. What spec 2 will consume

Spec 2 (`2026-09-20-validation-agent-design.md`) is written and depends on every
field below. Recorded here so implementation does not break it.

**This run is also spec 2's calibration data.** Spec 2 §8.1 lists five parameters
that are deliberately unset until the Q216 smoke run measures them — premises per
report, the share marked `load_bearing`, and how often the validator trigger *would*
have fired. Those are reads of this spec's ledger and cost nothing extra, so the
run must log the ledger in full, not just its effect on the gates.

- `load_bearing` + `round_first_seen` + `status` are the validation agent's trigger:
  a load-bearing premise still UNVERIFIED after ≥2 rounds with the senior's candidate
  unchanged
- `Premise.text` alone, plus the SPL and result behind it, is the validator's entire
  briefing — the question is withheld, and the underlying reports are **not** sent
  (they carry the question's concept in their own text, which would make the
  withholding cosmetic)
- `status="REFUTED"` with `author` = a validation agent is what triggers the
  alternative-agent hand-over
- a validation agent writes to the ledger like any other author, via the same
  transition rules and the same quote check

## 8. Files

| File | Change |
|---|---|
| `agent/v1/premise.py` | **new** — models, ledger, transitions, quote check, rendering |
| `agent/v1/finding.py` | `submit_finding` gains `new_premises`, `premise_updates`, `open_questions` |
| `agent/v1/senior_report.py` | regex layer deleted; `open_questions` reads the schema |
| `agent/v1/conversation.py` | `AuditLine` folded into `Premise`; gates rewired |
| `agent/v1/sh_loop.py` | per-senior ledger, carry-forward block, `render_wave` table, prompt updates |
| `agent/v1/senior_session.py` | ledger block passed into the round message |
| `agent/v1/tests/` | as §6 |
