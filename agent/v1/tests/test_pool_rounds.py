import inspect
import threading
from types import SimpleNamespace

from splunk_subagent import SplunkWorkerPool


class _Recorder:
    """Stands in for the compiled worker graph; records what it was invoked with."""

    def __init__(self):
        self.calls = []
        # A real graph invocation always appends at least the assistant's final
        # message; run_agent_traced indexes messages[-1] unconditionally, so an
        # empty list here would fault on code this task does not touch.
        self.state = {"messages": [SimpleNamespace(content="ack", tool_calls=None)],
                      "step_count": 3, "output_tokens": 10,
                      "last_prompt_tokens": 1234}

    def invoke(self, payload, config=None):
        self.calls.append((payload, config))
        return self.state


def _pool_without_graphs() -> SplunkWorkerPool:
    """A pool whose __init__ never ran — building real graphs needs an API key."""
    pool = SplunkWorkerPool.__new__(SplunkWorkerPool)
    pool.splunk = None
    pool.tracker = None
    pool.senior_model = "gpt-5.4-mini"
    pool.senior_base_url = None
    pool._senior_api_key = "test"
    pool._http = None
    pool._graphs = {}
    pool._graphs_lock = threading.Lock()
    pool._clarify_llm = None
    pool.exploration_graph = None
    pool.exploration_budget = {"content_scans": 0}
    return pool


def test_graphs_are_keyed_by_role_and_cap_so_a_round_graph_can_exist():
    src = inspect.getsource(SplunkWorkerPool._graph_for)
    assert "(role, cap)" in src


def test_run_round_reuses_the_thread_id_it_is_given():
    pool = _pool_without_graphs()
    rec = _Recorder()
    pool._graphs[("hunter", 8)] = rec
    for message in ("first directive", "second directive"):
        pool.run_round(thread_id="senior_Q216_s1", message=message, qid="Q216",
                       idx=1, technique="hunter", max_iter=8)
    threads = {c[1]["configurable"]["thread_id"] for c in rec.calls}
    assert threads == {"senior_Q216_s1"}, "a round must resume the senior's own thread"


def test_run_round_caps_the_round_at_its_iteration_budget():
    pool = _pool_without_graphs()
    rec = _Recorder()
    pool._graphs[("hunter", 8)] = rec
    pool.run_round(thread_id="t", message="d", qid="Q216", idx=1,
                   technique="hunter", max_iter=8)
    assert rec.calls[0][1]["recursion_limit"] == 8 * 4
    assert rec.calls[0][0]["step_count"] == 0, "each round starts a fresh iteration budget"


def test_run_round_returns_the_thread_context_size():
    pool = _pool_without_graphs()
    pool._graphs[("hunter", 8)] = _Recorder()
    out = pool.run_round(thread_id="t", message="d", qid="Q216", idx=1,
                         technique="hunter", max_iter=8)
    assert out["last_prompt_tokens"] == 1234


def test_a_crashed_round_is_api_failed_not_a_reasoning_outcome():
    class _Boom:
        def invoke(self, payload, config=None):
            raise RuntimeError("502 upstream")

    pool = _pool_without_graphs()
    pool._graphs[("hunter", 8)] = _Boom()
    out = pool.run_round(thread_id="t", message="d", qid="Q216", idx=1,
                         technique="hunter", max_iter=8)
    assert out["status"] == "api_failed"


def test_clarify_never_touches_a_tool():
    src = inspect.getsource(SplunkWorkerPool.clarify)
    assert "bind_tools" not in src and "run_agent_traced" not in src, \
        "a clarify reply must be answerable from memory alone — no tools, no round"


# ── review fixes ──────────────────────────────────────────────────────────────


class _StatefulRecorder:
    """A graph double that, unlike _Recorder, actually threads state across
    calls the way a real MemorySaver-backed graph does: get_state sees what a
    prior invoke (or update_state) appended, and invoke appends to the same
    running transcript instead of returning one fixed snapshot."""

    def __init__(self, prior_messages=None):
        self.messages = list(prior_messages or [])
        self.calls = []
        self.state_updates = []
        # what the *next* invoke() appends, and the step/token counts it reports
        self.next_new_messages = []
        self.next_step_count = 1
        self.next_output_tokens = 0
        self.next_last_prompt_tokens = 0

    def get_state(self, config):
        return SimpleNamespace(values={"messages": list(self.messages)})

    def update_state(self, config, values, as_node=None):
        self.state_updates.append({"config": config, "values": values, "as_node": as_node})
        self.messages.extend(values.get("messages", []))

    def invoke(self, payload, config=None):
        self.calls.append((payload, config))
        self.messages.extend(self.next_new_messages)
        return {"messages": list(self.messages), "step_count": self.next_step_count,
                "output_tokens": self.next_output_tokens,
                "last_prompt_tokens": self.next_last_prompt_tokens}


def test_a_round_ending_on_a_dangling_tool_call_is_closed_before_return():
    """Cap/runaway routes should_continue -> END on an AIMessage that still has
    tool_calls (should_continue only checks step/token count, not whether the
    call was ever executed). Left open, the next round's invoke sends that
    dangling tool_calls message straight back to the provider with no matching
    ToolMessage, which OpenAI rejects outright."""
    dangling = SimpleNamespace(
        content="", tool_calls=[{"id": "call_abc", "name": "submit_finding",
                                 "args": {"status": "partial"}}])
    rec = _StatefulRecorder()
    rec.next_new_messages = [dangling]
    pool = _pool_without_graphs()
    pool._graphs[("hunter", 8)] = rec

    pool.run_round(thread_id="t", message="d", qid="Q216", idx=1,
                   technique="hunter", max_iter=8)

    assert rec.state_updates, "a thread left on a dangling tool call must be closed"
    update = rec.state_updates[-1]
    assert update["as_node"] == "agent"
    closes = update["values"]["messages"]
    assert len(closes) == 1
    assert closes[0].tool_call_id == "call_abc"
    assert closes[0].name == "submit_finding"


def test_a_round_with_no_dangling_tool_call_does_not_touch_state():
    finished = SimpleNamespace(content="done", tool_calls=None)
    rec = _StatefulRecorder()
    rec.next_new_messages = [finished]
    pool = _pool_without_graphs()
    pool._graphs[("hunter", 8)] = rec

    pool.run_round(thread_id="t", message="d", qid="Q216", idx=1,
                   technique="hunter", max_iter=8)

    assert rec.state_updates == []


def test_a_round_that_ends_without_submit_finding_ignores_the_prior_rounds_value():
    """Round 1 finished with submit_finding(value='ROUND1') and a
    run_splunk_search call. Round 2's invoke appends only prose - no
    submit_finding. Reported value/insight/spl_used must come from round 2
    alone, not from the thread's accumulated history."""
    round1_search = SimpleNamespace(
        content="", tool_calls=[{"id": "s1", "name": "run_splunk_search",
                                 "args": {"query": "index=botsv3 sourcetype=round1_st | stats count"}}])
    round1_finding = SimpleNamespace(
        content="", tool_calls=[{"id": "f1", "name": "submit_finding",
                                 "args": {"status": "solved", "value": "ROUND1",
                                          "insight": "FOUND"}}])
    rec = _StatefulRecorder(prior_messages=[round1_search, round1_finding])
    rec.next_new_messages = [SimpleNamespace(content="still looking", tool_calls=None)]
    pool = _pool_without_graphs()
    pool._graphs[("hunter", 8)] = rec

    out = pool.run_round(thread_id="t", message="round 2 directive", qid="Q216",
                         idx=1, technique="hunter", max_iter=8)

    assert out["value"] == "", "round 2 must not inherit round 1's value"
    assert out["insight"] == "NOT_FOUND"
    assert out["spl_used"] == [], "round 2 must not inherit round 1's SPL queries"
    assert out["full_state"] == [
        {"type": "SimpleNamespace", "content": "still looking"}
    ], "full_state must hold only this round's messages"


def test_graph_for_builds_under_a_lock_so_concurrent_callers_cannot_double_build():
    src = inspect.getsource(SplunkWorkerPool._graph_for)
    assert "_graphs_lock" in src, \
        "two threads racing the same (role, cap) key must not each build a graph"


def test_clarify_llm_uses_the_full_worker_token_budget_and_transport_settings():
    """splunk_agent.py documents that a reasoning model (GLM-5.3, the default
    senior) can spend a tight completion-token budget entirely on hidden
    reasoning and return "" — workers get 16384 for exactly this reason. The
    clarify LLM must match, plus have the same timeout/retry budget as every
    other LLM call in the pipeline instead of relying on SDK defaults (600s).

    The budget is now sent through token_limit_kwargs — the plain field never
    reached Featherless, which capped it at 4096 (see test_token_limit.py)."""
    import splunk_agent as agent_mod
    pool = SplunkWorkerPool(None, senior_api_key="sk-fake", senior_model="m",
                            senior_base_url="https://api.featherless.ai/v1")
    llm = pool._clarify_llm
    assert llm.request_timeout == agent_mod.LLM_TIMEOUT_S
    assert llm.max_retries == agent_mod.LLM_MAX_RETRIES
    assert llm.extra_body == {"max_tokens": 32768}


def test_high_value_threshold_constant_is_gone():
    import splunk_subagent
    assert not hasattr(splunk_subagent, "HIGH_VALUE_THRESHOLD"), \
        "iter_budget is the single source of truth for the iteration count"


def test_the_clarify_model_sends_the_token_cap_the_provider_reads():
    # Same 4096 trap as the worker graph: langchain renames max_tokens, Featherless
    # ignores the renamed field, and a truncated clarify reply reaches SH as "".
    from splunk_subagent import SplunkWorkerPool
    pool = SplunkWorkerPool(None, senior_api_key="sk-fake",
                            senior_model="zai-org/GLM-5.3",
                            senior_base_url="https://api.featherless.ai/v1")
    assert pool._clarify_llm.extra_body == {"max_tokens": 32768}
    assert pool._clarify_llm.max_tokens is None


def test_truncated_calls_reads_cut_short_tool_results():
    from langchain_core.messages import AIMessage, ToolMessage
    from splunk_subagent import truncated_calls
    msgs = [AIMessage(content="", tool_calls=[
                {"id": "a", "name": "run_splunk_search", "args": {"query": "q1"}},
                {"id": "b", "name": "run_splunk_search", "args": {"query": "q2"}}]),
            ToolMessage(content='{"meta": {"truncated": "showing 50 of 1573 rows"}}', tool_call_id="a"),
            ToolMessage(content='{"meta": {}}', tool_call_id="b")]
    assert truncated_calls({"messages": msgs}) == ["`run_splunk_search: q1` (50 of 1573 rows seen)"]
