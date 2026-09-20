"""The three moves that got 112 past the validator in the Q216 v1.4.3 acceptance run.

Full analysis in `docs/version_architecture/v1/v1.4.3.md`. Each move was legal on its
own; the combination let a refuted chain answer anyway.
"""

from conversation import ledger_violations
from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from question_state import QuestionState

RESULT = '{"dh": "coinhive.com", "count": "1", "procs": "chrome.exe"}'


def _state():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    return st


def _answer(ids):
    class _E:
        route = "ANSWER"
        source_senior = "s1"
        answer_premise_ids = list(ids)
    return _E()


def _ledger_with_validator_refutation():
    """SH files a coverage premise, verifies it itself, a validator refutes it."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="coverage: only the stratum port matters",
                          kind="coverage", load_bearing=True)], author="sh", round_n=2)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=RESULT,
                             evidence="the port census")],
              author="sh", corpus=[RESULT], round_n=2)
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=RESULT,
                             evidence="a full dh scan shows coinhive, an uncovered route")],
              author="v1", corpus=[RESULT], round_n=3)
    return led


def test_a_validator_refutation_blocks_an_answer_that_does_not_cite_it():
    """Move 1. The gate read `answer_premise_ids`, so SH filed a fresh coverage premise
    and cited that instead. A premise marked load-bearing and then shown false does not
    stop mattering because the next turn stops mentioning it."""
    led = _ledger_with_validator_refutation()
    led.add([PremiseDraft(text="coverage: restated, now with feeling", kind="coverage",
                          load_bearing=True)], author="sh", round_n=4)
    led.apply([PremiseUpdate(id="p2", status="VERIFIED", quote=RESULT,
                             evidence="same census, reworded")],
              author="sh", corpus=[RESULT], round_n=4)

    out = ledger_violations([_answer(["p2"])], led, _state())
    assert any("p1" in v for v in out), out


def test_a_replacement_verified_by_a_validator_unblocks_the_answer():
    """The escape has to be real, or every refuted premise ends the question. An
    independently verified replacement of the same kind is that escape."""
    led = _ledger_with_validator_refutation()
    led.add([PremiseDraft(text="coverage: stratum AND browser mining", kind="coverage",
                          load_bearing=True)], author="sh", round_n=4)
    led.apply([PremiseUpdate(id="p2", status="VERIFIED", quote=RESULT,
                             evidence="both routes now enumerated")],
              author="v2", corpus=[RESULT], round_n=5)

    assert ledger_violations([_answer(["p2"])], led, _state()) == []


def test_a_replacement_the_author_verified_itself_does_not_unblock():
    """Which is precisely what SH did: p6 and p7 were settled by SH on the ANSWER turn,
    where no wave follows and so no validator ever saw them."""
    led = _ledger_with_validator_refutation()
    led.add([PremiseDraft(text="coverage: stratum AND browser mining", kind="coverage",
                          load_bearing=True)], author="sh", round_n=4)
    led.apply([PremiseUpdate(id="p2", status="VERIFIED", quote=RESULT,
                             evidence="both routes now enumerated")],
              author="sh", corpus=[RESULT], round_n=4)

    assert ledger_violations([_answer(["p2"])], led, _state()) != []


def test_an_author_refuting_its_own_premise_does_not_block_anything():
    """Self-correction is healthy investigation, not a broken chain. Q216 r1: s1 filed
    the iexeplorer.exe lead and killed it itself the next round. Only a VALIDATOR's
    refutation means the answer's own party was overruled."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="the homoglyph process is the miner", kind="selection",
                          load_bearing=True)], author="s1", round_n=1)
    led.apply([PremiseUpdate(id="p1", status="REFUTED", quote=RESULT,
                             evidence="it talks only to an internal host")],
              author="s1", corpus=[RESULT], round_n=2)
    led.add([PremiseDraft(text="the stratum flow is the miner", kind="selection",
                          load_bearing=True)], author="s1", round_n=2)
    led.apply([PremiseUpdate(id="p2", status="VERIFIED", quote=RESULT,
                             evidence="the port census")],
              author="s1", corpus=[RESULT], round_n=2)

    assert ledger_violations([_answer(["p2"])], led, _state()) == []
