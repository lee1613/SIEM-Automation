#!/usr/bin/env python3
"""Offline scorer for BOTSv3 agent runs.

Reads artifacts that are already in the repo — no API key, no Splunk, no LLM
calls. Verdicts are recomputed from the submitted/official answer pair using
the same exact-match rule as the live scoreboard, so this is a real
re-scoring, not a replay of a cached boolean.

Source-of-truth note: `run_summary.json`'s `score`/`correct`/`results` keys are
NOT trustworthy — run_1.1's were overwritten by a later partial re-run. Only
`scoreboard_submissions.json` (verdicts) and `run_summary["token_usage"]`
(cost) are used.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG_ROOT = REPO / "log" / "v1"
TIERS = (100, 500, 1000)
EVAL_DIR = REPO / "datasets" / "evaluation"
README = REPO / "README.md"
BLOCK_RE = re.compile(
    r"(?<=<!-- LEADERBOARD:START -->\n).*?(?=\n<!-- LEADERBOARD:END -->)", re.DOTALL
)


def is_correct(submitted: str | None, official: str | None) -> bool:
    """The scoreboard's rule, mirrored from agent/scoreboard_client.py:9."""
    if submitted is None or official is None:
        return False
    return str(submitted).lower().strip() == str(official).lower().strip()


def load_rows(run_dir: Path) -> list[dict]:
    path = run_dir / "scoreboard_submissions.json"
    if not path.exists():
        sys.exit(
            f"{path} not found. Only runs with a submissions file can be scored "
            f"(run_1.0 predates it)."
        )
    return json.loads(path.read_text())


def filter_rows(rows: list[dict], tier: int | None, ids: list[str] | None) -> list[dict]:
    selected = rows
    if ids:
        wanted = {i.strip().upper().removeprefix("Q") for i in ids}
        # Check id existence against full rows before tier narrowing
        found_in_all = {str(r["number"]) for r in rows}
        missing = sorted(wanted - found_in_all)
        if missing:
            sys.exit(f"No such question(s) in this run: {', '.join('Q' + m for m in missing)}")
        # Now narrow by ids
        selected = [r for r in selected if str(r["number"]) in wanted]
    if tier is not None:
        selected = [r for r in selected if r["base_points"] == tier]
    if not selected:
        sys.exit("Filter matched no questions.")
    return selected


def summarize(rows: list[dict]) -> dict:
    correct = points_earned = points_possible = 0
    tiers = {}
    for row in rows:
        hit = is_correct(row["submitted"], row["official"])
        points = row["base_points"]
        points_possible += points
        if hit:
            correct += 1
            points_earned += points
        if points not in tiers:
            tiers[points] = {"correct": 0, "total": 0}
        tiers[points]["total"] += 1
        tiers[points]["correct"] += int(hit)
    return {
        "tiers": {t: tiers[t] for t in sorted(tiers.keys())},
        "correct": correct,
        "total": len(rows),
        "points_earned": points_earned,
        "points_possible": points_possible,
    }


def load_cost(run_dir: Path) -> dict:
    """Per-model USD from run_summary['token_usage'].

    Keys wrapped in double underscores are bookkeeping aggregates, not models.
    Runs predating cost tracking (run_1.0) report total_usd=None — cost is
    unknown for them, not zero.
    """
    path = run_dir / "run_summary.json"
    if not path.exists():
        return {"models": {}, "total_usd": None}
    usage = json.loads(path.read_text()).get("token_usage") or {}
    if not usage:
        return {"models": {}, "total_usd": None}
    models = {
        name: entry.get("estimated_usd", 0.0)
        for name, entry in usage.items()
        if not name.startswith("__") and isinstance(entry, dict)
    }
    aggregate = usage.get("__total__")
    total = aggregate.get("estimated_usd") if isinstance(aggregate, dict) else None
    return {
        "models": models,
        "total_usd": float(total if total is not None else sum(models.values())),
    }


def latest_run() -> Path:
    """Highest-numbered scorable run_1.N directory, compared numerically."""
    runs = []
    for path in LOG_ROOT.glob("run_1.*"):
        match = re.fullmatch(r"run_1\.(\d+)", path.name)
        if match and (path / "scoreboard_submissions.json").exists():
            runs.append((int(match.group(1)), path))
    if not runs:
        sys.exit(f"No scorable runs under {LOG_ROOT}")
    return max(runs, key=lambda item: item[0])[1]


def render_report(run_dir: Path, summary: dict, cost: dict) -> str:
    correct, total = summary["correct"], summary["total"]
    lines = [
        f"Run:      {run_dir.name}",
        f"Accuracy: {correct}/{total} = {100 * correct / total:.1f}%",
        f"Points:   {summary['points_earned']} / {summary['points_possible']}",
        "",
        "By tier:",
    ]
    for tier, stats in sorted(summary["tiers"].items()):
        tier_pct = 100 * stats["correct"] / stats["total"]
        lines.append(f"  {tier:>4} pt   {stats['correct']:>2}/{stats['total']:<2}  {tier_pct:5.1f}%")
    if cost["total_usd"] is None:
        lines += ["", "Cost:     not tracked for this run"]
    else:
        lines += ["", f"Cost:     ${cost['total_usd']:.2f} (whole run)"]
        for name, usd in sorted(cost["models"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {name:<28} ${usd:.4f}")
    return "\n".join(lines)


def load_versions() -> dict:
    return json.loads((EVAL_DIR / "versions.json").read_text())


def render_leaderboard_markdown(summary: dict, versions: list[dict]) -> str:
    correct, total = summary["correct"], summary["total"]
    lines = ["| Tier | Solved / Total | Rate |", "|------|:---:|:---:|"]
    for tier, stats in sorted(summary["tiers"].items()):
        rate = 100 * stats["correct"] / stats["total"]
        lines.append(f"| {tier} pt | {stats['correct']} / {stats['total']} | {rate:.1f}% |")
    lines.append(
        f"| **Overall** | **{correct} / {total}** | **{100 * correct / total:.1f}%** "
        f"— {summary['points_earned']} / {summary['points_possible']} pts |"
    )
    lines += ["", "| Version | Correct | Points | Cost | Notes |", "|---|:---:|:---:|:---:|---|"]
    for version in versions:
        lines.append(
            f"| {version['version']} | {version['correct']} / {version['questions']} | "
            f"{version['points']} | ${version['cost_usd']:.2f} | {version['label']} |"
        )
    return "\n".join(lines)


def extract_block(readme_text: str) -> str | None:
    match = BLOCK_RE.search(readme_text)
    return match.group(0).strip() if match else None


def replace_block(readme_text: str, markdown: str) -> str:
    if not BLOCK_RE.search(readme_text):
        sys.exit("README.md is missing the <!-- LEADERBOARD:START/END --> markers.")
    return BLOCK_RE.sub(lambda _: markdown.strip(), readme_text)


def build_leaderboard_payload(run_dir: Path, summary: dict, cost: dict) -> dict:
    """Canonical generated JSON content used by both --write and --check."""
    return {
        "_generated_by": "scripts/run_eval.py --write — do not hand-edit",
        "run": run_dir.name,
        "overall": {"correct": summary["correct"], "total": summary["total"]},
        "points": {
            "earned": summary["points_earned"],
            "possible": summary["points_possible"],
        },
        "tiers": {str(tier): stats for tier, stats in summary["tiers"].items()},
        "cost": cost,
        "versions": load_versions()["versions"],
    }


def write_artifacts(run_dir: Path, summary: dict, cost: dict) -> None:
    payload = build_leaderboard_payload(run_dir, summary, cost)
    markdown = render_leaderboard_markdown(summary, payload["versions"])
    new_readme = replace_block(README.read_text(), markdown)  # can sys.exit — do first

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    (EVAL_DIR / "leaderboard.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    README.write_text(new_readme)
    print(f"Wrote {EVAL_DIR / 'leaderboard.json'} and refreshed the README leaderboard block.")


def check_artifacts(run_dir: Path, summary: dict, cost: dict) -> int:
    payload = build_leaderboard_payload(run_dir, summary, cost)
    failed = False
    leaderboard = EVAL_DIR / "leaderboard.json"
    try:
        actual_payload = json.loads(leaderboard.read_text())
    except FileNotFoundError:
        print(
            "leaderboard.json is missing. Run: python3 scripts/run_eval.py --write",
            file=sys.stderr,
        )
        failed = True
    except json.JSONDecodeError as exc:
        print(
            f"leaderboard.json is malformed ({exc}). "
            "Run: python3 scripts/run_eval.py --write",
            file=sys.stderr,
        )
        failed = True
    else:
        if actual_payload != payload:
            print(
                "leaderboard.json is stale. Run: python3 scripts/run_eval.py --write",
                file=sys.stderr,
            )
            failed = True

    expected = render_leaderboard_markdown(summary, payload["versions"]).strip()
    if extract_block(README.read_text()) != expected:
        print(
            "README leaderboard is stale. Run: python3 scripts/run_eval.py --write",
            file=sys.stderr,
        )
        failed = True
    if failed:
        return 1
    print("Generated leaderboard artifacts are in sync.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Score a BOTSv3 agent run offline. No API key, no Splunk, no LLM calls."
    )
    parser.add_argument("--run", help="Run directory name, e.g. run_1.1 (default: latest scorable run)")
    parser.add_argument("--tier", type=int, choices=TIERS, help="Score only this point tier")
    parser.add_argument("--ids", help="Comma-separated question ids, e.g. Q332,Q333")
    parser.add_argument("--write", action="store_true", help="Regenerate leaderboard.json and the README table")
    parser.add_argument("--check", action="store_true", help="Exit 1 if the README leaderboard is stale (CI)")
    args = parser.parse_args(argv)

    if args.write and args.check:
        sys.exit("--write and --check are mutually exclusive.")
    if (args.tier or args.ids) and (args.write or args.check):
        sys.exit("--write/--check operate on the full run; drop --tier/--ids.")

    run_dir = LOG_ROOT / args.run if args.run else latest_run()
    if not run_dir.exists():
        sys.exit(f"No such run: {run_dir}")
    rows = filter_rows(load_rows(run_dir), args.tier, args.ids.split(",") if args.ids else None)
    summary = summarize(rows)
    cost = load_cost(run_dir)

    if args.write:
        write_artifacts(run_dir, summary, cost)
        return 0
    if args.check:
        return check_artifacts(run_dir, summary, cost)

    print(render_report(run_dir, summary, cost))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
