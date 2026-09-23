import pytest
from conversation import (
    BASES,
    ROUTES,
    TECHNIQUES,
    SeniorDirective,
    SHTurn,
    answer_blocked,
    directive_violations,
    effective_r2,
    grade_violations,
    ledger_violations,
    open_question_violations,
    premise_audit_violations,
    spawn_overlap_violations,
)
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from pydantic import ValidationError
from question_state import QuestionState

BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RETIRE",
    "open_question_answers": [], "new_premises": [],
    "answer_premise_ids": [],
    "premise_stamps": [], "nominate_premise_id": "",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "deviation": "", "inherited_entities": "", "recall_qid": "", "recall_what": "",
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
              technique="metrics", subquestion="s", value="v", source_senior="s1",
              justification="j", recall_qid="Q216", recall_what="summary")
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


def test_spawn_needs_a_type_and_a_subquestion():
    e = entry(route="SPAWN", spawn_type="senior", technique="metrics",
              subquestion="Compute the p25/p75 of flow duration in SPL.",
              reason="The metrics rule has to be enforced at spawn time.")
    assert e.technique == "metrics"
    with pytest.raises(ValidationError):
        entry(route="SPAWN", spawn_type="exploration", subquestion="", reason="y")


def test_a_plain_senior_spawn_needs_no_technique():
    e = entry(route="SPAWN", spawn_type="senior", technique="", subquestion="x", reason="y")
    assert e.technique == ""


def test_hunter_and_content_are_no_longer_offered_to_sh():
    # Pruned on smoke-run evidence: SH's directives already carry both rules.
    assert TECHNIQUES == ("metrics",)
    for gone in ("hunter", "content"):
        with pytest.raises(ValidationError):
            entry(route="SPAWN", spawn_type="senior", technique=gone,
                  subquestion="x", reason="y")


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
    e = entry(route="SPAWN", spawn_type="senior", technique="",
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
        st.record_wave()
        st.record_round("s1")
    e = entry(senior_id="s1", route="CRITIC", basis="shape_mismatch", flaw="f",
              why_it_fails="w", fix_directive="d", r1_scope_alignment="PASS",
              r2_progress="PASS", r3_answer_readiness="WEAK")
    assert directive_violations([e], st) != []


def test_a_fourth_spawn_is_refused():
    st = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        st.open_senior(sid)
    e = entry(route="SPAWN", spawn_type="senior", technique="",
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
    graded = dict(r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK",
                  r4_premise_verification="PASS")
    only_s1 = entry(senior_id="s1", route="RETIRE", reason="done", **graded)
    assert grade_violations([only_s1], graded={"s1", "s2"}, exploration=set()) != []
    answer_s2 = entry(route="ANSWER", value="v", source_senior="s2", justification="j",
                      r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
                      r4_premise_verification="PASS")
    assert grade_violations([only_s1, answer_s2], graded={"s1", "s2"}, exploration=set()) == []


def test_an_answer_turn_need_not_route_its_siblings():
    answer_s1 = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
                      r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
                      r4_premise_verification="PASS")
    assert grade_violations([answer_s1], graded={"s1", "s2"}, exploration=set()) == []


def test_a_clarify_must_target_an_active_senior():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    st.retire("s1")
    e = entry(senior_id="s1", route="CLARIFY", clarify_reason="unclear", questions=["what?"])
    assert directive_violations([e], st) != []
    assert directive_violations([entry(senior_id="e2", route="CLARIFY", clarify_reason="unclear",
                                       questions=["what?"])], st) != []


# ── the capped-report gate (§3.5) ──────────────────────────────────────────────
# test_20260918_104111: s1's round 1 ran out of iterations, its report carried the
# runner's "Iteration cap reached" line and two open questions for SH, and SH
# graded it all-PASS and answered 4 seconds later. The value was wrong. A report
# the senior was cut off mid-way through is not a finished report.

def _spawned(sid="s1", *, capped: bool) -> QuestionState:
    st = QuestionState(points=1000)
    st.open_senior(sid)
    st.record_round(sid, capped=capped)
    return st


def test_answer_is_blocked_when_its_source_report_was_cut_off_at_the_cap():
    e = entry(route="ANSWER", value="7113", value_kind="count", source_senior="s1",
              justification="the report computes the duration",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    out = directive_violations([e], _spawned(capped=True))
    assert any("cut off at the iteration cap" in v for v in out), out


def test_answer_passes_when_the_source_round_finished_on_its_own():
    e = entry(route="ANSWER", value="1666", value_kind="count", source_senior="s1",
              justification="coinhive flows bracket the window",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert directive_violations([e], _spawned(capped=False)) == []


def test_a_later_uncapped_round_clears_the_block():
    st = _spawned(capped=True)
    st.record_round("s1", capped=False)
    e = entry(route="ANSWER", value="1666", value_kind="count", source_senior="s1",
              justification="confirmed after one more round",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
    assert directive_violations([e], st) == []


def test_the_block_does_not_touch_other_routes():
    st = _spawned(capped=True)
    e = entry(senior_id="s1", route="COMMAND", decision="continue",
              rationale="finish the window", directive="Bracket the coinhive flows.",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK")
    assert directive_violations([e], st) == []


# ── R4 premise verification ──────────────────────────────────────────────────

def _graded(**kw):
    base = dict(senior_id="s1", route="COMMAND", decision="continue", rationale="r",
                directive="d", r1_scope_alignment="PASS", r2_progress="PASS",
                r3_answer_readiness="WEAK", r4_premise_verification="PASS")
    base.update(kw)
    return entry(**base)


def test_r4_is_required_on_a_graded_report():
    assert grade_violations([_graded()], graded={"s1"}, exploration=set()) == []
    no_r4 = _graded(r4_premise_verification="NA")
    assert grade_violations([no_r4], graded={"s1"}, exploration=set()) != []


def test_an_exploration_entry_must_not_carry_r4():
    e = entry(senior_id="e1", route="RETIRE", reason="scope proposed",
              r4_premise_verification="PASS")
    assert grade_violations([e], graded=set(), exploration={"e1"}) != []


def test_r4_fail_does_not_block_an_answer():
    # R4 is a warning, not a gate: an educated guess may be submitted.
    a = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
              r4_premise_verification="FAIL")
    st = QuestionState(points=1000)
    st.open_senior("s1")
    assert directive_violations([a], st) == []


def test_r4_fail_does_not_block_a_command():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    assert directive_violations([_graded(r4_premise_verification="FAIL")], st) == []


# ── SH must answer the senior's open questions ───────────────────────────────

def _asked(*texts, author="s1") -> PremiseLedger:
    led = PremiseLedger()
    led.ask(list(texts), author=author, round_n=1)
    return led


def test_unanswered_open_questions_reject_the_turn():
    led = _asked("Was the window the one you gave me?", "Do I stay in cisco:nvm?")
    assert open_question_violations([_graded()], led) != []
    one = _graded(open_question_answers=[{"id": "q1", "answer": "Yes, that window."},
                                         {"id": "q2", "answer": "   "}])
    assert open_question_violations([one], led) != []      # blanks do not count
    both = _graded(open_question_answers=[{"id": "q1", "answer": "Yes, that window."},
                                          {"id": "q2", "answer": "Stay in scope."}])
    assert open_question_violations([both], led) == []


def test_answering_one_question_twice_does_not_settle_the_other():
    # The old count check passed on two answers whichever questions they named.
    led = _asked("Was the window mine?", "Do I stay in cisco:nvm?")
    twice = _graded(open_question_answers=[{"id": "q1", "answer": "Yes."},
                                           {"id": "q1", "answer": "Yes, truly."}])
    out = open_question_violations([twice], led)
    assert out and "q2" in out[0]


def test_a_senior_that_asked_nothing_needs_no_answers():
    assert open_question_violations([_graded()], PremiseLedger()) == []
    assert open_question_violations([_graded()], _asked("q?", author="s2")) == []


def test_an_answer_route_answers_its_source_seniors_questions():
    led = _asked("Is host A the one in scope?")
    a = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
              r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
              r4_premise_verification="PASS")
    assert open_question_violations([a], led) != []
    a2 = entry(route="ANSWER", value="v", source_senior="s1", justification="j",
               r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
               r4_premise_verification="PASS",
               open_question_answers=[{"id": "q1", "answer": "Only the one host."}])
    assert open_question_violations([a2], led) == []


def test_every_route_to_a_senior_must_answer_its_questions():
    for route_kw in (dict(route="RETIRE", reason="done"),
                     dict(route="CLARIFY", clarify_reason="suspect", questions=["q?"]),
                     dict(route="CRITIC", basis=BASES[0], flaw="f", why_it_fails="w",
                          fix_directive="d")):
        e = entry(senior_id="s1", r1_scope_alignment="PASS", r2_progress="PASS",
                  r3_answer_readiness="WEAK", r4_premise_verification="PASS", **route_kw)
        assert open_question_violations([e], _asked("q?")) != [], route_kw["route"]


# ── a parallel senior must own a scope no other active senior touches ────────

def _scope(sourcetypes=(), sources=()):
    return {"sourcetypes": list(sourcetypes), "sources": list(sources), "fields": []}


def _senior_spawn(**scope):
    return entry(route="SPAWN", spawn_type="senior", subquestion="s", reason="r",
                 constraints=_scope(**scope))


def test_a_lone_spawn_needs_no_constraints():
    assert spawn_overlap_violations([_senior_spawn()], {}) == []


def test_disjoint_parallel_seniors_are_allowed():
    active = {"s1": SeniorDirective.model_fields["constraints"].annotation(**_scope(["dns"]))}
    assert spawn_overlap_violations([_senior_spawn(sourcetypes=["o365"])], active) == []
    two = [_senior_spawn(sourcetypes=["dns"]), _senior_spawn(sources=["smtp"])]
    assert spawn_overlap_violations(two, {}) == []


def test_an_overlapping_parallel_spawn_is_refused():
    active = {"s1": SeniorDirective.model_fields["constraints"].annotation(**_scope(["DNS"]))}
    out = spawn_overlap_violations([_senior_spawn(sourcetypes=["dns", "o365"])], active)
    assert out and "s1" in out[0]
    same_turn = [_senior_spawn(sources=["a"]), _senior_spawn(sources=["a"])]
    assert spawn_overlap_violations(same_turn, {}) != []


def test_an_unscoped_senior_cannot_run_in_parallel():
    active = {"s1": SeniorDirective.model_fields["constraints"].annotation(**_scope())}
    assert spawn_overlap_violations([_senior_spawn(sourcetypes=["dns"])], active) != []
    assert spawn_overlap_violations([_senior_spawn(), _senior_spawn(sources=["x"])], {}) != []


def test_exploration_spawns_are_not_scope_checked():
    e = entry(route="SPAWN", spawn_type="exploration", subquestion="s", reason="r")
    active = {"s1": SeniorDirective.model_fields["constraints"].annotation(**_scope())}
    assert spawn_overlap_violations([e], active) == []


# ── the premise ledger: what an ANSWER must rest on ──────────────────────────

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


def test_a_spent_senior_with_an_open_premise_calls_for_an_alternative_senior():
    # Q216 smoke5_r1: s1 spent its rounds on one lead; two slots were still free.
    state = QuestionState(points=1000)
    state.open_senior("s1")
    for _ in range(state.budget["rounds"]):
        state.record_round("s1")
    v = ledger_violations([_answer()], _ledger_with(), state)
    assert any("SPAWN an alternative senior" in x for x in v)


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


def test_retire_and_replace_in_one_turn_is_not_an_overlap():
    from conversation import spawn_overlap_violations
    sc = {"sourcetypes": ["stream:http"], "sources": [], "fields": []}
    turn = [entry(route="RETIRE", senior_id="s2", reason="r"),
            entry(route="SPAWN", spawn_type="senior", subquestion="q", reason="r",
                  technique="", constraints=sc)]
    active = {"s2": turn[1].constraints}
    assert spawn_overlap_violations(turn, active) == []


def test_retiring_a_retired_senior_is_rejected():
    st = QuestionState(points=1000)
    st.open_senior("s2")
    st.retire("s2")
    v = directive_violations([entry(route="RETIRE", senior_id="s2", reason="r")], st)
    assert any("already retired or was never spawned" in x for x in v)


def test_a_spawn_without_a_free_slot_gets_a_reminder():
    st = QuestionState(points=1000)
    st.spawns_used = st.budget["seniors"]
    v = directive_violations([entry(route="SPAWN", spawn_type="senior", subquestion="q",
                                    reason="r")], st)
    assert any("no free senior slot" in x for x in v)
