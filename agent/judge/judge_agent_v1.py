#!/usr/bin/env python3
"""
Judge Agent v1 — Cybersecurity Analyst with Hypothesis-Driven Investigation

The Judge is the analytical brain of the multi-agent SIEM system.
It receives BOTSv3 questions, forms cybersecurity hypotheses, generates
targeted Splunk queries, evaluates results as evidence, and extracts
exact answers in the required scoreboard format.

Design principles:
- Separation of concerns: Judge REASONS, Query Planner EXECUTES
- Hypothesis-driven: every search has an explicit purpose
- Evidence accumulation: findings persist across search iterations
- Format-aware answers: strict extraction matching answer_guidance
- Observability: every reasoning step and tool call is logged

Communication with Query Planner:
- Judge calls query_planner.execute_search(spl) via LangChain tool
- Results flow back to the Judge for evaluation

Model: meta/llama-3.3-70b-instruct (verified function-calling support)
Framework: LangGraph StateGraph
Version: v1
"""

import json
import logging
import os
import sys
import re
from typing import Annotated, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

# ── Path setup ─────────────────────────────────────────────────────────────────

_JUDGE_DIR = os.path.dirname(os.path.abspath(__file__))
_AGENT_DIR = os.path.dirname(_JUDGE_DIR)
sys.path.insert(0, _AGENT_DIR)

from query_planner.query_planner_v1 import QueryPlannerV1

# ── Logging ────────────────────────────────────────────────────────────────────

logger = logging.getLogger("judge_agent_v1")

# ── Configuration ──────────────────────────────────────────────────────────────

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
JUDGE_MODEL  = "meta/llama-3.3-70b-instruct"
MAX_ITER     = 20

# ── System Prompt ──────────────────────────────────────────────────────────────
# CRITICAL: Keep this concise. The 70b model fails to use tools with prompts >6K chars.
# Embed only the most critical BOTSv3 knowledge needed to generate correct SPL queries.

JUDGE_SYSTEM_PROMPT = """You are a Tier 1 SOC analyst investigating the BOTSv3 dataset — an APT attack against Frothly Brewing Company in August 2018. Answer questions using Splunk tools. Every answer must come from actual query results.

## Rules
- Call submit_final_answer with the EXACT value only. No prose, no explanation.
- Never infer a specific value (ID, name, count) — extract it from data.
- Never submit "None"/"Not found" without first trying 3+ distinct strategies.
- Sanity-check your answer before submitting: filename must have extension, UUID is 36-char hex, count is integer.

## Investigation Steps
1. Identify the relevant sourcetype for the question (AWS, Windows, network, email…).
2. START BROAD: first query uses only 1-2 conditions. Do NOT assume field names or add keyword guesses until you've seen the data.
3. When 0 results: DIAGNOSE before retrying:
   a. Remove all field=value filters and retry with keyword-only search. If results appear, the fields aren't pre-parsed — use `| rex field=_raw "pattern"` to extract.
   b. Check if the sourcetype has any data at all: `index=botsv3 sourcetype="name" | head 3`
4. Use get_field_values or sample_sourcetype_events to discover actual field names and values before filtering.
5. Extract exact values: `| table field` or `| stats ... by field`. Then call submit_final_answer.

## SPL Rules
- All queries: `index=botsv3 sourcetype="name" ...`
- Use `| stats`, `| top`, `| table`, `| rare` — never return raw events as the final answer
- Temporal order: `| sort _time` or `| stats min(_time) as first by field`
- No leading wildcards (`*val` is forbidden; `val*` is fine)
- Unparsed logs (S3, IIS, syslog): always use `| rex field=_raw` to extract fields

## Sourcetypes
aws:cloudtrail          — AWS API calls (CloudTrail); well-structured JSON fields
aws:s3:accesslogs       — S3 access log; RAW text, space-separated columns; fields like operation/key NOT pre-parsed; must use rex
aws:cloudwatchlogs:vpcflow — VPC flow records (src/dst IP, ports, bytes, action)
aws:elb:accesslogs      — ELB access log (raw text)
aws:rds:audit           — RDS DB audit
aws:description         — AWS resource inventory
hardware                — Host hardware inventory
XmlWinEventLog:Microsoft-Windows-Sysmon/Operational — Sysmon (process, network, file, registry)
XmlWinEventLog:Security — Windows Security log (auth, account management)
XmlWinEventLog:System   — Windows System log
WinRegistry             — Registry key/value changes
symantec:ep:security:file — Symantec EP threat detections
symantec:ep:agent:file  — SEP agent status
stream:dns              — DNS traffic (wire capture)
stream:http             — HTTP traffic decoded
stream:smtp             — SMTP email traffic
stream:tcp              — Raw TCP sessions
iis                     — IIS web server log (raw text)
suricata                — IDS/IPS alerts
pan:traffic             — Palo Alto firewall log
cisco:nvm               — Cisco NVM endpoint flows
code42:security         — Code42 DLP events
osquery:results         — Osquery endpoint telemetry
linux:audit             — Linux auditd
linux:syslog            — Linux syslog

## Answer Format
- List: alphabetical, comma-separated, no spaces (a,b,c)
- Number: digits only, no units (2.93 not "2.93 MB")
- Hostname: short form unless FQDN explicitly required
- ID/UUID/path: exact copy from data"""

# ── Agent State ────────────────────────────────────────────────────────────────

class JudgeState(TypedDict):
    messages:        Annotated[list, add_messages]
    question:        str
    answer_guidance: str
    evidence:        list
    failed_queries:  list   # SPL queries that returned error/0 results — dedup guard
    search_count:    int
    nudge_count:     int    # How many times nudge has fired — caps loops
    final_answer:    str
    done:            bool


# ── Tool factory ───────────────────────────────────────────────────────────────

def make_judge_tools(query_planner: QueryPlannerV1) -> list:
    """Return LangChain tools that close over the given QueryPlannerV1 instance."""

    @tool
    def execute_splunk_search(spl_query: str, purpose: str, max_results: int = 100) -> str:
        """Execute a Splunk SPL query. Query MUST start with index=botsv3.

        Args:
            spl_query: Full SPL string starting with index=botsv3
            purpose: One sentence explaining what this search is trying to find
            max_results: Max rows to return (default 100)

        If this query previously failed or returned 0 results, CHANGE the query
        significantly before calling again — don't repeat a failed query.
        """
        logger.info("[QP] search | purpose=%s | spl=%s", purpose, spl_query)
        print(f"\n[QueryPlanner] Purpose: {purpose}")
        print(f"[QueryPlanner] SPL: {spl_query}")
        result = query_planner.execute_search(spl_query, max_results=int(max_results))
        try:
            parsed = json.loads(result)
            n = len(parsed.get("results", []))
            total = parsed.get("meta", {}).get("total_event_count", "?")
            print(f"[QueryPlanner] -> {n} results (total={total})")
        except Exception:
            pass
        print(f"[QueryPlanner] Raw: {result[:600]}{'...' if len(result) > 600 else ''}\n")
        return result

    @tool
    def sample_sourcetype_events(sourcetype: str, keyword: str = "", count: int = 3) -> str:
        """Sample raw events from a sourcetype to discover field structure.

        Args:
            sourcetype: e.g. 'aws:cloudtrail', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'
            keyword: optional keyword filter
            count: number of events to return (max 8)
        """
        logger.info("[QP] sample | sourcetype=%s keyword=%s", sourcetype, keyword)
        print(f"\n[QueryPlanner] Sampling: sourcetype={sourcetype} keyword={keyword!r}")
        result = query_planner.sample_events(sourcetype=sourcetype, keyword=keyword, count=count)
        print(f"[QueryPlanner] Sample: {result[:500]}{'...' if len(result) > 500 else ''}\n")
        return result

    @tool
    def get_field_values(field: str, sourcetype: str = "", top_n: int = 20) -> str:
        """Get the top distinct values for a field within a sourcetype.

        Args:
            field: Field name (e.g. 'eventName', 'userIdentity.userName')
            sourcetype: Optional scoping sourcetype
            top_n: Max distinct values to return
        """
        logger.info("[QP] field_values | field=%s sourcetype=%s", field, sourcetype)
        print(f"\n[QueryPlanner] Field values: field={field} sourcetype={sourcetype}")
        result = query_planner.get_field_values(field=field, sourcetype=sourcetype, top_n=top_n)
        print(f"[QueryPlanner] Values: {result[:400]}{'...' if len(result) > 400 else ''}\n")
        return result

    @tool
    def submit_final_answer(answer: str, confidence: str, reasoning: str) -> str:
        """Submit the final answer to conclude the investigation.

        Args:
            answer: The EXACT answer value. NO prose, NO units, NO explanation.
                    Match the answer_guidance format precisely.
            confidence: 'high', 'medium', or 'low'
            reasoning: 1-2 sentences explaining how you found this answer

        IMPORTANT: This ends the investigation. The answer goes directly to the scoreboard.
        """
        logger.info("[Judge] FINAL ANSWER | answer=%s | confidence=%s", answer, confidence)
        print(f"\n[Judge] === FINAL ANSWER ===")
        print(f"[Judge] Answer: {answer!r}")
        print(f"[Judge] Confidence: {confidence}")
        print(f"[Judge] Reasoning: {reasoning}\n")
        return json.dumps({"status": "answer_submitted", "answer": answer})

    return [
        execute_splunk_search,
        sample_sourcetype_events,
        get_field_values,
        submit_final_answer,
    ]


# ── Graph factory ──────────────────────────────────────────────────────────────

def create_judge_agent(api_key: str, query_planner: QueryPlannerV1):
    """Build and compile the Judge Agent LangGraph. Returns (graph, checkpointer).

    Graph topology:
        judge_node ──(tool calls)──► tool_node ──► judge_node
                   └─(submit_final_answer or max iter)──► END
    """
    tools    = make_judge_tools(query_planner)
    tool_map = {t.name: t for t in tools}

    llm = ChatOpenAI(
        base_url=NIM_BASE_URL,
        api_key=api_key,
        model=JUDGE_MODEL,
        max_tokens=2048,
        temperature=0,
    )
    model_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    # Bare model for forced conclusion (no tools to avoid infinite tool loop)
    model_bare = ChatOpenAI(
        base_url=NIM_BASE_URL,
        api_key=api_key,
        model=JUDGE_MODEL,
        max_tokens=512,
        temperature=0,
    )

    print(f"[Judge] Model: {JUDGE_MODEL}")
    system_msg = SystemMessage(content=JUDGE_SYSTEM_PROMPT)

    # ── Node: judge ────────────────────────────────────────────────────────────
    def judge_node(state: JudgeState) -> dict:
        step = state.get("search_count", 0) + 1
        msgs = [system_msg] + list(state["messages"])

        if step > MAX_ITER:
            print(f"\n[Judge] Max iterations ({MAX_ITER}) — forcing conclusion")
            # Force bare model to extract answer from conversation history
            evidence = state.get("evidence", [])
            evidence_txt = "\n".join(f"- {e}" for e in evidence) if evidence else "None recorded"
            guidance = state.get("answer_guidance", "")
            force_msg = HumanMessage(
                f"FINAL STEP: Based on everything found so far, call submit_final_answer now.\n"
                f"Evidence gathered:\n{evidence_txt}\n"
                f"Answer format: {guidance}\n"
                f"Give ONLY the exact answer value in the required format."
            )
            response = model_with_tools.invoke(msgs + [force_msg])
        else:
            response = model_with_tools.invoke(msgs)

        # Logging
        if response.content:
            label = "[Judge thinking]" if getattr(response, "tool_calls", None) else "[Judge response]"
            print(f"\n{label}\n{response.content}\n")
        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                args_preview = json.dumps(tc["args"])[:300]
                print(f"[Judge] -> {tc['name']}({args_preview})")

        return {"messages": [response], "search_count": step}

    # ── Node: tools ────────────────────────────────────────────────────────────
    def tool_node(state: JudgeState) -> dict:
        """Execute all pending tool calls, collect evidence, and track failed queries."""
        last           = state["messages"][-1]
        results        = []
        new_evidence   = list(state.get("evidence", []))
        failed_queries = set(state.get("failed_queries", []))
        done           = state.get("done", False)
        final_ans      = state.get("final_answer", "")

        for tc in last.tool_calls:
            logger.info("[tool_node] %s", tc["name"])

            # Dedup guard: reject identical failed/empty queries to break loops
            if tc["name"] == "execute_splunk_search":
                spl = tc["args"].get("spl_query", "")
                if spl in failed_queries:
                    warn = (
                        f"Rejected: this exact query already returned an error or 0 results. "
                        f"Rewrite the query with different filters, sourcetype, or approach.\n"
                        f"Rejected query: {spl}"
                    )
                    print(f"[Judge] [DEDUP REJECT] {spl[:80]}")
                    results.append(ToolMessage(
                        content=json.dumps({"error": warn}),
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    ))
                    continue

            try:
                raw    = tool_map[tc["name"]].invoke(tc["args"])
                output = raw if isinstance(raw, str) else json.dumps(raw)
            except Exception as exc:
                output = json.dumps({"error": str(exc)})
                logger.error("[tool_node] %s failed: %s", tc["name"], exc)

            # Handle submit_final_answer → signals done
            if tc["name"] == "submit_final_answer":
                try:
                    parsed = json.loads(output)
                    if parsed.get("status") == "answer_submitted":
                        final_ans = tc["args"].get("answer", "")
                        done = True
                except Exception:
                    pass

            # Track failed searches and accumulate evidence
            elif tc["name"] == "execute_splunk_search":
                spl = tc["args"].get("spl_query", "")
                try:
                    parsed = json.loads(output)
                    if parsed.get("error"):
                        failed_queries.add(spl)
                        new_evidence.append(
                            f"[FAILED] {tc['args'].get('purpose','')}: {parsed['error'][:150]}"
                        )
                    else:
                        n = len(parsed.get("results", []))
                        purpose = tc["args"].get("purpose", "search")
                        if n == 0:
                            failed_queries.add(spl)
                            new_evidence.append(f"[EMPTY] {purpose}: 0 results")
                        else:
                            sample = str(parsed["results"][0])[:200]
                            new_evidence.append(
                                f"[Found {n} rows] {purpose}: {sample}"
                            )
                except Exception:
                    failed_queries.add(spl)

            results.append(ToolMessage(
                content=output,
                tool_call_id=tc["id"],
                name=tc["name"],
            ))

        return {
            "messages":      results,
            "evidence":      new_evidence,
            "failed_queries": list(failed_queries),
            "done":          done,
            "final_answer":  final_ans,
        }

    # ── Node: nudge ────────────────────────────────────────────────────────────
    def nudge_node(state: JudgeState) -> dict:
        """Inject a targeted reminder when model gives prose without submit_final_answer."""
        nudge_count = state.get("nudge_count", 0) + 1
        guidance    = state.get("answer_guidance", "")

        # Extract concrete values from the most recent successful ToolMessage
        found_values: list[str] = []
        for msg in reversed(state["messages"][-20:]):
            if isinstance(msg, ToolMessage):
                try:
                    parsed = json.loads(msg.content)
                    if parsed.get("results"):
                        r0 = parsed["results"][0]
                        for k, v in r0.items():
                            if not k.startswith("_") and isinstance(v, (str, int, float)):
                                found_values.append(f"{k}={v!r}")
                        break
                except Exception:
                    pass

        values_hint = (
            "Values found in last result:\n  " + "\n  ".join(found_values[:6])
            if found_values else "See search results in conversation above."
        )

        print(f"[Judge] Nudging model (nudge #{nudge_count}) | extracted: {found_values[:3]}")
        nudge_msg = HumanMessage(
            f"INSTRUCTION: call submit_final_answer RIGHT NOW.\n"
            f"{values_hint}\n"
            f"Answer format required: {guidance}\n"
            f"The 'answer' argument must be ONLY the exact value — not a sentence.\n"
            f"Example: answer='frothlywebcode' NOT answer='The bucket name is frothlywebcode'.\n"
            f"Call submit_final_answer NOW."
        )
        return {"messages": [nudge_msg], "nudge_count": nudge_count}

    # ── Routers ────────────────────────────────────────────────────────────────
    def should_continue(state: JudgeState) -> str:
        if state.get("done"):
            return END
        if state.get("search_count", 0) > MAX_ITER:
            return END
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        # Model gave prose without calling submit_final_answer.
        # Nudge up to 3 times, then give up to avoid infinite loop.
        if state.get("evidence") and not state.get("done"):
            if state.get("nudge_count", 0) < 3:
                return "nudge"
        return END

    def after_tools(state: JudgeState) -> str:
        if state.get("done"):
            return END
        return "judge"

    def after_nudge(_state: JudgeState) -> str:
        return "judge"

    # ── Assemble graph ─────────────────────────────────────────────────────────
    checkpointer = MemorySaver()
    g = StateGraph(JudgeState)
    g.add_node("judge", judge_node)
    g.add_node("tools", tool_node)
    g.add_node("nudge", nudge_node)
    g.set_entry_point("judge")
    g.add_conditional_edges("judge", should_continue, {"tools": "tools", "nudge": "nudge", END: END})
    g.add_conditional_edges("tools", after_tools, {"judge": "judge", END: END})
    g.add_conditional_edges("nudge", after_nudge, {"judge": "judge"})
    return g.compile(checkpointer=checkpointer), checkpointer


# ── Public API ─────────────────────────────────────────────────────────────────

def run_judge(
    graph,
    question: str,
    answer_guidance: str = "",
    thread_id: str = "default",
) -> tuple[str, str]:
    """
    Run the Judge Agent on one question.

    Returns (verbose_answer, extracted_answer):
    - verbose_answer: last AI message text content
    - extracted_answer: value from submit_final_answer, or verbose fallback
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_ITER * 4,
    }

    question_msg = question
    if answer_guidance:
        question_msg = f"{question}\n\nAnswer format required: {answer_guidance}"

    initial_state = {
        "messages":        [HumanMessage(content=question_msg)],
        "question":        question,
        "answer_guidance": answer_guidance,
        "evidence":        [],
        "failed_queries":  [],
        "search_count":    0,
        "nudge_count":     0,
        "final_answer":    "",
        "done":            False,
    }

    result = graph.invoke(initial_state, config=config)

    # Primary: answer from submit_final_answer
    extracted = result.get("final_answer", "")

    # Verbose: last AI message with text content
    verbose = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            verbose = msg.content
            break

    # If no tool-submitted answer, fall back to verbose
    if not extracted:
        extracted = verbose

    return verbose, extracted


# ── Standalone CLI ──────────────────────────────────────────────────────────────

def main():
    load_dotenv(os.path.join(_AGENT_DIR, ".env"))

    from splunk_client import SplunkClient

    api_key     = os.getenv("NIM_API_KEY", "")
    splunk_host = os.getenv("SPLUNK_HOST", "https://localhost:8089")
    splunk_user = os.getenv("SPLUNK_USER", "admin")
    splunk_pass = os.getenv("SPLUNK_PASS", "")

    if not api_key or not splunk_pass:
        raise SystemExit("NIM_API_KEY and SPLUNK_PASS must be set in agent/.env")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    splunk   = SplunkClient(splunk_host, splunk_user, splunk_pass)
    planner  = QueryPlannerV1(splunk)
    graph, _ = create_judge_agent(api_key, planner)

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        guidance = ""
    else:
        question = "List out the IAM users that accessed an AWS service in Frothly's AWS environment?"
        guidance = "Comma separated without spaces, in alphabetical order."

    print(f"\n{'='*70}\nJudge Agent v1 | Question: {question}\n{'='*70}\n")
    verbose, answer = run_judge(graph, question, answer_guidance=guidance, thread_id="cli_test")
    print(f"\n{'='*70}\nFINAL ANSWER: {answer!r}\n{'='*70}\n")


if __name__ == "__main__":
    main()
