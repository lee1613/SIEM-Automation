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
