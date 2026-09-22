"""SH's stamp: its reading of one newly-claimed verification (v1.4.3 revision).

The measurement this replaces, across three runs and six seniors: R4 flipped to PASS on
the turn SH stopped investigating, without exception. A single word about a whole report
is easy to wave through. "Does this quote establish this claim as written", asked about
one named premise one round before the answering turn, is the bet.
"""

from conversation import (
    PremiseStamp,
    SeniorDirective,
    grade_ceiling_violations,
    nomination_violations,
    r4_ceiling,
    stamp_violations,
)
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
    assert led.stamp_premise("p1", establishes=False, claim_holds=True, holds_reason="no rival",
                             reason="the claim says route (c) was not searched and the "
                                    "quote is the result of searching it",
                             round_n=3) is True
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].stamp == "false"
    assert "not searched" in led.premises["p1"].stamp_reason


def test_a_premise_is_stamped_once():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, claim_holds=True,
                      holds_reason="no rival", reason="it does", round_n=3)
    assert led.stamp_premise("p1", establishes=False, claim_holds=True,
                             holds_reason="no rival", reason="changed my mind",
                             round_n=4) is False
    assert led.premises["p1"].stamp == "true"


def test_a_stamped_premise_is_no_longer_owed_one():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, claim_holds=True,
                      holds_reason="no rival", reason="it does", round_n=3)
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
    led.stamp_premise("p1", establishes=False, claim_holds=True,
                      holds_reason="no rival",
                      reason="it walks past its own limit", round_n=3)
    led.add([PremiseDraft(text="this flow and not the CoinHive six", kind="selection",
                          load_bearing=True, rival="the six ws*.coinhive.com flows")],
            author="s1", round_n=3)
    led.add([PremiseDraft(text="someone else's open claim", kind="coverage",
                          load_bearing=True)], author="s2", round_n=3)
    assert [p.id for p in led.nominatable("s1")] == ["p1", "p2"]


def test_the_stamp_is_in_the_table_and_the_dump():
    led = _verified_by()
    led.stamp_premise("p1", establishes=False, claim_holds=True, holds_reason="no rival", reason="no", round_n=3)
    assert "stamp" in led.render_table()
    assert "false" in led.render_table()
    [rec] = led.to_records("Q216")
    assert rec["stamp"] == "false" and rec["stamp_reason"] == "no"
    assert rec["rival"] == "the other flows in the window"


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
    return entry(**{"route": "COMMAND", "senior_id": "s1", "decision": "continue",
                    "directive": "go further", "r1_scope_alignment": "PASS",
                    "r2_progress": "PASS", "r3_answer_readiness": "WEAK",
                    "r4_premise_verification": "WEAK", **kw})


def test_a_turn_leaving_a_new_verification_unstamped_is_rejected():
    led = _verified_by()
    out = stamp_violations([_command()], led)
    assert out and "p1" in out[0]


def test_a_stamped_verification_passes_the_gate():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(
            id="p1", establishes=False, claim_holds=True, holds_reason="no rival",
            reason="the claim says route (c) was not searched; the quote is the "
                   "result of searching it")])],
        led)
    assert out == []


def test_a_stamp_needs_a_reason():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(
            id="p1", establishes=True, claim_holds=True,
            holds_reason="no rival", reason="  ")])],
        led)
    assert out and "no reason" in out[0]


def test_a_premise_stamped_in_an_earlier_turn_is_not_restamped():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, claim_holds=True, holds_reason="no rival", reason="it does", round_n=2)
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(id="p1", establishes=False, claim_holds=True, holds_reason="no rival",
                                               reason="second thoughts")])],
        led)
    assert out and "earlier turn" in out[0]


def test_a_stamp_on_an_unknown_id_is_rejected():
    led = _verified_by()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(id="p9", establishes=True, claim_holds=True, holds_reason="no rival",
                                               reason="it does")])],
        led)
    assert out and "not a premise" in out[0]


def test_a_stamp_may_arrive_on_a_different_entry_of_the_same_turn():
    """The turn is judged as a whole: SH may stamp in one entry and route in another."""
    led = _verified_by()
    out = stamp_violations(
        [entry(route="RETIRE", senior_id="s1", reason="done",
               premise_stamps=[PremiseStamp(id="p1", establishes=True, claim_holds=True, holds_reason="no rival",
                                            reason="the census covers it")]),
         _command(senior_id="s2")],
        led)
    assert out == []


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
                 premise_stamps=[PremiseStamp(id="p1", establishes=False, claim_holds=True, holds_reason="no rival",
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
                 premise_stamps=[PremiseStamp(id="p1", establishes=True, claim_holds=True, holds_reason="no rival",
                                              reason="the census covers every route")])
    assert r4_ceiling("s1", e, led) == "PASS"
    assert grade_ceiling_violations([e], led) == []


def test_sh_may_always_grade_below_the_ceiling():
    led = _verified_by()
    e = _command(r4_premise_verification="FAIL",
                 premise_stamps=[PremiseStamp(id="p1", establishes=True, claim_holds=True, holds_reason="no rival",
                                              reason="the census covers every route")])
    assert grade_ceiling_violations([e], led) == []


def test_an_ungraded_entry_has_no_ceiling():
    """A SPAWN grades NA, and an exploration worker is never graded at all."""
    led = _verified_by()
    assert grade_ceiling_violations(
        [entry(route="SPAWN", spawn_type="senior", subquestion="go", deviation="x")],
        led) == []


def _false_stamp(**kw):
    return _command(premise_stamps=[PremiseStamp(
        id="p1", establishes=False, claim_holds=True, holds_reason="no rival",
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
