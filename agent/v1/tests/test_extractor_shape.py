from extractor import build_extract_prompt


def test_prompt_includes_shape_when_given():
    p = build_extract_prompt("What processor?", "bare model number, no suffix",
                             "The CPU is Intel Xeon E5-2676 v3 @ 2.40GHz",
                             expected_shape="bare processor model like E5-XXXX, drop ' vN' suffix")
    assert "drop ' vN' suffix" in p
    assert "E5-2676 v3" in p  # the analysis is included


def test_prompt_without_shape_still_valid():
    p = build_extract_prompt("q", "", "answer text", expected_shape="")
    assert "answer text" in p
