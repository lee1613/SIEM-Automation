#!/usr/bin/env python3
"""
Multi-Agent Runner v1 — Judge + Query Planner architecture

Runs the Judge Agent against all BOTSv3 questions and scores via the
Splunk CTF scoreboard. This is the v1 upgrade over run_all.py which
used a single monolithic agent.

Architecture:
    JudgeAgentV1 (cybersecurity reasoning)
        └─ calls QueryPlannerV1 (Splunk executor) as tools

Usage:
    python agent/run_multiagent_v1.py                  # all questions
    python agent/run_multiagent_v1.py --start Q201     # resume from Q201
    python agent/run_multiagent_v1.py --question Q203  # single question
    python agent/run_multiagent_v1.py --dry-run        # list questions only

Output:
    results/v1_run_YYYYMMDD_HHMMSS.log   — full transcript
    results/v1_run_YYYYMMDD_HHMMSS.json  — machine-readable results

Version tag: v1
"""

import argparse
import datetime
import json
import logging
import os
import sys
import textwrap

# ── Path setup ─────────────────────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient
from query_planner.query_planner_v1 import QueryPlannerV1
from judge.judge_agent_v1 import create_judge_agent, run_judge

# ── Config ─────────────────────────────────────────────────────────────────────

NIM_API_KEY  = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST  = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER  = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS  = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")
RESULTS_DIR    = os.path.join(PROJECT_ROOT, "results")

VERSION = "v1"

# ── Tee: console + log file ────────────────────────────────────────────────────

class Tee:
    """Mirror stdout to console (encoding-safe) and a UTF-8 log file."""

    def __init__(self, console_stream, file_stream):
        self.console = console_stream
        self.file    = file_stream

    def write(self, data):
        try:
            self.file.write(data)
        except Exception:
            pass
        try:
            enc  = getattr(self.console, "encoding", "utf-8") or "utf-8"
            safe = data.encode(enc, errors="replace").decode(enc)
            self.console.write(safe)
        except Exception:
            pass

    def flush(self):
        for s in (self.console, self.file):
            try:
                s.flush()
            except Exception:
                pass

    def __enter__(self):
        self._old  = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, *_):
        sys.stdout = self._old


# ── Scoring ────────────────────────────────────────────────────────────────────

def local_score(agent_answer: str, correct_answer: str) -> tuple[str, str]:
    """Local scoring for diagnostics (scoreboard is authoritative)."""
    import re

    def norm(s):
        return re.sub(r'\s+', ' ', s.strip().lower())

    a = norm(agent_answer)
    c = norm(correct_answer)

    if not c:
        return "unknown", "no reference answer"
    if a == c:
        return "exact", "exact match"
    if c in a:
        return "partial", "correct found as substring"
    tokens = [t.strip() for t in re.split(r'[,\s]+', c) if t.strip()]
    if tokens and all(tok in a for tok in tokens):
        return "partial", "all tokens found"
    return "wrong", "not found"


# ── Main runner ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=f"Multi-Agent BOTSv3 Runner {VERSION}")
    parser.add_argument("--start",    default=None, help="Resume from question ID (e.g. Q201)")
    parser.add_argument("--question", default=None, help="Run a single question by ID (e.g. Q203)")
    parser.add_argument("--dry-run",  action="store_true", help="List questions without running")
    args = parser.parse_args()

    if not NIM_API_KEY:
        sys.exit("NIM_API_KEY not set — check agent/.env")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set — check agent/.env")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = os.path.join(RESULTS_DIR, f"{VERSION}_run_{timestamp}.log")
    json_path = os.path.join(RESULTS_DIR, f"{VERSION}_run_{timestamp}.json")

    questions = json.load(open(QUESTIONS_PATH, encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(ANSWERS_PATH, encoding="utf-8"))}

    # Filter to single question if requested
    if args.question:
        questions = [q for q in questions if q["id"] == args.question]
        if not questions:
            sys.exit(f"Question {args.question!r} not found in dataset.")

    # Dry run
    if args.dry_run:
        print(f"{'ID':<8} {'Level':>6} {'Points':>8}  Question")
        print("-" * 80)
        for q in questions:
            print(f"{q['id']:<8} {q.get('level','?'):>6} {q.get('base_points',0):>8}  {q['question'][:60]}")
        print(f"\n{len(questions)} question(s) total.")
        return

    # Connect to services
    print(f"Connecting to Splunk at {SPLUNK_HOST} ...")
    splunk     = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    scoreboard = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")

    # Build the multi-agent system
    print("Building QueryPlannerV1 + JudgeAgentV1 ...")
    planner  = QueryPlannerV1(splunk)
    graph, _ = create_judge_agent(NIM_API_KEY, planner)
    print(f"Agent system ready [{VERSION}]\n")

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path.replace(".log", "_debug.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ]
    )

    # Determine start index
    start_idx = 0
    if args.start:
        ids = [q["id"] for q in questions]
        if args.start in ids:
            start_idx = ids.index(args.start)
        else:
            print(f"Warning: --start={args.start!r} not found; starting from Q0.")

    results      = []
    total_points = 0
    earned_pts   = 0

    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        tee = Tee(sys.__stdout__, log_file)

        with tee:
            print(f"BOTSv3 Multi-Agent Run {VERSION} — {timestamp}")
            print(f"Questions: {len(questions)}  |  Starting at index {start_idx}")
            print(f"Log: {log_path}")
            print("=" * 80 + "\n")

            for idx, q in enumerate(questions):
                if idx < start_idx:
                    continue

                qid      = q["id"]
                qtext    = q["question"]
                qnum     = q.get("number", int(qid.replace("Q", "")))
                points   = q.get("base_points", 0)
                level    = q.get("level", "?")
                cat      = q.get("category", "")
                guidance = q.get("answer_guidance", "") or ""

                total_points += points

                ans_entry    = answers.get(qid, {})
                correct      = ans_entry.get("answer", "") or ""

                print(f"\n{'─'*80}")
                print(f"[{qid}]  Level {level}  |  {cat}  |  {points} pts")
                print(f"Q: {textwrap.fill(qtext, width=76, subsequent_indent='   ')}")
                if guidance:
                    print(f"   Guidance: {guidance}")
                print(f"   Reference answer: {correct!r}")
                print("─" * 40)

                thread_id = f"botsv3_{VERSION}_{qid}_{timestamp}"

                try:
                    verbose, clean_answer = run_judge(
                        graph,
                        question=qtext,
                        answer_guidance=guidance,
                        thread_id=thread_id,
                    )
                except Exception as e:
                    verbose      = f"[AGENT ERROR: {e}]"
                    clean_answer = ""
                    print(verbose)

                print(f"\n[Judge verbose answer]\n{verbose}")
                print(f"\n[Extracted answer for scoreboard]\n{clean_answer!r}")
                print("─" * 40)

                # Submit to scoreboard
                sb_result  = scoreboard.submit(qnum, clean_answer)
                pts_earned = sb_result.earned
                earned_pts += pts_earned

                verdict, reason = local_score(clean_answer, correct)
                verdict_label   = "[CORRECT]" if sb_result.correct else "[WRONG]"

                print(f"  Scoreboard: {verdict_label}  Earned: {pts_earned}/{points} pts")
                print(f"  Local match: {verdict} — {reason}")
                print(f"  Running total: {earned_pts} pts")

                entry = {
                    "id":           qid,
                    "version":      VERSION,
                    "question":     qtext,
                    "category":     cat,
                    "level":        level,
                    "base_points":  points,
                    "correct":      correct,
                    "verbose":      verbose,
                    "clean_answer": clean_answer,
                    "sb_correct":   sb_result.correct,
                    "local_verdict": verdict,
                    "earned":       pts_earned,
                    "guidance":     guidance,
                }
                results.append(entry)

                # Persist after every question
                summary = {
                    "version":   VERSION,
                    "run":       timestamp,
                    "score":     earned_pts,
                    "total":     total_points,
                    "attempted": len(results),
                    "correct":   sum(1 for r in results if r["sb_correct"]),
                    "wrong":     sum(1 for r in results if not r["sb_correct"]),
                    "accuracy":  round(sum(1 for r in results if r["sb_correct"]) / len(results) * 100, 1),
                    "results":   results,
                }
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(summary, jf, indent=2, ensure_ascii=False)

            # ── Final scoreboard ───────────────────────────────────────────────
            attempted  = len(results)
            correct_n  = sum(1 for r in results if r["sb_correct"])
            wrong_n    = sum(1 for r in results if not r["sb_correct"])
            accuracy   = correct_n / max(attempted, 1) * 100

            live_score = scoreboard.get_score()
            live_pts   = live_score.get("total_points", earned_pts)

            print(f"\n{'='*80}")
            print(f"FINAL SCOREBOARD — {VERSION} — {timestamp}")
            print(f"{'='*80}")
            print(f"  Questions attempted  : {attempted}")
            print(f"  Correct (scoreboard) : {correct_n}  ({accuracy:.1f}%)")
            print(f"  Wrong               : {wrong_n}  ({wrong_n/max(attempted,1)*100:.1f}%)")
            print(f"  Points (this run)   : {earned_pts} / {total_points}  ({earned_pts/max(total_points,1)*100:.1f}%)")
            print(f"  Points (scoreboard) : {live_pts}  (cumulative)")
            print(f"\n  Target accuracy     : 33%  ({int(attempted*0.33)} questions)")
            print(f"  {'GOAL MET ✓' if accuracy >= 33 else f'Gap: {33 - accuracy:.1f}%'}")
            print(f"\n  Scoreboard UI : http://localhost:8000/en-US/app/SA-ctf_scoreboard/")
            print(f"  Results JSON  : {json_path}")
            print(f"  Full log      : {log_path}")
            print(f"{'='*80}\n")

            # Per-question breakdown
            print(f"{'ID':<8} {'RESULT':<10} {'EARNED':>8} {'MAX':>6}  REFERENCE")
            print("─" * 72)
            for r in results:
                v = "CORRECT" if r["sb_correct"] else "wrong"
                print(f"{r['id']:<8} {v:<10} {r['earned']:>8} {r['base_points']:>6}  {str(r['correct'])[:40]}")


if __name__ == "__main__":
    main()
