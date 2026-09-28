import inspect

import splunk_agent


def test_agent_state_declares_last_prompt_tokens():
    assert "last_prompt_tokens" in splunk_agent.AgentState.__annotations__


def test_agent_node_records_the_prompt_size_of_the_call_it_just_made():
    src = inspect.getsource(splunk_agent.create_agent)
    agent_node = src.split("def agent_node", 1)[1].split("def verify_node", 1)[0]
    assert 'um.get("input_tokens"' in agent_node, \
        "agent_node no longer reads input_tokens off usage_metadata"
    assert '"last_prompt_tokens"' in agent_node, \
        "agent_node does not return last_prompt_tokens"


def test_both_run_entrypoints_seed_the_key():
    for fn in (splunk_agent.run_agent, splunk_agent.run_agent_traced):
        assert '"last_prompt_tokens"' in inspect.getsource(fn), \
            f"{fn.__name__} does not seed last_prompt_tokens"
