# s2 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,pn,fss,fes,fst,fet,ibc,obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 82

## Prior rounds
R1: Confirmed feed (78,459 events); found the feed's only dp=3333 flow (192.168.70.186 → 45.77.53.176, powershell.exe, 112s) as candidate; left 443 flows, pn tail, da enumeration open.
R2: Settled selection and coverage — 443 flows are sub-second C2 beacons (same process hash as the 3333 flow); full 22-row port enumeration shows 3333 is the only pool-port flow; powershell.exe on the endpoint contacts only 45.77.53.176 on 3333+443; rivals (3,564s / 3,452s / 7,841s / 399s) rejected.

## This round
### What I ran
- `sa=192.168.70.186 da=45.77.53.176 dp=3333 | eval duration_seconds=fes-fss | stats ...` → 1 row: flow_start_epoch=1534762025, flow_end_epoch=1534762137, **duration_seconds=112**, fst="Mon Aug 20 10:47:05 2018", fet="Mon Aug 20 10:48:57 2018", 5,782,875B in / 177B out, powershell.exe.
- `sa=192.168.70.186 da=45.77.53.176 | eval dur=fes-fss | stats count sum(dur) avg(dur) max(dur) perc50(dur) sum(ibc) sum(obc) by dp` → 2 rows: dp=3333 — 1 flow, 112s total/avg/max/median, 5.7MB in / 177B out; dp=443 — 3,814 flows, 3,452s total, avg 0.905s, median 1s, max 31s, 9.0MB in / 2.4MB out.

### What it means
The Cisco NVM timing computation, as query output: `duration_seconds = fes - fss = 1534762137 - 1534762025 = 112`.

Why that one flow and not the 443 beacons or any span: the 443 set is 3,814 sub-second beacons (median 1s, max 31s) spread over ~2 hours — C2 check-in shape, not generation; the 3333 flow is a single sustained 112-second connection with 5.7MB inbound on the canonical Monero Stratum port — the only mining-shaped flow. A span across mixed traffic (7,841s over all 45.77.53.176 flows) covers three source IPs and MicrosoftEdgeCP.exe browsing; the question says "the endpoint" (single), so mixed-traffic spans do not fit.

Coverage, restated from existing results: the full 22-row dp enumeration of all 78,459 events shows dp=3333 is the only canonical pool-port flow (4444/5555/7777 absent), and `sa=192.168.70.186 pn=powershell.exe | stats by da` returned exactly one row — 45.77.53.176 on ports 3333+443 only. Only 3333 is mining-shaped.

## Ruled out
- 443 flows to 45.77.53.176 as mining — 3,814 beacons, avg 0.905s, median 1s, max 31s: C2, not generation.
- 3,564s (all powershell.exe flows) / 3,452s (443 only) — include C2 beacons.
- 7,841s span of all 45.77.53.176 traffic — 3 source IPs + Edge browsing; not "the endpoint".
- 399s on dp=8080 — internal 192.168.8.x → 192.168.9.30 with chrome.exe; not a pool.
- dp 4444/5555/7777/14444 — absent from the full port enumeration.

**Candidate value, unchanged: 112**

_Premise updates refused by the runner:_
- p20 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
