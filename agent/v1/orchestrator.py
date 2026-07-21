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

from grounding import is_grounded, best_candidate
from splunk_subagent import VERIFIER_MAX_ITER
from case_file import build_ledger, render_ledger, snap_to_ledger, CaseFile, parse_case_updates
from adjudicator import (adjudicate_once, resolve_choice, fallback_choice,
                         ADJUDICATOR_SYSTEM_PROMPT, majority_answer)
from specialists import parse_specialist_tag


MAX_PLAN_ROUNDS = 3   # max planner→executor→joiner cycles per question
MAX_WORKERS     = 6   # matches SplunkConnectionPool default size
MAX_HISTORY_MSGS = 24  # cross-question memory window fed to SH LLM calls
                       # (~4-8 msgs/question => ~3-5 prior questions visible).
                       # Unbounded replay cost $0.95 of SH input on run_1.2's Q202 alone.
ADJUDICATE_MIN_CANDIDATES = 2     # adjudication only when selection is a real choice
ESCALATE_MIN_POINTS       = 1000  # C3: low-confidence 1000-pt questions escalate to gpt-5.4
METRICS_SAMPLES   = 3     # C4: samples per metrics task (majority vote)
SAMPLE_MIN_POINTS = 500   # only high-value questions pay the 3x metrics cost


def _window(messages):
    """Bounded history for SH LLM calls. The persistent thread accumulates every
    prior question's planner/joiner transcript; replaying all of it into every
    call scales cost quadratically over the run."""
    return list(messages)[-MAX_HISTORY_MSGS:]


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
  Do NOT write TASKS in that case.
- Also output one line:  EXPECTED SHAPE: <the exact form the scoreboard wants —
  e.g. "bare MAC address lowercase", "integer only", "comma-separated lowercase
  list no spaces", "filename with extension". Derive it from the answer guidance.>
- Prefix every task with a specialist tag: [HUNTER] for entity hunts across
  hosts/users/IPs, [CONTENT] when the answer is inside raw event text (emails,
  scripts, logs to READ), [METRICS] for any computed number (averages,
  percentiles, durations, counts with arithmetic). Untagged tasks default to
  [HUNTER].
- If the question message contains a DUAL-TRACK instruction: your TASKS must
  form two clearly orthogonal approaches (different sourcetype families or
  methods), 2-3 tasks each within the 6-task cap, and at least one task must
  enumerate the whole population unfiltered before narrowing.
- Never use DIRECT ANSWER for a value that comes from the CASE FILE block; delegate a task to re-verify it instead.

A CASE FILE block may precede this conversation — treat `[?]`/`[X]` findings as unproven; \
re-verify before building a plan on them."""


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


# ── Verifier prompt (prove-or-refute pass for >=500pt questions) ───────────────
VERIFIER_SYSTEM_PROMPT = """You are a Senior Splunk verification worker. You are NOT \
answering a fresh question — you are checking whether a candidate answer someone else \
already produced is actually correct.

You will be given the original question and a CANDIDATE ANSWER. Run AT MOST 3 targeted \
Splunk queries to prove or refute the candidate — e.g. re-check the exact field value, \
re-check event ordering/timestamps if "first"/"earliest"/"last" is involved, or re-check \
that the entity type matches what was asked (do not accept a plausible-but-wrong category,
e.g. a connection event mistaken for a mining event).

Do NOT re-investigate from scratch. Do NOT explore unrelated leads. Your only job is to
confirm or refute the ONE candidate value with hard evidence.

End your response with EXACTLY ONE of:
CONFIRMED: <the value you confirmed>
REFUTED. CORRECTION: <the corrected value, if your evidence supports one>

If you cannot find evidence either way after your 3 queries, treat it as CONFIRMED
(never block the pipeline on an inconclusive check)."""


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


def _should_verify(ctx: "DelegationContext") -> bool:
    """Points-gated: only >=500pt questions get a Verifier pass."""
    return ctx.current_points >= 500


def parse_verifier_verdict(text: str) -> dict:
    """Parse a Verifier worker's prove-or-refute output.
    Inconclusive defaults to 'confirmed' so verification never blocks a pipeline
    that already has a grounded answer."""
    t = text or ""
    if re.search(r'\bREFUTED\b', t, re.IGNORECASE):
        cm = re.search(r'CORRECTION:\s*(.+)', t, re.IGNORECASE)
        return {"verdict": "refuted",
                "correction": (cm.group(1).strip().split('\n')[0].strip() if cm else "")}
    return {"verdict": "confirmed", "correction": ""}


def promote_from_verdict(case_file, answer: str, verdict: dict) -> None:
    """Reflect a Verifier verdict into the case file: findings whose claim
    contains the checked answer flip to verified/refuted accordingly."""
    a = (answer or "").strip().lower()
    if not a:
        return
    for f in case_file.iter_findings():
        if len(a) < 4 or f.get("source_qid") == "RECON":
            continue
        if not re.search(rf'(?<!\w){re.escape(a)}(?!\w)', f["claim"].lower()):
            continue
        if verdict["verdict"] == "confirmed":
            case_file.set_status(f["id"], "verified")
        elif verdict["verdict"] == "refuted":
            case_file.set_status(f["id"], "refuted")


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
    run_1.2 burned $26.53 on replacement workers re-running discovery from zero.
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
    """The delegation-record dict shape shared by executor/verifier/adjudicator
    nodes — same 10 keys, same values, every call site."""
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
    }


def plan_samples(subquestion: str, points: int) -> int:
    """C4 self-consistency: [METRICS] tasks on high-value questions run 3x
    (temperature 0.3) and the majority extracted value wins. Everything else
    runs once. Gated at >=500pt as a cost guard — the spec samples all metrics
    questions, but low-value ones can't recoup the 3x spend."""
    if (parse_specialist_tag(subquestion) == "metrics"
            and (points or 0) >= SAMPLE_MIN_POINTS):
        return METRICS_SAMPLES
    return 1


class SHState(TypedDict):
    messages:     Annotated[list, add_messages]  # persistent across all questions
    plan_text:    str                            # last plan/replan text (debug)
    tasks:        list                           # [{idx, subquestion, deps}]
    task_results: dict                           # {task_idx (int): result_dict}
    plan_round:   int                            # 1-based cycle counter (reset per Q)
    final_answer: str                            # populated when done
    done:         bool
    needs_replan: bool                           # True -> route joiner back to planner
    verified:     bool                           # True once the verifier pass has run
    adjudicated:  bool                           # True once the adjudicator pass has run


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

    llm         = ChatOpenAI(api_key=api_key, model=model,
                             max_completion_tokens=4096, temperature=0)
    sys_planner = SystemMessage(content=PLANNER_SYSTEM_PROMPT)
    sys_joiner  = SystemMessage(content=JOINER_SYSTEM_PROMPT)

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
        msgs      = [sys_planner] + extra + _window(state["messages"])
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
                "needs_replan": False,
                "verified":     False,
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
            "needs_replan": False,
            "verified":     False,
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

            submissions = sum(plan_samples(t.subquestion, ctx.current_points)
                              for t in ready)
            n_workers = min(submissions, MAX_WORKERS)
            print(f"\n[SH EXECUTOR] dispatching {len(ready)} task(s), "
                  f"{submissions} worker run(s) ({n_workers} parallel slot(s))")

            parent_run_tree = get_current_run_tree()
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as exe:
                futures: dict = {}
                for t in ready:
                    subq = substitute_deps(t.subquestion, completed)
                    if ctx.q_handoffs:
                        subq += ("\n\nCONTEXT FROM PRIOR ATTEMPTS ON THIS QUESTION "
                                 "(resume the hunt, do not restart it):\n"
                                 + "\n\n".join(ctx.q_handoffs[-HANDOFF_KEEP:]))
                    n = plan_samples(t.subquestion, ctx.current_points)
                    if n > 1:
                        print(f"[SH EXECUTOR] metrics task {t.idx}: sampling {n}x "
                              f"(temperature 0.3, majority vote)")
                    for _s in range(n):
                        worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
                        print(f"\n[SH -> SENIOR #{worker_idx}  task={t.idx}]\n{subq[:300]}")
                        futures[exe.submit(_run_senior, ctx, subq, worker_idx,
                                           parent_run_tree,
                                           sample=(n > 1))] = (t, worker_idx, subq)

                per_task: dict[int, list] = {}
                # A sampled [METRICS] task (plan_samples>1) dispatches up to 3
                # futures for the SAME t.idx — count/hand-off its failure at
                # most once per task per round, not once per failing sample.
                counted_failed_idx: set[int] = set()
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
                    per_task.setdefault(t.idx, []).append(result)

                    if (result["status"] in ("too_big", "failed")
                            or result.get("cap_hit")):
                        if t.idx not in counted_failed_idx:
                            if result["status"] in ("too_big", "failed"):
                                ctx.failed_delegations += 1
                            ctx.q_handoffs.append(build_handoff_digest(
                                {**result, "worker": f"senior#{worker_idx}"}))
                            counted_failed_idx.add(t.idx)

                    record = _delegation_record(worker_idx, ctx.current_qid, subq, result)
                    ctx.q_delegations.append(record)
                    ctx.all_delegations.append(record)

                    ctx.logger.timeline(
                        f"- **Senior #{worker_idx}**  _[{result['status']}]_  task={t.idx}\n"
                        f"    - subquestion: {subq[:200]}\n"
                        f"    - answer: {(result['answer'] or '').strip()[:400]}\n"
                        f"    - SPL: {result['spl_used']}"
                    )

                for idx_, res_list in per_task.items():
                    if len(res_list) > 1:
                        winner = majority_answer(res_list)
                        if winner is not None:
                            print(f"[SH EXECUTOR] task {idx_}: majority vote -> "
                                  f"{(winner.get('answer') or '')[:120]!r}")
                        completed[idx_] = winner or res_list[0]
                    else:
                        completed[idx_] = res_list[0]

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
            # run_1.2 ground-checked (and verifier-refuted) answers against Q200's
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
                    "tasks":        [{"idx": t.idx, "subquestion": t.subquestion,
                                      "deps": t.deps} for t in replan_tasks],
                    "task_results": {},
                    "plan_round":   plan_round + 1,
                    "done":         False,
                }

        # Fallback — joiner produced neither a usable FINAL ANSWER nor a runnable
        # replan (typically: REPLAN requested with rounds exhausted). Prefer the
        # best real worker answer from ANY round of this question over joiner
        # prose — run_1.2's Q200 submitted the last line of a replan plan (a task
        # description) because this branch grabbed jtext's last line.
        cand = best_candidate({i: {"answer": d.get("answer"), "status": d.get("status")}
                               for i, d in enumerate(ctx.q_delegations)})
        if cand:
            print("[SH JOINER] no FINAL/REPLAN available — falling back to best worker answer")
            answer = cand
        else:
            print("[SH JOINER] no FINAL ANSWER / REPLAN tag — extracting from last line")
            lines  = [l.strip() for l in jtext.splitlines() if l.strip()]
            answer = lines[-1] if lines else jtext[:200]
        return {
            "messages":     [joiner_hm, response],
            "plan_text":    jtext,
            "final_answer": answer,
            "done":         True,
        }

    # ── Verifier (>=500pt prove-or-refute pass, runs at most once per question) ─
    def verifier_node(state: SHState) -> dict:
        answer = state.get("final_answer", "")
        # ctx.current_question, NOT state["messages"] (see joiner grounding note).
        qtext  = ctx.current_question

        verify_subq = (
            f"{VERIFIER_SYSTEM_PROMPT}\n\n"
            f"Original question: {qtext}\n"
            f"Candidate answer to verify: {answer}"
        )

        worker_idx      = ctx.logger.next_worker("senior", ctx.current_qid)
        parent_run_tree = get_current_run_tree()
        print(f"\n[SH -> VERIFIER #{worker_idx}]  candidate={answer!r}")
        try:
            result = _run_senior(ctx, verify_subq, worker_idx, parent_run_tree,
                                 max_iter=VERIFIER_MAX_ITER)
        except Exception as exc:
            print(f"[SH VERIFIER] VERIFIER FAILED (crashed: {exc}) — keeping original answer")
            _emit = getattr(ctx.logger, "events", None)
            if _emit:
                _emit.emit("verifier_failed", qid=ctx.current_qid, error=str(exc)[:200])
            return {"verified": True, "done": True}

        if result.get("status") in ("failed", "too_big") or result.get("cap_hit"):
            # Verifier couldn't do its <=3-query job — do NOT let it override
            # anything; keep the answer, flag loudly for post-run review.
            print(f"[SH VERIFIER] VERIFIER FAILED (status={result.get('status')}, "
                  f"cap_hit={result.get('cap_hit')}) — keeping original answer")
            _emit = getattr(ctx.logger, "events", None)
            if _emit:
                _emit.emit("verifier_failed", qid=ctx.current_qid,
                           status=result.get("status"), cap_hit=result.get("cap_hit"))
            return {"verified": True, "done": True}

        verdict = parse_verifier_verdict(result.get("answer", ""))
        print(f"[SH VERIFIER OUTPUT] verdict={verdict['verdict']} "
              f"correction={verdict.get('correction')!r}")

        if ctx.case_file and ctx.use_case_file:
            promote_from_verdict(ctx.case_file, answer, verdict)

        record = _delegation_record(worker_idx, ctx.current_qid, verify_subq, result)
        ctx.q_delegations.append(record)
        ctx.all_delegations.append(record)
        ctx.logger.timeline(
            f"- **Verifier #{worker_idx}**  _[{verdict['verdict']}]_\n"
            f"    - candidate: {answer}\n"
            f"    - result: {(result.get('answer') or '').strip()[:400]}"
        )

        if verdict["verdict"] == "refuted" and verdict.get("correction"):
            task_results = dict(state.get("task_results") or {})
            combined = dict(task_results)
            combined["verifier"] = result
            if is_grounded(verdict["correction"], combined, qtext):
                print(f"[SH VERIFIER] REFUTED — replacing answer "
                      f"{answer!r} -> {verdict['correction']!r}")
                return {"final_answer": verdict["correction"], "verified": True,
                        "done": True}
            print("[SH VERIFIER] REFUTED but correction not grounded — "
                  "keeping original answer")
            return {"verified": True, "done": True}

        # confirmed, or refuted with no usable correction — keep original answer.
        # No replan branch here: verification runs at most once per question so
        # the joiner<->verifier loop always terminates.
        return {"verified": True, "done": True}

    # ── Adjudicator (Plan C: rule-ranked selection over the candidate ledger) ─
    def adjudicator_node(state: SHState) -> dict:
        answer = state.get("final_answer", "")
        ledger = build_ledger(ctx.q_delegations)
        if len(ledger) < ADJUDICATE_MIN_CANDIDATES:
            return {"adjudicated": True}   # nothing to select between

        def _invoke(prompt_text: str) -> str:
            resp = llm.invoke([SystemMessage(content=ADJUDICATOR_SYSTEM_PROMPT),
                               HumanMessage(content=prompt_text)])
            return (resp.content or "").strip()

        print(f"\n[SH ADJUDICATOR]  {len(ledger)} candidate(s), joiner pick={answer!r}")
        verdict = adjudicate_once(_invoke, ctx.current_question,
                                  ctx.current_guidance, ledger)

        # One bounded follow-up per question: a targeted tiebreak query, or —
        # on low-confidence 1000-pt questions — a strong-model escalation run.
        escalate = ctx.current_points >= ESCALATE_MIN_POINTS
        needs_followup = bool(verdict["tiebreak"]) or (
            verdict["confidence"] == "low" and escalate)
        if needs_followup:
            subq = verdict["tiebreak"] or (
                f"{ctx.current_question}\n\nPrior workers produced conflicting "
                f"candidates (below). Independently determine the answer using "
                f"a DIFFERENT approach or sourcetype family — do not just "
                f"re-run their queries.\n\n{render_ledger(ledger)}")
            worker_idx = ctx.logger.next_worker("senior", ctx.current_qid)
            label = "ESCALATION" if escalate else "TIEBREAK"
            print(f"[SH ADJUDICATOR] {label} -> senior#{worker_idx}: {subq[:200]}")
            try:
                result = _run_senior(ctx, subq, worker_idx,
                                     get_current_run_tree(), escalate=escalate)
            except Exception as exc:
                result = None
                print(f"[SH ADJUDICATOR] {label} worker crashed: {exc} — "
                      f"adjudicating on the existing ledger")
            if result is not None:
                record = _delegation_record(worker_idx, ctx.current_qid, subq, result)
                ctx.q_delegations.append(record)
                ctx.all_delegations.append(record)
                ctx.logger.timeline(
                    f"- **Adjudicator {label.lower()} #{worker_idx}**  "
                    f"_[{record['status']}]_\n"
                    f"    - answer: {(record['answer'] or '').strip()[:400]}")
                ledger = build_ledger(ctx.q_delegations)
                verdict = adjudicate_once(_invoke, ctx.current_question,
                                          ctx.current_guidance, ledger)

        chosen = verdict["answer"]
        if not chosen:
            # UNKNOWN / synthesized choice. Q321 hard rule: keep the joiner's
            # answer if it is itself an honest ledger/question value, else take
            # the best honest candidate — never a value from nowhere.
            if resolve_choice(answer, ledger, ctx.current_question):
                chosen = answer
            else:
                chosen = fallback_choice(ledger) or answer
        changed = (chosen != answer)
        print(f"[SH ADJUDICATOR] choice={chosen!r} "
              f"confidence={verdict['confidence']} changed={changed}")
        _emit = getattr(ctx.logger, "events", None)
        if _emit:
            _emit.emit("adjudication", qid=ctx.current_qid, chosen=chosen,
                       confidence=verdict["confidence"], changed=changed,
                       candidates=len(ledger))
        ctx.logger.timeline(
            f"- **Adjudicator**  confidence={verdict['confidence']} "
            f"candidates={len(ledger)}\n"
            f"    - joiner pick: {answer!r}\n"
            f"    - adjudicated: {chosen!r}{'  (CHANGED)' if changed else ''}")
        out: dict = {"adjudicated": True}
        if changed:
            out["final_answer"] = chosen
        return out

    # ── Graph wiring ──────────────────────────────────────────────────────────
    def route_planner(state: SHState) -> str:
        return END if state.get("done") else "executor"

    def route_joiner(state: SHState) -> str:
        if state.get("needs_replan"):
            return "planner"
        if state.get("done"):
            return "adjudicator"
        if state.get("plan_round", 0) >= MAX_PLAN_ROUNDS:
            return END
        if state.get("tasks"):      # replan set new tasks
            return "executor"
        return END

    def route_adjudicator(state: SHState) -> str:
        if _should_verify(ctx) and not state.get("verified"):
            return "verifier"
        return END

    g = StateGraph(SHState)
    g.add_node("planner",     planner_node)
    g.add_node("executor",    executor_node)
    g.add_node("joiner",      joiner_node)
    g.add_node("adjudicator", adjudicator_node)
    g.add_node("verifier",    verifier_node)
    g.set_entry_point("planner")
    g.add_conditional_edges("planner",  route_planner,
                            {"executor": "executor", END: END})
    g.add_edge("executor", "joiner")
    g.add_conditional_edges("joiner",   route_joiner,
                            {"executor": "executor", "planner": "planner",
                             "adjudicator": "adjudicator", END: END})
    g.add_conditional_edges("adjudicator", route_adjudicator,
                            {"verifier": "verifier", END: END})
    g.add_edge("verifier", END)

    if checkpoint_db_path:
        conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    else:
        checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer), checkpointer


def _run_senior(ctx: DelegationContext, subquestion: str, idx: int, parent_run_tree,
                max_iter: int | None = None, sample: bool = False,
                escalate: bool = False) -> dict:
    """Submit one Senior worker task (called from ThreadPoolExecutor thread).

    contextvars (which LangSmith's tracing relies on) don't propagate into a
    fresh ThreadPoolExecutor thread, so without this the worker's whole trace
    would show up as a disconnected root trace instead of nesting under the
    SH's trace. `parent_run_tree` is captured in the main thread (where the
    contextvar is still populated) and re-applied here.
    """
    with tracing_context(parent=parent_run_tree):
        return ctx.pool.run_senior(subquestion, ctx.current_qid, idx,
                                   points=ctx.current_points, max_iter=max_iter,
                                   sample=sample, escalate=escalate)


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
            "needs_replan": False,
            "verified":     False,
            "adjudicated":  False,
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
