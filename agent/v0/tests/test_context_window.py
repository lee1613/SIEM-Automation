import usage_tracker
from usage_tracker import DEFAULT_CONTEXT_WINDOW, context_window


def test_glm_53_is_the_provider_served_window_not_the_checkpoint():
    assert context_window("zai-org/GLM-5.3") == 256_000


def test_a_prefixed_or_snapshot_name_still_resolves():
    assert context_window("GLM-5.3") == 256_000


def test_an_unknown_model_falls_back_to_the_conservative_default(capsys):
    assert context_window("some/unlisted-model") == DEFAULT_CONTEXT_WINDOW
    assert "no served context window" in capsys.readouterr().out


def test_the_default_rounds_down_rather_than_guessing_optimistically():
    assert DEFAULT_CONTEXT_WINDOW <= 128_000


def test_the_window_table_lives_beside_the_price_table():
    assert hasattr(usage_tracker, "PRICES_PER_1M")
    assert hasattr(usage_tracker, "CONTEXT_WINDOW_PER_MODEL")


def test_gpt_54_is_the_user_supplied_served_window():
    assert context_window("gpt-5.4") == 272_000


def test_gpt_54_mini_falls_back_to_default():
    """gpt-5.4-mini was not supplied by the user, so it uses the default."""
    result = context_window("gpt-5.4-mini")
    assert result == DEFAULT_CONTEXT_WINDOW
