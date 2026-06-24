#!/usr/bin/env python3
"""Temporary runner: uses DeepSeek V4 Pro via NIM instead of Llama 3.3."""

import os
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MODEL = "deepseek-ai/deepseek-v4-pro"

import splunk_agent as agent_mod
agent_mod.MODEL = MODEL

import run_all
run_all.MODEL = MODEL

if __name__ == "__main__":
    run_all.main()
