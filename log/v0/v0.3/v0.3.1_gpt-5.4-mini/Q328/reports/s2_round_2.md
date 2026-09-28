# s2 - Q328 - Round 2
_stamped by runner: rounds_remaining=2 novel_spl=1_
**Scope:** sourcetype=syslog,cron-too_small,package,access_combined | source=/var/log/syslog,/var/log/messages,/var/log/cron,/var/log/httpd/access_log,/var/log/apache2/access.log | fields=host,process,message,cmd,path,filename,url,uri,command,exe
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
1. Bash history and linux audit/ps/osquery FIM had already established the likely file path on hoth.
2. I confirmed hoth exists in osquery:results and that it carries file-hash and scheduled-task metadata.
3. A broad filename search for the target script returned nothing.
4. Bash history showed generic transfer behavior (python s3-upload.py), but no target script text.
5. This retry shifted scope to syslog/cron/package/access logs for preserved content artifacts.
6. No verified line 2 text was recovered.

## This round
### What I ran
- `get_sourcetype_fields(sourcetype="syslog", index="botsv3", source="/var/log/syslog", min_count=1)` -> confirmed hoth syslog with process values osqueryd, CRON, systemd.
- `sample_events(sourcetype="syslog", index="botsv3", source="/var/log/syslog", keyword="definitelydont", count=10)` -> no results.
- `get_raw_events(sourcetype="syslog", index="botsv3", source="/var/log/syslog", limit=20)` -> osqueryd error chatter, no target file/body.
- `get_sourcetype_fields(sourcetype="cron-too_small", index="botsv3", min_count=1)` -> 44 events, mostly hoth-adjacent metadata but no preserved command body.
- `get_sourcetype_fields(sourcetype="package", index="botsv3", min_count=1)` and `get_raw_events(..., keyword="wget", limit=20)` -> package listings only, not install-script content.
- `get_sourcetype_fields(sourcetype="access_combined", index="botsv3", min_count=1)` -> confirmed web logs and a preserved command-like field (`ping_ip`) that may be a useful pivot.
- `run_splunk_search(...)` -> rejected because I accidentally used a leading wildcard in the filter.
### What it means
NOT_FOUND: I established that the right alternative telemetry exists on hoth and that web logs can preserve command-like strings, but I did not recover the body of `/tmp/definitelydontinvestigatethisfile.sh` or its line 2 exactly.

## Ruled out
- syslog as a direct content source - only osquery/system logs seen.
- cron-too_small as a direct content source - no command body recovered.
- package as a direct content source - package rows only.
- access_combined as confirmed evidence source - promising, but unqueried successfully for the target script.

## Open questions for SH
- If another round is allowed, should I pivot specifically to the preserved `ping_ip` artifact in access_combined or to any web/app log that records request parameters/commands on hoth?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
