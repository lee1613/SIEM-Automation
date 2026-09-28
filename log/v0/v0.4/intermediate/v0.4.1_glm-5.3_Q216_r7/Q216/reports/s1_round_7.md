# s1 - Q216 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dh,dp,ds,pn,ppn,ppa,pph,pa,paa,ph,liuid,liuida,mnl,mhl,ibc,obc,pr,puat,sp,udid,iid,fss,fes,dest,dvc,fv,vendor_product,fst,fet,liuat,liuidp,pap,ppuat
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 62

## Prior rounds
- R1–R2: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; endpoints .70.186 (7070s) and .24.128 (7102s); .8.103 proxy-relayed only.
- R3: Byte counts verified (volume, not duration); union 7113 SPL-verified; continuity proven by 5-min binning.
- R4–R5: udid corrected to deployment ID; .70.186/.8.103 share iid 35/36 = one physical host; all 49 sa enumerated; iexepler.exe resolved (15 proxy flows).

## This round
### What I ran
- `| stats dc(dest),values(dest),dc(dvc),values(dvc),dc(fv),values(fv),dc(vendor_product),values(vendor_product),dc(udid),values(udid)` → all five single-valued constants feed-wide.
- `da=45.77.53.176 | stats dc(pn),values(pn),dc(ppn),values(ppn),dc(ppa),values(ppa),dc(pph),dc(pr),values(pr),dc(puat),values(puat),dc(sp),dc(ppuat),values(ppuat)` → pn=2, ppn=3, ppa=3, pph=6, pr=1 (TCP), puat=1, sp=4,387 ephemeral, ppuat=1.

### What it means
FOUND: **7070 seconds**. Coverage of the 13 runner-named fields: dest, dvc, fv, vendor_product, udid — single-valued constants feed-wide, cannot carry mining or endpoint identity — VERIFIED. pn — 2 values on pool flows (powershell.exe = the miner; MicrosoftEdgeCP.exe = 2 benign) — VERIFIED. ppa — 3 values (SYSTEM = WMI deployment on Host A; AlBungstein/Fyodor = user context) — VERIFIED. pph — 6 distinct hashes on pool flows, miner hash traced feed-wide to 3 addresses — VERIFIED. ppn — 3 values (WmiPrvSE.exe = attacker deployment vector on Host A) — VERIFIED. ppuat, puat — single value (2), no signal — VERIFIED. pr — all pool flows TCP (6) — VERIFIED. sp — 4,387 distinct ephemeral ports, no signal — VERIFIED.

## Assumptions
- Selection: Host A (.70.186/.8.103) is "the endpoint" — 79% of pool flows, only Stratum-3333 flow, 6.2x pool bytes, SYSTEM-context WMI deployment, storyline identity — VERIFIED. Host B and union ruled out (see Ruled out).
- Definition: elapsed window max(fes)−min(fss), no gaps — VERIFIED.
- Singular reading of "the endpoint" — UNVERIFIED externally (web_lookup ×3 empty); interpretive, defended by the five discriminators.

## Ruled out
- Host B/.24.128 as "the endpoint" (secondary: 21% of flows, no Stratum, user-context, re-fetch inside window); union 7113 (two physical hosts); all 45 non-participating sa; udid as identity; BSTOLL-L; proxy onward paths; byte/sum-of-duration metrics; other pools.

## Open questions for SH
- None. SPL-verified alternates if the reading differs: 7113 (union), 7102 (Host B), 7841 (all pool flows incl. benign Edge).

## Final
7070 (Host A, 192.168.70.186) | 7102 (Host B, 192.168.24.128) | 7113 (union). **7070 is the submission value**: the singular wording "the endpoint" plus five independent Cisco NVM discriminators identify 192.168.70.186 as the Monero-generating endpoint, and its SPL-computed generation window is 1534766374−1534759304

_[truncated at 400 words]_

_Coverage check (runner): 35 field(s) of syslog are never named in your Coverage line: da, dest, dh, dp, ds, dvc, fes, fet, fss, fst, fv, ibc, iid, liuat, liuid, mhl, mnl, obc, pa, ph, pn, ppa, pph, ppn, ppuat, pr, puat, sa, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
