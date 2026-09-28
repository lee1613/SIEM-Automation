# s2 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,sp,pn,ppn,liuid,fss,fes,ibc,obc,dh,mnl,mhl
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 88

## Prior rounds
- s1 R1-R2 (retired): dp=3333 candidate via CoinHive/keyword path; unresolved pivot to another hypothesis.
- My R1: feed mechanics learned; complete dp enumeration (22 ports, dp=3333 unique in 78,459 events); 4 patterns to pool IP profiled; raw event read; submitted 112 @ 82.
- My R2: duration SPL-computed (112); domain axis closed (CoinHive browser flows on 192.168.247.131, 1758s — excluded per q3); leeholmes.com flow identified; submitted 112 @ 85.

## This round
### What I ran
- web_lookup x3 (port 3333 = Monero stratum) -> no snippets returned; external fact untestable, so p4 settled feed-based per q5.
- `| stats count, dc(sa), values(dp) by pn` (both orderings) -> all 60 process names seen (top-50 by count + 25 rarest ascending); no miner binary; powershell.exe (4,835 flows, 3 endpoints) is the only process touching dp=3333.
- `| stats ... by ppn` -> all 24 parent names; only powershell.exe-as-parent touches dp=3333.
- `| where match(mnl,...) OR match(mhl,...)` (xmr|miner|stratum|cryptonight|monero|pool) -> 0 events.
- `sa=45.77.53.176` -> 0 flows (reverse-flow axis closed).
- `dp=3333 | eval dur=fes-fss | stats count as qualifying_flows, sum(dur) as total_seconds, ...` -> 1 flow, 112 seconds.

### What it means
The feed has no direct Monero label (qualifying record: dh="Unknown", mnl/mhl empty; module scan 0 matches feed-wide), so the act is identified from this feed alone by elimination across every representation axis, each searched to completion: port (22 values, dp=3333 unique), domain (only CoinHive browser flows + false positives), process (60 names, no miner binary), parent (24 names), modules (0), reverse flows (0), duration/byte pattern (complete powershell and pool-IP profiles). The single surviving record is the 112-second powershell.exe session 192.168.70.186 -> 45.77.53.176 (10:47:05-10:48:57), 5,782,875 bytes in vs 177 out — pool-job byte asymmetry, the only non-standard service port the APT malware process uses, destined to the same IP that receives its 4,829 C2 beacons. Duration from NVM timestamps only, computed in SPL: sum(fes-fss) = 112, already integral so rounding is a no-op. p4 and p6 both settled with these outputs.

## Ruled out
- CoinHive browser flows (chrome.exe, 192.168.247.131, 6 flows, 1758s) — browser JavaScript mining on a different endpoint over HTTPS; not the stratum-style service connection; alternative answer 1758 rejected.
- powershell.exe -> 104.31.76.227:80 (147s, 5.19MB) — dh=www.leeholmes.com, legitimate site.
- dp=443 powershell beacons to 45.77.53.176 (4,829, avg 0.9s/2.4KB) — C2 check-ins.
- Edge dp=80 to 45.77.53.176 (2, avg 10.6KB) — browser fetch.
- hdoor.exe (ports 21/22/3306, internal 192.168.9.x) — lateral movement, not mining.
- iexepler.exe:8080 (15 flows) — misspelled-explorer artifact, not a mining port.
- External port-fact verification — web_lookup returned no snippets on three attempts.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints,…` (50 of 60 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints,…` (25 of 60 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['dp', 'sa', 'da', 'dh', 'pn', 'ppn', 'pa', 'liuid', 'fss', 'fes', 'fst', 'fet', 'ibc', 'obc']
- Rounds worked: 3/8  (iterations: 32, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | stats count by dp | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=3333 OR sp=3333) | eval dur=fes-fss | stats count, sum(dur) as total_seconds, values(sa) as src, values(da) as dst, values(pn) as proc, values(fss) as flow_start, values(fes) as flow_end by dp, sp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=104.31.76.227 | stats count, values(dh) as host, values(pn) as proc, values(ppn) as parent, values(liuid) as user, values(mnl) as modules, values(fss) as starts, values(fes) as ends, values(ibc) as in_bytes, values(obc) as out_bytes by sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval dur=fes-fss | stats count as flows, avg(dur) as avg_dur, max(dur) as max_dur, avg(ibc) as avg_ibc, max(ibc) as max_ibc, avg(obc) as avg_obc, dc(sp) as distinct_src_ports, min(fss) as first_start, max(fes) as last_end by sa, pn, dp | eval avg_dur=round(avg_dur,1), avg_ibc=round(avg_ibc,0), avg_obc=round(avg_obc,0) | sort -flows
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval dur=fes-fss | stats count as flows, round(avg(dur),1) as avg_dur, max(dur) as max_dur, round(avg(ibc),0) as avg_ibc, max(ibc) as max_ibc, round(avg(obc),0) as avg_obc, dc(sp) as distinct_src_ports, min(fss) as first_start, max(fes) as last_end by sa, pn, dp | sort -flows
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, min(fss) as start, max(fes) as end, sum(ibc) as bytes_in, sum(obc) as bytes_out by sa, pn, dp | sort sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, min(fss), max(fes), values(pn), values(sa), values(dp) by da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | eval dur=fes-fss | stats count, sum(dur) as total_dur, values(dur) as durs, values(sa) as src, values(pn) as proc, values(fss) as starts, values(fes) as ends by dh, da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | eval dur=fes-fss | stats count as qualifying_flows, sum(dur) as total_seconds, min(fss) as first_start, max(fes) as last_end, values(sa) as src, values(da) as dst, values(pn) as proc, values(ppn) as parent, values(liuid) as user, values(ibc) as bytes_in, values(obc) as bytes_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count, values(sa), values(da), values(dh), values(pn), values(ppn), values(pa), values(fss), values(fes), values(fst), values(fet), values(ibc), values(obc), values(pr), values(sp), values(liuid) by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | eval dur=fes-fss | stats count as flows, sum(dur) as total_dur, max(dur) as max_dur, sum(ibc) as total_ibc, max(ibc) as max_ibc, dc(sa) as endpoints, values(sa) as srcs, min(fss) as first_start, max(fes) as last_end by da, dp | sort -total_ibc
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=45.77.53.176 | stats count, values(da) as dest_ips, values(dp) as ports, values(pn) as procs, values(sa) as srcs
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | where dur>=60 OR ibc>=1000000 | stats count as flows, max(dur) as max_dur, max(ibc) as max_ibc, dc(sa) as endpoints, values(pn) as procs by dp, da | sort -max_ibc
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints, values(dp) as ports by pn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints, values(dp) as ports by ppn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints, values(dp) as ports, values(da) as dest_ips by pn | sort count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, values(da) as dest_ips, values(dp) as ports by dh | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(dh, "(?i)(pool|xmr|monero|stratum|coinhive|mine|minexmr|nanopool|supportxmr)") | stats count, values(da) as dest_ips, values(dp) as ports, values(pn) as procs, values(sa) as srcs by dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(mnl, "(?i)(xmr|miner|stratum|cryptonight|monero|pool)") OR match(mhl, "(?i)(xmr|miner|stratum|cryptonight|monero|pool)") | stats count, values(pn) as procs, values(sa) as srcs, values(da) as dest_ips, values(dp) as ports by mnl
