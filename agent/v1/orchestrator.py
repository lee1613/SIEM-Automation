#!/usr/bin/env python3
"""
SH (orchestrator / mastermind) agent for v1.

A stateful GPT-5.4 planner that NEVER touches Splunk directly. Its only tool is
`spawn_senior(subquestion)`, which recruits a fresh Senior Splunk worker (the v0 graph).
The SH plans, delegates atomic sub-questions one at a time, reads each worker's structured
findings, replans, and finally writes a plain-text answer (no tool call) — at which point
the graph terminates the standard ReAct way and the answer flows to the Extractor.

The SH keeps ONE persistent MemorySaver thread for the whole 58-question run, so the
mastermind accumulates cross-question context (entities, hosts, timeframes) exactly like
v0 did.
"""

import json
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


SH_MAX_ROUNDS = 12   # max agent turns per question (decomposition + replans)


SH_SYSTEM_PROMPT = """You are the SH agent — the mastermind orchestrator for a BOTSv3 \
security investigation (August 2018 APT attack against Frothly, all data in Splunk index=botsv3).

YOUR ROLE
- You PLAN and DELEGATE. You do NOT query Splunk yourself and you have no Splunk tools.
- For each question you decide what information is needed, break it into sub-questions when
  necessary, and delegate each to a Splunk worker. You then assemble the final answer.

YOUR TEAM (you must choose who is responsible and say so out loud)
- Senior Splunk Agent — call via spawn_senior(subquestion). A Splunk EXPERT with multi-step
  reasoning and 6 Splunk tools (sourcetype discovery, keyword/field search, event sampling,
  SPL search). Use it for anything requiring investigation or a multi-step pivot.
- (A Junior Splunk Agent for trivial single-hop lookups will join in a later version. For
  now, route all data lookups to the Senior.)

PLAN-AND-ACT CYCLE (mandatory before your FIRST delegation on each question)
Before calling spawn_senior for the first time, write a PLAN block:

  PLAN:
  - Goal: [what the question is asking for; what type of value is expected]
  - Prior knowledge: [entities from your memory relevant to THIS question — hosts, IPs,
    usernames, bucket names, time windows, sourcetypes that proved useful in earlier Qs]
  - Enrichment: [what known context you will embed directly in the subquestion]
  - Suggested approach: [which sourcetypes or investigation path to try first]

Only after writing the PLAN call spawn_senior, with the relevant context from "Prior
knowledge" woven inline into the subquestion text.

DELEGATION RULES
1. Decomposition is OPTIONAL. If a question is a single atomic lookup, delegate it whole in
   ONE spawn_senior call. Only decompose genuinely multi-hop questions.
2. Workers have NO shared memory — each spawn_senior call is a fresh session. Make every
   subquestion fully self-contained: restate all known entities, hosts, time ranges, and
   sourcetype hints. Never say "the host from before" — name it explicitly every time.
3. Delegate ONE sub-question at a time and use its result to shape the next.
4. Before EVERY delegation, state explicitly who is responsible and why, e.g.:
   "Responsibility: Senior Splunk Agent — this needs a cloudtrail->s3 pivot (multi-step)."
5. If a worker returns status 'too_big' or 'failed', that means YOU scoped it poorly. Narrow
   the sub-question (smaller, more specific, with concrete hints) and delegate again.

HANDLING WORKER RESPONSES
- status='solved': Worker found a confident answer. Use it directly or as evidence for a
  follow-up sub-question.
- status='partial': Worker found useful evidence but is NOT certain. The response includes
  PARTIAL ANSWER (the best candidate), UNCERTAINTY (why it's unsure), NEXT STEP (what
  would confirm it). You should: (a) re-delegate with a targeted verification subquestion
  incorporating the candidate, or (b) accept it if the partial finding is specific and
  your cross-question memory corroborates it. Do NOT treat 'partial' as a failure.
- status='too_big' or 'failed': Worker could not proceed. Narrow the sub-question and
  retry with a more specific scope and explicit hints.

CROSS-QUESTION MEMORY
- You remember everything from earlier questions in this run. Carry forward key entities
  (hosts, IPs, users, bucket names, time windows) and restate them inside every subquestion.
- Do NOT assume a worker knows any context from a prior question — always state it explicitly.

ANSWERING
- Anything that depends on the dataset MUST be delegated — never invent dataset facts.
- Pure general knowledge (e.g. "what company makes Splunk") you may answer directly.
- When you have enough information, STOP calling tools and write your final answer as plain
  text. End with a line exactly:  FINAL ANSWER: <the precise value>
- Keep the final value in the exact format the question asks for (an extractor will read the
  FINAL ANSWER line)."""


class SHState(TypedDict):
    messages:   Annotated[list, add_messages]   # persists across the whole run
    step_count: int                             # reset to 0 per question


class DelegationContext:
    """Mutable per-run context the spawn_senior tool reads at call time.

    Built once and shared with the (persistent) SH graph; `current_qid` is updated before
    each question so the single graph can serve all 58 while logging to the right place.
    """

    def __init__(self, pool, logger):
        self.pool   = pool
        self.logger = logger
        self.current_qid       = None
        self.failed_delegations = 0     # cumulative (req c): worker couldn't resolve
        self.q_delegations      = []    # delegations for the current question
        self.all_delegations    = []    # everything, for the run JSON

    def reset_question(self, qid: str) -> None:
        self.current_qid = qid
        self.q_delegations = []


def make_sh_tools(ctx: DelegationContext) -> list:
    @tool
    def spawn_senior(subquestion: str) -> str:
        """Delegate ONE atomic, self-contained sub-question to a FRESH Senior Splunk worker.
        The worker is a Splunk expert (multi-step reasoning + 6 Splunk tools) with NO memory
        of any other sub-question — so restate all known entities, time ranges, and sourcetype
        hints inside `subquestion`. Returns the worker's findings: answer, the SPL it ran, the
        sourcetypes it used, and status (solved | partial | too_big | failed).
        - solved: confident answer found — use it directly.
        - partial: useful evidence but uncertain — verify or accept with corroboration.
        - too_big / failed: re-scope with a narrower, more specific subquestion."""
        qid = ctx.current_qid
        idx = ctx.logger.next_worker("senior", qid)
        print(f"\n[SH -> SENIOR #{idx}]  {subquestion}")

        result = ctx.pool.run_senior(subquestion, qid, idx)

        if result["status"] in ("too_big", "failed"):
            ctx.failed_delegations += 1

        record = {
            "worker":      f"senior#{idx}",
            "qid":         qid,
            "subquestion": subquestion,
            "status":      result["status"],
            "answer":      result["answer"],
            "spl_used":    result["spl_used"],
            "sourcetypes": result["sourcetypes"],
            "full_state":  result["full_state"],
        }
        ctx.q_delegations.append(record)
        ctx.all_delegations.append(record)

        ctx.logger.timeline(
            f"- **Senior #{idx}**  _[{result['status']}]_  "
            f"(LangSmith: `Senior-{idx}-{qid}`)\n"
            f"    - task: {subquestion}\n"
            f"    - answer: {(result['answer'] or '').strip()[:400]}\n"
            f"    - SPL: {result['spl_used']}"
        )

        return json.dumps({
            "worker":      f"senior#{idx}",
            "status":      result["status"],
            "answer":      result["answer"],
            "spl_used":    result["spl_used"],
            "sourcetypes": result["sourcetypes"],
        }, ensure_ascii=False)

    return [spawn_senior]


def build_sh_agent(api_key: str, model: str, tools: list):
    """Compile the SH graph. Returns (graph, checkpointer)."""
    llm = ChatOpenAI(api_key=api_key, model=model,
                     max_completion_tokens=4096, temperature=0)
    model_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    tool_map = {t.name: t for t in tools}
    sys_msg  = SystemMessage(content=SH_SYSTEM_PROMPT)

    def agent_node(state: SHState) -> dict:
        step = state.get("step_count", 0) + 1
        msgs = [sys_msg] + list(state["messages"])
        if step > SH_MAX_ROUNDS:
            print("[SH max rounds reached — forcing final answer]")
            msgs = msgs + [HumanMessage(
                "You have reached the maximum delegation rounds. Using everything gathered "
                "so far, give your FINAL ANSWER now. Do not delegate again."
            )]
            response = llm.invoke(msgs)
        else:
            response = model_with_tools.invoke(msgs)

        if response.content:
            tag = "[SH thinking]" if getattr(response, "tool_calls", None) else "[SH FINAL]"
            print(f"\n{tag}\n{response.content}\n")
        return {"messages": [response], "step_count": step}

    def tools_node(state: SHState) -> dict:
        last = state["messages"][-1]
        out  = []
        for tc in last.tool_calls:
            try:
                res = tool_map[tc["name"]].invoke(tc["args"])
            except Exception as exc:
                res = json.dumps({"error": str(exc)})
            out.append(ToolMessage(
                content=res if isinstance(res, str) else json.dumps(res),
                tool_call_id=tc["id"], name=tc["name"],
            ))
        return {"messages": out}

    def should_continue(state: SHState) -> str:
        if state.get("step_count", 0) > SH_MAX_ROUNDS:
            return END
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    g = StateGraph(SHState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tools_node)
    g.set_entry_point("agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer), checkpointer


def run_sh(graph, message: str, thread_id: str,
           *, qid: str = "", run_name: str = "") -> tuple[str, dict]:
    """Send one message to the SH on its persistent thread. Returns (answer, state)."""
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": SH_MAX_ROUNDS * 4,
    }
    if run_name:
        config["run_name"] = run_name
    if qid:
        config["tags"]     = ["SH", qid]
        config["metadata"] = {"role": "SH", "qid": qid}

    result = graph.invoke(
        {"messages": [HumanMessage(content=message)], "step_count": 0},
        config=config,
    )
    last = result["messages"][-1]
    return getattr(last, "content", "") or "", result
