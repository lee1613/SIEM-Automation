#!/usr/bin/env python3
"""Temporary runner: uses GPT-5.4 via OpenAI API instead of Llama 3.3 via NIM.
Patches splunk_agent config before importing, then delegates to run_all logic."""

import os
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    sys.exit("OPENAI_API_KEY not set in .env")

# Patch splunk_agent to use GPT-5.4 via OpenAI before anything imports it
import splunk_agent as agent_mod
agent_mod.NIM_BASE_URL = "https://api.openai.com/v1"
agent_mod.NIM_API_KEY  = OPENAI_API_KEY
agent_mod.MODEL        = "gpt-5.4"

# Now import run_all and patch its constants too
import run_all
run_all.NIM_BASE_URL = "https://api.openai.com/v1"
run_all.NIM_API_KEY  = OPENAI_API_KEY
run_all.MODEL         = "gpt-5.4"

# Monkey-patch extract_clean_answer to use max_completion_tokens for GPT-5.4
from openai import OpenAI as _OpenAI

_orig_extract = run_all.extract_clean_answer

def _patched_extract(nim_client, question, guidance, verbose_answer):
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
        model="gpt-5.4",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=256,
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()

run_all.extract_clean_answer = _patched_extract

if __name__ == "__main__":
    run_all.main()
