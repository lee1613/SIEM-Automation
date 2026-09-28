# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http host=hoth "kernel priv esc" | stats count by uri_path, http_method, status
### What it means
Intention: The response body isn't in stream:http form_data; check the stream:http events around the `cat /tmp/colonel.c` request for the response content, and also check the FIM events for definitelydontinvestigatethisfile.sh to settle the selection.
