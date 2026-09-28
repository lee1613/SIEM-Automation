# s2 - Q202 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=cpu | stats count by host
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by host, columns.cpu_brand
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" | stats count by name, source
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by name, host
### What it means
Intention: cpu_brand comes from osquery `system_info` — which never ran on i-0920036c8ca91e501 (its 12 query names don't include it). I'll check the remaining CPU-oriented feeds for that host: `top` (header carries CPU model) and `ps` (ps aux output can show CPU model in headers on some systems).
