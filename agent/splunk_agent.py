#!/usr/bin/env python3
"""
SIEM Automation Agent — LangGraph stateful agent with two-stage tool dispatch.

Flow per tool call:
    agent ──► verify_node ──(approved)──► execute_node ──► agent
                           └─(rejected)──► agent  (self-correction)

verify_node runs before any tool executes and rejects calls that:
  - duplicate a prior failed call this turn (dedup guard)
  - reference a sourcetype not in the manifest
  - run_splunk_search without aggregation (| stats / | top / | rare)
  - run_splunk_search with a leading wildcard (=*value forces full scan)

execute_node only runs approved calls and records execution errors in seen_errors.

Model:  gpt-5.4 via OpenAI API
Brain:  LangGraph StateGraph + MemorySaver (cross-question statefulness)
Data:   Splunk Enterprise REST API (port 8089)
"""

import json
import os
import re
import sys
import textwrap
import threading
import uuid
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from splunk_client import SplunkClient

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SPLUNK_HOST    = os.getenv("SPLUNK_HOST", "https://localhost:8089")
SPLUNK_USER    = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS    = os.getenv("SPLUNK_PASS", "")
MODEL          = "gpt-5.4"
MAX_ITER       = 15
# Runaway guard, NOT a working limit, counted per invoke (one round of a live
# senior). A graph built WITHOUT a context window uses this flat cap: one-shot
# workers emit ~11-12K output tokens in total (measured over two Q216 runs), so
# 100K is ~8x typical. A graph built WITH one (v1.4 seniors) caps each round at
# what the window can still hold: window minus the context the round started
# with — see round_output_cap(). GLM-5.3 at 12 iterations spends ~16K per call,
# so a flat 100K cut off a working senior 7 steps into its round (Q216,
# 2026-09-18). Crossing the cap ends the worker with status="runaway".
OUTPUT_TOKEN_CAP = 100_000


def round_output_cap(context_window: int | None, prompt_tokens: int) -> int:
    """The runaway cap for one round: the room left in the window after the
    context the round started with, or the flat cap when no window is known."""
    if not context_window:
        return OUTPUT_TOKEN_CAP
    return max(context_window - prompt_tokens, 1)


def over_output_cap(state: dict) -> bool:
    """True once this round's output passed its cap (a runaway)."""
    return state.get("output_tokens", 0) > (state.get("output_cap") or OUTPUT_TOKEN_CAP)
# Per-request LLM timeout / retry budget. SDK defaults are 600s and 2 retries;
# 600s of silence on a stalled connection is the "process died but is still
# running" symptom. Retries use the SDK's own capped-exponential backoff.
LLM_TIMEOUT_S    = 300.0   # workers do long tool-heavy turns; GLM-5.3 exceeded 120s on long contexts (Q317, Q328)
LLM_MAX_RETRIES  = 3
MANIFEST_PATH  = os.path.join(os.path.dirname(__file__), "botsv3_fields.json")


def token_limit_kwargs(base_url: str | None, limit: int = 65536) -> dict:
    """ChatOpenAI kwargs that actually reach a non-OpenAI endpoint as a token cap.

    langchain-openai renames `max_tokens` to `max_completion_tokens` in the
    request body (1.3.2). OpenAI wants that name; Featherless silently ignores it
    and applies its own 4096 default, so every GLM-5.3 senior ran at 4096 rather
    than the 16384 this code asked for. Probed 2026-09-18 against
    zai-org/GLM-5.3 with a prompt long enough to overrun it:

        max_tokens=12000            -> 8211 completion tokens, finish "stop"
        max_completion_tokens=12000 -> 4096 completion tokens, finish "length"
        neither                     -> 4096 completion tokens, finish "length"

    `extra_body` is passed through untouched, so it is the only way to send the
    raw field. That cap cost the Q216 smoke runs every round report: a reasoning
    model spends the budget on hidden chain-of-thought and is cut off before it
    writes its `submit_finding` call, which reaches SH as a blank report.

    The default was 32768, GLM-5.3's ceiling as probed on Featherless. v1.4.2
    raises it to 65536: AI& accepts 65536 and 131072 without error (probed
    2026-09-20), and 32768 was being spent in full on hidden reasoning — two
    smoke3_r2 rounds came back finish_reason=length with 32768 output tokens and
    no tool call at all. This is a limit on ONE reply (reasoning + report), not on
    the 256K context it reads. Its successful calls run 47-2 667 output tokens, so
    this is headroom rather than a working budget. Runaway generation is bounded
    by OUTPUT_TOKEN_CAP across a worker's whole round, not here.
    """
    return ({"extra_body": {"max_tokens": limit}} if base_url
            else {"max_completion_tokens": limit})


def chat_llm(api_key: str, model: str, base_url: str | None, *,
             temperature: float = 0, http_client=None) -> ChatOpenAI:
    """A worker ChatOpenAI with the project's timeout, retries and token field.
    Explicit timeout + retries: the SDK default is 600s, so a stalled connection
    sits silent for 10 minutes per attempt and looks like a dead-but-running
    process. max_retries drives the SDK's own backoff - we add none of our own."""
    return ChatOpenAI(
        api_key=api_key, model=model, base_url=base_url, temperature=temperature,
        timeout=LLM_TIMEOUT_S, max_retries=LLM_MAX_RETRIES,
        # Optional: see llm_errors.resilient_http_client - upgrades a
        # 200-with-error-body into a 5xx so the SDK's retry engine fires.
        **({"http_client": http_client} if http_client else {}),
        **token_limit_kwargs(base_url),
    )


def iter_budget(points: int) -> int:
    """Iteration cap scaled by question value. High-value (>=500pt) questions
    get a larger tool-call budget; everything else gets the base MAX_ITER."""
    return 25 if (points or 0) >= 500 else MAX_ITER

# ── Field manifest helpers ─────────────────────────────────────────────────────

# Parallel Senior workers share this manifest file; the lock serialises
# read-modify-write cycles and the tmp+rename keeps readers from ever seeing
# a half-written file.
_MANIFEST_LOCK = threading.Lock()

def _load_manifest() -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_manifest(manifest: dict) -> None:
    tmp = MANIFEST_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp, MANIFEST_PATH)

def _manifest_get_source_types() -> str:
    manifest = _load_manifest()
    source_types = list(manifest.get("source_types", {}).keys())
    return json.dumps({"source_types": source_types, "count": len(source_types)})

def _manifest_expand(sourcetype: str, fields: list) -> None:
    with _MANIFEST_LOCK:
        manifest = _load_manifest()
        source_types = manifest.setdefault("source_types", {})
        entry = source_types.setdefault(sourcetype, {"fields": []})
        existing = set(entry.get("fields", []))
        new_fields = [f for f in fields if f not in existing]
        if new_fields:
            entry["fields"].extend(new_fields)
            _save_manifest(manifest)

def _search_keyword_in_manifest(keyword: str) -> list:
    """Return [{sourcetype, field}] for every field containing keyword.
    Skips entries where keyword exactly matches a sourcetype name."""
    manifest = _load_manifest()
    kw_lower = keyword.lower()
    matches = []
    for st_name, entry in manifest.get("source_types", {}).items():
        if kw_lower == st_name.lower():
            continue
        for field in entry.get("fields", []):
            if kw_lower in field.lower():
                matches.append({"sourcetype": st_name, "field": field})
    return matches

def _known_sourcetypes() -> set:
    return set(json.loads(_manifest_get_source_types())["source_types"])

# ── Result formatter ───────────────────────────────────────────────────────────

_STRIP = frozenset({
    "_bkt", "_cd", "_indextime", "_kv", "_si", "_sourcetype",
    "_serial", "_subsecond", "punct", "linecount", "splunk_server",
    "splunk_server_group", "timestartpos", "timeendpos",
})

def repair_tool_calls(response, tools: list):
    """Mend malformed tool calls before they reach the graph. GLM-5.3 on
    Featherless once emitted submit_finding with no name and no id (Q216 r8): the
    empty name failed to execute and ToolMessage(tool_call_id=None) crashed the
    worker. A missing id gets a fresh one; a missing name is recovered only when
    exactly one bound tool's parameters fit the arguments."""
    calls = getattr(response, "tool_calls", None) or []
    if all(tc.get("id") and tc.get("name") for tc in calls):
        return response
    fixed = []
    for tc in calls:
        tc = dict(tc)
        tc["id"] = tc.get("id") or f"call_{uuid.uuid4().hex[:12]}"
        if not tc.get("name"):
            keys = set(tc.get("args") or {})
            fits = [t.name for t in tools
                    if keys and keys <= set((t.args or {}).keys())]
            if len(fits) == 1:
                tc["name"] = fits[0]
        print(f"[Repaired tool call] name={tc.get('name')!r} id={tc['id']}")
        fixed.append(tc)
    return response.model_copy(update={"tool_calls": fixed})


CLIP_CHARS = 1_500


def _clip(v):
    if isinstance(v, list):
        return [_clip(x) for x in v]
    if isinstance(v, str) and len(v) > CLIP_CHARS:
        return f"{v[:CLIP_CHARS]}…[{len(v) - CLIP_CHARS} more chars cut]"
    return v


def _format_result(result: dict, keep_raw: bool = False) -> str:
    strip_set = _STRIP if keep_raw else (_STRIP | {"_raw"})
    if "results" in result:
        cleaned = [
            {k: v for k, v in row.items() if k not in strip_set}
            for row in result["results"]
        ]
        meta = dict(result.get("_meta", {}))
        total = int(meta.get("total_event_count") or 0)
        if total > len(cleaned):
            # A row cap is silent otherwise: the top-N of a sorted listing reads as
            # the whole set, and the rare value being hunted sits in the unseen rest.
            meta["truncated"] = (f"showing {len(cleaned)} of {total} rows, in the query's "
                                 f"own order — the other {total - len(cleaned)} were not "
                                 "returned, so this result says nothing about them. To "
                                 "reach what you need among them, don't page: narrow the "
                                 "query with what the question tells you.")
        payload = json.dumps({"results": cleaned, "meta": meta})
        if len(payload) > 12_000:
            # One mail or HTTP event can outgrow the whole budget alone, and halving
            # rows then returns none (Q217 smoke5_r1: "0 of 10 rows" on stream:smtp,
            # so the senior never saw attach_filename{}). Clip long values first:
            # every row keeps its field names and the start of each value.
            cleaned = [{k: _clip(v) for k, v in row.items()} for row in cleaned]
            meta["clipped"] = (f"values longer than {CLIP_CHARS} chars are cut; "
                               "extract what you need with rex/eval to read the rest")
            payload = json.dumps({"results": cleaned, "meta": meta})
        if len(payload) > 12_000:
            # Drop whole rows so the payload stays valid JSON (a raw byte slice
            # breaks both the model's evidence and the error/empty dedup guard).
            kept = list(cleaned)
            while kept and len(payload) > 12_000:
                kept = kept[:max(len(kept) // 2, 0)] if len(kept) > 1 else []
                meta["truncated"] = (f"showing {len(kept)} of {max(total, len(cleaned))} rows "
                                     "— the rest were not returned (too large); narrow "
                                     "the query to get a shorter answer")
                payload = json.dumps({"results": kept, "meta": meta})
        return payload
    return json.dumps(result)

# ── Graph state ────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages:             Annotated[list, add_messages]  # grows across questions
    seen_errors:          list   # [[name, args_str], ...] calls that errored — reset per question
    seen_empty:           list   # [[name, args_str], ...] calls that returned 0 results — reset per question
    step_count:           int    # agent-node calls — reset per question
    output_tokens:        int    # cumulative completion tokens this invoke — runaway guard
    output_cap:           int    # this invoke's runaway cap, set on its first call (0 = unset)
    last_prompt_tokens:   int    # prompt size of the most recent call — context-window tracking
    verification_passed:  bool   # set by verify_node, read by after_verify router
    intention_retries:    int    # tracks retries for missing Intention — reset per question

# ── Tool factory ───────────────────────────────────────────────────────────────

def make_tools(splunk: SplunkClient) -> list:
    """Return LangChain tool objects that close over the given Splunk client."""

    @tool
    def get_source_types() -> str:
        """Return the full list of all known sourcetypes from the local manifest.
        One of the two entry points for an investigation — get_sources is the
        other, and covers feeds this list cannot name.
        No Splunk call, instant response."""
        return _manifest_get_source_types()

    @tool
    def get_sources(sourcetype: str = "", keyword: str = "", top_n: int = 100) -> str:
        """List `source` values with their sourcetype and event count, busiest first.

        The SECOND discovery axis. A sourcetype can hide many distinct feeds:
        in BOTSv3, sourcetype=syslog contains Cisco NVM flow data that is only
        addressable as source="cisconvmflowdata". Whenever a sourcetype is too
        coarse to answer the question, call this to see what is inside it.

        - no arguments      -> the top sources across the whole index
        - sourcetype="..."  -> the distinct feeds hiding under that sourcetype
        - keyword="cisco"   -> sources whose events mention that keyword
        """
        result = splunk.get_sources(sourcetype=sourcetype, keyword=keyword,
                                    top_n=int(top_n))
        return _format_result(result)

    @tool
    def search_keyword(keyword: str) -> str:
        """Search for a keyword across all BOTSv3 fields.
        Returns every field (with its sourcetype path) whose name contains the keyword.
        If nothing is found in the local manifest, falls back to a live Splunk fieldsummary.
        Call this before run_splunk_search to discover which sourcetypes and fields
        are relevant to a keyword."""
        matches = _search_keyword_in_manifest(keyword)
        if matches:
            return json.dumps({"matches": matches, "count": len(matches), "source": "manifest"})
        # Strip quotes/pipes so a model-supplied keyword can't break out of the
        # SPL term and inject pipeline stages.
        keyword = re.sub(r'["|]', " ", keyword).strip()
        query = (
            f"index=botsv3 *{keyword}* | fields sourcetype *{keyword}*"
            f" | untable sourcetype field_name field_value"
            f" | stats count values(field_value) as example_values by field_name, sourcetype"
        )
        result = splunk.search(query=query, earliest="0", latest="now", max_results=50)
        try:
            for row in result.get("results", []):
                st = row.get("sourcetype")
                field = row.get("field_name")
                if st and field:
                    _manifest_expand(st, [field])
        except Exception:
            pass
        return _format_result(result)

    @tool
    def get_sourcetype_fields(sourcetype: str = "", index: str = "botsv3",
                               min_count: int = 1, source: str = "") -> str:
        """Run Splunk fieldsummary: every field with coverage %, distinct value
        count, and sample values. Scope it by `sourcetype`, by `source`, or both.
        Use when search_keyword returns no match for a feed you want to explore —
        including a `source` you found via get_sources."""
        result = splunk.get_sourcetype_fields(
            sourcetype=sourcetype, index=index, min_count=min_count, source=source
        )
        return _format_result(result)

    @tool
    def get_field_values(field: str, index: str = "botsv3",
                         sourcetype: str = "", top_n: int = 20,
                         source: str = "") -> str:
        """Count every distinct value of a field (optionally scoped to a sourcetype
        and/or a source) and return the `top_n` MOST FREQUENT, each with its count
        and percent. meta.total_event_count is how many distinct values exist.
        When that exceeds `top_n`, the rest were not returned — and they are the
        rarer values, which is often where the thing you are hunting sits.
        Use it to see what a field looks like. To find something specific among
        many values, use run_splunk_search and narrow with what the question
        tells you — filter on it, or group values into coarser units."""
        result = splunk.get_field_values(
            field=field, index=index, top_n=int(top_n), sourcetype=sourcetype,
            source=source
        )
        return _format_result(result)

    @tool
    def sample_events(sourcetype: str = "", index: str = "botsv3",
                      keyword: str = "", count: int = 3, source: str = "") -> str:
        """Return raw event content to discover embedded field names and log structure.
        Scope by `sourcetype` (a value from get_source_types), by `source` (a value
        from get_sources), or both — give at least one.
        `keyword` is an optional free-text filter within that scope — it narrows which events are
        returned but does NOT select the feed. Omit or leave blank to sample any events."""
        result = splunk.sample_events(
            sourcetype=sourcetype, index=index, keyword=keyword,
            count=min(count, 5), source=source
        )
        return _format_result(result, keep_raw=True)

    @tool
    def run_splunk_search(query: str, max_results: int = 50) -> str:
        """Execute an SPL search against Splunk.
        Scope every search to a feed you have confirmed exists — a `sourcetype=`
        from get_source_types, a `source=` from get_sources, or both. A source
        filter alone is valid and is sometimes the only way to reach the data.
        Must aggregate with | stats, | top, or | rare.
        No leading wildcards. Max 50 results — shape the query so its whole
        answer fits: filter on the question's clues, or group into coarser units."""
        result = splunk.search(
            query=query, earliest="0", latest="now", max_results=int(max_results)
        )
        return _format_result(result)

    @tool
    def get_raw_events(sourcetype: str = "", keyword: str = "", index: str = "botsv3",
                       limit: int = 10, source: str = "") -> str:
        """Return RAW event content (not aggregated) from a sourcetype, to read
        the actual text of emails, scripts, bash history, HTTP payloads, etc.
        Use when the answer is INSIDE the event content rather than a field value.
        `limit` is capped at 20 to protect context. Prefer a specific `keyword`."""
        n = max(1, min(int(limit), 20))
        result = splunk.sample_events(sourcetype=sourcetype, index=index,
                                      keyword=keyword, count=n, source=source)
        return _format_result(result, keep_raw=True)

    @tool
    def read_image(spl: str, question: str, name: str = "",
                   extract_spl: str = "") -> str:
        """LOOK AT an image carried inside an event, and answer one question about what
        it shows. Use this when the answer is a property of the PICTURE — a chart type,
        a colour, which word is biggest, what a screenshot says — and no text in the
        dataset states it.

        `spl`      a search for the event that carries the image (an email, an upload,
                   a response). Narrow it to that ONE event when you know which it is.
                   If you are not sure, a search matching a few events is fine: the
                   runner reads the whole _raw of up to 10 of them and finds every image
                   itself — MIME attachments, JSON fields, base64 or data: URIs, hex, or
                   raw bytes.
        `question` ONE narrow question about what is VISIBLE ("what kind of chart is
                   this?", "which word is in the largest font?"). Never hand it the
                   investigation's question — you do the reasoning, this only reports
                   what is on screen.
        `name`     part of the one image you mean (a filename, or "#2"). Without it,
                   every image found is shown to the vision model one by one and you get
                   one labelled answer per image; choosing between them is yours.
        `extract_spl` a fallback, only if the runner found no image: a search whose
                   output IS the encoded image (e.g. a rex or eval that isolates it).
                   The runner runs it and decodes it; its output never comes back here.

        The image is re-encoded to pixels only before the vision model sees it — no
        text, no metadata. It describes what it sees in ordinary language. Mapping that
        onto a product's own vocabulary is YOUR job, not its: if the answer must be a
        name from some tool's menu, ask about the VISIBLE PROPERTY that distinguishes
        those names (orientation, stacking, axis) and do the naming yourself.

        Nothing encoded enters this conversation: a call costs you one short answer."""
        # Imported here, not at module scope: agent/v1 is only on sys.path for the v1
        # runner, and a missing openai/NIM key must not break importing this module.
        try:
            import vision
        except ImportError:
            return "Image reading is not available in this deployment."

        def _texts_of(query: str) -> tuple[list, str]:
            """Every matching event, not the first: one SMTP session is several events
            and the one carrying the message is rarely the one Splunk returns first."""
            try:
                result = splunk.search(query, max_results=vision.MAX_EVENTS)
            except Exception as exc:                  # noqa: BLE001
                return [], f"Search failed: {type(exc).__name__}: {str(exc)[:200]}"
            if (result or {}).get("error"):
                return [], str(result["error"])[:300]
            rows = (result or {}).get("results") or []
            if not rows:
                return [], "That search returned no events."
            total = int(((result or {}).get("_meta") or {}).get("total_event_count")
                        or len(rows))
            texts = []
            for row in rows:
                if row.get("_raw"):
                    texts.append(str(row["_raw"]))
                else:
                    texts += [v if isinstance(v, str) else "\n".join(map(str, v))
                              for k, v in row.items() if not k.startswith("_")]
            return texts, f"read {len(rows)} of {total} matching events"

        texts, read = _texts_of(spl)
        if not texts:
            return read + " Narrow `spl` to the one event carrying the image."
        images, notes = vision.extract_images(texts)
        if not images and extract_spl:
            texts, more_read = _texts_of(extract_spl)
            if not texts:
                return f"extract_spl: {more_read}"
            images, more = vision.extract_images(texts)
            notes += ["(extract_spl) " + n for n in more]
        if not images:
            return (f"{vision.listing(images, notes)} ({read}.) If you know where the "
                    "image sits, narrow `spl` to that event or call again with "
                    "`extract_spl` isolating it.")
        if name:
            chosen = vision.pick(images, name)
            if chosen is None:
                return f"None matches {name!r}. {vision.listing(images, notes)}"
            images = [chosen]
        answers = []
        for im in images[:vision.MAX_IMAGES]:
            try:
                seen = vision.describe(im.png, "image/png", question)
            except RuntimeError as exc:
                seen = f"could not read it: {exc}"
            answers.append(f"({im.label}, {im.size[0]}x{im.size[1]}) {seen}")
        if len(images) > vision.MAX_IMAGES:
            answers.append(f"{len(images) - vision.MAX_IMAGES} more not shown — pass "
                           f"`name` to pick one. {vision.listing(images, notes)}")
        return "\n".join(answers)

    return [
        get_source_types,
        get_sources,
        search_keyword,
        get_sourcetype_fields,
        get_field_values,
        sample_events,
        run_splunk_search,
        get_raw_events,
        read_image,
    ]

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a SIEM analyst on the BOTSv3 dataset (Frothly, August 2018), querying Splunk Enterprise. All data is in index=botsv3; every SPL query starts with `index=botsv3`.

Before every tool call, write one line stating why you are making it and what you expect to learn:
  Intention: <reason>
A call without it is rejected.

FINDING THE FEED. Data is addressed on two axes, `sourcetype` and `source`. A generic sourcetype can hold several distinct feeds, each reachable only by its `source=` value, so when no sourcetype matches what the question names, look along the source axis with get_sources before concluding the data is absent. Search only a feed you have confirmed exists (get_source_types / get_sources). Before querying an unfamiliar feed, learn its fields and value formats with get_sourcetype_fields and sample_events.

SPL. Aggregate with | stats (the search tool rejects unaggregated queries); use IN for several literal values; filter after aggregation with | search; only trailing wildcards (value*), never leading ones; prefer exact tokens to substring wildcards. When the answer is text inside an event (an email body, a command line, a script), read it with get_raw_events instead of aggregating.

SUSPICION COMES FROM BEHAVIOUR, NOT NAMES. Never exclude a process, file or host because its name looks benign or well known, and do not add NOT filters that drop candidates by name. An unusual parent, network destination, volume or timing is what makes something suspicious.
"""
# ── Verification helpers ───────────────────────────────────────────────────────

def _verify_call(tc: dict, seen_errors: set, seen_empty: set) -> str | None:
    """Return a rejection reason string, or None if the call is approved."""
    name     = tc["name"]
    args     = tc["args"]
    args_str = json.dumps(args, sort_keys=True, separators=(",", ":"))
    call_key = (name, args_str)

    # 1. Dedup guard — identical call already errored this turn
    if call_key in seen_errors:
        return (
            "Rejected: this exact tool call already failed with an error this turn. "
            "Try different arguments or a different approach."
        )

    # 2. Empty-result guard — identical call already returned 0 results this turn
    if call_key in seen_empty:
        return (
            "Rejected: this exact tool call already returned zero results this turn. "
            "Change the sourcetype, field name, filter value, or search strategy."
        )

    # Remaining checks only apply to run_splunk_search
    if name != "run_splunk_search":
        return None

    query = args.get("query", "")

    # 3. Must start with index=botsv3
    if not re.match(r'\s*index\s*=\s*botsv3\b', query, re.IGNORECASE):
        return (
            "Rejected: every SPL query must begin with 'index=botsv3'. "
            "All BOTSv3 data lives in that index. "
            "Prepend 'index=botsv3' to the query."
        )

    # 4. Must have aggregation
    if not re.search(r'\|\s*(stats|top|rare)\b', query, re.IGNORECASE):
        return (
            "Rejected: SPL query must aggregate results with | stats, | top, or | rare. "
            "Add an aggregation command before submitting."
        )

    # 5. Sourcetype must be present and in the manifest.
    #    Accept both sourcetype=<value> and sourcetype IN (v1, v2, ...) — the
    #    system prompt itself recommends IN for multiple literal values.
    known = _known_sourcetypes()
    in_match = re.search(r'sourcetype\s+IN\s*\(([^)]*)\)', query, re.IGNORECASE)
    st_match = re.search(r'sourcetype\s*=\s*"?([^\s",|)]+)', query, re.IGNORECASE)
    if in_match:
        sts = [v.strip().strip('"\'') for v in in_match.group(1).split(",") if v.strip()]
        unknown = [s for s in sts if s not in known]
        if not sts or unknown:
            return (
                f"Rejected: sourcetype(s) {unknown or ['<empty>']} not in the field manifest. "
                f"Call get_source_types to see valid sourcetypes, then adjust the query."
            )
    elif st_match:
        st = st_match.group(1).strip('"\'')
        if st not in known:
            return (
                f"Rejected: sourcetype '{st}' is not in the field manifest. "
                f"Call get_source_types to see valid sourcetypes, then adjust the query."
            )
    else:
        return (
            "Rejected: every run_splunk_search query must include a sourcetype filter. "
            "Call get_source_types to find the right sourcetype, then add sourcetype=<value> to the query."
        )

    # 6. No leading wildcards (=*word forces sequential scan)
    if re.search(r'=\s*\*[^\s*|,)"\']', query):
        return (
            "Rejected: leading wildcard detected (=*value). "
            "Leading wildcards force a full sequential scan. "
            "Use a trailing wildcard (value*) or an exact value instead."
        )

    return None

# ── Graph factory ──────────────────────────────────────────────────────────────

def create_agent(api_key: str, splunk: SplunkClient, *,
                 model: str = MODEL, base_url: str | None = None,
                 extra_instructions: str = "", extra_tools: list | None = None,
                 max_iter: int = MAX_ITER, temperature: float = 0,
                 http_client=None, context_window: int | None = None):
    """Build and compile the LangGraph agent. Returns (graph, checkpointer).

    Graph topology:
        agent ──► verify_node ──(approved)──► execute_node ──► agent
                              └─(rejected)──► agent

    Args:
        model:              chat model id (e.g. "gpt-5.4", "gpt-5.4-mini",
                            "meta/llama-3.3-70b-instruct").
        base_url:           OpenAI-compatible endpoint. None → OpenAI; pass the NIM
                            base URL to run a Llama worker through the same code path.
        extra_instructions: appended to SYSTEM_PROMPT — used by the v1 worker pool to
                            inject the submit_finding contract without altering v0 behaviour.
        extra_tools:        additional LangChain tools appended after the Splunk tool
                            set — used by the v1 worker pool to give workers the
                            keyless `web_lookup` tool without changing v0's tool list.
        max_iter:           iteration cap for this graph instance. Defaults to the
                            module MAX_ITER; the v1 worker pool builds a second,
                            higher-budget graph (see `iter_budget`) for >=500pt
                            questions. All in-closure iteration-cap checks use this
                            local value, not the module constant.
        temperature:        sampling temperature (default 0 — deterministic;
                            the v1 pool passes 0.3 for self-consistency
                            sampling of metrics tasks).
    """
    tools    = make_tools(splunk)
    if extra_tools:
        tools = tools + list(extra_tools)
    tool_map = {t.name: t for t in tools}

    llm = chat_llm(api_key, model, base_url, temperature=temperature, http_client=http_client)
    model_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    # Used when the iteration cap is hit. Search tools are withdrawn so the
    # worker cannot start another hunt, but any TERMINAL tool the caller
    # supplied stays bound - otherwise a capped worker has no way to report
    # except prose, and prose is exactly what the structured contract exists to
    # avoid. v0 passes no extra_tools, so for it this is still a bare model.
    _terminal  = [t for t in (extra_tools or []) if getattr(t, "name", "") == "submit_finding"]
    model_bare = llm.bind_tools(_terminal, parallel_tool_calls=False) if _terminal else llm

    prompt_text = SYSTEM_PROMPT
    if extra_instructions:
        prompt_text = SYSTEM_PROMPT + "\n" + extra_instructions
    system_msg = SystemMessage(content=prompt_text)

    def _print_state(label: str, state: AgentState) -> None:
        msgs = state.get("messages", [])
        print(
            f"\n[STATE:{label}]"
            f"  step={state.get('step_count', 0)}"
            f"  msgs={len(msgs)}"
            f"  errors={len(state.get('seen_errors', []))}"
            f"  empty={len(state.get('seen_empty', []))}"
            f"  verified={state.get('verification_passed', '?')}"
        )
        last = msgs[-1] if msgs else None
        if last:
            kind = type(last).__name__
            tcs  = getattr(last, "tool_calls", None)
            if tcs:
                for tc in tcs:
                    args_str = json.dumps(tc['args'], separators=(',', ':'))
                    print(f"  last_msg: {kind} -> tool_call: {tc['name']}({args_str})")
            else:
                snippet = (getattr(last, "content", "") or "")[:120].replace("\n", " ")
                print(f"  last_msg: {kind} -> {snippet!r}")

    # ── Node: agent ────────────────────────────────────────────────────────────
    def agent_node(state: AgentState) -> dict:
        step = state.get("step_count", 0) + 1
        _print_state("agent_in", state)
        msgs = [system_msg] + list(state["messages"])

        if step > max_iter:
            print("[Max iterations reached — forcing final answer]")
            msgs = msgs + [HumanMessage(
                "You have reached the maximum number of tool calls and the search "
                "tools are now withdrawn. Do NOT invent a value. Report what you "
                "actually have: if you have a credible candidate use status "
                "'partial' and put it in `value`; if you do not, leave `value` "
                "empty, use status 'partial' or 'failed', and put what you learned "
                "and what you eliminated in `notes` and `ruled_out`. Use status "
                "'too_big' if the task needs narrowing to be answerable at all."
            )]
            response = model_bare.invoke(msgs)
        else:
            response = model_with_tools.invoke(msgs)

        # An empty reply (no text, no tool call) ends the round with nothing to
        # report - the provider failed to parse a tool call, or reasoning ate the
        # token budget. GLM-5.3 on Featherless did this twice in Q216's smoke test
        # and both rounds reached SH blank. Ask once more, submit_finding only.
        wasted_out = 0
        if _terminal and not response.content and not getattr(response, "tool_calls", None):
            meta = getattr(response, "response_metadata", None) or {}
            wasted_out = int((getattr(response, "usage_metadata", None) or {}).get("output_tokens", 0))
            print(f"[Empty reply] finish_reason={meta.get('finish_reason')} "
                  f"output_tokens={wasted_out} — asking once more for submit_finding")
            response = model_bare.invoke(msgs + [HumanMessage(
                "Your last reply was empty: no text and no tool call. Call "
                "submit_finding now with what you have so far. Do not invent a "
                "value - an empty `value` with honest `notes` is fine."
            )])

        response = repair_tool_calls(response, tools)

        if response.content:
            tag = "[Agent thinking]" if getattr(response, "tool_calls", None) else "[Agent response]"
            print(f"\n{tag}\n{response.content}\n")

        um = getattr(response, "usage_metadata", None) or {}
        out_total = state.get("output_tokens", 0) + wasted_out + int(um.get("output_tokens", 0))
        # The prompt size of the call just made IS this thread's current context
        # size. v1.4 projects a round's growth off it to decide whether to
        # compact before working (spec §6); nothing else reads it.
        prompt_tokens = int(um.get("input_tokens", 0))
        cap = state.get("output_cap") or round_output_cap(context_window, prompt_tokens)
        if out_total > cap:
            print(f"[RUNAWAY] {out_total:,} output tokens > cap {cap:,} "
                  "— stopping this worker")
        return {"messages": [response], "step_count": step, "output_cap": cap,
                "output_tokens": out_total, "last_prompt_tokens": prompt_tokens}

    # ── Node: verify ───────────────────────────────────────────────────────────
    def verify_node(state: AgentState) -> dict:
        _print_state("verify_in", state)
        """Pre-flight check: inspect proposed tool calls before execution.

        Approves  → sets verification_passed=True, adds nothing to messages.
        Rejects   → sets verification_passed=False, injects ToolMessage(error)
                    for every rejected call so the agent can self-correct.
        """
        seen_errors = {(e[0], e[1]) for e in state.get("seen_errors", [])}
        seen_empty  = {(e[0], e[1]) for e in state.get("seen_empty",  [])}
        last        = state["messages"][-1]
        rejections  = []

        # ── Intention protocol soft check ─────────────────────────────────
        intention_missing = not last.content or "intention" not in last.content.lower()
        intention_retries = state.get("intention_retries", 0)

        if intention_missing and intention_retries < 2:
            for tc in last.tool_calls:
                rejections.append(ToolMessage(
                    content=json.dumps({"error":
                        "Rejected: You must state your reasoning before calling any tool. "
                        "Write an 'Intention: <why you are making this call>' line, "
                        "then repeat your tool call."}),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
            print(f"[Verify REJECT] No Intention stated (retry {intention_retries + 1}/2)")
            return {"messages": rejections, "verification_passed": False,
                    "intention_retries": intention_retries + 1}

        for tc in last.tool_calls:
            reason = _verify_call(tc, seen_errors, seen_empty)
            if reason:
                print(f"[Verify REJECT] {tc['name']} — {reason}")
                rejections.append(ToolMessage(
                    content=json.dumps({"error": reason}),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
            else:
                print(f"[Verify OK]     {tc['name']}")

        if rejections:
            return {"messages": rejections, "verification_passed": False}
        return {"verification_passed": True}

    # ── Node: execute ──────────────────────────────────────────────────────────
    def execute_node(state: AgentState) -> dict:
        """Run verified tool calls; record execution errors and empty results."""
        _print_state("execute_in", state)
        seen_errors = {(e[0], e[1]) for e in state.get("seen_errors", [])}
        seen_empty  = {(e[0], e[1]) for e in state.get("seen_empty",  [])}
        new_errors  = [list(e) for e in seen_errors]
        new_empty   = [list(e) for e in seen_empty]
        last        = state["messages"][-1]
        results     = []

        for tc in last.tool_calls:
            args_str = json.dumps(tc["args"], sort_keys=True, separators=(",", ":"))
            call_key  = (tc["name"], args_str)

            try:
                raw    = tool_map[tc["name"]].invoke(tc["args"])
                output = raw if isinstance(raw, str) else json.dumps(raw)
            except Exception as exc:
                output = json.dumps({"error": str(exc)})

            try:
                parsed = json.loads(output)
                if "error" in parsed:
                    new_errors.append(list(call_key))
                elif (parsed.get("results") is not None
                      and len(parsed["results"]) == 0):
                    new_empty.append(list(call_key))
            except Exception:
                pass

            print(f"[Execute] {tc['name']}({args_str})")
            print(f"          -> {output}\n")

            results.append(ToolMessage(
                content=output,
                tool_call_id=tc["id"],
                name=tc["name"],
            ))

        return {"messages": results, "seen_errors": new_errors, "seen_empty": new_empty}

    # ── Routers ────────────────────────────────────────────────────────────────
    def should_continue(state: AgentState) -> str:
        """Route agent output: to verify if tool calls present, else END."""
        if state.get("step_count", 0) > max_iter:
            return END
        if over_output_cap(state):
            return END          # runaway — _run turns this into status="runaway"
        last = state["messages"][-1]
        calls = getattr(last, "tool_calls", None)
        if calls and all(tc["name"] == "submit_finding" for tc in calls):
            # The finding is read off this message (finding.parse_finding) and the
            # caller closes the dangling call; running it would only buy one more
            # paid model turn after the worker has already reported.
            return END
        if calls:
            return "verify"
        return END

    def after_verify(state: AgentState) -> str:
        """Route verify output: to execute if approved, back to agent if rejected."""
        return "execute" if state.get("verification_passed") else "agent"

    # ── Assemble graph ─────────────────────────────────────────────────────────
    checkpointer = MemorySaver()

    g = StateGraph(AgentState)
    g.add_node("agent",   agent_node)
    g.add_node("verify",  verify_node)
    g.add_node("execute", execute_node)

    g.set_entry_point("agent")
    g.add_conditional_edges("agent",  should_continue,
                            {"verify": "verify", END: END})
    g.add_conditional_edges("verify", after_verify,
                            {"execute": "execute", "agent": "agent"})
    g.add_edge("execute", "agent")

    return g.compile(checkpointer=checkpointer), checkpointer


# ── Public run API ─────────────────────────────────────────────────────────────

def run_agent(graph, question: str, thread_id: str = "default") -> str:
    """Invoke the agent on one question and return the final answer string.

    Same thread_id across questions → model sees full prior Q&A history.
    Fresh thread_id → clean conversation.
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_ITER * 4,
    }
    result = graph.invoke(
        {
            "messages":            [HumanMessage(content=question)],
            "seen_errors":         [],
            "seen_empty":          [],
            "step_count":          0,
            "output_tokens":       0,
            "output_cap":          0,
            "last_prompt_tokens":  0,
            "verification_passed": False,
            "intention_retries":   0,
        },
        config=config,
    )
    last = result["messages"][-1]
    return getattr(last, "content", "") or ""


def run_agent_traced(graph, question: str, thread_id: str = "default",
                     *, run_name: str = "", tags: list | None = None,
                     metadata: dict | None = None, tracker=None,
                     max_iter: int = MAX_ITER) -> tuple[str, dict]:
    """Like run_agent but also returns the full final AgentState.

    Extra kwargs (run_name, tags, metadata) are forwarded to LangSmith when
    LANGSMITH_TRACING is enabled, making each worker trace identifiable.
    tracker, if provided, receives on_llm_end callbacks for token counting.
    max_iter must match the iteration cap the graph was built with (see
    `create_agent(max_iter=...)`/`iter_budget`) so recursion_limit scales too —
    otherwise a >=500pt worker graph (max_iter=25) would hit LangGraph's
    recursion ceiling before its own iteration cap fires.
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_iter * 4,
    }
    if run_name:
        config["run_name"] = run_name
    if tags:
        config["tags"] = tags
    if metadata:
        config["metadata"] = metadata
    if tracker is not None:
        config["callbacks"] = [tracker]

    result = graph.invoke(
        {
            "messages":            [HumanMessage(content=question)],
            "seen_errors":         [],
            "seen_empty":          [],
            "step_count":          0,
            "output_tokens":       0,
            "output_cap":          0,
            "last_prompt_tokens":  0,
            "verification_passed": False,
            "intention_retries":   0,
        },
        config=config,
    )
    last   = result["messages"][-1]
    answer = getattr(last, "content", "") or ""
    return answer, result


# ── CLI entry point ────────────────────────────────────────────────────────────

def _connect_splunk() -> SplunkClient:
    if not SPLUNK_PASS:
        raise SystemExit("SPLUNK_PASS not set — copy .env.example to .env.")
    print(f"Connecting to Splunk at {SPLUNK_HOST} as '{SPLUNK_USER}'...")
    c = SplunkClient(SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS)
    print("Connected.\n")
    return c


def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY not set.")

    splunk    = _connect_splunk()
    graph, _  = create_agent(OPENAI_API_KEY, splunk)
    thread_id = "interactive"

    if len(sys.argv) > 1:
        query  = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        answer = run_agent(graph, query, thread_id=thread_id)
        print("\n" + "=" * 60)
        print(answer)
        return

    print(f"SIEM Agent ready  [model: {MODEL}  |  LangGraph + verify gate  |  OpenAI]")
    print("Type your question or 'exit' to quit. Context persists across turns.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break
        answer = run_agent(graph, query, thread_id=thread_id)
        print("\nAgent:", textwrap.fill(answer, width=100, subsequent_indent="       "))
        print()


if __name__ == "__main__":
    main()
