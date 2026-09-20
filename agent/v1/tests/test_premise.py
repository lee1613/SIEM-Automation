import pytest
from premise import MIN_QUOTE_CHARS, Premise, PremiseDraft, PremiseUpdate, _norm
from pydantic import ValidationError


def test_a_draft_carries_only_what_the_senior_decides():
    d = PremiseDraft(text="The 3333 flow is inbound-heavy", kind="other",
                     load_bearing=True)
    assert d.load_bearing and d.kind == "other"


def test_a_draft_rejects_a_kind_outside_the_four():
    with pytest.raises(ValidationError):
        PremiseDraft(text="x", kind="guesswork", load_bearing=False)


def test_an_update_rejects_a_status_outside_the_three():
    with pytest.raises(ValidationError):
        PremiseUpdate(id="p1", status="PROBABLY", quote="", evidence="")


def test_a_premise_starts_unverified_with_nothing_behind_it():
    p = Premise(id="p1", author="s1", kind="coverage", text="Mining could surface as...",
                load_bearing=True, round_first_seen=1)
    assert p.status == "UNVERIFIED" and p.verified_by == "" and p.quote == ""


def test_norm_ignores_markdown_case_and_whitespace():
    assert _norm("  **ibc=5782875**\n obc=177 ") == _norm("ibc=5782875 obc=177")


def test_min_quote_chars_is_defined_here_now():
    assert MIN_QUOTE_CHARS == 12


from premise import PremiseLedger


def _draft(text, kind="other", lb=True):
    return PremiseDraft(text=text, kind=kind, load_bearing=lb)


def test_the_runner_assigns_ids_the_author_never_picks_one():
    led = PremiseLedger()
    added = led.add([_draft("a"), _draft("b")], author="s1", round_n=1)
    assert [p.id for p in added] == ["p1", "p2"]


def test_ids_keep_counting_across_authors_and_rounds():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    added = led.add([_draft("b")], author="s2", round_n=1)
    assert added[0].id == "p2"


def test_a_premise_the_senior_stops_mentioning_is_still_there():
    """The Q216 bug: s1 filed the byte-profile premise in round 1, wrote a cleaner
    report in round 3, and the doubt vanished. It cannot vanish now."""
    led = PremiseLedger()
    led.add([_draft("The 3333 flow's byte profile is download-like")],
            author="s1", round_n=1)
    led.add([_draft("chrome.exe is the process")], author="s1", round_n=3)
    open_ids = [p.id for p in led.unresolved_for("s1")]
    assert "p1" in open_ids


def test_unresolved_is_per_author():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    led.add([_draft("b")], author="s2", round_n=1)
    assert [p.id for p in led.unresolved_for("s2")] == ["p2"]


def test_load_bearing_open_premises_are_the_ones_that_block():
    led = PremiseLedger()
    led.add([_draft("heavy", lb=True), _draft("light", lb=False)],
            author="s1", round_n=1)
    assert [p.id for p in led.blocking()] == ["p1"]


def test_a_candidate_is_recorded_per_round_for_later_calibration():
    led = PremiseLedger()
    led.record_candidate("s1", 1, "112")
    led.record_candidate("s1", 2, "112")
    assert led.candidates["s1"] == {1: "112", 2: "112"}
