#!/usr/bin/env python3
"""
The Senior worker's return contract.

A worker used to finish by writing prose and letting downstream code scrape a
value out of it. That scraping is where run_1.2 lost 5,100 points - not to wrong
investigation, but to wrong transcription: Q215 BSTOLL-L.froth.ly -> BSTOLL-L,
Q221 nullweb_admin -> web_admin, Q331 1367.875 -> 1499.25. Scoring is exact
match, so a value that survives the investigation and dies in the handoff scores
exactly zero.

So the worker now finishes with a TOOL CALL whose arguments are the schema. The
provider validates the shape, `value` arrives as its own field, and the
compensating stack downstream (a FINAL/PARTIAL ANSWER regex, a casing snap, a
label-prefix strip) has nothing left to repair.

A tool call rather than `response_format`, deliberately: the worker is a ReAct
loop whose terminal turn is not a single constrained completion, and tool calling
is the one structured-output mechanism every provider here supports.

Prose remains the fallback. Models skip the tool sometimes, and a worker that
answered in text is more useful than one recorded as having failed, so
`parse_finding` degrades to the old tags when no tool call is present.
"""

from __future__ import annotations

from langchain_core.tools import tool

# Ordered worst-to-best; mirrors grounding._STATUS_RANK.
VALID_STATUS = ("failed", "too_big", "partial", "solved")

# Shape of a submittable answer, measured against all 58 real BOTSv3 answers:
# the longest is 110 chars and 11 words (a User-Agent string), none contains a
# newline or a question mark, and every one has alphanumerics. These lived in
# extractor.py until that tier was deleted; they describe the SCOREBOARD's
# contract rather than any one model's, so they belong next to the schema.
MAX_ANSWER_CHARS = 200
MAX_ANSWER_WORDS = 12

# "solved" means "I am confident in `value`". Below this the worker has said
# both things at once, and the status is the half the joiner ranks on. 50 is
# the schema default and is already this project's line for "not confident" -
# it is the threshold at which SH is told to decompose a task.
SOLVED_MIN_CONFIDENCE = 50


def answer_shaped(value: str) -> bool:
    """Could this string be submitted to the scoreboard as-is?

    Not "is it correct" - only "is it an answer at all". Measured against the
    58 real BOTSv3 answers: none contains a newline, none exceeds 110 chars or
    11 words, none contains a question mark, and every one has alphanumeric
    characters. The word cap is what separates an answer from a sentence -
    length alone does not, because the longest real answer (a 110-char User-
    Agent string) is longer than most of the prose that needed rejecting.

    The caps are tight on purpose. Being too tight costs a demotion to `notes`,
    where the joiner still reads the text; being too loose puts a paragraph on
    the scoreboard. If this is ever pointed at a dataset with longer answers,
    these two numbers are what to re-measure.

    This exists because the prompt alone did not hold. In
    test_20260915_174228, 16 of 21 `partial` findings carried a `value`, and
    about ten of those were prose: "High-volume Linux privilege-escalation
    evidence is concentrated on hoth...", "stream:dns exposes query/queries,
    answer, dest/dest_ip...", "tomcat-users.xml not yet confirmed", "buser?",
    and one that was the single character "?". A `value` field holding a
    sentence defeats the entire reason schema B exists, and it flows straight
    into the ledger and the extractor fallback as though it were an answer.

    A hedge is rejected rather than repaired - "buser?" does NOT become
    "buser". Stripping the hedge would manufacture a confident answer out of
    an admission of doubt, which is the class of compensating hack schema B
    was built to delete.
    """
    v = (value or "").strip()
    return (bool(v) and "\n" not in v and len(v) <= MAX_ANSWER_CHARS
            and len(v.split()) <= MAX_ANSWER_WORDS
            and "?" not in v and any(c.isalnum() for c in v))


@tool
def submit_finding(status: str, value: str = "", value_kind: str = "",
                   evidence: str = "", confidence: int = 50,
                   sourcetypes_used: str = "", sources_used: str = "",
                   ruled_out: str = "", notes: str = "") -> str:
    """Finish the task. Call this EXACTLY ONCE, as your final action.

    Every other tool gathers evidence; this one reports it. Do not write a prose
    answer instead - a value typed into a sentence gets mangled on the way to the
    scoreboard, which is scored on an exact string match.

    - status: "solved" if you are confident in `value`; "partial" if you have
      something useful but not a confirmed answer; "too_big" if the task needs
      narrowing; "failed" if you found nothing usable.
    - value: THE ANSWER ALONE, or EMPTY. Nothing downstream edits it - it is
      submitted for exact-match scoring exactly as you write it. So it carries
      no label, no units unless the question asks for them, no sentence around
      it and no hedge. Write "1367.875"; never "duration = 1367.875 seconds",
      never "1367.875 (not yet confirmed)", never "1367.875?". A value with a
      question mark or a caveat in it cannot be submitted and is discarded.
      IF YOU CANNOT STATE THE ANSWER ALONE, LEAVE `value` EMPTY and put what
      you found in `notes`. An empty `value` with strong `notes` is a useful
      result that shapes the next round; a paragraph in `value` is a wasted
      one. Always empty for status "failed" or "too_big".
    - value_kind: what `value` is - e.g. "count", "duration_seconds", "hostname",
      "username", "ip", "filename", "hash", "cve", "list". If the only honest
      kind you could write is "summary", "finding" or "analysis", then it is
      not an answer: empty `value` and move the text to `notes`.
    - evidence: the SPL that produced `value`, then what it returned, including
      the event count you saw.
    - confidence: 0-100, how sure you are of `value`. Be honest; a low number is
      more useful than a wrong high one. It must agree with `status`: below 50
      you are not confident, so the status is "partial", not "solved". Reporting
      "solved" at low confidence is read as "partial" regardless.
      If the question names a specific feed and you did not query that feed,
      you are not solved - whatever you found somewhere else is corroboration.
    - sourcetypes_used / sources_used: comma-separated feeds you actually queried.
    - ruled_out: feeds or hypotheses you CHECKED and eliminated, with why - e.g.
      "cisco:asa - carries no flow-duration field". This is worth nearly as much
      as an answer: it is what stops the next round re-treading your dead ends.
    - notes: what you learned that is NOT the answer - a field you discovered, a
      time window you narrowed, a host worth pivoting on, why a candidate could
      not be confirmed. A "partial" with no clean value belongs here, and the
      orchestrator reads it to plan the next round.
    """
    return "Finding recorded. Stop here - do not call any further tools."


def _split(s: str) -> list[str]:
    return [p.strip() for p in (s or "").replace("\n", ",").split(",") if p.strip()]


def _find_tool_call(messages: list) -> dict | None:
    """Arguments of the last submit_finding call, or None.

    Scans the final state rather than having the tool write to shared memory:
    LangGraph runs fan-out branches on its own threads, so a module-level
    accumulator would need locking and would still interleave concurrent workers.
    """
    for msg in reversed(messages or []):
        for call in (getattr(msg, "tool_calls", None) or []):
            if (call.get("name") or "") == "submit_finding":
                return dict(call.get("args") or {})
    return None


def _classify_prose(answer: str) -> str:
    """Status from a worker's terminal text, for the no-tool-call fallback.

    'solved' requires an explicit FINAL ANSWER commitment - a non-empty tail with
    no tag means the worker never actually answered (e.g. ran out of iterations
    mid-tool-call), which must read as 'failed', not 'solved'.
    """
    a = (answer or "").strip()
    if not a:
        return "failed"
    upper = a.upper()
    if "ESCALATE:" in upper or upper.startswith("ESCALATE"):
        return "too_big"
    if "FINAL ANSWER" in upper:
        return "solved"
    if "PARTIAL ANSWER" in upper:
        return "partial"
    return "failed"


def empty_finding(status: str = "failed") -> dict:
    """Schema-B shaped result with nothing in it, for callers that never ran a
    worker (a provider outage, a runaway) but must still return the full shape."""
    return {
        "status":            status,
        "value":             "",
        "value_kind":        "",
        "evidence":          "",
        "confidence":        None,
        "search_space_used": {"sourcetypes": [], "sources": []},
        "negative_findings": [],
        "notes":             "",
        "structured":        False,
    }


def parse_finding(messages: list, answer: str) -> dict:
    """Schema-B finding from a finished worker.

    Returns the structured fields when the worker called submit_finding, and
    degrades to prose classification when it did not. `structured` records which
    happened, so the fallback rate is measurable rather than guessed at.
    """
    args = _find_tool_call(messages)
    if args is None:
        return empty_finding(_classify_prose(answer))

    status = str(args.get("status", "")).strip().lower()
    if status not in VALID_STATUS:
        # A worker that reported an unknown status still did the work. Infer from
        # whether it committed to a value rather than discarding the result.
        status = "partial" if str(args.get("value", "")).strip() else "failed"

    try:
        confidence = max(0, min(100, int(args.get("confidence", 50))))
    except (TypeError, ValueError):
        confidence = None

    # `value` is submitted verbatim, so anything that is not submittable is not
    # a value. Move it to `notes` rather than dropping it - the text is usually
    # a real finding written into the wrong field, and the joiner can still use
    # it there. Blanking without preserving would lose work; leaving it in
    # place would put a paragraph on the scoreboard (see answer_shaped).
    value = str(args.get("value", "")).strip()
    notes = str(args.get("notes", "")).strip()
    if value and not answer_shaped(value):
        notes = "\n".join(filter(None, [f"[not answer-shaped] {value}", notes]))
        value = ""
        # "solved" asserts confidence in a value that no longer exists. A worker
        # that wrote a paragraph where the answer goes did not solve anything.
        if status == "solved":
            status = "partial"

    # A worker cannot be both solved and unsure. Q216 of test_20260915_174228
    # was lost to exactly this: a worker that never queried the Cisco NVM feed
    # the question names returned `solved` at confidence 38, and `solved`
    # outranks `partial` in _STATUS_RANK, so it beat two workers that were on
    # the right feed. The confidence it reported on itself was already the
    # warning; nothing was reading it.
    if status == "solved" and confidence is not None \
            and confidence < SOLVED_MIN_CONFIDENCE:
        status = "partial"

    return {
        "status":     status,
        "value":      value,
        "value_kind": str(args.get("value_kind", "")).strip(),
        "evidence":   str(args.get("evidence", "")).strip(),
        "confidence": confidence,
        "search_space_used": {
            "sourcetypes": _split(args.get("sourcetypes_used", "")),
            "sources":     _split(args.get("sources_used", "")),
        },
        "negative_findings": _split(args.get("ruled_out", "")),
        "notes":      notes,
        "structured": True,
    }
