#!/usr/bin/env python3
"""
Deterministic grounding check for the SH's final answer.

The joiner's FINAL ANSWER must appear verbatim (case-insensitive substring) in
at least one worker's answer text or in the question itself. If it doesn't, the
SH invented a value no delegate produced — the v1.1 fabrication failure mode
(Q221 'glacier', Q303 'tomcat7:Summer2018!', Q330 'james', Q333 'cve-2018-7600').
This module is pure so the guard is unit-testable without a live run.
"""

from __future__ import annotations

_STATUS_RANK = {"solved": 3, "partial": 2, "too_big": 1, "failed": 0}


def is_grounded(answer: str, task_results: dict, question_text: str = "") -> bool:
    """Whole answer — or, for comma-joined lists, EVERY component — must appear
    in some worker's answer text or the question itself.

    Component-wise matters: scoreboard list answers are comma-joined
    ('bstoll,btun,splunk_access,web_admin') while worker evidence lists the same
    values as prose/bullets, so the joined string never appears verbatim.
    run_1.2's Q200 lost 100 pts to replan churn because of this. A fabricated
    component still fails (it appears in no evidence), so the anti-fabrication
    guarantee is unchanged."""
    a = (answer or "").strip().lower()
    if not a:
        return False
    haystacks = [(question_text or "").lower()]
    haystacks += [(r.get("answer") or "").lower() for r in task_results.values()]
    parts = [p.strip() for p in a.split(",") if p.strip()] or [a]
    return all(any(p in h for h in haystacks) for p in parts)


def best_candidate(task_results: dict) -> str | None:
    """Highest-confidence non-empty worker answer, for the ungrounded fallback."""
    best = None
    best_rank = -1
    for r in task_results.values():
        ans = (r.get("answer") or "").strip()
        if not ans:
            continue
        rank = _STATUS_RANK.get(r.get("status", "failed"), 0)
        if rank > best_rank:
            best, best_rank = ans, rank
    return best
