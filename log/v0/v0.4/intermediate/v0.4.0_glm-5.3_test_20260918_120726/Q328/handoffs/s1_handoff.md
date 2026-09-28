# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetype=osquery:results | source=/var/log/osquery/osqueryd.results.log | fields=host, name, columns.cmdline, columns.path, columns.uid, columns.euid, decorations.username
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 40

## Prior rounds
- Round 1: Mapped 102 sourcetypes; no tomcat sourcetype. Established hoth as the tomcat8 host; out-3/localhost-5 are catalina logs showing Struts2 modelDrivenResult_jsp exploit traces.
- Round 1: Ruled out bash_history (empty), linux_audit (gacrux-only), suid_bin pack (standard binaries only).
- Round 2: proc_events exist on hoth (76,085) but username lives in decorations.username, not columns.username — first filter returned 0.
- Round 2: FIM CREATED on hoth revealed /tmp/colonel, /tmp/colonel.c, /tmp/colonelnew, /tmp/backpipe — the escalation artifact set.

## This round
### What I ran
- `... name="pack_process-monitoring_proc_events" host=hoth decorations.username=tomcat8 | stats count by columns.cmdline` -> 38 events, 9 distinct commands
- `sample_events keyword=colonel` -> raw JSON showing gcc compile (pid 8609) and cc1 with uid=111 euid=111
### What it means
NOT_FOUND for the line-2 text, but the escalation chain and file are confirmed: tomcat8 base64-decoded /tmp/colonel into /tmp/colonel.c, compiled it with gcc to /tmp/colonelnew, executed ./colonelnew (kernel local-root exploit, "colonel" puns "kernel"), then ran cat /tmp/colonel.c, cat /etc/passwd, and established a reverse shell via /tmp/backpipe to 45.77.53.176:8088. The file used is /tmp/colonel.c. osquery records command execution only — the cat output (line 2) is not in this feed, so the value cannot come from this scope.

## Ruled out
- osquery proc_events as a source of file content - logs cmdline only, no stdout
- /tmp/definitelydontinvestigatethisfile.sh - FIM-created on hoth but not in the tomcat8 command chain (decoy)
- The large hex echo cmdline seen in the 38-event set - decodes to a JPEG (/9j/ magic), not colonel.c

## Open questions for SH
- The line-2 text requires the staged base64 blob /tmp/colonel, which arrived over HTTP to the Struts app — may I branch to stream:http on hoth (outside my current osquery-only scope) to recover the POST body?
- Alternatively, is a prior finding held on the Struts2 initial-access POST (out-3/localhost-5) that contains the uploaded payload?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: s1 completed the host-side attribution needed for this question: on hoth, tomcat8 decoded /tmp/colonel into /tmp/colonel.c, compiled it to /tmp/colonelnew, and used that chain for local root escalation. Its osquery-only scope cannot recover the file’s displayed contents or HTTP-delivered source text, so further rounds in the same scope would pursue a missing artifact class rather than the answer.
- Scope I owned: sourcetypes=['bash_history', 'osquery:results', 'linux_secure', 'syslog', 'access_combined', 'lsof', 'ps'] sources=[] fields=['_time', 'host', 'user', 'username', 'cmd', 'command', 'path', 'filepath', 'file_name', 'cwd', '_raw']
- Rounds worked: 2/8  (iterations: 18, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=bash_history | top limit=20 user
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" host=hoth columns.action=CREATED | stats count by columns.target_path | sort - count
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | stats count by host, columns.action
- index=botsv3 sourcetype=osquery:results name="pack_incident-response_shell_history" *tomcat* | stats count by host, columns.command
- index=botsv3 sourcetype=osquery:results name="pack_incident-response_shell_history" host=hoth (columns.command="sudo*" OR columns.command="su *" OR columns.command="chmod*" OR columns.command="chown*" OR columns.command="wget*" OR columns.command="curl*" OR columns.command="python*" OR columns.command="*passwd*" OR columns.command="*shadow*" OR columns.command="*sudoers*") | stats count by columns.username, columns.command | sort columns.command
- index=botsv3 sourcetype=osquery:results name="pack_incident-response_shell_history" host=hoth | stats count by columns.username, columns.command | sort columns.username
- index=botsv3 sourcetype=osquery:results name="pack_incident-response_suid_bin" | stats count by host, columns.path
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth *colonel* | stats count by columns.cmdline, columns.username, columns.uid, columns.euid | sort - count
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth *tomcat8* | stats count by columns.username, columns.cmdline | sort - count
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth columns.username=tomcat8 | stats count by columns.cmdline | sort - count
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth decorations.username=tomcat8 | stats count by columns.cmdline | sort columns.cmdline
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth decorations.username=tomcat8 | stats count by columns.cmdline, columns.path, columns.uid, columns.euid | sort - count
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth | head 3 | stats list(columns) as columns
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" host=hoth | top limit=20 columns.username
- index=botsv3 sourcetype=osquery:results name="pack_process-monitoring_proc_events" | stats count by host
- index=botsv3 sourcetype=osquery:results | top limit=20 name
