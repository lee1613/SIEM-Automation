#!/usr/bin/env python3
"""
One-line, source-naming descriptions of LLM API failures.

Every LLM call in the pipeline (SH, Senior, exploration) reaches a different
provider, and `str(exc)` on an openai exception prints only the response body —
it never names the exception *type*, so a 429 and a 500 read identically in the
logs. These helpers put the type, the HTTP status, the component and the
provider host into a single greppable line.

The openai SDK ships the typed exception hierarchy (RateLimitError,
APITimeoutError, InternalServerError, ...) but no classifier, so this is ours.
It is deliberately description-only: retry/backoff is the SDK's job
(`max_retries=` / `timeout=`).
"""

import json
from urllib.parse import urlsplit

import httpx


def provider_of(base_url: str | None) -> str:
    """Host serving a client, for log attribution. No base_url -> OpenAI direct."""
    return urlsplit(base_url).hostname or base_url if base_url else "api.openai.com"


def describe_llm_error(exc: BaseException, component: str,
                       base_url: str | None = None) -> str:
    """'[LLM ERROR] Senior via api.vultrinference.com: RateLimitError (HTTP 429) - ...'

    component is the caller's role (SH / Senior / Exploration) so a failure line
    says which part of the pipeline died, not just that something did.
    """
    status = getattr(exc, "status_code", None)
    code   = f" (HTTP {status})" if status else ""
    return (f"[LLM ERROR] {component} via {provider_of(base_url)}: "
            f"{type(exc).__name__}{code} - {exc}")


# ── Non-compliant-provider safety net ────────────────────────────────────────

class _ErrorBodyTransport(httpx.BaseTransport):
    """Rewrite an error envelope served with HTTP 200 into a real 5xx.

    Some OpenAI-compatible providers report their own internal failures as
    `200 {"error": {...}}` with no `choices` (observed on Featherless:
    `{'type': 'server_error', 'code': 'internal_server_error'}`). A 200 is a
    success to the openai SDK, so `_should_retry` is never consulted and
    `max_retries` never fires; langchain later spots the `error` key and raises
    a bare `ValueError` (chat_models/base.py:1771) - seven layers above the
    retry machinery, untyped, and impossible to classify.

    Rewriting the status at the transport boundary makes the provider look
    compliant to everything above it: the SDK's own retry/backoff/jitter
    handles it, and anything that still fails surfaces as a typed
    `openai.InternalServerError` instead.

    Deliberately stricter than langchain's check - it requires `choices` to be
    absent/empty, so a provider returning a usable completion alongside a
    warning-shaped `error` field is left alone.
    """

    def __init__(self, inner: httpx.BaseTransport):
        self._inner = inner

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self._inner.handle_request(request)
        if response.status_code != 200:
            return response
        response.read()                      # buffer; non-streaming only
        try:
            body = json.loads(response.content)
        except (ValueError, UnicodeDecodeError):
            return response                  # not JSON - leave it alone
        if not (isinstance(body, dict) and body.get("error") and not body.get("choices")):
            return response
        print(f"[LLM ERROR] provider returned HTTP 200 with an error body "
              f"({request.url.host}); treating as 500 so the SDK retries: "
              f"{json.dumps(body.get('error'))[:200]}")
        return httpx.Response(500, json=body, request=request)


def resilient_http_client() -> httpx.Client:
    """httpx client that upgrades 200-with-error-body responses to 5xx.

    Pass to ChatOpenAI(http_client=...) / OpenAI(http_client=...). Sync only -
    this project never uses the async path.
    """
    return httpx.Client(transport=_ErrorBodyTransport(httpx.HTTPTransport()))
