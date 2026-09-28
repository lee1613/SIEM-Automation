# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "tomcat8" | stats count by columns.target_path, columns.action | head 50
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.cmdline | head 50
- index=botsv3 sourcetype=stream:http "colonel" | stats count by http_method, status, uri_path, src_ip | head 50
- index=botsv3 sourcetype=stream:http "definitelydontinvestigatethisfile" | stats count by _time, http_method, status, bytes_out | head 20
### What it means
Intention: Check osquery:results for any mention of definitelydontinvestigatethisfile.sh to see if it was executed or read, which would make it a rival candidate for the escalation file.
