"""Regression: run_1.2 Q202 — verifier/joiner must judge against the CURRENT
question, and SH history fed to the LLM must be bounded."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator import MAX_HISTORY_MSGS, DelegationContext, _window


def test_reset_question_stores_question_text():
    ctx = DelegationContext(pool=None, logger=None)
    ctx.reset_question("Q202", points=500, question="What is the processor number?")
    assert ctx.current_question == "What is the processor number?"
    assert ctx.current_qid == "Q202"
    assert ctx.current_points == 500


def test_reset_question_replaces_previous_question():
    ctx = DelegationContext(pool=None, logger=None)
    ctx.reset_question("Q200", points=100, question="List IAM users")
    ctx.reset_question("Q202", points=500, question="What is the processor number?")
    assert ctx.current_question == "What is the processor number?"


def test_window_caps_history():
    msgs = list(range(100))
    out = _window(msgs)
    assert len(out) == MAX_HISTORY_MSGS
    assert out[-1] == 99  # keeps the most recent messages


def test_window_passes_short_history_through():
    msgs = list(range(5))
    assert _window(msgs) == msgs
