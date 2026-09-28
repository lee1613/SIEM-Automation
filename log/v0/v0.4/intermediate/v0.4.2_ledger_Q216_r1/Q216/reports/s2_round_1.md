# s2 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn,ppn,sa,da,dp,sp,pr,fss,fes,fst,fet,ibc,obc
**Insight:** FOUND (partial — candidate held, verification incomplete)
**Candidate:** 112   **Confidence:** 40

## Prior rounds
None — round 1.

## This round
### What I ran
- get_sources sourcetype=syslog → confirmed source=cisconvmflowdata, 78,459 events (siblings cisconvmifdata 8, cisconvmsysdata 11).
- get_sourcetype_fields → timing fss/fes (epoch s) + fst/fet (strings); network sa/da/dp/sp/pr; process pn/ppn/pa; bytes ibc/obc; single udid.
- `| top pn limit=20` → no miner-typical name; powershell.exe 4,835 (6th).
- `| top dp limit=20` → 443/53/80 dominate; **dp=3333 exactly 1 event**; 4444/5555/7777 absent (≤1 event each).
- `dp=3333 | stats count min(fss) max(fes) values(...)` → 1 event: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, fss=1534762025, fes=1534762137, ibc=5,782,875, obc=177.
- `da=45.77.53.176 | stats ...` → 4,832 events, dp∈{3333,443,80}, pn∈{MicrosoftEdgeCP.exe,powershell.exe}, sa∈{.105.214,.24.128,.70.186}, span 1534758533–1534766374.

### What it means
The only flow in the entire 78,459-event feed to the canonical Monero Stratum port 3333 is a 112-second powershell.exe flow from 192.168.70.186 to 45.77.53.176 (10:47:05–10:48:57 UTC, Mon Aug 20 2018). Duration = fes−fss = 1534762137−1534762025 = **112 s**. That is the flow-log representation of Monero generation this round's network-behavior path found.

PARTIAL — three things keep this below full confidence, and the round ended (tools withdrawn) before they could be settled:
1. powershell.exe's other flows to 45.77.53.176 on 443/80 were never isolated — if they are pool traffic, the single-endpoint duration is larger.
2. The retired senior's rare-process-name path implies a rare pn is the miner; the pn tail below 67 events and the da values beyond the top 3 + 45.77.53.176 are unenumerated, so another pool IP is not ruled out.
3. The 3333 flow's byte profile (5.7MB in / 177B out) behaves like a download, not sustained mining — it may be miner retrieval rather than generation.

Next round, run first: `index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count values(dp) values(pn) min(fss) max(fes) sum(eval(fes-fss))`, then `| top da limit=20` and `| rare pn limit=20`.

## Ruled out
- dp 4444/5555/7777/14433/14444 — absent from top-20 dp (≤1 event each); only 3333 carries a pool-port flow.
- The full 45.77.53.176 set (4,832 events, 7,841s span) as the answer — spans 3 source IPs and MicrosoftEdgeCP.exe browsing; the question says "the endpoint" (single).
- Top-20 pn values as a separate miner process — none is mining-typical; powershell.exe owns the 3333 flow.

Method note: the final subtraction was done by hand after tools were withdrawn; the in-SPL form is `dp=3333 | eval dur=fes-fss | stats sum(dur)`.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
