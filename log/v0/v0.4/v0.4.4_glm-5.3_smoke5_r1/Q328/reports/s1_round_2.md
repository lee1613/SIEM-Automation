# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=5_
**Scope:** sourcetypes out-3, localhost-5, history-2, config_file, syslog, linux_audit | sources /var/log/tomcat8/catalina.out, /var/log/tomcat8/localhost.2018-07-25.log, /var/log/apt/history.log, /etc/{osquery/osquery.conf,pear.conf,resolv.conf}, /var/log/{auth.log,syslog,messages} | fields _raw, host, source, count

**Insight:** NOT_FOUND  **Candidate:** none  **Confidence:** 0

## Prior rounds
- R1: Enumerated 102 sourcetypes; keyword "tomcat8" 0 matches; linux_secure and bash_history/klagerfield (first 20 of 83 rows, Splunk config only) held nothing.
- R2: linux_audit, auth.log, syslog, messages — 0 tomcat8 events; located the tomcat8 feed: /var/log/tomcat8/catalina.out (out-3) on host **hoth**, showing Struts2 exploit errors.

## This round
### What I ran
- `sourcetype=linux_audit tomcat8 | stats count by host` -> 0 events.
- `syslog source=/var/log/auth.log tomcat8` -> 0; `/var/log/syslog` and `/var/log/messages` tomcat8 -> 0 each.
- get_sources history-2 -> /var/log/apt/history.log (2 events, apt only).
- get_sources out-3 -> /var/log/tomcat8/catalina.out (17 events); raw read returned 4 of 17 (rows clipped at 1500 chars) — all Struts2 Dispatcher exceptions during request processing.
- get_sources localhost-5 -> /var/log/tomcat8/localhost.2018-07-25.log (30 events, unread).
- get_sources config_file -> osquery.conf, pear.conf, resolv.conf only.
- `sourcetype=out-3 | stats count by host, source` -> single row: host=hoth.

### What it means
NOT_FOUND. The tomcat8 service runs on host hoth and was exploited via Struts2 (catalina.out errors), but no feed I queried names the escalation file or shows its contents, so line 2 cannot be read yet. The dataset's only tomcat8-named feed is catalina.out on hoth; auth/audit feeds carry no tomcat8 records at all.

## Ruled out
- linux_audit, /var/log/auth.log, /var/log/syslog, /var/log/messages, linux_secure — 0 tomcat8 events each.
- history-2 — apt package history only.
- config_file — only osquery/pear/resolv configurations.
- bash_history:/home/klagerfield/.bash_history — first 20 of 83 rows are Splunk forwarder config; 63 rows still unread (not fully eliminated).
- catalina.out as the answer source — its events are exploit errors, not the escalation file (though 13 of 17 rows unread and 4 clipped; full text unexamined).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"limit": 20, "sourcetype": "out-3"}` (4 of 17 rows seen). A claim resting on them alone is UNVERIFIED._
