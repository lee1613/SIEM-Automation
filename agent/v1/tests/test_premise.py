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


from premise import PremiseUpdate, quote_supported

CORPUS = ["sourcetype=cisco:nvm | 1 result: ibc=5782875 obc=177 dest_port=3333"]


def _upd(pid, status, quote="", evidence="because"):
    return PremiseUpdate(id=pid, status=status, quote=quote, evidence=evidence)


def _led():
    led = PremiseLedger()
    led.add([_draft("The 3333 flow is submission, not download")],
            author="s1", round_n=1)
    return led


def test_quote_supported_matches_across_markdown_and_whitespace():
    assert quote_supported("**ibc=5782875**   obc=177", CORPUS)


def test_quote_supported_rejects_a_quote_nobody_received():
    assert not quote_supported("obc=5782875 ibc=177", CORPUS)


def test_quote_supported_rejects_a_quote_too_short_to_mean_anything():
    assert not quote_supported("ibc=57", CORPUS)


def test_verified_needs_a_quote_from_a_result_the_author_received():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert notes == [] and led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].verified_by == "s1"


def test_verified_without_a_real_quote_is_dropped_and_reported():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "the flow is clearly mining traffic")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert len(notes) == 1 and "p1" in notes[0]


def test_refuted_is_terminal():
    led = _led()
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=3)
    assert led.premises["p1"].status == "REFUTED"
    assert len(notes) == 1 and "REFUTED" in notes[0]


def test_withdrawing_a_verdict_needs_no_quote():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    notes = led.apply([_upd("p1", "UNVERIFIED", "")], author="s1",
                      corpus=CORPUS, round_n=3)
    assert notes == [] and led.premises["p1"].status == "UNVERIFIED"


def test_a_sibling_senior_may_settle_another_seniors_premise():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s2", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p1"].verified_by == "s2"
    assert led.premises["p1"].author == "s1"


def test_an_update_naming_an_unknown_id_is_reported_not_crashed():
    led = _led()
    notes = led.apply([_upd("p99", "VERIFIED", "ibc=5782875 obc=177")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert len(notes) == 1 and "p99" in notes[0]


def test_every_transition_is_recorded_in_history():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED", "VERIFIED"]


def test_the_carry_forward_block_quotes_the_premise_word_for_word():
    led = PremiseLedger()
    text = "The 3333 record's byte profile (5.7MB in / 177B out) is download-like"
    led.add([_draft(text)], author="s1", round_n=1)
    block = led.render_for_senior("s1")
    assert text in block and "[p1]" in block and "open since round 1" in block


def test_the_carry_forward_block_is_empty_when_nothing_is_open():
    led = PremiseLedger()
    led.add([_draft("a")], author="s1", round_n=1)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    assert led.render_for_senior("s1") == ""


def test_a_senior_is_not_handed_another_seniors_premises():
    led = PremiseLedger()
    led.add([_draft("s1 only")], author="s1", round_n=1)
    assert led.render_for_senior("s2") == ""


def test_the_sh_table_shows_status_load_bearing_and_who_settled_it():
    led = PremiseLedger()
    led.add([_draft("mining could surface as stratum", kind="coverage")],
            author="s1", round_n=1)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s2", corpus=CORPUS, round_n=2)
    table = led.render_table()
    assert "p1" in table and "coverage" in table and "VERIFIED" in table and "s2" in table


def test_the_sh_table_says_so_when_there_are_no_premises():
    assert "no premises" in PremiseLedger().render_table().lower()


def test_the_refuted_block_carries_the_evidence_that_killed_it():
    led = PremiseLedger()
    led.add([_draft("the flow is submission")], author="s1", round_n=1)
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177",
                    evidence="inbound bytes dwarf outbound")],
              author="s2", corpus=CORPUS, round_n=2)
    block = led.render_refuted()
    assert "the flow is submission" in block and "ibc=5782875" in block
