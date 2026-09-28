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


## What I'd tell my replacement
- Retired because: runaway: transport failure
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'dest_port', 'app', 'bytes', 'packets', 'duration']
- Rounds worked: 2/8  (iterations: 21, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | top limit=30 da
- index=botsv3 source=cisconvmflowdata | top limit=30 dp by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=34.215.24.225 dp=9997 | stats count values(sa) values(pn) values(fss) values(fes) values(fst) values(fet)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=34.215.24.225 | top limit=20 dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 dp=3333 | stats count values(sa) values(pn) values(fss) values(fes) values(fst) values(fet) values(ibc) values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) max(fes) by sa dp pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count values(liuid) values(pa) by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | top limit=20 dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp IN (3333,4444,5555,7777,8888,9999,14444,14433,45700) | stats count values(sa) values(da) values(pn) by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata liuida=BSTOLL-L | stats count values(sa) values(liuid) values(da) values(dp) values(pn)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata ph=D3F8FADE829D2B7BD596C4504A6DAE5C034E789B6A3DEFBE013BDA7D14466677 | stats count min(fss) as first_fss max(fes) as last_fes sum(eval(fes-fss)) as total_dur sum(ibc) as tibc sum(obc) as tobc by sa da dp | sort sa da dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count dc(da) values(sa) values(da) values(dp) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count min(fss) max(fes) by sa da dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count values(sa) values(da) values(dp) values(fss) values(fes) values(ibc) values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 dp=443 | stats count as flows avg(eval(fes-fss)) as avg_dur_s avg(ibc) as avg_in avg(obc) as avg_out min(fss) as first_fss max(fes) as last_fes | eval span_s=last_fes-first_fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count sum(ibc) as total_ibc sum(obc) as total_obc sum(eval(fes-fss)) as total_dur min(fss) as first_fss max(fes) as last_fes values(ph)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | stats count as flows sum(eval(fes-fss)) as total_monero_generation_seconds values(fss) as fss values(fes) as fes values(fst) as fst values(fet) as fet values(ibc) as bytes_in values(obc) as bytes_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | stats count values(ph) values(ppn) values(sp) values(ibc) values(obc) values(fss) values(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | stats values(mnl) as mnl values(mhl) as mhl values(pn) as pn values(ppn) as ppn values(ph) as ph values(pph) as pph values(liuid) as liuid values(pa) as pa values(ibc) as ibc values(obc) as obc values(fss) as fss values(fes) as fes values(sp) as sp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=443 | stats count avg(eval(fes-fss)) as avg_dur perc25(eval(fes-fss)) as p25_dur perc75(eval(fes-fss)) as p75_dur max(eval(fes-fss)) as max_dur avg(ibc) as avg_in avg(obc) as avg_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=443 | stats count sum(ibc) sum(obc) avg(eval(fes-fss)) min(eval(fes-fss)) max(eval(fes-fss))
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | bin fss span=5m as t | stats count sum(eval(fes-fss)) as dur sum(ibc) as inb sum(obc) as outb values(dp) as ports by t | sort t
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | sort fss | streamstats window=1 current=f last(fes) as prev_fes | eval gap=fss-prev_fes | stats max(gap) as max_gap_s avg(gap) as avg_gap_s perc95(gap) as p95_gap_s count as flows
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count sum(eval(fes-fss)) as dur sum(ibc) as inb sum(obc) as outb by dp ppn pn | sort dp ppn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count sum(eval(fes-fss)) as dur sum(ibc) as inb sum(obc) as outb min(fss) as first max(fes) as last by dp ph pn | sort dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count sum(eval(fes-fss)) as total_dur sum(ibc) as total_ibc sum(obc) as total_obc min(fss) as first_fss max(fes) as last_fes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count values(dp) values(pn) values(fss) values(fes) values(fst) values(fet) values(ibc) values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | eval dur=fes-fss | where dur>60 | stats count values(pn) values(ph) sum(dur) as total_dur values(fst) as fst values(fet) as fet by da dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | eval dur=fes-fss | where ibc>1000000 | stats count values(pn) values(dp) sum(ibc) as inb sum(obc) as outb sum(dur) as total_dur by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count dc(da) values(da) values(dp) values(pn) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=30 da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=30 dp by da
