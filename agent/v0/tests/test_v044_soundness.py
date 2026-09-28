"""v0.4.4: the four changes the v0.4.3 smoke run's post-mortem asked for.

The run scored 2/5, and so did v0.4.1 before it — same three questions, same wrong
value on Q216. Four separate mechanisms were implicated, and each one gets a section
here:

  1. The stamp obligation arrived as a REJECTION, after the turn, though the runner
     could compute it before. Turns were spent re-issuing a turn whose only fault was
     a missing stamp, and a rejected turn is not given back.
  2. The stamp asked one question — is this quote real and does it support the claim —
     and Q216's selection premise passed it five times while being false. Validity is
     not soundness.
  3. The validator re-checked the incumbent, which is a confirmation frame. Nobody was
     ever sent to make the rival's case.
  4. "The value cannot be read with these tools" had no way to be said, so SH kept
     spawning into feeds a senior had already proven empty.
"""

import json

from conversation import (
    UNANSWERABLE_VALUE,
    PremiseStamp,
    SeniorDirective,
    stamp_is_false,
    stamp_violations,
    unanswerable_violations,
)
from premise import (
    PremiseDraft,
    PremiseLedger,
    PremiseUpdate,
    dump_ledgers,
    dump_question_ledger,
)
from sh_loop import render_wave
from validator import as_rival_verdict, brief_for_rival, rival_mode

QUOTE = '{"sa": "192.168.70.186", "dp": "3333", "count": "1", "dur": "112"}'

BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RETIRE",
    "open_question_answers": [], "new_premises": [], "answer_premise_ids": [],
    "premise_stamps": [], "nominate_premise_id": "",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "deviation": "", "inherited_entities": "", "recall_qid": "", "recall_what": "",
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}


def entry(**kw) -> SeniorDirective:
    return SeniorDirective(**{**BLANK, **kw})


def _command(**kw):
    return entry(**{"route": "COMMAND", "senior_id": "s1", "decision": "continue",
                    "directive": "go further", "r1_scope_alignment": "PASS",
                    "r2_progress": "PASS", "r3_answer_readiness": "WEAK",
                    "r4_premise_verification": "WEAK", **kw})


def _ledger(kind="selection", author="s1",
            text="the endpoint asked about is 192.168.70.186",
            rival="192.168.247.131, the CoinHive host, as the endpoint"):
    led = PremiseLedger()
    led.add([PremiseDraft(text=text, kind=kind, load_bearing=True, rival=rival)],
            author=author, round_n=1)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                             evidence="the sole pool-port row")],
              author=author, corpus=[QUOTE], round_n=2)
    return led


# ── 1. the stamp is asked for BEFORE the turn, not after it ─────────────────────

def test_the_wave_names_the_premises_it_will_reject_the_turn_for():
    """`stamp_violations` computes this set after the turn to build its rejection. The
    same set is knowable before, and SH never saw it there."""
    led = _ledger()
    wave = render_wave({"s1": {"report": "found it", "novel_spl_count": 3}},
                       slots_remaining=1, turns_remaining=4, ledger=led)
    assert "STAMP FIRST" in wave
    assert "p1" in wave.split("STAMP FIRST")[1]
    # Both questions named where the turn's instructions are, not only in the system
    # prompt a hundred lines away.
    assert "establishes" in wave and "claim_holds" in wave


def test_a_wave_owing_no_stamp_says_nothing_about_stamping():
    led = _ledger()
    led.stamp_premise("p1", establishes=True, claim_holds=True,
                      holds_reason="no rival", reason="it does", round_n=2)
    wave = render_wave({"s1": {"report": "found it", "novel_spl_count": 3}},
                       slots_remaining=1, turns_remaining=4, ledger=led)
    assert "STAMP FIRST" not in wave


# ── 2. validity and soundness are different questions ──────────────────────────

def test_a_validly_cited_claim_can_still_fail_on_soundness():
    """Q216 in one assertion: the quote is real, it is read correctly, it supports the
    claim as written — and the claim is about the wrong endpoint."""
    s = PremiseStamp(id="p1", establishes=True,
                     reason="the row does show .186 holds the only dp=3333 flow",
                     claim_holds=False,
                     holds_reason="the same feed shows .247.131 running CoinHive, "
                                  "which is Monero mining and fits the question's "
                                  "wording at least as well")
    assert stamp_is_false(s), "a false soundness reading must fire the mechanism"


def test_a_stamp_answering_only_the_first_question_is_rejected():
    led = _ledger()
    out = stamp_violations(
        [_command(premise_stamps=[PremiseStamp(
            id="p1", establishes=True, reason="the quote supports it as written",
            claim_holds=True, holds_reason="   ")])],
        led)
    assert out and "holds_reason" in out[0]


def test_both_readings_are_kept_separately_in_the_ledger():
    """`stamp` stays the one verdict the machinery keys on; which question failed has
    to survive into the ledger or the post-run reading cannot be done at all."""
    led = _ledger()
    led.stamp_premise("p1", establishes=True, reason="cited cleanly",
                      claim_holds=False, holds_reason="the CoinHive host fits too",
                      round_n=3)
    p = led.premises["p1"]
    assert p.stamp == "false", "either reading failing makes the stamp false"
    assert p.stamp_holds == "false"
    assert "CoinHive" in p.holds_reason
    rec = led.to_records("Q216")[0]
    assert rec["stamp_holds"] == "false" and "CoinHive" in rec["holds_reason"]


# ── 3. the validator argues the rival's case, and only ever downward ───────────

def test_a_selection_premise_with_a_rival_is_checked_by_steelmanning_the_rival():
    led = _ledger()
    p = led.premises["p1"]
    assert rival_mode(p) is True
    brief = brief_for_rival(p)
    assert "192.168.247.131" in brief
    # Blindness: the validator must not learn what it is arguing against.
    assert "192.168.70.186" not in brief


def test_a_premise_with_no_rival_keeps_the_original_brief():
    led = _ledger(kind="coverage", text="route (c) is NOT yet searched", rival="")
    assert rival_mode(led.premises["p1"]) is False


def test_standing_the_rival_up_refutes_the_incumbent():
    v = as_rival_verdict(PremiseUpdate(id="p1", status="VERIFIED", quote=QUOTE,
                                       evidence="CoinHive flows span 1666s"))
    assert v is not None and v.status == "REFUTED"


def test_failing_to_stand_the_rival_up_proves_nothing():
    """The argument from ignorance, refused in code. No evidence for the rival is not
    evidence for the incumbent, so the premise is left exactly where it was."""
    for status in ("REFUTED", "UNVERIFIED"):
        assert as_rival_verdict(
            PremiseUpdate(id="p1", status=status, quote=QUOTE,
                          evidence="could not stand it up")) is None
    assert as_rival_verdict(None) is None


# ── 4. "cannot be read" is a claim, held to the standard of any other claim ─────

def _unanswerable(**kw):
    return entry(**{"route": "ANSWER", "value": UNANSWERABLE_VALUE,
                    "value_kind": "not_answerable",
                    "source_senior": "s1", "answer_premise_ids": ["p1"],
                    "justification": "the value is in the pixels of image001.jpg, "
                                     "base64 in stream:smtp; nothing here renders "
                                     "an image", **kw})


def test_sh_cannot_declare_a_question_unanswerable_on_its_own_say_so():
    """The exit SH would take most eagerly is the one nothing can contradict. It needs
    a senior's verified, true-stamped premise, and SH verifies nothing."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="the value is only in image pixels", kind="coverage",
                          load_bearing=True, rival="")], author="s1", round_n=1)
    out = unanswerable_violations([_unanswerable()], led)
    assert out and "VERIFIED BY A SENIOR" in out[0]


def test_an_unanswerable_claim_a_senior_proved_and_sh_stamped_is_allowed():
    led = _ledger(kind="coverage", text="the visualization type appears nowhere in "
                                        "stream:smtp text; it is only in the pixels",
                  rival="")
    led.stamp_premise("p1", establishes=True, reason="the MIME walk shows it",
                      claim_holds=True, holds_reason="no textual rival remains",
                      round_n=3)
    assert unanswerable_violations([_unanswerable()], led) == []


def test_an_unanswerable_claim_needs_to_name_the_wall():
    led = _ledger(kind="coverage", text="only in the pixels", rival="")
    led.stamp_premise("p1", establishes=True, reason="shown", claim_holds=True,
                      holds_reason="none", round_n=3)
    out = unanswerable_violations([_unanswerable(justification="cannot")], led)
    assert out and "artifact" in out[0]


def test_an_ordinary_answer_is_untouched_by_the_unanswerable_gate():
    led = _ledger()
    ordinary = entry(route="ANSWER", value="112", value_kind="count",
                     source_senior="s1", answer_premise_ids=["p1"],
                     justification="the sole dp=3333 flow")
    assert unanswerable_violations([ordinary], led) == []


# ── the ledger survives the process that wrote it ──────────────────────────────

def test_a_questions_ledger_is_durable_the_moment_the_question_ends(tmp_path):
    """v0.4.3's single dump sat outside any try/finally, past the end of the question
    loop; a RunPaused unwound main() before it and took Q216's and Q217's premises
    with it."""
    dump_question_ledger(str(tmp_path), "Q216", _ledger())
    written = tmp_path / "premise_ledgers" / "Q216.json"
    assert written.exists()
    assert json.loads(written.read_text(encoding="utf-8"))[0]["qid"] == "Q216"


def test_a_resumed_segment_cannot_overwrite_an_earlier_one(tmp_path):
    """A resumed process starts with `ledgers = {}` and cannot re-derive what ran
    before it, so a single shared file could only ever be rewritten with less."""
    dump_question_ledger(str(tmp_path), "Q216", _ledger())      # first process
    dump_question_ledger(str(tmp_path), "Q224", _ledger())      # second process
    merged = tmp_path / "premise_ledger.json"
    # The resumed process holds only Q224 in memory, as the real runner does.
    n = dump_ledgers(str(merged), {"Q224": _ledger()}, run_dir=str(tmp_path))
    qids = {r["qid"] for r in json.loads(merged.read_text(encoding="utf-8"))}
    assert qids == {"Q216", "Q224"}, "the earlier segment must survive the merge"
    assert n == 2


def test_a_question_with_no_file_yet_still_reaches_the_merged_view(tmp_path):
    """A question the process holds but never finished is still better in than out."""
    merged = tmp_path / "premise_ledger.json"
    dump_ledgers(str(merged), {"Q329": _ledger()}, run_dir=str(tmp_path))
    qids = {r["qid"] for r in json.loads(merged.read_text(encoding="utf-8"))}
    assert qids == {"Q329"}


def test_the_wave_also_names_the_open_questions_owed_an_answer():
    """The same fault as the stamp, and a larger one: unanswered open questions
    rejected 17 turns in the v0.4.3 smoke run to the stamp's 11, and
    `open_question_violations` reads exactly this list to write its rejection."""
    led = _ledger()
    led.ask(["which endpoint do you mean?"], author="s1", round_n=1)
    wave = render_wave({"s1": {"report": "found it", "novel_spl_count": 3}},
                       slots_remaining=1, turns_remaining=4, ledger=led)
    assert "ANSWER BY ID" in wave
    assert "s1 asks q1" in wave


def test_a_wave_with_no_open_questions_says_nothing_about_them():
    led = _ledger()
    wave = render_wave({"s1": {"report": "found it", "novel_spl_count": 3}},
                       slots_remaining=1, turns_remaining=4, ledger=led)
    assert "ANSWER BY ID" not in wave
