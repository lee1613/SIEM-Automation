"""SH's structured plan, the dataset briefing, and the task shape they produce."""

import pytest
from plan_schema import Plan, Spawn, render_briefing, render_plan_text, render_scope, to_tasks
from pydantic import ValidationError


def _spawn(**kw):
    base = dict(spawn_type="senior", subquestion="find X", sourcetypes=[],
                sources=[], prior_info="", confidence=50, deps=[])
    base.update(kw)
    return Spawn(**base)


def _plan(*spawns, direct=""):
    return Plan(goal="g", expected_shape="integer", direct_answer=direct,
                spawns=list(spawns))


_MANIFEST = {
    "source_types": {"syslog": {"fields": []}, "cisco:asa": {"fields": []}},
    "sources": [
        {"source": "lsof", "sourcetype": "lsof", "count": 322336},
        {"source": "cisconvmflowdata", "sourcetype": "syslog", "count": 78459},
        {"source": "tiny", "sourcetype": "syslog", "count": 3},
    ],
}


# ── schema ─────────────────────────────────────────────────────────────────────

def test_confidence_outside_0_100_is_rejected():
    # The field is recorded and calibrated, so an out-of-range value would
    # silently corrupt the decile table spawn_report builds.
    with pytest.raises(ValidationError):
        _spawn(confidence=101)
    with pytest.raises(ValidationError):
        _spawn(confidence=-1)


def test_spawn_type_is_constrained():
    with pytest.raises(ValidationError):
        _spawn(spawn_type="junior")


def test_both_axes_are_carried_into_the_task():
    t = to_tasks(_plan(_spawn(sourcetypes=["syslog"],
                              sources=["cisconvmflowdata"])))[0]
    assert t["search_space"] == {"sourcetypes": ["syslog"],
                                 "sources": ["cisconvmflowdata"]}


def test_a_source_only_scope_is_valid():
    # The Q216 case: the feed is addressable only by source, because its
    # sourcetype is the generic `syslog`.
    t = to_tasks(_plan(_spawn(sources=["cisconvmflowdata"])))[0]
    assert t["search_space"]["sourcetypes"] == []
    assert t["search_space"]["sources"] == ["cisconvmflowdata"]


# ── deps ───────────────────────────────────────────────────────────────────────

def test_tasks_are_numbered_from_one_to_match_dollar_n():
    tasks = to_tasks(_plan(_spawn(), _spawn(), _spawn()))
    assert [t["idx"] for t in tasks] == [1, 2, 3]


def test_dangling_and_self_deps_are_dropped():
    # A dep on a task that does not exist would stall its wave forever.
    tasks = to_tasks(_plan(_spawn(), _spawn(deps=[1, 2, 99])))
    assert tasks[1]["deps"] == [1]


def test_independent_spawns_stay_parallel():
    tasks = to_tasks(_plan(_spawn(), _spawn()))
    assert all(t["deps"] == [] for t in tasks)


# ── briefing ───────────────────────────────────────────────────────────────────

def test_briefing_names_both_axes_and_ranks_by_volume():
    b = render_briefing(_MANIFEST, top_n=2)
    assert "cisco:asa, syslog" in b          # sourcetypes, sorted
    assert "source=" in b                    # the two-axis warning
    # busiest first, checked inside the source list - the warning above it also
    # names cisconvmflowdata, so a whole-document index would compare the wrong text
    listing = b.split("SOURCES of", 1)[1]
    assert listing.index("lsof") < listing.index("cisconvmflowdata")
    assert "322,336" in listing


def test_briefing_caps_sources_and_says_what_it_omitted():
    b = render_briefing(_MANIFEST, top_n=2)
    assert "tiny" not in b
    assert "1 lower-volume" in b
    assert "exploration worker" in b


def test_briefing_survives_a_manifest_with_no_sources_block():
    b = render_briefing({"source_types": {"syslog": {}}})
    assert "syslog" in b


# ── scope rendering ────────────────────────────────────────────────────────────

def test_scope_tells_the_worker_where_to_start_without_caging_it():
    # A worker forbidden to look outside SH's guess cannot correct SH's guess.
    t = to_tasks(_plan(_spawn(sourcetypes=["syslog"], sources=["cisconvmflowdata"],
                              prior_info="host BSTOLL-L")))[0]
    scope = render_scope(t)
    assert "syslog" in scope and "cisconvmflowdata" in scope
    assert "widen the hunt" in scope
    assert "host BSTOLL-L" in scope


def test_scope_is_empty_when_nothing_was_named():
    assert render_scope(to_tasks(_plan(_spawn()))[0]) == ""


# ── plan text (what re-enters cross-question memory) ───────────────────────────

def test_plan_text_records_scope_and_confidence_for_later_rounds():
    txt = render_plan_text(_plan(
        _spawn(sourcetypes=["syslog"], confidence=70),
        _spawn(spawn_type="exploration", confidence=20, deps=[1])))
    assert "conf=70" in txt and "conf=20" in txt
    assert "exploration" in txt
    assert "deps=[1]" in txt


def test_direct_answer_plan_carries_no_tasks():
    plan = _plan(direct="mkraeusen")
    assert to_tasks(plan) == []
    assert "DIRECT ANSWER: mkraeusen" in render_plan_text(plan)


# ── the joiner reads these dicts ───────────────────────────────────────────────

def test_task_dicts_expose_the_keys_the_joiner_and_record_read():
    # Regression: the joiner did `Task(**t)`, which raised TypeError as soon as
    # tasks carried spawn_type/search_space/prior_info/confidence.
    t = to_tasks(_plan(_spawn()))[0]
    for key in ("idx", "subquestion", "deps", "spawn_type", "search_space",
                "prior_info", "confidence"):
        assert key in t, key
