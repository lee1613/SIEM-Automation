# s1 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=2_
**Scope:** sourcetype=bash_history, ps, lsof, top, osquery:results, localhost-5, out-3, Unix:* | source=/home/klagerfield/.bash_history, /home/ec2-user/.bash_history | fields=_raw, source, _time
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1 (this round): mapped feeds; eliminated bash_history as the escalation vector; no candidate yet.

## This round
### What I ran
- get_source_types -> 102 sourcetypes available.
- get_sources keyword=tomcat -> 17 sources mention tomcat8: stream:http, osquery:results, syslog(/var/log/auth.log), out-3(/var/log/tomcat8/catalina.out), localhost-5, ps, lsof, top, Unix:UserAccounts/Service/ListeningPorts, package, bash_history, lambda:DNS, WinEventLog, usersWithLoginPrivs.
- get_raw_events /home/klagerfield/.bash_history (20 rows) -> benign splunk admin commands only (splunk restart, vi inputs.conf, cd/ls).
- get_raw_events bash_history keyword=sudo -> 2 rows, both "sudo bash" (2018-08-20T19:06:55 and 19:35:53 +08:00).
- get_raw_events bash_history keyword=chmod -> 0 rows.

### What it means
NOT_FOUND: hoth's only shell history contains no command that creates a privilege-escalation file (no chmod/setuid/sudoers/tomcat lines), so the escalation was not performed from an interactive shell whose history was captured. The artifact must be named in the RCE command channel (stream:http), osquery:results, linux_audit, or auth.log — none of which I queried before the cap. The two "sudo bash" timestamps give a pivot window for those feeds.

## Ruled out
- bash_history (klagerfield on hoth, ec2-user) - full keyword sweep for sudo/chmod/chown/setuid/sudoers/tomcat/passwd/root returned only "sudo bash" x2; no file-creation commands, so this feed cannot name the escalation file.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
