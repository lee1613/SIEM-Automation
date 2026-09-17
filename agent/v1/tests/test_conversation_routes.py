import pytest
from pydantic import ValidationError

from conversation import (BASES, ROUTES, TECHNIQUES, SeniorDirective, SHTurn,
                          answer_blocked, directive_violations, effective_r2,
                          grade_violations)
from question_state import QuestionState

BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "route": "RETIRE",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}


def entry(**kw) -> SeniorDirective:
    """Every field is required under strict json_schema, so tests fill the rest."""
    return SeniorDirective(**{**BLANK, **kw})


def test_a_well_formed_command_parses():
    e = entry(senior_id="s1", route="COMMAND", decision="continue",
              rationale="The account id is established; the user axis is next.",
              directive="Establish which IAM principal performed the enumeration.",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK")
    assert e.route == "COMMAND" and e.decision == "continue"


def test_command_rejects_critic_as_a_decision():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="COMMAND", decision="critic",
              rationale="x", directive="y")


def test_command_requires_a_directive():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="COMMAND", decision="retry",
              rationale="x", directive="   ")


def test_critic_requires_a_flaw():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CRITIC", basis="shape_mismatch",
              flaw="", why_it_fails="w", fix_directive="f")


def test_critic_requires_why_it_fails():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CRITIC", basis="shape_mismatch",
              flaw="f", why_it_fails="", fix_directive="d")


def test_critic_requires_a_fix_directive():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CRITIC", basis="shape_mismatch",
              flaw="f", why_it_fails="w", fix_directive="")


def test_critic_rejects_a_basis_outside_the_five():
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CRITIC", basis="other",
              flaw="f", why_it_fails="w", fix_directive="d")


def test_every_documented_basis_is_accepted():
    for b in BASES:
        e = entry(senior_id="s1", route="CRITIC", basis=b, flaw="f",
                  why_it_fails="w", fix_directive="d")
        assert e.basis == b


def test_routes_and_techniques_tuples_match_the_literals():
    for r in ROUTES:
        entry(senior_id="s1", route=r, reason="x", directive="x", decision="continue",
              rationale="x", basis=BASES[0], flaw="f", why_it_fails="w", fix_directive="d",
              clarify_reason="unclear", questions=["q"], spawn_type="senior",
              technique="hunter", subquestion="s", value="v", source_senior="s1",
              justification="j")
    for t in TECHNIQUES:
        e = entry(route="SPAWN", spawn_type="senior", technique=t,
                  subquestion="s", reason="r")
        assert e.technique == t


def test_a_route_requiring_senior_id_rejects_a_blank_one():
    for r in ("COMMAND", "CRITIC", "CLARIFY", "RETIRE"):
        with pytest.raises(ValidationError):
            entry(senior_id="", route=r, reason="x", directive="x", decision="continue",
                  rationale="x", basis=BASES[0], flaw="f", why_it_fails="w",
                  fix_directive="d", clarify_reason="unclear", questions=["q"])


def test_clarify_needs_a_reason_and_one_to_three_questions():
    e = entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect",
              questions=["Was the window the one I gave you?"])
    assert len(e.questions) == 1
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect", questions=[])
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CLARIFY", clarify_reason="", questions=["q"])
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="CLARIFY", clarify_reason="unclear",
              questions=["a", "b", "c", "d"])


def test_spawn_needs_a_type_a_subquestion_and_a_technique():
    e = entry(route="SPAWN", spawn_type="senior", technique="metrics",
              subquestion="Compute the p25/p75 of flow duration in SPL.",
              reason="The metrics rule has to be enforced at spawn time.")
    assert e.technique == "metrics"
    with pytest.raises(ValidationError):
        entry(route="SPAWN", spawn_type="senior", technique="", subquestion="x", reason="y")
    with pytest.raises(ValidationError):
        entry(route="SPAWN", spawn_type="exploration", subquestion="", reason="y")


def test_retire_needs_a_target_and_a_reason():
    assert entry(senior_id="s1", route="RETIRE", reason="Two dead rounds.").route == "RETIRE"
    with pytest.raises(ValidationError):
        entry(senior_id="s1", route="RETIRE", reason="")


def test_answer_needs_a_value_and_a_source():
    e = entry(route="ANSWER", value="199.66.91.253", value_kind="ip",
              source_senior="s1", justification="s1 round 2 showed it in cloudtrail.",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert e.value == "199.66.91.253"
    with pytest.raises(ValidationError):
        entry(route="ANSWER", value="", source_senior="s1", justification="j")
    with pytest.raises(ValidationError):
        entry(route="ANSWER", value="v", source_senior="", justification="j")


def test_a_turn_is_a_reading_plus_entries():
    t = SHTurn(reading="Senior #1 ruled out cloudtrail.",
               entries=[entry(senior_id="s1", route="RETIRE", reason="done")])
    assert len(t.entries) == 1


# ── grades ───────────────────────────────────────────────────────────────────

def test_a_senior_entry_must_carry_real_grades():
    e = entry(senior_id="s1", route="COMMAND", decision="continue",
              rationale="r", directive="d")           # grades left NA
    assert grade_violations([e], graded={"s1"}, exploration=set()) != []


def test_an_exploration_entry_must_not_be_graded():
    e = entry(senior_id="e1", route="RETIRE", reason="scope proposed",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert grade_violations([e], graded=set(), exploration={"e1"}) != []
    ok = entry(senior_id="e1", route="RETIRE", reason="scope proposed")
    assert grade_violations([ok], graded=set(), exploration={"e1"}) == []


def test_spawn_entries_are_not_graded():
    e = entry(route="SPAWN", spawn_type="senior", technique="hunter",
              subquestion="s", reason="r")
    assert grade_violations([e], graded=set(), exploration=set()) == []


def test_code_r2_fail_is_not_overridable_by_sh():
    assert effective_r2("PASS", novel_spl_count=0) == "FAIL"
    assert effective_r2("WEAK", novel_spl_count=0) == "FAIL"


def test_sh_can_fail_r2_on_novel_but_useless_queries():
    assert effective_r2("FAIL", novel_spl_count=3) == "FAIL"
    assert effective_r2("PASS", novel_spl_count=3) == "PASS"


def test_r1_fail_blocks_answer_and_r2_r3_do_not():
    bad = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
                r1_scope_alignment="FAIL", r2_progress="PASS", r3_answer_readiness="PASS")
    assert answer_blocked(bad) is True
    for grade in ("r2_progress", "r3_answer_readiness"):
        kw = {"r1_scope_alignment": "PASS", "r2_progress": "PASS",
              "r3_answer_readiness": "PASS"}
        kw[grade] = "FAIL"
        ok = entry(route="ANSWER", value="v", source_senior="s1", justification="j", **kw)
        assert answer_blocked(ok) is False


# ── turn-level validation against the budget ─────────────────────────────────

def test_continue_is_refused_after_two_r2_fails():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    st.record_r2("s1", failed=True)
    st.record_r2("s1", failed=True)
    e = entry(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
              directive="d", r1_scope_alignment="PASS", r2_progress="WEAK",
              r3_answer_readiness="WEAK")
    assert directive_violations([e], st) != []


def test_a_directive_to_a_senior_with_no_rounds_left_is_refused():
    st = QuestionState(points=100)          # 3 rounds
    st.open_senior("s1")
    for _ in range(3):
        st.record_wave(); st.record_round("s1")
    e = entry(senior_id="s1", route="CRITIC", basis="shape_mismatch", flaw="f",
              why_it_fails="w", fix_directive="d", r1_scope_alignment="PASS",
              r2_progress="PASS", r3_answer_readiness="WEAK")
    assert directive_violations([e], st) != []


def test_a_fourth_spawn_is_refused():
    st = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        st.open_senior(sid)
    e = entry(route="SPAWN", spawn_type="senior", technique="hunter",
              subquestion="s", reason="r")
    assert directive_violations([e], st) != []


def test_a_second_exploration_is_refused_and_costs_no_slot():
    st = QuestionState(points=1000)
    st.open_exploration("e1")
    e = entry(route="SPAWN", spawn_type="exploration", subquestion="s", reason="r")
    assert directive_violations([e], st) != []
    assert st.spawns_used == 0


def test_two_explorations_in_one_turn_are_refused_even_from_a_fresh_state():
    st = QuestionState(points=1000)          # nothing committed yet
    e1 = entry(route="SPAWN", spawn_type="exploration", subquestion="s1", reason="r")
    e2 = entry(route="SPAWN", spawn_type="exploration", subquestion="s2", reason="r")
    assert directive_violations([e1, e2], st) != []


def test_answer_with_r1_fail_is_refused_at_turn_level():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    e = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
              r1_scope_alignment="FAIL", r2_progress="PASS", r3_answer_readiness="PASS")
    assert directive_violations([e], st) != []


def test_a_clean_turn_has_no_violations():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    e = entry(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
              directive="Establish which principal did it.", r1_scope_alignment="PASS",
              r2_progress="PASS", r3_answer_readiness="WEAK")
    assert directive_violations([e], st) == []


def test_two_routes_to_one_senior_are_refused():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    graded = dict(r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK")
    cont = entry(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
                 directive="d", **graded)
    retire = entry(senior_id="s1", route="RETIRE", reason="done", **graded)
    assert directive_violations([cont, retire], st) != []


def test_a_read_report_left_unrouted_is_refused():
    graded = dict(r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK")
    only_s1 = entry(senior_id="s1", route="RETIRE", reason="done", **graded)
    assert grade_violations([only_s1], graded={"s1", "s2"}, exploration=set()) != []
    answer_s2 = entry(route="ANSWER", value="v", source_senior="s2", justification="j",
                      r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert grade_violations([only_s1, answer_s2], graded={"s1", "s2"}, exploration=set()) == []


def test_an_answer_turn_need_not_route_its_siblings():
    answer_s1 = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
                      r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert grade_violations([answer_s1], graded={"s1", "s2"}, exploration=set()) == []


def test_a_clarify_must_target_an_active_senior():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    st.retire("s1")
    e = entry(senior_id="s1", route="CLARIFY", clarify_reason="unclear", questions=["what?"])
    assert directive_violations([e], st) != []
    assert directive_violations([entry(senior_id="e2", route="CLARIFY", clarify_reason="unclear",
                                       questions=["what?"])], st) != []
