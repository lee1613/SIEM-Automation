"""The Q216 ledger smoke run's failure mode: SH re-filed one premise triplet six times.

`log/v0/v0.4/intermediate/v0.4.2_ledger_Q216_r1/premise_ledger.json` holds 28 premises, 18 of them SH's,
and those 18 are six copies of the same coverage/selection/definition claims (rounds 4, 5,
8, 10, 16, 18). Three distinct claims, eighteen ids, no answer, $2.03.

The loop had four links; these tests pin the three that live in `premise.py`. The fourth
is the SH prompt.
"""

from premise import PremiseDraft, PremiseLedger, PremiseUpdate

# Verbatim from the run: SH's round-4 and round-8 selection premises. Same claim, reworded
# enough that `_match_form` sees two different strings.
SELECTION_R4 = ("Selection: The measured duration should come from the only flow in the "
                "feed matching Monero stratum behavior, because the report identifies "
                "dp=3333 as the only Monero port present.")
SELECTION_R8 = ("Selection: The duration to report should come from the single dp=3333 "
                "stratum flow, because that is the only Monero pool port in the feed.")

REPORT = ('s1 round 2: `| stats count dc(sa) as endpoints values(pn) as processes by dp` '
          '-> {"dp": "3333", "count": "1", "endpoints": "1", "processes": "powershell.exe"}')

# The rival every SELECTION_R4/R8 draft below names - the change under test requires one.
RIVAL = "the six ws*.coinhive.com HTTPS flows, ruled out for carrying no stratum handshake"


def _ledger_with_open_sh_selection():
    led = PremiseLedger()
    led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL)],
            author="sh", round_n=4)
    return led


def test_sh_cannot_open_a_second_premise_of_a_kind_it_already_has_open():
    """The rewording defeats `_match_form`, so text dedupe cannot catch this. One open
    premise per kind per author does, and it matches the prompt's own singular framing
    ('a coverage premise... a selection premise... a definition premise')."""
    led = _ledger_with_open_sh_selection()

    filed = led.add([PremiseDraft(text=SELECTION_R8, kind="selection", load_bearing=True, rival=RIVAL)],
                    author="sh", round_n=8)

    assert len(led.premises) == 1, "a reworded re-file must not mint a second id"
    assert filed[0].id == "p1", "the author is handed back the premise it already owns"
    assert led.premises["p1"].text == SELECTION_R4, "the filed text stays immutable"


def test_a_settled_premise_does_not_block_a_later_one_of_the_same_kind():
    """The guard is about what is still OPEN. Once p1 is settled, a genuinely new
    selection premise is legitimate - otherwise one kind is spent for the question."""
    led = _ledger_with_open_sh_selection()
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=REPORT,
                             evidence="the dp enumeration shows 3333 is the only pool port")],
              author="s1", corpus=[REPORT], round_n=5)

    filed = led.add([PremiseDraft(text=SELECTION_R8, kind="selection", load_bearing=True, rival=RIVAL)],
                    author="sh", round_n=8)

    assert len(led.premises) == 2
    assert filed[0].id == "p2"


def test_a_different_author_is_not_blocked_by_sh_s_open_premise():
    """Cross-author agreement is meaningful and stays its own row."""
    led = _ledger_with_open_sh_selection()

    filed = led.add([PremiseDraft(text=SELECTION_R8, kind="selection", load_bearing=True, rival=RIVAL)],
                    author="s1", round_n=8)

    assert len(led.premises) == 2
    assert filed[0].author == "s1"


# -- filing and settling in one turn -----------------------------------------------

def test_a_draft_carrying_a_quote_is_settled_as_it_is_filed():
    """The deadlock: the runner owns the ids, so an author cannot name a premise it is
    filing this turn in `premise_updates`. The auto-link then makes that premise an
    instant load-bearing blocker on the very ANSWER that filed it. Filing with the quote
    already attached is the way out, and it weakens nothing - the quote runs the same
    corpus and circularity checks. (SH cannot use this door at all now - `apply` refuses
    author="sh" outright, including the settle call `add` makes internally - so this is
    exercised by a senior, the only author for whom the deadlock still applies.)"""
    led = PremiseLedger()

    filed = led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL,
                                  quote=REPORT,
                                  evidence="dp=3333 is the only Monero pool port present")],
                    author="s1", round_n=4, corpus=[REPORT])

    assert filed[0].status == "VERIFIED"
    assert filed[0].verified_by == "s1"
    assert [h["status"] for h in filed[0].history] == ["UNVERIFIED", "VERIFIED"]


def test_a_draft_quote_that_is_in_no_result_leaves_the_premise_unverified():
    led = PremiseLedger()

    filed = led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL,
                                  quote="dp=9999 was the only pool port in the feed",
                                  evidence="made up")],
                    author="sh", round_n=4, corpus=[REPORT])

    assert filed[0].status == "UNVERIFIED"


def test_a_draft_quote_that_cites_sh_leaves_the_premise_unverified():
    """The same guard as `apply`: filing must not become a way around it."""
    led = PremiseLedger()
    circular = "the attribution was established by SH outside this feed"

    filed = led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL,
                                  quote=circular, evidence="SH settled it")],
                    author="sh", round_n=4, corpus=[circular])

    assert filed[0].status == "UNVERIFIED"


def test_a_draft_with_no_quote_is_filed_unverified_as_before():
    led = PremiseLedger()
    filed = led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL)],
                    author="sh", round_n=4)
    assert filed[0].status == "UNVERIFIED"


# -- a load-bearing premise must be visible to whoever is told to settle it ---------

def test_a_senior_is_shown_the_load_bearing_premises_it_is_told_to_settle():
    """`ledger_violations` tells SH to 'COMMAND s1 to settle them' for SH-authored
    premises that `render_for_senior` never showed s1. In the Q216 run no senior ever
    settled another author's premise - the path exists in the gates and is unreachable
    in the prompt."""
    led = PremiseLedger()
    led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL)],
            author="sh", round_n=4)
    led.add([PremiseDraft(text="s1's own open premise", kind="coverage",
                          load_bearing=True)], author="s1", round_n=4)

    shown = led.render_for_senior("s1")

    assert "s1's own open premise" in shown
    assert SELECTION_R4 in shown, "s1 cannot settle a premise it is never shown"
    assert "p1" in shown, "and it needs the id to address it"


def test_another_author_s_settled_premises_are_not_carried_to_a_senior():
    """Only what is still open and load-bearing. A settled premise is noise."""
    led = PremiseLedger()
    led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=True, rival=RIVAL)],
            author="sh", round_n=4)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=REPORT,
                             evidence="the dp enumeration settles it")],
              author="s2", corpus=[REPORT], round_n=5)
    led.add([PremiseDraft(text="s1 open", kind="coverage", load_bearing=True)],
            author="s1", round_n=5)

    shown = led.render_for_senior("s1")

    assert SELECTION_R4 not in shown


def test_another_author_s_non_load_bearing_premises_are_not_carried():
    led = PremiseLedger()
    led.add([PremiseDraft(text=SELECTION_R4, kind="selection", load_bearing=False, rival=RIVAL)],
            author="sh", round_n=4)
    led.add([PremiseDraft(text="s1 open", kind="coverage", load_bearing=True)],
            author="s1", round_n=4)

    assert SELECTION_R4 not in led.render_for_senior("s1")


def test_a_senior_with_nothing_open_anywhere_is_shown_nothing():
    assert PremiseLedger().render_for_senior("s1") == ""
