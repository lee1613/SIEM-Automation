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


@tool
def submit_finding(status: str, value: str = "", value_kind: str = "",
                   evidence: str = "", confidence: int = 50,
                   sourcetypes_used: str = "", sources_used: str = "",
                   ruled_out: str = "", notes: str = "") -> str:
    """Finish the task. Call this EXACTLY ONCE, as your final action.

    Every other tool gathers evidence; this one reports it. Do not write a prose
    answer instead - a value typed into a sentence gets mangled on the way to the
    scoreboard, which is scored on an exact string match.

    - status: "solved" if you are confident in `value`; "partial" if you found a
      credible candidate but could not confirm it; "too_big" if the task needs
      narrowing; "failed" if you found nothing usable.
    - value: THE ANSWER ALONE, exactly as it should be submitted. No label, no
      units unless the question asks for them, no sentence around it. Write
      "1367.875", never "duration = 1367.875 seconds". Leave empty for status
      "failed" or "too_big".
    - value_kind: what `value` is - e.g. "count", "duration_seconds", "hostname",
      "username", "ip", "filename", "hash", "cve", "list".
    - evidence: the SPL that produced `value`, then what it returned, including
      the event count you saw.
    - confidence: 0-100, how sure you are of `value`. Be honest; a low number is
      more useful than a wrong high one.
    - sourcetypes_used / sources_used: comma-separated feeds you actually queried.
    - ruled_out: feeds or hypotheses you CHECKED and eliminated, with why - e.g.
      "cisco:asa - carries no flow-duration field". This is worth nearly as much
      as an answer: it is what stops the next round re-treading your dead ends.
    - notes: anything the orchestrator needs that does not fit above.
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

    return {
        "status":     status,
        "value":      str(args.get("value", "")).strip(),
        "value_kind": str(args.get("value_kind", "")).strip(),
        "evidence":   str(args.get("evidence", "")).strip(),
        "confidence": confidence,
        "search_space_used": {
            "sourcetypes": _split(args.get("sourcetypes_used", "")),
            "sources":     _split(args.get("sources_used", "")),
        },
        "negative_findings": _split(args.get("ruled_out", "")),
        "notes":      str(args.get("notes", "")).strip(),
        "structured": True,
    }
