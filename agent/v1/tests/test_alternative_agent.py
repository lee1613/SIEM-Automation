"""The alternative agent (spec 2 §4, built in the v1.4.3 revision).

Not a new agent type: an ordinary senior whose brief the runner augments with the
refuted premises. Treating it as a new type would duplicate the whole senior stack to
add one prompt section.

What is NOT tested, because it is deliberately not enforced (spec 2 §4.3): that the AA's
candidate differs from the retired senior's, or that its reasoning avoids a refuted
premise. Both are observed in the run log. A hard "the value must differ" forces the AA
away from a correct answer; "must not re-derive a refuted premise" cannot be done from
free text without reintroducing a fuzzy string match under a new name.
"""

from conversation import SeniorDirective, deviation_violations
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from sh_loop import _spawn_directive

# Repeated rather than imported from another test module: agent/v1/tests is not a
# package and the repo has a second top-level tests/ directory, so a cross-test import
# is ambiguous. Same reason test_sh_loop.py carries its own copy.
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
