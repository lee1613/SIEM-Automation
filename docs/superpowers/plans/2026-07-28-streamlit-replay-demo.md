# Streamlit Replay Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-serve, replay-only Streamlit app that guides a visitor through a linear
story (Problem → Architecture → Trajectory → Score) proving why the SH → Senior → Extractor
multi-agent architecture matters, using real curated data from `log/v1/run_1.2`.

**Architecture:** A dev-time extraction script (`scripts/extract_demo_trajectories.py`) parses
`log/v1/run_1.2/timeline.md` + `scoreboard_submissions.json` once, producing a committed static
JSON file with tier-tagged trajectory records. The deployed `streamlit_app/app.py` only ever
does `json.load()` on that file plus the existing `datasets/evaluation/leaderboard.json` — zero
runtime log parsing, zero LLM/network calls per visitor. A single shared render function draws
the SH/Senior/Extractor waterfall for both the abstract Architecture-step diagram and the real
Trajectory-step data, guaranteeing visual consistency between "concept" and "proof."

**Tech Stack:** Python 3, Streamlit (dark theme + monospace via native `.streamlit/config.toml`,
no CSS injection), pandas for table rendering. No new dependency beyond `streamlit` + `pandas`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-28-streamlit-replay-demo-design.md`
- `streamlit_app/requirements.txt` contains only `streamlit` and `pandas` — never add a graph-viz
  or HTTP-client dependency; hierarchy visuals use native Streamlit components only
  (`st.columns`, `st.expander`, `st.container`, `:blue[]`/`:green[]`/`:orange[]` markdown,
  `st.badge`).
- Tier color code, used everywhere, no exceptions: SH = blue, Senior = green, Extractor = amber.
- Curated question set is exactly these 6, with these fixed `kind` labels — do not add, remove,
  or relabel: `Q332` (correct, 1000pt), `Q333` (correct, 1000pt), `Q303` (refusal, 100pt),
  `Q328` (refusal, 1000pt), `Q330` (wrong, 1000pt), `Q224` (wrong, 1000pt).
- Never display a dollar cost figure or a v1.1-vs-v1.2 cost multiplier claim anywhere in the
  app. The Score step's cost narrative is the data-integrity-fix story only (commit `8aa9fa1`),
  with no `$` amount attached to it. (`datasets/evaluation/leaderboard.json`'s own `cost` field,
  already public via the Phase 1 README table, may still be rendered as-is in the version
  history table — the constraint is on new narrative claims, not on re-displaying that existing
  public artifact.)
- No test framework, no Streamlit UI tests (locked testing decision in the spec). The one
  automated test is the `assert`-based `demo()` self-check in the extraction script.
- Source path is `log/v1/run_1.2/timeline.md` and `log/v1/run_1.2/scoreboard_submissions.json`
  — read-only inputs, never modified.
- Output path is `datasets/evaluation/demo_trajectories.json` (not `data/evaluation/` — that
  directory doesn't exist in this repo; the real sibling artifact `leaderboard.json` lives under
  `datasets/evaluation/`).

---

### Task 1: Extraction script — `timeline.md` → tier-tagged `demo_trajectories.json`

**Files:**
- Create: `scripts/extract_demo_trajectories.py`
- Reads: `log/v1/run_1.2/timeline.md`, `log/v1/run_1.2/scoreboard_submissions.json`
- Produces: `datasets/evaluation/demo_trajectories.json`

**Interfaces:**
- Produces (consumed by Task 3's Trajectory step): `demo_trajectories.json` is a JSON object
  keyed by question ID string (e.g. `"Q332"`), each value shaped:
  ```json
  {
    "points": 1000,
    "question": "What is the CVE of the vulnerability that escalated permissions on Linux host hoth?",
    "kind": "correct",
    "final_answer": "cve-2017-16995",
    "verdict": "CORRECT",
    "entries": [
      {"tier": "sh", "type": "delegate", "content": "Task 1 → Senior #122: In Splunk `index=botsv3` for August 2018, investigate Linux host `hoth`..."},
      {"tier": "senior", "type": "investigate", "content": "[failed] Intention: I need to see all available sourcetypes...", "spl": "[]"},
      {"tier": "extractor", "type": "answer", "content": "cve-2017-16995", "verdict": "CORRECT"}
    ]
  }
  ```
  `kind` is one of `"correct"`, `"refusal"`, `"wrong"` — set from this task's hardcoded
  `QUESTION_PLAN`, not inferred from the data. `verdict` on the top-level object and on the
  final `extractor` entry is `"CORRECT"` or `"WRONG"` as parsed from the `**SH FINAL →
  extractor:**` line — note that both refusal questions (Q303, Q328) have `verdict: "WRONG"`
  in the source data; `kind: "refusal"` is what the UI uses to badge them differently, not
  `verdict`.

- [ ] **Step 1: Write the script with hardcoded question plan and parser**

```python
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
```

- [ ] **Step 2: Run the script**

Run: `python3 scripts/extract_demo_trajectories.py`
Expected output:
```
Wrote /Users/june/Desktop/Project/SIEM-Automation/datasets/evaluation/demo_trajectories.json with 6 questions.
demo() OK: 6 questions, all tier-tagged and non-empty.
```
If it raises an `AssertionError` or `KeyError` on a question number, re-check that
`log/v1/run_1.2/timeline.md` still contains `## Q<num>` headings for all of
`332, 333, 303, 328, 330, 224` (`grep -n "^## Q332\|^## Q333\|^## Q303\|^## Q328\|^## Q330\|^## Q224" log/v1/run_1.2/timeline.md`).

- [ ] **Step 3: Spot-check the output for the two refusal questions**

Run: `python3 -c "import json; d=json.load(open('datasets/evaluation/demo_trajectories.json')); print(d['Q303']['final_answer']); print(d['Q328']['final_answer'])"`
Expected: prints the two refusal answers (`The password is not provided in the context.` and
the Q328 "I cannot provide..." text) — confirms the refusal framing has real text to display,
not an empty string.

- [ ] **Step 4: Commit**

```bash
git add scripts/extract_demo_trajectories.py datasets/evaluation/demo_trajectories.json
git commit -m "feat: extract tier-tagged demo trajectories for Streamlit replay demo"
```

---

### Task 2: App scaffold — wizard navigation, theme, Problem step

**Files:**
- Create: `streamlit_app/requirements.txt`
- Create: `streamlit_app/app.py`
- Create: `.streamlit/config.toml`

**Interfaces:**
- Consumes: nothing from other tasks yet (Problem step is static prose).
- Produces (consumed by Task 3 and Task 4): `app.py` defines `STEPS = ["problem", "architecture", "trajectory", "score"]` and a `st.session_state["step_index"]` int, plus a `render_step()` dispatcher function that Task 3/4 will extend with `elif` branches for `"architecture"`, `"trajectory"`, `"score"`. Also defines `TIER_COLORS = {"sh": "blue", "senior": "green", "extractor": "orange"}` (Streamlit's native colored-markdown keyword is `orange`, used for the amber/extractor tier) — Task 3's shared render function imports this constant.

- [ ] **Step 1: Write `requirements.txt`**

```
streamlit>=1.38
pandas>=2.0
```

- [ ] **Step 2: Write `.streamlit/config.toml`**

```toml
[theme]
base = "dark"
font = "monospace"
```

- [ ] **Step 3: Write `app.py` with wizard skeleton and Problem step**

```python
"""Self-serve replay demo for the SIEM-Automation multi-agent BOTSv3 agent.
Reads only static committed JSON — no live Splunk/LLM calls, zero cost per visitor.
"""
from __future__ import annotations

import streamlit as st

STEPS = ["problem", "architecture", "trajectory", "score"]
STEP_LABELS = {
    "problem": "1. The Problem",
    "architecture": "2. The Architecture",
    "trajectory": "3. Watch It Reason",
    "score": "4. The Score",
}

TIER_COLORS = {"sh": "blue", "senior": "green", "extractor": "orange"}
TIER_LABELS = {"sh": "SH (orchestrator)", "senior": "Senior (investigator)", "extractor": "Extractor (answer-strip)"}


def render_problem_step() -> None:
    st.header("1. The Problem")
    st.markdown(
        """
A BOTSv3 investigation is 58 questions across **100+ Splunk sourcetypes** —
AWS CloudTrail, Windows event logs, DNS, VPN sessions, email, endpoint telemetry,
all covering a single simulated breach at a fictional brewery, Frothly.

A single agent asked to answer all 58 questions in one continuous context
hits two walls fast:

- **Context budget.** Each question needs several exploratory Splunk searches
  before the right sourcetype and fields are even known. Multiply that by 58
  questions in one context window and the agent runs out of room to reason
  before it runs out of questions.
- **Error isolation.** One bad search, one wrong assumption about a field name,
  and it pollutes the reasoning for every question that follows in the same
  context.

The architecture on the next step exists specifically to solve those two
problems — not as an abstract "multi-agent is better" choice, but as a direct
answer to a scale failure.
"""
    )


def render_step() -> None:
    step = STEPS[st.session_state["step_index"]]
    if step == "problem":
        render_problem_step()
    elif step == "architecture":
        st.header("2. The Architecture")
        st.info("Architecture step — implemented in Task 3.")
    elif step == "trajectory":
        st.header("3. Watch It Reason")
        st.info("Trajectory step — implemented in Task 3.")
    elif step == "score":
        st.header("4. The Score")
        st.info("Score step — implemented in Task 4.")


def main() -> None:
    st.set_page_config(page_title="SIEM Agent Replay Demo", layout="centered")
    if "step_index" not in st.session_state:
        st.session_state["step_index"] = 0

    st.caption(" · ".join(STEP_LABELS.values()))
    render_step()

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back", disabled=st.session_state["step_index"] == 0):
            st.session_state["step_index"] -= 1
            st.rerun()
    with col_next:
        is_last = st.session_state["step_index"] == len(STEPS) - 1
        if st.button("Next →", disabled=is_last):
            st.session_state["step_index"] += 1
            st.rerun()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run locally and manually verify navigation**

Run: `cd streamlit_app && pip install -r requirements.txt && streamlit run app.py`
Expected: browser opens on a dark-themed page showing "1. The Problem" with the SOC-scale
prose, a disabled "← Back" button, and an enabled "Next →" button. Clicking "Next →" four
times moves through all four step headers in order and disables "Next →" on the last step;
clicking "← Back" returns to "1. The Problem" and disables "← Back" there. No test framework
per the locked testing decision — this manual click-through is the verification.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/requirements.txt streamlit_app/app.py .streamlit/config.toml
git commit -m "feat: scaffold Streamlit replay demo with step wizard and Problem step"
```

---

### Task 3: Shared hierarchy render function — Architecture and Trajectory steps

**Files:**
- Modify: `streamlit_app/app.py` (add `render_waterfall()`, `render_architecture_step()`,
  `render_trajectory_step()`; extend `render_step()`'s `elif` branches)
- Reads: `datasets/evaluation/demo_trajectories.json` (produced by Task 1)

**Interfaces:**
- Consumes: `TIER_COLORS`, `TIER_LABELS` from Task 2's `app.py`; the `entries` list shape from
  Task 1 (`{"tier": "sh"|"senior"|"extractor", "type": ..., "content": str, ...}`); the
  top-level per-question shape from Task 1 (`points`, `question`, `kind`, `final_answer`,
  `verdict`, `entries`).
- Produces: `render_waterfall(entries: list[dict]) -> None` — consumed by both
  `render_architecture_step()` (called with a small abstract 3-entry list) and
  `render_trajectory_step()` (called with a real question's `entries`), so any future visual
  change only has to happen once.

- [ ] **Step 1: Add `render_waterfall()` and the Architecture step**

Insert into `streamlit_app/app.py`, above `render_step()`:

```python
def render_waterfall(entries: list[dict]) -> None:
    """Renders tier-tagged entries as an indented, color-coded waterfall.
    Shared by the Architecture step (abstract data) and Trajectory step (real
    data) so both use the exact same visual language.
    """
    indent_for_tier = {"sh": 0, "senior": 1, "extractor": 2}
    for entry in entries:
        tier = entry["tier"]
        color = TIER_COLORS[tier]
        indent = indent_for_tier[tier]
        cols = st.columns([indent, 6 - indent]) if indent else [st.container()]
        target = cols[-1]
        with target:
            st.markdown(f":{color}[**{TIER_LABELS[tier]}**]")
            st.markdown(entry["content"])
            if entry.get("spl"):
                st.code(entry["spl"], language="text")
            if entry.get("verdict"):
                badge_color = "green" if entry["verdict"] == "CORRECT" else "red"
                st.markdown(f":{badge_color}[{entry['verdict']}]")


ABSTRACT_WATERFALL = [
    {"tier": "sh", "type": "delegate", "content": "\"Investigate lateral movement on host X\" → spawns a Senior worker with a focused subquestion."},
    {"tier": "senior", "type": "investigate", "content": "Runs Splunk searches, reasons over results, reports a finding back to SH.", "spl": "index=botsv3 host=X ..."},
    {"tier": "extractor", "type": "answer", "content": "Strips SH's final prose answer down to the bare value the scoreboard expects."},
]


def render_architecture_step() -> None:
    st.header("2. The Architecture")
    st.markdown(
        """
Three tiers, each with one job:

- **SH (orchestrator)** — plans, delegates focused subquestions to Senior
  workers, and decides when it has enough to answer.
- **Senior (investigator)** — runs the actual Splunk searches for one focused
  subquestion, with its own bounded tool-call budget, isolated from every
  other question's context.
- **Extractor** — strips SH's final prose answer down to the bare value the
  scoreboard expects, so reasoning stays readable but scoring stays exact.

Here's the pattern in the abstract — the next step shows it applied to real
questions, with the exact same visual layout:
"""
    )
    render_waterfall(ABSTRACT_WATERFALL)
```

- [ ] **Step 2: Add the Trajectory step**

Insert into `streamlit_app/app.py`, below `render_architecture_step()`:

```python
import json
from pathlib import Path

DEMO_TRAJECTORIES_PATH = Path(__file__).resolve().parent.parent / "datasets" / "evaluation" / "demo_trajectories.json"

KIND_BADGE = {
    "correct": ("green", "CORRECT"),
    "wrong": ("red", "INCORRECT"),
    "refusal": ("orange", "REFUSED TO GUESS"),
}


@st.cache_data
def load_demo_trajectories() -> dict:
    return json.loads(DEMO_TRAJECTORIES_PATH.read_text())


def render_trajectory_step() -> None:
    st.header("3. Watch It Reason")
    try:
        trajectories = load_demo_trajectories()
    except FileNotFoundError:
        st.error(
            "Trajectory data not found. Run `python3 scripts/extract_demo_trajectories.py` "
            "and redeploy."
        )
        return

    question_id = st.selectbox("Choose a question", list(trajectories.keys()))
    entry = trajectories[question_id]

    color, label = KIND_BADGE[entry["kind"]]
    st.markdown(f"**{question_id}** · {entry['points']}pt · :{color}[{label}]")
    st.markdown(f"> {entry['question']}")
    if entry["kind"] == "refusal":
        st.caption(
            "The agent declined to fabricate an answer under uncertainty, rather than "
            "guessing to avoid a zero. Scored the same as a wrong answer, but the "
            "difference matters in a real investigation."
        )

    render_waterfall(entry["entries"])
    st.markdown(f"**Final answer:** `{entry['final_answer']}`")
```

- [ ] **Step 3: Wire both steps into `render_step()`**

```python
def render_step() -> None:
    step = STEPS[st.session_state["step_index"]]
    if step == "problem":
        render_problem_step()
    elif step == "architecture":
        render_architecture_step()
    elif step == "trajectory":
        render_trajectory_step()
    elif step == "score":
        st.header("4. The Score")
        st.info("Score step — implemented in Task 4.")
```

- [ ] **Step 4: Run locally and manually verify**

Run: `cd streamlit_app && streamlit run app.py`
Expected: on step 2, an abstract 3-row waterfall (blue SH → green Senior → amber Extractor,
increasing indent) renders below the role explanations. On step 3, a dropdown lists
`Q332, Q333, Q303, Q328, Q330, Q224`; selecting `Q303` or `Q328` shows an orange "REFUSED TO
GUESS" badge and the refusal caption; selecting `Q330` or `Q224` shows a red "INCORRECT" badge
with no refusal caption; selecting `Q332` or `Q333` shows a green "CORRECT" badge. Each
selection renders a waterfall with real SPL queries visible in code blocks.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/app.py
git commit -m "feat: add shared waterfall render and Architecture/Trajectory steps"
```

---

### Task 4: Score step — leaderboard table and cost-integrity callout

**Files:**
- Modify: `streamlit_app/app.py` (add `render_score_step()`; extend `render_step()`)
- Reads: `datasets/evaluation/leaderboard.json` (existing Phase 1 artifact)

**Interfaces:**
- Consumes: `datasets/evaluation/leaderboard.json`'s real schema — top-level keys `overall`
  (`correct`, `total`), `points` (`earned`, `possible`), `tiers` (keys `"100"`, `"500"`,
  `"1000"`, each `{"correct": int, "total": int}`), `cost` (`models` dict, `total_usd` float),
  `versions` (list of `{"version", "label", "correct", "questions", "points", "cost_usd",
  "source"}`).
- Produces: nothing consumed by later tasks — this is the final step.

- [ ] **Step 1: Add `render_score_step()`**

```python
import pandas as pd

LEADERBOARD_PATH = Path(__file__).resolve().parent.parent / "datasets" / "evaluation" / "leaderboard.json"


@st.cache_data
def load_leaderboard() -> dict:
    return json.loads(LEADERBOARD_PATH.read_text())


def render_score_step() -> None:
    st.header("4. The Score")
    try:
        board = load_leaderboard()
    except FileNotFoundError:
        st.error(f"Leaderboard data not found at {LEADERBOARD_PATH}.")
        return

    st.metric(
        "Overall",
        f"{board['overall']['correct']} / {board['overall']['total']} correct",
        f"{board['points']['earned']} / {board['points']['possible']} pts",
    )

    tier_rows = [
        {"Tier": f"{tier}pt", "Correct": stats["correct"], "Total": stats["total"]}
        for tier, stats in board["tiers"].items()
    ]
    st.dataframe(pd.DataFrame(tier_rows), hide_index=True)

    st.subheader("Version history")
    version_rows = [
        {
            "Version": v["version"],
            "Label": v["label"],
            "Correct": v["correct"],
            "Points": v["points"],
        }
        for v in board["versions"]
    ]
    st.dataframe(pd.DataFrame(version_rows), hide_index=True)

    st.info(
        "**Cost tracking earns trust the hard way.** A run that was restarted mid-way once "
        "let its recorded cost silently pass through as if the run were free, because the "
        "tracker's default for \"no usage data\" was `$0.00` instead of \"unknown.\" That's "
        "now fixed — the tracker returns \"not tracked\" instead of a false zero — so the "
        "numbers above are validated before they're published, not assumed correct."
    )
```

- [ ] **Step 2: Wire the Score step into `render_step()`**

```python
def render_step() -> None:
    step = STEPS[st.session_state["step_index"]]
    if step == "problem":
        render_problem_step()
    elif step == "architecture":
        render_architecture_step()
    elif step == "trajectory":
        render_trajectory_step()
    elif step == "score":
        render_score_step()
```

- [ ] **Step 3: Run locally and manually verify**

Run: `cd streamlit_app && streamlit run app.py`
Expected: on step 4, a metric shows "26 / 56 correct" with "8000 / 22900 pts" beneath it, a
tier table shows rows for 100/500/1000pt with the correct/total counts from
`datasets/evaluation/leaderboard.json`, a version-history table lists v0 through v1.2, and an
info box shows the cost-tracking-integrity text with no dollar figure or multiplier claim
anywhere on the page. Confirm by reading the rendered page text — no `$` character should
appear outside the version-history table (which mirrors the already-public README figures).

- [ ] **Step 4: Full click-through of all four steps**

Run: `cd streamlit_app && streamlit run app.py`
Expected: starting from step 1, click "Next →" three times to reach step 4 without error,
then "← Back" three times to return to step 1 without error. This is the final end-to-end
verification matching the original spec's Verification item #2.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app/app.py
git commit -m "feat: add Score step with leaderboard table and cost-integrity callout"
```

---

## Self-Review Notes

- **Spec coverage**: Problem/Architecture/Trajectory/Score steps (Task 2–4), shared render
  function (Task 3), 6-question tier-tagged extraction (Task 1), refusal vs wrong badging
  (Task 3), leaderboard + no-dollar-figure cost callout (Task 4), native-only theme/hierarchy
  (Tasks 2–3), `.streamlit/config.toml` (Task 2) — all covered. Streamlit Community Cloud
  deployment itself is a manual dashboard action outside this repo's code, not a codeable task;
  not included as a plan step.
- **Type consistency**: `entries` list shape (`tier`, `type`, `content`, optional `spl`/
  `verdict`) is defined once in Task 1 and consumed identically by `render_waterfall()` in
  Task 3. `TIER_COLORS`/`TIER_LABELS` defined in Task 2, used unchanged in Task 3. `kind` values
  (`correct`/`wrong`/`refusal`) defined in Task 1's `QUESTION_PLAN`, consumed by `KIND_BADGE` in
  Task 3 with matching keys.
- **Placeholder scan**: no TBDs; every step has complete, runnable code and exact verification
  commands with expected output.
