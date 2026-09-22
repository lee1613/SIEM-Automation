#!/usr/bin/env python3
"""
The validation agent (v1.4.3, spec 2 §3).

WHY. Two Q216 ledger runs showed the same hole from opposite sides. In r1 SH filed
18 premises and verified 15 of its own; in r2 the senior filed all 3 and verified
all 3 of its own. Both are self-certification — the ANSWER gate is satisfied by a
premise whose author is also its only witness, and no amount of prompt tuning fixes
that, because neither party is disinterested.

WHAT IT CATCHES. r2's coverage premise said, in its own text, that route (c) —
flows to the pool IP on any port — was "NOT yet searched". It was marked VERIFIED,
quoting the result of searching route (c): 4,832 flows across three hosts, where the
answer assumed one. The quote is genuine output of a search the author really ran
(`quote_supported` passes) and does not cite SH (`CIRCULAR` passes). Both gates are
correct by their own terms. Reading the premise against its quote is comprehension,
not a string test — so it needs a reader, and a reader who wants nothing.

THE BLINDNESS IS THE POINT (spec 2 §3.2). The validator is given the claim and the
evidence offered for it, and NOT the question, the reports, the candidate or the
other premises. Handing it the reports would make it better informed and faster, and
would also make it a second opinion briefed to confirm — which is exactly what the
senior it is checking already is.
"""

from __future__ import annotations

from premise import CIRCULAR, PremiseUpdate, quote_supported
from senior_session import tool_outputs

VALIDATOR_ROUNDS = 1
VALIDATOR_ITERS = 8

# The id a validator is told to use. It is handed exactly one premise, so it has no
# id to copy and must not be shown the real one - ids leak the question's shape (how
# many premises exist, in what order). The runner substitutes the real id.
PLACEHOLDER_ID = "p"

def brief_for_rival(premise) -> str:
    """Hand the validator the RIVAL as the claim to settle, and never mention the
    incumbent.

    THE SHAPE IS PROOF BY CONTRADICTION (reductio ad absurdum): to test "the answer is
    X", assume the strongest not-X and go looking for what would make it true. Popper's
    falsification is the same move in empirical dress - you do not go out to confirm the
    thing you believe, you go out to break it, and it earns its keep by surviving.

    WHY IT IS NEEDED HERE. Checking the incumbent is a confirmation frame: the claim
    arrives already argued for, with its evidence attached, and the reader's job is
    phrased as agreeing or not. Q216 shows what that costs - "the endpoint is
    192.168.70.186 because it alone has the pool-port flow" was re-checked round after
    round and passed every time, while the endpoint the question actually meant sat two
    rows below it in the same table and was never once made the subject of a search.
    Nobody was ever asked to make the CoinHive host's case.

    THE LIMIT, STATED SO IT IS NOT MISREAD. A validator that fails to stand the rival up
    does NOT prove the incumbent. "No evidence was found for X" is not "X is false" -
    treating it as proof is the argument from ignorance, and this function must never be
    read as supplying one. It yields evidence in one direction only: a rival that IS
    stood up refutes the incumbent outright, and a rival that is not merely leaves the
    incumbent exactly where it already stood.

    The blindness rule is unchanged: the validator gets the rival claim and nothing that
    would identify the question, the incumbent, or whose side it is on.
    """
    return "\n".join([
        f'THE CLAIM TO CHECK, word for word:\n\n  "{premise.rival.strip()}"\n',
        "No evidence has been offered for it. YOUR TASK: settle this claim from the "
        "data yourself - run the searches that would show it true, and report what you "
        "find either way. Do not conclude it is false because it is unproven; go and "
        "look. If it names something as not yet searched, or not yet checked, search "
        "it.",
        "File your verdict with submit_finding.",
    ])


def brief_for(premise) -> str:
    """The validator's entire briefing: one claim, and the evidence offered for it when
    there is any.

    Two modes, because a nomination has two sources:
      * an offered quote - does this evidence establish this claim as written?
      * no quote (a premise its senior left UNVERIFIED) - settle it from the data.

    The second is the mode that worked. Handed r2's `p1` - "(c) flows to pool IP
    45.77.53.176 on any port - NOT yet searched" - with nothing attached and told to
    settle it, the obvious move is to go and search route (c). That is what `v1` did in
    v1.4.3 r1 with its full-feed `dh` scan, the one time this architecture found the
    right lead. It also answers the standing question about the briefing: both r2
    validator failures were "quoted something it did not run", the validator echoing
    the evidence it was handed, and this mode hands it nothing to echo.

    Everything that could identify the question is left out either way, including the
    premise's `kind` (coverage/selection names the shape of the investigation) and its
    id.
    """
    parts = [f'THE CLAIM TO CHECK, word for word:\n\n  "{premise.text}"\n']
    if premise.quote:
        parts.append("THE EVIDENCE ITS AUTHOR OFFERED, which you are checking - it is "
                     "a claim about the data, not a fact:\n\n"
                     f"  {premise.quote}\n")
        if premise.evidence:
            parts.append(f"WHY ITS AUTHOR SAID THAT SETTLES IT:\n\n  {premise.evidence}\n")
        parts.append("YOUR TASK: does that evidence establish this claim as written? "
                     "Check the claim against its own words first, then against the "
                     "data - your own results decide, not the author's.")
    else:
        parts.append("No evidence has been offered for it. YOUR TASK: settle this claim "
                     "from the data yourself - run the searches that show it true or "
                     "false. If the claim names something as not yet searched, or not "
                     "yet checked, search it.")
    parts.append("File your verdict with submit_finding.")
    return "\n".join(parts)


def _verdict_from(result: dict):
    """The single `premise_updates` entry a validator files, or None.

    A validator that files nothing, or files several, has not done the one thing it
    was asked to do; the premise then keeps the status it had, which is the safe
    direction.
    """
    updates = result.get("premise_updates") or []
    return updates[0] if len(updates) == 1 else None


def rival_mode(premise) -> bool:
    """Check the rival instead of the incumbent when there IS a named rival.

    Only `selection` premises are required to name one (`PremiseLedger.add` refuses a
    selection premise with an empty `rival`), and a selection premise is precisely the
    kind that picks one entity over another - the kind Q216 got wrong. A coverage or
    other premise with no rival has nothing to steelman, so it keeps the original brief.
    """
    return premise.kind == "selection" and bool((premise.rival or "").strip())


def validate(pool, premise, *, vid: str, qid: str, idx: int,
             iters: int = VALIDATOR_ITERS) -> dict:
    """Run one validator against one premise. Returns what the runner needs to log.

    `update` is None when the validator filed no usable verdict. `corpus` is the
    validator's OWN tool output - the quote is checked against what this agent
    received, never against the author's, or the check would be circular in the
    other direction.
    """
    rival = rival_mode(premise)
    brief = brief_for_rival(premise) if rival else brief_for(premise)
    result = pool.run_round(thread_id=f"{qid}-{vid}", message=brief,
                            qid=qid, idx=idx, technique="validator", max_iter=iters,
                            sid=vid)
    update = _verdict_from(result)
    if update is not None:
        update = PremiseUpdate(id=premise.id, status=update.status,
                               quote=update.quote, evidence=update.evidence)
    return {
        "vid": vid,
        "premise_id": premise.id,
        "rival_mode": rival,
        "update": update,
        "corpus": tool_outputs(result.get("full_state")),
        "iterations": result.get("iterations", 0),
        "notes": result.get("notes", ""),
        "report": result.get("report", ""),
        "last_prompt_tokens": result.get("last_prompt_tokens", 0),
    }


def refusal_reason(update, corpus: list[str]) -> str:
    """Why the ledger will refuse this verdict, or "" when it will take it.

    `PremiseLedger.apply` already enforces all of this and returns a note. This
    duplicates the *reasons* only so the runner can log a validator's wasted round
    distinctly from a senior's - a validator that cannot quote its own result is a
    budget question, not a correctness one.
    """
    if update is None:
        return "filed no single verdict"
    if update.status not in ("VERIFIED", "REFUTED"):
        return ""
    if CIRCULAR.search(update.quote or ""):
        return "quoted SH as the authority"
    if not quote_supported(update.quote, corpus):
        return "quoted something it did not run"
    if not update.evidence.strip():
        return "gave no reason the quote settles it"
    return ""


def as_rival_verdict(update):
    """Translate a verdict about the RIVAL into a verdict about the incumbent premise.

    The validator was shown the rival's words and nothing else, so its status is a
    statement about the rival:

      * rival VERIFIED   -> the incumbent selection is REFUTED. Something that fits the
                            question at least as well has been stood up from data, so
                            the claim "it is this one and not another" is false.
      * rival REFUTED     -> the incumbent is NOT confirmed. It is left alone. Concluding
      * rival UNVERIFIED     otherwise would be the argument from ignorance: failing to
                             make the rival's case is not making the incumbent's.

    The asymmetry is deliberate and is the whole safety property of doing it this way -
    the test can only ever take a claim DOWN, never prop one up, so a lazy or unlucky
    validator cannot manufacture support for whatever SH already believed.
    """
    if update is None or update.status != "VERIFIED":
        return None
    return PremiseUpdate(
        id=update.id, status="REFUTED", quote=update.quote,
        evidence="an independent reader stood up the rival reading from data, so this "
                 "selection does not hold: " + (update.evidence or "no reason given"))


def as_refutation(update):
    """An UNVERIFIED verdict is a refutation; anything else passes through.

    Two readers could not stand the claim up, and the premise is not left looking
    settled because the second one ran out of room. Without this the mechanism costs a
    senior slot and changes nothing: the premise SH stamped false is VERIFIED, and a
    validator that shrugs leaves it VERIFIED.

    `None` - no usable verdict, a quote it did not run, a crash in transport - is NOT
    a refutation. That validator ruled on nothing, and a transport failure is not a
    reasoning outcome.
    """
    if update is None or update.status != "UNVERIFIED":
        return update
    return PremiseUpdate(
        id=update.id, status="REFUTED", quote=update.quote,
        evidence="the claim could not be settled by an independent reader: "
                 + (update.evidence or "no reason given"))
