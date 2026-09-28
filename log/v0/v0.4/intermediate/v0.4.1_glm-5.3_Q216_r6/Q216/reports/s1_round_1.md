# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=21_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dh, dp, fss, fes, liuid
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 60

## Prior rounds
- Round 1 (this round): confirmed feed (78,459 events); enumerated pn/dh/dp; found two Monero candidates; computed spans/sums.

## This round
### What I ran
- `...source=cisconvmflowdata | stats count by dp` -> 22 ports; dp=3333 (Monero stratum) has exactly 1 flow.
- `... dp=3333 | stats ...` -> sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, liuid=AzureAD\FyodorMalteskesko.
- `... sa="192.168.70.186" pn="powershell.exe" | stats count values(da)... min(fss) max(fes)` -> 3,815 flows, all to 45.77.53.176, dh=Unknown, dp=[3333,443], 1534759304->1534766374.
- `... dh="*coinhive*" | stats sum(eval(fes-fss))...` -> 6 flows from 192.168.247.131 (chrome.exe, BudStoll), sum=1758, span=1667.

### What it means
FOUND: endpoint 192.168.70.186 (FyodorMalteskesko) generates Monero traffic as 3,815 powershell.exe flows to 45.77.53.176 (dh=Unknown) on 443/3333 — the only stratum-3333 flow in the feed. Span = 1534766374-1534759304 = **7070 seconds**. Competing candidate: coinhive browser mining from 192.168.247.131 (1758s sum / 1667s span) — not eliminated.

## Assumptions
- Coverage: dh — searched via regex (?i)(xmr|monero|pool|mine|coin|crypto|hash) over all values -> coinhive.com+ws0XX only; pn — all 60 values enumerated -> powershell.exe selected; dp — all 22 values enumerated -> 3333 unique; da — coinhive IP ranges and 45.77.53.176 searched; sa/fss/fes/liuid — used for endpoint/duration; mnl/mhl (module lists) could carry a miner DLL name — UNVERIFIED, never searched.
- Selection: powershell.exe on 192.168.70.186 chosen over coinhive on 192.168.247.131 because of the stratum-3333 flow and sustained traffic (3,815 flows) - VERIFIED; coinhive alternative NOT ruled out.
- "45.77.53.176 is a Monero pool" - UNVERIFIED: inferred from port 3333 + powershell only; dh=Unknown; some flows to this IP resolve to www.frothly.com.
- "Span (not summed durations) is the intended metric" - UNVERIFIED: sum over 3,815 flows not computed (calls exhausted).

## Ruled out
- Minesweeper.exe (172.16.133.131) — Microsoft/Vungle ad-game traffic only.
- minesweeperonline.com (192.168.105.214, Edge) — game site.
- pool.adizio.com, pool.admedo.com, webpoolblu3a.infra.lync.com — ad/Lync infra, not crypto.

## Open questions for SH
- Is the intended Monero activity the powershell.exe/stratum traffic on 192.168.70.186, or BudStoll's coinhive browsing on 192.168.247.131?
- Should the total be the span (min fss -> max fes) or the sum of per-flow durations?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Coverage check (runner): 25 field(s) of syslog are never named in your Coverage line: dest, ds, dvc, fet, fst, fv, ibc, iid, liuat, obc, pa, ph, ppa, pph, ppn, ppuat, pr, puat, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
