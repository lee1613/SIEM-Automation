#!/usr/bin/env python3
"""
Render human-readable views from a run's canonical event stream + metrics.json.

    python agent/v1/make_report.py <run_dir>

Writes <run_dir>/report.md. Pure rendering — reads events.jsonl and metrics.json,
computes score/cost/latency rollups, ranks slowest & most expensive questions,
and surfaces the ungrounded-answer list (the fabrication signal) and cap-hit list.
"""

from __future__ import annotations

import json
import os
import sys
import time


def load_events(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                break  # last line is mid-write; stop here, keep what parsed
    return out


def load_metrics(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []  # mid-write full-file rewrite; --watch will pick it up next poll


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100) * (len(s) - 1)))))
    return s[k]


def render_report(events: list[dict], metrics: list[dict]) -> str:
    run_end = next((e for e in events if e.get("event") == "run_end"), {})
    run_start = next((e for e in events if e.get("event") == "run_start"), {})
    correct = run_end.get("correct", sum(1 for m in metrics if m.get("verdict") == "correct"))
    attempted = run_end.get("attempted", len(metrics))
    score = run_end.get("score", sum(m.get("earned", 0) for m in metrics))
    total = run_end.get("total", sum(m.get("points", 0) for m in metrics))

    lats = [m["latency_s"]["total"] for m in metrics if m.get("latency_s")]
    lines = []
    lines.append(f"# Run report — {run_start.get('run', '?')}")
    if run_start.get("git_sha"):
        lines.append(f"\n_git {run_start['git_sha']}, "
                     f"models {run_start.get('models', {})}_")
    lines.append(f"\n## Score\n\n**{correct}/{attempted}** correct — "
                 f"{score}/{total} pts\n")

    lines.append("## Latency (per question, s)\n")
    lines.append(f"- p50 {_pct(lats,50):.0f} · p95 {_pct(lats,95):.0f} · "
                 f"max {max(lats) if lats else 0:.0f}\n")

    slow = sorted(metrics, key=lambda m: m.get("latency_s", {}).get("total", 0), reverse=True)[:5]
    lines.append("### Slowest questions\n")
    lines.append("| qid | s | verdict |\n|---|---|---|")
    for m in slow:
        lines.append(f"| {m['qid']} | {m['latency_s']['total']:.0f} | {m['verdict']} |")
    lines.append("")

    exp = sorted(metrics, key=lambda m: sum(m.get("cost_by_role", {}).values()), reverse=True)[:5]
    lines.append("### Most expensive questions\n")
    lines.append("| qid | $ | verdict |\n|---|---|---|")
    for m in exp:
        lines.append(f"| {m['qid']} | {sum(m.get('cost_by_role', {}).values()):.4f} | {m['verdict']} |")
    lines.append("")

    ungrounded = [m for m in metrics if m.get("verdict") == "wrong" and not m.get("grounded")]
    lines.append(f"## Ungrounded wrong answers ({len(ungrounded)})\n")
    lines.append("_Submitted a value no worker produced — fabrication signal._\n")
    lines.append("| qid | pts | submitted |\n|---|---|---|")
    for m in ungrounded:
        lines.append(f"| {m['qid']} | {m['points']} | `{m.get('clean_answer','')}` |")
    lines.append("")

    caps = [m for m in metrics if m.get("cap_hits")]
    lines.append(f"## Questions that hit the iteration cap ({len(caps)})\n")
    lines.append("| qid | cap_hits | verdict |\n|---|---|---|")
    for m in caps:
        lines.append(f"| {m['qid']} | {m['cap_hits']} | {m['verdict']} |")
    lines.append("")

    lines.append("## Wrong / Not Answered\n")
    lines.append("| qid | pts | submitted | grounded |\n|---|---|---|---|")
    for m in metrics:
        if m.get("verdict") == "wrong":
            lines.append(f"| {m['qid']} | {m['points']} | `{m.get('clean_answer','')}` "
                         f"| {m.get('grounded')} |")
    return "\n".join(lines) + "\n"


def progress_line(metrics: list[dict]) -> str:
    """One-line pure summary of current progress, for --watch ticks."""
    attempted = len(metrics)
    correct = sum(1 for m in metrics if m.get("verdict") == "correct")
    earned = sum(m.get("earned", 0) for m in metrics)
    cost = sum(sum(m.get("cost_by_role", {}).values()) for m in metrics)
    lats = [m["latency_s"]["total"] for m in metrics if m.get("latency_s")]
    p50 = _pct(lats, 50)
    return (f"{correct}/{attempted} correct | {earned} pts | "
            f"${cost:.4f} | p50 {p50:.0f}s")


def _render_once(run_dir: str) -> str:
    events = load_events(os.path.join(run_dir, "events.jsonl"))
    metrics = load_metrics(os.path.join(run_dir, "metrics.json"))
    md = render_report(events, metrics)
    out = os.path.join(run_dir, "report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    return out


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python make_report.py <run_dir> [--watch [interval_s]]")
    run_dir = sys.argv[1]

    if "--watch" in sys.argv:
        watch_idx = sys.argv.index("--watch")
        interval = 20
        if len(sys.argv) > watch_idx + 1:
            try:
                interval = int(sys.argv[watch_idx + 1])
            except ValueError:
                pass
        print(f"watching {run_dir} every {interval}s (Ctrl-C to stop)")
        try:
            while True:
                out = _render_once(run_dir)
                metrics = load_metrics(os.path.join(run_dir, "metrics.json"))
                print(f"wrote {out} - {progress_line(metrics)}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nstopped watching")
        return

    out = _render_once(run_dir)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
