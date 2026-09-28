# s1 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=2_
**Scope:** sourcetype=bash_history,linux_audit,ps | source=/home/ec2-user/.bash_history,/var/log/audit/audit.log,ps | fields=host,user,USER,process_name,process_exec,app,ARGS,command,exe,type,op,msg,bash_command
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 41

## Prior rounds
- Confirmed BOTSv3 Linux telemetry exists in bash_history, linux_audit, and ps.
- Found tomcat8 activity on hoth in ps telemetry, including a reverse-shell style bash command.
- Observed a suspicious process name `colonelnew` running as tomcat8 on hoth.
- linux_audit on Aug 20 shows sudo/session events, but not the escalation file itself.
- Sampled bash_history (ec2-user) and only saw routine S3 upload commands.
- No file-content telemetry was reached this round, so the requested line could not be recovered.

## This round
### What I ran
- `index=botsv3 sourcetype=linux_audit (tomcat8 OR tomcat* OR sudo OR su OR chmod OR chown OR setuid OR setcap OR pwnkit OR pkexec) | stats count by host, user_name, command, exe, type, op, msg | sort -count` -> 24 grouped results, mostly sudo session events on gacrux hosts.
- `index=botsv3 sourcetype=ps (COMMAND=tomcat8 OR process_name=tomcat8 OR process_exec=tomcat8 OR app=tomcat8 OR process=tomcat8 OR USER=tomcat8 OR user=tomcat8 OR process_name=sh OR process_exec=sh) | stats count by host, USER, process_name, process_exec, app, ARGS | sort -count` -> 50 rows returned; hoth had tomcat8 shell/reverse-shell evidence and `colonelnew`.
- `sample_events sourcetype=bash_history source=/home/ec2-user/.bash_history` -> routine commands only.
### What it means
The compromise is clearly on hoth under tomcat8, and the likely escalation artifact is associated with the suspicious `colonelnew` process, but I do not yet have the actual filename or the line-2 content from that file.

## Ruled out
- gacrux audit hosts - sudo activity exists but no tomcat8 linkage.
- ec2-user bash history - no escalation file evidence.
- ps on non-hoth hosts - no tomcat8 compromise signal.

## Open questions for SH
- Which host/file telemetry scope should I pivot to next: command history, file listings, or audit/write events on hoth?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
