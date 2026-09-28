from finding import empty_finding, parse_finding


class _Call:
    """A message carrying one submit_finding tool call, as parse_finding scans for."""

    def __init__(self, args):
        self.tool_calls = [{"name": "submit_finding", "args": args}]


def _parse(**args):
    return parse_finding([_Call({"insight": "FOUND", "value": "112", **args})], "")


def test_premise_drafts_come_back_as_objects():
    f = _parse(new_premises=[{"text": "the flow is inbound-heavy", "kind": "other",
                              "load_bearing": True}])
    assert f["new_premises"][0].text == "the flow is inbound-heavy"
    assert f["new_premises"][0].load_bearing is True


def test_premise_drafts_survive_arriving_as_a_json_string():
    """Some providers flatten a list[object] tool argument to a string (Task 0)."""
    f = _parse(new_premises='[{"text": "the flow is inbound-heavy", '
                            '"kind": "other", "load_bearing": true}]')
    assert f["new_premises"][0].kind == "other"


def test_a_draft_missing_a_field_gets_a_safe_default_not_a_crash():
    f = _parse(new_premises=[{"text": "no kind given"}])
    assert f["new_premises"][0].kind == "other"
    assert f["new_premises"][0].load_bearing is False


def test_a_malformed_draft_is_dropped_not_fatal():
    f = _parse(new_premises=[{"kind": "other"}, "just a string",
                             {"text": "kept", "kind": "other", "load_bearing": False}])
    assert [p.text for p in f["new_premises"]] == ["just a string", "kept"]


def test_updates_come_back_as_objects():
    f = _parse(premise_updates=[{"id": "p1", "status": "VERIFIED",
                                 "quote": "ibc=5782875", "evidence": "why"}])
    assert f["premise_updates"][0].id == "p1"
    assert f["premise_updates"][0].status == "VERIFIED"


def test_an_update_with_an_illegal_status_is_dropped():
    f = _parse(premise_updates=[{"id": "p1", "status": "MAYBE", "quote": "x",
                                 "evidence": "y"}])
    assert f["premise_updates"] == []


def test_open_questions_come_back_as_plain_strings():
    f = _parse(open_questions=["which feed owns the byte counts?", "  ", "and this?"])
    assert f["open_questions"] == ["which feed owns the byte counts?", "and this?"]


def test_a_finding_with_no_premise_fields_is_still_valid():
    f = _parse()
    assert f["new_premises"] == [] and f["premise_updates"] == []
    assert f["open_questions"] == []


def test_empty_finding_carries_the_new_keys():
    e = empty_finding("failed")
    assert e["new_premises"] == [] and e["premise_updates"] == []
    assert e["open_questions"] == []
