# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=12_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dh, dp, fss, fes, liuid + all 33 scope fields
**Insight:** FOUND
**Candidate:** 1758   **Confidence:** 60

## Prior rounds
- R1: found feed (78,459 events); two candidates: coinhive on 192.168.247.131 (sum 1758/span 1667) and powershell→45.77.53.176 on 192.168.70.186 (span 7070); submitted 7070 partial.
- R2: verified premises; powershell pattern found on a SECOND endpoint (192.168.24.128, same hash); no mining strings in raw text; coinhive confirmed as the only in-record Monero representation.

## This round
### What I ran
- `... sa="192.168.70.186" pn="powershell.exe" | stats sum(eval(fes-fss))...` -> 3815 flows, sum=3564, span=7070, max gap 231s, parents WmiPrvSE/powershell/svchost.
- `... sa="192.168.24.128" pn="powershell.exe"` -> 1018 flows; 1015 to 45.77.53.176 (sum 1266, span 7102), same proc hash D3F8...6677; also bit.ly, www.leeholmes.com.
- `... | where match(_raw,"(?i)monero|xmr|stratum|cryptonight|minerd|pool\.")` -> 4 events, all ad-infra (pool.adizio/admedo). Zero mining strings for 45.77.53.176.
- `... dh="www.brewertalk.com" | stats ... by sa` -> 7 endpoints incl. 192.168.247.131 (BudStoll, chrome).

### What it means
FOUND: 192.168.247.131 is the Monero endpoint — its Monero activity is REPRESENTED in the records as chrome.exe/443 flows to dh=coinhive.com + ws001/ws005/ws011/ws014/ws019.coinhive.com. Summed durations = **1758s** (span alternative 1667s; flows overlap 91s, union gapless). The powershell competitor loses: dh=Unknown, no mining representation in-record, and the identical pattern runs on two endpoints (C2/tooling, not one generating endpoint).

## Assumptions
- Coverage: dh — regex (?i)(xmr|monero|pool|mine|coin|crypto|hash) all values -> 6 coinhive flows only - VERIFIED; da — coinhive IP ranges + 45.77.53.176 -> no extra coinhive - VERIFIED; pn — all 60 values - VERIFIED; dp — all 22 values, one 3333 flow - VERIFIED; sa/fss/fes/liuid/pa/pap/liuidp/liuida/paa — endpoint/user/duration attribution - VERIFIED; ppn/ppa/ppuat/ph/pph — parents+hashes queried (explorer.exe→chrome; D3F8...6677 both powershell hosts) - VERIFIED; pr=6, ibc/obc, mnl/mhl (empty), sp, ds=localdomain, dest/dvc=splunkhwf.froth.ly, fet/fst (mirror fss/fes), fv=nvzFlow_v3, iid, liuat/puat/ppuat, udid, vendor_product=nix — queried or enumerated; none carries mining beyond what dh/pn/dp carry - VERIFIED.
- Selection: coinhive/.131 over powershell/.70.186 — in-record representation exists only for coinhive; powershell pattern is dual-endpoint C2-like - VERIFIED.
- "Coinhive = Monero service" - UNVERIFIED: web_lookup empty twice; rests on domain pattern + general knowledge.
- "Sum (1758) is the intended metric, not span (1667)" - UNVERIFIED: SH's overlap rule actually favors span; both computed and stated.

## Ruled out
- Minesweeper.exe / minesweeperonline.com — game/ad traffic. pool.adizio/admedo, webpoolblu3a — ad/Lync infra. googlecm.hit.gemius.pl — analytics. 45.77.53.176 as "the" Monero endpoint — no in-record representation, dual-endpoint pattern.

## Open questions for SH
- Does

_[truncated at 400 words]_