#!/usr/bin/env python3
"""
The exploration worker: find WHICH feeds could hold the answer, not the answer.

SH plans from a static briefing of sourcetype and source names. When no name
matches what a question describes, SH is left guessing - and a guessed scope is
how Q216 spent 14 delegations locked to the wrong axis. This worker is what SH
spawns instead of guessing. It reports feeds; a Senior then investigates them.

WHY THE PIVOTS ARE ORDERED THE WAY THEY ARE, measured against live BOTSv3:

    | metadata type=sources ... search source=*cisco*     1.1s   found all 3 feeds
    index=botsv3 source=*cisco* | stats count by source   3.2s   found all 3 feeds
    index=botsv3 *cisco*        | stats count by source  28.4s   found 1 of 3

The last one is the obvious query and it is the worst: it scans raw event *text*,
so it missed `cisconvmflowdata` (78,459 events, rank 13) entirely - that feed's
Cisco-ness is in its NAME, not in its payloads - while costing 26x the cheapest
pivot. So name pivots run first and a content scan is a deliberate last resort.

The risk there is not a timeout (splunk_client allows 600s; the worst scan here
is ~40s). It is POOL STARVATION: SplunkConnectionPool holds 6 connections and
MAX_WORKERS is 6, so a 40s scan holds a slot for its whole duration and a few
concurrent ones can block every Senior in the wave. Cheapest-first plus a hard
per-run cap is the mitigation; a longer timeout would not help.

The model is a cheap NIM one and the reasoning budget is deliberately small:
this is a lookup task, not an analysis task. NIM models are priced at 0, which is
a known and accepted accounting gap - see docs/future_work.md #2.
"""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from llm_errors import describe_llm_error, resilient_http_client

EXPLORATION_MODEL    = "nvidia/nemotron-3-super-120b-a12b"
EXPLORATION_MAX_ITER = 8       # a lookup task; 8 tool calls is generous
CONTENT_SCAN_MAX     = 2       # hard cap on ~30s raw scans per exploration run

SYSTEM_PROMPT = """You find WHERE data lives in a Splunk index. You do NOT answer the \
user's question - another worker does that with what you report.

The index is `botsv3`. Data is addressed on two axes, `sourcetype` and `source`, and a
single sourcetype can hide many unrelated feeds. You were called because the obvious
names did not match, so assume the answer is hiding under a name that does not describe
it.

METHOD - cheapest first, and do not skip ahead:
1. `find_feeds_by_name` for each key term in the question (a vendor, a product, a
   protocol, a hostname). This reads the index catalogue and is nearly free. It also
   returns each feed's time range - a feed that does not span the window the question
   asks about is not the answer, whatever its name says.
2. Still nothing? `find_feeds_by_field` - matches the term against feed names through a
   real search, which catches a few cases step 1 misses.
3. Only if both come up empty, `find_feeds_by_content` - this scans raw event text and
   takes ~30 seconds per call, so you get at most two. Use your best single term.

Then call `report_feeds` EXACTLY ONCE with what you found. Report a feed if it is
plausible: a wrong lead costs one worker, a missed feed costs the question. If you found
nothing, call `report_feeds` with empty lists and say in `insights` which terms you
tried, so the next round does not repeat them."""


def make_tools(splunk, budget: dict) -> list:
    """Discovery tools bound to a Splunk client.

    `budget` is a per-run mutable counter for the expensive content scan. The
    prompt asks for restraint; this enforces it.
    """

    @tool
    def find_feeds_by_name(term: str) -> str:
        """Find feeds whose NAME contains `term`. Start here - it reads the index
        catalogue rather than scanning events, so it costs ~1s regardless of index
        size, and it returns each feed's event count and time coverage."""
        safe = re.sub(r'["|\s]', "", term)
        if not safe:
            return "give a non-empty term"
        out = []
        for kind, field in (("sourcetypes", "sourcetype"), ("sources", "source")):
            r = splunk.search(
                f"| metadata type={kind} index=botsv3 | search {field}=*{safe}* "
                f"| table {field} totalCount firstTime lastTime",
                earliest="0", max_results=50)
            for row in (r.get("results") or []):
                out.append(f"{field}={row.get(field)}  events~{row.get('totalCount')}  "
                           f"first={row.get('firstTime')} last={row.get('lastTime')}")
        return "\n".join(out) if out else f"no feed name contains '{safe}'"

    @tool
    def find_feeds_by_field(term: str) -> str:
        """Find feeds by name through a real search rather than the catalogue.
        Slower than find_feeds_by_name (~3s) and catches a few cases it misses.
        Use after find_feeds_by_name has come up empty."""
        safe = re.sub(r'["|\s]', "", term)
        if not safe:
            return "give a non-empty term"
        r = splunk.search(
            f'index=botsv3 (source=*{safe}* OR sourcetype=*{safe}*) '
            f'| stats count by source, sourcetype | sort -count | head 30',
            earliest="0", max_results=30)
        rows = r.get("results") or []
        return "\n".join(
            f"source={x.get('source')}  sourcetype={x.get('sourcetype')}  "
            f"events={x.get('count')}" for x in rows) or f"no feed named like '{safe}'"

    @tool
    def find_feeds_by_content(term: str) -> str:
        """LAST RESORT. Find feeds whose raw EVENT TEXT mentions `term`. This scans
        the whole index, takes ~30 seconds, and you get at most two calls. It finds
        things the name pivots cannot - and misses things they find, because a feed
        can be about a vendor without naming it in every event."""
        if budget["content_scans"] >= CONTENT_SCAN_MAX:
            return (f"content-scan budget spent ({CONTENT_SCAN_MAX}). "
                    "Report what you have with report_feeds.")
        safe = re.sub(r'["|\s]', "", term)
        if not safe:
            return "give a non-empty term"
        budget["content_scans"] += 1
        r = splunk.search(
            f'index=botsv3 *{safe}* | stats count by source, sourcetype '
            f'| sort -count | head 30',
            earliest="0", max_results=30)
        rows = r.get("results") or []
        return "\n".join(
            f"source={x.get('source')}  sourcetype={x.get('sourcetype')}  "
            f"events={x.get('count')}" for x in rows) or f"no event text contains '{safe}'"

    @tool
    def report_feeds(source_types: str = "", sources: str = "",
                     insights: str = "") -> str:
        """Report what you found and STOP. Call this exactly once, as your last action.

        - source_types: comma-separated sourcetype names worth investigating.
        - sources: comma-separated source names worth investigating.
        - insights: what you learned - which term matched, the feed's time range,
          and which terms found nothing, so the next round can skip them.
        """
        return "Reported. Stop here - do not call any further tools."

    return [find_feeds_by_name, find_feeds_by_field, find_feeds_by_content,
            report_feeds]


def _split(s: str) -> list[str]:
    return [p.strip() for p in (s or "").replace("\n", ",").split(",") if p.strip()]


def parse_report(messages: list) -> dict:
    """The schema SH gets back: {source_types, sources, insights}.

    Read from the last report_feeds tool call, the same way the Senior's
    submit_finding is read - the final state comes back intact, so no shared
    mutable accumulator is needed and concurrent workers cannot interleave.
    """
    for msg in reversed(messages or []):
        for call in (getattr(msg, "tool_calls", None) or []):
            if (call.get("name") or "") == "report_feeds":
                args = call.get("args") or {}
                return {
                    "source_types": _split(args.get("source_types", "")),
                    "sources":      _split(args.get("sources", "")),
                    "insights":     str(args.get("insights", "")).strip(),
                    "structured":   True,
                }
    return {"source_types": [], "sources": [], "insights": "", "structured": False}


def render_report(report: dict) -> str:
    """The report as prose, for the joiner and the delegation record.

    An exploration worker never answers the question, so its `answer` field is
    this: the feeds it found. A Senior spawned afterwards reads it as prior_info.
    """
    parts = []
    if report.get("source_types"):
        parts.append("sourcetypes to investigate: " + ", ".join(report["source_types"]))
    if report.get("sources"):
        parts.append("sources to investigate: " + ", ".join(report["sources"]))
    if report.get("insights"):
        parts.append("insights: " + report["insights"])
    if not parts:
        return "EXPLORATION found no candidate feeds."
    return "EXPLORATION - " + "; ".join(parts)


def build_exploration_agent(api_key: str, base_url: str, splunk, *,
                            model: str = EXPLORATION_MODEL):
    """Compile the exploration ReAct agent. Returns (graph, budget)."""
    budget = {"content_scans": 0}
    llm = ChatOpenAI(api_key=api_key, model=model, base_url=base_url,
                     temperature=0, max_completion_tokens=2048,
                     http_client=resilient_http_client())
    graph = create_react_agent(llm, make_tools(splunk, budget))
    return graph, budget


def run_exploration(graph, budget: dict, question: str, *, qid: str = "",
                    idx: int = 0, tracker=None,
                    max_iter: int = EXPLORATION_MAX_ITER) -> dict:
    """Run one exploration pass.

    Never raises: a discovery worker that fails must degrade to "found nothing",
    not take the question down with it. SH can still plan from the briefing.
    """
    budget["content_scans"] = 0
    config = {"recursion_limit": max_iter * 4,
              "run_name": f"Exploration-{idx}-{qid}",
              "tags": ["exploration", qid],
              "metadata": {"role": "exploration", "qid": qid, "idx": idx}}
    if tracker is not None:
        config["callbacks"] = [tracker]

    try:
        state = graph.invoke(
            {"messages": [SystemMessage(content=SYSTEM_PROMPT),
                          HumanMessage(content=question)]},
            config=config)
    except Exception as exc:
        detail = describe_llm_error(exc, f"Exploration-{idx}-{qid}", None)
        print(detail)
        return {"source_types": [], "sources": [],
                "insights": f"exploration failed: {detail}",
                "structured": False, "api_failed": True}

    report = parse_report(state.get("messages") or [])
    report["api_failed"] = False
    return report
