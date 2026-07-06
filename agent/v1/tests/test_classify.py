from splunk_subagent import _classify


def test_final_answer_is_solved():
    assert _classify("Here is the result.\nFINAL ANSWER: 199.66.91.253") == "solved"

def test_partial_answer_is_partial():
    assert _classify("PARTIAL ANSWER: FYODOR-L\nUNCERTAINTY: not confirmed") == "partial"

def test_escalate_is_too_big():
    assert _classify("ESCALATE: searched dns, found nothing, narrow the window") == "too_big"

def test_empty_is_failed():
    assert _classify("") == "failed"

def test_prose_without_final_answer_tag_is_failed():
    # Q330 case: non-empty transcript tail but no FINAL ANSWER committed
    assert _classify("I was still looking at cisco:asa message_id 113019 when") == "failed"
