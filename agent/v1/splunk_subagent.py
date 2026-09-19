#!/usr/bin/env python3
"""
Splunk worker pool for the v1 multi-agent system.

A worker is the v0 LangGraph agent reused verbatim (verify -> execute gate, 6 Splunk
tools, Intention protocol) with two additions:
  - the model is selectable (Senior = gpt-5.4 via OpenAI; Junior = Llama via NIM in v1.1)
  - the submit_finding contract: the worker reports via a terminal tool call whose
    arguments are the schema, never as prose (see finding.py)

Worker graphs are built lazily and cached by (role, iteration cap): a task either
starts a FRESH session (new thread_id, `run_senior`) or resumes a live senior's own
thread_id with a new directive (`run_round`), consuming another round against the
same graph. The worker's full state is returned for the run summary JSON and for
LangSmith tracing.

Per-step traces (LLM calls, tool calls) are sent to LangSmith automatically via
LANGCHAIN_TRACING_V2. Each worker is tagged with its role, parent qid, and sequential
index so traces are filterable in the LangSmith UI.
"""

import json
import re
import threading
import uuid

import splunk_agent as agent_mod
from exploration import EXPLORATION_MODEL, build_exploration_agent, render_report, run_exploration
from finding import _classify_prose, empty_finding, parse_finding, submit_finding
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from llm_errors import describe_llm_error, provider_of, resilient_http_client
from specialists import SPECIALISTS, parse_specialist_tag
from splunk_agent import MAX_ITER, iter_budget
from usage_tracker import context_window
from web_tool import web_lookup

FINISH_INSTRUCTIONS = (
    "HOW TO FINISH — call `submit_finding` exactly once, as your final action.\n\n"
    "It is the ONLY way to report. Do not write your answer as prose instead, and "
    "do not write it as prose as well as calling the tool: a value typed into a "
    "sentence has to be scraped back out, and that scraping is where correct "
    "answers get mangled on the way to a scoreboard that scores exact matches.\n\n"
    "`status` says which of the four outcomes you reached:\n"
    "  solved   — you found the exact value and verified it. Put it in `value`.\n"
    "  partial  — you have something useful but not a confirmed answer. If you "
    "have a clean candidate put it in `value`; if you do not, leave `value` EMPTY "
    "and put what you learned in `notes`.\n"
    "  too_big  — the task needs narrowing before it can be answered.\n"
    "  failed   — you found nothing usable after a thorough search.\n\n"
    "Never claim `solved` for a value you are not confident in — that is what "
    "`partial` is for, and an honest low `confidence` is more useful than a wrong "
    "high one. Whatever you checked and eliminated goes in `ruled_out`; it is what "
    "stops the next worker re-treading your dead ends.\n\n"
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


def truncated_calls(state: dict) -> list[str]:
    """Every tool call this round whose result was cut short, with how much went
    unseen — read from the tool results, so a senior cannot report it away."""
    calls = {tc["id"]: tc for m in state.get("messages", [])
             for tc in (getattr(m, "tool_calls", None) or [])}
    out = []
    for m in state.get("messages", []):
        if not isinstance(m, ToolMessage):
            continue
        cut = re.search(r"showing (\d+) of (\d+) rows", str(m.content))
        tc = calls.get(m.tool_call_id)
        if cut and tc:
            args = tc["args"].get("query") or json.dumps(tc["args"], sort_keys=True)
            args = args if len(args) <= 90 else args[:90] + "…"   # SH needs which search, not all of it
            out.append(f"`{tc['name']}: {args}` ({cut.group(1)} of {cut.group(2)} rows seen)")
    return out


def _classify(answer: str) -> str:
    """Status from a worker's terminal text. Lives in finding.py now, next to the
    structured path it is the fallback for; re-exported here for existing callers."""
    return _classify_prose(answer)


class SplunkWorkerPool:
    """Builds worker graphs lazily, keyed by (role, iteration cap), and runs
    fresh-session tasks or resumable rounds against them on demand."""

    def __init__(self, splunk, *, senior_api_key: str, senior_model: str = "gpt-5.4",
                 senior_base_url: str | None = None, tracker=None,
                 exploration_api_key: str | None = None,
                 exploration_base_url: str | None = None,
                 senior_fallback: dict | None = None,
                 senior_price_as: str | None = None):
        self.splunk  = splunk
        self.senior_price_as = senior_price_as   # see splunk_agent.chat_llm
        # {"api_key", "model", "base_url"} of the provider that takes a senior
        # call the primary refuses (Featherless out of credit -> AI&).
        self.senior_fallback = senior_fallback
        self.tracker = tracker
        self.senior_model = senior_model
        self.senior_base_url = senior_base_url
        self._senior_api_key = senior_api_key
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

        # Worker graphs are built on demand and cached by (role, iteration cap).
        # v1.3.0 pre-built six (3 roles x 2 budgets); v1.4 adds a third cap —
        # one round (8 iterations) — and building nine eagerly would pay for
        # graphs a given run never uses.
        self._graphs: dict = {}
        # Guards check-and-build below: two senior threads racing the same
        # (role, cap) key would otherwise each build a graph (each with its own
        # MemorySaver) and the loser's graph — and any thread_id already run
        # against it — is gone from self._graphs after the winner overwrites it.
        self._graphs_lock = threading.Lock()

        # A CLARIFY reply is answered from what the senior already holds: no
        # tools, no Splunk, no round consumed (§3.3). So it is a bare model call
        # over the thread's history, not a graph invocation. Same token budget
        # and transport settings as a worker graph's own LLM (see create_agent)
        # — a reasoning model (GLM-5.3 is the default senior) can spend a
        # tighter budget entirely on hidden reasoning and return "".
        # Same field trap as the worker graph - see token_limit_kwargs.
        fb = senior_fallback
        self._clarify_llm = agent_mod.with_fallback(
            agent_mod.chat_llm(senior_api_key, senior_model, senior_base_url,
                               http_client=self._http, price_as=senior_price_as),
            agent_mod.chat_llm(fb["api_key"], fb["model"], fb["base_url"],
                               http_client=self._http,
                               price_as=fb.get("price_as")) if fb else None)

    def _graph_for(self, role: str, cap: int):
        """The worker graph for this specialist role at this iteration cap."""
        key = (role, cap)
        if key not in self._graphs:
            with self._graphs_lock:
                if key not in self._graphs:  # re-check: lost the race while waiting
                    extra = SPECIALISTS.get(role, "")
                    instructions = FINISH_INSTRUCTIONS + ("\n\n" + extra if extra else "")
                    self._graphs[key], _ = agent_mod.create_agent(
                        self._senior_api_key, self.splunk,
                        model=self.senior_model, base_url=self.senior_base_url,
                        http_client=self._http,
                        extra_instructions=instructions,
                        extra_tools=[web_lookup, submit_finding],
                        max_iter=cap,
                        context_window=context_window(self.senior_model),
                        fallback=self.senior_fallback,
                        price_as=self.senior_price_as,
                    )
        return self._graphs[key]

    def run_senior(self, subquestion: str, parent_qid: str, idx: int,
                   points: int = 0, max_iter: int | None = None) -> dict:
        """Route to the graph for this task's specialist role and points
        budget. `max_iter` is accepted for callers that want to cap a single
        run below its role budget."""
        budget = max_iter if max_iter is not None else iter_budget(points)
        role   = parse_specialist_tag(subquestion)
        graph  = self._graph_for(role, budget)
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

    def run_round(self, *, thread_id: str, message: str, qid: str, idx: int,
                  technique: str = "senior", max_iter: int = 8) -> dict:
        """One round of a LIVE senior: resume `thread_id` with a new directive.

        The thread is the whole point. `run_agent_traced` seeds `step_count: 0`
        on every invoke while `messages` uses the add_messages reducer, so this
        appends the directive to the senior's existing transcript and hands it a
        fresh iteration budget — no re-briefing, which is the cost v1.3.0 paid on
        every replan round.

        A given senior must call this with the SAME (technique, max_iter) on
        every round: its thread_id lives inside the graph built for that
        (role, cap) key's checkpointer, so resuming it against a different cap
        resumes a graph that has never seen this thread_id.
        """
        graph = self._graph_for(technique, max_iter)
        return self._run("senior", graph, self.senior_model, message, qid, idx,
                         max_iter=max_iter, thread_id=thread_id)

    def clarify(self, *, thread_id: str, qid: str, idx: int, questions: list,
                technique: str = "senior", max_iter: int = 8, preface: str = "") -> str:
        """Answer SH's clarifying questions from the senior's existing context.
        `preface` (SH's answers to the senior's own open questions) precedes them.

        No tools and no round consumed (§3.3): if the senior would have to touch
        Splunk to answer, the route was a COMMAND, not a CLARIFY. The exchange is
        written back into the thread so the next round sees it.
        """
        graph   = self._graph_for(technique, max_iter)
        config  = {"configurable": {"thread_id": thread_id}}
        history = list((graph.get_state(config).values or {}).get("messages", []))
        ask = HumanMessage(content=(
            preface
            + "Your orchestrator has questions about the report you just filed. "
            "Answer them from what you ALREADY know — do not search, do not call "
            "any tool. If you genuinely cannot answer without a new query, say so "
            "in one line and name the query that would settle it.\n\n"
            + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))))
        reply = self._clarify_llm.invoke(
            [SystemMessage(content="You are the Senior Splunk analyst answering your "
                                   "orchestrator. Be brief and concrete.")]
            + history + [ask],
            config={"callbacks": [self.tracker] if self.tracker else [],
                    "tags": ["senior", qid],
                    "metadata": {"role": "senior", "qid": qid, "idx": idx}},
        )
        text = (reply.content or "").strip()
        graph.update_state(config, {"messages": [ask, reply]})
        return text

    def _run(self, role: str, graph, model: str,
             subquestion: str, parent_qid: str, idx: int,
             max_iter: int = MAX_ITER, thread_id: str | None = None) -> dict:
        thread_id  = thread_id or f"{role}_{parent_qid}_{idx}_{uuid.uuid4().hex[:8]}"
        run_name   = f"{role.capitalize()}-{idx}-{parent_qid}"
        api_failed = False
        cfg        = {"configurable": {"thread_id": thread_id}}

        # A resumed thread already holds every prior round's messages. Only the
        # ones THIS invoke appends belong to this round - record how many exist
        # before invoking so they can be sliced off below. 0 for a fresh thread,
        # a graph with no checkpointer (the exploration graph, a test double)
        # or a thread that has never been invoked.
        before = 0
        if hasattr(graph, "get_state"):
            snap   = graph.get_state(cfg)
            values = getattr(snap, "values", None) or {}
            before = len(values.get("messages", []))

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
            answer = f"worker crashed — {detail}"
            state  = {"messages": [], "step_count": 0}
            api_failed = True

        print(f"\n[WORKER RESULT] {run_name}: {answer[:200]}")

        # This round's messages only - see `before` above. Everything downstream
        # (the finding, the SPL/sourcetypes it used, the serialized transcript)
        # reads round_state instead of the full accumulated thread, or a round
        # that ends without submit_finding would report the PRIOR round's value.
        all_msgs   = state.get("messages", []) if isinstance(state, dict) else []
        round_msgs = all_msgs[before:]
        round_state = dict(state) if isinstance(state, dict) else {}
        round_state["messages"] = round_msgs

        spl_used, sourcetypes = extract_spl_and_sourcetypes(round_state)
        # A provider outage is not a reasoning outcome. Without this the crash
        # text ("worker crashed - ...") would classify as an ordinary give-up
        # like an honest give-up, and SH responds to an outage by decomposing the
        # task and dispatching more workers at the same dead endpoint.
        # A worker that blew the output-token guard is stuck, not thorough - its
        # answer (if any) is untrustworthy. Flag it so the executor routes to the
        # HITL interrupt rather than folding it into an ordinary reasoning failure.
        runaway = (isinstance(state, dict)
                   and agent_mod.over_output_cap(state))
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
            finding = parse_finding(round_msgs, answer)
            status  = finding["status"]

        steps   = int(state.get("step_count", 0)) if isinstance(state, dict) else 0
        cap_hit = steps > max_iter

        # The cap (step > max_iter) and runaway (output_tokens > cap) paths both
        # route should_continue -> END on an AIMessage that still has tool_calls
        # (the cap's forced final call is made with submit_finding still bound;
        # runaway can hit mid-ordinary-turn). That leaves the thread ending in a
        # tool_calls message with no matching ToolMessage, which OpenAI rejects
        # on any later call against this thread (the next clarify or round). Close
        # them here - skipped when the graph has no checkpointer to update (an
        # api_failed run never reached the graph; the exploration graph and test
        # doubles have no update_state).
        if not api_failed and hasattr(graph, "update_state"):
            last = round_msgs[-1] if round_msgs else None
            tool_calls = getattr(last, "tool_calls", None) if last is not None else None
            if tool_calls:
                closes = [ToolMessage(content="Finding recorded.",
                                      tool_call_id=tc["id"], name=tc["name"])
                         for tc in tool_calls]
                graph.update_state(cfg, {"messages": closes}, as_node="agent")

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
            "full_state":  serialize_messages(round_state),
            "truncated":   truncated_calls(round_state),
            "iterations":  steps,
            "cap_hit":     cap_hit,
            "last_prompt_tokens": (int(state.get("last_prompt_tokens", 0))
                                   if isinstance(state, dict) else 0),
            # Schema B fields - see finding.py.
            "value":             finding["value"],
            "value_kind":        finding["value_kind"],
            "evidence":          finding["evidence"],
            "confidence":        finding["confidence"],
            "search_space_used": finding["search_space_used"],
            "negative_findings": finding["negative_findings"],
            "notes":             finding["notes"],
            "structured":        finding["structured"],
            "insight":           finding["insight"],
            "report":            finding["report"],
        }
