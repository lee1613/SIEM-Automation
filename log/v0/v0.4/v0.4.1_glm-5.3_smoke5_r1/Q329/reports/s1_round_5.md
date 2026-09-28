# s1 - Q329 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:mysql query="*mybb_attachments*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*INSERT*mybb_posts*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*INSERT*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*UPDATE*mybb_sessions*" | stats count by query
### What it means

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:mysql query="*UPDATE*mybb_sessions*" | stats count by query` (25 of 91 rows seen). A claim resting on them alone is UNVERIFIED._
