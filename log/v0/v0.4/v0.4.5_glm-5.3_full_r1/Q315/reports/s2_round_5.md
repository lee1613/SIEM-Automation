# s2 - Q315 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=1_
**Scope:** sourcetype=osquery:results (host=hoth, pack_fim_file_events, pack_process-monitoring_proc_events) | stream:http RCE channel | fields: columns.target_path, columns.action, columns.time, columns.uid, columns.size, columns.cmdline
**Insight:** FOUND
**Candidate:** colonel,definitelydontinvestigatethisfile.sh   **Confidence:** 93

## Prior rounds
- R1: Enumerated all 15 Struts2 RCE commands from stream:http form_data; found `echo <base64 C source> >> /tmp/colonel` (1534763317) and a JPEG-base64 echo (1534763390) whose redirect was clipped; ruled colonel.c/backpipe local; free-text name searches returned 0 (false negative).
- R2: osquery FIM directly recorded /tmp/definitelydontinvestigatethisfile.sh CREATED at 1534763390 (uid 111, 21857 bytes) and /tmp/colonel CREATED at 1534763317 (uid 111, 7701 bytes); process events confirmed colonel.c/colonelnew as local decode/compile; stream:tcp nc channel carries no payload; linux_audit empty.
- R3: Settled p4 VERIFIED: FIM at the two echo seconds returned only the two files; all six derivatives' FIM rows complete.
- R4: Complete in-window CREATED list (25/25) confirmed no other /tmp file at either echo second; JPEG echo request bytes_in=24704 vs ~8.5KB captured (clipping documented); filed replacement selection premise p6.

## This round
### What I ran
- Consolidated FIM CREATED for all eight named files (complete 8/8 rows): colonel 1534763317 uid 111; definitelydontinvestigatethisfile.sh 1534763390 uid 111; colonel.c 1534763456 uid 111; backpipe 1534763573 uid 111; colonelnew 1534763660 uid 111; loot.txt 1534764186 uid 0; suitecrm.sql 1534765138 uid 0; blargh.tgz 1534765279 uid 0.

### What it means
p6 (the replacement selection premise for the refuted bash_history-based p2) and p5 are both settled VERIFIED from complete results. The exact RCE write to /tmp/colonel is `echo <base64 C source> >> /tmp/colonel` at 1534763317.466, with the unique FIM CREATED row at 1534763317 (uid 111, 0→7701 bytes). The second content-bearing RCE command is the JPEG-base64 echo at 1534763390.299 (redirect clipped at capture, request 24704 bytes_in), with the unique FIM CREATED row at exactly 1534763390 for /tmp/definitelydontinvestigatethisfile.sh (uid 111, 0→21857 bytes). All six rivals are later local artifacts with local creation commands — and loot.txt, suitecrm.sql, blargh.tgz were created by uid 0 (root) after the local privilege escalation via colonelnew, not by the RCE context at all. The two filenames are unchanged: colonel, definitelydontinvestigatethisfile.sh.

## Ruled out
- /tmp/colonel.c — CREATED 1534763456, local decode (`base64 --decode /tmp/colonel`, process event 1534763464).
- /tmp/colonelnew — CREATED 1534763660, local build (`gcc colonel.c -o colonelnew` 1534763701, `chmod +x`, `./colonelnew`).
- /tmp/backpipe — CREATED 1534763573, local FIFO (`mknod /tmp/backpipe p`).
- /tmp/loot.txt — CREATED 1534764186 by uid 0 (root), post-privilege-escalation local output.
- /tmp/suitecrm.sql — CREATED 1534765138 by uid 0, local dump output.
- /tmp/blargh.tgz — CREATED 1534765279 by uid 0 with MOVED_FROM, local archive.