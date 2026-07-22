# Spec: SIEM Automation — Multi-Agent BOTSv3 Solver

## Objective

Build a multi-agent LLM system that autonomously answers the Splunk BOTSv3 CTF
question set (56 scored questions) against a live Splunk instance, as a research
entry toward automated SIEM investigation.

- **User:** the researcher iterating on agent architectures (v0 → v1 → v1.x).
- **Success:** each new version scores strictly more scoreboard points than its
  predecessor on a full 56-question run, at recorded cost. Baseline to beat:
  v1.1 = 26/56 correct, 8,300 pts, $0.63.
- **Why multi-agent:** single-agent v0 plateaued; hierarchical
  orchestrator/worker/extractor with grounding + verification is the research
  hypothesis under test.

## Tech Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph StateGraph (LLMCompiler pattern: plan → parallel execute → join → replan) |
| SH (mastermind) | gpt-5.4 (OpenAI) |
| Senior workers | GLM-5.2-fp8 (Vultr inference) |
| Extractor | Qwen3.6-27B, thinking disabled (Vultr; was DeepSeek-V4-Flash — cluster outage 2026-07-08) |
| Data plane | Splunk Enterprise (localhost:8089), `index=botsv3`, SplunkConnectionPool (6 slots) |
| Scoring | SA-ctf_scoreboard KV store via `agent/scoreboard_client.py` — exact match, lowercase/strip |
| Observability | `events.jsonl` + `metrics.json` per run; LangSmith project `botsv3-<run>` |
| Tests | pytest 9.x, Python 3.11 |
| Persistence | SqliteSaver checkpoint (cross-question SH memory) |

## Commands

```bash
# Full scored run (versioned, logged to log/v1/run_1.x/) — user-triggered only
python agent/v1/run_all_v1.py

# Smoke run (unversioned, log/temp/) — for validating changes
python agent/v1/run_all_v1.py --ids Q200,Q210

# Tests
python -m pytest agent/v1/tests/ -q

# Reports
python agent/v1/make_report.py log/v1/run_1.2          # render report.md
python agent/v1/make_report.py log/v1/run_1.2 --watch   # live tail during run
python agent/v1/compare.py log/v1/run_1.1 log/v1/run_1.2  # cross-run diff

# Live score check
# Splunk: index=scoreboard sourcetype=scoreboard | rex "Result=(?P<r>[^,]+)" | stats count by r
```

## Project Structure

```
├── CLAUDE.md                  # agent-behaviour + versioning/logging rules
├── docs/
│   ├── spec.md                # this file
│   ├── observability_plan.md  # instrumentation design (P0-P2 done)
│   ├── BOTS_V3_SETUP.md       # Splunk install guide
│   ├── DATASET_EXPLORATION_GUIDE.md / FIELD_AWARENESS_PLAN.md / BOTSV3_QUESTIONS_AND_ANSWERS.md
│   ├── version_architecture/  # v0/, v1/ — per-version design docs + in-progress changelog
│   ├── scoreboard_result/     # v0/, v1/ — per-version full-run results
│   └── superpowers/plans/     # TDD implementation plans
├── agent/
│   ├── splunk_agent.py        # v0 ReAct graph — reused as Senior worker engine
│   ├── splunk_client.py       # single Splunk REST session
│   ├── splunk_pool.py         # thread-safe pool (6 slots) — production data plane
│   ├── scoreboard_client.py   # scoring: KV store submit + index=scoreboard log (FROZEN)
│   ├── setup_scoreboard.py    # one-time CTF app data load
│   ├── build_manifest.py      # regenerates botsv3_fields.json
│   ├── botsv3_fields.json     # 102-sourcetype field manifest (agent search index)
│   └── v1/                    # current architecture (one dir per major version)
│       ├── orchestrator.py    # SH: planner/executor/joiner/verifier + grounding guard
│       ├── splunk_subagent.py # Senior pool; dual iteration budgets; status classifier
│       ├── extractor.py       # prose → bare answer; single submit point
│       ├── grounding.py       # is_grounded / best_candidate (anti-fabrication)
│       ├── web_tool.py        # web_lookup (DuckDuckGo) for external-knowledge Qs
│       ├── event_log.py       # events.jsonl canonical stream
│       ├── usage_tracker.py   # per-(qid,role,model) token/cost attribution
│       ├── agent_logger.py    # hierarchical run dirs; SIEM_LOG_ROOT override
│       ├── run_all_v1.py      # runner: full → log/v1/run_1.x/, test → log/temp/
│       ├── make_report.py     # report.md renderer + --watch
│       ├── compare.py         # cross-run fixes/regressions diff
│       └── tests/             # pytest suite (all green required)
├── datasets/                  # botsv3_questions.json / answers.json (answers = reference only)
├── botsv3/                    # raw BOTSv3 dataset (922M; tgz + extracted app) — data plane source
├── botsv3content/             # official CTF CSVs (loaded into KV stores)
├── log/                       # v1/run_1.x/ versioned; baseline/ baseline runs; temp/ unversioned

```

Structure rule: **infra is shared, architecture is versioned.** New major
architecture = new `agent/vN/` dir + `docs/version_architecture/vN/` +
`log/vN/`. Shared clients stay at `agent/` top level (future: `agent/core/`).

## Code Style

Follow existing v1 idiom — pure functions for logic, thin I/O wrappers, tested
at the seam:

```python
def decide_joiner_answer(answer, task_results, question_text, *, plan_round, max_rounds):
    """Grounded -> final; ungrounded -> replan while rounds remain, else best candidate."""
    if is_grounded(answer, task_results, question_text):
        return {"action": "final", "answer": answer}
    if plan_round < max_rounds:
        return {"action": "replan"}
    fallback = best_candidate(task_results)
    return {"action": "final", "answer": fallback or answer}
```

- snake_case; module-level constants UPPER_CASE.
- Decision logic = pure function (unit-testable); node functions call them.
- ASCII only in print paths (cp1252 console history — `force_utf8_stdio()`
  guards, but don't rely on it).
- Defensive readers: missing/old-schema files → empty result, never raise.

## Testing Strategy

- **Framework:** pytest, tests in `agent/v1/tests/`, named `test_*.py`.
- **Unit tests** for every pure decision function (grounding, joiner routing,
  status classification, metrics rows, parsers). No LLM calls in unit tests.
- **Smoke runs** (`--ids` with 2–4 questions) validate integration against live
  Splunk + live models. Cheap, unversioned, required before claiming a feature works.
- **Full runs** are the only accepted evidence of score improvement —
  user-triggered (real cost, ~4 h).
- Seam rule: when a value crosses a component boundary (worker → orchestrator
  record → metrics), add a contract test — hand-built dicts hide seam bugs.

## Boundaries

- **Always:** run pytest before commit; changelog entry in the in-progress
  `docs/version_architecture/v1/v1.x.md` in the same turn as any code change;
  smoke-test behavior changes with `--ids` before claiming done; keep test runs
  out of `log/v1/`.
- **Ask first:** full 56-Q runs (user triggers; real cost); model swaps;
  new dependencies; changing datasets/ or botsv3content/; deleting files not
  authored this session.
- **Never:** modify the scoring/submit path (`scoreboard_client.py`, exact-match
  rule); leak `datasets/botsv3_answers.json` into any agent prompt or tool
  (data-leakage = invalid research); commit `.env`/credentials; switch off
  branch `jy`.

## Success Criteria

1. `python -m pytest agent/v1/tests/ -q` — all green.
2. Full run of vNext scores > 8,300 pts (v1.1 baseline) on the scoreboard.
3. Every answered question's `metrics.json` row has `grounded: true` or an
   explicit fallback record — zero silent fabrications.
4. Run completes without manual resume (no encoding/persistence crashes).
5. `compare.py` vs previous run shows net-positive fixed-minus-regressed.
6. Cost per full run recorded in `docs/scoreboard_result/` (user supplies $).

## Open Questions

- **Extractor over-trims answer components (deferred, run_1.2 Q209)**. `FYODOR-L` extracted
  to `fyodor` — dropped the `-L` suffix the SH's evidence actually contained. User directive:
  do NOT patch this by adding more special-case suffix-stripping instructions to the
  extractor prompt (that's how Q202's `v3`-vs-`E5-2676` ambiguity happened — competing
  "strip vendor/version suffix" guidance with no way to know which suffixes are real vs
  decoration). Keep the extractor prompt generic; it should follow the question's own
  `answer_guidance`/`expected_shape` field, not a growing list of trim heuristics. Root cause
  is likely prompt-following fidelity on the extractor model (Qwen3.6-27B, thinking
  disabled), not the prompt wording — investigate that angle first. Q202's `v3` truncation is
  explicitly accepted as-is, not worth fixing.
- **"Intention:" preamble before tool calls (Senior worker prompt) — helps or just burns
  tokens?** Every Senior tool call currently prefaces with a spoken-out `Intention: ...` line
  before the call. Unverified whether this improves tool-call accuracy/reasoning (a
  lightweight chain-of-thought anchor) or is pure token overhead with no behavior change.
  **Verify after run_1.2 finishes**: A/B a handful of questions with the preamble stripped
  from `splunk_agent.py`'s system prompt vs kept — same questions, compare tool-call
  correctness (right SPL/right sourcetype first try) and token count. Small sample (3-5
  questions), not a full run. Decide keep/cut based on result.
- Plan B (case-file blackboard, hints economy, specialists, recon) — implement
  before or after Plan A's full-run verdict?
- `agent/core/` migration for shared clients — worth the import churn now?
- `agent/judge/` legacy — archive or delete?
