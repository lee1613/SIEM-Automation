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

import json
import re

from langchain_core.tools import tool
from premise import KINDS, PremiseDraft, PremiseUpdate
from pydantic import ValidationError

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
def submit_finding(insight: str, value: str = "", value_kind: str = "",
                   evidence: str = "", confidence: int = 50,
                   sourcetypes_used: str = "", sources_used: str = "",
                   ruled_out: str = "", notes: str = "",
                   report: str = "", new_premises: list = None,
                   premise_updates: list = None,
                   open_questions: list = None) -> str:
    """Finish the task. Call this EXACTLY ONCE, as your final action.

    Every other tool gathers evidence; this one reports it. Do not write a prose
    answer instead - a value typed into a sentence gets mangled on the way to the
    scoreboard, which is scored on an exact string match.

    - insight: "FOUND" or "NOT_FOUND" — your one outcome. FOUND only when `value`
      holds a candidate for the question as asked AND its records show the act
      the question names. Otherwise NOT_FOUND, with `value` empty and what you
      learned in `notes`.
    - value: THE ANSWER ALONE, or EMPTY. Nothing downstream edits it - it is
      submitted for exact-match scoring exactly as you write it. So it carries
      no label, no units unless the question asks for them, no sentence around
      it and no hedge. Write "1367.875"; never "duration = 1367.875 seconds",
      never "1367.875 (not yet confirmed)", never "1367.875?". A value with a
      question mark or a caveat in it cannot be submitted and is discarded.
      IF YOU CANNOT STATE THE ANSWER ALONE, LEAVE `value` EMPTY and put what
      you found in `notes`. An empty `value` with strong `notes` is a useful
      result that shapes the next round; a paragraph in `value` is a wasted
      one. Always empty for NOT_FOUND.
    - value_kind: what `value` is - e.g. "count", "duration_seconds", "hostname",
      "username", "ip", "filename", "hash", "cve", "list". If the only honest
      kind you could write is "summary", "finding" or "analysis", then it is
      not an answer: empty `value` and move the text to `notes`.
    - evidence: the SPL that produced `value`, then what it returned, including
      the event count you saw.
    - confidence: 0-100, how sure you are of `value`. Be honest; a low number is
      more useful than a wrong high one. If the question names a specific feed
      and you did not query that feed, whatever you found somewhere else is
      corroboration, not the answer.
    - sourcetypes_used / sources_used: comma-separated feeds you actually queried.
    - ruled_out: feeds or hypotheses you CHECKED and eliminated, with why - e.g.
      "cisco:asa - carries no flow-duration field". This is worth nearly as much
      as an answer: it is what stops the next round re-treading your dead ends.
    - notes: what you learned that is NOT the answer - a field you discovered, a
      time window you narrowed, a host worth pivoting on, why a candidate could
      not be confirmed. A NOT_FOUND belongs here, and the orchestrator reads it
      to plan the next round.
    - new_premises: the premises you are filing THIS round, each an object
      {"text": ..., "kind": "coverage"|"selection"|"other",
       "load_bearing": true|false, "quote": ..., "evidence": ...}. Do NOT re-send
      premises you filed earlier - the runner holds them and shows them back to
      you every round, and a second open premise of a kind you already have open
      is read as a re-file and handed back to you. `text` is immutable once filed,
      so write it as you want it read in five rounds' time. `load_bearing` is true
      only when the answer breaks if this premise is false; marking everything
      load-bearing is the same as marking nothing.
      `quote`/`evidence` are optional and go together: leave them empty to file a
      hypothesis, or, when a result you ALREADY have settles the premise, put that
      output in `quote` word for word and why it settles it in `evidence` - the
      runner files it VERIFIED in one step, under the same checks as
      `premise_updates`, so you do not wait a round for its id.
    - premise_updates: verdicts on premises ALREADY in your ledger, each
      {"id": "p3", "status": "VERIFIED"|"REFUTED"|"UNVERIFIED",
       "quote": ..., "evidence": ...}. VERIFIED and REFUTED need a quote copied
      word for word from a query output you actually received - the runner checks
      it and keeps the old status if it is not there. UNVERIFIED withdraws a
      verdict and needs no quote.
    - open_questions: what you need SH to answer, one plain string each. SH must
      answer every one before your next round, so ask only what SH can settle:
      which entity is in scope, whether a prior finding applies, which scope to
      try next. Never an SPL question.
    - report: your round report in markdown, following the template you were given
      at spawn. ~600 words maximum. REWRITE the "Prior rounds" section each round
      instead of appending to it - six lines total, covering every prior round.
    """
    return "Finding recorded. Stop here - do not call any further tools."


def _split(s: str) -> list[str]:
    return [p.strip() for p in (s or "").replace("\n", ",").split(",") if p.strip()]


def _coerce_objects(value) -> list:
    """A list of dicts (or strings) from whatever the provider actually sent.

    Task 0 probed GLM-5.3 on AI& for nested tool arguments. This accepts a real
    list OR a JSON string either way, so the probe's outcome changes one type
    annotation on the tool and no logic at all - and a provider that changes its
    mind later costs nothing.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    if isinstance(value, dict):
        value = [value]
    return [v for v in (value or []) if isinstance(v, (dict, str))]


def _drafts(value) -> list:
    """PremiseDrafts from the tool's `new_premises`. A malformed one is dropped, not
    fatal: a round that filed four good premises and one bad is worth four."""
    out = []
    for d in _coerce_objects(value):
        if isinstance(d, str):
            d = {"text": d}
        text = str(d.get("text", "")).strip()
        if not text:
            continue
        kind = str(d.get("kind", "") or "other").strip().lower()
        try:
            out.append(PremiseDraft(text=text,
                                    kind=kind if kind in KINDS else "other",
                                    load_bearing=bool(d.get("load_bearing", False)),
                                    quote=str(d.get("quote", "") or "").strip(),
                                    evidence=str(d.get("evidence", "") or "").strip()))
        except ValidationError:
            continue
    return out


def _updates(value) -> list:
    """PremiseUpdates from the tool's `premise_updates`. An illegal status is dropped -
    the premise then keeps its old status, which is the safe direction."""
    out = []
    for u in _coerce_objects(value):
        if not isinstance(u, dict):
            continue
        try:
            out.append(PremiseUpdate(id=str(u.get("id", "")).strip(),
                                     status=str(u.get("status", "")).strip().upper(),
                                     quote=str(u.get("quote", "") or ""),
                                     evidence=str(u.get("evidence", "") or "")))
        except ValidationError:
            continue
    return out


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
        "insight":           "NOT_FOUND",
        "report":            "",
        "new_premises":      [],
        "premise_updates":   [],
        "open_questions":    [],
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

    # `insight` is the one outcome the worker reports; `status` is derived from it
    # for the ledger and the v1.3 compiler loop. A worker that still sends a legal
    # `status` (older transcripts, test fixtures) keeps it.
    status = str(args.get("status", "")).strip().lower()
    if status not in VALID_STATUS:
        found = re.sub(r"[\s_-]+", "", str(args.get("insight") or "").upper()) == "FOUND"
        has_value = bool(str(args.get("value", "")).strip())
        status = ("solved" if found and has_value else
                  "partial" if has_value or str(args.get("notes", "")).strip() else "failed")

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

    # `insight` is the routing enum SH reads first. A worker that omitted it, or
    # wrote something outside the two legal values, is classified the way the
    # ledger already classifies it: a committed, submittable value is FOUND.
    # Separators (spaces, hyphens, underscores) are stripped before comparison
    # so "Not-Found" / "NOTFOUND" / "not_found" all normalise the same way.
    insight_raw = re.sub(r"[\s_-]+", "", str(args.get("insight") or "").strip().upper())
    if insight_raw == "FOUND":
        insight = "FOUND"
    elif insight_raw == "NOTFOUND":
        insight = "NOT_FOUND"
    else:
        insight = "FOUND" if value else "NOT_FOUND"
    if not value:
        # A value demoted to `notes` above leaves no candidate to route on.
        insight = "NOT_FOUND"

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
        "insight":    insight,
        "report":     str(args.get("report") or "").strip(),
        "new_premises":    _drafts(args.get("new_premises")),
        "premise_updates": _updates(args.get("premise_updates")),
        # _coerce_objects, not a bare loop: a provider that sends the list as a JSON
        # string would otherwise be iterated character by character, filing one
        # open question per character - each with an id SH is then gated on.
        "open_questions":  [str(q).strip() for q in _coerce_objects(args.get("open_questions"))
                            if str(q).strip()],
    }
