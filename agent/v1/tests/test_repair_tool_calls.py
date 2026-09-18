"""Malformed provider tool calls are mended, not crashed on (Q216 r8)."""
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from splunk_agent import repair_tool_calls


@tool
def run_splunk_search(query: str, max_results: int = 50) -> str:
    """search"""
    return ""


@tool
def submit_finding(status: str, value: str, report: str, confidence: int) -> str:
    """finish"""
    return ""


TOOLS = [run_splunk_search, submit_finding]


def _msg(name, args, id_):
    m = AIMessage(content="", tool_calls=[{"name": "x", "args": {}, "id": "i"}])
    return m.model_copy(update={"tool_calls": [{"name": name, "args": args, "id": id_,
                                                "type": "tool_call"}]})


def test_a_nameless_idless_call_is_recovered_by_its_arguments():
    out = repair_tool_calls(_msg("", {"status": "solved", "value": "1", "report": "r",
                                      "confidence": 90}, None), TOOLS)
    tc = out.tool_calls[0]
    assert tc["name"] == "submit_finding" and tc["id"].startswith("call_")


def test_an_ambiguous_nameless_call_keeps_no_name_but_gets_an_id():
    out = repair_tool_calls(_msg("", {}, None), TOOLS)
    assert out.tool_calls[0]["name"] == "" and out.tool_calls[0]["id"]


def test_a_well_formed_call_is_returned_untouched():
    m = _msg("run_splunk_search", {"query": "q"}, "abc")
    assert repair_tool_calls(m, TOOLS) is m
