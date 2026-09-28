#!/usr/bin/env python3
"""
SH (orchestrator / mastermind) agent for v1 — LLMCompiler edition.

Architecture:
    Planner → Parallel Executor → Joiner → (Replan once | FINAL ANSWER)

The SH LLM (gpt-5.4, persistent MemorySaver thread) generates a numbered task
DAG. Tasks with no $N dependencies fan out to one LangGraph node each.
Tasks with $N references wait for those results, then run. The Joiner assembles
all findings into a FINAL ANSWER, or requests a single focused replan round if
a critical datum is missing.

Cross-question memory is preserved: the MemorySaver thread accumulates every
plan + task-results summary + final answer across all 58 questions.
"""

import os
import re
import sqlite3
import time
import traceback
from dataclasses import dataclass, field
from typing import Annotated, Any, TypedDict

from case_file import build_ledger, parse_case_updates, render_ledger, snap_to_ledger
from executor_graph import build_executor_graph
from grounding import best_candidate, is_grounded
from plan_schema import (Plan, load_manifest, render_briefing, render_plan_text,
                         render_scope, to_tasks)
from hitl import RunPaused, resolve_interrupt
from llm_errors import describe_llm_error, resilient_http_client
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from langsmith.run_helpers import get_current_run_tree, tracing_context

MAX_PLAN_ROUNDS = 3   # max planner→executor→joiner cycles per question
MAX_WORKERS     = 6   # matches SplunkConnectionPool default size
MAX_HISTORY_MSGS = 24  # cross-question memory window fed to SH LLM calls
SH_TIMEOUT_S     = 90.0  # SH turns are plan/join text only - shorter than a worker turn
SH_MAX_RETRIES   = 3
                       # (~4-8 msgs/question => ~3-5 prior questions visible).
                       # Unbounded replay cost $0.95 of SH input on run_0.2's Q202 alone.


def _window(messages):
    """Bounded history for SH LLM calls. The persistent thread accumulates every
    prior question's planner/joiner transcript; replaying all of it into every
    call scales cost quadratically over the run."""
    return list(messages)[-MAX_HISTORY_MSGS:]


# ── Planner prompt ─────────────────────────────────────────────────────────────
PLANNER_SYSTEM_PROMPT = """You are the SH agent - the mastermind orchestrator for a BOTSv3 security investigation (August 2018 APT attack against Frothly, all data in Splunk index=botsv3).

YOUR ROLE
- You PLAN and DELEGATE. You do NOT query Splunk yourself.
- A DATASET block below lists every sourcetype and the busiest sources in the index.
  Your first job on any question is to decide WHERE the answer lives, then hand each
  worker a scope narrow enough to be tractable.
- Workers run IN PARALLEL unless you make one depend on another.

TWO AXES - THIS IS THE MOST COMMON WAY TO GET A QUESTION WRONG
Data is addressed by `sourcetype` AND by `source`, and they are not interchangeable.
A single sourcetype can hide many unrelated feeds: `sourcetype=syslog` contains the
Cisco NVM flow data, which is reachable only as `source="cisconvmflowdata"` and is the
13th busiest feed in the index. If no sourcetype name matches what the question
describes, that is NOT evidence the data is absent - check the source list. Scoping a
worker by `sources` alone is valid and is sometimes the only thing that works.

CHOOSING A SCOPE - in this order
1. A sourcetype whose name matches what the question is about.
2. Failing that, a source from the briefing whose name matches.
3. Failing both, spawn an `exploration` worker. It searches for which feeds even
   mention the question's key terms and reports back - use it when you genuinely
   cannot name a scope, not as a substitute for reading the briefing.

CROSS-QUESTION MEMORY
You remember every earlier question in this run. Carry entities forward (hosts, IPs,
users, bucket names, time windows, feeds) and restate them explicitly inside every
subquestion and in `prior_info`. Never write "the host from before" - workers share no
memory with you or with each other.

WRITING SPAWNS
- 1-6 spawns. Exactly ONE if the question is a single atomic lookup.
- Each `subquestion` must stand alone: every entity, time range and feed spelled out.
- `deps` only where a task genuinely cannot start until another finishes. Everything
  else runs in parallel - prefer that.
- Use $N inside a subquestion to reference task N's result inline.
- `confidence` is your honest estimate that the answer lies in the scope you named.
  It is recorded and calibrated, never used to judge you - a low number on a genuinely
  uncertain scope is more useful than a confident guess.
- `prior_info` is what you already know that narrows the hunt, including feeds a
  previous round ruled out.

DIRECT ANSWER
Fill `direct_answer` only when you already know the value from cross-question memory or
general knowledge, and leave `spawns` empty. Never use it for a value that came from a
CASE FILE finding - delegate a task to re-verify that instead.

`expected_shape` is the exact form the scoreboard wants (e.g. "bare MAC address
lowercase", "integer only", "comma-separated lowercase list no spaces"). Derive it from
the answer guidance.

A CASE FILE block may precede this conversation - treat `[?]`/`[X]` findings as unproven and re-verify before building a plan on them."""


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
  format, nothing else on that line.

GROUNDING RULE — CRITICAL:
- Your FINAL ANSWER must be a value that literally appears in one of the task
  results above (or the question). Never invent, guess, or synthesize a value
  no worker reported. If the tasks did not produce the needed value, prefer a
  focused REPLAN. If you must answer without it, use the closest value a worker
  actually reported, not a plausible-sounding fabrication.

LEDGER RULE — when a CANDIDATES list is provided, your FINAL ANSWER must be one
of those values copied character-for-character (or a value from the question
text). Do not re-type, trim, expand, or reformat a candidate: no dropping
domain suffixes, no rounding numbers, no removing prefixes. If two candidates
conflict, prefer the one whose SPL and status best satisfy the question's own
constraints, and copy it exactly.

CASE UPDATES — after your FINAL ANSWER line, record durable incident facts:
CASE UPDATES:
- entity <host|user|ip|domain|file|hash|bucket|cve> <value>
- finding [verified|hypothesis] <one-sentence claim> | evidence: <sourcetype/SPL fragment>
Only include facts a future question could reuse. Mark [verified] only if a
worker proved it with a query this round."""


@dataclass
class Task:
    idx: int
    subquestion: str
    deps: list = field(default_factory=list)    # list of int task indices


def parse_plan(text: str) -> list[Task]:
    """Extract numbered tasks from planner/replan output."""
    tasks = []
    # \s* prefix: the joiner's REPLAN template indents tasks by two spaces
    pattern = re.compile(
        r'^\s*(\d+)\.\s+(.+?)(?=^\s*\d+\.|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        idx  = int(m.group(1))
        subq = m.group(2).strip()
        deps = sorted(set(int(d) for d in re.findall(r'\$(\d+)', subq)))
        tasks.append(Task(idx=idx, subquestion=subq, deps=deps))
    # Drop $N refs that don't correspond to a real task (e.g. literal dollar
    # amounts like "$40" in the subquestion text).
    valid_idx = {t.idx for t in tasks}
    for t in tasks:
        t.deps = [d for d in t.deps if d in valid_idx and d != t.idx]
    return tasks


def decide_joiner_answer(answer: str, task_results: dict, question_text: str,
                         *, plan_round: int, max_rounds: int) -> dict:
    """Grounding gate for the joiner's FINAL ANSWER.

    - grounded            -> keep it ('final')
    - ungrounded, rounds  -> 'replan' with a pointed reason
    - ungrounded, no rnds -> fall back to best worker candidate, else keep
    """
    if is_grounded(answer, task_results, question_text):
        return {"action": "final", "answer": answer}
    if plan_round < max_rounds:
        return {"action": "replan",
                "reason": (f"Your proposed answer {answer!r} was NOT found in any "
                           f"task result or the question. Either run a task that "
                           f"produces it as an exact value, or choose a value that "
                           f"DOES appear in the evidence.")}
    cand = best_candidate(task_results)
    return {"action": "final", "answer": cand if cand else answer}


def apply_case_updates(case_file, joiner_text: str, *, source_qid: str) -> int:
    """Parse a CASE UPDATES block and write it into the case file. Returns count."""
    n = 0
    for u in parse_case_updates(joiner_text):
        if u["kind"] == "entity":
            case_file.add_entity(u["etype"], u["value"], qid=source_qid)
            n += 1
        elif u["kind"] == "finding":
            case_file.add_finding(u["claim"], evidence=u.get("evidence", ""),
                                  source_qid=source_qid, status=u["status"])
            n += 1
    return n


HANDOFF_MAX_CHARS = 1500
HANDOFF_KEEP      = 3      # most recent digests injected per question


def build_handoff_digest(record: dict) -> str:
    """Structured handoff for the worker that replaces a failed/too_big/cap-hit
    delegation: what was tried, what to not repeat, where the trail went cold.
    run_0.2 burned $26.53 on replacement workers re-running discovery from zero.
    """
    label = record.get("status", "?")
    if record.get("cap_hit"):
        label += ", cap-hit"
    lines = [f"PRIOR ATTEMPT ({label}, {record.get('iterations', 0)} iterations) "
             f"by {record.get('worker', '?')}:"]
    sts = record.get("sourcetypes") or []
    if sts:
        lines.append(f"- sourcetypes already examined: {', '.join(sts)}")
    spl = record.get("spl_used") or []
    if spl:
        lines.append("- SPL already run (do NOT repeat these; go one step further):")
        lines += [f"    {q[:200]}" for q in spl[-6:]]
    tail = (record.get("answer") or "").strip()
    if tail:
        lines.append(f"- where the trail went cold: {tail[-400:]}")
    out = "\n".join(lines)
    # ponytail: char truncation, not token-aware; upgrade if digests start clipping SPL
    return out[:HANDOFF_MAX_CHARS]


def substitute_deps(subquestion: str, completed: dict) -> str:
    """Replace $N references with a brief summary of task N's result."""
    def _replace(m):
        n = int(m.group(1))
        if n not in completed:
            return m.group(0)   # not a task ref (e.g. a dollar amount) — leave as-is
        result = completed[n]
        answer = (result.get("answer") or "(no result)").strip()[:400]
        status = result.get("status", "?")
        return f"[Task-{n} ({status}): {answer}]"
    return re.sub(r'\$(\d+)', _replace, subquestion)


def _delegation_record(worker_idx, qid, subq: str, result: dict) -> dict:
    """The delegation-record dict shape used at every worker call site —
    same 10 keys, same values."""
    return {
        "worker":      f"senior#{worker_idx}",
        "qid":         qid,
        "subquestion": subq,
        "status":      result.get("status", "?"),
        "answer":      result.get("answer", ""),
        "spl_used":    result.get("spl_used", []),
        "sourcetypes": result.get("sourcetypes", []),
        "full_state":  result.get("full_state", []),
        "iterations":  result.get("iterations", 0),
        "cap_hit":     result.get("cap_hit", False),
        "duration_s":  result.get("duration_s", 0.0),
        # Schema B (finding.py): `value` is the bare answer as its own field, so
        # the ledger reads it instead of scraping prose. negative_findings is
        # what this worker ruled OUT - 73% of delegations end partial or failed,
        # and until now everything they eliminated was discarded, which is why
        # replan rounds re-tread ground round 1 already covered.
        "value":             result.get("value", ""),
        "value_kind":        result.get("value_kind", ""),
        "evidence":          result.get("evidence", ""),
        "worker_confidence": result.get("confidence"),
        "search_space_used": result.get("search_space_used") or
                             {"sourcetypes": [], "sources": []},
        "negative_findings": result.get("negative_findings") or [],
        "notes":             result.get("notes", ""),
        "structured":        result.get("structured", False),
        # Set by the planner when it spawned this worker (spawn_report.py reads
        # these against status to calibrate SH's self-reported confidence).
        "spawn_type":  result.get("spawn_type", "senior"),
        "search_space": result.get("search_space") or {},
        "prior_info":  result.get("prior_info", ""),
        "confidence":  result.get("sh_confidence"),
    }


class SHState(TypedDict):
    messages:     Annotated[list, add_messages]  # persistent across all questions
    plan_text:    str                            # last plan/replan text (debug)
    tasks:        list                           # [{idx, subquestion, deps}]
    task_results: dict                           # {task_idx (int): result_dict}
    plan_round:   int                            # 1-based cycle counter (reset per Q)
    final_answer: str                            # populated when done
    done:         bool
    needs_replan: bool                           # True -> route joiner back to planner


class DelegationContext:
    """Shared mutable context: pool, logger, and per-question delegation log."""

    def __init__(self, pool, logger, case_file=None, use_case_file=True):
        self.pool          = pool
        self.logger        = logger
        self.case_file     = case_file
        self.use_case_file = use_case_file
        self.current_qid        = None
        self.current_points     = 0
        self.current_question   = ""
        self.current_guidance   = ""
        self.failed_delegations = 0
        self.q_delegations      = []
        self.q_handoffs         = []
        self.all_delegations    = []
        # The LangSmith parent for the current wave of workers. It lives here,
        # not in the Send payload, because a Send payload is checkpointed state
        # and a live RunTree cannot be serialised - see _prepare_sends.
        self.parent_run_tree: Any = None

    def reset_question(self, qid: str, points: int = 0, question: str = "",
                       guidance: str = "") -> None:
        self.current_qid      = qid
        self.current_points   = points
        self.current_question = question
        self.current_guidance = guidance
        self.q_delegations    = []
        self.q_handoffs       = []


def build_sh_agent_compiler(api_key: str, model: str, ctx: DelegationContext,
                             checkpoint_db_path: str | None = None):
    """Compile the LLMCompiler SH graph. Returns (graph, checkpointer).

    checkpoint_db_path, if given, backs the checkpointer with a SQLite file
    instead of MemorySaver's in-process RAM. This is what makes cross-question
    memory survive a process restart when resuming a killed run with the same
    --run-name: MemorySaver starts empty on every new process regardless of
    thread_id, silently dropping all prior findings.
    """

    # See LLM_TIMEOUT_S note in splunk_agent.py - SDK default is 600s.
    llm         = ChatOpenAI(api_key=api_key, model=model,
                             max_completion_tokens=4096, temperature=0,
                             timeout=SH_TIMEOUT_S, max_retries=SH_MAX_RETRIES,
                             http_client=resilient_http_client())
    # strict json_schema: a malformed plan fails the call instead of silently
    # degrading to the old "no structured tasks parsed" single-task fallback,
    # which hid a planning failure as one broad delegation.
    planner_llm = llm.with_structured_output(Plan, method="json_schema", strict=True)
    sys_planner = SystemMessage(content=PLANNER_SYSTEM_PROMPT)
    sys_joiner  = SystemMessage(content=JOINER_SYSTEM_PROMPT)

    # Read once per process, not per question: BOTSv3 is static, so re-reading
    # 93KB of JSON 56 times would buy nothing (docs/future_work.md #1).
    try:
        sys_dataset = [SystemMessage(content=render_briefing(load_manifest()))]
    except (OSError, ValueError) as exc:
        # A missing or corrupt manifest must not take the run down - SH can
        # still plan, just blind to the source axis, which is v0.2 behaviour.
        print(f"[SH PLANNER] dataset briefing unavailable ({exc}) - planning without it")
        sys_dataset = []

    # ── Planner ───────────────────────────────────────────────────────────────
    def planner_node(state: SHState) -> dict:
        round_n  = state.get("plan_round", 0) + 1
        print(f"\n[SH PLANNER — round {round_n}]")

        extra = []
        if ctx.case_file and ctx.use_case_file:
            digest = ctx.case_file.render_digest()
            if digest.strip():
                extra = [SystemMessage(content=(
                    "CASE FILE (known incident state — verified [OK], "
                    "hypothesis [?], refuted [X]; re-verify [?]/[X] findings "
                    "before relying on them):\n" + digest))]
        msgs = [sys_planner] + sys_dataset + extra + _window(state["messages"])
        plan = planner_llm.invoke(msgs)
        plan_text = render_plan_text(plan)
        # The plan re-enters the persistent thread as text: cross-question
        # memory is a message history, and a pydantic object is not a message.
        response = AIMessage(content=plan_text)
        print(f"\n[SH PLAN]\n{plan_text}\n")

        if plan.direct_answer:
            answer = plan.direct_answer.strip()
            print(f"[SH PLANNER] direct answer from memory: {answer!r}")
            return {
                "messages":     [response],
                "plan_text":    plan_text,
                "tasks":        [],
                "task_results": {},
                "plan_round":   round_n,
                "final_answer": answer,
                "done":         True,
                "needs_replan": False,
            }

        tasks = to_tasks(plan)
        if not tasks:
            # Neither a direct answer nor a spawn. Delegate the question whole
            # rather than stalling it - v0.2 did this on every unparsed plan;
            # here it is the genuinely rare case.
            last_q = next((m.content for m in reversed(state["messages"])
                           if isinstance(m, HumanMessage)), "")
            tasks = [{"idx": 1, "subquestion": last_q, "deps": [],
                      "spawn_type": "senior", "prior_info": "", "confidence": 0,
                      "search_space": {"sourcetypes": [], "sources": []}}]
            print("[SH PLANNER] plan carried no spawns - delegating whole question")

        print(f"[SH PLANNER] {len(tasks)} task(s), "
              f"{sum(1 for t in tasks if not t['deps'])} parallel-eligible, "
              f"mean confidence {sum(t['confidence'] for t in tasks) / len(tasks):.0f}")

        return {
            "messages":     [response],
            "plan_text":    plan_text,
            "tasks":        tasks,
            "task_results": {},
            "plan_round":   round_n,
            "final_answer": "",
            "done":         False,
            "needs_replan": False,
        }

    # ── Executor ──────────────────────────────────────────────────────────────
    # ── Executor: one LangGraph node per Senior worker ────────────────────────
    # Workers used to run on a ThreadPoolExecutor *inside* one node, invisible to
    # LangGraph, so a worker result was not graph state and an API failure had
    # nowhere framework-native to pause. They are now a fan-out subgraph
    # (executor_graph.py) embedded as a node: siblings finish before anything
    # pauses, and a resume replays only the cheap hitl node - never a paid worker.

    def _prepare_sends(task: dict, completed: dict) -> list[dict]:
        """One payload per worker to dispatch for this task (main dispatch node).

        Worker numbering, dependency substitution and handoff context all happen
        here, once per worker, exactly as the old executor did before submitting.
        """
        subq = substitute_deps(task["subquestion"], completed)
        # The search space SH chose, and what it already knows, ride into the
        # subquestion itself - workers share no state with the planner, so a
        # scope that is not written into the task text does not exist.
        scope = render_scope(task)
        if scope:
            subq += "\n\n" + scope
        if ctx.q_handoffs:
            subq += ("\n\nCONTEXT FROM PRIOR ATTEMPTS ON THIS QUESTION "
                     "(resume the hunt, do not restart it):\n"
                     + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]))
        # Captured here rather than inside the worker: LangGraph runs fan-out
        # branches on its own threads and contextvars do not propagate, so the
        # LangSmith parent must be passed explicitly (same reason _run_senior
        # exists for the old ThreadPoolExecutor).
        #
        # It goes on ctx, NOT into the payload. A Send payload is checkpointed
        # graph state, and a live RunTree carries a client and locks, so writing
        # one crashed the whole question with "Type is not msgpack serializable:
        # Send" - the error names the Send envelope, not the object inside it.
        # ctx is plain process memory and is never checkpointed.
        ctx.parent_run_tree = get_current_run_tree()
        kind = "EXPLORE" if task.get("spawn_type") == "exploration" else "SENIOR"
        worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
        print(f"\n[SH -> {kind} #{worker_idx}  task={task['idx']}]\n{subq[:300]}")
        return [{"task": task, "subq": subq, "worker_idx": worker_idx}]

    def _run_task(payload: dict) -> dict:
        task, subq  = payload["task"], payload["subq"]
        worker_idx  = payload["worker_idx"]
        # An exploration spawn answers "which feeds could hold this", not the
        # question itself, so it runs a different agent on a cheap model. It is
        # still a worker: same record shape, same ledger, same accounting.
        if task.get("spawn_type") == "exploration":
            t0 = time.perf_counter()
            with tracing_context(parent=ctx.parent_run_tree):
                result = ctx.pool.run_exploration(subq, ctx.current_qid, worker_idx)
            result["duration_s"] = round(time.perf_counter() - t0, 1)
        else:
            result = _run_senior(ctx, subq, worker_idx, ctx.parent_run_tree)
        # idx/worker_idx ride along so collect() can account per task.
        # SH-side spawn metadata travels with the result so the delegation
        # record carries both what SH intended and what came back - that pairing
        # is what spawn_report.py calibrates confidence against.
        result = {**result, "idx": task["idx"], "worker_idx": worker_idx,
                  "spawn_type":    task.get("spawn_type", "senior"),
                  "search_space":  task.get("search_space") or {},
                  "prior_info":    task.get("prior_info", ""),
                  "sh_confidence": task.get("confidence")}

        record = _delegation_record(worker_idx, ctx.current_qid, subq, result)
        ctx.q_delegations.append(record)
        ctx.all_delegations.append(record)
        ctx.logger.timeline(
            f"- **Senior #{worker_idx}**  _[{result['status']}]_  task={task['idx']}\n"
            f"    - subquestion: {subq[:200]}\n"
            f"    - answer: {(result.get('answer') or '').strip()[:400]}\n"
            f"    - SPL: {result.get('spl_used')}"
        )
        return result

    def _on_wave(results: list) -> None:
        """Per-wave accounting. Counts a task's failure once per task per round,
        keyed on idx rather than on the worker that reported it."""
        counted: set = set()
        for r in results:
            if not (r.get("status") in ("too_big", "failed") or r.get("cap_hit")):
                continue
            idx = r.get("idx")
            if idx in counted:
                continue
            if r.get("status") in ("too_big", "failed"):
                ctx.failed_delegations += 1
            ctx.q_handoffs.append(build_handoff_digest(
                {**r, "worker": f"senior#{r.get('worker_idx')}"}))
            counted.add(idx)

    # checkpointer=None on purpose: the parent SH graph's checkpointer owns this
    # subgraph's state, which is what makes an interrupt in here resumable from
    # the parent with Command(resume=...).
    executor_subgraph = build_executor_graph(
        _run_task,
        prepare_sends=_prepare_sends,
        on_wave=_on_wave,
        # The old ThreadPoolExecutor bounded concurrency at MAX_WORKERS, and
        # SplunkConnectionPool holds exactly that many connections. LangGraph
        # would otherwise run every Send in the superstep at once.
        max_parallel=MAX_WORKERS,
    )

    # ── Joiner ────────────────────────────────────────────────────────────────
    def joiner_node(state: SHState) -> dict:
        if state.get("done"):
            return {}

        # Read the task dicts directly. Task() is the joiner-replan shape and
        # would reject the planner's extra spawn keys (spawn_type, search_space,
        # prior_info, confidence) with a TypeError.
        tasks        = list(state["tasks"] or [])
        task_results = state.get("task_results") or {}
        plan_round   = state.get("plan_round", 1)

        parts = []
        for t in tasks:
            r = task_results.get(t["idx"], {})
            parts.append(
                f"Task {t['idx']} [{r.get('status', '?')}]:\n"
                f"  Question: {t['subquestion'][:300]}\n"
                f"  Result: {(r.get('answer') or '(no result)').strip()[:600]}"
            )
        findings = "\n\n".join(parts)

        ledger = build_ledger(ctx.q_delegations)
        ledger_block = render_ledger(ledger)

        handoff_block = ""
        if ctx.q_handoffs:
            handoff_block = ("=== Failed-Attempt Digests ===\n"
                             + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]) + "\n\n")

        joiner_msg_text = (
            f"All delegated tasks are complete (round {plan_round}).\n\n"
            f"=== Task Results ===\n{findings}\n\n"
            + (ledger_block + "\n\n" if ledger_block else "")
            + handoff_block
            + "Synthesize the above and give your FINAL ANSWER, "
              "or request a focused REPLAN if a critical datum is missing."
        )
        joiner_hm = HumanMessage(content=joiner_msg_text)

        print(f"\n[SH JOINER — round {plan_round}]")
        msgs     = [sys_joiner] + _window(state["messages"]) + [joiner_hm]
        response = llm.invoke(msgs)
        jtext    = (response.content or "").strip()
        print(f"\n[SH JOINER OUTPUT]\n{jtext}\n")

        # Option A — FINAL ANSWER
        fa_m = re.search(r'FINAL ANSWER:\s*(.+)', jtext, re.IGNORECASE | re.DOTALL)
        if fa_m:
            answer = fa_m.group(1).strip().split('\n')[0].strip()
            snapped = snap_to_ledger(answer, ledger)
            if snapped != answer:
                print(f"[SH JOINER] ledger snap: {answer!r} -> {snapped!r}")
                answer = snapped
            # ctx.current_question, NOT a scan of state["messages"]: the persistent
            # cross-question thread's first HumanMessage is always the run's first
            # question, and later HumanMessages are joiner/replan scaffolding.
            # run_0.2 ground-checked answers against Q200's
            # question text because of this.
            qtext = ctx.current_question
            # task_results resets to {} on every REPLAN, but a value proven in
            # an earlier round can still be the correct restated FINAL ANSWER —
            # ground against every delegation this question has produced so far
            # (ctx.q_delegations), not just this round's.
            grounding_evidence = dict(task_results)
            grounding_evidence.update({
                f"prior_{i}": {"answer": d.get("answer")}
                for i, d in enumerate(ctx.q_delegations)
            })
            decision = decide_joiner_answer(
                answer, grounding_evidence, qtext,
                plan_round=plan_round, max_rounds=MAX_PLAN_ROUNDS)
            if decision["action"] == "replan":
                print(f"[SH JOINER] grounding check FAILED for {answer!r} — "
                      f"forcing replan (round {plan_round} → {plan_round + 1})")
                replan_hm = HumanMessage(content=(
                    "GROUNDING CHECK FAILED. " + decision["reason"] +
                    "\nProduce a REPLAN with 1-2 targeted tasks, or a corrected "
                    "FINAL ANSWER that is present in the evidence."))
                return {
                    "messages":     [joiner_hm, response, replan_hm],
                    "plan_text":    jtext,
                    "tasks":        [],
                    "task_results": task_results,
                    "plan_round":   plan_round,
                    "done":         False,
                    "needs_replan": True,
                }
            answer = decision["answer"]
            if ctx.case_file and ctx.use_case_file:
                apply_case_updates(ctx.case_file, jtext, source_qid=ctx.current_qid)
            return {
                "messages":     [joiner_hm, response],
                "plan_text":    jtext,
                "final_answer": answer,
                "done":         True,
                "needs_replan": False,
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
                    # Replan tasks carry the full spawn shape so _prepare_sends
                    # and the delegation record see the same keys either way.
                    "tasks":        [{"idx": t.idx, "subquestion": t.subquestion,
                                      "deps": t.deps, "spawn_type": "senior",
                                      "search_space": {"sourcetypes": [], "sources": []},
                                      "prior_info": "", "confidence": 0}
                                     for t in replan_tasks],
                    "task_results": {},
                    "plan_round":   plan_round + 1,
                    "done":         False,
                }

        # Fallback — joiner produced neither a usable FINAL ANSWER nor a runnable
        # replan (typically: REPLAN requested with rounds exhausted). Prefer the
        # best real worker answer from ANY round of this question over joiner
        # prose — run_0.2's Q200 submitted the last line of a replan plan (a task
        # description) because this branch grabbed jtext's last line.
        cand = best_candidate({i: {"answer": d.get("answer"), "status": d.get("status")}
                               for i, d in enumerate(ctx.q_delegations)})
        if cand:
            print("[SH JOINER] no FINAL/REPLAN available — falling back to best worker answer")
            answer = cand
        else:
            print("[SH JOINER] no FINAL ANSWER / REPLAN tag — extracting from last line")
            lines  = [ln.strip() for ln in jtext.splitlines() if ln.strip()]
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
        if state.get("needs_replan"):
            return "planner"
        if state.get("done"):
            return END
        if state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):      # replan set new tasks
            return "executor"
        return END

    g = StateGraph(SHState)
    g.add_node("planner",     planner_node)
    g.add_node("executor",    executor_subgraph)
    g.add_node("joiner",      joiner_node)
    g.set_entry_point("planner")
    g.add_conditional_edges("planner",  route_planner,
                            {"executor": "executor", END: END})
    g.add_edge("executor", "joiner")
    g.add_conditional_edges("joiner",   route_joiner,
                            {"executor": "executor", "planner": "planner", END: END})

    if checkpoint_db_path:
        conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    else:
        checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer), checkpointer


def _run_senior(ctx: DelegationContext, subquestion: str, idx: int, parent_run_tree,
                max_iter: int | None = None) -> dict:
    """Submit one Senior worker task (called from ThreadPoolExecutor thread).

    contextvars (which LangSmith's tracing relies on) don't propagate into a
    fresh ThreadPoolExecutor thread, so without this the worker's whole trace
    would show up as a disconnected root trace instead of nesting under the
    SH's trace. `parent_run_tree` is captured in the main thread (where the
    contextvar is still populated) and re-applied here.
    """
    t0 = time.perf_counter()
    with tracing_context(parent=parent_run_tree):
        result = ctx.pool.run_senior(subquestion, ctx.current_qid, idx,
                                     points=ctx.current_points, max_iter=max_iter)
    # Every worker reaches Splunk through here, so one timer covers all of them.
    # Summed worker time exceeds the SH stage's wall clock whenever the fan-out
    # actually ran in parallel; that ratio is the only readout of whether
    # parallelism is paying off.
    if isinstance(result, dict):
        result["duration_s"] = round(time.perf_counter() - t0, 1)
    return result


def run_sh(graph, message: str, thread_id: str,
           *, qid: str = "", run_name: str = "", tracker=None,
           run_dir: str = ".") -> tuple[str, dict]:
    """Invoke the SH graph for one question or extractor-retry message.

    Returns (final_answer, full_state). Same interface as the v0.0 version so
    run_all_v0.py needs no structural changes.
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

    # A failed SH turn must not kill a multi-hour run - this was the only LLM
    # call path in the pipeline with no exception guard (Senior workers have two
    # layers). Both run_sh callers live in run_all_v0.py, so the guard goes here
    # once rather than at each call site. Returns the empty-answer sentinel; the
    # caller falls back to the best worker answer for that question. Cross-question
    # memory is unaffected - the SH graph's SQLite checkpointer holds it on disk.
    try:
        result = graph.invoke(
            {
                "messages":     [HumanMessage(content=message)],
                "plan_text":    "",
                "tasks":        [],
                "task_results": {},
                "plan_round":   0,
                "final_answer": "",
                "done":         False,
                "needs_replan": False,
            },
            config=config,
        )
    except RunPaused:
        # A deliberate pause is not a crash. It must reach main() rather than be
        # converted into the empty sentinel, which would silently resume the run
        # past the very failure a human was being asked to decide about.
        raise
    except Exception as exc:
        print(describe_llm_error(exc, run_name or (f"SH-{qid}" if qid else "SH")))
        traceback.print_exc()
        return "", {}

    # The executor subgraph's hitl node interrupts rather than raising, so
    # invoke() RETURNS with __interrupt__ set. Ignoring it would hand back an
    # empty answer and silently continue past the failure. Feed the human's
    # choice back with Command(resume=...) - only the hitl node replays.
    while result.get("__interrupt__"):
        choice = resolve_interrupt(result["__interrupt__"], qid=qid, run_dir=run_dir)
        print(f"[HITL] resuming {qid} with: {choice}")
        result = graph.invoke(Command(resume=choice), config=config)

    answer = result.get("final_answer", "")
    if not answer:
        for m in reversed(result.get("messages", [])):
            if isinstance(m, AIMessage) and m.content:
                answer = m.content
                break
    return answer, result
