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

## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['stream:http', 'osquery:results'] sources=[] fields=['form_data', 'uri_path', 'src_ip', 'dest_ip', 'columns.target_path', 'columns.action', 'columns.time', '_time', 'host']
- Rounds worked: 5/5  (iterations: 32, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 definitelydontinvestigatethisfile | stats count by sourcetype, source
- index=botsv3 sourcestype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" form_data=* | rex field=form_data "#cmd='echo\s+(?<echo_head>[A-Za-z0-9+/=]{20})" | stats count values(bytes_in) as bytes_in values(bytes) as bytes values(_time) as times by echo_head
- index=botsv3 sourcetype=bash_history definitelydontinvestigatethisfile | stats count by host, source
- index=botsv3 sourcetype=linux_audit definitelydontinvestigatethisfile* | stats count by host, name
- index=botsv3 sourcetype=osquery:info host=hoth | stats count by name
- index=botsv3 sourcetype=osquery:results definitelydontinvestigatethisfile | stats count by source, columns.name
- index=botsv3 sourcetype=osquery:results host=hoth columns.target_path="/tmp/*" | stats count values(_time) as times by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth columns.target_path="/tmp/colonel" | stats count values(_raw) as raw_events
- index=botsv3 sourcetype=osquery:results host=hoth columns.target_path="/tmp/definitelydontinvestigatethisfile.sh" | stats count values(_raw) as raw_events
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.action="CREATED" columns.target_path IN ("/tmp/colonel","/tmp/definitelydontinvestigatethisfile.sh","/tmp/colonel.c","/tmp/colonelnew","/tmp/backpipe","/tmp/loot.txt","/tmp/suitecrm.sql","/tmp/blargh.tgz") | stats count values(columns.time) as created_time values(columns.uid) as uid by columns.target_path | sort created_time
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.target_path IN ("/tmp/colonel.c","/tmp/colonelnew","/tmp/backpipe","/tmp/loot.txt","/tmp/suitecrm.sql","/tmp/blargh.tgz") | stats count dc(columns.time) as distinct_file_times min(columns.time) as first_file_time max(columns.time) as last_file_time values(columns.action) as actions by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.target_path="/tmp/*" columns.action="CREATED" columns.time>=1534763000 columns.time<=1534766200 | stats count values(columns.time) as file_times by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.time IN (1534763317,1534763390) | stats count values(columns.action) as actions values(columns.size) as sizes values(columns.uid) as uids by columns.target_path, columns.time
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events columns.cmdline="*colonel*" | stats count values(_time) as times by columns.cmdline
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events columns.cmdline="*definitelydont*" | stats count values(_time) as times values(columns.cmdline) as cmdlines
- index=botsv3 sourcetype=osquery:results host=hoth | rex field=columns.path "(/tmp/[^/]+)" | search path=* | stats count values(_time) as times by columns.path
- index=botsv3 sourcetype=osquery:results host=hoth | stats count by name
- index=botsv3 sourcetype=stream:http definitelydontinvestigatethisfile | stats count by source, uri_path
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" form_data=* | rex field=form_data "#cmd='(?<rce_cmd>[^']*)" | stats count values(_time) as times by rce_cmd | sort rce_cmd
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" form_data=* | rex field=form_data "#cmd='echo\s+(?<echo_head>[A-Za-z0-9+/=]{20})" | stats count values(bytes_in) as bytes_in values(bytes) as bytes values(_time) as times by echo_head
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" form_data=* | rex field=form_data "#cmd='echo\s+[A-Za-z0-9+/=]+(?<echo_tail>[^']*)" | stats count values(_time) as time by echo_tail
- index=botsv3 sourcetype=stream:tcp (dest_ip=45.77.53.176 OR src_ip=45.77.53.176) | stats count dc(_time) as distinct_times by src_ip, dest_ip, src_port, dest_port
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.9.30 dest_ip=45.77.53.176 dest_port=8088 | stats count dc(_time) as distinct_times min(_time) as first max(_time) as last
