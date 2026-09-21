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

from collections import Counter
from typing import Literal

from premise import PremiseDraft, is_validator
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


class QuestionAnswer(BaseModel):
    """SH's answer to one open question, addressed by id.

    A bare list matched by index let SH answer question 2 twice and pass the count
    check, which is what `open_question_violations` used to do."""

    id: str = Field(description="The question id, e.g. 'q2'. Copy it exactly.")
    answer: str = Field(description="Your answer. If you cannot settle it, say what would.")


class PremiseStamp(BaseModel):
    """SH's reading of one newly-claimed verification. An annotation, not an edit."""

    id: str = Field(description="The premise id, e.g. 'p3'. Copy it exactly.")
    establishes: bool = Field(
        description="Does that quote establish THIS claim, AS WRITTEN? Read the claim's "
                    "own words before the quote: a claim that states its own limit - a "
                    "route not searched, a case not checked, a choice unresolved - is "
                    "NOT established by evidence that walks past the limit. True or "
                    "false, not a grade.")
    reason: str = Field(
        description="One or two sentences: what the quote shows, and why that does or "
                    "does not establish the claim as written.")


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
        description="Is every premise the senior's conclusion or direction rests on "
                    "backed by a result shown in the report? PASS: each has a query and "
                    "result behind it. WEAK: minor premises untested, the chain holds "
                    "without them. FAIL: the candidate or the direction depends on a "
                    "premise nobody tested. The runner CAPS this: PASS is refused while "
                    "that senior has a load-bearing UNVERIFIED premise or a stamp of "
                    "yours reads false, and a REFUTED one forces FAIL. Grade lower than "
                    "the cap whenever you mean it; you may never grade above it.")
    open_question_answers: list[QuestionAnswer] = Field(
        description="One entry per OPEN question the senior you are addressing has "
                    "asked (for ANSWER: the source senior's). Each names the question's "
                    "id and your answer. Answer from the case, the question text and "
                    "sibling reports; if you cannot, say what would settle it - that is "
                    "still an answer. Empty only when it has asked nothing.")
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
    new_premises: list[PremiseDraft] = Field(
        description="Premises YOU are adding to the ledger - the ones the chain from "
                    "the question's words to the value rests on that the senior never "
                    "filed. Before any ANSWER, trace that chain and file what is "
                    "missing, opening with a 'coverage' premise: every way the "
                    "question's key concept could show up in the data, and whether the "
                    "seniors searched each. Then a 'selection' premise: why this entity "
                    "and not another that could fit. Empty on other routes unless you "
                    "have a premise to add.")
    answer_premise_ids: list[str] = Field(
        description="ANSWER only. Every premise id the value rests on. The runner "
                    "checks each is VERIFIED, and refuses an answer resting on a "
                    "REFUTED one however little budget is left.")
    premise_stamps: list[PremiseStamp] = Field(
        description="One entry for EVERY premise a report in this wave newly claims "
                    "VERIFIED, for the senior this route addresses. You do not settle "
                    "premises; you read the senior's claim against its own quote and "
                    "record whether it holds. A turn that leaves a new verification "
                    "unstamped is rejected. Premises settled in an earlier turn are not "
                    "re-stamped. A FALSE stamp retires that senior and spawns a "
                    "validator - it is not free, and it is on the record.")
    nominate_premise_id: str = Field(
        description="Required on a turn carrying a FALSE stamp, empty otherwise: the ONE "
                    "premise an independent validator will settle. Choose from what you "
                    "stamped false or what that senior left UNVERIFIED.")
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


def premise_audit_violations(entries: list, ledger) -> list[str]:
    """An ANSWER must name the premises it rests on, and one of them must be the
    Coverage premise - every way the question's concept could show up in the data.
    A candidate can only win against candidates that were looked for."""
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        cited = [ledger.premises.get(i) for i in e.answer_premise_ids]
        missing = [i for i, p in zip(e.answer_premise_ids, cited) if p is None]
        if missing:
            out.append(f"ANSWER cites {', '.join(missing)}, which is not a premise on "
                       "this question - cite ids from the ledger, or file the premise "
                       "in new_premises first")
        found = [p for p in cited if p is not None]
        if not found:
            out.append(f"ANSWER from {e.source_senior} names no premises - trace the "
                       "chain from the question to the value and cite every premise "
                       "it rests on in answer_premise_ids")
        elif not any(p.kind == "coverage" for p in found):
            out.append(f"ANSWER from {e.source_senior} rests on no Coverage premise - "
                       "list every way the question's concept could show up in the "
                       "data and whether each was searched")
    return out


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


def ledger_violations(entries: list, ledger, state: QuestionState) -> list[str]:
    """The ANSWER gate, read off the ledger.

    Two blocks with different force:
      * a load-bearing premise still UNVERIFIED blocks while there is a remedy -
        a round left on the source senior, or a free slot for an alternative;
      * a REFUTED premise blocks FULL STOP. It is not "unsettled", it is known
        false, and an answer resting on it scores zero and poisons the case file
        for every later question. There is deliberately no escape here.
    """
    out = []
    for e in entries:
        if e.route != "ANSWER":
            continue
        cited = [ledger.premises[i] for i in e.answer_premise_ids
                 if i in ledger.premises]
        dead = [p for p in cited if p.status == "REFUTED"]
        if dead:
            out.append("ANSWER is blocked: it rests on REFUTED premise(s) - "
                       + "; ".join(f'{p.id} "{p.text[:80]}"' for p in dead)
                       + ". A refuted premise is not unsettled, it is false: this "
                       "value cannot be answered from. RETIRE and work a direction "
                       "that does not need it.")
        # A validator's refutation is not escaped by no longer citing the premise.
        # Q216 v1.4.3 r1: v1 refuted SH's coverage premise p1, SH filed p6 - a fresh
        # coverage premise, self-verified on the ANSWER turn, where no wave follows and
        # so no validator ever saw it - cited p6 instead of p1, and answered. Each move
        # was legal; the combination put a known-broken chain on the scoreboard.
        overruled = [p for p in ledger.premises.values()
                     if p.load_bearing and p.status == "REFUTED" and is_validator(p.verified_by)]
        for p in overruled:
            replaced = any(q.kind == p.kind and q.status == "VERIFIED"
                           and is_validator(q.verified_by)
                           for q in ledger.premises.values())
            if not replaced:
                out.append(
                    f'ANSWER is blocked: an independent validator REFUTED {p.id} '
                    f'"{p.text[:80]}", which was filed load-bearing. Not citing it does '
                    "not answer it. Either work the gap the validator found, or file a "
                    f"replacement {p.kind} premise and let it be validated - one you "
                    "verify yourself does not clear this.")
        open_ = [p for p in cited if p.load_bearing and p.status == "UNVERIFIED"]
        fix = unsure_remedy(state, e.source_senior) if open_ else ""
        if fix:
            out.append(f"ANSWER is blocked: {len(open_)} load-bearing premise(s) it "
                       f"rests on are still UNVERIFIED - {fix}: "
                       + " | ".join(f'{p.id} "{p.text[:80]}"' for p in open_))
    return out


def open_question_violations(entries: list[SeniorDirective], ledger) -> list[str]:
    """SH answers every OPEN question, by id. The entry that owes the answers is the
    route addressed to that senior, or the ANSWER built on its report."""
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        if not sid:
            continue
        owed = {q.id for q in ledger.open_questions_for(sid)}
        got = {a.id for a in e.open_question_answers if a.answer.strip()}
        missing = sorted(owed - got)
        if missing:
            out.append(f"{sid} is waiting on {', '.join(missing)} - answer each by id "
                       "in open_question_answers")
    return out


def stamp_violations(entries: list, ledger) -> list[str]:
    """Every verification a senior newly claims is read by SH, once, the turn it is
    claimed.

    What this replaces: across three runs and six seniors, R4 flipped to PASS on the
    turn SH stopped investigating, without exception. One word about a whole report is
    easy to wave through. The bet is that a specific per-premise question - does this
    quote establish this claim as written - asked one round before the answering turn
    is materially harder.

    The turn is judged as a whole, so SH may stamp in one entry and route in another.
    """
    out, stamped = [], set()
    for e in entries:
        for s in e.premise_stamps:
            p = ledger.premises.get(s.id)
            if p is None:
                out.append(f"stamp names {s.id}, which is not a premise on this question")
            elif p.stamp:
                out.append(f"{s.id} was stamped in an earlier turn - a stamp is recorded "
                           "once, when the verification is first claimed")
            elif not s.reason.strip():
                out.append(f"stamp on {s.id} gives no reason - say what the quote shows, "
                           "and why that does or does not establish the claim as written")
            else:
                stamped.add(s.id)
    addressed = {(e.source_senior if e.route == "ANSWER" else e.senior_id)
                 for e in entries}
    for sid in sorted(a for a in addressed if a):
        missing = sorted((p.id for p in ledger.unstamped(sid) if p.id not in stamped),
                         key=lambda i: int(i[1:]))
        if missing:
            out.append(
                f"{sid} newly claims {', '.join(missing)} VERIFIED and you have not read "
                "them - one `premise_stamps` entry each: does that quote establish that "
                "claim as written, and why")
    return out


def nomination_violations(entries: list, ledger) -> list[str]:
    """A false stamp fires the mechanism, and the mechanism needs an aim.

    The nomination is drawn from premises SH stamped false, or premises that senior
    left UNVERIFIED. It may not range wider: the false stamp is what fired this, so
    letting SH aim the validator elsewhere would retire the senior and leave the
    triggering doubt unexamined.
    """
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        false_here = [s.id for s in e.premise_stamps if s.establishes is False]
        pid = e.nominate_premise_id.strip()
        if not false_here:
            if pid:
                out.append("nominate_premise_id is set with no false stamp on this turn "
                           "- a validator is spawned by a false stamp and by nothing else")
            continue
        allowed = {p.id for p in ledger.nominatable(sid)} | set(false_here)
        if not pid:
            out.append(
                f"you stamped {', '.join(false_here)} false, so {sid} is retired and one "
                "independent validator is spawned - name the ONE premise it should "
                f"settle in nominate_premise_id (from {', '.join(sorted(allowed))})")
        elif pid not in allowed:
            out.append(
                f"nominate_premise_id {pid} is neither a premise you stamped false nor "
                f"one {sid} left open - choose from {', '.join(sorted(allowed))}")
    return out


def r4_ceiling(sid: str, entry, ledger) -> str:
    """The highest R4 SH may write for this senior: FAIL, WEAK or PASS.

    R4 was a permission slip. Across three runs and six seniors it flipped to PASS on
    the turn SH stopped investigating, without exception, and `premise.py` predicted
    that in prose a version earlier. PASS is a claim about the ground the senior stands
    on, and the runner holds the facts that decide it; the grade now records rather than
    triggers.

    This turn's stamps count, not only the ledger's: SH cannot stamp a verification
    false and grade the same senior's ground sound in the same breath.
    """
    if any(p.load_bearing and p.status == "REFUTED"
           for p in ledger.premises.values()
           if p.author == sid or p.verified_by == sid):
        return "FAIL"
    if any(s.establishes is False for s in entry.premise_stamps):
        return "WEAK"
    if any(p.load_bearing and p.status == "UNVERIFIED"
           for p in ledger.premises.values() if p.author == sid):
        return "WEAK"
    if ledger.false_stamped(sid):
        return "WEAK"
    return "PASS"


def grade_ceiling_violations(entries: list, ledger) -> list[str]:
    """SH may always grade lower than the ceiling, never above it."""
    rank = {"FAIL": 0, "WEAK": 1, "PASS": 2}
    out = []
    for e in entries:
        sid = e.source_senior if e.route == "ANSWER" else e.senior_id
        if not sid or e.r4_premise_verification == NA:
            continue
        cap = r4_ceiling(sid, e, ledger)
        if rank.get(e.r4_premise_verification, 2) > rank[cap]:
            why = ("a load-bearing premise of its is REFUTED" if cap == "FAIL" else
                   "it has a load-bearing premise still UNVERIFIED, or you stamped one "
                   "of its verifications false")
            out.append(f"{sid}: R4 cannot be {e.r4_premise_verification} - {why}. "
                       f"The most you may write is {cap}; lower is always yours.")
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
        if e.route == "ANSWER" and state.last_round_capped(e.source_senior):
            out.append(f"ANSWER is blocked: {e.source_senior}'s last round was cut off "
                       "at the iteration cap — CLARIFY it (costs no round; its reply "
                       "clears this block) or COMMAND one more round before answering "
                       "from it")
    return out
