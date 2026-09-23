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
import email
import hashlib
import io
import json
import os
import re
from typing import NamedTuple

# Priority order, as the operator specified (2026-09-23): Nemotron on NIM first, then
# gpt-5.4-mini on OpenAI when it fails. meta/llama-3.2-90b-vision-instruct was dropped
# after returning nothing but 504s. Both are priced at 0 (usage_tracker).
VISION_MODELS = (
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "gpt-5.4-mini",
)
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Beyond this the request is refused rather than sent. A senior that points the tool at a
# 40 MB object should be told so, not left waiting on a request that will fail anyway.
MAX_IMAGE_BYTES = 12 * 1024 * 1024

# One search is read to this many events: an SMTP session alone is several (greeting,
# commands, message), and the message is rarely the first Splunk returns.
MAX_EVENTS = 10
# Without a `name`, each image found is described in turn, up to this many.
MAX_IMAGES = 5

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


class Image(NamedTuple):
    label: str        # where it came from: a filename, a MIME type, or "#n"
    png: bytes        # re-encoded pixels only
    size: tuple       # (width, height)


# A base64 run shorter than this cannot hold a real image and is almost always a hash,
# a DKIM signature or a token.
_MIN_B64 = 200
_B64_RUN = re.compile(r"(?:[A-Za-z0-9+/]{4}\s*){%d,}[A-Za-z0-9+/=]{0,4}" % (_MIN_B64 // 4))
_HEX_RUN = re.compile(r"(?:[0-9a-fA-F]{2}){%d,}" % _MIN_B64)
_DATA_URI = re.compile(r"data:image/[\w.+-]+;base64,([A-Za-z0-9+/=\s]+)")


def pixels_only(raw: bytes) -> tuple[bytes, tuple] | None:
    """Magic-checked, decoded and re-encoded to PNG, or None if this is not an image.

    The re-encode is the guarantee the vision model sees pixels and nothing else: EXIF,
    comments, XMP and any bytes trailing the image are dropped, because only the
    decoded bitmap is written back out.
    """
    if not raw or len(raw) > MAX_IMAGE_BYTES or not sniff_type(raw):
        return None
    from PIL import Image as PILImage  # lazy: Pillow is only needed when a senior looks
    try:
        with PILImage.open(io.BytesIO(raw)) as im:
            im.load()
            out = io.BytesIO()
            im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB").save(out, "PNG")
            return out.getvalue(), im.size
    except Exception:                                  # noqa: BLE001 - not an image
        return None


def _texts(value) -> list[str]:
    """Every string in a JSON value, plus each list of strings joined back together:
    stream:smtp splits one RFC822 message across a list, and only the whole is MIME."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in _texts(v)]
    if isinstance(value, list):
        # The whole message first, so an image is labelled by its MIME filename
        # rather than by whichever chunk happened to hold its base64.
        whole = (["".join(value)] if len(value) > 1
                 and all(isinstance(v, str) for v in value) else [])
        return whole + [t for v in value for t in _texts(v)]
    return []


def _mime_images(text: str, notes: list) -> list[tuple[str, bytes]]:
    if "content-type:" not in text[:20000].lower():
        return []
    found = []
    for part in email.message_from_string(text).walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        notes.append(f"MIME part {ctype}" + (f" {part.get_filename()!r}"
                                             if part.get_filename() else ""))
        try:
            body = part.get_payload(decode=True) or b""
        except Exception:                              # noqa: BLE001
            continue
        found.append((part.get_filename() or ctype, body))
    return found


def _candidates(text: str, notes: list) -> list[tuple[str, bytes]]:
    """Every byte string in `text` that might be an image, by format."""
    found = _mime_images(text, notes)
    found += [("data: URI", _b64(m.group(1))) for m in _DATA_URI.finditer(text)]
    found += [("base64 run", _b64(m.group(0))) for m in _B64_RUN.finditer(text)]
    found += [("hex run", bytes.fromhex(m.group(0))) for m in _HEX_RUN.finditer(text)]
    # Raw bytes (an HTTP body carried as text): start at each signature in the text.
    blob = text.encode("latin-1", "ignore")
    for magic, mime in _MAGIC:
        if len(magic) >= 3:
            k = blob.find(magic)
            if k > 0:
                found.append((f"raw {mime} bytes", blob[k:]))
    return found


def _b64(s: str) -> bytes:
    try:
        return base64.b64decode("".join(s.split()), validate=False)
    except (binascii.Error, ValueError):
        return b""


def extract_images(texts: list[str]) -> tuple[list[Image], list[str]]:
    """Every distinct image in these texts, pixels only, plus notes on what else was
    there. `texts` is a Splunk event's `_raw` or a result row's field values; JSON is
    walked, MIME is parsed, base64/hex/data: runs are decoded, raw bytes are scanned.
    """
    notes, images, seen = [], [], set()
    for text in texts:
        try:
            parts = _texts(json.loads(text))
            notes.append("JSON event")
        except (ValueError, TypeError):
            parts = [text]
        for t in parts:
            for label, raw in _candidates(t, notes):
                got = pixels_only(raw)
                if got is None:
                    continue
                png, size = got
                key = hashlib.sha256(png).hexdigest()
                if key not in seen:
                    seen.add(key)
                    images.append(Image(label, png, size))
    for n, im in enumerate(images, start=1):
        if im.label in ("base64 run", "hex run", "data: URI") or im.label.startswith("raw "):
            images[n - 1] = im._replace(label=f"#{n} ({im.label})")
    return images, notes


def pick(images: list[Image], name: str) -> Image | None:
    """The one image to look at: the only one, or the one whose label contains `name`."""
    if name:
        hits = [im for im in images if name.lower() in im.label.lower()]
        return hits[0] if len(hits) == 1 else None
    return images[0] if len(images) == 1 else None


def listing(images: list[Image], notes: list) -> str:
    if images:
        return "Images found: " + "; ".join(
            f"{im.label} {im.size[0]}x{im.size[1]}" for im in images)
    seen = sorted(set(notes))[:15]
    return ("No image found. " + ("What the event does hold: " + ", ".join(seen)
                                  if seen else "The event held no MIME parts, no JSON, "
                                  "and no base64, hex or raw image bytes."))


def _is_nim(model: str) -> bool:
    return model.startswith(("nvidia/", "meta/"))


def _client(model: str):
    from openai import OpenAI  # imported lazily: this module is imported at startup
    env = "NIM_API_KEY" if _is_nim(model) else "OPENAI_API_KEY"
    key = os.getenv(env, "")
    if not key:
        raise RuntimeError(f"{env} is not set")
    return OpenAI(base_url=NIM_BASE_URL, api_key=key) if _is_nim(model) else OpenAI(api_key=key)


def describe(raw: bytes, mime: str, question: str, *, client=None,
             models=VISION_MODELS, tracker=None, qid: str = "",
             max_tokens: int = 300) -> str:
    """Ask a vision model one perceptual question about one image. Returns its answer.

    Tries each model in order and returns the first that answers; if all fail, raises
    with every failure named, because "the vision model is down" and "this model id is
    dead" need different fixes from the operator.
    """
    data_url = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    failures = []
    for model in models:
        # gpt-5 models reject max_tokens and spend part of the budget reasoning.
        limit = ({"max_tokens": max_tokens} if _is_nim(model)
                 else {"max_completion_tokens": max(max_tokens, 2000)})
        try:
            resp = (client or _client(model)).chat.completions.create(
                model=model, **limit,
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
                    model if _is_nim(model) else f"{model} (vision)",
                    getattr(u, "prompt_tokens", 0) or 0, 0,
                    getattr(u, "completion_tokens", 0) or 0,
                    qid=qid, role="vision")
        text = (resp.choices[0].message.content or "").strip()
        if text:
            return f"[{model}] {text}"
        failures.append(f"{model}: empty reply")
    raise RuntimeError("no vision model answered — " + " | ".join(failures))
