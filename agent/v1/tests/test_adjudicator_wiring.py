from orchestrator import build_sh_agent_compiler, DelegationContext


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
