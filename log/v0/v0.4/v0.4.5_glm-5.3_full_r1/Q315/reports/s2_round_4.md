# s2 - Q315 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=4_
**Scope:** sourcetype=osquery:results (host=hoth, pack_fim_file_events, pack_process-monitoring_proc_events) | stream:http RCE channel | fields: columns.target_path, columns.action, columns.time, columns.size, columns.uid, columns.cmdline, bytes_in
**Insight:** FOUND
**Candidate:** colonel,definitelydontinvestigatethisfile.sh   **Confidence:** 92

## Prior rounds
- R1: Enumerated all 15 Struts2 RCE commands from stream:http form_data; found `echo <base64 C source> >> /tmp/colonel` (1534763317) and a JPEG-base64 echo (1534763390) whose redirect was clipped; ruled colonel.c/backpipe local; free-text name searches returned 0 (false negative).
- R2: osquery FIM directly recorded /tmp/definitelydontinvestigatethisfile.sh CREATED at 1534763390 (uid 111, 21857 bytes) and /tmp/colonel CREATED at 1534763317 (uid 111, 7701 bytes); process events confirmed colonel.c/colonelnew as local decode/compile; stream:tcp nc channel carries no payload; linux_audit empty. Filed FOUND at 90.
- R3: Settled p4 VERIFIED with complete results: FIM at the two echo seconds returned only the two files; all six derivatives' FIM rows complete. Filed FOUND at 92.

## This round
### What I ran
- FIM CREATED in attack window 1534763000-1534766200 → 25/25 rows complete: colonel 1534763317, definitelydontinvestigatethisfile.sh 1534763390, colonel.c 1534763456, cclBJ1WV.s 1534763658, colonelnew+cc* 1534763660, backpipe 1534763573, loot.txt 1534764186, suitecrm.sql 1534765138, blargh.tgz 1534765279, plus tmpf*/systemd OS noise.
- Process events for definitelydont* → 0 events (RCE's /bin/bash -c child too short-lived for the 5-min scheduled query).
- Echo request sizes → 2/2 rows: JPEG echo bytes_in=24704 at 1534763390.299; C-source echo bytes_in=9200 at 1534763317.466.

### What it means
The replacement selection premise is now supported end-to-end on complete results. The two remote inbound writes are each tied to their RCE echo by to-the-second FIM creation by uid 111 (tomcat8, the RCE context): colonel — recovered redirect `>> /tmp/colonel` at 1534763317.466 + FIM CREATED 1534763317 (0→7701 bytes); definitelydontinvestigatethisfile.sh — JPEG echo at 1534763390.299 (redirect clipped: request 24704 bytes_in vs ~8.5KB captured) + the unique FIM CREATED at exactly 1534763390 (0→21857 bytes). The complete in-window CREATED list (25/25) shows no other file at either second. All six rivals are later local artifacts with local creation commands in the complete process-event list (base64 --decode → gcc → chmod → execute; mknod; nc-backpipe-phase collection). The two filenames are unchanged: colonel, definitelydontinvestigatethisfile.sh.

## Ruled out
- /tmp/colonel.c — CREATED 1534763456, local decode (`base64 --decode /tmp/colonel`, process event 1534763464).
- /tmp/colonelnew — CREATED 1534763660, local build (`gcc colonel.c -o colonelnew` 1534763701, `chmod +x`, `./colonelnew`).
- /tmp/backpipe — CREATED 1534763573, local FIFO (`mknod /tmp/backpipe p`).
- /tmp/loot.txt — CREATED 1534764186, nc-backpipe-phase local output.
- /tmp/suitecrm.sql — CREATED 1534765138, local dump output.
- /tmp/blargh.tgz — CREATED 1534765279 with MOVED_FROM, local archive.