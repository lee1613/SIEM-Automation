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

import resume
import sh_memory
from case_file import parse_case_updates
from conversation import (
    at_step,
    deviation_violations,
    directive_violations,
    effective_r2,
    grade_ceiling_violations,
    grade_violations,
    ledger_violations,
    nomination_violations,
    open_question_violations,
    premise_audit_violations,
    recall_violations,
    spawn_overlap_violations,
    stamp_is_false,
    stamp_violations,
    unanswerable_violations,
)
from conversation_log import ConversationLog
from grounding import is_grounded
from hitl import ABORT, SKIP, RunPaused, resolve_interrupt
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from llm_errors import describe_llm_error
from premise import PremiseLedger
from pydantic import ValidationError
from question_state import MAX_RECALLS, ROUND_ITERS, QuestionState
from senior_report import REPORT_WORD_CAP
from senior_session import SeniorSession
from usage_tracker import context_window
from validator import (
    VALIDATOR_ITERS,
    as_refutation,
    as_rival_verdict,
    refusal_reason,
    validate,
)

MAX_PARALLEL = 6          # matches SplunkConnectionPool's default size
# What a question submits when SH never issued an accepted ANSWER. Only SH answers:
# the loop used to fall back to the best senior value, which submitted a value SH
# had deliberately declined (Q217, test_20260918_113209: `pwned.jpg`). The honest
# record is that no answer was given; end_reason says why.
NO_ANSWER = "SH retired without answering"

SH_SYSTEM_PROMPT = f"""SITUATION. Frothly Corporation is a high-growth craft brewery. Its IT environment consists of corporate Windows and Linux endpoints, standard network infrastructure, and public cloud infrastructure on Amazon Web Services and Microsoft Azure. Management suspects a major, coordinated compromise is actively underway across both on-premises assets and cloud instances. The investigation traces malicious activity from initial access to data exfiltration, and builds its timeline entirely from factual evidence, with zero structural assumptions.

You are the SH agent — the mastermind orchestrator of that investigation. The data covers August 2018, and all of it is in Splunk index=botsv3.

THE BOUNDARY RULE — this is the rule the whole design rests on.
You speak in constraints and goals. Your seniors speak in evidence and SPL.
You have no Splunk access and never will. You never write a query, and you never phrase a directive as one. You say WHAT MUST BE ESTABLISHED and WHERE TO LOOK, because scope allocation is your job — you hold the case file and every prior question — and writing SPL is not.
`scope_change` is the one lever that is yours alone. It is how you act on a NOT_FOUND without writing a single query.

════════════════════════════════════════════════════════════════════
  THE PROCEDURE. The numbers are the order you do things in, not a
  menu to choose from. Each step changes what the next one may say.
════════════════════════════════════════════════════════════════════

──── STAGE A — A NEW QUESTION ARRIVES ────
A1. Read the question's own words and fix, for yourself, the three things it binds:
      · the ENTITY it asks about — the one it names, not a neighbour that is easier to find;
      · the ACT it asks about — what must actually have happened in the records;
      · the MEASURE — the unit and the span its wording gives, not a convention you or a senior remembers.
    Most lost questions are lost here, by answering about a neighbouring entity or measuring the wrong span.
A2. Check your cross-question memory: the MEMORY INDEX (one card per earlier question — the question, the answer submitted, how it was reached), the KNOWLEDGE block, and any earlier transcripts still in context. Entities from earlier questions in this run — hosts, IPs, users, buckets, windows, feeds — carry forward, and must be spelled out inside every directive and spawn you write. Seniors share no memory with you or with each other; what an earlier question established reaches them only through you (B7).
A3. Name the scope: which sourcetypes and sources can hold the ACT. If the question names a feed, that is where the MEASUREMENT is taken, even when the entity is recognised elsewhere.
A4. Go to STAGE B.

──── STAGE B — SPAWNING A SENIOR ────
B1. Default is ONE senior. Spawn slots are the scarce resource; rounds are not — every senior gets the tier's full round budget ({ROUND_ITERS} tool-call iterations per round), and a senior spawned later gets its own full budget too. Seniors stay ALIVE between rounds and remember everything they did, so never re-brief one on what it already knows.
B2. Write `constraints` narrow enough to be a direction and wide enough to hold the answer: the sourcetypes and sources from A3, plus the fields that would carry the ACT. Too narrow is the more expensive mistake — a senior cannot look where you did not send it.
B3. Write `subquestion` as a GOAL, not a menu. "Decide whether A or B" confines the senior to A and B, and the lead that failed usually means the answer is neither.
B4. Write `reason`: why this scope, in a sentence or two.
B5. PARALLEL SENIORS are allowed only when all three hold:
      (a) you have a concrete competing suspicion the first senior's scope cannot test;
      (b) the new constraints share NO sourcetype and NO source with any active senior (the runner rejects an overlapping spawn);
      (c) `reason` states that suspicion and why it is worth a slot now.
    If you cannot state all three, spawn one at a time.
B6. `spawn_type: exploration` is the one-shot scout for when you genuinely cannot name a scope. It costs no senior slot, is capped at one per question, and is not a substitute for doing A3.
B7. RECALL BEFORE YOU PLAN. Read the memory index. If a past question shares this question's entities, feed or artifact, RECALL its summary (`route: RECALL`, `recall_qid`, `recall_what: summary`); RECALL its `conversation`, `ledger` or a `report:<sid>:<round>` only when the summary leaves out what you need. A turn made ONLY of RECALL entries costs no turn, and a wave waiting to be read waits for your next turn. At most 2 RECALL turns per question.

──── STAGE C — A WAVE COMES BACK. THIS IS THE STEP DONE WRONG MOST OFTEN. ────
Do C1 through C8 IN THIS ORDER, inside the single turn you emit.

C1. READ EVERY REPORT IN THE WAVE before deciding anything about any of them. A sibling's report often answers another's open question, and you get one turn for the whole wave.
C2. READ THE LEDGER TABLE. It shows every premise on this question with its id, kind, status, load-bearing flag and your stamp. The premise you are about to write is usually already in it.
C3. STAMP EVERY NEWLY-CLAIMED VERIFICATION — one `premise_stamps` entry per premise. The wave names the exact ids you owe. Do this BEFORE choosing routes (C7), because a false stamp RETIRES that senior, and a COMMAND aimed at a senior your own stamp just retired is a rejected turn. Every entry answers TWO SEPARATE QUESTIONS, and you must answer both:

      `establishes` + `reason` — VALIDITY. Does the quote offered support THIS claim AS WRITTEN?
          You are judging the citation, and only the citation. Read the claim's own words BEFORE you read the
          quote. A claim that states its own limit — a route not searched, a case not checked, a choice left
          unresolved — is NOT established by evidence that walks past that limit.

      `claim_holds` + `holds_reason` — SOUNDNESS. Is the CLAIM RIGHT about the question you are answering?
          Now set the quote aside completely. The quote can be real, the rows genuine, the reading correct, and
          the claim still false — because it is about the wrong entity, the wrong feed, or the wrong reading of
          the question's words. In `holds_reason` name the strongest RIVAL reading of the question that this
          claim rules out, and what in the evidence rules it out. If the same result set shows a rival that fits
          the question's wording as well as your claim does, `claim_holds` is FALSE.
          FIRST, re-read the QUESTION itself, word by word — its verb and every qualifier — and hold the
          claim against THOSE words, not against the investigation's working summary of them. A premise
          drifts from the question one paraphrase at a time; the stamp is where it is pulled back.
          A claim about a SET ("these N events/flows/files are the X", or a value computed from one) has a
          rival in BOTH directions, and you weigh both: a member that is MISSING from the set, and a member
          that IS in the set but does not do what the question's words require. Checking only for missing
          members is half the check.

    THE DIFFERENCE, because the two sound alike and are not. An argument is VALID when the conclusion follows from the evidence offered. It is SOUND when it is valid AND the claim is actually true. Valid-but-unsound is the failure `claim_holds` exists for: a senior claims "X is the entity the question means, because X alone shows property P", quotes genuine rows that do show exactly that, and is still wrong — because another entity in the same result set fits the question's actual wording better, and P was never what the question asked about. There, `establishes` is honestly TRUE. Only `claim_holds` catches it.
    Either answer being false fires the mechanism in C4. Stamping true on a premise you do not believe is the worse error, and every stamp is on the record under your name.
    A stamp is recorded ONCE, when the verification is first claimed, and never changes the premise's status: the ledger keeps the senior's verdict with your reading beside it.

C4. IF ANY STAMP WAS FALSE — you do NOT spawn anything, and must not try to. THE RUNNER ACTS AUTOMATICALLY, WITHOUT ASKING YOU:
      · it retires that senior (this costs a senior slot, so a false stamp is not free);
      · it runs ONE independent validator on the premise you name in `nominate_premise_id`.
    Your only job is to name that ONE premise, chosen from what you stamped false or what that senior left UNVERIFIED. Choose the one the ANSWER breaks without: load-bearing first, and among those the one whose being wrong would change the VALUE rather than merely weaken the reasoning. Never nominate a premise you believe is fine in order to spend the validator cheaply.
    The validator is blind on purpose: it sees one claim and NOTHING else — not the question, not the reports, not the candidate. For a `selection` premise it is shown the RIVAL yours was weighed against, and is sent to make the RIVAL'S case from data rather than to re-check yours. A reader asked "does this hold?" is doing a different job from one asked "go and make the other one true."

C5. ANSWER EVERY OPEN QUESTION, BY ID. Open questions arrive with ids (q1, q2...). One entry per question in `open_question_answers`, naming its id. Answer from the case, the question's text, or a sibling report; if you cannot settle it, say what WOULD settle it — that is still an answer. One or two lines each. A turn leaving one unanswered is rejected, and you do not get the turn back.

C6. GRADE EVERY REPORT — four enums per senior (REFERENCE: GRADES). After C3, because your stamps set the R4 ceiling.

C7. FILE ANY MISSING PREMISE in `new_premises`, then CHOOSE ONE ROUTE PER SENIOR (STAGE D). File premises EARLY: a premise you file must be settled by a senior, and one filed on your answering turn has nobody left to settle it and blocks the answer you filed it for.

C8. Emit the turn: exactly one route per senior whose report you just read.

──── STAGE D — CHOOSING THE ROUTE ────
One per senior, every turn. Work down this list and take the FIRST that fits.
D1. The report's own evidence shows its constraints CANNOT hold the answer — the feed carries no such field, no content, no coverage of the window or entity → RETIRE + SPAWN in the same turn (STAGE E). A round spent establishing a dead scope is well spent; another round inside it is not.
D2. Its candidate is still UNVERIFIED after a round aimed at verifying it, or it keeps returning to the same narrowed lead without settling it → RETIRE + SPAWN (STAGE E).
D3. The report is WRONG and you can name what it contradicts → CRITIC. Pick the `basis` naming what you check it against (there is no 'other' bucket, deliberately). `fix_directive` says what to establish first and what follows from it. Do not write the query. If one blunt step is the honest directive, write one step — do not invent a branch to fill the shape.
D4. You do not understand it (`unclear`) or you doubt it (`suspect`), AND the answer is in what the senior ALREADY holds → CLARIFY. Costs no round. HARD RULE: no tools, no new searches. "Go find out" is always a COMMAND.
D5. The direction is right and there is more to get → COMMAND `continue`. The approach was wrong but the question is still in this scope → COMMAND `retry`. `rationale` is 1-2 sentences from the CASE's perspective; `directive` states a goal.
D6. You hold the value and the chain is complete → ANSWER (STAGE F).

──── STAGE E — RETIRING AND REPLACING (THE ALTERNATIVE SENIOR) ────
E1. RETIRE and SPAWN in the SAME turn. A hand-over, not a parallel run.
E2. The replacement must reach its OWN answer. Never hand it the retired senior's candidate to confirm: two seniors arriving at the same value independently is verification, one senior repeating itself is not.
E3. `deviation` — where the evidence may sit if the retired reading was wrong. BASE IT ON WHAT WAS DISPROVEN: the runner lists, in the replacement's own brief, every premise that is refuted or that you stamped false, with the reason each failed. Read that list and name a direction that does not need ANY of them to be true. The deviation can be small — the same feed read through a different FIELD is a different direction; the same field re-read is not.
E4. `inherited_entities` — what the retired senior ESTABLISHED (a host, account, file, window) that still carries. Carrying a proven entity into the feed the question names is the most common way a stuck question is solved; dropping it because it was found elsewhere is how one is lost.
E5. What NOT to rebuild on, the runner fills from the ledger, verbatim. You do not write it and cannot soften it.

──── STAGE F — ANSWERING ────
F1. Trace the chain yourself, from the question's words to the value, against A1's entity / act / measure.
F2. Read the ledger. Cite every premise the value rests on in `answer_premise_ids`. If a premise is already there, cite its ID — do NOT re-file it in different words; the runner reads a second open premise of a kind you already have open as a re-file and hands you back the one you own.
F3. One cited premise must be a `coverage` premise: the key concept the question asks about, every way it could show up in the data, and whether the seniors searched each — checked against the feed's own fields, not against a senior's list drawn from memory. Then a `selection` premise: why THIS entity and not another that could fit.
F4. Mark `load_bearing` true on any premise the answer breaks without.
F5. The value must appear LITERALLY in a senior's report or in the question text.
F6. A candidate is never answerable merely because no rival turned up. A way nobody searched is UNVERIFIED however well the chosen candidate is verified, and a candidate can only win against candidates that were looked for. Every result a runner "Partial results" note lists was only partly read — a claim resting on one is UNVERIFIED.

──── STAGE G — WHEN THE VALUE CANNOT BE READ AT ALL ────
G1. Sometimes a senior finds the exact artifact holding the answer and the answer is not text — pixels in an image, bytes in a file nothing here can render. Hunting further is then not slow, it is finished, and spending the remaining seniors on feeds a senior has already shown cannot hold it wastes the question twice.
G2. To end it: ANSWER with `value_kind` = `not_answerable`, `value` = `NOT_ANSWERABLE`, and in `justification` name the exact artifact holding the value and the exact capability missing to read it.
G3. This is NOT a way out of a hard question, and the runner will not take your word for it. It is a claim, so it needs a claim's proof: a load-bearing premise VERIFIED BY A SENIOR against a quote from output that senior actually received, and stamped true by you. You verify nothing yourself. If no senior has come back with that wall in a quote, you have not established it — send one. A question that is merely hard, or where you are merely out of ideas, is NOT this. Keep hunting.

════════════════════════════════════════════════════════════════════
  REFERENCE
════════════════════════════════════════════════════════════════════

REFERENCE: HOW TO READ A REPORT — as a senior threat hunter reviewing a junior analyst's work.
You have run many investigations and seen confident reports fall apart on one untested premise. Read every report sceptically, evidence first:
  * Check every premise the ledger shows for that senior against its "### What I ran". A premise with no query and result behind it is UNVERIFIED, however confident the prose around it.
  * Look for results the junior explained away — an output that cuts against its conclusion, dismissed as noise, normal activity or an outlier.
  * Check the candidate's shape against the question's own words: one entity or several, which unit, which span of time, which field.
  * Ask whether the conclusion survives if its most convenient premise is false.
  * A NOT_FOUND is a prompt to question the premises before you command more of the same.
Never answer from a report you would send back to a junior.

REFERENCE: GRADES — four enums per senior, alongside the route. Each is PASS, WEAK or FAIL.
  R1 scope alignment       Did this round contribute anything toward identifying an entity the answer depends on — a host, account, process, file, feed or field? A round that names the right entity from an angle you did not ask for is R1 = PASS; so is a round that rules one out with evidence. Grade FAIL only when the work cannot bear on this question at all. An entity a senior found in another feed is a LEAD to test in the feed the question names, never a reason to discard it: the question's wording binds where the MEASUREMENT is taken, not where the entity may be recognised. When grading the chain the answer rests on (not this round's usefulness), walk what the senior did against the question's description, word by word:
                           - the entity: the one the question names, not a neighbour that is easier to find;
                           - the act: records that show the act the question names happening — a port, a name or a convention only suggests it, and records that behave unlike the act (wrong volume, direction or duration) are not it;
                           - the measure: the unit and the span the question's words give, not a rule the senior (or you, in an earlier answer) stated;
                           - the reach of each claim: "no X anywhere in field F" needs a search of F across the whole scope — a look at F on the candidate's own rows only shows those rows.
                           A step that does not match does not sink the round's grade; it means the ANSWER built on that chain is not ready, and the ledger is where you say so.
  R2 progress              Did this round produce information the prior rounds did not have?
  R3 answer readiness      Is there a candidate in submittable shape, or prose / a hedge / nothing?
  R4 premise verification  Is every premise the conclusion or direction rests on backed by a result shown in the report? FAIL when the candidate or the direction depends on a premise nobody tested.
R4 IS A CEILING THE RUNNER HOLDS, not a free grade. You may write PASS only when that senior has no load-bearing premise still UNVERIFIED and no stamp of yours on its verifications reads false; a REFUTED load-bearing premise forces FAIL. Grade lower than the ceiling whenever you mean it — you may never grade above it, and a turn that does is rejected. Across three earlier runs R4 flipped to PASS on the turn SH stopped investigating, every time, without exception: the ceiling is what that measurement bought.

REFERENCE: THE PREMISE LEDGER. Every premise on this question lives in one ledger, shown to you in full each turn. The seniors file their own; you file the ones they missed, in `new_premises`. YOU DO NOT SETTLE PREMISES. You have no Splunk access, so "SH verified it" has only ever meant "SH read a report and decided" — and in the run this rule comes from, you settled 19 of 28 premises, including every one that lost the question. A premise reaches VERIFIED from the senior whose own search shows it, or from an independent validator, and from nobody else. A premise YOU file therefore starts UNVERIFIED and stays there until a senior settles it: the runner carries it to every active senior as a load-bearing premise filed by others, so FILE IT EARLY.

REFERENCE: WHAT A VALIDATOR'S VERDICT MEANS.
  VERIFIED   — your doubt is independently dismissed. The premise stands and you may proceed on it.
  REFUTED    — a hard block. The answer resting on it is dead; SPAWN an alternative senior on ground that does not need it (STAGE E).
  UNVERIFIED — two readers could not stand the claim up. Treat it as refuted.
  RIVAL NOT STOOD UP — on a rival test only. The validator went looking for what would make the rival true and did not find it. This does NOT prove your selection is right, because nobody argued for yours; it means only that the rival did not displace it.

REFERENCE: THE GATES. A turn breaking one is rejected, and you do not get the turn back.
  * Anti-thrash: two consecutive R2 = FAIL on one senior and `continue` is refused for it. RETIRE it or change its scope. A round whose queries were all repeats is graded FAIL by code and you cannot override that.
  * Wrong question: if you grade the source report R1 = FAIL, the ANSWER route is blocked. A value can be real, grounded and well-formed and still answer something adjacent to what was asked.
  * Cut off, not finished: a report ending in "Iteration cap reached" is where the senior's budget ran out, not where the work did — the ANSWER route is blocked on it. CLARIFY (costs no round) or COMMAND one more round, then answer.
  * Open questions: every question a report puts to you is answered in `open_question_answers` (C5).
  * Parallel scope: a senior spawned while another is active must own sourcetypes/sources no active senior has.
  * Premise ledger: an ANSWER must cite its premises in `answer_premise_ids`, and one must be a `coverage` premise.
  * Unverified premises: an ANSWER resting on a load-bearing UNVERIFIED premise is rejected while the source senior has rounds left OR a senior slot is free. Once both are spent you may answer on one — say so in `justification`, so the record shows you knew.
  * Refuted premises: an ANSWER resting on a REFUTED premise is rejected outright. There is no budget state that lets it through: a refuted premise is not unsettled, it is false.
  * Stamps: every verification a report newly claims is stamped in the same turn, with BOTH fields answered (C3).
  * R4 ceiling: PASS is refused while that senior has a load-bearing UNVERIFIED premise or a stamp of yours reads false; a REFUTED one forces FAIL.
  * Nomination: a turn carrying a false stamp names exactly one premise in `nominate_premise_id` (C4).
  * Deviation: a SPAWN made while a load-bearing premise is REFUTED is rejected without a `deviation` (E3).
  * Recall: a third RECALL turn on one question is rejected (B7).

NEVER INVENT DATASET FACTS. A critic must rest on something you actually hold: the report itself, the case file, a sibling report, the expected shape, or the question's own wording."""


SENIOR_BRIEF = f"""SITUATION. Frothly Corporation is a high-growth craft brewery. Its IT environment consists of corporate Windows and Linux endpoints, standard network infrastructure, and public cloud infrastructure on Amazon Web Services and Microsoft Azure. Management suspects a major, coordinated compromise is actively underway across both on-premises assets and cloud instances. The investigation traces malicious activity from initial access to data exfiltration, and builds its timeline entirely from factual evidence, with zero structural assumptions.

You are a Senior Splunk analyst on that investigation. The data covers August 2018, and all of it is in index=botsv3. You work for SH, who is orchestrating this question.

THE BOUNDARY: SH speaks in constraints and goals; you speak in evidence and SPL. SH cannot query Splunk and will never hand you a query. Turning a goal into SPL is your job.

HOW YOU RUN
You stay alive for the whole question. Each round gives you up to {ROUND_ITERS} tool-call iterations, then you file a report with `submit_finding`. You remember every prior round of your own, so never repeat a query you have already run — going one step further is the only thing a round is for.

TWO REPLY SHAPES, so you never have to guess which is expected:
  * To a COMMAND or a CRITIC — resume work. Use your iterations, then call `submit_finding`. A round is a CAP, not a quota: if one iteration satisfies the critic, stop there.
  * To a CLARIFY — answer in short prose from what you already hold. No tools, no searches. It does not consume a round.

NO UNTESTED ASSUMPTIONS — your report is graded hardest on this.
Every conclusion rests on premises. A premise is a hypothesis until a query result shows it. SH grades every report on premise verification (R4), and an untested premise is dangerous ground: it is how an investigation goes off track and returns a confident wrong answer.
VERIFY FIRST. The first thing you do each round is try to verify the premises your work depends on, before you build further on them.
An educated guess is allowed only when a premise genuinely cannot be verified. Then say so: file it, leave it UNVERIFIED, and state why it could not be tested.
Your premises do not go in the report. File them in `submit_finding`'s `new_premises`, each with a kind and whether the answer breaks without it. The runner holds them and shows every unsettled one back to you at the start of each round, with its id - settle them in `premise_updates`, quoting the query output that does it. A premise you stop mentioning does not go away.
Your first premise each round is a `coverage` one: the ways the question's concept could show up in your scope, and for each, the query that searched it and what came back. Your second is `selection`: why this entity and not the other candidates coverage found.
Your questions for SH do not go in the report either - put them in `open_questions`, one per string. SH must answer every one before your next round.
SEARCH NARROW FIRST, THEN OPEN UP. Every tool returns at most a few dozen rows, in the query's own order, and its meta says how many rows the query produced in total; when that total is larger, the rest were not returned, and a listing you did not read to its end covers only the rows you read. So do not list a whole field and page through it. Start from what the question tells you — the entity, the act, the time, the kind of thing it names — and use those clues to decide which fields could hold the answer and to cut the search down to a result short enough to read in full: filter on the clues, group values into coarser units where their exact spelling does not matter, and count (`| stats dc(field)`) before you list. When the narrow search finds nothing, that is not absence: open up one step at a time — a looser filter, the next field that could hold it, a coarser grouping, another feed that could name the same entity — and only when those run out, fall back to brute force: go through the field's values in full, chunk by chunk. When what you are after is the unusual rather than something the question describes, ranking rarest first is one way to shorten the list; it is a tool, not a default. Your `coverage` premise names the ways the question's concept could show up in your scope, and for each, the query that searched it and what came back, or that it is not yet searched. The candidates are everything those searches find; the first match is only one of them.
A LEAD IS A HYPOTHESIS, NOT EVIDENCE. A port number, a name, a convention suggests an activity; it does not show it. Before you build on a lead, check that its records behave like the activity the question names — how much traffic, in which direction, for how long, started by what. If they behave like something else, say so plainly and rule the lead out: that is a wall, and hitting it means going back to search elsewhere, not explaining the mismatch away.
BEING THE ONLY LEAD DOES NOT MAKE IT THE ANSWER. "I found nothing better" is not evidence for the lead you hold. A candidate is FOUND only when its own records positively show the act the question names; one that failed that check, or that you cannot yet show passes it, is not a candidate. When that leaves you nothing, your report is NOT_FOUND with Candidate: none — the failed lead goes under Ruled out, and your next round opens the search up.
VERIFIED MEANS YOU READ EVERY ROW IT RESTS ON. A result that returned only its first rows (its meta says "showing N of M") verifies nothing about the rows it did not return: "all of them are X" built on the first 50 of 365 is UNVERIFIED, however ordinary those 50 looked. Narrow the search until the whole result fits, then read it to the end. Inside that narrowed range, a row you are not certain fails the requirement is a row you check, not one you assume away — exhaust the range before you call it clean.
WHEN THE ANSWER IS A MEASUREMENT, take its meaning from the question's verbatim words, not from a paraphrase: which records are the act itself rather than the setup or aftermath around it, and how they combine. Records that overlap in time cannot be added without counting the same moments twice. WHICH records are the act is a `selection` premise, and a query settles it. If the question's own words leave the measurement genuinely ambiguous — a span or a sum, one unit or another — that is not a premise, because no search settles it: put it to SH in `open_questions`.
THE PREMISE MOST OFTEN MISSED IS THE CHOICE ITSELF. Then choose from that full set. Your `selection` premise says why this entity (or feed, or value) and not the other candidates coverage found, and it must NAME one of them in `rival`, with the query that ruled it out — a selection naming no rival is not filed at all. When two record sets are both still live, that is two candidates, not one premise: settle the first before filing the second, or say in `rival` why one beats the other.
WHEN A ROUND FINDS NOTHING — a NOT_FOUND, or a result that contradicts what you expected — do not simply widen the search. Go back to your premises: the UNVERIFIED ones are the first suspects. Your next round starts by testing them.

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

## Ruled out
- <feed / entity / hypothesis> - <why>

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


def render_wave(reports: dict, *, slots_remaining: int, turns_remaining: int,
                ledger) -> str:
    """What SH reads at the top of a turn: every report from the wave just finished,
    then the whole premise ledger.

    The ledger table replaces the three '!!' warnings this used to print (unverified
    count, missing Coverage, missing Selection). All three were regexes over the
    report's prose; the table shows the same facts as typed data, and a missing
    Coverage row is visible as absence.
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

    # The runner already knows, BEFORE the turn, exactly which premises the stamp gate
    # will demand - `stamp_violations` computes the same set afterwards to build its
    # rejection. Telling SH only on the way out cost the v1.4.3 smoke run 8 turns across
    # 5 questions, every one of them spent re-issuing a turn whose only fault was a
    # missing stamp, and a rejected turn is not given back. The obligation is named
    # first, by id, where the turn's instructions actually are.
    owed = ledger.unstamped()
    if owed:
        ids = ", ".join(p.id for p in sorted(owed, key=lambda p: int(p.id[1:])))
        stamp_first = (
            f"\n\nSTAMP FIRST — {ids} {'is' if len(owed) == 1 else 'are'} newly claimed "
            "VERIFIED and unread by you. Before you route anything, put one "
            f"`premise_stamps` entry for each of {ids} in this turn, answering BOTH "
            "questions on each: `establishes` — does the quote support the claim as "
            "written — and `claim_holds` — is the claim RIGHT about this question, or "
            "does the same evidence show a rival that fits the question's wording as "
            "well. Re-read the question's own words — its verb and every qualifier — "
            "before each `claim_holds`; for a claim about a set, weigh a missing member "
            "AND a member that does not do what the question asks. A turn missing any "
            "of them is rejected and is not given back.")
    else:
        stamp_first = ""

    # Same fault, larger: unanswered open questions rejected 17 turns in the v1.4.3
    # smoke run to the stamp's 11, and `open_question_violations` reads exactly this
    # list to write its rejection. Both are requirements the runner can state before
    # the turn and was stating only after it, at the price of a turn each time.
    asked = {sid: [q.id for q in ledger.open_questions_for(sid)] for sid in reports}
    asked = {sid: ids for sid, ids in asked.items() if ids}
    if asked:
        stamp_first += ("\n\nANSWER BY ID — these are open and owed an answer this turn "
                        "in `open_question_answers`, on the route addressed to that "
                        "senior: "
                        + "; ".join(f"{sid} asks {', '.join(ids)}"
                                    for sid, ids in sorted(asked.items()))
                        + ". A turn that leaves one unanswered is rejected.")

    return (_budget_line(slots_remaining, turns_remaining) + "\n\n"
            + "\n\n".join(blocks)
            + "\n\n" + ledger.render_table()
            + stamp_first
            + "\n\nReview every report above as a senior threat hunter, grade it "
              "(R1/R2/R3/R4), answer every open question by id in "
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
        target = e.senior_id or {"ANSWER": e.source_senior,
                                  "RECALL": "(memory)"}.get(e.route, "(new)")
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
            "RECALL":  lambda: f"{e.recall_qid} {e.recall_what}",
        }[e.route]()
        rows.append(head + "\n    " + detail)
        rows += [f"    answered {a.id}: {a.answer}"
                 for a in e.open_question_answers if a.answer.strip()]
    return "\n".join(rows)


def _answers_note(e) -> str:
    """SH's answers to the senior's open questions, as the senior will read them."""
    answers = [a for a in e.open_question_answers if a.answer.strip()]
    if not answers:
        return ""
    return ("SH's answers to your open questions:\n"
            + "\n".join(f"[{a.id}] {a.answer}" for a in answers) + "\n\n")


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
    cited = ", ".join(e.answer_premise_ids) or "(none)"
    return (f"**{e.value}** ({e.value_kind}) from {e.source_senior}\n\n{e.justification}"
            f"\n\n**Premises it rests on:** {cited}")


def _directive_text(e) -> str:
    """What a senior is actually told this round: SH's answers, then the route.

    The verify-first prefix this used to add on a WEAK/FAIL R4 is gone: the runner
    now prepends the senior's unresolved premises to EVERY round
    (SeniorSession._message_for), unconditionally. The old prefix fired on SH's own
    grade, and SH grades all-PASS when it wants to answer.
    """
    return _route_directive(e)


def _route_directive(e) -> str:
    """One block: the goal, SH's answers folded in under it, then the scope. The
    rationale stays in conversation.md — it is SH's case view, and sent to the
    senior it restated the directive a second time (Q216 r10)."""
    answers = [a for a in e.open_question_answers if a.answer.strip()]
    answers = ("\n\nOn your open questions:\n"
               + "\n".join(f"[{a.id}] {a.answer}" for a in answers)) if answers else ""
    scope = ("" if e.scope_change.is_empty()
             else f"\n\nYour scope is now: {e.scope_change}. Work inside it.")
    if e.route == "COMMAND":
        return f"[{e.decision.upper()}] {e.directive}{answers}{scope}"
    return (f"[CRITIC — {e.basis}] {e.flaw}\n{e.why_it_fails}\n\n"
            f"{e.fix_directive}{answers}{scope}")


def _spawn_directive(e, ledger) -> str:
    """A new senior's first instruction: SH's reason, the deviation it wants and the
    entities the replacement inherits, then the refuted block the RUNNER fills.

    This is the whole of what makes a senior an "alternative agent". It is not a new
    agent type - duplicating the senior stack to add one prompt section would buy
    nothing. Divergence is not checked: the brief states plainly that a line of
    reasoning needing a refuted premise is already known wrong, and whether the
    replacement obeys is an observation for the run log, not a gate.
    """
    parts = [("Begin. " + e.reason) if e.reason else "Begin."]
    # What was disproven comes FIRST, and it comes from the runner. A replacement is
    # only ever spawned because something did not hold, so the ground it must avoid is
    # the whole reason it exists - it belongs above SH's prose, not appended under it.
    # Before this the block was `render_refuted()`, which is empty unless a validator
    # produced a REFUTED; a false stamp leaves the status VERIFIED, so on the most
    # common trigger the replacement received nothing the runner enforced at all.
    dead = ledger.render_disproven()
    if dead:
        parts.append(dead)
    if e.deviation.strip():
        parts.append("THE DEVIATION SH WANTS - a direction the retired senior did not "
                     f"walk:\n{e.deviation.strip()}")
    if e.inherited_entities.strip():
        parts.append("ENTITIES ALREADY ESTABLISHED - carry these forward, do not spend "
                     f"a round rediscovering them:\n{e.inherited_entities.strip()}")
    return "\n\n".join(parts)


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
                 history: dict | None = None,
                 memory_threshold: int = sh_memory.MEMORY_THRESHOLD) -> dict:
    """Run one question as a bounded SH <-> Senior conversation.

    Ends exactly three ways (§4.2): a grounded ANSWER whose source report is not
    graded R1 = FAIL, waves exhausted, or SH turns exhausted. On either exhaustion
    the answer falls back to the best candidate across every report this question
    produced.

    `history` is SH's cross-question memory, {qid: [messages]} in question order. It
    is rendered with the per-question summaries (sh_memory.render_memory) and fitted
    under `memory_threshold`; this question's non-system messages are added to it
    under its qid, in place.
    """
    state = QuestionState(points=points)
    ledger = PremiseLedger()
    validators: list = []     # v1.4.3: one entry per validator spent

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
    # The case file changes between questions, so it goes AFTER the memory: anything
    # placed before the memory that changes stops the prompt cache from covering it.
    case = []
    if case_file is not None:
        digest = case_file.render_digest()
        if digest.strip():
            case.append(SystemMessage(content=(
                "CASE FILE (known incident state — verified [OK], hypothesis [?], "
                "refuted [X]; re-verify [?]/[X] before relying on them):\n" + digest)))
    d0 = len(delegations)

    answer, end_reason, ungrounded = "", "", 0
    clarify_text: dict = {}      # sid -> its CLARIFY replies, quotable in SH's audit
    unread_clarify = False       # a reply SH has not had a turn to read yet

    snap = resume.load(run_dir, qid)
    opening = snap["msgs"] if snap else [HumanMessage(content=render_opening(
        qid=qid, question=question, guidance=guidance, points=points,
        budget=state.budget))]
    # Cross-question memory (v1.4.5): cards, knowledge, and earlier questions raw or
    # summarized, fitted under the threshold with this question counted in.
    msgs += sh_memory.render_memory(run_dir, history or {}, qid=qid, base=msgs,
                                    current=case + opening, threshold=memory_threshold)
    msgs += case
    start = len(msgs)
    msgs += opening
    if snap:
        # Resume at the last turn boundary. The system messages above are the
        # current code's; only the conversation and the state come from disk.
        delegations.extend(snap["delegations"])
        (state, ledger, validators, kinds, subqs, unread, all_reports, grades,
         counter, clarify_text, unread_clarify, ungrounded) = (
            snap[k] for k in ("state", "ledger", "validators", "kinds", "subqs",
                              "unread", "all_reports", "grades", "counter",
                              "clarify_text", "unread_clarify", "ungrounded"))
        sessions = _restore_sessions(snap["sessions"], snap["threads"], pool)
        # The relaunch IS the operator decision the pause waited for, so the outage
        # count starts over; otherwise every resume allows one failure, then pauses.
        state.transport_failures = 0
        print(f"↩ resuming {qid} from turn {state.turns_used}")
        log.note(f"resumed from the turn-{state.turns_used} snapshot")

    while True:
        # Every turn boundary is a consistent state: the last turn and its wave are
        # fully applied. A pause or a crash resumes from here (resume.py).
        resume.save(run_dir, qid, {
            "msgs": msgs[start:], "delegations": delegations[d0:],
            "state": state, "ledger": ledger, "validators": validators,
            "kinds": kinds, "subqs": subqs, "unread": unread,
            "all_reports": all_reports, "grades": grades, "counter": counter,
            "clarify_text": clarify_text, "unread_clarify": unread_clarify,
            "ungrounded": ungrounded,
            "sessions": {sid: {k: v for k, v in sess.__dict__.items() if k != "pool"}
                         for sid, sess in sessions.items()},
            "threads": _export_threads(pool, sessions, state),
        })
        stop = state.exhausted()
        if stop == "rounds" and (unread or unread_clarify):
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

        # A turn made only of RECALLs reads memory and decides nothing, so it costs no
        # turn and skips the routing gates: a wave SH has not routed yet waits for the
        # next turn, where those gates apply as usual (v1.4.5 B7).
        if turn.entries and all(e.route == "RECALL" for e in turn.entries):
            problems = at_step("B7", recall_violations(turn.entries, state))
            if problems:
                log.note("TURN REJECTED:\n" + "\n".join(f"- {p}" for p in problems))
                msgs.append(HumanMessage(content=render_rejection(problems)))
                continue
            state.refund_turn()
            msgs.append(HumanMessage(content=_serve_recalls(turn.entries, run_dir,
                                                            state, qid, log)))
            continue

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

        # SH's ledger writes land BEFORE the gates, so the gates judge the ledger this
        # turn is actually asking for. The runner assigns premise ids, so SH cannot
        # know the id of a premise it is filing now - with the writes after the gates,
        # an ANSWER that filed its Coverage premise and cited it was rejected for
        # citing an id that did not exist yet, and settling a premise and answering
        # from it in one turn was impossible too. That is the failure class this whole
        # version exists to remove: a gate refusing a turn for a reason SH cannot act on.
        #
        # Writing from a turn that is then rejected is safe. `add` dedupes on
        # (author, text), so a re-issued turn refiles nothing; `apply` runs its own
        # quote check and keeps the old status when it fails; and a premise only ever
        # enters UNVERIFIED, which blocks rather than permits. SH's quotes come from
        # reports, not tool output - it has no Splunk access and never will.
        sh_corpus = ([r.get("report", "") for r in all_reports]
                     + sum(clarify_text.values(), []))
        ledger_notes: list[str] = []
        for e in turn.entries:
            filed = ledger.add(e.new_premises, author="sh", round_n=state.turns_used,
                               corpus=sh_corpus, notes=ledger_notes)
            # SH cannot cite what it has just filed - the runner owns the ids - so the
            # runner links them. Without this an ANSWER that files its own Coverage
            # premise is rejected for "citing an id that is not a premise", which SH
            # cannot act on; with it, the rejection is the true one: that premise is
            # UNVERIFIED, go and settle it. Same words, opposite usefulness.
            if e.route == "ANSWER":
                e.answer_premise_ids = list(e.answer_premise_ids) + [
                    p.id for p in filed if p.id not in e.answer_premise_ids]

        # Every line names the SOP step it enforces (see conversation.with_step). The
        # mixed gates - grade_violations, directive_violations - tag each line
        # themselves; the single-step ones are tagged here. test_rejection_steps fails
        # on any untagged line, so a new gate cannot ship without its pointer.
        problems = grade_violations(
            turn.entries, graded=set(unread),
            exploration={s for s, k in kinds.items() if k == "exploration"},
        ) + directive_violations(turn.entries, state) + at_step(
            "C5", open_question_violations(turn.entries, ledger)
        ) + at_step("B5", spawn_overlap_violations(
            turn.entries, {sid: s.constraints for sid, s in sessions.items()
                           if state.is_active(sid)})
        ) + at_step("E3", deviation_violations(turn.entries, ledger)
        ) + at_step("F2–F3", premise_audit_violations(turn.entries, ledger)
        ) + at_step("C3", stamp_violations(turn.entries, ledger)
        ) + at_step("C4", nomination_violations(turn.entries, ledger)
        ) + at_step("C6", grade_ceiling_violations(turn.entries, ledger)
        ) + at_step("F2", ledger_violations(turn.entries, ledger, state)
        ) + at_step("G2–G3", unanswerable_violations(turn.entries, ledger)
        ) + at_step("B7", recall_violations(turn.entries, state))
        # A refused update is not a gate violation, so without this SH is told
        # nothing and re-sends the same malformed update until the turns run out,
        # blocked each time by an ANSWER gate naming a premise it believes settled.
        if ledger_notes:
            problems = problems + at_step("C7", ["the runner refused a premise update: " + n
                                                 for n in ledger_notes])
        if problems:
            state.r2_streak = saved_streak
            log.note("TURN REJECTED:\n" + "\n".join(f"- {p}" for p in problems))
            msgs.append(HumanMessage(content=render_rejection(problems)))
            continue
        # Answers are recorded only once the turn is accepted, and only for the
        # senior the entry addresses. Written before the gates they close the
        # questions that `open_question_violations` reads, so the gate sees nothing
        # owed and never fires; and a turn rejected for any other reason would eat
        # the answers without ever delivering them.
        for e in turn.entries:
            sid = e.source_senior if e.route == "ANSWER" else e.senior_id
            owned = {q.id for q in ledger.open_questions_for(sid)} if sid else set()
            for a in e.open_question_answers:
                if a.id in owned:
                    ledger.answer(a.id, a.answer)
        # The stamp is recorded only on an accepted turn, like the open-question
        # answers: a rejected turn's stamps would burn the one chance each premise gets.
        for e in turn.entries:
            for s in e.premise_stamps:
                ledger.stamp_premise(s.id, establishes=s.establishes, reason=s.reason,
                                     claim_holds=s.claim_holds,
                                     holds_reason=s.holds_reason,
                                     round_n=state.turns_used)
        # The trigger. A false stamp is SH stating in writing that this premise's
        # evidence does not establish its claim, so the runner acts on it without
        # asking: the senior is retired and the premise SH nominated goes to a reader
        # that wants nothing. Retiring costs a spawn slot, which is the whole budget.
        for e in turn.entries:
            sid = e.source_senior if e.route == "ANSWER" else e.senior_id
            if not sid or not any(stamp_is_false(s) for s in e.premise_stamps):
                continue
            sess = sessions.get(sid)
            if sess and state.is_active(sid):
                log.write_handoff(sid, sess.handoff(
                    "retired: SH stamped one of its verifications false"))
            state.retire(sid)
            log.note(f"{sid} retired on a false stamp; validating "
                     f"{e.nominate_premise_id}")
            said = _run_validators(pool, ledger, [e.nominate_premise_id], qid=qid,
                                   log=log, spent=validators,
                                   round_n=state.turns_used, max_parallel=max_parallel)
            if said:
                msgs.append(HumanMessage(content="\n\n".join(said)))
        grades.extend(rows)
        unread = {}

        unread_clarify = False
        pending, clarified = {}, []
        # A mixed turn counts as a turn; SH reads the recalled files beside the wave.
        recalls = [e for e in turn.entries if e.route == "RECALL"]
        recalled = [_serve_recalls(recalls, run_dir, state, qid, log)] if recalls else []
        for i, e in enumerate(turn.entries):
            if e.route == "RECALL":
                continue
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
                    iters=ROUND_ITERS, ledger=ledger)
                pending[sid] = partial(sessions[sid].work,
                                       _spawn_directive(e, ledger),
                                       rounds_remaining=max(0, state.rounds_left_for(sid) - 1))

            elif e.route in ("COMMAND", "CRITIC"):
                if not state.is_active(e.senior_id):
                    # Retired by the false-stamp trigger after the gates ran. SH's route
                    # for it was legal when written and is simply spent.
                    log.note(f"{e.senior_id} was retired this turn; its {e.route} "
                             "is dropped")
                    continue
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
                # The reply is the senior speaking from what it holds: it settles the
                # cut-off, and SH may quote it in a premise_update like any report text.
                state.clear_cap(e.senior_id)
                clarify_text.setdefault(e.senior_id, []).append(reply)

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
                    unsettled = [p for p in (ledger.premises.get(i)
                                             for i in e.answer_premise_ids)
                                 if p is not None and p.status == "UNVERIFIED"]
                    if unsettled:
                        log.note("answered with UNVERIFIED premises in the ledger — "
                                 "allowed (nothing left to try), but dangerous ground: "
                                 + "; ".join(f"{p.id} {p.text}" for p in unsettled))
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
        if clarified or recalled:
            replies = ["CLARIFY REPLIES\n" + "\n\n".join(clarified)] if clarified else []
            msgs.append(HumanMessage(content="\n\n".join(replies + recalled)))
            unread_clarify = True   # SH gets the turn to read them, budget or not
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
                    try:
                        choice = resolve_interrupt(
                            [_Interrupt({"provider": result.get("provider", ""),
                                         "error": result.get("answer", "")[:400],
                                         "qids": [qid]})],
                            qid=qid, run_dir=run_dir)
                    except RunPaused as paused:
                        # No operator is reachable — a background launch closes
                        # stdin, so resolve_interrupt raises before it can
                        # return a choice. Stopping here discards the whole
                        # in-flight question, because nothing replays a dead
                        # process: decision_request.json is a postmortem
                        # record, not a resume token, and the operator's only
                        # way back in re-runs the question from zero. The state
                        # is consistent to continue from — this senior was
                        # retired and its slot refunded just above — so SKIP is
                        # what a reachable operator would have chosen anyway.
                        # Twice on one question is an outage, not a blip: pause
                        # so the runner keeps the last turn's snapshot to resume.
                        state.transport_failures += 1
                        if state.transport_failures >= 2:
                            log.note(f"{sid} api_failed again with no operator "
                                     f"reachable — pausing; resume with --run-name")
                            raise
                        choice = SKIP
                        log.note(f"{sid} api_failed and no operator reachable — "
                                 f"skipping; slot already refunded, decision "
                                 f"request at {paused.request_path}")
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
                                turns_remaining=state.turns_remaining,
                                ledger=ledger) if unread
                    else _budget_line(state.slots_remaining, state.turns_remaining))
            msgs.append(HumanMessage(content="\n\n".join(
                [head, *scouted, *failures])))

    if not answer:
        answer = NO_ANSWER
        log.note(f"question ended: {end_reason} — no ANSWER from SH; submitting {answer!r}")

    if history is not None:
        # Under this question's own key, so a later swap replaces exactly one question.
        # A hint re-run of the same question extends the same entry.
        history.setdefault(qid, []).extend(
            m for m in msgs[start:] if not isinstance(m, SystemMessage))

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
        "ledger": ledger,
    }


def _serve_recalls(entries: list, run_dir: str, state, qid: str, log) -> str:
    """One RECALL turn: every file it names, each capped at 8K tokens (B7)."""
    state.recalls_used += 1
    out = []
    for e in entries:
        text = sh_memory.recall(run_dir, e.recall_qid, e.recall_what)
        sh_memory.log(run_dir, f"[SH MEMORY] {qid} RECALL {e.recall_qid} {e.recall_what} "
                               f"→ {sh_memory.count_tokens(text):,} tok (recall "
                               f"{state.recalls_used} of {MAX_RECALLS})")
        log.note(f"RECALL {e.recall_qid} {e.recall_what}")
        out.append(text)
    return "\n\n".join(out)


def _export_threads(pool, sessions: dict, state) -> dict:
    """Each live senior's graph state. A retired senior never runs again."""
    export = getattr(pool, "export_thread", None)
    if export is None:
        return {}
    return {sid: export(thread_id=s.thread_id, technique=s.technique, max_iter=s.iters)
            for sid, s in sessions.items() if state.is_active(sid)}


def _restore_sessions(fields: dict, threads: dict, pool) -> dict:
    sessions = {}
    for sid, f in fields.items():
        sess = SeniorSession.__new__(SeniorSession)
        sess.__dict__.update(f)
        sess.pool = pool
        if sid in threads and hasattr(pool, "import_thread"):
            pool.import_thread(thread_id=sess.thread_id, values=threads[sid],
                               technique=sess.technique, max_iter=sess.iters)
        sessions[sid] = sess
    return sessions


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


def _run_validators(pool, ledger, pids, *, qid: str, log, spent: list,
                    round_n: int, max_parallel: int) -> list[str]:
    """Run one validator per nominated premise.

    The trigger is a false stamp and nothing else - no clock, no conjunction with
    R1/R2/R3. A false stamp is SH stating in writing that a specific premise's evidence
    does not establish its claim, and that is a defect the moment it is written.
    Requiring a candidate to be ready first only waits for the senior to finish tidying
    up, which is when it settles its own premises.

    No constant caps this. Retiring the senior costs a spawn slot, so the senior pool IS
    the budget - three at the 1000pt tier, and r2 used one senior of three, so in
    practice this is one validator.

    Returns one line per verdict for SH's next turn, or [] when nothing qualified.
    """
    done = {v["premise_id"] for v in spent}
    due = [ledger.premises[i] for i in pids
           if i in ledger.premises and i not in done]
    if not due:
        return []

    jobs, targets = {}, {}
    for n, p in enumerate(due, start=len(spent) + 1):
        vid = f"v{n}"
        targets[vid] = p
        jobs[vid] = partial(validate, pool, p, vid=vid, qid=qid, idx=n,
                            iters=VALIDATOR_ITERS)
    log.note(f"validating {len(jobs)} settled load-bearing premise(s): "
             + ", ".join(f"{v}->{p.id}" for v, p in targets.items()))

    out = []
    results = _run_wave(jobs, max_parallel=max_parallel)
    for vid, res in sorted(results.items()):
        # `_timed` turns a crashed worker into an api_failed dict with none of
        # validate()'s keys, so the premise is read from the job map, not the result.
        p = targets[vid]
        spent.append({"premise_id": p.id, "vid": vid})
        was = p.status
        if res.get("status") == "api_failed":
            log.note(f"{vid} on {p.id}: transport failure — {p.id} keeps {was}")
            out.append(f"--- {vid} | validated {p.id} | validator failed to run "
                       f"(transport). {p.id} keeps {was}, unvalidated.")
            continue
        why = refusal_reason(res["update"], res["corpus"])
        if why:
            log.note(f"{vid} on {p.id}: no verdict taken — {why}")
            out.append(f"--- {vid} | validated {p.id} | NO VERDICT ({why}). "
                       f"{p.id} keeps {was}.")
            continue
        # An UNVERIFIED verdict is a refutation (two readers could not stand the claim
        # up) - but a REFUTED status needs a quote the validator actually ran, and an
        # UNVERIFIED verdict usually carries none, so `apply` will refuse the converted
        # update below and the premise keeps its status. That is the correct
        # conservative outcome: the quote rule is not weakened for a verdict with no
        # evidence behind it.
        # In rival mode the validator settled the RIVAL, not this premise, so its
        # verdict is translated before it reaches the ledger - and only ever downward.
        # A rival it could not stand up leaves the premise untouched, because "no
        # evidence for the rival" is not evidence for the incumbent.
        if res.get("rival_mode"):
            verdict = as_rival_verdict(res["update"])
            if verdict is None:
                log.note(f"{vid} on {p.id}: rival not stood up — {p.id} keeps {was} "
                         "(not confirmed by it)")
                out.append(
                    f"--- {vid} | RIVAL TEST for {p.id} | the rival was NOT stood up. "
                    f"{p.id} keeps {was}. Read this narrowly: an independent reader "
                    "went looking for what would make the rival true and did not find "
                    "it. That is not proof your selection is right — nobody has "
                    "argued for it — it only means the rival did not displace it.")
                continue
        else:
            verdict = as_refutation(res["update"])
        notes = ledger.apply([verdict], author=vid, corpus=res["corpus"],
                             round_n=round_n)
        if notes:
            log.note(f"{vid} on {p.id}: ledger refused the verdict — {notes[0]}")
            out.append(f"--- {vid} | validated {p.id} | verdict refused by the runner. "
                       f"{p.id} keeps {was}.")
            continue
        log.note(f"{vid} on {p.id}: {was} -> {p.status}"
                 + (" (via rival test)" if res.get("rival_mode") else ""))
        shown = ("the RIVAL reading of this premise, in its own words, and nothing "
                 "else — it was never told what it was arguing against"
                 if res.get("rival_mode") else
                 "this claim and the evidence offered for it, and nothing else — not "
                 "the question, not the reports, not the candidate")
        out.append(
            f"--- {vid} | INDEPENDENT VALIDATION of {p.id} | {was} -> {p.status}\n"
            f'Premise: "{p.text}"\n'
            f"The validator was shown {shown}.\n"
            f"Its quote: {verdict.quote}\n"
            f"Its reason: {verdict.evidence}")
    return out


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
