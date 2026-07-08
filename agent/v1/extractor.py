#!/usr/bin/env python3
"""
Extractor agent for v1.

Strips the orchestrator's prose down to the bare scoreboard answer
(DeepSeek-V4-Flash via Vultr — a plain non-reasoning model, chosen so hidden
chain-of-thought can't eat the completion-token budget on this fixed-format task;
reuses the v0 extract_clean_answer approach).

Caller submits the extracted answer directly to the scoreboard.
"""

import time

import openai
from openai import OpenAI

try:
    from langsmith import traceable
except Exception:
    def traceable(*a, **k):
        def _wrap(fn): return fn
        return _wrap if not (len(a) == 1 and callable(a[0])) else a[0]


EXTRACT_MODEL = "Qwen/Qwen3.6-27B"  # was DeepSeek-V4-Flash; its Vultr cluster went down mid-run_1.2
# Qwen3.6 is a hybrid-reasoning model: thinking must be disabled or hidden CoT
# eats the completion budget and content comes back null.
EXTRACT_EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}
EXTRACT_MAX_RETRIES = 5
EXTRACT_RETRY_BACKOFF = 10.0  # seconds; doubles each retry (10+20+40+80 — rides out ~2.5 min gateway outage)


def build_extract_prompt(question: str, guidance: str, verbose_answer: str,
                         expected_shape: str = "") -> str:
    """Pure prompt builder for the extractor's prose-strip call.

    `expected_shape` is an optional hint (e.g. from planner/runner guidance) telling
    the extractor to strip vendor/version suffixes and normalize list formatting
    (fixes cases like submitting 'E5-2676 v3' when the scoreboard wants 'E5-2676').
    """
    guidance_line = f"Answer format guidance: {guidance}" if guidance else ""
    shape_line = f"Required answer shape: {expected_shape}" if expected_shape else ""
    return (
        f"Question: {question}\n\n"
        f"{guidance_line}\n{shape_line}\n\n"
        f"Agent's analysis: {verbose_answer}\n\n"
        "Based on the analysis above, state ONLY the exact answer with no "
        "explanation, no punctuation beyond what the format requires, and no "
        "surrounding text. Strip any vendor/version suffix not asked for. "
        "If the answer is a list, use comma-separated values with no spaces. "
        "If a number, give only the number. Output nothing else."
    )


class Extractor:
    def __init__(self, nim_api_key: str, nim_base_url: str,
                 model: str = EXTRACT_MODEL, tracker=None):
        self.client  = OpenAI(base_url=nim_base_url, api_key=nim_api_key)
        self.model   = model
        self.tracker = tracker

    @traceable(run_type="llm", name="Extractor")
    def _complete(self, prompt: str):
        """The raw network call, wrapped so it shows as a span in LangSmith."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,  # reasoning models spend budget on hidden chain-of-thought before the answer
            temperature=0,
            extra_body=EXTRACT_EXTRA_BODY if self.model == EXTRACT_MODEL else None,
        )

    def extract(self, question: str, guidance: str, verbose_answer: str, qid: str = "",
                expected_shape: str = "") -> str:
        """Prose-strip to the bare answer the scoreboard expects."""
        prompt = build_extract_prompt(question, guidance, verbose_answer, expected_shape)
        delay = EXTRACT_RETRY_BACKOFF
        for attempt in range(1, EXTRACT_MAX_RETRIES + 1):
            try:
                resp = self._complete(prompt)
                break
            except (openai.APIStatusError, openai.APITimeoutError, openai.APIConnectionError) as exc:
                if attempt == EXTRACT_MAX_RETRIES:
                    raise
                print(f"[EXTRACTOR] API call failed (attempt {attempt}/{EXTRACT_MAX_RETRIES}): {exc}. Retrying in {delay:.0f}s...")
                time.sleep(delay)
                delay *= 2
        if self.tracker and resp.usage:
            u = resp.usage
            cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
            self.tracker.add_nim_usage(
                self.model,
                inp=u.prompt_tokens or 0,
                cached=cached,
                out=u.completion_tokens or 0,
                qid=qid,
                role="extractor",
            )
        return (resp.choices[0].message.content or "").strip()
