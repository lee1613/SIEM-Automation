# Leaderboard

Version numbers are `v0.x` while the project is in development; `v1` is reserved for the first published release. The single-agent baseline is `v0.0.0`, and the multi-agent line was renumbered from `v1.x` to `v0.x` on 2026-09-28 (text inside older logs keeps the old names). The tier table is the last complete full run (run_0.2). The version table covers every version with a scored run, generated from `datasets/evaluation/versions.json`, and each row is checked against its run logs. "5 hard" rows are smoke tests on the five 1000-point questions that no full run had solved (Q216, Q217, Q224, Q328, Q329), so they aren't comparable with full-run scores.

<!-- LEADERBOARD:START -->
| Tier | Solved / Total | Rate |
|------|:---:|:---:|
| 100 pt | 15 / 24 | 62.5% |
| 500 pt | 9 / 23 | 39.1% |
| 1000 pt | 2 / 9 | 22.2% |
| **Overall** | **26 / 56** | **46.4%** — 8000 / 22900 pts |

| Version | Scope | Correct | Points | Cost | Latency | Notes |
|---|---|:---:|:---:|:---:|:---:|---|
| v0 | full 56 | 20 / 56 | 5700 | n/a¹ | n/a¹ | One LangGraph ReAct agent (gpt-5.4) with an SPL verify gate, a sourcetype field manifest and a 15-step cap. The baseline. |
| v0.0 | full 58 | 20 / 58 | 5650 | n/a¹ | n/a¹ | Split into an SH orchestrator that plans and fresh gpt-5.4 senior workers that search, plus an extractor that submits a bare value. Same 20 correct: the split alone added no accuracy. |
| v0.1 | full 56 | 26 / 56 | 8300 | n/a¹ | n/a¹ | Plan-and-execute DAG: up to 6 seniors (GLM-5.2) chase competing hypotheses in parallel, and a junior tier takes single lookups. +6 correct, the biggest jump. |
| v0.2 | full 56 | 26 / 56 | 8000 | n/a¹ | n/a¹ | Crash-safe persistence, a grounding guard and structured findings. Same 26: most misses were the right evidence transcribed wrong, and 28 wrong answers were submitted with confidence. |
| v0.3.0 | 5 hard (smoke) | 0 / 5 | 0 | $1.36 | 18 min | Consensus voting removed (it never reached a majority); SH briefed with every sourcetype and the top 100 sources; seniors return a structured `submit_finding`. Found Q216's hidden Cisco feed, still 0/5. |
| v0.4.0 mini | 5 hard (smoke) | 0 / 5 | 0 | $1.26 | 37 min | Conversational loop: seniors keep their thread across rounds, and SH grades every report and routes the senior. With gpt-5.4-mini seniors: 0/5, but 3 honest refusals instead of guesses. |
| v0.4.0 GLM-5.3 | 5 hard (3 runs) | 2 / 5 | 2000 | $6.45 | 1.6 h | Same loop, with the senior swapped to the reasoning model GLM-5.3. 2/5: Q224 and Q328 solved for the first time in any version. |
| v0.4.1 | 5 hard (smoke) | 2 / 5 | 2000 | $7.27 | 1.8 h | Only SH may answer: an exhausted budget becomes an explicit refusal instead of a senior's guess, and unverified premises are flagged and checked first. 2/5, 1 wrong, 2 refused. |
| v0.4.4 | 5 hard (smoke) | 2 / 5 | 2000 | $6.31 | 2.5 h | Premise ledger (quotes must appear in real tool output), a blind validation agent (v0.4.2 to v0.4.3) and soundness checks. 2/5; Q216 moved from a stable 112 to within 1 of the answer. |
| v0.4.5 | full, stopped at 50 | 24 / 50 | 6900 | $44.95 | 11.3 h | SH memory across questions and per-turn resume. 24/50 correct with only 4 wrong answers submitted; the other 22 were refusals. |

¹ v0.2 and earlier are compared on correctness and points only: their cost and latency traces predate the tested tracing added in v0.3 and were never verified (senior spend was booked to SH, the extractor was priced at $0, and the totals were not reconciled with provider billing). Latency is summed question time.
<!-- LEADERBOARD:END -->

Regenerate with `python3 scripts/run_eval.py --write`. CI fails if this table drifts from `log/v0/`.

Back to the [README](../README.md).
