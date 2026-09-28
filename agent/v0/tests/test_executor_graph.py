from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from executor_graph import ABORT, RETRY, SKIP, build_executor_graph, ready_tasks

CFG = {"configurable": {"thread_id": "t"}}


def _tasks(*specs):
    return [{"idx": i, "subquestion": f"q{i}", "deps": list(d)} for i, d in specs]


def _stub(calls, fail_on=()):
    def run(payload):
        task = payload["task"]
        calls.append(task["idx"])
        if task["idx"] in fail_on:
            return {"idx": task["idx"], "status": "api_failed",
                    "provider": "api.featherless.ai",
                    "answer": "ESCALATE: worker crashed - InternalServerError"}
        return {"idx": task["idx"], "status": "solved", "answer": f"a{task['idx']}"}
    return run


def test_independent_tasks_fan_out_in_one_wave():
    calls = []
    app = build_executor_graph(_stub(calls))
    out = app.invoke({"tasks": _tasks((1, []), (2, []), (3, [])), "task_results": {}})
    assert sorted(calls) == [1, 2, 3]
    assert sorted(out["task_results"]) == [1, 2, 3]


def test_dependencies_are_respected_across_waves():
    calls = []
    app = build_executor_graph(_stub(calls))
    out = app.invoke({"tasks": _tasks((1, []), (2, [1])), "task_results": {}})
    assert calls == [1, 2]                      # 2 waited for its dependency
    assert sorted(out["task_results"]) == [1, 2]


def test_unresolvable_dependency_runs_one_task_instead_of_deadlocking():
    assert ready_tasks(_tasks((1, [99])), {})[0]["idx"] == 1


def test_api_failure_pauses_but_siblings_still_finish():
    calls = []
    app = build_executor_graph(_stub(calls, fail_on={2}), checkpointer=MemorySaver())
    out = app.invoke({"tasks": _tasks((1, []), (2, []), (3, [])), "task_results": {}},
                     config=CFG)
    assert sorted(calls) == [1, 2, 3]           # nothing cancelled or orphaned
    assert out.get("__interrupt__")             # paused for a human
    # Siblings' work is real graph state, not a side-record.
    assert out["task_results"][1]["status"] == "solved"
    assert out["task_results"][3]["status"] == "solved"


def test_resume_replays_only_the_hitl_node_not_the_paid_workers():
    # THE property this design exists for. interrupt() restarts its own node, so
    # if it lived inside the worker every resume would re-issue that worker's
    # LLM call. It lives in a side-effect-free node instead.
    calls = []
    app = build_executor_graph(_stub(calls, fail_on={2}), checkpointer=MemorySaver())
    app.invoke({"tasks": _tasks((1, []), (2, []), (3, [])), "task_results": {}}, config=CFG)
    calls.clear()
    out = app.invoke(Command(resume=SKIP), config=CFG)
    assert calls == []                          # no worker re-ran, nothing re-paid
    assert out["decision"] == SKIP


def test_retry_redispatches_only_the_failed_task():
    calls = []
    runs = {"n": 0}
    def run(payload):
        task = payload["task"]
        calls.append(task["idx"])
        runs["n"] += 1
        # fail task 2 the first time only, so RETRY can succeed
        if task["idx"] == 2 and runs["n"] <= 3:
            return {"idx": 2, "status": "api_failed", "provider": "p", "answer": "boom"}
        return {"idx": task["idx"], "status": "solved", "answer": f"a{task['idx']}"}
    app = build_executor_graph(run, checkpointer=MemorySaver())
    app.invoke({"tasks": _tasks((1, []), (2, []), (3, [])), "task_results": {}}, config=CFG)
    calls.clear()
    out = app.invoke(Command(resume=RETRY), config=CFG)
    assert calls == [2]                         # only the failed one, not all three
    assert out["task_results"][2]["status"] == "solved"


def test_abort_stops_the_run():
    app = build_executor_graph(_stub([], fail_on={2}), checkpointer=MemorySaver())
    app.invoke({"tasks": _tasks((1, []), (2, [])), "task_results": {}}, config=CFG)
    out = app.invoke(Command(resume=ABORT), config=CFG)
    assert out["aborted"] is True


def test_one_result_per_task_lands_in_task_results():
    # v0.3 removed 3x self-consistency sampling (it reached a majority 0 times in
    # 14 attempts, always falling through to results[0]), so a task dispatches
    # exactly one worker and collect() stores that worker's result directly.
    app = build_executor_graph(
        lambda p: {"idx": p["task"]["idx"], "status": "solved", "answer": "x"})
    out = app.invoke({"tasks": _tasks((1, []), (2, [])), "task_results": {}})
    assert out["task_results"][1]["answer"] == "x"
    assert out["task_results"][2]["answer"] == "x"


def test_a_live_object_in_a_send_payload_breaks_checkpointing():
    """Pins the Q216 crash. A Send payload IS checkpointed state, so any live
    object in it (the LangSmith RunTree, which carries a client and locks) kills
    the whole question with "Type is not msgpack serializable: Send" - the error
    names the Send envelope, not the object inside. Hence ctx.parent_run_tree:
    tracing handles stay in process memory and never enter a payload."""
    import os, sqlite3, tempfile, threading
    from typing import TypedDict
    import pytest
    from langgraph.graph import END, START, StateGraph
    from langgraph.checkpoint.sqlite import SqliteSaver

    class _S(TypedDict, total=False):
        tasks: list
        task_results: dict

    def _build(live: bool):
        def prep(task, completed):
            p = {"task": task, "subq": "s", "worker_idx": 1, "sample": False}
            if live:
                p["parent_run_tree"] = threading.Lock()   # stands in for a RunTree
            return [p]
        sub = build_executor_graph(
            lambda p: {"idx": p["task"]["idx"], "status": "solved", "answer": "a"},
            prepare_sends=prep)
        g = StateGraph(_S)
        g.add_node("executor", sub)
        g.add_edge(START, "executor"); g.add_edge("executor", END)
        db = os.path.join(tempfile.mkdtemp(), f"ckpt_{live}.sqlite")
        return g.compile(checkpointer=SqliteSaver(
            sqlite3.connect(db, check_same_thread=False)))

    tasks = [{"idx": 1, "subquestion": "t1", "deps": []}]
    cfg   = {"configurable": {"thread_id": "t"}}

    with pytest.raises(TypeError, match="not msgpack serializable"):
        _build(live=True).invoke({"tasks": tasks}, cfg)

    # The shape _prepare_sends now emits - plain data only - checkpoints fine.
    out = _build(live=False).invoke({"tasks": tasks}, cfg)
    assert out["task_results"][1]["status"] == "solved"


def test_runaway_worker_reaches_the_hitl_interrupt():
    """A worker past OUTPUT_TOKEN_CAP is stuck, not thorough. It must reach the
    same human decision point as a provider outage rather than being folded into
    an ordinary reasoning failure that SH just replans around."""
    from langgraph.checkpoint.memory import MemorySaver
    from executor_graph import INTERRUPT_STATUSES

    assert "runaway" in INTERRUPT_STATUSES

    app = build_executor_graph(
        lambda p: {"idx": p["task"]["idx"], "status": "runaway",
                   "answer": "", "provider": "featherless"},
        checkpointer=MemorySaver())
    out = app.invoke({"tasks": [{"idx": 1, "subquestion": "t", "deps": []}]},
                     {"configurable": {"thread_id": "runaway"}})
    assert out.get("__interrupt__"), "a runaway worker must pause for a human"
    assert out["__interrupt__"][0].value["reason"] == "runaway"
