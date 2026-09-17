import inspect
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
