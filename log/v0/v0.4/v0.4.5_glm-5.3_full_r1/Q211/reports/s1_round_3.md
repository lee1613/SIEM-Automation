# s1 - Q211 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count, dc(src_ip) as srcs, values(src_ip) as src_ips, values(dest_port) as ports, min(_time) as first, max(_time) as last
- index=botsv3 sourcetype=stream:dns (src_ip="192.168.24.128" OR src_ip="192.168.70.186" OR src_ip="192.168.9.30") | stats count, values(host_addr) as resolved_ips by query | sort -count
- index=botsv3 sourcetype=stream:dns query="splunk.froth.ly" | stats count, values(host_addr) as resolved_ips, dc(src_ip) as src_count
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count by src_ip, dest_port | sort -count
### What it means
Intention: The bulk is TLS on 443 (4955 events) plus one stratum-port connection on 3333. I need to identify what 45.77.53.176 is — checking whether any DNS query from these endpoints resolved to it, and what the 3333 connection actually was.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:dns (src_ip="192.168.24.128" OR src_ip="192.168.70.186" OR …` (50 of 1479 rows seen). A claim resting on them alone is UNVERIFIED._
