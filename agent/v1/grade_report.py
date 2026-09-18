#!/usr/bin/env python3
"""
Turns the emitted R1/R2/R3 grades into the table spec §10 criterion 4 is judged on.

The honest limitation, stated in the spec and worth repeating here: SH grades
before it routes, so the grades are not an INDEPENDENT measurement of the
routing — they are part of the same decision. The table shows consistency, not
correctness. What it can still catch:

  * an all-PASS column        -> the rubric is inert and the run can be killed early;
  * a flat continue-rate      -> SH is not acting on its own judgement;
  * contradictions            -> `continue` after a FAIL, ANSWER from a WEAK scope;
  * frequent novel_spl zeros  -> seniors thrash and §4.1's ceiling is approached
                                 for nothing.

Usage: python agent/v1/grade_report.py <run_dir>
"""

from __future__ import annotations

import json
import os
import sys

GRADES = ("PASS", "WEAK", "FAIL")
DIMENSIONS = ("r1", "r2_sh", "r2_effective", "r3", "r4")


def summarize(grades: list) -> dict:
    dist = {d: {g: 0 for g in GRADES} for d in DIMENSIONS}
    for row in grades:
        for d in DIMENSIONS:
            if row.get(d) in dist[d]:
                dist[d][row[d]] += 1

    by_r2: dict = {}
    for row in grades:
        b = by_r2.setdefault(row.get("r2_effective", "?"), [0, 0])
        b[1] += 1
        if row.get("route") == "COMMAND" and row.get("decision") == "continue":
            b[0] += 1
    continue_rate = {k: (v[0] / v[1]) for k, v in by_r2.items() if v[1] and k in GRADES}

    critics: dict = {}
    for row in grades:
        if row.get("route") == "CRITIC" and row.get("basis"):
            critics[row["basis"]] = critics.get(row["basis"], 0) + 1

    return {
        "distribution": dist,
        # A dimension that only ever came back PASS is not measuring anything.
        "inert_dimensions": [d for d in DIMENSIONS
                             if dist[d]["PASS"] and not (dist[d]["WEAK"] or dist[d]["FAIL"])],
        "continue_rate_by_r2": continue_rate,
        "contradictions": {
            "continue_after_fail": sum(
                1 for r in grades if r.get("r2_effective") == "FAIL"
                and r.get("route") == "COMMAND" and r.get("decision") == "continue"),
            "answer_from_weak_scope": sum(
                1 for r in grades if r.get("route") == "ANSWER"
                and r.get("r1") == "WEAK"),
        },
        "critics_by_basis": critics,
        "novel_spl": {
            "rounds": len(grades),
            "zeros": sum(1 for r in grades if int(r.get("novel_spl_count", 0)) == 0),
            "mean": (sum(int(r.get("novel_spl_count", 0)) for r in grades) / len(grades))
                    if grades else 0.0,
        },
    }


def load_grades(run_dir: str) -> list:
    """Every grade row this run recorded, read from questions/<qid>.json."""
    out = []
    qdir = os.path.join(run_dir, "questions")
    for name in sorted(os.listdir(qdir)) if os.path.isdir(qdir) else []:
        if not name.endswith(".json"):
            continue
        with open(os.path.join(qdir, name), encoding="utf-8") as f:
            out.extend(json.load(f).get("grades") or [])
    return out


def report(run_dir: str) -> int:
    grades = load_grades(run_dir)
    s = summarize(grades)
    print(f"\nGRADE REPORT — {run_dir}   ({s['novel_spl']['rounds']} graded rounds)\n")
    for dim in DIMENSIONS:
        row = s["distribution"][dim]
        print(f"  {dim:<14} PASS={row['PASS']:<4} WEAK={row['WEAK']:<4} FAIL={row['FAIL']:<4}")
    if s["inert_dimensions"]:
        print(f"\n  !! INERT (all PASS): {', '.join(s['inert_dimensions'])} — "
              "the rubric measured nothing on these.")
    print("\n  continue-rate by effective R2:")
    for g in GRADES:
        if g in s["continue_rate_by_r2"]:
            print(f"    {g:<5} {s['continue_rate_by_r2'][g]:.0%}")
    print(f"\n  contradictions: {s['contradictions']}")
    print(f"  critics by basis: {s['critics_by_basis'] or '(none raised)'}")
    print(f"  novel SPL: {s['novel_spl']['zeros']} zero-round(s) of "
          f"{s['novel_spl']['rounds']}, mean {s['novel_spl']['mean']:.1f}\n")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python agent/v1/grade_report.py <run_dir>")
        return 2
    return report(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
