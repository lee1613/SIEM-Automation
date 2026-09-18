# agent/v1/tests/test_senior_report.py
from senior_report import (
    PRIOR_ROUNDS_MAX_LINES,
    REPORT_WORD_CAP,
    novel_spl,
    open_questions,
    report_violations,
    stamp_header,
    truncate_words,
    unverified_premises,
)

GOOD = """# Senior #1 - Q216 - Round 1
**Scope:** sourcetype=cisco:nvm | source=cisconvmflowdata | fields=duration
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
- Round 1: first round.

## This round
### What I ran
- index=botsv3 sourcetype=cisco:nvm | stats count -> 0 events
### What it means
The feed carries no events in the window, so this scope cannot hold the answer.

## Assumptions
- The window SH gave me is the incident window - UNVERIFIED

## Ruled out
- cisco:nvm - no events in the given window

## Open questions for SH
- Is the window you gave me the incident window, or the whole index?
"""


def test_a_repeated_query_counts_as_zero_novel():
    prior = {"index=botsv3 sourcetype=aws:cloudtrail | stats count"}
    n, updated = novel_spl(prior, ["index=botsv3  SOURCETYPE=aws:cloudtrail | stats count"])
    assert n == 0
    assert updated == prior


def test_a_new_query_counts_as_one_novel():
    prior = {"index=botsv3 | stats count"}
    n, updated = novel_spl(prior, ["index=botsv3 sourcetype=stream:dns | stats count"])
    assert n == 1
    assert len(updated) == 2


def test_novel_spl_counts_distinct_queries_only():
    n, _ = novel_spl(set(), ["search a", "search a", "search b"])
    assert n == 2


def test_no_queries_at_all_is_zero_novel():
    n, updated = novel_spl({"x"}, [])
    assert n == 0 and updated == {"x"}


def test_truncate_words_leaves_a_short_report_alone():
    out, cut = truncate_words("one two three", cap=REPORT_WORD_CAP)
    assert out == "one two three" and cut is False


def test_truncate_words_cuts_at_the_cap_and_flags_it():
    out, cut = truncate_words(" ".join(["w"] * (REPORT_WORD_CAP + 50)))
    assert cut is True
    assert len(out.split()) <= REPORT_WORD_CAP + 10        # + the truncation marker
    assert "[truncated" in out


def test_a_good_report_has_no_violations():
    assert report_violations(GOOD) == []


def test_a_missing_section_is_a_violation():
    assert report_violations(GOOD.replace("## Ruled out", "## Notes")) != []


def test_prior_rounds_over_six_lines_is_a_violation():
    bloated = GOOD.replace(
        "- Round 1: first round.",
        "\n".join(f"- Round {i}: something." for i in range(1, PRIOR_ROUNDS_MAX_LINES + 3)))
    assert report_violations(bloated) != []


def test_the_runner_stamps_round_rounds_remaining_and_novel_spl():
    out = stamp_header(GOOD, senior_id="s1", qid="Q216", round_n=3,
                       rounds_remaining=5, novel_spl_count=2)
    assert out.splitlines()[0] == "# s1 - Q216 - Round 3"
    assert "rounds_remaining=5" in out
    assert "novel_spl=2" in out


def test_stamping_replaces_a_self_reported_header():
    out = stamp_header(GOOD, senior_id="s1", qid="Q216", round_n=3,
                       rounds_remaining=5, novel_spl_count=2)
    assert "# Senior #1 - Q216 - Round 1" not in out


def test_stamping_an_empty_report_still_produces_a_header():
    out = stamp_header("", senior_id="s2", qid="Q999", round_n=1,
                       rounds_remaining=0, novel_spl_count=0)
    assert out.startswith("# s2 - Q999 - Round 1")


def test_truncate_words_preserves_newlines_in_multiline_report():
    """Truncation should preserve original whitespace, not join all words."""
    multiline = "line one\nline two\nline three\n" + " ".join(["word"] * (REPORT_WORD_CAP + 50))
    out, cut = truncate_words(multiline)
    assert cut is True
    assert out.startswith("line one\nline two\nline three\n")  # Original lines with newlines preserved
    assert "[truncated" in out


def test_truncate_then_stamp_preserves_sections():
    """Integration test: truncate then stamp should not lose report structure."""
    long_report = GOOD + " " + " ".join(["filler"] * 420)
    truncated, _ = truncate_words(long_report)
    stamped = stamp_header(truncated, senior_id="s1", qid="Q216", round_n=1,
                          rounds_remaining=5, novel_spl_count=2)
    assert "## Prior rounds" in stamped
    assert "## Ruled out" in stamped


def test_stamp_header_removes_title_anywhere_in_body():
    """Title line matching ^# can appear anywhere, not just at position 0."""
    report_with_preamble = "Here is my report:\n# Senior #1 - Q216 - Round 1\n## Prior rounds\nfoo"
    out = stamp_header(report_with_preamble, senior_id="s1", qid="Q216", round_n=2,
                      rounds_remaining=5, novel_spl_count=1)
    assert "# Senior #1 - Q216 - Round 1" not in out  # Old title removed
    assert "Here is my report:" in out  # Preamble preserved
    assert out.splitlines()[0].startswith("# s1 - Q216 - Round 2")  # New title first


def test_stamp_header_removes_prior_runner_stamps():
    """Any prior _stamped by runner: line should be removed."""
    old_stamp = """# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=5 novel_spl=0_
## Prior rounds
content"""
    out = stamp_header(old_stamp, senior_id="s1", qid="Q216", round_n=2,
                      rounds_remaining=5, novel_spl_count=2)
    assert "_stamped by runner: rounds_remaining=5 novel_spl=0_" not in out
    assert "rounds_remaining=5" in out  # New stamp is there
    assert "novel_spl=2" in out


def test_report_violations_checks_prior_rounds_even_at_end():
    """Prior rounds section can appear last; cap should still be checked."""
    report = """# Senior #1 - Q216 - Round 1
**Scope:** sourcetype=test
**Insight:** NOT_FOUND
**Candidate:** none **Confidence:** 20

## This round
### What I ran
- query
### What it means
result

## Ruled out
- feed

## Open questions for SH
- question

## Prior rounds
- Round 1: a.
- Round 2: b.
- Round 3: c.
- Round 4: d.
- Round 5: e.
- Round 6: f.
- Round 7: g.
- Round 8: h.
"""
    violations = report_violations(report)
    assert any("Prior rounds" in v for v in violations)


def test_prior_rounds_cap_applies_to_a_modified_heading():
    """Modified headings like '## Prior rounds (compressed)' should still be cap-checked."""
    report = """# Senior #1 - Q216 - Round 1
**Scope:** sourcetype=test
**Insight:** NOT_FOUND
**Candidate:** none **Confidence:** 20

## This round
### What I ran
- query
### What it means
result

## Ruled out
- feed

## Open questions for SH
- question

## Prior rounds (compressed)
- Round 1: a.
- Round 2: b.
- Round 3: c.
- Round 4: d.
- Round 5: e.
- Round 6: f.
- Round 7: g.
- Round 8: h.
"""
    violations = report_violations(report)
    assert any("Prior rounds" in v for v in violations)


def test_novel_spl_normalizes_prior_set():
    """Prior set should be normalized even if passed in unnormalized."""
    prior = {"Index=botsv3  | stats count"}
    n, updated = novel_spl(prior, ["index=botsv3 | stats count"])
    assert n == 0  # Same query, even though prior had different case/spacing
    assert updated == {"index=botsv3 | stats count"}  # Normalized


def test_prior_rounds_with_h1_line_inside_does_not_end_early():
    """A # line inside Prior rounds (e.g. in a code fence) should not end the section."""
    report = """# Senior #1 - Q216 - Round 1
**Scope:** sourcetype=test
**Insight:** NOT_FOUND
**Candidate:** none **Confidence:** 20

## This round
### What I ran
- query
### What it means
result

## Ruled out
- feed

## Open questions for SH
- question

## Prior rounds
- Round 1: a.
# note
- Round 2: b.
- Round 3: c.
- Round 4: d.
- Round 5: e.
- Round 6: f.
- Round 7: g.
- Round 8: h.
"""
    violations = report_violations(report)
    assert any("Prior rounds" in v for v in violations)


def test_a_report_without_an_assumptions_section_is_a_violation():
    assert report_violations(GOOD.replace("## Assumptions", "## Notes")) != []


def test_open_questions_are_the_bullets_of_that_section():
    assert open_questions(GOOD) == [
        "Is the window you gave me the incident window, or the whole index?"]


def test_none_is_not_an_open_question():
    for blank in ("- none", "- None.", "- n/a", "- (none)", "none"):
        md = GOOD.split("## Open questions for SH")[0] + "## Open questions for SH\n" + blank
        assert open_questions(md) == [], blank


def test_open_questions_stop_at_the_next_heading_and_at_the_cap_line():
    md = (GOOD + "- Should I widen to the whole feed?\n\n"
          "_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._\n")
    assert open_questions(md) == [
        "Is the window you gave me the incident window, or the whole index?",
        "Should I widen to the whole feed?"]
    later = GOOD + "\n## Something else\n- not a question for SH\n"
    assert len(open_questions(later)) == 1


def test_no_open_questions_section_means_none():
    assert open_questions(GOOD.split("## Open questions for SH")[0]) == []


def test_unverified_premises_counts_only_the_assumptions_section():
    assert unverified_premises(GOOD) == 1
    md = GOOD.replace("- The window SH gave me is the incident window - UNVERIFIED",
                      "- a - VERIFIED: q -> 3 events\n- b - UNVERIFIED\n- c - UNVERIFIED")
    assert unverified_premises(md) == 2
    assert unverified_premises(GOOD.split("## Assumptions")[0]) == 0
