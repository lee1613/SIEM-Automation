# agent/v0/tests/test_v050_resilience.py — v0.5.0 R5–R8 (design: docs/version_architecture/v0/v0.5.0.md)
import os
import re

import httpx
import openai
import pytest
import splunk_agent as agent_mod
from langchain_core.messages import AIMessage, HumanMessage
from senior_session import SeniorSession

WINDOW = 100_000
_REQ = httpx.Request("POST", "https://x/v1/chat/completions")


# ── R5 / D8–D9: the graph stops a round at 80% of the window ─────────────────────

SUBMIT = {"name": "submit_finding", "id": "c1", "args": {"status": "partial", "notes": "lead"}}


class _Script:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def factory(self, *a, **k):
        return self

    def bind_tools(self, tools, **k):
        script, names = self, [t.name for t in tools]

        class _Bound:
            def invoke(self, msgs, *a, **k):
                script.calls.append((names, msgs))
                return script.replies.pop(0)
        return _Bound()


def _reply(input_tokens, tool_calls):
    return AIMessage(content="Intention: next", tool_calls=tool_calls,
                     usage_metadata={"input_tokens": input_tokens, "output_tokens": 10,
                                     "total_tokens": input_tokens + 10})


def _run_graph(monkeypatch, first_call_tokens):
    from finding import submit_finding
    script = _Script([_reply(first_call_tokens, [{"name": "get_source_types", "id": "g1", "args": {}}]),
                      AIMessage(content="", tool_calls=[SUBMIT])])
    monkeypatch.setattr(agent_mod, "ChatOpenAI", script.factory)
    graph, _ = agent_mod.create_agent("sk-fake", splunk=None, base_url="https://x/v1",
                                      extra_tools=[submit_finding], max_iter=25,
                                      context_window=WINDOW)
    state = graph.invoke({"messages": [HumanMessage("find it")], "step_count": 0},
                         {"configurable": {"thread_id": "t"}, "recursion_limit": 100})
    return state, script


def test_a_call_at_80_percent_of_the_window_ends_the_round_with_a_handover(monkeypatch):
    state, script = _run_graph(monkeypatch, int(agent_mod.COMPACT_AT * WINDOW))
    names, msgs = script.calls[1]
    assert names == ["submit_finding"], "past the threshold the tools are withdrawn"
    assert "handover" in msgs[-1].content.lower(), "the senior is asked for the handover template"
    assert state.get("context_full") is True


def test_a_call_under_80_percent_keeps_the_tools(monkeypatch):
    state, script = _run_graph(monkeypatch, int(agent_mod.COMPACT_AT * WINDOW) - 1)
    names, _ = script.calls[1]
    assert "get_source_types" in names
    assert not state.get("context_full")


# ── R5 / D9–D11: the session continues on a fresh thread ─────────────────────────

class _Pool:
    def __init__(self, results):
        self.results, self.rounds, self.clarifies = list(results), [], []

    def run_round(self, **kw):
        self.rounds.append(kw)
        return self.results.pop(0) if len(self.results) > 1 else dict(self.results[0])

    def clarify(self, **kw):
        self.clarifies.append(kw)
        return "answer"


def _result(status, iterations, report="REPORT", tokens=1_000):
    return {"status": status, "value": "", "value_kind": "", "evidence": "", "confidence": 40,
            "notes": "", "insight": "", "report": report, "spl_used": ["index=botsv3 | head 1"],
            "sourcetypes": [], "negative_findings": [], "iterations": iterations,
            "cap_hit": False, "structured": True, "last_prompt_tokens": tokens,
            "answer": "", "full_state": [],
            "search_space_used": {"sourcetypes": [], "sources": []}}


def _session(pool, iters=25):
    return SeniorSession(sid="s1", pool=pool, qid="Q328", technique="senior",
                         subquestion="Find the file.", brief="BRIEF", window=WINDOW,
                         rounds_granted=4, iters=iters)


def test_a_context_full_round_continues_on_a_fresh_thread_with_the_calls_left():
    pool = _Pool([_result("context_full", 10, report="HANDOVER-1", tokens=81_000),
                  _result("partial", 5, report="AFTER")])
    s = _session(pool)
    out = s.work("go", rounds_remaining=3)
    first, second = pool.rounds
    assert second["thread_id"] != first["thread_id"]
    assert "BRIEF" in second["message"] and "HANDOVER-1" in second["message"]
    assert second["budget"] == 25 - 10, "the handover continues the same round's budget"
    assert s.rounds_used == 1 and s.compactions == 1, "a handover costs no round"
    assert "AFTER" in out["report"]


def test_handovers_repeat_until_the_round_budget_is_spent():
    pool = _Pool([_result("context_full", 10, tokens=81_000),
                  _result("context_full", 10, tokens=81_000),
                  _result("partial", 5)])
    _session(pool).work("go", rounds_remaining=3)
    assert [r["budget"] for r in pool.rounds] == [25, 15, 5]


def test_a_seed_that_is_already_over_the_threshold_fails_instead_of_looping():
    pool = _Pool([_result("context_full", 10, tokens=81_000),
                  _result("context_full", 1, tokens=90_000)])
    out = _session(pool).work("go", rounds_remaining=3)
    assert len(pool.rounds) == 2
    assert out["status"] == "context_full"


def test_a_clarify_at_the_threshold_hands_over_first():
    s = _session(_Pool([_result("partial", 5)]))
    s.last_prompt_tokens, s.last_report = 80_000, "LAST REPORT"
    old = s.thread_id
    s.clarify(["which host?"])
    kw = s.pool.clarifies[0]
    assert kw["thread_id"] != old
    assert "BRIEF" in kw["seed"] and "LAST REPORT" in kw["seed"]


def test_a_clarify_under_the_threshold_stays_on_its_thread():
    s = _session(_Pool([_result("partial", 5)]))
    s.last_prompt_tokens, old = 79_999, s.thread_id
    s.clarify(["which host?"])
    assert s.pool.clarifies[0]["thread_id"] == old and not s.pool.clarifies[0].get("seed")


def test_a_crashed_round_still_records_its_size():
    s = _session(_Pool([_result("api_failed", 0, tokens=150_000)]))
    s.work("go", rounds_remaining=3)
    assert s.last_prompt_tokens == 150_000, "I7: the oversized request must stay visible"


def test_the_between_round_projection_is_gone():
    import senior_session
    assert not hasattr(senior_session, "should_compact"), "D8: one mechanism, not two"


# ── R6 / D12: a call gives up within the deadline ────────────────────────────────

def test_a_timed_out_call_gives_up_within_ten_minutes():
    assert agent_mod.LLM_TIMEOUT_S == 120
    assert (1 + agent_mod.LLM_MAX_RETRIES) * agent_mod.LLM_TIMEOUT_S <= 600


# ── R7 / D13: brief API errors are retried with long waits ───────────────────────

def _flaky(errors):
    seq = list(errors)

    def fn():
        if seq:
            raise seq.pop(0)
        return "ok"
    return fn


def _status(code):
    cls = {400: openai.BadRequestError, 500: openai.InternalServerError}.get(code, openai.APIStatusError)
    return cls("boom", response=httpx.Response(code, request=_REQ), body=None)


def test_502s_are_retried_with_the_designed_waits():
    from llm_errors import retry_transient
    slept = []
    assert retry_transient(_flaky([_status(502), _status(502)]), sleep=slept.append) == "ok"
    assert slept == [30, 60]


def test_a_connection_error_is_retried():
    from llm_errors import retry_transient
    slept = []
    assert retry_transient(_flaky([openai.APIConnectionError(request=_REQ)]), sleep=slept.append) == "ok"
    assert slept == [30]


def test_a_timeout_is_not_retried_by_the_outer_loop():
    from llm_errors import retry_transient
    slept = []
    with pytest.raises(openai.APITimeoutError):
        retry_transient(_flaky([openai.APITimeoutError(request=_REQ)]), sleep=slept.append)
    assert slept == [], "D12 already bounds timeouts; an oversized request would only stall again"


def test_a_client_error_is_not_retried():
    from llm_errors import retry_transient
    with pytest.raises(openai.BadRequestError):
        retry_transient(_flaky([_status(400)]), sleep=lambda s: None)


def test_the_fourth_failure_falls_through_to_todays_handling():
    from llm_errors import retry_transient
    slept = []
    with pytest.raises(openai.InternalServerError):
        retry_transient(_flaky([_status(500)] * 4), sleep=slept.append)
    assert slept == [30, 60, 120]


# ── R8 / D14: a locked file swap is retried, everywhere ──────────────────────────

def test_a_briefly_locked_swap_is_retried(monkeypatch, tmp_path):
    import fileio
    real, fails, slept = os.replace, [PermissionError(13, "locked")] * 2, []

    def flaky(src, dst):
        if fails:
            raise fails.pop()
        real(src, dst)
    monkeypatch.setattr(fileio.os, "replace", flaky)
    (tmp_path / "a.tmp").write_text("x")
    fileio.atomic_replace(str(tmp_path / "a.tmp"), str(tmp_path / "a"), sleep=slept.append)
    assert (tmp_path / "a").read_text() == "x" and slept == [0.2, 0.2]


def test_a_swap_locked_for_good_still_raises(monkeypatch, tmp_path):
    import fileio

    def locked(src, dst):
        raise PermissionError(13, "locked")
    monkeypatch.setattr(fileio.os, "replace", locked)
    with pytest.raises(PermissionError):
        fileio.atomic_replace(str(tmp_path / "a.tmp"), str(tmp_path / "a"), sleep=lambda s: None)


def test_every_file_swap_goes_through_the_helper():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bare = []
    for dirpath, _, files in os.walk(root):
        if "tests" in dirpath.split(os.sep):
            continue
        for f in files:
            if f.endswith(".py") and f != "fileio.py":
                text = open(os.path.join(dirpath, f), encoding="utf-8").read()
                if re.search(r"\bos\.replace\(", text):
                    bare.append(f)
    assert bare == [], f"I9: bare os.replace in {bare}"
