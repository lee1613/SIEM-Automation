# Design — Phase 2 Streamlit Replay Demo

**Date**: 2026-07-28
**Status**: Approved design, ready for implementation plan
**Scope**: Phase 2 only, as named in `docs/superpowers/specs/2026-07-27-readme-storefront-design.md` roadmap section. Live-run mode explicitly out of scope.

## Context

Phase 1 (README storefront) shipped: rewritten README, `scripts/run_eval.py` offline CLI
scorer, CI, `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md`. No runtime demo exists — visitors
can read numbers and logs but can't interact with anything in a browser. This spec covers
the Phase 2 roadmap item: a hosted, replay-only Streamlit dashboard.

## Decisions (locked with user)

1. **Demo mode**: replay only. Reads existing `log/v1/run_1.2` artifacts. No live agent
   execution, no Splunk, no API key, zero cost per visitor.
2. **Hosting**: Streamlit Community Cloud. Connect GitHub repo, entrypoint
   `streamlit_app/app.py`, branch `main`, auto-redeploy on push.
3. **Content scope**: two pages — Leaderboard (point-tier table) and Trajectory viewer
   (curated 4 questions: Q332/Q333 correct 1000pt hit, Q303/Q328 honest-refusal). Mirrors
   README section 4 exactly; not a full 56-question browser.
4. **Data source**: pre-extracted static JSON (`data/evaluation/demo_trajectories.json`),
   built once by a dev-time script from `log/v1/run_1.2/timeline.md` +
   `run_summary.json`. App never parses logs at runtime.
5. **App location**: `streamlit_app/` directory, own lightweight `requirements.txt`
   (streamlit, pandas) — kept separate from `agent/requirements.txt`'s heavy LLM/Splunk
   dependency tree.

## Architecture

```
streamlit_app/
  app.py                         # 2-page Streamlit app
  requirements.txt               # streamlit, pandas only
data/evaluation/
  leaderboard.json               # existing (Phase 1)
  demo_trajectories.json         # NEW — curated extract, 4 questions
scripts/
  extract_demo_trajectories.py   # NEW — one-shot, run_1.2 logs -> demo_trajectories.json
```

## Components

- **`app.py`**: `st.set_page_config` + `st.sidebar.radio` nav between two views.
  - Leaderboard view: reads `data/evaluation/leaderboard.json`, renders tier table
    (100/500/1000/overall) via `st.dataframe`.
  - Trajectory view: `st.selectbox` over the 4 curated question IDs, renders tool calls,
    reasoning, final answer, and correctness badge from `demo_trajectories.json`.
- **`extract_demo_trajectories.py`**: dev-time only, not deployed. Run once locally;
  output committed to git. Extracts Q332/Q333 and Q303/Q328 from
  `log/v1/run_1.2/timeline.md` + `run_summary.json`.

Illustrative schema for `demo_trajectories.json` (field names/shape, not real content):

```json
{
  "Q332": {
    "tier": 1000,
    "correct": true,
    "tool_calls": [{"tool": "search", "query": "...", "result_summary": "..."}],
    "reasoning": "...",
    "final_answer": "..."
  }
}
```

## Data flow

Build-time: `extract_demo_trajectories.py` -> `demo_trajectories.json` (committed,
rerun manually only if source logs change). Runtime: `app.py` does `json.load()` on two
static files — no log parsing, no network calls, no LLM calls at runtime. Fully offline,
zero per-visitor cost.

## Error handling

Data is static and checked in; main failure mode is a missing/malformed file. One
`try/except` at load time in `app.py`, falling back to `st.error()` — avoids a raw
traceback on a recruiter's screen. Not a deep error-handling surface; this is a
static-data viewer, not logic-bearing code.

## Testing

Ponytail-scale: one `assert`-based `demo()` check in `extract_demo_trajectories.py`
(under `if __name__ == "__main__"`) confirming all 4 expected question IDs land in
output with non-empty `tool_calls`. No test framework, no Streamlit UI tests.

## What is deliberately NOT built

- Live agent execution / Splunk connection — roadmap only, per Phase 1 spec's original
  "optional live mode" note.
- Full 56-question browser — only the 4 curated trajectories.
- `run_eval.py` in-browser execution — leaderboard + trajectories only.

## Verification

1. `python scripts/extract_demo_trajectories.py` produces
   `data/evaluation/demo_trajectories.json` with exactly 4 entries (Q332, Q333, Q303,
   Q328), each with non-empty `tool_calls`. `demo()` self-check passes.
2. `streamlit run streamlit_app/app.py` runs locally, both pages render without error,
   leaderboard numbers match `data/evaluation/leaderboard.json`.
3. Deployed on Streamlit Community Cloud from `main` branch, entrypoint
   `streamlit_app/app.py`; app loads without secrets configured.
4. `streamlit_app/requirements.txt` installs cleanly without pulling in
   `agent/requirements.txt`'s LLM/Splunk dependencies.
