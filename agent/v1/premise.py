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

KINDS = ("coverage", "selection", "definition", "other")

# Shorter than this and a "quote" matches almost any text. Will move to
# conversation.py in a later task, once conversation can import it without a cycle.
MIN_QUOTE_CHARS = 12


def _norm(text: str) -> str:
    """Whitespace-, case- and markdown-insensitive form, so a faithful quote matches.

    Exported for a later task's import - do not delete even though `quote_supported`
    below no longer uses it.
    """
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", text or "")).strip().lower()


def _match_form(text: str) -> str:
    """Alphanumeric runs only, lowercased, single-spaced.

    What a senior receives is JSON (`splunk_agent._format_result` returns
    `json.dumps({"results": ..., "meta": ...})`), and what it writes back is
    usually the same fact in its own punctuation - `dest_port=3333` for
    `"dest_port": "3333"`. Both carry the same evidence, so the check compares
    the words and the numbers and ignores what sits between them. The length
    floor is what stops that looseness matching everything.
    """
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


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
    """Does this quote's evidence appear in something the author actually received?

    This checks provenance, not proof: that the author saw this fact somewhere in
    its own tool output, not that the fact settles the premise (that is `evidence`'s
    job). The senior-side equivalent of the rule that stops SH citing its own
    instruction as evidence. Without it a senior can assert VERIFIED with nothing
    behind it and only SH's judgement stands between that and an answer - which is
    what happened on Q216.
    """
    q = _match_form(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return False
    return any(q in _match_form(chunk) for chunk in corpus or [])


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
        """File new premises. The runner assigns ids and stamps the round.

        Deduped by (author, matched text): the carry-forward block hands a senior
        its own open premises back every round, so it re-filing the same one
        verbatim is the expected case, not an edge case. Without this, the
        re-filed copy gets a second id and settling the first never closes the
        second, so it stays open forever. A different author filing the same
        text is cross-author agreement, which is meaningful, so it still gets
        its own id.
        """
        out = []
        for d in drafts or []:
            key = _match_form(d.text)
            existing = next((p for p in self.premises.values()
                             if p.author == author and _match_form(p.text) == key), None)
            if existing is not None:
                out.append(existing)
                continue
            self._n += 1
            p = Premise(id=f"p{self._n}", author=author, kind=d.kind, text=d.text,
                        load_bearing=bool(d.load_bearing), round_first_seen=round_n,
                        history=[{"round": round_n, "status": "UNVERIFIED",
                                  "by": author, "quote": "", "evidence": ""}])
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
            if u.status in ("VERIFIED", "REFUTED") and not u.evidence.strip():
                notes.append(f"{u.id} stays {p.status}: say why that quote settles "
                             "it in `evidence`")
                continue
            same_status = u.status == p.status
            p.status = u.status
            p.evidence = u.evidence
            if u.status == "UNVERIFIED":
                p.verified_by, p.quote = "", ""
            else:
                p.verified_by, p.quote = author, u.quote
            # A restated identical verdict doesn't get a new history entry: spec 2
            # counts rounds UNVERIFIED by reading `history`, and a senior restating
            # the same status every round (which the carry-forward block invites)
            # would inflate that count without anything having actually changed.
            if not same_status:
                p.history.append({"round": round_n, "status": u.status,
                                  "by": author, "quote": u.quote, "evidence": u.evidence})
        return notes

    def answer(self, question_id: str, text: str) -> bool:
        """Record SH's answer to one open question.

        False when the id is unknown, or when `text` is blank/whitespace: a
        whitespace-only answer still leaves `open_questions_for` counting the
        question as open (it strips before checking), so this must agree or a
        caller could believe it closed something that is still open.
        """
        q = self.questions.get(question_id)
        if q is None or not text.strip():
            return False
        q.answer = text
        return True

    # -- rendering ------------------------------------------------------------
    def render_for_senior(self, author: str) -> str:
        """This author's still-open (UNVERIFIED) premises, verbatim, for its next round.

        Carried by the runner unconditionally. The v1.4.2 equivalent fired only
        when SH graded R4 WEAK or FAIL - and SH grades all-PASS when it wants to
        answer. The runner has no candidate and no preference.

        Only UNVERIFIED, not `unresolved_for` (which also includes REFUTED):
        `apply()` refuses every update to a REFUTED premise, so listing one here
        and then telling the senior to "settle" it tells it to do something that
        is rejected every time, and the rejection note lands in SH's report.
        `render_refuted()` already tells the senior which premises are dead.
        """
        open_ = [p for p in self.unresolved_for(author) if p.status == "UNVERIFIED"]
        if not open_:
            return ""
        lines = ["YOUR UNRESOLVED PREMISES - carried forward by the runner, "
                 "in your own words:"]
        for p in open_:
            tag = "load-bearing, " if p.load_bearing else ""
            lines.append(f'[{p.id}] {tag}open since round {p.round_first_seen}'
                         f' - "{p.text}"')
        lines.append("\nSettle each with `premise_updates`: a status, and a quote from "
                     "a result you actually ran. Not mentioning one does not remove it.")
        return "\n".join(lines)

    def render_table(self) -> str:
        """The whole ledger, for SH. Replaces the three '!!' warning blocks - a
        missing Coverage row is visible as absence."""
        if not self.premises:
            return "PREMISE LEDGER - no premises filed yet."
        rows = ["PREMISE LEDGER",
                f"{'id':<4} {'kind':<11} {'status':<11} {'LB':<3} {'since':<6} who / text"]
        for p in self.premises.values():
            by = f"[{p.verified_by}] " if p.verified_by else ""
            text = p.text if len(p.text) <= 70 else p.text[:70] + "…"
            rows.append(f"{p.id:<4} {p.kind:<11} {p.status:<11} "
                        f"{'Y' if p.load_bearing else 'n':<3} r{p.round_first_seen:<5} "
                        f"{by}{p.author}: {text}")
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

    def to_records(self, qid: str) -> list[dict]:
        """One JSON-serialisable record per premise, for `premise_ledger.json`.

        The HISTORY is the point, not the end state. Spec 2's validation-agent
        trigger is "load-bearing, UNVERIFIED for N rounds, candidate unchanged" -
        a report shows only where a premise finished, so without this the single
        reading that decides whether that trigger is aimed correctly is lost.
        """
        return [{
            "qid": qid,
            "senior": p.author,
            "id": p.id,
            "kind": p.kind,
            "text": p.text,
            "load_bearing": p.load_bearing,
            "round_first_seen": p.round_first_seen,
            "status": p.status,
            "verified_by": p.verified_by,
            "evidence": p.evidence,
            "history": list(p.history),
            "candidate_at_each_round": {str(r): v for r, v
                                        in sorted(self.candidates
                                                  .get(p.author, {}).items())},
        } for p in self.premises.values()]


def dump_ledgers(path: str, ledgers: dict) -> None:
    """Write every question's ledger to one file. `ledgers` maps qid -> PremiseLedger."""
    records = [r for qid, led in ledgers.items() for r in led.to_records(qid)]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
