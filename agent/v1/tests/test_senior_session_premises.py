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

    def run_round(self, *, thread_id, message, qid, idx, technique, max_iter,
                  sid=""):
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
