#!/usr/bin/env python3
"""
Native GPT-4.5-mini runner — no LangGraph, raw OpenAI tool-call loop.
Same 6 tools as splunk_agent.py, but zero verify gate / state graph overhead.
Results: results/gpt5.4mini_native_base_result.{log,json}

Usage (from project root or agent/ directory):
    python agent/run_gpt54mini_native.py
    python agent/run_gpt54mini_native.py --start Q201 --limit 10
"""

import os
import sys
import re
import json
import datetime
import argparse
import textwrap

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from openai import OpenAI
from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient
import splunk_agent as agent_mod

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SPLUNK_HOST    = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER    = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS    = os.getenv("SPLUNK_PASS", "")

MODEL    = "gpt-5.4-mini"
MAX_ITER = 20

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
ANSWERS_PATH   = os.path.join(PROJECT_ROOT, "datasets", "botsv3_answers.json")
RESULTS_DIR    = os.path.join(PROJECT_ROOT, "results")

# ── OpenAI tool schemas (matching make_tools in splunk_agent.py) ───────────────

OAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_source_types",
            "description": (
                "Return the full list of all known sourcetypes from the local manifest. "
                "Call this FIRST — it is the entry point for all investigations. "
                "No Splunk call, instant response."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_keyword",
            "description": (
                "Search for a keyword across all BOTSv3 fields. "
                "Returns every field (with its sourcetype path) whose name contains the keyword. "
                "If nothing is found in the local manifest, falls back to a live Splunk fieldsummary. "
                "Call this before run_splunk_search to discover which sourcetypes and fields "
                "are relevant to a keyword."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Keyword to search for in field names."},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sourcetype_fields",
            "description": (
                "Run Splunk fieldsummary on a sourcetype: every field with coverage %, "
                "distinct value count, and sample values. Use when search_keyword returns "
                "no match for a sourcetype you want to explore."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sourcetype": {"type": "string"},
                    "index":      {"type": "string", "default": "botsv3"},
                    "min_count":  {"type": "integer", "default": 1},
                },
                "required": ["sourcetype"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_field_values",
            "description": (
                "Get the top distinct values for a field, optionally scoped to a sourcetype. "
                "Use to enumerate the range of values a field contains before filtering on it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field":      {"type": "string"},
                    "index":      {"type": "string", "default": "botsv3"},
                    "sourcetype": {"type": "string", "default": ""},
                    "top_n":      {"type": "integer", "default": 20},
                },
                "required": ["field"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sample_events",
            "description": (
                "Return raw event content from a sourcetype to discover embedded field names "
                "and log structure. `sourcetype` MUST be a value returned by get_source_types. "
                "`keyword` is an optional free-text filter — it narrows which events are returned "
                "but does NOT select the sourcetype. Omit or leave blank to sample any events."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sourcetype": {"type": "string"},
                    "index":      {"type": "string", "default": "botsv3"},
                    "keyword":    {"type": "string", "default": ""},
                    "count":      {"type": "integer", "default": 3},
                },
                "required": ["sourcetype"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_splunk_search",
            "description": (
                "Execute an SPL search against Splunk. "
                "Only call this when you are certain the sourcetype exists — verified via get_source_types. "
                "Always include a sourcetype filter. Must aggregate with | stats, | top, or | rare. "
                "No leading wildcards. Max 50 results."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query":       {"type": "string"},
                    "max_results": {"type": "integer", "default": 50},
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tee: console + log file ────────────────────────────────────────────────────

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
        for s in (self.console, self.file):
            try: s.flush()
            except Exception: pass

    def __enter__(self):
        self._old   = sys.stdout
        sys.stdout  = self
        return self

    def __exit__(self, *_):
        sys.stdout = self._old


# ── Scoring helpers ────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip().lower())


def score_answer(agent_answer: str, correct_answer: str) -> tuple:
    a_norm = normalize(agent_answer)
    c_norm = normalize(correct_answer)
    if not c_norm:
        return "wrong", "no correct answer on record"
    if a_norm == c_norm:
        return "exact", "normalised strings match"
    if c_norm in a_norm:
        return "partial", "correct answer found as substring in agent reply"
    tokens = [t.strip() for t in re.split(r'[,\s]+', c_norm) if t.strip()]
    if tokens and all(tok in a_norm for tok in tokens):
        return "partial", "all answer tokens found in agent reply (format differs)"
    return "wrong", "answer not found"


# ── Native tool executor ───────────────────────────────────────────────────────

def execute_tool(tool_map: dict, name: str, args: dict) -> str:
    if name not in tool_map:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = tool_map[name].invoke(args)
        return result if isinstance(result, str) else json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Native agent loop ──────────────────────────────────────────────────────────

def run_question_native(client: OpenAI, tool_map: dict, question: str,
                        qid: str, max_iter: int = MAX_ITER) -> str:
    """Pure OpenAI tool-call loop — no LangGraph, no verify gate."""
    messages = [
        {"role": "system", "content": agent_mod.SYSTEM_PROMPT},
        {"role": "user",   "content": question},
    ]

    print(f"\n[Native loop start] {qid}: {question[:80]}")

    for step in range(1, max_iter + 1):
        print(f"\n[Step {step}/{max_iter}]")

        kwargs = dict(
            model=MODEL,
            messages=messages,
            tools=OAI_TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:
            print(f"[API error] {e}")
            return f"[API error: {e}]"

        msg = resp.choices[0].message

        # Log thinking / text content
        if msg.content:
            label = "[Agent thinking]" if msg.tool_calls else "[Agent response]"
            print(f"\n{label}\n{msg.content}\n")

        # Append assistant turn to history
        assistant_entry = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id":       tc.id,
                    "type":     "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_entry)

        # Terminal condition: no tool calls → final answer
        if not msg.tool_calls:
            return msg.content or ""

        # Execute each tool call and feed results back
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            args_repr = json.dumps(args, separators=(",", ":"))
            print(f"\n[Tool call] {name}({args_repr})")

            result = execute_tool(tool_map, name, args)
            snippet = result[:800] + ("…" if len(result) > 800 else "")
            print(f"[Tool result] {snippet}")

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result,
            })

    # Max iterations hit — force a bare final answer
    print(f"\n[Max iterations {max_iter} reached — forcing final answer]")
    messages.append({
        "role":    "user",
        "content": (
            "You have used the maximum number of tool calls. "
            "Give your best final answer now based on everything found so far."
        ),
    })
    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"[Final answer error: {e}]"


# ── Answer extractor (prose-stripping pass) ────────────────────────────────────

def extract_clean_answer(client: OpenAI, question: str, guidance: str,
                         verbose_answer: str) -> str:
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
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=256,
            temperature=0,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[extract error: {e}]"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=None,
                        help="Question ID to start from (e.g. Q201).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after this many questions.")
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set in .env")
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set in .env")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_path  = os.path.join(RESULTS_DIR, "gpt5.4mini_native_base_result.log")
    json_path = os.path.join(RESULTS_DIR, "gpt5.4mini_native_base_result.json")

    questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))
    answers   = {a["id"]: a for a in json.load(open(ANSWERS_PATH, "r", encoding="utf-8"))}

    print(f"Connecting to Splunk at {SPLUNK_HOST} ...")
    splunk     = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    scoreboard = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")

    # Build LangChain tool objects (reuse exact implementations from splunk_agent)
    lc_tools = agent_mod.make_tools(splunk)
    tool_map = {t.name: t for t in lc_tools}

    client    = OpenAI(api_key=OPENAI_API_KEY)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine start index
    start_idx = 0
    if args.start:
        ids = [q["id"] for q in questions]
        if args.start in ids:
            start_idx = ids.index(args.start)
        else:
            print(f"Warning: --start={args.start!r} not found; starting from beginning.")

    # Fixed filenames: preload any existing results so a resume appends instead
    # of clobbering Q1..Qn, and append to the log instead of truncating it.
    results      = []
    total_points = 0
    earned_pts   = 0
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as jf:
            results = json.load(jf).get("results", [])
        total_points = sum(r.get("base_points", 0) for r in results)
        earned_pts   = sum(r.get("earned", 0) for r in results)
        print(f"Resuming: {len(results)} prior result(s) loaded from {json_path}")
    done_ids = {r["id"] for r in results}
    log_mode = "a" if results else "w"

    with open(log_path, log_mode, encoding="utf-8", errors="replace") as log_file:
        with Tee(sys.__stdout__, log_file):
            limit_label = str(args.limit) if args.limit else "all"
            print(f"GPT-4.5-mini Native (No LangGraph) — {timestamp}")
            print(f"Model: {MODEL}  |  Max iterations per Q: {MAX_ITER}")
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

                print(f"\n{'─'*80}")
                print(f"[{qid}]  Level {level}  |  {cat}  |  {points} pts")
                print(f"Q: {textwrap.fill(qtext, width=78, subsequent_indent='   ')}")
                if notes:
                    print(f"   [Note: {notes}]")
                print(f"   Correct answer: {correct!r}")
                print("─" * 40)

                try:
                    agent_answer = run_question_native(client, tool_map, qtext, qid)
                except Exception as e:
                    agent_answer = f"[AGENT ERROR: {e}]"

                print(f"\n{'─'*40}")
                print(f"[AGENT VERBOSE ANSWER]\n{agent_answer}")

                guidance     = q.get("answer_guidance", "") or ""
                clean_answer = extract_clean_answer(client, qtext, guidance, agent_answer)
                print(f"\n[EXTRACTED ANSWER FOR SCOREBOARD]\n{clean_answer}")
                print("─" * 40)

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

                verdict, reason = score_answer(agent_answer, correct)
                print(f"  (local match: {verdict} — {reason})")
                print(f"  Running total: {earned_pts} pts earned from scoreboard")

                results.append({
                    "id":           qid,
                    "question":     qtext,
                    "category":     cat,
                    "level":        level,
                    "base_points":  points,
                    "correct":      correct,
                    "agent_answer": agent_answer,
                    "clean_answer": clean_answer,
                    "sb_correct":   sb_correct,
                    "local_verdict": verdict,
                    "earned":       pts_earned,
                    "notes":        notes,
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

            # ── Final summary ──────────────────────────────────────────────────
            correct_n = sum(1 for r in results if r["sb_correct"])
            wrong_n   = sum(1 for r in results if not r["sb_correct"])
            attempted = len(results)

            try:
                live_score = scoreboard.get_score()
                live_pts   = live_score.get("total_points", earned_pts)
            except Exception:
                live_pts   = earned_pts

            print(f"\n{'='*80}")
            print(f"FINAL SCOREBOARD  (GPT-4.5-mini native)  — {timestamp}")
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
            print("─" * 72)
            for r in results:
                v = "CORRECT" if r["sb_correct"] else "WRONG"
                print(f"{r['id']:<8} {v:<12} {r['earned']:>8} {r['base_points']:>6}  {str(r['correct'])[:40]}")


if __name__ == "__main__":
    main()
