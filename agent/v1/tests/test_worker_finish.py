"""A worker round must end with a finding, not silently.

Q216 smoke test test_20260917_231500: GLM-5.3 on Featherless returned a reply
with no text and no tool call (a tool call its parser failed to extract), on the
8th iteration of round 1 and on the 1st of round 2. should_continue read "no
tool calls" as done, so both rounds reached SH as blank NOT_FOUND reports while
the senior had real leads in its transcript.
"""

import builtins

import pytest
import splunk_agent as agent_mod
from hitl import RunPaused, resolve_interrupt
from langchain_core.messages import AIMessage, HumanMessage

SUBMIT = {"name": "submit_finding", "id": "c1",
          "args": {"status": "partial", "notes": "port 3333 lead"}}


class _Script:
    """Stands in for ChatOpenAI: records which tools each call had bound."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []                      # (bound tool names, messages)

    def factory(self, *a, **k):
        return self

    def bind_tools(self, tools, **k):
        script, names = self, [t.name for t in tools]

        class _Bound:
            def invoke(self, msgs, *a, **k):
                script.calls.append((names, msgs))
                return script.replies.pop(0)
        return _Bound()


def _graph(monkeypatch, replies, max_iter=8):
    from finding import submit_finding
    script = _Script(replies)
    monkeypatch.setattr(agent_mod, "ChatOpenAI", script.factory)
    graph, _ = agent_mod.create_agent("sk-fake", splunk=None, base_url="https://x/v1",
                                      extra_tools=[submit_finding], max_iter=max_iter)
    return graph, script


def _invoke(graph):
    return graph.invoke({"messages": [HumanMessage("find the miner")], "step_count": 0},
                        {"configurable": {"thread_id": "t"}, "recursion_limit": 40})


def test_an_empty_reply_is_asked_once_more_for_submit_finding(monkeypatch):
    graph, script = _graph(monkeypatch, [AIMessage(content=""),
                                         AIMessage(content="", tool_calls=[SUBMIT])])
    state = _invoke(graph)

    assert len(script.calls) == 2
    names, msgs = script.calls[1]
    assert names == ["submit_finding"], "the retry must only offer submit_finding"
    assert "empty" in msgs[-1].content.lower()
    assert state["messages"][-1].tool_calls[0]["name"] == "submit_finding"


def test_submit_finding_ends_the_round_without_another_model_call(monkeypatch):
    # Before: submit_finding went verify -> execute -> agent, one more paid call,
    # and a second empty reply there would have been nudged into a second finding.
    graph, script = _graph(monkeypatch, [AIMessage(content="Intention: done",
                                                   tool_calls=[SUBMIT])])
    _invoke(graph)
    assert len(script.calls) == 1


def test_an_empty_reply_without_a_terminal_tool_still_ends(monkeypatch):
    # v0 binds no submit_finding: there is nothing to nudge towards.
    script = _Script([AIMessage(content="")])
    monkeypatch.setattr(agent_mod, "ChatOpenAI", script.factory)
    graph, _ = agent_mod.create_agent("sk-fake", splunk=None, base_url="https://x/v1")
    _invoke(graph)
    assert len(script.calls) == 1


def test_a_closed_stdin_that_claims_to_be_a_tty_pauses_instead_of_crashing(tmp_path, monkeypatch):
    # Git Bash background shells report isatty() True with stdin already at EOF:
    # input() raised EOFError and killed the whole run mid-question.
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)

    def _eof(*a, **k):
        raise EOFError
    monkeypatch.setattr(builtins, "input", _eof)
    interrupt = type("I", (), {"value": {"provider": "api.featherless.ai",
                                         "error": "boom", "qids": ["Q216"],
                                         "options": ["skip", "abort"]}})()

    with pytest.raises(RunPaused) as paused:
        resolve_interrupt([interrupt], qid="Q216", run_dir=str(tmp_path))
    assert (tmp_path / "decision_request.json").exists()
    assert paused.value.request_path.endswith("decision_request.json")
