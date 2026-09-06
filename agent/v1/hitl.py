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
RETRY = "retry"   # re-run the node that failed; only that node replays
VALID = (RETRY, SKIP, ABORT)


class RunPaused(Exception):
    """Raised when a decision is needed but no human is reachable.

    Carries the path of the decision request so the caller can name it in the
    exit message rather than making the operator hunt for it.
    """

    def __init__(self, request_path: str, summary: str):
        super().__init__(summary)
        self.request_path = request_path
        self.summary      = summary


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
