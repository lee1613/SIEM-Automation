# s1 - Q216 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=10_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dh,dp,ds,pn,ppn,pa,paa,ph,pph,liuid,liuida,mnl,mhl,ibc,obc,pr,puat,sp,udid,iid,fss,fes,dest,dvc,fv,vendor_product
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 58

## Prior rounds
- R1: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; endpoints .70.186 (7070s) and .24.128 (7102s).
- R2: mnl/mhl empty on pool flows; .8.103 runs miner hash but only to internal proxy 192.168.9.30.
- R3: Byte counts verified (volume, not duration); union 7113 SPL-verified; continuity proven by 5-min binning.
- R4: udid corrected to deployment ID (constant feed-wide); .70.186/.8.103 share iid 35/36 = same physical host; BSTOLL-L (.247.131) benign; submitted 7070.

## This round
### What I ran
- `| stats count by sa | sort sa` → all 49 sa values enumerated, no truncation: Monero-participating = .70.186 (3,815 direct), .24.128 (1,015 direct), .8.103 (17 proxy-relayed), .105.214 (2 benign); other 45 values carry nothing.
- `sa=192.168.8.103 | stats count by pn` → iexepler.exe=15 flows to proxy 192.168.9.30:8080 (10:45–11:33 UTC) — resolves R2's 0-count contradiction (base-search token-match failure; eval pattern reaches it).
- `iid=0 | stats count by sa` → iid 0 is a shared/special interface across 7 hosts; the same-host proof for .70.186/.8.103 rests on iid 35/36, not iid 0.
- Host A window: `da=45.77.53.176 sa=192.168.70.186` → 1534759304→1534766374 = **7070s** (proxy flows fall inside).
- Host B window: `sa=192.168.24.128 da=45.77.53.176` → **7102s**. Union across both hosts: **7113s**.

### What it means
FOUND: endpoint model — Host A = .70.186 + .8.103 (same physical host: shared iid 35/36, same user FyodorMalteskesko, direct mDNS); Host B = .24.128 (iid 33, AlBungstein). Candidates: 7070 / 7102 / 7113. **7070 wins**: .70.186 carries 79% of pool flows, the dataset's only Stratum-3333 flow, 6.2x pool bytes, SYSTEM-context WMI deployment, and the compromised identity of the storyline. 7102 loses (.24.128 is secondary: 21% of flows, no Stratum, user-context; its 11:55 bit.ly fetch is inside its mining window — re-fetch, not delivery). 7113 loses (spans two physical hosts — environment duration, not "the endpoint"). No other sa value participates in Monero traffic, so none can change the answer.

## Assumptions
- Coverage: sa — all 49 values enumerated; 4 Monero-participating identified — VERIFIED. All other fields covered R1–R4 — VERIFIED.
- Selection: .70.186 over .24.128 (5 discriminators), .8.103 (same host as .70.186), .105.214/.247.131/.247.129 (no mining) — VERIFIED.
- Definition: elapsed window max(fes)−min(fss); no gaps — VERIFIED.
- Singular-endpoint reading of the wording — UNVERIFIED externally (web_lookup empty ×3); interpretive, documented.

## Ruled out
- All 45 non-participating sa values; udid as endpoint identity; BSTOLL-L;

_[truncated at 400 words]_

_Coverage check (runner): 34 field(s) of syslog are never named in your Coverage line: da, dest, dh, dp, ds, dvc, fes, fet, fss, fst, fv, ibc, iid, liuat, liuid, mhl, mnl, obc, pa, ph, pn, ppa, pph, ppn, ppuat, pr, puat, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
