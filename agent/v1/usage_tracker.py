#!/usr/bin/env python3
"""
Token and cost tracker for v1 multi-agent runs.

UsageTracker is a LangChain callback registered on every graph.invoke() call.
It accumulates token counts from the LLM API responses (exact — these are the
numbers OpenAI / NVIDIA bills you for). The Extractor uses the raw OpenAI SDK
so it calls add_nim_usage() directly.

Cost calculation uses PRICES_PER_1M. Verify prices before each full run at:
  OpenAI  → platform.openai.com/pricing
  NIM     → build.nvidia.com  (model → API → pricing tab)

GPT-5.4 has tiered pricing: requests with prompt_tokens >= 272 000 use the
long-context rate. This is evaluated per-call, matching OpenAI's billing.

Cached tokens are billed at the lower cached_input rate; non-cached input
tokens are billed at the full input rate.

After the run, call tracker.totals() to get per-model counts + cost estimates.
Cross-check the dollar figure against your OpenAI Usage dashboard and NVIDIA
NIM dashboard — those are the authoritative billing sources.
"""

from __future__ import annotations

import threading

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


# ── Price table ───────────────────────────────────────────────────────────────
# Structure per model:
#   "short": prices when prompt_tokens < long_ctx_threshold (or no tier exists)
#   "long":  prices when prompt_tokens >= long_ctx_threshold
# Keys: input, cached_input (None → no cache discount), output  (all per 1M tokens)
# long_ctx_threshold defaults to 272_000 for GPT-5.4.

PRICES_PER_1M: dict[str, dict] = {
    "gpt-5.4": {
        "long_ctx_threshold": 272_000,
        "short": {"input": 2.50,  "cached_input": 0.25,   "output": 15.00},
        "long":  {"input": 5.00,  "cached_input": 0.50,   "output": 22.50},
    },
    "gpt-5.4-mini": {
        "short": {"input": 0.75,  "cached_input": 0.075,  "output": 4.50},
    },
    "GLM-5.2-fp8": {
        "short": {"input": 0.85,  "cached_input": None,   "output": 3.10},
    },
    "meta/llama-3.3-70b-instruct": {
        "short": {"input": 0.23,  "cached_input": None,   "output": 0.40},
    },
}


def _call_cost(model: str, inp: int, cached: int, out: int) -> float:
    """Cost in USD for a single LLM call, accounting for context tier + cache."""
    spec = PRICES_PER_1M.get(model)
    if not spec:
        return 0.0
    threshold = spec.get("long_ctx_threshold", 272_000)
    tier = spec["long"] if ("long" in spec and inp >= threshold) else spec["short"]

    non_cached = max(0, inp - cached)
    cached_price = tier.get("cached_input") or tier["input"]   # fallback if no discount

    cost  = non_cached * tier["input"]  / 1_000_000
    cost += cached     * cached_price   / 1_000_000
    cost += out        * tier["output"] / 1_000_000
    return cost


def _empty_bucket() -> dict:
    return {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0, "estimated_usd": 0.0}


class UsageTracker(BaseCallbackHandler):
    """Accumulates token usage across all LangChain/LangGraph LLM calls."""

    def __init__(self) -> None:
        self._lock    = threading.Lock()         # guards all mutable counters
        self._models: dict[str, dict] = {}      # per-model totals (all agents)
        self._nim:    dict[str, dict] = {}      # NIM raw-SDK totals (Extractor)
        self._sh_cum  = _empty_bucket()         # cumulative SH totals for the whole run
        self._sh_snap = _empty_bucket()         # snapshot at start of current question

    # ── LangChain callback ────────────────────────────────────────────────────
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        lo    = response.llm_output or {}
        usage = lo.get("token_usage", {})

        # LangChain ≥0.3 may put counts in usage_metadata on the generation
        if not usage and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    um = getattr(gen, "usage_metadata", None) or {}
                    if um:
                        usage = {
                            "prompt_tokens":     um.get("input_tokens", 0),
                            "completion_tokens": um.get("output_tokens", 0),
                        }
                        # Newer LangChain: cache hits in input_token_details
                        details = um.get("input_token_details", {})
                        if details.get("cache_read"):
                            usage["prompt_tokens_details"] = {
                                "cached_tokens": details["cache_read"]
                            }
                    if usage:
                        break
                if usage:
                    break

        inp    = int(usage.get("prompt_tokens", 0))
        out    = int(usage.get("completion_tokens", 0))
        cached = int(
            (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
        )
        model  = lo.get("model_name", "unknown")

        if not (inp or out):
            return

        usd  = _call_cost(model, inp, cached, out)
        tags = kwargs.get("tags") or []
        with self._lock:
            b = self._models.setdefault(model, _empty_bucket())
            b["input_tokens"]  += inp
            b["cached_tokens"] += cached
            b["output_tokens"] += out
            b["estimated_usd"] += usd

            if "SH" in tags:
                self._sh_cum["input_tokens"]  += inp
                self._sh_cum["cached_tokens"] += cached
                self._sh_cum["output_tokens"] += out
                self._sh_cum["estimated_usd"] += usd

    # ── NIM / raw-SDK helper ──────────────────────────────────────────────────
    def add_nim_usage(self, model: str, inp: int, cached: int, out: int) -> None:
        """Called by Extractor after each NIM completion."""
        if not (inp or out):
            return
        usd = _call_cost(model, inp, cached, out)
        with self._lock:
            b = self._nim.setdefault(model, _empty_bucket())
            b["input_tokens"]  += inp
            b["cached_tokens"] += cached
            b["output_tokens"] += out
            b["estimated_usd"] += usd

    # ── Per-question SH tracking ──────────────────────────────────────────────
    def reset_sh_question(self) -> None:
        """Save a snapshot of current SH cumulative counts. Call before each question."""
        self._sh_snap = dict(self._sh_cum)

    def sh_question_tokens(self) -> dict:
        """Return SH token delta since the last reset_sh_question() call."""
        delta = {}
        for k in ("input_tokens", "cached_tokens", "output_tokens", "estimated_usd"):
            delta[k] = round(self._sh_cum[k] - self._sh_snap[k], 6)
        return delta

    # ── Final summary ─────────────────────────────────────────────────────────
    def totals(self) -> dict:
        """Per-model + grand-total breakdown for run_summary.json.

        Token counts are exact API values. Cost estimates are only as reliable as
        PRICES_PER_1M — always cross-check against OpenAI and NIM dashboards.
        """
        rows: dict[str, dict] = {}
        grand_in = grand_cached = grand_out = 0
        grand_usd = 0.0
        missing: list[str] = []

        combined = {**self._models, **self._nim}
        for model, b in combined.items():
            inp    = b["input_tokens"]
            cached = b["cached_tokens"]
            out    = b["output_tokens"]
            usd    = b["estimated_usd"]
            grand_in     += inp
            grand_cached += cached
            grand_out    += out
            grand_usd    += usd

            if model not in PRICES_PER_1M:
                missing.append(model)

            rows[model] = {
                "input_tokens":  inp,
                "cached_tokens": cached,
                "output_tokens": out,
                "total_tokens":  inp + out,
                "estimated_usd": round(usd, 6),
            }

        note = "verify against OpenAI + NIM billing dashboards"
        if missing:
            note += f"; cost for {missing} may be wrong (not in PRICES_PER_1M)"

        rows["__sh_cumulative__"] = {
            "input_tokens":  self._sh_cum["input_tokens"],
            "cached_tokens": self._sh_cum["cached_tokens"],
            "output_tokens": self._sh_cum["output_tokens"],
            "total_tokens":  self._sh_cum["input_tokens"] + self._sh_cum["output_tokens"],
            "estimated_usd": round(self._sh_cum["estimated_usd"], 6),
        }

        rows["__total__"] = {
            "input_tokens":  grand_in,
            "cached_tokens": grand_cached,
            "output_tokens": grand_out,
            "total_tokens":  grand_in + grand_out,
            "estimated_usd": round(grand_usd, 6),
            "note":          note,
        }
        return rows
