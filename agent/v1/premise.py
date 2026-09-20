#!/usr/bin/env python3
"""
The premise ledger (spec 1, v1.5).

A senior's premises used to live in its report's "## Assumptions" section as
prose, read by five regexes. v1.4.2's Q216 was lost to that: s1 flagged the 3333
flow's byte profile as download-like and UNVERIFIED in rounds 1 and 2, SH
commanded a restate-only round, and round 3 came back all-VERIFIED with the line
simply gone. A regex cannot tell a premise that was settled from one that was
dropped, and `carry_doubts`/`_label` matched premises by their first four words.

So the RUNNER owns the list. The senior emits new premises and id-keyed updates
and never the list itself, which makes dropping one structurally impossible
rather than merely discouraged, and makes the premise text immutable once filed.

A status only reaches VERIFIED or REFUTED with a quote the runner finds in a
tool result the author actually received (`quote_supported`) - the senior-side
equivalent of the rule that stops SH citing itself.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field

STATUSES = ("UNVERIFIED", "VERIFIED", "REFUTED")
KINDS = ("coverage", "selection", "definition", "other")

# Shorter than this and a "quote" matches almost any text. Moved here from
# conversation.py so conversation can import from premise without a cycle.
MIN_QUOTE_CHARS = 12


def _norm(text: str) -> str:
    """Whitespace-, case- and markdown-insensitive form, so a faithful quote matches."""
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", text or "")).strip().lower()


class PremiseDraft(BaseModel):
    """A premise as its author files it. No id and no status: both are the runner's."""

    text: str = Field(description="The premise, in one sentence. Immutable once filed.")
    kind: Literal["coverage", "selection", "definition", "other"] = Field(
        description="'coverage': the ways the question's concept could show up in the "
                    "data. 'selection': why this entity and not another candidate. "
                    "'definition': what the question's words mean for the measurement. "
                    "'other': anything else your conclusion or next step rests on.")
    load_bearing: bool = Field(
        description="True when the answer breaks if this premise is false. Be honest: "
                    "marking everything load-bearing is the same as marking nothing.")


class PremiseUpdate(BaseModel):
    """A settled (or unsettled) verdict on a premise already in the ledger."""

    id: str = Field(description="The premise id, e.g. 'p3'. Copy it exactly.")
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"] = Field(
        description="VERIFIED: a result you ran shows it holds. REFUTED: a result you "
                    "ran shows it is false. UNVERIFIED: you are withdrawing a previous "
                    "verdict.")
    quote: str = Field(description="VERIFIED/REFUTED: the query output that settles it, "
                                   "copied word for word. The runner checks it against "
                                   "results you actually received.")
    evidence: str = Field(description="Why that quote settles it. For UNVERIFIED, what "
                                      "would test it.")


class Premise(BaseModel):
    """One premise in the ledger. `text` never changes after it is filed."""

    id: str
    author: str
    kind: Literal["coverage", "selection", "definition", "other"]
    text: str
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"] = "UNVERIFIED"
    load_bearing: bool = False
    round_first_seen: int = 0
    verified_by: str = ""
    quote: str = ""
    evidence: str = ""
    history: list[dict] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    """A senior's question for SH, addressable by id so an answer cannot be miscounted."""

    id: str
    author: str
    text: str
    answer: str = ""
    round_asked: int = 0


def quote_supported(quote: str, corpus: list) -> bool:
    """Does this quote appear, word for word, in something the author actually received?

    The senior-side equivalent of the rule that stops SH citing its own instruction
    as evidence. Without it a senior can assert VERIFIED with nothing behind it and
    only SH's judgement stands between that and an answer - which is what happened
    on Q216.
    """
    q = _norm(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return False
    return any(q in _norm(chunk) for chunk in corpus or [])


class PremiseLedger:
    """Every premise on one question, for every author. One instance per question.

    Ids are global to the question, not per senior: cross-author verification is
    allowed (a sibling senior may settle a premise another filed), so an id has
    to mean the same thing to everyone reading it.
    """

    def __init__(self):
        self.premises: dict[str, Premise] = {}
        self.questions: dict[str, OpenQuestion] = {}
        self.candidates: dict[str, dict[int, str]] = {}   # author -> round -> value
        self._n = 0
        self._qn = 0

    # -- filing ---------------------------------------------------------------
    def add(self, drafts: list, author: str, round_n: int) -> list[Premise]:
        """File new premises. The runner assigns ids and stamps the round."""
        out = []
        for d in drafts or []:
            self._n += 1
            p = Premise(id=f"p{self._n}", author=author, kind=d.kind, text=d.text,
                        load_bearing=bool(d.load_bearing), round_first_seen=round_n,
                        history=[{"round": round_n, "status": "UNVERIFIED",
                                  "by": author, "quote": ""}])
            self.premises[p.id] = p
            out.append(p)
        return out

    def ask(self, texts: list, author: str, round_n: int) -> list[OpenQuestion]:
        """File a senior's open questions, each addressable by id."""
        out = []
        for t in texts or []:
            if not str(t).strip():
                continue
            self._qn += 1
            q = OpenQuestion(id=f"q{self._qn}", author=author, text=str(t).strip(),
                             round_asked=round_n)
            self.questions[q.id] = q
            out.append(q)
        return out

    def record_candidate(self, author: str, round_n: int, value: str) -> None:
        """What this author's candidate was at this round.

        Spec 2's trigger is "load-bearing premise unverified for N rounds AND the
        candidate unchanged", which is unrecoverable from the reports afterwards.
        Recorded here so the ledger dump can answer it.
        """
        self.candidates.setdefault(author, {})[round_n] = value or ""

    # -- reading --------------------------------------------------------------
    def unresolved_for(self, author: str) -> list[Premise]:
        """This author's premises that are not VERIFIED, oldest first."""
        return [p for p in self.premises.values()
                if p.author == author and p.status != "VERIFIED"]

    def blocking(self) -> list[Premise]:
        """Load-bearing premises that are not VERIFIED - the ones that gate an ANSWER."""
        return [p for p in self.premises.values()
                if p.load_bearing and p.status != "VERIFIED"]

    def refuted(self) -> list[Premise]:
        return [p for p in self.premises.values() if p.status == "REFUTED"]

    def open_questions_for(self, author: str) -> list[OpenQuestion]:
        return [q for q in self.questions.values()
                if q.author == author and not q.answer.strip()]

    # -- transitions ------------------------------------------------------------
    def apply(self, updates: list, author: str, corpus: list, round_n: int) -> list[str]:
        """Apply this round's verdicts. Returns a note per REJECTED update.

        A senior round cannot be rejected mid-flight the way an SH turn can, so a
        bad update is dropped rather than raised: the premise keeps its old status
        and the note goes into the report SH reads. The effect on the gates is the
        same as if the update had never been sent.
        """
        notes = []
        for u in updates or []:
            p = self.premises.get(u.id)
            if p is None:
                notes.append(f"update ignored: {u.id} is not a premise on this question")
                continue
            if p.status == "REFUTED":
                notes.append(f"update ignored: {u.id} is REFUTED, which is final")
                continue
            if u.status in ("VERIFIED", "REFUTED") and not quote_supported(u.quote, corpus):
                notes.append(
                    f"{u.id} stays {p.status}: its quote is in no result you ran - "
                    "copy the query output that shows it word for word")
                continue
            p.status = u.status
            p.evidence = u.evidence
            if u.status == "UNVERIFIED":
                p.verified_by, p.quote = "", ""
            else:
                p.verified_by, p.quote = author, u.quote
            p.history.append({"round": round_n, "status": u.status,
                              "by": author, "quote": u.quote})
        return notes

    def answer(self, question_id: str, text: str) -> bool:
        """Record SH's answer to one open question. False when the id is unknown."""
        q = self.questions.get(question_id)
        if q is None:
            return False
        q.answer = text
        return True

    # -- rendering ------------------------------------------------------------
    def render_for_senior(self, author: str) -> str:
        """The unresolved premises this author owns, verbatim, for its next round.

        Carried by the runner unconditionally. The v1.4.2 equivalent fired only
        when SH graded R4 WEAK or FAIL - and SH grades all-PASS when it wants to
        answer. The runner has no candidate and no preference.
        """
        open_ = self.unresolved_for(author)
        if not open_:
            return ""
        lines = ["YOUR UNRESOLVED PREMISES - carried forward by the runner, "
                 "in your own words:"]
        for p in open_:
            tag = "load-bearing, " if p.load_bearing else ""
            state = ", REFUTED" if p.status == "REFUTED" else ""
            lines.append(f'[{p.id}] {tag}open since round {p.round_first_seen}'
                         f'{state} - "{p.text}"')
        lines.append("\nSettle each with `premise_updates`: a status, and a quote from "
                     "a result you actually ran. Not mentioning one does not remove it.")
        return "\n".join(lines)

    def render_table(self) -> str:
        """The whole ledger, for SH. Replaces the three '!!' warning blocks - a
        missing Coverage row is visible as absence."""
        if not self.premises:
            return "PREMISE LEDGER - no premises filed yet."
        rows = ["PREMISE LEDGER",
                f"{'id':<4} {'kind':<11} {'status':<11} {'LB':<3} {'since':<6} text"]
        for p in self.premises.values():
            by = f"  [{p.verified_by}]" if p.verified_by else ""
            rows.append(f"{p.id:<4} {p.kind:<11} {p.status:<11} "
                        f"{'Y' if p.load_bearing else 'n':<3} r{p.round_first_seen:<5} "
                        f"{p.author}: {p.text[:70]}{by}")
        return "\n".join(rows)

    def render_refuted(self) -> str:
        """What a replacement senior must not rebuild on. Empty when nothing is refuted.

        ponytail: no caller until spec 2's alternative-agent brief. Four lines, and
        the ledger already holds everything it needs - delete it if spec 2 slips.
        """
        dead = self.refuted()
        if not dead:
            return ""
        lines = ["PREMISES ALREADY DISPROVEN - do not rebuild on these:"]
        for p in dead:
            lines.append(f'[{p.id}] REFUTED by {p.verified_by} - "{p.text}"')
            lines.append(f'     disproven by: {p.quote}')
        lines.append("\nA line of reasoning that needs one of these to be true is "
                     "already known wrong.")
        return "\n".join(lines)
