from specialists import SPECIALISTS, parse_specialist_tag


def test_parse_tag_defaults_to_hunter():
    assert parse_specialist_tag("Search dns for the C2 domain") == "hunter"


def test_parse_content_tag():
    assert parse_specialist_tag("[CONTENT] Read the phishing email body") == "content"


def test_parse_metrics_tag_case_insensitive():
    assert parse_specialist_tag("  [metrics] Average subdomain length") == "metrics"


def test_all_specialists_have_prompt_text():
    assert set(SPECIALISTS) == {"hunter", "content", "metrics", "validator"}
    for name in ("content", "metrics"):
        assert SPECIALISTS[name].strip()
