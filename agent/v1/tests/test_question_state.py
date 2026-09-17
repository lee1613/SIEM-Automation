import pytest

from question_state import ROUND_ITERS, QuestionState, tier_budget


def test_tier_table_matches_the_spec():
    assert tier_budget(100)  == {"tier": 100,  "seniors": 1, "rounds": 3, "sh_turns": 5,  "iters": 8}
    assert tier_budget(500)  == {"tier": 500,  "seniors": 2, "rounds": 5, "sh_turns": 8,  "iters": 8}
    assert tier_budget(1000) == {"tier": 1000, "seniors": 3, "rounds": 8, "sh_turns": 12, "iters": 8}


def test_points_below_500_fall_to_the_base_tier():
    assert tier_budget(0)["tier"] == 100
    assert tier_budget(499)["tier"] == 100
    assert tier_budget(999)["tier"] == 500


def test_ceiling_is_seniors_times_rounds_times_iterations():
    st = QuestionState(points=1000)
    assert st.senior_iteration_ceiling == 3 * 8 * ROUND_ITERS == 192


def test_spawn_slots_are_consumed_and_capped():
    st = QuestionState(points=1000)
    for sid in ("s1", "s2", "s3"):
        st.open_senior(sid)
    assert st.can_spawn_senior() is False
    with pytest.raises(ValueError):
        st.open_senior("s4")


def test_retiring_does_not_return_a_spawn_slot():
    st = QuestionState(points=500)
    st.open_senior("s1")
    st.retire("s1")
    st.open_senior("s2")
    assert st.can_spawn_senior() is False      # 2-senior tier, both slots spent


def test_api_failure_refunds_the_spawn_slot():
    st = QuestionState(points=100)
    st.open_senior("s1")
    assert st.can_spawn_senior() is False
    st.refund_spawn("s1")
    assert st.can_spawn_senior() is True


def test_exploration_is_capped_at_one_and_costs_no_senior_slot():
    st = QuestionState(points=100)
    st.open_exploration("e1")
    assert st.can_spawn_senior() is True       # slot untouched
    assert st.can_spawn_exploration() is False


def test_a_senior_spawned_late_gets_only_the_waves_that_remain():
    st = QuestionState(points=1000)            # 8 rounds
    st.open_senior("s1")
    for _ in range(6):
        st.record_wave()
    assert st.open_senior("s2") == 2           # min(8, 8 - 6)


def test_rounds_left_for_is_bounded_by_both_clocks():
    st = QuestionState(points=500)             # 5 rounds
    st.open_senior("s1")
    st.record_wave(); st.record_round("s1")
    assert st.rounds_left_for("s1") == 4
    for _ in range(4):
        st.record_wave()
    assert st.rounds_left_for("s1") == 0


def test_question_ends_when_waves_run_out():
    st = QuestionState(points=100)             # 3 rounds, 5 turns
    for _ in range(3):
        st.record_wave()
    assert st.exhausted() == "rounds"


def test_question_ends_when_turns_run_out_with_rounds_left():
    st = QuestionState(points=100)             # 3 rounds, 5 turns
    for _ in range(5):
        st.record_turn()
    assert st.exhausted() == "turns"


def test_two_consecutive_r2_fails_block_continue():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    st.record_r2("s1", failed=True)
    assert st.continue_blocked("s1") is False
    st.record_r2("s1", failed=True)
    assert st.continue_blocked("s1") is True


def test_a_passing_round_clears_the_thrash_streak():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    st.record_r2("s1", failed=True)
    st.record_r2("s1", failed=False)
    st.record_r2("s1", failed=True)
    assert st.continue_blocked("s1") is False
