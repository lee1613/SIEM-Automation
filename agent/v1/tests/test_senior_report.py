# agent/v1/tests/test_senior_report.py
from senior_report import (
    PRIOR_ROUNDS_MAX_LINES,
    REPORT_WORD_CAP,
    novel_spl,
    report_violations,
    stamp_header,
    truncate_words,
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
