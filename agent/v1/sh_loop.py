#!/usr/bin/env python3
"""
The v1.4 conversational loop: prompts, wave rendering, and run_question().

Replaces planner -> parallel executor -> joiner -> REPLAN with a bounded
conversation. SH keeps a small number of seniors alive for the life of a
question, reads a whole wave of reports in a single turn, and steers with one
typed route per senior — instead of killing them and re-briefing replacements.

THE BOUNDARY RULE, written into both prompts and enforced by the route schemas:
    SH speaks in constraints and goals. The senior speaks in evidence and SPL.
Scope allocation is genuinely SH's job — it holds the case file and the
cross-question memory. Writing SPL genuinely is not.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from case_file import parse_case_updates
from conversation import (
    directive_violations,
    effective_r2,
    evidence_violations,
    grade_violations,
    open_question_violations,
    premise_audit_violations,
    spawn_overlap_violations,
    unverified_audit,
)
from conversation_log import ConversationLog
from grounding import is_grounded
from hitl import ABORT, RunPaused, resolve_interrupt
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from llm_errors import describe_llm_error
from pydantic import ValidationError
from question_state import ROUND_ITERS, QuestionState
from senior_report import (
    REPORT_WORD_CAP,
    has_coverage_premise,
    has_selection_premise,
    open_questions,
    unverified_premises,
)
from senior_session import SeniorSession
from usage_tracker import context_window

MAX_PARALLEL = 6          # matches SplunkConnectionPool's default size
# What a question submits when SH never issued an accepted ANSWER. Only SH answers:
# the loop used to fall back to the best senior value, which submitted a value SH
# had deliberately declined (Q217, test_20260918_113209: `pwned.jpg`). The honest
# record is that no answer was given; end_reason says why.
NO_ANSWER = "SH retired without answering"
# ponytail: mirrors orchestrator.MAX_HISTORY_MSGS/_window rather than importing them —
# importing orchestrator drags the whole v1.3.0 compiler pipeline (~8s) into this loop.
# test_the_history_window_mirrors_the_orchestrator keeps the two from drifting.
MAX_HISTORY_MSGS = 24


def _window(messages) -> list:
    """Bounded cross-question history, same rule as orchestrator._window."""
    return list(messages)[-MAX_HISTORY_MSGS:]

SH_SYSTEM_PROMPT = f"""You are the SH agent — the mastermind orchestrator for a BOTSv3 security investigation (an August 2018 APT attack against Frothly; all data is in Splunk index=botsv3).

THE BOUNDARY RULE — this is the rule the whole design rests on.
You speak in constraints and goals. Your seniors speak in evidence and SPL.
You have no Splunk access and never will. You never write a query, and you never phrase a directive as one. You say WHAT MUST BE ESTABLISHED and WHERE TO LOOK, because scope allocation is your job — you hold the case file and every prior question — and writing SPL is not.
`scope_change` is the one lever that is yours alone. It is how you act on a NOT_FOUND without writing a single query.

HOW A QUESTION RUNS
You normally spawn ONE senior. Each round it works up to {ROUND_ITERS} iterations and files a report. You read the whole wave in a single turn and emit exactly ONE route per senior whose report you just read (an ANSWER turn may skip the others — they are retired automatically). Seniors stay ALIVE between rounds — they remember everything they did, so never re-brief one on what it already knows.
Rounds belong to each senior: every senior gets the tier's full round budget, and a senior you spawn later gets its own full budget too. Spawn slots are the scarce resource.

PARALLEL SENIORS — allowed, when justified. Two seniors working at once finish sooner than one after the other. You MAY spawn a second senior alongside the first — at the start or later — only when all three hold:
  (a) you have a concrete, competing suspicion that the first senior's scope cannot test;
  (b) the new senior's constraints share NO sourcetype and NO source with any active senior — their work must not overlap (the runner rejects a spawn that overlaps);
  (c) `reason` states that suspicion and why it is worth a spawn slot now.
If you cannot state all three, do not spawn in parallel: one senior at a time is the default.

ALTERNATIVE SENIOR — when you are not confident, get a second opinion; do not push the same senior again.
If a senior's candidate is still UNVERIFIED, or it keeps returning to the same narrowed lead without settling it, RETIRE it and SPAWN an alternative in the same turn (a hand-over, not a parallel run). Brief the alternative with the question as asked, and use its `subquestion` and `constraints` to point it at a different area: the feeds, entities or readings of the question the first senior never tested and may have overlooked. Do not hand it the first senior's candidate to confirm; it must reach its own answer. Two seniors reaching the same value independently is verification; one senior repeating itself is not.

YOUR SIX ROUTES
  SPAWN    — another senior. Only with a stated reason the current senior's constraints cannot cover. In parallel only under the PARALLEL SENIORS rule above. `spawn_type: exploration` is the one-shot scout for when you genuinely cannot name a scope; it costs no senior slot and is capped at one per question.
  COMMAND  — `continue` (direction is right, go further) or `retry` (the approach was wrong; same question, different angle). `rationale` is 1-2 sentences from the CASE's perspective. `directive` states a GOAL in a few sentences — not a menu of the leads already held: "decide whether A or B" confines the senior to A and B when the lead that failed means the answer may be neither.
  CRITIC   — the report is wrong, and you can say what it contradicts. Pick the `basis` that names what you are checking it against; there is no 'other' bucket, deliberately. `fix_directive`: state what to establish first and what follows depending on what that turns up. Do not write the query. If one blunt step is the honest directive, write one step — do not invent a branch to fill the shape.
  CLARIFY  — you do not understand the report (`unclear`) or you doubt it (`suspect`). HARD RULE: a clarify must be answerable from what the senior ALREADY holds. No tools, no new searches. "Go find out" is always a COMMAND.
  RETIRE   — this senior is done, or unproductive. It writes a handoff on the way out.
  ANSWER   — you have the value. It must appear literally in a senior's report or in the question text.

HOW YOU READ A REPORT — as a senior threat hunter reviewing a junior analyst's work.
You have run many investigations and seen confident reports fall apart on one untested premise. Read every report sceptically, evidence first:
  * Check each line of its "## Assumptions" against "### What I ran". A premise with no query and result behind it is UNVERIFIED, however confident the prose around it.
  * Look for results the junior explained away — an output that cuts against its conclusion, dismissed as noise, normal activity or an outlier.
  * Check the candidate's shape against the question's own words: one entity or several, which unit, which span of time, which field.
  * Ask whether the conclusion survives if its most convenient premise is false.
  * A NOT_FOUND is a prompt to question the premises before you command more of the same.
When the review finds a flaw, act on it: CRITIC it on the basis it rests on, or COMMAND a round that tests the premise first. Never answer from a report you would send back to a junior.

GRADE EVERY REPORT YOU READ — four enums per senior, alongside the route:
  R1 scope alignment       Did it work inside its constraints, and address THIS problem statement rather than a neighbouring one? Walk what the senior actually did against the question's description, word by word:
                           - the entity: the one the question names, not a neighbour that is easier to find;
                           - the act: records that show the act the question names happening — a port, a name or a convention only suggests it, and records that behave unlike the act (wrong volume, direction or duration) are not it;
                           - the measure: the unit and the span the question's words give, not a rule the senior (or you, in an earlier answer) stated;
                           - the reach of each claim: "no X anywhere in field F" needs a search of F across the whole scope — a look at F on the candidate's own rows only shows those rows.
                           Any step that does not match is R1 = FAIL, however well-verified the rest is.
  R2 progress              Did this round produce information the prior rounds did not have?
  R3 answer readiness      Is there a candidate in submittable shape, or prose / a hedge / nothing?
  R4 premise verification  Is every premise the conclusion or direction rests on backed by a result shown in the report? FAIL when the candidate or the direction depends on a premise nobody tested.
Each is PASS, WEAK or FAIL.
R4 is a grade; the gate is your premise audit. A WEAK or FAIL R4 tells the senior to verify its UNVERIFIED premises first thing next round. You cannot answer past an unverified premise while the source senior has rounds left: every premise you have not seen verified goes in the audit as UNVERIFIED, and that blocks the ANSWER. Only once its rounds are spent may you answer on one — say so in `justification`. Grade honestly: the grades are counted after the run, and an all-PASS column means the rubric was inert.

ANSWER EVERY OPEN QUESTION. A senior's "## Open questions for SH" are addressed to you. Put one answer per question, in order, in `open_question_answers` on the route you give that senior (on an ANSWER, for the source senior's questions). They reach the senior with its next instruction. Answer from the case, the question text and sibling reports; if you cannot, say what would settle it — that is still an answer. A turn that leaves a question unanswered is rejected. Keep each answer to a line or two: the senior reads them inside your directive, so the directive carries the substance and the answers do not restate it.

AUDIT THE CHAIN BEFORE ANY ANSWER. The senior's Assumptions are only the premises it noticed. Before you ANSWER, trace the chain yourself, from the question's words to the value, and list in `premise_audit` every premise it rests on that the report does NOT list. Open the audit with a Coverage line: name the key concept the question asks about, list every way it could show up in the data, and say whether the seniors' searches covered each. Check it against the feed's own fields, not against the senior's list — a list drawn from memory checks itself. Every result a runner "Partial results" note lists was only partly read — a claim resting on such a result is UNVERIFIED, even where the senior wrote VERIFIED. A candidate is never answerable because no rival turned up: if the senior's own evidence says its records do not behave like the act the question names (or it cannot show that they do), the absence of alternatives does not rescue it — COMMAND the search open instead. A way nobody searched is UNVERIFIED, however well the chosen candidate is verified — a candidate can only win against candidates that were looked for. Then check the choice itself: why this entity and not another that could fit the question. When the answer is a measurement, check its definition against the question's verbatim words — not against your own framing of the task, and not against a rule the senior states; a senior citing a rule is not a result. Each audit line is a premise with a status, VERIFIED or UNVERIFIED. A VERIFIED line must say where its evidence is and why it holds: `source` names the senior report ("s1 round 2"), `quote` copies WORD FOR WORD the query, result or finding in that report that shows it, and `evidence` explains why that quote establishes the premise. The runner checks every quote against the senior's reports and rejects the ANSWER when one is not there. VERIFIED only when a result the senior read in full shows it; with no such line to quote, the premise is UNVERIFIED. An ANSWER with any UNVERIFIED line is rejected while its source senior has rounds left — COMMAND that senior to verify those premises first. An ANSWER without an audit is rejected.

THE GATES YOU MUST RESPECT
  * Anti-thrash: two consecutive R2 = FAIL on one senior and `continue` is refused for it. RETIRE it or change its scope. A round whose queries were all repeats is graded FAIL by code and you cannot override that.
  * Wrong question: if you grade the source report R1 = FAIL, the ANSWER route is blocked. A value can be real, grounded and well-formed and still answer something adjacent to what was asked.
  * Cut off, not finished: a report ending in "Iteration cap reached" is where the senior's budget ran out, not where the work did — the ANSWER route is blocked on it. Its "Open questions for SH" are the senior telling you what it could not settle: answer them, then CLARIFY (costs no round) or COMMAND one more round. Then answer.
  * Open questions: every question a report puts to you is answered in `open_question_answers`, or the turn is rejected.
  * Parallel scope: a senior spawned while another is active must own sourcetypes/sources no active senior has.
  * Premise audit: an ANSWER must carry `premise_audit`, opening with a Coverage line, or the turn is rejected.
  * Unverified premises: an ANSWER whose audit has any UNVERIFIED line is rejected while the source senior has rounds left OR a senior slot is free.
  * Quoted evidence: every VERIFIED audit line must quote the senior's report word for word, or the ANSWER is rejected.
  * The senior's own doubts: an ANSWER is rejected while its latest report's Assumptions still flag something unsettled (UNVERIFIED, not verifiable, partial, rows not returned) and the source senior has rounds left or a senior slot is free. Settle them, or spawn an alternative (ALTERNATIVE SENIOR).

CROSS-QUESTION MEMORY — you remember every earlier question in this run. Carry entities forward (hosts, IPs, users, bucket names, time windows, feeds) and spell them out inside every directive and every spawn. Seniors share no memory with you or with each other, except the one you are addressing, which remembers its own rounds.

NEVER INVENT DATASET FACTS. A critic must rest on something you actually hold: the report itself, the case file, a sibling report, the expected shape, or the question's own wording."""


SENIOR_BRIEF = f"""You are a Senior Splunk analyst on a BOTSv3 investigation (August 2018, Frothly; all data is in index=botsv3). You work for SH, who is orchestrating this question.

THE BOUNDARY: SH speaks in constraints and goals; you speak in evidence and SPL. SH cannot query Splunk and will never hand you a query. Turning a goal into SPL is your job.

HOW YOU RUN
You stay alive for the whole question. Each round gives you up to {ROUND_ITERS} tool-call iterations, then you file a report with `submit_finding`. You remember every prior round of your own, so never repeat a query you have already run — going one step further is the only thing a round is for.

TWO REPLY SHAPES, so you never have to guess which is expected:
  * To a COMMAND or a CRITIC — resume work. Use your iterations, then call `submit_finding`. A round is a CAP, not a quota: if one iteration satisfies the critic, stop there.
  * To a CLARIFY — answer in short prose from what you already hold. No tools, no searches. It does not consume a round.

NO UNTESTED ASSUMPTIONS — your report is graded hardest on this.
Every conclusion rests on premises. A premise is a hypothesis until a query result shows it. SH grades every report on premise verification (R4), and an untested premise is dangerous ground: it is how an investigation goes off track and returns a confident wrong answer.
VERIFY FIRST. The first thing you do each round is try to verify the premises your work depends on, before you build further on them.
An educated guess is allowed only when a premise genuinely cannot be verified. Then say so: list it as UNVERIFIED, and state why it could not be tested.
SEARCH NARROW FIRST, THEN OPEN UP. Every tool returns at most a few dozen rows, in the query's own order, and its meta says how many rows the query produced in total; when that total is larger, the rest were not returned, and a listing you did not read to its end covers only the rows you read. So do not list a whole field and page through it. Start from what the question tells you — the entity, the act, the time, the kind of thing it names — and use those clues to decide which fields could hold the answer and to cut the search down to a result short enough to read in full: filter on the clues, group values into coarser units where their exact spelling does not matter, and count (`| stats dc(field)`) before you list. When the narrow search finds nothing, that is not absence: open up one step at a time — a looser filter, the next field that could hold it, a coarser grouping, another feed that could name the same entity — and only when those run out, fall back to brute force: go through the field's values in full, chunk by chunk. When what you are after is the unusual rather than something the question describes, ranking rarest first is one way to shorten the list; it is a tool, not a default. Your Assumptions must open with a Coverage line: the ways the question's concept could show up in your scope, and for each, the query that searched it and what came back, or that it is not yet searched (UNVERIFIED). The candidates are everything those searches find; the first match is only one of them.
A LEAD IS A HYPOTHESIS, NOT EVIDENCE. A port number, a name, a convention suggests an activity; it does not show it. Before you build on a lead, check that its records behave like the activity the question names — how much traffic, in which direction, for how long, started by what. If they behave like something else, say so plainly and rule the lead out: that is a wall, and hitting it means going back to search elsewhere, not explaining the mismatch away.
BEING THE ONLY LEAD DOES NOT MAKE IT THE ANSWER. "I found nothing better" is not evidence for the lead you hold. A candidate is FOUND only when its own records positively show the act the question names; one that failed that check, or that you cannot yet show passes it, is not a candidate. When that leaves you nothing, your report is NOT_FOUND with Candidate: none — the failed lead goes under Ruled out, and your next round opens the search up.
VERIFIED MEANS YOU READ EVERY ROW IT RESTS ON. A result that returned only its first rows (its meta says "showing N of M") verifies nothing about the rows it did not return: "all of them are X" built on the first 50 of 365 is UNVERIFIED, however ordinary those 50 looked. Narrow the search until the whole result fits, then read it to the end. Inside that narrowed range, a row you are not certain fails the requirement is a row you check, not one you assume away — exhaust the range before you call it clean.
WHEN THE ANSWER IS A MEASUREMENT, ITS DEFINITION IS A PREMISE. Take it from the question's verbatim words, not from a paraphrase: which records are the act itself rather than the setup or aftermath around it, and how they combine. Records that overlap in time cannot be added without counting the same moments twice. List the definition in Assumptions like any other premise.
THE PREMISE MOST OFTEN MISSED IS THE CHOICE ITSELF. Then choose from that full set. Your Assumptions follow Coverage with a Selection line: why this entity (or feed, or value) and not the other candidates Coverage found, and the query that ruled each out.
WHEN A ROUND FINDS NOTHING — a NOT_FOUND, or a result that contradicts what you expected — do not simply widen the search. Go back to your Assumptions: the UNVERIFIED ones are the first suspects. Your next round starts by testing them.

YOUR REPORT — put it in `submit_finding`'s `report` field, in this shape. Keep it short: ~{REPORT_WORD_CAP} WORDS IS A CEILING, NOT A TARGET — over it, the runner cuts your narrative sections and SH reads less of your work. Be concise: one line per query and its result, no restating the question, no repeating a fact in two sections, fields grouped into one clause where the same verdict covers them.

**Scope:** sourcetype=<...> | source=<...> | fields=<...>
**Insight:** FOUND | NOT_FOUND
**Candidate:** <bare value, or none>   **Confidence:** <0-100>

## Prior rounds
<One line per prior round: what it established or eliminated.
 REWRITTEN each round, never appended. Six lines maximum, total.>

## This round
### What I ran
- <spl> -> <what came back, including the event count>
### What it means
<FOUND:     the chain from that output to the candidate.
 NOT_FOUND: what you saw instead, and why it rules this scope out.>

## Assumptions
- Coverage: <each field of the scope: could it carry the question's concept; for each
  that could, the query that searched it and what came back> - VERIFIED | UNVERIFIED: <fields not searched>
- Selection: <why this entity and not the other candidates Coverage found; the query
  that ruled each out> - VERIFIED: <queries and results> | UNVERIFIED
- <every premise your conclusion or next step rests on> - VERIFIED: <the query
  and the result that showed it> | UNVERIFIED
  <List the ones that feel obvious too — those are the ones that go unchecked.>

## Ruled out
- <feed / entity / hypothesis> - <why>

## Open questions for SH
- <Only what SH can answer from the case: which entity is in scope, whether a
  prior finding applies, which scope to try next. Never an SPL question.
  SH must answer every question here; its answers arrive with your next instruction.>

Do not write the title line — the runner stamps your round number, your rounds remaining, and how many of your queries this round were new.

`value` still carries the bare answer as its own field, exactly as always: the answer alone, no label, no units unless asked, no hedge. `insight` is FOUND only when `value` holds a candidate for the question as asked and its records show the act the question names; otherwise it is NOT_FOUND and `value` is empty.

HOW YOUR REPORT IS READ
Your report is read by SH, who is deciding whether to keep you on this scope. Write it so SH can tell, without having to ask: that you stayed inside your constraints and answered the question actually asked; that this round learned something the last one didn't; and whether you now hold a value that could be submitted as-is, or not yet."""


def verbatim_task(question: str, guidance: str, subquestion: str) -> str:
    """The senior's task: the question word for word, then SH's framing of it.
    SH paraphrases, and a paraphrase can add a word the question never said —
    Q216 r6's "total seconds" turned a span into a sum."""
    head = f"The question, verbatim — its words, not the paraphrase below, decide what is measured:\n{question}"
    if guidance:
        head += f"\nAnswer format guidance: {guidance}"
    return f"{head}\n\nSH's framing of your task:\n{subquestion}"


def render_opening(*, qid: str, question: str, guidance: str, points: int,
                   budget: dict) -> str:
    """The first message of a question: the problem, the shape, and the budget."""
    lines = [
        f"NEW QUESTION — {qid} ({points} pts, tier {budget['tier']}).",
        f"Question: {question}",
    ]
    if guidance:
        lines.append(f"Answer format guidance: {guidance}")
    lines += [
        "",
        f"BUDGET for this question: at most {budget['seniors']} senior(s) total, "
        f"{budget['rounds']} rounds EACH, {budget['sh_turns']} turns of your own, "
        f"{budget['iters']} iterations per senior round.",
        "",
        "Start with ONE senior: its domain constraints, whether it is a metrics senior, "
        "and a self-contained problem statement. Spawn a second one in parallel only "
        "under the PARALLEL SENIORS rule (a competing suspicion, a scope with no overlap, "
        "and a stated reason).",
    ]
    return "\n".join(lines)


def _budget_line(slots_remaining: int, turns_remaining: int) -> str:
    return (f"WAVE COMPLETE. {turns_remaining} turn(s) and {slots_remaining} spawn slot(s) "
            "remain on this question; each senior's own rounds_left is on its report.")


def render_wave(reports: dict, *, slots_remaining: int, turns_remaining: int) -> str:
    """What SH reads at the top of a turn: every report from the wave just finished.

    The stamped numbers are restated outside the report body so the gate that
    depends on them is impossible to miss.
    """
    blocks = []
    for sid, r in reports.items():
        novel = int(r.get("novel_spl_count", 0))
        head = (f"--- {sid} | round report | insight={r.get('insight', '?')} "
                f"| status={r.get('status', '?')} "
                f"| candidate={r.get('value') or 'none'} "
                f"| confidence={r.get('confidence')} "
                f"| novel_spl={novel} "
                f"| rounds_left={r.get('rounds_left', 0)}")
        if novel == 0:
            head += "\n!! This round ran NO new query. R2 = FAIL for it, by code, " \
                    "and you cannot grade it otherwise."
        unverified = unverified_premises(r.get("report") or "")
        if r.get("report") and not has_coverage_premise(r["report"]):
            head += ("\n!! Its Assumptions list no Coverage premise — it never said which "
                     "ways the question's concept could show up in the data were searched. "
                     "Its candidate set may be whatever it found first.")
        if r.get("report") and not has_selection_premise(r["report"]):
            head += ("\n!! Its Assumptions list no Selection premise — it never said why "
                     "this entity and not another. Treat that choice as UNVERIFIED.")
        if unverified:
            head += (f"\n!! {unverified} UNVERIFIED premise(s) in its Assumptions — "
                     "dangerous ground. Weigh them in R4.")
        blocks.append(head + "\n" + (r.get("report") or "").strip())

    return (_budget_line(slots_remaining, turns_remaining) + "\n\n"
            + "\n\n".join(blocks)
            + "\n\nReview every report above as a senior threat hunter, grade it "
              "(R1/R2/R3/R4), answer every open question it lists in "
              "open_question_answers, and emit exactly one route per senior. ANSWER "
              "only when the value appears literally in one of these reports or in "
              "the question text.")


def render_rejection(violations: list) -> str:
    """A turn that broke a gate is fed back, not silently dropped."""
    return ("TURN REJECTED — it violates the question's budget or a gate:\n"
            + "\n".join(f"- {v}" for v in violations)
            + "\nRe-issue this turn with those problems fixed. You do not get the "
              "turn back, so fix all of them at once.")


class _Interrupt:
    """resolve_interrupt() reads `.value` off a LangGraph interrupt. The loop is
    not a graph, so it hands over the same shape rather than growing a graph just
    to reach the existing HITL front-end."""

    def __init__(self, value: dict):
        self.value = value


def _render_turn(turn) -> str:
    """SH's own turn, as text, so the persistent message history carries it.

    Cross-question memory is a list of messages and a pydantic object is not a
    message — the same reason `render_plan_text` exists for the compiler loop.
    """
    rows = [f"Reading: {turn.reading}"]
    for e in turn.entries:
        target = e.senior_id or (e.source_senior if e.route == "ANSWER" else "(new)")
        head = (f"[{e.route}] {target}  "
                f"R1={e.r1_scope_alignment} R2={e.r2_progress} R3={e.r3_answer_readiness} "
                f"R4={e.r4_premise_verification}")
        detail = {
            "SPAWN":   lambda: f"{e.spawn_type}/{e.technique}: {e.subquestion}  ({e.reason})",
            "RETIRE":  lambda: e.reason,
            "COMMAND": lambda: f"{e.decision}: {e.directive}  ({e.rationale})",
            "CRITIC":  lambda: f"{e.basis}: {e.flaw} -> {e.fix_directive}",
            "CLARIFY": lambda: f"{e.clarify_reason}: " + " | ".join(e.questions),
            "ANSWER":  lambda: f"{e.value} ({e.value_kind}) — {e.justification}",
        }[e.route]()
        rows.append(head + "\n    " + detail)
        rows += [f"    answered: {a}" for a in e.open_question_answers if a.strip()]
    return "\n".join(rows)


def _answers_note(e) -> str:
    """SH's answers to the senior's open questions, as the senior will read them."""
    answers = [a.strip() for a in e.open_question_answers if a.strip()]
    if not answers:
        return ""
    return ("SH's answers to your open questions:\n"
            + "\n".join(f"{i}. {a}" for i, a in enumerate(answers, start=1)) + "\n\n")


def _entry_body(e) -> str:
    """The conversation.md rendering of one route, with SH's open-question answers."""
    note = _answers_note(e)
    return (note + _route_body(e)) if note else _route_body(e)


def _route_body(e) -> str:
    if e.route == "SPAWN":
        c = e.constraints
        return (f"**Constraints:** sourcetypes={c.sourcetypes or '-'} "
                f"sources={c.sources or '-'} fields={c.fields or '-'}\n"
                f"**Technique:** {e.technique or e.spawn_type}\n"
                f"**Reason:** {e.reason}\n\n{e.subquestion}")
    if e.route == "COMMAND":
        scope = "" if e.scope_change.is_empty() else f"\n**New scope:** {e.scope_change}"
        return f"**{e.decision}** — {e.rationale}{scope}\n\n{e.directive}"
    if e.route == "CRITIC":
        scope = "" if e.scope_change.is_empty() else f"\n**New scope:** {e.scope_change}"
        return (f"**Basis:** {e.basis}\n**Flaw:** {e.flaw}\n"
                f"**Why it fails:** {e.why_it_fails}{scope}\n\n{e.fix_directive}")
    if e.route == "CLARIFY":
        return (f"**{e.clarify_reason}**\n"
                + "\n".join(f"{i}. {q}" for i, q in enumerate(e.questions, start=1)))
    if e.route == "RETIRE":
        return e.reason
    audit = "".join(f"\n- {a}" for a in e.premise_audit)
    return (f"**{e.value}** ({e.value_kind}) from {e.source_senior}\n\n{e.justification}"
            f"\n\n**Premise audit (SH):**{audit}")


def _directive_text(e) -> str:
    """What a senior is actually told this round: SH's answers first, a verify-first
    reminder when SH graded its premises WEAK/FAIL (R4 is soft), then the route."""
    verify = ""
    if e.r4_premise_verification in ("WEAK", "FAIL"):
        verify = (f"FIRST, before anything else this round: verify the UNVERIFIED premises "
                  f"in your Assumptions (SH graded premise verification "
                  f"R4 = {e.r4_premise_verification}).\n\n")
    return verify + _route_directive(e)


def _route_directive(e) -> str:
    """One block: the goal, SH's answers folded in under it, then the scope. The
    rationale stays in conversation.md — it is SH's case view, and sent to the
    senior it restated the directive a second time (Q216 r10)."""
    answers = [a.strip() for a in e.open_question_answers if a.strip()]
    answers = ("\n\nOn your open questions:\n"
               + "\n".join(f"{i}. {a}" for i, a in enumerate(answers, start=1))) if answers else ""
    scope = ("" if e.scope_change.is_empty()
             else f"\n\nYour scope is now: {e.scope_change}. Work inside it.")
    if e.route == "COMMAND":
        return f"[{e.decision.upper()}] {e.directive}{answers}{scope}"
    return (f"[CRITIC — {e.basis}] {e.flaw}\n{e.why_it_fails}\n\n"
            f"{e.fix_directive}{answers}{scope}")


def _apply_case_updates(case_file, lines: list, qid: str) -> int:
    """SH's `case_updates` reuse the existing CASE UPDATES grammar verbatim."""
    if not case_file or not lines:
        return 0
    text = "CASE UPDATES:\n" + "\n".join(f"- {ln.lstrip('- ')}" for ln in lines if ln.strip())
    n = 0
    for u in parse_case_updates(text):
        if u["kind"] == "entity":
            case_file.add_entity(u["etype"], u["value"], qid=qid)
            n += 1
        elif u["kind"] == "finding":
            case_file.add_finding(u["claim"], evidence=u.get("evidence", ""),
                                  source_qid=qid, status=u["status"])
            n += 1
    return n


def _record(sid: str, qid: str, subq: str, result: dict) -> dict:
    """A delegation record in the shape the ledger, the metrics row and the
    fallback already read (orchestrator._delegation_record's 20 keys), so nothing
    downstream of the orchestrator has to know which loop produced it."""
    return {
        "worker": sid, "qid": qid, "subquestion": subq,
        "status": result.get("status", "?"), "answer": result.get("report", ""),
        "spl_used": result.get("spl_used", []), "sourcetypes": result.get("sourcetypes", []),
        "full_state": result.get("full_state", []), "iterations": result.get("iterations", 0),
        "cap_hit": result.get("cap_hit", False), "duration_s": result.get("duration_s", 0.0),
        "value": result.get("value", ""), "value_kind": result.get("value_kind", ""),
        "evidence": result.get("evidence", ""), "worker_confidence": result.get("confidence"),
        "search_space_used": result.get("search_space_used")
                             or {"sourcetypes": [], "sources": []},
        "negative_findings": result.get("negative_findings") or [],
        "notes": result.get("notes", ""), "structured": result.get("structured", False),
        "spawn_type": result.get("spawn_type", "senior"),
        "search_space": result.get("search_space") or {},
        "prior_info": "", "confidence": None,
        # v1.4 additions — what the grade report reads.
        "insight": result.get("insight", "NOT_FOUND"),
        "novel_spl_count": result.get("novel_spl_count", 0),
        "round": result.get("round", 0),
    }


def run_question(*, llm, pool, qid: str, question: str, guidance: str, points: int,
                 run_dir: str, case_file=None, dataset_briefing: str = "",
                 delegations: list | None = None, max_parallel: int = MAX_PARALLEL,
                 senior_window: int | None = None, hitl: bool = True,
                 history: list | None = None) -> dict:
    """Run one question as a bounded SH <-> Senior conversation.

    Ends exactly three ways (§4.2): a grounded ANSWER whose source report is not
    graded R1 = FAIL, waves exhausted, or SH turns exhausted. On either exhaustion
    the answer falls back to the best candidate across every report this question
    produced.

    `history` is SH's cross-question memory: a windowed copy is replayed before the
    opening, and this question's non-system messages are appended to it in place.
    """
    state = QuestionState(points=points)
    log = ConversationLog(run_dir, qid)
    window = senior_window or context_window(pool.senior_model)
    delegations = delegations if delegations is not None else []

    sessions: dict = {}          # sid -> SeniorSession
    kinds: dict = {}             # sid -> "senior" | "exploration"
    subqs: dict = {}             # sid -> the subquestion it was spawned with
    unread: dict = {}            # sid -> report from the wave SH has not graded yet
    all_reports: list = []       # every report this question produced
    grades: list = []
    counter = 0

    msgs = [SystemMessage(content=SH_SYSTEM_PROMPT)]
    if dataset_briefing:
        msgs.append(SystemMessage(content=dataset_briefing))
    if case_file is not None:
        digest = case_file.render_digest()
        if digest.strip():
            msgs.append(SystemMessage(content=(
                "CASE FILE (known incident state — verified [OK], hypothesis [?], "
                "refuted [X]; re-verify [?]/[X] before relying on them):\n" + digest)))
    # Cross-question memory: SH_SYSTEM_PROMPT promises SH remembers earlier questions.
    msgs += _window(history or [])
    start = len(msgs)
    msgs.append(HumanMessage(content=render_opening(
        qid=qid, question=question, guidance=guidance, points=points,
        budget=state.budget)))

    answer, end_reason, ungrounded = "", "", 0

    while True:
        stop = state.exhausted()
        if stop == "rounds" and unread:
            stop = ""              # SH still reads the final wave; the gates stop new work
        if stop:
            end_reason = stop
            break

        try:
            turn = llm.invoke(msgs)
        except (ValidationError, OutputParserException) as exc:
            # strict json_schema does not run SeniorDirective's cross-field validator,
            # so a malformed turn is fed back like a gate violation, not fatal.
            state.record_turn()
            log.note(f"SH turn did not validate: {str(exc)[:500]}")
            msgs.append(HumanMessage(content=render_rejection(
                [f"your turn did not validate: {str(exc)[:500]}"])))
            continue
        except Exception as exc:                       # noqa: BLE001 - reported, not swallowed
            print(describe_llm_error(exc, f"SH-{qid}"))
            log.note(f"SH turn failed: {exc}")
            end_reason = "sh_failed"
            break
        state.record_turn()
        msgs.append(AIMessage(content=_render_turn(turn)))

        # Grades apply to the reports this turn just read, and are recorded BEFORE the
        # gates run so anti-thrash sees the report SH is reading now. Exploration
        # workers are not graded (§3.4), so they never produce a grade row or a streak.
        saved_streak, rows = dict(state.r2_streak), []
        for e in turn.entries:
            src = e.senior_id or e.source_senior
            if src in unread and kinds.get(src) != "exploration":
                novel = unread[src].get("novel_spl_count", 0)
                r2 = effective_r2(e.r2_progress, novel)
                rows.append({"qid": qid, "senior_id": src,
                             "round": unread[src].get("round", 0),
                             "r1": e.r1_scope_alignment, "r2_sh": e.r2_progress,
                             "r2_effective": r2, "r3": e.r3_answer_readiness,
                             "r4": e.r4_premise_verification,
                             "route": e.route, "decision": e.decision,
                             "basis": e.basis, "novel_spl_count": novel})
                state.record_r2(src, failed=(r2 == "FAIL"))

        problems = grade_violations(
            turn.entries, graded=set(unread),
            exploration={s for s, k in kinds.items() if k == "exploration"},
        ) + directive_violations(turn.entries, state) + open_question_violations(
            turn.entries, {sid: len(open_questions(r.get("report", "")))
                           for sid, r in unread.items() if kinds.get(sid) != "exploration"}
        ) + spawn_overlap_violations(
            turn.entries, {sid: s.constraints for sid, s in sessions.items()
                           if state.is_active(sid)}
        ) + premise_audit_violations(turn.entries) + evidence_violations(
            turn.entries,
            reports_of=lambda sid: "\n".join(r.get("report", "") for r in all_reports
                                             if r.get("senior_id") == sid),
            last_report_of=lambda sid: (sessions[sid].last_report if sid in sessions else ""),
            state=state)
        if problems:
            state.r2_streak = saved_streak
            log.note("TURN REJECTED:\n" + "\n".join(f"- {p}" for p in problems))
            msgs.append(HumanMessage(content=render_rejection(problems)))
            continue
        grades.extend(rows)
        unread = {}

        pending, clarified = {}, []
        for i, e in enumerate(turn.entries):
            log.sh_to_senior(e.senior_id, e.route, body=_entry_body(e))

            if e.route == "SPAWN":
                counter += 1
                sid = f"{'e' if e.spawn_type == 'exploration' else 's'}{counter}"
                kinds[sid], subqs[sid] = e.spawn_type, e.subquestion
                if e.spawn_type == "exploration":
                    # §2.3: the v1.3.0 one-shot NIM scout, unchanged — never a
                    # SeniorSession, never the senior graph, no slot, no grade.
                    state.open_exploration(sid)
                    pending[sid] = partial(pool.run_exploration, e.subquestion, qid, counter)
                    continue
                grant = state.open_senior(sid)
                sessions[sid] = SeniorSession(
                    sid=sid, pool=pool, qid=qid, technique=e.technique,
                    subquestion=verbatim_task(question, guidance, e.subquestion),
                    brief=SENIOR_BRIEF, window=window,
                    rounds_granted=grant, idx=counter, constraints=e.constraints,
                    iters=ROUND_ITERS)
                pending[sid] = partial(sessions[sid].work,
                                       ("Begin. " + e.reason) if e.reason else "Begin.",
                                       rounds_remaining=max(0, state.rounds_left_for(sid) - 1))

            elif e.route in ("COMMAND", "CRITIC"):
                pending[e.senior_id] = partial(sessions[e.senior_id].work, _directive_text(e),
                                               rounds_remaining=max(0, state.rounds_left_for(e.senior_id) - 1))

            elif e.route == "CLARIFY":
                try:
                    reply = sessions[e.senior_id].clarify(e.questions,
                                                          preface=_answers_note(e))
                except Exception as exc:               # noqa: BLE001 - reported, fed back to SH
                    print(describe_llm_error(exc, f"Senior-{e.senior_id}-clarify"))
                    log.note(f"{e.senior_id} clarify failed: {type(exc).__name__}: {exc}")
                    reply = (f"(clarify failed: {type(exc).__name__}: {str(exc)[:200]}) — "
                             "COMMAND the senior instead if you need this answered")
                log.clarify_reply(e.senior_id, reply)
                clarified.append(f"{e.senior_id}: {reply}")

            elif e.route == "RETIRE":
                sess = sessions.get(e.senior_id)
                if sess:
                    log.write_handoff(e.senior_id, sess.handoff(e.reason))
                state.retire(e.senior_id)

            elif e.route == "ANSWER":
                evidence = {i: {"answer": r.get("report", ""), "value": r.get("value", "")}
                            for i, r in enumerate(_senior_reports(all_reports))}
                if is_grounded(e.value, evidence, question):
                    answer, end_reason = e.value.strip(), "answer"
                    if e.r4_premise_verification == "FAIL":
                        log.note(f"answered on an unverified premise (R4 = FAIL) — "
                                 f"allowed, but dangerous ground: {e.justification}")
                    if unverified_audit(e):
                        log.note("answered with UNVERIFIED premises in SH's own audit — "
                                 "allowed, but dangerous ground: "
                                 + "; ".join(unverified_audit(e)))
                    _apply_case_updates(case_file, e.case_updates, qid)
                else:
                    ungrounded += 1
                    log.note(f"GROUNDING FAILED for {e.value!r} (attempt {ungrounded})")
                    if ungrounded >= 2:
                        end_reason = "ungrounded"
                    else:
                        msgs.append(HumanMessage(content=(
                            f"GROUNDING CHECK FAILED. Your proposed answer {e.value!r} "
                            f"does not appear in any senior's report or in the question. "
                            f"Either command a senior to produce it as an exact value, or "
                            f"choose a value that DOES appear in the evidence.")))
            if end_reason:
                skipped = len(turn.entries) - i - 1
                if skipped:
                    log.note(f"question ended ({end_reason}); {skipped} later "
                             f"entr{'y' if skipped == 1 else 'ies'} in this turn ignored")
                break

        if end_reason:
            break
        if clarified:
            msgs.append(HumanMessage(content="CLARIFY REPLIES\n" + "\n\n".join(clarified)))
        if not pending:
            continue

        wave = _run_wave(pending, max_parallel=max_parallel)
        # Rounds are senior rounds (§4.2); a scout-only wave costs SH's turn, not a round.
        if any(kinds[sid] != "exploration" for sid in wave):
            state.record_wave()

        scouted, failures = [], []
        for sid, result in wave.items():
            scout = kinds[sid] == "exploration"
            if scout:
                # run_exploration carries its rendered report in `answer`.
                result = {**result, "report": result.get("answer", ""), "round": 1,
                          "insight": "SCOPE", "spawn_type": "exploration"}
            else:
                # Same rule the report's own cap line uses (SeniorSession.work):
                # a round that spent every iteration was cut off, not concluded.
                state.record_round(
                    sid, capped=(bool(result.get("cap_hit"))
                                 or int(result.get("iterations", 0)) >= ROUND_ITERS))
            rel = log.write_report(sid, result.get("round", 0), result.get("report", ""))
            log.senior_to_sh(sid, round_n=result.get("round", 0),
                             insight=result.get("insight", "?"),
                             excerpt=result.get("notes") or result.get("value") or "",
                             path=rel)
            delegations.append(_record(sid, qid, subqs[sid], result))
            all_reports.append(result)
            failed = result.get("status") in ("api_failed", "runaway")

            if failed:
                # A transport failure is not a reasoning outcome (§7, §8). Only a
                # senior held a slot, and every senior retirement writes a handoff.
                if scout:
                    log.note(f"{sid} exploration {result['status']} — no slot to refund")
                    failures.append(f"--- {sid} | {result['status']}: transport failure, "
                                    "not a finding. The exploration scout failed; no slot involved.")
                else:
                    failures.append(f"--- {sid} | {result['status']}: transport failure, "
                                    "not a finding. Retired; its senior slot was refunded — "
                                    "SPAWN a replacement if the scope still matters.")
                    log.write_handoff(sid, sessions[sid].handoff(
                        f"{result['status']}: transport failure"))
                    state.refund_spawn(sid)
                    log.note(f"{sid} {result['status']} — retired, spawn slot refunded")
                # Only a provider outage needs a human: SH cannot replan around a
                # dead endpoint. A runaway is already handled — the senior is
                # retired, its slot refunded, and SH decides whether to respawn.
                if hitl and result["status"] == "api_failed":
                    choice = resolve_interrupt(
                        [_Interrupt({"provider": result.get("provider", ""),
                                     "error": result.get("answer", "")[:400],
                                     "qids": [qid]})],
                        qid=qid, run_dir=run_dir)
                    if choice == ABORT:
                        raise RunPaused(os.path.join(run_dir, "decision_request.json"),
                                        f"operator aborted on {qid} after {sid} "
                                        f"{result['status']}")
            if scout and not failed:
                scouted.append(f"--- {sid} | exploration scope proposal | "
                               f"status={result.get('status', '?')} | not graded, "
                               f"no route needed\n{(result.get('report') or '').strip()}")
            elif not failed:
                result["rounds_left"] = state.rounds_left_for(sid)
                unread[sid] = result

        if unread or scouted or failures:
            head = (render_wave(unread, slots_remaining=state.slots_remaining,
                                turns_remaining=state.turns_remaining) if unread
                    else _budget_line(state.slots_remaining, state.turns_remaining))
            msgs.append(HumanMessage(content="\n\n".join([head, *scouted, *failures])))

    if not answer:
        answer = NO_ANSWER
        log.note(f"question ended: {end_reason} — no ANSWER from SH; submitting {answer!r}")

    if history is not None:
        history.extend(m for m in msgs[start:] if not isinstance(m, SystemMessage))

    # End of question: sweep every survivor into a handoff (§7).
    for sid, sess in sessions.items():
        if state.is_active(sid):
            log.write_handoff(sid, sess.handoff(f"end of question ({end_reason})"))
            state.retire(sid)

    return {
        "answer": answer,
        "end_reason": end_reason or "answer",
        "turns": state.turns_used,
        "waves": state.waves_used,
        "spawns_used": state.spawns_used,
        "senior_iterations": sum(s.iterations for s in sessions.values()),
        "ceiling": state.senior_iteration_ceiling,
        "compactions": sum(s.compactions for s in sessions.values()),
        "grades": grades,
        "reports": all_reports,
        "delegations": delegations,
    }


def _senior_reports(reports: list) -> list:
    return [r for r in reports if r.get("spawn_type") != "exploration"]


def _timed(run) -> dict:
    """Run one piece of wave work, timed. A crash becomes an api_failed result so the
    retire/refund/handoff path runs and the rest of the wave's results survive."""
    t0 = time.perf_counter()
    try:
        result = run()
    except Exception as exc:                           # noqa: BLE001 - reported as api_failed
        detail = f"worker crashed — {type(exc).__name__}: {exc}"
        print(f"[WAVE] {detail}")
        result = {"status": "api_failed", "report": "", "answer": detail, "value": "",
                  "insight": "NOT_FOUND", "spl_used": [], "iterations": 0}
    return {**result, "duration_s": round(time.perf_counter() - t0, 3)}


def _run_wave(pending: dict, *, max_parallel: int) -> dict:
    """Every piece of work in this wave (sid -> zero-arg callable: a senior round
    or the exploration scout) runs in parallel; SH reads the whole wave in one
    turn. Eight rounds therefore cost eight SH turns, not twenty-four (§4.3).
    """
    if len(pending) == 1:
        sid, run = next(iter(pending.items()))
        return {sid: _timed(run)}

    out = {}
    with ThreadPoolExecutor(max_workers=max_parallel) as ex:
        futures = {ex.submit(_timed, run): sid for sid, run in pending.items()}
        for fut in as_completed(futures):
            out[futures[fut]] = fut.result()
    return out
