# s2 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=9_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,sp,pn,ppn,liuid,fss,fes,ibc,obc,dh,mnl,mhl
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 85

## Prior rounds
- s1 R1-R2 (path retired): established the 192.168.70.186 -> 45.77.53.176 dp=3333 candidate (112s) via a CoinHive/domain-keyword route, then pivoted to another hypothesis without resolving it; SH retired the path and filed p1-p3.
- My R1: learned feed mechanics (fss/fes epoch flow start/end, ibc/obc bytes); complete dp enumeration (22 ports, all rows) — dp=3333 occurs once in 78,459 events; profiled all 4 patterns to the pool IP; read the raw dp=3333 event; submitted 112 @ 82 with the subtraction not yet executed in SPL.

## This round
### What I ran
- `(dp=3333 OR sp=3333) | eval dur=fes-fss | stats count, sum(dur) as total_seconds ... by dp, sp` -> 1 flow, total_seconds=112; sp=3333 adds nothing.
- get_raw_events keyword=1534762025 -> full dp=3333 record: dh="Unknown", mnl="''", mhl="''" — the feed carries NO direct Monero/stratum/pool label; identification must be behavioral.
- `| where match(dh,"(?i)(pool|xmr|monero|stratum|coinhive|mine|...)")` -> 10 rows, closing the domain axis: only CoinHive domains (chrome.exe, 192.168.247.131) plus false positives (minesweeperonline.com game, pool.adizio/pool.admedo ad networks, webpoolblu3a16.infra.lync.com Skype). No pool/stratum domain resolves for 45.77.53.176.
- `dh="*coinhive*" | eval dur=fes-fss | stats ...` -> 6 flows, all chrome.exe on 192.168.247.131: 124+4+12+2+13+1603 = 1758s total.
- `da=104.31.76.227 | stats ... by sa, dp` -> the competing 147s/5.19MB powershell.exe flow is to dh=www.leeholmes.com (user AlBungstein) — a legitimate website, not a pool.

### What it means
The feed gives no protocol label, so per SH's q3/q4 guidance the act is the unique stratum-style service connection: dp=3333 appears exactly once in the whole feed — a single powershell.exe session from 192.168.70.186 to 45.77.53.176 (10:47:05-10:48:57) pulling 5,782,875 bytes in against 177 out. Every competitor is materially different: the dp=443 powershell beacons to the same IP average 0.9s/2.4KB (C2 check-ins, 4,829 flows), the Edge dp=80 flows average 10.6KB (browser), the leeholmes.com flow is a legit-site download, and the CoinHive flows are browser JavaScript mining on a different endpoint over ordinary HTTPS — not the stratum-style connection q3 names, and not "the endpoint" of the APT narrative. Duration from the NVM timestamps, computed in SPL: sum(fes-fss) = 112 seconds — already integral, so rounding is a no-op.

## Ruled out
- CoinHive flows (6, chrome.exe, 192.168.247.131, 1758s total) — browser mining on another endpoint via HTTPS web fetches; filed as a premise so SH can overturn it (alternative answer 1758).
- powershell.exe -> 104.31.76.227:80 (147s, 5.19MB) — www.leeholmes.com, legitimate site.
- dp=443 powershell beacons to 45.77.53.176 (4,829) — avg 0.9s/2.4KB C2 check-ins.
- Edge dp=80 to 45.77.53.176 (2) — browser fetch of the pool web page.
- minesweeperonline.com, pool.adizio.com, pool.admedo.com, webpoolblu3a16.infra.lync.com — domain-keyword false positives.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | where dur>=60 …` (50 of 2047 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, values(da) as dest_i…` (25 of 1573 rows seen). A claim resting on them alone is UNVERIFIED._
