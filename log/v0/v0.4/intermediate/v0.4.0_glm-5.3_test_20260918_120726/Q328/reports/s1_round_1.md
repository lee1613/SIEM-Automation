# s1 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=osquery:results | source=/var/log/osquery/osqueryd.results.log | fields=host, name, columns.command, columns.username
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- Round 1: Mapped all 102 sourcetypes; no "tomcat" sourcetype exists. linux_audit (112 events) is gacrux-only, useradd/sudo activity, no tomcat8.
- Round 1: Sampled history-2 (apt-get netcat), out-3 and localhost-5 (Tomcat catalina logs with Struts2 modelDrivenResult_jsp stack traces — exploit vector confirmed).
- Round 1: bash_history sourcetype is empty (0 events); shell history lives in osquery:results pack_incident-response_shell_history.
- Round 1: Confirmed hoth is the tomcat8 host (install, tomcat-users.xml, restarts all on hoth).
- Round 1: suid_bin pack (44 events) shows only standard SUID binaries on gacrux hosts — no anomalous SUID escalation artifact.

## This round
### What I ran
- `index=botsv3 sourcetype=osquery:results name="pack_incident-response_shell_history" host=hoth *tomcat*` -> 8 events, all tomcat8 admin commands on hoth
- `sample_events` on out-3/localhost-5 -> Struts2 exploit stack traces (modelDrivenResult_jsp)
- `get_sources` -> full source manifest; osqueryd.results.log is the dominant Linux process/history feed
### What it means
NOT_FOUND: I established the host (hoth) and the initial-access vector (Struts2 OGNL RCE against the frothlyinventory Tomcat app) but ran out of iterations before querying pack_process-monitoring_proc_events (214,923 events) and pack_fim_file_events (406 events) — the two feeds that will name the escalation file. No candidate value is held.

## Ruled out
- sourcetype=bash_history - zero events in index; shell history is only in osquery:results
- linux_audit - gacrux hosts only, useradd/sudo/groupadd admin activity, no tomcat8 involvement
- pack_incident-response_suid_bin - standard SUID binaries only, no anomalous escalation artifact
- history-2 - only 2 events (apt-get netcat), unrelated

## Open questions for SH
- Is the escalation expected on hoth specifically, or on another Linux host (gacrux.*) that tomcat8 reached laterally?
- Does a prior finding exist on the Struts2 initial access (out-3/localhost-5) that pins the exploit timestamp, so I can window proc_events around it?
- Should the "file used in that escalation" be expected as a FIM-observed artifact (pack_fim_file_events) or as content inside a logged command/HTTP payload?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
