from types import SimpleNamespace

from finding import empty_finding, parse_finding


def _msg(**args):
    return SimpleNamespace(tool_calls=[{"name": "submit_finding", "args": args}])


def test_insight_and_report_survive_the_tool_call():
    f = parse_finding([_msg(status="partial", value="", insight="NOT_FOUND",
                            report="# r\n## Prior rounds\n- none")], "")
    assert f["insight"] == "NOT_FOUND"
    assert f["report"].startswith("# r")


def test_insight_is_normalised_to_the_two_legal_values():
    f = parse_finding([_msg(status="solved", value="42", confidence=90,
                            insight="found", report="r")], "")
    assert f["insight"] == "FOUND"


def test_a_missing_insight_is_inferred_from_whether_a_value_was_committed():
    with_value = parse_finding([_msg(status="partial", value="42")], "")
    without    = parse_finding([_msg(status="partial", value="")], "")
    assert with_value["insight"] == "FOUND"
    assert without["insight"] == "NOT_FOUND"


def test_a_non_answer_shaped_value_reports_not_found():
    # answer_shaped demotes the value to notes, so there is no candidate to call FOUND
    f = parse_finding([_msg(status="solved", value="the password sat in cloud-init "
                                                   "raw text on a host we have not named yet",
                            insight="FOUND")], "")
    assert f["value"] == ""
    assert f["insight"] == "NOT_FOUND"


def test_empty_finding_carries_the_new_keys():
    e = empty_finding("api_failed")
    assert e["insight"] == "NOT_FOUND"
    assert e["report"] == ""


def test_prose_fallback_still_produces_the_new_keys():
    f = parse_finding([], "FINAL ANSWER: 42")
    assert f["insight"] == "NOT_FOUND" and f["report"] == ""


def test_explicit_none_report_and_insight_are_null_safe():
    f = parse_finding([_msg(status="partial", value="", report=None, insight=None)], "")
    assert f["report"] == ""
    assert f["insight"] == "NOT_FOUND"


def test_insight_normalisation_tolerates_hyphens_and_no_separators():
    hyphenated = parse_finding([_msg(status="partial", value="42", insight="Not-Found")], "")
    smashed    = parse_finding([_msg(status="partial", value="42", insight="NOTFOUND")], "")
    assert hyphenated["insight"] == "NOT_FOUND"
    assert smashed["insight"] == "NOT_FOUND"
