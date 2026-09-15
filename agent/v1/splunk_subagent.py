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
from llm_errors import describe_llm_error, provider_of, resilient_http_client
from splunk_agent import MAX_ITER, iter_budget
from exploration import (EXPLORATION_MODEL, build_exploration_agent,
                         render_report, run_exploration)
from finding import _classify_prose, empty_finding, parse_finding, submit_finding
from web_tool import web_lookup

# Points at/above this threshold get the higher-budget worker graph (see
# splunk_agent.iter_budget). Kept as a local constant so the pool's graph
# selection reads standalone; iter_budget is the single source of truth for
# the actual iteration count.
HIGH_VALUE_THRESHOLD = 500



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
    """Status from a worker's terminal text. Lives in finding.py now, next to the
    structured path it is the fallback for; re-exported here for existing callers."""
    return _classify_prose(answer)


class SplunkWorkerPool:
    """Builds worker graphs once per role and runs fresh-session tasks on demand."""

    def __init__(self, splunk, *, senior_api_key: str, senior_model: str = "gpt-5.4",
                 senior_base_url: str | None = None, tracker=None,
                 exploration_api_key: str | None = None,
                 exploration_base_url: str | None = None):
        self.splunk  = splunk
        self.tracker = tracker
        self.senior_model = senior_model
        self.senior_base_url = senior_base_url
        # One pooled, thread-safe client shared by every worker graph.
        self._http = resilient_http_client()

        # Exploration runs on a cheap NIM model and only when SH cannot name a
        # search space at all. Built lazily-by-config: no NIM key, no agent, and
        # an exploration spawn then degrades to an ordinary Senior rather than
        # failing the question.
        self.exploration_graph = None
        self.exploration_budget = {"content_scans": 0}
        if exploration_api_key and exploration_base_url:
            self.exploration_graph, self.exploration_budget = build_exploration_agent(
                exploration_api_key, exploration_base_url, splunk)

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
                    model=senior_model, base_url=senior_base_url, http_client=self._http,
                    extra_instructions=instructions,
                    extra_tools=[web_lookup, submit_finding],
                    max_iter=cap,
                )

    def run_senior(self, subquestion: str, parent_qid: str, idx: int,
                   points: int = 0, max_iter: int | None = None) -> dict:
        """Route to the pre-built graph for this task's specialist role and
        points budget. `max_iter` is accepted for callers that want to cap a
        single run below its role budget."""
        budget = max_iter if max_iter is not None else iter_budget(points)
        role   = parse_specialist_tag(subquestion)
        graph  = self._graphs[(role, budget > MAX_ITER)]
        return self._run("senior", graph, self.senior_model,
                         subquestion, parent_qid, idx, max_iter=budget)

    def run_exploration(self, question: str, parent_qid: str, idx: int) -> dict:
        """Find which feeds could hold the answer. Returns a delegation-shaped
        dict so the executor and the ledger handle it like any other worker -
        `answer` carries the rendered report, and `value` stays empty because an
        exploration worker never produces a scoreboard answer."""
        if self.exploration_graph is None:
            return {**empty_finding("failed"), "role": "exploration",
                    "answer": "exploration agent not configured",
                    "spl_used": [], "sourcetypes": [], "full_state": [],
                    "iterations": 0, "cap_hit": False,
                    "model": "", "provider": "nim"}
        report = run_exploration(self.exploration_graph, self.exploration_budget,
                                 question, qid=parent_qid, idx=idx,
                                 tracker=self.tracker)
        found = bool(report["source_types"] or report["sources"])
        status = ("api_failed" if report.get("api_failed")
                  else "partial" if found else "failed")
        finding = empty_finding(status)
        finding["structured"] = report["structured"]
        finding["search_space_used"] = {"sourcetypes": report["source_types"],
                                        "sources": report["sources"]}
        finding["notes"] = report["insights"]
        return {**finding,
                "role": "exploration", "idx": idx, "parent_qid": parent_qid,
                "subquestion": question, "model": EXPLORATION_MODEL,
                "provider": "nim", "answer": render_report(report),
                "spl_used": [], "sourcetypes": report["source_types"],
                "full_state": [], "iterations": 0, "cap_hit": False}

    def _run(self, role: str, graph, model: str,
             subquestion: str, parent_qid: str, idx: int,
             max_iter: int = MAX_ITER) -> dict:
        thread_id  = f"{role}_{parent_qid}_{idx}_{uuid.uuid4().hex[:8]}"
        run_name   = f"{role.capitalize()}-{idx}-{parent_qid}"
        api_failed = False

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
            api_failed = True

        print(f"\n[WORKER RESULT] {run_name}: {answer[:200]}")

        spl_used, sourcetypes = extract_spl_and_sourcetypes(state)
        # A provider outage is not a reasoning outcome. Without this the crash
        # text ("ESCALATE: worker crashed - ...") classifies as "too_big" exactly
        # like an honest give-up, and SH responds to an outage by decomposing the
        # task and dispatching more workers at the same dead endpoint.
        # A worker that blew the output-token guard is stuck, not thorough - its
        # answer (if any) is untrustworthy. Flag it so the executor routes to the
        # HITL interrupt rather than folding it into an ordinary reasoning failure.
        runaway = (isinstance(state, dict)
                   and state.get("output_tokens", 0) > agent_mod.OUTPUT_TOKEN_CAP)
        # Schema B: the finding comes from the worker's terminal submit_finding
        # call, with a prose fallback when it skipped the tool (see finding.py).
        # api_failed and runaway are transport outcomes, not findings - they keep
        # their own status and carry an empty finding rather than whatever text
        # the crash handler synthesised.
        if runaway:
            print(f"[WORKER RUNAWAY] {run_name}: "
                  f"{state.get('output_tokens', 0):,} output tokens")
        if api_failed or runaway:
            status  = "api_failed" if api_failed else "runaway"
            finding = empty_finding(status)
        else:
            msgs    = state.get("messages") if isinstance(state, dict) else []
            finding = parse_finding(msgs, answer)
            status  = finding["status"]

        steps   = int(state.get("step_count", 0)) if isinstance(state, dict) else 0
        cap_hit = steps > max_iter

        return {
            "role":        role,
            "idx":         idx,
            "parent_qid":  parent_qid,
            "subquestion": subquestion,
            "model":       model,
            "provider":    provider_of(self.senior_base_url),
            "answer":      answer,
            "status":      status,
            "spl_used":    spl_used,
            "sourcetypes": sourcetypes,
            "full_state":  serialize_messages(state),
            "iterations":  steps,
            "cap_hit":     cap_hit,
            # Schema B fields - see finding.py.
            "value":             finding["value"],
            "value_kind":        finding["value_kind"],
            "evidence":          finding["evidence"],
            "confidence":        finding["confidence"],
            "search_space_used": finding["search_space_used"],
            "negative_findings": finding["negative_findings"],
            "notes":             finding["notes"],
            "structured":        finding["structured"],
        }
