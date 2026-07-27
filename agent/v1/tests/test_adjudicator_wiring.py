import orchestrator
from orchestrator import DelegationContext, build_sh_agent_compiler


class _FakeLogger:
    def next_worker(self, role, qid):
        return 1

    def timeline(self, text):
        pass


class _FakeLLM:
    """Simulates the adjudicator LLM proposing a synthesized value that isn't
    in the ledger or the question text — the Q321 hard-rule case."""

    def invoke(self, msgs):
        class _Resp:
            content = "CHOICE: 99999\nCONFIDENCE: LOW\nREASON: guessing"
        return _Resp()


def _delegation(worker, status, value):
    return {"worker": worker, "qid": "Q999", "subquestion": "sub",
            "status": status, "answer": f"FINAL ANSWER: {value}",
            "spl_used": [], "sourcetypes": [], "full_state": [],
            "iterations": 1, "cap_hit": False}


def test_adjudicator_node_never_submits_synthesized_choice(monkeypatch):
    """adjudicator_node must enforce the same Q321 hard rule end-to-end: when
    the LLM proposes a value resolve_choice rejects (not in the ledger, not
    in the question text), the node must fall back to a real ledger value —
    never the raw/synthesized LLM output."""
    monkeypatch.setattr(orchestrator, "ChatOpenAI", lambda *a, **kw: _FakeLLM())

    ctx = DelegationContext(pool=None, logger=_FakeLogger())
    ctx.current_qid      = "Q999"
    ctx.current_points   = 100          # below ESCALATE_MIN_POINTS -> no escalation call
    ctx.current_question = "What is the answer?"
    ctx.current_guidance = ""
    ctx.q_delegations = [
        _delegation("senior#1", "solved",  "alpha-value"),
        _delegation("senior#2", "partial", "beta-value"),
    ]

    graph, _ = build_sh_agent_compiler("sk-fake-key", "gpt-5.4", ctx)
    adjudicator_node = graph.get_graph().nodes["adjudicator"].data.func

    # joiner's pick is itself not a genuine value (not in ledger/question text)
    state = {"final_answer": "unrelated-guess"}
    out = adjudicator_node(state)

    assert out["adjudicated"] is True
    chosen = out.get("final_answer")
    assert chosen is not None
    assert chosen != "99999"            # never the raw synthesized LLM choice
    assert chosen != "unrelated-guess"  # never the ungrounded joiner pick either
    assert chosen == "alpha-value"      # fallback_choice: solved beats partial


def test_reset_question_records_guidance():
    ctx = DelegationContext(pool=None, logger=None)
    ctx.reset_question("Q331", points=1000, question="fence?",
                       guidance="number only")
    assert ctx.current_guidance == "number only"
    ctx.reset_question("Q1", points=100, question="next?")
    assert ctx.current_guidance == ""      # resets between questions


def test_graph_contains_adjudicator_node():
    ctx = DelegationContext(pool=None, logger=None)
    graph, _ = build_sh_agent_compiler("sk-fake-key", "gpt-5.4", ctx)
    nodes = graph.get_graph().nodes
    assert "adjudicator" in nodes and "verifier" in nodes
