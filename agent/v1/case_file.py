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
    to a value (ESCALATE / empty / crashed).

    Schema B's `value` is preferred and needs no parsing - it arrives as its own
    field from the worker's submit_finding call, so there is nothing to scrape
    and no casing to restore. The regex below is the fallback for a worker that
    skipped the tool and answered in prose (see finding.parse_finding).
    """
    text  = delegation.get("answer") or ""
    value = (delegation.get("value") or "").strip()
    if not value:
        m = _ANSWER_TAG.search(text)
        if not m:
            return None
        value = m.group(1).strip().splitlines()[0].strip()
    if not value:
        return None
    spl = delegation.get("spl_used") or []
    # Schema B's `evidence` is the SPL and result the worker cited for this exact
    # value; the prose tail is a fallback for workers that skipped the tool.
    evidence = (delegation.get("evidence") or "").strip() or text
    return {
        "value":    value,                       # verbatim — the joiner copies this
        "status":   delegation.get("status", "?"),
        "worker":   delegation.get("worker", ""),
        "spl":      spl[-1:],                    # the query that produced it
        "evidence": evidence[:400],
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


def finalize_answer(clean: str, delegations: list) -> str:
    """Last normalization before scoreboard submit, on BOTH the normal and the
    post-hint extract paths.

    Placement is the point: snap_to_ledger used to run only inside joiner_node,
    so anything reaching the scoreboard via the post-hint path was never snapped
    at all (the Q331 regression). Running it at the true submit choke point
    covers every path.

    The label-prefix strip that used to live here is gone. It existed to turn an
    extractor's 'UF = 2059' back into '2059' - a patch on a symptom of the worker
    returning prose. Schema B's `value` field cannot carry a label, so there is
    nothing left for it to repair."""
    return snap_to_ledger(clean, build_ledger(delegations))


_LEDGER_MAX_CHARS = 4000


def render_ledger(ledger: list) -> str:
    """Joiner-facing candidate block. Entry-boundary capped: whole entries are
    appended until the block would exceed _LEDGER_MAX_CHARS, then a summary
    line notes how many were omitted. Never truncates a candidate value itself
    — the joiner copies it character-for-character, so a clipped value could
    never snap back to the ledger's verbatim form."""
    if not ledger:
        return ""
    lines = ["CANDIDATES (each captured verbatim from a worker — your FINAL ANSWER "
             "must be copied character-for-character from one of these, or from "
             "the question text):"]
    total = sum(len(line) + 1 for line in lines)
    omitted = 0
    for i, c in enumerate(ledger, 1):
        spl = f"  SPL: {c['spl'][0][:160]}" if c["spl"] else ""
        entry = f"  {i}. `{c['value']}`  [{c['status']}, {c['worker']}]{spl}"
        if total + len(entry) + 1 > _LEDGER_MAX_CHARS:
            omitted = len(ledger) - i + 1
            break
        lines.append(entry)
        total += len(entry) + 1
    if omitted:
        lines.append(f"  ...[{omitted} more candidates omitted]")
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
            try:
                with open(path, encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                print(f"[CASE FILE] corrupt or unreadable {path} — starting empty")
                self._data = {"entities": [], "findings": []}

    def _save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

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
        if not ents and not self._data["findings"]:
            return ""   # empty case file -> no digest, planner injects nothing
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


def reconcile_findings(case_file, qid: str, correct: bool) -> int:
    """Post-submit truth feedback: a WRONG scoreboard verdict demotes that
    question's verified findings to hypothesis so later planners re-verify
    them (the joiner over-marks [verified] — smoke test_20260716_095627 put
    12/12 findings verified, including from wrong answers). Returns count."""
    if correct:
        return 0
    n = 0
    for f in case_file.iter_findings():
        if f["source_qid"] == qid and f["status"] == "verified":
            case_file.set_status(f["id"], "hypothesis")
            n += 1
    return n


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
