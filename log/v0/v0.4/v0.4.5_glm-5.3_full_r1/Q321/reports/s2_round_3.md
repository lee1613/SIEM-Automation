# s2 - Q321 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="aws:rds:audit" "email" | stats count by _raw | head 30
- index=botsv3 sourcetype="stream:mysql" "COUNT(u.uid)" | stats count, values(result_row_count) as rows, values(result_column_count) as cols, min(_time) as first, max(_time) as last by query
- index=botsv3 sourcetype="aws:rds:audit" "COUNT(u.uid)" | stats count
- index=botsv3 sourcetype="aws:rds:audit" "SELECT COUNT" | stats count, values(_raw) as sample_raws | head 5
### What it means
Intention: The stats output was clipped; run a plain count to confirm whether any "SELECT COUNT" statement exists in the RDS audit log.

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:rds:audit"}` (46 of 92 rows seen); `get_raw_events: {"keyword": "email", "limit": 10, "sourcetype": "aws:rds:audit"}` (5 of 10 rows seen); `run_splunk_search: index=botsv3 sourcetype="aws:rds:audit" "SELECT COUNT" | stats count, values(_raw) as samp…` (0 of 1 rows seen). A claim resting on them alone is UNVERIFIED._
