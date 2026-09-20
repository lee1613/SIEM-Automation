#!/usr/bin/env python3
"""
The SH <-> Senior data contract for v1.4 (spec §3.2, §3.4).

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

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from question_state import MAX_EXPLORATIONS, QuestionState
from senior_report import open_doubts  # noqa: F401  (re-exported for tests)

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
# hunter/content were pruned on 2026-09-18 smoke evidence: SH's per-round directives
# already carry both rules. metrics stays — SH cannot enforce it mid-round.
TECHNIQUES = ("metrics",)


class Scope(BaseModel):
    """A domain constraint. Empty lists mean 'unset' — strict schemas have no null."""

    sourcetypes: list[str] = Field(description="Sourcetypes this scope covers. Empty if unset.")
    sources: list[str] = Field(description="Sources this scope covers. Empty if unset.")
    fields: list[str] = Field(description="Fields that matter in this scope. Empty if unset.")

    def is_empty(self) -> bool:
        return not (self.sourcetypes or self.sources or self.fields)


class AuditLine(BaseModel):
    """One premise of SH's pre-ANSWER audit. Structured so code can read the verdict:
    as free text, "could change the answer" was prose no gate could rely on."""

    premise: str = Field(description="The premise the answer rests on. The first line's "
                                     "premise starts with 'Coverage'.")
    status: Literal["VERIFIED", "UNVERIFIED"] = Field(
        description="VERIFIED only when a result in a report, read in full, shows it.")
    source: str = Field(description="VERIFIED: which senior report holds the evidence, "
                                    "e.g. 's1 round 2'. UNVERIFIED: empty.")
    quote: str = Field(description="VERIFIED: the senior's query, result or finding that "
                                   "shows it, copied WORD FOR WORD from that report (the "
                                   "runner checks it is there). UNVERIFIED: empty.")
    evidence: str = Field(description="VERIFIED: why that quote establishes the premise. "
                                      "UNVERIFIED: what would test it.")

    def render(self) -> str:
        cite = f" [{self.source}: \"{self.quote}\"]" if self.quote else ""
        return (f"{self.premise} - {self.status}" + cite
                + (f": {self.evidence}" if self.evidence else ""))


def _norm(text: str) -> str:
    """Whitespace-, case- and markdown-insensitive form, so a faithful quote matches."""
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", text or "")).strip().lower()


MIN_QUOTE_CHARS = 12   # shorter than this, a "quote" matches almost any report


_AUDIT_TEXT = re.compile(r"^(.*?)\s*(?:-|\u2013|\u2014)\s*(UNVERIFIED|VERIFIED)(?![A-Z])\s*:?\s*(.*)$", re.S)


class SeniorDirective(BaseModel):
    """One graded route aimed at one senior (or, for SPAWN/ANSWER, at the question)."""

    senior_id: str = Field(description="The senior this route addresses. Empty for SPAWN and ANSWER.")
    r1_scope_alignment: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Did this round contribute anything toward identifying an entity the "
                    "answer depends on — a host, account, process, file, feed or field? "
                    "PASS: it did, even if the value itself is still missing and even if "
                    "the finding came from a different angle than the one you set. WEAK: "
                    "it worked the problem but established nothing new. FAIL: it answered "
                    "a different question, or its work cannot bear on this one at all. "
                    "'NA' only for SPAWN or an exploration worker.")
    r2_progress: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Did this round produce information the prior rounds did not have?")
    r3_answer_readiness: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Is there a candidate in submittable shape, or prose / a hedge / nothing?")
    r4_premise_verification: Literal["PASS", "WEAK", "FAIL", "NA"] = Field(
        description="Is every premise the senior's conclusion or direction rests on backed by "
                    "a result shown in the report? PASS: each has a query and result behind "
                    "it. WEAK: minor premises untested, the chain holds without them. FAIL: "
                    "the candidate or the direction depends on a premise nobody tested. A "
                    "WEAK/FAIL tells the senior to verify first; the ANSWER gate is the "
                    "premise audit, not this grade.")
    open_question_answers: list[str] = Field(
        description="Your answer to each bullet in the '## Open questions for SH' section of "
                    "the report this entry addresses (for ANSWER: the source senior's report), "
                    "in order, one per question. Answer from the case, the question text and "
                    "sibling reports; if you cannot, say what would settle it. Empty only when "
                    "that report asked nothing, and for SPAWN.")
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
    technique: Literal["metrics", ""] = Field(
        description="SPAWN of a senior. 'metrics' when the answer is a number that must be "
                    "computed in SPL (every number via eval/stats, never by hand). Otherwise "
                    "empty: a plain senior, whose approach you set in the subquestion and your "
                    "directives.")
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
    premise_audit: list[AuditLine] = Field(
        description="ANSWER only. Your own audit before answering: trace the chain from the "
                    "question's words to the value and list every premise it rests on that the "
                    "source report's Assumptions do NOT list. Open with a 'Coverage' premise: "
                    "every way the question's key concept could show up in the data and whether "
                    "the seniors searched each. Then above all, why this entity and not another "
                    "that could fit the question. An ANSWER with any UNVERIFIED line is rejected "
                    "while its source senior has rounds left. Empty for every other route.")
    case_updates: list[str] = Field(
        description="ANSWER only. Durable incident facts for the case file, each in the form "
                    "'entity <type> <value>' or 'finding [verified|hypothesis] <claim> | evidence: <spl>'.")

    # Enforces only the fields whose absence would change routing or leave the
    # entry unactionable: `senior_id` for every route aimed at an existing senior
    # (COMMAND/CRITIC/CLARIFY/RETIRE); COMMAND's `decision`/`directive`; CRITIC's `basis`/
    # `flaw`/`why_it_fails`/`fix_directive`; CLARIFY's `clarify_reason`/
    # `questions`; SPAWN's `spawn_type`/`subquestion`;
    # RETIRE's `reason`; ANSWER's `value`/`source_senior`. `rationale`, SPAWN's
    # `reason`, `value_kind`, `justification` and SPAWN's `constraints` are
    # deliberately left advisory — an unscoped or unexplained spawn is a bad
    # turn, not a malformed one, and it's the orchestrator's prompt, not this
    # validator, that has to push SH toward supplying them.
    @field_validator("premise_audit", mode="before")
    @classmethod
    def _audit_from_text(cls, v):
        """Accept the legacy '<premise> - VERIFIED: <where>' strings. A line with no
        verdict reads as UNVERIFIED: an unmarked premise is an untested one."""
        out = []
        for a in v or []:
            if isinstance(a, str):
                if not a.strip():
                    continue
                m = _AUDIT_TEXT.match(a.strip())
                a = ({"premise": m.group(1), "status": m.group(2), "source": "",
                      "quote": m.group(3), "evidence": m.group(3)} if m
                     else {"premise": a.strip(), "status": "UNVERIFIED", "source": "",
                           "quote": "", "evidence": ""})
            out.append(a)
        return out

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


def spawn_overlap_violations(entries: list[SeniorDirective], active: dict) -> list[str]:
    """Parallel seniors must own disjoint scopes (v1.4.1). `active` maps each
    active senior to the constraints it was spawned with. Once two or more seniors
    would be live, every one needs its own sourcetypes/sources and no two may
    share one — overlapping seniors only duplicate each other's work. A lone
    senior may still be spawned unscoped. Exploration scouts are not checked.

    ponytail: compares spawn-time constraints; a later COMMAND scope_change is not
    tracked here. Track per-senior scope on the session if that ever matters."""
    # An ANSWER ends the question and later entries are ignored (M7), so a spawn
    # riding along with it never runs — rejecting the turn for it only burns a turn.
    if any(e.route == "ANSWER" for e in entries):
        return []
    spawns = [e for e in entries if e.route == "SPAWN" and e.spawn_type == "senior"]
    # RETIRE s2 + SPAWN a replacement in one turn is a hand-over, not a parallel run
    # (Q217 smoke5_r1: rejecting it left SH retiring s2 alone, ten times over).
    retiring = {e.senior_id for e in entries if e.route == "RETIRE"}
    active = {sid: sc for sid, sc in active.items() if sid not in retiring}
    scopes = list(active.items()) + [(f"new SPAWN #{i}", e.constraints)
                                     for i, e in enumerate(spawns, start=1)]
    if not spawns or len(scopes) < 2:
        return []

    def keys(sc) -> set:
        if sc is None:
            return set()
        return ({("sourcetype", x.lower()) for x in sc.sourcetypes}
                | {("source", x.lower()) for x in sc.sources})

    out = []
    for i in range(len(active), len(scopes)):
        name, mine = scopes[i][0], keys(scopes[i][1])
        if not mine:
            out.append(f"{name}: a senior running beside another needs its own "
                       "sourcetype/source constraints")
            continue
        for other, sc in scopes[:i]:
            theirs = keys(sc)
            if not theirs:
                out.append(f"{name}: {other} has no constraints, so overlap cannot be "
                           "ruled out — scope or retire it before running a parallel senior")
            elif mine & theirs:
                shared = ", ".join(sorted(v for _, v in mine & theirs))
                out.append(f"{name} overlaps {other} on {shared} — a parallel senior "
                           "must own a scope no other active senior touches")
    return out


def premise_audit_violations(entries: list) -> list[str]:
    """An ANSWER must carry SH's own premise audit (`premise_audit`): the premises the
    chain rests on that the senior never listed. Soft on content — an UNVERIFIED line
    is allowed, like R4 — but an ANSWER with no audit at all is rejected."""
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        if not e.premise_audit:
            out.append(f"ANSWER from {e.source_senior} has no premise_audit — trace the chain "
                       "from the question to the value and list the premises the report did not")
        elif not any(a.premise.strip().lstrip("-* ").lower().startswith("coverage")
                     for a in e.premise_audit):
            out.append(f"ANSWER from {e.source_senior}: premise_audit has no Coverage line — "
                       "list every way the question's concept could show up in the data and "
                       "whether each was searched")
    return out


def unverified_audit(entry) -> list[str]:
    """The audit lines SH itself marked UNVERIFIED."""
    return [a.render() for a in entry.premise_audit if a.status == "UNVERIFIED"]


def unsure_remedy(state: QuestionState, src: str) -> str:
    """What SH must do instead of answering on unsettled ground; '' when nothing is
    left to try. A senior still holding rounds may be told to verify, but a senior
    that keeps circling one narrowed lead is better replaced than pushed again — so
    a free slot is always offered. Once the source senior is spent, a free slot is
    the only way forward (Q216 smoke5_r1: s1 spent 8 rounds on one lead and SH
    answered it UNVERIFIED with two senior slots unused)."""
    alt = ("RETIRE it if it is circling the same lead and SPAWN an alternative senior "
           "on a different area, constrained to where it may have overlooked")
    if state.rounds_left_for(src) > 0:
        return (f"COMMAND {src} to settle them, or {alt}" if state.can_spawn_senior()
                else f"COMMAND {src} to settle them")
    if state.can_spawn_senior():
        return (f"{src} has no rounds left and a senior slot is free — "
                f"SPAWN an alternative senior on a different area, constrained to where "
                f"{src} may have overlooked")
    return ""


# A quote that cites SH is SH's own claim coming back as evidence. v1.4.2 Q216:
# SH told s1 the attribution was settled, s1 wrote "established by SH outside this
# feed", and SH quoted that sentence as the evidence for its VERIFIED line.
_CIRCULAR = re.compile(r"\b(established|confirmed|settled|told|instructed)\b"
                       r"[^.]{0,60}\bSH\b|\bper SH\b|\bSH (?:said|states?|instruction)",
                       re.IGNORECASE)


def evidence_violations(entries: list, *, reports_of, doubts_of,
                        state: QuestionState) -> list[str]:
    """Checks an ANSWER against the senior's own words, which SH cannot relabel.

    * Every VERIFIED audit line must quote, word for word, a senior's query, result
      or finding that shows it. The quote is checked against the source senior's
      reports first and then against every senior's, because a premise established
      by a sibling is still evidence. A VERIFIED with nothing behind it is SH's
      opinion, not evidence. `reports_of(None)` must return every senior's text.
    * The source senior must have no OPEN doubt left (`doubts_of` carries every
      unsettled premise forward across its rounds, so one cannot be dropped by
      writing a cleaner report next round — see senior_report.carry_doubts).
    * A VERIFIED line may not cite SH itself: an orchestrator's instruction is not
      evidence, however faithfully the senior wrote it down.
    """
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        src = e.source_senior
        text = _norm(reports_of(src))
        for a in e.premise_audit:
            if a.status != "VERIFIED":
                continue
            q = _norm(a.quote)
            # Any senior's report may hold the quote: an answer built on s2 routinely
            # rests on a premise s1 established, and SH names the real source in
            # `a.source` (v1.4.2 Q216 was blocked three turns for quoting s1 under s2).
            if _CIRCULAR.search(a.quote or ""):
                out.append(f"audit line '{a.premise[:80]}' quotes SH as the authority — "
                           "your own instruction is not evidence. Quote the senior's query "
                           "or result that shows it, or mark the line UNVERIFIED")
            elif len(q) < MIN_QUOTE_CHARS or (q not in text and q not in _norm(reports_of(None))):
                out.append(f"audit line '{a.premise[:80]}' is VERIFIED but its quote is in "
                           "no senior's report — copy the query, result or finding that "
                           "shows it word for word, or mark the line UNVERIFIED")
        doubts = doubts_of(src)
        fix = unsure_remedy(state, src) if doubts else ""
        if fix:
            out.append(f"ANSWER is blocked: {src}'s latest report still flags "
                       f"{len(doubts)} unsettled premise(s) in its own Assumptions — {fix}: "
                       + " | ".join(d[:160] for d in doubts))
    return out


def open_question_violations(entries: list[SeniorDirective], asked: dict) -> list[str]:
    """SH answers every open question a senior put to it. `asked` maps each senior
    whose report was just read to how many questions it asked (see
    senior_report.open_questions). The entry that owes the answers is the route
    addressed to that senior, or the ANSWER built on its report."""
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        need = asked.get(sid, 0)
        got = sum(1 for a in e.open_question_answers if a.strip())
        if need and got < need:
            out.append(f"{sid} asked {need} open question(s) and you answered {got} — "
                       f"answer each one, in order, in open_question_answers")
    return out


def grade_violations(entries: list[SeniorDirective], *, graded: set, exploration: set) -> list[str]:
    """Grades must be emitted for every senior whose report was read, and never
    for an exploration worker (which structurally cannot produce a value)."""
    out = []
    for e in entries:
        got = (e.r1_scope_alignment, e.r2_progress, e.r3_answer_readiness,
               e.r4_premise_verification)
        if e.senior_id in exploration:
            if any(g != NA for g in got):
                out.append(f"{e.senior_id}: exploration workers are not graded")
            continue
        needs_grades = (e.route == "ANSWER") or (e.senior_id in graded)
        if needs_grades and any(g not in GRADES for g in got):
            out.append(f"{e.senior_id or e.route}: all four grades required (PASS/WEAK/FAIL)")
    # An ANSWER ends the question and the sweep retires every survivor, so
    # rejecting it for an unrouted sibling would only burn a turn.
    if any(e.route == "ANSWER" for e in entries):
        return out
    addressed = {e.senior_id for e in entries}
    for sid in sorted(graded - exploration - addressed):
        out.append(f"{sid}: its report was read but no route addressed it — "
                   "grade it and give it exactly one route")
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
    if senior_spawns > state.slots_remaining:
        out.append(f"no free senior slot for this SPAWN — only {state.slots_remaining} "
                   f"of {state.budget['seniors']} left")
    if senior_spawns and state.turns_remaining < 1:
        out.append("no SH turn left to read a new senior's report — do not SPAWN")
    if explore_spawns > (MAX_EXPLORATIONS - state.explorations_used):
        out.append("exploration already used on this question")

    targets = Counter(e.senior_id for e in entries if e.route != "SPAWN" and e.senior_id)
    for sid, n in sorted(targets.items()):
        if n > 1:
            out.append(f"{sid} got more than one route this turn — exactly one per senior")

    for e in entries:
        if e.route == "CLARIFY" and not state.is_active(e.senior_id):
            out.append(f"{e.senior_id} is not an active senior")
        if e.route == "RETIRE" and not state.is_active(e.senior_id):
            out.append(f"{e.senior_id} is already retired or was never spawned — "
                       "do not RETIRE it again")
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
        # The cut-off gate (§3.5). A round that ran out of iterations stopped where
        # the budget ended, not where the work did: test_20260918_104111's s1 filed
        # a FOUND report carrying the runner's cap line and two unanswered questions
        # for SH, and SH graded it all-PASS and answered it verbatim — wrongly.
        # CLARIFY costs no round, so the cheap move is always available.
        if e.route == "ANSWER" and unverified_audit(e):
            fix = unsure_remedy(state, e.source_senior)
            if fix:
                out.append(f"ANSWER is blocked: your premise audit marks "
                           f"{len(unverified_audit(e))} premise(s) UNVERIFIED — {fix}: "
                           + "; ".join(unverified_audit(e)))
        if e.route == "ANSWER" and state.last_round_capped(e.source_senior):
            out.append(f"ANSWER is blocked: {e.source_senior}'s last round was cut off "
                       "at the iteration cap — CLARIFY it (costs no round; its reply "
                       "clears this block) or COMMAND one more round before answering "
                       "from it")
    return out
