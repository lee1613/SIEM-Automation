#!/usr/bin/env python3
"""
One-line, source-naming descriptions of LLM API failures.

Every LLM call in the pipeline (SH, Senior, Extractor) reaches a different
provider, and `str(exc)` on an openai exception prints only the response body —
it never names the exception *type*, so a 429 and a 500 read identically in the
logs. These helpers put the type, the HTTP status, the component and the
provider host into a single greppable line.

The openai SDK ships the typed exception hierarchy (RateLimitError,
APITimeoutError, InternalServerError, ...) but no classifier, so this is ours.
It is deliberately description-only: retry/backoff is the SDK's job
(`max_retries=` / `timeout=`), except in extractor.py where the SDK's hard
8s MAX_RETRY_DELAY cap can't ride out a multi-minute NIM outage.
"""

from urllib.parse import urlsplit


def provider_of(base_url: str | None) -> str:
    """Host serving a client, for log attribution. No base_url -> OpenAI direct."""
    return urlsplit(base_url).hostname or base_url if base_url else "api.openai.com"


def describe_llm_error(exc: BaseException, component: str,
                       base_url: str | None = None) -> str:
    """'[LLM ERROR] Senior via api.vultrinference.com: RateLimitError (HTTP 429) - ...'

    component is the caller's role (SH / Senior / Extractor) so a failure line
    says which part of the pipeline died, not just that something did.
    """
    status = getattr(exc, "status_code", None)
    code   = f" (HTTP {status})" if status else ""
    return (f"[LLM ERROR] {component} via {provider_of(base_url)}: "
            f"{type(exc).__name__}{code} - {exc}")
