# s1 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=syslog | source=cisconvmflowdata (+ cisconvmsysdata, cisconvmifdata for identity) | fields=pn, sa, da, dp, fss, fes, ibc, obc, dh, iid, liuidp
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 65

## Prior rounds
- R1: Feed located (78,459 events); no miner-named process; 45.77.53.176 = only large unattributed dest, powershell.exe only; one dp=3333 flow from 192.168.70.186.
- R2: Raw record verified (fss=1534762025, fes=1534762137 = 112s); three measures computed (112/3564/7070); .24.128 ruled out (no pool flow).
- R3: Byte direction calibrated (obc=endpoint-sent); 443 rate unchanged before/during/after the 3333 session; no Monero text in feed; BSTOLL-L ruled out.

## This round
### What I ran
- 443 coverage: `sort 0 fss | streamstats max(fes) as prev_max by sa | eval gap=fss-prev_max | stats sum(idle) ...` -> .70.186 idle 4,737s inside a 7,070s span (33% coverage, max gap 230s); .24.128 18% coverage.
- Rival scan: `pn=powershell.exe | where dur>45` -> 5 rows, all read: the 3333 flow (112s, 5.78MB, external, dh=Unknown) plus internal scans (<4KB), bit.ly (530B), leeholmes.com:80 download from .24.128 (5.19MB, end of window).
- Identity: cisconvmsysdata (11 events, all read) + cisconvmifdata -> vsn=FYODOR-L.froth.ly at 11:12:07 with iid=35/MAC 00:0c:29:55:51:1a; `stats values(iid), values(liuidp) by sa` -> 192.168.70.186 carries iid=35, sole user FyodorMalteskesko.

### What it means
FOUND: 112 seconds. Ignoring port semantics entirely, the 3333 session is still the only record that behaves like the act: sustained (112s vs 0.9s avg), bulk (5.78MB), external and unattributed, from the implant process on the endpoint with the heaviest implant activity. Every rival fails: the 443 polling is intermittent (33% wall-clock coverage, gaps to 230s) and duplicated on a host that never touches a pool port — C2; the leeholmes.com fetch is plain HTTP from a different endpoint at the window's end — staging; the internal scans are lateral movement. No record feed-wide shows outbound-heavy sustained transfer either, so the 3333 session is the feed's representation of Monero generation. Duration = fes-fss = 1534762137-1534762025 = 112. Endpoint identity from the data: 192.168.70.186 = FYODOR-L.froth.ly (iid=35 ↔ sysdata vsn, user FyodorMalteskesko).

## Assumptions
- Coverage: Monero generation as process name (0 events), pool-port flow (1: dp=3333), sustained bulk transfer to unattributed external (only the 3333 flow), explicit text (none) — VERIFIED.
- Selection: 3333 session over 443 polling (intermittent, 33% coverage, duplicated on non-mining host), over leeholmes.com (plain HTTP, named host, different endpoint, end of window), over internal scans — VERIFIED.
- Endpoint identity: 192.168.70.186 = FYODOR-L.froth.ly via iid=35 ↔ sysdata vsn at 11:12:07 and sole user FyodorMalteskesko — VERIFIED.
- Definition: duration = fes-fss of the pool session — VERIFIED.
- Port 3333 = Monero stratum — UNVERIFIED externally (web_lookup empty twice); rests on the record's feed-wide uniqueness and the question's premise.

## Ruled out
- 443 powershell polling as generation — intermittent (33% coverage), avg 0.9s, identical on .24.128, unchanged around the 3333 session.
- leeholmes.com / bit.ly fetches — staging download, port 80, different endpoint, 11:44.
- Internal scans from 192.168.8.103 — lateral movement, tiny bytes.
- BSTOLL-L (192.168.247.131) — no powershell.exe, no 45.77.53.176 traffic.

## Open questions for SH
- None material; the residual is the byte-direction oddity (inbound-heavy), which no rival record resolves — the feed contains no outbound-heavy sustained session anywhere.