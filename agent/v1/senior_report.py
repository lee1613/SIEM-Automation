#!/usr/bin/env python3
"""
The senior's report (spec §3.1): template validation, the word cap, and the
three header fields the RUNNER stamps rather than the senior.

`round`, `rounds_remaining` and `novel_spl_count` are stamped here because a
self-reported progress number is a progress number the senior can report
favourably. `novel_spl_count == 0` is literal thrashing and hard-fails R2
without an LLM in the loop (see conversation.effective_r2).

The "Prior rounds" section is the compression mechanism: the senior REWRITES it
each round rather than appending, so its own history stays six lines instead of
growing linearly — which is also why the latest report doubles as the
compaction artifact (§6).
"""

from __future__ import annotations

import re

REPORT_WORD_CAP = 400
PRIOR_ROUNDS_MAX_LINES = 6

REQUIRED_SECTIONS = (
    "## Prior rounds",
    "## This round",
    "### What I ran",
    "### What it means",
    "## Assumptions",
    "## Ruled out",
    "## Open questions for SH",
)


def _norm_query(q: str) -> str:
    """Whitespace- and case-insensitive form, so re-running a query with different
    spacing still counts as a repeat."""
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def novel_spl(prior: set, spl_used: list) -> tuple[int, set]:
    """How many queries this round this senior had not already run, and the
    updated seen-set. Diffed against ALL of its prior rounds, not just the last."""
    seen = {_norm_query(q) for q in prior}
    fresh = {_norm_query(q) for q in (spl_used or []) if _norm_query(q)}
    new = fresh - seen
    return len(new), seen | fresh


def truncate_words(text: str, cap: int = REPORT_WORD_CAP) -> tuple[str, bool]:
    """Cut a report at the word cap. `value`/`confidence` are separate schema
    fields, so truncating the prose never touches the answer (§8)."""
    m = list(re.finditer(r"\S+", text or ""))
    if len(m) <= cap:
        return text or "", False
    return text[:m[cap - 1].end()] + f"\n\n_[truncated at {cap} words]_", True


def report_violations(md: str) -> list[str]:
    """Template problems worth logging. Advisory: a malformed report is still
    read by SH — the rubric is what judges it."""
    out = [f"missing section {s!r}" for s in REQUIRED_SECTIONS if s not in (md or "")]
    body = re.search(r"^## Prior rounds[^\n]*$(.*?)(?=^## |\Z)", md or "",
                     re.MULTILINE | re.DOTALL)
    if body:
        lines = [ln for ln in body.group(1).splitlines() if ln.strip()]
        if len(lines) > PRIOR_ROUNDS_MAX_LINES:
            out.append(f"Prior rounds has {len(lines)} lines "
                       f"(cap {PRIOR_ROUNDS_MAX_LINES})")
    return out


_NOT_A_QUESTION = {"", "none", "n/a", "na", "(none)", "nothing", "no"}


def open_questions(md: str) -> list[str]:
    """The senior's "## Open questions for SH" bullets. SH must answer each one
    (conversation.open_question_violations), so a bullet saying "none" is not a
    question. The section ends at the next heading or the runner's cap line."""
    m = re.search(r"^## Open questions for SH[^\n]*$(.*?)(?=^#{1,3} |^_Iteration cap|\Z)",
                  md or "", re.MULTILINE | re.DOTALL)
    if not m:
        return []
    out = []
    for ln in m.group(1).splitlines():
        b = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", ln)
        if b and b.group(1).strip().strip(".").lower() not in _NOT_A_QUESTION:
            out.append(b.group(1).strip())
    return out


def unverified_premises(md: str) -> int:
    """How many lines of the "## Assumptions" section are marked UNVERIFIED —
    surfaced to SH as a warning, never a gate (R4 is soft by design)."""
    m = re.search(r"^## Assumptions[^\n]*$(.*?)(?=^#{1,3} |^_Iteration cap|\Z)",
                  md or "", re.MULTILINE | re.DOTALL)
    return sum(1 for ln in (m.group(1).splitlines() if m else []) if "UNVERIFIED" in ln)


def _has_assumption(md: str, label: str) -> bool:
    """Whether "## Assumptions" has a bullet opening with `label`."""
    m = re.search(r"^## Assumptions[^\n]*$(.*?)(?=^#{1,3} |^_Iteration cap|\Z)",
                  md or "", re.MULTILINE | re.DOTALL)
    return bool(m and re.search(rf"^\s*[-*]\s*\**{label}", m.group(1),
                                re.MULTILINE | re.IGNORECASE))


def has_selection_premise(md: str) -> bool:
    """Whether the report says why this entity and not another (a 'Selection' line)."""
    return _has_assumption(md, "Selection")


def has_coverage_premise(md: str) -> bool:
    """Whether the report lists the ways the question's concept could show up in the
    data and what searched each (a 'Coverage' line) — the set Selection chooses from."""
    return _has_assumption(md, "Coverage")


# Splunk bookkeeping present in every feed — never where a concept shows up.
_META_FIELD = re.compile(r"^(date_\w+|punct|linecount|splunk_server\w*|index|source|"
                         r"sourcetype|host|timeendpos|timestartpos|eventtype|tag(::\w+)?)$")


def report_scope(md: str) -> tuple[str, str]:
    """The (sourcetype, source) a report's **Scope:** line names; '' where absent."""
    m = re.search(r"^\*\*Scope:\*\*(.*)$", md or "", re.MULTILINE)
    if not m:
        return "", ""

    def one(key):
        v = re.search(rf"\b{key}\s*=\s*([^\s|,]+)", m.group(1))
        return v.group(1).strip("`\"'<>") if v else ""
    return one("sourcetype"), one("source")


def coverage_text(md: str) -> str:
    """The Coverage bullet of "## Assumptions", continuation lines included."""
    m = re.search(r"^\s*[-*]\s*\**Coverage(.*?)(?=^\s*[-*]\s|^#{1,3} |^_|\Z)",
                  md or "", re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def uncovered_fields(md: str, fields: list[str]) -> list[str]:
    """Fields of the report's scope its Coverage line never names — ways the
    concept could show up that nobody said were considered."""
    text = coverage_text(md).lower()
    return [f for f in fields
            if not _META_FIELD.match(f)
            and not re.search(rf"(?<![\w:]){re.escape(f.lower())}(?![\w:])", text)]


def stamp_header(md: str, *, senior_id: str, qid: str, round_n: int,
                 rounds_remaining: int, novel_spl_count: int) -> str:
    """Replace whatever title the senior wrote with the runner's own, and add the
    three fields the senior is not allowed to self-report."""
    body = (md or "").lstrip()
    # Remove the FIRST line matching ^# (senior's title) and any prior _stamped by runner: line
    lines = body.splitlines(keepends=True)
    filtered = []
    title_removed = False
    for line in lines:
        if not title_removed and re.match(r"^# ", line):
            title_removed = True
            continue
        if re.match(r"^_stamped by runner:", line):
            continue
        filtered.append(line)
    body = "".join(filtered).lstrip("\n")
    head = (f"# {senior_id} - {qid} - Round {round_n}\n"
            f"_stamped by runner: rounds_remaining={rounds_remaining} "
            f"novel_spl={novel_spl_count}_\n")
    return head + body
