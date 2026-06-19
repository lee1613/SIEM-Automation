#!/usr/bin/env python3
"""Run the agent on Q225 only, with full untruncated logging."""

import os, sys, json, datetime

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
from openai import OpenAI
from splunk_client import SplunkClient
from scoreboard_client import ScoreboardClient
import splunk_agent as agent_mod

load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NIM_API_KEY = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS = os.getenv("SPLUNK_PASS", "")
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL        = "meta/llama-3.3-70b-instruct"

os.makedirs(os.path.join(PROJECT_ROOT, "results"), exist_ok=True)
ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_path = os.path.join(PROJECT_ROOT, "results", f"q225_{ts}.log")

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
        self._old = sys.stdout
        sys.stdout = self
        return self
    def __exit__(self, *_):
        sys.stdout = self._old

def extract_clean_answer(nim_client, question, guidance, verbose_answer):
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
    resp = nim_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()

QUESTION = "Using the payload data found in the memcached attack, what is the name of the .jpeg file that is used by Taedonggang to deface other brewery websites?"
GUIDANCE = "Include the file extension."
CORRECT  = "index1.jpeg"

with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
    tee = Tee(sys.__stdout__, log_file)
    with tee:
        print(f"Q225 Full-Verbose Run — {ts}")
        print(f"Log: {log_path}")
        print("=" * 80)
        print(f"Q: {QUESTION}")
        print(f"   Correct answer: {CORRECT!r}")
        print("=" * 80 + "\n")

        splunk    = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
        sb        = ScoreboardClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
        graph, _  = agent_mod.create_agent(NIM_API_KEY, splunk)
        nim_client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)

        try:
            agent_answer = agent_mod.run_agent(graph, QUESTION, thread_id="q225_solo")
        except Exception as e:
            agent_answer = f"[AGENT ERROR: {e}]"

        print(f"\n{'='*80}")
        print(f"[AGENT VERBOSE ANSWER]\n{agent_answer}")

        clean = extract_clean_answer(nim_client, QUESTION, GUIDANCE, agent_answer)
        print(f"\n[EXTRACTED ANSWER FOR SCOREBOARD]\n{clean}")

        sb_result = sb.submit(225, clean)
        verdict   = "CORRECT" if sb_result.correct else "WRONG"
        print(f"\n[SCOREBOARD] {verdict}  |  Earned: {sb_result.earned} pts")
        print(f"[LOG FILE]   {log_path}")
