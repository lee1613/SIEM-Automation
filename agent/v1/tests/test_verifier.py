from orchestrator import parse_verifier_verdict


def test_pool_builds_dedicated_verifier_graph():
    from splunk_subagent import SplunkWorkerPool, VERIFIER_MAX_ITER

    calls = []

    def fake_create_agent(*a, **kw):
        calls.append(kw.get("max_iter"))
        return (f"graph_maxiter_{kw.get('max_iter')}", None)

    import splunk_subagent
    orig = splunk_subagent.agent_mod.create_agent
    splunk_subagent.agent_mod.create_agent = fake_create_agent
    try:
        pool = SplunkWorkerPool(splunk=None, senior_api_key="x")
    finally:
        splunk_subagent.agent_mod.create_agent = orig

    assert VERIFIER_MAX_ITER in calls
    assert pool.verifier_graph == f"graph_maxiter_{VERIFIER_MAX_ITER}"


def test_confirm_verdict():
    v = parse_verifier_verdict("Checked event order by _time. CONFIRMED: 30358")
    assert v["verdict"] == "confirmed"


def test_refute_verdict_with_correction():
    v = parse_verifier_verdict("The earliest by _time is 30358, not 30356. "
                               "REFUTED. CORRECTION: 30358")
    assert v["verdict"] == "refuted"
    assert v["correction"] == "30358"


def test_unknown_defaults_to_confirmed():
    # if the verifier is inconclusive, don't block the pipeline
    v = parse_verifier_verdict("could not run additional queries")
    assert v["verdict"] == "confirmed"
