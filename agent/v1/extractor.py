#!/usr/bin/env python3
"""
Extractor agent for v1.

Strictly two jobs, kept deliberately simple (per the brief):
  1. Strip the orchestrator's prose down to the bare scoreboard answer
     (Llama-3.3-70B via NIM — reuses the v0 extract_clean_answer approach).
  2. Validate that bare answer against the question's `answer_guidance` format.
     It has NO ground truth, so "validate" = format / plausibility only:
       - non-empty
       - not an ESCALATE / "couldn't find" style non-answer
       - matches simple guidance hints (e.g. an IP, a number, an N-letter word)

Valid   -> caller submits ONCE to the scoreboard.
Invalid -> caller reports back to the SH (no submission), and the SH may retry (capped).
"""

import re

from openai import OpenAI


EXTRACT_MODEL = "meta/llama-3.3-70b-instruct"

_NON_ANSWER = re.compile(
    r"\b(escalate|i (?:could not|cannot|couldn't|don't|do not)\s|"
    r"unable to|not found|no (?:answer|data|result)|insufficient|unknown)\b",
    re.IGNORECASE,
)


class Extractor:
    def __init__(self, nim_api_key: str, nim_base_url: str,
                 model: str = EXTRACT_MODEL, tracker=None):
        self.client  = OpenAI(base_url=nim_base_url, api_key=nim_api_key)
        self.model   = model
        self.tracker = tracker

    def extract(self, question: str, guidance: str, verbose_answer: str) -> str:
        """Prose-strip to the bare answer the scoreboard expects."""
        guidance_line = f"Answer format guidance: {guidance}" if guidance else ""
        prompt = (
            f"Question: {question}\n\n"
            f"{guidance_line}\n\n"
            f"Agent's analysis: {verbose_answer}\n\n"
            "Based on the analysis above, state ONLY the exact answer with no "
            "explanation, no punctuation beyond what the format requires, and no "
            "surrounding text. If the answer is a list, use comma-separated values "
            "with no spaces. If a number, give only the number. Output nothing else."
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0,
        )
        if self.tracker and resp.usage:
            u = resp.usage
            cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
            self.tracker.add_nim_usage(
                self.model,
                inp=u.prompt_tokens or 0,
                cached=cached,
                out=u.completion_tokens or 0,
            )
        return (resp.choices[0].message.content or "").strip()

    def validate(self, clean_answer: str, guidance: str) -> tuple[bool, str]:
        """Format/plausibility check. Returns (is_valid, reason)."""
        a = (clean_answer or "").strip()
        if not a:
            return False, "empty answer"
        if _NON_ANSWER.search(a):
            return False, f"looks like a non-answer / escalation: {a!r}"

        g = (guidance or "").lower()

        # Length hint: "a six-letter word", "8 characters"
        m = re.search(r'\b(\d+)[- ]?(?:letter|character|char|digit)', g)
        if m:
            want = int(m.group(1))
            token = a.split()[0]
            if len(token) != want and len(a) != want:
                return False, f"expected {want} characters, got {len(a)} ({a!r})"

        # IP hint
        if "ip" in g and re.search(r'\baddress\b', g):
            if not re.search(r'\d{1,3}(?:\.\d{1,3}){3}', a):
                return False, f"guidance expects an IP address, got {a!r}"

        # Numeric hint
        if re.search(r'\b(?:a number|numeric|count|how many|integer)\b', g):
            if not re.search(r'\d', a):
                return False, f"guidance expects a number, got {a!r}"

        return True, "format ok"

    def process(self, question: str, guidance: str, verbose_answer: str) -> dict:
        """Convenience: extract + validate in one call."""
        clean = self.extract(question, guidance, verbose_answer)
        valid, reason = self.validate(clean, guidance)
        print(f"[EXTRACTOR] clean={clean!r}  valid={valid}  reason={reason}")
        return {"clean_answer": clean, "valid": valid, "reason": reason}
