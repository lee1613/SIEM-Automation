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
