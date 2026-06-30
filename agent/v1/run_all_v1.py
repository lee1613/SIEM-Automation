#!/usr/bin/env python3
"""
v1 multi-agent runner for BOTSv3.

  SH (GPT-5.4, persistent memory)  ->  spawn_senior  ->  Senior Splunk worker (gpt-5.4,
  fresh session)  ->  Extractor (Llama-3.3-70B via NIM, format-validate)  ->  scoreboard (1x).

Per-step traces (LLM calls, tool calls, node visits) are sent to LangSmith automatically
when LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY are set in .env. Each run creates its
own LangSmith project (botsv3-run_1.x or botsv3-test_<ts>). Each SH question and each
Senior worker is a named trace filterable in the LangSmith UI.

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

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))     # agent/v1
AGENT_DIR    = os.path.dirname(SCRIPT_DIR)                    # agent
PROJECT_ROOT = os.path.dirname(AGENT_DIR)
for p in (AGENT_DIR, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient

from agent_logger import RunLogger
from splunk_subagent import SplunkWorkerPool
from extractor import Extractor
from orchestrator import (DelegationContext, make_sh_tools, build_sh_agent, run_sh)

# ── Models ───────────────────────────────────────────────────────────────────────
SH_MODEL      = "gpt-5.4"
SENIOR_MODEL  = "gpt-5.4"
NIM_BASE_URL  = "https://integrate.api.nvidia.com/v1"

EXTRACTOR_MAX_RETRIES = 1

load_dotenv(os.path.join(AGENT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NIM_API_KEY    = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST    = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER    = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS    = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")

VULTR_BASE_URL = "https://api.vultrinference.com/v1"
NIM_BASE_URL   = "https://integrate.api.nvidia.com/v1"


def build_sh_message(qid, qtext, guidance):
    lines = [f"New question — {qid}.", f"Question: {qtext}"]
    if guidance:
        lines.append(f"Answer format guidance: {guidance}")
    lines.append(
        "Before delegating, write your PLAN: scan your memory for relevant prior findings "
        "(hosts, IPs, usernames, bucket names, time windows, sourcetypes) and state what "
        "context you will include in the subquestion. Then delegate with that enriched "
        "context and give your FINAL ANSWER in the exact required format."
    )
    return "\n".join(lines)


def main():
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
                        help="Name of the env var holding the Senior API key (default: OPENAI_API_KEY).")
    parser.add_argument("--run-name", default=None,
                        help="Reuse an existing temp run dir (e.g. test_20260630_144242). Appends to its timeline.md.")
    args = parser.parse_args()

    senior_model    = args.senior_model or SENIOR_MODEL
    senior_base_url = args.senior_base_url or None
    senior_api_key  = os.getenv(args.senior_api_key_env, "")

    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set — check .env")
    if not senior_api_key:
        sys.exit(f"{args.senior_api_key_env} not set — check .env")
    if not NIM_API_KEY:
        sys.exit("NIM_API_KEY not set — check .env (needed for the extractor)")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set — check .env")

    questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(ANSWERS_PATH, "r", encoding="utf-8"))}

    id_filter = None
    if args.ids:
        id_filter = {s.strip() for s in args.ids.split(",") if s.strip()}
    full_run = (id_filter is None) and (args.limit is None)

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

    logger = RunLogger(full_run=full_run, version_major=1, run_name=args.run_name)

    # Point LangSmith at a per-run project so every trace is grouped correctly.
    os.environ["LANGCHAIN_PROJECT"] = f"botsv3-{logger.run_name}"

    run_label = "FULL RUN" if full_run else "TEST RUN"

    print(f"Connecting to Splunk at {SPLUNK_HOST} ...")
    splunk     = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    scoreboard = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.")

    pool      = SplunkWorkerPool(splunk, senior_api_key=senior_api_key,
                                 senior_model=senior_model,
                                 senior_base_url=senior_base_url)
    ctx       = DelegationContext(pool, logger)
    sh_tools  = make_sh_tools(ctx)
    sh_graph, _ = build_sh_agent(OPENAI_API_KEY, SH_MODEL, sh_tools)
    extractor = Extractor(NIM_API_KEY, NIM_BASE_URL)

    run_thread = f"sh_{logger.run_name}"
    ls_project = os.environ["LANGCHAIN_PROJECT"]
    senior_provider = senior_base_url or "OpenAI"
    print(f"\n{run_label}  [{logger.run_name}]")
    print(f"  SH={SH_MODEL}  Senior={senior_model} ({senior_provider})  Extractor=Llama-3.3-70B(NIM)")
    print(f"  Questions: {len(selected)}   Log dir: {logger.run_dir}")
    print(f"  LangSmith project: {ls_project}")
    print("=" * 80)

    results              = []
    total_points         = 0
    earned_pts           = 0
    extractor_rejections = 0
    summary_path         = os.path.join(logger.run_dir, "run_summary.json")

    for q in selected:
        qid      = q["id"]
        qtext    = q["question"]
        points   = q.get("base_points", 0)
        guidance = q.get("answer_guidance", "") or ""
        q_number = q.get("number", int(qid.replace("Q", "")))
        correct  = (answers.get(qid, {}) or {}).get("answer", "") or ""
        total_points += points

        ctx.reset_question(qid)
        logger.timeline_question_header(qid, qtext, points)
        print(f"\n{'-'*80}\n[{qid}]  {points} pts  |  {qtext[:90]}")

        # ── SH solves the question ────────────────────────────────────────────────
        sh_answer, _ = run_sh(
            sh_graph,
            build_sh_message(qid, qtext, guidance),
            run_thread,
            qid=qid,
            run_name=f"SH-{qid}",
        )

        # ── Extractor: strip + validate; let SH retry once if format is rejected ─
        ext = extractor.process(qtext, guidance, sh_answer)
        retries = 0
        while not ext["valid"] and retries < EXTRACTOR_MAX_RETRIES:
            retries += 1
            extractor_rejections += 1
            print(f"[EXTRACTOR] rejected -> asking SH to correct (retry {retries})")
            feedback = (
                f"The extractor could not validate your FINAL ANSWER: {ext['reason']}. "
                f"Expected format: {guidance or 'exact value only'}. Re-examine your "
                "findings (delegate again if needed) and give a corrected FINAL ANSWER."
            )
            sh_answer, _ = run_sh(
                sh_graph, feedback, run_thread,
                qid=qid, run_name=f"SH-{qid}-retry{retries}",
            )
            ext = extractor.process(qtext, guidance, sh_answer)
        clean = ext["clean_answer"]

        # ── Single scoreboard submission ──────────────────────────────────────────
        try:
            sb = scoreboard.submit(q_number, clean)
            pts_earned = sb.earned
            sb_correct = sb.correct
            earned_pts += pts_earned
            verdict = "[CORRECT]" if sb_correct else "[WRONG]"
        except Exception as exc:
            pts_earned, sb_correct = 0, False
            verdict = f"[SB UNAVAILABLE: {exc}]"

        print(f"  Extracted: {clean!r}  ->  {verdict}  ({pts_earned}/{points})")
        logger.timeline(
            f"\n**SH FINAL → extractor:** `{clean}`  {verdict}  "
            f"(delegations: {len(ctx.q_delegations)}, "
            f"cumulative failed delegations: {ctx.failed_delegations})\n"
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
            "extractor_valid":  ext["valid"],
            "extractor_reason": ext["reason"],
            "num_delegations":  len(ctx.q_delegations),
            "delegations":      ctx.q_delegations,
        })

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "run":                  logger.run_name,
                "full_run":             full_run,
                "langsmith_project":    ls_project,
                "models":               {"sh": SH_MODEL, "senior": senior_model,
                                          "senior_base_url": senior_base_url or "openai",
                                          "extractor": "meta/llama-3.3-70b-instruct"},
                "score":                earned_pts,
                "total":                total_points,
                "correct":              sum(1 for r in results if r["sb_correct"]),
                "attempted":            len(results),
                "failed_delegations":   ctx.failed_delegations,
                "extractor_rejections": extractor_rejections,
                "results":              results,
            }, f, indent=2, ensure_ascii=False)

    # ── Final summary ──────────────────────────────────────────────────────────────
    correct_n = sum(1 for r in results if r["sb_correct"])
    att       = len(results)
    print(f"\n{'='*80}\nFINAL — {logger.run_name}  ({run_label})")
    print(f"  Correct           : {correct_n}/{att}"
          f"  ({(correct_n/att*100 if att else 0):.1f}%)")
    print(f"  Points (this run) : {earned_pts}/{total_points}")
    print(f"  Failed delegations: {ctx.failed_delegations}")
    print(f"  Extractor rejects : {extractor_rejections}")
    print(f"  Summary JSON      : {summary_path}")
    print(f"  Timeline          : {logger.timeline_path}")
    print(f"  LangSmith project : {ls_project}")
    print("=" * 80)

    logger.timeline(
        f"\n---\n\n## SUMMARY\n\n"
        f"- Correct: {correct_n}/{att}\n"
        f"- Points: {earned_pts}/{total_points}\n"
        f"- Failed delegations: {ctx.failed_delegations}\n"
        f"- Extractor rejections: {extractor_rejections}\n"
        f"- LangSmith project: `{ls_project}`\n"
    )


if __name__ == "__main__":
    main()
