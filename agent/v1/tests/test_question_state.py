import pytest
from question_state import ROUND_ITERS, QuestionState, tier_budget


def test_tier_table_matches_the_spec():
    assert tier_budget(100)  == {"tier": 100,  "seniors": 1, "rounds": 3, "sh_turns": 5,  "iters": 12}
    assert tier_budget(500)  == {"tier": 500,  "seniors": 2, "rounds": 5, "sh_turns": 13, "iters": 12}
    assert tier_budget(1000) == {"tier": 1000, "seniors": 3, "rounds": 8, "sh_turns": 28, "iters": 12}


def test_points_below_500_fall_to_the_base_tier():
    assert tier_budget(0)["tier"] == 100
    assert tier_budget(499)["tier"] == 100
    assert tier_budget(999)["tier"] == 500


def test_ceiling_is_seniors_times_rounds_times_iterations():
    st = QuestionState(points=1000)
    assert st.senior_iteration_ceiling == 3 * 8 * ROUND_ITERS == 288


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


def _work(st, sid, n):
    for _ in range(n):
        st.record_wave()
        st.record_round(sid)


def test_a_late_senior_gets_its_own_full_rounds():
    # Rounds are per senior: a replacement is not left with the question's leftovers.
    st = QuestionState(points=1000)            # 8 rounds per senior
    st.open_senior("s1")
    _work(st, "s1", 8)
    assert st.open_senior("s2") == 8
    assert st.rounds_left_for("s2") == 8


def test_rounds_left_for_counts_only_the_seniors_own_rounds():
    st = QuestionState(points=500)             # 5 rounds per senior
    st.open_senior("s1")
    _work(st, "s1", 1)
    st.open_senior("s2")
    _work(st, "s2", 3)                         # other seniors' waves do not spend s1's rounds
    assert st.rounds_left_for("s1") == 4
    assert st.rounds_left_for("s2") == 2


def test_a_spent_senior_with_a_free_slot_does_not_end_the_question():
    st = QuestionState(points=500)             # 2 seniors x 5 rounds
    st.open_senior("s1")
    _work(st, "s1", 5)
    assert st.exhausted() == ""                # SH can still spawn s2


def test_question_ends_when_every_slot_is_used_and_every_senior_is_spent():
    st = QuestionState(points=100)             # 1 senior x 3 rounds
    assert st.exhausted() == ""                # nothing spawned yet
    st.open_senior("s1")
    _work(st, "s1", 2)
    assert st.exhausted() == ""
    _work(st, "s1", 1)
    assert st.exhausted() == "rounds"


def test_retiring_the_last_senior_with_no_slot_left_ends_the_question():
    st = QuestionState(points=100)
    st.open_senior("s1")
    st.retire("s1")
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


def test_record_round_remembers_whether_the_round_hit_the_cap():
    st = QuestionState(points=1000)
    st.open_senior("s1")
    assert st.last_round_capped("s1") is False      # nothing worked yet
    st.record_round("s1", capped=True)
    assert st.last_round_capped("s1") is True
    st.record_round("s1", capped=False)
    assert st.last_round_capped("s1") is False, "only the LAST round counts"


def test_an_unknown_senior_is_not_capped():
    assert QuestionState(points=100).last_round_capped("nobody") is False


def test_sh_turns_cover_every_senior_running_all_rounds_in_sequence():
    for pts in (100, 500, 1000):
        b = tier_budget(pts)
        assert b["sh_turns"] >= b["seniors"] * (b["rounds"] + 1) + 1
