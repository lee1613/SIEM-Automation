# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http host=hoth "root:x:0:0" | stats count by uri_path, status
### What it means
Intention: Test whether stream:http captures HTTP response bodies at all — the `cat /etc/passwd` RCE wrote its output to the response stream, so if bodies were captured, "root:x:0:0" would appear; this decides whether the `cat /tmp/colonel colonel.c` output could exist anywhere in the feed.

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen). A claim resting on them alone is UNVERIFIED._
