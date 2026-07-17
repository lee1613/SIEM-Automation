from splunk_subagent import graph_key


def test_sampled_key_only_for_metrics_role():
    assert graph_key("metrics", True, True) == ("metrics_sampled", True)
    assert graph_key("metrics", False, True) == ("metrics_sampled", False)


def test_sample_flag_ignored_for_other_roles():
    assert graph_key("hunter", True, True) == ("hunter", True)
    assert graph_key("content", False, True) == ("content", False)


def test_unsampled_is_identity():
    assert graph_key("metrics", False, False) == ("metrics", False)
    assert graph_key("hunter", True, False) == ("hunter", True)
