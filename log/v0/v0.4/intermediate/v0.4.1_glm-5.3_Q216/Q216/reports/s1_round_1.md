# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=21_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,sp,dp,pn,ph,liuid,fss,fes,ibc,obc
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 60

## Prior rounds
- Round 1 (this round): confirmed feed, identified Monero endpoint and pool, computed duration metrics.

## This round
### What I ran
- get_sources/get_sourcetype_fields on cisconvmflowdata -> feed confirmed: 78,459 events, all Mon Aug 20 2018; fields sa/da/sp/dp/pn/ph/fss/fes/ibc/obc/liuid.
- `... | top limit=30 da` -> top externals: 34.215.24.225 (18,392), 45.77.53.176 (4,832).
- `... da=34.215.24.225 | top dp` and `da=45.77.53.176 | top dp` -> 45.77.53.176 serves dp=3333 (classic Monero stratum); 34.215.24.225 does not.
- `... dp IN (3333,4444,5555,7777,8888,9999,14444,14433,45700) | stats ... by dp` -> exactly ONE stratum-port flow in the entire feed: sa=192.168.70.186 -> 45.77.53.176:3333, pn=powershell.exe, ph=D3F8FADE..., fss=1534762025, fes=1534762137, ibc=5,782,875.
- `... sa=192.168.70.186 da=45.77.53.176 | stats count sum(eval(fes-fss)) as total_dur min(fss) as first_fss max(fes) as last_fes` -> 3,815 flows, total_dur=3,564, first_fss=1534759304, last_fes=1534766374.

### What it means
FOUND: 192.168.70.186 (AzureAD\FyodorMalteskesko) is the only endpoint in the whole NVM feed with a Monero stratum (3333) flow — to pool 45.77.53.176 via powershell.exe (hash D3F8FADE...), pulling 5.7MB in 112s. The same hash generated all 3,815 flows from that endpoint to the pool (443+3333), spanning 10:01:44–11:59:34. Span = 1534766374 − 1534759304 = **7,070 seconds**.

## Assumptions
- Monero activity = all flows from 192.168.70.186 to 45.77.53.176 (identical process hash on every flow) - VERIFIED via stats by sa/da/dp + values(ph).
- "Total seconds" = activity span (max fes − min fss) - UNVERIFIED interpretation; alternates: sum of durations = 3,564s; stratum session alone = 112s.
- 45.77.53.176 is the Monero pool - VERIFIED by stratum port + 5.7MB inbound byte profile; no other stratum port exists in the feed.

## Ruled out
- 34.215.24.225 - ports 443/9997 only, process splunkd.exe; no stratum indicator.
- All other stratum ports (4444,5555,7777,8888,9999,14444,14433,45700) - zero flows.
- 192.168.24.128 (AlBungstein) - same hash to pool on 443 only (1,015 flows, 1,266s sum) but never mines; not the generating endpoint.

## Open questions for SH
- Which aggregation does the answer key want: span (7,070), sum of flow durations (3,564), or the stratum session (112)?
- Should 192.168.24.128's 443-only pool traffic count toward the total?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
