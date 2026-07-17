from adjudicator import (parse_adjudication, resolve_choice, fallback_choice,
                         render_adjudication_input, adjudicate_once)

LEDGER = [
    {"value": "1367.875", "status": "solved",  "worker": "senior#2",
     "spl": ["| stats perc25(x) perc75(x)"], "evidence": "FINAL ANSWER: 1367.875"},
    {"value": "1499.25",  "status": "partial", "worker": "senior#4",
     "spl": [], "evidence": "PARTIAL ANSWER: 1499.25 (manual Tukey fences)"},
]


def test_parse_full_block():
    out = parse_adjudication(
        "CHOICE: 1367.875\nCONFIDENCE: HIGH\nREASON: SPL-native perc75\n"
        "TIEBREAK: re-run perc75 with exact filter")
    assert out == {"choice": "1367.875", "confidence": "high",
                   "tiebreak": "re-run perc75 with exact filter"}


def test_parse_unknown_choice_is_empty():
    out = parse_adjudication("CHOICE: UNKNOWN\nCONFIDENCE: LOW")
    assert out["choice"] == "" and out["confidence"] == "low"


def test_parse_garbage_defaults():
    out = parse_adjudication("I think the answer is probably 42.")
    assert out == {"choice": "", "confidence": "low", "tiebreak": ""}


def test_resolve_choice_snaps_to_verbatim_ledger_form():
    assert resolve_choice("1367.875", LEDGER) == "1367.875"
    assert resolve_choice("  1499.25 ", LEDGER) == "1499.25"


def test_resolve_choice_case_insensitive_returns_ledger_casing():
    ledger = [{"value": "nullweb_admin", "status": "solved", "worker": "s#1",
               "spl": [], "evidence": ""}]
    assert resolve_choice("NULLWEB_ADMIN", ledger) == "nullweb_admin"


def test_resolve_choice_accepts_question_text_value():
    assert resolve_choice("Frothly", LEDGER, "Which host at Frothly?") == "Frothly"


def test_resolve_choice_rejects_synthesized_value():
    assert resolve_choice("2085", LEDGER, "what is the fence?") is None
    assert resolve_choice("", LEDGER) is None


def test_fallback_choice_prefers_solved_over_partial():
    assert fallback_choice(LEDGER) == "1367.875"
    assert fallback_choice([]) is None


def test_render_input_contains_values_and_constraints():
    r = render_adjudication_input("Using Splunk commands only, find the fence.",
                                  "number only", LEDGER)
    assert "1367.875" in r and "1499.25" in r
    assert "Using Splunk commands only" in r and "number only" in r
    assert "perc25" in r          # SPL method visible to rule (a)
    assert "partial" in r         # status visible to rule (d)


def test_adjudicate_once_resolves_choice():
    def fake_invoke(prompt):
        return "CHOICE: 1367.875\nCONFIDENCE: HIGH\nREASON: SPL-native"
    v = adjudicate_once(fake_invoke, "q?", "", LEDGER)
    assert v["answer"] == "1367.875" and v["confidence"] == "high"


def test_adjudicate_once_synthesized_choice_yields_none():
    def fake_invoke(prompt):
        return "CHOICE: 9999\nCONFIDENCE: HIGH"
    v = adjudicate_once(fake_invoke, "q?", "", LEDGER)
    assert v["answer"] is None
