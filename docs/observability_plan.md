# Observability, Cost & Latency Tracking Plan (independent of v1.2 architecture work)

> **Status**: Design proposal. No code changed by this document.
> **Evidence base**: audit of `agent/v1/` (usage_tracker.py, agent_logger.py, run_all_v1.py),
> `log/v1/run_1.1/` contents, and a live probe of the LangSmith APAC API
> (project `V1.1`, 17,856 runs; 70 SH root traces).

## 1. What run_1.1 actually recorded — audit

### Local (`log/v1/run_1.1/`)
| Artifact | State |
|---|---|
| `run_summary.json` (275 KB) | Per-question results + delegations, **but** full `full_state` retained only for the last 4 questions (pre-resume segments were overwritten — the v1.2 resume-merge changelog entry fixes the overwrite; per-question splitting below fixes the size). Score field read 0/4000 — misrepresented the run. |
| `timeline.md` (315 KB) | Human narrative. **No timestamps on any entry.** Worker answers truncated at 400 chars. |
| `scoreboard_submissions.json` | Source of truth for score. Fine. |
| `SH/`, `Senior Splunk/`, `Extractor/` per-worker logs | **Absent** — docs (v1.0.md) promise them; `LogCapture` no longer exists. |
| Latency | **Zero latency data anywhere locally.** No per-question, per-stage, per-tool timing. |
| Token/cost | Per-model totals only. Per-question breakdown exists only for SH (`__sh_cumulative__` delta). Senior/Extractor cost cannot be attributed to a question. |

### LangSmith (project `V1.1`)
- Has what local lacks: per-node latency, per-LLM-call tokens, full parent/child trace tree
  (Senior correctly nested under SH — verified).
- **Gaps found by live probe**:
  - `LANGSMITH_PROJECT` hardcoded to `"V1.1"` in `run_all_v1.py:142` — contradicts `.env` comment
    and v1.1 architecture doc; 17,856 runs from multiple sessions mixed in one project while
    `botsv3-run_1.1` (600 runs) sits half-populated.
  - **Extractor invisible** (raw OpenAI SDK — zero spans).
  - **GLM-5.2-fp8 cost = null** on every span (no LangSmith price entry) — dollar totals there
    silently exclude the model that does 95% of the work.
  - 13 questions have duplicate SH root traces from crash-resumes; 8 lack `end_time`. No
    "resumed" marker → any consumer must dedup by heuristic.
  - `first_token_time` null everywhere (no streaming) — fine, but means latency = full-call only.
- Latency facts it yielded (nothing local could): p50 = 232 s/question, mean 275 s, p95 = 670 s,
  max 1090 s (Q329). Top-5 slowest are all wrong answers — latency is a failure signal worth
  having locally.

### Bugs blocking the next run
1. `run_all_v1.py:262-263` — `ext["valid"]` / `ext["reason"]` reference a variable deleted with
   the extractor-validation removal → **NameError on the first question**.
2. Status mislabeling — delegations marked `solved` with transcripts ending mid-tool-call and no
   answer (confirmed Q330). Aggregate "70% solved" is not trustworthy.
3. ~30-min periodic process kills during run_1.1 (7 resumes at near-exact half-hour marks).
   Likely environmental (OneDrive sync locking `sh_checkpoints.sqlite`/log files, or power
   policy). Runs live inside a OneDrive-synced tree — move `log/` + checkpoint DB to a local
   non-synced path (e.g. `%LOCALAPPDATA%\siem-runs\`, symlink or config) or exclude from sync.

## 2. Design principles

1. **One canonical, machine-first event stream per run; everything else is a view.** Humans get
   rendered reports; AIs get JSONL. Never again hand-grep a 315 KB timeline to find out where a
   question failed.
2. **Attribution over totals.** Every token, dollar, and second must be attributable to
   (question, stage, role, model). Totals are derivable; the reverse is not.
3. **LangSmith is a debugging view, not the system of record.** Its pricing/coverage gaps (GLM
   null cost, invisible extractor) mean local capture must be complete on its own.

## 3. The plan

### P0 — before any next full run
**3.1 Fix the three bugs above** (NameError; truthful status classifier: `solved` requires a
`FINAL ANSWER:` tag, empty/truncated → `failed`, cap-hit → `partial` + `cap_hit`; run dir out of
OneDrive).

**3.2 `events.jsonl` — canonical run event log.** One JSON object per line, append-only, written
by a small `EventLog` class (wraps the existing `RunLogger`). Schema (versioned, `"v": 1`):

```json
{"v":1,"ts":"2026-07-06T14:03:22.114+08:00","run":"run_1.2","event":"task_end",
 "qid":"Q210","stage":"senior","worker":"senior#12","task_idx":2,"status":"partial",
 "cap_hit":false,"iterations":9,"verify_rejections":{"aggregation":1,"intention":0},
 "empty_results":2,"spl_count":6,"latency_ms":87214,
 "tokens":{"in":41230,"cached":0,"out":2101},"cost_usd":0.0416,"model":"GLM-5.2-fp8",
 "answer_head":"PARTIAL ANSWER: FYODOR-L ..."}
```

Event types: `run_start` (manifest: git SHA, models, price-table hash, pool size, args),
`process_resume`, `question_start`, `plan` (round, task list, DIRECT-ANSWER flag),
`task_dispatch`, `task_end`, `join` (decision: final/replan, grounded flag),
`extract`, `submit` (verdict, points), `question_end` (rollups), `run_end` (aggregates),
`heartbeat` (every 60 s — makes external kills diagnosable post-hoc).

**3.3 Per-question / per-role attribution in `UsageTracker`.** The tags are already there
(`["SH", qid]`, `["senior", qid]`) — today only SH is broken out. Change: bucket by
`(qid, role, model)`; keep model totals as a view. Extractor calls pass `qid` into
`add_nim_usage`. Wall-clock timers per stage (planner call, each executor wave, each senior,
joiner, extractor, submit) recorded via the event log; plus Splunk-pool metrics per search:
checkout-wait vs execution time (detects pool saturation — the concurrency benchmark showed the
6-slot knee, this verifies it in production).

**3.4 `metrics.json` — one row per question**, emitted at `question_end` and finalized at
`run_end`. This is the feedback table the next architecture iteration reads:

| column | example |
|---|---|
| qid, points, verdict, earned | Q210, 500, wrong, 0 |
| latency_s (total + per stage: plan/exec/join/extract) | 1007 (12/941/38/9) |
| tokens & cost by role (sh/senior/extractor) | $0.002 / $0.041 / $0.0002 |
| delegations, statuses, replans, cap_hits | 3, [solved,partial,solved], 0, 1 |
| verify_rejections by type, empty_result_count | {agg:1}, 4 |
| grounded (answer found verbatim in worker evidence?) | false |
| resumed_mid_question | false |

`grounded` + `verdict` alone would have flagged every fabrication case (Q221, Q303, Q330, Q333)
without reading a single log line.

**3.5 `run_summary.json` restructure.** Split the heavy payload: `questions/Qxxx.json` holds
`sh_answer`, delegations incl. `full_state`; `run_summary.json` keeps the light rollup
(< 50 KB) + `schema_version` + pointers. Resume appends per-question files — no merge logic can
lose them.

### P1 — same week
**3.6 LangSmith hygiene.**
- Restore per-run project naming (`botsv3-run_1.x` / `botsv3-test_<ts>`) — delete the hardcode
  at `run_all_v1.py:142`.
- Wrap `Extractor.extract` with `@traceable` (langsmith SDK) so it appears in traces.
- Add GLM-5.2-fp8 + DeepSeek-V4-Flash prices in LangSmith model-pricing settings, but treat
  local `UsageTracker` as the billing source of truth (its counts come from API `usage` fields).
- On resume, set trace metadata `{"attempt": n, "resumed": true}` so duplicate SH-Qxxx roots are
  filterable.

**3.7 `make_report.py` — render views from `events.jsonl` + `metrics.json`:**
- `report.md`: score table; per-stage cost/latency percentiles; slowest & most expensive
  questions vs verdict; verify-rejection histogram; crash/resume timeline; ungrounded-answer
  list; the "Wrong / Not Answered" table pre-filled for `docs/scoreboard_result/` (today that
  doc is hand-assembled).
- `timeline.md` stays, but generated from events (with timestamps) instead of ad-hoc writes.
- Optional `report.html` single-file dashboard later (P2).

### P2 — nice to have
- Live tail: `python make_report.py --watch` printing question verdict/cost/latency as the run
  progresses.
- Cross-run comparison view (`compare.py run_1.1 run_1.2`): per-question verdict flips
  (fixes/regressions), cost & latency deltas — exactly the table the version docs require.

## 4. Effort estimate

| Item | Size |
|---|---|
| P0 bugfixes | ~30 min |
| EventLog + timers + tracker attribution | ~½ day |
| metrics.json + summary split | ~½ day |
| LangSmith hygiene | ~1 h |
| make_report.py | ~½ day |

All P0/P1 items are pure instrumentation — no agent-behavior change — so they can land and be
smoke-tested (`--ids Q200,Q210`) independently of the v1.2 architecture work.
