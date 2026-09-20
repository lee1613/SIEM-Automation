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
