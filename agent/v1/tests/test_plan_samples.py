from orchestrator import plan_samples, METRICS_SAMPLES


def test_metrics_high_value_sampled_3x():
    assert plan_samples("[METRICS] average duration of x", 1000) == METRICS_SAMPLES
    assert plan_samples("[METRICS] perc75 of bytes", 500) == METRICS_SAMPLES


def test_low_value_metrics_not_sampled():
    assert plan_samples("[METRICS] count events", 100) == 1


def test_non_metrics_never_sampled():
    assert plan_samples("[HUNTER] find the host", 1000) == 1
    assert plan_samples("[CONTENT] read the email body", 1000) == 1
    assert plan_samples("untagged task", 1000) == 1
