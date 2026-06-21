#!/usr/bin/env python3
"""
SIEM Automation Agent — LangGraph stateful agent with two-stage tool dispatch.

Flow per tool call:
    agent ──► verify_node ──(approved)──► execute_node ──► agent
                           └─(rejected)──► agent  (self-correction)

verify_node runs before any tool executes and rejects calls that:
  - duplicate a prior failed call this turn (dedup guard)
  - reference a sourcetype not in the manifest
  - run_splunk_search without aggregation (| stats / | top / | rare)
  - run_splunk_search with a leading wildcard (=*value forces full scan)

execute_node only runs approved calls and records execution errors in seen_errors.

Model:  meta/llama-3.3-70b-instruct via NVIDIA NIM
Brain:  LangGraph StateGraph + MemorySaver (cross-question statefulness)
Data:   Splunk Enterprise REST API (port 8089)
"""

import os
import re
import sys
import json
import textwrap
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from splunk_client import SplunkClient

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────

NIM_API_KEY   = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST   = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER   = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS   = os.getenv("SPLUNK_PASS", "")
NIM_BASE_URL  = "https://integrate.api.nvidia.com/v1"
MODEL         = "meta/llama-3.3-70b-instruct"
MAX_ITER      = 15
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "botsv3_fields.json")

# ── Field manifest helpers ─────────────────────────────────────────────────────

def _load_manifest() -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_manifest(manifest: dict) -> None:
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def _manifest_get_source_types() -> str:
    manifest = _load_manifest()
    source_types = list(manifest.get("source_types", {}).keys())
    return json.dumps({"source_types": source_types, "count": len(source_types)})

def _manifest_search(pattern: str) -> str:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return json.dumps({"error": f"Invalid regex pattern: {e}"})
    manifest = _load_manifest()
    matches = []
    for st_name, entry in manifest.get("source_types", {}).items():
        for field in entry.get("fields", []):
            if regex.search(field):
                matches.append({"sourcetype": st_name, "type": "field", "value": field})
        if regex.search(st_name):
            matches.append({"sourcetype": st_name, "type": "sourcetype", "value": st_name})
    return json.dumps({"matches": matches, "count": len(matches)})

def _manifest_expand(sourcetype: str, fields: list) -> str:
    manifest = _load_manifest()
    source_types = manifest.setdefault("source_types", {})
    entry = source_types.setdefault(sourcetype, {"fields": []})
    existing_fields = set(entry.get("fields", []))
    new_fields = [f for f in fields if f not in existing_fields]
    entry["fields"].extend(new_fields)
    _save_manifest(manifest)
    return json.dumps({"sourcetype": sourcetype, "fields_added": new_fields})

def _known_sourcetypes() -> set:
    return set(json.loads(_manifest_get_source_types())["source_types"])

# ── Result formatter ───────────────────────────────────────────────────────────

_STRIP = frozenset({
    "_bkt", "_cd", "_indextime", "_kv", "_si", "_sourcetype",
    "_serial", "_subsecond", "punct", "linecount", "splunk_server",
    "splunk_server_group", "timestartpos", "timeendpos",
})

def _format_result(result: dict, keep_raw: bool = False) -> str:
    strip_set = _STRIP if keep_raw else (_STRIP | {"_raw"})
    if "results" in result:
        cleaned = [
            {k: v for k, v in row.items() if k not in strip_set}
            for row in result["results"]
        ]
        payload = json.dumps({"results": cleaned, "meta": result.get("_meta", {})})
        if len(payload) > 12_000:
            payload = payload[:12_000] + '... [truncated — use a more specific query]"}'
        return payload
    return json.dumps(result)

# ── Graph state ────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages:             Annotated[list, add_messages]  # grows across questions
    seen_errors:          list   # [[name, args_str], ...] calls that errored — reset per question
    seen_empty:           list   # [[name, args_str], ...] calls that returned 0 results — reset per question
    step_count:           int    # agent-node calls — reset per question
    verification_passed:  bool   # set by verify_node, read by after_verify router

# ── Tool factory ───────────────────────────────────────────────────────────────

def make_tools(splunk: SplunkClient) -> list:
    """Return LangChain tool objects that close over the given Splunk client."""

    @tool
    def get_source_types() -> str:
        """Return the full list of all known sourcetypes from the local manifest.
        Call this FIRST — it is the entry point for all investigations.
        No Splunk call, instant response."""
        return _manifest_get_source_types()

    @tool
    def search_field_manifest(pattern: str) -> str:
        """Search the BOTSv3 field registry by keyword or Python regex.
        Call this to check whether a field already exists in the local manifest before querying Splunk."""
        return _manifest_search(pattern)

    @tool
    def get_sourcetype_fields(sourcetype: str, index: str = "botsv3",
                               min_count: int = 1) -> str:
        """Run Splunk fieldsummary on a sourcetype: every field with coverage %,
        distinct value count, and sample values. Use when search_field_manifest
        returns no match. Follow up with expand_field_manifest."""
        result = splunk.get_sourcetype_fields(
            sourcetype=sourcetype, index=index, min_count=min_count
        )
        return _format_result(result)

    @tool
    def get_field_values(field: str, index: str = "botsv3",
                         sourcetype: str = "", top_n: int = 20) -> str:
        """Get the top distinct values for a field, optionally scoped to a sourcetype.
        Use to enumerate the range of values a field contains before filtering on it."""
        result = splunk.get_field_values(
            field=field, index=index, top_n=int(top_n), sourcetype=sourcetype
        )
        return _format_result(result)

    @tool
    def sample_events(sourcetype: str, index: str = "botsv3",
                      keyword: str = "", count: int = 3) -> str:
        """Return raw event content from a sourcetype to discover embedded field names and log structure.
        `sourcetype` MUST be a value returned by get_source_types.
        `keyword` is an optional free-text filter within that sourcetype — it narrows which events are
        returned but does NOT select the sourcetype. Omit or leave blank to sample any events."""
        result = splunk.sample_events(
            sourcetype=sourcetype, index=index, keyword=keyword, count=min(count, 5)
        )
        return _format_result(result, keep_raw=True)

    @tool
    def expand_field_manifest(sourcetype: str, fields: list) -> str:
        """Persist newly discovered fields into the local registry for a sourcetype.
        Call this whenever get_sourcetype_fields or sample_events reveals field names
        that were not already returned by search_field_manifest — so they are available
        to future searches without re-querying Splunk."""
        return _manifest_expand(sourcetype, fields)

    @tool
    def run_splunk_search(query: str, max_results: int = 50) -> str:
        """Execute an SPL search against Splunk.
        Only call this when you are certain the sourcetype exists — verified via get_source_types.
        Always include a sourcetype filter. Must aggregate with | stats, | top, or | rare.
        No leading wildcards. Max 50 results."""
        result = splunk.search(
            query=query, earliest="0", latest="now", max_results=int(max_results)
        )
        return _format_result(result)

    return [
        get_source_types,
        search_field_manifest,
        get_sourcetype_fields,
        get_field_values,
        sample_events,
        expand_field_manifest,
        run_splunk_search,
    ]

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a SIEM analyst agent on the BOTSv3 dataset (August 2018 APT attack against Frothly). You are running inside Splunk Enterprise.

MANDATORY: Every SPL query MUST begin with `index=botsv3`. All BOTSv3 data lives in this index.

Always aggregate SPL results with | stats, | top, or | rare. Use dot-notation for nested fields and {} for multi-value arrays. Never return raw event streams. Max 50 results per query.

SPL rules:
- Use IN for multiple literal values
- Filter after aggregation with | search
- Boolean precedence in base search: NOT -> OR -> AND
- Never use leading wildcards (=*value) — always trailing wildcards (value*)
- Match exact tokens over substring wildcards

run_splunk_search rules — only invoke when you are certain the sourcetype exists.
To be certain: call get_source_types first to confirm the sourcetype is present, then run the search.
Never run a search without a sourcetype filter.

Use sample_events to inspect the raw structure of events inside a sourcetype before searching. This reveals actual field names, value formats, and keywords that can lead you to the answer. Call this whenever you are unsure what a sourcetype contains or what fields to search on.

"""
# ── Verification helpers ───────────────────────────────────────────────────────

def _verify_call(tc: dict, seen_errors: set, seen_empty: set) -> str | None:
    """Return a rejection reason string, or None if the call is approved."""
    name     = tc["name"]
    args     = tc["args"]
    args_str = json.dumps(args, sort_keys=True, separators=(",", ":"))
    call_key = (name, args_str)

    # 1. Dedup guard — identical call already errored this turn
    if call_key in seen_errors:
        return (
            "Rejected: this exact tool call already failed with an error this turn. "
            "Try different arguments or a different approach."
        )

    # 2. Empty-result guard — identical call already returned 0 results this turn
    if call_key in seen_empty:
        return (
            "Rejected: this exact tool call already returned zero results this turn. "
            "Change the sourcetype, field name, filter value, or search strategy."
        )

    # Remaining checks only apply to run_splunk_search
    if name != "run_splunk_search":
        return None

    query = args.get("query", "")

    # 3. Must start with index=botsv3
    if not re.match(r'\s*index\s*=\s*botsv3\b', query, re.IGNORECASE):
        return (
            "Rejected: every SPL query must begin with 'index=botsv3'. "
            "All BOTSv3 data lives in that index. "
            "Prepend 'index=botsv3' to the query."
        )

    # 4. Must have aggregation
    if not re.search(r'\|\s*(stats|top|rare)\b', query, re.IGNORECASE):
        return (
            "Rejected: SPL query must aggregate results with | stats, | top, or | rare. "
            "Add an aggregation command before submitting."
        )

    # 5. Sourcetype must be present and in the manifest
    st_match = re.search(r'sourcetype\s*=\s*"?([^\s",|)]+)', query, re.IGNORECASE)
    if not st_match:
        return (
            "Rejected: every run_splunk_search query must include a sourcetype filter. "
            "Call get_source_types to find the right sourcetype, then add sourcetype=<value> to the query."
        )
    st = st_match.group(1).strip('"\'')
    known = _known_sourcetypes()
    if st not in known:
        return (
            f"Rejected: sourcetype '{st}' is not in the field manifest. "
            f"Call get_source_types to see valid sourcetypes, then adjust the query."
        )

    # 6. No leading wildcards (=*word forces sequential scan)
    if re.search(r'=\s*\*[^\s*|,)"\']', query):
        return (
            "Rejected: leading wildcard detected (=*value). "
            "Leading wildcards force a full sequential scan. "
            "Use a trailing wildcard (value*) or an exact value instead."
        )

    return None

# ── Graph factory ──────────────────────────────────────────────────────────────

def create_agent(api_key: str, splunk: SplunkClient):
    """Build and compile the LangGraph agent. Returns (graph, checkpointer).

    Graph topology:
        agent ──► verify_node ──(approved)──► execute_node ──► agent
                              └─(rejected)──► agent
    """
    tools    = make_tools(splunk)
    tool_map = {t.name: t for t in tools}

    llm = ChatOpenAI(
        base_url=NIM_BASE_URL,
        api_key=api_key,
        model=MODEL,
        max_tokens=4096,
        temperature=0,
    )
    model_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    model_bare       = llm  # no tools — used when iteration cap is hit

    system_msg = SystemMessage(content=SYSTEM_PROMPT)

    # ── Node: agent ────────────────────────────────────────────────────────────
    def agent_node(state: AgentState) -> dict:
        step = state.get("step_count", 0) + 1
        msgs = [system_msg] + list(state["messages"])

        if step > MAX_ITER:
            print("[Max iterations reached — forcing final answer]")
            msgs = msgs + [HumanMessage(
                "You have used the maximum number of tool calls. "
                "Give your best final answer now based on everything found so far."
            )]
            response = model_bare.invoke(msgs)
        else:
            response = model_with_tools.invoke(msgs)

        if response.content:
            label = "[Agent thinking]" if getattr(response, "tool_calls", None) else "[Agent response]"
            print(f"\n{label}\n{response.content}\n")

        return {"messages": [response], "step_count": step}

    # ── Node: verify ───────────────────────────────────────────────────────────
    def verify_node(state: AgentState) -> dict:
        """Pre-flight check: inspect proposed tool calls before execution.

        Approves  → sets verification_passed=True, adds nothing to messages.
        Rejects   → sets verification_passed=False, injects ToolMessage(error)
                    for every rejected call so the agent can self-correct.
        """
        seen_errors = {(e[0], e[1]) for e in state.get("seen_errors", [])}
        seen_empty  = {(e[0], e[1]) for e in state.get("seen_empty",  [])}
        last        = state["messages"][-1]
        rejections  = []

        for tc in last.tool_calls:
            reason = _verify_call(tc, seen_errors, seen_empty)
            if reason:
                print(f"[Verify REJECT] {tc['name']} — {reason}")
                rejections.append(ToolMessage(
                    content=json.dumps({"error": reason}),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
            else:
                print(f"[Verify OK]     {tc['name']}")

        if rejections:
            return {"messages": rejections, "verification_passed": False}
        return {"verification_passed": True}

    # ── Node: execute ──────────────────────────────────────────────────────────
    def execute_node(state: AgentState) -> dict:
        """Run verified tool calls; record execution errors and empty results."""
        seen_errors = {(e[0], e[1]) for e in state.get("seen_errors", [])}
        seen_empty  = {(e[0], e[1]) for e in state.get("seen_empty",  [])}
        new_errors  = [list(e) for e in seen_errors]
        new_empty   = [list(e) for e in seen_empty]
        last        = state["messages"][-1]
        results     = []

        for tc in last.tool_calls:
            args_str = json.dumps(tc["args"], sort_keys=True, separators=(",", ":"))
            call_key  = (tc["name"], args_str)

            try:
                raw    = tool_map[tc["name"]].invoke(tc["args"])
                output = raw if isinstance(raw, str) else json.dumps(raw)
            except Exception as exc:
                output = json.dumps({"error": str(exc)})

            try:
                parsed = json.loads(output)
                if "error" in parsed:
                    new_errors.append(list(call_key))
                elif (parsed.get("results") is not None
                      and len(parsed["results"]) == 0):
                    new_empty.append(list(call_key))
            except Exception:
                pass

            print(f"[Execute] {tc['name']}({args_str})")
            print(f"          -> {output}\n")

            results.append(ToolMessage(
                content=output,
                tool_call_id=tc["id"],
                name=tc["name"],
            ))

        return {"messages": results, "seen_errors": new_errors, "seen_empty": new_empty}

    # ── Routers ────────────────────────────────────────────────────────────────
    def should_continue(state: AgentState) -> str:
        """Route agent output: to verify if tool calls present, else END."""
        if state.get("step_count", 0) > MAX_ITER:
            return END
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "verify"
        return END

    def after_verify(state: AgentState) -> str:
        """Route verify output: to execute if approved, back to agent if rejected."""
        return "execute" if state.get("verification_passed") else "agent"

    # ── Assemble graph ─────────────────────────────────────────────────────────
    checkpointer = MemorySaver()

    g = StateGraph(AgentState)
    g.add_node("agent",   agent_node)
    g.add_node("verify",  verify_node)
    g.add_node("execute", execute_node)

    g.set_entry_point("agent")
    g.add_conditional_edges("agent",  should_continue,
                            {"verify": "verify", END: END})
    g.add_conditional_edges("verify", after_verify,
                            {"execute": "execute", "agent": "agent"})
    g.add_edge("execute", "agent")

    return g.compile(checkpointer=checkpointer), checkpointer


# ── Public run API ─────────────────────────────────────────────────────────────

def run_agent(graph, question: str, thread_id: str = "default") -> str:
    """Invoke the agent on one question and return the final answer string.

    Same thread_id across questions → model sees full prior Q&A history.
    Fresh thread_id → clean conversation.
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_ITER * 4,
    }
    result = graph.invoke(
        {
            "messages":            [HumanMessage(content=question)],
            "seen_errors":         [],
            "seen_empty":          [],
            "step_count":          0,
            "verification_passed": False,
        },
        config=config,
    )
    last = result["messages"][-1]
    return getattr(last, "content", "") or ""


# ── CLI entry point ────────────────────────────────────────────────────────────

def _connect_splunk() -> SplunkClient:
    if not SPLUNK_PASS:
        raise SystemExit("SPLUNK_PASS not set — copy .env.example to .env.")
    print(f"Connecting to Splunk at {SPLUNK_HOST} as '{SPLUNK_USER}'...")
    c = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")
    return c


def main():
    if not NIM_API_KEY:
        raise SystemExit("NIM_API_KEY not set.")

    splunk    = _connect_splunk()
    graph, _  = create_agent(NIM_API_KEY, splunk)
    thread_id = "interactive"

    if len(sys.argv) > 1:
        query  = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        answer = run_agent(graph, query, thread_id=thread_id)
        print("\n" + "=" * 60)
        print(answer)
        return

    print(f"SIEM Agent ready  [model: {MODEL}  |  LangGraph + verify gate]")
    print("Type your question or 'exit' to quit. Context persists across turns.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break
        answer = run_agent(graph, query, thread_id=thread_id)
        print("\nAgent:", textwrap.fill(answer, width=100, subsequent_indent="       "))
        print()


if __name__ == "__main__":
    main()
