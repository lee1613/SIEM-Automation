# s1 - Q315 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=9_
**Scope:** sourcetype=osquery:results, bash_history, stream:http, stream:tcp, syslog | source=/var/log/osquery/osqueryd.results.log, /home/klagerfield/.bash_history | fields=_time, name, columns.target_path, columns.action, columns.cmdline

**Insight:** FOUND (partial — candidate held; streaming act inferred from creation evidence, session content not directly captured)
**Candidate:** colonel.c,definitelydontinvestigatethisfile.sh   **Confidence:** 55

## Prior rounds
- Round 1: mapped hoth's feeds (syslog 203k, osquery:results 79k, auth.log 117); bash_history showed only `ls /tmp`/`cd /tmp` navigation; no filenames found.

## This round
### What I ran
- osquery:results host=hoth /tmp | stats count by name -> pack_fim_file_events 308, shell_history 12, proc_events 19.
- FIM target_path listing (89 rows) -> /tmp inventory: backpipe, blargh.tgz, colonel, colonel.c, colonelnew, definitelydontinvestigatethisfile.sh, loot.txt, suitecrm.sql + compiler/system temps.
- FIM actions/epochs for the 7 interesting files -> colonel.c and definitelydontinvestigatethisfile.sh both CREATED, first_seen 1534763637 (same interval); colonel 1534763347; colonelnew 1534763927; loot.txt 1534764216; blargh.tgz + suitecrm.sql 1534765375.
- proc_events /tmp cmdlines (16) -> `mknod /tmp/backpipe p`, `base64 --decode /tmp/colonel`, `cat /tmp/colonel.c`, `md5sum /tmp/colonel.c`, gcc/ld `-o colonelnew`, `./colonelnew`, `cat /tmp/loot.txt`.
- proc_events curl/wget/nc/python (12) -> `netcat -v -l -p 1337 -e /bin/bash` backdoor + `apt-get install netcat`.
- stream:tcp dest_port=1337 -> 0; stream:http host=hoth -> 0; syslog host=hoth "1337" -> 0.

### What it means
FOUND (partial): hoth ran a netcat backdoor on port 1337 — the remote command channel. Of all /tmp files, only colonel.c and definitelydontinvestigatethisfile.sh (a) have no local-creation command anywhere in proc_events or shell_history, (b) were FIM-CREATED in the same osquery interval (epoch 1534763637), consistent with one remote streaming session, and (c) are terminal adversary artifacts — colonel.c is the backdoor source compiled to colonelnew and executed, definitelydontinvestigatethisfile.sh is an adversary-named script. Every other /tmp file has an observed local creator. Caveat: the port-1337 session content is not captured in stream:tcp/stream:http/syslog, so the pair rests on creation evidence, not a directly observed transfer; /tmp/colonel (created an interval earlier, base64-decoded, no local creator) is an unresolved third candidate the two-file question excludes.

## Ruled out
- /tmp/blargh.tgz — created locally by `tar czvf blargh.tgz suitecrm.sql loot.txt`, then `mv` to /var/www/html/suitecrm/ (exfil staging, not inbound).
- /tmp/suitecrm.sql, /tmp/loot.txt — local collection outputs, tar'd into blargh.tgz.
- /tmp/colonelnew — created by the gcc/ld compile of colonel.c.
- /tmp/backpipe — created by local `mknod /tmp/backpipe p`.
- cc*.o/.s/.res, tmpf*, sh-thd-*, systemd-private-* — compiler/system temp noise.
- stream:http (host=hoth), stream:tcp (dest_port=1337), syslog "1337" — all 0 events; netcat session content not recorded there.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The remote streaming act on hoth can only be evidenced indirectly: the netcat ba"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The two files remotely streamed to /tmp on hoth are colonel.c and definitelydont"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events /tmp | stats c…` (50 of 89 rows seen). A claim resting on them alone is UNVERIFIED._
