"""The validation agent (v0.4.3, spec 2 §3).

The case built against is Q216 r2's `p1`, verbatim from
`log/temp/v0.4.2_ledger_Q216_r2/premise_ledger.json`: a coverage premise whose own
text says route (c) was "NOT yet searched", marked VERIFIED by its author, quoting
the result of searching route (c) — 4,832 flows where the answer assumed one.
"""

from premise import PremiseDraft, PremiseLedger, PremiseUpdate
from validator import (
    as_refutation,
    brief_for,
    refusal_reason,
    validate,
)

P1_TEXT = ("In source=cisconvmflowdata, Monero generation can surface four ways: "
           "(a) a process-name census anomaly - searched, 60 names read; (b) a "
           "destination port in the Monero pool range - searched, only 3333 present "
           "with exactly 1 event; (c) flows to pool IP 45.77.53.176 on any port - NOT "
           "yet searched; (d) a sustained byte-volume signature - only partially "
           "examined.")
P1_QUOTE = ('{"da": "45.77.53.176", "count": "4832", "first_start": "1534758533", '
            '"last_end": "1534766374", "dp": ["3333", "443", "80"]}')

# What the validator's OWN searches returned. The quote it cites must be in here.
VALIDATOR_CORPUS = [
    '{"results": [{"da": "45.77.53.176", "count": "4832", "dp": ["3333", "443", "80"]}]}'
]


def _settled_ledger():
    led = PremiseLedger()
    led.add([PremiseDraft(text=P1_TEXT, kind="coverage", load_bearing=True)],
            author="s1", round_n=2)
    led.apply([PremiseUpdate(id="p1", status="VERIFIED", quote=P1_QUOTE,
                             evidence="the pool-IP census settles coverage")],
              author="s1", corpus=[P1_QUOTE], round_n=3)
    return led


class _Pool:
    """Records what the validator was asked, and replies with a fixed finding."""

    senior_model = "glm-5.3"

    def __init__(self, result):
        self.result = result
        self.seen = []

    def run_round(self, *, thread_id, message, qid, idx, technique, max_iter,
                  sid=""):
        self.seen.append({"message": message, "technique": technique,
                          "max_iter": max_iter, "thread_id": thread_id})
        return dict(self.result)


def _result(update, corpus=VALIDATOR_CORPUS):
    return {
        "premise_updates": [update] if update is not None else [],
        "full_state": [{"type": "ToolMessage", "name": "run_splunk_search",
                        "content": c} for c in corpus],
        "iterations": 4, "notes": "checked", "report": "r", "last_prompt_tokens": 10,
    }


# -- the briefing tells it the claim and nothing that identifies the question ----

def test_the_briefing_carries_the_claim_and_the_evidence_offered():
    p = _settled_ledger().premises["p1"]
    brief = brief_for(p)
    assert P1_TEXT in brief
    assert P1_QUOTE in brief


def test_the_briefing_hides_the_id_and_the_kind():
    """Both leak the shape of the investigation: the id says how many premises exist
    and in what order, the kind names the move the author was making.

    Checked on a premise whose own text says neither, so a hit is the briefing
    emitting the field rather than the author having used the word."""
    led = PremiseLedger()
    led.add([PremiseDraft(text="the miner ran on one host", kind="coverage",
                          load_bearing=True)], author="s1", round_n=2)
    brief = brief_for(led.premises["p1"])
    assert "p1" not in brief
    assert "coverage" not in brief.lower()


def test_a_premise_with_no_quote_still_briefs():
    led = PremiseLedger()
    led.add([PremiseDraft(text="a bare claim", kind="other", load_bearing=True)],
            author="s1", round_n=1)
    assert "a bare claim" in brief_for(led.premises["p1"])


# -- the verdict path -----------------------------------------------------------

def test_a_refutation_overturns_the_authors_own_verdict():
    """The whole point. s1 filed it, s1 verified it, and nothing else in the system
    reads the premise against its quote."""
    led = _settled_ledger()
    pool = _Pool(_result(PremiseUpdate(
        id="p", status="REFUTED",
        quote='{"da": "45.77.53.176", "count": "4832", "dp": ["3333", "443", "80"]}',
        evidence="the claim says route (c) was not searched; this is route (c), and "
                 "it returns 4,832 flows across three ports")))

    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert refusal_reason(out["update"], out["corpus"]) == ""
    assert led.apply([out["update"]], author="v1", corpus=out["corpus"],
                     round_n=4) == []
    assert led.premises["p1"].status == "REFUTED"
    assert led.premises["p1"].verified_by == "v1"


def test_the_runner_substitutes_the_real_id_for_the_placeholder():
    """The validator is handed one premise and told to use the literal "p"."""
    led = _settled_ledger()
    pool = _Pool(_result(PremiseUpdate(id="p", status="REFUTED",
                                       quote=VALIDATOR_CORPUS[0], evidence="why")))
    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert out["update"].id == "p1"


def test_the_validator_runs_as_its_own_role_with_its_own_iteration_cap():
    led = _settled_ledger()
    pool = _Pool(_result(None))
    validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1, iters=8)
    assert pool.seen[0]["technique"] == "validator"
    assert pool.seen[0]["max_iter"] == 8


def test_a_quote_the_validator_did_not_run_is_refused():
    """Quoting the evidence it was handed is not running a search - and the corpus it
    is checked against is its OWN tool output, never the author's."""
    led = _settled_ledger()
    pool = _Pool(_result(PremiseUpdate(id="p", status="REFUTED",
                                       quote="something nobody ran at all",
                                       evidence="why"), corpus=VALIDATOR_CORPUS))
    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert refusal_reason(out["update"], out["corpus"]) == "quoted something it did not run"
    led.apply([out["update"]], author="v1", corpus=out["corpus"], round_n=4)
    assert led.premises["p1"].status == "VERIFIED", "a refused verdict changes nothing"


def test_filing_no_verdict_is_refused_and_changes_nothing():
    led = _settled_ledger()
    pool = _Pool(_result(None))
    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert out["update"] is None
    assert refusal_reason(out["update"], out["corpus"]) == "filed no single verdict"
    assert led.premises["p1"].status == "VERIFIED"


def test_filing_several_verdicts_is_refused():
    """One premise, one ruling. Several means it did not do the one thing asked."""
    led = _settled_ledger()
    res = _result(PremiseUpdate(id="p", status="REFUTED", quote=VALIDATOR_CORPUS[0],
                                evidence="why"))
    res["premise_updates"].append(PremiseUpdate(id="p", status="VERIFIED",
                                                quote=VALIDATOR_CORPUS[0],
                                                evidence="no, why not"))
    out = validate(_Pool(res), led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert out["update"] is None


def test_an_unverified_verdict_needs_no_quote():
    led = _settled_ledger()
    pool = _Pool(_result(PremiseUpdate(id="p", status="UNVERIFIED", quote="",
                                       evidence="a full pool-IP census would settle it")))
    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert refusal_reason(out["update"], out["corpus"]) == ""


def test_a_circular_quote_is_refused():
    led = _settled_ledger()
    circular = "the coverage was established by SH outside this feed"
    pool = _Pool(_result(PremiseUpdate(id="p", status="VERIFIED", quote=circular,
                                       evidence="SH said so"), corpus=[circular]))
    out = validate(pool, led.premises["p1"], vid="v1", qid="Q216", idx=1)
    assert refusal_reason(out["update"], out["corpus"]) == "quoted SH as the authority"


def test_the_budget_is_the_senior_pool():
    """No constant caps validators any more. Retiring the senior costs a spawn slot, so
    the mechanism self-caps at the tier's senior count - three, and r2 used one."""
    import validator
    assert not hasattr(validator, "MAX_VALIDATORS_PER_QUESTION")


# -- an UNVERIFIED verdict is a refutation ---------------------------------------

def test_an_unverified_verdict_becomes_a_refutation():
    """Two readers could not stand the claim up. Without this the premise keeps the
    status it had - which, on the premise SH just stamped false, is VERIFIED."""
    out = as_refutation(PremiseUpdate(id="p1", status="UNVERIFIED", quote="",
                                      evidence="a full-feed census would settle it"))
    assert out.status == "REFUTED"
    assert "could not be settled" in out.evidence
    assert out.id == "p1"


def test_a_verified_or_refuted_verdict_passes_through_untouched():
    for status in ("VERIFIED", "REFUTED"):
        u = PremiseUpdate(id="p1", status=status, quote=VALIDATOR_CORPUS[0],
                          evidence="why")
        assert as_refutation(u) is u


def test_no_verdict_at_all_is_not_a_refutation():
    """A validator that filed nothing, or quoted something it did not run, or died in
    transport, has not ruled on anything - a transport failure is not a reasoning
    outcome."""
    assert as_refutation(None) is None


# -- the validator's second mode --------------------------------------------------

def test_an_offered_quote_asks_whether_it_establishes_the_claim():
    p = _settled_ledger().premises["p1"]
    brief = brief_for(p)
    assert "does that evidence establish this claim as written" in brief.lower()
    assert P1_QUOTE in brief


def test_no_offered_quote_asks_it_to_settle_the_claim_itself():
    """The mode that worked. Handed r2's p1 with nothing attached, the obvious move is
    to go and search route (c) - which is what v1 did with its full-feed dh scan, the
    one time this architecture found the right lead."""
    led = PremiseLedger()
    led.add([PremiseDraft(text=P1_TEXT, kind="coverage", load_bearing=True)],
            author="s1", round_n=2)
    brief = brief_for(led.premises["p1"])
    assert "settle this claim from the data yourself" in brief.lower()
    assert "no evidence has been offered" in brief.lower()
    assert P1_TEXT in brief
