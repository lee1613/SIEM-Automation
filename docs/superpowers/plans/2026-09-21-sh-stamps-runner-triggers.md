# SH Stamps, The Runner Triggers, The AA Replaces — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the power to verify a premise away from SH, give it a per-premise stamp instead, and make a false stamp the one thing that retires a senior and spawns an independent validator.

**Architecture:** Three parties with hard-separated powers. A **senior** files premises and verifies them from its own searches. **SH** files premises, *stamps* a senior's verifications (an annotation, never an edit), grades, nominates and routes — and settles nothing, because it has no Splunk access. A **validator** verifies or refutes one premise from its own searches, blind to the question. The runner enforces all of it: R4 becomes a ceiling it computes, a false stamp retires the senior and fires a validator without asking SH, and the refuted-premise block is filled into every senior's brief from the ledger.

**Tech Stack:** Python 3.11, pydantic v2 (strict `json_schema` structured output), pytest, ruff. No new dependencies.

**Spec:** `docs/version_architecture/v1/v1.4.3.md`, section *"Revision — SH stamps, the runner triggers, the AA replaces (2026-09-21)"* (status there: *designed, not built*). It supersedes `docs/superpowers/specs/2026-09-20-validation-agent-design.md` §3.1 and §7, and finally builds that spec's §4.

**Two decisions taken with the user before writing this plan (they are not in the spec text):**

1. **What lifts a refutation block.** The existing escape in `conversation.ledger_violations` stays: a same-kind premise VERIFIED *by a validator* clears the block. SH reaches it by stamping the replacement false and nominating it, which costs a senior slot like any other false stamp. The spec's *"the REFUTED block never lifts"* therefore means only *"it does not lift when the budget runs out"* — the contrast it draws with the UNVERIFIED block.
2. **When SH nominates.** On the same turn as the false stamp. A turn carrying a false stamp must also carry `nominate_premise_id`, or it is rejected. No grade conjunction fires anything — the spec measured `R1/R2/R3 = PASS and R4 != PASS` at zero occurrences in both r2 runs.

**Where the changelog goes:** `docs/version_architecture/v1/v1.4.3.md`. Per `CLAUDE.md`, a version is in progress until its own first **full** `run_all_v1.py` run completes; v1.4.3 has only had smoke runs, so it is still in progress and the revision spec already lives in that file. Every task below writes its changelog line in the same commit as its code.

---

## File Structure

| File | Responsibility after this plan |
|---|---|
| `agent/v1/premise.py` | The ledger. Gains the stamp (`stamp`, `stamp_reason`, `stamp_premise`, `unstamped`, `false_stamped`, `nominatable`), the selection `rival` requirement, the refusal of any settlement authored by `"sh"`, and refuted-premise rendering into every senior's brief. Loses the `definition` kind. |
| `agent/v1/conversation.py` | The SH turn schema and the gates. Gains `PremiseStamp`, `premise_stamps`, `nominate_premise_id`, `deviation`, `inherited_entities`, and four gates: `stamp_violations`, `grade_ceiling_violations`, `nomination_violations`, `deviation_violations`. Loses `premise_updates` and `sh_update_violations`. |
| `agent/v1/sh_loop.py` | The loop and both prompts. Applies stamps, fires the retire-and-validate trigger, builds the AA's spawn directive. `_run_validators` becomes nomination-driven. |
| `agent/v1/validator.py` | The validation worker. `brief_for` gains its second mode; `as_refutation` turns an UNVERIFIED verdict into a refutation. `MAX_VALIDATORS_PER_QUESTION` is deleted. |
| `agent/v1/finding.py` | The senior's `submit_finding` contract: parses `rival`, drops `definition`. |
| `agent/v1/tests/` | New: `test_stamp.py`, `test_alternative_agent.py`. Extended: `test_premise.py`, `test_conversation_routes.py`, `test_sh_loop.py`, `test_validator.py`, `test_validator_bypass.py`. |

`agent/v1/question_state.py` is **not** touched: the spec's budget rule ("retirement consumes a slot, so the mechanism self-caps") is already how spawn slots work — a slot is spent at spawn and retirement never returns it.

---

### Task 1: Open the changelog for the revision

**Files:**
- Modify: `docs/version_architecture/v1/v1.4.3.md` (append at end of file)

- [ ] **Step 1: Append the changelog section**

Add this to the very end of `docs/version_architecture/v1/v1.4.3.md`:

```markdown

---

## Changelog — building the revision (2026-09-21)

The revision above, implemented. Entries are added as each change lands, per
`CLAUDE.md`'s rule that every code change is recorded in the in-progress version's doc
in the same turn as the change.

- (entries follow)
```

- [ ] **Step 2: Commit**

```bash
git add docs/version_architecture/v1/v1.4.3.md
git commit -m "docs(v1.4.3): open the changelog for the revision

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 2: Delete the `definition` kind

The distinction was wrong. `p3` — *"whether it is the wall-clock span `max(fes)-min(fss)` or the sum of per-flow durations is unresolved and changes the answer"* — was called unfalsifiable by search, but *do these records overlap in time* is a query. The genuinely interpretive part (*which records are the act*) is a **selection** claim and always was; `p12` was a selection claim wearing the definition label, which is exactly why it could be "verified". A measurement ambiguity becomes an open question from the senior to SH — existing machinery, hard-gated.

**Files:**
- Modify: `agent/v1/premise.py:29`, `:78-82`, `:117`
- Modify: `agent/v1/finding.py:135`
- Modify: `agent/v1/sh_loop.py:128` (SH_SYSTEM_PROMPT), `:170` (SENIOR_BRIEF)
- Test: `agent/v1/tests/test_premise.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_premise.py`:

```python
def test_definition_is_no_longer_a_kind():
    """A measurement ambiguity is an open question to SH, not a premise: no search
    settles "span or sum", while "do these records overlap" is a query. p12 was a
    selection claim wearing the label, which is why it could be "verified"."""
    from premise import KINDS
    assert KINDS == ("coverage", "selection", "other")
    with pytest.raises(ValidationError):
        PremiseDraft(text="the measure is the wall-clock span", kind="definition",
                     load_bearing=True)


def test_a_senior_still_saying_definition_keeps_its_claim_as_other():
    """finding._drafts maps an unknown kind to 'other' rather than dropping the draft,
    so a senior on an older habit loses the label, never the premise."""
    from finding import _drafts
    [d] = _drafts([{"text": "the measure is the wall-clock span", "kind": "definition"}])
    assert d.kind == "other"
    assert d.text == "the measure is the wall-clock span"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_premise.py -k definition -v`
Expected: FAIL — `test_definition_is_no_longer_a_kind` fails on the `KINDS` assertion (it is still the four-tuple).

- [ ] **Step 3: Narrow the kinds in `premise.py`**

Replace line 29:

```python
KINDS = ("coverage", "selection", "other")
```

Replace `PremiseDraft.kind` (lines 78-82):

```python
    kind: Literal["coverage", "selection", "other"] = Field(
        description="'coverage': the ways the question's concept could show up in the "
                    "data. 'selection': why this entity and not another candidate. "
                    "'other': anything else your conclusion or next step rests on.")
```

Replace `Premise.kind` (line 117):

```python
    kind: Literal["coverage", "selection", "other"]
```

- [ ] **Step 4: Update the senior's tool contract**

In `agent/v1/finding.py`, replace line 135:

```python
      {"text": ..., "kind": "coverage"|"selection"|"other",
```

- [ ] **Step 5: Update both prompts**

In `agent/v1/sh_loop.py`, inside `SH_SYSTEM_PROMPT` at line 128, delete this sentence from the "BEFORE ANY ANSWER" paragraph (leave the rest of the paragraph intact):

```
When the answer is a measurement, a `definition` premise: its meaning taken from the question's verbatim words, not your framing and not a rule a senior states - a senior citing a rule is not a result.
```

In `SENIOR_BRIEF`, replace the whole of line 170 with:

```
WHEN THE ANSWER IS A MEASUREMENT, take its meaning from the question's verbatim words, not from a paraphrase: which records are the act itself rather than the setup or aftermath around it, and how they combine. Records that overlap in time cannot be added without counting the same moments twice. WHICH records are the act is a `selection` premise, and a query settles it. If the question's own words leave the measurement genuinely ambiguous — a span or a sum, one unit or another — that is not a premise, because no search settles it: put it to SH in `open_questions`.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_premise.py agent/v1/tests/test_finding_premises.py -v`
Expected: PASS.

- [ ] **Step 7: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: PASS, except `agent/v1/tests/test_ledger_refile_loop.py`, which files a `definition` draft. In that file, change every `kind="definition"` to `kind="other"` and update the surrounding comment to say the triplet is now a pair plus an `other`. Re-run until green.

- [ ] **Step 8: Changelog**

Add under `## Changelog — building the revision (2026-09-21)` in `docs/version_architecture/v1/v1.4.3.md`:

```markdown
- **`definition` is deleted** (`KINDS = ("coverage", "selection", "other")`). The
  distinction was wrong: *do these records overlap in time* is a query, so `p3` was
  never unfalsifiable, and the genuinely interpretive part — which records are the act
  — is a `selection` claim. `p12` was a selection claim wearing the definition label,
  which is exactly why it could be "verified". A measurement ambiguity is now an open
  question from the senior to SH: existing machinery, hard-gated, semantically exact.
  `SENIOR_BRIEF` keeps the interval-arithmetic sentence — *records that overlap in time
  cannot be added without counting the same moments twice* — which is the instruction
  that separates 1758 from 1666. `finding._drafts` maps an unknown kind to `other`, so
  a senior still saying "definition" loses the label, never the premise.
```

- [ ] **Step 9: Commit**

```bash
git add agent/v1/premise.py agent/v1/finding.py agent/v1/sh_loop.py agent/v1/tests/test_premise.py agent/v1/tests/test_ledger_refile_loop.py docs/version_architecture/v1/v1.4.3.md
git commit -m "feat(v1.4.3): delete the definition premise kind

A measurement ambiguity is an open question, not a premise. Which records
are the act is a selection claim and a query settles it.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 3: A selection premise names its rival, and absorption is never silent

Two changes to the singular-selection rule, which itself stays (it is what killed r1's re-file loop).

`s1` in r1 held two live record sets — the `dp=3333` flow and the six CoinHive flows — and the ledger had no way to hold both, so one became a premise and the other stayed prose in a report and was argued away. A selection premise must now name at least one rival record set it beats; the prompt already asked for this in prose, and it becomes a schema requirement. And a draft folded into an existing open premise of the same kind is reported back in that turn's feedback instead of having its text silently discarded.

**Files:**
- Modify: `agent/v1/premise.py` (`PremiseDraft`, `Premise`, `PremiseLedger.add`)
- Modify: `agent/v1/finding.py` (`_drafts`, the `new_premises` docstring)
- Modify: `agent/v1/sh_loop.py` (`SENIOR_BRIEF` line 171)
- Test: `agent/v1/tests/test_premise.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_premise.py`:

```python
def test_a_selection_premise_without_a_rival_is_not_filed():
    """r1's s1 held two live record sets - the dp=3333 flow and the six CoinHive flows.
    The ledger could hold one, so the other stayed prose in a report and was argued
    away. A selection that names no rival is a first match, not a choice."""
    led = PremiseLedger()
    notes = []
    out = led.add([PremiseDraft(text="the 3333 flow is the mining activity",
                                kind="selection", load_bearing=True)],
                  author="s1", round_n=1, notes=notes)
    assert out == []
    assert led.premises == {}
    assert any("rival" in n for n in notes), notes


def test_a_selection_premise_with_a_rival_is_filed():
    led = PremiseLedger()
    led.add([PremiseDraft(text="the 3333 flow is the mining activity", kind="selection",
                          load_bearing=True,
                          rival="the six ws*.coinhive.com HTTPS flows")],
            author="s1", round_n=1)
    assert led.premises["p1"].rival == "the six ws*.coinhive.com HTTPS flows"


def test_absorption_into_an_open_premise_of_the_same_kind_is_reported_back():
    """The kind is singular, so a second open one is a re-file - but the draft's text
    is discarded, and an author never told that believes it filed a claim that does
    not exist."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining surfaces on the stratum port", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    notes = []
    out = led.add([PremiseDraft(text="mining could also surface in DNS", kind="coverage",
                                load_bearing=True)],
                  author="s1", round_n=2, notes=notes)
    assert out[0].id == "p1", "still handed back the premise it owns"
    assert len(led.premises) == 1
    assert any("p1" in n and "discarded" in n for n in notes), notes


def test_refiling_the_same_text_is_silent():
    """The carry-forward block hands a senior its own open premises back every round,
    so re-filing one verbatim is the expected case and not worth a note."""
    led = PremiseLedger()
    draft = PremiseDraft(text="mining surfaces on the stratum port", kind="coverage",
                         load_bearing=True)
    led.add([draft], author="s1", round_n=1)
    notes = []
    led.add([draft], author="s1", round_n=2, notes=notes)
    assert notes == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_premise.py -k "rival or absorption or refiling" -v`
Expected: FAIL — `PremiseDraft` has no `rival` field (`ValidationError`), and the absorption test finds no note.

- [ ] **Step 3: Add `rival` to the draft and the premise**

In `agent/v1/premise.py`, add to `PremiseDraft` after the `load_bearing` field:

```python
    rival: str = Field(
        default="",
        description="Required on a 'selection' premise: at least one OTHER record set "
                    "that could fit the question and that you are claiming this one "
                    "beats, and the query that ruled it out. A selection naming no "
                    "rival is a first match, not a choice.")
```

Add to `Premise` after `load_bearing`:

```python
    rival: str = ""
```

- [ ] **Step 4: Enforce both rules in `add`**

In `PremiseLedger.add`, replace the body of the `for d in drafts or []:` loop (everything from `key = _match_form(d.text)` through the `return out`) with:

```python
        for d in drafts or []:
            rival = (getattr(d, "rival", "") or "").strip()
            if d.kind == "selection" and not rival:
                if notes is not None:
                    notes.append(
                        "selection premise not filed: name in `rival` at least one other "
                        "record set that could fit and that this one beats, with the "
                        "query that ruled it out - a selection naming no rival is a "
                        f'first match, not a choice. Your text: "{d.text[:80]}"')
                continue
            key = _match_form(d.text)
            same_text = next((p for p in self.premises.values()
                              if p.author == author and _match_form(p.text) == key), None)
            if same_text is not None:
                # The carry-forward block hands a senior its own open premises back
                # every round, so re-filing one verbatim is expected, not an error.
                out.append(same_text)
                continue
            open_of_kind = next((p for p in self.premises.values()
                                 if p.author == author and p.kind == d.kind
                                 and p.status == "UNVERIFIED"), None)
            if open_of_kind is not None:
                # No silent absorption. The draft's text is discarded here, and an
                # author never told that believes it filed a claim that does not exist.
                if notes is not None:
                    notes.append(
                        f"{d.kind} premise not filed: you already have an open {d.kind} "
                        f"premise {open_of_kind.id} - amend or settle that one. The text "
                        f'you sent was discarded: "{d.text[:80]}"')
                out.append(open_of_kind)
                continue
            self._n += 1
            p = Premise(id=f"p{self._n}", author=author, kind=d.kind, text=d.text,
                        load_bearing=bool(d.load_bearing), rival=rival,
                        round_first_seen=round_n,
                        history=[{"round": round_n, "status": "UNVERIFIED",
                                  "by": author, "quote": "", "evidence": ""}])
            self.premises[p.id] = p
            out.append(p)
            quote = getattr(d, "quote", "")
            if quote:
                refused = self.apply(
                    [PremiseUpdate(id=p.id, status="VERIFIED", quote=quote,
                                   evidence=getattr(d, "evidence", ""))],
                    author=author, corpus=corpus or [], round_n=round_n)
                if notes is not None:
                    notes.extend(refused)
        return out
```

- [ ] **Step 5: Parse `rival` off the senior's tool call**

In `agent/v1/finding.py`, inside `_drafts`, add the field to the `PremiseDraft(...)` construction:

```python
            out.append(PremiseDraft(text=text,
                                    kind=kind if kind in KINDS else "other",
                                    load_bearing=bool(d.get("load_bearing", False)),
                                    rival=str(d.get("rival", "") or "").strip(),
                                    quote=str(d.get("quote", "") or "").strip(),
                                    evidence=str(d.get("evidence", "") or "").strip()))
```

And in the `new_premises` docstring (around line 135), replace the object shape line with:

```python
      {"text": ..., "kind": "coverage"|"selection"|"other",
       "load_bearing": true|false, "rival": ..., "quote": ..., "evidence": ...}.
       `rival` is REQUIRED on a "selection" premise: another record set that could
       fit and that this one beats, with the query that ruled it out. A selection
       naming no rival is not filed, and the runner says so.
```

- [ ] **Step 6: Update the senior's brief**

In `agent/v1/sh_loop.py`, replace line 171 of `SENIOR_BRIEF`:

```
THE PREMISE MOST OFTEN MISSED IS THE CHOICE ITSELF. Then choose from that full set. Your `selection` premise says why this entity (or feed, or value) and not the other candidates coverage found, and it must NAME one of them in `rival`, with the query that ruled it out — a selection naming no rival is not filed at all. When two record sets are both still live, that is two candidates, not one premise: settle the first before filing the second, or say in `rival` why one beats the other.
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_premise.py -v`
Expected: PASS.

- [ ] **Step 8: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failures in every test that files a `kind="selection"` draft without a rival — `test_sh_loop.py` (its `PREMISES` constant), `test_ledger.py`, `test_ledger_wiring.py`, `test_validator_bypass.py`, `test_conversation_routes.py`. Fix each by adding a rival to the draft, e.g. in `test_sh_loop.py`:

```python
PREMISES = [PremiseDraft(text="mining could surface as stratum or DNS", kind="coverage",
                         load_bearing=True),
            PremiseDraft(text="this endpoint and not another", kind="selection",
                         load_bearing=True, rival="the two other hosts in the window")]
```

Re-run until green.

- [ ] **Step 9: Changelog**

```markdown
- **A selection premise must name its rival** (`PremiseDraft.rival`, enforced in
  `PremiseLedger.add`). The prompt already asked for this in prose; it is now a schema
  requirement, and a selection naming no rival is not filed at all. r1's `s1` held two
  live record sets — the `dp=3333` flow and the six CoinHive flows — and the ledger
  could hold one, so the other stayed prose in a report and was argued away.
- **No more silent absorption.** A draft folded into an existing open premise of the
  same kind is reported back in that turn's feedback ("you already have an open
  selection premise p2; amend or settle it") instead of having its text discarded with
  no one told. Re-filing the same text stays silent — the carry-forward block invites
  it every round.
```

- [ ] **Step 10: Commit**

```bash
git add agent/v1/premise.py agent/v1/finding.py agent/v1/sh_loop.py agent/v1/tests/
git commit -m "feat(v1.4.3): a selection premise names its rival; absorption is reported

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 4: SH settles nothing

The largest single change. In r1 SH settled **19 of 28** premises — all 18 it authored, plus `s1`'s `p3`, `s2`'s `p20` and `s3`'s `p27`. The premises that lost Q216 (`p10`/`p11`/`p12`, the triplet that discarded the CoinHive reading) were filed by SH and verified by SH in the same round. SH has no Splunk access and never will, so "SH verified it" has always meant "SH read a report and decided" — which is the stamp (Task 5), and the stamp is explicitly not an edit.

Two enforcement points, because the schema alone is not enough: `PremiseDraft.quote` also settles a premise, through `add`'s file-and-settle path.

**Files:**
- Modify: `agent/v1/conversation.py` (delete `premise_updates` from `SeniorDirective`; delete `sh_update_violations`)
- Modify: `agent/v1/premise.py` (`PremiseLedger.apply` refuses `author="sh"`)
- Modify: `agent/v1/sh_loop.py` (drop the `sh_update_violations` call and the SH `apply` call)
- Test: `agent/v1/tests/test_premise.py`, `agent/v1/tests/test_conversation_routes.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_premise.py`:

```python
SH_QUOTE = '{"dest_port": "3333", "count": "3"}'


def test_sh_cannot_verify_a_premise():
    """r1: SH settled 19 of 28 premises, and the triplet that lost Q216 was filed by SH
    and verified by SH in the same round. SH has no Splunk access, so "SH verified it"
    has only ever meant "SH read a report and decided" - which is the stamp."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining surfaces on the stratum port", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    notes = led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=SH_QUOTE,
                                     evidence="the port census")],
                      author="sh", corpus=[SH_QUOTE], round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert notes and "does not settle premises" in notes[0]


def test_sh_cannot_refute_a_premise_either():
    """'Verify' is read as 'settle', in either direction. SH's channel for disbelief is
    the stamp, which costs it a senior slot and is on the record."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining surfaces on the stratum port", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=SH_QUOTE, evidence="no")],
              author="sh", corpus=[SH_QUOTE], round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"


def test_sh_cannot_file_and_settle_in_one_step():
    """`PremiseDraft.quote` is the other way a premise reaches VERIFIED, and it routes
    through the same `apply`, so one guard closes both."""
    led = PremiseLedger()
    notes = []
    led.add([PremiseDraft(text="every route was covered", kind="coverage",
                          load_bearing=True, quote=SH_QUOTE, evidence="the census")],
            author="sh", round_n=4, corpus=[SH_QUOTE], notes=notes)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert notes and "does not settle premises" in notes[0]


def test_a_senior_and_a_validator_still_settle():
    led = PremiseLedger()
    led.add([PremiseDraft(text="mining surfaces on the stratum port", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    assert led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=SH_QUOTE,
                                    evidence="the port census")],
                     author="s1", corpus=[SH_QUOTE], round_n=2) == []
    assert led.premises["p1"].verified_by == "s1"
    assert led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=SH_QUOTE,
                                    evidence="a full dh scan shows another route")],
                     author="v1", corpus=[SH_QUOTE], round_n=3) == []
    assert led.premises["p1"].verified_by == "v1"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_premise.py -k "sh_cannot or still_settle" -v`
Expected: FAIL — `apply` takes SH's verdict and `p1` is VERIFIED.

- [ ] **Step 3: Refuse any settlement authored by SH**

In `agent/v1/premise.py`, inside `PremiseLedger.apply`, insert at the very top of the `for u in updates or []:` loop, before `p = self.premises.get(u.id)`:

```python
            if author == "sh":
                # SH has no Splunk access, so "SH verified it" has only ever meant "SH
                # read a report and decided". That reading is the stamp, which is an
                # annotation, costs a senior slot when it is false, and is on the
                # record. r1: SH settled 19 of 28 premises, including the triplet that
                # lost the question.
                notes.append(
                    f"{u.id} unchanged: SH does not settle premises. Your reading of a "
                    "senior's verification goes in `premise_stamps`; a premise reaches "
                    "VERIFIED from the senior whose search shows it, or from an "
                    "independent validator.")
                continue
```

Update the `apply` docstring's opening to:

```python
        """Apply this round's verdicts. Returns a note per REJECTED update.

        Only a senior or a validator settles anything: an update authored by "sh" is
        refused whatever it says, because SH has no Splunk access and never will.
```

- [ ] **Step 4: Remove SH's settling channel from the schema**

In `agent/v1/conversation.py`, delete the `premise_updates` field from `SeniorDirective` (lines 161-165) entirely. Delete the whole `sh_update_violations` function (lines 394-414). Then run `grep -n "quote_supported\|_CIRCULAR" agent/v1/conversation.py` and delete the now-unused imports it reports.

- [ ] **Step 5: Drop both call sites in the loop**

In `agent/v1/sh_loop.py`, in `run_question`, replace the ledger-write block (lines 536-549) with:

```python
        ledger_notes: list[str] = []
        for e in turn.entries:
            filed = ledger.add(e.new_premises, author="sh", round_n=state.turns_used,
                               corpus=sh_corpus, notes=ledger_notes)
            # SH cannot cite what it has just filed - the runner owns the ids - so the
            # runner links them. Without this an ANSWER that files its own Coverage
            # premise is rejected for "citing an id that is not a premise", which SH
            # cannot act on; with it, the rejection is the true one: that premise is
            # UNVERIFIED, go and get a senior to settle it.
            if e.route == "ANSWER":
                e.answer_premise_ids = list(e.answer_premise_ids) + [
                    p.id for p in filed if p.id not in e.answer_premise_ids]
```

Then delete the `sh_update_violations(...)` clause from the `problems = ...` chain (lines 574-580), leaving the chain as `grade_violations(...) + directive_violations(...) + open_question_violations(...) + spawn_overlap_violations(...) + premise_audit_violations(...) + ledger_violations(...)`. Remove `sh_update_violations` from the `from conversation import (...)` list at the top of the file.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_premise.py -v`
Expected: PASS.

- [ ] **Step 7: Repoint the bypass tests off SH**

`agent/v1/tests/test_validator_bypass.py` builds its ledger by having SH verify a premise, which no longer works. Replace `_ledger_with_validator_refutation` with:

```python
def _ledger_with_validator_refutation():
    """s1 files a coverage premise, verifies it itself, a validator refutes it.

    r2's shape exactly: the senior filed all three premises and verified all three of
    its own. SH cannot do this any more; a senior still can, and that is the
    self-certification the validator exists to break."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="coverage: only the stratum port matters",
                          kind="coverage", load_bearing=True)], author="s1", round_n=2)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=RESULT,
                             evidence="the port census")],
              author="s1", corpus=[RESULT], round_n=2)
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=RESULT,
                             evidence="a full dh scan shows coinhive, an uncovered route")],
              author="v1", corpus=[RESULT], round_n=3)
    return led
```

In `test_a_validator_refutation_blocks_an_answer_that_does_not_cite_it` and `test_a_replacement_the_author_verified_itself_does_not_unblock`, change the replacement premise's `author="sh"` to `author="s2"` in both the `add` and the `apply` call. The point of both tests is unchanged: a replacement its own author verified does not clear a validator's refutation.

- [ ] **Step 8: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failures in `test_conversation_routes.py` (imports `sh_update_violations`, and `BLANK` carries `"premise_updates": []`) and `test_sh_loop.py` (same `BLANK`). Fix by deleting the `sh_update_violations` import and its tests from `test_conversation_routes.py`, and removing `"premise_updates": []` from the `BLANK` dict in **both** test files. Re-run until green.

- [ ] **Step 9: Changelog**

```markdown
- **SH loses the power to verify** (`PremiseLedger.apply` refuses `author="sh"`;
  `SeniorDirective.premise_updates` and `sh_update_violations` deleted). In r1 SH
  settled 19 of 28 premises — all 18 it authored, plus `s1`'s `p3`, `s2`'s `p20` and
  `s3`'s `p27` — and the triplet that discarded the CoinHive reading was filed by SH
  and verified by SH in the same round. SH has no Splunk access and never will, so "SH
  verified it" has only ever meant "SH read a report and decided": that is the stamp,
  and the stamp is not an edit.

  The guard sits in `apply`, not only in the schema, because `PremiseDraft.quote` is a
  second route to VERIFIED and it routes through the same call. Consequence taken
  deliberately: a premise SH files now starts UNVERIFIED and stays there until a senior
  or a validator settles it, so SH must file it early enough for a senior to reach —
  `render_for_senior` already carries load-bearing premises filed by others to every
  active senior.
```

- [ ] **Step 10: Commit**

```bash
git add agent/v1/premise.py agent/v1/conversation.py agent/v1/sh_loop.py agent/v1/tests/
git commit -m "feat(v1.4.3): SH settles nothing

A premise reaches VERIFIED from the senior whose search shows it or from an
independent validator. SH read a report and decided; that is a stamp.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 5: The stamp — the ledger side

**Files:**
- Modify: `agent/v1/premise.py` (`Premise`, `PremiseLedger`)
- Test: `agent/v1/tests/test_stamp.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `agent/v1/tests/test_stamp.py`:

```python
"""SH's stamp: its reading of one newly-claimed verification (v1.4.3 revision).

The measurement this replaces, across three runs and six seniors: R4 flipped to PASS on
the turn SH stopped investigating, without exception. A single word about a whole report
is easy to wave through. "Does this quote establish this claim as written", asked about
one named premise one round before the answering turn, is the bet.
"""

from premise import PremiseDraft, PremiseLedger, PremiseUpdate

QUOTE = '{"da": "45.77.53.176", "count": "4832", "dp": ["3333", "443", "80"]}'


def _verified_by(author="s1", kind="coverage", text="route (c) is NOT yet searched"):
    led = PremiseLedger()
    led.add([PremiseDraft(text=text, kind=kind, load_bearing=True,
                          rival="the other flows in the window")],
            author=author, round_n=1)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                             evidence="the pool-IP census")],
              author=author, corpus=[QUOTE], round_n=2)
    return led


def test_a_newly_verified_premise_is_owed_a_stamp():
    led = _verified_by()
    assert [p.id for p in led.unstamped("s1")] == ["p1"]


def test_a_stamp_is_an_annotation_never_an_edit():
    """A false-stamped premise stays VERIFIED. Status belongs to the quote rule and the
    validator; the stamp is SH's reading of it, recorded beside it."""
    led = _verified_by()
    assert led.stamp_premise("p1", establishes=False,
                             reason="the claim says route (c) was not searched and the "
                                    "quote is the result of searching it",
                             round_n=3) is True
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].stamp == "false"
    assert "not searched" in led.premises["p1"].stamp_reason


def test_a_premise_is_stamped_once():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, reason="it does", round_n=3)
    assert led.stamp_premise("p1", establishes=False, reason="changed my mind",
                             round_n=4) is False
    assert led.premises["p1"].stamp == "true"


def test_a_stamped_premise_is_no_longer_owed_one():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, reason="it does", round_n=3)
    assert led.unstamped("s1") == []


def test_a_validators_verdict_is_not_stamped():
    """The validator is the thing that outranks the stamp, not something for SH to
    grade. SH files none of its own either, since it can no longer settle."""
    led = _verified_by()
    led.apply([PremiseUpdate(id="p1", status="UNVERIFIED", quote="",
                             evidence="withdrawn")], author="s1", corpus=[], round_n=3)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                             evidence="my own scan")],
              author="v1", corpus=[QUOTE], round_n=4)
    assert led.unstamped("s1") == []
    assert led.unstamped() == []


def test_nominatable_is_what_sh_stamped_false_or_what_the_senior_left_open():
    """It may not range wider: the false stamp is what fired the mechanism, so aiming
    the validator elsewhere would leave the triggering doubt unexamined."""
    led = _verified_by()
    led.stamp_premise("p1", establishes=False, reason="it walks past its own limit",
                      round_n=3)
    led.add([PremiseDraft(text="this flow and not the CoinHive six", kind="selection",
                          load_bearing=True, rival="the six ws*.coinhive.com flows")],
            author="s1", round_n=3)
    led.add([PremiseDraft(text="someone else's open claim", kind="coverage",
                          load_bearing=True)], author="s2", round_n=3)
    assert [p.id for p in led.nominatable("s1")] == ["p1", "p2"]


def test_the_stamp_is_in_the_table_and_the_dump():
    led = _verified_by()
    led.stamp_premise("p1", establishes=False, reason="no", round_n=3)
    assert "stamp" in led.render_table()
    assert "false" in led.render_table()
    [rec] = led.to_records("Q216")
    assert rec["stamp"] == "false" and rec["stamp_reason"] == "no"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_stamp.py -v`
Expected: FAIL with `AttributeError: 'PremiseLedger' object has no attribute 'unstamped'`.

- [ ] **Step 3: Add the stamp to `Premise`**

In `agent/v1/premise.py`, add to `Premise` after `evidence`:

```python
    stamp: Literal["", "true", "false"] = ""
    stamp_reason: str = ""
```

- [ ] **Step 4: Add the ledger methods**

In `agent/v1/premise.py`, add to `PremiseLedger` in the `# -- reading ---` section, after `refuted`:

```python
    def unstamped(self, author: str | None = None) -> list[Premise]:
        """Verifications by a SENIOR that SH has not yet read against their quote.

        Not a validator's: the validator is what outranks the stamp, not something for
        SH to grade. Not SH's own either - it files no verdicts any more.
        """
        return [p for p in self.premises.values()
                if p.status == "VERIFIED" and not p.stamp
                and p.verified_by and p.verified_by != "sh"
                and not is_validator(p.verified_by)
                and (author is None or p.verified_by == author)]

    def false_stamped(self, author: str) -> list[Premise]:
        """Premises this senior claimed VERIFIED and SH read as not establishing them.

        Keyed on `verified_by`, not `author`: the stamp is on the CLAIM, and a senior
        that settles a sibling's premise is the party that claimed it.
        """
        return [p for p in self.premises.values()
                if p.stamp == "false" and p.verified_by == author]

    def nominatable(self, author: str) -> list[Premise]:
        """What SH may point a validator at once it has stamped one of this senior's
        verifications false: what it stamped false, or what this senior left open.

        It may not range wider. The false stamp is what fired the mechanism, so letting
        SH aim the validator elsewhere would retire the senior and leave the triggering
        doubt unexamined.
        """
        by_id = {p.id: p for p in self.false_stamped(author)}
        by_id.update({p.id: p for p in self.premises.values()
                      if p.author == author and p.status == "UNVERIFIED"})
        return sorted(by_id.values(), key=lambda p: int(p.id[1:]))
```

And in the `# -- transitions ---` section, after `apply`:

```python
    def stamp_premise(self, pid: str, *, establishes: bool, reason: str,
                      round_n: int) -> bool:
        """Record SH's reading of one newly-claimed verification. False when the id is
        unknown or already stamped - a stamp is recorded once, when the verification is
        first claimed.

        An annotation, never an edit: the status is untouched. A false-stamped premise
        stays VERIFIED, because status belongs to the quote rule and the validator,
        while the stamp is SH's reading of it.
        """
        p = self.premises.get(pid)
        if p is None or p.stamp:
            return False
        p.stamp = "true" if establishes else "false"
        p.stamp_reason = reason
        p.history.append({"round": round_n, "status": p.status, "by": "sh-stamp",
                          "quote": "", "evidence": f"stamp={p.stamp}: {reason}"})
        return True
```

- [ ] **Step 5: Show the stamp to SH and to the dump**

Replace `render_table`'s body (keeping its docstring) with:

```python
        if not self.premises:
            return "PREMISE LEDGER - no premises filed yet."
        rows = ["PREMISE LEDGER",
                f"{'id':<4} {'kind':<10} {'status':<11} {'LB':<3} {'stamp':<6} "
                f"{'since':<6} who / text"]
        for p in self.premises.values():
            by = f"[{p.verified_by}] " if p.verified_by else ""
            text = p.text if len(p.text) <= 70 else p.text[:70] + "…"
            rows.append(f"{p.id:<4} {p.kind:<10} {p.status:<11} "
                        f"{'Y' if p.load_bearing else 'n':<3} {p.stamp or '-':<6} "
                        f"r{p.round_first_seen:<5} {by}{p.author}: {text}")
        return "\n".join(rows)
```

In `to_records`, add two keys to the dict, after `"verified_by": p.verified_by,`:

```python
            "stamp": p.stamp,
            "stamp_reason": p.stamp_reason,
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_stamp.py -v`
Expected: PASS (8 tests).

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest agent/v1/tests -q`
Expected: PASS. If `test_ledger.py` asserts on the exact `render_table` header, update the expected string to include the `stamp` column.

- [ ] **Step 8: Changelog**

```markdown
- **The stamp, ledger side** (`Premise.stamp` / `stamp_reason`,
  `PremiseLedger.stamp_premise` / `unstamped` / `false_stamped` / `nominatable`). SH
  records, per newly-claimed verification, whether that quote establishes that claim as
  written. It is an annotation and never an edit — a false-stamped premise stays
  VERIFIED, because status belongs to the quote rule and the validator. Once only, on
  first claim. A validator's verdict is never stamped: it is the thing that outranks the
  stamp. `nominatable` is deliberately narrow — what SH stamped false, or what that
  senior left UNVERIFIED — so a firing cannot be aimed away from the doubt that caused
  it. The stamp shows in `render_table` and in `premise_ledger.json`.
```

- [ ] **Step 9: Commit**

```bash
git add agent/v1/premise.py agent/v1/tests/test_stamp.py
git commit -m "feat(v1.4.3): the stamp - SH's reading, recorded beside the status

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 6: The stamp — the turn schema and the mandatory gate

**Files:**
- Modify: `agent/v1/conversation.py` (add `PremiseStamp`, two fields, `stamp_violations`)
- Modify: `agent/v1/sh_loop.py` (call the gate; apply accepted stamps)
- Test: `agent/v1/tests/test_stamp.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_stamp.py`:

```python
from conversation import PremiseStamp, SeniorDirective, stamp_violations

BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RETIRE",
    "open_question_answers": [], "new_premises": [], "answer_premise_ids": [],
    "premise_stamps": [], "nominate_premise_id": "",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "deviation": "", "inherited_entities": "",
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}


def entry(**kw) -> SeniorDirective:
    return SeniorDirective(**{**BLANK, **kw})


def _command(**kw):
    return entry(route="COMMAND", senior_id="s1", decision="continue",
                 directive="go further", r1_scope_alignment="PASS",
                 r2_progress="PASS", r3_answer_readiness="WEAK",
                 r4_premise_verification="WEAK", **kw)


def test_a_turn_leaving_a_new_verification_unstamped_is_rejected():
    led = _verified_by()
    out = stamp_violations([_command()], led)
    assert out and "p1" in out[0]


def test_a_stamped_verification_passes_the_gate():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(
            id="p1", establishes=False,
            reason="the claim says route (c) was not searched; the quote is the "
                   "result of searching it")])],
        led)
    assert out == []


def test_a_stamp_needs_a_reason():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(id="p1", establishes=True, reason="  ")])],
        led)
    assert out and "no reason" in out[0]


def test_a_premise_stamped_in_an_earlier_turn_is_not_restamped():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, reason="it does", round_n=2)
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(id="p1", establishes=False,
                                               reason="second thoughts")])],
        led)
    assert out and "earlier turn" in out[0]


def test_a_stamp_on_an_unknown_id_is_rejected():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(id="p9", establishes=True,
                                               reason="it does")])],
        led)
    assert out and "not a premise" in out[0]


def test_a_stamp_may_arrive_on_a_different_entry_of_the_same_turn():
    """The turn is judged as a whole: SH may stamp in one entry and route in another."""
    led = _verified_by()
    out = stamp_violations(
        [entry(route="RETIRE", senior_id="s1", reason="done",
               premise_stamps=[PremiseStamp(id="p1", establishes=True,
                                            reason="the census covers it")]),
         _command(senior_id="s2")],
        led)
    assert out == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_stamp.py -k "gate or stamped or restamped or unknown_id or different_entry" -v`
Expected: FAIL — `ImportError: cannot import name 'PremiseStamp' from 'conversation'`.

- [ ] **Step 3: Add the model and the fields**

In `agent/v1/conversation.py`, add after the `QuestionAnswer` class:

```python
class PremiseStamp(BaseModel):
    """SH's reading of one newly-claimed verification. An annotation, not an edit."""

    id: str = Field(description="The premise id, e.g. 'p3'. Copy it exactly.")
    establishes: bool = Field(
        description="Does that quote establish THIS claim, AS WRITTEN? Read the claim's "
                    "own words before the quote: a claim that states its own limit - a "
                    "route not searched, a case not checked, a choice unresolved - is "
                    "NOT established by evidence that walks past the limit. True or "
                    "false, not a grade.")
    reason: str = Field(
        description="One or two sentences: what the quote shows, and why that does or "
                    "does not establish the claim as written.")
```

Add to `SeniorDirective`, in place of the deleted `premise_updates` field:

```python
    premise_stamps: list[PremiseStamp] = Field(
        description="One entry for EVERY premise a report in this wave newly claims "
                    "VERIFIED, for the senior this route addresses. You do not settle "
                    "premises; you read the senior's claim against its own quote and "
                    "record whether it holds. A turn that leaves a new verification "
                    "unstamped is rejected. Premises settled in an earlier turn are not "
                    "re-stamped. A FALSE stamp retires that senior and spawns a "
                    "validator - it is not free, and it is on the record.")
    nominate_premise_id: str = Field(
        description="Required on a turn carrying a FALSE stamp, empty otherwise: the ONE "
                    "premise an independent validator will settle. Choose from what you "
                    "stamped false or what that senior left UNVERIFIED.")
```

- [ ] **Step 4: Write the gate**

In `agent/v1/conversation.py`, add after `open_question_violations`:

```python
def stamp_violations(entries: list, ledger) -> list[str]:
    """Every verification a senior newly claims is read by SH, once, the turn it is
    claimed.

    What this replaces: across three runs and six seniors, R4 flipped to PASS on the
    turn SH stopped investigating, without exception. One word about a whole report is
    easy to wave through. The bet is that a specific per-premise question - does this
    quote establish this claim as written - asked one round before the answering turn
    is materially harder.

    The turn is judged as a whole, so SH may stamp in one entry and route in another.
    """
    out, stamped = [], set()
    for e in entries:
        for s in e.premise_stamps:
            p = ledger.premises.get(s.id)
            if p is None:
                out.append(f"stamp names {s.id}, which is not a premise on this question")
            elif p.stamp:
                out.append(f"{s.id} was stamped in an earlier turn - a stamp is recorded "
                           "once, when the verification is first claimed")
            elif not s.reason.strip():
                out.append(f"stamp on {s.id} gives no reason - say what the quote shows, "
                           "and why that does or does not establish the claim as written")
            else:
                stamped.add(s.id)
    addressed = {(e.source_senior if e.route == "ANSWER" else e.senior_id)
                 for e in entries}
    for sid in sorted(a for a in addressed if a):
        missing = sorted((p.id for p in ledger.unstamped(sid) if p.id not in stamped),
                         key=lambda i: int(i[1:]))
        if missing:
            out.append(
                f"{sid} newly claims {', '.join(missing)} VERIFIED and you have not read "
                "them - one `premise_stamps` entry each: does that quote establish that "
                "claim as written, and why")
    return out
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_stamp.py -v`
Expected: PASS.

- [ ] **Step 6: Wire the gate and apply accepted stamps**

In `agent/v1/sh_loop.py`, add `stamp_violations` to the `from conversation import (...)` list and to the `problems = ...` chain:

```python
        ) + premise_audit_violations(
            turn.entries, ledger
        ) + stamp_violations(
            turn.entries, ledger
        ) + ledger_violations(turn.entries, ledger, state)
```

Then, immediately after the accepted-turn open-question block (the `for e in turn.entries: ... ledger.answer(a.id, a.answer)` loop), add:

```python
        # The stamp is recorded only on an accepted turn, like the open-question
        # answers: a rejected turn's stamps would burn the one chance each premise gets.
        for e in turn.entries:
            for s in e.premise_stamps:
                ledger.stamp_premise(s.id, establishes=s.establishes, reason=s.reason,
                                     round_n=state.turns_used)
```

- [ ] **Step 7: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failures in `test_conversation_routes.py` and `test_sh_loop.py`, whose `BLANK` dicts lack the two new required fields. Add `"premise_stamps": [], "nominate_premise_id": "",` to `BLANK` in both files.

`test_sh_loop.py` will then fail on the new gate, because its fake senior verifies `p1` every round and no scripted turn stamps it. Fix by adding stamps to the answering turn — in `_answer`, extend the base dict:

```python
def _answer(value="1367.875", **kw):
    base = dict(route="ANSWER", value=value, value_kind="duration_seconds",
                source_senior="s1", justification="s1 round 1 showed it.",
                answer_premise_ids=["p1"],
                premise_stamps=[PremiseStamp(
                    id="p1", establishes=True,
                    reason="the 22-value port listing covers every route")],
                r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
                r4_premise_verification="PASS")
    base.update(kw)
    return entry(**base)
```

and add `from conversation import PremiseStamp` at the top of `test_sh_loop.py`. Re-run until green.

- [ ] **Step 8: Changelog**

```markdown
- **The stamp is mandatory** (`conversation.PremiseStamp`,
  `SeniorDirective.premise_stamps`, `stamp_violations`). A turn that leaves a
  newly-claimed verification unread is rejected. It is due the round the verification is
  claimed, not at ANSWER: for r2 that puts `p1`'s stamp at round 3, where SH graded
  `R3=WEAK` and was still investigating — one round before the moment R4 has flipped to
  PASS in every run we have. The turn is judged as a whole, so SH may stamp in one entry
  and route in another. Stamps are applied only on an accepted turn, like the
  open-question answers: a rejected turn's stamps would burn the one chance each premise
  gets.
```

- [ ] **Step 9: Commit**

```bash
git add agent/v1/conversation.py agent/v1/sh_loop.py agent/v1/tests/
git commit -m "feat(v1.4.3): the stamp is mandatory, and due the round it is claimed

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 7: R4 becomes a runner-enforced ceiling

R4 was a permission slip. Every grade SH gave, across three runs and six seniors, flipped to PASS on the turn SH stopped investigating — no exceptions. The grade now **records**; it triggers nothing, and the runner holds the facts that cap it.

**Files:**
- Modify: `agent/v1/conversation.py` (`r4_ceiling`, `grade_ceiling_violations`, R4's field description)
- Modify: `agent/v1/sh_loop.py` (call the gate; R4's prompt paragraph)
- Test: `agent/v1/tests/test_stamp.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_stamp.py`:

```python
from conversation import grade_ceiling_violations, r4_ceiling


def test_pass_is_refused_while_a_load_bearing_premise_is_unverified():
    led = PremiseLedger()
    led.add([PremiseDraft(text="every route enumerated", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    e = _command(r4_premise_verification="PASS")
    assert r4_ceiling("s1", e, led) == "WEAK"
    assert grade_ceiling_violations([e], led)


def test_pass_is_refused_on_a_turn_carrying_a_false_stamp():
    led = _verified_by()
    e = _command(r4_premise_verification="PASS",
                 premise_stamps=[PremiseStamp(id="p1", establishes=False,
                                              reason="it walks past its own limit")])
    assert r4_ceiling("s1", e, led) == "WEAK"
    assert grade_ceiling_violations([e], led)


def test_a_refuted_load_bearing_premise_forces_fail():
    led = _verified_by()
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=QUOTE,
                             evidence="my own scan of the whole feed")],
              author="v1", corpus=[QUOTE], round_n=4)
    assert r4_ceiling("s1", _command(), led) == "FAIL"
    assert grade_ceiling_violations([_command(r4_premise_verification="WEAK")], led)
    assert grade_ceiling_violations([_command(r4_premise_verification="FAIL")], led) == []


def test_pass_is_allowed_on_clean_ground():
    led = _verified_by()
    e = _command(r4_premise_verification="PASS",
                 premise_stamps=[PremiseStamp(id="p1", establishes=True,
                                              reason="the census covers every route")])
    assert r4_ceiling("s1", e, led) == "PASS"
    assert grade_ceiling_violations([e], led) == []


def test_sh_may_always_grade_below_the_ceiling():
    led = _verified_by()
    e = _command(r4_premise_verification="FAIL",
                 premise_stamps=[PremiseStamp(id="p1", establishes=True,
                                              reason="the census covers every route")])
    assert grade_ceiling_violations([e], led) == []


def test_an_ungraded_entry_has_no_ceiling():
    """A SPAWN grades NA, and an exploration worker is never graded at all."""
    led = _verified_by()
    assert grade_ceiling_violations(
        [entry(route="SPAWN", spawn_type="senior", subquestion="go", deviation="x")],
        led) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agent/v1/tests/test_stamp.py -k ceiling -v`
Expected: FAIL — `ImportError: cannot import name 'r4_ceiling'`.

- [ ] **Step 3: Write the ceiling**

In `agent/v1/conversation.py`, add after `grade_violations`:

```python
def r4_ceiling(sid: str, entry, ledger) -> str:
    """The highest R4 SH may write for this senior: FAIL, WEAK or PASS.

    R4 was a permission slip. Across three runs and six seniors it flipped to PASS on
    the turn SH stopped investigating, without exception, and `premise.py` predicted
    that in prose a version earlier. PASS is a claim about the ground the senior stands
    on, and the runner holds the facts that decide it; the grade now records rather than
    triggers.

    This turn's stamps count, not only the ledger's: SH cannot stamp a verification
    false and grade the same senior's ground sound in the same breath.
    """
    if any(p.load_bearing and p.status == "REFUTED"
           for p in ledger.premises.values()
           if p.author == sid or p.verified_by == sid):
        return "FAIL"
    if any(s.establishes is False for s in entry.premise_stamps):
        return "WEAK"
    if any(p.load_bearing and p.status == "UNVERIFIED"
           for p in ledger.premises.values() if p.author == sid):
        return "WEAK"
    if ledger.false_stamped(sid):
        return "WEAK"
    return "PASS"


def grade_ceiling_violations(entries: list, ledger) -> list[str]:
    """SH may always grade lower than the ceiling, never above it."""
    rank = {"FAIL": 0, "WEAK": 1, "PASS": 2}
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        if not sid or e.r4_premise_verification == NA:
            continue
        cap = r4_ceiling(sid, e, ledger)
        if rank.get(e.r4_premise_verification, 2) > rank[cap]:
            why = ("a load-bearing premise of its is REFUTED" if cap == "FAIL" else
                   "it has a load-bearing premise still UNVERIFIED, or you stamped one "
                   "of its verifications false")
            out.append(f"{sid}: R4 cannot be {e.r4_premise_verification} - {why}. "
                       f"The most you may write is {cap}; lower is always yours.")
    return out
```

- [ ] **Step 4: Rewrite R4's field description**

In `agent/v1/conversation.py`, replace the `r4_premise_verification` field (lines 84-90) with:

```python
    r4_premise_verification: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Is every premise the senior's conclusion or direction rests on "
                    "backed by a result shown in the report? PASS: each has a query and "
                    "result behind it. WEAK: minor premises untested, the chain holds "
                    "without them. FAIL: the candidate or the direction depends on a "
                    "premise nobody tested. The runner CAPS this: PASS is refused while "
                    "that senior has a load-bearing UNVERIFIED premise or a stamp of "
                    "yours reads false, and a REFUTED one forces FAIL. Grade lower than "
                    "the cap whenever you mean it; you may never grade above it.")
```

- [ ] **Step 5: Wire the gate**

In `agent/v1/sh_loop.py`, add `grade_ceiling_violations` to the `from conversation import (...)` list and to the `problems = ...` chain, right after `stamp_violations`:

```python
        ) + stamp_violations(
            turn.entries, ledger
        ) + grade_ceiling_violations(
            turn.entries, ledger
        ) + ledger_violations(turn.entries, ledger, state)
```

- [ ] **Step 6: Rewrite R4's prompt paragraph**

In `agent/v1/sh_loop.py`, replace line 122 of `SH_SYSTEM_PROMPT` in full:

```
R4 IS A CEILING THE RUNNER HOLDS, not a free grade. You may write PASS only when that senior has no load-bearing premise still UNVERIFIED and no stamp of yours on its verifications reads false; a REFUTED load-bearing premise forces FAIL. Grade lower than the ceiling whenever you mean it — you may never grade above it, and a turn that does is rejected. Across three earlier runs R4 flipped to PASS on the turn SH stopped investigating, every time, without exception: the ceiling is what that measurement bought.
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_stamp.py -v`
Expected: PASS.

- [ ] **Step 8: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failures in `test_sh_loop.py`, where scripted turns grade `r4_premise_verification="PASS"` while `p2` (the selection premise the fake senior files) is load-bearing and UNVERIFIED. Fix by having the fake senior settle `p2` too — extend `UPDATES`:

```python
UPDATES = [PremiseUpdate(id="p1", status="VERIFIED", quote="dest_port=3333 count=3",
                         evidence="the full 22-value listing"),
           PremiseUpdate(id="p2", status="VERIFIED", quote="dest_port=3333 count=3",
                         evidence="the only endpoint in the listing")]
```

and add `p2`'s stamp to `_answer`:

```python
                premise_stamps=[
                    PremiseStamp(id="p1", establishes=True,
                                 reason="the 22-value port listing covers every route"),
                    PremiseStamp(id="p2", establishes=True,
                                 reason="the listing shows no other endpoint")],
```

Tests that deliberately exercise a blocked-answer path (the ones that leave a premise open on purpose) must grade R4 `WEAK` rather than `PASS`. Re-run until green.

- [ ] **Step 9: Changelog**

```markdown
- **R4 is a runner-enforced ceiling** (`conversation.r4_ceiling`,
  `grade_ceiling_violations`). SH cannot write PASS while a load-bearing premise
  authored by that senior is UNVERIFIED, or while a stamp on its verifications reads
  false; a REFUTED load-bearing premise forces FAIL. SH may always grade lower, never
  above. R4 now records and triggers nothing, and the clause that taught SH the grade
  was inert — *"the ANSWER gate is the ledger, not this grade"* — is gone from its
  description and from the prompt. The measurement behind it: across three runs and six
  seniors, R4 flipped to PASS on the turn SH stopped investigating, without exception.
  This turn's stamps count toward the ceiling, not only the ledger's, so SH cannot stamp
  a verification false and grade that senior's ground sound in the same breath.
```

- [ ] **Step 10: Commit**

```bash
git add agent/v1/conversation.py agent/v1/sh_loop.py agent/v1/tests/
git commit -m "feat(v1.4.3): R4 becomes a ceiling the runner holds

R4 flipped to PASS on the turn SH stopped investigating, in every run.
It now records; it triggers nothing.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 8: The trigger — a false stamp retires the senior and spawns one validator

No clock, no conjunction with R1/R2/R3. A false stamp is SH stating in writing that a specific premise's evidence does not establish its claim; that is a defect the moment it is written. Requiring a candidate to be ready first only waits for the senior to finish tidying up — which is when it settles its own premises.

This task deletes the two triggers v1.4.3 shipped: the settle-time trigger and the ANSWER-cited pass. Both are made redundant by Task 4 — the bypass they closed (SH settling `p6`/`p7` on the answering turn, where no wave follows) is no longer reachable, because SH settles nothing.

**Files:**
- Modify: `agent/v1/conversation.py` (`nomination_violations`)
- Modify: `agent/v1/sh_loop.py` (`_run_validators` rewritten; the trigger block; delete both old call sites)
- Modify: `agent/v1/validator.py` (delete `MAX_VALIDATORS_PER_QUESTION`)
- Test: `agent/v1/tests/test_stamp.py`, `agent/v1/tests/test_sh_loop.py`

- [ ] **Step 1: Write the failing gate tests**

Append to `agent/v1/tests/test_stamp.py`:

```python
from conversation import nomination_violations


def _false_stamp(**kw):
    return _command(premise_stamps=[PremiseStamp(
        id="p1", establishes=False,
        reason="the claim says route (c) was not searched and the quote is the "
               "result of searching it")], **kw)


def test_a_false_stamp_without_a_nomination_is_rejected():
    led = _verified_by()
    out = nomination_violations([_false_stamp()], led)
    assert out and "nominate_premise_id" in out[0]


def test_a_false_stamp_with_a_nomination_passes():
    led = _verified_by()
    assert nomination_violations([_false_stamp(nominate_premise_id="p1")], led) == []


def test_a_nomination_outside_the_doubt_is_rejected():
    """It may not range wider: the false stamp is what fired the mechanism."""
    led = _verified_by()
    led.add([PremiseDraft(text="someone else's open claim", kind="coverage",
                          load_bearing=True)], author="s2", round_n=2)
    out = nomination_violations([_false_stamp(nominate_premise_id="p2")], led)
    assert out and "p2" in out[0]


def test_an_unverified_premise_of_the_same_senior_may_be_nominated():
    led = _verified_by()
    led.add([PremiseDraft(text="this flow and not the CoinHive six", kind="selection",
                          load_bearing=True, rival="the six ws*.coinhive.com flows")],
            author="s1", round_n=2)
    assert nomination_violations([_false_stamp(nominate_premise_id="p2")], led) == []


def test_a_nomination_without_a_false_stamp_is_rejected():
    """A validator is spawned by a false stamp and by nothing else."""
    led = _verified_by()
    out = nomination_violations([_command(nominate_premise_id="p1")], led)
    assert out and "no false stamp" in out[0]
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_stamp.py -k nomination -v`
Expected: FAIL — `ImportError: cannot import name 'nomination_violations'`.

- [ ] **Step 3: Write the nomination gate**

In `agent/v1/conversation.py`, add after `stamp_violations`:

```python
def nomination_violations(entries: list, ledger) -> list[str]:
    """A false stamp fires the mechanism, and the mechanism needs an aim.

    The nomination is drawn from premises SH stamped false, or premises that senior
    left UNVERIFIED. It may not range wider: the false stamp is what fired this, so
    letting SH aim the validator elsewhere would retire the senior and leave the
    triggering doubt unexamined.
    """
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        false_here = [s.id for s in e.premise_stamps if s.establishes is False]
        pid = e.nominate_premise_id.strip()
        if not false_here:
            if pid:
                out.append("nominate_premise_id is set with no false stamp on this turn "
                           "- a validator is spawned by a false stamp and by nothing else")
            continue
        allowed = {p.id for p in ledger.nominatable(sid)} | set(false_here)
        if not pid:
            out.append(
                f"you stamped {', '.join(false_here)} false, so {sid} is retired and one "
                "independent validator is spawned - name the ONE premise it should "
                f"settle in nominate_premise_id (from {', '.join(sorted(allowed))})")
        elif pid not in allowed:
            out.append(
                f"nominate_premise_id {pid} is neither a premise you stamped false nor "
                f"one {sid} left open - choose from {', '.join(sorted(allowed))}")
    return out
```

- [ ] **Step 4: Run to verify the gate tests pass**

Run: `python -m pytest agent/v1/tests/test_stamp.py -k nomination -v`
Expected: PASS.

- [ ] **Step 5: Write the failing integration test**

Append to `agent/v1/tests/test_sh_loop.py`:

```python
def test_a_false_stamp_retires_the_senior_and_spawns_one_validator(tmp_path):
    """SH is not asked and cannot decline. The senior's route for this turn is dropped:
    the runner retires it, and the premise SH named goes to a blind reader."""
    pool = _Pool()
    llm = _LLM([
        _turn(_spawn()),
        _turn(entry(route="COMMAND", senior_id="s1", decision="continue",
                    directive="keep going",
                    r1_scope_alignment="PASS", r2_progress="PASS",
                    r3_answer_readiness="WEAK", r4_premise_verification="WEAK",
                    nominate_premise_id="p1",
                    premise_stamps=[
                        PremiseStamp(id="p1", establishes=False,
                                     reason="the listing does not cover DNS at all"),
                        PremiseStamp(id="p2", establishes=True,
                                     reason="the only endpoint in the listing")])),
        _turn(_spawn(deviation="read the proxy feed, not cisco:nvm")),
        _turn(_answer(source_senior="s2", r4_premise_verification="WEAK")),
    ])
    out = _run(llm, pool, tmp_path)
    assert pool.validations == 1, "exactly one validator, for the nominated premise"
    assert pool.rounds == 2, "s1 got its first round only; its COMMAND was dropped"
    assert out["spawns_used"] == 2


def test_a_true_stamp_spawns_no_validator(tmp_path):
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.validations == 0
```

- [ ] **Step 6: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_sh_loop.py -k "false_stamp or true_stamp" -v`
Expected: FAIL — `pool.validations == 0` on the first test, and `pool.rounds == 3` (the COMMAND still ran).

- [ ] **Step 7: Rewrite `_run_validators` to be nomination-driven**

In `agent/v1/sh_loop.py`, replace everything from `def _run_validators(` down to (but not including) `    jobs, targets = {}, {}` with:

```python
def _run_validators(pool, ledger, pids, *, qid: str, log, spent: list,
                    round_n: int, max_parallel: int) -> list[str]:
    """Run one validator per nominated premise.

    The trigger is a false stamp and nothing else - no clock, no conjunction with
    R1/R2/R3. A false stamp is SH stating in writing that a specific premise's evidence
    does not establish its claim, and that is a defect the moment it is written.
    Requiring a candidate to be ready first only waits for the senior to finish tidying
    up, which is when it settles its own premises.

    No constant caps this. Retiring the senior costs a spawn slot, so the senior pool IS
    the budget - three at the 1000pt tier, and r2 used one senior of three, so in
    practice this is one validator.

    Returns one line per verdict for SH's next turn, or [] when nothing qualified.
    """
    done = {v["premise_id"] for v in spent}
    due = [ledger.premises[i] for i in pids
           if i in ledger.premises and i not in done]
    if not due:
        return []

    jobs, targets = {}, {}
```

Everything below that line — the `for n, p in enumerate(due, ...)` loop, the `log.note`, and the whole results loop — is unchanged.

- [ ] **Step 8: Delete the two old triggers**

In `agent/v1/sh_loop.py`:

Delete the ANSWER-cited block (the `answer_cited` assignment, its comment, and the `answer_verdicts = ...` block, lines 551-564). Then, in the rejection path, replace

```python
            msgs.append(HumanMessage(content="\n\n".join(
                [render_rejection(problems), *answer_verdicts])))
            continue
        if answer_verdicts:
            msgs.append(HumanMessage(content="\n\n".join(answer_verdicts)))
```

with

```python
            msgs.append(HumanMessage(content=render_rejection(problems)))
            continue
```

Delete the `pre_status` line:

```python
        pre_status = {pid: p.status for pid, p in ledger.premises.items()}
```

Delete the post-wave validator call:

```python
        verdicts = _run_validators(pool, ledger, pre_status, qid=qid, log=log,
                                   spent=validators, round_n=state.turns_used,
                                   max_parallel=max_parallel)
```

and change the wave message assembly to:

```python
        if unread or scouted or failures:
            head = (render_wave(unread, slots_remaining=state.slots_remaining,
                                turns_remaining=state.turns_remaining,
                                ledger=ledger) if unread
                    else _budget_line(state.slots_remaining, state.turns_remaining))
            msgs.append(HumanMessage(content="\n\n".join(
                [head, *scouted, *failures])))
```

Remove `MAX_VALIDATORS_PER_QUESTION` from the `from validator import (...)` line.

- [ ] **Step 9: Add the trigger block**

In `agent/v1/sh_loop.py`, immediately after the stamp-application loop added in Task 6 (and before `grades.extend(rows)`), insert:

```python
        # The trigger. A false stamp is SH stating in writing that this premise's
        # evidence does not establish its claim, so the runner acts on it without
        # asking: the senior is retired and the premise SH nominated goes to a reader
        # that wants nothing. Retiring costs a spawn slot, which is the whole budget.
        for e in turn.entries:
            sid = e.source_senior if e.route == "ANSWER" else e.senior_id
            if not sid or not any(s.establishes is False for s in e.premise_stamps):
                continue
            sess = sessions.get(sid)
            if sess and state.is_active(sid):
                log.write_handoff(sid, sess.handoff(
                    "retired: SH stamped one of its verifications false"))
            state.retire(sid)
            log.note(f"{sid} retired on a false stamp; validating "
                     f"{e.nominate_premise_id}")
            said = _run_validators(pool, ledger, [e.nominate_premise_id], qid=qid,
                                   log=log, spent=validators,
                                   round_n=state.turns_used, max_parallel=max_parallel)
            if said:
                msgs.append(HumanMessage(content="\n\n".join(said)))
```

Then make the route loop skip work for a senior the trigger just retired — replace the `elif e.route in ("COMMAND", "CRITIC"):` branch with:

```python
            elif e.route in ("COMMAND", "CRITIC"):
                if not state.is_active(e.senior_id):
                    # Retired by the false-stamp trigger after the gates ran. SH's route
                    # for it was legal when written and is simply spent.
                    log.note(f"{e.senior_id} was retired this turn; its {e.route} "
                             "is dropped")
                    continue
                pending[e.senior_id] = partial(sessions[e.senior_id].work, _directive_text(e),
                                               rounds_remaining=max(0, state.rounds_left_for(e.senior_id) - 1))
```

- [ ] **Step 10: Add the nomination gate to the chain**

Add `nomination_violations` to the `from conversation import (...)` list and to `problems`:

```python
        ) + stamp_violations(
            turn.entries, ledger
        ) + nomination_violations(
            turn.entries, ledger
        ) + grade_ceiling_violations(
```

- [ ] **Step 11: Delete the constant**

In `agent/v1/validator.py`, delete `MAX_VALIDATORS_PER_QUESTION = 6` and the three comment lines above it, leaving `VALIDATOR_ROUNDS` and `VALIDATOR_ITERS`.

- [ ] **Step 12: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_sh_loop.py -k "false_stamp or true_stamp" -v`
Expected: PASS.

- [ ] **Step 13: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failure in `test_validator.py` — `test_the_question_budget_is_a_real_number` imports the deleted constant. Delete that test and drop `MAX_VALIDATORS_PER_QUESTION` from its import list, then add:

```python
def test_the_budget_is_the_senior_pool():
    """No constant caps validators any more. Retiring the senior costs a spawn slot, so
    the mechanism self-caps at the tier's senior count - three, and r2 used one."""
    import validator
    assert not hasattr(validator, "MAX_VALIDATORS_PER_QUESTION")
```

Also expect failures in any `test_sh_loop.py` test that asserted on the settle-time trigger (a validator firing after a wave); delete those — the trigger they describe no longer exists. Re-run until green.

- [ ] **Step 14: Changelog**

```markdown
- **The trigger is a false stamp, alone** (`conversation.nomination_violations`,
  `sh_loop`'s trigger block, `_run_validators` rewritten). False stamp → retire that
  senior → SH nominates ONE premise → one validator. No clock and no conjunction: the
  interview's first candidate, `R1/R2/R3 = PASS and R4 != PASS`, occurs **zero times**
  in both r2 runs, because R3 and R4 move together — a senior firms up its candidate and
  settles its own premises in the same round. That is the same failure shape as the
  staleness clock: a condition describing a state the system passes through too fast to
  catch. SH nominates on the same turn as the stamp, from what it stamped false or what
  that senior left open; a nomination ranging wider is rejected, and a nomination with no
  false stamp is rejected too.

  The senior's route for that turn is dropped — it was legal when written and is simply
  spent. **`MAX_VALIDATORS_PER_QUESTION` is deleted**: retirement consumes a spawn slot,
  so the senior pool is the budget (3 at the 1000pt tier; r2 used 1).

- **Both v1.4.3 triggers are deleted**: the settle-time trigger and the ANSWER-cited
  pass. The bypass the ANSWER-cited pass closed — SH settling `p6`/`p7` on the answering
  turn, where no wave follows — is unreachable now that SH settles nothing.
```

- [ ] **Step 15: Commit**

```bash
git add agent/v1/conversation.py agent/v1/sh_loop.py agent/v1/validator.py agent/v1/tests/
git commit -m "feat(v1.4.3): a false stamp retires the senior and spawns one validator

No clock, no grade conjunction. The senior pool is the budget.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 8b: A validator that cannot settle it refutes it

*"UNVERIFIED | Treated as REFUTED — two readers could not stand the claim up."*

This is the step that makes the trigger bite. Without it: SH stamps `p1` false, the senior is retired, the validator runs, returns UNVERIFIED — and `p1` keeps the status it had, which is **VERIFIED**. The mechanism would fire, cost a senior slot, and leave the premise looking settled. Two readers failing to stand a claim up is not neutral.

The mapping applies to a **verdict**, not to a failure. A validator that files no usable verdict, quotes something it did not run, or dies in transport leaves the status untouched and says so — a transport failure is not a reasoning outcome, the same principle `state.refund_spawn` rests on.

**Files:**
- Modify: `agent/v1/sh_loop.py` (`_run_validators`, the verdict branch)
- Test: `agent/v1/tests/test_validator.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_validator.py`:

```python
from premise import PremiseUpdate as _PU
from validator import as_refutation


def test_an_unverified_verdict_becomes_a_refutation():
    """Two readers could not stand the claim up. Without this the premise keeps the
    status it had - which, on the premise SH just stamped false, is VERIFIED."""
    out = as_refutation(_PU(id="p1", status="UNVERIFIED", quote="",
                            evidence="a full-feed census would settle it"))
    assert out.status == "REFUTED"
    assert "could not be settled" in out.evidence
    assert out.id == "p1"


def test_a_verified_or_refuted_verdict_passes_through_untouched():
    for status in ("VERIFIED", "REFUTED"):
        u = _PU(id="p1", status=status, quote=VALIDATOR_CORPUS[0], evidence="why")
        assert as_refutation(u) is u


def test_no_verdict_at_all_is_not_a_refutation():
    """A validator that filed nothing, or quoted something it did not run, or died in
    transport, has not ruled on anything - a transport failure is not a reasoning
    outcome."""
    assert as_refutation(None) is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_validator.py -k refutation -v`
Expected: FAIL — `ImportError: cannot import name 'as_refutation'`.

- [ ] **Step 3: Write the mapping**

In `agent/v1/validator.py`, add after `refusal_reason`:

```python
def as_refutation(update):
    """An UNVERIFIED verdict is a refutation; anything else passes through.

    Two readers could not stand the claim up, and the premise is not left looking
    settled because the second one ran out of room. Without this the mechanism costs a
    senior slot and changes nothing: the premise SH stamped false is VERIFIED, and a
    validator that shrugs leaves it VERIFIED.

    `None` - no usable verdict, a quote it did not run, a crash in transport - is NOT
    a refutation. That validator ruled on nothing, and a transport failure is not a
    reasoning outcome.
    """
    if update is None or update.status != "UNVERIFIED":
        return update
    return PremiseUpdate(
        id=update.id, status="REFUTED", quote=update.quote,
        evidence="the claim could not be settled by an independent reader: "
                 + (update.evidence or "no reason given"))
```

- [ ] **Step 4: Apply it in the runner**

In `agent/v1/sh_loop.py`, inside `_run_validators`'s results loop, replace the two lines that compute the refusal and apply the update:

```python
        why = refusal_reason(res["update"], res["corpus"])
```

with

```python
        why = refusal_reason(res["update"], res["corpus"])
        verdict = as_refutation(res["update"])
```

and change the `ledger.apply` call and the two lines below it from `res["update"]` to `verdict`:

```python
        notes = ledger.apply([verdict], author=vid, corpus=res["corpus"],
                             round_n=round_n)
```

and in the final success block:

```python
            f"Its quote: {verdict.quote}\n"
            f"Its reason: {verdict.evidence}")
```

Add `as_refutation` to the `from validator import (...)` list.

> Note on the quote rule: a REFUTED status needs a quote the validator ran, and an
> UNVERIFIED verdict usually carries none — so `ledger.apply` will refuse the converted
> update and the premise keeps its status, with a note SH reads. That is the correct,
> conservative outcome and the reason this is a mapping rather than a forced write: the
> quote rule is not weakened for a verdict that has no evidence behind it. Where the
> validator DID quote a real result while still calling it unsettled, the refutation
> lands.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_validator.py -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest agent/v1/tests -q`
Expected: PASS. `test_an_unverified_verdict_needs_no_quote` still passes — it asserts on `refusal_reason`, which is unchanged.

- [ ] **Step 7: Changelog**

```markdown
- **A validator's UNVERIFIED verdict is a refutation** (`validator.as_refutation`).
  Two readers could not stand the claim up. Without this the mechanism costs a senior
  slot and changes nothing: the premise SH stamped false is VERIFIED, and a validator
  that shrugs leaves it VERIFIED. The mapping applies to a *verdict* only — no usable
  verdict, a quote it did not run, or a crash in transport leaves the status untouched,
  because that validator ruled on nothing and a transport failure is not a reasoning
  outcome. The quote rule is not weakened: a converted refutation carrying no quote is
  refused by `apply` like any other, and SH reads the note.
```

- [ ] **Step 8: Commit**

```bash
git add agent/v1/validator.py agent/v1/sh_loop.py agent/v1/tests/test_validator.py
git commit -m "feat(v1.4.3): an UNVERIFIED verdict is a refutation

Two readers could not stand the claim up. Leaving it VERIFIED made the
mechanism cost a senior slot and change nothing.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 9: The validator's second mode

A nomination has two sources, so the brief has two shapes. Handed r2's `p1` — *"(c) flows to pool IP 45.77.53.176 on any port — NOT yet searched"* — with nothing attached and told to settle it, the obvious move is to go and search route (c). That is what `v1` did in v1.4.3 r1 with its full-feed `dh` scan, which is the one time this architecture found the right lead.

The mode lives in `brief_for`, not in `SPECIALISTS["validator"]`: the difference is per-premise, and the system prompt has no premise to look at.

**Files:**
- Modify: `agent/v1/validator.py` (`brief_for`)
- Test: `agent/v1/tests/test_validator.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_validator.py`:

```python
def test_an_offered_quote_asks_whether_it_establishes_the_claim():
    p = _settled_ledger().premises["p1"]
    brief = brief_for(p)
    assert "does that evidence establish this claim as written" in brief.lower()
    assert P1_QUOTE in brief


def test_no_offered_quote_asks_it_to_settle_the_claim_itself():
    """The mode that worked. Handed r2's p1 with nothing attached, the obvious move is
    to go and search route (c) - which is what v1 did with its full-feed dh scan, the
    one time this architecture found the right lead."""
    led = PremiseLedger()
    led.add([PremiseDraft(text=P1_TEXT, kind="coverage", load_bearing=True)],
            author="s1", round_n=2)
    brief = brief_for(led.premises["p1"])
    assert "settle this claim from the data yourself" in brief.lower()
    assert "no evidence has been offered" in brief.lower()
    assert P1_TEXT in brief
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_validator.py -k "offered_quote or settle_the_claim" -v`
Expected: FAIL — neither phrase is in the brief.

- [ ] **Step 3: Branch the brief**

In `agent/v1/validator.py`, replace `brief_for` in full:

```python
def brief_for(premise) -> str:
    """The validator's entire briefing: one claim, and the evidence offered for it when
    there is any.

    Two modes, because a nomination has two sources:
      * an offered quote - does this evidence establish this claim as written?
      * no quote (a premise its senior left UNVERIFIED) - settle it from the data.

    The second is the mode that worked. Handed r2's `p1` - "(c) flows to pool IP
    45.77.53.176 on any port - NOT yet searched" - with nothing attached and told to
    settle it, the obvious move is to go and search route (c). That is what `v1` did in
    v1.4.3 r1 with its full-feed `dh` scan, the one time this architecture found the
    right lead.

    Everything that could identify the question is left out either way, including the
    premise's `kind` (coverage/selection names the shape of the investigation) and its
    id.
    """
    parts = [f'THE CLAIM TO CHECK, word for word:\n\n  "{premise.text}"\n']
    if premise.quote:
        parts.append("THE EVIDENCE ITS AUTHOR OFFERED, which you are checking - it is "
                     "a claim about the data, not a fact:\n\n"
                     f"  {premise.quote}\n")
        if premise.evidence:
            parts.append(f"WHY ITS AUTHOR SAID THAT SETTLES IT:\n\n  {premise.evidence}\n")
        parts.append("YOUR TASK: does that evidence establish this claim as written? "
                     "Check the claim against its own words first, then against the "
                     "data - your own results decide, not the author's.")
    else:
        parts.append("No evidence has been offered for it. YOUR TASK: settle this claim "
                     "from the data yourself - run the searches that show it true or "
                     "false. If the claim names something as not yet searched, or not "
                     "yet checked, search it.")
    parts.append("File your verdict with submit_finding.")
    return "\n".join(parts)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_validator.py -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest agent/v1/tests -q`
Expected: PASS.

- [ ] **Step 6: Changelog**

```markdown
- **The validator gains a second mode** (`validator.brief_for`). With an offered quote:
  *does this evidence establish this claim as written?* Without one — SH nominating a
  premise its senior left UNVERIFIED — *settle this claim from the data yourself*. The
  mode lives in the brief, not in `SPECIALISTS["validator"]`: the difference is
  per-premise and the system prompt has no premise to look at. The second mode is the
  one with evidence behind it: handed r2's `p1` with nothing attached, the obvious move
  is to search route (c), which is what `v1` did in v1.4.3 r1 with its full-feed `dh`
  scan — the one time this architecture found the right lead. It also answers the
  standing `§7.4` question: both r2 validator failures were *"quoted something it did
  not run"*, the validator echoing the evidence it was handed, and this mode hands it
  nothing to echo.
```

- [ ] **Step 7: Commit**

```bash
git add agent/v1/validator.py agent/v1/tests/test_validator.py
git commit -m "feat(v1.4.3): the validator's second mode - settle it yourself

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 10: The alternative agent (spec 2 §4, finally built)

Spawned after a REFUTED verdict. Carries `deviation` and `inherited_entities` (SH fills) plus the runner-injected refuted-premise block. The SPAWN is rejected if `deviation` is empty. Divergence is **observed, not checked** — both candidate checks were designed and dropped.

This task also closes a live defect: `render_refuted()` has never had a caller, and `render_for_senior` excludes REFUTED premises justifying it with *"render_refuted() already tells the senior which premises are dead"*. Today no senior is told which premises are dead. It is now wired into **every** senior's carried brief, not only the AA's spawn.

**Files:**
- Modify: `agent/v1/conversation.py` (two SPAWN fields, `deviation_violations`)
- Modify: `agent/v1/premise.py` (`render_for_senior` carries `render_refuted`)
- Modify: `agent/v1/sh_loop.py` (`_spawn_directive`; the SPAWN branch; the ALTERNATIVE SENIOR prompt block)
- Test: `agent/v1/tests/test_alternative_agent.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `agent/v1/tests/test_alternative_agent.py`:

```python
"""The alternative agent (spec 2 §4, built in the v1.4.3 revision).

Not a new agent type: an ordinary senior whose brief the runner augments with the
refuted premises. Treating it as a new type would duplicate the whole senior stack to
add one prompt section.

What is NOT tested, because it is deliberately not enforced (spec 2 §4.3): that the AA's
candidate differs from the retired senior's, or that its reasoning avoids a refuted
premise. Both are observed in the run log. A hard "the value must differ" forces the AA
away from a correct answer; "must not re-derive a refuted premise" cannot be done from
free text without reintroducing `_label()` under a new name.
"""

from conversation import SeniorDirective, deviation_violations
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from sh_loop import _spawn_directive

# Repeated rather than imported from test_stamp: agent/v1/tests is not a package and
# the repo has a second top-level tests/ directory, so a cross-test import is
# ambiguous. Same reason test_sh_loop.py carries its own copy.
BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RETIRE",
    "open_question_answers": [], "new_premises": [], "answer_premise_ids": [],
    "premise_stamps": [], "nominate_premise_id": "",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "deviation": "", "inherited_entities": "",
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}

RESULT = '{"ibc": "5782875", "obc": "177", "dp": "3333"}'


def entry(**kw) -> SeniorDirective:
    return SeniorDirective(**{**BLANK, **kw})


def _spawn(**kw):
    base = dict(route="SPAWN", spawn_type="senior",
                subquestion="Find the mining duration in the proxy feed.",
                reason="cisco:nvm cannot hold it.")
    base.update(kw)
    return entry(**base)


def _refuted_ledger():
    led = PremiseLedger()
    led.add([PremiseDraft(text="The 3333 flow's byte profile shows submission, "
                               "not download", kind="other", load_bearing=True)],
            author="s1", round_n=1)
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=RESULT,
                             evidence="ibc dwarfs obc - this is a download")],
              author="v1", corpus=[RESULT], round_n=2)
    return led


def test_a_spawn_on_refuted_ground_needs_a_deviation():
    out = deviation_violations([_spawn()], _refuted_ledger())
    assert out and "deviation" in out[0]


def test_a_spawn_with_a_deviation_passes():
    assert deviation_violations(
        [_spawn(deviation="read the proxy feed's cs_bytes, do not re-walk cisco:nvm")],
        _refuted_ledger()) == []


def test_a_spawn_with_nothing_refuted_needs_no_deviation():
    assert deviation_violations([_spawn()], PremiseLedger()) == []


def test_the_spawn_directive_carries_the_deviation_and_the_inherited_entities():
    d = _spawn_directive(
        _spawn(deviation="read the proxy feed's cs_bytes",
               inherited_entities="host BSTOLL-L, window 2018-08-20T09:00-11:00Z"),
        _refuted_ledger())
    assert "read the proxy feed's cs_bytes" in d
    assert "BSTOLL-L" in d


def test_the_runner_fills_the_refuted_block_and_sh_cannot_soften_it():
    """SH does not write this and cannot alter it: it is rendered from the ledger."""
    d = _spawn_directive(_spawn(deviation="elsewhere"), _refuted_ledger())
    assert "PREMISES ALREADY DISPROVEN" in d
    assert "byte profile shows submission" in d
    assert "ibc" in d, "the evidence that disproved it travels with the claim"


def test_every_senior_is_told_which_premises_are_dead():
    """render_refuted() has never had a caller, and render_for_senior excluded REFUTED
    premises on the grounds that it did. Until now, no senior was told."""
    led = _refuted_ledger()
    led.add([PremiseDraft(text="the duration is the wall-clock span", kind="other",
                          load_bearing=True)], author="s2", round_n=3)
    carried = led.render_for_senior("s2")
    assert "PREMISES ALREADY DISPROVEN" in carried
    assert "byte profile shows submission" in carried


def test_a_clean_ledger_carries_no_refuted_block():
    led = PremiseLedger()
    led.add([PremiseDraft(text="an open claim", kind="other", load_bearing=True)],
            author="s1", round_n=1)
    assert "DISPROVEN" not in led.render_for_senior("s1")
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_alternative_agent.py -v`
Expected: FAIL — `ImportError: cannot import name 'deviation_violations'`.

- [ ] **Step 3: Add the two SPAWN fields**

In `agent/v1/conversation.py`, add to `SeniorDirective` in the `# SPAWN` block, after `reason`:

```python
    deviation: str = Field(
        description="SPAWN. Where the evidence may sit if the retired senior's reading "
                    "was wrong: the fields, feeds or entities it did not touch, and what "
                    "NOT to re-walk. Required on any SPAWN made while a load-bearing "
                    "premise is REFUTED. The deviation can be small - the same feed read "
                    "through a different field is a different direction; the same field "
                    "re-read is not.")
    inherited_entities: str = Field(
        description="SPAWN. Entities the retired senior ESTABLISHED - a host, account, "
                    "file, window - that carry forward. Dropping a proven entity because "
                    "it was found in another feed is how a stuck question is lost.")
```

- [ ] **Step 4: Write the gate**

In `agent/v1/conversation.py`, add after `nomination_violations`:

```python
def deviation_violations(entries: list, ledger) -> list[str]:
    """A replacement spawned onto ground that is already known dead is a wasted slot.

    `deviation` is what makes a SPAWN an alternative rather than a retry. The third
    thing a replacement needs - what NOT to rebuild on - is filled by the runner from
    the ledger, so SH cannot omit it or soften it.
    """
    if not any(p.load_bearing and p.status == "REFUTED"
               for p in ledger.premises.values()):
        return []
    return [f'SPAWN "{e.subquestion[:50]}" needs a `deviation`: a load-bearing premise '
            "is REFUTED, so a replacement needs a direction that does not need it - name "
            "the fields, feeds or entities the retired senior did not touch, and what "
            "not to re-walk"
            for e in entries
            if e.route == "SPAWN" and e.spawn_type == "senior"
            and not e.deviation.strip()]
```

- [ ] **Step 5: Carry the refuted block to every senior**

In `agent/v1/premise.py`, in `render_for_senior`, replace the docstring's closing sentence (*"`render_refuted()` already tells the senior which premises are dead."*) with:

```python
        `render_refuted()` is rendered at the head of this block, for EVERY senior and
        not only a replacement: before this it had no caller at all, so no senior was
        ever told which premises were dead.
```

Replace the body from `open_ = [...]` through the first `lines = []` with:

```python
        open_ = [p for p in self.unresolved_for(author) if p.status == "UNVERIFIED"]
        others = [p for p in self.premises.values()
                  if p.author != author and p.load_bearing and p.status == "UNVERIFIED"]
        dead = self.render_refuted()
        if not open_ and not others and not dead:
            return ""
        lines = []
        if dead:
            lines.append(dead)
```

(keeping the existing explanatory comment above `others`), and give the `if open_:` block a separator:

```python
        if open_:
            if lines:
                lines.append("")
            lines.append("YOUR UNRESOLVED PREMISES - carried forward by the runner, "
                         "in your own words:")
```

Replace `render_refuted`'s docstring, which is now wrong about having no caller:

```python
        """What a senior must not rebuild on. Empty when nothing is refuted.

        Carried into every senior's round by `render_for_senior`, and into a
        replacement's first instruction by `sh_loop._spawn_directive`. SH does not
        write this and cannot soften it.
        """
```

- [ ] **Step 6: Build the AA's spawn directive**

In `agent/v1/sh_loop.py`, add after `_route_directive`:

```python
def _spawn_directive(e, ledger) -> str:
    """A new senior's first instruction: SH's reason, the deviation it wants and the
    entities the replacement inherits, then the refuted block the RUNNER fills.

    This is the whole of what makes a senior an "alternative agent". It is not a new
    agent type - duplicating the senior stack to add one prompt section would buy
    nothing. Divergence is not checked (spec 2 §4.3): the brief states plainly that a
    line of reasoning needing a refuted premise is already known wrong, and whether the
    replacement obeys is an observation for the run log, not a gate.
    """
    parts = [("Begin. " + e.reason) if e.reason else "Begin."]
    if e.deviation.strip():
        parts.append("THE DEVIATION SH WANTS - a direction the retired senior did not "
                     f"walk:\n{e.deviation.strip()}")
    if e.inherited_entities.strip():
        parts.append("ENTITIES ALREADY ESTABLISHED - carry these forward, do not spend "
                     f"a round rediscovering them:\n{e.inherited_entities.strip()}")
    dead = ledger.render_refuted()
    if dead:
        parts.append(dead)
    return "\n\n".join(parts)
```

In the SPAWN branch of the route loop, replace the `pending[sid] = partial(...)` call with:

```python
                pending[sid] = partial(sessions[sid].work, _spawn_directive(e, ledger),
                                       rounds_remaining=max(0, state.rounds_left_for(sid) - 1))
```

- [ ] **Step 7: Wire the gate**

Add `deviation_violations` to the `from conversation import (...)` list and to `problems`, after `spawn_overlap_violations`:

```python
        ) + deviation_violations(
            turn.entries, ledger
        ) + premise_audit_violations(
```

- [ ] **Step 8: Replace the prose ALTERNATIVE SENIOR paragraph**

In `agent/v1/sh_loop.py`, replace lines 91-92 of `SH_SYSTEM_PROMPT` with:

```
Brief the replacement on the question as asked, then fill two fields. `deviation`: where the evidence may sit if the retired reading was wrong — the fields, feeds or entities it did not touch, and what not to re-walk. The deviation can be small; the same feed read through a different field is a different direction, the same field re-read is not. `inherited_entities`: what the retired senior ESTABLISHED — a host, account, file, window — that carries forward. Carrying a proven entity into the feed the question names is the most common way a stuck question is solved; dropping it because it was found elsewhere is how one is lost. A SPAWN made while a load-bearing premise is REFUTED is rejected without a `deviation`.
The third thing a replacement needs — what NOT to rebuild on — the runner fills from the ledger. You do not write it and cannot soften it. Do not hand over the retired senior's candidate to confirm: it must reach its own answer, and two seniors arriving at the same value independently is verification, while one senior repeating itself is not.
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_alternative_agent.py -v`
Expected: PASS (7 tests).

- [ ] **Step 10: Run the full suite and fix the fallout**

Run: `python -m pytest agent/v1/tests -q`
Expected: failures in `test_conversation_routes.py` / `test_sh_loop.py` `BLANK` dicts — add `"deviation": "", "inherited_entities": "",` to both. Any test that spawns while a premise is REFUTED needs a `deviation=` on its spawn. Re-run until green.

- [ ] **Step 11: Changelog**

```markdown
- **The alternative agent, built** (`SeniorDirective.deviation` /
  `inherited_entities`, `deviation_violations`, `sh_loop._spawn_directive`). Spec 2 §4,
  designed since 2026-09-20 and never built. It is not a new agent type: it is an
  ordinary senior whose first instruction the runner augments. SH fills `deviation` and
  `inherited_entities`; a SPAWN made while a load-bearing premise is REFUTED is rejected
  without a `deviation`. The refuted-premise block is filled by the runner from the
  ledger, so SH cannot omit or soften it, and the prose ALTERNATIVE SENIOR paragraph is
  replaced by fields — the same move the ledger makes for premises. §4.3 stands:
  divergence is observed, not checked.

- **`render_refuted()` is wired into every senior's carried brief**, not only a
  replacement's spawn. This closes a live defect: `render_for_senior` excluded REFUTED
  premises and justified it with *"render_refuted() already tells the senior which
  premises are dead"* — a function that had never had a caller. Until now, no senior was
  told which premises were dead.
```

- [ ] **Step 12: Commit**

```bash
git add agent/v1/conversation.py agent/v1/premise.py agent/v1/sh_loop.py agent/v1/tests/
git commit -m "feat(v1.4.3): the alternative agent, and a refuted block that reaches seniors

render_refuted() has had no caller since it was written. Every senior now
gets it, and a replacement gets deviation + inherited_entities as fields.

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 11: The SH prompt catches up with the mechanism

The gates are built; the prompt still describes the old ones. Every edit here is text in `SH_SYSTEM_PROMPT` — no logic.

**Files:**
- Modify: `agent/v1/sh_loop.py` (`SH_SYSTEM_PROMPT` lines 126, 128, 132-141)
- Test: `agent/v1/tests/test_sh_prompts.py`

- [ ] **Step 1: Write the failing tests**

Append to `agent/v1/tests/test_sh_prompts.py`:

```python
def test_the_prompt_does_not_invite_sh_to_settle_a_premise():
    from sh_loop import SH_SYSTEM_PROMPT
    assert "premise_updates" not in SH_SYSTEM_PROMPT
    assert "YOU DO NOT SETTLE PREMISES" in SH_SYSTEM_PROMPT


def test_the_prompt_teaches_the_stamp_and_what_a_false_one_costs():
    from sh_loop import SH_SYSTEM_PROMPT
    assert "premise_stamps" in SH_SYSTEM_PROMPT
    assert "nominate_premise_id" in SH_SYSTEM_PROMPT
    assert "RETIRES THAT SENIOR" in SH_SYSTEM_PROMPT


def test_r4_is_no_longer_described_as_inert():
    """The clause "the ANSWER gate is the ledger, not this grade" taught SH the grade
    was inert, and SH agreed: R4 flipped to PASS on the turn it stopped investigating,
    in every run."""
    from conversation import SeniorDirective
    from sh_loop import SH_SYSTEM_PROMPT
    desc = SeniorDirective.model_fields["r4_premise_verification"].description
    assert "the ANSWER gate is" not in desc
    assert "the ANSWER gate is the ledger, not this grade" not in SH_SYSTEM_PROMPT
    assert "CEILING" in SH_SYSTEM_PROMPT
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest agent/v1/tests/test_sh_prompts.py -v`
Expected: FAIL on the first two — the prompt still says `premise_updates` and has no stamp section.

- [ ] **Step 3: Rewrite the ledger paragraph**

In `agent/v1/sh_loop.py`, replace line 126 of `SH_SYSTEM_PROMPT` in full:

```
THE PREMISE LEDGER. Every premise on this question lives in one ledger, shown to you in full each turn. The seniors file their own; you file the ones they missed, in `new_premises`. YOU DO NOT SETTLE PREMISES. You have no Splunk access, so "SH verified it" has only ever meant "SH read a report and decided" — and in the run this rule comes from, you settled 19 of 28 premises, including every one that lost the question. A premise reaches VERIFIED from the senior whose own search shows it, or from an independent validator, and from nobody else. A premise YOU file therefore starts UNVERIFIED and stays there until a senior settles it: the runner carries it to every active senior as a load-bearing premise filed by others, so FILE IT EARLY — one you file on your answering turn has nobody left to settle it.
```

- [ ] **Step 4: Add the stamp section**

Insert immediately after the line you just replaced:

```
YOUR STAMP — this is what replaces settling. When a report in the wave you just read NEWLY claims a premise VERIFIED, you record your reading of it: one `premise_stamps` entry per premise, with `establishes` true or false and a reason. Read the claim's OWN WORDS before you read the quote. A claim that states its own limit — a route not searched, a case not checked, a choice left unresolved — is NOT established by evidence that walks past that limit, and that is the single most common way this system has gone wrong. A turn that leaves a new verification unstamped is rejected. A stamp is recorded once, when the verification is first claimed, and it never changes the status: the ledger keeps the senior's verdict with your reading beside it.
A FALSE STAMP RETIRES THAT SENIOR AND SPAWNS A VALIDATOR. You are stating in writing that its ground does not hold, and the runner acts on it without asking you: the senior is retired, and one independent validator — which sees the claim and nothing else, not the question, not the reports, not the candidate — settles the premise you name in `nominate_premise_id`, chosen from what you stamped false or what that senior left UNVERIFIED. Retiring costs a senior slot, so a false stamp is not free. Stamping true on a premise you do not believe is worse, and every stamp is on the record.
WHAT A VERDICT MEANS. VERIFIED: your doubt is independently dismissed — the premise stands and you may proceed on it. REFUTED: a hard block. The answer resting on it is dead; SPAWN an alternative senior on ground that does not need it. UNVERIFIED: two readers could not stand the claim up — treat it as refuted.
```

- [ ] **Step 5: Update the gates list**

In the `THE GATES YOU MUST RESPECT` block, delete the last bullet (`* Quoted evidence: ...`) and append:

```
  * Stamps: every verification a report newly claims is stamped in the same turn, or the turn is rejected.
  * R4 ceiling: PASS is refused while that senior has a load-bearing UNVERIFIED premise or a stamp of yours reads false; a REFUTED one forces FAIL.
  * Nomination: a turn carrying a false stamp names exactly one premise in `nominate_premise_id`, drawn from what you stamped false or what that senior left open.
  * Deviation: a SPAWN made while a load-bearing premise is REFUTED is rejected without a `deviation`.
```

- [ ] **Step 6: Trim the ANSWER paragraph's dead instruction**

In line 128 (`BEFORE ANY ANSWER, ...`), delete this sentence, which describes something SH can no longer do:

```
WHEN YOU FILE ONE YOU CAN ALREADY SETTLE, settle it in the same turn: put the senior's output in that premise's `quote` and why it settles it in `evidence`. You cannot name a premise in `premise_updates` on the turn you file it - the runner assigns the id after your turn - so filing without the quote makes it an UNVERIFIED blocker on your own ANSWER.
```

and put this in its place:

```
A premise you file is UNVERIFIED until a senior settles it, so file it while a senior still has rounds — one filed on the answering turn has nobody left to settle it and blocks the answer you filed it for.
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest agent/v1/tests/test_sh_prompts.py -v`
Expected: PASS.

- [ ] **Step 8: Run the full suite**

Run: `python -m pytest agent/v1/tests -q`
Expected: PASS.

- [ ] **Step 9: Changelog**

```markdown
- **The SH prompt catches up with the mechanism.** The ledger paragraph now says plainly
  that SH settles nothing and that a premise it files must be filed early enough for a
  senior to reach. A stamp section replaces the settling instructions and states what a
  false stamp costs. The gates list gains stamps, the R4 ceiling, the nomination and the
  deviation, and loses the quoted-evidence rule that applied to `premise_updates`.
```

- [ ] **Step 10: Commit**

```bash
git add agent/v1/sh_loop.py agent/v1/tests/test_sh_prompts.py
git commit -m "docs(v1.4.3): the SH prompt catches up with the mechanism

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

---

### Task 12: Pin the endgame, then run the smoke test

*Slots spent with a load-bearing premise REFUTED: the run returns nothing.* No answer and a wrong answer both score 0, so letting SH answer on dead ground buys nothing and writes a known-false premise into the case file for every later question on the dataset.

This behaviour already holds — `ledger_violations`' two REFUTED blocks have no budget escape, and `run_question` returns `NO_ANSWER` when no ANSWER route is ever accepted. It has never been pinned by a test, and it is exactly the property a future "let it answer anyway" patch would quietly remove.

**Files:**
- Test: `agent/v1/tests/test_validator_bypass.py`

- [ ] **Step 1: Write the test**

Append to `agent/v1/tests/test_validator_bypass.py`:

```python
def test_the_refuted_block_does_not_lift_when_the_budget_runs_out():
    """The UNVERIFIED block lifts once there is nothing left to try; this one never
    does. No answer and a wrong answer both score 0, so answering on dead ground buys
    nothing and writes a known-false premise into the case file for every later
    question on the dataset."""
    led = _ledger_with_validator_refutation()
    spent = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        spent.open_senior(sid)
        spent.used[sid] = spent.granted[sid]
        spent.retire(sid)
    assert spent.slots_remaining == 0
    assert spent.exhausted() == "rounds"

    assert ledger_violations([_answer(["p1"])], led, spent), \
        "a refuted premise blocks with every budget spent"


def test_an_unverified_block_does_lift_when_the_budget_runs_out():
    """The contrast that gives the sentence above its meaning."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="every route was enumerated", kind="coverage",
                          load_bearing=True)], author="s1", round_n=1)
    spent = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        spent.open_senior(sid)
        spent.used[sid] = spent.granted[sid]
        spent.retire(sid)

    assert ledger_violations([_answer(["p1"])], led, spent) == []
```

- [ ] **Step 2: Run it**

Run: `python -m pytest agent/v1/tests/test_validator_bypass.py -v`
Expected: PASS. Both describe behaviour that already holds — if either fails, an earlier task broke the gate, and that is the bug to fix, not the test.

- [ ] **Step 3: Run the whole suite and the linter**

Run: `python -m pytest agent/v1/tests tests -q`
Expected: PASS, no failures. Record the count.

Run: `python -m ruff check agent/`
Expected: `All checks passed!`. Fix anything it reports — most likely an unused import left by Task 4 or Task 8.

- [ ] **Step 4: Changelog**

```markdown
- **The endgame is pinned** (`test_validator_bypass.py`). Slots and rounds spent with a
  load-bearing premise REFUTED: the ANSWER stays blocked and the run returns nothing.
  The behaviour already held — neither REFUTED block in `ledger_violations` has a budget
  escape — but nothing tested it, and it is exactly the property a later "let it answer
  anyway" patch would quietly remove. The paired test pins the contrast: the UNVERIFIED
  block does lift once there is nothing left to try.

Tests: N passed, ruff clean. **Not yet measured** — no run has been made on this
mechanism. The next Q216 smoke run is its acceptance test.
```

Replace `N` with the number from Step 3.

- [ ] **Step 5: Commit**

```bash
git add agent/v1/tests/test_validator_bypass.py docs/version_architecture/v1/v1.4.3.md
git commit -m "test(v1.4.3): pin the endgame - a refuted premise outlasts the budget

Claude-Session: https://claude.ai/code/session_0164q3usEHekK9HHT9p8JzWR"
```

- [ ] **Step 6: Smoke test — ask the user before running**

Do **not** run this without the user's go-ahead: `CLAUDE.md`'s cost-limited-runs policy is active, and every run is a smoke test on ~5 hard questions, never a full run.

The acceptance run for this mechanism is Q216, the question every reading in the spec comes from:

```bash
python agent/v1/run_all_v1.py --ids Q216 --run-name v1.4.3_stamp_Q216_r1
```

Output lands in `log/temp/`. What to read, in order:

1. **Did SH ever stamp false?** `grep -c '"stamp": "false"' log/temp/v1.4.3_stamp_Q216_r1/premise_ledger.json`. Zero means the mechanism never fired, and the risk the spec accepted in the open ("SH can stamp everything true and the mechanism never fires") is what happened.
2. **Where did the true stamps sit?** For each `"stamp": "true"`, read `stamp_reason` against the premise text and its quote. A true stamp on a premise the answer then dies on is the diagnosable failure the spec traded for, and it reads straight out of the ledger.
3. **Did a validator run, and did it reach a verdict?** The usable-verdict rate was 2/4 then 4/6 across the two v1.4.3 runs, both times failing as *"quoted something it did not run"*. Task 9's second briefing mode is the change aimed at it.
4. **Did the AA rebuild on a premise it was handed as refuted?** (spec 2 §8.2 — read its ledger entries against the refuted list by hand.) If it did, that is the evidence needed to design a check, and the shape of the real failure beats a guess at it. If it did not, the brief was enough and no check is owed.
5. **Cost**, with the senior's share broken out separately.

Write the readings into `docs/version_architecture/v1/v1.4.3.md` as a new `## Q216 acceptance run` section, and ask the user for the run's dollar figure rather than guessing it.

---

## Notes for the implementer

**What is deliberately NOT built, and why.** Do not "fix" these — each was decided against with a reason.

- **No divergence check on the AA** (spec 2 §4.3). Two were designed and both dropped. *"The value must differ"* forces the AA away from a correct answer when the retired senior happened to be right, and gives it no way to report "I checked, and the original value holds for a different reason". *"The AA must not re-derive a refuted premise"* cannot be done from free text — any implementation is a fuzzy string match, the exact class of mechanism the ledger exists to delete; it would reintroduce `_label()` under a new name. The brief states the rule plainly and the run log observes whether it is obeyed.
- **The coverage premise is still required only at ANSWER.** Requiring one at the first SPAWN was considered and declined: at spawn time SH has no data, so its coverage list comes from priors — and *"dp=3333 is the canonical Monero pool port"* is precisely a prior.
- **No two-candidate scheme.** On a REFUTED premise the answer dies rather than surviving as one of two candidates for SH to choose between. r1 is the reason: SH already had 112 and 1667 side by side in `s1`'s round-5 report and took 112. A formal mechanism for that choice formalises a judgement we have watched fail.
- **Laundering through an open question is recorded, not fixed.** `p5`'s text reads *"per SH's q3 guidance the act is the unique stratum-style service connection"*. `CIRCULAR` reads the **quote**, and the quote was genuine — the instruction is in the premise's *text*. A senior acting on its orchestrator's scope guidance is the design working; what made that case bad is that the guidance was wrong. Distinguishing the two needs a reader, not a regex. Worth doing once there is a second example.

**Risks the spec accepts in the open, restated so they are not rediscovered as bugs.**

1. **SH can stamp everything true and the mechanism never fires.** Deliberate — "trust the stamp". The bet is that a specific per-premise question asked one round before the answering turn is materially harder to wave through than one word. If it is not, the stamps are on the record and the failure is diagnosable rather than mysterious.
2. **Honest stamping costs a senior slot.** This is the same pressure, in the same direction, at the same moment, that turned R4 into a permission slip. Accepted, because every stamp is on the record.
3. **The stamp is still SH.** It is a better question asked at a better moment of the same interested party. It is not independence; independence remains the validator's job.
