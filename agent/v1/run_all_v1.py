#!/usr/bin/env python3
"""
v1.1 multi-agent runner for BOTSv3 — LLMCompiler edition.

  SH (GPT-5.4, persistent memory, LLMCompiler planner+executor+joiner)
    -> parallel Senior Splunk workers (gpt-5.4-mini via OpenAI)
    -> Extractor (Llama-3.3-70B via NIM, prose-strip only)
    -> scoreboard (1x)

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

import os
import sys
import json
import argparse
import subprocess

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))     # agent/v1
AGENT_DIR    = os.path.dirname(SCRIPT_DIR)                    # agent
PROJECT_ROOT = os.path.dirname(AGENT_DIR)
for p in (AGENT_DIR, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
from splunk_client import SplunkClient
from splunk_pool import SplunkConnectionPool
from local_scoreboard import LocalScoreboard

from agent_logger import RunLogger
from usage_tracker import UsageTracker
from splunk_subagent import SplunkWorkerPool
from extractor import Extractor
from orchestrator import (DelegationContext, build_sh_agent_compiler, run_sh)
from grounding import is_grounded, best_candidate
from case_file import CaseFile, build_ledger, finalize_answer, reconcile_findings
from hint_client import HintBook

# ── Models ───────────────────────────────────────────────────────────────────────
SH_MODEL         = "gpt-5.4"
SENIOR_MODEL     = "gpt-5.4-mini"
ESCALATION_MODEL = "gpt-5.4"   # C3: adjudicator's strong-model track B
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
                      stage_ms, usage_by_role, question_text="", hint_cost=0):
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
        },
        "cost_by_role": {r: round(v.get("estimated_usd", 0.0), 6)
                         for r, v in usage_by_role.items()},
    }


def extractor_fallback_answer(sh_answer: str, delegations: list) -> str:
    """Used when the extractor fails all retries — prefer a real worker's
    answer (best_candidate, same ranking the joiner's own ungrounded-fallback
    uses) over blindly taking the last line of sh_answer, which can be raw
    multi-line prose when sh_answer came from decide_joiner_answer's
    best_candidate fallback rather than a single-line FINAL ANSWER tag."""
    task_results = {i: {"answer": d.get("answer"), "status": d.get("status")}
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
    parser.add_argument("--senior-base-url", default=None,
                        help="Base URL for Senior's API (NIM: https://integrate.api.nvidia.com/v1, "
                             "Vultr: https://api.vultrinference.com/v1). Omit to use OpenAI.")
    parser.add_argument("--senior-api-key-env", default="OPENAI_API_KEY",
                        help="Name of the env var holding the Senior API key "
                             "(default: OPENAI_API_KEY for gpt-5.4-mini).")
    parser.add_argument("--run-name", default=None,
                        help="Reuse an existing temp run dir (e.g. test_20260630_144242). Appends to its timeline.md.")
    parser.add_argument("--recon", action="store_true",
                        help="Run the Phase-0 recon pass before the question loop (seeds the case file).")
    parser.add_argument("--hints", action="store_true",
                        help="Buy official hint 1 on ungrounded >=500pt answers (cost deducted from earned points).")
    args = parser.parse_args()

    senior_model    = args.senior_model or SENIOR_MODEL
    senior_base_url = args.senior_base_url          # None -> OpenAI
    senior_api_key  = os.getenv(args.senior_api_key_env, "")
    nim_api_key     = os.getenv("NIM_API_KEY", "")

    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set — check .env")
    if not senior_api_key:
        sys.exit(f"{args.senior_api_key_env} not set — check .env  "
                 f"(Senior model={senior_model}, base_url={senior_base_url})")
    if not nim_api_key:
        sys.exit("NIM_API_KEY not set — check .env (Extractor runs on NIM)")
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
                                 tracker=tracker,
                                 escalation_api_key=OPENAI_API_KEY,
                                 escalation_model=ESCALATION_MODEL)
    ctx       = DelegationContext(pool, logger, case_file=case_file)
    # SQLite-backed so cross-question memory survives a killed/resumed process
    # (same --run-name -> same run_dir -> same checkpoint file picked back up).
    checkpoint_db_path = os.path.join(logger.run_dir, "sh_checkpoints.sqlite")
    sh_graph, _ = build_sh_agent_compiler(OPENAI_API_KEY, SH_MODEL, ctx,
                                          checkpoint_db_path=checkpoint_db_path)
    extractor = Extractor(nim_api_key, NIM_BASE_URL, tracker=tracker)

    run_thread = f"sh_{logger.run_name}"
    ls_project = os.environ["LANGSMITH_PROJECT"]
    senior_provider = senior_base_url or "OpenAI"
    print(f"\n{run_label}  [{logger.run_name}]")
    print(f"  SH={SH_MODEL}  Senior={senior_model} ({senior_provider})  "
          f"Escalation={ESCALATION_MODEL}  Extractor={extractor.model}(NIM)")
    print(f"  Questions: {len(selected)}   Log dir: {logger.run_dir}")
    print(f"  LangSmith project: {ls_project}")
    print("=" * 80)

    results              = []
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
        models={"sh": SH_MODEL, "senior": senior_model, "extractor": extractor.model},
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
        with logger.events.timer() as t_sh:
            sh_answer, _ = run_sh(
                sh_graph,
                build_sh_message(qid, qtext, guidance, points=points),
                run_thread,
                qid=qid,
                run_name=f"SH-{qid}",
                tracker=tracker,
            )
        stage_ms["sh"] = t_sh.ms

        # ── Extractor: strip prose down to the bare answer ────────────────────────
        with logger.events.timer() as t_ext:
            try:
                clean = extractor.extract(qtext, guidance, sh_answer, qid=qid, expected_shape=guidance)
            except Exception as exc:
                # Extractor outage must not kill the run: fall back to the best
                # worker answer (best_candidate) rather than blindly taking
                # sh_answer's raw last line, which can be unrelated prose when
                # sh_answer came from the joiner's own best_candidate fallback.
                clean = extractor_fallback_answer(sh_answer, ctx.q_delegations)
                print(f"[EXTRACTOR] FAILED after retries ({exc}); falling back to best worker answer")
                logger.events.emit("extract_failed", qid=qid, error=str(exc)[:200])
        stage_ms["extract"] = t_ext.ms
        clean = finalize_answer(clean, ctx.q_delegations)
        print(f"[EXTRACTOR] clean={clean!r}")

        # ── Hint economy: ungrounded >=500pt answer buys official hint 1 ─────────
        hint_cost = 0
        if hint_book and points >= 500:
            tr = {i: {"answer": d.get("answer")} for i, d in enumerate(ctx.q_delegations)}
            if not is_grounded(clean, tr, qtext):
                hint = hint_book.get_hint(q_number, 1)
                if hint:
                    hint_cost = hint["cost"]
                    print(f"[HINT] buying hint 1 for {qid} (cost {hint_cost}): {hint['text']!r}")
                    logger.events.emit("hint_bought", qid=qid, cost=hint_cost)
                    with logger.events.timer() as t_hint:
                        sh_answer, _ = run_sh(
                            sh_graph,
                            (f"OFFICIAL HINT for {qid} (cost {hint_cost} pts, already "
                             f"paid): {hint['text']}\nRe-investigate with this hint "
                             f"and give a corrected FINAL ANSWER."),
                            run_thread, qid=qid, run_name=f"SH-{qid}-hint",
                            tracker=tracker)
                    stage_ms["hint"] = t_hint.ms
                    try:
                        clean = extractor.extract(qtext, guidance, sh_answer,
                                                  qid=qid, expected_shape=guidance)
                    except Exception:
                        clean = extractor_fallback_answer(sh_answer, ctx.q_delegations)
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
            f"\n**SH FINAL → extractor:** `{clean}`  {verdict}  "
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
        })
        with open(os.path.join(questions_dir, f"{qid}.json"), "w", encoding="utf-8") as f:
            json.dump(results[-1], f, indent=2, ensure_ascii=False)

        # ── Events + per-question metrics row ─────────────────────────────────────
        verdict_str = "correct" if sb_correct else "wrong"
        ubr = tracker.by_question().get(qid, {})
        row = build_metrics_row(
            qid=qid, points=points, verdict=verdict_str, earned=pts_earned,
            clean_answer=clean, delegations=ctx.q_delegations,
            stage_ms=stage_ms, usage_by_role=ubr, question_text=qtext,
            hint_cost=hint_cost,
        )
        logger.events.emit("submit", qid=qid, verdict=verdict_str, earned=pts_earned,
                           grounded=row["grounded"], clean=clean)
        logger.events.emit("question_end", qid=qid, **{k: row[k] for k in
                           ("latency_s", "delegations", "statuses", "cap_hits", "cost_by_role")})
        upsert_metrics_row(metrics_rows, row)   # idempotent by qid across resumes
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_rows, f, indent=2, ensure_ascii=False)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version":       1,
                "run":                  logger.run_name,
                "full_run":             full_run,
                "langsmith_project":    ls_project,
                "models":               {"sh": SH_MODEL, "senior": senior_model,
                                          "senior_base_url": senior_base_url or "openai",
                                          "extractor": extractor.model},
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

    # ── Final summary ──────────────────────────────────────────────────────────────
    correct_n  = sum(1 for r in results if r["sb_correct"])
    att        = len(results)
    tok        = tracker.totals()
    tok_total  = tok.get("__total__", {})
    logger.events.emit("run_end", correct=correct_n, attempted=att,
                       score=earned_pts, total=total_points,
                       estimated_usd=tok_total.get("estimated_usd", 0))
    print(f"\n{'='*80}\nFINAL — {logger.run_name}  ({run_label})")
    print(f"  Correct           : {correct_n}/{att}"
          f"  ({(correct_n/att*100 if att else 0):.1f}%)")
    print(f"  Points (this run) : {earned_pts}/{total_points}")
    print(f"  Failed delegations: {ctx.failed_delegations}")
    print(f"  Summary JSON      : {summary_path}")
    print(f"  Timeline          : {logger.timeline_path}")
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


if __name__ == "__main__":
    main()
