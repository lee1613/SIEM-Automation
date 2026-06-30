#!/usr/bin/env python3
"""
Splunk worker pool for the v1 multi-agent system.

A worker is the v0 LangGraph agent reused verbatim (verify -> execute gate, 6 Splunk
tools, Intention protocol) with two additions:
  - the model is selectable (Senior = gpt-5.4 via OpenAI; Junior = Llama via NIM in v1.1)
  - the ESCALATE protocol: if the data isn't there / the task is too broad, the worker
    replies with a single `ESCALATE:` line instead of guessing

Each delegated task runs in a FRESH session (new thread_id, no cross-task memory). The
worker's full state is returned for the run summary JSON and for LangSmith tracing.

Per-step traces (LLM calls, tool calls) are sent to LangSmith automatically via
LANGCHAIN_TRACING_V2. Each worker is tagged with its role, parent qid, and sequential
index so traces are filterable in the LangSmith UI.
"""

import re
import uuid

import splunk_agent as agent_mod


ESCALATE_INSTRUCTIONS = (
    "RESPONSE PROTOCOL — end every response with exactly ONE of these three modes:\n\n"
    "1. CONFIDENT ANSWER — you found the exact value and verified it:\n"
    "   FINAL ANSWER: <the precise value>\n"
    "   SPL: <the query or sourcetype that produced it>\n\n"
    "2. PARTIAL ANSWER — you found useful evidence but are NOT fully certain:\n"
    "   PARTIAL ANSWER: <your best candidate value or key finding>\n"
    "   UNCERTAINTY: <why you cannot be 100% sure>\n"
    "   NEXT STEP: <what specific check would confirm it>\n"
    "   Use this when you found something concrete but couldn't fully verify it. "
    "The orchestrator will use your finding to issue a targeted follow-up if needed. "
    "Include the actual evidence (field values, event counts, SPL used).\n\n"
    "3. ESCALATE — you found nothing useful after thorough investigation:\n"
    "   ESCALATE: <exactly what you searched, what was missing, how to narrow the task>\n"
    "   Only use this as a last resort — first try alternative sourcetypes and keywords.\n\n"
    "NEVER guess a FINAL ANSWER you are not confident in. If in doubt, use PARTIAL ANSWER."
)


def serialize_messages(state: dict) -> list:
    """Convert LangChain messages in a final state into JSON-serializable dicts."""
    out = []
    for m in state.get("messages", []):
        entry = {"type": type(m).__name__, "content": getattr(m, "content", "") or ""}
        tcs = getattr(m, "tool_calls", None)
        if tcs:
            entry["tool_calls"] = [{"name": tc["name"], "args": tc["args"]} for tc in tcs]
        name = getattr(m, "name", None)
        if name:
            entry["name"] = name
        out.append(entry)
    return out


def extract_spl_and_sourcetypes(state: dict) -> tuple[list, list]:
    """Pull every run_splunk_search query and the sourcetypes it touched from a state."""
    spls, sts = [], set()
    for m in state.get("messages", []):
        for tc in (getattr(m, "tool_calls", None) or []):
            if tc["name"] == "run_splunk_search":
                q = tc["args"].get("query", "")
                if q:
                    spls.append(q)
                mt = re.search(r'sourcetype\s*=\s*"?([^\s",|)]+)', q, re.IGNORECASE)
                if mt:
                    sts.add(mt.group(1).strip('"\''))
    return spls, sorted(sts)


def _classify(answer: str) -> str:
    a = (answer or "").strip()
    if not a:
        return "failed"
    upper = a.upper()
    if upper.startswith("ESCALATE") or "ESCALATE:" in upper:
        return "too_big"
    if upper.startswith("PARTIAL ANSWER") or "PARTIAL ANSWER:" in upper:
        return "partial"
    return "solved"


class SplunkWorkerPool:
    """Builds worker graphs once per role and runs fresh-session tasks on demand."""

    def __init__(self, splunk, *, senior_api_key: str, senior_model: str = "gpt-5.4",
                 senior_base_url: str | None = None):
        self.splunk = splunk
        self.senior_model = senior_model
        self.senior_graph, _ = agent_mod.create_agent(
            senior_api_key, splunk,
            model=senior_model, base_url=senior_base_url,
            extra_instructions=ESCALATE_INSTRUCTIONS,
        )

    def run_senior(self, subquestion: str, parent_qid: str, idx: int) -> dict:
        return self._run("senior", self.senior_graph, self.senior_model,
                         subquestion, parent_qid, idx)

    def _run(self, role: str, graph, model: str,
             subquestion: str, parent_qid: str, idx: int) -> dict:
        thread_id = f"{role}_{parent_qid}_{idx}_{uuid.uuid4().hex[:8]}"
        run_name  = f"{role.capitalize()}-{idx}-{parent_qid}"

        try:
            answer, state = agent_mod.run_agent_traced(
                graph, subquestion, thread_id,
                run_name=run_name,
                tags=[role, parent_qid],
                metadata={"role": role, "qid": parent_qid, "idx": idx},
            )
        except Exception as exc:
            answer = f"ESCALATE: worker crashed — {exc}"
            state  = {"messages": []}

        print(f"\n[WORKER RESULT] {run_name}: {answer[:200]}")

        spl_used, sourcetypes = extract_spl_and_sourcetypes(state)
        status = _classify(answer)

        return {
            "role":        role,
            "idx":         idx,
            "parent_qid":  parent_qid,
            "subquestion": subquestion,
            "model":       model,
            "answer":      answer,
            "status":      status,
            "spl_used":    spl_used,
            "sourcetypes": sourcetypes,
            "full_state":  serialize_messages(state),
        }
