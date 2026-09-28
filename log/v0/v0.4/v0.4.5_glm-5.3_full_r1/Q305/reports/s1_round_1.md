# s1 - Q305 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** sourcetype=Unix:ListeningPorts | source=Unix:ListeningPorts | fields=dest_port,pid,app,user,host,transport
**Insight:** FOUND
**Candidate:** 14356   **Confidence:** 95

## Prior rounds
None — first round.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; port-listing candidates: Script:ListeningPorts, Unix:ListeningPorts, netstat, lsof, openPorts.
- get_sourcetype_fields Script:ListeningPorts -> 867 Windows events, dest_port + pid fields, 15 distinct ports.
- get_sourcetype_fields Unix:ListeningPorts -> 490 events, dest_port + pid + app + user fields, 6 hosts.
- `index=botsv3 sourcetype IN ("Script:ListeningPorts","Unix:ListeningPorts") dest_port=1337 | stats ...` -> 1 event: host=hoth, app=netcat, user=root, pid=14356, TCP.
- `index=botsv3 sourcetype="Unix:ListeningPorts" dest_port=1337 | stats count list(_raw)` -> raw: "Mon Aug 20 11:48:24 UTC 2018 app=netcat dest_ip=* dest_port=1337 pid=14356 user=root fd=3u ip_version=4 dvc_id=254926 transport=TCP".
- `index=botsv3 sourcetype IN (5 port feeds) dest_port IN (1337,31337,1338,13370,7331)` -> 33 events, ALL dest_port=1337, host=hoth, app=netcat, pid=14356; zero for 31337 and other variants.
- `index=botsv3 sourcetype=netstat dest_port=1337` -> 32 events, all "tcp 0 1 *:1337 *:* LISTEN" on hoth (no PID field in this feed).
- get_sourcetype_fields lsof -> raw lsof columns (COMMAND/PID/NAME), no dest_port field.

### What it means
"Leet" port = 1337. The only listening record on 1337 anywhere in the port-listing feeds is netcat, running as root on Linux host hoth, with pid=14356 — read directly from the raw event. The netstat feed independently confirms a TCP LISTEN socket on *:1337 on the same host, so the record genuinely shows the act of listening, not a transient connection. No other leet-number port (31337, 1338, 13370, 7331) has any record in any of the five feeds, so 1337 is the only qualifying port and 14356 the only PID attached to it. The value is submittable as-is.

## Ruled out
- 31337 / 1338 / 13370 / 7331 as the "leet" port - zero records across all five port feeds.
- Script:ListeningPorts (Windows endpoints) - 867 events, 15 distinct ports, none 1337; no Windows host qualifies.
- netstat as PID source - shows LISTEN on *:1337 but carries no PID field; used only as corroboration.
- lsof - no dest_port field (raw lsof columns); not needed since Unix:ListeningPorts answers directly.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
