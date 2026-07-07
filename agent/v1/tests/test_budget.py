from splunk_agent import iter_budget


def test_high_value_gets_more_iterations():
    assert iter_budget(1000) >= 25
    assert iter_budget(500) >= 25


def test_low_value_gets_base():
    assert iter_budget(100) == 15
    assert iter_budget(0) == 15
