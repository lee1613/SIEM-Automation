from run_all_v1 import build_sh_message, DUAL_TRACK_MIN_POINTS


def test_dual_track_line_for_1000pt():
    msg = build_sh_message("Q331", "What is the fence?", "number", points=1000)
    assert "DUAL-TRACK" in msg


def test_no_dual_track_below_threshold():
    msg = build_sh_message("Q209", "Which host?", "", points=500)
    assert "DUAL-TRACK" not in msg


def test_points_default_keeps_old_behaviour():
    msg = build_sh_message("Q1", "Which host?", "")
    assert "DUAL-TRACK" not in msg and "Q1" in msg


def test_threshold_is_1000():
    assert DUAL_TRACK_MIN_POINTS == 1000
