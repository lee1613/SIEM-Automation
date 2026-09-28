# s1 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=syslog, linux_audit, bash_history | source=/var/log/syslog, /var/log/auth.log, /home/klagerfield/.bash_history | fields=_raw, host, source
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1 (this round): began the hunt for the tomcat8 privilege-escalation file on hoth.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; relevant: bash_history, linux_audit, osquery:results, stream:http, config_file.
- index=botsv3 sourcetype=syslog "tomcat8" | stats count by source, host -> 0 events.
- index=botsv3 sourcetype=linux_audit "tomcat8" | stats count by host -> 0 events.
- index=botsv3 sourcetype=bash_history | stats count by host, source -> hoth /home/klagerfield/.bash_history = 83 events (also gacrux and mars EC2 hosts).
- get_raw_events on hoth's bash history (first 20) -> Splunk config commands only (vi inputs.conf, splunk restart, cd/ls) — benign admin work.
- bash_history keyword search (sudo OR chmod OR chown OR /tmp OR wget OR curl OR passwd OR root) -> 4 events matched, but the stats output returned only counts, not the _raw text, so the matching commands were not read.

### What it means
NOT_FOUND: I narrowed the host-side feeds but did not yet reach the escalation file or any artifact exposing its contents. The 4 keyword-matching bash history commands are the strongest unread lead — they likely name the escalation file — but the aggregation hid their text. The string "tomcat8" is absent from both syslog and linux_audit, so the escalation evidence lives elsewhere (osquery:results FIM, stream:http Struts2 command stream, or config_file).

## Ruled out
- sourcetype=syslog (all 6 sources incl. /var/log/syslog, /var/log/auth.log) - 0 events mention tomcat8.
- sourcetype=linux_audit - 0 events mention tomcat8.
- First 20 entries of hoth's /home/klagerfield/.bash_history - Splunk config/admin commands, no escalation activity.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
