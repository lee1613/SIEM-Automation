#!/usr/bin/env python3
"""
Post-hoc report on what SH spawned and what came back.

Reads a run directory's `questions/*.json`. Nothing is instrumented at runtime,
so this cannot slow or break a run, and it works on any run already on disk.

The headline metric is SOLVED-RATE BY CONFIDENCE DECILE, because that is the one
number that says whether SH's self-reported confidence means anything. Until it
does, confidence must not gate fan-out: routing cost on an uncalibrated number is
backwards, and on questions this hard a low confidence is the expected output, so
"low confidence -> more spawns" degenerates into "always fan out to the cap".
See docs/future_work.md #4.

`partial` counts as not-solved for that headline. It is the plurality status
(100 of 239 delegations across every logged run) and means "returned something,
unclear if useful" - calibrating a probability against a bucket with no crisp
definition produces a number you cannot act on. The full three-way split is
printed below it.

Baseline to beat, measured across all runs logged before v0.3:
    solved 63 / partial 100 / failed 73 / too_big 3   ->  26.4% solved

Usage:
    python spawn_report.py log/temp/test_20260907_220052
    python spawn_report.py log/v0/run_0.3
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter, defaultdict

STATUSES = ("solved", "partial", "failed", "too_big", "api_failed", "runaway")
BASELINE_SOLVED_RATE = 26.4


def load_questions(run_dir: str) -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(run_dir, "questions", "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                out.append(json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ! skipping {os.path.basename(path)}: {exc}")
    return out


def _bar(n: int, total: int, width: int = 24) -> str:
    if not total:
        return ""
    filled = round(width * n / total)
    return "#" * filled + "." * (width - filled)


def report(run_dir: str) -> int:
    questions = load_questions(run_dir)
    if not questions:
        print(f"No questions/*.json under {run_dir}")
        return 1

    status_total = Counter()
    by_decile: dict[int, Counter] = defaultdict(Counter)
    spawn_types = Counter()
    shape       = Counter()
    per_q       = []
    no_conf     = 0
    ruled_out   = 0

    for q in questions:
        delegs = q.get("delegations") or []
        per_q.append({
            "id":       q.get("id", "?"),
            "points":   q.get("base_points", 0),
            "correct":  bool(q.get("sb_correct")),
            "spawns":   len(delegs),
            "solved":   sum(1 for d in delegs if d.get("status") == "solved"),
            "worker_s": round(sum(d.get("duration_s") or 0.0 for d in delegs), 1),
        })
        for d in delegs:
            st = d.get("status", "?")
            status_total[st] += 1
            spawn_types[d.get("spawn_type") or "senior"] += 1
            shape["structured" if d.get("structured") else "prose"] += 1
            ruled_out += len(d.get("negative_findings") or [])
            try:
                decile = min(9, max(0, int(d["confidence"]) // 10))
            except (KeyError, TypeError, ValueError):
                no_conf += 1
                continue
            by_decile[decile][st] += 1

    total   = sum(status_total.values())
    solved  = status_total["solved"]
    n_q     = len(questions)

    print(f"\n=== spawn report: {run_dir} ===")
    print(f"questions {n_q}   spawns {total}   mean {total / max(1, n_q):.1f} per question")

    print("\n-- SH confidence vs solved-rate --")
    if not by_decile:
        print(f"  no confidence recorded on any spawn ({no_conf} without).")
        print("  Either SH does not emit one yet, or this run predates the field.")
    else:
        print(f"  {'confidence':>12}  {'n':>4}  {'solved':>6}  {'rate':>6}")
        for decile in sorted(by_decile):
            row = by_decile[decile]
            n, s = sum(row.values()), row["solved"]
            print(f"  {decile * 10:>4}-{decile * 10 + 9:<7}  {n:>4}  {s:>6}  "
                  f"{s / n * 100:>5.0f}%  {_bar(s, n)}")
        if no_conf:
            print(f"  ({no_conf} spawns carried no confidence)")

    print("\n-- outcome split --")
    for st in STATUSES:
        n = status_total.get(st, 0)
        if n:
            print(f"  {st:<11} {n:>4}  {n / total * 100:>5.1f}%  {_bar(n, total)}")
    rate = solved / max(1, total) * 100
    print(f"  {'SOLVED RATE':<11} {solved:>4}/{total}  {rate:>5.1f}%   "
          f"(pre-v0.3 baseline {BASELINE_SOLVED_RATE}%, "
          f"{'better' if rate > BASELINE_SOLVED_RATE else 'not better'})")

    print("\n-- spawn types --")
    for k, n in spawn_types.most_common():
        print(f"  {k:<12} {n:>4}")

    print("\n-- return shape --")
    for k, n in shape.most_common():
        print(f"  {k:<12} {n:>4}  {n / max(1, total) * 100:>5.1f}%")
    print(f"  ruled-out notes captured: {ruled_out}")

    print("\n-- per question --")
    print(f"  {'qid':<7} {'pts':>5} {'spawns':>7} {'solved':>7} {'worker_s':>9}  ok")
    for r in sorted(per_q, key=lambda x: -x["spawns"]):
        print(f"  {r['id']:<7} {r['points']:>5} {r['spawns']:>7} {r['solved']:>7} "
              f"{r['worker_s']:>9}  {'Y' if r['correct'] else '.'}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    return report(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
