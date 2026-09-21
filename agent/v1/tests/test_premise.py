import json

import pytest
from premise import (
    MIN_QUOTE_CHARS,
    Premise,
    PremiseDraft,
    PremiseLedger,
    PremiseUpdate,
    quote_supported,
)
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


def test_min_quote_chars_is_defined_here_now():
    assert MIN_QUOTE_CHARS == 12


def _draft(text, kind="other", lb=True):
    return PremiseDraft(text=text, kind=kind, load_bearing=lb)


def test_the_runner_assigns_ids_the_author_never_picks_one():
    led = PremiseLedger()
    # Different kinds: one author may hold only one OPEN premise per kind, so two
    # `other` drafts would be read as a re-file (see the re-file loop tests).
    added = led.add([_draft("a", kind="coverage"), _draft("b", kind="selection")],
                    author="s1", round_n=1)
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


def test_a_candidate_is_recorded_per_round_for_later_calibration():
    led = PremiseLedger()
    led.record_candidate("s1", 1, "112")
    led.record_candidate("s1", 2, "112")
    assert led.candidates["s1"] == {1: "112", 2: "112"}


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


def test_a_senior_is_handed_another_authors_open_load_bearing_premises():
    """Changed by the Q216 ledger run. The block used to filter on author alone, which
    made `ledger_violations`' "COMMAND s1 to settle them" name an action s1 could not
    take - it had never seen the premise or its id. That run settled 0 premises
    senior-to-senior while SH verified all 15 of its own."""
    led = PremiseLedger()
    led.add([_draft("s1 only", lb=True)], author="s1", round_n=1)
    block = led.render_for_senior("s2")
    assert "s1 only" in block and "p1" in block


def test_a_senior_is_not_handed_another_authors_incidental_premises():
    """Only load-bearing and only still-open. Everything else is noise in a round."""
    led = PremiseLedger()
    led.add([_draft("s1 aside", lb=False)], author="s1", round_n=1)
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


def test_the_dump_carries_history_and_the_per_round_candidate():
    led = PremiseLedger()
    led.add([_draft("The 3333 flow is submission")], author="s1", round_n=1)
    led.record_candidate("s1", 1, "112")
    led.record_candidate("s1", 2, "112")
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)

    rec = led.to_records("216")[0]
    assert rec["qid"] == "216" and rec["id"] == "p1" and rec["load_bearing"] is True
    assert [h["status"] for h in rec["history"]] == ["UNVERIFIED", "REFUTED"]
    assert rec["candidate_at_each_round"] == {"1": "112", "2": "112"}
    json.dumps(rec)   # must be serialisable


def test_the_dump_is_empty_for_an_empty_ledger():
    assert PremiseLedger().to_records("216") == []


# -- FIX 1: quote_supported must match the JSON a senior actually receives -------

JSON_CORPUS = ['{"results": [{"dest_port": "3333", "ibc": "5782875"}], "meta": {}}']


def test_quote_supported_matches_a_field_value_restatement_of_json():
    assert quote_supported("dest_port=3333 ibc=5782875", JSON_CORPUS)


def test_quote_supported_rejects_a_restatement_with_different_values():
    assert not quote_supported("dest_port=4444 ibc=5782875", JSON_CORPUS)


def test_quote_supported_floor_still_applies_after_normalisation():
    # "port 33" match-forms to "port 33", 7 chars - under the 12-char floor even
    # though it would appear in the JSON corpus above.
    assert not quote_supported("port: 33!!", JSON_CORPUS)


# -- FIX 2: the carry-forward block never tells a senior to settle a REFUTED ----

def test_a_refuted_premise_does_not_appear_in_the_carry_forward_block():
    led = _led()
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)
    assert "p1" not in led.render_for_senior("s1")


def test_the_carry_forward_block_is_empty_when_the_only_premise_is_refuted():
    led = _led()
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)
    assert led.render_for_senior("s1") == ""


# -- FIX 3: re-filing the same premise text dedupes per author -------------------

def test_refiling_identical_text_as_the_same_author_returns_the_existing_premise():
    led = PremiseLedger()
    first = led.add([_draft("The 3333 flow is download-like")], author="s1", round_n=1)
    second = led.add([_draft("the 3333 flow is download-like")], author="s1", round_n=2)
    assert first[0].id == second[0].id == "p1"
    assert len(led.premises) == 1


def test_the_same_text_from_a_different_author_gets_its_own_id():
    led = PremiseLedger()
    led.add([_draft("The 3333 flow is download-like")], author="s1", round_n=1)
    added = led.add([_draft("The 3333 flow is download-like")], author="s2", round_n=1)
    assert added[0].id == "p2"
    assert len(led.premises) == 2


# -- FIX 4: VERIFIED/REFUTED needs non-blank evidence -----------------------------

def test_verified_with_blank_evidence_is_dropped_and_reported():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177", evidence="")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert len(notes) == 1 and "p1" in notes[0] and "evidence" in notes[0]


def test_verified_with_whitespace_only_evidence_is_dropped():
    led = _led()
    notes = led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177", evidence="   ")],
                      author="s1", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "UNVERIFIED"
    assert len(notes) == 1


# -- FIX 6: no history entry for a restated identical status --------------------

def test_restating_the_same_status_does_not_grow_history():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=3)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED", "VERIFIED"]


# -- FIX 6: answer() disagrees with a caller who thinks whitespace closed it -----

def test_answer_rejects_a_whitespace_only_answer():
    led = PremiseLedger()
    led.ask(["is the process chrome.exe?"], author="s1", round_n=1)
    ok = led.answer("q1", "   ")
    assert ok is False
    assert led.open_questions_for("s1")[0].id == "q1"


# -- FIX 7: a REJECTED update must not append to history -------------------------

def test_a_rejected_update_does_not_append_to_history():
    led = _led()
    led.apply([_upd("p1", "VERIFIED", "the flow is clearly mining traffic")],
              author="s1", corpus=CORPUS, round_n=2)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED"]


def test_an_unknown_id_update_does_not_touch_any_history():
    led = _led()
    led.apply([_upd("p99", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=2)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED"]


def test_a_refuted_terminal_rejection_does_not_append_to_history():
    led = _led()
    led.apply([_upd("p1", "REFUTED", "ibc=5782875 obc=177")],
              author="v1", corpus=CORPUS, round_n=2)
    led.apply([_upd("p1", "VERIFIED", "ibc=5782875 obc=177")],
              author="s1", corpus=CORPUS, round_n=3)
    assert [h["status"] for h in led.premises["p1"].history] == ["UNVERIFIED", "REFUTED"]


# -- FIX 7: a mixed batch lands the valid update and reports only the invalid one -

def test_a_mixed_batch_applies_the_valid_update_and_reports_only_the_invalid_one():
    led = PremiseLedger()
    led.add([_draft("a", kind="coverage"), _draft("b", kind="selection")],
            author="s1", round_n=1)
    notes = led.apply([
        _upd("p1", "VERIFIED", "ibc=5782875 obc=177"),
        _upd("p2", "VERIFIED", "the flow is clearly mining traffic"),
    ], author="s1", corpus=CORPUS, round_n=2)
    assert led.premises["p1"].status == "VERIFIED"
    assert led.premises["p2"].status == "UNVERIFIED"
    assert len(notes) == 1 and "p2" in notes[0]


# -- FIX 7: ask / answer / open_questions_for had zero coverage ------------------

def test_ask_files_questions_addressable_by_id_and_skips_blank_text():
    led = PremiseLedger()
    qs = led.ask(["is chrome.exe the process?", "  ", ""], author="s1", round_n=1)
    assert [q.id for q in qs] == ["q1"]
    assert led.questions["q1"].text == "is chrome.exe the process?"
    assert led.questions["q1"].round_asked == 1


def test_open_questions_for_excludes_answered_questions():
    led = PremiseLedger()
    led.ask(["q one"], author="s1", round_n=1)
    led.ask(["q two"], author="s1", round_n=1)
    led.answer("q1", "yes, confirmed")
    ids = [q.id for q in led.open_questions_for("s1")]
    assert ids == ["q2"]


def test_open_questions_for_is_per_author():
    led = PremiseLedger()
    led.ask(["s1's question"], author="s1", round_n=1)
    led.ask(["s2's question"], author="s2", round_n=1)
    assert [q.id for q in led.open_questions_for("s2")] == ["q2"]


def test_answer_returns_false_for_an_unknown_question_id():
    led = PremiseLedger()
    assert led.answer("q99", "an answer") is False


def test_answer_returns_true_and_records_the_text_for_a_known_id():
    led = PremiseLedger()
    led.ask(["is it chrome.exe?"], author="s1", round_n=1)
    assert led.answer("q1", "yes") is True
    assert led.questions["q1"].answer == "yes"


# -- FIX 7: dump_ledgers writes and reads back correctly, merging ledgers -------

def test_dump_ledgers_merges_multiple_ledgers_and_round_trips_through_a_file(tmp_path):
    from premise import dump_ledgers

    led_a = PremiseLedger()
    led_a.add([_draft("A's premise")], author="s1", round_n=1)
    led_b = PremiseLedger()
    led_b.add([_draft("B's premise")], author="s2", round_n=1)

    out = tmp_path / "premise_ledger.json"
    dump_ledgers(str(out), {"216": led_a, "217": led_b})

    records = json.loads(out.read_text(encoding="utf-8"))
    by_qid = {r["qid"] for r in records}
    assert by_qid == {"216", "217"}
    assert len(records) == 2
    texts = {r["text"] for r in records}
    assert texts == {"A's premise", "B's premise"}


def test_definition_is_no_longer_a_kind():
    """A measurement ambiguity is an open question to SH, not a premise: no search
    settles "span or sum", while "do these records overlap" is a query. p12 was a
    selection claim wearing the label, which is why it could be "verified"."""
    from premise import KINDS
    assert KINDS == ("coverage", "selection", "other")
    with pytest.raises(ValidationError):
        PremiseDraft(text="the measure is the wall-clock span", kind="definition",
                     load_bearing=True)


def test_a_senior_still_saying_definition_keeps_its_claim_as_other():
    """finding._drafts maps an unknown kind to 'other' rather than dropping the draft,
    so a senior on an older habit loses the label, never the premise."""
    from finding import _drafts
    [d] = _drafts([{"text": "the measure is the wall-clock span", "kind": "definition"}])
    assert d.kind == "other"
    assert d.text == "the measure is the wall-clock span"
