#!/usr/bin/env python3
"""
Candidate ledger + (Task 4) case-file store for the v1 SH.

Ledger: every delegation's FINAL/PARTIAL ANSWER value is captured VERBATIM at
delegation time, with its evidence and SPL. The joiner chooses FROM the ledger
and copies — never re-types. run_1.2 lost 5,100 pts to values that existed in
a worker's answer and were mangled or bypassed at synthesis time (Q215
BSTOLL-L.froth.ly -> BSTOLL-L, Q221 nullweb_admin -> web_admin, Q331
1367.875 -> 1499.25). The ledger is also Plan C's adjudication input.
"""

from __future__ import annotations

import re

_ANSWER_TAG = re.compile(r'(?:FINAL|PARTIAL)\s+ANSWER:\s*(.+)', re.IGNORECASE)


def extract_candidate(delegation: dict) -> dict | None:
    """Verbatim candidate from one delegation record; None if it never committed
    to a value (ESCALATE / empty / crashed)."""
    text = delegation.get("answer") or ""
    m = _ANSWER_TAG.search(text)
    if not m:
        return None
    value = m.group(1).strip().splitlines()[0].strip()
    if not value:
        return None
    spl = delegation.get("spl_used") or []
    return {
        "value":    value,                       # verbatim — the joiner copies this
        "status":   delegation.get("status", "?"),
        "worker":   delegation.get("worker", ""),
        "spl":      spl[-1:],                    # the query that produced it
        "evidence": text[:400],
    }


def build_ledger(delegations: list) -> list[dict]:
    """One entry per distinct value (case-insensitive), first-seen form wins."""
    seen: set = set()
    out = []
    for d in delegations:
        c = extract_candidate(d)
        if c and c["value"].lower() not in seen:
            seen.add(c["value"].lower())
            out.append(c)
    return out


def snap_to_ledger(answer: str, ledger: list) -> str:
    """Byte-exact fidelity: if the answer case-insensitively equals a ledger
    value, return the ledger's verbatim form. Never substitutes a different
    value — truncations/supersets are a selection judgment (Plan C), not a
    casing slip."""
    a = (answer or "").strip().lower()
    for c in ledger:
        if c["value"].strip().lower() == a:
            return c["value"]
    return answer


def render_ledger(ledger: list) -> str:
    """Joiner-facing candidate block."""
    if not ledger:
        return ""
    lines = ["CANDIDATES (each captured verbatim from a worker — your FINAL ANSWER "
             "must be copied character-for-character from one of these, or from "
             "the question text):"]
    for i, c in enumerate(ledger, 1):
        spl = f"  SPL: {c['spl'][0][:160]}" if c["spl"] else ""
        lines.append(f"  {i}. `{c['value']}`  [{c['status']}, {c['worker']}]{spl}")
    return "\n".join(lines)
