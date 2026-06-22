#!/usr/bin/env python3
"""
Multi-Agent Runner v2 — Judge v2 (RAG + Reflection + Auto-Diagnostic) + Query Planner

Usage:
    python agent/run_multiagent_v2.py                  # all 58 questions
    python agent/run_multiagent_v2.py --start Q203     # resume from Q203
    python agent/run_multiagent_v2.py --question Q205  # single question
    python agent/run_multiagent_v2.py --dry-run        # list questions, no execution

Output:
    results/v2_run_YYYYMMDD_HHMMSS.log
    results/v2_run_YYYYMMDD_HHMMSS.json

Version tag: v2
"""

import argparse
import datetime
import json
import logging
import os
import sys
import textwrap

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient
from query_planner.query_planner_v1 import QueryPlannerV1
from judge.judge_agent_v2 import create_judge_agent, run_judge
from rag.knowledge_base import build_siem_knowledge_base

NIM_API_KEY  = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST  = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER  = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS  = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")
RESULTS_DIR    = os.path.join(PROJECT_ROOT, "results")

VERSION = "v2"

# ── Tee ────────────────────────────────────────────────────────────────────────

class Tee:
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
        try:
            self.file.flush()
        except Exception:
            pass
        try:
            self.console.flush()
        except Exception:
            pass

    def fileno(self):
        return self.console.fileno()

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run Judge Agent v2 on BOTSv3")
    parser.add_argument("--start",    default=None, help="Start at question ID (e.g. Q203)")
    parser.add_argument("--question", default=None, help="Run only this question ID")
    parser.add_argument("--dry-run",  action="store_true", help="List questions without running")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = os.path.join(RESULTS_DIR, f"v2_run_{ts}.log")
    json_path = os.path.join(RESULTS_DIR, f"v2_run_{ts}.json")

    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, log_file)

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    with open(QUESTIONS_PATH) as f:
        questions = json.load(f)
    with open(ANSWERS_PATH) as f:
        answers = {a["id"]: a["answer"] for a in json.load(f)}

    if args.question:
        questions = [q for q in questions if q["id"] == args.question]
    elif args.start:
        ids = [q["id"] for q in questions]
        idx = ids.index(args.start) if args.start in ids else 0
        questions = questions[idx:]

    if args.dry_run:
        print(f"Dry run — {len(questions)} questions:")
        for q in questions:
            print(f"  {q['id']} | {q['question'][:60]}")
        return

    print(f"Connecting to Splunk at {SPLUNK_HOST} ...")
    splunk = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")

    print("Building QueryPlannerV1 + JudgeAgentV2 + RAG ...")
    planner  = QueryPlannerV1(splunk)
    kb       = build_siem_knowledge_base(SCRIPT_DIR)
    graph, _ = create_judge_agent(NIM_API_KEY, planner, kb)

    scoreboard = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Agent system ready [v2]\n")

    print(f"\nBOTSv3 Multi-Agent Run {VERSION} — {ts}")
    print(f"Questions: {len(questions)}  |  Starting at index 0")
    print(f"Log: {log_path}")
    print("=" * 80)

    run_results = []
    correct     = 0
    total_pts   = 0

    for i, q in enumerate(questions):
        qid      = q["id"]
        question = q["question"]
        guidance = q.get("answer_guidance", "")
        ref_ans  = answers.get(qid, "")
        pts      = q.get("points", 0)

        print(f"\n\n{'?' * 80}")
        print(f"[{qid}]  {q.get('category','')}  |  {pts} pts")
        wrapped = textwrap.fill(question, width=76, initial_indent="Q: ", subsequent_indent="   ")
        print(wrapped)
        if guidance:
            wrapped_g = textwrap.fill(guidance, width=76, initial_indent="   Guidance: ", subsequent_indent="   ")
            print(wrapped_g)
        if ref_ans:
            print(f"   Reference answer: {ref_ans!r}")
        print("?" * 40)

        try:
            verbose, extracted = run_judge(
                graph, question,
                answer_guidance=guidance,
                thread_id=f"{ts}_{qid}",
            )
        except Exception as exc:
            logging.error("[Runner] Question %s failed: %s", qid, exc, exc_info=True)
            verbose = extracted = f"ERROR: {exc}"

        print(f"\n[Judge verbose answer]\n{verbose[:200] if verbose else ''}\n")
        print(f"\n[Extracted answer for scoreboard]\n{extracted!r}")

        # Score
        sb_result  = scoreboard.submit(qid, extracted)
        sb_correct = getattr(sb_result, "correct", False)
        sb_pts     = getattr(sb_result, "earned", 0)

        local_correct = (
            isinstance(ref_ans, str) and
            extracted.lower().strip() == ref_ans.lower().strip()
        ) if ref_ans else False

        result_label = "CORRECT" if sb_correct else "wrong"
        local_label  = "correct" if local_correct else "wrong — not found" if not ref_ans else "wrong"

        print(f"{'?' * 40}")
        print(f"  Scoreboard: [{result_label}]  Earned: {sb_pts}/{pts} pts")
        print(f"  Local match: {local_label}")

        if sb_correct:
            correct   += 1
            total_pts += sb_pts

        cumulative = scoreboard.get_score()
        print(f"  Running total: {cumulative.get('total_points', 0)} pts")

        run_results.append({
            "id":          qid,
            "question":    question,
            "answer":      extracted,
            "reference":   ref_ans,
            "correct":     sb_correct,
            "local":       local_correct,
            "points":      sb_pts,
            "max_points":  pts,
        })

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(run_results, jf, indent=2)

    # ── Final report ───────────────────────────────────────────────────────────
    n      = len(run_results)
    pct    = correct / n * 100 if n else 0
    target = 33.0
    gap    = max(0, target - pct)

    print(f"\n\n{'=' * 80}")
    print(f"FINAL SCOREBOARD — {VERSION} — {ts}")
    print(f"{'=' * 80}")
    print(f"  Questions attempted  : {n}")
    print(f"  Correct (scoreboard) : {correct}  ({pct:.1f}%)")
    print(f"  Wrong               : {n - correct}  ({100 - pct:.1f}%)")
    print(f"  Points (this run)   : {total_pts} / {sum(q.get('points',0) for q in questions)}  ({total_pts / max(sum(q.get('points',0) for q in questions),1)*100:.1f}%)")
    print(f"  Target accuracy     : {target}%  ({int(n * target / 100)} questions)")
    print(f"  Gap: {gap:.1f}%")
    print(f"\n  Scoreboard UI : http://localhost:8000/en-US/app/SA-ctf_scoreboard/")
    print(f"  Results JSON  : {json_path}")
    print(f"  Full log      : {log_path}")
    print(f"{'=' * 80}")

    hdr = f"{'ID':<8} {'RESULT':<12} {'EARNED':>8} {'MAX':>6}  REFERENCE"
    sep = "?" * 72
    print(f"\n{hdr}\n{sep}")
    for r in run_results:
        label = "correct" if r["correct"] else "wrong"
        print(f"{r['id']:<8} {label:<12} {r['points']:>8}  {r['max_points']:>4}  {r['reference']}")

    log_file.close()


if __name__ == "__main__":
    main()
