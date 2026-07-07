#!/usr/bin/env python3
"""Runner: nvidia/nemotron-ultra-253b-v1 via NIM, full LangGraph v0 architecture.
Results are saved as nemotron_ultra_v0.{log,json} in results/.

Usage (from project root or agent/ directory):
    python agent/run_nemotron_ultra.py
    python agent/run_nemotron_ultra.py --start Q201 --limit 10
"""

import os
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MODEL = "moonshotai/kimi-k2.6"

import splunk_agent as agent_mod
import run_all

# Override result filenames to nemotron_ultra_v0.*
import datetime
import os as _os

_orig_main = run_all.main

def _patched_main():
    import sys, json, re, textwrap, argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    _os.makedirs(run_all.RESULTS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = _os.path.join(run_all.RESULTS_DIR, "kimi_k2_6_v0.log")
    json_path = _os.path.join(run_all.RESULTS_DIR, "kimi_k2_6_v0.json")

    from openai import OpenAI
    from splunk_client import SplunkClient
    from scoreboard_client import ScoreboardClient

    NIM_API_KEY = _os.getenv("NIM_API_KEY", "")
    SPLUNK_PASS = _os.getenv("SPLUNK_PASS", "")
    if not NIM_API_KEY:
        sys.exit("NIM_API_KEY not set")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set")

    questions = json.load(open(run_all.QUESTIONS_PATH, "r", encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(run_all.ANSWERS_PATH, "r", encoding="utf-8"))}

    print(f"Connecting to Splunk at {run_all.SPLUNK_HOST} ...")
    splunk     = SplunkClient(run_all.SPLUNK_HOST, run_all.SPLUNK_USER, SPLUNK_PASS)
    scoreboard = ScoreboardClient(run_all.SPLUNK_HOST, run_all.SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")

    print("Building LangGraph agent ...")
    # model/base_url must be passed explicitly — create_agent's defaults are
    # bound at import time, so patching agent_mod.MODEL was a silent no-op
    # (the run would have hit api.openai.com with gpt-5.4 and a NIM key).
    graph, _ = agent_mod.create_agent(NIM_API_KEY, splunk,
                                      model=MODEL, base_url=run_all.NIM_BASE_URL)
    run_thread_id = f"nemotron_ultra_v0_{timestamp}"
    print(f"Agent ready  [thread: {run_thread_id}]\n")

    nim_client = OpenAI(base_url=run_all.NIM_BASE_URL, api_key=NIM_API_KEY)

    start_idx = 0
    if args.start:
        ids = [q["id"] for q in questions]
        if args.start in ids:
            start_idx = ids.index(args.start)
        else:
            print(f"Warning: --start={args.start!r} not found.")

    # Fixed filenames: preload any existing results so a resume appends instead
    # of clobbering Q1..Qn, and append to the log instead of truncating it.
    results      = []
    total_points = 0
    earned_pts   = 0
    if _os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as jf:
            results = json.load(jf).get("results", [])
        total_points = sum(r.get("base_points", 0) for r in results)
        earned_pts   = sum(r.get("earned", 0) for r in results)
        print(f"Resuming: {len(results)} prior result(s) loaded from {json_path}")
    done_ids = {r["id"] for r in results}
    log_mode = "a" if results else "w"

    with open(log_path, log_mode, encoding="utf-8", errors="replace") as log_file:
        tee = run_all.Tee(sys.__stdout__, log_file)
        with tee:
            limit_label = str(args.limit) if args.limit else "all"
            print(f"BOTSv3 Kimi-K2.6 v0 Run — {timestamp}")
            print(f"Model: {MODEL}  |  LangGraph verify-gate architecture")
            print(f"Questions: {len(questions)}  |  Start idx: {start_idx}  |  Limit: {limit_label}")
            print(f"Log: {log_path}")
            print("=" * 80 + "\n")

            for idx, q in enumerate(questions):
                qid    = q["id"]
                qtext  = q["question"]
                points = q.get("base_points", 0)
                level  = q.get("level", "?")
                cat    = q.get("category", "")

                if idx < start_idx or qid in done_ids:
                    continue
                if args.limit is not None and (idx - start_idx) >= args.limit:
                    break

                total_points += points
                ans_entry = answers.get(qid, {})
                correct   = ans_entry.get("answer", "") or ""
                notes     = ans_entry.get("notes", "") or ""

                print(f"\n{'-'*80}")
                print(f"[{qid}]  Level {level}  |  {cat}  |  {points} pts")
                print(f"Q: {textwrap.fill(qtext, width=78, subsequent_indent='   ')}")
                if notes:
                    print(f"   [Note: {notes}]")
                print(f"   Correct answer: {correct!r}")
                print("-" * 40)

                try:
                    agent_answer = agent_mod.run_agent(graph, qtext, thread_id=run_thread_id)
                except Exception as e:
                    agent_answer = f"[AGENT ERROR: {e}]"

                print(f"\n{'-'*40}")
                print(f"[AGENT VERBOSE ANSWER]\n{agent_answer}")

                guidance = q.get("answer_guidance", "") or ""
                try:
                    clean_answer = run_all.extract_clean_answer(nim_client, qtext, guidance, agent_answer)
                except Exception as ex_err:
                    print(f"  [extractor error: {ex_err}] — submitting raw agent answer")
                    clean_answer = agent_answer.strip()
                print(f"\n[EXTRACTED ANSWER FOR SCOREBOARD]\n{clean_answer}")
                print("-" * 40)

                q_number = q.get("number", int(qid.replace("Q", "")))
                try:
                    sb_result   = scoreboard.submit(q_number, clean_answer)
                    pts_earned  = sb_result.earned
                    earned_pts += pts_earned
                    sb_correct  = sb_result.correct
                    label       = "[CORRECT]" if sb_correct else "[WRONG]"
                    print(f"  Scoreboard: {label}  |  Earned: {pts_earned}/{points} pts")
                except Exception as sb_err:
                    print(f"  Scoreboard: [UNAVAILABLE] — {sb_err}")
                    pts_earned = 0
                    sb_correct = False

                verdict, reason = run_all.score_answer(agent_answer, correct)
                print(f"  (local match: {verdict} — {reason})")
                print(f"  Running total: {earned_pts} pts earned from scoreboard")

                results.append({
                    "id":            qid,
                    "question":      qtext,
                    "category":      cat,
                    "level":         level,
                    "base_points":   points,
                    "correct":       correct,
                    "agent_answer":  agent_answer,
                    "clean_answer":  clean_answer,
                    "sb_correct":    sb_correct,
                    "local_verdict": verdict,
                    "earned":        pts_earned,
                    "notes":         notes,
                })

                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump({
                        "run":     timestamp,
                        "model":   MODEL,
                        "score":   earned_pts,
                        "total":   total_points,
                        "correct": sum(1 for r in results if r["sb_correct"]),
                        "wrong":   sum(1 for r in results if not r["sb_correct"]),
                        "results": results,
                    }, jf, indent=2, ensure_ascii=False)

            correct_n = sum(1 for r in results if r["sb_correct"])
            wrong_n   = sum(1 for r in results if not r["sb_correct"])
            attempted = len(results)

            try:
                live_score = scoreboard.get_score()
                live_pts   = live_score.get("total_points", earned_pts)
            except Exception:
                live_pts   = earned_pts

            print(f"\n{'='*80}")
            print(f"FINAL SCOREBOARD  (Kimi-K2.6 v0)  — {timestamp}")
            print(f"{'='*80}")
            print(f"  Questions attempted  : {attempted}")
            if attempted:
                print(f"  Correct (scoreboard): {correct_n}  ({correct_n/attempted*100:.1f}%)")
                print(f"  Wrong               : {wrong_n}  ({wrong_n/attempted*100:.1f}%)")
                print(f"  Points (this run)   : {earned_pts} / {total_points}  ({earned_pts/max(total_points,1)*100:.1f}%)")
            print(f"  Points (scoreboard) : {live_pts}  (cumulative, all runs)")
            print(f"\n  Results JSON : {json_path}")
            print(f"  Full log     : {log_path}")
            print(f"{'='*80}\n")

            print(f"{'ID':<8} {'SCOREBOARD':<12} {'EARNED':>8} {'MAX':>6}  CORRECT ANSWER")
            print("-" * 72)
            for r in results:
                v = "CORRECT" if r["sb_correct"] else "WRONG"
                print(f"{r['id']:<8} {v:<12} {r['earned']:>8} {r['base_points']:>6}  {str(r['correct'])[:40]}")


if __name__ == "__main__":
    _patched_main()
