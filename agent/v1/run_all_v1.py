#!/usr/bin/env python3
"""
v1.1 multi-agent runner for BOTSv3 — LLMCompiler edition.

  SH (GPT-5.4, persistent memory, LLMCompiler planner+executor+joiner)
    -> parallel Senior Splunk workers (zai-org/GLM-5.3 via AI&)
    -> scoreboard (1x)

There is no extractor tier: the joiner's FINAL ANSWER is already the bare
value, and over 84 recorded extractions the tier's net score effect was zero.

The SH plans a DAG of tasks and dispatches independent tasks concurrently via
ThreadPoolExecutor (up to 6 parallel Senior workers, backed by SplunkConnectionPool).
Dependent tasks ($N refs) wait for their prerequisites before running. The Joiner
synthesizes all findings or requests one replan round if a critical datum is missing.

Per-step traces (LLM calls, tool calls, node visits) are sent to LangSmith
automatically when LANGSMITH_TRACING=true and LANGSMITH_API_KEY are set in .env.
Each run creates its own LangSmith project (botsv3-run_1.x or botsv3-test_<ts>).

Usage (from project root or agent/v1/):
    python agent/v1/run_all_v1.py                 # FULL run  -> log/v1/run_1.<n>/
    python agent/v1/run_all_v1.py --ids Q1,Q205   # TEST run  -> log/temp/<ts>/
    python agent/v1/run_all_v1.py --limit 5       # TEST run  -> log/temp/<ts>/
    python agent/v1/run_all_v1.py --start Q210    # resume a full run from a question id

Any use of --ids or --limit marks the run as a TEST run (output under log/temp, never
logged as a versioned run, never cost-tracked).
"""

import argparse
import json
import os
import subprocess
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))     # agent/v1
AGENT_DIR    = os.path.dirname(SCRIPT_DIR)                    # agent
PROJECT_ROOT = os.path.dirname(AGENT_DIR)
for p in (AGENT_DIR, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import resume
import sh_memory
from agent_logger import RunLogger
from case_file import CaseFile, build_ledger, finalize_answer, reconcile_findings
from conversation import UNANSWERABLE_VALUE
from dotenv import load_dotenv
from finding import answer_shaped
from grounding import best_candidate, is_grounded
from hint_client import HintBook
from hitl import RunPaused
from local_scoreboard import LocalScoreboard
from orchestrator import DelegationContext, build_sh_agent_compiler, run_sh
from premise import dump_ledgers, dump_question_ledger
from sh_loop import NO_ANSWER, run_question
from splunk_pool import SplunkConnectionPool
from splunk_subagent import SplunkWorkerPool
from usage_tracker import UsageTracker

# ── Models ───────────────────────────────────────────────────────────────────────
SH_MODEL         = "gpt-5.4"
# The Senior is GLM-5.3 on AI&. The three values move together: changing the
# model alone would send `zai-org/glm-5.3` to OpenAI.
SENIOR_MODEL       = "zai-org/glm-5.3"
SENIOR_BASE_URL    = "https://api.aiand.com/v1"
SENIOR_API_KEY_ENV = "AI_AND_API_KEY"
DUAL_TRACK_MIN_POINTS = 1000   # C2: 1000-pt questions get two orthogonal plan tracks

load_dotenv(os.path.join(AGENT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SPLUNK_HOST    = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER    = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS    = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


def force_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 with error replacement.

    On Windows, the console is often cp1252 ('charmap'). Any print() of a
    Unicode character outside that codec (e.g. the arrow U+2192, em-dashes)
    raises UnicodeEncodeError and kills the process mid-run. Reconfiguring
    the streams here fixes every print() call at once instead of hunting
    down each non-ASCII character across the codebase.
    """
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def build_sh_message(qid, qtext, guidance, points=0):
    lines = [f"New question — {qid}.", f"Question: {qtext}"]
    if guidance:
        lines.append(f"Answer format guidance: {guidance}")
    if points >= DUAL_TRACK_MIN_POINTS:
        lines.append(
            "DUAL-TRACK: this is a 1000-point question. Produce TWO orthogonal "
            "task tracks that attack it via DIFFERENT sourcetype families or "
            "approaches (2-3 tasks each). At least one task must enumerate the "
            "whole candidate population UNFILTERED (e.g. `stats count by "
            "<entity>` / `stats sum(bytes) by Username`) before any track "
            "narrows to a specific lead. Keep tracks $N-independent so they "
            "run in parallel."
        )
    lines.append(
        "Write your PLAN block, then produce your TASKS list. "
        "Scan your memory for relevant prior findings (hosts, IPs, usernames, bucket names, "
        "time windows, sourcetypes) and embed that context in every task you write."
    )
    return "\n".join(lines)


def build_metrics_row(*, qid, points, verdict, earned, clean_answer, delegations,
                      stage_ms, usage_by_role, question_text="", hint_cost=0,
                      usage_by_worker=None):
    """Assemble one per-question metrics row (pure data — unit-testable).

    `grounded` reuses grounding.is_grounded (component-wise for comma-joined
    list answers) so this diagnostic agrees with the actual gate the joiner
    used to accept the answer — a second, naive whole-string copy of this
    check previously reported every correct list answer as "ungrounded".
    """
    task_results = {i: {"answer": d.get("answer")} for i, d in enumerate(delegations)}
    grounded = is_grounded(clean_answer, task_results, question_text)
    statuses = [d.get("status", "?") for d in delegations]
    cap_hits = sum(1 for d in delegations if d.get("cap_hit"))
    total_ms = sum(stage_ms.values())
    worker_s = {d.get("worker") or f"senior#?{i}": round(d.get("duration_s", 0.0), 1)
                for i, d in enumerate(delegations)}
    return {
        "qid": qid,
        "points": points,
        "verdict": verdict,
        "earned": earned,
        "clean_answer": clean_answer,
        "grounded": grounded,
        "hint_cost": hint_cost,
        "delegations": len(delegations),
        "statuses": statuses,
        "cap_hits": cap_hits,
        "latency_s": {
            "total": round(total_ms / 1000, 1),
            **{k: round(v / 1000, 1) for k, v in stage_ms.items()},
            # Per-worker wall time, and its sum. worker_total > sh means the
            # fan-out really overlapped; worker_total ~= sh means it did not.
            "worker_total": round(sum(worker_s.values()), 1),
            "workers": worker_s,
        },
        "cost_by_role": {r: round(v.get("estimated_usd", 0.0), 6)
                         for r, v in usage_by_role.items()},
        # One row per senior/validator/scout. cost_by_role cannot say WHICH worker
        # spent a question's senior budget, which is the only question worth asking
        # of it when one worker runs away or a provider caches unevenly.
        "cost_by_worker": {w: {"usd": round(v.get("estimated_usd", 0.0), 6),
                               "in": v.get("input_tokens", 0),
                               "cached": v.get("cached_tokens", 0),
                               "out": v.get("output_tokens", 0),
                               "cache_hit_pct": v.get("cache_hit_pct", 0.0)}
                           for w, v in sorted((usage_by_worker or {}).items())},
    }


def fallback_answer(sh_answer: str, delegations: list) -> str:
    """Used when SH produced nothing submittable — prefer a real worker's
    answer (best_candidate, same ranking the joiner's own ungrounded-fallback
    uses) over blindly taking the last line of sh_answer, which can be raw
    multi-line prose when sh_answer came from decide_joiner_answer's
    best_candidate fallback rather than a single-line FINAL ANSWER tag.

    Schema B's `value` is preferred over the prose `answer` for the same reason
    the ledger prefers it: `value` is the bare answer the worker committed to,
    while `answer` is its whole terminal message. Falling back to prose put
    3,316 characters of narration on the scoreboard in test_20260907_132802."""
    task_results = {i: {"answer": (d.get("value") or "").strip() or d.get("answer"),
                        "status": d.get("status")}
                    for i, d in enumerate(delegations)}
    cand = best_candidate(task_results)
    if cand:
        return cand
    stripped = (sh_answer or "").strip()
    return stripped.splitlines()[-1].strip() if stripped else ""


def upsert_metrics_row(rows: list, row: dict) -> None:
    """Replace-or-append `row` in `rows` keyed by qid (in place).

    Idempotent per question: if a crash left a stale row in metrics.json and
    the question is reprocessed after resume, the stale row is replaced instead
    of duplicated (a duplicate would also poison the summary's index lookup,
    which takes the first match by qid).
    """
    qid = row.get("qid")
    rows[:] = [m for m in rows if m.get("qid") != qid]
    rows.append(row)


def seed_resume_results(prior: dict, questions_dir: str) -> list:
    """Rebuild the `results` list from a prior run_summary.json on resume.

    New schema (v1.2+): summary carries an `index` list and the heavy records
    live in questions/<qid>.json — reload each one (skipping any file a crash
    prevented from being written). Old schema (run_1.0/run_1.1): no `index`
    key, the full `results` array is embedded in the summary — use it directly.
    """
    if prior.get("index") is not None:
        results = []
        for entry in prior["index"]:
            qpath = os.path.join(questions_dir, f"{entry['id']}.json")
            if os.path.exists(qpath):
                with open(qpath, "r", encoding="utf-8") as qf:
                    results.append(json.load(qf))
        return results
    return prior.get("results", [])


def memory_answer(clean: str, sh_answer: str) -> str:
    """What the memory card says was submitted: the value, or why there was none."""
    if clean:
        return clean
    if sh_answer.strip() == UNANSWERABLE_VALUE:
        return UNANSWERABLE_VALUE
    return "NO_ANSWER" if sh_answer.strip() in ("", NO_ANSWER) else "NO_ANSWER (unshaped)"


def main():
    force_utf8_stdio()

    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", default=None,
                        help="Comma-separated question ids to run (e.g. Q1,Q205). Marks a TEST run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N questions. Marks a TEST run.")
    parser.add_argument("--start", default=None, help="Resume a full run from this question id.")
    parser.add_argument("--senior-model", default=None,
                        help="Override the Senior worker model (e.g. openai/gpt-oss-120b).")
    parser.add_argument("--senior-base-url", default=SENIOR_BASE_URL,
                        help=f"Base URL for Senior's API (default: {SENIOR_BASE_URL}). "
                             "Pass an empty string to use OpenAI.")
    parser.add_argument("--senior-api-key-env", default=SENIOR_API_KEY_ENV,
                        help="Name of the env var holding the Senior API key "
                             f"(default: {SENIOR_API_KEY_ENV}; use OPENAI_API_KEY for an OpenAI Senior).")
    parser.add_argument("--run-name", default=None,
                        help="Reuse an existing temp run dir (e.g. test_20260630_144242). Appends to its timeline.md.")
    parser.add_argument("--recon", action="store_true",
                        help="Run the Phase-0 recon pass before the question loop (seeds the case file).")
    parser.add_argument("--hints", action="store_true",
                        help="Buy official hint 1 on ungrounded >=500pt answers (cost deducted from earned points).")
    parser.add_argument("--loop", default="conversational",
                        choices=["conversational", "compiler"],
                        help="conversational: the v1.4 SH<->Senior conversation "
                             "(default on this branch). compiler: the v1.3.0 "
                             "planner/executor/joiner loop, kept for A/B.")
    parser.add_argument("--memory-threshold", type=int, default=sh_memory.MEMORY_THRESHOLD,
                        help="SH prompt tokens above which the oldest past questions are "
                             "swapped for their summaries (default: 60%% of 272K). Set low "
                             "on a smoke run so the swap fires within 5 questions.")
    args = parser.parse_args()

    senior_model    = args.senior_model or SENIOR_MODEL
    senior_base_url = args.senior_base_url or None  # "" or None -> OpenAI
    senior_api_key  = os.getenv(args.senior_api_key_env, "")
    nim_api_key     = os.getenv("NIM_API_KEY", "")

    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set — check .env")
    if not senior_api_key:
        sys.exit(f"{args.senior_api_key_env} not set — check .env  "
                 f"(Senior model={senior_model}, base_url={senior_base_url})")
    if not nim_api_key:
        sys.exit("NIM_API_KEY not set — check .env (exploration runs on NIM)")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set — check .env")

    questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(ANSWERS_PATH, "r", encoding="utf-8"))}

    id_filter = None
    if args.ids:
        id_filter = {s.strip() for s in args.ids.split(",") if s.strip()}
    full_run = (id_filter is None) and (args.limit is None)

    # --start on a full run without --run-name would allocate a NEW run_1.x dir,
    # stranding the prior segment's results, checkpoints, and SH memory.
    if full_run and args.start and not args.run_name:
        sys.exit("--start on a full run requires --run-name <existing run dir> "
                 "so the resumed segment lands in the same run (e.g. --run-name run_1.2).")

    selected = []
    started  = args.start is None
    for q in questions:
        if id_filter is not None:
            if q["id"] in id_filter:
                selected.append(q)
            continue
        if not started:
            if q["id"] == args.start:
                started = True
            else:
                continue
        selected.append(q)
    if args.limit is not None:
        selected = selected[:args.limit]

    logger  = RunLogger(full_run=full_run, version_major=1, run_name=args.run_name)
    case_file = CaseFile(os.path.join(logger.run_dir, "case_file.json"))
    tracker = UsageTracker()

    # Each run gets its own LangSmith project, named after the run so traces
    # don't pile into one shared project (full runs: botsv3-run_1.x; test
    # runs: botsv3-test_<ts>). LANGSMITH_PROJECT takes precedence over the
    # legacy LANGCHAIN_PROJECT variable.
    os.environ["LANGSMITH_PROJECT"] = f"botsv3-{logger.run_name}"

    run_label = "FULL RUN" if full_run else "TEST RUN"

    print(f"Connecting to Splunk at {SPLUNK_HOST} (pool size=6) ...")
    splunk     = SplunkConnectionPool(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS, size=6)
    scoreboard = LocalScoreboard(
        questions_csv=os.path.join(PROJECT_ROOT, "datasets", "botsv3", "ctf_questions.csv"),
        answers_csv=os.path.join(PROJECT_ROOT, "datasets", "botsv3", "ctf_answers.csv"),
        results_path=os.path.join(logger.run_dir, "scoreboard_submissions.json"),
    )
    hint_book = HintBook(os.path.join(PROJECT_ROOT, "datasets", "botsv3", "ctf_hints.csv")) if args.hints else None
    print(f"Connected.  {splunk}")

    pool      = SplunkWorkerPool(splunk, senior_api_key=senior_api_key,
                                 senior_model=senior_model,
                                 senior_base_url=senior_base_url,
                                 # Exploration runs on NIM. Without a key an
                                 # exploration spawn degrades to an ordinary
                                 # Senior rather than failing the question.
                                 exploration_api_key=nim_api_key,
                                 exploration_base_url=NIM_BASE_URL,
                                 tracker=tracker,
                                 )
    ctx       = DelegationContext(pool, logger, case_file=case_file)
    # SQLite-backed so cross-question memory survives a killed/resumed process
    # (same --run-name -> same run_dir -> same checkpoint file picked back up).
    checkpoint_db_path = os.path.join(logger.run_dir, "sh_checkpoints.sqlite")
    sh_graph, _ = build_sh_agent_compiler(OPENAI_API_KEY, SH_MODEL, ctx,
                                          checkpoint_db_path=checkpoint_db_path)

    # The conversational loop drives one structured-output model directly rather
    # than a graph: its routing decision is a validated object, and its memory is
    # the message list run_question carries per question plus the case file.
    from conversation import SHTurn
    from langchain_openai import ChatOpenAI
    from llm_errors import resilient_http_client
    from plan_schema import load_manifest, render_briefing

    sh_llm = ChatOpenAI(
        api_key=OPENAI_API_KEY, model=SH_MODEL, max_completion_tokens=4096,
        temperature=0, timeout=90.0, max_retries=3,
        http_client=resilient_http_client(),
    ).with_structured_output(SHTurn, method="json_schema", strict=True)
    try:
        briefing = render_briefing(load_manifest())
    except (OSError, ValueError) as exc:
        print(f"[SH] dataset briefing unavailable ({exc}) — running without it")
        briefing = ""
    # SH's cross-question memory for the conversational loop: {qid: [messages]},
    # rendered each question with the per-question summaries (sh_memory, v1.4.5).
    # Persisted per question (resume.py), so a resumed process renders the same
    # memory SH had, not an empty one.
    sh_history: dict = resume.load_history(logger.run_dir)
    # The summarizer: one call per finished question, costed under role `memory`.
    memory_llm = ChatOpenAI(
        api_key=OPENAI_API_KEY, model=sh_memory.SUMMARIZER_MODEL,
        max_completion_tokens=4096, temperature=0, timeout=120.0, max_retries=3,
        http_client=resilient_http_client(),
    ).with_structured_output(sh_memory.Digest, method="json_schema", strict=True)

    run_thread = f"sh_{logger.run_name}"
    ls_project = os.environ["LANGSMITH_PROJECT"]
    senior_provider = senior_base_url or "OpenAI"
    print(f"\n{run_label}  [{logger.run_name}]")
    print(f"  SH={SH_MODEL}  Senior={senior_model} ({senior_provider})")
    print(f"  Questions: {len(selected)}   Log dir: {logger.run_dir}")
    print(f"  LangSmith project: {ls_project}")
    print("=" * 80)

    results              = []
    # qid -> PremiseLedger. Dumped once at the end of the run: spec 2's
    # calibration reads each premise's status HISTORY, which the per-question
    # reports cannot recover after the fact.
    ledgers: dict        = {}
    metrics_rows         = []
    total_points         = 0
    earned_pts           = 0
    summary_path         = os.path.join(logger.run_dir, "run_summary.json")
    metrics_path         = os.path.join(logger.run_dir, "metrics.json")
    questions_dir        = os.path.join(logger.run_dir, "questions")
    os.makedirs(questions_dir, exist_ok=True)

    # Resume support: pick up where a killed/interrupted process left off
    # instead of overwriting run_summary.json with just this segment's data.
    resumed = False
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            prior = json.load(f)
        total_points         = prior.get("total", 0)
        earned_pts           = prior.get("score", 0)
        ctx.failed_delegations = prior.get("failed_delegations", 0)
        tracker.seed(prior.get("token_usage"))
        resumed = True
        # Heavy per-question records live under questions/<qid>.json (new
        # schema, via the summary's index); old-schema summaries (run_1.0/1.1)
        # embed the full results array directly — handle both.
        results = seed_resume_results(prior, questions_dir)
        print(f"Resuming {logger.run_name}: {len(results)} question(s) already "
              f"recorded, {earned_pts}/{total_points} pts so far.")

    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_rows = json.load(f)

    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        git_sha = "unknown"
    logger.events.emit(
        "run_start", git_sha=git_sha, full_run=full_run,
        models={"sh": SH_MODEL, "senior": senior_model},
        langsmith_project=ls_project, questions=len(selected), resumed=resumed,
    )

    # Never re-run (and double-count) a question already recorded in this run dir.
    done_ids = {r["id"] for r in results}

    if args.recon:
        already = any(f.get("source_qid") == "RECON"
                      for f in case_file.iter_findings())
        if already:
            print("[RECON] case file already seeded — skipping (resume).")
        else:
            from recon import run_recon, seed_case_from_recon
            print("[RECON] Phase-0 incident recon ...")
            recon_results = run_recon(ctx)
            seeded = seed_case_from_recon(case_file, recon_results)
            logger.events.emit("recon_done", findings=seeded,
                               tasks=len(recon_results))
            print(f"[RECON] seeded {seeded} verified finding(s).")

    for q in selected:
        qid      = q["id"]
        if qid in done_ids:
            print(f"[{qid}] already recorded in {logger.run_name} — skipping.")
            continue
        qtext    = q["question"]
        points   = q.get("base_points", 0)
        guidance = q.get("answer_guidance", "") or ""
        q_number = q.get("number", int(qid.replace("Q", "")))
        correct  = (answers.get(qid, {}) or {}).get("answer", "") or ""
        total_points += points

        ctx.reset_question(qid, points=points, question=qtext, guidance=guidance)
        tracker.reset_sh_question()
        logger.timeline_question_header(qid, qtext, points)
        print(f"\n{'-'*80}\n[{qid}]  {points} pts  |  {qtext[:90]}")
        logger.events.emit("question_start", qid=qid, points=points)
        stage_ms = {}

        # ── SH solves the question ────────────────────────────────────────────────
        conv = {}
        sh_llm_bound = None
        with logger.events.timer() as t_sh:
            if args.loop == "conversational":
                # Bare sh_llm.invoke() never reaches the tracker (run_question
                # calls llm.invoke(msgs) with no config) — bind tracker/tags/
                # metadata onto the model itself so every SH call this question
                # is costed, same as run_sh's config= does for the compiler graph.
                sh_llm_bound = sh_llm.with_config({
                    "callbacks": [tracker], "tags": ["SH", qid],
                    "metadata": {"role": "SH", "qid": qid},
                    "run_name": f"SH-{qid}",
                })
                conv = run_question(
                    llm=sh_llm_bound, pool=pool, qid=qid, question=qtext,
                    guidance=guidance, points=points, run_dir=logger.run_dir,
                    case_file=case_file, dataset_briefing=briefing,
                    delegations=ctx.q_delegations, history=sh_history,
                    memory_threshold=args.memory_threshold,
                )
                ledgers[qid] = conv["ledger"]
                sh_answer = conv["answer"]
                ctx.all_delegations.extend(ctx.q_delegations)
                print(f"[SH CONV] {qid}: end={conv['end_reason']}  "
                      f"turns={conv['turns']}  waves={conv['waves']}  "
                      f"iterations={conv['senior_iterations']}/{conv['ceiling']}  "
                      f"compactions={conv['compactions']}")
            else:
                sh_answer, _ = run_sh(
                    sh_graph,
                    build_sh_message(qid, qtext, guidance, points=points),
                    run_thread,
                    qid=qid,
                    run_name=f"SH-{qid}",
                    tracker=tracker,
                    run_dir=logger.run_dir,
                )
        stage_ms["sh"] = t_sh.ms

        # ── The answer SH already produced ───────────────────────────────────────
        # There is no extractor tier any more. The joiner's FINAL ANSWER line is
        # already the bare value - orchestrator.py strips the tag and keeps line
        # one - so there was nothing left to normalise. Measured over the 84
        # recorded extractions, the tier saved one answer, destroyed one
        # ('1368' -> '2085', where 1368 was correct), and changed nothing in 57.
        # Net zero, for a model dependency that twice put catastrophic text on
        # the scoreboard.
        if args.loop == "conversational":
            # run_question's `answer` is SH's accepted ANSWER or its honest
            # NO_ANSWER marker — never a senior value SH declined to submit.
            # Routing it through fallback_answer() would risk picking a
            # delegation's `answer` field, which for conversational records is
            # the whole markdown report, not a bare value — never submit that.
            if sh_answer.strip() == UNANSWERABLE_VALUE:
                # SH ended the question because a senior proved, with a quote, that the
                # value is not readable by anything here (Q217/Q329: pixels in a base64
                # image). Scores zero either way; recorded distinctly so the run record
                # separates "could not hunt" from "could not read".
                clean = ""
                print(f"[SH CONV] {qid}: unanswerable with current capabilities — "
                      "submitting blank")
                logger.events.emit("sh_conv_unanswerable", qid=qid)
            elif answer_shaped(sh_answer):
                clean = sh_answer
            else:
                clean = ""
                if sh_answer:
                    print(f"[SH CONV] answer not submittable ({sh_answer[:60]!r}); "
                          "leaving blank rather than submitting report text")
                    logger.events.emit("sh_conv_answer_unshaped", qid=qid)
        else:
            clean = sh_answer
            if not sh_answer:
                # run_sh returned its failure sentinel (it logged the reason).
                clean = fallback_answer(sh_answer, ctx.q_delegations)
                print("[SH] FAILED for this question; falling back to best worker answer")
                logger.events.emit("sh_failed", qid=qid)
            elif not answer_shaped(sh_answer):
                # SH emitted something unsubmittable - a REPLAN block, a paragraph,
                # a bare "?". A real worker's value beats it. This is the one case
                # the extractor ever genuinely rescued (Q332, a REPLAN block that
                # still contained the CVE), now handled without a model.
                clean = fallback_answer(sh_answer, ctx.q_delegations)
                print(f"[SH] answer not submittable ({sh_answer[:60]!r}); "
                      "falling back to best worker answer")
                logger.events.emit("sh_answer_unshaped", qid=qid)
        clean = finalize_answer(clean, ctx.q_delegations)
        print(f"[SH FINAL] clean={clean!r}")

        # ── Hint economy: ungrounded >=500pt answer buys official hint 1 ─────────
        hint_cost = 0
        hint_conv: dict = {}
        if hint_book and points >= 500:
            tr = {i: {"answer": d.get("answer")} for i, d in enumerate(ctx.q_delegations)}
            if not is_grounded(clean, tr, qtext):
                hint = hint_book.get_hint(q_number, 1)
                if hint:
                    hint_cost = hint["cost"]
                    print(f"[HINT] buying hint 1 for {qid} (cost {hint_cost}): {hint['text']!r}")
                    logger.events.emit("hint_bought", qid=qid, cost=hint_cost)
                    if args.loop == "conversational":
                        # Same loop, same llm binding/history/case file — a
                        # bare run_sh(sh_graph, ...) here would run the v1.3.0
                        # compiler SH mid-experiment. run_dir is nested under
                        # "hint" so its conversation artifacts don't overwrite
                        # the first pass's.
                        n_before = len(ctx.q_delegations)
                        with logger.events.timer() as t_hint:
                            hint_result = run_question(
                                llm=sh_llm_bound, pool=pool, qid=qid, question=qtext,
                                guidance=(f"{guidance}\nOFFICIAL HINT (cost {hint_cost} "
                                          f"pts, already paid): {hint['text']}"),
                                points=points,
                                run_dir=os.path.join(logger.run_dir, "hint"),
                                case_file=case_file, dataset_briefing=briefing,
                                delegations=ctx.q_delegations, history=sh_history,
                                memory_threshold=args.memory_threshold,
                            )
                        ledgers[f"{qid}-hint"] = hint_result["ledger"]
                        stage_ms["hint"] = t_hint.ms
                        ctx.all_delegations.extend(ctx.q_delegations[n_before:])
                        hint_conv = {
                            "end_reason":        hint_result["end_reason"],
                            "turns":             hint_result["turns"],
                            "waves":             hint_result["waves"],
                            "senior_iterations": hint_result["senior_iterations"],
                            "ceiling":           hint_result["ceiling"],
                            "compactions":       hint_result["compactions"],
                        }
                        if answer_shaped(hint_result["answer"]):
                            clean = hint_result["answer"]
                        # else: keep the pre-hint `clean`.
                        clean = finalize_answer(clean, ctx.q_delegations)
                        print(f"[HINT] post-hint clean={clean!r}")
                    else:
                        with logger.events.timer() as t_hint:
                            sh_answer, _ = run_sh(
                                sh_graph,
                                (f"OFFICIAL HINT for {qid} (cost {hint_cost} pts, already "
                                 f"paid): {hint['text']}\nRe-investigate with this hint "
                                 f"and give a corrected FINAL ANSWER."),
                                run_thread, qid=qid, run_name=f"SH-{qid}-hint",
                                tracker=tracker, run_dir=logger.run_dir)
                        stage_ms["hint"] = t_hint.ms
                        clean = sh_answer
                        if not answer_shaped(clean):
                            clean = fallback_answer(sh_answer, ctx.q_delegations)
                        clean = finalize_answer(clean, ctx.q_delegations)
                        print(f"[HINT] post-hint clean={clean!r}")

        # ── Single scoreboard submission ──────────────────────────────────────────
        try:
            sb = scoreboard.submit(q_number, clean)
            pts_earned = sb.earned
            pts_earned = max(0, pts_earned - hint_cost)
            sb_correct = sb.correct
            earned_pts += pts_earned
            verdict = "[CORRECT]" if sb_correct else "[WRONG]"
            demoted = reconcile_findings(case_file, qid, sb_correct)
            if demoted:
                print(f"[CASE] verdict WRONG — demoted {demoted} finding(s) from {qid} to hypothesis")
        except Exception as exc:
            pts_earned, sb_correct = 0, False
            verdict = f"[SB UNAVAILABLE: {exc}]"

        print(f"  Extracted: {clean!r}  ->  {verdict}  ({pts_earned}/{points})")

        # ── SH token report for this question ────────────────────────────────────
        sh_q = tracker.sh_question_tokens()
        sh_tok_line = (
            f"  SH tokens [{qid}]: "
            f"input={sh_q['input_tokens']:,}  "
            f"cached={sh_q['cached_tokens']:,}  "
            f"output={sh_q['output_tokens']:,}  "
            f"est=${sh_q['estimated_usd']:.4f}"
        )
        print(sh_tok_line)

        logger.timeline(
            f"\n**SH FINAL:** `{clean}`  {verdict}  "
            f"(delegations: {len(ctx.q_delegations)}, "
            f"cumulative failed delegations: {ctx.failed_delegations})\n"
            f"\n{sh_tok_line}\n"
        )

        results.append({
            "id":               qid,
            "question":         qtext,
            "base_points":      points,
            "correct_answer":   correct,
            "sh_answer":        sh_answer,
            "clean_answer":     clean,
            "sb_correct":       sb_correct,
            "earned":           pts_earned,
            "hint_cost":        hint_cost,
            "num_delegations":  len(ctx.q_delegations),
            "delegations":      ctx.q_delegations,
            "candidate_ledger": build_ledger(ctx.q_delegations),
            # §4.1: the experiment fails on cost if actuals track the ceiling.
            "loop":              args.loop,
            "end_reason":        conv.get("end_reason", ""),
            "sh_turns":          conv.get("turns", 0),
            "waves":             conv.get("waves", 0),
            "senior_iterations": conv.get("senior_iterations", 0),
            "ceiling":           conv.get("ceiling", 0),
            "compactions":       conv.get("compactions", 0),
            "grades":            conv.get("grades", []),
            "hint_conv":         hint_conv,
        })
        with open(os.path.join(questions_dir, f"{qid}.json"), "w", encoding="utf-8") as f:
            json.dump(results[-1], f, indent=2, ensure_ascii=False)

        # ── SH memory: summarize this question once, before its metrics row, so the
        # summarizer's cost lands in this question's cost_by_role.memory. It is given
        # what SH saw and what SH submitted - never `correct` or the verdict (D3).
        if args.loop == "conversational" and qid in sh_history:
            sh_memory.summarize_question(
                memory_llm.with_config({"callbacks": [tracker], "tags": ["memory", qid],
                                        "metadata": {"role": "memory", "qid": qid},
                                        "run_name": f"memory-{qid}"}),
                run_dir=logger.run_dir, qid=qid, question=qtext, guidance=guidance,
                answer=memory_answer(clean, sh_answer),
                transcript=sh_history[qid], ledger=ledgers.get(qid))

        # ── Events + per-question metrics row ─────────────────────────────────────
        verdict_str = "correct" if sb_correct else "wrong"
        ubr = tracker.by_question().get(qid, {})
        ubw = tracker.by_worker().get(qid, {})
        row = build_metrics_row(
            qid=qid, points=points, verdict=verdict_str, earned=pts_earned,
            clean_answer=clean, delegations=ctx.q_delegations,
            stage_ms=stage_ms, usage_by_role=ubr, usage_by_worker=ubw,
            question_text=qtext,
            hint_cost=hint_cost,
        )
        logger.events.emit("submit", qid=qid, verdict=verdict_str, earned=pts_earned,
                           grounded=row["grounded"], clean=clean)
        logger.events.emit("question_end", qid=qid, **{k: row[k] for k in
                           ("latency_s", "delegations", "statuses", "cap_hits", "cost_by_role")})
        upsert_metrics_row(metrics_rows, row)   # idempotent by qid across resumes
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_rows, f, indent=2, ensure_ascii=False)

        # This question's premises, durable NOW rather than at the end of main().
        # v1.4.3's smoke run lost Q216's and Q217's ledgers outright: the only dump sat
        # past the end of the question loop, outside any try/finally, and a RunPaused
        # from the HITL gate unwound main() before reaching it. Everything else here
        # already survives a resume — metrics, summary, case file, scoreboard, token
        # totals — and the ledger was the one artifact that did not.
        if qid in ledgers:
            dump_question_ledger(logger.run_dir, qid, ledgers[qid])

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version":       1,
                "run":                  logger.run_name,
                "full_run":             full_run,
                "langsmith_project":    ls_project,
                "models":               {"sh": SH_MODEL, "senior": senior_model,
                                          "senior_base_url": senior_base_url or "openai"},
                "score":                earned_pts,
                "total":                total_points,
                "correct":              sum(1 for r in results if r["sb_correct"]),
                "attempted":            len(results),
                "failed_delegations":   ctx.failed_delegations,
                "token_usage":          tracker.totals(),
                "questions_dir":        "questions",
                "index":                [
                    {"id": r["id"], "verdict": "correct" if r["sb_correct"] else "wrong",
                     "earned": r["earned"],
                     "grounded": next((m["grounded"] for m in metrics_rows if m["qid"] == r["id"]), None)}
                    for r in results
                ],
            }, f, indent=2, ensure_ascii=False)

        # Recorded: the question is done, so its turn snapshot is not a resume point
        # any more, and SH's memory now includes it.
        resume.clear(logger.run_dir, qid)
        resume.save_history(logger.run_dir, sh_history)

    # ── Final summary ──────────────────────────────────────────────────────────────
    correct_n  = sum(1 for r in results if r["sb_correct"])
    att        = len(results)
    tok        = tracker.totals()
    tok_total  = tok.get("__total__", {})
    logger.events.emit("run_end", correct=correct_n, attempted=att,
                       score=earned_pts, total=total_points,
                       estimated_usd=tok_total.get("estimated_usd", 0))

    # One file for the whole run. The per-premise status HISTORY is the point, not
    # the end state: the follow-up spec's trigger asks how long a premise sat
    # UNVERIFIED while the candidate held still, and a finished report cannot say.
    # Merged from the per-question files on disk, not from this process's `ledgers`
    # dict — on a resume that dict holds only the segment that just ran, so building
    # the merged view from it would overwrite the earlier segment's premises with
    # fewer of them. The per-question files are the record; this is a convenience view.
    ledger_path = os.path.join(logger.run_dir, "premise_ledger.json")
    n_premises = dump_ledgers(ledger_path, ledgers, run_dir=logger.run_dir)

    print(f"\n{'='*80}\nFINAL — {logger.run_name}  ({run_label})")
    print(f"  Correct           : {correct_n}/{att}"
          f"  ({(correct_n/att*100 if att else 0):.1f}%)")
    print(f"  Points (this run) : {earned_pts}/{total_points}")
    print(f"  Failed delegations: {ctx.failed_delegations}")
    print(f"  Summary JSON      : {summary_path}")
    print(f"  Timeline          : {logger.timeline_path}")
    print(f"  Premise ledger    : {ledger_path}  ({n_premises} premises)")
    print(f"  LangSmith project : {ls_project}")
    print(f"  Total tokens      : {tok_total.get('total_tokens', 0):,}"
          f"  (in={tok_total.get('input_tokens',0):,}"
          f"  cached={tok_total.get('cached_tokens',0):,}"
          f"  out={tok_total.get('output_tokens',0):,})")
    print(f"  Estimated cost    : ${tok_total.get('estimated_usd', 0):.4f}"
          f"  ({tok_total.get('note', '')})")
    print("=" * 80)

    tok_lines = "\n".join(
        f"  - {m}: in={v['input_tokens']:,}  cached={v['cached_tokens']:,}"
        f"  out={v['output_tokens']:,}  est=${v['estimated_usd']:.4f}"
        for m, v in tok.items() if not m.startswith("__")
    )
    logger.timeline(
        f"\n---\n\n## SUMMARY\n\n"
        f"- Correct: {correct_n}/{att}\n"
        f"- Points: {earned_pts}/{total_points}\n"
        f"- Failed delegations: {ctx.failed_delegations}\n"
        f"- LangSmith project: `{ls_project}`\n"
        f"- Token usage:\n{tok_lines}\n"
        f"- Total tokens: {tok_total.get('total_tokens',0):,}"
        f"  estimated ${tok_total.get('estimated_usd',0):.4f}\n"
    )


# Exit code for "paused, awaiting a human decision" - distinct from a crash (1)
# and from success (0), so a supervisor or agent harness can tell them apart.
# 75 is sysexits.h EX_TEMPFAIL: temporary failure, retry later.
EXIT_PAUSED = 75


if __name__ == "__main__":
    try:
        main()
    except RunPaused as paused:
        # Not a crash. State is on disk and the run is resumable with
        # --start <qid> --run-name <same run>; see the decision request.
        bar = "=" * 78
        print("")
        print(bar)
        print(f"[RUN PAUSED] {paused.summary}")
        print(f"  decision request: {paused.request_path}")
        print("  resume with: python agent/v1/run_all_v1.py "
              "--start <qid> --run-name <this run>")
        print(bar)
        sys.exit(EXIT_PAUSED)
