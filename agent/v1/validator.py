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


def validate(pool, premise, *, vid: str, qid: str, idx: int,
             iters: int = VALIDATOR_ITERS) -> dict:
    """Run one validator against one premise. Returns what the runner needs to log.

    `update` is None when the validator filed no usable verdict. `corpus` is the
    validator's OWN tool output - the quote is checked against what this agent
    received, never against the author's, or the check would be circular in the
    other direction.
    """
    result = pool.run_round(thread_id=f"{qid}-{vid}", message=brief_for(premise),
                            qid=qid, idx=idx, technique="validator", max_iter=iters)
    update = _verdict_from(result)
    if update is not None:
        update = PremiseUpdate(id=premise.id, status=update.status,
                               quote=update.quote, evidence=update.evidence)
    return {
        "vid": vid,
        "premise_id": premise.id,
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
