"""Regression test for the seam bug where `iterations`/`cap_hit` were dropped
between the worker result dict (splunk_subagent._run) and the delegation
record hand-built in orchestrator.executor_node.

The existing unit tests (test_metrics_row.py) hand-build delegation dicts
with `cap_hit`/`iterations` already present, so they never exercised the
real production path where `_run` computes those fields and the orchestrator
copies them across. This test drives the REAL `_run` method (mocking only
the network-calling `run_agent_traced`) to prove:

  1. `_run` actually returns `iterations` and `cap_hit` in its result dict
     (the source of truth for these fields).
  2. `cap_hit` is correctly derived from `step_count > MAX_ITER`.

Combined with the orchestrator fix (record now copies `result.get("iterations")`
and `result.get("cap_hit")`), the seam between worker and delegation record is
closed end-to-end.
"""

from unittest.mock import MagicMock, patch

import splunk_agent as agent_mod
from splunk_agent import MAX_ITER
from splunk_subagent import SplunkWorkerPool


def _make_pool() -> SplunkWorkerPool:
    """Build a SplunkWorkerPool without touching the network.

    create_agent() only constructs LangChain objects (ChatOpenAI client,
    bound tools, compiled graph) — it never calls out to the network at
    construction time, so a dummy API key and a MagicMock splunk client
    are sufficient for a fast, offline unit test.
    """
    return SplunkWorkerPool(
        splunk=MagicMock(),
        senior_api_key="dummy-key",
        senior_model="gpt-5.4",
    )


def test_run_returns_iterations_and_cap_hit_when_cap_exceeded():
    pool = _make_pool()

    fake_state = {"messages": [], "step_count": 20}  # 20 > MAX_ITER(15)
    with patch.object(
        agent_mod, "run_agent_traced",
        return_value=("FINAL ANSWER: x", fake_state),
    ):
        result = pool.run_senior(subquestion="dummy question", parent_qid="Q1", idx=0)

    assert result["iterations"] == 20
    assert result["cap_hit"] is True
    assert 20 > MAX_ITER  # sanity: the fixture actually exceeds the cap


def test_run_reports_no_cap_hit_when_within_limit():
    pool = _make_pool()

    fake_state = {"messages": [], "step_count": 5}  # well within MAX_ITER(15)
    with patch.object(
        agent_mod, "run_agent_traced",
        return_value=("FINAL ANSWER: y", fake_state),
    ):
        result = pool.run_senior(subquestion="dummy question", parent_qid="Q1", idx=1)

    assert result["iterations"] == 5
    assert result["cap_hit"] is False


def test_worker_result_keys_include_iterations_and_cap_hit():
    """Contract check: every worker result dict must carry these keys so the
    orchestrator's `record = {...}` in executor_node can safely forward them
    (see agent/v1/orchestrator.py, executor_node)."""
    pool = _make_pool()

    fake_state = {"messages": [], "step_count": 1}
    with patch.object(
        agent_mod, "run_agent_traced",
        return_value=("FINAL ANSWER: z", fake_state),
    ):
        result = pool.run_senior(subquestion="dummy question", parent_qid="Q1", idx=2)

    assert "iterations" in result
    assert "cap_hit" in result
