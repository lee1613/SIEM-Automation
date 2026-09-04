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


def test_samples_are_reduced_by_majority_vote():
    app = build_executor_graph(
        lambda p: {"idx": p["task"]["idx"], "status": "solved", "answer": "x"},
        reduce_samples=lambda rs: {**rs[0], "answer": "majority"})
    out = app.invoke({"tasks": _tasks((1, [])), "task_results": {}})
    assert out["task_results"][1]["answer"] == "x"   # single sample -> untouched
