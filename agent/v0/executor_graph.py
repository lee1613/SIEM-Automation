#!/usr/bin/env python3
"""
Executor as a real LangGraph fan-out, one node per Senior worker.

Replaces the old design where all workers ran on a ThreadPoolExecutor *inside* a
single `executor` node. LangGraph could not see them, so a worker's result was
not graph state and an API failure had nowhere framework-native to pause.

Topology:

    dispatch ──Send(task)──▶ worker (xN, parallel) ──▶ collect ──┬─▶ dispatch  (more waves)
                                                                 ├─▶ hitl      (api failure)
                                                                 └─▶ END       (all done)
    hitl ──(resume)──┬─▶ dispatch   (operator chose to retry the failed tasks)
                     └─▶ END        (skip / abort)

Two properties this buys, both verified against the installed langgraph:

1. **Siblings finish before anything pauses.** LangGraph runs every task in a
   superstep to completion, then surfaces the interrupt. No worker is cancelled
   or orphaned mid-flight, so nothing already paid for is thrown away.
2. **Resume replays only the cheap node.** `interrupt()` restarts its own node
   from the top, so it must NOT live inside the worker - that would re-issue the
   worker's LLM call on every resume. Workers therefore *return* their result
   (checkpointed as real state) and a separate, side-effect-free `hitl` node
   does the interrupting. Resuming replays that node alone.
"""

import operator
from typing import Annotated, Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

# Worker outcomes a human must decide on, rather than ordinary reasoning
# failures SH can replan around. "api_failed" is a provider outage; "runaway" is
# a worker past OUTPUT_TOKEN_CAP, which is stuck rather than thorough.
INTERRUPT_STATUSES = frozenset({"api_failed", "runaway"})

RETRY = "retry"
SKIP  = "skip"
ABORT = "abort"


def _accumulate(old, new):
    """Append, with None as an explicit reset (used to clear between waves)."""
    if new is None:
        return []
    return list(old or []) + list(new)


class ExecState(TypedDict, total=False):
    tasks:        list[dict]   # [{"idx": int, "subquestion": str, "deps": [int]}]
    task_results: dict         # idx -> result, accumulated across waves
    wave_results: Annotated[list, _accumulate]
    wave:         list[int]    # task idxs dispatched in the current wave
    decision:     str          # last human decision
    aborted:      bool


def ready_tasks(tasks: list[dict], completed: dict) -> list[dict]:
    """Tasks whose $N dependencies are all satisfied.

    Falls back to the first pending task if nothing is ready, so a malformed
    dependency graph stalls one task rather than deadlocking the question.
    """
    remaining = [t for t in tasks if t["idx"] not in completed]
    if not remaining:
        return []
    ready = [t for t in remaining if all(d in completed for d in t.get("deps") or [])]
    return ready or [remaining[0]]


def build_executor_graph(run_task: Callable[[dict], dict],
                         *, prepare_sends: Callable[[dict, dict], list] | None = None,
                         on_wave: Callable[[list], None] | None = None,
                         max_parallel: int | None = None,
                         checkpointer=None):
    """Compile the fan-out executor.

    run_task(payload)       -> result dict carrying at least "idx" and "status".
    prepare_sends(task, completed) -> one payload per worker to dispatch for that
                               task. This is where dependency substitution, prior
                               handoff context and worker numbering belong, and
                               where a sampled task fans out to several workers.
                               Defaults to a single {"task": task} payload.
    reduce_samples(results) -> winner when a task was sampled more than once
                               (majority vote); defaults to the first result.
    on_wave(results)        -> called once per wave with that wave's results,
                               for accounting that must happen at most once per
                               task per round (failure counters, handoff digests).
    max_parallel            -> cap on workers dispatched in one wave. The old
                               ThreadPoolExecutor bounded this at MAX_WORKERS,
                               and SplunkConnectionPool only holds 6 connections,
                               so an uncapped fan-out could starve it. Tasks that
                               do not fit simply run in the next wave.

    Pass checkpointer=None when embedding this as a node in a parent graph - the
    parent's checkpointer then owns the subgraph's state, which is what makes an
    interrupt inside here resumable from the parent.
    """
    prep    = prepare_sends  or (lambda task, completed: [{"task": task}])
    account = on_wave        or (lambda results: None)

    def dispatch(state: ExecState) -> dict:
        completed = dict(state.get("task_results") or {})
        wave = [t["idx"] for t in ready_tasks(state.get("tasks") or [], completed)]
        # Reset the per-wave accumulator so the previous wave's results are not
        # re-reduced into this one.
        return {"wave": wave, "wave_results": None}

    def fan_out(state: ExecState):
        completed = dict(state.get("task_results") or {})
        by_idx = {t["idx"]: t for t in state.get("tasks") or []}
        sends = []
        for i in state.get("wave") or []:
            payloads = prep(by_idx[i], completed)
            if max_parallel and sends and len(sends) + len(payloads) > max_parallel:
                break
            for payload in payloads:
                sends.append(Send("worker", {**payload, "completed": completed}))
        return sends

    def worker(payload: dict) -> dict:
        # One Senior worker = one node. Returns its result into graph state
        # BEFORE any interrupt can happen, so a pause never re-runs this call.
        return {"wave_results": [run_task(payload)]}

    def collect(state: ExecState) -> dict:
        completed = dict(state.get("task_results") or {})
        # Accounting first, once per wave - a failed task counts once per task
        # per round, not once per worker that reported it.
        account(list(state.get("wave_results") or []))
        for r in state.get("wave_results") or []:
            completed.setdefault(r.get("idx"), r)
        return {"task_results": completed}

    def hitl(state: ExecState) -> dict:
        """Side-effect-free by design - this is the node that replays on resume."""
        failed = [r for r in state.get("wave_results") or []
                  if r.get("status") in INTERRUPT_STATUSES]
        decision = interrupt({
            "reason":   (failed[0].get("status") if failed else "api_failed"),
            "qids":     [r.get("idx") for r in failed],
            "provider": (failed[0].get("provider") if failed else None),
            "error":    (failed[0].get("answer") if failed else None),
            "options":  [RETRY, SKIP, ABORT],
        })
        choice = decision if decision in (RETRY, SKIP, ABORT) else SKIP
        if choice == RETRY:
            # Drop the failed tasks' results so ready_tasks re-dispatches them.
            completed = {k: v for k, v in (state.get("task_results") or {}).items()
                         if k not in {r.get("idx") for r in failed}}
            return {"decision": choice, "task_results": completed}
        return {"decision": choice, "aborted": choice == ABORT}

    def route_after_collect(state: ExecState) -> str:
        if any(r.get("status") in INTERRUPT_STATUSES
               for r in state.get("wave_results") or []):
            return "hitl"
        return "dispatch" if ready_tasks(state.get("tasks") or [],
                                         state.get("task_results") or {}) else END

    def route_after_hitl(state: ExecState) -> str:
        if state.get("decision") == ABORT:
            return END
        return "dispatch" if ready_tasks(state.get("tasks") or [],
                                         state.get("task_results") or {}) else END

    g = StateGraph(ExecState)
    g.add_node("dispatch", dispatch)
    g.add_node("worker",   worker)
    g.add_node("collect",  collect)
    g.add_node("hitl",     hitl)
    g.add_edge(START, "dispatch")
    g.add_conditional_edges("dispatch", fan_out, ["worker"])
    g.add_edge("worker", "collect")
    g.add_conditional_edges("collect", route_after_collect,
                            {"hitl": "hitl", "dispatch": "dispatch", END: END})
    g.add_conditional_edges("hitl", route_after_hitl,
                            {"dispatch": "dispatch", END: END})
    return g.compile(checkpointer=checkpointer)
