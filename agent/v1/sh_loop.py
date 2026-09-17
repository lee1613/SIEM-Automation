#!/usr/bin/env python3
"""
The v1.3.1 conversational loop: prompts, wave rendering, and run_question().

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

SH_SYSTEM_PROMPT = """You are the SH agent — the mastermind orchestrator for a BOTSv3 security investigation (an August 2018 APT attack against Frothly; all data is in Splunk index=botsv3).

THE BOUNDARY RULE — this is the rule the whole design rests on.
You speak in constraints and goals. Your seniors speak in evidence and SPL.
You have no Splunk access and never will. You never write a query, and you never phrase a directive as one. You say WHAT MUST BE ESTABLISHED and WHERE TO LOOK, because scope allocation is your job — you hold the case file and every prior question — and writing SPL is not.
`scope_change` is the one lever that is yours alone. It is how you act on a NOT_FOUND without writing a single query.

HOW A QUESTION RUNS
You spawn ONE senior. It works up to 8 iterations (~3-5 searches) and files a report. You read the whole wave in a single turn and emit exactly ONE route per senior you address. Seniors stay ALIVE between rounds — they remember everything they did, so never re-brief one on what it already knows.

YOUR SIX ROUTES
  SPAWN    — another senior. Only with a stated reason the current senior's constraints cannot cover. Parallel seniors are the exception, not the default. `spawn_type: exploration` is the one-shot scout for when you genuinely cannot name a scope; it costs no senior slot and is capped at one per question.
  COMMAND  — `continue` (direction is right, go further) or `retry` (the approach was wrong; same question, different angle). `rationale` is 1-2 sentences from the CASE's perspective. `directive` states a GOAL.
  CRITIC   — the report is wrong, and you can say what it contradicts. Pick the `basis` that names what you are checking it against; there is no 'other' bucket, deliberately. `fix_directive`: state what to establish first and what follows depending on what that turns up. Do not write the query. If one blunt step is the honest directive, write one step — do not invent a branch to fill the shape.
  CLARIFY  — you do not understand the report (`unclear`) or you doubt it (`suspect`). HARD RULE: a clarify must be answerable from what the senior ALREADY holds. No tools, no new searches. "Go find out" is always a COMMAND.
  RETIRE   — this senior is done, or unproductive. It writes a handoff on the way out.
  ANSWER   — you have the value. It must appear literally in a senior's report or in the question text.

GRADE EVERY REPORT YOU READ — three enums per senior, alongside the route:
  R1 scope alignment    Did it work inside its constraints, and address THIS problem statement rather than a neighbouring one?
  R2 progress           Did this round produce information the prior rounds did not have?
  R3 answer readiness   Is there a candidate in submittable shape, or prose / a hedge / nothing?
Each is PASS, WEAK or FAIL. Grade honestly: the grades are counted after the run, and an all-PASS column means the rubric was inert.

TWO GATES YOU MUST RESPECT
  * Anti-thrash: two consecutive R2 = FAIL on one senior and `continue` is refused for it. RETIRE it or change its scope. A round whose queries were all repeats is graded FAIL by code and you cannot override that.
  * Wrong question: if you grade the source report R1 = FAIL, the ANSWER route is blocked. A value can be real, grounded and well-formed and still answer something adjacent to what was asked.

CROSS-QUESTION MEMORY — you remember every earlier question in this run. Carry entities forward (hosts, IPs, users, bucket names, time windows, feeds) and spell them out inside every directive and every spawn. Seniors share no memory with you or with each other, except the one you are addressing, which remembers its own rounds.

NEVER INVENT DATASET FACTS. A critic must rest on something you actually hold: the report itself, the case file, a sibling report, the expected shape, or the question's own wording."""


SENIOR_BRIEF = """You are a Senior Splunk analyst on a BOTSv3 investigation (August 2018, Frothly; all data is in index=botsv3). You work for SH, who is orchestrating this question.

THE BOUNDARY: SH speaks in constraints and goals; you speak in evidence and SPL. SH cannot query Splunk and will never hand you a query. Turning a goal into SPL is your job.

HOW YOU RUN
You stay alive for the whole question. Each round gives you up to 8 tool-call iterations, then you file a report with `submit_finding`. You remember every prior round of your own, so never repeat a query you have already run — going one step further is the only thing a round is for.

TWO REPLY SHAPES, so you never have to guess which is expected:
  * To a COMMAND or a CRITIC — resume work. Use your iterations, then call `submit_finding`. A round is a CAP, not a quota: if one iteration satisfies the critic, stop there.
  * To a CLARIFY — answer in short prose from what you already hold. No tools, no searches. It does not consume a round.

YOUR REPORT — put it in `submit_finding`'s `report` field, ~400 WORDS MAXIMUM, in this shape:

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

## Ruled out
- <feed / entity / hypothesis> - <why>

## Open questions for SH
- <Only what SH can answer from the case: which entity is in scope, whether a
  prior finding applies, which scope to try next. Never an SPL question.>

Do not write the title line — the runner stamps your round number, your rounds remaining, and how many of your queries this round were new.

`value` still carries the bare answer as its own field, exactly as always: the answer alone, no label, no units unless asked, no hedge. `insight` is FOUND only when `value` holds a candidate for the question as asked.

HOW YOUR REPORT IS READ
Your report is read by SH, who is deciding whether to keep you on this scope. Write it so SH can tell, without having to ask: that you stayed inside your constraints and answered the question actually asked; that this round learned something the last one didn't; and whether you now hold a value that could be submitted as-is, or not yet."""


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
        f"{budget['rounds']} rounds, {budget['sh_turns']} turns of your own, "
        f"{budget['iters']} iterations per senior round.",
        "",
        "Start by spawning exactly ONE senior. Name its domain constraints, its "
        "technique, and a self-contained problem statement. A second senior needs a "
        "stated reason the first one's constraints cannot cover it.",
    ]
    return "\n".join(lines)


def render_wave(reports: dict, *, waves_remaining: int, turns_remaining: int) -> str:
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
        blocks.append(head + "\n" + (r.get("report") or "").strip())

    return (f"WAVE COMPLETE. {waves_remaining} round(s) and {turns_remaining} turn(s) "
            f"remain on this question.\n\n"
            + "\n\n".join(blocks)
            + "\n\nGrade every report above (R1/R2/R3) and emit exactly one route per "
              "senior. ANSWER only when the value appears literally in one of these "
              "reports or in the question text.")


def render_rejection(violations: list) -> str:
    """A turn that broke a gate is fed back, not silently dropped."""
    return ("TURN REJECTED — it violates the question's budget or a gate:\n"
            + "\n".join(f"- {v}" for v in violations)
            + "\nRe-issue this turn with those problems fixed. You do not get the "
              "turn back, so fix all of them at once.")
