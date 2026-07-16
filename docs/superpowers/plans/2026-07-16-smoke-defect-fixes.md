# Smoke-Run Defect Fixes (test_20260716_095627) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two defects the Plan-B combined 5-question smoke (`log/temp/test_20260716_095627`) exposed in the submit path — the hint path bypasses the ledger snap (submitted `'UF = 2059'` raw), and the joiner marks every CASE UPDATE `[verified]` so wrong verdicts persist as trusted findings — then re-verify with a 2-question micro-smoke.

**Architecture:** One pure helper `finalize_answer` in `case_file.py` (label-prefix strip + snap-to-ledger) applied at BOTH extractor call sites in the runner, so the hint path gets the same byte-fidelity guarantee as the joiner path. One pure helper `reconcile_findings` in `case_file.py` demotes a question's `verified` findings to `hypothesis` when the scoreboard says WRONG — post-submit truth feedback closing the verified-inflation hole.

**Tech Stack:** Python 3.11, pytest. No new dependencies.

---

## Smoke-run defect record (what this plan fixes — and what it doesn't)

Source: `log/temp/test_20260716_095627` (Q216, Q303, Q329, Q330, Q331 + `--recon --hints`; 1/5 correct, $1.09, `failed_delegations=2`).

| # | Defect | Evidence | Status |
|---|--------|----------|--------|
| 1 | **Hint path bypasses ledger snap + label prose reaches scoreboard.** Post-hint flow in `run_all_v1.py` is `run_sh → extractor.extract → submit`; `snap_to_ledger` only runs inside `joiner_node`, and the extractor kept a label prefix. | Q331 submitted `'UF = 2059'` — prose prefix, not byte-identical to any ledger entry (`1374`, `1368`). | **Fixed by Task 2–3** |
| 2 | **Joiner marks every CASE UPDATE `[verified]`.** Prompt says "Mark [verified] only if a worker proved it with a query this round" — model ignored it; all 12 findings landed `verified`, including ones from questions scored WRONG (Q216 `0 seconds`, Q330 `bstoll`, Q331 `1374`). Verifier-promotion path (Plan B Task 8) never exercised. | `case_file.json`: 12/12 findings `status=verified`. | **Mitigated by Task 4** (post-submit demotion). Prompt-tightening deliberately skipped — deterministic demotion is the reliable lever; revisit only if hypothesis discipline still matters after a full run. |
| 3 | ~~Encoding corruption (`bstoll � 65,291,570`)~~ | **Disproven.** `python` check on `questions/Q330.json`: the char is `0x2014` (em-dash), intact UTF-8. The `�` was a console display artifact during review, not data corruption. | No action |

**Standing constraint (user directive, 2026-07-16): NO full 56-question run until the user explicitly says so.** All validation in this plan is micro-smoke scale (`--ids`, ≤2 questions, output to `log/temp/`).

## Global constraints

- Every code change gets a same-turn changelog line in `docs/version_architecture/v1/v1.3.md` (in-progress version).
- Commit prefix: `fix(v1.3-planB): …`.
- Suite baseline after Plan B: run `python -m pytest agent/v1/tests/ -q` before starting and note the passing count; every task ends green at that count + its new tests.
- Tests import bare module names — `agent/v1/tests/conftest.py` already puts `agent/` and `agent/v1/` on `sys.path`.

## File structure

| File | Responsibility | Change |
|------|----------------|--------|
| `agent/v1/case_file.py` | add `finalize_answer` (label strip + snap) and `reconcile_findings` (post-submit demotion) | Modify |
| `agent/v1/run_all_v1.py` | apply `finalize_answer` at both extract sites; call `reconcile_findings` after submit | Modify |
| `agent/v1/tests/test_finalize_answer.py` | tests for defect 1 | Create |
| `agent/v1/tests/test_reconcile_findings.py` | tests for defect 2 | Create |
| `docs/version_architecture/v1/v1.3.md` | defect record + changelog lines | Modify |

---

## Task 1: Record the smoke result + defects in v1.3.md

**Files:**
- Modify: `docs/version_architecture/v1/v1.3.md`

- [ ] **Step 1: Add a "Plan B combined smoke (test_20260716_095627)" section**

Append to `docs/version_architecture/v1/v1.3.md` (after the changelog):

```markdown
## Plan B combined smoke — test_20260716_095627 (2026-07-16)

`python agent/v1/run_all_v1.py --ids Q216,Q303,Q329,Q330,Q331 --recon --hints`
Result: 1/5 correct (Q303 `ilovedavidverve`, a 0 in run_1.2), 100/4100 pts,
`failed_delegations=2` (run_1.2: 62), 3.02M tokens, est $1.09.
All Plan-B mechanisms fired: recon seeded 5 findings; planner tasks cited case
entities; specialist tags on every task; handoff digests injected on Q303/Q329/Q331;
ledger recorded per question; hint bought on Q331.

Defects found:
1. Hint path bypasses ledger snap — Q331 submitted `'UF = 2059'` (label prose,
   not in ledger). Post-hint flow never re-snaps. → fixed by
   `finalize_answer` at both extract sites (see changelog).
2. Joiner marked all 12 case findings `[verified]`, including ones from WRONG
   questions — verified-inflation propagates bad verdicts. → mitigated by
   post-submit `reconcile_findings` demotion (see changelog).
3. Suspected encoding corruption in ledger values was DISPROVEN — em-dash
   0x2014 intact in `questions/Q330.json`; console artifact only.
```

- [ ] **Step 2: Commit**

```bash
git add docs/version_architecture/v1/v1.3.md
git commit -m "docs(v1.3-planB): record combined-smoke result + defects (hint-path snap bypass, verified inflation)"
```

---

## Task 2: `finalize_answer` — label strip + snap (pure function)

**Files:**
- Modify: `agent/v1/case_file.py`
- Create: `agent/v1/tests/test_finalize_answer.py`

**Interfaces:**
- Consumes: `build_ledger`, `snap_to_ledger` (already in `case_file.py`).
- Produces: `finalize_answer(clean: str, delegations: list) -> str` — the one normalization every to-be-submitted answer passes through.

**Order of operations matters:** snap the raw value FIRST (a verbatim ledger match must never be modified — a legit answer could contain `=`), then strip a leading `<label> = ` and snap again.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_finalize_answer.py`:

```python
from case_file import finalize_answer


def _deleg(answer):
    return {"answer": f"FINAL ANSWER: {answer}", "status": "solved",
            "worker": "senior#1", "spl_used": [], "sourcetypes": [],
            "iterations": 3, "cap_hit": False}


def test_strips_label_prefix():
    # Q331 regression: extractor kept 'UF = ' and it reached the scoreboard.
    assert finalize_answer("UF = 2059", []) == "2059"


def test_strip_then_snap_restores_ledger_form():
    delegs = [_deleg("1374")]
    assert finalize_answer("UF = 1374", delegs) == "1374"


def test_snap_wins_before_strip():
    # A verbatim ledger value containing '=' must never be stripped.
    delegs = [_deleg("user=root")]
    assert finalize_answer("user=root", delegs) == "user=root"


def test_plain_value_snaps_case():
    delegs = [_deleg("NullWeb_Admin")]
    assert finalize_answer("nullweb_admin", delegs) == "NullWeb_Admin"


def test_no_label_no_ledger_unchanged():
    assert finalize_answer("mkraeusen", []) == "mkraeusen"


def test_empty_is_safe():
    assert finalize_answer("", []) == ""
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_finalize_answer.py -v`
Expected: FAIL — `ImportError: cannot import name 'finalize_answer'`.

- [ ] **Step 3: Implement**

Append to `agent/v1/case_file.py` (after `snap_to_ledger`):

```python
# 'UF = 2059' — short alnum label, '=', then the value. Deliberately narrow so
# sentence-shaped answers are never touched.
_LABEL_PREFIX = re.compile(r'^\s*[A-Za-z][A-Za-z0-9_ ]{0,30}=\s*(?=\S)')


def finalize_answer(clean: str, delegations: list) -> str:
    """Last normalization before scoreboard submit (both the normal and the
    post-hint extract paths). Snap first — a verbatim ledger match is never
    modified — then strip a leading '<label> = ' and snap again. Q331
    regression: post-hint extractor emitted 'UF = 2059' and it was submitted
    raw because snap_to_ledger only ran inside joiner_node."""
    clean = (clean or "").strip()
    ledger = build_ledger(delegations)
    snapped = snap_to_ledger(clean, ledger)
    if snapped != clean:
        return snapped
    stripped = _LABEL_PREFIX.sub("", clean).strip()
    if stripped and stripped != clean:
        return snap_to_ledger(stripped, ledger)
    return clean
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_finalize_answer.py -v`
Expected: 6 passed.

- [ ] **Step 5: Changelog + commit**

Add to `docs/version_architecture/v1/v1.3.md` changelog: "Smoke-defect fix: `finalize_answer` in `case_file.py` — snap-first label-prefix strip, the single normalization for every to-be-submitted answer."

```bash
git add agent/v1/case_file.py agent/v1/tests/test_finalize_answer.py docs/version_architecture/v1/v1.3.md
git commit -m "fix(v1.3-planB): finalize_answer — label strip + snap for every submitted answer"
```

---

## Task 3: Wire `finalize_answer` at both extract sites

**Files:**
- Modify: `agent/v1/run_all_v1.py`

**Context:** two extractor call sites exist — the normal one (`run_all_v1.py:388-400`) and the post-hint one (`run_all_v1.py:421-426`). Both must route through `finalize_answer` so the hint path stops bypassing the snap.

- [ ] **Step 1: Import**

In `agent/v1/run_all_v1.py`, extend the existing import (line ~53, `from case_file import CaseFile, build_ledger`):

```python
from case_file import CaseFile, build_ledger, finalize_answer
```

- [ ] **Step 2: Normal extract site**

After the extract try/except block, immediately before `print(f"[EXTRACTOR] clean={clean!r}")` (line ~400), add:

```python
        clean = finalize_answer(clean, ctx.q_delegations)
```

- [ ] **Step 3: Post-hint extract site**

Inside the hint block, after the post-hint try/except, immediately before `print(f"[HINT] post-hint clean={clean!r}")` (line ~426), add:

```python
                    clean = finalize_answer(clean, ctx.q_delegations)
```

- [ ] **Step 4: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import run_all_v1; print('ok')"`

- [ ] **Step 5: Changelog + commit**

v1.3.md changelog: "Smoke-defect fix: both runner extract sites (normal + post-hint) route through `finalize_answer` — hint path no longer bypasses the ledger snap (Q331 `'UF = 2059'` regression)."

```bash
git add agent/v1/run_all_v1.py docs/version_architecture/v1/v1.3.md
git commit -m "fix(v1.3-planB): hint path routes through finalize_answer (no more snap bypass)"
```

---

## Task 4: Post-submit case-file reconciliation

**Files:**
- Modify: `agent/v1/case_file.py`, `agent/v1/run_all_v1.py`
- Create: `agent/v1/tests/test_reconcile_findings.py`

**Interfaces:**
- Consumes: `CaseFile.iter_findings()` / `.set_status()`.
- Produces: `reconcile_findings(case_file, qid: str, correct: bool) -> int` — number of findings demoted.

**Context:** the joiner marks everything `[verified]`; the scoreboard verdict is the only ground truth we get. When a question scores WRONG, its `verified` findings must drop to `hypothesis` so later planners re-verify instead of trusting them (the Q210→Q216 cascade class). Correct questions keep their findings. RECON findings are untouched (source_qid `"RECON"` is never a submitted qid). Only runs when the scoreboard submit actually succeeded — an SB outage must not demote anything.

- [ ] **Step 1: Write failing tests**

Create `agent/v1/tests/test_reconcile_findings.py`:

```python
from case_file import CaseFile, reconcile_findings


def test_wrong_verdict_demotes_verified_to_hypothesis(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("endpoint mined for 0 seconds", source_qid="Q216",
                         status="verified")
    other = cf.add_finding("password is ilovedavidverve", source_qid="Q303",
                           status="verified")
    n = reconcile_findings(cf, "Q216", correct=False)
    assert n == 1
    assert cf.get_finding(fid)["status"] == "hypothesis"
    assert cf.get_finding(other)["status"] == "verified"   # other qid untouched


def test_correct_verdict_keeps_verified(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("password is ilovedavidverve", source_qid="Q303",
                         status="verified")
    assert reconcile_findings(cf, "Q303", correct=True) == 0
    assert cf.get_finding(fid)["status"] == "verified"


def test_refuted_and_hypothesis_untouched_on_wrong(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    h = cf.add_finding("maybe", source_qid="Q330", status="hypothesis")
    r = cf.add_finding("nope", source_qid="Q330", status="refuted")
    assert reconcile_findings(cf, "Q330", correct=False) == 0
    assert cf.get_finding(h)["status"] == "hypothesis"
    assert cf.get_finding(r)["status"] == "refuted"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest agent/v1/tests/test_reconcile_findings.py -v`
Expected: FAIL — no `reconcile_findings`.

- [ ] **Step 3: Implement**

Append to `agent/v1/case_file.py`:

```python
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
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `python -m pytest agent/v1/tests/test_reconcile_findings.py -v`
Expected: 3 passed.

- [ ] **Step 5: Wire into the runner (inside the successful-submit branch only)**

In `agent/v1/run_all_v1.py`, extend the import: `from case_file import CaseFile, build_ledger, finalize_answer, reconcile_findings`.

In the submit block (line ~429), add the call INSIDE the `try`, after `verdict = ...` — so an SB outage (except branch) never demotes:

```python
        try:
            sb = scoreboard.submit(q_number, clean)
            pts_earned = sb.earned
            pts_earned = max(0, pts_earned - hint_cost)
            sb_correct = sb.correct
            earned_pts += pts_earned
            verdict = "[CORRECT]" if sb_correct else "[WRONG]"
            demoted = reconcile_findings(case_file, qid, sb_correct)
            if demoted:
                print(f"[CASE] verdict WRONG — demoted {demoted} finding(s) from {qid} to hypothesis")
        except Exception as exc:
            pts_earned, sb_correct = 0, False
            verdict = f"[SB UNAVAILABLE: {exc}]"
```

- [ ] **Step 6: Full suite + import check**

Run: `python -m pytest agent/v1/tests/ -q` — all green.
Run: `python -c "import sys; sys.path.insert(0,'agent'); sys.path.insert(0,'agent/v1'); import run_all_v1; print('ok')"`

- [ ] **Step 7: Changelog + commit**

v1.3.md changelog: "Smoke-defect fix: `reconcile_findings` — WRONG scoreboard verdict demotes that question's verified case findings to hypothesis (SB-outage-safe: only on successful submit); closes the verified-inflation hole the joiner prompt alone couldn't."

```bash
git add agent/v1/case_file.py agent/v1/run_all_v1.py agent/v1/tests/test_reconcile_findings.py docs/version_architecture/v1/v1.3.md
git commit -m "fix(v1.3-planB): wrong verdicts demote case findings to hypothesis (reconcile_findings)"
```

---

## Task 5: Verification micro-smoke (2 questions — NOT the full run)

**Files:** none — integration gate.

**Reminder: the full 56-question run stays forbidden until the user explicitly authorizes it.**

- [ ] **Step 1: Full unit suite**

Run: `python -m pytest agent/v1/tests/ -q`
Expected: baseline + 9 new tests, zero failures.

- [ ] **Step 2: Micro-smoke exercising both fixes**

Run: `python agent/v1/run_all_v1.py --ids Q216,Q331 --hints`

Report (mechanism-firing is the gate, correctness is bonus):

| Question | Fix under test | Signal to report |
|---|---|---|
| Q331 (1000) | finalize_answer on the hint path | if a hint fires, the submitted `clean` has NO label prefix (`UF = ` class) and, when it case-matches a ledger entry, is byte-identical to it |
| Q216 (1000) | reconcile_findings | if the verdict is WRONG, the `[CASE] verdict WRONG — demoted N finding(s)` line fires and `case_file.json` shows those findings at `hypothesis` |

Also report: `failed_delegations`, whether `[EXTRACTOR] clean=` values differ pre/post `finalize_answer` anywhere, and total est cost.

- [ ] **Step 3: Hand off to the human**

Report the micro-smoke signals and stop. The user decides if/when the full 56-Q run happens.

---

## Done criteria

- Defect record landed in `docs/version_architecture/v1/v1.3.md` (including the disproven encoding suspicion).
- `finalize_answer` guards BOTH extract sites; `reconcile_findings` runs only on successful submits.
- `python -m pytest agent/v1/tests/ -q` fully green.
- Micro-smoke signals reported; no full run without explicit user go-ahead.
