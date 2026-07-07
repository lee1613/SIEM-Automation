#!/usr/bin/env python3
"""
Run the SIEM agent on a single BOTSv3 question and dump all state messages.

Usage:
    python agent/run_single.py <question_number> <version>

Log saved to: results/{date}_query_planner_v{version}_{question}.log
"""

import os
import sys
import json
import datetime

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from splunk_client import SplunkClient
import splunk_agent as agent_mod

load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NIM_API_KEY = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS = os.getenv("SPLUNK_PASS", "")

QUESTIONS_PATH = os.path.join(PROJECT_ROOT, "datasets", "botsv3_questions.json")
RESULTS_DIR    = os.path.join(PROJECT_ROOT, "results")


class Tee:
    """Mirror stdout to both console and a log file simultaneously."""

    def __init__(self, console_stream, file_stream):
        self.console = console_stream
        self.file    = file_stream

    def write(self, data):
        try:
            self.file.write(data)
        except Exception:
            if not getattr(self, "_file_warned", False):
                self._file_warned = True
                try:
                    self.console.write("\n[Tee] log-file write failed — transcript no longer being saved\n")
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


def format_message(msg) -> str:
    lines = []
    mtype = type(msg).__name__
    if isinstance(msg, SystemMessage):
        lines.append("[SystemMessage]")
        lines.append(msg.content)
    elif isinstance(msg, HumanMessage):
        lines.append("[HumanMessage]")
        lines.append(msg.content)
    elif isinstance(msg, AIMessage):
        lines.append("[AIMessage]")
        if msg.content:
            lines.append(msg.content)
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                lines.append(f"  -> tool_call: {tc['name']}({json.dumps(tc['args'], indent=4)})")
    elif isinstance(msg, ToolMessage):
        lines.append(f"[ToolMessage: {getattr(msg, 'name', '?')}]")
        lines.append(msg.content)
    else:
        lines.append(f"[{mtype}]")
        lines.append(str(msg))
    return "\n".join(lines)


def main():
    q_num   = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    version = sys.argv[2] if len(sys.argv) > 2 else "0"

    questions = json.load(open(QUESTIONS_PATH, encoding="utf-8"))
    q = next((x for x in questions if x.get("number") == q_num), None)
    if not q:
        sys.exit(f"Question {q_num} not found.")

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    log_name = f"{date_str}_query_planner_v{version}_{q_num}.log"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_path = os.path.join(RESULTS_DIR, log_name)

    splunk = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    # NIM key requires the NIM endpoint + a NIM-served model; without these
    # kwargs create_agent defaults to gpt-5.4 on api.openai.com -> 401.
    graph, checkpointer = agent_mod.create_agent(
        NIM_API_KEY, splunk,
        model="meta/llama-3.3-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
    )
    thread_id = f"q{q_num}_v{version}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": agent_mod.MAX_ITER * 4,
    }

    with open(log_path, "w", encoding="utf-8") as log_file:
        with Tee(sys.__stdout__, log_file):
            header = (
                f"BOTSv3 Query Planner v{version} — Question {q_num}\n"
                f"Date    : {datetime.datetime.now().isoformat()}\n"
                f"Question: {q['question']}\n"
                f"Guidance: {q.get('answer_guidance', '')}\n"
                f"{'='*80}\n\n"
                f"[AGENT EXECUTION LOG]\n"
            )
            print(header)

            final_state = graph.invoke(
                {
                    "messages":            [HumanMessage(content=q["question"])],
                    "seen_errors":         [],
                    "seen_empty":          [],
                    "step_count":          0,
                    "verification_passed": False,
                },
                config=config,
            )

            all_messages = final_state["messages"]

            print(f"\n{'='*80}")
            print("[STATE MESSAGES]\n")
            for i, msg in enumerate(all_messages):
                print(f"--- Message {i+1} ---")
                print(format_message(msg))
                print()

            last = all_messages[-1]
            final_answer = getattr(last, "content", "") or ""
            print(f"\n{'='*80}")
            print(f"FINAL ANSWER:\n{final_answer}")
            print(f"{'='*80}\n")

    print(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()
