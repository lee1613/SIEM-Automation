#!/usr/bin/env python3
"""
SH's memory across a whole run (v0.4.5, docs/version_architecture/v0/v0.4.5.md).

Before this, SH replayed the last 24 messages of earlier questions, so after about a
question and a half everything older was simply gone. Now:

  * every finished question is summarized ONCE by a cheap model (gpt-5.4-mini) into a
    `QuestionMemory`, written to <run>/memory/<QID>.json and .md;
  * SH's prompt carries a card per past question and a size-capped knowledge block,
    always, plus the raw transcripts of past questions while they fit;
  * past the threshold (60% of gpt-5.4's 272K input) the oldest raw transcripts are
    swapped, whole question by whole question, for their detailed summaries. No model
    call happens at the swap, and a summary is never summarized again;
  * SH can RECALL any past question's summary, conversation, ledger or report in full.

The summarizer sees only what SH saw: the transcript, the ledger and the submitted
answer. Never the answer key or the scoreboard verdict (D3).
"""

from __future__ import annotations

import json
import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field, field_validator

MEMORY_THRESHOLD = 163_200    # D1: 60% of gpt-5.4's 272K input window
SWAP_TARGET = 0.75            # a swap brings the prompt down to this share of the threshold
KNOWLEDGE_CAP = 6_000         # tokens, all three knowledge lists together
RECALL_CAP = 8_000            # tokens returned by one RECALL
SPL_PER_SOURCETYPE = 3        # newest working searches kept per sourcetype
SUMMARIZER_MODEL = "gpt-5.4-mini"

RECALL_WHAT = re.compile(r"^(summary|conversation|ledger|report:[A-Za-z0-9_.-]+:\d+)$")

_ENC = None


def _enc():
    global _ENC
    if _ENC is None:
        import tiktoken
        _ENC = tiktoken.get_encoding("o200k_base")
    return _ENC


def count_tokens(text: str) -> int:
    """Exact count with tiktoken o200k (the GPT-5 encoding), not a character guess."""
    return len(_enc().encode(text or "", disallowed_special=()))


def _truncate(text: str, cap: int) -> tuple[str, bool]:
    toks = _enc().encode(text or "", disallowed_special=())
    if len(toks) <= cap:
        return text, False
    return _enc().decode(toks[:cap]), True


def _msgs_tokens(msgs) -> int:
    return sum(count_tokens(str(m.content)) for m in msgs)


def memory_dir(run_dir: str) -> str:
    return os.path.join(run_dir, "memory")


def log(run_dir: str, line: str) -> None:
    """D5: every memory step goes to the console AND to memory/compaction_log.md."""
    print(line)
    os.makedirs(memory_dir(run_dir), exist_ok=True)
    with open(os.path.join(memory_dir(run_dir), "compaction_log.md"), "a",
              encoding="utf-8") as fh:
        fh.write(line + "\n")


# ── the per-question memory ───────────────────────────────────────────────────

class Entity(BaseModel):
    key: str = Field(description="The identifier exactly as in the data: a host, IP, "
                                 "account, file, bucket.")
    fact: str = Field(description="What it is, e.g. '192.168.247.131, Bud Stoll's laptop'.")


class FeedFact(BaseModel):
    sourcetype: str = Field(description="The sourcetype (or source) the fact is about.")
    fact: str = Field(description="How the feed behaves or which field carries what.")


class WorkingSpl(BaseModel):
    sourcetype: str = Field(description="The sourcetype the search runs on.")
    purpose: str = Field(description="What the search establishes, in a few words.")
    spl: str = Field(description="The search, copied from a report's 'What I ran'.")
    returns: str = Field(description="What it returned.")


class Digest(BaseModel):
    """What the summarizer writes. The runner adds everything it can state exactly."""

    flow: list[str] = Field(
        description="4-6 steps from the question to the answer. Each says what was "
                    "found AND why that led to the next step. No numbering.")
    derivation: str = Field(
        description="Prose, first search to final value: which feeds, which pivots, "
                    "and why each choice was made.")
    entities: list[Entity] = Field(description="Durable identifiers this question established.")
    feed_facts: list[FeedFact] = Field(description="Feed and field behaviour this question established.")
    working_spl: list[WorkingSpl] = Field(description="One canonical search per finding.")
    ruled_out: str = Field(description="ONE line: the disproven paths, so they are not walked again.")

    @field_validator("flow")
    @classmethod
    def _has_a_flow(cls, v):
        steps = [s for s in v if s.strip()]
        if not steps:
            raise ValueError("a memory needs a flow: at least one step")
        return steps


class QuestionMemory(Digest):
    qid: str
    question: str
    guidance: str = ""
    answer: str
    verified_premises: list[str] = Field(default_factory=list)
    validator_verdicts: list[str] = Field(default_factory=list)


SUMMARY_PROMPT = """You write SH's long-term memory of ONE finished question in a threat-hunting investigation (Splunk index=botsv3, the Frothly compromise, August 2018). Later questions read your summary in place of the full transcript, so write what a later question can reuse.

You are given the question, the answer SH submitted, the premise ledger, and SH's whole transcript for the question: its own turns and every senior report it read.

KEEP ONLY WHAT HELD. The flow and the derivation follow the chain that led to the submitted answer and the facts established along the way. Leave out dead ends, abandoned leads and disproven premises; name them once, together, in `ruled_out`, so nobody walks them again. If SH gave no answer, the flow is what was established and where it stopped.

You are not told whether the answer is correct. Do not guess, and do not say.

Name hosts, IPs, accounts, files, sourcetypes and fields exactly as the transcript writes them. Copy searches from the reports' "What I ran" lines rather than writing new ones. State only what the transcript establishes."""


def _ledger_lines(ledger) -> tuple[list[str], list[str]]:
    """Verified premises and validator verdicts, read off the ledger - exact, so no
    model is asked to restate them."""
    if ledger is None:
        return [], []
    verified, verdicts = [], []
    for p in ledger.premises.values():
        if p.status == "VERIFIED":
            why = p.holds_reason or p.stamp_reason or "not stamped"
            verified.append(f"{p.id} [{p.kind}] {p.text} — holds: {why}")
        for h in p.history:
            if re.fullmatch(r"v\d+", h.get("by", "")):
                verdicts.append(f"{p.id} → {h['status']} by {h['by']}"
                                + (f" (rival tested: {p.rival})" if p.rival else ""))
    return verified, verdicts


def _transcript(messages) -> str:
    who = {AIMessage: "SH", HumanMessage: "RUNNER"}
    return "\n\n".join(f"[{who.get(type(m), 'SYSTEM')}] {m.content}" for m in messages)


def summarize_question(llm, *, run_dir: str, qid: str, question: str, guidance: str,
                       answer: str, transcript: list, ledger) -> QuestionMemory | None:
    """One structured-output call, once, when the question ends (D8).

    Returns None and logs why when the call fails: the question then stays in memory
    as a raw transcript only, which is what every question was before this version.
    """
    verified, verdicts = _ledger_lines(ledger)
    table = ledger.render_table() if ledger is not None else "(no ledger)"
    body = (f"QUESTION {qid}: {question}\nAnswer guidance: {guidance or '-'}\n"
            f"ANSWER SH SUBMITTED: {answer}\n\nPREMISE LEDGER:\n{table}\n\n"
            f"SH TRANSCRIPT:\n{_transcript(transcript)}")
    log(run_dir, f"[SH MEMORY] {qid} finished → summarizing with {SUMMARIZER_MODEL} "
                 f"({count_tokens(SUMMARY_PROMPT + body):,} tok in)")
    try:
        digest = llm.invoke([SystemMessage(content=SUMMARY_PROMPT),
                             HumanMessage(content=body)])
    except Exception as exc:                            # noqa: BLE001 - logged, not fatal
        log(run_dir, f"[SH MEMORY] {qid} summary FAILED ({type(exc).__name__}: "
                     f"{str(exc)[:200]}) — kept as a raw transcript only")
        return None
    mem = QuestionMemory(**digest.model_dump(), qid=qid, question=question,
                         guidance=guidance, answer=answer,
                         verified_premises=verified, validator_verdicts=verdicts)
    _write_memory(run_dir, mem)
    card, detail = render_card(mem), render_detail(mem)
    log(run_dir, f"[SH MEMORY] {qid} summary: {count_tokens(card + detail):,} tok "
                 f"(card {count_tokens(card):,}) → memory/{qid}.md")
    log(run_dir, f"[SH MEMORY]   +{len(mem.entities)} entities, +{len(mem.feed_facts)} "
                 f"feed facts, +{len(mem.working_spl)} SPL\n\n{render_markdown(mem)}\n")
    return mem


def _atomic(path: str, text: str) -> None:
    with open(path + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(path + ".tmp", path)


def _write_memory(run_dir: str, mem: QuestionMemory) -> None:
    d = memory_dir(run_dir)
    os.makedirs(d, exist_ok=True)
    _atomic(os.path.join(d, f"{mem.qid}.json"), mem.model_dump_json(indent=2))
    _atomic(os.path.join(d, f"{mem.qid}.md"), render_markdown(mem))


def load_memories(run_dir: str) -> dict[str, QuestionMemory]:
    """qid -> memory, oldest first.

    ponytail: ordered by file mtime, which is question order because each is written
    once when its question ends. A question re-run after a crash moves to the end."""
    d = memory_dir(run_dir)
    if not os.path.isdir(d):
        return {}
    files = [f for f in os.listdir(d) if re.fullmatch(r"Q\d+\.json", f)]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(d, f)))
    out = {}
    for f in files:
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            m = QuestionMemory.model_validate_json(fh.read())
        out[m.qid] = m
    return out


# ── rendering ─────────────────────────────────────────────────────────────────

def render_card(m: QuestionMemory) -> str:
    """D7: enough on its own that SH knows what the question found and whether to read on."""
    head = f'**{m.qid}** — "{m.question}"' + (f" ({m.guidance})" if m.guidance else "")
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(m.flow, start=1))
    return f"{head}\n**Answer: {m.answer}**\n{steps}"


def render_detail(m: QuestionMemory) -> str:
    lines = [f"### {m.qid} — detail", f"Derivation: {m.derivation}"]
    if m.verified_premises:
        lines += ["Verified premises:"] + [f"- {p}" for p in m.verified_premises]
    if m.validator_verdicts:
        lines += ["Validator verdicts:"] + [f"- {v}" for v in m.validator_verdicts]
    lines.append(f"Ruled out: {m.ruled_out}")
    return "\n".join(lines)


def render_markdown(m: QuestionMemory) -> str:
    """memory/<QID>.md: everything SH will remember about this question."""
    knowledge = _render_knowledge(_entries(merge_knowledge([m])))
    return f"{render_card(m)}\n\n{render_detail(m)}\n\n{knowledge}".rstrip() + "\n"


# ── knowledge blocks ──────────────────────────────────────────────────────────

def merge_knowledge(memories: list[QuestionMemory]) -> dict:
    """Three dicts, rebuilt from the memories in question order. Deterministic, no
    model call. A later question's entry for the same key replaces the earlier one;
    each value carries the position of the question that last wrote it.

    Feed facts are keyed on (sourcetype, fact) rather than sourcetype alone: two
    questions usually learn different things about one feed, and replacing would
    drop the first."""
    ents, feeds, spl = {}, {}, {}
    for n, m in enumerate(memories):
        for e in m.entities:
            ents[e.key.strip().lower()] = (f"{e.key}: {e.fact}", m.qid, n)
        for f in m.feed_facts:
            feeds[(f.sourcetype.lower(), f.fact.strip().lower())] = (
                f"[{f.sourcetype}] {f.fact}", m.qid, n)
        for s in m.working_spl:
            key = (s.sourcetype.lower(), s.purpose.strip().lower())
            spl.pop(key, None)                      # re-insert so the newest is last
            spl[key] = (f"[{s.sourcetype}] {s.purpose}: `{s.spl}` → {s.returns}", m.qid, n)
    for st in {k[0] for k in spl}:                  # keep the newest N per sourcetype
        for k in [k for k in spl if k[0] == st][:-SPL_PER_SOURCETYPE]:
            del spl[k]
    return {"Entities": ents, "Feed and field facts": feeds, "Working SPL": spl}


def _entries(k: dict) -> list[tuple[str, str, str, int]]:
    return [(section, text, qid, n) for section, d in k.items()
            for text, qid, n in d.values()]


def _render_knowledge(entries: list) -> str:
    out = []
    for section in ("Entities", "Feed and field facts", "Working SPL"):
        rows = [f"- {text} ({qid})" for s, text, qid, _ in entries if s == section]
        if rows:
            out += [f"{section}:"] + rows
    return "\n".join(out)


def cap_knowledge(k: dict, cap: int = KNOWLEDGE_CAP) -> tuple[str, int]:
    """The knowledge block under `cap` tokens; the entries touched least recently
    drop first. A dropped entry stays in its question's memory/<QID>.json, reachable
    through RECALL. Returns (text, how many were dropped)."""
    entries = _entries(k)
    dropped = 0
    text = _render_knowledge(entries)
    while entries and count_tokens(text) > cap:
        entries.pop(min(range(len(entries)), key=lambda i: entries[i][3]))
        dropped += 1
        text = _render_knowledge(entries)
    return text, dropped


# ── the prompt SH gets at the start of a question ─────────────────────────────

def _swapped_path(run_dir: str) -> str:
    return os.path.join(memory_dir(run_dir), "swapped.json")


def _load_swapped(run_dir: str) -> list[str]:
    try:
        with open(_swapped_path(run_dir), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def _save_swapped(run_dir: str, swapped: list[str]) -> None:
    os.makedirs(memory_dir(run_dir), exist_ok=True)
    _atomic(_swapped_path(run_dir), json.dumps(swapped))


def render_memory(run_dir: str, history: dict, *, qid: str, base: list, current: list,
                  threshold: int = MEMORY_THRESHOLD) -> list:
    """Sections 3-6 of SH's prompt (design §1), fitted under `threshold` (§4).

    `base` (system prompt, briefing) and `current` (the case file and the question being
    opened) count toward the threshold and are never summarized. An earlier pass at
    this same question (the hint re-run) rides with the current question, raw.

    ORDERED FOR THE PROMPT CACHE. OpenAI bills the part of a prompt that repeats an
    earlier prompt from its first token at a tenth of the price, so what changes
    between questions goes last: summaries (append-only), then raw transcripts
    (append-only between swaps), then the cards and knowledge that change every
    question. The caller puts the case file, which also changes, after all of it.

    THE SWAP GOES DOWN TO SWAP_TARGET x threshold, NOT JUST UNDER IT. Swapping one
    question at a time would change the prompt's start on nearly every question once
    the threshold is reached, losing the cache each time. Swapped questions are kept in
    memory/swapped.json and stay summarized, so the next several questions only add to
    the end. SWAP_TARGET = 1.0 restores the plan's original swap-just-under rule.
    """
    memories = {q: m for q, m in load_memories(run_dir).items() if q != qid}
    past = [q for q in history if q != qid]
    same = list(history.get(qid, []))
    if not memories and not past and not same:
        return []

    tail = []
    if memories:
        tail.append(SystemMessage(content=(
            "MEMORY INDEX — one card per earlier question in this run: the question, "
            "the answer SH submitted, and how it was reached. RECALL a question's "
            "summary, conversation, ledger or a report when a card touches this one.\n\n"
            + "\n\n".join(render_card(m) for m in memories.values()))))
        text, dropped = cap_knowledge(merge_knowledge(list(memories.values())))
        if text:
            tail.append(SystemMessage(content=(
                "KNOWLEDGE carried from earlier questions (the question each came from "
                "is in brackets):\n" + text)))
        if dropped:
            log(run_dir, f"[SH MEMORY] knowledge over {KNOWLEDGE_CAP:,} tok: dropped "
                         f"{dropped} least-recent entr{'y' if dropped == 1 else 'ies'} "
                         "(still in memory/<QID>.json)")

    raw = {q: _msgs_tokens(history[q]) for q in past}
    detail = {q: render_detail(memories[q]) for q in past if q in memories}
    fixed = (_msgs_tokens(base) + _msgs_tokens(tail) + _msgs_tokens(current)
             + _msgs_tokens(same))
    swapped = [q for q in _load_swapped(run_dir) if q in raw]   # once swapped, stays so
    held = [q for q in past if q not in swapped]

    def total() -> int:
        return (fixed + sum(count_tokens(detail[q]) for q in swapped if q in detail)
                + sum(raw[q] for q in held))

    size = total()
    if size > threshold and held:
        target, notes = int(threshold * SWAP_TARGET), []
        while size > target and held:
            q = held.pop(0)
            swapped.append(q)
            size = total()
            notes.append(f"{q or '(unnamed)'} raw {raw[q]:,} → "
                         + (f"summary {count_tokens(detail[q]):,}" if q in detail
                            else "no summary, dropped (RECALL its conversation)"))
        _save_swapped(run_dir, swapped)
        log(run_dir, f"[SH MEMORY] prompt for {qid} > {threshold:,} tok → down to "
                     f"{target:,}: " + " · ".join(notes) + f" → now {size:,}")
    else:
        log(run_dir, f"[SH MEMORY] prompt for {qid}: {size:,} tok ≤ {threshold:,} — "
                     f"{len(held)} past question(s) raw, {len(swapped)} summarized, "
                     f"{len(memories)} card(s)")

    out = []
    summaries = [detail[q] for q in swapped if q in detail]
    if summaries:
        out.append(SystemMessage(content=(
            "DETAILED SUMMARIES of earlier questions whose full transcripts are no "
            "longer in context (RECALL <qid> conversation brings one back):\n\n"
            + "\n\n".join(summaries))))
    for q in held:
        out += history[q]
    return out + tail + same


# ── RECALL ────────────────────────────────────────────────────────────────────

def _recall_path(run_dir: str, qid: str, what: str) -> str:
    if what == "summary":
        return os.path.join(memory_dir(run_dir), f"{qid}.md")
    if what == "conversation":
        return os.path.join(run_dir, qid, "conversation.md")
    if what == "ledger":
        return os.path.join(run_dir, "premise_ledgers", f"{qid}.json")
    _, sid, n = what.split(":")
    return os.path.join(run_dir, qid, "reports", f"{sid}_round_{n}.md")


def _available(run_dir: str, qid: str) -> list[str]:
    have = [w for w in ("summary", "conversation", "ledger")
            if os.path.exists(_recall_path(run_dir, qid, w))]
    reports = os.path.join(run_dir, qid, "reports")
    if os.path.isdir(reports):
        for f in sorted(os.listdir(reports)):
            m = re.fullmatch(r"(.+)_round_(\d+)\.md", f)
            if m:
                have.append(f"report:{m.group(1)}:{m.group(2)}")
    return have


def recall(run_dir: str, qid: str, what: str) -> str:
    """The file SH asked for, capped at RECALL_CAP tokens. An unknown question or
    file returns what does exist, so the next RECALL can aim right."""
    qid = qid.strip().upper()
    what = what.strip()
    path = _recall_path(run_dir, qid, what) if RECALL_WHAT.match(what) else ""
    if not path or not os.path.exists(path):
        have = _available(run_dir, qid)
        if not have:
            known = sorted(load_memories(run_dir)) or ["none yet"]
            return (f"RECALLED {qid} {what}: nothing is recorded for {qid}. Past "
                    f"questions with a memory: {', '.join(known)}.")
        return (f"RECALLED {qid} {what}: no such file. What exists for {qid}: "
                f"{', '.join(have)}.")
    with open(path, encoding="utf-8") as fh:
        text, cut = _truncate(fh.read(), RECALL_CAP)
    note = f" — truncated at {RECALL_CAP:,} tokens, the rest is on disk" if cut else ""
    return f"RECALLED {qid} {what} ({count_tokens(text):,} tok{note})\n\n{text}"
