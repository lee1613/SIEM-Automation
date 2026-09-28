# s1 - Q216 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dh,dp,ds,pn,ppn,ppa,pph,pa,paa,pap,ph,liuid,liuida,liuidp,liuat,mnl,mhl,ibc,obc,pr,puat,ppuat,sp,udid,iid,fss,fes,fst,fet,dest,dvc,fv,vendor_product
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 62

## Prior rounds
- R1–R2: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; endpoints .70.186 (7070s) and .24.128 (7102s); .8.103 proxy-relayed only.
- R3: Byte counts verified (volume, not duration); union 7113 SPL-verified; continuity proven by 5-min binning.
- R4–R5: udid corrected to deployment ID; .70.186/.8.103 share iid 35/36 = one physical host; all 49 sa enumerated; iexepler.exe resolved.
- R6: All 13 then-flagged fields covered; 7070 submitted solved.

## This round
### What I ran
- `da=45.77.53.176 | stats count,min(fss),max(fes) by sa | appendpipe [stats sum(count),min(first_start),max(last_end) | eval sa="UNION_ALL_POOL_FLOWS"] | eval duration_seconds=last_end-first_start` → .105.214: 219s (benign); .24.128: 7102s; .70.186: 7070s; UNION: 7841s.
- `sa=192.168.70.186 da=45.77.53.176 | stats count,min(fss),max(fes) | eval duration_seconds=last_end-first_start` → 3,815 flows, 1534759304→1534766374, 7070.

### What it means
FOUND: **7070 seconds**. Coverage of every field: **Endpoint identity** — sa: all 49 values enumerated; 4 Monero-participating — VERIFIED. iid: .70.186/.8.103 share 35/36 (one host); .24.128=33 — VERIFIED. liuid/liuidp/liuida/liuat: FyodorMalteskesko on Host A, AlBungstein on Host B, BSTOLL-L benign — VERIFIED. pa/paa/pap: SYSTEM (WMI) on Host A vs user on Host B — VERIFIED. udid: constant feed-wide, deployment ID — VERIFIED. **Mining indication** — da: complete powershell destination set (7 rows); 45.77.53.176 only sustained pool — VERIFIED. dh: Unknown on 4,830 pool flows; www.frothly.com on 2 benign — VERIFIED. dp: 443×4,829 + 3333×1 (only Stratum flow) — VERIFIED. ds: localdomain on all pool flows — VERIFIED. pn: all 60 values; powershell.exe = miner — VERIFIED. ppn: WmiPrvSE.exe deployment on Host A — VERIFIED. ph: miner hash traced to 3 addresses — VERIFIED. pph: 6 distinct — VERIFIED. mnl/mhl: empty on all pool flows — VERIFIED. pr: all TCP — VERIFIED. puat/ppuat: single value — VERIFIED. sp: 4,387 ephemeral — VERIFIED. ibc/obc: summed (14.8MB vs 2.38MB) — volume, not time — VERIFIED. **Timing** — fss/fes: all duration math — VERIFIED. fst/fet: text twins — VERIFIED. **Feed metadata** — dest/dvc/fv/vendor_product: single-valued constants — VERIFIED.

## Assumptions
- Selection: Host A (.70.186/.8.103) is "the endpoint" — 79% of pool flows, only Stratum-3333 flow, 6.2x pool bytes, SYSTEM-context WMI deployment, storyline identity — VERIFIED.
- Definition: elapsed window max(fes)−min(fss), no gaps — VERIFIED.
- Singular reading of "the endpoint" — UNVERIFIED externally (web_lookup ×3 empty); interpretive, defended by five discriminators.

## Ruled out
- 7102 (Host B: secondary, 21% of flows, no Stratum, user-context, re-fetch inside window); 7113 (union: two physical hosts —

_[truncated at 400 words]_

_Coverage check (runner): 35 field(s) of syslog are never named in your Coverage line: da, dest, dh, dp, ds, dvc, fes, fet, fss, fst, fv, ibc, iid, liuat, liuid, mhl, mnl, obc, pa, ph, pn, ppa, pph, ppn, ppuat, pr, puat, sa, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
