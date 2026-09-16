from splunk_agent import iter_budget


def test_high_value_gets_more_iterations():
    assert iter_budget(1000) >= 25
    assert iter_budget(500) >= 25


def test_low_value_gets_base():
    assert iter_budget(100) == 15
    assert iter_budget(0) == 15


# ── the iteration cap must not force a worker back into prose ─────────────────

def test_a_capped_worker_keeps_its_terminal_tool():
    """At the cap, search tools are withdrawn so the worker cannot start another
    hunt - but `submit_finding` has to survive, or a capped worker's only way to
    report is prose, which is the thing the structured contract exists to avoid.

    v0 supplies no extra_tools and must be unaffected: for it the capped model
    stays genuinely bare.
    """
    import inspect

    import splunk_agent
    from finding import submit_finding

    src = inspect.getsource(splunk_agent.create_agent)
    assert 'getattr(t, "name", "") == "submit_finding"' in src, \
        "the capped model no longer filters for a terminal tool"
    assert submit_finding.name == "submit_finding", \
        "the tool was renamed; the filter in create_agent now matches nothing"


def test_the_cap_message_does_not_teach_the_deleted_prose_protocol():
    import inspect

    import splunk_agent
    src = inspect.getsource(splunk_agent.create_agent)
    cap_msg = src.split("maximum number of tool calls", 1)[1][:600]
    for dead in ("PARTIAL ANSWER:", "ESCALATE", "UNCERTAINTY:"):
        assert dead not in cap_msg, f"cap message still teaches {dead!r}"
    assert "Do NOT invent a value" in cap_msg   # the part worth keeping
