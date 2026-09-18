"""The per-round runaway cap (splunk_agent.round_output_cap / over_output_cap)."""
from splunk_agent import OUTPUT_TOKEN_CAP, over_output_cap, round_output_cap


def test_a_known_window_caps_the_round_at_the_room_left():
    assert round_output_cap(256_000, 40_000) == 216_000


def test_no_window_falls_back_to_the_flat_cap():
    assert round_output_cap(None, 40_000) == OUTPUT_TOKEN_CAP


def test_a_full_window_still_leaves_a_positive_cap():
    assert round_output_cap(256_000, 300_000) == 1


def test_q216_round_two_is_not_a_runaway_under_the_window_cap():
    # 2026-09-18: 113,542 output tokens 7 steps into a GLM round tripped the flat 100K cap.
    state = {"output_tokens": 113_542, "output_cap": round_output_cap(256_000, 60_000)}
    assert not over_output_cap(state)
    assert over_output_cap({"output_tokens": 113_542})          # unset cap = flat 100K
