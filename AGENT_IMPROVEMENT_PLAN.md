# Plan: Improve SIEM Agent Field Awareness & Discovery

## Context
The agent failed on BOTSv3 Q225 (memcached attack) because it didn't know `stream:udp` exists or that payload data is in `src_content`/`dest_content`. This is not an isolated case — at least 12 of 40+ questions rely on sourcetypes or fields the LLM cannot guess. The root cause is that the agent has no way to discover data schemas dynamically and the system prompt only covers ~40% of sourcetypes and ~25% of fields.

## Approach: Tools First, Prompt Second

### Change 1: Add `get_fields` tool
**Files:** `agent/splunk_client.py`, `agent/splunk_agent.py`

Add a method that runs `| fieldsummary` on a sampled subset of events for a given sourcetype:
```python
# splunk_client.py
def get_fields(self, sourcetype, index="botsv3", sample_size=1000):
    return self.search(
        f'index={index} sourcetype="{sourcetype}" | head {sample_size} '
        f'| fieldsummary | where count > 10 '
        f'| table field, count, distinct_count | sort -count',
        earliest="0", max_results=200,
    )
```
Register as a tool in TOOLS list with description: *"List all fields in a sourcetype with their frequency. Use this BEFORE writing queries against unfamiliar sourcetypes to discover real field names."*

### Change 2: Add `sample_events` tool
**Files:** `agent/splunk_client.py`, `agent/splunk_agent.py`

Returns 3-5 raw events so the LLM can see actual data structure:
```python
# splunk_client.py
def sample_events(self, sourcetype, index="botsv3", count=3, search_term=""):
    term = f' "{search_term}"' if search_term else ""
    return self.search(
        f'index={index} sourcetype="{sourcetype}"{term} | head {count}',
        earliest="0", max_results=count,
    )
```
Keep `_raw` in results for this tool only (modify STRIP set logic in `execute_tool`).

### Change 3: Rewrite system prompt
**File:** `agent/splunk_agent.py`

Key changes to SYSTEM_PROMPT:

1. **Add investigation workflow** — teach the LLM a step-by-step discovery strategy:
   - Search broadly by keyword: `index=botsv3 "keyword" | stats count by sourcetype`
   - Call `get_fields(sourcetype)` before querying unfamiliar sourcetypes
   - If 0 results → broaden search, try different sourcetypes, use `sample_events`
   - Never give up after just one failed approach

2. **Expand sourcetype reference** — add the missing ones the LLM can't guess:
   - `stream:udp` (UDP payload captures)
   - `cisconvmflowdata` / `cisconvmsysdata` (Cisco network visibility)
   - `PerfmonMk:Process` (Windows performance counters)
   - `osquery:results` (fields under `columns.*`, `decorations.*`)
   - `cloud-init-output`, `lambda:dns`, `ms:o365:reporting:messagetrace`

3. **Add field syntax note** — mention Splunk's array notation: `attach_filename{}`, `Parameters{}.Value`, `targets{}.modifiedProperties{}.name`

4. **Remove hardcoded field-per-sourcetype mappings** — replace with instruction to use `get_fields` tool. This keeps the prompt lean and makes the agent work for any dataset.

### Change 4: Add iteration cap to agent loop
**File:** `agent/splunk_agent.py`

Cap `run_agent` while loop at 15 iterations to prevent runaway tool calls.

## What NOT to Do
- Don't create a static field manifest JSON — `get_fields` makes it unnecessary
- Don't inject BOTSv3-specific IOCs (coinhive, Taedonggang) — they appear in the questions themselves
- Don't add few-shot SPL examples per sourcetype — too many tokens for Llama 3.3

## How Q225 Gets Solved After Changes
1. LLM sees "memcached attack" → knows it's UDP-based
2. Prompt now lists `stream:udp` as a sourcetype (or LLM discovers it via `index=botsv3 "memcached" | stats count by sourcetype`)
3. LLM calls `get_fields("stream:udp")` → discovers `src_content`, `dest_content`
4. LLM queries: `index=botsv3 sourcetype="stream:udp" | table src_content dest_content`
5. Finds `index1.jpeg` in the payload

## Verification
Re-run agent on these questions that rely on obscure sourcetypes/fields:
- Q225 (stream:udp, memcached) — the original failure
- Q215 (cisconvmsysdata, Cisco NVM abbreviations)
- Q216 (cisconvmflowdata, flow duration)
- Q303 (osquery:results, columns.cmdline / decorations.username)
- Q208 (PerfmonMk:Process, process CPU usage)

## Files to Modify
1. `agent/splunk_client.py` — add `get_fields()` and `sample_events()` methods
2. `agent/splunk_agent.py` — add 2 tool definitions, rewrite SYSTEM_PROMPT, modify `execute_tool`, add iteration cap
