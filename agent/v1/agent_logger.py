#!/usr/bin/env python3
"""
Run directory management and narrative logging for the v1 multi-agent run.

Per-step agent traces (LLM calls, tool calls, node visits) are handled by LangSmith.
This module manages only:
  - the run directory (log/v1/run_1.<minor>/ or log/temp/<ts>/)
  - timeline.md  — human-readable narrative used for docs
  - worker counter — sequential index across all workers in a run

Full runs go to  log/v1/run_1.<minor>/  (auto-incrementing).
Test runs  go to  log/temp/<timestamp>/  and are never versioned.
"""

import os
import datetime


_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))


class RunLogger:
    """Owns one run's directory, timeline narrative, and worker counter."""

    def __init__(self, *, full_run: bool, version_major: int = 1, run_name: str | None = None):
        self.full_run = full_run
        log_root = os.path.join(PROJECT_ROOT, "log")

        if run_name:
            # Reuse an existing run dir (append mode).
            self.run_name = run_name
            if full_run:
                self.run_dir = os.path.join(log_root, f"v{version_major}", run_name)
            else:
                self.run_dir = os.path.join(log_root, "temp", run_name)
            append = True
        elif full_run:
            vdir = os.path.join(log_root, f"v{version_major}")
            minor = self._next_minor(vdir, version_major)
            self.run_name = f"run_{version_major}.{minor}"
            self.run_dir  = os.path.join(vdir, self.run_name)
            append = False
        else:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_name = f"test_{ts}"
            self.run_dir  = os.path.join(log_root, "temp", self.run_name)
            append = False

        os.makedirs(self.run_dir, exist_ok=True)

        self.timeline_path = os.path.join(self.run_dir, "timeline.md")
        self._counters     = {"senior": 0, "junior": 0}

        if not append:
            with open(self.timeline_path, "w", encoding="utf-8") as f:
                kind = "FULL RUN" if full_run else "TEST RUN"
                f.write(f"# v{version_major} timeline — {self.run_name}  ({kind})\n\n")
                f.write(f"Started: {datetime.datetime.now().isoformat(timespec='seconds')}\n\n")
        else:
            with open(self.timeline_path, "a", encoding="utf-8") as f:
                f.write(f"\n---\n\n## ↩ Resumed: {datetime.datetime.now().isoformat(timespec='seconds')}\n\n")

    @staticmethod
    def _next_minor(vdir: str, major: int) -> int:
        if not os.path.isdir(vdir):
            return 0
        prefix = f"run_{major}."
        minors = []
        for name in os.listdir(vdir):
            if name.startswith(prefix):
                tail = name[len(prefix):]
                if tail.isdigit():
                    minors.append(int(tail))
        return (max(minors) + 1) if minors else 0

    def next_worker(self, role: str, qid: str) -> int:
        """Reserve and return the next global sequential index for this role."""
        self._counters[role] += 1
        return self._counters[role]

    def timeline(self, text: str) -> None:
        with open(self.timeline_path, "a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")

    def timeline_question_header(self, qid: str, question: str, points) -> None:
        self.timeline(
            f"\n---\n\n## {qid}  ({points} pts)\n\n> {question}\n"
        )
