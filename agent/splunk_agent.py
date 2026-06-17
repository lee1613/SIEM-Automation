#!/usr/bin/env python3
"""
SIEM Automation Agent — connects Llama 3.3 (via NVIDIA NIM) to local Splunk Enterprise.

Model: meta/llama-3.3-70b-instruct
Brain: NVIDIA NIM (OpenAI-compatible API at integrate.api.nvidia.com)
Data:  Splunk Enterprise REST API (port 8089)

Usage:
    python splunk_agent.py                  # interactive mode
    python splunk_agent.py "your question"  # single query mode

Configure via .env (copy from .env.example):
    NIM_API_KEY, SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS
"""

import os
import sys
import json
import textwrap
from dotenv import load_dotenv
from openai import OpenAI
from splunk_client import SplunkClient

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

NIM_API_KEY  = os.getenv("NIM_API_KEY", "")
SPLUNK_HOST  = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER  = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS  = os.getenv("SPLUNK_PASS", "")

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL        = "meta/llama-3.3-70b-instruct"

# ── Tool definitions (OpenAI / NIM format) ────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_splunk_search",
            "description": (
                "Execute an SPL (Splunk Processing Language) search against local Splunk Enterprise. "
                "Use this to search for events, aggregate data, or investigate security incidents. "
                "The BOTSv3 dataset covers August 2018 security incidents in index=botsv3."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "SPL query to run. Examples: "
                            "'index=botsv3 sourcetype=WinEventLog EventCode=4625 | stats count by host', "
                            "'index=botsv3 src_ip=192.168.1.1 | head 20'"
                        ),
                    },
                    "earliest": {
                        "type": "string",
                        "description": (
                            "Start of time window. Use '0' for all-time, '-24h' for last 24 h, "
                            "or ISO timestamps like '2018-08-01T00:00:00'. Default: '0'."
                        ),
                        "default": "0",
                    },
                    "latest": {
                        "type": "string",
                        "description": "End of time window. Default: 'now'.",
                        "default": "now",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum rows to return (1–1000). Default: 50.",
                        "default": 50,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_indexes",
            "description": "List all available Splunk indexes. Use this to discover what data is accessible.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sourcetypes",
            "description": (
                "List all sourcetypes in a Splunk index with event counts. "
                "Useful for understanding what kinds of log data are present."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index name (default: botsv3)",
                        "default": "botsv3",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of sourcetypes to return (default: 30)",
                        "default": 30,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_field_values",
            "description": (
                "Get the most common values for a specific field in an index. "
                "Useful for recon, pivoting on an IP/user/host, and building targeted queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Field name (e.g. 'src_ip', 'host', 'user', 'EventCode', 'uri_path')",
                    },
                    "index": {
                        "type": "string",
                        "description": "Index name (default: botsv3)",
                        "default": "botsv3",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "How many top values to return (default: 20)",
                        "default": 20,
                    },
                },
                "required": ["field"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a SIEM (Security Information and Event Management) analyst agent connected to a local Splunk Enterprise instance.

You have access to the BOTSv3 (Boss of the SOC v3) dataset — a realistic security incident dataset from August 2018. The primary index is `botsv3`.

Your capabilities:
- Search Splunk using SPL (Splunk Processing Language)
- Investigate security incidents across Windows, Linux, network, DNS, HTTP, and cloud logs
- Identify attack patterns, lateral movement, data exfiltration, and malware activity
- Correlate events across multiple sourcetypes

Key dataset facts:
- Index: botsv3
- Time range: August 2018
- 50+ sourcetypes: WinEventLog, Sysmon, stream:http, stream:dns, suricata, linux_secure, aws:cloudtrail, iis, etc.
- Key fields by sourcetype:
  - WinEventLog/Sysmon: host, EventCode, User, ComputerName, CommandLine, Image, ParentImage
  - aws:cloudtrail: userIdentity.userName, userIdentity.type, user_type, eventName, eventSource, errorCode, sourceIPAddress
  - stream:http / iis: src_ip, dest_ip, uri_path, status, http_method, bytes
  - stream:dns: query, src_ip, dest_ip
  - linux_secure: user, src_ip, action
  - ms:o365:management / ms:aad:signin: UserId, UserPrincipalName, IPAddress, Operation, Workload

SPL tips:
- Always scope with `index=botsv3` unless listing indexes
- ALWAYS aggregate with `| stats` or `| top` — never fetch raw events unless you need a specific _raw field value
- Use `| sort -count` and `| head N` to limit large results
- Use `earliest=0` to search the full BOTSv3 time range
- Wrap multi-word field values in quotes
- Keep max_results at 50 or below for aggregated queries; never request 1000 raw events

When answering:
1. Think through what SPL queries will answer the question
2. Run searches to gather evidence — if a search returns 0 results, try a different field name or broader query before concluding there is no data
3. Synthesize findings into a clear, concise answer
4. Highlight suspicious or notable findings"""


# ── Tool execution ────────────────────────────────────────────────────────────

def execute_tool(splunk: SplunkClient, tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "run_splunk_search":
            result = splunk.search(
                query=tool_input["query"],
                earliest=tool_input.get("earliest", "0"),
                latest=tool_input.get("latest", "now"),
                max_results=tool_input.get("max_results", 50),
            )
        elif tool_name == "list_indexes":
            return json.dumps({"indexes": splunk.list_indexes()})
        elif tool_name == "get_sourcetypes":
            result = splunk.get_sourcetypes(
                index=tool_input.get("index", "botsv3"),
                top_n=tool_input.get("top_n", 30),
            )
        elif tool_name == "get_field_values":
            result = splunk.get_field_values(
                field=tool_input["field"],
                index=tool_input.get("index", "botsv3"),
                top_n=tool_input.get("top_n", 20),
            )
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        if "results" in result:
            # Strip internal Splunk metadata fields and the bulky _raw field
            # from each row to keep token count manageable.
            STRIP = {"_raw", "_bkt", "_cd", "_indextime", "_kv", "_si", "_sourcetype",
                     "_serial", "_subsecond", "punct", "linecount", "splunk_server",
                     "splunk_server_group", "timestartpos", "timeendpos"}
            cleaned = [
                {k: v for k, v in row.items() if k not in STRIP}
                for row in result["results"]
            ]
            payload = json.dumps({"results": cleaned, "meta": result.get("_meta", {})})
            # Hard cap: truncate to ~12 000 chars so we never blow the context window.
            if len(payload) > 12_000:
                payload = payload[:12_000] + '... [truncated — use a more specific query or aggregation]"}'
            return payload
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Agent loop (OpenAI / NIM tool-use protocol) ───────────────────────────────

def run_agent(client: OpenAI, splunk: SplunkClient, user_query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_query},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4096,
        )

        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Append assistant turn to history (preserves tool_calls for context)
        messages.append(msg)

        # If no tool calls, we're done
        if finish_reason != "tool_calls" or not msg.tool_calls:
            return msg.content or ""

        # Print any inline text the model emitted before calling tools
        if msg.content:
            print(f"\n[Agent thinking]\n{msg.content}\n")

        # Execute every requested tool and collect results
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"[Tool] {tc.function.name}({json.dumps(args, separators=(',', ':'))})")
            output = execute_tool(splunk, tc.function.name, args)
            preview = output[:300] + "..." if len(output) > 300 else output
            print(f"       -> {preview}\n")

            # Each tool result is a separate message with role="tool"
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      output,
            })


# ── Entry point ───────────────────────────────────────────────────────────────

def connect_splunk() -> SplunkClient:
    if not SPLUNK_PASS:
        raise SystemExit(
            "SPLUNK_PASS is not set. Copy .env.example to .env and fill in your password."
        )
    print(f"Connecting to Splunk at {SPLUNK_HOST} as '{SPLUNK_USER}'...")
    try:
        c = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
        print("Connected.\n")
        return c
    except Exception as e:
        raise SystemExit(f"Failed to connect to Splunk: {e}")


def main():
    if not NIM_API_KEY:
        raise SystemExit(
            "NIM_API_KEY is not set. Copy .env.example to .env and add your NVIDIA NIM key."
        )

    nim_client = OpenAI(base_url=NIM_BASE_URL, api_key=NIM_API_KEY)
    splunk     = connect_splunk()

    # Single-query mode
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        answer = run_agent(nim_client, splunk, query)
        print("\n" + "=" * 60)
        print(answer)
        return

    # Interactive mode
    print(f"SIEM Agent ready  [model: {MODEL}]")
    print("Type your question or 'exit' to quit.")
    print("Example: 'What are the top source IPs hitting the web server?'\n")
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
        answer = run_agent(nim_client, splunk, query)
        print("\nAgent:", textwrap.fill(answer, width=100, subsequent_indent="       "))
        print()


if __name__ == "__main__":
    main()
