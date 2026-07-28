"""Self-serve replay demo for the SIEM-Automation multi-agent BOTSv3 agent.
Reads only static committed JSON — no live Splunk/LLM calls, zero cost per visitor.
"""
from __future__ import annotations

import json
from pathlib import Path

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
