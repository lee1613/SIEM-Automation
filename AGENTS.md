# AGENTS.md — Project Instructions

## Agent Testing Behaviour

When running or testing the Splunk SIEM agent (`agent/splunk_agent.py`):

- **Report** the full agent output, including every tool call made and the result returned.
- **Present** the model's decision-making process — what it searched for, why, and how it reached its conclusion.
- **Suggest** fixes if something goes wrong, but do NOT apply any code changes unless the user explicitly asks.

## Running the Agent Against BOTSv3 (Scoreboard Mode)

When the user asks the agent to attempt BOTSv3 questions (e.g. "run all questions", "attempt the scoreboard", "test the agent on BOTS"), use the **Splunk CTF scoreboard** for scoring instead of any internal scoring script.

### Architecture

- **Scoreboard app**: `SA-ctf_scoreboard` + `SA-ctf_scoreboard_admin`, installed at `C:\Program Files\Splunk\etc\apps\`
- **Questions KV store**: `SA-ctf_scoreboard / ctf_questions` (58 BOTSv3 questions)
- **Answers KV store**: `SA-ctf_scoreboard_admin / ctf_answers` (58 correct answers)
- **Scoring rule**: `submitted_answer.lower().strip() == correct_answer.lower().strip()` — exact match only, same as the official controller
- **Submission log**: every answer (correct or not) is written to `index=scoreboard sourcetype=scoreboard` in real time
- **Scoreboard UI**: `http://localhost:8000/en-US/app/SA-ctf_scoreboard/`

> Note: The SA-ctf_scoreboard web CherryPy controller (`/en-US/custom/SA-ctf_scoreboard/submit_question`) does NOT load on Splunk 9/10 Windows due to `No module named 'splunklib.six.moves'`. The `ScoreboardClient` in `agent/scoreboard_client.py` bypasses this by talking directly to the KV store REST API and writing events to `index=scoreboard` — producing the same scoring outcome.

### Canonical Run Workflow

1. **Run the agent on all questions** using `agent/run_all.py`. This script:
   - Loads questions from `datasets/botsv3_questions.json`
   - Runs `run_agent()` for each question, streaming all tool calls and thinking to both console and a timestamped log file in `results/`
   - After each question, calls `ScoreboardClient.submit()` to post the answer to the Splunk scoreboard
   - Saves incremental JSON results to `results/run_YYYYMMDD_HHMMSS.json`
   - Prints the final scoreboard at the end

2. **Check the live score** at any time:
   ```python
   from agent.scoreboard_client import ScoreboardClient
   sb = ScoreboardClient("https://localhost:8089", SPLUNK_USER, SPLUNK_PASS)
   print(sb.get_score())
   ```
   Or in Splunk: `index=scoreboard sourcetype=scoreboard | rex "Result=(?P<r>[^,]+)" | stats count by r`

3. **Setup** (one-time, already done):
   - Both CTF apps cloned into Splunk apps directory
   - Data loaded via `agent/setup_scoreboard.py --skip-restart`
   - `scoreboard` and `scoreboard_admin` indexes exist
   - EULA accepted and `ctf_users` entry created for the Splunk admin user

### Key Files

| File | Purpose |
|------|---------|
| `agent/splunk_agent.py` | Main SIEM agent (Llama 3.3 + Splunk tools) |
| `agent/scoreboard_client.py` | Submits answers to `ctf_answers` KV store; logs to `index=scoreboard` |
| `agent/run_all.py` | Runs agent on all questions and scores via scoreboard |
| `agent/setup_scoreboard.py` | One-time setup: loads KV data, creates EULA/user |
| `agent/botsv3_fields.json` | Local field manifest (102 sourcetypes, searched by agent) |
| `datasets/botsv3/ctf_questions.csv` | Official BOTSv3 questions (loaded into `ctf_questions` KV store) |
| `datasets/botsv3/ctf_answers.csv` | Official BOTSv3 answers (loaded into `ctf_answers` KV store) |
| `datasets/botsv3/ctf_hints.csv` | Official BOTSv3 hints (loaded into `ctf_hints` KV store) |
| `datasets/botsv3_questions.json` | Questions in JSON format (used by `run_all.py`) |
| `datasets/botsv3_answers.json` | Answers in JSON format (reference only — scoring uses KV store) |

## Cost-Limited Runs (active policy)

**No full `run_all_v1.py` runs until the user lifts this.** v1.2's full run cost $31.36 (50x
v1.1) with net-zero score gain — future runs must stay smoke-test scale.

- Every future agent run (v1 or later) is a **smoke test on ~5 hard questions**, not a full
  56-question run. Purpose: exercise reasoning capability / verify a fix, not score.
- Run via `python agent/v1/run_all_v1.py --ids <5 question ids>`. Output goes to `log/temp/`
  per the existing smoke-test rule below (unversioned, not cost-tracked, not compared in docs).
- Default "hard" set (pick 5 from this list unless the user names specific IDs): the 1000-pt
  residue that survived two full runs per `docs/version_architecture/v1/v1.2_improvement_plans.md`
  — **Q216, Q217, Q224, Q328, Q329, Q330, Q331**.
- Escalating back to a full run against the scoreboard requires explicit user go-ahead.

## Versioning & Logging (v1+ multi-agent)

### Every change must be recorded in the current in-progress version's doc

A version `v1.x` is considered **in progress** from the moment any code change is made after
its predecessor's full run, until `v1.x`'s own first full `run_all_v1.py` run completes. While
`v1.x` is in progress:

- **Every code change**, no matter how small, must be accompanied by a one-line (or short
  paragraph, if significant) entry in `docs/version_architecture/v1/v1.x.md`'s changelog —
  written **in the same turn as the change**, not deferred. A simple sentence is enough for
  small/mechanical changes (e.g. "Remove extractor validation node"). Give a fuller description
  — what changed, why, and how it was verified — for anything that affects correctness,
  architecture, or the scoring pipeline (e.g. swapping the planning pattern, fixing a
  persistence bug).
- If `docs/version_architecture/v1/v1.x.md` doesn't exist yet, create it with a `## Changelog`
  section (see `v1.2.md` for the template) rather than waiting for the version to be "finished."
- Once `v1.x`'s first full run completes, fold the changelog into a proper "What changed vs
  v1.(x-1)" comparison section (see `v1.1.md` for the target shape) and start a fresh `v1.(x+1)`
  changelog for whatever comes next.

When a new version (e.g. `v1.x`, `v2.x`) is run **against the full scoreboard**:

1. **Update `docs/version_architecture/`** — finalize the version's architecture doc
   (`docs/version_architecture/v1/v1.x.md`) and describe **how it compares to the previous
   version** (what changed and why) — this supersedes the running changelog kept during
   development.
2. **Update `docs/scoreboard_result/`** — write the version's result doc
   (`docs/scoreboard_result/v1/v1.x.md`) including **which questions were not answered
   correctly**.
3. **Prompt the user for the run's cost in dollars** — do not guess it; the user will
   provide the figure to record in the result doc.

Logging rules:
- **Only full runs are logged** under `log/v1/run_1.x/` (auto-incrementing). Run with
  `python agent/v1/run_all_v1.py` (no `--ids`/`--limit`).
- **Test/smoke runs** (`--ids` or `--limit`) go to `log/temp/` and are NOT versioned, NOT
  compared in docs, and NOT cost-tracked.
- Each run produces hierarchical logs: `SH/`, `Senior Splunk/` (and `Junior Splunk/` from
  v1.1), `Extractor/`, a `timeline.md` sequential narrative, and `run_summary.json` (which
  carries `failed_delegations` and each worker's full state).

### v1 Key Files

| File | Purpose |
|------|---------|
| `agent/v1/orchestrator.py` | SH mastermind: persistent-memory planning graph + `spawn_senior` |
| `agent/v1/splunk_subagent.py` | Senior worker pool (reuses v0 graph); structured findings |
| `agent/v1/extractor.py` | Prose-strip to bare answer; single scoreboard submit |
| `agent/v1/agent_logger.py` | Hierarchical `RunLogger` + `LogCapture` |
| `agent/v1/run_all_v1.py` | v1 runner (full run → `log/v1/run_1.x/`; test → `log/temp/`) |
