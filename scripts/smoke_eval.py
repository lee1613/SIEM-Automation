#!/usr/bin/env python3
"""Smoke-test comparison for the demo: the same hard questions across architectures.

Smoke runs live in `log/temp/` and are not versioned (CLAUDE.md), so this does not
touch the full-run leaderboard. Instead:

  --write   copy each arm's per-question rows out of its run dirs' metrics.json into
            datasets/evaluation/smoke/<arm>.json (committed), then regenerate
            datasets/evaluation/smoke_comparison.json from those rows.
  --check   regenerate the comparison from the committed rows and exit 1 if the
            committed smoke_comparison.json differs (CI). Needs no log/temp.

Arms, questions and the baseline full run are hand-curated in
datasets/evaluation/smoke/arms.json. Cost is our own PRICES_PER_1M pricing, not
provider billing. The insight lines are computed, never typed, so CI proves they
match the numbers.
"""
from __future__ import annotations

import json
import sys

import run_eval

REPO = run_eval.REPO
SMOKE_DIR = REPO / "datasets" / "evaluation" / "smoke"
ARMS = SMOKE_DIR / "arms.json"
OUT = REPO / "datasets" / "evaluation" / "smoke_comparison.json"
TEMP = REPO / "log" / "temp"
ANSWER_CHARS = 60


def _slim(row: dict) -> dict:
    answer = str(row.get("clean_answer") or "")
    return {
        "qid": row["qid"],
        "verdict": row["verdict"],
        "answer": answer if len(answer) <= ANSWER_CHARS else answer[:ANSWER_CHARS] + "…",
        "latency_s": row["latency_s"]["total"],
        "cost_by_role": row["cost_by_role"],
    }


def collect(arm: dict, questions: list[str]) -> list[dict]:
    """One arm's rows, from every run dir it names (a killed run can span several)."""
    rows = {}
    for name in arm["runs"]:
        hits = list(TEMP.glob(f"**/{name}/metrics.json"))
        if len(hits) != 1:
            sys.exit(f"{arm['id']}: expected one {name}/metrics.json under log/temp, found {len(hits)}")
        for r in json.loads(hits[0].read_text(encoding="utf-8")):
            rows[r["qid"]] = _slim(r)
    if sorted(rows) != sorted(questions):
        sys.exit(f"{arm['id']}: runs cover {sorted(rows)}, arms.json wants {sorted(questions)}")
    return [rows[q] for q in questions]


def _arm_summary(arm: dict, rows: list[dict]) -> dict:
    cost = {"sh": 0.0, "senior": 0.0, "total": 0.0}
    for r in rows:
        cost["sh"] += r["cost_by_role"].get("sh", 0.0)
        cost["senior"] += r["cost_by_role"].get("senior", 0.0)
        cost["total"] += sum(r["cost_by_role"].values())
    return {
        **{k: arm[k] for k in ("id", "version", "loop", "senior")},
        "correct": sum(r["verdict"] == "correct" for r in rows),
        "total": len(rows),
        "solved": [r["qid"] for r in rows if r["verdict"] == "correct"],
        "cost_usd": {k: round(v, 2) for k, v in cost.items()},
        "cost_per_question_usd": round(cost["total"] / len(rows), 2),
        "latency_min": round(sum(r["latency_s"] for r in rows) / 60, 1),
        "rows": rows,
    }


def build(spec: dict, rows_by_arm: dict) -> dict:
    arms = {a["id"]: _arm_summary(a, rows_by_arm[a["id"]]) for a in spec["arms"]}
    base_run = run_eval.LOG_ROOT / spec["baseline_run"]
    base = run_eval.summarize(run_eval.filter_rows(run_eval.load_rows(base_run), None, spec["questions"]))

    old, new = (arms[i] for i in spec["same_senior"])
    best = arms[spec["best"]]
    delta = (new["cost_usd"]["total"] / old["cost_usd"]["total"] - 1) * 100
    insights = [
        f"Cost: on the same {old['senior']} senior, the {new['loop']} loop cost "
        f"{abs(delta):.0f}% {'less' if delta < 0 else 'more'} than the {old['loop']} loop "
        f"(${old['cost_usd']['total']:.2f} → ${new['cost_usd']['total']:.2f}); the senior's share went "
        f"${old['cost_usd']['senior']:.2f} → ${new['cost_usd']['senior']:.2f}.",
        f"Accuracy: {best['version']} with a {best['senior']} senior solved {best['correct']}/{best['total']} "
        f"({', '.join(best['solved']) or 'none'}), where the {spec['baseline_run']} full run got "
        f"{base['correct']}/{base['total']} of these questions right.",
        f"Latency: {new['latency_min'] / old['latency_min']:.1f}× on the same senior "
        f"({old['latency_min']:.1f} → {new['latency_min']:.1f} min), because the conversation is "
        "sequential. Questions are independent, so solving them in parallel is the planned fix.",
    ]
    return {
        "_generated_by": "scripts/smoke_eval.py --write — do not hand-edit",
        "questions": spec["questions"],
        "baseline": {"run": spec["baseline_run"], "correct": base["correct"], "total": base["total"]},
        "arms": list(arms.values()),
        "insights": insights,
    }


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Smoke-test comparison for the demo.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = p.parse_args(argv)

    spec = json.loads(ARMS.read_text(encoding="utf-8"))
    rows_by_arm = {}
    for arm in spec["arms"]:
        path = SMOKE_DIR / f"{arm['id']}.json"
        if args.write:
            rows_by_arm[arm["id"]] = collect(arm, spec["questions"])
            path.write_text(_dump(rows_by_arm[arm["id"]]), encoding="utf-8")
        else:
            rows_by_arm[arm["id"]] = json.loads(path.read_text(encoding="utf-8"))

    expected = _dump(build(spec, rows_by_arm))
    if args.write:
        OUT.write_text(expected, encoding="utf-8")
        print(f"Wrote {OUT.relative_to(REPO)} and {len(spec['arms'])} arm row files.")
        return 0
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != expected:
        print("smoke_comparison.json is stale. Run: python3 scripts/smoke_eval.py --write", file=sys.stderr)
        return 1
    print("Smoke comparison is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
