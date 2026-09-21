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

KINDS = ("coverage", "selection", "other")

# Shorter than this and a "quote" matches almost any text. Lives here rather than
# in conversation.py so that module can import it without a cycle.
MIN_QUOTE_CHARS = 12

# A quote that cites SH is SH's own claim coming back as evidence. v1.4.2 Q216:
# SH told s1 the attribution was settled, s1 wrote "established by SH outside this
# feed", and SH quoted that sentence as the evidence for its VERIFIED line.
#
# Lives here, not in conversation.py, because the gate alone is not enough: the
# runner writes the ledger BEFORE the gates run (so SH can cite an id it just
# filed), and a rejected turn is not rolled back. A check that only the gate knows
# about flips the status, gets the turn rejected, and leaves the laundered VERIFIED
# standing for the re-issued turn. `apply` has to refuse it too.
CIRCULAR = re.compile(r"\b(established|confirmed|settled|told|instructed)\b"
                      r"[^.]{0,60}\bSH\b|\bper SH\b|\bSH (?:said|states?|instruction)",
                      re.IGNORECASE)


def is_validator(author: str) -> bool:
    """Was this verdict reached by an independent validator (v1.4.3)?

    The distinction the ANSWER gate turns on. An author refuting its own premise is
    healthy investigation - Q216 r1's s1 filed the iexeplorer.exe lead and killed it
    itself the next round. A VALIDATOR's refutation means the party that wanted the
    answer was overruled by one that wanted nothing, and the chain is broken until
    something independent says otherwise.
    """
    return bool(re.fullmatch(r"v\d+", author or ""))


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
    kind: Literal["coverage", "selection", "other"] = Field(
        description="'coverage': the ways the question's concept could show up in the "
                    "data. 'selection': why this entity and not another candidate. "
                    "'other': anything else your conclusion or next step rests on.")
    load_bearing: bool = Field(
        description="True when the answer breaks if this premise is false. Be honest: "
                    "marking everything load-bearing is the same as marking nothing.")
    rival: str = Field(
        default="",
        description="Required on a 'selection' premise: at least one OTHER record set "
                    "that could fit the question and that you are claiming this one "
                    "beats, and the query that ruled it out. A selection naming no "
                    "rival is a first match, not a choice.")
    quote: str = Field(
        default="",
        description="Leave empty when you are filing a hypothesis. When a result you "
                    "ALREADY have settles it, put that output here word for word and "
                    "the runner files it VERIFIED in one step - you do not have to wait "
                    "a round for its id. The same checks apply as for `premise_updates`.")
    evidence: str = Field(
        default="",
        description="Required with `quote`: why that output settles this premise.")


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
    kind: Literal["coverage", "selection", "other"]
    text: str
    status: Literal["UNVERIFIED", "VERIFIED", "REFUTED"] = "UNVERIFIED"
    load_bearing: bool = False
    rival: str = ""
    round_first_seen: int = 0
    verified_by: str = ""
    quote: str = ""
    evidence: str = ""
    stamp: Literal["", "true", "false"] = ""
    stamp_reason: str = ""
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
    def add(self, drafts: list, author: str, round_n: int,
            corpus: list[str] | None = None,
            notes: list[str] | None = None) -> list[Premise]:
        """File new premises. The runner assigns ids and stamps the round.

        Two things stop the same claim being filed twice.

        Deduped by (author, matched text): the carry-forward block hands a senior
        its own open premises back every round, so it re-filing the same one
        verbatim is the expected case, not an edge case. Without this, the
        re-filed copy gets a second id and settling the first never closes the
        second, so it stays open forever. A different author filing the same
        text is cross-author agreement, which is meaningful, so it still gets
        its own id.

        And one OPEN premise per kind per author. Text dedupe alone was not
        enough: in the Q216 ledger run SH filed the same coverage/selection/
        definition triplet six times (18 ids for 3 claims, no answer, $2.03),
        rewording each time - "the only flow in the feed matching Monero stratum
        behavior" became "the single dp=3333 stratum flow" - which `_match_form`
        reads as two different premises. The kinds are singular by construction
        (the prompt asks for *a* coverage premise, *a* selection premise, *a*
        definition premise), so a second open one of a kind is a re-file, not a
        new claim. Once the first is settled the kind is free again.

        `corpus` enables filing and settling in one step. The runner owns the
        ids, so an author cannot name a premise it is filing *this* turn in
        `premise_updates`; the auto-link then makes that premise an immediate
        load-bearing blocker on the very ANSWER that filed it. A draft carrying
        its own quote breaks that deadlock and weakens nothing, because the quote
        runs the same corpus and circularity checks `apply` runs.

        Absorption into an existing open premise of the same kind is reported back
        in `notes`, naming the id it was folded into - the draft's text is
        discarded there, and an author never told believes it filed a claim that
        does not exist. Re-filing the exact same text stays silent: the
        carry-forward block hands a senior its own open premises back every
        round, so that case is expected, not an error.
        """
        out = []
        for d in drafts or []:
            rival = (getattr(d, "rival", "") or "").strip()
            if d.kind == "selection" and not rival:
                if notes is not None:
                    notes.append(
                        "selection premise not filed: name in `rival` at least one other "
                        "record set that could fit and that this one beats, with the "
                        "query that ruled it out - a selection naming no rival is a "
                        f'first match, not a choice. Your text: "{d.text[:80]}"')
                continue
            key = _match_form(d.text)
            same_text = next((p for p in self.premises.values()
                              if p.author == author and _match_form(p.text) == key), None)
            if same_text is not None:
                # The carry-forward block hands a senior its own open premises back
                # every round, so re-filing one verbatim is expected, not an error.
                out.append(same_text)
                continue
            open_of_kind = next((p for p in self.premises.values()
                                 if p.author == author and p.kind == d.kind
                                 and p.status == "UNVERIFIED"), None)
            if open_of_kind is not None:
                # No silent absorption. The draft's text is discarded here, and an
                # author never told that believes it filed a claim that does not exist.
                if notes is not None:
                    notes.append(
                        f"{d.kind} premise not filed: you already have an open {d.kind} "
                        f"premise {open_of_kind.id} - amend or settle that one. The text "
                        f'you sent was discarded: "{d.text[:80]}"')
                out.append(open_of_kind)
                continue
            self._n += 1
            p = Premise(id=f"p{self._n}", author=author, kind=d.kind, text=d.text,
                        load_bearing=bool(d.load_bearing), rival=rival,
                        round_first_seen=round_n,
                        history=[{"round": round_n, "status": "UNVERIFIED",
                                  "by": author, "quote": "", "evidence": ""}])
            self.premises[p.id] = p
            out.append(p)
            quote = getattr(d, "quote", "")
            if quote:
                refused = self.apply(
                    [PremiseUpdate(id=p.id, status="VERIFIED", quote=quote,
                                   evidence=getattr(d, "evidence", ""))],
                    author=author, corpus=corpus or [], round_n=round_n)
                if notes is not None:
                    notes.extend(refused)
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

    def unstamped(self, author: str | None = None) -> list[Premise]:
        """Verifications by a SENIOR that SH has not yet read against their quote.

        Not a validator's: the validator is what outranks the stamp, not something for
        SH to grade. Not SH's own either - it files no verdicts any more.
        """
        return [p for p in self.premises.values()
                if p.status == "VERIFIED" and not p.stamp
                and p.verified_by and p.verified_by != "sh"
                and not is_validator(p.verified_by)
                and (author is None or p.verified_by == author)]

    def false_stamped(self, author: str) -> list[Premise]:
        """Premises this senior claimed VERIFIED and SH read as not establishing them.

        Keyed on `verified_by`, not `author`: the stamp is on the CLAIM, and a senior
        that settles a sibling's premise is the party that claimed it.
        """
        return [p for p in self.premises.values()
                if p.stamp == "false" and p.verified_by == author]

    def nominatable(self, author: str) -> list[Premise]:
        """What SH may point a validator at once it has stamped one of this senior's
        verifications false: what it stamped false, or what this senior left open.

        It may not range wider. The false stamp is what fired the mechanism, so letting
        SH aim the validator elsewhere would retire the senior and leave the triggering
        doubt unexamined.
        """
        by_id = {p.id: p for p in self.false_stamped(author)}
        by_id.update({p.id: p for p in self.premises.values()
                      if p.author == author and p.status == "UNVERIFIED"})
        return sorted(by_id.values(), key=lambda p: int(p.id[1:]))

    def open_questions_for(self, author: str) -> list[OpenQuestion]:
        return [q for q in self.questions.values()
                if q.author == author and not q.answer.strip()]

    # -- transitions ------------------------------------------------------------
    def apply(self, updates: list, author: str, corpus: list, round_n: int) -> list[str]:
        """Apply this round's verdicts. Returns a note per REJECTED update.

        Only a senior or a validator settles anything: an update authored by "sh" is
        refused whatever it says, because SH has no Splunk access and never will.

        A senior round cannot be rejected mid-flight the way an SH turn can, so a
        bad update is dropped rather than raised: the premise keeps its old status
        and the note goes into the report SH reads. The effect on the gates is the
        same as if the update had never been sent.
        """
        notes = []
        for u in updates or []:
            if author == "sh":
                # SH has no Splunk access, so "SH verified it" has only ever meant "SH
                # read a report and decided". That reading is the stamp, which is an
                # annotation, costs a senior slot when it is false, and is on the
                # record. r1: SH settled 19 of 28 premises, including the triplet that
                # lost the question.
                notes.append(
                    f"{u.id} unchanged: SH does not settle premises. Your reading of a "
                    "senior's verification goes in `premise_stamps`; a premise reaches "
                    "VERIFIED from the senior whose search shows it, or from an "
                    "independent validator.")
                continue
            p = self.premises.get(u.id)
            if p is None:
                notes.append(f"update ignored: {u.id} is not a premise on this question")
                continue
            if p.status == "REFUTED":
                notes.append(f"update ignored: {u.id} is REFUTED, which is final")
                continue
            if u.status in ("VERIFIED", "REFUTED") and CIRCULAR.search(u.quote or ""):
                notes.append(
                    f"{u.id} stays {p.status}: that quote cites SH as the authority - "
                    "an instruction is not evidence. Quote the query or result.")
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

    def stamp_premise(self, pid: str, *, establishes: bool, reason: str,
                      round_n: int) -> bool:
        """Record SH's reading of one newly-claimed verification. False when the id is
        unknown or already stamped - a stamp is recorded once, when the verification is
        first claimed.

        An annotation, never an edit: the status is untouched. A false-stamped premise
        stays VERIFIED, because status belongs to the quote rule and the validator,
        while the stamp is SH's reading of it.
        """
        p = self.premises.get(pid)
        if p is None or p.stamp:
            return False
        p.stamp = "true" if establishes else "false"
        p.stamp_reason = reason
        p.history.append({"round": round_n, "status": p.status, "by": "sh-stamp",
                          "quote": "", "evidence": f"stamp={p.stamp}: {reason}"})
        return True

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
        `render_refuted()` is rendered at the head of this block, for EVERY senior and
        not only a replacement: before this it had no caller at all, so no senior was
        ever told which premises were dead.
        """
        open_ = [p for p in self.unresolved_for(author) if p.status == "UNVERIFIED"]
        # Premises someone else filed that this senior is expected to settle. Without
        # these the gate's "COMMAND s1 to settle them" names an action s1 cannot take:
        # it has never seen the premise and does not know the id exists. The Q216 ledger
        # run settled 0 premises senior-to-senior for exactly this reason, while SH
        # verified all 15 of its own. Only load-bearing and still open - anything else
        # is noise in a senior's round.
        others = [p for p in self.premises.values()
                  if p.author != author and p.load_bearing and p.status == "UNVERIFIED"]
        dead = self.render_refuted()
        if not open_ and not others and not dead:
            return ""
        lines = []
        if dead:
            lines.append(dead)
        if open_:
            if lines:
                lines.append("")
            lines.append("YOUR UNRESOLVED PREMISES - carried forward by the runner, "
                         "in your own words:")
            for p in open_:
                tag = "load-bearing, " if p.load_bearing else ""
                lines.append(f'[{p.id}] {tag}open since round {p.round_first_seen}'
                             f' - "{p.text}"')
            lines.append("\nSettle each with `premise_updates`: a status, and a quote "
                         "from a result you actually ran. Not mentioning one does not "
                         "remove it.")
        if others:
            if lines:
                lines.append("")
            lines.append("LOAD-BEARING PREMISES FILED BY OTHERS, still unsettled. The "
                         "answer to this question rests on these, and whoever filed one "
                         "cannot settle it from your searches:")
            for p in others:
                lines.append(f'[{p.id}] by {p.author}, open since round '
                             f'{p.round_first_seen} - "{p.text}"')
            lines.append("\nIf a result you ran settles one, say so in `premise_updates` "
                         "by its id - the same quote rule applies. If your work cannot "
                         "reach it, leave it alone.")
        return "\n".join(lines)

    def render_table(self) -> str:
        """The whole ledger, for SH. Replaces the three '!!' warning blocks - a
        missing Coverage row is visible as absence."""
        if not self.premises:
            return "PREMISE LEDGER - no premises filed yet."
        rows = ["PREMISE LEDGER",
                f"{'id':<4} {'kind':<10} {'status':<11} {'LB':<3} {'stamp':<6} "
                f"{'since':<6} who / text"]
        for p in self.premises.values():
            by = f"[{p.verified_by}] " if p.verified_by else ""
            text = p.text if len(p.text) <= 70 else p.text[:70] + "…"
            rows.append(f"{p.id:<4} {p.kind:<10} {p.status:<11} "
                        f"{'Y' if p.load_bearing else 'n':<3} {p.stamp or '-':<6} "
                        f"r{p.round_first_seen:<5} {by}{p.author}: {text}")
        return "\n".join(rows)

    def render_refuted(self) -> str:
        """What a senior must not rebuild on. Empty when nothing is refuted.

        Carried into every senior's round by `render_for_senior`, and into a
        replacement's first instruction by `sh_loop._spawn_directive`. SH does not
        write this and cannot soften it.
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

        `rival` is carried here for the same reason it exists at all: it holds the
        second live record set, so a losing candidate is recorded as data instead of
        staying prose in a report where it can be argued away. Left out of the dump
        it would be unreadable in exactly the post-run analysis it serves.
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
            "rival": p.rival,
            "stamp": p.stamp,
            "stamp_reason": p.stamp_reason,
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
