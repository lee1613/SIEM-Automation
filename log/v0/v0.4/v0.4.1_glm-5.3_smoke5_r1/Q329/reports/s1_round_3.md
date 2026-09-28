# s1 - Q329 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=5_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/attachment.php" | stats count by uri, clientip, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="*.php" | stats count by uri_path | sort -count
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/member.php" | stats count by uri, status
- index=botsv3 sourcetype=stream:http uri="*brewertalk*" | stats count by uri, method, status
### What it means

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" | stats count b…` (50 of 71 rows seen). A claim resting on them alone is UNVERIFIED._
