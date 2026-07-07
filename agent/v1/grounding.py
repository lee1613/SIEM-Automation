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
    a = (answer or "").strip().lower()
    if not a:
        return False
    if a in (question_text or "").lower():
        return True
    for r in task_results.values():
        if a in (r.get("answer") or "").lower():
            return True
    return False


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
