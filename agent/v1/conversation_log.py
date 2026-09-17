#!/usr/bin/env python3
"""
The v1.3.1 artifacts (spec §5):

    log/<run>/<qid>/
      conversation.md                     every message, in order
      reports/senior_<n>_round_<r>.md     one per report, templated
      handoffs/senior_<n>_handoff.md      one per retirement

`conversation.md` is the monitoring surface — a group-chat transcript of how the
two tiers actually talk to each other. Reports are excerpted there and written in
full beside it, so the transcript stays readable while nothing is lost.

Plain file appends by design: the whole point is to be readable mid-run with a
tail, and to cost zero tokens.
"""

from __future__ import annotations

import datetime
import os
import re


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", (text or "x")).strip("_") or "x"


class ConversationLog:
    """One question's transcript and artifacts."""

    def __init__(self, run_dir: str, qid: str):
        self.qid = qid
        self.dir = os.path.join(run_dir, qid)
        self.reports_dir = os.path.join(self.dir, "reports")
        self.handoffs_dir = os.path.join(self.dir, "handoffs")
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.handoffs_dir, exist_ok=True)
        self.conversation_path = os.path.join(self.dir, "conversation.md")
        if not os.path.exists(self.conversation_path):
            self._append(f"# {qid} — SH <-> Senior conversation\n")

    # ── writing ───────────────────────────────────────────────────────────────
    def _append(self, text: str) -> None:
        with open(self.conversation_path, "a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n\n")

    @staticmethod
    def _stamp() -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    def sh_to_senior(self, senior_id: str, route: str, *, body: str) -> None:
        target = senior_id or "(new)"
        self._append(f"### {self._stamp()} - SH -> {target}   [{route}]\n{body}")

    def senior_to_sh(self, senior_id: str, *, round_n: int, insight: str,
                     excerpt: str, path: str) -> None:
        one_line = " ".join((excerpt or "").split())[:300]
        self._append(f"### {self._stamp()} - {senior_id} -> SH   "
                     f"[REPORT - round {round_n} - {insight}]\n"
                     f"> {one_line}\n_full: {path}_")

    def clarify_reply(self, senior_id: str, text: str) -> None:
        self._append(f"### {self._stamp()} - {senior_id} -> SH   [CLARIFY REPLY]\n"
                     f"{(text or '').strip()[:1200]}")

    def note(self, text: str) -> None:
        """Runner-side events worth seeing in the transcript: gate rejections,
        budget exhaustion, a refunded spawn slot."""
        self._append(f"### {self._stamp()} - runner   [NOTE]\n{text}")

    # ── artifacts ─────────────────────────────────────────────────────────────
    def write_report(self, senior_id: str, round_n: int, md: str) -> str:
        rel = os.path.join("reports", f"{_slug(senior_id)}_round_{round_n}.md")
        with open(os.path.join(self.dir, rel), "w", encoding="utf-8") as f:
            f.write(md or "")
        return rel.replace("\\", "/")

    def write_handoff(self, senior_id: str, md: str) -> str:
        rel = os.path.join("handoffs", f"{_slug(senior_id)}_handoff.md")
        with open(os.path.join(self.dir, rel), "w", encoding="utf-8") as f:
            f.write(md or "")
        self._append(f"### {self._stamp()} - {senior_id} -> SH   [HANDOFF]\n"
                     f"_full: {rel.replace(chr(92), '/')}_")
        return rel.replace("\\", "/")
