#!/usr/bin/env python3
"""
Keyless web lookup tool for external knowledge the BOTSv3 dataset can't answer
(vendor threat severity/dates, CVE identification). Uses DuckDuckGo's HTML
endpoint and returns the top result snippets as plain text.

Degrades gracefully: any network/parse failure returns a clear string rather
than raising, so offline runs and unit tests never break the worker graph.
"""

from __future__ import annotations

import re
import html

import requests
from langchain_core.tools import tool

_DDG = "https://html.duckduckgo.com/html/"
_SNIPPET = re.compile(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
                      re.IGNORECASE | re.DOTALL)


def _fetch(query: str) -> str:
    resp = requests.post(_DDG, data={"q": query},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    return resp.text


def _clean(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


@tool
def web_lookup(query: str) -> str:
    """Look up EXTERNAL knowledge not in the Splunk dataset — e.g. a vendor's
    published threat severity/date, or which CVE matches an exploit technique.
    Returns the top web result snippets. Use ONLY for facts outside BOTSv3."""
    try:
        raw = _fetch(query)
    except Exception as exc:
        return f"web_lookup unavailable ({exc}); answer from dataset evidence instead."
    snippets = [_clean(m) for m in _SNIPPET.findall(raw)]
    snippets = [s for s in snippets if s][:5]
    if not snippets:
        return "web_lookup: no result snippets found."
    return " | ".join(snippets)
