#!/usr/bin/env python3
"""
Run the SIEM agent on every BOTSv3 question, stream full output, and score the results.

Usage (from project root, or from agent/ directory):
    python agent/run_all.py
    python agent/run_all.py --start Q201    # resume from a question ID

Output files in  results/  (created automatically):
    run_YYYYMMDD_HHMMSS.log   — full human-readable transcript (tool calls, thinking, verdicts)
    run_YYYYMMDD_HHMMSS.json  — machine-readable results with per-question data and score
"""

import os
import sys
import re
import json
import datetime
import argparse
import textwrap

# ── Path setup ─────────────────────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
from openai import OpenAI
from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient
import splunk_agent as agent_mod

# extract_clean_answer uses the raw OpenAI client (lightweight, no tools)
MODEL         = "gpt-5.4"
EXTRACT_MODEL = "gpt-5.4"


def extract_clean_answer(oai_client: OpenAI, question: str, guidance: str,
                         verbose_answer: str) -> str:
    """
    One additional LLM call that strips prose from the agent's answer and
    returns only the exact value(s) the scoreboard expects.
    """
    guidance_line = f"Answer format guidance: {guidance}" if guidance else ""
    prompt = (
        f"Question: {question}\n\n"
        f"{guidance_line}\n\n"
        f"Agent's analysis: {verbose_answer}\n\n"
        "Based on the analysis above, state ONLY the exact answer with no "
        "explanation, no punctuation beyond what the format requires, and no "
        "surrounding text. If the answer is a list, use comma-separated values "
        "with no spaces. If a number, give only the number. Output nothing else."
    )
    resp = oai_client.chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=256,
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()

load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SPLUNK_HOST    = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER    = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS    = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")
RESULTS_DIR    = os.path.join(PROJECT_ROOT, "results")


# ── Tee: write to console + log file simultaneously ───────────────────────────

class Tee:
    """Write to console (recoded to avoid cp1252 errors) and UTF-8 log file."""

    def __init__(self, console_stream, file_stream):
        self.console = console_stream
        self.file    = file_stream

    def write(self, data):
        # Write to file (UTF-8, never fails)
        try:
            self.file.write(data)
        except Exception:
            pass
        # Write to console: replace characters unsupported by the terminal encoding
        try:
            enc = getattr(self.console, "encoding", "utf-8") or "utf-8"
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
        self._old = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, *_):
        sys.stdout = self._old


# ── Scoring ────────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Lowercase, strip, collapse internal whitespace."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def score_answer(agent_answer: str, correct_answer: str) -> tuple[str, str]:
    """
    Returns (verdict, reason):
      exact   — agent answer matches correct (normalised)
      partial — all tokens of correct answer appear somewhere in agent reply
      wrong   — not found
    """
    a_norm = normalize(agent_answer)
    c_norm = normalize(correct_answer)

    if not c_norm:
        return "wrong", "no correct answer on record"

    if a_norm == c_norm:
        return "exact", "normalised strings match"

    # Verbatim substring match
    if c_norm in a_norm:
        return "partial", "correct answer found as substring in agent reply"

    # Token-set match: all comma/space-separated tokens of correct answer in agent reply
    tokens = [t.strip() for t in re.split(r'[,\s]+', c_norm) if t.strip()]
    if tokens and all(tok in a_norm for tok in tokens):
        return "partial", "all answer tokens found in agent reply (format differs)"

    return "wrong", "answer not found"


# ── Main runner ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=None,
                        help="Question ID to start from (e.g. Q201). Skip earlier questions.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after attempting this many questions.")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = os.path.join(RESULTS_DIR, f"run_{timestamp}.log")
    json_path = os.path.join(RESULTS_DIR, f"run_{timestamp}.json")

    questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(ANSWERS_PATH, "r", encoding="utf-8"))}

    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set — check .env")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set — check .env")

    print(f"Connecting to Splunk at {SPLUNK_HOST} ...")
    splunk     = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    scoreboard = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")

    # LangGraph agent — single graph + MemorySaver shared across all questions
    print("Building LangGraph agent ...")
    graph, _   = agent_mod.create_agent(OPENAI_API_KEY, splunk)
    # Single thread per run: the model accumulates context across all 58 questions
    run_thread_id = f"botsv3_run_{timestamp}"
    print(f"Agent ready  [thread: {run_thread_id}]\n")

    # OpenAI client for extract_clean_answer (prose-stripping pass, no tools)
    oai_client = OpenAI(api_key=OPENAI_API_KEY)

    results      = []
    total_points = 0
    earned_pts   = 0

    # Skip questions before --start
    start_idx = 0
    if args.start:
        ids = [q["id"] for q in questions]
        if args.start in ids:
            start_idx = ids.index(args.start)
        else:
            print(f"Warning: --start={args.start!r} not found; starting from beginning.")

    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        tee = Tee(sys.__stdout__, log_file)

        with tee:
            limit_label = str(args.limit) if args.limit else "all"
            print(f"BOTSv3 Agent Full Run — {timestamp}")
            print(f"Questions: {len(questions)}  |  Starting at index {start_idx}  |  Limit: {limit_label}")
            print(f"Log: {log_path}")
            print("=" * 80 + "\n")

            for idx, q in enumerate(questions):
                qid    = q["id"]
                qtext  = q["question"]
                points = q.get("base_points", 0)
                level  = q.get("level", "?")
                cat    = q.get("category", "")

                if idx < start_idx:
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

                # Run the agent; all its print() output goes through Tee automatically.
                # Same thread_id -> model sees all prior Q&A for cross-question reasoning.
                try:
                    agent_answer = agent_mod.run_agent(graph, qtext, thread_id=run_thread_id)
                except Exception as e:
                    agent_answer = f"[AGENT ERROR: {e}]"

                print(f"\n{'-'*40}")
                print(f"[AGENT VERBOSE ANSWER]\n{agent_answer}")

                # Extract a clean bare answer for scoreboard submission
                guidance = q.get("answer_guidance", "") or ""
                clean_answer = extract_clean_answer(
                    oai_client, qtext, guidance, agent_answer
                )
                print(f"\n[EXTRACTED ANSWER FOR SCOREBOARD]\n{clean_answer}")
                print("-" * 40)

                # Submit to Splunk CTF scoreboard (official scoring)
                q_number = q.get("number", int(qid.replace("Q", "")))
                try:
                    sb_result = scoreboard.submit(q_number, clean_answer)
                    pts_earned = sb_result.earned
                    earned_pts += pts_earned
                    verdict_label = "[CORRECT]" if sb_result.correct else "[WRONG]"
                    sb_correct = sb_result.correct
                    print(f"  Scoreboard: {verdict_label}  |  Earned: {pts_earned}/{points} pts")
                except Exception as sb_err:
                    print(f"  Scoreboard: [UNAVAILABLE] — {sb_err}")
                    pts_earned = 0
                    sb_correct = False
                    verdict_label = "[UNAVAILABLE]"

                # Also compute a local verdict for the breakdown table
                verdict, reason = score_answer(agent_answer, correct)

                print(f"  (local match: {verdict} — {reason})")
                print(f"  Running total: {earned_pts} pts earned from scoreboard")

                entry = {
                    "id":              qid,
                    "question":        qtext,
                    "category":        cat,
                    "level":           level,
                    "base_points":     points,
                    "correct":         correct,
                    "agent_answer":    agent_answer,
                    "clean_answer":    clean_answer,
                    "sb_correct":      sb_correct,
                    "local_verdict":   verdict,
                    "earned":          pts_earned,
                    "notes":           notes,
                }
                results.append(entry)

                # Persist incrementally after every question
                summary = {
                    "run":        timestamp,
                    "score":      earned_pts,
                    "total":      total_points,
                    "correct":    sum(1 for r in results if r["sb_correct"]),
                    "wrong":      sum(1 for r in results if not r["sb_correct"]),
                    "results":    results,
                }
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(summary, jf, indent=2, ensure_ascii=False)

            # ── Final scoreboard ───────────────────────────────────────────────
            correct_n  = sum(1 for r in results if r["sb_correct"])
            wrong_n    = sum(1 for r in results if not r["sb_correct"])
            attempted  = len(results)

            # Read authoritative total from the Splunk scoreboard index
            live_score = scoreboard.get_score()
            live_pts   = live_score.get("total_points", earned_pts)

            print(f"\n{'='*80}")
            print(f"FINAL SCOREBOARD -- {timestamp}")
            print(f"{'='*80}")
            print(f"  Questions attempted  : {attempted}")
            print(f"  Correct (scoreboard) : {correct_n}  ({correct_n/attempted*100:.1f}%)")
            print(f"  Wrong               : {wrong_n}  ({wrong_n/attempted*100:.1f}%)")
            print(f"  Points (this run)   : {earned_pts} / {total_points}  ({earned_pts/max(total_points,1)*100:.1f}%)")
            print(f"  Points (scoreboard) : {live_pts}  (cumulative, all runs)")
            print(f"\n  Scoreboard UI : http://localhost:8000/en-US/app/SA-ctf_scoreboard/")
            print(f"  Results JSON  : {json_path}")
            print(f"  Full log      : {log_path}")
            print(f"{'='*80}\n")

            # Per-question breakdown table
            print(f"{'ID':<8} {'SCOREBOARD':<12} {'EARNED':>8} {'MAX':>6}  CORRECT ANSWER")
            print("-" * 72)
            for r in results:
                v = "CORRECT" if r["sb_correct"] else "WRONG"
                print(f"{r['id']:<8} {v:<12} {r['earned']:>8} {r['base_points']:>6}  {str(r['correct'])[:40]}")


if __name__ == "__main__":
    main()
