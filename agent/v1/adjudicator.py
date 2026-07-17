#!/usr/bin/env python3
"""
Plan C adjudicator: evidence-ranked candidate selection over the Plan B ledger.

run_1.2 lost 5,100 pts on questions where a correct candidate existed in some
delegation and the joiner picked a different grounded-but-wrong one by
recency/fluency (Q318 Canada-over-Russia, Q331 manual-Tukey-over-SPL, Q324
T-Mobile, Q323 superset). The adjudicator ranks candidates by explicit rules;
a deterministic guard (resolve_choice) makes it impossible for the pipeline to
submit a value the adjudicator invented — Q321's `1000`-from-nowhere class.
"""

from __future__ import annotations

import re
from case_file import extract_candidate

_STATUS_RANK = {"solved": 3, "partial": 2, "too_big": 1, "failed": 0}


ADJUDICATOR_SYSTEM_PROMPT = """You are the ADJUDICATOR for a BOTSv3 security \
investigation. Splunk workers produced candidate answers to one question. Pick \
the ONE candidate that best answers it — by the explicit rules below, never by \
fluency, recency, or which worker sounded most confident.

RANKING RULES, in priority order:
(a) CONSTRAINT COMPLIANCE — the winning candidate's METHOD must satisfy the
    question's own constraints. "using Splunk commands only" -> the SPL shown
    must do the computation (perc25()/perc75()/avg()), never hand arithmetic.
    "first/earliest/last by event order" -> ordering must come from the data.
(b) FIELD-VALUE FIDELITY — prefer the candidate that is a verbatim field value
    over a re-typed, trimmed, or expanded variant (keep domain suffixes,
    prefixes, exact casing).
(c) CARDINALITY/SHAPE — match the answer guidance. "at least two short
    hostnames" -> the minimal consistent set, never a superset.
(d) EVIDENCE STRENGTH — direct measurement > inference; sustained behaviour >
    a single connection; status solved > partial > too_big/failed.

HARD RULE: your CHOICE must be one of the listed candidates copied
character-for-character (or a value that appears in the question text). If no
candidate satisfies the question, output the best honest candidate — or
UNKNOWN if none is defensible. NEVER synthesize a new value or number.

OUTPUT FORMAT — exactly these lines:
CHOICE: <one candidate value copied character-for-character, or UNKNOWN>
CONFIDENCE: HIGH|MEDIUM|LOW
REASON: <one line citing the rule(s) that decided it>
TIEBREAK: <one fully self-contained Splunk subquestion that would settle it>
The TIEBREAK line is optional — include it ONLY when two candidates genuinely
conflict and one targeted query would resolve which is right."""


def parse_adjudication(text: str) -> dict:
    """Parse the adjudicator LLM's output. Missing/garbage fields degrade to
    empty choice + low confidence so the caller falls back deterministically."""
    t = text or ""
    cm = re.search(r'CHOICE:\s*(.+)', t, re.IGNORECASE)
    choice = cm.group(1).strip().splitlines()[0].strip() if cm else ""
    if choice.upper() == "UNKNOWN":
        choice = ""
    conf_m = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', t, re.IGNORECASE)
    confidence = conf_m.group(1).lower() if conf_m else "low"
    tb_m = re.search(r'TIEBREAK:\s*(.+)', t, re.IGNORECASE)
    tiebreak = tb_m.group(1).strip().splitlines()[0].strip() if tb_m else ""
    return {"choice": choice, "confidence": confidence, "tiebreak": tiebreak}


def resolve_choice(choice: str, ledger: list, question_text: str = "") -> str | None:
    """Deterministic guard: the choice is only usable if it case-insensitively
    equals a ledger value (returned in the ledger's verbatim form) or appears
    in the question text. Anything else is a synthesized value -> None."""
    c = (choice or "").strip()
    if not c:
        return None
    cl = c.lower()
    for entry in ledger:
        if entry["value"].strip().lower() == cl:
            return entry["value"]
    if question_text and cl in question_text.lower():
        return c
    return None


def fallback_choice(ledger: list) -> str | None:
    """Best honest candidate by status rank — the Q321 hard-rule fallback."""
    best, best_rank = None, -1
    for e in ledger:
        rank = _STATUS_RANK.get(e.get("status", "failed"), 0)
        if rank > best_rank:
            best, best_rank = e["value"], rank
    return best


def render_adjudication_input(question: str, guidance: str, ledger: list) -> str:
    """Adjudicator-facing digest: question + guidance + every candidate with
    its status, worker, SPL method, and evidence excerpt. KB-scale by design."""
    lines = [f"QUESTION: {question}"]
    if guidance:
        lines.append(f"ANSWER GUIDANCE: {guidance}")
    lines.append("\nCANDIDATES:")
    for i, c in enumerate(ledger, 1):
        lines.append(f"{i}. `{c['value']}`  [status={c['status']}, {c['worker']}]")
        if c.get("spl"):
            lines.append(f"   SPL: {c['spl'][0][:200]}")
        if c.get("evidence"):
            lines.append(f"   evidence: {c['evidence'][:300]}")
    lines.append("\nApply the ranking rules and output CHOICE / CONFIDENCE / "
                 "REASON (and TIEBREAK only if one query would settle a "
                 "genuine conflict).")
    return "\n".join(lines)


def adjudicate_once(invoke, question: str, guidance: str, ledger: list) -> dict:
    """One adjudication pass. `invoke` is Callable[[str], str] so tests inject
    a fake and the orchestrator injects the real gpt-5.4 call."""
    raw = invoke(render_adjudication_input(question, guidance, ledger))
    parsed = parse_adjudication(raw)
    answer = resolve_choice(parsed["choice"], ledger, question)
    return {"answer": answer, "confidence": parsed["confidence"],
            "tiebreak": parsed["tiebreak"], "raw": raw}


def majority_answer(records: list) -> dict | None:
    """C4 self-consistency: metrics tasks are sampled 3x (temperature 0.3);
    the value extracted from a strict majority (>=2) of records wins. Returns
    the winning record (best status among the majority's holders) so the
    executor can use it verbatim as the task result; None when no majority —
    caller falls back to its first result. Q206's 2.9348->2.94 rounding slip
    and Q331's manual-vs-SPL method split are both caught by a 3-sample vote."""
    votes: dict[str, list] = {}
    for r in records:
        c = extract_candidate(r)
        if not c:
            continue
        votes.setdefault(c["value"].strip().lower(), []).append(r)
    if not votes:
        return None
    holders = max(votes.values(), key=len)
    if len(holders) < 2:
        return None
    return max(holders, key=lambda r: _STATUS_RANK.get(r.get("status"), 0))
