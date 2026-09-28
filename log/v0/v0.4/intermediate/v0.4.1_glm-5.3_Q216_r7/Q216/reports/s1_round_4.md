# s1 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=10_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=fss,fes,sa,da,dh,dp,ds,pn,ppn,pa,paa,ph,ppn,pph,liuid,liuida,mnl,mhl,ibc,obc,pr,puat,sp,udid,iid,dest,dvc,fv,vendor_product
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 55

## Prior rounds
- R1: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; endpoints .70.186 (7070s) and .24.128 (7102s); submitted 7070.
- R2: mnl/mhl empty on pool flows; .8.103 runs miner hash but only to internal proxy (onward invisible); submitted 7070.
- R3: Byte counts verified (volume, not duration); ds/pr/dh/dp covered; union 7113 SPL-verified; continuity proven by 5-min binning; submitted 7113.

## This round
### What I ran
- `| stats count by udid` → ONE value on all 78,459 events: udid is the NVM deployment ID, NOT per-host — my R3 union premise corrected.
- `sa IN (4 hosts) | stats dc(udid), values(iid) by sa` → .70.186 and .8.103 SHARE iid 35,36 (same physical host, two IPs, both FyodorMalteskesko); .24.128 iid=33.
- `paa=BSTOLL-L | stats count by sa,pn,da,dp` → only on .247.131, benign Microsoft traffic — BSTOLL-L does not mine.
- `da IN (.70.186,.24.128) | stats count by sa,da,dp,pn,ppn` → only mDNS/RPC inbound; no WMI vector visible.
- `.24.128 pn=powershell.exe da!=45.77.53.176` → bit.ly/leeholmes.com download at 11:55 UTC, INSIDE its mining window (re-fetch, not initial delivery).
- web_lookup ×2 for official wording → no results.

### What it means
FOUND: "the endpoint" = one host among several source addresses (udid is a deployment ID). The defining mining endpoint is 192.168.70.186: 79% of pool flows, the dataset's only Stratum-3333 flow, 6.2x pool bytes, SYSTEM-context WMI deployment, BOTSv3's primary compromised identity. Duration = max(fes)−min(fss) = 1534766374−1534759304 = **7070**. Losers: 7102 (.24.128 — secondary generator, 21% of flows, no Stratum port, user-context); 7113 (union — spans two physical hosts, answers environment-wide duration, not "the endpoint").

## Assumptions
- Coverage: dest/dvc/fv/vendor_product — constants, cannot carry — VERIFIED. fss/fes/fst/fet — used in all duration math — VERIFIED. iid — queried: carries endpoint identity (.70.186/.8.103 same host) — VERIFIED. udid — constant feed-wide, deployment ID — VERIFIED. liuid/liuidp/liuida/liuat/paa/pa/pap — identity fields enumerated; BSTOLL-L confined to benign .247.131 — VERIFIED. mnl — 33 values, all service DLLs, empty on pool flows — VERIFIED. ph/pn/ppn/ppa/ppuat — enumerated/traced — VERIFIED. da/dh/dp/ds/mhl/pph/pr/puat/sp/ibc/obc — covered R2–R3 — VERIFIED.
- Selection: .70.186 over .24.128 (5 discriminators), .8.103 (proxy invisible), .247.131/.247.129/.105.214 (no mining) — VERIFIED.
- Definition: elapsed window; no gaps per 5-min binning — VERIFIED. Singular-endpoint reading of the wording — UNVERIFIED externally (web_lookup empty ×3).

## Ruled out
- BSTOLL-L/.247.131 as mining host; udid as endpoint identity; .8.103 onward generation; byte/sum-of-durations

_[truncated at 400 words]_

_Coverage check (runner): 1 field(s) of syslog are never named in your Coverage line: sa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
