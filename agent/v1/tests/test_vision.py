"""v1.4.4: reading an image that exists only as base64 in a Splunk field.

Two of the five questions in the standing hard set are decode-and-look questions, and
the official hints say so: "You will need to find a site to decode the base64 to a
viewable image." The network call is not exercised here — `describe` takes an injectable
client so the decode, the type sniff, the refusals and the fallback are all testable
without touching NIM.
"""
import base64

import pytest
from vision import (
    MAX_IMAGE_BYTES,
    VISION_MODELS,
    decode_field,
    describe,
    sniff_type,
)

# Smallest valid files of each type; synthetic, not from the dataset.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32


def test_the_type_comes_from_the_bytes_not_the_filename():
    """A MIME header is whatever the sender wrote, and this dataset has already been
    seen carrying a base64-encoded attach_filename."""
    assert sniff_type(PNG) == "image/png"
    assert sniff_type(JPEG) == "image/jpeg"
    assert sniff_type(b"GIF89a....") == "image/gif"
    assert sniff_type(b"not an image at all") == ""


def test_a_field_wrapped_across_mime_lines_still_decodes():
    """Splunk hands the field back with the original MIME part's line wrapping, which
    b64decode rejects unless it is stripped first."""
    wrapped = "\n".join(
        base64.b64encode(PNG).decode()[i:i + 8]
        for i in range(0, len(base64.b64encode(PNG).decode()), 8))
    raw, mime = decode_field(wrapped)
    assert raw == PNG and mime == "image/png"


def test_an_empty_field_says_which_thing_to_check():
    with pytest.raises(ValueError, match="empty"):
        decode_field("   ")


def test_bytes_that_are_not_an_image_are_refused_not_sent():
    with pytest.raises(ValueError, match="not an image"):
        decode_field(base64.b64encode(b"just some text here").decode())


def test_an_oversized_image_is_refused_before_the_request():
    """A senior pointing this at a 40MB object should be told so, not left waiting on a
    request that fails anyway."""
    big = base64.b64encode(b"\xff\xd8\xff" + b"\x00" * MAX_IMAGE_BYTES).decode()
    with pytest.raises(ValueError, match="over the"):
        decode_field(big)


class _Reply:
    def __init__(self, text):
        self.choices = [type("C", (), {"message": type("M", (), {"content": text})()})()]
        self.usage = None


class _Client:
    """Fails for every model in `dead`, answers for the rest."""
    def __init__(self, text="a column chart", dead=()):
        self.text, self.dead, self.seen = text, set(dead), []

        outer = self

        class _Completions:
            def create(self, *, model, messages, max_tokens):
                outer.seen.append((model, messages))
                if model in outer.dead:
                    raise RuntimeError("404 model not found")
                return _Reply(outer.text)

        self.chat = type("Chat", (), {"completions": _Completions()})()


def test_the_image_reaches_the_model_as_a_data_url_with_the_question():
    c = _Client()
    out = describe(PNG, "image/png", "what kind of chart is this?", client=c)
    assert "column chart" in out
    model, messages = c.seen[0]
    assert model == VISION_MODELS[0], "the operator's priority order is honoured"
    parts = messages[0]["content"]
    assert parts[0]["text"] == "what kind of chart is this?"
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_a_dead_model_id_falls_through_to_the_next():
    """NIM lists far more models than it will serve, and a dead name returns a bare 404
    with no deprecation signal — so one id is not enough."""
    c = _Client(dead=[VISION_MODELS[0]])
    out = describe(PNG, "image/png", "what is this?", client=c)
    assert VISION_MODELS[1] in out
    assert [m for m, _ in c.seen] == list(VISION_MODELS[:2])


def test_when_nothing_answers_every_failure_is_named():
    """'the vision endpoint is down' and 'this model id is dead' need different fixes."""
    c = _Client(dead=VISION_MODELS)
    with pytest.raises(RuntimeError) as exc:
        describe(PNG, "image/png", "what is this?", client=c)
    for model in VISION_MODELS:
        assert model in str(exc.value)
