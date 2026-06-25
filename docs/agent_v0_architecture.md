# SIEM Agent v0 — Architecture & Design Reference

> **Codebase snapshot**: `agent/splunk_agent.py` (LangGraph edition)  
> **Purpose**: Baseline design record for the BOTSv3 CTF agent before any architectural evolution.

---

## Overview

v0 is a stateful, tool-calling LangGraph agent that investigates BOTSv3 Splunk data to answer CTF questions. Every design decision is oriented around one constraint: a moderately capable LLM (70B–550B parameter class) must produce reliable, non-hallucinated SPL queries against a live Splunk instance with no prior knowledge of the dataset's schema.

---

## Feature Catalogue

### 1. LangGraph as the Orchestration Framework

The agent runs inside a compiled `StateGraph` (`langgraph.graph.StateGraph`). Rather than a simple prompt-loop, execution is split across three dedicated nodes that enforce a strict pre-execution gate before any tool call reaches Splunk.

**Why LangGraph?**  
Raw tool-call loops (e.g. the native OpenAI loop in `run_gpt54mini_native.py`) give the LLM full authority to call any tool with any arguments. In practice, moderate-reasoning models hallucinate sourcetype names and run expensive full-scan SPL queries. LangGraph's graph topology makes it possible to intercept every proposed tool call before execution and apply deterministic validation rules the LLM cannot override.

The verify node enforces:
- **Sourcetype existence check**: the `sourcetype=` value in every `run_splunk_search` call must exist in the local field manifest. Calls referencing invented sourcetypes are rejected before touching Splunk.
- **Aggregation requirement**: every SPL query must contain `| stats`, `| top`, or `| rare`. Raw event stream queries are rejected.
- **Leading wildcard ban**: `=*value` patterns force a full sequential scan and are blocked. Only trailing wildcards (`value*`) are allowed.
- **Dedup guard**: identical (tool, args) pairs that previously errored or returned zero results are blocked from repeating — see Feature 5.

---

### 2. Maximum 15 Agentic Iterations Per Question

```python
MAX_ITER = 15   # agent-node invocations (each may produce one tool call)
```

When `step_count > MAX_ITER`, the agent node switches from `model_with_tools` to `model_bare` (no tools bound) and injects a forced-finalize instruction:

```
"You have used the maximum number of tool calls.
 Give your best final answer now based on everything found so far."
```

The graph router (`should_continue`) also returns `END` unconditionally once the cap is reached, preventing any further verify/execute cycles regardless of whether the model still wants to call tools.

Additionally, the LangGraph recursion limit is set to `MAX_ITER * 4` to provide a hard ceiling at the graph level as a secondary safeguard.

---

### 3. Verbalized ReAct Framework — Intention-Before-Tool-Call

The system prompt opens with a **CRITICAL RULE** block that requires the model to write an `Intention:` line before every tool call:

```
CRITICAL RULE — READ FIRST: You MUST write an "Intention:" line before EVERY tool call.
NEVER call a tool without first stating your reasoning. Your tool call WILL BE REJECTED
if you do not include "Intention:" in your message.

Example:
  Intention: I need to see all available sourcetypes to find where DNS data lives.
  → call get_source_types()
```

This is enforced structurally in `verify_node`:

```python
intention_missing = not last.content or "intention" not in last.content.lower()
intention_retries = state.get("intention_retries", 0)

if intention_missing and intention_retries < 2:
    # Inject rejection ToolMessage for every proposed call
    return {"messages": rejections, "verification_passed": False,
            "intention_retries": intention_retries + 1}
```

The model gets up to 2 retries before the intention check is waived (preventing infinite loops on models that consistently skip the prefix). This is the **Verbalized ReAct** pattern: Reason → Act, with the reasoning explicitly surfaced in the message content rather than implied.

The system prompt also provides a canonical investigation flow as a worked example:

```
Intention: Understand what sourcetypes are available.
→ get_source_types()

Intention: stream:udp looked relevant; check its fields.
→ get_sourcetype_fields(sourcetype="stream:udp")

Intention: No useful dest field; search the manifest for 'dest'.
→ search_keyword(keyword="dest")

Intention: stream:ip has a 'dest' field; sample a raw event first.
→ sample_events(sourcetype="stream:ip")

Intention: Field confirmed. Run aggregation.
→ run_splunk_search(query="index=botsv3 sourcetype=stream:ip | top limit=20 dest")
```

---

### 4. JSON Field Manifest — Schema-Aware Without Iterative Discovery

**File**: `agent/botsv3_fields.json`

The manifest is a JSON dictionary with the schema:

```json
{
  "source_types": {
    "<sourcetype_name>": {
      "fields": ["field_a", "field_b", "field_c"]
    },
    ...
  }
}
```

It covers **102 sourcetypes** with pre-populated field lists derived from the BOTSv3 dataset. A reference copy with all fields populated is kept at `agent/botsv3_fields_filled.json`; a blank template (sourcetypes only, `"fields": []`) is at `agent/botsv3_fields_template.json`.

**How the agent uses it** — the manifest is accessed through two hidden helpers that the agent never sees directly:

| Helper | Exposed to agent? | Purpose |
|---|---|---|
| `_manifest_get_source_types()` | via `get_source_types` tool | Returns all 102 sourcetype names instantly |
| `_search_keyword_in_manifest(keyword)` | via `search_keyword` tool | Returns all fields whose name contains the keyword |
| `_manifest_expand(sourcetype, fields)` | never | Writes new fields discovered from Splunk fallback back into the JSON |

**`search_keyword` fallback and self-population**:  
If a keyword is not found in any manifest field, the tool falls back to a live Splunk query:

```spl
index=botsv3 *keyword* | fields sourcetype *keyword*
| untable sourcetype field_name field_value
| stats count values(field_value) as example_values by field_name, sourcetype
```

Results are parsed and written back into `botsv3_fields.json` via `_manifest_expand`, so the manifest grows richer with each run. The agent sees only the keyword search result, never the manifest internals.

**Benefits**:
- Zero Splunk calls for "what fields exist in sourcetype X?" when the manifest already has them — instant schema lookup.
- Prevents hallucinated field names: the verify node checks the proposed sourcetype against `_known_sourcetypes()` before running any SPL.

---

### 5. Loop-Break Guardrail — Dedup Guard Against Stuck Reasoning

Two sets are maintained in `AgentState` across the question's lifecycle:

| State field | What it tracks |
|---|---|
| `seen_errors` | `[(tool_name, args_str), ...]` — calls that returned an `{"error": ...}` |
| `seen_empty` | `[(tool_name, args_str), ...]` — calls where `results == []` |

`verify_node` checks every proposed tool call against both sets before allowing execution. If an identical `(name, args)` pair is found:

```python
# Error dedup
if call_key in seen_errors:
    return "Rejected: this exact tool call already failed with an error this turn. "
           "Try different arguments or a different approach."

# Empty dedup
if call_key in seen_empty:
    return "Rejected: this exact tool call already returned zero results this turn. "
           "Change the sourcetype, field name, filter value, or search strategy."
```

The rejection message is injected back as a `ToolMessage` so the model sees it as the tool's response — it understands that retrying the same call is blocked and must pivot. This is especially important for lower-reasoning models (e.g. 7B–70B) that tend to retry identical queries without variation when they hit an empty result.

The guardrail resets per question (both lists are initialized to `[]` in each `run_agent` invocation) so it does not interfere with cross-question context.

---

### 6. Architecture Diagram — Closed-Loop LangGraph StateGraph

```
                        ┌─────────────────────────────────┐
                        │        LangGraph StateGraph      │
                        │                                  │
  Question ────────────►│  ┌──────────────────────────┐   │
  (HumanMessage)        │  │       agent_node          │   │
                        │  │                           │   │
                        │  │  [system_msg + history]   │   │
                        │  │          │                │   │
                        │  │   LLM (model_with_tools)  │   │
                        │  │          │                │   │
                        │  │  AIMessage (+ tool_calls?)│   │
                        │  └──────────┬────────────────┘   │
                        │             │                     │
                        │    should_continue()              │
                        │     ┌───────┴───────┐            │
                        │  tool_calls?      no tool_calls   │
                        │     │                    │        │
                        │     ▼                    ▼        │
                        │  ┌──────────┐          END        │
                        │  │verify_   │       (final ans)   │
                        │  │ node     │                     │
                        │  │          │                     │
                        │  │ Checks:  │                     │
                        │  │ ✓ Intention present?           │
                        │  │ ✓ sourcetype in manifest?      │
                        │  │ ✓ | stats / top / rare ?       │
                        │  │ ✓ no leading wildcard?         │
                        │  │ ✓ not a repeated failed call?  │
                        │  └──────────┬───────────┘         │
                        │             │                     │
                        │       after_verify()              │
                        │    ┌────────┴────────┐           │
                        │ APPROVED          REJECTED        │
                        │    │                  │           │
                        │    ▼                  │           │
                        │  ┌──────────┐         │           │
                        │  │execute_  │    ToolMessage      │
                        │  │ node     │  (error feedback)   │
                        │  │          │         │           │
                        │  │ Runs tool│         │           │
                        │  │ Records  │         │           │
                        │  │ errors / │         │           │
                        │  │ empties  │         └──────────►│
                        │  └────┬─────┘            agent_  │
                        │       │                  node     │
                        │       │ ToolMessage(result)       │
                        │       └──────────────────────────►│
                        │                      agent_node   │
                        └─────────────────────────────────┘

  State fields carried across the loop:
  ┌─────────────────────────────────────────────────────────────┐
  │  AgentState                                                  │
  │  ─────────────────────────────────────────────────────────  │
  │  messages            : list  — full conversation history     │
  │  seen_errors         : list  — (tool, args) pairs that errored│
  │  seen_empty          : list  — (tool, args) pairs → 0 results│
  │  step_count          : int   — agent-node invocation count   │
  │  verification_passed : bool  — verify node approval status   │
  │  intention_retries   : int   — times Intention check waived  │
  └─────────────────────────────────────────────────────────────┘

  Tools exposed to agent (6 total):
  ┌─────────────────────────────────────────────────────────────┐
  │  get_source_types()          — manifest lookup, no Splunk   │
  │  search_keyword(keyword)     — manifest search + fallback   │
  │  get_sourcetype_fields(st)   — live Splunk fieldsummary     │
  │  get_field_values(field, st) — top N distinct values        │
  │  sample_events(st, keyword)  — raw event inspection         │
  │  run_splunk_search(query)    — gated SPL execution          │
  └─────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|---|---|---|
| Verify gate before every tool call | Catch hallucinated sourcetypes before they hit Splunk | Adds one LLM-free node per call; latency is negligible vs. Splunk round-trip |
| Manifest as hidden internal (not a tool) | Prevents agent from reasoning about manifest structure; keeps the search API clean | Manifest must be pre-populated; cold-start for unknown sourcetypes requires Splunk fallback |
| Intention check with 2-retry grace | Enforces ReAct without hard-failing models that occasionally skip the prefix | Grace limit means the check can be bypassed; strict mode would reject more often |
| `seen_errors` / `seen_empty` reset per question | Prevents inter-question state pollution | Within a question, a genuinely valid call that previously failed won't be retried |
| Single thread across all 58 questions | Model accumulates cross-question context (IAM users found in Q200 help Q201) | Context window grows; late questions see a very long message history |
| `MemorySaver` checkpointer | Enables resumable runs and cross-question memory | In-memory only; lost on process restart |

---

## File Map

| File | Role |
|---|---|
| `agent/splunk_agent.py` | Full v0 agent: LangGraph graph, tools, verify node, state, system prompt |
| `agent/run_all.py` | Run orchestrator: loads questions, calls agent, scores via scoreboard |
| `agent/run_nemotron_ultra.py` | Nemotron Ultra variant runner (same architecture, different model) |
| `agent/botsv3_fields.json` | Live manifest — grows during runs via `_manifest_expand` |
| `agent/botsv3_fields_filled.json` | Reference copy with all fields populated |
| `agent/botsv3_fields_template.json` | Blank template (102 sourcetypes, empty field lists) |
| `agent/scoreboard_client.py` | CTF scoreboard KV store client + submission logger |
| `agent/splunk_client.py` | Splunk REST API wrapper (search, fieldsummary, field values, sample) |
