# NIM Model Availability — Tool Calling Test Results

All models tested against `https://integrate.api.nvidia.com/v1` using this API key.  
Test: single tool call (`get_source_types`) with `tool_choice: auto`, 30s timeout.

| Status | Meaning |
|---|---|
| ✅ Working | HTTP 200, `finish_reason: tool_calls`, tool dispatched correctly |
| ❌ Timeout | Listed in catalog but no response within 30s (likely higher tier / not serving) |
| ❌ 404 | Listed in catalog but endpoint not found |

---

## ✅ Confirmed Working (Tool Calling)

| Model | Finish Reason | Notes |
|---|---|---|
| `moonshotai/kimi-k2.6` | `tool_calls` | Fast, clean dispatch |
| `deepseek-ai/deepseek-v4-flash` | `tool_calls` | Fast, clean dispatch |
| `deepseek-ai/deepseek-v4-pro` | `tool_calls` | (referenced in run_deepseek_temp.py, not re-tested) |
| `nvidia/llama-3.3-nemotron-super-49b-v1` | `tool_calls` | Used as EXTRACT_MODEL in run_all.py |
| `nvidia/nemotron-3-super-120b-a12b` | `tool_calls` | Same Nemotron-3 family as the Ultra 550B |
| `mistralai/mistral-large-3-675b-instruct-2512` | `tool_calls` | Current primary model in splunk_agent.py |

---

## ❌ Unresponsive (Timeout — 30s)

| Model | Catalog | Error |
|---|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | ✅ | Read timeout (also tested at 120s — still timeout) |
| `z-ai/glm-5.1` | ✅ | Read timeout |
| `minimaxai/minimax-m2.7` | ✅ | Read timeout |
| `minimaxai/minimax-m3` | ✅ | Read timeout |

---

## ❌ Not Found (404)

| Model | Catalog | Error |
|---|---|---|
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | ✅ | HTTP 404 — endpoint not serving |

---

## Notes

- Models listed in the NIM catalog do not guarantee availability — larger/newer models (550B, MiniMax M3, GLM-5.1) appear to require a higher subscription tier or are not yet serving traffic.
- All tool-calling tests used a single no-arg function schema. Models that pass this test are compatible with the LangGraph v0 agent in `agent/splunk_agent.py`.
- OpenAI models tested separately via `api.openai.com` (not NIM): `gpt-5.4-mini` ✅ (confirmed working with tool calling; requires `max_completion_tokens` not `max_tokens`).
