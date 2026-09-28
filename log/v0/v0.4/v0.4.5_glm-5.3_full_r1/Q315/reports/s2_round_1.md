# s2 - Q315 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=stream:http (POST /frothlyinventory/integration/saveGangster.action → 192.168.9.30:8080, hoth) | fields: form_data, rce_cmd, echo_tail; name searches in osquery:results, bash_history
**Insight:** partial
**Candidate:** colonel,definitelydontinvestigatethisfile.sh   **Confidence:** 60

## Prior rounds
- Established hoth (192.168.9.30) compromised via Struts2 RCE on saveGangster.action; candidate files colonel + definitelydontinvestigatethisfile.sh; related /tmp artifacts colonel.c, colonelnew, loot.txt, suitecrm.sql, blargh.tgz, backpipe.
- p2 (bash_history source ownership) REFUTED by v1; not rebuilt on this round.

## This round
### What I ran
- get_source_types → 102 sourcetypes confirmed.
- get_raw_events stream:http "saveGangster.action" (5 events) → RCE is OGNL `#cmd='...'` inside POST form_data, python-requests/2.18.4 from 192.168.8.103.
- `index=botsv3 sourcetype=stream:http uri_path=".../saveGangster.action" form_data=* | rex field=form_data "#cmd='(?<rce_cmd>[^']*)" | stats count values(_time) by rce_cmd` → 15 commands, complete enumeration (no clipping of the command list).
- Same base `| rex "#cmd='echo\s+[A-Za-z0-9+/=]+(?<echo_tail>[^']*)"` → 2 echo commands: C-source tail " >> /tmp/colonel"; JPEG tail "" (empty).
- Full-token search "definitelydontinvestigatethisfile" → 0 events in stream:http, 0 in osquery:results, 0 in bash_history.
- osquery /tmp timeline attempt → rex syntax error; not completed.

### What it means
- /tmp/colonel is a directly evidenced remote inbound write: `echo <base64 Ubuntu 16.04.4 kernel priv-esc C source> >> /tmp/colonel` at 11:35:17Z over the HTTP RCE channel.
- The only other remote content push in that channel is `echo <base64 JPEG (/9j/...)>` at 11:36:30Z. Its redirect is absent from the captured form_data (echo_tail empty) — either no redirect, or Stream truncated the form_data mid-base64 (JPEG base64 ~8.5KB vs the C source's ~7.5KB, which was captured complete with its redirect). `ls -lf /tmp` runs 24s later; its response body was not retrieved.
- definitelydontinvestigatethisfile.sh is NOT directly evidenced in the three feeds checked (0 events each). It remains the established candidate; unchecked: stream:tcp (nc channel 45.77.53.176:8088), linux_audit, ps, response bodies, and a partial-token search ("definitelydont") in case the form_data clip cut the filename mid-string.

## Ruled out
- /tmp/colonel.c — local derivative: `base64 --decode /tmp/colonel > /tmp/colonel.c` (11:37:36Z).
- /tmp/backpipe — local FIFO: `mknod /tmp/backpipe p` (11:39:33Z, 12:00:27Z).
- loot.txt, suitecrm.sql, blargh.tgz, colonelnew — none of the 15 RCE commands reference them; created outside the HTTP channel (nc backpipe phase), not remote inbound writes via the RCE channel.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
