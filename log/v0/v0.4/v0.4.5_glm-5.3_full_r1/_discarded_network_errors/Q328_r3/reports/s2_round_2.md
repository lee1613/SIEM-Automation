# s2 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http "colonel" | stats count by host, src_ip, dest_ip, http_method
- index=botsv3 sourcetype=stream:http "colonel" | stats count by _time, uri_path, form_data
- index=botsv3 sourcetype=stream:http "Ubuntu 16.04.4" | stats count by host, src_ip, dest_ip, http_method
- index=botsv3 sourcetype=stream:http "unistd.h" | stats count by host, src_ip, dest_ip, http_method
### What it means
Intention: No literal C-source tokens in stream:http. Now check the other output-bearing feeds for the decoded text — starting with osquery:results (which had the colonel events) for "unistd.h", and also check whether the `cat` response body exists in stream:http at all.
