#!/usr/bin/env python3
"""Extracts 6 curated question trajectories from log/v1/run_1.2 into a tier-tagged
static JSON file for the Streamlit replay demo. Dev-time only, not deployed.
Run manually; re-run only if source logs change.

Output entries are tier-tagged (sh/senior/extractor) so the demo can render the
delegation hierarchy visually, not just a flat tool-call log.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TIMELINE = REPO / "log" / "v1" / "run_1.2" / "timeline.md"
SUBMISSIONS = REPO / "log" / "v1" / "run_1.2" / "scoreboard_submissions.json"
OUTPUT = REPO / "datasets" / "evaluation" / "demo_trajectories.json"

# question id (without "Q") -> narrative kind for the demo UI. Fixed by design
# decision — see docs/superpowers/specs/2026-07-28-streamlit-replay-demo-design.md
QUESTION_PLAN = {
    "332": "correct",
    "333": "correct",
    "303": "refusal",
    "328": "refusal",
    "330": "wrong",
    "224": "wrong",
}

SENIOR_HEADER_RE = re.compile(
    r"^- \*\*Senior #(?P<num>\d+)\*\*\s+_\[(?P<status>\w+)\]_\s+task=(?P<task>\d+)"
)
FIELD_RE = re.compile(r"^\s{4}- (subquestion|answer|SPL): ?(.*)$")
FINAL_RE = re.compile(
    r"^\*\*SH FINAL.*?:\*\*\s+`(?P<answer>.*)`\s+\[(?P<verdict>CORRECT|WRONG)\]"
)
HEADING_RE = re.compile(r"^## Q(?P<num>\d+)\s+\((?P<points>\d+) pts\)$")
QUESTION_TEXT_RE = re.compile(r"^> (?P<text>.+)$")


def truncate(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def split_question_blocks(timeline_text: str) -> dict[str, str]:
    """Splits timeline.md into {question_num: block_text} on '## Q<n>' headings."""
    lines = timeline_text.splitlines()
    blocks: dict[str, list[str]] = {}
    current_num: str | None = None
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            current_num = m.group("num")
            blocks[current_num] = [line]
            continue
        if current_num is not None:
            blocks[current_num].append(line)
    return {num: "\n".join(text) for num, text in blocks.items()}


def parse_block(block_text: str) -> dict:
    lines = block_text.splitlines()
    points = int(HEADING_RE.match(lines[0]).group("points"))
    question_text = ""
    seniors: list[dict] = []
    final_answer: str | None = None
    verdict: str | None = None

    current_senior: dict | None = None
    current_field: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_field, current_lines
        if current_field is not None and current_senior is not None:
            current_senior[current_field] = "\n".join(current_lines).strip()
        current_field = None
        current_lines = []

    for line in lines[1:]:
        qm = QUESTION_TEXT_RE.match(line)
        if qm and not question_text:
            question_text = qm.group("text").strip()
            continue

        sm = SENIOR_HEADER_RE.match(line)
        if sm:
            flush()
            current_senior = {
                "num": sm.group("num"),
                "status": sm.group("status"),
                "task": sm.group("task"),
                "subquestion": "",
                "answer": "",
                "SPL": "",
            }
            seniors.append(current_senior)
            continue

        fm = FIELD_RE.match(line)
        if fm and current_senior is not None:
            flush()
            current_field = fm.group(1)
            current_lines = [fm.group(2)]
            continue

        finm = FINAL_RE.match(line)
        if finm:
            flush()
            final_answer = finm.group("answer")
            verdict = finm.group("verdict")
            continue

        if current_field is not None:
            current_lines.append(line)
    flush()

    return {
        "points": points,
        "question": question_text,
        "seniors": seniors,
        "final_answer": final_answer,
        "verdict": verdict,
    }


def build_entries(parsed: dict) -> list[dict]:
    entries: list[dict] = []
    for s in parsed["seniors"]:
        entries.append(
            {
                "tier": "sh",
                "type": "delegate",
                "content": f"Task {s['task']} → Senior #{s['num']}: "
                + truncate(s["subquestion"], 220),
            }
        )
        entries.append(
            {
                "tier": "senior",
                "type": "investigate",
                "content": f"[{s['status']}] " + truncate(s["answer"], 400),
                "spl": truncate(s["SPL"], 200),
            }
        )
    entries.append(
        {
            "tier": "extractor",
            "type": "answer",
            "content": parsed["final_answer"] or "",
            "verdict": parsed["verdict"] or "UNKNOWN",
        }
    )
    return entries


def main() -> None:
    timeline_text = TIMELINE.read_text()
    blocks = split_question_blocks(timeline_text)
    submissions = {
        str(row["number"]): row for row in json.loads(SUBMISSIONS.read_text())
    }

    output: dict[str, dict] = {}
    for num, kind in QUESTION_PLAN.items():
        block_text = blocks[num]
        parsed = parse_block(block_text)
        submission = submissions.get(num, {})
        output[f"Q{num}"] = {
            "points": parsed["points"],
            "question": parsed["question"],
            "kind": kind,
            "final_answer": parsed["final_answer"],
            "verdict": parsed["verdict"],
            "submitted": submission.get("submitted"),
            "official": submission.get("official"),
            "entries": build_entries(parsed),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Wrote {OUTPUT} with {len(output)} questions.")


def demo() -> None:
    """Self-check: run after main() writes the file."""
    data = json.loads(OUTPUT.read_text())
    expected_ids = {f"Q{num}" for num in QUESTION_PLAN}
    assert set(data.keys()) == expected_ids, (
        f"expected {expected_ids}, got {set(data.keys())}"
    )
    for qid, entry in data.items():
        assert entry["kind"] in ("correct", "refusal", "wrong"), qid
        assert entry["entries"], f"{qid} has no entries"
        tiers_present = {e["tier"] for e in entry["entries"]}
        assert tiers_present == {"sh", "senior", "extractor"}, (
            f"{qid} missing tiers, got {tiers_present}"
        )
        assert entry["final_answer"], f"{qid} has empty final_answer"
    print(f"demo() OK: {len(data)} questions, all tier-tagged and non-empty.")


if __name__ == "__main__":
    main()
    demo()
