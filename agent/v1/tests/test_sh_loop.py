# agent/v1/tests/test_sh_loop.py
import os

from conversation import PremiseStamp, SeniorDirective, SHTurn
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from sh_loop import NO_ANSWER, render_wave, run_question

# Every SeniorDirective field is required under strict json_schema, so tests fill
# the unused ones. Repeated here rather than imported from
# test_conversation_routes: agent/v1/tests is not a package, and the repo has a
# second top-level tests/ directory, so a cross-test import is ambiguous.
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
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}


def entry(**kw) -> SeniorDirective:
    return SeniorDirective(**{**BLANK, **kw})


REPORT = ("# s1 - Q216 - Round 1\n**Insight:** FOUND\n\n## Prior rounds\n- r1\n\n"
          "## This round\n### What I ran\n- search x -> 3 events\n"
          "### What it means\nThe duration is 1367.875.\n\n## Ruled out\n- none\n")

# What the fake senior files into the ledger each round. p1 is the coverage premise
# every _answer() below rests on; p2 is the selection premise. v1.4.3: R4 is a ceiling
# on s1's WHOLE ground, not just what an answer cites, so p2 must be settled too or
# every PASS-graded turn below is refused. UPDATES verifies both for the tests that
# want clean ground; P1_ONLY_UPDATE (p2 left UNVERIFIED) is for the handful that are
# about the UNVERIFIED-premise block itself and must not be cleaned out from under it.
PREMISES = [PremiseDraft(text="mining could surface as stratum or DNS", kind="coverage",
                         load_bearing=True),
            PremiseDraft(text="this endpoint and not another", kind="selection",
                         load_bearing=True, rival="the two other hosts in the window")]
UPDATES = [PremiseUpdate(id="p1", status="VERIFIED", quote="dest_port=3333 count=3",
                         evidence="the full 22-value listing"),
           PremiseUpdate(id="p2", status="VERIFIED", quote="dest_port=3333 count=3",
                         evidence="the only endpoint in the listing")]
P1_ONLY_UPDATE = UPDATES[:1]
# The tool output those quotes are checked against (SeniorSession.tool_outputs).
TOOL_STATE = [{"type": "ToolMessage",
               "content": '{"results": [{"dest_port": "3333", "count": "3"}]}'}]


class _LLM:
    """Replays a scripted list of SHTurns; records what it was fed."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.seen = []

    def invoke(self, msgs, **kw):
        self.seen.append(list(msgs))    # a snapshot: the loop keeps appending to msgs
        if not self.turns:
            raise AssertionError("the loop asked for more turns than the test scripted")
        turn = self.turns.pop(0)
        if isinstance(turn, Exception):
            raise turn
        return turn


class _Pool:
    senior_model = "gpt-5.4-mini"

    def __init__(self, **over):
        self.result = {
            "status": "partial", "value": "1367.875", "value_kind": "duration_seconds",
            "evidence": "search x", "confidence": 70, "notes": "", "insight": "FOUND",
            "report": REPORT, "spl_used": ["search x"], "sourcetypes": ["cisco:nvm"],
            "negative_findings": [], "search_space_used": {"sourcetypes": [], "sources": []},
            "iterations": 6, "cap_hit": False, "structured": True,
            "last_prompt_tokens": 500, "answer": "", "full_state": TOOL_STATE,
            "new_premises": PREMISES, "premise_updates": UPDATES, "open_questions": [],
        }
        self.result.update(over)
        self.rounds = 0
        self.validations = 0
        self.clarifies = 0

    def run_round(self, **kw):
        # v1.4.3: validators share the worker pool but are not senior rounds. Without
        # this branch a validator would re-file the senior's premises and updates, and
        # `rounds` would count it against the senior's budget.
        if kw.get("technique") == "validator":
            self.validations += 1
            return {**self.result, "new_premises": [], "premise_updates": [],
                    "open_questions": [], "report": "validator report"}
        self.rounds += 1
        return dict(self.result)

    def clarify(self, **kw):
        self.clarifies += 1
        return "Yes — the window you gave me."


def _scoped(sourcetype, **kw):
    """A senior spawn that owns one sourcetype, so it can run beside another."""
    return _spawn(constraints={"sourcetypes": [sourcetype], "sources": [], "fields": []}, **kw)


def _spawn(**kw):
    base = dict(route="SPAWN", spawn_type="senior", technique="",
                subquestion="Find the flow duration in cisco:nvm.",
                reason="Only feed with a duration field.")
    base.update(kw)
    return entry(**base)


def _stamp_p1_only():
    """p1 alone: for the tests that run against P1_ONLY_UPDATE and deliberately leave
    p2 UNVERIFIED - the ceiling caps those turns at WEAK, so p2 is never owed a stamp."""
    return [PremiseStamp(id="p1", establishes=True,
                         reason="the 22-value port listing covers every route")]


def _stamp_p1_and_p2():
    """p1 and p2 are both VERIFIED from round 1 on (the fake senior's fixed UPDATES),
    so the first turn to read that wave owes a stamp on each - a load-bearing
    UNVERIFIED premise caps R4 at WEAK (v1.4.3's ceiling), so leaving p2 unstamped
    would cap every PASS-graded turn below. Only one turn per test may carry this -
    stamp_premise is once-only - so later turns pass premise_stamps=[] instead."""
    return [PremiseStamp(id="p1", establishes=True,
                         reason="the 22-value port listing covers every route"),
            PremiseStamp(id="p2", establishes=True,
                         reason="the listing shows no other endpoint")]


def _answer(value="1367.875", **kw):
    base = dict(route="ANSWER", value=value, value_kind="duration_seconds",
                source_senior="s1", justification="s1 round 1 showed it.",
                answer_premise_ids=["p1"],
                premise_stamps=_stamp_p1_and_p2(),
                r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS",
                r4_premise_verification="PASS")
    base.update(kw)
    return entry(**base)


def _turn(*entries):
    return SHTurn(reading="reading", entries=list(entries))


def _run(llm, pool, tmp_path, **kw):
    args = dict(llm=llm, pool=pool, qid="Q216", question="How long was the flow?",
                guidance="decimal seconds", points=1000, run_dir=str(tmp_path),
                hitl=False)
    args.update(kw)
    return run_question(**args)


def test_spawn_then_answer_solves_the_question(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["answer"] == "1367.875"
    assert out["end_reason"] == "answer"


def test_the_senior_runs_exactly_one_round_per_wave(tmp_path):
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.rounds == 1


def test_iterations_are_reported_against_the_tier_ceiling(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["senior_iterations"] == 6
    assert out["ceiling"] == 240            # 1000pt tier: 3 seniors x 8 rounds x 10


def test_an_ungrounded_answer_is_pushed_back_once_then_gives_no_answer(tmp_path):
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(value="999.999")),
                _turn(_answer(value="888.888", premise_stamps=[]))])
    out = _run(llm, _Pool(), tmp_path)
    assert out["end_reason"] == "ungrounded"
    # Neither of SH's values was grounded; the senior's value was never SH's answer.
    assert out["answer"] == NO_ANSWER


def test_a_rejected_turn_is_fed_back_and_costs_a_turn(tmp_path):
    # ANSWER graded R1 = FAIL is blocked by the wrong-question gate
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(r1_scope_alignment="FAIL")),
                _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["answer"] == "1367.875"
    assert out["turns"] == 3
    with open(os.path.join(str(tmp_path), "Q216", "conversation.md"), encoding="utf-8") as f:
        assert "REJECTED" in f.read()


def test_an_unstamped_verification_is_rejected_by_the_loop(tmp_path):
    """The stamp gate is IN the chain, not merely written in conversation.py.

    Its own unit tests would pass just as well if nobody had wired it up, and the
    fallout that proved the wiring - every scripted turn failing at once - disappears
    the moment those turns are given their stamps. This is what is left holding it.
    """
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(premise_stamps=[])),
                _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["answer"] == "1367.875"
    assert out["turns"] == 3, "the unstamped turn was refused and cost a turn"
    with open(os.path.join(str(tmp_path), "Q216", "conversation.md"), encoding="utf-8") as f:
        assert "you have not read them" in f.read()


def test_running_out_of_turns_ends_the_question_with_no_answer(tmp_path):
    # 100pt tier: 5 SH turns. Script 5 spawn-less no-op turns by clarifying forever.
    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="unclear",
                    questions=["what?"], r1_scope_alignment="WEAK",
                    r2_progress="PASS", r3_answer_readiness="WEAK", r4_premise_verification="PASS")
    llm = _LLM([_turn(_spawn())] + [_turn(clarify) for _ in range(6)])
    out = _run(llm, _Pool(), tmp_path, points=100)
    assert out["end_reason"] == "turns"
    assert out["answer"] == NO_ANSWER


def test_a_clarify_consumes_a_turn_but_no_wave(tmp_path):
    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect",
                    questions=["Was the window mine?"], r1_scope_alignment="PASS",
                    r2_progress="PASS", r3_answer_readiness="WEAK", r4_premise_verification="PASS",
                    premise_stamps=_stamp_p1_and_p2())
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(clarify), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, pool, tmp_path)
    assert pool.rounds == 1, "a clarify must not run a round"
    assert out["waves"] == 1
    assert out["turns"] == 3
    with open(os.path.join(str(tmp_path), "Q216", "conversation.md"), encoding="utf-8") as f:
        assert "[CLARIFY REPLY]" in f.read()


def test_retirement_writes_a_handoff(tmp_path):
    retire = entry(senior_id="s1", route="RETIRE", reason="scope exhausted",
                   r1_scope_alignment="PASS", r2_progress="WEAK",
                   r3_answer_readiness="WEAK", r4_premise_verification="PASS")
    llm = _LLM([_turn(_spawn()), _turn(retire), _turn(_answer())])
    _run(llm, _Pool(), tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "s1_handoff.md"))


def test_every_survivor_is_swept_into_a_handoff_at_the_end(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, _Pool(), tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "s1_handoff.md"))


def test_a_transport_failure_does_not_consume_a_slot(tmp_path):
    pool = _Pool(status="api_failed", value="", insight="NOT_FOUND", report="")
    # 100pt tier has exactly ONE slot; a refunded failure must allow a second spawn
    llm = _LLM([_turn(_spawn()), _turn(_spawn()), _turn(_spawn())])
    out = _run(llm, pool, tmp_path, points=100)
    assert out["spawns_used"] <= 1
    assert pool.rounds >= 2, "the refunded slot allowed another senior to run"


def test_grades_are_recorded_for_every_report_read(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    g = out["grades"][0]
    assert g["senior_id"] == "s1"
    assert g["r1"] == "PASS" and g["route"] == "ANSWER"
    assert g["novel_spl_count"] == 1


def test_a_repeated_round_is_graded_r2_fail_by_code(tmp_path):
    # both rounds run the same query, so round 2 has zero novel SPL
    cont = entry(senior_id="s1", route="COMMAND", decision="continue",
                 rationale="keep going", directive="Go one step further.",
                 r1_scope_alignment="PASS", r2_progress="PASS",
                 r3_answer_readiness="WEAK", r4_premise_verification="PASS",
                 premise_stamps=_stamp_p1_and_p2())
    llm = _LLM([_turn(_spawn()), _turn(cont), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, _Pool(), tmp_path)
    second = [g for g in out["grades"] if g["round"] == 2][0]
    assert second["r2_effective"] == "FAIL", "SH graded PASS; code overrides it"


def test_delegation_records_are_appended_for_the_ledger(tmp_path):
    sink = []
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, _Pool(), tmp_path, delegations=sink)
    assert len(sink) == 1
    assert sink[0]["value"] == "1367.875"
    assert sink[0]["worker"] == "s1"


# ── corrections to the plan (reviews of earlier tasks) ────────────────────────

SCOUT_REPORT = "EXPLORATION: flow durations live in sourcetype=cisco:nvm"


class _ScoutPool(_Pool):
    """A pool whose exploration worker is the one-shot NIM scout, not a senior."""

    def __init__(self, scout_status="partial", **over):
        super().__init__(**over)
        self.scout_status = scout_status
        self.explorations = 0

    def run_exploration(self, question, parent_qid, idx):
        self.explorations += 1
        return {"status": self.scout_status, "value": "", "value_kind": "",
                "evidence": "", "confidence": None, "notes": "try cisco:nvm",
                "insight": "NOT_FOUND", "report": "", "answer": SCOUT_REPORT,
                "spl_used": [], "sourcetypes": ["cisco:nvm"], "full_state": [],
                "iterations": 0, "cap_hit": False, "structured": True,
                "search_space_used": {"sourcetypes": ["cisco:nvm"], "sources": []},
                "negative_findings": [], "role": "exploration", "provider": "nim"}


def _scout():
    return entry(route="SPAWN", spawn_type="exploration",
                 subquestion="Which feed records flow durations?",
                 reason="Cannot name a scope yet.")


def test_an_exploration_spawn_runs_once_as_a_scout_not_a_senior(tmp_path):
    pool, sink = _ScoutPool(), []
    llm = _LLM([_turn(_spawn(), _scout()), _turn(_answer())])
    out = _run(llm, pool, tmp_path, delegations=sink)
    assert pool.explorations == 1
    assert pool.rounds == 1, "the scout must not run through the senior graph"
    assert out["spawns_used"] == 1, "a scout takes no senior slot"
    assert [g["senior_id"] for g in out["grades"]] == ["s1"], "a scout is never graded"
    assert any(SCOUT_REPORT in str(m.content) for m in llm.seen[-1]), \
        "SH is shown the scope proposal"
    assert sorted(d["spawn_type"] for d in sink) == ["exploration", "senior"]
    assert not os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "e2_handoff.md"))


def test_an_exploration_failure_does_not_refund_a_senior_slot(tmp_path):
    pool = _ScoutPool(scout_status="api_failed")
    llm = _LLM([_turn(_spawn(), _scout()), _turn(_answer())])
    out = _run(llm, pool, tmp_path, points=100)
    assert out["spawns_used"] == 1, "only a senior's transport failure refunds a slot"


def test_a_transport_failure_writes_a_handoff(tmp_path):
    pool = _Pool(status="api_failed", value="", insight="NOT_FOUND", report="")
    llm = _LLM([_turn(_spawn()), _turn(_spawn()), _turn(_spawn())])
    _run(llm, pool, tmp_path, points=100)
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "s1_handoff.md"))


def test_a_failed_clarify_is_fed_back_and_the_question_continues(tmp_path):
    class _BrokenClarify(_Pool):
        def clarify(self, **kw):
            raise RuntimeError("HTTP 429 rate limited")

    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect",
                    questions=["Was the window mine?"], r1_scope_alignment="PASS",
                    r2_progress="PASS", r3_answer_readiness="WEAK", r4_premise_verification="PASS",
                    premise_stamps=_stamp_p1_and_p2())
    llm = _LLM([_turn(_spawn()), _turn(clarify), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, _BrokenClarify(), tmp_path)
    assert out["answer"] == "1367.875"
    assert any("clarify failed" in str(m.content) for m in llm.seen[-1])


# ── review fixes on 9795a4e ───────────────────────────────────────────────────

def _continue(**kw):
    base = dict(senior_id="s1", route="COMMAND", decision="continue",
                rationale="keep going", directive="Go one step further.",
                r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK",
                r4_premise_verification="PASS")
    base.update(kw)
    return entry(**base)


def _retire(sid="s1", **kw):
    base = dict(senior_id=sid, route="RETIRE", reason="done", r1_scope_alignment="PASS",
                r2_progress="PASS", r3_answer_readiness="WEAK", r4_premise_verification="PASS")
    base.update(kw)
    return entry(**base)


def _conversation(tmp_path, qid="Q216"):
    with open(os.path.join(str(tmp_path), qid, "conversation.md"), encoding="utf-8") as f:
        return f.read()


def test_anti_thrash_sees_the_grades_of_the_report_being_read(tmp_path):
    # I1: rounds 2 and 3 repeat round 1's SPL -> both code-FAIL. The continue on turn 4
    # reads round 3, so the streak is already 2 and it must be refused.
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_continue(premise_stamps=_stamp_p1_and_p2())),
                _turn(_continue()),
                _turn(_continue()), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, pool, tmp_path)
    assert pool.rounds == 3, "a third consecutive continue must not run round 4"
    assert out["answer"] == "1367.875"
    assert "two consecutive R2 FAILs" in _conversation(tmp_path)


def test_sh_reads_and_can_answer_from_the_final_wave(tmp_path):
    # I2: 100pt has 3 rounds; the third wave must still be read by SH.
    llm = _LLM([_turn(_spawn()), _turn(_continue(premise_stamps=_stamp_p1_and_p2())),
                _turn(_continue()), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, _Pool(), tmp_path, points=100)
    assert out["end_reason"] == "answer"
    assert len(out["grades"]) == 3


def test_sh_is_told_about_a_transport_failed_round(tmp_path):
    # I3
    pool = _Pool(status="api_failed", value="", insight="NOT_FOUND", report="")
    llm = _LLM([_turn(_spawn()), _turn(_spawn()), _turn(_spawn())])
    _run(llm, pool, tmp_path, points=100)
    last = str(llm.seen[1][-1].content)
    assert "transport failure" in last and "s1" in last


def test_sh_remembers_earlier_questions_through_history(tmp_path):
    # I4
    history = []
    _run(_LLM([_turn(_spawn()), _turn(_answer())]), _Pool(), tmp_path, history=history)
    after_first = len(history)
    assert after_first > 0
    assert not any(type(m).__name__ == "SystemMessage" for m in history)

    llm2 = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm2, _Pool(), tmp_path, qid="Q217", history=history)
    assert any("Q216" in str(m.content) for m in llm2.seen[0]), \
        "question 2's first SH call sees question 1"
    assert len(history) > after_first


def test_no_history_means_a_fresh_thread_per_question(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, _Pool(), tmp_path)
    assert len(llm.seen[0]) == 2          # system prompt + opening only


def test_the_history_window_mirrors_the_orchestrator():
    import orchestrator
    import sh_loop
    assert sh_loop.MAX_HISTORY_MSGS == orchestrator.MAX_HISTORY_MSGS


def test_a_malformed_sh_turn_is_fed_back_not_fatal(tmp_path):
    # I5: strict json_schema does not run the cross-field validator
    import pydantic
    bad = None
    try:
        entry(senior_id="s1", route="RETIRE", reason="")
    except pydantic.ValidationError as exc:
        bad = exc
    assert bad is not None
    llm = _LLM([_turn(_spawn()), bad, _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["end_reason"] == "answer"
    assert out["turns"] == 3
    assert any("did not validate" in str(m.content) for m in llm.seen[-1])


def test_a_read_report_sh_does_not_route_is_rejected(tmp_path):
    # M1: two seniors report; SH routes only s1, then fixes it
    pool = _Pool()
    # s2's own premises (p3/p4) are never in the fixture's fixed-id UPDATES, so they
    # stay UNVERIFIED for the life of this test - the ANSWER built on s2's report is
    # graded WEAK, the most the ceiling allows while that ground is never settled.
    llm = _LLM([_turn(_scoped("dns"), _scoped("smtp", subquestion="Other feed.")),
                _turn(_continue()),
                _turn(_answer(source_senior="s2", r4_premise_verification="WEAK"),
                     _retire("s1"))])
    out = _run(llm, pool, tmp_path)
    assert "no route addressed it" in _conversation(tmp_path)
    assert pool.rounds == 2, "the half-routed turn ran nothing"
    assert out["end_reason"] == "answer"


def test_two_routes_to_one_senior_in_a_turn_are_rejected(tmp_path):
    # M1
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_continue(), _retire()), _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.rounds == 1
    assert "more than one route" in _conversation(tmp_path)


def test_a_clarify_to_a_retired_senior_is_rejected(tmp_path):
    # M2
    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect",
                    questions=["Sure?"])
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_retire(premise_stamps=_stamp_p1_and_p2())),
                _turn(clarify), _turn(_answer(premise_stamps=[]))])
    _run(llm, pool, tmp_path)
    assert pool.clarifies == 0
    assert "s1 is not an active senior" in _conversation(tmp_path)


def test_no_value_anywhere_ends_with_the_honest_marker(tmp_path):
    # report text is never submitted, and neither is an empty string
    pool = _Pool(value="", insight="NOT_FOUND")
    llm = _LLM([_turn(_spawn()), _turn(_retire(premise_stamps=_stamp_p1_and_p2()))]
              + [_turn() for _ in range(3)])
    out = _run(llm, pool, tmp_path, points=100)
    assert out["end_reason"] == "rounds"   # the one slot is spent and retired
    assert out["answer"] == NO_ANSWER


def test_a_value_sh_never_answered_with_is_not_submitted(tmp_path):
    # Q217 (test_20260918_113209): SH retired its seniors "rather than force an
    # unsupported answer", then the old fallback submitted a senior's value anyway.
    # The senior's report here holds a value and is graded R1 PASS.
    llm = _LLM([_turn(_spawn()), _turn(_retire(premise_stamps=_stamp_p1_and_p2()))]
              + [_turn() for _ in range(3)])
    out = _run(llm, _Pool(), tmp_path, points=100)
    assert out["end_reason"] == "rounds"
    assert out["answer"] == NO_ANSWER
    assert out["answer"] != "1367.875"


def test_the_stamped_rounds_remaining_counts_this_round_as_spent(tmp_path):
    # M5: 100pt grants 3 rounds; after round 1, 2 remain
    llm = _LLM([_turn(_spawn()), _turn(_answer())])
    _run(llm, _Pool(), tmp_path, points=100)
    with open(os.path.join(str(tmp_path), "Q216", "reports", "s1_round_1.md"),
              encoding="utf-8") as f:
        assert "rounds_remaining=2" in f.read()


def test_a_crashing_senior_is_retired_and_its_sibling_survives(tmp_path):
    # M6
    class _Crashy(_Pool):
        def run_round(self, **kw):
            if kw["idx"] == 1:
                raise RuntimeError("graph exploded")
            return super().run_round(**kw)

    llm = _LLM([_turn(_scoped("dns"), _scoped("smtp", subquestion="Other feed.")),
                _turn(_answer(source_senior="s2"))])
    out = _run(llm, _Crashy(), tmp_path)
    assert out["answer"] == "1367.875"
    assert out["spawns_used"] == 1, "the crashed senior's slot was refunded"
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "s1_handoff.md"))


def test_entries_after_a_grounded_answer_are_ignored(tmp_path):
    # M7
    llm = _LLM([_turn(_spawn()), _turn(_answer(), _spawn(subquestion="Too late."))])
    out = _run(llm, _Pool(), tmp_path)
    assert out["end_reason"] == "answer"
    assert out["spawns_used"] == 1
    assert not os.path.exists(os.path.join(str(tmp_path), "Q216", "handoffs", "s2_handoff.md"))


def test_each_delegation_records_its_duration(tmp_path):
    # M8
    import time

    class _Slow(_Pool):
        def run_round(self, **kw):
            time.sleep(0.02)
            return super().run_round(**kw)

    sink = []
    _run(_LLM([_turn(_spawn()), _turn(_answer())]), _Slow(), tmp_path, delegations=sink)
    assert sink[0]["duration_s"] >= 0.01


# ── SH must answer the senior's open questions; R4 is recorded ───────────────

class _Recording(_Pool):
    def __init__(self, **over):
        super().__init__(**over)
        self.messages = []
        self.validator_messages = []

    def run_round(self, **kw):
        # `messages` means "what the SENIOR was told", which is what the carry-forward
        # assertions are about. Validators share the pool, so their briefings would
        # otherwise interleave and shift every index.
        if kw.get("technique") == "validator":
            self.validator_messages.append(kw.get("message", ""))
        else:
            self.messages.append(kw.get("message", ""))
        return super().run_round(**kw)


class _Asking(_Recording):
    """Files one open question into the ledger, on its first round only."""

    def run_round(self, **kw):
        r = super().run_round(**kw)
        if self.rounds == 1:
            r["open_questions"] = ["Is host A the one the question means?"]
        return r


def test_ignoring_a_seniors_open_question_is_rejected(tmp_path):
    pool = _Asking()
    answered = _continue(open_question_answers=[
        {"id": "q1", "answer": "Yes: host A is the endpoint in scope."}],
        premise_stamps=_stamp_p1_and_p2())
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(answered),
                _turn(_answer(premise_stamps=[]))])
    _run(llm, pool, tmp_path)
    assert pool.rounds == 2, "the ignoring turn must not run a round"
    assert "waiting on q1" in _conversation(tmp_path)
    assert "host A is the endpoint in scope" in pool.messages[-1], \
        "SH's answer must reach the senior with its next directive"


def test_an_answered_question_is_not_owed_again(tmp_path):
    # Settled in the ledger, so the ANSWER turn that follows owes nothing.
    pool = _Asking()
    answered = _continue(open_question_answers=[
        {"id": "q1", "answer": "Yes: host A is the endpoint in scope."}],
        premise_stamps=_stamp_p1_and_p2())
    llm = _LLM([_turn(_spawn()), _turn(answered), _turn(_answer(premise_stamps=[]))])
    out = _run(llm, pool, tmp_path)
    assert out["end_reason"] == "answer"
    assert out["ledger"].open_questions_for("s1") == []


def test_grade_rows_record_r4(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer(r4_premise_verification="WEAK"))])
    out = _run(llm, _Pool(), tmp_path)
    assert out["grades"][0]["r4"] == "WEAK"


# ── v1.4.1: soft R4, parallel seniors on disjoint scopes ─────────────────────

def test_an_answer_on_an_unverified_premise_is_allowed_but_logged(tmp_path):
    # R4 is a warning, not a gate: an educated guess may be submitted.
    llm = _LLM([_turn(_spawn()), _turn(_answer(r4_premise_verification="FAIL"))])
    out = _run(llm, _Pool(), tmp_path)
    assert out["answer"] == "1367.875"
    assert "unverified premise" in _conversation(tmp_path).lower()


def test_the_runner_carries_the_unresolved_premises_into_the_next_round(tmp_path):
    # Replaces the verify-first prefix: the runner prepends p2 (still UNVERIFIED)
    # to round 2 itself, so SH's grade cannot decide whether the senior is reminded.
    # p2 must stay UNVERIFIED for this test to mean anything, so the pool settles p1
    # alone (v1.4.3's ceiling would otherwise cap every PASS-graded turn at WEAK).
    pool = _Recording(premise_updates=P1_ONLY_UPDATE)
    llm = _LLM([_turn(_spawn()),
                _turn(_continue(r4_premise_verification="WEAK", premise_stamps=_stamp_p1_only())),
                _turn(_answer(r4_premise_verification="WEAK", premise_stamps=[]))])
    _run(llm, pool, tmp_path)
    assert "YOUR UNRESOLVED PREMISES" in pool.messages[1]
    assert "p2" in pool.messages[1]


def test_the_carry_forward_does_not_depend_on_shs_r4_grade(tmp_path):
    # v1.4.2: the old reminder fired on WEAK/FAIL R4 only, and SH grades all-PASS
    # when it wants to answer. p2 stays UNVERIFIED here for the same reason as above;
    # R4 is graded WEAK to match the ceiling, not PASS, since the ground is still dirty.
    pool = _Recording(premise_updates=P1_ONLY_UPDATE)
    llm = _LLM([_turn(_spawn()),
                _turn(_continue(r4_premise_verification="WEAK", premise_stamps=_stamp_p1_only())),
                _turn(_answer(r4_premise_verification="WEAK", premise_stamps=[]))])
    _run(llm, pool, tmp_path)
    assert "YOUR UNRESOLVED PREMISES" in pool.messages[1]


def test_the_wave_shows_sh_every_unsettled_premise():
    led = PremiseLedger()
    led.add(PREMISES, author="s1", round_n=1)
    led.apply(P1_ONLY_UPDATE, author="s1", corpus=[TOOL_STATE[0]["content"]], round_n=1)
    text = render_wave({"s1": {"report": REPORT, "novel_spl_count": 1}},
                       slots_remaining=1, turns_remaining=3, ledger=led)
    assert "p2" in text and "UNVERIFIED" in text
    assert "p1" in text and "VERIFIED" in text


def test_two_parallel_seniors_on_disjoint_scopes_both_run(tmp_path):
    pool = _Pool()
    llm = _LLM([_turn(_scoped("dns"), _scoped("smtp", subquestion="Other feed.")),
                _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.rounds == 2


def test_an_overlapping_parallel_spawn_is_rejected(tmp_path):
    pool = _Pool()
    llm = _LLM([_turn(_scoped("dns"), _scoped("dns", subquestion="Same feed.")),
                _turn(_spawn()), _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.rounds == 1, "the overlapping turn ran nothing"
    assert "overlap" in _conversation(tmp_path).lower()


def test_a_runaway_senior_is_retired_without_pausing_the_run(tmp_path, monkeypatch):
    # Q216 2026-09-18: a runaway reached the HITL pause and stopped the whole run.
    import sh_loop
    paused = []
    monkeypatch.setattr(sh_loop, "resolve_interrupt", lambda *a, **k: paused.append(a) or "skip")
    llm = _LLM([_turn(_spawn()), _turn()] + [_turn() for _ in range(3)])
    out = _run(llm, _Pool(status="runaway"), tmp_path, hitl=True, points=100)
    assert paused == [], "a runaway is handled by the loop, not by a human"
    assert out["answer"] == NO_ANSWER


def test_a_provider_outage_still_asks_a_human(tmp_path, monkeypatch):
    import sh_loop
    paused = []
    monkeypatch.setattr(sh_loop, "resolve_interrupt", lambda *a, **k: paused.append(a) or "skip")
    llm = _LLM([_turn(_spawn()), _turn()] + [_turn() for _ in range(3)])
    _run(llm, _Pool(status="api_failed"), tmp_path, hitl=True, points=100)
    assert len(paused) == 1


def test_an_answer_citing_no_premise_is_rejected_then_accepted(tmp_path):
    llm = _LLM([_turn(_spawn()), _turn(_answer(answer_premise_ids=[])), _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    assert out["answer"] == "1367.875" and out["turns"] == 3
    log = _conversation(tmp_path)
    assert "names no premises" in log and "Premises it rests on:** p1" in log


def test_an_answer_on_an_unverified_premise_is_blocked_while_rounds_remain(tmp_path):
    # Q216 r10 answered over two UNVERIFIED premises that decided the value. p2 stays
    # UNVERIFIED here (P1_ONLY_UPDATE), so the second answer's R4 is WEAK - the most
    # the ceiling allows while s1 still holds a load-bearing UNVERIFIED premise.
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(answer_premise_ids=["p1", "p2"])),
                _turn(_answer(r4_premise_verification="WEAK",
                              premise_stamps=_stamp_p1_only()))])
    out = _run(llm, _Pool(premise_updates=P1_ONLY_UPDATE), tmp_path)
    assert out["end_reason"] == "answer"
    assert "load-bearing premise(s) it rests on are still UNVERIFIED" \
        in _conversation(tmp_path)


def test_a_missing_coverage_premise_is_visible_to_sh_as_absence():
    # The table replaces the old '!!' warnings: SH sees which kinds were filed.
    led = PremiseLedger()
    led.add(PREMISES[1:], author="s1", round_n=1)     # selection only
    text = render_wave({"s1": {"report": REPORT, "novel_spl_count": 1}},
                       slots_remaining=2, turns_remaining=5, ledger=led)
    assert "selection" in text and "coverage" not in text


def test_the_senior_task_leads_with_the_question_verbatim():
    from sh_loop import verbatim_task
    t = verbatim_task("For how many seconds?", "Round it.", "Compute the total seconds.")
    assert t.index("For how many seconds?") < t.index("Compute the total seconds.")
    assert "Answer format guidance: Round it." in t


def test_retiring_a_retired_senior_again_gets_a_reminder(tmp_path):
    # Q217 smoke5_r1: SH retired the same senior ten times over.
    retire = entry(senior_id="s1", route="RETIRE", reason="scope exhausted",
                   r1_scope_alignment="PASS", r2_progress="WEAK",
                   r3_answer_readiness="WEAK", r4_premise_verification="PASS",
                   premise_stamps=_stamp_p1_and_p2())
    llm = _LLM([_turn(_spawn()), _turn(retire), _turn(retire),
                _turn(_answer(premise_stamps=[]))])
    _run(llm, _Pool(), tmp_path)
    assert "s1 is already retired or was never spawned" in _conversation(tmp_path)


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


# ── SH's own ledger writes land before the gates (v1.5) ───────────────────────
# The runner assigns premise ids, so SH cannot cite a premise it is filing this
# turn. With the writes after the gates, such an ANSWER was rejected for citing an
# id that did not exist yet - a rejection SH has no way to act on, which is the
# failure class this version exists to delete.

SH_COVERAGE = PremiseDraft(text="SH traced a way the concept could show up",
                           kind="coverage", load_bearing=True)


def test_sh_can_file_a_premise_and_cite_it_in_the_same_answer_turn(tmp_path):
    """The ANSWER is still blocked - but for the RIGHT reason."""
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(new_premises=[SH_COVERAGE], answer_premise_ids=[])),
                _turn(_answer())])
    _run(llm, _Pool(), tmp_path)
    rejection = "\n".join(
        m.content for m in llm.seen[-1]
        if isinstance(getattr(m, "content", ""), str) and "TURN REJECTED" in m.content)
    # Not "p3 is not a premise on this question" - the id was linked by the runner.
    assert "not a premise on this question" not in rejection
    assert "UNVERIFIED" in rejection


def test_a_premise_sh_filed_survives_the_turn_that_was_rejected(tmp_path):
    """Writing from a rejected turn is safe and deliberate: add() dedupes, so the
    re-issued turn refiles nothing, and SH does not lose the tracing it did."""
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(new_premises=[SH_COVERAGE], answer_premise_ids=[])),
                _turn(_answer())])
    out = _run(llm, _Pool(), tmp_path)
    sh_filed = [p for p in out["ledger"].premises.values() if p.author == "sh"]
    assert [p.text for p in sh_filed] == [SH_COVERAGE.text]


# ── v1.4.3: the validation agent fires on a premise as it is settled ─────────

class _Validating(_Recording):
    """Its validators refute whatever they are given, quoting their own tool output.

    Q216 r2 in miniature: s1 files p1, s1 verifies p1 from its own search, and
    nothing else in the system reads the premise against its quote.
    """

    def run_round(self, **kw):
        r = super().run_round(**kw)
        if kw.get("technique") == "validator":
            r["premise_updates"] = [PremiseUpdate(
                id="p", status="REFUTED", quote='{"dest_port": "3333", "count": "3"}',
                evidence="the claim names a route it says was not searched")]
        return r


def test_a_settled_load_bearing_premise_is_validated_without_sh_being_asked(tmp_path):
    pool = _Validating()
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_answer())])
    out = _run(llm, pool, tmp_path)

    # p1 is the premise the fake senior VERIFIES on round 1 (UPDATES, above).
    assert pool.validator_messages, "no validator ran"
    assert out["ledger"].premises["p1"].status == "REFUTED"
    assert out["ledger"].premises["p1"].verified_by.startswith("v")


def test_the_validator_is_shown_the_claim_and_not_the_question(tmp_path):
    pool = _Validating()
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_answer())])
    _run(llm, pool, tmp_path, question="How long was the flow?")

    brief = pool.validator_messages[0]
    assert "mining could surface as stratum or DNS" in brief
    assert "How long was the flow" not in brief
    assert "1367.875" not in brief, "the candidate must not leak into the briefing"


def test_a_refuted_premise_blocks_the_answer_that_rests_on_it(tmp_path):
    """Spec 1's no-escape gate, now reachable: the author said VERIFIED, an
    independent reader said REFUTED, and the ANSWER citing it cannot go through."""
    pool = _Validating()
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_answer()),
                _turn(_answer()), _turn(_answer())])
    out = _run(llm, pool, tmp_path)

    assert out["answer"] == NO_ANSWER
    assert "REFUTED" in _conversation(tmp_path)


def test_a_premise_is_validated_once_not_every_wave(tmp_path):
    pool = _Validating()
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_continue()),
                _turn(_answer())])
    _run(llm, pool, tmp_path)
    # p1 and p2 are both VERIFIED in round 1 (v1.4.3: UPDATES settles both), so each
    # is validated once - the invariant this test names is "once", not "once total".
    assert len(pool.validator_messages) == 2


def test_a_premise_sh_files_on_the_answer_turn_is_never_silently_verified(tmp_path):
    """Q216 v1.4.3 r1's second move depended on SH being able to settle a premise on
    its own ANSWER turn, where no wave follows and so no validator could ever see it.
    That move is closed at the root now, not patched at the validator: `apply` refuses
    author="sh" outright, so a premise SH files here - however good its own quote looks
    - starts and stays UNVERIFIED, and is never handed to a validator as if it had
    already been settled."""
    pool = _Validating()
    late = _answer(new_premises=[PremiseDraft(
        text="coverage: the duration is the whole of it", kind="coverage",
        load_bearing=True, quote="The duration is 1367.875.",
        evidence="s1's report states it")])
    llm = _LLM([_turn(_spawn()), _turn(late), _turn(_answer()), _turn(_answer()), _turn(_answer())])
    out = _run(llm, pool, tmp_path, points=100)

    filed = [p for p in out["ledger"].premises.values()
             if p.text == "coverage: the duration is the whole of it"]
    assert filed and filed[0].status == "UNVERIFIED"
    briefed = "\n".join(pool.validator_messages)
    assert "coverage: the duration is the whole of it" not in briefed


def test_a_validators_verdict_is_not_reported_as_a_refused_update(tmp_path):
    """Q216 v1.4.3 r2 logged: "the runner refused a premise update: --- v6 | INDEPENDENT
    VALIDATION of p6 | VERIFIED -> VERIFIED". The ANSWER-turn verdicts were folded into
    `ledger_notes`, which the gate block turns into rejections, so every successful
    validation rejected the turn it belonged to."""
    pool = _Confirming()
    late = _answer(new_premises=[PremiseDraft(
        text="coverage: the duration is the whole of it", kind="coverage",
        load_bearing=True, quote="The duration is 1367.875.",
        evidence="s1's report states it")])
    llm = _LLM([_turn(_spawn()), _turn(late), _turn(_answer())])
    out = _run(llm, pool, tmp_path)

    convo = _conversation(tmp_path)
    assert "refused a premise update: ---" not in convo
    assert out["answer"] == "1367.875", "a confirming validator must not block the answer"


class _Confirming(_Recording):
    """Its validators uphold whatever they are given, quoting their own tool output."""

    def run_round(self, **kw):
        r = super().run_round(**kw)
        if kw.get("technique") == "validator":
            r["premise_updates"] = [PremiseUpdate(
                id="p", status="VERIFIED", quote='{"dest_port": "3333", "count": "3"}',
                evidence="my own scan agrees")]
        return r
