#!/usr/bin/env python3
"""
Cross-run comparison: per-question verdict flips (fixes/regressions) plus
score/cost/latency deltas between two run directories.

    python agent/v0/compare.py <run_dir_a> <run_dir_b>

Writes <run_dir_b>/comparison_vs_<basename(run_dir_a)>.md and prints the path.

Reads `metrics.json` when present (new schema). Falls back to
`run_summary.json`'s `results` array (old schema: `id`, `base_points`,
`sb_correct`, `earned`) — or its `index` if that's all that's present.
Missing files never raise; they just yield an empty run.
"""

from __future__ import annotations

import json
import os
import sys


def _load_json(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def load_run(run_dir: str) -> dict:
    """Load a run dir into {qid: {verdict, points, earned, latency_s, cost}}."""
    run = {}

    metrics = _load_json(os.path.join(run_dir, "metrics.json"))
    if isinstance(metrics, list):
        for m in metrics:
            qid = m.get("qid")
            if not qid:
                continue
            run[qid] = {
                "verdict": m.get("verdict"),
                "points": m.get("points", 0),
                "earned": m.get("earned", 0),
                "latency_s": m.get("latency_s", {}).get("total", 0) if m.get("latency_s") else 0,
                "cost": sum((m.get("cost_by_role") or {}).values()),
            }
        return run

    summary = _load_json(os.path.join(run_dir, "run_summary.json"))
    if not isinstance(summary, dict):
        return run

    results = summary.get("results")
    if isinstance(results, list):
        for r in results:
            qid = r.get("id")
            if not qid:
                continue
            verdict = "correct" if r.get("sb_correct") else "wrong"
            run[qid] = {
                "verdict": verdict,
                "points": r.get("base_points", 0),
                "earned": r.get("earned", 0),
                "latency_s": 0,
                "cost": 0,
            }
        return run

    index = summary.get("index")
    if isinstance(index, list):
        for r in index:
            qid = r.get("id") or r.get("qid")
            if not qid:
                continue
            verdict = "correct" if r.get("sb_correct") else r.get("verdict", "wrong")
            run[qid] = {
                "verdict": verdict,
                "points": r.get("base_points", r.get("points", 0)),
                "earned": r.get("earned", 0),
                "latency_s": 0,
                "cost": 0,
            }
        return run
    if isinstance(index, dict):
        for qid, r in index.items():
            verdict = "correct" if r.get("sb_correct") else r.get("verdict", "wrong")
            run[qid] = {
                "verdict": verdict,
                "points": r.get("base_points", r.get("points", 0)),
                "earned": r.get("earned", 0),
                "latency_s": 0,
                "cost": 0,
            }
        return run

    return run


def diff_runs(a: dict, b: dict) -> dict:
    """Diff two loaded runs into fixed/regressed/same + score/cost totals."""
    fixed = []
    regressed = []
    same = []

    for qid in sorted(set(a) | set(b)):
        va = a.get(qid, {})
        vb = b.get(qid, {})
        verdict_a = va.get("verdict")
        verdict_b = vb.get("verdict")
        points = vb.get("points", va.get("points", 0))

        if verdict_a != "correct" and verdict_b == "correct":
            fixed.append({"qid": qid, "points": points})
        elif verdict_a == "correct" and verdict_b != "correct":
            regressed.append({"qid": qid, "points": points})
        else:
            same.append({"qid": qid, "points": points})

    score_a = sum(v.get("earned", 0) for v in a.values())
    score_b = sum(v.get("earned", 0) for v in b.values())
    cost_a = sum(v.get("cost", 0) for v in a.values())
    cost_b = sum(v.get("cost", 0) for v in b.values())
    latency_a = sum(v.get("latency_s", 0) for v in a.values())
    latency_b = sum(v.get("latency_s", 0) for v in b.values())

    return {
        "fixed": fixed,
        "regressed": regressed,
        "same": same,
        "score_a": score_a,
        "score_b": score_b,
        "cost_a": cost_a,
        "cost_b": cost_b,
        "latency_a": latency_a,
        "latency_b": latency_b,
    }


def render_comparison(name_a: str, name_b: str, diff: dict) -> str:
    lines = []
    lines.append(f"# Comparison: {name_a} -> {name_b}\n")

    score_delta = diff["score_b"] - diff["score_a"]
    cost_delta = diff["cost_b"] - diff["cost_a"]
    latency_delta = diff["latency_b"] - diff["latency_a"]

    lines.append("## Headline\n")
    lines.append(f"- Score: {diff['score_a']} -> {diff['score_b']} "
                 f"({'+' if score_delta >= 0 else ''}{score_delta})")
    lines.append(f"- Cost: ${diff['cost_a']:.4f} -> ${diff['cost_b']:.4f} "
                 f"({'+' if cost_delta >= 0 else ''}{cost_delta:.4f})")
    lines.append(f"- Latency (sum, s): {diff['latency_a']:.0f} -> {diff['latency_b']:.0f} "
                 f"({'+' if latency_delta >= 0 else ''}{latency_delta:.0f})")
    lines.append(f"- Fixed: {len(diff['fixed'])} · Regressed: {len(diff['regressed'])} · "
                 f"Unchanged: {len(diff['same'])}\n")

    lines.append(f"## Fixed ({name_a} -> {name_b}) — {len(diff['fixed'])}\n")
    lines.append("| qid | pts |\n|---|---|")
    for x in diff["fixed"]:
        lines.append(f"| {x['qid']} | {x['points']} |")
    lines.append("")

    lines.append(f"## Regressed ({name_a} -> {name_b}) — {len(diff['regressed'])}\n")
    lines.append("| qid | pts |\n|---|---|")
    for x in diff["regressed"]:
        lines.append(f"| {x['qid']} | {x['points']} |")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: python compare.py <run_dir_a> <run_dir_b>")
    dir_a, dir_b = sys.argv[1], sys.argv[2]

    run_a = load_run(dir_a)
    run_b = load_run(dir_b)
    diff = diff_runs(run_a, run_b)

    name_a = os.path.basename(os.path.normpath(dir_a))
    name_b = os.path.basename(os.path.normpath(dir_b))
    md = render_comparison(name_a, name_b, diff)

    out = os.path.join(dir_b, f"comparison_vs_{name_a}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
