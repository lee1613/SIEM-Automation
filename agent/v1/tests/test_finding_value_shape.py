"""`value` holds a submittable answer or nothing at all.

Schema B exists so the answer arrives as its own field and needs no scraping.
That only works if `value` actually holds an answer. In test_20260915_174228 it
frequently did not: 16 of 21 `partial` findings carried a `value`, and about ten
of those were prose, a hedge, or a caveat. Every case below is one of them.

The prompt now says this explicitly; these tests are the enforcement, because
the prompt saying it once already failed.
"""

from finding import answer_shaped, parse_finding


class _AI:
    def __init__(self, args):
        self.tool_calls = [{"name": "submit_finding", "args": args}]


def _parse(**args):
    return parse_finding([_AI(args)], "")


# ── real values from test_20260915_174228 that are not answers ─────────────────

NOT_ANSWERS = [
    "High-volume Linux privilege-escalation evidence is concentrated on hoth, "
    "with tomcat8 and kernel artifacts present across the window",        # prose
    "buser?",                                                             # hedge
    "?",                                                                  # no answer at all
    "thumbnail IDs 2,3,4,5\nretrieval timestamps observed",               # multi-line
]

# Also real, also not answers - and shape cannot tell. Both are short enough
# and few enough words to be indistinguishable from "* Ubuntu 16.04.4 kernel
# priv esc". Catching these is the prompt's job, not the guard's, and this list
# is here so that limit stays visible instead of being assumed away.
SHAPE_CANNOT_CATCH = [
    "stream:dns exposes query/queries, answer, dest/dest_ip, src/src_ip",
    "tomcat-users.xml not yet confirmed",
]


def test_none_of_the_observed_non_answers_is_answer_shaped():
    for v in NOT_ANSWERS:
        assert not answer_shaped(v), v


def test_the_documented_blind_spot_is_still_the_blind_spot():
    # If a tightening ever makes these fail, the guard got stricter than the
    # data justifies - check it against the 58 real answers before celebrating.
    for v in SHAPE_CANNOT_CATCH:
        assert answer_shaped(v), v


def test_a_hedged_value_is_moved_to_notes_not_repaired():
    # "buser?" must NOT become "buser". Stripping the hedge manufactures a
    # confident answer out of an admission of doubt.
    f = _parse(status="partial", value="buser?", confidence=93)
    assert f["value"] == ""
    assert "buser?" in f["notes"]


def test_prose_in_value_is_preserved_in_notes_not_dropped():
    prose = NOT_ANSWERS[0]
    f = _parse(status="partial", value=prose, notes="checked hoth only")
    assert f["value"] == ""
    assert prose in f["notes"]
    assert "checked hoth only" in f["notes"]   # the worker's own notes survive


def test_solved_is_demoted_when_its_value_was_not_an_answer():
    # "solved" asserts confidence in a value that no longer exists.
    f = _parse(status="solved", value="the escalation happened via tomcat8 "
                                      "but the exact vector is unclear so far")
    assert f["value"] == ""
    assert f["status"] == "partial"


# ── the values that must survive untouched ────────────────────────────────────

def test_real_answers_pass_through_byte_for_byte():
    for v in ("1367.875", "BSTOLL-L.froth.ly", "nullweb_admin", "Column Chart",
              "bstoll,btun,splunk_access,web_admin",
              "* Ubuntu 16.04.4 kernel priv esc",
              "Frothly-Brewery-Financial-Planning-FY2019-Draft.xlsm"):
        assert answer_shaped(v), v
        assert _parse(status="solved", value=v)["value"] == v


def test_a_solved_finding_with_a_real_value_stays_solved():
    f = _parse(status="solved", value="1666", notes="from cisconvmflowdata")
    assert (f["status"], f["value"], f["notes"]) == ("solved", "1666",
                                                     "from cisconvmflowdata")


def test_an_empty_value_is_left_alone():
    # The documented way to report a partial with no clean candidate.
    f = _parse(status="partial", value="", notes="stream:dns carries the field")
    assert f["value"] == ""
    assert f["notes"] == "stream:dns carries the field"
    assert "[not answer-shaped]" not in f["notes"]
