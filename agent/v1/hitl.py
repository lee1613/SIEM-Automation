#!/usr/bin/env python3
"""
Human-in-the-loop pause for unrecoverable API failures (v1.3, phase 1).

An LLM provider failure is not a reasoning failure, and during the testing phase
the right response is to stop and ask a human rather than let SH burn budget
replanning around a dead endpoint.

The pause point is written as "persist state -> emit a decision request", not
"block on stdin", because a blocking `input()` only works when a human is
actually at a terminal. Under an agent harness stdin is the null device, so
`input()` raises EOFError immediately - turning a pause into a *new* crash in
exactly the environment the pipeline most often runs in. Same seam, two
front-ends:

  * interactive  (stdin is a tty) -> prompt, return the operator's choice
  * non-interactive               -> write decision_request.json, raise RunPaused

Persisting is plain JSON serialization by design: preserving the work already
paid for must cost zero extra tokens, so it never calls an LLM to summarize.
"""

import json
import os
import sys
from datetime import datetime, timezone

SKIP  = "skip"    # fall back to the best worker answer, continue the run
ABORT = "abort"   # stop now; resume later with --start/--run-name
VALID = (SKIP, ABORT)


class RunPaused(Exception):
    """Raised when a decision is needed but no human is reachable.

    Carries the path of the decision request so the caller can name it in the
    exit message rather than making the operator hunt for it.
    """

    def __init__(self, request_path: str, summary: str):
        super().__init__(summary)
        self.request_path = request_path
        self.summary      = summary


def request_decision(*, qid: str, component: str, provider: str, error: str,
                     run_dir: str, partial: dict | None = None) -> str:
    """Persist what the run has earned so far, then ask a human what to do.

    Returns SKIP or ABORT when a human is present. Raises RunPaused otherwise.
    """
    record = {
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "qid":          qid,
        "component":    component,
        "provider":     provider,
        "error":        error,
        "options":      list(VALID),
        # Everything the run has paid for on this question, so a resume does not
        # have to rediscover it. Plain serialization - no LLM call.
        "partial":      partial or {},
    }
    path = os.path.join(run_dir, "decision_request.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, default=str)

    banner = (f"API FAILURE on {qid} - {component} via {provider}\n"
              f"  {error}\n"
              f"  decision request written to: {path}")

    if not sys.stdin.isatty():
        # No human reachable. Do NOT call input() here - it would EOFError.
        raise RunPaused(path, banner)

    print(f"\n{'='*78}\n[HITL] {banner}\n{'='*78}")
    while True:
        choice = input(f"[HITL] {'/'.join(VALID)} (skip = fall back and continue, "
                       f"abort = stop the run)> ").strip().lower()
        if choice in VALID:
            print(f"[HITL] operator chose: {choice}")
            return choice
        print(f"[HITL] answer must be one of {', '.join(VALID)}")


def pause_if_api_failed(results, *, qid: str, run_dir: str,
                        partial: dict | None = None, where: str = "") -> bool:
    """Ask a human what to do if any worker result is an API failure.

    MUST be called on the main thread, with every worker already collected.
    Not inside a ThreadPoolExecutor worker: `_run_senior` runs on up to 6
    threads at once in the executor path, so a pause there would have six
    threads racing for one prompt and clobbering one decision file, while their
    still-running siblings kept burning tokens on the same dead provider.

    Returns True if the operator chose to continue; raises RunPaused on abort,
    or when no human is reachable.
    """
    failures = [r for r in results if isinstance(r, dict) and r.get("status") == "api_failed"]
    if not failures:
        return False

    first = failures[0]
    decision = request_decision(
        qid=qid,
        component=f"{where or 'Senior'} ({len(failures)} of {len(results)} failed)",
        provider=first.get("provider", "?"),
        error=(first.get("answer") or "")[:600],
        run_dir=run_dir,
        partial=partial,
    )
    if decision == ABORT:
        raise RunPaused(os.path.join(run_dir, "decision_request.json"),
                        f"operator chose to abort on {qid} ({where})")
    print(f"[HITL] continuing past {len(failures)} API failure(s) on {qid} ({where})")
    return True


def resolve_interrupt(interrupts, *, qid: str, run_dir: str,
                      partial: dict | None = None) -> str:
    """Turn a LangGraph __interrupt__ into a human decision.

    The executor subgraph's `hitl` node interrupts instead of raising, so
    `graph.invoke` RETURNS with `__interrupt__` set. Feed the choice back with
    `Command(resume=<choice>)`; only the hitl node replays, never a paid worker.

    Same two front-ends as request_decision: a tty gets a prompt, anything else
    gets a decision request on disk and RunPaused.
    """
    payload = {}
    first = (list(interrupts) or [None])[0]
    if first is not None:
        payload = getattr(first, "value", None) or {}
    options = [o for o in (payload.get("options") or []) if o] or [SKIP, ABORT]

    record_partial = dict(partial or {})
    record_partial.setdefault("interrupt", payload)
    path = os.path.join(run_dir, "decision_request.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "qid":          qid,
            "component":    "executor (fan-out worker)",
            "provider":     payload.get("provider"),
            "error":        payload.get("error"),
            "failed_tasks": payload.get("qids"),
            "options":      options,
            "partial":      record_partial,
        }, fh, indent=2, default=str)

    banner = (f"API FAILURE on {qid} - tasks {payload.get('qids')} via "
              f"{payload.get('provider')}")
    if not sys.stdin.isatty():
        raise RunPaused(path, banner + f" | decision request: {path}")

    print("")
    print("=" * 78)
    print(f"[HITL] {banner}")
    print(f"[HITL] {payload.get('error')}")
    print("=" * 78)
    while True:
        choice = input(f"[HITL] {'/'.join(options)}> ").strip().lower()
        if choice in options:
            print(f"[HITL] operator chose: {choice}")
            return choice
        print(f"[HITL] answer must be one of {', '.join(options)}")
