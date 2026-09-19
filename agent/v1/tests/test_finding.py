"""Schema B: the worker's structured return, and its prose fallback."""

from case_file import build_ledger, finalize_answer
from finding import parse_finding, submit_finding
from grounding import is_grounded


class _AI:
    """Minimal stand-in for an AIMessage carrying tool calls."""

    def __init__(self, tool_calls=None, content=""):
        self.tool_calls = tool_calls or []
        self.content = content


def _call(**args):
    return [_AI([{"name": "submit_finding", "args": args}])]


# ── the structured path ────────────────────────────────────────────────────────

def test_value_arrives_as_its_own_field_not_scraped_from_prose():
    f = parse_finding(_call(status="solved", value="1367.875",
                            value_kind="duration_seconds"), "")
    assert f["structured"] is True
    assert f["value"] == "1367.875"
    assert f["value_kind"] == "duration_seconds"
    assert f["status"] == "solved"


def test_ruled_out_becomes_negative_findings():
    # The point of the field: 73% of delegations end partial/failed, and what
    # they eliminated used to be discarded, so replan rounds re-tread dead ends.
    f = parse_finding(_call(status="failed",
                            ruled_out="cisco:asa - no flow duration field, "
                                      "stream:ip - wrong time window"), "")
    assert f["negative_findings"] == [
        "cisco:asa - no flow duration field",
        "stream:ip - wrong time window",
    ]


def test_search_space_used_splits_both_axes():
    f = parse_finding(_call(status="solved", value="x",
                            sourcetypes_used="syslog, cisco:asa",
                            sources_used="cisconvmflowdata"), "")
    assert f["search_space_used"] == {
        "sourcetypes": ["syslog", "cisco:asa"],
        "sources": ["cisconvmflowdata"],
    }


def test_confidence_is_clamped_and_survives_a_string():
    assert parse_finding(_call(status="solved", value="x", confidence=140), "")["confidence"] == 100
    assert parse_finding(_call(status="solved", value="x", confidence=-5), "")["confidence"] == 0
    assert parse_finding(_call(status="solved", value="x", confidence="70"), "")["confidence"] == 70
    assert parse_finding(_call(status="solved", value="x", confidence="n/a"), "")["confidence"] is None


def test_unknown_status_is_inferred_rather_than_discarded():
    # A worker that did the work but mislabelled the outcome keeps its value.
    assert parse_finding(_call(status="done", value="2059"), "")["status"] == "partial"
    assert parse_finding(_call(status="done", value=""), "")["status"] == "failed"


def test_the_last_submit_finding_call_wins():
    msgs = [_AI([{"name": "submit_finding", "args": {"status": "partial", "value": "old"}}]),
            _AI([{"name": "run_splunk_search", "args": {"query": "..."}}]),
            _AI([{"name": "submit_finding", "args": {"status": "solved", "value": "new"}}])]
    assert parse_finding(msgs, "")["value"] == "new"


# ── the prose fallback ─────────────────────────────────────────────────────────

def test_no_tool_call_falls_back_to_prose_tags():
    f = parse_finding([_AI(content="FINAL ANSWER: mkraeusen")],
                      "FINAL ANSWER: mkraeusen")
    assert f["structured"] is False
    assert f["status"] == "solved"
    assert f["value"] == ""          # nothing to trust as a bare value


def test_prose_fallback_status_vocabulary():
    assert parse_finding([], "PARTIAL ANSWER: 13139")["status"] == "partial"
    assert parse_finding([], "ESCALATE: too broad")["status"] == "too_big"
    assert parse_finding([], "")["status"] == "failed"
    # a non-empty tail with no tag never counts as an answer
    assert parse_finding([], "I looked at several sourcetypes.")["status"] == "failed"


# ── what the schema buys downstream ────────────────────────────────────────────

def test_ledger_reads_value_without_needing_a_final_answer_tag():
    deleg = {"value": "BSTOLL-L.froth.ly", "status": "solved", "worker": "senior#1",
             "answer": "", "spl_used": ["index=botsv3 ..."], "evidence": "12 events"}
    ledger = build_ledger([deleg])
    assert [c["value"] for c in ledger] == ["BSTOLL-L.froth.ly"]
    assert ledger[0]["evidence"] == "12 events"


def test_grounding_accepts_a_value_that_never_appears_in_prose():
    # run_1.2's fabrication guard required the answer as a substring of a
    # worker's sentence. A structured value grounds on the field itself.
    results = {1: {"answer": "see attached", "value": "1367.875", "status": "solved"}}
    assert is_grounded("1367.875", results, "how long did it run?")
    assert not is_grounded("1499.25", results, "how long did it run?")


def test_submit_finding_tool_is_callable_and_terminal():
    out = submit_finding.invoke({"insight": "FOUND", "value": "2059"})
    assert "do not call any further tools" in out.lower()


def test_finalize_answer_no_longer_strips_labels():
    delegs = [{"value": "2059", "status": "solved", "worker": "senior#1",
               "answer": "", "spl_used": []}]
    assert finalize_answer("2059", delegs) == "2059"
    assert finalize_answer("UF = 2059", delegs) == "UF = 2059"


def test_status_is_derived_from_insight_when_the_worker_sends_none():
    # insight is the worker's one outcome scale; status is derived for the ledger.
    from langchain_core.messages import AIMessage
    def call(**args):
        return [AIMessage(content="", tool_calls=[{"name": "submit_finding", "args": args,
                                                    "id": "c1", "type": "tool_call"}])]
    assert parse_finding(call(insight="FOUND", value="1666", confidence=80), "")["status"] == "solved"
    assert parse_finding(call(insight="NOT_FOUND", notes="lead ruled out"), "")["status"] == "partial"
    assert parse_finding(call(insight="NOT_FOUND"), "")["status"] == "failed"
