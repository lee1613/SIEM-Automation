# s2 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** index=botsv3 | sourcetype=stream:http | source=stream:http | fields: form_data, _raw, uri_path, src_ip, dest_ip
**Insight:** FOUND
**Candidate:** ` * Ubuntu 16.04.4 kernel priv esc`   **Confidence:** 85

## Prior rounds
- R1: literal "colonel" dead — 0 hits index-wide and in bash_history, linux_audit, ps, lsof, linux_secure; no tomcat8 shell history exists.
- R2: found the command channel — 17 Struts2 OGNL POSTs to /frothlyinventory/integration/saveGangster.action (192.168.9.30:8080) from 192.168.8.103, run via java.lang.ProcessBuilder as the Tomcat service account.
- R3: extracted all 15 distinct commands, confirmed /tmp/colonel.c as the escalation file, decoded its header from the echo payload.

## This round
### What I ran
- rex `#cmd='(?<cmd>[^']*)` over saveGangster -> 15 distinct commands, chronological
- rex on echo redirect targets -> ` >> /tmp/colonel` (C source); second echo is a JPEG
- get_raw_events `cat /tmp/colonel.c` -> 1 event, HTTP 200, 5775-byte response (body not a searchable field)
- stream:http search "Ubuntu 16.04.4 kernel priv esc" -> 0 rows (decoded text stored nowhere as a field)

### What it means
The full chain on hoth: OGNL RCE as tomcat8 -> whoami/id/groups/cat /etc/passwd -> `useradd -ou 0 -g 0 -M -N -r -s /bin/bash tomcat7 -p davidverve.com` (root account) -> uname -a / lsb_release -a -> `echo <base64> >> /tmp/colonel` -> `base64 --decode /tmp/colonel > /tmp/colonel.c` -> `cat /tmp/colonel.c` -> `md5sum /tmp/colonel.c` -> mknod backpipe -> reverse shell to 45.77.53.176:8088. The escalation file is **/tmp/colonel.c**, independently confirmed in stream:http (not osquery). Its base64 payload decodes to the Ubuntu 16.04.4 kernel priv-esc exploit (CVE-2017-1000112, credits @bleidl, author vnik). Byte-by-byte decode of the header: line 1 `/*`, line 2 ` * Ubuntu 16.04.4 kernel priv esc`, line 3 ` *`, line 4 ` * all credits to @bleidl`, line 5 ` * - vnik`, line 6 ` */`. Line 2 is the candidate value. The decode was hand-verified group-by-group (LyoK=`/*\n`, ICog=` * `, VWJ1bnR1=`Ubuntu`, IDE2LjA0LjQg=` 16.04.4 `, a2VybmVs=`kernel`, IHByaXYgZXNj=` priv esc`) and matches the public exploit source.

## Ruled out
- /tmp/colonel (base64 container) as "the file" - holds encoded text; the .c is the decoded exploit source
- JPEG echo payload - image data, not escalation source
- Decoded text in stream:http response bodies - 0 hits; response body not captured as a field
- IoT-scanner /tmp traffic (qtx.mips, dlink, xoxo) - unrelated noise against 172.16.0.x
- osquery:results - excluded by SH's constraint; not re-read

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The file used to escalate tomcat8's permissions to root on hoth is /tmp/colonel."
