#!/usr/bin/env python3
"""
Candidate ledger + (Task 4) case-file store for the v1 SH.

Ledger: every delegation's FINAL/PARTIAL ANSWER value is captured VERBATIM at
delegation time, with its evidence and SPL. The joiner chooses FROM the ledger
and copies — never re-types. run_1.2 lost 5,100 pts to values that existed in
a worker's answer and were mangled or bypassed at synthesis time (Q215
BSTOLL-L.froth.ly -> BSTOLL-L, Q221 nullweb_admin -> web_admin, Q331
1367.875 -> 1499.25). The ledger is also Plan C's adjudication input.
"""

from __future__ import annotations

import json
import os
import re
import threading

_ANSWER_TAG = re.compile(r'(?:FINAL|PARTIAL)\s+ANSWER:\s*(.+)', re.IGNORECASE)


def extract_candidate(delegation: dict) -> dict | None:
    """Verbatim candidate from one delegation record; None if it never committed
    to a value (ESCALATE / empty / crashed)."""
    text = delegation.get("answer") or ""
    m = _ANSWER_TAG.search(text)
    if not m:
        return None
    value = m.group(1).strip().splitlines()[0].strip()
    if not value:
        return None
    spl = delegation.get("spl_used") or []
    return {
        "value":    value,                       # verbatim — the joiner copies this
        "status":   delegation.get("status", "?"),
        "worker":   delegation.get("worker", ""),
        "spl":      spl[-1:],                    # the query that produced it
        "evidence": text[:400],
    }


def build_ledger(delegations: list) -> list[dict]:
    """One entry per distinct value (case-insensitive), first-seen form wins."""
    seen: set = set()
    out = []
    for d in delegations:
        c = extract_candidate(d)
        if c and c["value"].lower() not in seen:
            seen.add(c["value"].lower())
            out.append(c)
    return out


def snap_to_ledger(answer: str, ledger: list) -> str:
    """Byte-exact fidelity: if the answer case-insensitively equals a ledger
    value, return the ledger's verbatim form. Never substitutes a different
    value — truncations/supersets are a selection judgment (Plan C), not a
    casing slip."""
    a = (answer or "").strip().lower()
    for c in ledger:
        if c["value"].strip().lower() == a:
            return c["value"]
    return answer


def render_ledger(ledger: list) -> str:
    """Joiner-facing candidate block."""
    if not ledger:
        return ""
    lines = ["CANDIDATES (each captured verbatim from a worker — your FINAL ANSWER "
             "must be copied character-for-character from one of these, or from "
             "the question text):"]
    for i, c in enumerate(ledger, 1):
        spl = f"  SPL: {c['spl'][0][:160]}" if c["spl"] else ""
        lines.append(f"  {i}. `{c['value']}`  [{c['status']}, {c['worker']}]{spl}")
    return "\n".join(lines)


_STATUSES    = ("verified", "hypothesis", "refuted")
_STATUS_MARK = {"verified": "[OK]", "hypothesis": "[?]", "refuted": "[X]"}


class CaseFile:
    """Cross-question incident store: entities + confidence-tagged findings.
    JSON-backed so it survives process resume (same run_dir, like metrics.json).
    Thread-locked: parallel Senior threads report via the joiner (main thread)
    today, but the lock makes direct worker writes safe if that changes."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._data = {"entities": [], "findings": []}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def add_entity(self, etype: str, value: str, *, qid: str = "") -> None:
        with self._lock:
            if not any(e["value"].lower() == value.lower()
                       for e in self._data["entities"]):
                self._data["entities"].append(
                    {"type": etype, "value": value, "qid": qid})
                self._save()

    def add_finding(self, claim: str, *, evidence: str = "", source_qid: str = "",
                    status: str = "hypothesis", confidence: float = 0.5) -> int:
        if status not in _STATUSES:
            status = "hypothesis"
        with self._lock:
            fid = len(self._data["findings"])
            self._data["findings"].append({
                "id": fid, "claim": claim, "evidence": evidence,
                "source_qid": source_qid, "status": status,
                "confidence": confidence,
            })
            self._save()
            return fid

    def get_finding(self, fid: int) -> dict:
        return self._data["findings"][fid]

    def iter_findings(self):
        return list(self._data["findings"])

    def set_status(self, fid: int, status: str) -> None:
        if status not in _STATUSES:
            return
        with self._lock:
            self._data["findings"][fid]["status"] = status
            self._save()

    def render_digest(self, *, max_chars: int = 4000) -> str:
        """Planner-facing view: verified first, hypotheses next, refuted last
        with a warning marker so the planner distrusts them."""
        ents = self._data["entities"]
        ent_line = ("ENTITIES: " + ", ".join(f"{e['type']}={e['value']}"
                                             for e in ents)) if ents else ""
        order = {"verified": 0, "hypothesis": 1, "refuted": 2}
        finds = sorted(self._data["findings"],
                       key=lambda f: order.get(f["status"], 3))
        lines = [ent_line, "", "FINDINGS:"]
        for f in finds:
            lines.append(f"  {_STATUS_MARK.get(f['status'], '[?]')} "
                         f"{f['claim']} (src {f['source_qid']}"
                         f"{'; ' + f['evidence'] if f['evidence'] else ''})")
        out = "\n".join(lines)
        if len(out) > max_chars:
            out = out[:max_chars - 24].rstrip() + "\n  ...[digest truncated]"
        return out


def parse_case_updates(text: str) -> list[dict]:
    """Parse a `CASE UPDATES:` block. Grammar (one per line under the header):
      - entity <type> <value>
      - finding [<status>] <claim> | evidence: <evidence>
    """
    m = re.search(r'CASE UPDATES:\s*(.+)$', text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    updates = []
    for raw in m.group(1).splitlines():
        line = raw.strip().lstrip("-").strip()
        if not line:
            continue
        em = re.match(r'entity\s+(\S+)\s+(.+)$', line, re.IGNORECASE)
        if em:
            updates.append({"kind": "entity", "etype": em.group(1),
                            "value": em.group(2).strip()})
            continue
        fm = re.match(r'finding\s+\[(\w+)\]\s+(.+)$', line, re.IGNORECASE)
        if fm:
            claim, evidence = fm.group(2).strip(), ""
            if "|" in claim:
                claim, _, tail = claim.partition("|")
                claim = claim.strip()
                evidence = re.sub(r'^\s*evidence:\s*', '', tail.strip(),
                                  flags=re.IGNORECASE)
            updates.append({"kind": "finding", "status": fm.group(1).lower(),
                            "claim": claim, "evidence": evidence})
    return updates
