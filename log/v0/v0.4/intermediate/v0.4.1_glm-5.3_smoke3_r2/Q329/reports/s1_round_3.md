# s1 - Q329 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="aws:s3:accesslogs" http_method="PUT" | stats count by bucket | sort -count
- index=botsv3 sourcetype="stream:http" "taedonggang*" | stats count
- index=b transactions=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
### What it means

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:s3:accesslogs"}` (38 of 76 rows seen). A claim resting on them alone is UNVERIFIED._
