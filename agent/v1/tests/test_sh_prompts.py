from sh_loop import SENIOR_BRIEF, SH_SYSTEM_PROMPT, render_opening, render_rejection, render_wave


def test_the_boundary_rule_is_in_both_prompts():
    for prompt in (SH_SYSTEM_PROMPT, SENIOR_BRIEF):
        assert "constraints and goals" in prompt
        assert "evidence and SPL" in prompt


def test_sh_is_told_it_never_writes_spl():
    assert "never write SPL" in SH_SYSTEM_PROMPT.lower() or \
           "do not write the query" in SH_SYSTEM_PROMPT.lower()


def test_sh_prompt_names_all_six_routes():
    for route in ("SPAWN", "RETIRE", "COMMAND", "CRITIC", "CLARIFY", "ANSWER"):
        assert route in SH_SYSTEM_PROMPT


def test_sh_prompt_carries_the_three_rubric_dimensions_and_both_gates():
    for token in ("R1", "R2", "R3", "scope alignment", "progress", "answer readiness"):
        assert token.lower() in SH_SYSTEM_PROMPT.lower()
    assert "two consecutive" in SH_SYSTEM_PROMPT.lower()
    assert "R1 = FAIL" in SH_SYSTEM_PROMPT


def test_the_senior_brief_carries_the_report_template_and_the_reply_shapes():
    for section in ("## Prior rounds", "## This round", "### What I ran",
                    "### What it means", "## Ruled out", "## Open questions for SH"):
        assert section in SENIOR_BRIEF
    assert "CLARIFY" in SENIOR_BRIEF and "COMMAND" in SENIOR_BRIEF
    assert "400" in SENIOR_BRIEF


def test_the_senior_is_told_intent_not_the_rubric():
    assert "PASS" not in SENIOR_BRIEF and "WEAK" not in SENIOR_BRIEF
    assert "deciding whether to keep you on this scope" in SENIOR_BRIEF


def test_the_opening_states_the_question_the_shape_and_the_budget():
    text = render_opening(qid="Q216", question="How long was the flow?",
                          guidance="integer seconds", points=1000,
                          budget={"tier": 1000, "seniors": 3, "rounds": 8,
                                  "sh_turns": 12, "iters": 8})
    assert "Q216" in text and "How long was the flow?" in text
    assert "integer seconds" in text
    assert "3" in text and "8" in text and "12" in text


def test_the_opening_asks_for_exactly_one_spawn_first():
    text = render_opening(qid="Q1", question="q", guidance="", points=100,
                          budget={"tier": 100, "seniors": 1, "rounds": 3,
                                  "sh_turns": 5, "iters": 8})
    assert "ONE senior" in text


def test_a_wave_renders_every_report_with_its_stamped_numbers():
    reports = {
        "s1": {"report": "# s1 - Q216 - Round 2\nbody", "novel_spl_count": 0,
               "insight": "NOT_FOUND", "status": "partial", "value": "",
               "confidence": 20, "rounds_left": 3},
        "s2": {"report": "# s2 - Q216 - Round 1\nother", "novel_spl_count": 4,
               "insight": "FOUND", "status": "solved", "value": "1367.875",
               "confidence": 80, "rounds_left": 6},
    }
    text = render_wave(reports, slots_remaining=5, turns_remaining=7)
    assert "s1" in text and "s2" in text
    assert "novel_spl=0" in text or "novel SPL: 0" in text
    assert "1367.875" in text
    assert "5" in text and "7" in text


def test_a_wave_flags_the_code_side_r2_failure_explicitly():
    reports = {"s1": {"report": "r", "novel_spl_count": 0, "insight": "NOT_FOUND",
                      "status": "partial", "value": "", "confidence": 10,
                      "rounds_left": 2}}
    text = render_wave(reports, slots_remaining=2, turns_remaining=3)
    assert "R2 = FAIL" in text


def test_a_rejection_tells_sh_exactly_what_to_fix():
    text = render_rejection(["s1 has no rounds left — RETIRE or ANSWER"])
    assert "REJECTED" in text
    assert "no rounds left" in text
