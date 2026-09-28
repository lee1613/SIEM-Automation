# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http host=hoth "kernel priv esc" | stats count by uri_path, http_method, status
### What it means
Intention: The response body isn't in stream:http form_data; check the stream:http events around the `cat /tmp/colonel.c` request for the response content, and also check the FIM events for definitelydontinvestigatethisfile.sh to settle the selection.


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['stream:http', 'osquery:results', 'bash_history', 'linux_audit', 'syslog'] sources=['stream:http', '/var/log/osquery/osqueryd.results.log', 'bash_history', '/var/log/auth.log', '/var/log/syslog'] fields=['host', 'form_data', '_raw', 'columns.cmdline', 'columns.path', 'columns.target_path', 'columns.action', 'Message']
- Rounds worked: 4/8  (iterations: 24, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat8" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype=bash_history source="/home/klagerfield/.bash_history" (sudo OR chmod OR chown OR /tmp OR wget OR curl OR passwd OR root) | stats count by _raw
- index=botsv3 sourcetype=bash_history | stats count by host, source
- index=botsv3 sourcetype=linux_audit "tomcat8" | stats count by host | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth "tomcat8" | stats count by name
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "tomcat8" | stats count by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_incident-response_shell_history" "tomcat8" | stats count by columns.username, columns.command
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.cmdline
- index=botsv3 sourcetype=stream:http host=hoth "colonel" | stats count by uri_path, http_method
- index=botsv3 sourcetype=stream:http host=hoth "kernel priv esc" | stats count by uri_path, http_method, status
- index=botsv3 sourcetype=stream:http host=hoth "tomcat8" | stats count by uri_path, http_method
- index=botsv3 sourcetype=stream:http host=hoth "Ubuntu 16.04.4 kernel priv esc" | stats count by uri_path, http_method, status
- index=botsv3 sourcetype=syslog "tomcat8" | stats count by source, host | sort -count
