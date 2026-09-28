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


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['stream:http', 'osquery:results', 'bash_history', 'linux_audit', 'syslog'] sources=['/var/log/httpd/access_log', '/var/log/syslog', '/var/log/auth.log'] fields=['host', 'form_data', 'uri_path', '_raw', 'columns.cmdline', 'columns.path', 'columns.target_path', 'Message']
- Rounds worked: 3/8  (iterations: 20, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat8" | stats count by sourcetype, source | head 50
- index=botsv3 sourcetype=osquery:results "tomcat8" | stats count by source, host | head 50
- index=botsv3 sourcetype=osquery:results host=hoth "tomcat8" | stats count by name | sort -count | head 50
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "tomcat8" | stats count by columns.target_path, columns.action | head 50
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_incident-response_shell_history" "tomcat8" | stats count by columns.username, columns.time, columns.command | head 50
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.cmdline | head 50
- index=botsv3 sourcetype=stream:http "colonel" | stats count by http_method, status, uri_path, src_ip | head 50
- index=botsv3 sourcetype=stream:http "definitelydontinvestigatethisfile" | stats count by _time, http_method, status, bytes_out | head 20
- index=botsv3 sourcetype=syslog host=hoth "tomcat8" | stats count by _time, source, host | head 50
- index=botsv3 sourcetype=syslog host=hoth | stats count by source
