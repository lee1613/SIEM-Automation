#!/usr/bin/env python3
"""
One live Senior, for the life of one question (spec §2.3, §6, §7).

The session owns what has to survive between rounds and what must not be
self-reported: the thread id, the round counter, the set of SPL already run, and
the context projection that decides whether to compact BEFORE working.

Compacting at the start of a round guarantees the senior has room for the whole
round rather than discovering mid-round that it does not. And it needs no new
prompt: the senior's own latest report is already the compressed state — that is
what the "Prior rounds" section was designed for — so the rebuilt thread is a
fresh thread_id seeded with [latest report, current directive]. The graph
prepends the system prompt on every call, so that IS
[system prompt, latest report, current directive] with the transcript dropped.
"""

from __future__ import annotations

import uuid

from question_state import ROUND_ITERS
from senior_report import (
    _norm_query,
    novel_spl,
    report_violations,
    stamp_header,
    truncate_words,
)

COMPACT_AT = 0.80    # projected context share that triggers a compaction
ALERT_AT   = 0.70    # current context share that prints an operator alert


def unseen_rows_note(truncated: list[str]) -> str:
    """The runner's record of results this round that were cut short. The senior
    got the tool's warning each time; this makes the gap impossible to report away."""
    if not truncated:
        return ""
    shown = "; ".join(truncated[:6]) + (f"; +{len(truncated) - 6} more" if len(truncated) > 6 else "")
    return (f"_Partial results (runner): {len(truncated)} result(s) this round returned "
            "only their first rows — " + shown + ". They say nothing about the rows "
            "they did not return, so Coverage resting on them alone is UNVERIFIED. To "
            "reach them, narrow the query with what the question tells you, or open up "
            "one step at a time._")


def should_compact(current_context: int, *, mean_per_iter: int, window: int,
                   iters: int = ROUND_ITERS) -> bool:
    """Would a full round of growth push this thread past 80% of its window?"""
    return (current_context + iters * max(0, mean_per_iter)) > COMPACT_AT * window


def should_alert(current_context: int, window: int) -> bool:
    """Is this thread already past 70% — worth an operator's attention?"""
    return current_context > ALERT_AT * window


class SeniorSession:
    """A question-scoped senior. One instance per spawn; never reused across questions."""

    def __init__(self, *, sid: str, pool, qid: str, technique: str,
                 subquestion: str, brief: str, window: int,
                 rounds_granted: int, idx: int = 0, constraints=None,
                 iters: int = ROUND_ITERS):
        self.sid = sid
        self.pool = pool
        self.qid = qid
        self.technique = technique or "senior"   # plain role: no SPECIALISTS prompt
        self.subquestion = subquestion
        self.brief = brief
        self.window = window
        self.rounds_granted = rounds_granted
        self.idx = idx or 1
        self.constraints = constraints
        self.iters = iters

        self.thread_id = self._new_thread()
        self.rounds_used = 0
        self.iterations = 0
        self.thread_iterations = 0
        self.compactions = 0
        self.prior_spl: set = set()
        self.spl_seen: dict = {}  # maps normalized query -> original spelling
        self.last_report = ""
        self.last_prompt_tokens = 0
        self.status = "active"
        self.briefed = False
        self.coverage_note = ""      # runner's partial-results note, relayed into the next round

    def _new_thread(self) -> str:
        return f"senior_{self.qid}_{self.sid}_{uuid.uuid4().hex[:8]}"

    @property
    def mean_tokens_per_iteration(self) -> int:
        """Measured, not assumed: this thread's context divided by the iterations
        that built it (per-thread only, not cumulative). ponytail: a flat average,
        not a growth curve — upgrade only if compaction starts firing late."""
        if self.thread_iterations <= 0:
            return 0
        return int(self.last_prompt_tokens / self.thread_iterations)

    # ── one round ─────────────────────────────────────────────────────────────
    def work(self, directive: str, *, rounds_remaining: int) -> dict:
        """Resume this senior for one round and return its stamped report."""
        message = self._message_for(directive)
        if self.coverage_note:
            message = f"{self.coverage_note}\n\n{message}"

        result = self.pool.run_round(
            thread_id=self.thread_id, message=message, qid=self.qid,
            idx=self.idx, technique=self.technique, max_iter=self.iters)

        self.rounds_used += 1
        round_iterations = int(result.get("iterations", 0))
        self.iterations += round_iterations
        self.status = result.get("status", "?")
        failed = self.status in ("api_failed", "runaway")

        # Track original SPL spelling
        for spl in (result.get("spl_used") or []):
            norm = _norm_query(spl)
            if norm and norm not in self.spl_seen:
                self.spl_seen[norm] = spl

        count, self.prior_spl = novel_spl(self.prior_spl, result.get("spl_used") or [])

        # Only update context and thread iterations on successful rounds
        if not failed:
            self.last_prompt_tokens = int(result.get("last_prompt_tokens", 0))
            self.thread_iterations += round_iterations

        # Single stamping path for both failed and successful rounds
        body, truncated = truncate_words(result.get("report") or self._fallback_report(result))
        if round_iterations >= self.iters:
            # Appended by the runner, after truncation, so SH always sees it: a
            # capped round's report is where the budget ran out, not a conclusion.
            body = (body.rstrip() + f"\n\n_Iteration cap reached: {self.iters}/{self.iters} "
                    "iterations used this round — cut off, not finished._\n")
        self.coverage_note = "" if failed else unseen_rows_note(result.get("truncated") or [])
        if self.coverage_note:
            body = body.rstrip() + f"\n\n{self.coverage_note}\n"
        report = stamp_header(body, senior_id=self.sid, qid=self.qid,
                              round_n=self.rounds_used,
                              rounds_remaining=rounds_remaining,
                              novel_spl_count=count)

        problems = report_violations(report)
        if truncated:
            problems.append("report truncated at the word cap")
        if problems:
            print(f"[{self.sid}] report template: {'; '.join(problems)}")

        # Only update last_report and alert on successful rounds
        if not failed:
            self.last_report = report
            if should_alert(self.last_prompt_tokens, self.window):
                print(f"[{self.sid}] context {self.last_prompt_tokens:,} is past "
                      f"{int(ALERT_AT * 100)}% of {self.window:,}")

        return {**result, "report": report, "novel_spl_count": count,
                "senior_id": self.sid, "round": self.rounds_used}

    def _render_spl_list(self) -> str:
        """Render the SPL already run with original spellings, sorted by normalized key."""
        if not self.spl_seen:
            return "- (none)"
        return "\n".join(f"- {self.spl_seen[norm]}"
                         for norm in sorted(self.spl_seen.keys()))

    def _message_for(self, directive: str) -> str:
        """The round's input: the brief on round one, a compaction seed when the
        projection says so, otherwise the bare directive."""
        if not self.briefed:
            self.briefed = True
            return f"{self.brief}\n\n## Your task\n{self.subquestion}\n\n## This round\n{directive}"

        if should_compact(self.last_prompt_tokens,
                          mean_per_iter=self.mean_tokens_per_iteration,
                          window=self.window, iters=self.iters):
            mean = self.mean_tokens_per_iteration
            self.thread_id = self._new_thread()
            self.thread_iterations = 0
            self.compactions += 1
            print(f"[{self.sid}] compacting: context {self.last_prompt_tokens:,} + "
                  f"{self.iters}x{mean:,} projected past "
                  f"{int(COMPACT_AT * 100)}% of {self.window:,}")
            spl_section = f"## SPL you already ran — do not repeat, go one step further\n{self._render_spl_list()}\n\n"
            return (f"{self.brief}\n\n## Your task\n{self.subquestion}\n\n"
                    f"## Where you got to (your own last report)\n{self.last_report}\n\n"
                    f"{spl_section}"
                    f"## This round\n{directive}")

        return directive

    def _fallback_report(self, result: dict) -> str:
        """A senior that skipped the `report` field still has to be readable."""
        return (f"**Insight:** {result.get('insight', 'NOT_FOUND')}\n"
                f"**Candidate:** {result.get('value') or 'none'}   "
                f"**Confidence:** {result.get('confidence')}\n\n"
                f"## This round\n### What I ran\n"
                + "\n".join(f"- {q}" for q in (result.get('spl_used') or [])[-4:])
                + f"\n### What it means\n{(result.get('notes') or '').strip()[:800]}\n")

    # ── clarify (§3.3) ────────────────────────────────────────────────────────
    def clarify(self, questions: list, preface: str = "") -> str:
        """No tools, no round. Only SH's turn budget bounds how often this happens.
        `preface` carries SH's answers to this senior's own open questions."""
        return self.pool.clarify(thread_id=self.thread_id, qid=self.qid, idx=self.idx,
                                 questions=list(questions), technique=self.technique,
                                 max_iter=self.iters, preface=preface)

    # ── retirement (§7) ───────────────────────────────────────────────────────
    def handoff(self, reason: str) -> str:
        """The report template plus what a replacement needs. Feeds the case file."""
        head = self.last_report or f"# {self.sid} - {self.qid} - no completed round\n"
        ruled = self._render_spl_list()
        return (f"{head}\n\n## What I'd tell my replacement\n"
                f"- Retired because: {reason}\n"
                f"- Scope I owned: {self.constraints or self.subquestion}\n"
                f"- Rounds worked: {self.rounds_used}/{self.rounds_granted}  "
                f"(iterations: {self.iterations}, compactions: {self.compactions})\n"
                f"- SPL already run — do not repeat these, go one step further:\n{ruled}\n")
