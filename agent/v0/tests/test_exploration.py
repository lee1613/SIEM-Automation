"""The exploration worker: pivot ordering, its budget, and its return schema."""

from exploration import (CONTENT_SCAN_MAX, SYSTEM_PROMPT, make_tools,
                         parse_report, render_report)


class _FakeSplunk:
    """Records the SPL it is asked to run and replays canned rows."""

    def __init__(self, rows=None):
        self.queries = []
        self.rows = rows if rows is not None else []

    def search(self, query, earliest="0", max_results=100, **kw):
        self.queries.append(query)
        return {"results": list(self.rows)}


def _tools(splunk, budget=None):
    return {t.name: t for t in make_tools(splunk, budget or {"content_scans": 0})}


class _AI:
    def __init__(self, tool_calls=None):
        self.tool_calls = tool_calls or []


# ── pivot shapes ───────────────────────────────────────────────────────────────

def test_name_pivot_reads_the_catalogue_not_the_events():
    # `| metadata` is ~1.1s regardless of index size; a raw scan is ~28s. The
    # cheap pivot is also the one that finds cisconvmflowdata.
    sp = _FakeSplunk()
    _tools(sp)["find_feeds_by_name"].invoke({"term": "cisco"})
    assert len(sp.queries) == 2                       # sourcetypes, then sources
    assert all(q.startswith("| metadata") for q in sp.queries)
    assert "type=sourcetypes" in sp.queries[0]
    assert "type=sources" in sp.queries[1]
    assert all("*cisco*" in q for q in sp.queries)
    # time coverage comes free and is how a wrong-window feed gets ruled out
    assert all("firstTime lastTime" in q for q in sp.queries)


def test_field_pivot_matches_names_on_both_axes():
    sp = _FakeSplunk()
    _tools(sp)["find_feeds_by_field"].invoke({"term": "cisco"})
    q = sp.queries[0]
    assert "source=*cisco*" in q and "sourcetype=*cisco*" in q
    assert "stats count by source, sourcetype" in q


def test_content_pivot_scans_raw_text():
    sp = _FakeSplunk()
    _tools(sp)["find_feeds_by_content"].invoke({"term": "monero"})
    q = sp.queries[0]
    assert "index=botsv3 *monero*" in q
    assert "stats count by source, sourcetype" in q


def test_pivots_strip_spl_injection_characters():
    sp = _FakeSplunk()
    _tools(sp)["find_feeds_by_name"].invoke({"term": 'a" | delete '})
    joined = "".join(sp.queries)
    assert "| delete" not in joined       # the pipe is stripped, not passed through
    assert 'a*' not in joined.split("search ")[-1].replace("*a", "")


# ── the content-scan budget ────────────────────────────────────────────────────

def test_content_scans_are_capped_because_they_hold_a_pool_connection():
    # SplunkConnectionPool holds 6 connections and MAX_WORKERS is 6, so a ~30s
    # scan blocks a slot for its whole duration. The prompt asks for restraint;
    # this enforces it.
    sp = _FakeSplunk()
    budget = {"content_scans": 0}
    tool = _tools(sp, budget)["find_feeds_by_content"]
    for _ in range(CONTENT_SCAN_MAX):
        tool.invoke({"term": "x"})
    assert budget["content_scans"] == CONTENT_SCAN_MAX
    out = tool.invoke({"term": "y"})
    assert "budget spent" in out
    assert len(sp.queries) == CONTENT_SCAN_MAX      # the extra call never ran


def test_cheap_pivots_are_not_capped():
    sp = _FakeSplunk()
    t = _tools(sp)
    for _ in range(5):
        t["find_feeds_by_field"].invoke({"term": "x"})
    assert len(sp.queries) == 5


# ── return schema ──────────────────────────────────────────────────────────────

def test_report_parses_into_the_three_field_schema():
    msgs = [_AI([{"name": "report_feeds",
                  "args": {"source_types": "syslog, cisco:asa",
                           "sources": "cisconvmflowdata",
                           "insights": "flow data is under a generic sourcetype"}}])]
    r = parse_report(msgs)
    assert r["source_types"] == ["syslog", "cisco:asa"]
    assert r["sources"] == ["cisconvmflowdata"]
    assert "generic sourcetype" in r["insights"]
    assert r["structured"] is True


def test_no_report_call_is_an_empty_report_not_a_crash():
    r = parse_report([_AI([{"name": "find_feeds_by_name", "args": {"term": "x"}}])])
    assert r == {"source_types": [], "sources": [], "insights": "",
                 "structured": False}


def test_render_report_names_both_axes_for_the_next_worker():
    text = render_report({"source_types": ["syslog"],
                          "sources": ["cisconvmflowdata"],
                          "insights": "matched on name"})
    assert "syslog" in text and "cisconvmflowdata" in text and "matched on name" in text


def test_render_report_says_so_when_nothing_was_found():
    assert "no candidate feeds" in render_report(
        {"source_types": [], "sources": [], "insights": ""})


# ── the prompt encodes the measured ordering ───────────────────────────────────

def test_prompt_orders_the_pivots_cheapest_first():
    assert (SYSTEM_PROMPT.index("find_feeds_by_name")
            < SYSTEM_PROMPT.index("find_feeds_by_field")
            < SYSTEM_PROMPT.index("find_feeds_by_content"))
    assert "Only if both come up empty" in SYSTEM_PROMPT
    assert "do NOT answer" in SYSTEM_PROMPT       # it reports feeds, not answers
