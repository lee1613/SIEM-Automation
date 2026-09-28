# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, sp, fss, fes, liuid, ibc, obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 85

## Prior rounds
- Round 1: located feed (78,459 events); full pn (60) and partial dp listings; found the lone dp=3333 flow (112s, powershell.exe, 192.168.70.186→45.77.53.176); flagged 4,829 powershell→pool:443 flows as unresolved alternative; several premises UNVERIFIED (R4 fail).
- Round 2: verified every premise; 443 flows proven beacons not mining; answer computed in SPL.

## This round
### What I ran
- Full dp listing (22/22) -> 3333 is the ONLY Monero Stratum port in the feed; no 4444/5555/7777/14444/14433.
- da=45.77.53.176 | eval dur=fes-fss | stats by sa,pn,dp -> 4 rows: 24.128 powershell:443 (1,015 flows, avg 1.25s, max 12s, sum 1,266s); 70.186 powershell:443 (3,814 flows, avg 0.91s, max 31s, sum 3,452s); 70.186 powershell:3333 (1 flow, 112s); Edge:80 (2 flows).
- pn=powershell.exe | eval dur=fes-fss | stats by sa,da,dp -> 7 rows, complete: only the 3333 flow is a sustained session to the pool; other destinations are Cloudflare/bit.ly/internal fetches (100-108s one-offs).
- dp=3333 | eval dur=fes-fss | stats sum(dur) -> **112** (SPL-computed).
- pn IN (iexeoler.exe,hdoor.exe) -> 7 flows, all internal 192.168.8.103→192.168.9.x ports 21/22/3306 — lateral movement, not mining.
- sa=45.77.53.176 -> 0 events (no reverse-direction flows).
- get_raw_events(dp=3333 event) -> powershell.exe parented by powershell.exe, ibc=5,782,875 obc=177, mhl/mnl empty; keyword search confirms exactly ONE event in the feed has dp=3333.

### What it means
FOUND: the mining act in this feed is uniquely evidenced by the single Stratum-port (3333) session. The 443 flows fail the mining-behavior check — avg ~1s, max 12–31s, ~1/sec for 2h from two hosts is beacon/C2 traffic, not mining (a miner holds few persistent connections). Only 192.168.70.186 performs the Stratum session, so "the endpoint" is unambiguous. Duration = fes−fss = 112 seconds, computed in SPL.

## Assumptions
- Coverage: mining as (a) miner-named process — none in all 60 pn values (VERIFIED); (b) Stratum-port flow — full 22-value dp listing, exactly one 3333 flow (VERIFIED); (c) sustained flow to pool under benign name — dur>60 sweep shows 2,415 groups, all visible are Dropbox/CrashPlan/Microsoft cloud IPs, none to 45.77.53.176 (VERIFIED for the pool IP; the 2,365 unreturned rows are other destinations, none powershell-to-pool per the complete 7-row powershell breakdown); (d) reverse-direction flows — 0 events (VERIFIED).
- Selection: 192.168.70.186 chosen over 192.168.24.128 because only it shows the Stratum session (VERIFIED: dp=3333 stats by sa). iexeoler.exe/hdoor.exe ruled out (VERIFIED: internal ports 21/22/3306).
- Definition: "generates Monero" = the Stratum mining session; duration = fes−fss of that single flow (VERIFIED: one event, sum(dur)=112 in SPL).
- Premise: 3333 is the Monero Stratum default port — external protocol knowledge, not verifiable in-feed; the flow's behavior (5.78MB in/177B out, powershell←powershell) corroborates.

## Ruled out
- powershell→45.77.53.176:443 flows as mining — avg 0.9–1.25s, max 12–31s, ~1/sec over 2h: beacon/C2 pattern, not mining sessions.
- iexeoler.exe, hdoor.exe — internal lateral movement (ports 21/22/3306), no pool contact.
- Other powershell destinations (Cloudflare, bit.ly, 192.168.9.30) — one-off ~100s fetches, not Stratum.

## Open questions for SH
- None blocking. If SH's intended answer is the 443-beacon span instead, the values would be 7,070s (70.186) / 7,113s (combined) — but those flows fail the mining-behavior check.

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_field_values: {"field": "da", "source": "cisconvmflowdata", "top_n": 15}` (15 of 2735 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | where dur>60 |…` (50 of 2415 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'bytes', 'packets', 'duration', 'app', 'url', 'flow direction', '_time']
- Rounds worked: 2/8  (iterations: 24, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata dp=3333 | stats count values(pn) values(sa) values(da) values(sp) min(fss) max(fes) values(fst) values(fet)
- index=botsv3 source=cisconvmflowdata pn=powershell.exe | stats count dc(sa) dc(da) dc(dp) min(fss) max(fes) values(sa) values(dp)
- index=botsv3 sourcetyle=syslog source=cisconvmflowdata sa=45.77.53.176 | stats count values(pn) values(da) values(dp) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count values(liuid) by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval dur=fes-fss | stats count avg(dur) min(dur) max(dur) perc25(dur) perc75(dur) sum(dur) min(fss) max(fes) by sa, pn, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count dc(pn) dc(sa) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) max(fes) by pn, sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) max(fes) values(dp) by pn, sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count values(pn) values(sa) values(dp) values(sp) min(fss) max(fes) dc(pn) dc(sa)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | eval dur=fes-fss | stats count sum(dur) as monero_seconds values(sa) values(da) values(pn) values(liuid) min(fst) max(fet)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(pn) values(sa) values(da) values(sp) min(fss) max(fes) values(fst) values(fet)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn IN (iexeoler.exe, hdoor.exe) | stats count values(sa) values(da) values(dp) values(liuid) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | eval dur=fes-fss | stats count max(dur) sum(dur) by sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count dc(sa) dc(da) dc(dp) min(fss) max(fes) values(sa) values(dp)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count min(fss) max(fes) by da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=45.77.53.176 | stats count values(pn) values(da) values(dp) min(fss) max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | where dur>60 | stats count max(dur) by pn, da, dp
