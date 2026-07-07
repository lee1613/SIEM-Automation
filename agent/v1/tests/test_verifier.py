from orchestrator import parse_verifier_verdict


def test_confirm_verdict():
    v = parse_verifier_verdict("Checked event order by _time. CONFIRMED: 30358")
    assert v["verdict"] == "confirmed"


def test_refute_verdict_with_correction():
    v = parse_verifier_verdict("The earliest by _time is 30358, not 30356. "
                               "REFUTED. CORRECTION: 30358")
    assert v["verdict"] == "refuted"
    assert v["correction"] == "30358"


def test_unknown_defaults_to_confirmed():
    # if the verifier is inconclusive, don't block the pipeline
    v = parse_verifier_verdict("could not run additional queries")
    assert v["verdict"] == "confirmed"
