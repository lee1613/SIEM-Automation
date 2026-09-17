#!/usr/bin/env python3
"""
The SH <-> Senior data contract for v1.3.1 (spec §3.2, §3.4).

SH emits one route per senior per wave as strict structured output. The six
routes share ONE flat model rather than a discriminated union, for the same
reason `plan_schema.py` expresses absence as an empty string: OpenAI's
`strict=True` json_schema has no optional fields, so every field is always
present and a route's required payload is enforced by a validator instead.

That still gives the two failures the design depends on:
  * a CRITIC with no `flaw` fails the call (it is not a legally-empty field);
  * `decision: "critic"` is not in COMMAND's Literal — CRITIC is its own route.

`basis` is a closed enum with no `other` bucket, deliberately: SH has no Splunk
access, so every permitted basis is checkable against something SH actually
holds. A doubt that fits none of the five is a CLARIFY, not a critic.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator
from question_state import MAX_EXPLORATIONS, QuestionState

GRADES = ("PASS", "WEAK", "FAIL")
NA = "NA"

BASES = (
    "internal_contradiction",        # the report undercuts its own conclusion
    "conflicts_case_file",           # a verified case-file finding says otherwise
    "conflicts_other_senior",        # a sibling report this question says otherwise
    "shape_mismatch",                # wrong units / granularity / format
    "violates_question_constraint",  # e.g. "using Splunk commands only"
)

ROUTES = ("SPAWN", "RETIRE", "COMMAND", "CRITIC", "CLARIFY", "ANSWER")
TECHNIQUES = ("hunter", "content", "metrics")


class Scope(BaseModel):
    """A domain constraint. Empty lists mean 'unset' — strict schemas have no null."""

    sourcetypes: list[str] = Field(description="Sourcetypes this scope covers. Empty if unset.")
    sources: list[str] = Field(description="Sources this scope covers. Empty if unset.")
    fields: list[str] = Field(description="Fields that matter in this scope. Empty if unset.")

    def is_empty(self) -> bool:
        return not (self.sourcetypes or self.sources or self.fields)


class SeniorDirective(BaseModel):
    """One graded route aimed at one senior (or, for SPAWN/ANSWER, at the question)."""

    senior_id: str = Field(description="The senior this route addresses. Empty for SPAWN and ANSWER.")
    r1_scope_alignment: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Did the senior work inside its constraints and address THIS problem "
                    "statement? 'NA' only for SPAWN or an exploration worker.")
    r2_progress: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Did this round produce information the prior rounds did not have?")
    r3_answer_readiness: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Is there a candidate in submittable shape, or prose / a hedge / nothing?")
    route: Literal["SPAWN", "RETIRE", "COMMAND", "CRITIC", "CLARIFY", "ANSWER"] = Field(
        description="Exactly one route for this senior this wave.")

    # COMMAND
    decision: Literal["continue", "retry", ""] = Field(
        description="COMMAND only. 'continue': direction is right, go further. "
                    "'retry': the approach was wrong, same question, different angle.")
    rationale: str = Field(description="COMMAND only. 1-2 sentences from the CASE's perspective.")
    directive: str = Field(
        description="COMMAND only. States a GOAL — what must be established, and where to "
                    "look. Never SPL: you do not write queries.")

    # CRITIC
    basis: Literal["internal_contradiction", "conflicts_case_file", "conflicts_other_senior",
                   "shape_mismatch", "violates_question_constraint", ""] = Field(
        description="CRITIC only. What you are checking the report against. There is no "
                    "'other' — a doubt that fits none of these is a CLARIFY.")
    flaw: str = Field(description="CRITIC only. What is wrong, one or two sentences.")
    why_it_fails: str = Field(description="CRITIC only. How the basis demonstrates the flaw.")
    fix_directive: str = Field(
        description="CRITIC only. What to establish first, and what follows depending on what "
                    "that turns up. Do not write the query. One honest step beats an invented branch.")

    scope_change: Scope = Field(
        description="COMMAND/CRITIC. A new domain constraint for this senior, or all-empty "
                    "lists for no change. This is the one lever that is yours alone.")

    # CLARIFY
    clarify_reason: Literal["unclear", "suspect", ""] = Field(
        description="CLARIFY only. 'unclear': the report did not parse as an argument. "
                    "'suspect': you doubt the discovery.")
    questions: list[str] = Field(
        description="CLARIFY only. 1-3 questions answerable from what the senior ALREADY "
                    "holds — no tools, no new searches. 'Go find out' is a COMMAND.")

    # SPAWN
    constraints: Scope = Field(description="SPAWN only. The domain this new senior owns.")
    technique: Literal["hunter", "content", "metrics", ""] = Field(
        description="SPAWN of a senior. hunter: enumerate the population before filtering. "
                    "content: read raw events first. metrics: compute every number in SPL.")
    spawn_type: Literal["senior", "exploration", ""] = Field(
        description="SPAWN only. 'exploration' is the one-shot scout for when you cannot name "
                    "a scope at all; it costs no senior slot and is capped at one per question.")
    subquestion: str = Field(description="SPAWN only. The self-contained problem statement.")
    reason: str = Field(
        description="SPAWN: why the current seniors' constraints cannot cover this. "
                    "RETIRE: why this senior is done.")

    # ANSWER
    value: str = Field(description="ANSWER only. The bare value, exactly as the scoreboard wants it.")
    value_kind: str = Field(description="ANSWER only. What the value is — count, hostname, ip, cve...")
    source_senior: str = Field(description="ANSWER only. The senior whose report the value came from.")
    justification: str = Field(description="ANSWER only. Why that report establishes this value.")
    case_updates: list[str] = Field(
        description="ANSWER only. Durable incident facts for the case file, each in the form "
                    "'entity <type> <value>' or 'finding [verified|hypothesis] <claim> | evidence: <spl>'.")

    # Enforces only the fields whose absence would change routing or leave the
    # entry unactionable: `senior_id` for every route aimed at an existing senior
    # (COMMAND/CRITIC/CLARIFY/RETIRE); COMMAND's `decision`/`directive`; CRITIC's `basis`/
    # `flaw`/`why_it_fails`/`fix_directive`; CLARIFY's `clarify_reason`/
    # `questions`; SPAWN's `spawn_type`/`subquestion`/(senior) `technique`;
    # RETIRE's `reason`; ANSWER's `value`/`source_senior`. `rationale`, SPAWN's
    # `reason`, `value_kind`, `justification` and SPAWN's `constraints` are
    # deliberately left advisory — an unscoped or unexplained spawn is a bad
    # turn, not a malformed one, and it's the orchestrator's prompt, not this
    # validator, that has to push SH toward supplying them.
    @model_validator(mode="after")
    def _payload_matches_route(self):
        r = self.route
        if r in ("COMMAND", "CRITIC", "CLARIFY", "RETIRE") and not self.senior_id.strip():
            raise ValueError(f"{r} must name a senior_id")
        if r == "COMMAND":
            if self.decision not in ("continue", "retry"):
                raise ValueError("COMMAND decision must be 'continue' or 'retry'")
            if not self.directive.strip():
                raise ValueError("COMMAND needs a directive")
        elif r == "CRITIC":
            if self.basis not in BASES:
                raise ValueError(f"CRITIC basis must be one of {BASES}")
            for name in ("flaw", "why_it_fails", "fix_directive"):
                if not getattr(self, name).strip():
                    raise ValueError(f"CRITIC needs {name}")
        elif r == "CLARIFY":
            if self.clarify_reason not in ("unclear", "suspect"):
                raise ValueError("CLARIFY reason must be 'unclear' or 'suspect'")
            asked = [q for q in self.questions if q.strip()]
            if not 1 <= len(asked) <= 3:
                raise ValueError("CLARIFY needs 1-3 questions")
        elif r == "SPAWN":
            if self.spawn_type not in ("senior", "exploration"):
                raise ValueError("SPAWN needs spawn_type 'senior' or 'exploration'")
            if not self.subquestion.strip():
                raise ValueError("SPAWN needs a subquestion")
            if self.spawn_type == "senior" and self.technique not in TECHNIQUES:
                raise ValueError(f"a senior SPAWN needs a technique from {TECHNIQUES}")
        elif r == "RETIRE":
            if not self.reason.strip():
                raise ValueError("RETIRE needs a reason")
        elif r == "ANSWER":
            if not self.value.strip():
                raise ValueError("ANSWER needs a value")
            if not self.source_senior.strip():
                raise ValueError("ANSWER needs a source_senior")
        return self


class SHTurn(BaseModel):
    """One SH turn: a short reading of the case, then one route per senior addressed."""

    reading: str = Field(description="1-2 sentences on where this question now stands.")
    entries: list[SeniorDirective] = Field(
        description="One entry per senior you are addressing this wave, plus any SPAWN, "
                    "or a single ANSWER when the question is done.")


# ── grade rules (§3.4) ────────────────────────────────────────────────────────

def effective_r2(sh_grade: str, novel_spl_count: int) -> str:
    """R2 has two independent FAIL sources and the code one wins.

    `novel_spl_count == 0` is literal repetition and needs no judgement to
    detect, so SH cannot grade it PASS. SH may still FAIL a round whose queries
    were new but which learned nothing — code cannot see novel-but-useless.
    """
    if novel_spl_count == 0:
        return "FAIL"
    return sh_grade


def answer_blocked(entry: SeniorDirective) -> bool:
    """The wrong-question gate: a value can be real, grounded and well-formed and
    still answer something adjacent to what was asked."""
    return entry.route == "ANSWER" and entry.r1_scope_alignment == "FAIL"


def grade_violations(entries: list[SeniorDirective], *, graded: set, exploration: set) -> list[str]:
    """Grades must be emitted for every senior whose report was read, and never
    for an exploration worker (which structurally cannot produce a value)."""
    out = []
    for e in entries:
        got = (e.r1_scope_alignment, e.r2_progress, e.r3_answer_readiness)
        if e.senior_id in exploration:
            if any(g != NA for g in got):
                out.append(f"{e.senior_id}: exploration workers are not graded")
            continue
        needs_grades = (e.route == "ANSWER") or (e.senior_id in graded)
        if needs_grades and any(g not in GRADES for g in got):
            out.append(f"{e.senior_id or e.route}: all three grades required (PASS/WEAK/FAIL)")
    return out


def directive_violations(entries: list[SeniorDirective], state: QuestionState) -> list[str]:
    """Turn-level checks against the question's budget and gate history.

    Rejected back into another SH turn rather than silently dropped — a COMMAND
    to a senior with no rounds left would otherwise look issued and never run.
    """
    out = []
    senior_spawns = sum(1 for e in entries
                        if e.route == "SPAWN" and e.spawn_type == "senior")
    explore_spawns = sum(1 for e in entries
                         if e.route == "SPAWN" and e.spawn_type == "exploration")
    if senior_spawns > (state.budget["seniors"] - state.spawns_used):
        out.append(f"only {state.budget['seniors'] - state.spawns_used} senior slot(s) left")
    if explore_spawns > (MAX_EXPLORATIONS - state.explorations_used):
        out.append("exploration already used on this question")

    for e in entries:
        if e.route in ("COMMAND", "CRITIC"):
            if not state.is_active(e.senior_id):
                out.append(f"{e.senior_id} is not an active senior")
            elif state.rounds_left_for(e.senior_id) <= 0:
                out.append(f"{e.senior_id} has no rounds left — RETIRE or ANSWER")
        if e.route == "COMMAND" and e.decision == "continue" \
                and state.continue_blocked(e.senior_id):
            out.append(f"{e.senior_id} has two consecutive R2 FAILs — "
                       "RETIRE it or change its scope, do not continue")
        if answer_blocked(e):
            out.append("ANSWER is blocked: the source report is graded R1 = FAIL")
    return out
