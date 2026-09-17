#!/usr/bin/env python3
"""
Token and cost tracker for v1 multi-agent runs.

UsageTracker is a LangChain callback registered on every graph.invoke() call.
It accumulates token counts from the LLM API responses (exact — these are the
numbers OpenAI / NVIDIA bills you for). A caller that bypasses LangChain and
uses the raw OpenAI SDK records its usage via add_nim_usage() instead.

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

import re
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
    # Featherless. Verified against ten billed calls on the Featherless usage
    # page: cost = (input - cached)*1.4 + cached*0.26 + output*4.4, per 1M.
    "zai-org/GLM-5.3": {
        "short": {"input": 1.40,  "cached_input": 0.26,   "output": 4.40},
    },
    # ── NIM (build.nvidia.com) ────────────────────────────────────────────────
    # Every NIM model is priced at 0 by decision - see CLAUDE.md. NIM carries the
    # roles that are deliberately cheap and low-reasoning (the exploration worker),
    # so run totals understate true spend by whatever NIM would bill. That is a
    # known, accepted gap for benchmarking; docs/future_work.md records why it has
    # to be closed before this automation is scaled.
    #
    # Only models CONFIRMED SERVABLE stay here. An unknown model already costs
    # 0.0 in _call_cost and lands in totals()' `missing` list, so a row for a
    # retired model buys nothing and quietly hides that the name is dead.
    #
    # Probed 2026-09-16 against the live catalogue: of 82 models listed, only 8
    # actually answer. NIM lists far more than it will serve, and a dead name
    # returns a bare 404 rather than any deprecation signal - so "it is in
    # models.list()" is not evidence that it works. Removed, all three now
    # absent from the catalogue entirely:
    #   meta/llama-3.3-70b-instruct    EOL 2026-08-26, had been returning 410
    #   Nemotron-Cascade-2-30B-A3B     gone; never used
    #   deepseek-ai/DeepSeek-V4-Flash  renamed to deepseek-v4-flash-0731, which
    #                                  is listed but times out (25s, no reply)
    "nvidia/nemotron-3-super-120b-a12b": {
        "short": {"input": 0.0,   "cached_input": 0.0,    "output": 0.0},
    },
}


def _normalize_model_name(name: str) -> str:
    """Strip provider prefixes and dated snapshot suffixes so lookups survive
    e.g. OpenAI returning "gpt-5.4-2026-03-05" for alias "gpt-5.4", or Vultr
    returning "zai-org/GLM-5.2-FP8" for catalog id "GLM-5.2-fp8"."""
    name = name.rsplit("/", 1)[-1]
    name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", name)
    return name.lower()


_NORMALIZED_PRICES = {_normalize_model_name(k): v for k, v in PRICES_PER_1M.items()}

# ── Served context windows ────────────────────────────────────────────────────
# Same file, same keying, same "verify before each full run" discipline as
# PRICES_PER_1M — one table to check, not two places to forget.
#
# THE RULE: record the window the PROVIDER SERVES, not the one the model card
# declares. Featherless serves zai-org/GLM-5.3 at 256K against a checkpoint that
# declares 1 048 576; tools that read the checkpoint value instead of the served
# one are a known class of bug.
#
# ROUND DOWN when unsure. The failure is asymmetric: a window set too low
# compacts earlier than necessary and wastes a little; a window set too high
# overflows mid-round, which is a hard failure that costs the whole round.
#
# Adding a model? Look its served window up from the provider's own docs at the
# same moment CLAUDE.md already requires asking for its price. One lookup, two
# numbers, one table.
CONTEXT_WINDOW_PER_MODEL: dict[str, int] = {
    "zai-org/GLM-5.3": 256_000,   # Featherless; checkpoint declares 1 048 576
    "gpt-5.4":         272_000,   # OpenAI-served input window, per the user (2026-09-17)
}

DEFAULT_CONTEXT_WINDOW = 128_000   # deliberately conservative — see "round down"

_NORMALIZED_WINDOWS = {_normalize_model_name(k): v
                       for k, v in CONTEXT_WINDOW_PER_MODEL.items()}


def context_window(model: str) -> int:
    """Served context window for `model`, or the conservative default."""
    win = (CONTEXT_WINDOW_PER_MODEL.get(model)
           or _NORMALIZED_WINDOWS.get(_normalize_model_name(model)))
    if win:
        return win
    print(f"[usage] no served context window recorded for {model!r} — assuming "
          f"{DEFAULT_CONTEXT_WINDOW:,} (round down; see spec §6.1)")
    return DEFAULT_CONTEXT_WINDOW


def _call_cost(model: str, inp: int, cached: int, out: int) -> float:
    """Cost in USD for a single LLM call, accounting for context tier + cache."""
    spec = PRICES_PER_1M.get(model) or _NORMALIZED_PRICES.get(_normalize_model_name(model))
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
        self._nim:    dict[str, dict] = {}      # NIM totals from raw-SDK callers
        self._sh_cum  = _empty_bucket()         # cumulative SH totals for the whole run
        self._sh_snap = _empty_bucket()         # snapshot at start of current question
        self._by_q: dict[tuple[str, str], dict] = {}   # (qid, role) -> bucket

    # ── Per-(qid, role) attribution ───────────────────────────────────────────
    def _add_by_q(self, qid: str, role: str, inp: int, cached: int, out: int, usd: float) -> None:
        if not qid:
            return
        b = self._by_q.setdefault((qid, role), _empty_bucket())
        b["input_tokens"]  += inp
        b["cached_tokens"] += cached
        b["output_tokens"] += out
        b["estimated_usd"] += usd

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
        # OpenAI nests the cache hit under prompt_tokens_details. Featherless
        # omits that key entirely and puts `cached_tokens` at the top level of
        # `usage`, so reading only the nested path scored every Featherless call
        # as 0 cached and billed all of it at the full input rate.
        cached = int(
            (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
            or usage.get("cached_tokens", 0)
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

            # A Senior worker's graph.invoke() runs nested inside the SH run's
            # still-active context, so LangChain's ambient tags=["SH", qid]
            # leak onto it alongside its own explicit "senior" tag. Without
            # this precedence check every Senior LLM call gets billed to SH.
            is_senior  = "senior" in tags
            is_explore = "exploration" in tags and not is_senior
            is_sh      = "SH" in tags and not (is_senior or is_explore)

            if is_sh:
                self._sh_cum["input_tokens"]  += inp
                self._sh_cum["cached_tokens"] += cached
                self._sh_cum["output_tokens"] += out
                self._sh_cum["estimated_usd"] += usd

            # Exploration is checked before SH for the same reason senior is: its
            # graph runs nested inside the SH run's still-active context, so
            # LangChain's ambient tags=["SH", qid] leak onto every one of its
            # calls and would otherwise bill the whole agent to SH.
            role = ("senior" if is_senior else
                    "exploration" if is_explore else
                    "sh" if is_sh else "other")
            qid  = next((tg for tg in tags if isinstance(tg, str) and tg.startswith("Q")), "")
            self._add_by_q(qid, role, inp, cached, out, usd)

    # ── NIM / raw-SDK helper ──────────────────────────────────────────────────
    def add_nim_usage(self, model: str, inp: int, cached: int, out: int,
                      qid: str = "", role: str = "nim") -> None:
        """Record a NIM completion made with the raw OpenAI SDK.

        LangChain callers are counted automatically by on_llm_end; this is
        for anything that bypasses LangChain. The Extractor was the only
        such caller until that tier was deleted.
        """
        if not (inp or out):
            return
        usd = _call_cost(model, inp, cached, out)
        with self._lock:
            b = self._nim.setdefault(model, _empty_bucket())
            b["input_tokens"]  += inp
            b["cached_tokens"] += cached
            b["output_tokens"] += out
            b["estimated_usd"] += usd
            self._add_by_q(qid, role, inp, cached, out, usd)

    # ── Resume support ────────────────────────────────────────────────────────
    def seed(self, prior_token_usage: dict | None) -> None:
        """Pre-load counters from a previous process's saved run_summary.json
        so a resumed process's totals keep accumulating instead of restarting
        at zero. The stored dollar figure is trusted as-is: recomputing from
        aggregate token counts would apply per-call long-context tiering to
        the whole segment's input at once (gpt-5.4 trips the >=272k long tier
        on any multi-question segment, roughly doubling the reported cost)."""
        if not prior_token_usage:
            return
        with self._lock:
            for model, b in prior_token_usage.items():
                if model.startswith("__"):
                    continue
                inp    = b.get("input_tokens", 0)
                cached = b.get("cached_tokens", 0)
                out    = b.get("output_tokens", 0)
                bucket = self._models.setdefault(model, _empty_bucket())
                bucket["input_tokens"]  += inp
                bucket["cached_tokens"] += cached
                bucket["output_tokens"] += out
                bucket["estimated_usd"] += float(b.get("estimated_usd", 0.0))

            sh = prior_token_usage.get("__sh_cumulative__")
            if sh:
                for k in ("input_tokens", "cached_tokens", "output_tokens", "estimated_usd"):
                    self._sh_cum[k] += sh.get(k, 0)
                self._sh_snap = dict(self._sh_cum)

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

    def by_question(self) -> dict:
        """Return {qid: {role: bucket}} with per-question, per-role usage."""
        out: dict[str, dict] = {}
        with self._lock:
            for (qid, role), b in self._by_q.items():
                out.setdefault(qid, {})[role] = {
                    "input_tokens":  b["input_tokens"],
                    "cached_tokens": b["cached_tokens"],
                    "output_tokens": b["output_tokens"],
                    "estimated_usd": round(b["estimated_usd"], 6),
                }
        return out

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

        combined: dict[str, dict] = {}
        for src in (self._models, self._nim):
            for model, b in src.items():
                c = combined.setdefault(model, _empty_bucket())
                c["input_tokens"]  += b["input_tokens"]
                c["cached_tokens"] += b["cached_tokens"]
                c["output_tokens"] += b["output_tokens"]
                c["estimated_usd"] += b["estimated_usd"]
        for model, b in combined.items():
            inp    = b["input_tokens"]
            cached = b["cached_tokens"]
            out    = b["output_tokens"]
            usd    = b["estimated_usd"]
            grand_in     += inp
            grand_cached += cached
            grand_out    += out
            grand_usd    += usd

            if model not in PRICES_PER_1M and _normalize_model_name(model) not in _NORMALIZED_PRICES:
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
