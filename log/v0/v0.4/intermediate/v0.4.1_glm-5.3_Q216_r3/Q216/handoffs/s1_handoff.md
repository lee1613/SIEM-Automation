# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=8_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=fss,fes,sa,da,sp,dp,pn,ppn,ph,liuid,ibc,obc
**Insight:** FOUND
**Candidate:** 3564   **Confidence:** 90

## Prior rounds
- R1: Confirmed feed (78,459 events); found powershell.exe→45.77.53.176 as the Monero pattern; ruled out hdoor.exe, iexepler.exe, svchost:58868, splunkd:9997; computed 3,564s for 192.168.70.186; selection vs 192.168.24.128 unproven.
- R2: Settled the selection on five independent flow indicators; verified duration data quality; confirmed 3333 flow belongs to the same activity; answer unchanged.

## This round
### What I ran
- Side-by-side `| stats count dc(dp) sum(eval(fes-fss)) avg(ibc) avg(obc) by sa` over da=45.77.53.176 -> 70.186: 3,815 flows, ports 443+3333, 3,564s; 24.128: 1,015 flows, 443 only, 1,266s.
- `dp=3333` detail -> 70.186, hash ...6677, parent powershell.exe, ibc=5,782,875B, 112s.
- `| stats by sa ph` -> 70.186 runs TWO powershell.exe hashes (...6677: 3,622 flows incl. 3333; ...6600: 193 flows), parents WmiPrvSE.exe/powershell.exe/svchost.exe, accounts FyodorMalteskesko + SYSTEM; 24.128 runs ONE hash, parent powershell.exe only, account AlBungstein only.
- Duration quality: 443 flows min 0s / max 31s / avg 0.905s -> 3,452s; 3333 -> 112s. No negatives.
- `sa=45.77.53.176` -> 0 events (no inbound pool traffic).

### What it means
FOUND: 192.168.70.186 is the endpoint that GENERATED Monero — it alone shows the stratum 3333 connection (5.78MB in, the actual mining data transfer), a second miner binary hash, WMI lateral-execution parent, and SYSTEM-account execution. 192.168.24.128 has no mining-specific indicator beyond generic 443 contact. The 3333 flow shares hash, user, destination, and time window with the 443 activity, so it is included: **3,452 + 112 = 3,564 seconds**.

## Assumptions
- Selection: 192.168.70.186 over 192.168.24.128 - VERIFIED by the five-indicator side-by-side above; 24.128 eliminated as generic-443-only.
- 3333 flow is part of the same Monero activity - VERIFIED: same hash ...6677, same user, same dest, window nested in 443 activity.
- Sum of per-flow durations is the correct "total seconds generating" measure - VERIFIED: fss/fes are per-flow epoch bounds; no negative durations.
- Port 3333 = Monero stratum - external knowledge, corroborated in-dataset by the 5.78MB inbound transfer unique to that flow.

## Ruled out
- 192.168.24.128 as the endpoint - single hash/parent/user, 443-only, generic byte profile.
- 192.168.105.214 - 2 benign Edge flows to the pool IP on 80.
- Inbound pool traffic as an indicator - zero events.

## Open questions for SH
- None; selection and inclusion are settled on flow evidence.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'app', 'bytes', 'packets', 'starttime', 'endtime', 'duration']
- Rounds worked: 2/8  (iterations: 17, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | top limit=50 dp
- index=botsv3 source=cisconvmflowdata | top limit=50 pn
- index=botsv3 sourcetype=stream:dns "45.77.53.176" | stats count values(query) as queries values(answer) as answers by src
- index=botsv3 sourcetype=stream:dns "45.77.53.176" | stats count values(query) as queries values(answer) as answers values(name) as names by src
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (da=45.77.53.176 OR sa=45.77.53.176) | stats count min(fss) as first_start max(fes) as last_end values(sa) as src values(sp) as sport values(dp) as dport values(pn) as proc values(liuid) as user by sa da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=9997 OR dp=58868 OR dp=50414 OR dp=8080 OR dp=4287 OR dp=22790 OR dp=3333) | stats count by pn sa da dp liuid | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.70.186 OR sa=192.168.24.128) da!=192.168.* da!=10.* da!=172.* | stats count sum(eval(fes-fss)) as sum_secs values(pn) as procs values(dp) as dports by sa da | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da!=192.168.* da!=10.* da!=172.* da!=127.0.0.1 | stats count dc(sa) as hosts values(pn) as procs by da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 dp=3333 | stats count values(sa) as src values(sp) as sport values(ph) as proc_hash values(ppn) as parent values(fss) as start values(fes) as end values(ibc) as bytes_in values(obc) as bytes_out values(liuid) as user values(pa) as proc_account
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | bin span=5m fss | stats count dc(sa) as hosts sum(eval(fes-fss)) as sum_secs by sa fss | sort fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats avg(ibc) as avg_in_bytes avg(obc) as avg_out_bytes avg(eval(fes-fss)) as avg_flow_secs by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count values(ph) as proc_hashes values(ppn) as parent_procs by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 sa=192.168.24.128 | stats count min(fss) as first_start max(fes) as last_end sum(eval(fes-fss)) as sum_flow_secs by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 sa=192.168.70.186 | stats count min(eval(fes-fss)) as min_dur max(eval(fes-fss)) as max_dur avg(eval(fes-fss)) as avg_dur sum(eval(fes-fss)) as total_dur by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 sa=192.168.70.186 | stats count min(fss) as first_start max(fes) as last_end sum(eval(fes-fss)) as sum_flow_secs by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count avg(ibc) as avg_in min(ibc) as min_in max(ibc) as max_in avg(obc) as avg_out avg(eval(fes-fss)) as avg_flow_secs sum(eval(fes-fss)) as sum_flow_secs by sa dp | sort sa dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count dc(dp) as distinct_dports values(dp) as dports min(fss) as first_flow_start max(fes) as last_flow_end sum(eval(fes-fss)) as total_flow_secs avg(ibc) as avg_in_bytes avg(obc) as avg_out_bytes by sa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(dp) as dports values(liuid) as users by sa pn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count values(dp) as dports values(ppn) as parents values(pa) as proc_accounts by sa ph
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count values(pn) as procs values(ph) as proc_hashes values(ppn) as parent_procs values(liuid) as users by sa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=hdoor.exe | stats count min(fss) as first_start max(fes) as last_end values(sa) as src_ips values(da) as dst_ips values(dp) as dst_ports values(liuid) as users values(ppn) as parent_procs
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler* | stats count min(fss) as first_start max(fes) as last_end values(sa) as src_ips values(da) as dst_ips values(dp) as dst_ports values(liuid) as users values(ppn) as parent_procs
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler.exe | stats count min(fss) as first_start max(fes) as last_end values(sa) as src_ips values(da) as dst_ips values(dp) as dst_ports values(sp) as src_ports values(liuid) as users values(ppn) as parent_procs
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe da!=192.168.* da!=10.* da!=172.* | stats count min(fss) as first_start max(fes) as last_end sum(eval(fes-fss)) as sum_secs by sa da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=45.77.53.176 | stats count values(da) as target_hosts values(dp) as target_ports values(pn) as procs values(liuid) as users
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=50 dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=50 pn
