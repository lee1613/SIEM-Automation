# s1 - Q316 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="stream:http" src_ip="192.168.70.186" | stats count, sum(bytes_out) as bytes_out_total by uri_path, dest_ip, site, status, http_method
- index=botsv3 sourcetype="stream:http" dest_ip="45.77.53.176" | stats count, sum(bytes_out) as total_bytes_out by uri_path, src_ip, http_method, status
### What it means
Intention: Get the Sysmon file-creation events on FYODOR-L with timestamps and creating-process details (Image, ProcessGuid) to tie the tool files to a process and establish the timeline relative to the 18:47 download.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="stream:http" src_ip="192.168.70.186" | stats count, sum(bytes_out…` (50 of 362 rows seen). A claim resting on them alone is UNVERIFIED._
