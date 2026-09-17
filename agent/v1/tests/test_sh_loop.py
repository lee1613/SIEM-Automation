# agent/v1/tests/test_sh_loop.py
import os

from conversation import SeniorDirective, SHTurn
from sh_loop import run_question

# Every SeniorDirective field is required under strict json_schema, so tests fill
# the unused ones. Repeated here rather than imported from
# test_conversation_routes: agent/v1/tests is not a package, and the repo has a
# second top-level tests/ directory, so a cross-test import is ambiguous.
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
    return SeniorDirective(**{**BLANK, **kw})


REPORT = ("# s1 - Q216 - Round 1\n**Insight:** FOUND\n\n## Prior rounds\n- r1\n\n"
          "## This round\n### What I ran\n- search x -> 3 events\n"
          "### What it means\nThe duration is 1367.875.\n\n## Ruled out\n- none\n\n"
          "## Open questions for SH\n- none\n")


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
            "last_prompt_tokens": 500, "answer": "", "full_state": [],
        }
        self.result.update(over)
        self.rounds = 0
        self.clarifies = 0

    def run_round(self, **kw):
        self.rounds += 1
        return dict(self.result)

    def clarify(self, **kw):
        self.clarifies += 1
        return "Yes — the window you gave me."


def _spawn(**kw):
    base = dict(route="SPAWN", spawn_type="senior", technique="hunter",
                subquestion="Find the flow duration in cisco:nvm.",
                reason="Only feed with a duration field.")
    base.update(kw)
    return entry(**base)


def _answer(value="1367.875", **kw):
    base = dict(route="ANSWER", value=value, value_kind="duration_seconds",
                source_senior="s1", justification="s1 round 1 showed it.",
                r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="PASS")
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
    assert out["ceiling"] == 192            # 1000pt tier: 3 x 8 x 8


def test_an_ungrounded_answer_is_pushed_back_once_then_falls_back(tmp_path):
    llm = _LLM([_turn(_spawn()),
                _turn(_answer(value="999.999")),
                _turn(_answer(value="888.888"))])
    out = _run(llm, _Pool(), tmp_path)
    assert out["end_reason"] == "ungrounded"
    assert out["answer"] == "1367.875", "falls back to a real candidate from the reports"


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


def test_running_out_of_turns_ends_the_question_on_the_best_candidate(tmp_path):
    # 100pt tier: 5 SH turns. Script 5 spawn-less no-op turns by clarifying forever.
    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="unclear",
                    questions=["what?"], r1_scope_alignment="WEAK",
                    r2_progress="PASS", r3_answer_readiness="WEAK")
    llm = _LLM([_turn(_spawn())] + [_turn(clarify) for _ in range(6)])
    out = _run(llm, _Pool(), tmp_path, points=100)
    assert out["end_reason"] == "turns"
    assert out["answer"] == "1367.875"


def test_a_clarify_consumes_a_turn_but_no_wave(tmp_path):
    clarify = entry(senior_id="s1", route="CLARIFY", clarify_reason="suspect",
                    questions=["Was the window mine?"], r1_scope_alignment="PASS",
                    r2_progress="PASS", r3_answer_readiness="WEAK")
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(clarify), _turn(_answer())])
    out = _run(llm, pool, tmp_path)
    assert pool.rounds == 1, "a clarify must not run a round"
    assert out["waves"] == 1
    assert out["turns"] == 3
    with open(os.path.join(str(tmp_path), "Q216", "conversation.md"), encoding="utf-8") as f:
        assert "[CLARIFY REPLY]" in f.read()


def test_retirement_writes_a_handoff(tmp_path):
    retire = entry(senior_id="s1", route="RETIRE", reason="scope exhausted",
                   r1_scope_alignment="PASS", r2_progress="WEAK",
                   r3_answer_readiness="WEAK")
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
                 r3_answer_readiness="WEAK")
    llm = _LLM([_turn(_spawn()), _turn(cont), _turn(_answer())])
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
                    r2_progress="PASS", r3_answer_readiness="WEAK")
    llm = _LLM([_turn(_spawn()), _turn(clarify), _turn(_answer())])
    out = _run(llm, _BrokenClarify(), tmp_path)
    assert out["answer"] == "1367.875"
    assert any("clarify failed" in str(m.content) for m in llm.seen[-1])


# ── review fixes on 9795a4e ───────────────────────────────────────────────────

def _continue(**kw):
    base = dict(senior_id="s1", route="COMMAND", decision="continue",
                rationale="keep going", directive="Go one step further.",
                r1_scope_alignment="PASS", r2_progress="PASS", r3_answer_readiness="WEAK")
    base.update(kw)
    return entry(**base)


def _retire(sid="s1", **kw):
    base = dict(senior_id=sid, route="RETIRE", reason="done", r1_scope_alignment="PASS",
                r2_progress="PASS", r3_answer_readiness="WEAK")
    base.update(kw)
    return entry(**base)


def _conversation(tmp_path, qid="Q216"):
    with open(os.path.join(str(tmp_path), qid, "conversation.md"), encoding="utf-8") as f:
        return f.read()


def test_anti_thrash_sees_the_grades_of_the_report_being_read(tmp_path):
    # I1: rounds 2 and 3 repeat round 1's SPL -> both code-FAIL. The continue on turn 4
    # reads round 3, so the streak is already 2 and it must be refused.
    pool = _Pool()
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_continue()),
                _turn(_continue()), _turn(_answer())])
    out = _run(llm, pool, tmp_path)
    assert pool.rounds == 3, "a third consecutive continue must not run round 4"
    assert out["answer"] == "1367.875"
    assert "two consecutive R2 FAILs" in _conversation(tmp_path)


def test_sh_reads_and_can_answer_from_the_final_wave(tmp_path):
    # I2: 100pt has 3 rounds; the third wave must still be read by SH.
    llm = _LLM([_turn(_spawn()), _turn(_continue()), _turn(_continue()), _turn(_answer())])
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
    llm = _LLM([_turn(_spawn(), _spawn(subquestion="Other feed.")),
                _turn(_continue()),
                _turn(_answer(source_senior="s2"), _retire("s1"))])
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
    llm = _LLM([_turn(_spawn()), _turn(_retire()), _turn(clarify), _turn(_answer())])
    _run(llm, pool, tmp_path)
    assert pool.clarifies == 0
    assert "s1 is not an active senior" in _conversation(tmp_path)


def test_the_fallback_is_a_bare_value_or_nothing(tmp_path):
    # M3: no report ever held a value -> report text is never submitted
    pool = _Pool(value="", insight="NOT_FOUND")
    llm = _LLM([_turn(_spawn()), _turn(_retire())] + [_turn() for _ in range(3)])
    out = _run(llm, pool, tmp_path, points=100)
    assert out["end_reason"] == "turns"
    assert out["answer"] == ""


def test_the_fallback_skips_values_from_r1_fail_reports(tmp_path):
    # M4
    llm = _LLM([_turn(_spawn()), _turn(_retire(r1_scope_alignment="FAIL"))]
               + [_turn() for _ in range(3)])
    out = _run(llm, _Pool(), tmp_path, points=100)
    assert out["end_reason"] == "turns"
    assert out["answer"] == ""


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

    llm = _LLM([_turn(_spawn(), _spawn(subquestion="Other feed.")),
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
