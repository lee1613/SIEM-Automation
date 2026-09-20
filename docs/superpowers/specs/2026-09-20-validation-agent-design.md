# Validation Agent & Alternative-Agent Hand-over — design (spec 2 of 2)

**Date:** 2026-09-20
**Status:** approved in design, **blocked on spec 1**
**Target version:** v1.4.3
**Depends on:** `2026-09-20-premise-ledger-design.md` (spec 1). Every trigger in this
spec reads ledger fields that do not exist until spec 1 ships.

> **Calibration note.** Five parameters in this spec (§7) are deliberately left as
> provisional numbers. They cannot be chosen honestly before the ledger has run
> once — they depend on how many premises a real question produces and how they
> are distributed. §8 says exactly which run measures what, and how to feed the
> answers back. Implement §1–§6 as written; set §7 from data.

---

## 1. The problem

Two failures survived v1.4.2, both visible in the Q216 trace.

**A premise nobody was assigned to test never gets tested.** s1 flagged the
byte-profile premise UNVERIFIED in round 1 and again in round 2. It held the same
candidate throughout. Nothing in the architecture converts "this senior has been
stuck on the same unproven premise for two rounds" into an action — SH's options
were to command the same senior again (it had already failed twice) or to answer
anyway.

**A second opinion that is briefed to confirm is not a second opinion.** s2 was
spawned to check s1's candidate. It queried the flow, read `app=http`,
`uri /images/logos.png`, `status 200` — a PNG download — and reported it as
"mining-consistent… disguised as HTTP". It also read the byte direction backwards
relative to Cisco NVM (NVM: `ibc=5,782,875` inbound; s2: "5.76MB out"). Neither
senior reconciled it. SH read "s2 confirms s1" as independent verification.

Spec 1 makes an unsettled premise impossible to lose. It does not assign anyone to
settle it, and it does not stop a confirming second opinion.

## 2. What this spec adds

**One new agent type, not two.**

- **Validation agent** — a new, narrow worker. Given one premise and nothing else,
  one round, it proves it, disproves it, or fails to do either.
- **Alternative agent (AA)** — *not* a new type. An ordinary senior spawned after a
  refutation, whose brief the runner augments with the refuted premises. Treating it
  as a new agent type would duplicate the entire senior stack to add one prompt
  section.

## 3. The validation agent

### 3.1 Trigger — the runner spawns it, SH is not asked

Evaluated by the runner after each wave, per active senior:

```
a load-bearing premise exists with
    status == "UNVERIFIED"
    current_round - round_first_seen >= VALIDATE_AFTER_ROUNDS
AND the senior's candidate value is unchanged across those rounds
AND validators_spent[senior] < MAX_VALIDATORS_PER_SENIOR
```

When it holds: **retire the senior, spawn one validator per qualifying premise**
(oldest `round_first_seen` first, capped). The senior's candidate is held, not
discarded.

SH does not choose this and cannot decline it. That is the point. Every version so
far has failed at exactly this moment because SH had a rule and did not follow it —
the restate-only COMMAND that laundered Q216's premise (*"Do not reopen non-NVM
validation"*) was SH exercising judgement while holding a candidate it wanted to
submit. The runner has no candidate and no preference.

Retiring the senior is right in both outcomes: if the premise verifies, its answer
stands and it had nothing left to add; if it is refuted, its direction is dead.

### 3.2 Briefing — the premise, and nothing that reveals the question

The validator receives:

- `Premise.text` — the claim, verbatim
- `Premise.evidence` — for an UNVERIFIED premise this field holds *what would test
  it* (spec 1 §3.2)
- the standard dataset briefing every worker gets (index, time range)
- the same Splunk tools a senior has

It does **not** receive: the question, the senior's reports, the candidate value, the
other premises, or the senior's open questions.

This was the design's crux and it was decided deliberately. Sending the underlying
reports would make the validator better-informed and much more efficient — and would
also defeat the entire reason it exists. A senior report's Coverage line is written
in the question's own vocabulary, and `verbatim_task` puts the question's words into
every senior. Ship the report and the question is revealed in all but name; the
validator inherits the bias it was spawned to escape, and becomes a second opinion
briefed to confirm — which is precisely what s2 was.

Its system prompt states its role plainly: *you are validating one claim; do not try
to work out what larger question it belongs to; use only what you are given.*

Whether this starves it of the context it needs to search efficiently is
**parameter §7.4**, and the first run measures it.

### 3.3 Output — the ledger's own vocabulary

Three outcomes, which are the three ledger statuses; no new words:

| Verdict | Meaning |
|---|---|
| `VERIFIED` | A result it ran shows the claim holds |
| `REFUTED` | A result it ran shows the claim is false |
| `UNVERIFIED` | It could not settle it within its round |

It writes to the ledger as `author="v1"` through the same transition rules and the
same tool-output quote check as any other author (spec 1 §3.4, §3.5). A validator
cannot assert VERIFIED without a quote from a result it actually received, exactly
like a senior.

A validator that exhausts its round without concluding leaves the premise
UNVERIFIED — which keeps blocking.

### 3.4 Budget

| | Value | Note |
|---|---|---|
| Rounds | `VALIDATOR_ROUNDS` = 1 | §7.2 |
| Iterations | `VALIDATOR_ITERS` = 8 | §7.3 — seniors get `ROUND_ITERS` = 10 |
| Per senior | `MAX_VALIDATORS_PER_SENIOR` = 3 | §7.1 |
| Senior spawn slot | **none** | a validator is not a senior |
| SH turn | folds into the normal cycle | validators run as a wave; SH reads the verdicts in its next turn |

### 3.5 What happens after the verdict

Nothing new is needed. The ledger drives the existing spec 1 gates:

- **all qualifying premises VERIFIED** → the ledger is clean, the ANSWER gate stops
  blocking, and SH may submit the retired senior's candidate
- **any REFUTED** → spec 1's no-escape gate blocks that answer permanently; the AA
  path opens (§4)
- **still UNVERIFIED** → it keeps blocking; SH spends remaining budget or spawns an AA

No new SH route, no new decision, no new prompt section. This is the main reason the
validator is worth its cost: it converts a judgement SH keeps getting wrong into a
ledger state the gates already read.

## 4. The alternative agent

### 4.1 It is a senior, spawned normally

Costs one senior spawn slot. Same prompt, same tools, same round budget. It can
trigger validators of its own under §3.1, and the question continues until the
senior slots are spent.

What makes it an AA is one runner-injected block in its brief, built from the
ledger — SH does not write it and cannot soften it:

```
PREMISES ALREADY DISPROVEN — do not rebuild on these:
[p5] REFUTED by v1 — "The 3333 flow's byte profile shows submission, not download"
     disproven by: ibc=5782875 obc=177

A line of reasoning that needs one of these to be true is already known wrong.
```

### 4.2 New SPAWN fields for the hand-over

`SeniorDirective` gains two SPAWN fields. The third thing a replacement needs —
what not to rebuild on — is filled by the runner from the ledger, so SH cannot omit
it:

| Field | Who fills it | Content |
|---|---|---|
| `deviation` | SH | Where the evidence may lie if the refuted reading was wrong: fields, feeds or entities the retired senior did not touch, and what not to re-walk |
| `inherited_entities` | SH | Entities the retired senior *established* — a host, account, file, window — that carry forward. Dropping a proven entity because it was found elsewhere is how a stuck question is lost |
| *(refuted premises)* | **runner** | Auto-filled from the ledger |

**Gate:** a SPAWN issued while any load-bearing premise is REFUTED must carry a
non-empty `deviation`, or the turn is rejected.

This replaces the prose ALTERNATIVE SENIOR paragraph in `SH_SYSTEM_PROMPT` with
fields SH must fill — the same move spec 1 makes for premises.

### 4.3 Divergence is NOT checked — deliberately

Nothing in this spec verifies that the AA diverges from the senior it replaced.

Two checks were designed and both were dropped:

- **"the value must differ"** — rejected because if the retired senior happened to
  be right, a hard check forces the AA away from the correct answer and gives it no
  way to report "I checked, and the original value holds for a different reason."
- **"the AA must not re-derive a refuted premise"** — rejected because code cannot
  do this from free text. Any implementation is a fuzzy string match, which is the
  exact class of mechanism spec 1 exists to delete; it would reintroduce `_label()`
  under a new name.

**What stands in their place is the brief itself.** §4.1 puts every REFUTED premise
in front of the AA verbatim, with the evidence that disproved it, and states that a
line of reasoning needing one of them is already known wrong. That is explicit
instruction, not inference.

Whether the AA obeys it is an **observation, not a gate**. The run will show whether
a replacement rebuilds on ground it was told was disproven. If it does, that is the
point at which to design a check — with a real example of the failure in hand rather
than a guess at its shape.

Spec 1 §3.8 still applies and is unaffected: an ANSWER may not cite a REFUTED
premise id. That is a direct contradiction, trivially checkable, and a different
thing from judging whether reasoning was rebuilt.

## 5. Risks

**Cost.** Worst case per question is `seniors × MAX_VALIDATORS_PER_SENIOR` = 3 × 3 =
9 extra workers. At v1.4.2's Q216 cost of $0.86 that is a large multiple, and the
cost-limited-runs policy is active. The provisional caps in §7 are deliberately
tight for this reason, and §8's first run is a single question.

**The trigger may fire on almost every question, or almost never.** `load_bearing`
is set by the senior, and a senior with an incentive to look thorough may mark
everything load-bearing — inflating validator spend — or mark nothing, disabling the
trigger. §7.5 is the mitigation and §8.2 the measurement.

**A blind validator may flounder.** §3.2 withholds context on purpose. If it spends
8 iterations discovering which feed it is even in, the verdict is worthless and the
spend is wasted. §7.4 covers the fallback: add the senior's SPL list, which leaks
less than the reports do.

**Automatic retirement could cost a productive senior.** The trigger retires a
senior mid-question without SH's consent. If the candidate-unchanged condition is
too loose, a senior making real progress on other fronts is lost. §7.5.

## 6. Testing

- the trigger fires when a load-bearing premise is UNVERIFIED for `VALIDATE_AFTER_ROUNDS` with the candidate unchanged, and not when the candidate moved
- the trigger does not fire past `MAX_VALIDATORS_PER_SENIOR`
- a validator's VERIFIED without a quote from its own tool output is refused
- a validator REFUTING a premise blocks the retired senior's answer with no remedy
- a validator leaving a premise UNVERIFIED keeps it blocking
- a validator consumes no senior spawn slot
- the AA's brief contains every REFUTED premise verbatim, with SH unable to alter it
- a SPAWN with a REFUTED load-bearing premise and empty `deviation` is rejected
- the validator's prompt contains no part of the question text (leakage regression guard)

Not tested, because not enforced (§4.3): that the AA's candidate differs from the
retired senior's, or that its reasoning avoids a refuted premise. Both are
**observed** in the run log instead — see §8.2.

## 7. Open parameters — set these from data, not from judgement

**Every value in this table is provisional and none of it is a design decision.**
The numbers came from the user's initial sketch, not from evidence. Before
implementing §3, read `log/temp/<run>/premise_ledger.json` from spec 1's Q216 run
and set them per §8 — which also says what to do if that file is missing.

| | Parameter | Provisional | What decides it |
|---|---|---|---|
| 7.1 | `MAX_VALIDATORS_PER_SENIOR` | 3 | How many load-bearing UNVERIFIED premises a real question actually produces. If the median is 1, 3 is dead weight; if it is 6, 3 validates an arbitrary third |
| 7.2 | `VALIDATOR_ROUNDS` | 1 | Whether validators conclude within one round or routinely run out |
| 7.3 | `VALIDATOR_ITERS` | 8 | Iterations actually used by validators that *did* conclude. If they conclude at 3, cut it; if they cap out at 8, the briefing is too thin (see 7.4) |
| 7.4 | Validator briefing content | premise + `evidence` only | Whether a blind validator can search efficiently. Fallback if not: add the senior's `spl_used` list — queries leak less than reports do. Last resort: a sanitized problem statement, which puts the biased party back in the loop |
| 7.5 | Trigger tightness | `load_bearing` + 2 rounds + candidate unchanged | The observed distribution of `load_bearing`. If seniors mark everything load-bearing, add a cap on load-bearing premises per report or have SH set the flag instead |

`VALIDATE_AFTER_ROUNDS` = 2 is folded into 7.5.

## 8. How the first run sets §7

> **Do not start implementing §3 until §8.1 has been read off a real spec 1 run.**
> Every parameter in §7 is a guess until then, and one of the readings can
> invalidate §3.1 outright.

The Q216 smoke run that validates spec 1 produces every number above, **before any
of this spec is implemented**. It costs nothing extra: the ledger is already being
measured, and these are reads of the same data.

### Where to read it

Spec 1's Q216 run is a smoke run, so under the project's logging rules it lands in
`log/temp/<run name>/` (not `log/v1/`, and not cost-tracked). The artifacts:

| Artifact | Holds |
|---|---|
| `log/temp/<run>/premise_ledger.json` | the full ledger per question, every premise with its status history. **Spec 1 must emit this** — see spec 1 §7 |
| `log/temp/<run>/<qid>/reports/s*_round_*.md` | the per-round reports |
| `log/temp/<run>/run_summary.json` | delegations, grades, per-worker state |
| `log/temp/<run>/<qid>/conversation.md` | SH's turns, routes and rejections |

If `premise_ledger.json` is absent, the run did not log what this spec needs and the
numbers below cannot be taken from the reports alone — the ledger's status *history*
is the point, and a report shows only its end state. Re-run rather than estimate.

**8.1 — from the spec 1 Q216 run, no code from this spec required:**

- count of premises per report, and the share marked `load_bearing` → **7.1, 7.5**
- how many load-bearing premises are still UNVERIFIED at round 2 with the candidate
  unchanged, i.e. how often the trigger *would* have fired → **7.1, 7.5**
- whether the Q216 byte-profile premise is among them. If it is, the trigger is
  correctly aimed at the bug that motivated it. If it is not, the trigger condition
  is wrong and §3.1 needs rewriting before anything is built

**8.2 — from the first run with validators, once §3 ships:**

- iterations used by validators that reached a verdict → **7.3**
- share of validators returning UNVERIFIED (failed to settle) → **7.2, 7.4**. A high
  share means the blind briefing is too thin, not that the premises are hard
- validator cost as a share of question cost → sanity check against §5
- **did the AA rebuild on a REFUTED premise it was explicitly handed?** (§4.3). Read
  its ledger entries against the refuted list by hand. If it did, that is the
  evidence needed to design a check — and the shape of the real failure beats a
  guess at it. If it did not, the brief was enough and no check is owed

**8.3 — recording.** Write the measured values into this file's §7 table alongside
the provisional ones, with the run they came from. Do not silently replace them:
the provisional number and the reason it was wrong are the useful record.

## 9. Files

| File | Change |
|---|---|
| `agent/v1/validator.py` | **new** — the validation worker: prompt, one-round runner, ledger write-back |
| `agent/v1/premise.py` | trigger predicate (`needs_validation`), validator accounting |
| `agent/v1/question_state.py` | `validators_spent` per senior; validators consume no spawn slot |
| `agent/v1/sh_loop.py` | automatic retire-and-spawn on the trigger; AA brief injection |
| `agent/v1/conversation.py` | SPAWN gains `deviation` + `inherited_entities`; the `deviation` gate |
| `agent/v1/tests/` | as §6 |
