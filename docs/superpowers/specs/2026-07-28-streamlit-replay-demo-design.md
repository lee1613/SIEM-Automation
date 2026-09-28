# Spec — Phase 2 Streamlit Replay Demo

**Date**: 2026-07-28 (updated same day after grilling session)
**Status**: Approved design, ready for implementation plan
**Scope**: Phase 2 only, as named in `docs/superpowers/specs/2026-07-27-readme-storefront-design.md`
roadmap section. Live-run mode explicitly out of scope.

## Problem Statement

Phase 1 shipped a rewritten README, an offline eval CLI (`scripts/run_eval.py`), CI, and
architecture/runbook docs. Someone landing on the repo — a recruiter, interviewer, or engineer
evaluating the project unattended, with no one narrating — can read numbers and static logs but
cannot see the agent reason, cannot see why a multi-agent hierarchy (SH orchestrator → Senior
worker → Extractor) was chosen over a single-agent approach, and cannot tell the difference
between a wrong answer and a deliberate refusal to guess. There is no interactive artifact that
makes the architecture's reasoning legible on its own, self-serve, with zero setup.

## Solution

A hosted, replay-only Streamlit app presented as a **linear guided story** (a step wizard, not a
free-roam sidebar), so a self-serve visitor sees the intended narrative in order rather than
landing on a raw data table first:

1. **Problem** — states the investigation scale (58 BOTSv3 questions, 100+ Splunk sourcetypes)
   and why naive single-agent prompting fails at that scale, framed as a real SOC problem, not
   competition trivia.
2. **Architecture** — explains the SH → Senior → Extractor hierarchy with a small abstract
   version of the same waterfall visual used later, so the pattern is recognized, not just read.
3. **Trajectory** — 6 curated real question walkthroughs (2 correct, 2 honest-refusal, 2
   wrong-answer) rendered as an indented, color-coded waterfall (blue=SH, green=Senior,
   amber=Extractor) proving the architecture live, with each tool call, reasoning line, and
   final answer visible.
4. **Score** — the leaderboard/tier table, plus a short, honest lesson-learned callout about the
   project's own cost-tracking data-integrity fix (no disputed dollar figures cited).

Visual direction: dark SOC/terminal theme (native Streamlit dark theme + monospace font via
`.streamlit/config.toml`), no CSS injection, no new dependency beyond the already-planned
`streamlit` + `pandas`.

## User Stories

1. As a self-serve visitor with no narrator, I want the app to open on a linear first step, so
   that I see the intended story order instead of landing on a raw table.
2. As a visitor unfamiliar with BOTSv3, I want the first step to explain the investigation scale
   and why it breaks naive prompting, so that the architecture step that follows makes sense.
3. As a visitor, I want to see the SH → Senior → Extractor roles explained with a small abstract
   diagram before seeing real data, so that I recognize the pattern when I see it applied.
4. As a visitor, I want the trajectory step to visually show which tier (SH/Senior/Extractor)
   produced which tool call or reasoning line, so that the delegation is provable, not just
   claimed in prose.
5. As a visitor, I want the hierarchy rendered as an indented, color-coded waterfall using the
   same three colors consistently (blue/green/amber), so that I learn the visual code once and
   reuse it across every example.
6. As a visitor, I want to browse 6 curated questions spanning three outcomes (correct,
   honest-refusal, wrong-answer), so that I see the full behavior spectrum, not a cherry-picked
   highlight reel.
7. As a visitor, I want the two honest-refusal cases badged explicitly as "Refused to guess"
   (not "Incorrect"), with a one-line rationale, so that I understand it as a deliberate safety
   behavior even on a skim.
8. As a visitor, I want the two wrong-answer cases shown plainly as incorrect, so that the
   refusal cases read as a genuine contrast rather than the agent hiding all its failures.
9. As a visitor, I want a final Score step with the tier/leaderboard table, so that I can see
   overall performance, not just the 6 curated examples.
10. As a visitor, I want a short, honest engineering lesson in the Score step about a
    cost-tracking bug that was found and fixed, so that I see evidence of engineering rigor
    without being shown a dollar figure the team can't fully stand behind.
11. As the developer, I want the trajectory data extracted once at dev time into a static JSON
    file with tier-tagged entries, so that the deployed app never parses logs at runtime and
    never pays per-visitor compute/LLM cost.
12. As the developer, I want the app's dependency footprint (`streamlit` + `pandas` only) kept
    separate from `agent/requirements.txt`'s heavy LLM/Splunk dependency tree, so that
    Streamlit Community Cloud installs cleanly and fast.
13. As the developer, I want the Architecture step's abstract diagram and the Trajectory step's
    real diagram to share the same rendering function/visual language, so that the "concept,
    then proof" narrative arc is guaranteed to be visually consistent rather than hand-matched.
14. As the developer, I want one `assert`-based self-check in the extraction script confirming
    all 6 expected question IDs land in output with non-empty, tier-tagged tool calls, so that a
    malformed extraction is caught before commit, without a test framework.
15. As a visitor on a failure path, I want a plain `st.error()` instead of a raw traceback if a
    data file is missing or malformed, so that the demo degrades gracefully instead of looking
    broken.

## Implementation Decisions

- **Navigation**: single-page step wizard using `st.session_state` to track current step index;
  Next/Back controls advance/retreat through Problem → Architecture → Trajectory → Score. Not
  the sidebar `st.radio` nav from the original design — free-roam nav let a visitor skip the
  setup needed for "why architecture matters" to land.
- **Visual theme**: `.streamlit/config.toml` sets `base="dark"` and `font="monospace"` — both
  native Streamlit theme options, no CSS injection. Tier color-coding uses Streamlit's native
  colored markdown syntax (`:blue[...]`, `:green[...]`, `:orange[...]`) and/or `st.badge`, not
  custom HTML.
- **Hierarchy rendering**: a shared render function takes a list of tier-tagged entries and
  renders each as an indented `st.container`/`st.expander` block, indentation depth and color
  keyed to tier (SH=blue, Senior=green, Extractor=amber). The Architecture step calls this
  function with small abstract/placeholder entries; the Trajectory step calls the same function
  with real per-question entries. One function, two call sites — guarantees visual consistency.
- **`demo_trajectories.json` schema change**: restructured from a flat `tool_calls` list (as in
  the original design) to tier-tagged entries per question, e.g. each question has an ordered
  list of `{tier: "sh"|"senior"|"extractor", type: "plan"|"tool_call"|"reasoning"|"answer",
  content: ...}` records, so the render function can group/indent/color by tier. Still committed
  static JSON, still `json.load()` at runtime, still zero log parsing in the deployed app.
- **Curated question set expanded 4 → 6**: 2 correct (Q332, Q333, 1000pt), 2 honest-refusal
  (Q303, Q328), 2 wrong-answer (2 of Q216/Q217/Q224/Q329/Q330/Q331 — the 1000pt residue list from
  `v0.2_improvement_plans.md` — selected during extraction for the clearest, most instructive
  wrong-reasoning trace).
- **Refusal badge**: Q303/Q328 display a distinct badge reading "Refused to guess" (not
  "Incorrect"), with a one-line rationale that the agent declined to fabricate an answer under
  uncertainty. Wrong-answer entries use a plain "Incorrect" badge with no reframing, so the
  refusal framing reads as a genuine, earned contrast.
- **Score step cost narrative**: no dollar figure is displayed. The callout describes the
  cost-tracking data-integrity fix (`load_cost` previously defaulted untracked runs to a false
  `$0.00`; now returns `None`/"not tracked" instead, per commit `8aa9fa1`) as evidence that cost
  numbers are validated before being trusted, without citing v0.1's `$0.63` or v0.2's `$31.36` —
  a run restart is known to have overwritten v0.1's recorded cost, making any multiplier
  comparison between the two unsafe to publish.
- **App location**: unchanged from original design — `streamlit_app/app.py`,
  `streamlit_app/requirements.txt` (`streamlit`, `pandas` only), `datasets/evaluation/
  demo_trajectories.json` (corrected from the original draft's `data/evaluation/` — the real
  existing leaderboard artifact lives at `datasets/evaluation/leaderboard.json`, confirmed by
  reading `scripts/run_eval.py`), `scripts/extract_demo_trajectories.py`.
  `.streamlit/config.toml` added at repo root for theme (Streamlit Community Cloud runs
  `streamlit run streamlit_app/app.py` with the repo root as CWD, which is where Streamlit
  resolves project-level `.streamlit/config.toml` from).
- **Hosting**: unchanged — Streamlit Community Cloud, GitHub-connected, entrypoint
  `streamlit_app/app.py`, branch `main`, auto-redeploy on push.
- **Data flow**: unchanged in principle — build-time extraction script produces committed JSON,
  runtime app only reads static files, zero network/LLM calls per visitor.

## Testing Decisions

- Ponytail-scale: one `assert`-based `demo()` self-check in `extract_demo_trajectories.py`
  (under `if __name__ == "__main__"`), updated from 4 to 6 expected question IDs
  (Q332, Q333, Q303, Q328, plus the 2 selected wrong-answer IDs), each with a non-empty,
  tier-tagged entry list. No test framework, no Streamlit UI tests — this is a static-data
  viewer, not logic-bearing code, consistent with the original spec's testing posture.
- The shared hierarchy render function is exercised implicitly by both the Architecture step
  (abstract data) and Trajectory step (real data) at `streamlit run` time; no separate unit test
  is planned given the ponytail-scale testing decision already made for this feature.

## Out of Scope

- Live agent execution / Splunk connection — roadmap-only, per Phase 1 spec's original
  "optional live mode" note.
- Full 56-question browser — only the 6 curated trajectories.
- `run_eval.py` in-browser execution — leaderboard + trajectories only, both from static JSON.
- Publishing or citing specific dollar cost figures for v0.1/v0.2 runs — the v0.1 baseline is
  known-unreliable (overwritten by a run restart), so no dollar-based comparison is shown
  publicly; only the qualitative data-integrity-fix story is told.
- Mobile-specific layout optimization — not raised as a requirement; default Streamlit
  responsiveness is assumed sufficient for a self-serve repo demo.
- Live-narrated/presenter mode — the demo is designed to be self-explanatory without a guide
  present, not a slide deck for someone driving live.

## Further Notes

- Cost figures were independently verified before this decision was made: v0.1 ($0.63) and
  v0.2 ($31.36) both come from real, non-zero `token_usage` blocks (not the "silently reported
  as $0" bug case that commit `8aa9fa1` fixed) — but the user has since flagged that v0.1's
  figure specifically was overwritten by a run restart and is not trustworthy as a baseline.
  The Score step's narrative was redesigned around this: tell the (accurate, verifiable) story
  of the integrity fix itself, and drop the (disputed) multiplier comparison entirely.
- The Architecture-step-reuses-Trajectory-step-render-function decision exists specifically to
  make the "concept, then proof" narrative arc self-enforcing — if the two steps ever visually
  diverge, it should be because the shared function changed, not because someone hand-copied and
  drifted one of the two call sites.
