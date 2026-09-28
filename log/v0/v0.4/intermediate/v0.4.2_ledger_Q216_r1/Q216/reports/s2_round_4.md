# s2 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=0_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,pn,fss,fes,fst,fet,ibc,obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 82

## Prior rounds
R1: Confirmed feed (78,459 events); found the feed's only dp=3333 flow (192.168.70.186 → 45.77.53.176, powershell.exe, 112s); left 443 flows, pn tail, da enumeration open.
R2: Settled selection and coverage — 443 flows are sub-second C2 beacons (same process hash); full 22-row port enumeration shows 3333 is the only pool-port flow; powershell.exe on the endpoint contacts only 45.77.53.176 on 3333+443; rivals rejected.
R3: Showed the timing computation as query output (duration_seconds=112 from eval fes-fss) and the flow-shape contrast by port; settled p18/p19/p20 as VERIFIED.

## This round
Restatement of the answer chain from my own query outputs, in three parts. No new queries — all evidence below is from results already run and read in full.

### Coverage — every Monero-generation representation tested in this feed
1. **Canonical pool ports** — full 22-row dp enumeration of all 78,459 events: `dp=3333, count=1, endpoints=192.168.70.186, processes=powershell.exe, total_dur=112`; 4444/5555/7777 absent entirely.
2. **Miner process names** — `| top pn limit=20`: no mining-typical name; powershell.exe (4,835 events) owns the 3333 flow.
3. **Pool IP on other ports** — `da=45.77.53.176`: 4,832 events, dp∈{3333,443,80}, 3 source IPs, 2 process names; the 443/80 sets are beacons and Edge browsing.
4. **Non-standard port rival** — `dp=8080`: 26 events, 399s, internal 192.168.8.103/111 → 192.168.9.30 with chrome.exe — not a pool.
5. **Long-duration flows from the endpoint** — `| where dur>=60`: all Microsoft/Google/CDN cloud services by normal processes.

**Only one mining candidate flow matched: the single dp=3333 flow.**

### Selection — why the duration comes from that one flow
`sa=192.168.70.186 pn=powershell.exe | stats by da` returned exactly one row: da=45.77.53.176, count=3815, values(dp)=[3333,443]. Flow-shape stats by dp: **dp=3333 — 1 flow, 112s, 5,782,875B in / 177B out** (single sustained, heavy-inbound connection on the canonical Monero Stratum port); **dp=443 — 3,814 flows, avg 0.905s, median 1s, max 31s, 9.0MB in / 2.4MB out** (sub-second beaconing spread over ~2 hours — C2 check-in shape, not generation). A mixed-traffic span (7,841s over all 45.77.53.176 flows) covers three source IPs (192.168.105.214, 192.168.24.128, 192.168.70.186) and MicrosoftEdgeCP.exe browsing — the question says "the endpoint" (single), so it does not fit.

### Definition — the timing result, verbatim
From `sa=192.168.70.186 da=45.77.53.176 dp=3333 | eval duration_seconds=fes-fss | stats ...`:
> "flow_start_epoch": "1534762025", "flow_end_epoch": "1534762137", "duration_seconds": "112"

with flow_start_time="Mon Aug 20 10:47:05 2018", flow_end_time="Mon Aug 20 10:48:57 2018". "For how many seconds does the endpoint generate Monero" is satisfied by the Cisco NVM timing-field duration (fes − fss) of that one mining flow.

**Candidate value, unchanged: 112**