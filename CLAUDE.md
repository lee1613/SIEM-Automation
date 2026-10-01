# CLAUDE.md — Project Instructions

## Project

A SIEM agent that answers the BOTSv3 capture-the-flag questions against Splunk (`index=botsv3`).

- **v0 multi-agent** (`agent/v0/`): **SH** (GPT-5.4) orchestrates and holds cross-question memory;
  **Senior Splunk** workers (GLM-5.3) run the searches. SH never queries Splunk itself.
- **v0.0.0 baseline** (`agent/splunk_agent.py`): the single-agent graph, its tools and its system prompt.
  The v0 seniors reuse it.

## Key files

| File | Purpose |
|------|---------|
| `agent/splunk_agent.py` | v0.0.0 single agent; Splunk tools and system prompt shared with the v0 seniors |
| `agent/botsv3_fields.json` | Local field manifest (102 sourcetypes, searched by the agent) |
| `agent/local_scoreboard.py` | Grades answers against the official CSVs (used by `run_all_v0.py`) |
| `agent/v0/run_all_v0.py` | v0 runner: full runs, smoke runs, resume |
| `agent/v0/sh_loop.py` | SH conversational loop (`--loop conversational`, the default) |
| `agent/v0/orchestrator.py` | SH planner/executor/joiner graph (`--loop compiler`, kept for A/B) |
| `agent/v0/splunk_subagent.py`, `senior_session.py` | Senior worker pool and sessions; structured findings via `submit_finding` |
| `agent/v0/premise.py`, `validator.py` | Premise ledger; blind validator for a load-bearing premise |
| `agent/v0/sh_memory.py` | Per-question summaries that serve as SH's cross-question memory |
| `agent/v0/agent_logger.py` | Hierarchical `RunLogger` + `LogCapture` |
| `agent/v0/usage_tracker.py` | Token and cost tracking; `PRICES_PER_1M` |
| `datasets/botsv3_questions.json` | Questions read by the runner |
| `datasets/botsv3/ctf_questions.csv`, `ctf_answers.csv` | Official questions and answers; `LocalScoreboard` grades from these |
| `datasets/botsv3/ctf_hints.csv` | Official hints (bought with `--hints`) |
| `datasets/botsv3_answers.json` | Answers in JSON (reference only; scoring uses `ctf_answers.csv`) |
| `agent/scoreboard_client.py`, `agent/setup_scoreboard.py` | Legacy Splunk CTF scoreboard client and setup (see Scoring) |

## Repository layout

```
agent/                         code: splunk_agent.py (v0.0.0), local_scoreboard.py, v0/ (multi-agent + tests)
datasets/                      questions, answers, hints, field manifests
docs/
  version_architecture/v0/     one architecture doc per version (changelog while in progress)
  scoreboard_result/v0/        one result doc per full run, plus that run's raw data beside it
                               (v0.0.0_full_run.json / .log back v0.0.0.md)
  superpowers/{plans,specs}/   design plans and specs
  agents/                      tooling notes for coding agents
  *.md                         setup, runbook, architecture and handover notes
log/
  v0/v0.<minor>/               filed runs: full runs, 5+ question smoke runs, intermediate/ (see Logging)
  root_cause_analysis/         one RCA timeline per minor version
  temp/                        staging for runs in progress; never committed
```

There is no top-level `results/` folder. A run's raw output lives in its `log/v0/` folder, and raw data that a
result doc reports on sits next to that doc in `docs/scoreboard_result/v0/`. Do not create new output folders
outside this layout.

## Working with the agent

### Testing behaviour

When running or testing the agent (`agent/splunk_agent.py` or `agent/v0/run_all_v0.py`):

- **Report** the full agent output, including every tool call made and the result returned.
- **Present** the model's decision-making process — what it searched for, why, and how it reached its conclusion.
- **Suggest** fixes if something goes wrong, but do NOT apply any code changes unless the user explicitly asks.

### Run policy

- **A full run needs the user's permission every time.** Never start one on your own.
- **Smoke tests are the default** for verifying a fix: `python agent/v0/run_all_v0.py --ids <ids>`.
  Output goes to `log/temp/` and is then filed (see Logging).
- **Default "hard" set** for smoke tests (pick 5 unless the user names IDs): the 1000-pt residue in
  `docs/version_architecture/v0/v0.2_improvement_plans.md` — **Q216, Q217, Q224, Q328, Q329, Q330, Q331**.
- **New model or provider:** ask the user for its price and add a row to `PRICES_PER_1M` in
  `agent/v0/usage_tracker.py`.
- **Run cost:** read it from the run's `run_summary.json` (`token_usage` → per-model `estimated_usd` and
  `__total__`). Do not ask the user for it. Break it out by role, with the senior's share shown; the figure
  comes from our price table, not a bill.

### Scoring

`run_all_v0.py` submits each answer to `LocalScoreboard`, which grades against the official CSVs with the
scoreboard's own rule: `submitted.lower().strip() == correct.lower().strip()` (exact match). Every run
writes its submissions to `scoreboard_submissions.json` in the run folder.

The Splunk CTF scoreboard (`SA-ctf_scoreboard` apps, `ctf_questions` / `ctf_answers` KV stores,
`index=scoreboard`) belongs to the v0.0.0 path through `ScoreboardClient`. The v0 runner does not use it,
and `local_scoreboard.py`'s docstring records that the KV store is unavailable on this host.

## Versioning

- The whole repo is in development, so every version is `v0.x`; `v1` is reserved for the first published
  release. The single-agent baseline is `v0.0.0`. Names such as `v1.4.5` in old logs and notes mean `v0.4.5`
  (renumbered 2026-09-28).
- A version `v0.x` is **in progress** from the first code change after its predecessor's full run until its
  own first full run completes.

### While a version is in progress

Every code change, however small, gets an entry in `docs/version_architecture/v0/v0.x.md`'s `## Changelog`,
written **in the same turn as the change**. A sentence is enough for a mechanical change. For anything that
affects correctness, architecture or the scoring pipeline, say what changed, why, and how it was verified.
If the doc doesn't exist yet, create it with a `## Changelog` section (template: `v0.2.md`).

### When a version's first full run completes

In the same turn:

1. **Architecture doc** — fold the changelog into `docs/version_architecture/v0/v0.x.md` as a "What changed
   vs v0.(x-1)" comparison (target shape: `v0.1.md`), then start a fresh `v0.(x+1)` changelog.
2. **Result doc** — write `docs/scoreboard_result/v0/v0.x.md`, including which questions were not answered
   correctly and the run's cost (from `run_summary.json`, per the Run policy). Cite the run by its filed
   `log/v0/` path.
3. **Root cause analysis** — see below.
4. **README** — see below.

## Logging

Each run produces hierarchical logs: `SH/`, `Senior Splunk/` (and `Junior Splunk/` from v0.1), a
`timeline.md` sequential narrative, `scoreboard_submissions.json`, and `run_summary.json` (which carries
`failed_delegations` and each worker's full state).

- **Full runs** go straight to `log/v0/v0.<minor>/v<version>_<senior-model>_full_r<N>/`
  (e.g. `log/v0/v0.4/v0.4.5_glm-5.3_full_r1/`; `N` auto-increments for repeat runs). Start one with
  `python agent/v0/run_all_v0.py --version 0.5.0` (no `--ids`/`--limit`); the runner refuses a new full
  run without `--version`.
- **Resume** a full run with `--run-name v0.5/v0.5.0_glm-5.3_full_r1`. Relaunching with `--ids` alone
  starts a new run folder and a new LangSmith project.
- **Test/smoke runs** (`--ids` or `--limit`) are written to `log/temp/`, which is a **staging area only**.
  As soon as a run finishes, move it under its version in `log/v0/v0.<minor>/` and commit it in the same
  turn. Never leave a finished run in `log/temp/` and never commit anything there.
  - A run covering **5 or more questions** sits at the version root
    (`log/v0/v0.4/v0.4.1_glm-5.3_smoke5_r1/`).
  - A run covering **fewer than 5 questions** goes in that version's `intermediate/` subfolder
    (`log/v0/v0.4/intermediate/v0.4.3_validator_Q216_r2/`).
  - Name the folder `v0.<minor>.<patch>_<senior-model>_<label>_r<N>`.
  - Console output from a background launch (`.out`/`.err`) goes inside the run's folder as
    `console.out` / `console.err` (a full run's resumes go in `console/`), never loose beside it.
- **Versions stay separate:** v0.3 runs never sit under v0.4.
- **Cite filed paths.** Everything that cites a run — root cause analyses, result docs, the README, the
  version changelog — cites its path under `log/v0/`, never `log/temp/`. File and commit the run before
  writing about it.
- Full runs before v0.3 (`log/v0/run_0.0` to `run_0.2`) keep their original folder names.
- **Unused runs are deleted.** A run that no doc, RCA or README cites is not kept; delete it rather than
  filing it.

## Root cause analysis after every run

After **every full run, and every smoke run of 5 or more questions**, analyse every question not answered
correctly, in the same turn the run finishes:

- Work out **why** each question failed from the run's logs (conversation, reports, premise ledger, tool
  output), not from the final answer alone. Group the failures into root-cause categories (for example: held
  the answer but never submitted, cross-question contamination, missing capability such as web search,
  search miss, right evidence but wrong value) and name the fix and target version for each.
- Record it in `log/root_cause_analysis/v0.<minor>.md` — **one file per minor version**, holding a
  **timeline** with one dated entry per run, oldest first, appended rather than rewritten. Each entry names
  the run directory, the score, the outcomes (correct / wrong submitted / refused), a table of root causes
  with questions and points, and what resolves each one.
- Runs under 5 questions are not analysed here; their findings go in the version's changelog.

## README shows the latest result, RCA and forecast

After every full run (and after an RCA that changes the plan), update `README.md` so it shows:

1. **The most advanced full run's result** and its version (score, points, cost, latency).
2. **The latest root cause analysis**: its categories and a link to its `log/root_cause_analysis/` file.
3. **The anticipated result once those root causes are resolved**, labelled as a forecast with its basis —
   the prediction for the next patch version that carries the fixes (the RCA of v0.5.0 is resolved by
   v0.5.1, so the README forecasts v0.5.1).
