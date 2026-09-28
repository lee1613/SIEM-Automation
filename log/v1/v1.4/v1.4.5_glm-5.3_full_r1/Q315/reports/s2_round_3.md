# s2 - Q315 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=2_
**Scope:** sourcetype=osquery:results (host=hoth, pack_fim_file_events, pack_process-monitoring_proc_events) | stream:http RCE channel (R1) | fields: columns.target_path, columns.action, columns.time, columns.size, columns.uid, columns.cmdline
**Insight:** FOUND
**Candidate:** colonel,definitelydontinvestigatethisfile.sh   **Confidence:** 92

## Prior rounds
- R1: Enumerated all 15 Struts2 RCE commands from stream:http form_data; found `echo <base64 C source> >> /tmp/colonel` (1534763317) and a JPEG-base64 echo (1534763390) whose redirect was clipped; ruled colonel.c/backpipe local; free-text name searches returned 0 (false negative).
- R2: osquery FIM directly recorded /tmp/definitelydontinvestigatethisfile.sh CREATED at 1534763390 (uid 111, 21857 bytes) and /tmp/colonel CREATED at 1534763317 (uid 111, 7701 bytes); process events confirmed colonel.c/colonelnew as local decode/compile; stream:tcp nc channel carries no payload; linux_audit empty. Filed FOUND at 90.

## This round
### What I ran
- FIM for the six derivatives (complete 6/6): colonel.c CREATED 1534763456; colonelnew CREATED 1534763660; backpipe CREATED 1534763573 (54 events to 1534765733); loot.txt CREATED 1534764186; suitecrm.sql CREATED 1534765138; blargh.tgz CREATED 1534765279 with MOVED_FROM.
- FIM at columns.time IN (1534763317,1534763390) (complete 2/2): only /tmp/colonel (CREATED+UPDATED, 0→7701, uid 111) and /tmp/definitelydontinvestigatethisfile.sh (CREATED+UPDATED, 0→21857, uid 111).

### What it means
p4 is settled VERIFIED on complete results. Each of the two files is a remote inbound write evidenced by two feeds agreeing to the second: colonel — RCE `echo <base64 C source> >> /tmp/colonel` at 1534763317.466 + FIM CREATED 1534763317 by uid 111 (tomcat8, the RCE context); definitelydontinvestigatethisfile.sh — RCE `echo <base64 JPEG>` at 1534763390.299 (redirect clipped in form_data) + FIM CREATED at exactly 1534763390 by the same uid 111, 21857 bytes. The complete FIM query at both seconds returned only these two files, so no other /tmp file was created at either echo second — the clipped redirect gap is closed host-side. All six derivatives were created later by local commands (base64 --decode → gcc → chmod → execute; mknod; nc-backpipe-phase collection), none at either echo second. The two filenames are unchanged: colonel, definitelydontinvestigatethisfile.sh.

## Ruled out
- /tmp/colonel.c — CREATED 1534763456, local decode (`base64 --decode /tmp/colonel`, process event 1534763464).
- /tmp/colonelnew — CREATED 1534763660, local build (`gcc colonel.c -o colonelnew` 1534763701, `chmod +x`, `./colonelnew`).
- /tmp/backpipe — CREATED 1534763573, local FIFO (`mknod /tmp/backpipe p`).
- /tmp/loot.txt — CREATED 1534764186, nc-backpipe-phase local output.
- /tmp/suitecrm.sql — CREATED 1534765138, local dump output.
- /tmp/blargh.tgz — CREATED 1534765279 with MOVED_FROM, local archive.