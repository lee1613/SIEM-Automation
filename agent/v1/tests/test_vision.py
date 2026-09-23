"""v1.4.4: reading an image that exists only as base64 in a Splunk field.

Two of the five questions in the standing hard set are decode-and-look questions, and
the official hints say so: "You will need to find a site to decode the base64 to a
viewable image." The network call is not exercised here — `describe` takes an injectable
client so the decode, the type sniff, the refusals and the fallback are all testable
without touching NIM.
"""
import base64
import io
import json

import pytest
from vision import (
    MAX_IMAGE_BYTES,
    VISION_MODELS,
    describe,
    extract_images,
    listing,
    pick,
    pixels_only,
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


def _jpeg(text_in_metadata: bytes = b"", color=(200, 30, 30)) -> bytes:
    """A real 40x20 JPEG made here, not a dataset artifact, optionally carrying text in
    a COM segment - the kind of non-pixel payload the model must never see."""
    from PIL import Image as PILImage
    out = io.BytesIO()
    PILImage.new("RGB", (40, 20), color).save(out, "JPEG")
    data = out.getvalue()
    if text_in_metadata:
        seg = b"\xff\xfe" + (len(text_in_metadata) + 2).to_bytes(2, "big") + text_in_metadata
        data = data[:2] + seg + data[2:]
    return data


def _wrapped(b: bytes, width: int = 76) -> str:
    s = base64.b64encode(b).decode()
    return "\r\n".join(s[i:i + width] for i in range(0, len(s), width))


def _email(img: bytes, filename: str = "chart.jpg") -> str:
    return ("Content-Type: multipart/related; boundary=\"B\"\r\n\r\n--B\r\n"
            "Content-Type: text/html\r\n\r\n<p>see attached</p>\r\n--B\r\n"
            f"Content-Type: image/jpeg; name=\"{filename}\"\r\n"
            f"Content-Disposition: inline; filename=\"{filename}\"\r\n"
            "Content-Transfer-Encoding: base64\r\n\r\n"
            + _wrapped(img) + "\r\n--B--\r\n")


def test_a_mime_attachment_split_across_a_json_list_is_found_by_filename():
    """stream:smtp carries one RFC822 message as a JSON list of chunks; only the
    rejoined whole parses as MIME."""
    msg = _email(_jpeg())
    event = json.dumps({"content": [msg[k:k + 90] for k in range(0, len(msg), 90)],
                        "subject": "hello"})
    images, _ = extract_images([event])
    assert [im.label for im in images] == ["chart.jpg"]
    assert images[0].size == (40, 20)


def test_what_reaches_the_model_is_pixels_only():
    """Text riding inside the image file is dropped by the re-encode."""
    png, size = pixels_only(_jpeg(b"THE ANSWER IS 42"))
    assert size == (40, 20) and png.startswith(b"\x89PNG")
    assert b"THE ANSWER" not in png


def test_a_data_uri_a_hex_run_and_raw_bytes_are_all_found():
    img = _jpeg()
    for text in (f'<img src="data:image/jpeg;base64,{base64.b64encode(img).decode()}">',
                 "blob=" + img.hex(),
                 "HTTP/1.1 200 OK\r\n\r\n" + img.decode("latin-1")):
        images, _ = extract_images([text])
        assert len(images) == 1, text[:40]


def test_bytes_that_are_not_an_image_are_never_sent():
    assert pixels_only(b"\xff\xd8\xff but not really a jpeg") is None
    assert pixels_only(b"just some text here") is None


def test_an_oversized_image_is_refused_before_the_request():
    assert pixels_only(b"\xff\xd8\xff" + b"\x00" * MAX_IMAGE_BYTES) is None


def test_two_images_need_a_name_and_nothing_found_lists_what_is_there():
    images, _ = extract_images([_email(_jpeg(), "a.jpg"), _email(_jpeg(color=(0, 0, 255)), "b.jpg")])
    assert len(images) == 2
    assert pick(images, "") is None, "never guess between two images"
    assert pick(images, "b.jpg").label == "b.jpg"
    images, notes = extract_images([_email(b"not an image", "c.jpg")])
    assert images == [] and "MIME part image/jpeg 'c.jpg'" in listing(images, notes)


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
            def create(self, *, model, messages, **limit):
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


def test_the_tool_reads_every_matching_event_not_just_the_first(monkeypatch):
    """v1.4.4_smoke5_r1 Q217: one SMTP flow_id matched 5 events (greeting, commands,
    message) and the tool read only the first, a 502-byte protocol record - so a search
    that did name the right session found nothing. Unsure which event holds the image,
    the senior may match several; every image in them goes to the vision model in turn."""
    from unittest.mock import MagicMock

    import splunk_agent
    import vision
    fake = MagicMock()
    fake.search.return_value = {
        "results": [{"_raw": json.dumps({"method": "QUIT"})},
                    {"_raw": json.dumps({"content": [_email(_jpeg(), "a.jpg")]})},
                    {"_raw": json.dumps({"content": [_email(_jpeg(color=(0, 0, 255)),
                                                            "b.jpg")]})}],
        "_meta": {"total_event_count": 3}}
    seen = []
    monkeypatch.setattr(vision, "describe",
                        lambda png, mime, q, **k: seen.append(png) or "a column chart")
    tool = {t.name: t for t in splunk_agent.make_tools(fake)}["read_image"]
    out = tool.invoke({"spl": "index=x flow_id=1", "question": "what chart is this?"})
    assert fake.search.call_args.kwargs["max_results"] == vision.MAX_EVENTS
    assert len(seen) == 2 and "(a.jpg, 40x20)" in out and "(b.jpg, 40x20)" in out
    out = tool.invoke({"spl": "index=x flow_id=1", "question": "q", "name": "b.jpg"})
    assert len(seen) == 3 and "b.jpg" in out and "a.jpg" not in out
