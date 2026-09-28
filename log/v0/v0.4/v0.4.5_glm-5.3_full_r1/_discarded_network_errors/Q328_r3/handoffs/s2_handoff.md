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


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['out-3', 'localhost-5', 'syslog', 'stream:http', 'osquery:results'] sources=['/var/log/tomcat8/catalina.out', 'localhost-5', '/var/log/auth.log', 'stream:http', '/var/log/osquery/osqueryd.results.log'] fields=['_raw', 'form_data', 'uri_path', 'name', 'columns.cmdline', 'host']
- Rounds worked: 3/8  (iterations: 19, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "colonel" | stats count by sourcetype, source
- index=botsv3 sourcetype=linux_audit "colonel" | stats count by source, host
- index=botsv3 sourcetype=linux_secure "colonel" | stats count by source, host
- index=botsv3 sourcetype=localhost-5 "colonel" | stats count by source, host
- index=botsv3 sourcetype=osquery:results "colonel" | stats count by source, host
- index=botsv3 sourcetype=out-3 "colonel" | stats count by source, host
- index=botsv3 sourcetype=stream:http "colonel" | stats count by _time, uri_path, form_data
- index=botsv3 sourcetype=stream:http "colonel" | stats count by host, src_ip, dest_ip, http_method
- index=botsv3 sourcetype=stream:http "setuid" | stats count by host, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http "setuid" | stats count by uri_path, uri_query, http_method, status
- index=botsv3 sourcetype=stream:http "Ubuntu 16.04.4" | stats count by host, src_ip, dest_ip, http_method
- index=botsv3 sourcetype=stream:http "unistd.h" | stats count by host, src_ip, dest_ip, http_method
- index=botsv3 sourcetype=syslog "colonel" | stats count by source, host
