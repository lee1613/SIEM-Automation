#!/usr/bin/env python3
"""Read an image that only exists as base64 inside a Splunk field (v1.4.4).

WHY THIS EXISTS. Two of the five questions in the standing hard set are decode-and-look
questions, and the official BOTSv3 hints say so outright:

    Q217 hint 3 / Q329 hint 3 — "You will need to find a site to decode the base64 to a
    viewable image. CyberChef is a good one!"

Q217 asks which kind of Splunk visualization is in Bud's first attachment; Q329 asks
which word in an uploaded file is in a much larger font than the rest. Both properties
are properties of rendered pixels. No text channel in the dataset encodes them — a
senior walked the MIME headers, the HTML body and the alt text of Q217's `image001.jpg`
and proved it, and another proved the file appears in ZERO events across osquery,
Sysmon, WinEventLog and stream:http because it never touched a disk. The bytes are
present; nothing here could look at them.

THE CONSTRAINT THAT DECIDES THE DESIGN. `attach_content` for Q217's image001.jpg is
~226 KB of base64. A tool that takes the base64 as an ARGUMENT would force the senior to
carry all of it through its own context to call the tool, and carry it again in the
transcript afterwards - far more expensive than the question is worth, and it would
crowd out the senior's actual working memory.

So the tool takes an SPL LOCATOR, never the bytes. It runs the search itself, pulls the
field server-side, decodes, sends the image to a vision model, and returns only the
model's short text answer. THE BASE64 NEVER ENTERS ANY AGENT'S CONTEXT. The senior pays
for one sentence of tool output; the image is seen by a model that costs nothing.

ON WHETHER THE VISION MODEL HAS TO REASON WELL. It does not have to solve the question -
it has to describe what it sees. The senior keeps the case, the constraints and the
judgement; it asks a narrow perceptual question ("what chart type is this", "which word
is largest") and decides for itself what the answer means. That division is deliberate:
a vision model asked to answer a CTF question would guess, and a guess in a tool result
is indistinguishable from evidence. Keep the question perceptual.
"""

from __future__ import annotations

import base64
import binascii
import os

# Priority order, as the operator specified. The first that answers is used; a NIM model
# that is listed but not servable returns a bare 404, so "it is in models.list()" is not
# evidence it works (see usage_tracker's NIM notes) - hence a fallback rather than one id.
VISION_MODELS = (
    "meta/llama-3.2-90b-vision-instruct",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
)
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Beyond this the request is refused rather than sent. A senior that points the tool at a
# 40 MB object should be told so, not left waiting on a request that will fail anyway.
MAX_IMAGE_BYTES = 12 * 1024 * 1024

_MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
]


def sniff_type(raw: bytes) -> str:
    """The media type from the bytes themselves, never from the filename.

    A MIME header is whatever the sender wrote; `attach_filename` in this dataset has
    already been seen base64-encoded. The magic number is the only honest source.
    """
    for magic, mime in _MAGIC:
        if raw.startswith(magic):
            return mime
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return ""


def decode_field(value: str) -> tuple[bytes, str]:
    """Base64 in a Splunk field -> (bytes, media type). Raises ValueError with a reason.

    Splunk fields arrive with the line wrapping and whitespace of the original MIME
    part, which `b64decode` rejects unless it is stripped; `validate=False` also lets the
    stray header text that sometimes leads a raw field be skipped rather than fatal.
    """
    cleaned = "".join((value or "").split())
    if not cleaned:
        raise ValueError("the field is empty - check the field name and that the search "
                         "returned the event you meant")
    try:
        raw = base64.b64decode(cleaned, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"the field is not base64: {exc}") from None
    if not raw:
        raise ValueError("the field decoded to nothing")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError(f"the image is {len(raw):,} bytes, over the "
                         f"{MAX_IMAGE_BYTES:,} limit")
    mime = sniff_type(raw)
    if not mime:
        raise ValueError("the decoded bytes are not an image this can read (no JPEG, "
                         "PNG, GIF, BMP or WEBP signature)")
    return raw, mime


def _client():
    from openai import OpenAI  # imported lazily: this module is imported at startup
    key = os.getenv("NIM_API_KEY", "")
    if not key:
        raise RuntimeError("NIM_API_KEY is not set")
    return OpenAI(base_url=NIM_BASE_URL, api_key=key)


def describe(raw: bytes, mime: str, question: str, *, client=None,
             models=VISION_MODELS, tracker=None, qid: str = "",
             max_tokens: int = 300) -> str:
    """Ask a vision model one perceptual question about one image. Returns its answer.

    Tries each model in order and returns the first that answers; if all fail, raises
    with every failure named, because "the vision model is down" and "this model id is
    dead" need different fixes from the operator.
    """
    client = client or _client()
    data_url = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    failures = []
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model, max_tokens=max_tokens,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]}])
        except Exception as exc:                      # noqa: BLE001 - reported, not swallowed
            failures.append(f"{model}: {type(exc).__name__}: {str(exc)[:160]}")
            continue
        if tracker is not None:
            u = getattr(resp, "usage", None)
            if u is not None:
                tracker.add_nim_usage(
                    model, getattr(u, "prompt_tokens", 0) or 0, 0,
                    getattr(u, "completion_tokens", 0) or 0,
                    qid=qid, role="vision")
        text = (resp.choices[0].message.content or "").strip()
        if text:
            return f"[{model}] {text}"
        failures.append(f"{model}: empty reply")
    raise RuntimeError("no vision model answered — " + " | ".join(failures))
