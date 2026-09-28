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

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'app', 'bytes', 'packets', 'duration', '_time']
- Rounds worked: 2/8  (iterations: 19, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | stats count by dh | sort - count
- index=botsv3 source=cisconvmflowdata | stats count by pn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (da="37.187.*" OR da="217.182.*" OR da="104.20.208.*" OR da="104.20.209.*") | stats count values(dh) as dh values(sa) as sa values(pn) as pn values(dp) as dp by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da IN ("104.20.208.59","217.182.164.14","37.187.165.41","37.187.166.108","37.187.167.21","37.187.167.47") OR da="37.187.16*" | stats count values(dh) as dh values(sa) as sa values(pn) as pn min(fss) as start max(fes) as end by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da="45.77.53.176" | stats count min(fss) as first max(fes) as last sum(ibc) as in_b sum(obc) as out_b by sa, pn, dh, ds, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da="45.77.53.176" | stats count values(sa) as sa values(pn) as pn values(liuid) as user values(dp) as dp values(pr) as pr min(fss) as first_start max(fes) as last_end values(dh) as dh values(ibc) as ibc values(obc) as obc
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | stats count min(fss) as start max(fes) as end values(sa) as sa values(pn) as pn values(dp) as dp values(da) as da by dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | stats count sum(eval(fes-fss)) as total_seconds_mined min(fss) as first_flow_start max(fes) as last_flow_end eval(max(fes)-min(fss)) as span_seconds values(sa) as endpoint values(liuid) as user values(pn) as process
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | stats count sum(eval(fes-fss)) as total_seconds_mined min(fss) as first_flow_start max(fes) as last_flow_end values(sa) as endpoint values(liuid) as user values(pn) as process | eval span_seconds=last_flow_end-first_flow_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="minesweeperonline.com" | stats count values(sa) as sa values(pn) as pn values(da) as da min(fss) as start max(fes) as end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="www.brewertalk.com" | stats count values(pn) as proc values(liuid) as user min(fss) as first max(fes) as last by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(sa) as sa values(da) as da values(dh) as dh values(pn) as pn values(liuid) as user min(fss) as start max(fes) as end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn IN ("iexeplorer.exe","hdoor.exe") | stats count values(sa) as sa values(da) as da values(dh) as dh values(dp) as dp values(liuid) as user values(ppn) as parent min(fss) as first max(fes) as last by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn="Minesweeper.exe" | stats count values(sa) as sa values(dh) as dh values(da) as da values(dp) as dp min(fss) as start max(fes) as end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn="powershell.exe" | stats count values(da) as dest_ip values(dh) as dest_host values(dp) as dp values(ph) as proc_hash values(ppn) as parent values(liuid) as user min(fss) as first_start max(fes) as last_end by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa IN ("192.168.70.186","192.168.24.128") | stats count values(da) as dest_ip values(dh) as dest_host values(dp) as dp values(liuid) as users min(fss) as first max(fes) as last by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.24.128" da="45.77.53.176" | stats count sum(eval(fes-fss)) as total_dur avg(eval(fes-fss)) as avg_dur max(eval(fes-fss)) as max_dur min(fss) as first_start max(fes) as last_end values(ph) as proc_hash values(ppn) as parent values(liuid) as user sum(ibc) as in_bytes sum(obc) as out_bytes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.24.128" pn="powershell.exe" | stats count sum(eval(fes-fss)) as total_dur avg(eval(fes-fss)) as avg_dur max(eval(fes-fss)) as max_dur min(fss) as first_start max(fes) as last_end values(ppn) as parent_proc values(pa) as proc_acct values(liuid) as users values(mnl) as modules values(mhl) as module_hashes values(dh) as dh values(dp) as dp values(ph) as proc_hashes sum(ibc) as in_bytes sum(obc) as out_bytes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.247.131" (da="37.187.*" OR da="104.20.*" OR da="217.182.*") | stats count values(dh) as dest_host values(pn) as proc by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.247.131" fss>=1534772200 fss<=1534774000 | stats count values(dh) as dest_host values(pn) as proc values(pr) as proto min(fss) as flow_start max(fes) as flow_end values(ibc) as in_bytes values(obc) as out_bytes by da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.247.131" fss>=1534772200 fss<=1534774000 | stats count values(dh) as dh values(da) as da values(dp) as dp values(pr) as pr values(pn) as pn min(fss) as fss max(fes) as fes values(ibc) as ibc values(obc) as obc by sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.247.131" | stats count by liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.70.186" pn="powershell.exe" | sort 0 fss | streamstats current=f window=1 last(fes) as prev_fes | eval gap=fss-prev_fes | stats max(gap) as max_gap avg(gap) as avg_gap perc75(gap) as p75 count(eval(gap>60)) as gaps_over_60s count(eval(gap>10)) as gaps_over_10s
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.70.186" pn="powershell.exe" | stats count sum(eval(fes-fss)) as dur_sum min(fss) as first max(fes) as last sum(ibc) as in_b sum(obc) as out_b values(ppn) as parents values(pa) as accts by ph, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.70.186" pn="powershell.exe" | stats count sum(eval(fes-fss)) as total_dur avg(eval(fes-fss)) as avg_dur max(eval(fes-fss)) as max_dur min(fss) as first_start max(fes) as last_end values(ppn) as parent_proc values(pa) as proc_acct values(ppa) as parent_acct values(mnl) as modules values(mhl) as module_hashes values(iid) as iface values(ds) as ds values(dh) as dh values(dp) as dp sum(ibc) as in_bytes sum(obc) as out_bytes dc(ph) as n_hashes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa="192.168.70.186" pn="powershell.exe" | stats count values(da) as da values(dh) as dh values(dp) as dp min(fss) as first_start max(fes) as last_end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort count | head 12
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(_raw, "(?i)monero|xmr|stratum|cryptonight|minerd|pool\.") | stats count values(sa) as sa values(pn) as pn values(dh) as dh values(dp) as dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(dh, "(?i)(authedmine|cryptoloot|crypto-loot|deepminer|minergate|supportxmr|nanopool|monerohash|coinhive|coin-hive)") | stats count values(sa) as sa values(pn) as pn by dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(dh, "(?i)(xmr|monero|pool|mine|coin|crypto|hash)") | stats count by dh | sort - count
