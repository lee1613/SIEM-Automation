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
from specialists import SPECIALISTS, parse_specialist_tag
from llm_errors import describe_llm_error
from splunk_agent import MAX_ITER, iter_budget
from web_tool import web_lookup

# Points at/above this threshold get the higher-budget worker graph (see
# splunk_agent.iter_budget). Kept as a local constant so the pool's graph
# selection reads standalone; iter_budget is the single source of truth for
# the actual iteration count.
HIGH_VALUE_THRESHOLD = 500

VERIFIER_MAX_ITER = 8  # verifier runs <=3 targeted queries; no 25-iter wandering

SAMPLE_TEMPERATURE = 0.3   # C4 self-consistency sampling for metrics tasks


def graph_key(role: str, high: bool, sample: bool) -> tuple:
    """Pure graph-selection key: sampled (temperature 0.3) graphs exist only
    for the metrics role; the sample flag is a no-op for hunter/content."""
    if sample and role == "metrics":
        return ("metrics_sampled", high)
    return (role, high)


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
    "NEVER guess a FINAL ANSWER you are not confident in. If in doubt, use PARTIAL ANSWER.\n\n"
    "A `web_lookup` tool is available for facts NOT in the Splunk dataset (e.g. a "
    "vendor's published threat severity/date, or which CVE matches a technique) — "
    "use it only for external knowledge, not for anything answerable from BOTSv3 data."
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
    """Status from the worker's terminal message.

    'solved' requires an explicit FINAL ANSWER commitment — a non-empty tail
    with no tag means the worker never actually answered (e.g. ran out of
    iterations mid-tool-call), which must read as 'failed', not 'solved'.
    """
    a = (answer or "").strip()
    if not a:
        return "failed"
    upper = a.upper()
    if "ESCALATE:" in upper or upper.startswith("ESCALATE"):
        return "too_big"
    if "FINAL ANSWER" in upper:
        return "solved"
    if "PARTIAL ANSWER" in upper:
        return "partial"
    return "failed"


class SplunkWorkerPool:
    """Builds worker graphs once per role and runs fresh-session tasks on demand."""

    def __init__(self, splunk, *, senior_api_key: str, senior_model: str = "gpt-5.4",
                 senior_base_url: str | None = None, tracker=None,
                 escalation_api_key: str | None = None,
                 escalation_model: str | None = None):
        self.splunk  = splunk
        self.tracker = tracker
        self.senior_model = senior_model
        self.senior_base_url = senior_base_url

        # Six worker graphs built once at init: 3 specialist roles (hunter/
        # content/metrics, see specialists.py) x 2 budgets each — the base
        # budget (MAX_ITER) for ordinary questions, and a higher budget
        # (iter_budget(>=500)) for high-value questions. All share the same
        # tools (ESCALATE protocol + web_lookup) — only the specialist's extra
        # prompt emphasis and max_iter differ.
        self._graphs = {}
        for name, extra in SPECIALISTS.items():
            instructions = ESCALATE_INSTRUCTIONS + ("\n\n" + extra if extra else "")
            for hi, cap in ((False, MAX_ITER),
                            (True, iter_budget(HIGH_VALUE_THRESHOLD))):
                self._graphs[(name, hi)], _ = agent_mod.create_agent(
                    senior_api_key, splunk,
                    model=senior_model, base_url=senior_base_url,
                    extra_instructions=instructions,
                    extra_tools=[web_lookup],
                    max_iter=cap,
                )
        self.verifier_graph, _ = agent_mod.create_agent(
            senior_api_key, splunk,
            model=senior_model, base_url=senior_base_url,
            extra_instructions=ESCALATE_INSTRUCTIONS,
            extra_tools=[web_lookup],
            max_iter=VERIFIER_MAX_ITER,
        )
        # C4: metrics graphs at temperature 0.3, both budgets — used only when
        # the executor samples a [METRICS] task 3x for a majority vote.
        metrics_instr = ESCALATE_INSTRUCTIONS + "\n\n" + SPECIALISTS["metrics"]
        for hi, cap in ((False, MAX_ITER),
                        (True, iter_budget(HIGH_VALUE_THRESHOLD))):
            self._graphs[("metrics_sampled", hi)], _ = agent_mod.create_agent(
                senior_api_key, splunk,
                model=senior_model, base_url=senior_base_url,
                extra_instructions=metrics_instr,
                extra_tools=[web_lookup],
                max_iter=cap,
                temperature=SAMPLE_TEMPERATURE,
            )
        # C3: escalation graph — the strong model (gpt-5.4) at the high budget,
        # dispatched by the adjudicator on low-confidence 1000-pt questions.
        self.escalation_graph = None
        self.escalation_model = escalation_model
        if escalation_model:
            self.escalation_graph, _ = agent_mod.create_agent(
                escalation_api_key or senior_api_key, splunk,
                model=escalation_model,
                extra_instructions=ESCALATE_INSTRUCTIONS,
                extra_tools=[web_lookup],
                max_iter=iter_budget(HIGH_VALUE_THRESHOLD),
            )

    def run_senior(self, subquestion: str, parent_qid: str, idx: int,
                   points: int = 0, max_iter: int | None = None,
                   sample: bool = False, escalate: bool = False) -> dict:
        """`max_iter` overrides the points-based budget for the one caller that
        needs a different real graph cap (the Verifier's <=3-query pass) —
        routed to a dedicated pre-built graph so the override actually reaches
        the LangGraph step-cap check baked in at create_agent() build time.
        `escalate` routes to the strong-model escalation graph (C3); `sample`
        routes metrics tasks to the temperature-0.3 graph (C4)."""
        if max_iter is not None:
            return self._run("senior", self.verifier_graph, self.senior_model,
                             subquestion, parent_qid, idx, max_iter=max_iter)
        if escalate and self.escalation_graph is not None:
            cap = iter_budget(HIGH_VALUE_THRESHOLD)
            return self._run("senior", self.escalation_graph,
                             self.escalation_model,
                             subquestion, parent_qid, idx, max_iter=cap)
        budget = iter_budget(points)
        role   = parse_specialist_tag(subquestion)
        graph  = self._graphs[graph_key(role, budget > MAX_ITER, sample)]
        return self._run("senior", graph, self.senior_model,
                         subquestion, parent_qid, idx, max_iter=budget)

    def _run(self, role: str, graph, model: str,
             subquestion: str, parent_qid: str, idx: int,
             max_iter: int = MAX_ITER) -> dict:
        thread_id = f"{role}_{parent_qid}_{idx}_{uuid.uuid4().hex[:8]}"
        run_name  = f"{role.capitalize()}-{idx}-{parent_qid}"

        try:
            answer, state = agent_mod.run_agent_traced(
                graph, subquestion, thread_id,
                run_name=run_name,
                tags=[role, parent_qid],
                metadata={"role": role, "qid": parent_qid, "idx": idx},
                tracker=self.tracker,
                max_iter=max_iter,
            )
        except Exception as exc:
            # str(exc) on an openai error prints only the response body, so a 429
            # and a 500 read identically. Name the type/status/provider.
            detail = describe_llm_error(exc, run_name, self.senior_base_url)
            print(detail)
            answer = f"ESCALATE: worker crashed — {detail}"
            state  = {"messages": [], "step_count": 0}

        print(f"\n[WORKER RESULT] {run_name}: {answer[:200]}")

        spl_used, sourcetypes = extract_spl_and_sourcetypes(state)
        status = _classify(answer)

        steps   = int(state.get("step_count", 0)) if isinstance(state, dict) else 0
        cap_hit = steps > max_iter

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
            "iterations":  steps,
            "cap_hit":     cap_hit,
        }
