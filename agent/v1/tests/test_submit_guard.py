"""Nothing that is not answer-shaped reaches the scoreboard.

This guard used to live on the extractor's output. The extractor is gone - over
84 recorded extractions it saved one answer, destroyed one ('1368' -> '2085',
where 1368 was correct), and changed nothing in 57 - so the guard moved to the
only place that still matters: SH's answer, at the submit choke point.

Every failing case below is a real submitted answer taken from the run logs.
"""

from finding import MAX_ANSWER_CHARS, answer_shaped

# test_20260915_174228/Q329. SH gave up and returned "?", the extractor had
# nothing to strip, spent its whole budget deliberating, and 4,487 characters of
# that deliberation went to the scoreboard. Its LAST LINE was "No", which is why
# the guard rejects outright rather than salvaging a tail.
Q329_COT = (
    'We need to answer: "One of the files uploaded by Taedonggang contains a '
    "word that is a much larger in font size than any other in the file. What "
    'is that word?" We need to find the file uploaded by user "Taedonggang". '
    "There's no file shown in the conversation.\n\n"
    "Given the constraints, I think we should output the username as the word.\n\n"
    "No")

# run_1.2/Q328 - single line, 254 chars, a refusal rather than an answer.
Q328_REFUSAL = (
    "I cannot provide the specific text from the file as I do not have access "
    "to the Splunk index `botsv3` or the host `hoth` to inspect the raw events "
    "and file contents. The information required to answer this question is "
    "simply not available to me here.")

# The other shape SH produces when it has no answer: an Option B block. The
# extractor's single lifetime save was digging a CVE out of one of these
# (Q332). Now it is caught deterministically and routed to the ledger instead.
Q332_REPLAN = ("REPLAN:\n- Missing: The exact CVE identifier. Corroborate the "
               "kernel version against the exploit database.\n- New tasks:\n"
               "  1. Search for the privilege escalation binary")


# ── what must be rejected ──────────────────────────────────────────────────────

def test_a_leaked_chain_of_thought_is_rejected():
    assert not answer_shaped(Q329_COT)


def test_the_last_line_of_a_truncated_cot_is_not_salvaged():
    # "No" is short, single-line and looks like an answer. Salvaging a tail
    # would submit noise with no signal that anything went wrong.
    assert Q329_COT.strip().endswith("No")
    assert not answer_shaped(Q329_COT)


def test_a_refusal_paragraph_is_rejected():
    assert len(Q328_REFUSAL) > MAX_ANSWER_CHARS
    assert not answer_shaped(Q328_REFUSAL)


def test_a_replan_block_is_rejected():
    assert not answer_shaped(Q332_REPLAN)


def test_a_bare_question_mark_is_rejected():
    # Q329's actual sh_answer. Without the extractor this would otherwise reach
    # the scoreboard verbatim.
    assert not answer_shaped("?")


def test_empty_is_rejected_without_crashing():
    for v in ("", None, "   \n  "):
        assert not answer_shaped(v)


# ── what must survive ──────────────────────────────────────────────────────────

def test_the_real_sh_answers_from_the_smoke_run_pass_through():
    # Every sh_answer test_20260915_174228 produced except Q329's "?".
    for v in ("7071", "bar chart", "6.80", "/etc/tomcat8/tomcat-users.xml"):
        assert answer_shaped(v), v


def test_the_longest_real_answer_survives():
    # The longest of the 58 BOTSv3 answers: 110 chars, 11 words.
    ua = ("Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 "
          "Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4")
    assert answer_shaped(ua)


# ── the fallback the guard hands off to ────────────────────────────────────────

def test_fallback_prefers_the_schema_b_value_over_the_prose_answer():
    # Rejecting noise is pointless if the fallback submits a different pile of
    # prose: that put 3,316 characters on the scoreboard in test_20260907_132802.
    from run_all_v1 import fallback_answer

    delegations = [{"answer": "I looked at cisconvmflowdata and computed the "
                              "total duration across the session.\n"
                              "FINAL ANSWER: 1666",
                    "value": "1666", "status": "solved"}]
    assert fallback_answer("?", delegations) == "1666"


def test_fallback_uses_the_last_line_when_there_are_no_delegations():
    from run_all_v1 import fallback_answer

    assert fallback_answer("line one\nFYODOR-L", []) == "FYODOR-L"
