#!/usr/bin/env python3
"""
Extractor agent for v1.

Strips the orchestrator's prose down to the bare scoreboard answer, which the
caller submits directly.

The task is fixed-format and needs no reasoning, so the model runs with thinking
disabled. That was always the intent - the original choice was a plain
non-reasoning model precisely so hidden chain-of-thought could not eat the
completion budget - but the choice drifted through four models as each was
retired, and the drift was never re-checked against that requirement. Q329
submitted 4,487 characters of a reasoning model's deliberation to the
scoreboard. See EXTRACT_EXTRA_BODY below for how it is switched off and what it
costs, and clean_completion for the guard that catches it regardless of model.
"""

import re
import time

import openai
from llm_errors import describe_llm_error, resilient_http_client
from openai import OpenAI

try:
    from langsmith import traceable
except Exception:
    def traceable(*a, **k):
        def _wrap(fn): return fn
        return _wrap if not (len(a) == 1 and callable(a[0])) else a[0]


# via NIM; was meta/llama-3.3-70b-instruct until it reached end of life on
# 2026-08-26 and began returning HTTP 410, before that Qwen3.6-27B (Vultr) and
# DeepSeek-V4-Flash.
#
# Nemotron is a reasoning model, and that is what leaked Q329: its chain of
# thought normally arrives in a separate `reasoning_content` field, but when it
# never reaches a final answer the thinking spills into `content` instead, and
# 4,487 characters of deliberation went to the scoreboard.
#
# So the reasoning is switched OFF at the API rather than the model swapped out.
# Probing the live NIM catalogue found only 8 of 82 listed models answer at all,
# and no servable non-reasoning one is usable here: ising-calibration-1.5-31b
# ignores the prompt and echoes "FINAL ANSWER:" labels (2/4), mistral-nemotron
# times out on 7 of 8 calls, and gemma-4-31b-it times out on every real prompt
# at any token cap (it answers only toy ones).
#
# Of the toggles NIM accepts, only chat_template_kwargs works. `/no_think` and
# "detailed thinking off" as system messages leave reasoning fully on, and
# min_thinking_tokens is rejected as an unsupported parameter.
EXTRACT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
EXTRACT_EXTRA_BODY = {"chat_template_kwargs": {"thinking": False}}

# With thinking off there is no hidden chain of thought to fund, so the budget
# only has to cover the answer. Measured: the longest real extraction spends 31
# output tokens (a 40-char hash); the same calls with reasoning on spent 40-687.
# A low cap also bounds the damage if a future model leaks again.
EXTRACT_MAX_TOKENS = 256

# KNOWN REGRESSION, accepted deliberately. Thinking off scores 5/6 on the
# extraction cases against 6/6 with it on. The one failure is
# "PARTIAL ANSWER: nullweb_admin" -> "web_admin" - the exact transcription that
# cost run_1.2 points. Two fixes were tried and both failed: a prompt line
# demanding character-for-character fidelity (still "web_admin"), and stripping
# the FINAL/PARTIAL ANSWER tag before the model sees it (made it worse -
# "admin"). The same value inside ordinary prose extracts correctly, so the
# model simply cannot hold it without reasoning. What still guards it: schema B
# has workers return `value` as its own field rather than behind a label, and
# case_file.snap_to_ledger restores a ledger value on an exact-match hit.
EXTRACT_MAX_RETRIES = 5
EXTRACT_RETRY_BACKOFF = 10.0  # seconds; doubles each retry (10+20+40+80 — rides out ~2.5 min gateway outage)
# Statuses no amount of waiting will fix. The ladder above exists for gateway
# blips; re-asking a decommissioned model (410) or a bad key (401) just burns
# 150s per question before failing anyway.
EXTRACT_FATAL_STATUS = frozenset({400, 401, 403, 404, 410, 422})

# Longest of the 58 real BOTSv3 answers is 110 chars (a User-Agent string) and
# none contains a newline. 200 leaves nearly 2x headroom.
MAX_ANSWER_CHARS = 200
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.S | re.I)


def clean_completion(text: str | None) -> str:
    """The model's `content` reduced to a plausible scoreboard answer, or "".

    A reasoning model sometimes emits its chain of thought into `content`
    instead of the separate `reasoning_content` field, and when it does it
    spends the whole completion budget there. Q329 of test_20260915_174228
    submitted 4,487 characters of deliberation, truncated mid-sentence at the
    token cap, because nothing between the model and `scoreboard.submit` ever
    asked whether the string looked like an answer.

    Across the 86 extractions on record, every multi-line output (3/3) and
    every output longer than 110 chars (4/4) was that failure mode; none was a
    real answer. So the shape test is the whole guard: single line, non-empty,
    within MAX_ANSWER_CHARS. Returning "" rather than a best-effort salvage is
    deliberate - the last line of a truncated CoT reads like a plausible answer
    ("No", in Q329's case) while being pure noise, and the caller has a real
    worker value to fall back on.
    """
    t = _THINK_BLOCK.sub("", text or "").strip()
    if not t or "\n" in t or len(t) > MAX_ANSWER_CHARS:
        return ""
    return t


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
        self.client   = OpenAI(base_url=nim_base_url, api_key=nim_api_key,
                               http_client=resilient_http_client())
        self.base_url = nim_base_url   # for error attribution only
        self.model   = model
        self.tracker = tracker

    @traceable(run_type="llm", name="Extractor")
    def _complete(self, prompt: str):
        """The raw network call, wrapped so it shows as a span in LangSmith."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=EXTRACT_MAX_TOKENS,
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
                if getattr(exc, "status_code", None) in EXTRACT_FATAL_STATUS:
                    raise            # permanent — waiting cannot make it true
                if attempt == EXTRACT_MAX_RETRIES:
                    raise
                print(
                    f"[EXTRACTOR] attempt {attempt}/{EXTRACT_MAX_RETRIES} failed: "
                    f"{describe_llm_error(exc, 'Extractor', self.base_url)}. "
                    f"Retrying in {delay:.0f}s..."
                )
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
        raw   = resp.choices[0].message.content or ""
        clean = clean_completion(raw)
        if not clean and raw.strip():
            print(f"[EXTRACTOR] discarded a {len(raw)}-char completion that is "
                  f"not answer-shaped: {raw.strip()[:120]!r}...")
        return clean
