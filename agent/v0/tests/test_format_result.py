"""A row-capped result must say which rows the model never saw (Q216 r5: 50 of 1573)."""
import json

from splunk_agent import _format_result


def test_a_row_capped_result_says_how_many_rows_went_unseen():
    rows = [{"dh": f"h{i}", "count": "9"} for i in range(50)]
    out = json.loads(_format_result({"results": rows,
                                     "_meta": {"total_event_count": 1573, "returned": 50}}))
    assert "showing 50 of 1573 rows" in out["meta"]["truncated"]
    assert "other 1523 were not returned" in out["meta"]["truncated"]


def test_a_complete_result_carries_no_truncation_note():
    out = json.loads(_format_result({"results": [{"a": "1"}],
                                     "_meta": {"total_event_count": 1, "returned": 1}}))
    assert "truncated" not in out["meta"]


def test_an_oversized_event_is_clipped_not_dropped():
    # Q217 smoke5_r1: one stream:smtp event outgrew the budget and 0 of 10 rows came back.
    rows = [{"attach_filename{}": ["chart.png"], "content{}": ["x" * 20_000]}]
    out = json.loads(_format_result({"results": rows,
                                     "_meta": {"total_event_count": 1, "returned": 1}}))
    assert out["results"][0]["attach_filename{}"] == ["chart.png"]
    assert "more chars cut" in out["results"][0]["content{}"][0]
