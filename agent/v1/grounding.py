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
    """Whole answer must appear in some worker's answer text or the question.

    For comma-joined lists whose full joined string doesn't appear verbatim
    (scoreboard list answers are comma-joined while worker evidence lists the
    same values as prose/bullets — 'bstoll,btun,...' never appears joined),
    fall back to requiring EVERY component present instead. The whole-string
    check runs first so a single value that happens to contain a comma (e.g.
    '1,234') isn't vacuously grounded by unrelated short fragments matching
    elsewhere — it only degrades to per-component matching when it looks like
    a genuine multi-value list (2+ non-empty comma-separated parts) AND the
    joined form itself isn't directly traceable."""
    a = (answer or "").strip().lower()
    if not a:
        return False
    haystacks = [(question_text or "").lower()]
    # Schema B's `value` is checked alongside the prose. A worker that called
    # submit_finding has the bare value as its own field, so grounding it is an
    # exact match rather than a substring hunt through a sentence.
    for r in task_results.values():
        haystacks.append((r.get("answer") or "").lower())
        haystacks.append((r.get("value") or "").lower())
    if any(a in h for h in haystacks):
        return True
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) <= 1:
        return False
    if all(p.isdigit() for p in parts):
        # All-digit parts (e.g. "1,234") are a thousands-separated number, not
        # a real list — component-wise matching would vacuously ground it on
        # unrelated short digit substrings appearing elsewhere in evidence.
        return False
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
