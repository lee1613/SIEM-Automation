# Handover — Step 2: wire the fan-out executor into the SH graph

> Supersedes `HANDOVER-2026-08-31-recovery-pipeline.md`. Every open question in
> that document (Q1–Q7) has been answered; do not re-open it except as history.
> Everything below is what step 2 actually needs.

**Branch:** `fix/llm-failure-resilience` (not pushed).
**Commits:** `ac68ef1` → `59b3bfe` → `c5c5642` → `bdb37f0` → `8495757`.
**Tests:** `python -m pytest agent/v1/tests/ -q` → **177 passed**.

---

## 1. The one job

Replace `executor_node` (`agent/v1/orchestrator.py:481`) — which runs all Senior
workers on a `ThreadPoolExecutor` *inside a single node* (`:504`) — with the
fan-out graph already built and tested in `agent/v1/executor_graph.py`, where
each worker is its own node and a side-effect-free `hitl` node interrupts.

`executor_graph.py` is complete, isolated, and passing 8 tests. It takes an
injected `run_task(task) -> result` callable, so it has no Splunk or LLM
dependency. **It is not wired into anything yet.**

---

## 2. Framework facts already verified — do not re-derive

Probed against the installed `langgraph`, no LLM calls:

- With `Send` fan-out where one branch interrupts, **all sibling branches still
  run to completion** and their results land in state. So "pause only after the
  other dispatched agents finish" needs no coordination code — the superstep
  gives it.
- The convergence node is correctly withheld while an interrupt is pending.
- **On resume only the interrupted branch replays.** Siblings are restored from
  the checkpoint, not re-executed.
- `interrupt()` **restarts its own node from the top.** This is why the interrupt
  must never live inside a worker — it would re-issue that worker's LLM call on
  every resume. Workers return their result; a separate side-effect-free node
  interrupts.
- `app.invoke(...)` **returns** a dict carrying `__interrupt__`; it does not
  raise. Resume with `app.invoke(Command(resume=<choice>), config)`.

---

## 3. What must port out of `executor_node`

Read `orchestrator.py:481-580` before starting. Behaviour that must survive:

| Behaviour | Detail |
|---|---|
| `$N` dependency DAG | already ported as `executor_graph.ready_tasks()` (with the one-pending-task fallback for a malformed graph) |
| Dependency substitution | `substitute_deps(t.subquestion, completed)` before dispatch |
| Handoff injection | last `HANDOFF_KEEP` entries of `ctx.q_handoffs` appended to the subquestion as "CONTEXT FROM PRIOR ATTEMPTS" |
| Sampling | `plan_samples(subq, ctx.current_points)` dispatches up to 3 workers for the *same* `t.idx`, reduced by `majority_answer` (wire as `reduce_samples=`) |
| Worker numbering | `ctx.logger.next_worker("senior", ctx.current_qid)` per dispatched worker |
| Failure accounting | `counted_failed_idx` dedupe — a sampled task's failure counts **once per task per round**, not once per failing sample. `ctx.failed_delegations` and `build_handoff_digest` both sit behind it |
| Delegation records | `_delegation_record(...)` appended to **both** `ctx.q_delegations` and `ctx.all_delegations` |
| Timeline | `ctx.logger.timeline(...)` per worker |

---

## 4. Hazards — each one has already bitten once

1. **Any blanket `except Exception` between a pause point and the caller
   disarms the pause.** This shipped as a real bug (`c5c5642`): `RunPaused`
   subclasses `Exception`, so `run_sh`'s guard swallowed it and the run
   continued past the failure a human was being asked about. `run_sh` now
   re-raises it. The verifier (`:752`) and adjudicator (`:837`) have the same
   blanket handlers, which is why their HITL calls sit *outside* their `try`.
   **Check this again for anything step 2 introduces.**
2. **`run_sh` must learn to handle `__interrupt__`.** It currently returns
   `result.get("final_answer", "")` and would silently return an empty answer on
   an interrupted run. It needs to detect `__interrupt__`, surface the decision
   request, and resume via `Command(resume=...)`.
3. **Tracing across the new executor.** `_run_senior` exists solely because
   contextvars don't propagate into `ThreadPoolExecutor` threads, so it re-applies
   `tracing_context(parent=parent_run_tree)` to keep LangSmith traces nested under
   the SH trace. LangGraph runs fan-out branches in its *own* executor — **re-check
   whether that wrapper is still needed, still sufficient, or now harmful.**
4. **Checkpointer.** The SH graph is already SQLite-backed (`run_all_v1.py:294`
   into `orchestrator.py:881-885`), so interrupts are durable across process
   death. The sub-graph must share it, not create a `MemorySaver`.

---

## 5. What becomes redundant

`hitl.RunPaused` / `pause_if_api_failed` were the pre-graph-native stopgap. After
step 2 the **executor** path should use the graph interrupt instead. The verifier
(`:752`) and adjudicator (`:837`) are *not* fan-out nodes and still call
`_run_senior` directly, so they keep using `pause_if_api_failed` unless they are
also converted. Do not delete `hitl.py`.

`EXIT_PAUSED = 75` in `run_all_v1.py` stays useful — a graph interrupt still has
to stop the process and be resumable from the CLI.

---

## 6. Blocker, and what to run when it clears

**The Splunk trial licence expired 2026-08-15** (`Trial` group active,
`status=EXPIRED`); every search returns a FATAL "license expired or you have
exceeded your license limit". The user is obtaining a licence. A Developer
licence keeps auth intact; switching to the `Free` group would disable Splunk
auth and break both `SPLUNK_USER`/`SPLUNK_PASS` and the scoreboard KV store.

Step 2 changes the live path and **cannot be integration-tested until this
clears.** Graph mechanics are stub-testable; "does a real 1000-pt question still
behave" is not. When the licence is live, the first real test is a single-question
smoke on Q216 with the Featherless Senior:

    python agent/v1/run_all_v1.py --ids Q216 \
      --senior-model zai-org/GLM-5.3 \
      --senior-base-url https://api.featherless.ai/v1 \
      --senior-api-key-env FEATHERLESS_API_KEY

Per `CLAUDE.md` this is a smoke test, so it lands in `log/temp/` and is not
cost-tracked. Full runs need explicit user go-ahead.

---

## 7. Settled — do not re-litigate

- **Featherless returns HTTP 200 with an error body on its own 5xx.** Handled at
  the transport boundary (`llm_errors.resilient_http_client`), which rewrites it
  to a 500 so the openai SDK's own retry fires. Its 4xx handling is correct and
  standards-compliant; only the server-error path is wrong.
- **Retry is the SDK's job**, configured via `timeout=`/`max_retries=`, not
  hand-rolled — except in `extractor.py`, whose 10 to 20 to 40 to 80s ladder the
  SDK cannot reproduce (`MAX_RETRY_DELAY = 8.0` is a hard module constant).
- **`api_failed` is set from the caught exception, not by parsing answer text.**
  Text parsing is what collapsed API failures onto `too_big`, making SH decompose
  the task and dispatch more workers at a dead provider — the documented cause of
  v1.2's 62 failed delegations and 50x cost blowup.
- **The HITL front-end is two-headed by necessity**: under an agent harness stdin
  is the null device, so a blocking `input()` raises `EOFError` and turns a pause
  into a new crash. The non-tty path must never call `input()`.
- **`retry` as a HITL option** was dropped from the `RunPaused` design (anything
  reaching it had already survived 3 SDK retries). The graph design restores it
  cheaply, because it re-dispatches only the task that actually failed.

---

## 8. STATUS UPDATE (end of 2026-09-04 session) — step 2 is DONE

Sections 1–7 above were written before the work; this section is what actually
landed. Read this first.

**Done:**

- `executor_node` is **gone**. `orchestrator.py` now registers the compiled
  fan-out graph directly as the `executor` node
  (`g.add_node("executor", executor_subgraph)`), with `checkpointer=None` so the
  parent SH graph's SQLite checkpointer owns its state.
- Verified by probe that a **subgraph-as-node** propagates its interrupt to the
  parent's `__interrupt__`, that the parent's joiner is correctly withheld, and
  that `Command(resume=...)` on the *parent* completes the run with **no worker
  re-executed** (`RE-ran: []`). This is why embedding beat flattening.
- All Section-3 behaviour ported: `substitute_deps` + handoff injection +
  worker numbering into `prepare_sends`; delegation records and timeline into
  `run_task`; the once-per-task-per-round failure dedupe into `on_wave`;
  `majority_answer` as `reduce_samples`.
- **`max_parallel=MAX_WORKERS`** added. Removing the ThreadPoolExecutor silently
  dropped the old `min(submissions, MAX_WORKERS)` bound, and
  `SplunkConnectionPool` holds exactly 6 connections, so an uncapped fan-out
  could have starved it. Tasks that do not fit run in the next wave; a task's
  samples are kept together so the majority vote still reduces per wave.
- **`majority_answer` returning `None`** (no majority) is guarded, matching the
  old `winner or res_list[0]`. Caught by the type checker, not by a test.
- Hazard 2 closed: `run_sh` takes `run_dir` and loops on `__interrupt__` via
  `hitl.resolve_interrupt`, which keeps the same two front-ends (tty prompt /
  `decision_request.json` + `RunPaused`). Both `run_sh` call sites in
  `run_all_v1.py` pass `run_dir`. Without this the executor's interrupt would
  have been ignored and `run_sh` would have returned an empty answer — a silent
  regression introduced by removing `executor_node`'s own pause.
- Hazard 3 handled: `get_current_run_tree()` is captured in `prepare_sends` and
  passed explicitly in each payload, since LangGraph also runs fan-out branches
  on its own threads. **Not yet confirmed against a live LangSmith trace.**
- Dead `import concurrent.futures` removed; module docstring updated.

**Tests: 178 passed.**

**What remains:**

1. **No integration test has run** — the Splunk licence is still expired. The
   Q216 smoke in Section 6 is the first real exercise of this path.
2. **LangSmith nesting is unverified** (hazard 3). Check the first real run's
   trace: Senior workers should nest under the SH trace, not appear as
   disconnected roots.
3. The verifier and adjudicator still use `pause_if_api_failed` (they are not
   fan-out nodes). That is intentional, but it means two pause mechanisms now
   coexist — `RunPaused` for those, graph interrupt for the executor.
4. `retry` is now a real option again for the executor path (it re-dispatches
   only the failed task) but is **untested against a live provider**.

---

## 9. Next step (user-directed, 2026-09-04): give SH the same resumable fallback

The executor's workers now fail into a checkpointed, resumable graph interrupt.
**SH's own nodes still do not.** A planner/joiner LLM error hits `run_sh`'s
`try/except`, returns the `("", {})` sentinel, and the runner falls back — the
question's work is lost and nothing is resumable. That is the same weakness the
JSON-record design had, still present on the SH path.

Apply the executor pattern to `planner`, `joiner`, `adjudicator`, `verifier`:

1. Each node catches its own LLM error and **returns an error marker into state**
   — never calls `interrupt()` inline. Same rule as workers: those nodes make the
   expensive call, and `interrupt()` replays its own node, so interrupting inside
   one would re-issue its LLM call on every resume.
2. A conditional edge routes to a single side-effect-free `sh_hitl` node that
   interrupts. Resume replays only that node; the planner's completed work stays
   checkpointed.
3. `run_sh`'s `while result.get("__interrupt__")` loop already handles the
   resume, so no runner change is needed.

Payoff: one pause mechanism instead of three (`RunPaused` for
verifier/adjudicator, graph interrupt for the executor, sentinel-plus-fallback
for SH), and `run_sh`'s blanket `except Exception` can shrink to genuine crashes
— removing the class of bug that caused `c5c5642`.

### Pool note (do not "optimise" this away)

`max_parallel=MAX_WORKERS` is not redundant with `SplunkConnectionPool`. The pool
blocks rather than fails when full (`queue.Queue.get(block=True, timeout=...)`,
`splunk_pool.py:108`), so over-fanning would not corrupt anything — but:

- the pool's own measured table puts the throughput peak at 6-7 concurrent; past
  8 Splunk's scheduler queues and throughput *drops* (12 -> 0.83 jobs/s, 20 -> 2
  failures);
- a blocked caller that exhausts `checkout_timeout` raises `TimeoutError`, which
  now surfaces as a worker crash and is classified **`api_failed`** — so an
  uncapped fan-out would manufacture fake API failures from self-inflicted
  congestion and interrupt the operator for them.
