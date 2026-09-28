# s1 - Q315 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=bash_history, osquery:results, syslog | source=/home/klagerfield/.bash_history, /var/log/osquery/osqueryd.results.log, /var/log/auth.log | fields=_time, _raw, host

**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
- Round 1 (this round): mapped hoth's feeds and began bash_history review; no filenames found yet.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; bash_history, osquery:results, stream:http, linux_audit all present.
- get_sources keyword=hoth -> /var/log/syslog (syslog, 203,740), /var/log/osquery/osqueryd.results.log (osquery:results, 79,098), /var/log/auth.log (117), df, kern.log.
- get_raw_events sourcetype=bash_history keyword=/tmp -> 2 events: "ls /tmp" @ 2018-08-20T21:28:41+08:00, "cd /tmp" @ 2018-08-20T19:06:55+08:00.
- get_raw_events sourcetype=bash_history (20 most recent) -> S3 upload commands (s3-upload.py, frothly_web_memcaced.tar.gz), splunk restarts, cd AWS_SCENARIOS; no /tmp writes in those rows.
- bash_history host breakdown -> hoth 83 events (/home/klagerfield/.bash_history); ec2-user history (17) belongs to AWS hosts gacrux/mars.

### What it means
NOT_FOUND: hoth's bash_history confirms the adversary interacted with /tmp (ls, cd) at 21:28 and 19:06 on Aug 20, but the 20 rows I read contain no file writes to /tmp — the writes, if recorded there, are in the ~63 unread rows between those timestamps. The osquery:results feed (79,098 events on hoth), which most likely records the literal filenames written, was not yet queried. No candidate value is held.

## Ruled out
- The 20 most-recent bash_history rows on hoth - contain only AWS S3 upload and splunk admin commands, no /tmp writes.
- /home/ec2-user/.bash_history - belongs to AWS instances gacrux.i-0920036c8ca91e501 and mars.i-08e52f8b5a034012d, not the on-prem server hoth.
- "ls /tmp" and "cd /tmp" themselves - navigation, not the streaming act the question names.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
