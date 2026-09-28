from run_all_v0 import force_utf8_stdio


def test_force_utf8_stdio_does_not_raise():
    # Should be safe to call repeatedly (e.g. if main() were invoked twice
    # in a test process) and must never raise, even on streams that don't
    # support reconfigure (e.g. pytest's captured streams).
    force_utf8_stdio()
    force_utf8_stdio()


def test_arrow_character_round_trips_utf8():
    # Documents the intent: the Windows console defaults to cp1252
    # ('charmap'), which cannot encode U+2192 (the arrow used in prints
    # throughout the v1 agents) and raises UnicodeEncodeError. UTF-8 with
    # errors="replace" (what force_utf8_stdio configures) must round-trip it.
    text = "SH FINAL → extractor"
    encoded = text.encode("utf-8", "replace")
    assert encoded.decode("utf-8") == text

    # cp1252 cannot encode it directly (this is the failure force_utf8_stdio
    # prevents by switching the stream's encoding away from cp1252).
    try:
        text.encode("cp1252")
        raised = False
    except UnicodeEncodeError:
        raised = True
    assert raised is True
