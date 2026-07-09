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


def test_extractor_fallback_prefers_best_candidate_over_raw_last_line():
    from run_all_v1 import extractor_fallback_answer

    delegations = [
        {"answer": "here is a lot of unrelated prose\nthe real answer is FYODOR-L",
         "status": "solved"},
    ]
    sh_answer = "here is a lot of unrelated prose\nthe real answer is FYODOR-L"
    result = extractor_fallback_answer(sh_answer, delegations)
    assert result == "here is a lot of unrelated prose\nthe real answer is FYODOR-L"
    # best_candidate returns the full worker answer (status=solved, highest rank) —
    # this documents that the fallback no longer blindly takes .splitlines()[-1]
    # of sh_answer when a real worker answer is available.


def test_extractor_fallback_uses_last_line_when_no_delegations():
    from run_all_v1 import extractor_fallback_answer

    result = extractor_fallback_answer("line one\nFYODOR-L", [])
    assert result == "FYODOR-L"
