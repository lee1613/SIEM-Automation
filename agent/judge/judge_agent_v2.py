#!/usr/bin/env python3
"""
Judge Agent v2 — Multi-Role Investigator with RAG, Reflection, and Auto-Diagnostic

Architecture improvements over v1:
  1. RAG context injection: domain-relevant cybersecurity knowledge retrieved at runtime
  2. Reflection/critique loop: a separate LLM pass validates the proposed answer before
     submission — catches format errors, weak evidence, false conclusions
  3. Auto-diagnostic sampling: when a filtered search returns 0 results, automatically
     samples raw events from the same sourcetype so the investigator can see the actual
     data structure (generalizable — requires no question-specific hints)
  4. propose_answer tool: candidate answer is held for reflection before final submission

Multi-agent graph topology (LangGraph):
  ┌─────────────┐
  │  classify   │ ← RAG context retrieval + domain classification
  └──────┬──────┘
         ▼
  ┌─────────────┐         ┌───────────┐
  │  investigate│◄────────│   tools   │ ← execute_splunk_search (+ auto-diagnostic)
  └──────┬──────┘         │  (tool    │   sample_sourcetype_events
         │  propose_answer │   node)   │   get_field_values
         ▼                └───────────┘
  ┌─────────────┐
  │   reflect   │ ← second LLM pass: validates answer vs. question + evidence
  └──────┬──────┘
         │  PASS → done
         │  FAIL → back to investigate with critique
         ▼
    [submit to scoreboard]

No question-specific content anywhere in this file. All investigation strategy
is derived by the model from general cybersecurity knowledge (via RAG) + the data.

Model: meta/llama-3.3-70b-instruct
Framework: LangGraph StateGraph
Version: v2
"""

import json
import logging
import os
import re
import sys
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
from rag.knowledge_base import KnowledgeBase

# ── Logging ────────────────────────────────────────────────────────────────────

logger = logging.getLogger("judge_agent_v2")

# ── Configuration ──────────────────────────────────────────────────────────────

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
JUDGE_MODEL  = "meta/llama-3.3-70b-instruct"
MAX_ITER     = 20
MAX_REFLECT  = 2     # Maximum reflection/critique passes before accepting best answer

# ── System Prompts ─────────────────────────────────────────────────────────────

INVESTIGATOR_SYSTEM = """You are a Tier 1 SOC analyst investigating a real cyberattack dataset (BOTSv3, August 2018, against Frothly Brewing Company). You have Splunk tools to search logs. Every answer must be extracted directly from query results — never inferred or guessed.

## Tools available
- execute_splunk_search: run SPL queries against index=botsv3
- sample_sourcetype_events: get raw events to understand field structure
- get_field_values: enumerate actual values a field contains
- propose_answer: submit your best answer for validation (do NOT write prose — call this tool)

## Investigation approach
1. Identify the likely data domain (cloud/AWS, Windows endpoint, network, email, identity…).
2. Before writing complex queries, sample events or enumerate field values to understand the actual schema.
3. Start with broad searches (1-2 conditions); narrow down after seeing results.
4. When a search returns 0 results with field filters: the field may not be parsed — try a keyword-only search first.
5. Extract the exact answer value with `| table field` or `| stats ... by field`.
6. Call propose_answer with the extracted value. Do NOT write the answer as prose.

## SPL rules
- All queries must start with: index=botsv3 sourcetype="<name>"
- Always project or aggregate: `| table`, `| stats`, `| top`, `| rare`
- No leading wildcards; use rex for unparsed log fields
- Temporal ordering: `| sort _time` or `| stats min(_time) as first by field`

## Answer format
- List → alphabetical, comma-separated, no spaces: a,b,c
- Number → digits only, no units
- Hostname → short form unless FQDN required
- ID/UUID/path → exact copy from data
- Filename → must include extension"""

REFLECTOR_SYSTEM = """You are a strict Quality Analyst reviewing a cybersecurity investigation result before it goes to the scoreboard.

Evaluate the proposed answer against FOUR mandatory criteria:

1. EVIDENCE: Was the answer directly extracted from Splunk query results? (NOT from prior knowledge or inference.)
   → If the evidence list is EMPTY, ALWAYS FAIL — the investigator must run actual searches.
2. FORMAT: Does it match the required answer format? (correct type, right structure)
   → Event ID → UUID format (36-char hex with dashes)
   → Filename → must have a file extension
   → Count → plain integer
   → List → comma-separated, no spaces
3. RELEVANCE: Does it answer the EXACT question? (not a related but different field)
   → "event ID" ≠ "event name"; "bucket name" ≠ "event name"
4. SPECIFICITY: Is it a concrete value (not "unknown", "not found", "N/A", "None")?

Respond with EXACTLY this structure — no other text:

VERDICT: PASS

OR:

VERDICT: FAIL
ISSUE: <one specific criterion that failed, in one sentence>
RETRY: <one concrete search action the investigator should take next>"""

# ── State ──────────────────────────────────────────────────────────────────────

class JudgeState(TypedDict):
    messages:         Annotated[list, add_messages]
    question:         str
    answer_guidance:  str
    rag_context:      str       # Retrieved knowledge (populated by classify_node)
    evidence:         list      # Findings accumulated across tool calls
    failed_queries:   list      # Dedup guard — failed/empty SPL queries
    search_count:     int
    nudge_count:      int
    proposed_answer:  str       # Candidate answer waiting for reflection
    reflection_count: int       # How many reflect passes have run
    final_answer:     str
    done:             bool


# ── Auto-diagnostic helper ─────────────────────────────────────────────────────

_FIELD_FILTER_RE = re.compile(r'\b\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)', re.IGNORECASE)
_SOURCETYPE_RE   = re.compile(r'sourcetype\s*=\s*"([^"]+)"', re.IGNORECASE)


def _has_field_filters(spl: str) -> bool:
    """Return True if the SPL has field=value conditions beyond index/sourcetype."""
    stripped = re.sub(r'\b(?:index|sourcetype)\s*=\s*\S+', '', spl, flags=re.IGNORECASE)
    return bool(_FIELD_FILTER_RE.search(stripped))


def _extract_sourcetype(spl: str) -> Optional[str]:
    m = _SOURCETYPE_RE.search(spl)
    return m.group(1) if m else None


# ── Tool factory ───────────────────────────────────────────────────────────────

def make_judge_tools(query_planner: QueryPlannerV1):
    """Return LangChain tools bound to the given QueryPlannerV1 instance."""

    @tool
    def execute_splunk_search(spl_query: str, purpose: str, max_results: int = 100) -> str:
        """Execute a Splunk SPL query. Query MUST start with index=botsv3.

        Args:
            spl_query: Full SPL string starting with index=botsv3
            purpose: One sentence — what are you trying to find?
            max_results: Max rows to return (default 100)

        When this query previously returned 0 results, you MUST change the
        approach significantly before calling again.
        """
        logger.info("[QP] search | purpose=%s | spl=%s", purpose, spl_query)
        print(f"\n[QueryPlanner] Purpose: {purpose}")
        print(f"[QueryPlanner] SPL: {spl_query}")

        result = query_planner.execute_search(spl_query, max_results=int(max_results))

        try:
            parsed = json.loads(result)
            n     = len(parsed.get("results", []))
            total = parsed.get("meta", {}).get("total_event_count", "?")
            print(f"[QueryPlanner] -> {n} results (total={total})")

            # ── Auto-diagnostic: 0 results + field filters → sample raw events ──
            if (
                total == 0
                and n == 0
                and not parsed.get("error")
                and _has_field_filters(spl_query)
                and "| rex" not in spl_query.lower()
            ):
                sourcetype = _extract_sourcetype(spl_query)
                if sourcetype:
                    print(f"[QueryPlanner] [auto-diagnostic] Sampling {sourcetype!r} to show actual field structure...")
                    sample_raw = query_planner.sample_events(sourcetype=sourcetype, count=3)
                    sample = json.loads(sample_raw)
                    if sample.get("results"):
                        parsed["auto_diagnostic"] = {
                            "hint": (
                                "Your field filters returned 0 results. "
                                "The fields you used may NOT be pre-parsed in this sourcetype. "
                                "Here are raw events — use them to understand the actual data format "
                                "and rewrite your query with rex or correct field names."
                            ),
                            "sample_events": sample["results"][:3],
                        }
                        result = json.dumps(parsed)
                        print(f"[QueryPlanner] [auto-diagnostic] Appended {len(sample['results'][:3])} raw events")
        except Exception:
            pass

        print(f"[QueryPlanner] Raw: {result[:700]}{'...' if len(result) > 700 else ''}\n")
        return result

    @tool
    def sample_sourcetype_events(sourcetype: str, keyword: str = "", count: int = 3) -> str:
        """Sample raw events from a sourcetype to understand its field structure.

        Call this BEFORE writing complex field-filter queries for any sourcetype
        you haven't sampled yet. Essential for sourcetypes that store raw text.

        Args:
            sourcetype: e.g. 'aws:s3:accesslogs', 'XmlWinEventLog:Security'
            keyword: optional keyword to narrow events (e.g., 'PUT', 'powershell')
            count: number of events (max 8)
        """
        logger.info("[QP] sample | sourcetype=%s keyword=%s", sourcetype, keyword)
        print(f"\n[QueryPlanner] Sampling: sourcetype={sourcetype!r} keyword={keyword!r}")
        result = query_planner.sample_events(sourcetype=sourcetype, keyword=keyword, count=count)
        print(f"[QueryPlanner] Sample: {result[:600]}{'...' if len(result) > 600 else ''}\n")
        return result

    @tool
    def get_field_values(field: str, sourcetype: str = "", top_n: int = 20) -> str:
        """Enumerate the top distinct values for a field within a sourcetype.

        Call this to discover what values a field contains before filtering on it.

        Args:
            field: Field name (e.g. 'eventName', 'action', 'http_method')
            sourcetype: Optional — scope to a specific sourcetype
            top_n: Max distinct values to return
        """
        logger.info("[QP] field_values | field=%s sourcetype=%s", field, sourcetype)
        print(f"\n[QueryPlanner] Field values: field={field!r} sourcetype={sourcetype!r}")
        result = query_planner.get_field_values(field=field, sourcetype=sourcetype, top_n=top_n)
        print(f"[QueryPlanner] Values: {result[:400]}{'...' if len(result) > 400 else ''}\n")
        return result

    @tool
    def propose_answer(answer: str, confidence: str, reasoning: str) -> str:
        """Propose a final answer for validation.

        This captures your best answer and sends it to a quality reviewer before
        it is submitted to the scoreboard. The reviewer may reject it and ask you
        to search further.

        Args:
            answer: The EXACT answer value. NO prose, NO units, NO explanation.
                    Match the answer_guidance format precisely.
            confidence: 'high', 'medium', or 'low'
            reasoning: Brief description of what evidence supports this answer
        """
        logger.info("[Judge] PROPOSED ANSWER | answer=%s | confidence=%s", answer, confidence)
        print(f"\n[Judge] === PROPOSED ANSWER (pending review) ===")
        print(f"[Judge] Answer: {answer!r}")
        print(f"[Judge] Confidence: {confidence}")
        print(f"[Judge] Reasoning: {reasoning}\n")
        return json.dumps({"status": "proposed", "answer": answer})

    return [execute_splunk_search, sample_sourcetype_events, get_field_values, propose_answer]


# ── Graph factory ──────────────────────────────────────────────────────────────

def create_judge_agent(api_key: str, query_planner: QueryPlannerV1, knowledge_base: KnowledgeBase):
    """Build and compile the v2 Judge Agent LangGraph. Returns (graph, checkpointer)."""
    tools    = make_judge_tools(query_planner)
    tool_map = {t.name: t for t in tools}

    llm_investigator = ChatOpenAI(
        base_url=NIM_BASE_URL,
        api_key=api_key,
        model=JUDGE_MODEL,
        max_tokens=2048,
        temperature=0,
    )
    model_with_tools = llm_investigator.bind_tools(tools, parallel_tool_calls=False)

    llm_reflector = ChatOpenAI(
        base_url=NIM_BASE_URL,
        api_key=api_key,
        model=JUDGE_MODEL,
        max_tokens=512,
        temperature=0,
    )

    print(f"[Judge v2] Model: {JUDGE_MODEL}")
    investigator_sys = SystemMessage(content=INVESTIGATOR_SYSTEM)
    reflector_sys    = SystemMessage(content=REFLECTOR_SYSTEM)

    # ── Node: classify ─────────────────────────────────────────────────────────
    def classify_node(state: JudgeState) -> dict:
        """Retrieve domain-relevant knowledge from the RAG and inject into state."""
        question = state["question"]
        context  = knowledge_base.retrieve(question, top_k=3)
        if context:
            print(f"[Judge v2] RAG context retrieved ({len(context)} chars)")
        return {"rag_context": context}

    # ── Node: investigate ──────────────────────────────────────────────────────
    def investigate_node(state: JudgeState) -> dict:
        """Main investigation: reason about the question, call tools, accumulate evidence."""
        step = state.get("search_count", 0) + 1

        # Build message list: system + optional RAG context + conversation
        msgs = [investigator_sys]

        rag = state.get("rag_context", "")
        if rag:
            msgs.append(SystemMessage(
                content=f"## Relevant investigation knowledge\n{rag}"
            ))

        msgs += list(state["messages"])

        if step > MAX_ITER:
            print(f"\n[Judge v2] Max iterations ({MAX_ITER}) — forcing proposal")
            evidence_txt = "\n".join(f"- {e}" for e in state.get("evidence", [])[-5:]) or "None"
            guidance     = state.get("answer_guidance", "")
            msgs.append(HumanMessage(
                f"FINAL: Based on all evidence so far, call propose_answer now.\n"
                f"Evidence:\n{evidence_txt}\nFormat required: {guidance}"
            ))

        response = model_with_tools.invoke(msgs)

        if response.content and not getattr(response, "tool_calls", None):
            print(f"\n[Judge response]\n{response.content}\n")
        elif response.content:
            print(f"\n[Judge thinking]\n{response.content}\n")
        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                print(f"[Judge] -> {tc['name']}({json.dumps(tc['args'])[:300]})")

        return {"messages": [response], "search_count": step}

    # ── Node: tools ────────────────────────────────────────────────────────────
    def tool_node(state: JudgeState) -> dict:
        """Execute tool calls; accumulate evidence; track failed queries; detect proposals."""
        last           = state["messages"][-1]
        results        = []
        new_evidence   = list(state.get("evidence", []))
        failed_queries = set(state.get("failed_queries", []))
        proposed       = state.get("proposed_answer", "")
        done           = state.get("done", False)

        for tc in last.tool_calls:
            logger.info("[tool_node] %s", tc["name"])

            # ── Dedup guard ────────────────────────────────────────────────────
            if tc["name"] == "execute_splunk_search":
                spl = tc["args"].get("spl_query", "")
                if spl in failed_queries:
                    warn = (
                        f"Rejected: this exact query already returned 0 results or an error. "
                        f"Try a different sourcetype, different field names, or sample first.\n"
                        f"Rejected: {spl}"
                    )
                    print(f"[Judge] [DEDUP REJECT] {spl[:80]}")
                    results.append(ToolMessage(
                        content=json.dumps({"error": warn}),
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    ))
                    continue

            # ── Execute ────────────────────────────────────────────────────────
            try:
                raw    = tool_map[tc["name"]].invoke(tc["args"])
                output = raw if isinstance(raw, str) else json.dumps(raw)
            except Exception as exc:
                output = json.dumps({"error": str(exc)})
                logger.error("[tool_node] %s failed: %s", tc["name"], exc)

            # ── Handle propose_answer ──────────────────────────────────────────
            if tc["name"] == "propose_answer":
                try:
                    parsed = json.loads(output)
                    if parsed.get("status") == "proposed":
                        proposed = tc["args"].get("answer", "")
                except Exception:
                    pass

            # ── Track search outcomes ──────────────────────────────────────────
            elif tc["name"] == "execute_splunk_search":
                spl = tc["args"].get("spl_query", "")
                try:
                    parsed = json.loads(output)
                    if parsed.get("error") and "auto_diagnostic" not in parsed:
                        failed_queries.add(spl)
                        new_evidence.append(
                            f"[FAILED] {tc['args'].get('purpose','')}: {str(parsed['error'])[:150]}"
                        )
                    else:
                        n = len(parsed.get("results", []))
                        purpose = tc["args"].get("purpose", "search")
                        if n == 0 and "auto_diagnostic" not in parsed:
                            failed_queries.add(spl)
                            new_evidence.append(f"[EMPTY] {purpose}: 0 results")
                        elif n > 0:
                            sample = str(parsed["results"][0])[:200]
                            new_evidence.append(f"[Found {n} rows] {purpose}: {sample}")
                except Exception:
                    failed_queries.add(spl)

            results.append(ToolMessage(
                content=output,
                tool_call_id=tc["id"],
                name=tc["name"],
            ))

        return {
            "messages":       results,
            "evidence":       new_evidence,
            "failed_queries": list(failed_queries),
            "proposed_answer": proposed,
            "done":           done,
        }

    # ── Node: reflect ──────────────────────────────────────────────────────────
    def reflect_node(state: JudgeState) -> dict:
        """Second LLM pass: validate the proposed answer before final submission."""
        reflection_count = state.get("reflection_count", 0) + 1
        proposed         = state.get("proposed_answer", "")
        question         = state.get("question", "")
        guidance         = state.get("answer_guidance", "")
        evidence         = state.get("evidence", [])

        evidence_txt = "\n".join(f"- {e}" for e in evidence[-6:]) or "No evidence collected."

        print(f"\n[Judge v2] Reflecting on proposed answer: {proposed!r} (pass #{reflection_count})")

        # If we've already reflected MAX_REFLECT times, accept the answer
        if reflection_count > MAX_REFLECT:
            print(f"[Judge v2] Max reflections reached — accepting: {proposed!r}")
            return {
                "final_answer":     proposed,
                "done":             True,
                "reflection_count": reflection_count,
            }

        reflect_prompt = (
            f"QUESTION: {question}\n"
            f"REQUIRED FORMAT: {guidance}\n"
            f"PROPOSED ANSWER: {proposed}\n\n"
            f"EVIDENCE COLLECTED:\n{evidence_txt}"
        )

        response = llm_reflector.invoke([
            reflector_sys,
            HumanMessage(content=reflect_prompt),
        ])
        verdict_text = response.content.strip()
        print(f"[Reflector]\n{verdict_text}\n")

        if "VERDICT: PASS" in verdict_text:
            print(f"[Judge v2] Reflection PASSED — submitting: {proposed!r}")
            return {
                "final_answer":     proposed,
                "done":             True,
                "reflection_count": reflection_count,
            }

        # Reflection failed — extract critique and push back to investigation
        critique_match = re.search(r"ISSUE:\s*(.+?)(?:\n|$)", verdict_text)
        retry_match    = re.search(r"RETRY:\s*(.+?)(?:\n|$)", verdict_text)
        critique = critique_match.group(1).strip() if critique_match else verdict_text
        retry    = retry_match.group(1).strip() if retry_match else "Try a different search approach."

        # Surface the most recent concrete search result so the investigator can
        # reformat/refilter from data it already has, instead of re-searching blindly.
        data_snapshot = ""
        for msg in reversed(state["messages"][-20:]):
            if isinstance(msg, ToolMessage):
                try:
                    parsed = json.loads(msg.content)
                    rows   = parsed.get("results") or (parsed.get("auto_diagnostic", {}) or {}).get("sample_events")
                    if rows:
                        data_snapshot = json.dumps(rows[:5])[:700]
                        break
                except Exception:
                    pass

        print(f"[Judge v2] Reflection FAILED — critique: {critique}")
        feedback_msg = HumanMessage(
            f"Your proposed answer {proposed!r} was REJECTED by the quality reviewer.\n"
            f"Issue: {critique}\n"
            f"Suggested next step: {retry}\n\n"
            f"Most recent search data you already have:\n{data_snapshot or '(none — run a new search)'}\n\n"
            f"If the correct value is already in this data, reformat/refilter it and call "
            f"propose_answer again. If not, run ONE new, different search first. "
            f"Do not repeat a search that already failed."
        )
        return {
            "messages":         [feedback_msg],
            "proposed_answer":  "",
            "reflection_count": reflection_count,
        }

    # ── Node: nudge ────────────────────────────────────────────────────────────
    def nudge_node(state: JudgeState) -> dict:
        """Force propose_answer when model gives prose without calling the tool."""
        nudge_count = state.get("nudge_count", 0) + 1
        guidance    = state.get("answer_guidance", "")

        # Pull concrete values from the last successful tool result
        found_values: list = []
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
            "Last search result fields: " + ", ".join(found_values[:5])
            if found_values else "Check the search results above."
        )

        print(f"[Judge v2] Nudging (#{nudge_count}) | extracted: {found_values[:3]}")
        return {
            "messages": [HumanMessage(
                f"You must call propose_answer NOW — do NOT write prose.\n"
                f"{values_hint}\n"
                f"Required format: {guidance}\n"
                f"Call propose_answer(answer='<exact_value>', ...) immediately."
            )],
            "nudge_count": nudge_count,
        }

    # ── Routers ────────────────────────────────────────────────────────────────

    def after_classify(_: JudgeState) -> str:
        return "investigate"

    def should_continue(state: JudgeState) -> str:
        if state.get("done"):
            return END
        if state.get("search_count", 0) > MAX_ITER:
            return END
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        # Prose response → nudge (up to 3 times)
        if state.get("evidence") and not state.get("done"):
            if state.get("nudge_count", 0) < 3:
                return "nudge"
        return END

    def after_tools(state: JudgeState) -> str:
        if state.get("done"):
            return END
        # A propose_answer was captured — route to reflector
        if state.get("proposed_answer"):
            return "reflect"
        return "investigate"

    def after_reflect(state: JudgeState) -> str:
        if state.get("done"):
            return END
        return "investigate"

    def after_nudge(_: JudgeState) -> str:
        return "investigate"

    # ── Assemble ───────────────────────────────────────────────────────────────
    checkpointer = MemorySaver()
    g = StateGraph(JudgeState)

    g.add_node("classify",    classify_node)
    g.add_node("investigate", investigate_node)
    g.add_node("tools",       tool_node)
    g.add_node("reflect",     reflect_node)
    g.add_node("nudge",       nudge_node)

    g.set_entry_point("classify")
    g.add_conditional_edges("classify",    after_classify,  {"investigate": "investigate"})
    g.add_conditional_edges("investigate", should_continue, {"tools": "tools", "nudge": "nudge", END: END})
    g.add_conditional_edges("tools",       after_tools,     {"investigate": "investigate", "reflect": "reflect", END: END})
    g.add_conditional_edges("reflect",     after_reflect,   {"investigate": "investigate", END: END})
    g.add_conditional_edges("nudge",       after_nudge,     {"investigate": "investigate"})

    return g.compile(checkpointer=checkpointer), checkpointer


# ── Public API ─────────────────────────────────────────────────────────────────

def run_judge(
    graph,
    question: str,
    answer_guidance: str = "",
    thread_id: str = "default",
) -> tuple:
    """
    Run the v2 Judge Agent on one question.

    Returns (verbose_answer, extracted_answer).
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_ITER * 6,
    }

    question_msg = question
    if answer_guidance:
        question_msg = f"{question}\n\nAnswer format required: {answer_guidance}"

    initial_state = {
        "messages":         [HumanMessage(content=question_msg)],
        "question":         question,
        "answer_guidance":  answer_guidance,
        "rag_context":      "",
        "evidence":         [],
        "failed_queries":   [],
        "search_count":     0,
        "nudge_count":      0,
        "proposed_answer":  "",
        "reflection_count": 0,
        "final_answer":     "",
        "done":             False,
    }

    result = graph.invoke(initial_state, config=config)

    extracted = result.get("final_answer", "")

    verbose = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            verbose = msg.content
            break

    if not extracted:
        extracted = verbose

    return verbose, extracted


# ── Standalone CLI ──────────────────────────────────────────────────────────────

def main():
    load_dotenv(os.path.join(_AGENT_DIR, ".env"))

    from splunk_client import SplunkClient
    from rag.knowledge_base import build_siem_knowledge_base

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
    kb       = build_siem_knowledge_base(_AGENT_DIR)
    graph, _ = create_judge_agent(api_key, planner, kb)

    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "List out the IAM users that accessed an AWS service in Frothly's AWS environment?"
    )
    guidance = "Comma separated without spaces, in alphabetical order." if len(sys.argv) <= 1 else ""

    print(f"\n{'='*70}\nJudge Agent v2 | {question}\n{'='*70}\n")
    verbose, answer = run_judge(graph, question, answer_guidance=guidance, thread_id="cli_test")
    print(f"\n{'='*70}\nFINAL ANSWER: {answer!r}\n{'='*70}\n")


if __name__ == "__main__":
    main()
