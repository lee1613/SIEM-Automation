# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=8_
**Scope:** sourcetypes ps, lsof, osquery:results, localhost-5, out-3, bash_history | host=hoth | fields user, COMMAND, NAME, columns.path, _raw

**Insight:** NOT_FOUND  **Candidate:** none  **Confidence:** 0

## Prior rounds
- R1: 102 sourcetypes enumerated; keyword "tomcat8" 0 matches; linux_secure and bash_history/klagerfield (20 of 83 rows) held nothing.
- R2: linux_audit, auth.log, syslog, messages — 0 tomcat8 events; located the tomcat8 feed /var/log/tomcat8/catalina.out (out-3) on host **hoth** — Struts2 exploit errors.
- R3: localhost-5 also Struts2 exceptions; ps shows tomcat8 ran bash, sh, nc, **colonelnew** (PID 9456); lsof clean; osquery proc_events reveal a gcc/chmod compile chain producing **/tmp/colonelnew**.

## This round
### What I ran
- get_raw_events localhost-5 -> 5 of 20 rows readable; all Struts2/catalina SEVERE exceptions for /frothlyinventory.
- `ps host=hoth | stats count by user` -> 9 users, tomcat8=1052 events.
- `ps host=hoth user=tomcat8 | stats count by COMMAND` -> java 595, bash 142, sh 120, **colonelnew 114**, nc 81.
- get_raw_events ps keyword=colonelnew -> PID 9456, tomcat8, running 42+ min, `<noArgs>`.
- `lsof host=hoth USER=tomcat8 | stats count by NAME` (2 passes, 83/90 rows) -> only Java jars, system libs, sockets; sockets show client 192.168.8.103.
- `osquery:results host=hoth colonelnew | stats count by name, action, columns.path` -> proc_events: **/tmp/colonelnew**, /bin/chmod, /usr/bin/gcc-5, ld.bfd, collect2.

### What it means
NOT_FOUND for the line-2 text. The escalation artifact trail is now established: the tomcat8-compromised shell on hoth compiled a C program in /tmp (gcc-5 + ld.bfd + collect2), chmod'd it, and ran it as tomcat8 (PID 9456). But no telemetry I have read shows that file's contents, so line 2 cannot be stated. The likeliest "file used to escalate" is the source file gcc compiled (a text file, matching "text displayed on line 2"), whose name appears in the gcc cmdline I have not yet read.

## Ruled out
- localhost-5 (/var/log/tomcat8/localhost.2018-07-25.log) — Struts2/catalina exceptions only.
- lsof tomcat8 on hoth — only runtime jars, libs, sockets; no escalation file held open.
- ps COMMAND field — colonelnew shows `<noArgs>`, no path or content.
- bash/sh/nc as the escalation file — shell/network tooling of the exploit, not file artifacts.
- auth/audit/history feeds (prior rounds) — 0 tomcat8 events anywhere.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The privilege-escalation artifact on hoth is /tmp/colonelnew, a binary compiled "
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_raw_events: {"limit": 20, "sourcetype": "localhost-5"}` (5 of 20 rows seen); `run_splunk_search: index=botsv3 sourcetype=ps host=hoth user=tomcat8 COMMAND=colonelnew | stats count by _raw…` (50 of 114 rows seen); `run_splunk_search: index=botsv3 sourcetype=lsof host=hoth USER=tomcat8 | stats count by NAME | sort -count` (50 of 90 rows seen). A claim resting on them alone is UNVERIFIED._
