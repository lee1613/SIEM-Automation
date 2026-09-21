"""SH's stamp: its reading of one newly-claimed verification (v1.4.3 revision).

The measurement this replaces, across three runs and six seniors: R4 flipped to PASS on
the turn SH stopped investigating, without exception. A single word about a whole report
is easy to wave through. "Does this quote establish this claim as written", asked about
one named premise one round before the answering turn, is the bet.
"""

from premise import PremiseDraft, PremiseLedger, PremiseUpdate

QUOTE = '{"da": "45.77.53.176", "count": "4832", "dp": ["3333", "443", "80"]}'


def _verified_by(author="s1", kind="coverage", text="route (c) is NOT yet searched"):
    led = PremiseLedger()
    led.add([PremiseDraft(text=text, kind=kind, load_bearing=True,
                          rival="the other flows in the window")],
            author=author, round_n=1)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                             evidence="the pool-IP census")],
              author=author, corpus=[QUOTE], round_n=2)
    return led


def test_a_newly_verified_premise_is_owed_a_stamp():
    led = _verified_by()
    assert [p.id for p in led.unstamped("s1")] == ["p1"]


def test_a_stamp_is_an_annotation_never_an_edit():
    """A false-stamped premise stays VERIFIED. Status belongs to the quote rule and the
    validator; the stamp is SH's reading of it, recorded beside it."""
    led = _verified_by()
    assert led.stamp_premise("p1", establishes=False,
                             reason="the claim says route (c) was not searched and the "
                                    "quote is the result of searching it",
                             round_n=3) is True
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].stamp == "false"
    assert "not searched" in led.premises["p1"].stamp_reason


def test_a_premise_is_stamped_once():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, reason="it does", round_n=3)
    assert led.stamp_premise("p1", establishes=False, reason="changed my mind",
                             round_n=4) is False
    assert led.premises["p1"].stamp == "true"


def test_a_stamped_premise_is_no_longer_owed_one():
    led = _verified_by()
    led.stamp_premise("p1", establishes=True, reason="it does", round_n=3)
    assert led.unstamped("s1") == []


def test_a_validators_verdict_is_not_stamped():
    """The validator is the thing that outranks the stamp, not something for SH to
    grade. SH files none of its own either, since it can no longer settle."""
    led = _verified_by()
    led.apply([PremiseUpdate(id="p1", status="UNVERIFIED", quote="",
                             evidence="withdrawn")], author="s1", corpus=[], round_n=3)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                             evidence="my own scan")],
              author="v1", corpus=[QUOTE], round_n=4)
    assert led.unstamped("s1") == []
    assert led.unstamped() == []


def test_nominatable_is_what_sh_stamped_false_or_what_the_senior_left_open():
    """It may not range wider: the false stamp is what fired the mechanism, so aiming
    the validator elsewhere would leave the triggering doubt unexamined."""
    led = _verified_by()
    led.stamp_premise("p1", establishes=False, reason="it walks past its own limit",
                      round_n=3)
    led.add([PremiseDraft(text="this flow and not the CoinHive six", kind="selection",
                          load_bearing=True, rival="the six ws*.coinhive.com flows")],
            author="s1", round_n=3)
    led.add([PremiseDraft(text="someone else's open claim", kind="coverage",
                          load_bearing=True)], author="s2", round_n=3)
    assert [p.id for p in led.nominatable("s1")] == ["p1", "p2"]


def test_the_stamp_is_in_the_table_and_the_dump():
    led = _verified_by()
    led.stamp_premise("p1", establishes=False, reason="no", round_n=3)
    assert "stamp" in led.render_table()
    assert "false" in led.render_table()
    [rec] = led.to_records("Q216")
    assert rec["stamp"] == "false" and rec["stamp_reason"] == "no"
    assert rec["rival"] == "the other flows in the window"
