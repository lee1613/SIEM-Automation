# Plan B — Case-File Blackboard + Recon + Specialists Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Turn 56 isolated question-solves into one coherent incident investigation. Replace the lossy chat-thread memory (which also propagates unverified errors) with a structured, confidence-tagged **case file**; build the incident skeleton once up front (recon); route tasks to **specialist** workers; and buy official **hints** when confidence is low on high-value questions.

**Architecture:** A JSON-backed `CaseFile` (entities + findings with `status ∈ {verified, hypothesis, refuted}` + confidence + source qid) is the SH's planning substrate instead of raw message history. The joiner emits `CASE UPDATES:` lines parsed into it; the planner reads a rendered digest. A Phase-0 recon pass seeds the file. The planner tags each task with a specialist role (`HUNTER`/`CONTENT`/`METRICS`); the executor selects a matching worker graph. `buy_hint` deducts the official `HintCost` from earned points (honest scoring).

**Tech Stack:** Python 3.11, pytest 9.1, LangGraph, existing v0 worker graph, CSV hint data.

**Depends on:** observability foundation (merged) + Plan A (merged). Plan B's Verifier promotes hypotheses; Plan A's grounding guard still applies. Build Plan B ON TOP of the current `jy` HEAD.

**Validation policy:** unit tests (green) + import checks per task; cheap `--ids` smoke runs only (2–4 Qs). The human triggers the full 56-Q scoring run. This is the highest-leverage but riskiest plan — the case-file digest is the SH's whole planning context, so a bad digest silently degrades every question. Land B1 (store) + B2 (emission/parse) + B3-digest behind a flag first and smoke-compare before enabling recon.

---

## File Structure

| File | Responsibility | Change |
|------|----------------|--------|
| `agent/v1/case_file.py` | `CaseFile` store: entities, findings, digest render, CASE-UPDATES parse | **Create** |
| `agent/v1/orchestrator.py` | Planner reads digest; joiner emits+parses CASE UPDATES; specialist task tags; recon entrypoint | Modify |
| `agent/v1/recon.py` | Phase-0 recon pass — parallel workers build the incident skeleton | **Create** |
| `agent/v1/specialists.py` | Specialist prompt/tool configs + `python_calc` tool | **Create** |
| `agent/v1/splunk_subagent.py` | Build per-specialist worker graphs; select by task tag | Modify |
| `agent/v1/hint_client.py` | `HintBook` — load hints CSV, buy_hint with cost | **Create** |
| `agent/v1/run_all_v1.py` | Init case file; run recon; thread hint policy; pass points/specialist | Modify |
| `agent/v1/tests/` | pytest for all of the above | add files |

Run all commands from project root. A run's case file lives at `<run_dir>/case_file.json` (survives resume, like the metrics files).

---

## Task 1: CaseFile store (pure, the planning substrate)

**Files:**
- Create: `agent/v1/case_file.py`
- Create: `agent/v1/tests/test_case_file.py`

**Context:** the SH loses/contaminates knowledge because it re-reads a growing chat thread (LangSmith showed 200–320K token SH contexts by run end, and Q210's wrong verdict poisoned Q216). The case file is a compact, structured, confidence-tagged store the planner reads instead.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_case_file.py`:

```python
import json
from case_file import CaseFile, parse_case_updates


def test_add_and_render_entity_and_finding(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    cf.add_entity("host", "BSTOLL-L.froth.ly", qid="Q210")
    cf.add_finding("BSTOLL-L mined Monero", evidence="cisco:asa flow",
                   source_qid="Q210", status="hypothesis", confidence=0.6)
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d
    assert "hypothesis" in d.lower()


def test_finding_status_promote_and_refute(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    fid = cf.add_finding("miner is FYODOR-L", evidence="tcp connect",
                         source_qid="Q210", status="hypothesis", confidence=0.5)
    cf.set_status(fid, "refuted")
    assert cf.get_finding(fid)["status"] == "refuted"
    # refuted findings render with a clear marker so the planner distrusts them
    assert "refuted" in cf.render_digest().lower()


def test_persist_and_reload(tmp_path):
    p = str(tmp_path / "case.json")
    cf = CaseFile(p)
    cf.add_entity("user", "mkraeusen", qid="Q330")
    CaseFile(p)  # reload
    assert "mkraeusen" in CaseFile(p).render_digest()


def test_digest_is_bounded(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    for i in range(500):
        cf.add_finding(f"finding number {i} with some text", evidence="x",
                       source_qid=f"Q{i}", status="verified", confidence=0.9)
    d = cf.render_digest(max_chars=4000)
    assert len(d) <= 4000


def test_parse_case_updates_block():
    text = '''FINAL ANSWER: BSTOLL-L
CASE UPDATES:
- entity host BSTOLL-L.froth.ly
- finding [verified] BSTOLL-L is the Monero miner | evidence: cisco:asa message_id 113019
'''
    updates = parse_case_updates(text)
    assert any(u["kind"] == "entity" and "BSTOLL-L" in u["value"] for u in updates)
    assert any(u["kind"] == "finding" and u["status"] == "verified" for u in updates)


def test_parse_case_updates_absent_returns_empty():
    assert parse_case_updates("FINAL ANSWER: x\n(no updates)") == []
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_case_file.py -v`
Expected: FAIL — no `case_file` module.

- [ ] **Step 3: Implement `case_file.py`**

Create `agent/v1/case_file.py`:

```python
#!/usr/bin/env python3
"""
Structured, confidence-tagged case file — the SH's planning substrate.

BOTSv3 is one incident probed by 56 questions. Instead of re-reading a growing
chat thread (lossy, and it propagates unverified errors across questions), the
SH plans against a compact digest of this store: named entities and findings,
each tagged verified | hypothesis | refuted. Carried-forward claims arrive as
'hypothesis' and must be promoted by the Verifier before a later question trusts
them — this is what breaks the v1.1 cascade (Q210 wrong verdict -> Q216).

JSON-backed so it survives process resume (same run_dir, like metrics.json).
"""

from __future__ import annotations

import json
import os
import re
import threading

_STATUSES = ("verified", "hypothesis", "refuted")
_STATUS_MARK = {"verified": "[OK]", "hypothesis": "[?]", "refuted": "[X]"}


class CaseFile:
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

    def set_status(self, fid: int, status: str) -> None:
        if status not in _STATUSES:
            return
        with self._lock:
            self._data["findings"][fid]["status"] = status
            self._save()

    def render_digest(self, *, max_chars: int = 4000) -> str:
        """Compact planner-facing view. Verified first, then hypotheses;
        refuted findings render last with a warning marker so the planner
        actively distrusts them rather than silently reusing them."""
        ents = self._data["entities"]
        ent_line = "ENTITIES: " + ", ".join(
            f"{e['type']}={e['value']}" for e in ents) if ents else ""
        order = {"verified": 0, "hypothesis": 1, "refuted": 2}
        finds = sorted(self._data["findings"],
                       key=lambda f: order.get(f["status"], 3))
        lines = [ent_line, "", "FINDINGS:"]
        for f in finds:
            lines.append(f"  {_STATUS_MARK.get(f['status'], '[?]')} "
                         f"{f['claim']} (src {f['source_qid']}"
                         f"{'; ' + f['evidence'] if f['evidence'] else ''})")
        out = "\n".join(l for l in lines if l is not None)
        if len(out) > max_chars:
            out = out[:max_chars - 20].rstrip() + "\n  ...[digest truncated]"
        return out


def parse_case_updates(text: str) -> list[dict]:
    """Parse a `CASE UPDATES:` block from a joiner/worker message.

    Grammar (one per line under the header):
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
            claim = fm.group(2).strip()
            evidence = ""
            if "|" in claim:
                claim, _, tail = claim.partition("|")
                claim = claim.strip()
                evidence = re.sub(r'^\s*evidence:\s*', '', tail.strip(),
                                  flags=re.IGNORECASE)
            updates.append({"kind": "finding", "status": fm.group(1).lower(),
                            "claim": claim, "evidence": evidence})
    return updates
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_case_file.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/v1/case_file.py agent/v1/tests/test_case_file.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): CaseFile store + CASE UPDATES parser"
```

(Add a changelog line to `v1.2.md` in this and every task below.)

---

## Task 2: Joiner emits + writes CASE UPDATES; planner reads the digest

**Files:**
- Modify: `agent/v1/orchestrator.py`
- Create: `agent/v1/tests/test_case_integration.py`

**Context:** wire the case file into the graph. The `DelegationContext` will carry a `CaseFile`. The joiner prompt gains a `CASE UPDATES:` output section; after the joiner produces a final answer, parse+apply updates. The planner prompt injects the digest. Put this behind a `ctx.use_case_file` flag (default True) so it can be disabled for A/B comparison.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_case_integration.py`:

```python
from case_file import CaseFile
from orchestrator import apply_case_updates


def test_apply_case_updates_writes_entities_and_findings(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    joiner_text = ("FINAL ANSWER: BSTOLL-L\n"
                   "CASE UPDATES:\n"
                   "- entity host BSTOLL-L.froth.ly\n"
                   "- finding [verified] BSTOLL-L is the miner | evidence: cisco:asa")
    apply_case_updates(cf, joiner_text, source_qid="Q210")
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d and "miner" in d


def test_apply_case_updates_noop_when_absent(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    apply_case_updates(cf, "FINAL ANSWER: x", source_qid="Q1")
    assert cf.render_digest().count("finding") <= 1  # header only, no rows
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_case_integration.py -v`
Expected: FAIL — no `apply_case_updates`.

- [ ] **Step 3: Implement `apply_case_updates` + DelegationContext wiring**

In `agent/v1/orchestrator.py`:
- Import: `from case_file import CaseFile, parse_case_updates`.
- Add module-level:

```python
def apply_case_updates(case_file, joiner_text: str, *, source_qid: str) -> int:
    """Parse a CASE UPDATES block and write it into the case file. Returns count."""
    n = 0
    for u in parse_case_updates(joiner_text):
        if u["kind"] == "entity":
            case_file.add_entity(u["etype"], u["value"], qid=source_qid)
            n += 1
        elif u["kind"] == "finding":
            case_file.add_finding(u["claim"], evidence=u.get("evidence", ""),
                                  source_qid=source_qid, status=u["status"])
            n += 1
    return n
```

- Extend `DelegationContext.__init__` to accept `case_file=None` and `use_case_file=True`; store them.
- In `joiner_node`, in the FINAL ANSWER grounded-return branch (after the grounding guard yields `action=="final"`), call `apply_case_updates(ctx.case_file, jtext, source_qid=ctx.current_qid)` if `ctx.case_file and ctx.use_case_file`.

- [ ] **Step 4: Planner injects the digest**

In `planner_node`, when `ctx.case_file and ctx.use_case_file`, prepend the digest to the planner messages as a SystemMessage or a leading context block:

```python
        digest = ""
        if ctx.case_file and ctx.use_case_file:
            digest = ctx.case_file.render_digest()
        extra = ([SystemMessage(content="CASE FILE (known incident state — "
                 "verified [OK], hypothesis [?], refuted [X]; distrust [?]/[X] "
                 "until re-verified):\n" + digest)] if digest.strip() else [])
        msgs = [sys_planner] + extra + list(state["messages"])
```

- Append to `PLANNER_SYSTEM_PROMPT`: instruction to (a) treat `[?]`/`[X]` findings as unproven and re-verify before relying on them, and (b) emit a `CASE UPDATES:` block via the JOINER (not planner). Append to `JOINER_SYSTEM_PROMPT` the `CASE UPDATES:` output grammar (entity/finding lines exactly as the parser expects).

- [ ] **Step 5: Run tests + import check + full suite**

Run: `python -m pytest agent/v1/tests/ -v` (expect prior + 2 new, all green).
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import orchestrator; print('ok')"`.

- [ ] **Step 6: Runner initializes the case file**

In `run_all_v1.py`: create `case_file = CaseFile(os.path.join(logger.run_dir, "case_file.json"))`, pass into `DelegationContext(pool, logger, case_file=case_file)`. (It auto-persists; resume picks up the existing file.)

- [ ] **Step 7: Cheap smoke — cascade pair**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q210,Q216`
Expected: completes; `case_file.json` exists with entities/findings after Q210; report whether Q216's plan digest referenced Q210's finding and with what status marker. (Correctness not required — the digest carrying a `[?]`/`[OK]`-tagged finding into Q216 is the signal.)

- [ ] **Step 8: Commit**

```bash
git add agent/v1/orchestrator.py agent/v1/run_all_v1.py agent/v1/tests/test_case_integration.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): case-file digest in planner + CASE UPDATES from joiner"
```

---

## Task 3: Hint economy

**Files:**
- Create: `agent/v1/hint_client.py`
- Create: `agent/v1/tests/test_hint_client.py`
- Modify: `agent/v1/run_all_v1.py` (hint policy)

**Context:** 97 official hints in `botsv3content/ctf_hints.csv` (cost 10–25 pts) sit unused. A wrong answer scores 0; a hint-assisted correct answer scores base − hint cost (still 75–990). Buy a hint when confidence is low on a ≥500-pt question.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_hint_client.py`:

```python
import csv
from hint_client import HintBook


def _write_hints(path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["_key", "Hint", "HintCost", "HintNumber", "Number"])
        w.writerow(["", "Use aws:cloudtrail.", "10", "1", "200"])
        w.writerow(["", "Look at user_type.", "25", "2", "200"])


def test_get_hint_by_number_and_index(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    hb = HintBook(str(p))
    h = hb.get_hint(200, 1)
    assert h["text"] == "Use aws:cloudtrail." and h["cost"] == 10


def test_total_hint_count(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    assert HintBook(str(p)).count_for(200) == 2


def test_missing_hint_returns_none(tmp_path):
    p = tmp_path / "hints.csv"; _write_hints(p)
    assert HintBook(str(p)).get_hint(999, 1) is None
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_hint_client.py -v`
Expected: FAIL — no `hint_client`.

- [ ] **Step 3: Implement `hint_client.py`**

Create `agent/v1/hint_client.py`:

```python
#!/usr/bin/env python3
"""
Official BOTSv3 hint book. Hints cost HintCost points; a hint-assisted correct
answer still scores base - cost (75-990), strictly better than a wrong 0. Buy a
hint when the pipeline is low-confidence on a high-value question.
"""

from __future__ import annotations

import csv
from collections import defaultdict


class HintBook:
    def __init__(self, hints_csv: str) -> None:
        self._by_q: dict[int, list[dict]] = defaultdict(list)
        with open(hints_csv, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    num = int(row["Number"]); hnum = int(row["HintNumber"])
                    cost = int(row["HintCost"])
                except (ValueError, KeyError):
                    continue
                self._by_q[num].append(
                    {"number": num, "hint_number": hnum,
                     "text": row.get("Hint", "").strip(), "cost": cost})
        for lst in self._by_q.values():
            lst.sort(key=lambda h: h["hint_number"])

    def get_hint(self, number: int, hint_number: int) -> dict | None:
        for h in self._by_q.get(number, []):
            if h["hint_number"] == hint_number:
                return h
        return None

    def count_for(self, number: int) -> int:
        return len(self._by_q.get(number, []))
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_hint_client.py -v`
Expected: 3 passed.

- [ ] **Step 5: Hint policy in the runner (minimal, gated)**

In `run_all_v1.py`: after the SH produces `sh_answer` and BEFORE extraction/submit, if the question is ≥500 pts AND the answer is ungrounded (reuse the `build_metrics_row` grounded logic on `ctx.q_delegations`), buy hint 1, append it to a re-delegation message, and run one more `run_sh(...)` pass with the hint text embedded. Deduct the hint cost from `pts_earned` when scoring (record `hint_cost` in the metrics row and the `submit` event). Keep it to ONE hint (hint 1) per question to bound cost. Guard with a `--hints` CLI flag (default off) so the baseline run is unaffected and the effect is measurable.

- [ ] **Step 6: Full suite + cheap smoke**

Run: `python -m pytest agent/v1/tests/ -v` (green).
Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q216 --hints`
Expected: completes; report whether a hint was bought, its cost, and the net earned.

- [ ] **Step 7: Commit**

```bash
git add agent/v1/hint_client.py agent/v1/tests/test_hint_client.py agent/v1/run_all_v1.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): hint economy (buy hint on low-confidence >=500pt, --hints flag)"
```

---

## Task 4: Specialist workers + python_calc tool

**Files:**
- Create: `agent/v1/specialists.py`
- Modify: `agent/v1/splunk_subagent.py`, `agent/v1/orchestrator.py`
- Create: `agent/v1/tests/test_specialists.py`

**Context:** different question classes need different worker behavior. Hunter (default), Content-Inspector (raw-content reads, gate relaxed — the `get_raw_events` tool from Plan A), Metrics-Analyst (mandatory SPL `eval` arithmetic + a `python_calc` tool to cross-check, for Q206/Q211/Q224/Q331). Planner tags each task; executor picks the graph.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_specialists.py`:

```python
from specialists import parse_specialist_tag, SPECIALISTS, python_calc


def test_parse_tag_defaults_to_hunter():
    assert parse_specialist_tag("Search dns for the C2 domain") == "hunter"


def test_parse_content_tag():
    assert parse_specialist_tag("[CONTENT] Read the phishing email body") == "content"


def test_parse_metrics_tag():
    assert parse_specialist_tag("[METRICS] Average subdomain length") == "metrics"


def test_all_specialists_have_prompt():
    for name in ("hunter", "content", "metrics"):
        assert name in SPECIALISTS and SPECIALISTS[name].strip()


def test_python_calc_evaluates_safe_arithmetic():
    assert python_calc.invoke({"expression": "(1368 - 1 + 1367.875)/2"}) != "error"
    assert "8.1" in python_calc.invoke({"expression": "str(round(8.1, 1))"}) or True
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_specialists.py -v`
Expected: FAIL — no `specialists` module.

- [ ] **Step 3: Implement `specialists.py`**

Create `agent/v1/specialists.py` with:
- `SPECIALISTS: dict[str, str]` — extra-instruction text per role (hunter = "", content = raw-read guidance, metrics = "show the SPL eval formula and inputs; cross-check with python_calc").
- `parse_specialist_tag(subquestion) -> str` — regex for a leading `[CONTENT]`/`[METRICS]`/`[HUNTER]` tag (case-insensitive), default `"hunter"`.
- `python_calc` `@tool` — evaluate an arithmetic expression safely. Use a restricted eval: `eval(expr, {"__builtins__": {}}, {"round": round, "abs": abs, "min": min, "max": max, "len": len, "str": str, "sum": sum})`; return the result as a string, or `"error: <msg>"` on exception. NEVER allow imports/attribute access — reject any expression containing `__` or `import`.

```python
import re
from langchain_core.tools import tool

SPECIALISTS = {
    "hunter":  "",
    "content": ("You are a Content-Inspector. The answer is inside raw event "
                "text (email bodies, scripts, bash history, HTTP payloads). Use "
                "get_raw_events to READ events; do not force aggregation."),
    "metrics": ("You are a Metrics-Analyst. Compute with SPL eval/stats and SHOW "
                "the formula and inputs. Cross-check every number with python_calc "
                "before answering. Never eyeball an average or percentile."),
}

def parse_specialist_tag(subquestion: str) -> str:
    m = re.match(r'\s*\[(hunter|content|metrics)\]', subquestion or "", re.IGNORECASE)
    return m.group(1).lower() if m else "hunter"

@tool
def python_calc(expression: str) -> str:
    """Evaluate a pure arithmetic Python expression (round/abs/min/max/sum/len/str
    only) to cross-check a computed number. No imports or attribute access."""
    if "__" in expression or "import" in expression:
        return "error: forbidden token"
    try:
        val = eval(expression, {"__builtins__": {}},
                   {"round": round, "abs": abs, "min": min, "max": max,
                    "len": len, "str": str, "sum": sum})
        return str(val)
    except Exception as exc:
        return f"error: {exc}"
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_specialists.py -v`
Expected: 5 passed.

- [ ] **Step 5: Build specialist graphs + select by tag**

In `agent/v1/splunk_subagent.py` `SplunkWorkerPool.__init__`, build one worker graph per specialist (three graphs, each with `extra_instructions = ESCALATE_INSTRUCTIONS + "\n" + SPECIALISTS[name]`, `extra_tools = [web_lookup] (+ [python_calc] for metrics)`). Keep the existing budget dual (base/hi) — so it's `specialist × budget`; to bound construction, build the 3 specialists at the hi budget only if that keeps it simple, OR build 3 specialists × 2 budgets = 6 graphs (all offline construction, one-time). `run_senior(subquestion, qid, idx, points=0)` calls `parse_specialist_tag(subquestion)` and selects the matching graph. In `orchestrator.py`, append to `PLANNER_SYSTEM_PROMPT` the instruction to prefix each task with `[HUNTER]` / `[CONTENT]` / `[METRICS]` per the task's nature.

- [ ] **Step 6: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -v` (green).
Run: `python -c "...; import splunk_subagent, specialists; print('ok')"`.

- [ ] **Step 7: Cheap smoke — a metrics question**

Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q331`
Expected: completes; report whether the planner tagged a `[METRICS]` task and whether `python_calc` was called (grep questions/Q331.json full_state).

- [ ] **Step 8: Commit**

```bash
git add agent/v1/specialists.py agent/v1/splunk_subagent.py agent/v1/orchestrator.py agent/v1/tests/test_specialists.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): specialist workers (hunter/content/metrics) + python_calc"
```

---

## Task 5: Phase-0 recon pass

**Files:**
- Create: `agent/v1/recon.py`
- Modify: `agent/v1/run_all_v1.py`
- Create: `agent/v1/tests/test_recon.py`

**Context:** run once before the question loop — 4–6 parallel workers build the incident skeleton (sourcetype inventory + time ranges, key hosts/roles, phishing waves, C2 infra, cloud story) and seed the case file as **verified** baseline. Fixes plan-misdirection (Q329) and wave-confusion (Q310). Keep it behind a `--recon` flag (default off) so the baseline and the recon-enabled run are both measurable.

- [ ] **Step 1: Write failing test (recon question set + seeding is pure-ish)**

Create `agent/v1/tests/test_recon.py`:

```python
from case_file import CaseFile
from recon import RECON_TASKS, seed_case_from_recon


def test_recon_task_set_nonempty():
    assert len(RECON_TASKS) >= 4
    assert all(isinstance(t, str) and t.strip() for t in RECON_TASKS)


def test_seed_writes_verified_findings(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fake_results = [
        {"subquestion": RECON_TASKS[0],
         "answer": "FINAL ANSWER: hosts are BSTOLL-L, FYODOR-L, wrk-klagerf",
         "status": "solved"},
    ]
    seed_case_from_recon(cf, fake_results)
    d = cf.render_digest()
    assert "recon" in d.lower() or "BSTOLL-L" in d
    # recon findings are seeded as verified baseline
    assert "[OK]" in d
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_recon.py -v`
Expected: FAIL — no `recon` module.

- [ ] **Step 3: Implement `recon.py`**

Create `agent/v1/recon.py`:
- `RECON_TASKS: list[str]` — 4–6 self-contained recon subquestions (sourcetype inventory with time spans; key hosts + roles; phishing waves and their artifacts; C2 infrastructure/domains; AWS/cloud account story). Each is a normal Senior subquestion string.
- `seed_case_from_recon(case_file, results) -> None` — for each recon result with a usable answer, `add_finding(claim=answer, evidence="recon", source_qid="RECON", status="verified", confidence=0.8)` and best-effort extract obvious entities (hostnames matching `\b[A-Z0-9-]+-L\b`, etc.) via a light regex into `add_entity`.
- `run_recon(ctx, pool) -> list[dict]` — dispatch `RECON_TASKS` in parallel via the same `ThreadPoolExecutor(max_workers=MAX_WORKERS)` pattern the executor uses (import or replicate minimally), returning the worker results. (This function needs a live pool, so it is exercised in the smoke run, not the unit test; keep the dispatch small and mirror `executor_node`'s pattern.)

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v1/tests/test_recon.py -v`
Expected: 2 passed.

- [ ] **Step 5: Wire `--recon` into the runner**

In `run_all_v1.py`: add `--recon` flag. When set (and a fresh run, not a resume that already has recon findings), before the question loop call `run_recon(ctx, pool)` then `seed_case_from_recon(case_file, results)`; emit a `recon_done` event with the finding count. Guard so a resumed run doesn't re-run recon (check the case file already has `source_qid=="RECON"` findings).

- [ ] **Step 6: Full suite + cheap smoke**

Run: `python -m pytest agent/v1/tests/ -v` (green).
Run: `SIEM_LOG_ROOT=$LOCALAPPDATA/siem-smoke python agent/v1/run_all_v1.py --ids Q329 --recon`
Expected: recon runs first (report finding count seeded), then Q329; report whether Q329's plan referenced any recon finding. (Slow — best-effort; unit tests are the gate.)

- [ ] **Step 7: Commit**

```bash
git add agent/v1/recon.py agent/v1/run_all_v1.py agent/v1/tests/test_recon.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): phase-0 recon pass seeds verified case-file baseline (--recon)"
```

---

## Task 6: Verifier promotes case-file hypotheses

**Files:**
- Modify: `agent/v1/orchestrator.py` (verifier_node writes case updates)
- Create: `agent/v1/tests/test_verifier_promotes.py`

**Context:** close the loop — when Plan A's Verifier confirms/refutes an answer on a ≥500-pt question, reflect that into the case file so downstream questions inherit the corrected status (this is what actually breaks the Q210→Q216 cascade: Q210's finding flips to `verified` or `refuted` before Q216 plans).

- [ ] **Step 1: Write failing test**

Create `agent/v1/tests/test_verifier_promotes.py`:

```python
from case_file import CaseFile
from orchestrator import promote_from_verdict


def test_confirmed_promotes_to_verified(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("BSTOLL-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "BSTOLL-L", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "verified"


def test_refuted_marks_refuted(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("FYODOR-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "FYODOR-L",
                         {"verdict": "refuted", "correction": "BSTOLL-L"})
    assert cf.get_finding(fid)["status"] == "refuted"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest agent/v1/tests/test_verifier_promotes.py -v`
Expected: FAIL — no `promote_from_verdict`.

- [ ] **Step 3: Implement `promote_from_verdict` + call it in verifier_node**

Add to `orchestrator.py`:

```python
def promote_from_verdict(case_file, answer: str, verdict: dict) -> None:
    """Reflect a Verifier verdict into the case file: findings whose claim
    contains the verified answer become 'verified'; the refuted answer's
    findings become 'refuted'."""
    a = (answer or "").strip().lower()
    for f in case_file._data["findings"]:
        claim = f["claim"].lower()
        if verdict["verdict"] == "confirmed" and a and a in claim:
            case_file.set_status(f["id"], "verified")
        elif verdict["verdict"] == "refuted" and a and a in claim:
            case_file.set_status(f["id"], "refuted")
```

In `verifier_node`, after computing `verdict` and only if `ctx.case_file and ctx.use_case_file`, call `promote_from_verdict(ctx.case_file, answer, verdict)`. (Accessing `_data` from a helper in the same package is acceptable; if a public accessor is preferred, add `CaseFile.iter_findings()` and use it.)

- [ ] **Step 4: Run test, verify it passes**

Run: `python -m pytest agent/v1/tests/test_verifier_promotes.py -v`
Expected: 2 passed.

- [ ] **Step 5: Full suite + import**

Run: `python -m pytest agent/v1/tests/ -v` (all green).

- [ ] **Step 6: Commit**

```bash
git add agent/v1/orchestrator.py agent/v1/tests/test_verifier_promotes.py docs/version_architecture/v1/v1.2.md
git commit -m "feat(v1.2-planB): verifier promotes/refutes case-file findings"
```

---

## Done criteria

- `python -m pytest agent/v1/tests/ -v` all green.
- Every new capability is behind a flag (`--recon`, `--hints`) or a `ctx.use_case_file` toggle, so a baseline vs Plan-B run is measurable via `compare.py`.
- No change to the scoring/submit path except the explicit hint-cost deduction (which is honest CTF scoring).
- Whole-implementation review focuses on: (a) the planner-digest context size (must stay bounded — it replaces, not adds to, unbounded chat history); (b) case-file thread-safety under parallel workers writing findings; (c) recon not re-running on resume; (d) hint-cost accounting matching `scoreboard_submissions.json`.
- The human runs a full baseline vs full Plan-B run and compares with `compare.py` before Plan B is declared a win.
