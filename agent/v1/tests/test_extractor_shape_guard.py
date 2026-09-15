"""Nothing that is not answer-shaped reaches the scoreboard.

Every case here is a real submitted answer, taken from the run logs. The
extractor had no output guard at all, so a reasoning model that spent its whole
completion budget deliberating in `content` got that deliberation submitted
verbatim and scored zero.

Calibration, from the 86 extractions on record: 3 were multi-line and all 3
were this failure; 4 exceeded 110 chars and all 4 were this failure; none of
the 58 real BOTSv3 answers contains a newline and the longest is 110 chars.
"""

from extractor import MAX_ANSWER_CHARS, clean_completion

# test_20260915_174228/Q329 - 4,487 chars of chain-of-thought, truncated at the
# token cap. Its LAST LINE was "No", which is why this guard rejects outright
# rather than salvaging a tail.
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


# ── the failures ───────────────────────────────────────────────────────────────

def test_leaked_chain_of_thought_is_rejected():
    assert clean_completion(Q329_COT) == ""


def test_the_last_line_of_a_truncated_cot_is_not_salvaged():
    # "No" is short, single-line and looks like an answer. Salvaging it would
    # submit noise with no signal that anything went wrong.
    assert clean_completion(Q329_COT).strip() != "No"


def test_an_over_long_single_line_is_rejected():
    assert len(Q328_REFUSAL) > MAX_ANSWER_CHARS
    assert clean_completion(Q328_REFUSAL) == ""


def test_an_explicit_think_block_is_stripped_not_rejected():
    assert clean_completion("<think>hmm, maybe 1666 or 7071</think>\n1666") == "1666"


# ── the answers that must survive ──────────────────────────────────────────────

def test_the_longest_real_answer_survives():
    # The longest of the 58 BOTSv3 answers, at 110 chars.
    ua = ("Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 "
          "Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4")
    assert clean_completion(ua) == ua


def test_ordinary_answers_survive_with_whitespace_trimmed():
    for raw, want in (("  1666  ", "1666"),
                      ("bstoll,btun,splunk_access,web_admin",
                       "bstoll,btun,splunk_access,web_admin"),
                      ("\nBSTOLL-L.froth.ly\n", "BSTOLL-L.froth.ly")):
        assert clean_completion(raw) == want


def test_empty_is_empty_not_a_crash():
    assert clean_completion("") == ""
    assert clean_completion(None) == ""
    assert clean_completion("   \n  ") == ""


# ── the fallback the guard hands off to ────────────────────────────────────────

def test_fallback_prefers_the_schema_b_value_over_the_prose_answer():
    # The guard is only half the fix: rejecting noise is pointless if the
    # fallback submits a different pile of prose.
    from run_all_v1 import extractor_fallback_answer

    delegations = [{"answer": "I looked at cisconvmflowdata and computed the "
                              "total duration across the session.\n"
                              "FINAL ANSWER: 1666",
                    "value": "1666", "status": "solved"}]
    assert extractor_fallback_answer("?", delegations) == "1666"
