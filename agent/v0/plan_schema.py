#!/usr/bin/env python3
"""
SH's plan as a validated object, plus the dataset briefing it plans against.

Two changes in one place, because they only make sense together.

THE BRIEFING. SH has no Splunk tools and never will - it plans and delegates, and
every Splunk call is priced on a cheaper model. But it was choosing search scopes
with no idea what the index contains, and BOTSv3 addresses data on two axes:
`sourcetype=syslog` hides 78,459 Cisco NVM flow events reachable only as
`source="cisconvmflowdata"`, the 13th busiest feed in the index. A plan that only
ever names sourcetypes cannot reach it. So SH opens every question with the
sourcetype list and the busiest sources, read from the manifest - static, because
BOTSv3 is static (docs/future_work.md #1 covers making this portable).

Top 100 sources rather than all 1003: the top 100 carry 99.565% of events at
~1.4K tokens; the remaining 903 carry 0.435% and cost ~29K more. The tail is
reachable on demand and is not worth paying for on every planner turn.

THE PLAN. The planner used to emit prose that a regex scraped numbered tasks out
of. Now it returns a validated object, so a spawn either parses or the call fails
loudly - no silent "no structured tasks parsed" fallback to a single task.

`confidence` is RECORDED, NOT ACTED ON. It is SH's own estimate that the answer
lies in the search space it named, and nothing in this system has ever emitted
one, so there is no calibration behind it. `spawn_report.py` builds the
solved-rate-by-decile table; once that says the number means something it can
start gating fan-out. Until then the existing 1-6 task cap governs. See
docs/future_work.md #4.
"""

from __future__ import annotations

import json
import os
from typing import Literal

from pydantic import BaseModel, Field

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "botsv3_fields.json")
BRIEFING_TOP_SOURCES = 100


class Spawn(BaseModel):
    """One worker SH wants dispatched."""

    spawn_type: Literal["senior", "exploration"] = Field(
        description="'senior' investigates a named search space. 'exploration' is "
                    "for when you cannot name one at all - it hunts for which feeds "
                    "even mention the question's key terms, and reports back.")
    subquestion: str = Field(
        description="Fully self-contained task. Name every entity, time range and "
                    "feed explicitly - workers share no memory with each other or "
                    "with you. Use $N to reference task N's result inline.")
    sourcetypes: list[str] = Field(
        description="Sourcetypes this worker should search, taken from the "
                    "briefing. Empty if you are scoping by source alone.")
    sources: list[str] = Field(
        description="Sources this worker should search, taken from the briefing. "
                    "A source filter alone is valid and is sometimes the only way "
                    "to reach a feed hidden under a generic sourcetype.")
    prior_info: str = Field(
        description="What you already know that narrows this worker's hunt - "
                    "entities from earlier questions, a time window, a feed already "
                    "ruled out. Empty string if you have nothing useful.")
    confidence: int = Field(
        ge=0, le=100,
        description="0-100: how sure you are the answer lies in the search space "
                    "you just named. Be honest - this is recorded and calibrated, "
                    "not used to judge you.")
    deps: list[int] = Field(
        description="Task numbers whose results this one needs first. Empty means "
                    "it runs in parallel with everything else - prefer that.")


class Plan(BaseModel):
    """SH's answer to one question: a direct answer, or workers to spawn."""

    goal: str = Field(description="What the question asks for, and what kind of "
                                  "value the scoreboard expects back.")
    expected_shape: str = Field(
        description="Exact form the scoreboard wants - e.g. 'bare MAC address "
                    "lowercase', 'integer only', 'comma-separated lowercase list "
                    "no spaces', 'filename with extension'.")
    direct_answer: str = Field(
        description="Fill ONLY if you already know the answer from cross-question "
                    "memory or general knowledge - never from an unverified "
                    "case-file finding. When set, leave spawns empty. Otherwise "
                    "an empty string.")
    spawns: list[Spawn] = Field(
        description="1-6 workers to dispatch. Exactly one if the question is a "
                    "single atomic lookup. Empty only when direct_answer is set.")


# ── briefing ──────────────────────────────────────────────────────────────────

def load_manifest(path: str = MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_briefing(manifest: dict, top_n: int = BRIEFING_TOP_SOURCES) -> str:
    """The dataset block prepended to SH's planning context."""
    sourcetypes = sorted(manifest.get("source_types", {}))
    all_sources = manifest.get("sources") or []
    sources     = all_sources[:top_n]

    lines = [
        "=== DATASET: what index=botsv3 actually contains ===",
        "",
        "Data is addressed on TWO axes. A sourcetype can hide many distinct feeds:",
        'sourcetype=syslog contains Cisco NVM flow data reachable only as',
        'source="cisconvmflowdata". If no sourcetype name matches what the question',
        "describes, that does NOT mean the data is absent - look along the source axis.",
        "",
        f"SOURCETYPES ({len(sourcetypes)}):",
        "  " + ", ".join(sourcetypes),
        "",
        f"TOP {len(sources)} SOURCES of {len(all_sources)}, busiest first "
        "(source | sourcetype | events):",
    ]
    for row in sources:
        lines.append(f"  {row.get('source', '')} | {row.get('sourcetype', '')} "
                     f"| {row.get('count', 0):,}")
    if len(all_sources) > len(sources):
        lines.append(f"  ... and {len(all_sources) - len(sources)} lower-volume "
                     "sources not listed. If none of the above fits the question, "
                     "spawn an exploration worker rather than guessing.")
    return "\n".join(lines)


def render_plan_text(plan: "Plan") -> str:
    """One-line-per-spawn rendering of a plan, for the log and for the persistent
    message thread.

    Cross-question memory is a list of messages, and a pydantic object is not a
    message - so the structured plan has to re-enter the thread as text. This is
    that text: everything a later planner turn needs to recall what was tried,
    including the search space and the confidence behind each spawn.
    """
    head = [f"Goal: {plan.goal}", f"EXPECTED SHAPE: {plan.expected_shape}"]
    if plan.direct_answer:
        head.append(f"DIRECT ANSWER: {plan.direct_answer}")
    rows = [
        f"{i}. [{sp.spawn_type} conf={sp.confidence}] {sp.subquestion}"
        f"  <- st={sp.sourcetypes or '-'} src={sp.sources or '-'}"
        + (f"  deps={sp.deps}" if sp.deps else "")
        for i, sp in enumerate(plan.spawns, start=1)
    ]
    return "\n".join(head + rows)


# ── plan -> executor tasks ────────────────────────────────────────────────────

def spawn_to_task(spawn: Spawn, idx: int) -> dict:
    """One executor task dict. Numbering is 1-based to match the $N the planner
    writes; to_tasks filters deps down to real task indices."""
    return {
        "idx":          idx,
        "subquestion":  spawn.subquestion,
        "deps":         list(spawn.deps),
        "spawn_type":   spawn.spawn_type,
        "search_space": {"sourcetypes": list(spawn.sourcetypes),
                         "sources":     list(spawn.sources)},
        "prior_info":   spawn.prior_info,
        "confidence":   spawn.confidence,
    }


def to_tasks(plan: Plan) -> list[dict]:
    """Executor tasks from a validated plan, with dangling deps dropped.

    A dep on a task that does not exist (or on itself) would stall its wave
    forever, so it is discarded - the same guard parse_plan applied to a `$40`
    that was really a dollar amount."""
    tasks = [spawn_to_task(s, i) for i, s in enumerate(plan.spawns, start=1)]
    valid = {t["idx"] for t in tasks}
    for t in tasks:
        t["deps"] = [d for d in t["deps"] if d in valid and d != t["idx"]]
    return tasks


def render_scope(task: dict) -> str:
    """The search-space instruction appended to a worker's subquestion.

    Named feeds are a starting point, not a cage. A worker forbidden to look
    outside where SH guessed cannot correct SH's guess - and SH is guessing from
    a list of names, which is exactly how Q216 stayed locked to the sourcetype
    axis. So this says where to start and explicitly permits leaving.
    """
    space = task.get("search_space") or {}
    sts   = space.get("sourcetypes") or []
    srcs  = space.get("sources") or []
    parts = []
    if sts:
        parts.append("sourcetype(s): " + ", ".join(sts))
    if srcs:
        parts.append("source(s): " + ", ".join(srcs))

    out = []
    if parts:
        out.append("SEARCH SPACE — start here: " + "; ".join(parts) +
                   ". If the answer is demonstrably not in these feeds, record that "
                   "in `ruled_out` and widen the hunt rather than returning nothing.")
    if task.get("prior_info"):
        out.append("PRIOR INFO: " + task["prior_info"])
    return "\n\n".join(out)
