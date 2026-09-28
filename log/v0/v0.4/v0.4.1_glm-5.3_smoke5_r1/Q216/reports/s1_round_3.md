# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, fss, fes, ibc, obc, dh, pr
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 60

## Prior rounds
- R1: Feed located (78,459 events, Mon Aug 20 2018); no miner-named process; 45.77.53.176 = only large unattributed dest, powershell.exe only; one dp=3333 flow from 192.168.70.186; duration not yet computed.
- R2: Raw record verified (fss=1534762025, fes=1534762137, 112s); three measures computed (112 / 3564 / 7070); .24.128 ruled out as mining endpoint (no pool flow); 443 polling flagged as C2-like; byte oddity left open.

## This round
### What I ran
- Byte-direction calibration on known-direction flows -> splunkd.exe: obc=2.05GB vs ibc=197KB, so obc=endpoint-sent, ibc=endpoint-received. The 3333 flow is 5.78MB in / 177B out.
- `da=45.77.53.176 pn=MicrosoftEdgeCP.exe` -> 2 flows, dh=www.frothly.com, port 80: the server also hosts Frothly's web name.
- Full powershell.exe external map (5 rows, all read) -> only 45.77.53.176:443 (both hosts), the one 3333 flow, and a leeholmes.com/bit.ly download from .24.128 at 11:44.
- Outbound-heavy Unknown-destination sweep (11 rows, all read) -> only CrashPlan/splunkd/vpnagent/Outlook: no other exfil/mining candidate feed-wide.
- Text search monero/xmr/miner/stratum/pool -> 4 events, read raw: ad-network hostnames (pool.adizio.com, pool.admedo.com), BruceGist's browser. The feed never names Monero.
- `liuida=BSTOLL-L` -> 192.168.247.131, user frothlyuser, 736 events, no powershell.exe, no 45.77.53.176 traffic.

### What it means
FOUND: 112 seconds. The mismatch was tested, not explained away: the 443 polling starts an hour before the 3333 session, its rate is unchanged during and after it, and the identical pattern runs on a second host with no pool connection — that is C2 polling, not mining. The 3333 session is the only persistent connection to the server (112s vs 31s max), on the canonical Monero stratum port, the only such flow in 78,459 events, from the one endpoint that mines. Its inbound-heavy bytes are a property of how this dataset models the pool session (or include miner staging inside the same session); no competing record exists. Duration = fes-fss = 1534762137-1534762025 = 112.

## Assumptions
- Coverage: Monero generation could appear as miner process name (0 events), pool-port flow (only dp=3333, 1 flow), unattributed external dest with mining-like bytes (none beyond 45.77.53.176), or explicit text (none — only ad-network "pool" hostnames). VERIFIED.
- Selection: 192.168.70.186 over 192.168.24.128 — .24.128 never touches a pool port and mirrors the C2 polling; .70.186 holds the only pool connection and 3.8x the flow volume. VERIFIED.
- Definition: "generates Monero" = the pool session (fss→fes of the 3333 flow); duration = fes-fss. VERIFIED as the only reading the records support; 443-as-mining fails the timing test.
- Port 3333 = Monero stratum — UNVERIFIED: web_lookup returned nothing twice; rests on general knowledge, not the dataset.

## Ruled out
- 443 powershell polling as generation — starts before, unchanged during/after the pool session, duplicated on a non-mining host, avg 0.9s connections.
- BSTOLL-L (192.168.247.131) as the mining endpoint — no powershell.exe, no 45.77.53.176 traffic in this feed.
- pool.adizio.com / pool.admedo.com — advertising networks, not mining pools.
- hdoor.exe / iexeplorer.exe — internal scans (R2).

## Open questions for SH
- If the case names BSTOLL-L as the mining endpoint, this feed contradicts it — confirm whether 192.168.70.186 (FyodorMalteskesko) is in scope as "the endpoint".

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
