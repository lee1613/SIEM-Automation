# Design — Phase 1 "Digital Storefront" (recruiter-facing README + repo restructure)

**Date**: 2026-07-27
**Status**: Approved design, ready for implementation plan
**Scope**: Phase 1 only. Streamlit dashboard + mock-Splunk sandbox = Phase 2 (separate spec).

## Context

The current `README.md` documents a *dataset download*, not the substantial agent
that now exists. The real work — a 3-tier multi-model orchestration (SH planner +
Senior workers + Extractor), grounding guards, adjudication, self-consistency
sampling, cost tracking, and a v0.0.0→v0.3 version history scoring **26/56 (46.4%)** on
BOTSv3 — is invisible to anyone opening the repo. The goal is a recruiter-facing
"digital storefront": a README and repo layout that read as an actively maintained,
production-grade engineering pipeline **using only real numbers**. No fabricated
metrics, no fake "100% passing" badges — the real 46.4% on a hard SOC benchmark,
framed well, survives a recruiter actually reading the code.

## Decisions (locked with user)

1. **Demo engine**: replay-now / live-later. Phase 1 ships no runtime demo; the
   README roadmap names the Streamlit *replay* demo (portable, no API key) as Phase 2.
2. **Scope**: Phase 1 storefront only.
3. **Leaderboard**: sliced **by point tier** (real, exact, computable).
4. **Framing**: honest-but-polished. Badges reflect real state.
5. **`datasets/` → `data/`**: rename the directory (retain all contents), add
   `data/evaluation/` alongside.
6. **ARCHITECTURE.md**: describes the **most current** architecture (v0.3 / Plan C).
7. **run_eval**: prints **real per-run cost** (from `run_summary.json` token_usage).

## Real numbers (source of truth = `log/v0/run_0.2/run_summary.json` + result docs)

Point-tier leaderboard, computed from v0.2 per-question results:

| Tier | Solved / Total | Rate |
|------|:---:|:---:|
| 100 pt | 15 / 24 | 62.5% |
| 500 pt | 9 / 23 | 39.1% |
| 1000 pt | 2 / 9 | 22.2% |
| **Overall** | **26 / 56** | **46.4%** — 8000 / 22900 pts |

Story the numbers tell (true): the 1000pt questions are the frontier. v0.1 hit the
same 26/56 for **$0.63**; v0.2 held score but cost **$31.36** due to failed-delegation
blowup — a real, documented engineering lesson, not a regression to hide.

## Deliverables

### 1. Repo restructure (`datasets/` → `data/`, additive `evaluation/`)

```
data/                        # RENAMED from datasets/ (all contents retained)
  ├── botsv3/                #   ctf_questions.csv, ctf_answers.csv, ctf_hints.csv, botsv3/ index
  ├── botsv3_questions.json
  ├── botsv3_answers.json
  └── evaluation/            # NEW
        ├── benchmark_v0.2.json   # per-question {id, tier, correct, submitted, grounded}
        └── leaderboard.json      # per-tier + overall + per-version cost/score (README + run_eval read this)
.github/workflows/ci.yml     # NEW — ruff lint + pytest on agent/v0/tests
docs/ARCHITECTURE.md         # NEW — system layout + agent-planning flow (v0.3 / Plan C)
docs/RUNBOOK.md              # NEW — recruiter step-by-step setup + how to run eval
scripts/run_eval.py          # NEW — offline scorer (subset → accuracy + cost)
README.md                    # REWRITE — the storefront
```

**Rename mechanics**: `git mv datasets data`, then update hardcoded paths:
- `agent/v0/run_all_v0.py` lines 70, 71, 280, 281, 284 (`"datasets"` → `"data"`)
- `agent/setup_scoreboard.py` (grep `datasets` → `data`)
- `.gitignore` (`datasets/botsv3/botsv3_data_set.tgz` → `data/...`)
- Docs referencing the path: `docs/BOTS_V3_SETUP.md`, `docs/spec.md`, `AGENTS.md`, `CLAUDE.md`
- No other `.py` files reference the string (verified by grep).

Untouched: `agent/`, `docs/version_architecture/`, `docs/scoreboard_result/`, `log/`.

### 2. `scripts/run_eval.py` — offline accuracy + cost scorer

Ponytail: the lazy *real* thing. No live LLM calls, no Splunk, recruiter-runnable in
a second. Reuses existing artifacts rather than re-running the agent.

- Reads submitted answers from a run's `scoreboard_submissions.json` and cost from the
  same run's `run_summary.json` (default: latest `log/v0/run_0.*`).
- Scores against `data/botsv3_answers.json` using the **same exact-match rule** as the
  scoreboard (`submitted.lower().strip() == answer.lower().strip()` — mirror
  `ScoreboardClient`, do not reinvent).
- `--tier {100,500,1000}` / `--ids Q216,Q331` subset filters.
- Prints: accuracy (n correct / n in subset), points, and **real cost** =
  sum of `token_usage[*].estimated_usd` from the run (per-model breakdown + total).
- `--live` flag: documented as roadmap only — delegates to existing `run_all_v0.py`
  (needs Splunk + API key), not implemented in Phase 1.
- One `assert`-based `__main__`/`demo()` self-check on the scoring function
  (known input → known accuracy), per ponytail. No test framework.

### 3. `.github/workflows/ci.yml`

Real CI, honest badge. On push/PR: install `agent/requirements.txt` + ruff, run
`ruff check`, run `pytest agent/v0/tests` (~20 existing tests). Badge in README points
at the workflow's real status — green because the tests genuinely pass, not asserted.

### 4. `docs/ARCHITECTURE.md`

Synthesized from `docs/version_architecture/v0/v0.3.md` (most current, Plan C):
system layout, the SH→Senior→Extractor flow, adjudication / escalation / dual-track /
self-consistency sampling. One ASCII flow diagram (reused in README, condensed).

### 5. `docs/RUNBOOK.md`

Recruiter-oriented: prerequisites, clone, `pip install -r agent/requirements.txt`,
run `scripts/run_eval.py` for an instant offline score, and (roadmap) the live-run
path via `run_all_v0.py`. Distilled from `docs/BOTS_V3_SETUP.md` (which stays as the
deep Splunk-install reference).

### 6. `README.md` (rewrite) — section order

1. **Hero** — one-line pitch + 3 real badges (CI status, success rate 46.4%, framework).
2. **Leaderboard** — the point-tier table above, note it's read from `leaderboard.json`.
3. **Architecture** — condensed prose + ASCII agent-flow; link to `docs/ARCHITECTURE.md`.
4. **Agent Trajectory Logs** — 2 concise real examples pulled from `log/v0/run_0.2/timeline.md`:
   one correct 1000pt CVE hit (Q332/Q333), one honest-refusal (grounding guard, e.g.
   Q303/Q328). Each ≤10 lines, each links to full `docs/scoreboard_result/v0/v0.2.md`
   and the run's `timeline.md`. "Show more" = the linked files, not README bloat.
5. **Quick Start (offline eval)** — `python scripts/run_eval.py --tier 1000`; shows
   accuracy + cost. Prerequisites: Python 3.10+, no API key for offline mode.
6. **Lessons Learned** — living section, real insights (each 1–3 lines):
   grounding-guard trade (honest refusal beats fabrication in a real SIEM);
   failed-delegation cost blowup (46.4% at $0.63 vs $31.36 — same score, 50× cost);
   self-consistency 3× sampling on high-value metrics questions; extractor
   over-trimming; the 1000pt frontier. User keeps appending here.
7. **Roadmap** — Phase 2 Streamlit *replay* dashboard (portable, no key) + optional
   live mode; cap replan rounds for high-value questions (from v0.2 open questions).

## What is deliberately NOT built (Phase 1)

- Streamlit dashboard / mock-Splunk sandbox → Phase 2.
- Live `run_eval` execution → roadmap flag only.
- No new agent-behavior code → this is docs + tooling + a mechanical rename, so the
  CLAUDE.md per-version changelog rule does not apply (no `v0.x.md` entry needed).

## Verification

1. `git mv` + path edits: `grep -rn "datasets" agent/ .gitignore` returns nothing;
   importing / dry-running `agent/v0/run_all_v0.py` resolves `data/botsv3_questions.json`
   without a path error.
2. `pytest agent/v0/tests` still green after the rename.
3. `python scripts/run_eval.py --tier 1000` prints **2/9 = 22.2%** and a non-zero USD
   cost matching the v0.2 doc figure; `--ids Q332,Q333` prints **2/2 = 100%**.
   The `demo()` self-check asserts a known subset scores as expected.
4. README badges render; leaderboard table matches `leaderboard.json`; every
   "show more" link resolves to a real file.
5. CI workflow runs green on a push (ruff + pytest).
