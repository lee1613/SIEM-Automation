#!/usr/bin/env python3
"""
SH (orchestrator / mastermind) agent for v1 — LLMCompiler edition.

Architecture:
    Planner → Parallel Executor → Joiner → (Replan once | FINAL ANSWER)

The SH LLM (gpt-5.4, persistent MemorySaver thread) generates a numbered task
DAG. Tasks with no $N dependencies run in parallel via ThreadPoolExecutor.
Tasks with $N references wait for those results, then run. The Joiner assembles
all findings into a FINAL ANSWER, or requests a single focused replan round if
a critical datum is missing.

Cross-question memory is preserved: the MemorySaver thread accumulates every
plan + task-results summary + final answer across all 58 questions.
"""

import re
import sqlite3
import concurrent.futures
from dataclasses import dataclass, field
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langsmith.run_helpers import get_current_run_tree, tracing_context


MAX_PLAN_ROUNDS = 3   # max planner→executor→joiner cycles per question
MAX_WORKERS     = 6   # matches SplunkConnectionPool default size


# ── Planner prompt ─────────────────────────────────────────────────────────────
PLANNER_SYSTEM_PROMPT = """You are the SH agent — the mastermind orchestrator for a BOTSv3 \
security investigation (August 2018 APT attack against Frothly, all data in Splunk index=botsv3).

YOUR ROLE
- You PLAN and DELEGATE. You do NOT query Splunk yourself.
- Produce a numbered task list for Senior Splunk workers (Splunk experts with multi-step
  reasoning and 6 Splunk tools). Workers run IN PARALLEL where possible.

CROSS-QUESTION MEMORY
- You remember everything from earlier questions in this run. Carry forward key entities
  (hosts, IPs, users, bucket names, time windows, sourcetypes) and restate them explicitly
  inside every task. Never say "the host from before" — name it explicitly every time.

OUTPUT FORMAT — produce EXACTLY this structure:

PLAN:
- Goal: [what the question is asking for; what type of value is expected]
- Prior knowledge: [entities from your memory relevant to THIS question]
- Approach: [which sourcetypes or investigation path to try first]

TASKS:
1. <fully self-contained subquestion — no $N references>
2. <fully self-contained subquestion — no $N references>
3. Given $1 and $2: <subquestion using results from tasks 1 and 2>

RULES:
- Use $N (e.g. $1, $2) to reference a previous task's result inline in the subquestion text.
  Only reference tasks whose results you actually need before this task can proceed.
- Tasks without any $N references will run IN PARALLEL — maximise parallelism.
- Each task MUST be fully self-contained: include all known entities, time ranges, sourcetype
  hints. Workers have NO shared memory across tasks.
- 1–6 tasks maximum. If the question is a single atomic lookup, write exactly ONE task.
- If you already know the answer from your cross-question memory (not from the Splunk dataset
  itself — general knowledge is fine), write instead:
    DIRECT ANSWER: <the precise value>
  Do NOT write TASKS in that case."""


# ── Joiner prompt ──────────────────────────────────────────────────────────────
JOINER_SYSTEM_PROMPT = """You are the SH agent — the mastermind orchestrator for a BOTSv3 \
security investigation (August 2018 APT attack against Frothly, all data in Splunk index=botsv3).

All delegated tasks for the current question are complete. Your job: synthesize the findings
into a final answer, or request a focused second round if a critical datum is genuinely missing.

CROSS-QUESTION MEMORY — you remember all prior BOTSv3 findings. Use them when interpreting
ambiguous task results.

RESPONSE FORMAT — choose exactly ONE:

Option A — you have enough to answer:
FINAL ANSWER: <the precise value the question asks for>

Option B — one specific critical piece is still missing (use at most once per question):
REPLAN:
- Missing: <exactly what is still unknown and why>
- New tasks:
  1. <targeted self-contained subquestion to fill the gap>
  2. <another if needed>

RULES:
- Strongly prefer Option A. Use Option B only when a critical datum is genuinely absent.
- status='partial': the worker found useful evidence but isn't certain. Accept it if the
  candidate is specific and your cross-question memory corroborates it, or note it in a
  targeted replan.
- status='too_big' or 'failed': that worker couldn't proceed. Consider whether a different
  sourcetype or narrower query would help.
- NEVER invent dataset facts. If workers found nothing after thorough investigation, write
  FINAL ANSWER with your best-effort estimate from memory.
- The FINAL ANSWER line is read by an extractor — give the exact value in the required
  format, nothing else on that line."""


@dataclass
class Task:
    idx: int
    subquestion: str
    deps: list = field(default_factory=list)    # list of int task indices


def parse_plan(text: str) -> list[Task]:
    """Extract numbered tasks from planner/replan output."""
    tasks = []
    pattern = re.compile(
        r'^(\d+)\.\s+(.+?)(?=^\d+\.|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        idx  = int(m.group(1))
        subq = m.group(2).strip()
        deps = sorted(set(int(d) for d in re.findall(r'\$(\d+)', subq)))
        tasks.append(Task(idx=idx, subquestion=subq, deps=deps))
    return tasks


def substitute_deps(subquestion: str, completed: dict) -> str:
    """Replace $N references with a brief summary of task N's result."""
    def _replace(m):
        n      = int(m.group(1))
        result = completed.get(n, {})
        answer = (result.get("answer") or "(no result)").strip()[:400]
        status = result.get("status", "?")
        return f"[Task-{n} ({status}): {answer}]"
    return re.sub(r'\$(\d+)', _replace, subquestion)


class SHState(TypedDict):
    messages:     Annotated[list, add_messages]  # persistent across all questions
    plan_text:    str                            # last plan/replan text (debug)
    tasks:        list                           # [{idx, subquestion, deps}]
    task_results: dict                           # {task_idx (int): result_dict}
    plan_round:   int                            # 1-based cycle counter (reset per Q)
    final_answer: str                            # populated when done
    done:         bool


class DelegationContext:
    """Shared mutable context: pool, logger, and per-question delegation log."""

    def __init__(self, pool, logger):
        self.pool   = pool
        self.logger = logger
        self.current_qid        = None
        self.failed_delegations = 0
        self.q_delegations      = []
        self.all_delegations    = []

    def reset_question(self, qid: str) -> None:
        self.current_qid   = qid
        self.q_delegations = []


def build_sh_agent_compiler(api_key: str, model: str, ctx: DelegationContext,
                             checkpoint_db_path: str | None = None):
    """Compile the LLMCompiler SH graph. Returns (graph, checkpointer).

    checkpoint_db_path, if given, backs the checkpointer with a SQLite file
    instead of MemorySaver's in-process RAM. This is what makes cross-question
    memory survive a process restart when resuming a killed run with the same
    --run-name: MemorySaver starts empty on every new process regardless of
    thread_id, silently dropping all prior findings.
    """

    llm         = ChatOpenAI(api_key=api_key, model=model,
                             max_completion_tokens=4096, temperature=0)
    sys_planner = SystemMessage(content=PLANNER_SYSTEM_PROMPT)
    sys_joiner  = SystemMessage(content=JOINER_SYSTEM_PROMPT)

    # ── Planner ───────────────────────────────────────────────────────────────
    def planner_node(state: SHState) -> dict:
        round_n  = state.get("plan_round", 0) + 1
        print(f"\n[SH PLANNER — round {round_n}]")

        msgs      = [sys_planner] + list(state["messages"])
        response  = llm.invoke(msgs)
        plan_text = (response.content or "").strip()
        print(f"\n[SH PLAN]\n{plan_text}\n")

        # DIRECT ANSWER — SH already knows from cross-question memory
        dm = re.search(r'DIRECT ANSWER:\s*(.+)', plan_text, re.IGNORECASE)
        if dm:
            answer = dm.group(1).strip().split('\n')[0].strip()
            print(f"[SH PLANNER] direct answer from memory: {answer!r}")
            return {
                "messages":     [response],
                "plan_text":    plan_text,
                "tasks":        [],
                "task_results": {},
                "plan_round":   round_n,
                "final_answer": answer,
                "done":         True,
            }

        tasks = parse_plan(plan_text)
        if not tasks:
            # Fallback: treat the last human message as a single senior task
            last_q = next(
                (m.content for m in reversed(state["messages"])
                 if isinstance(m, HumanMessage)), ""
            )
            tasks = [Task(idx=1, subquestion=last_q, deps=[])]
            print("[SH PLANNER] no structured tasks parsed — falling back to single task")

        print(f"[SH PLANNER] {len(tasks)} task(s), "
              f"{sum(1 for t in tasks if not t.deps)} parallel-eligible")

        return {
            "messages":     [response],
            "plan_text":    plan_text,
            "tasks":        [{"idx": t.idx, "subquestion": t.subquestion, "deps": t.deps}
                             for t in tasks],
            "task_results": {},
            "plan_round":   round_n,
            "final_answer": "",
            "done":         False,
        }

    # ── Executor ──────────────────────────────────────────────────────────────
    def executor_node(state: SHState) -> dict:
        if state.get("done"):
            return {}

        tasks     = [Task(**t) for t in state["tasks"]]
        completed = dict(state.get("task_results") or {})
        remaining = [t for t in tasks if t.idx not in completed]

        for _guard in range(len(remaining) + 1):
            if not remaining:
                break
            ready = [t for t in remaining if all(d in completed for d in t.deps)]
            if not ready:
                print("[SH EXECUTOR] unresolvable dependency — running first pending task")
                ready = [remaining[0]]

            n_workers = min(len(ready), MAX_WORKERS)
            print(f"\n[SH EXECUTOR] dispatching {len(ready)} task(s) "
                  f"({n_workers} parallel worker slot(s))")

            parent_run_tree = get_current_run_tree()
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as exe:
                futures: dict = {}
                for t in ready:
                    subq       = substitute_deps(t.subquestion, completed)
                    worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
                    print(f"\n[SH -> SENIOR #{worker_idx}  task={t.idx}]\n{subq[:300]}")
                    futures[exe.submit(_run_senior, ctx, subq, worker_idx, parent_run_tree)] = (t, worker_idx, subq)

                for fut, (t, worker_idx, subq) in futures.items():
                    try:
                        result = fut.result()
                    except Exception as exc:
                        result = {
                            "status": "failed",
                            "answer": f"worker crashed: {exc}",
                            "spl_used": [], "sourcetypes": [], "full_state": [],
                            "iterations": 0, "cap_hit": False,
                        }
                    completed[t.idx] = result

                    if result["status"] in ("too_big", "failed"):
                        ctx.failed_delegations += 1

                    record = {
                        "worker":      f"senior#{worker_idx}",
                        "qid":         ctx.current_qid,
                        "subquestion": subq,
                        "status":      result["status"],
                        "answer":      result["answer"],
                        "spl_used":    result["spl_used"],
                        "sourcetypes": result["sourcetypes"],
                        "full_state":  result["full_state"],
                        "iterations":  result.get("iterations", 0),
                        "cap_hit":     result.get("cap_hit", False),
                    }
                    ctx.q_delegations.append(record)
                    ctx.all_delegations.append(record)

                    ctx.logger.timeline(
                        f"- **Senior #{worker_idx}**  _[{result['status']}]_  task={t.idx}\n"
                        f"    - subquestion: {subq[:200]}\n"
                        f"    - answer: {(result['answer'] or '').strip()[:400]}\n"
                        f"    - SPL: {result['spl_used']}"
                    )

            remaining = [t for t in remaining if t.idx not in completed]

        return {"task_results": completed}

    # ── Joiner ────────────────────────────────────────────────────────────────
    def joiner_node(state: SHState) -> dict:
        if state.get("done"):
            return {}

        tasks        = [Task(**t) for t in state["tasks"]]
        task_results = state.get("task_results") or {}
        plan_round   = state.get("plan_round", 1)

        parts = []
        for t in tasks:
            r = task_results.get(t.idx, {})
            parts.append(
                f"Task {t.idx} [{r.get('status', '?')}]:\n"
                f"  Question: {t.subquestion[:300]}\n"
                f"  Result: {(r.get('answer') or '(no result)').strip()[:600]}"
            )
        findings = "\n\n".join(parts)

        joiner_msg_text = (
            f"All delegated tasks are complete (round {plan_round}).\n\n"
            f"=== Task Results ===\n{findings}\n\n"
            "Synthesize the above and give your FINAL ANSWER, "
            "or request a focused REPLAN if a critical datum is missing."
        )
        joiner_hm = HumanMessage(content=joiner_msg_text)

        print(f"\n[SH JOINER — round {plan_round}]")
        msgs     = [sys_joiner] + list(state["messages"]) + [joiner_hm]
        response = llm.invoke(msgs)
        jtext    = (response.content or "").strip()
        print(f"\n[SH JOINER OUTPUT]\n{jtext}\n")

        # Option A — FINAL ANSWER
        fa_m = re.search(r'FINAL ANSWER:\s*(.+)', jtext, re.IGNORECASE | re.DOTALL)
        if fa_m:
            answer = fa_m.group(1).strip().split('\n')[0].strip()
            return {
                "messages":     [joiner_hm, response],
                "plan_text":    jtext,
                "final_answer": answer,
                "done":         True,
            }

        # Option B — REPLAN (only if rounds remain)
        if re.search(r'\bREPLAN\b', jtext, re.IGNORECASE) and plan_round < MAX_PLAN_ROUNDS:
            replan_tasks = parse_plan(jtext)
            if replan_tasks:
                print(f"[SH JOINER] replan — {len(replan_tasks)} new task(s) "
                      f"(round {plan_round} → {plan_round + 1})")
                return {
                    "messages":     [joiner_hm, response],
                    "plan_text":    jtext,
                    "tasks":        [{"idx": t.idx, "subquestion": t.subquestion,
                                      "deps": t.deps} for t in replan_tasks],
                    "task_results": {},
                    "plan_round":   plan_round + 1,
                    "done":         False,
                }

        # Fallback — extract best-effort answer from the last non-empty line
        print("[SH JOINER] no FINAL ANSWER / REPLAN tag — extracting from last line")
        lines  = [l.strip() for l in jtext.splitlines() if l.strip()]
        answer = lines[-1] if lines else jtext[:200]
        return {
            "messages":     [joiner_hm, response],
            "plan_text":    jtext,
            "final_answer": answer,
            "done":         True,
        }

    # ── Graph wiring ──────────────────────────────────────────────────────────
    def route_planner(state: SHState) -> str:
        return END if state.get("done") else "executor"

    def route_joiner(state: SHState) -> str:
        if state.get("done") or state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):      # replan set new tasks
            return "executor"
        return END

    g = StateGraph(SHState)
    g.add_node("planner",  planner_node)
    g.add_node("executor", executor_node)
    g.add_node("joiner",   joiner_node)
    g.set_entry_point("planner")
    g.add_conditional_edges("planner",  route_planner,
                            {"executor": "executor", END: END})
    g.add_edge("executor", "joiner")
    g.add_conditional_edges("joiner",   route_joiner,
                            {"executor": "executor", END: END})

    if checkpoint_db_path:
        conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    else:
        checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer), checkpointer


def _run_senior(ctx: DelegationContext, subquestion: str, idx: int, parent_run_tree) -> dict:
    """Submit one Senior worker task (called from ThreadPoolExecutor thread).

    contextvars (which LangSmith's tracing relies on) don't propagate into a
    fresh ThreadPoolExecutor thread, so without this the worker's whole trace
    would show up as a disconnected root trace instead of nesting under the
    SH's trace. `parent_run_tree` is captured in the main thread (where the
    contextvar is still populated) and re-applied here.
    """
    with tracing_context(parent=parent_run_tree):
        return ctx.pool.run_senior(subquestion, ctx.current_qid, idx)


def run_sh(graph, message: str, thread_id: str,
           *, qid: str = "", run_name: str = "", tracker=None) -> tuple[str, dict]:
    """Invoke the SH graph for one question or extractor-retry message.

    Returns (final_answer, full_state). Same interface as the v1.0 version so
    run_all_v1.py needs no structural changes.
    """
    config: dict = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_PLAN_ROUNDS * 6 + 10,
    }
    if run_name:
        config["run_name"] = run_name
    if qid:
        config["tags"]     = ["SH", qid]
        config["metadata"] = {"role": "SH", "qid": qid}
    if tracker is not None:
        config["callbacks"] = [tracker]

    result = graph.invoke(
        {
            "messages":     [HumanMessage(content=message)],
            "plan_text":    "",
            "tasks":        [],
            "task_results": {},
            "plan_round":   0,
            "final_answer": "",
            "done":         False,
        },
        config=config,
    )
    answer = result.get("final_answer", "")
    if not answer:
        for m in reversed(result.get("messages", [])):
            if isinstance(m, AIMessage) and m.content:
                answer = m.content
                break
    return answer, result
