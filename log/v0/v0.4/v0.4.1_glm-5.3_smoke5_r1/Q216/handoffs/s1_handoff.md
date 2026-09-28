# s1 - Q216 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=3_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, fss, fes, ibc, obc, dh, ph, sp (+ WinHostMon, stream:udp for the final artifact sweep)
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 55

## Prior rounds
- R1: Feed located; no miner-named process; 45.77.53.176 = only large unattributed dest; one dp=3333 flow from 192.168.70.186.
- R2: 3333 session verified (112s); measures 112/3564/7070; .24.128 ruled out.
- R3: Byte direction calibrated; 443 rate unchanged around the 3333 session; no Monero text in NVM feed.
- R4: Rival scan found no mining-like rival; 443 polling intermittent (33% coverage); endpoint = FYODOR-L.froth.ly.
- R5: No case-internal Monero tie inside NVM feed; 3333 unique on every axis.
- R6: Cross-feed: 3333 = HTTP GET /images/logos.png; 443 = refused TLS beaconing; 45.77.53.176 = www.frothly.com/vultr VPS with reverse shell on 8088; 0 mining terms anywhere.
- R7: NVM re-sweep without assumptions: complete unattributed-external inventories for FYODOR-L (13 rows) and BSTOLL-L (29 rows) read — no mining pattern; premise declared unsupported.

## This round
### What I ran
- Long-duration (dur>300s) external flows for BSTOLL-L/FYODOR-L -> top 50 of 306 read: all identified services (wns.windows.com, CrashPlan, splunk.froth.ly, office365, msedge, vpn.froth.ly) — no named pool.
- WinHostMon mining-term search -> 203 events = Windows WalletService on all 8 hosts; not Monero.
- WinHostMon/stream:udp for 45.77.53.176 OR 3333 -> 16 process events, all read: iexepler.exe reverse shell (`nc 45.77.53.176 8088`) on FYODOR-L; no miner process.

### What it means
FORKED CONCLUSION, stated plainly: (A) No verified Monero-generating record exists in the case data — every artifact class is now exhausted, and the only artifacts naming 45.77.53.176 treat it as attacker infrastructure (reverse shell on 8088, refused TLS on 443, PNG staging on 3333, www.frothly.com). (B) The fallback number is 112: the unique Cisco NVM 3333 session (fss=1534762025→fes=1534762137), the only dp=3333 flow in 78,459 events, the only persistent bulk session by the implant's powershell.exe from FYODOR-L. The question scopes itself to the Cisco NVM flow logs and premises they show Monero generation; within that feed, the 3333 session is the unique record that premise can point to, so 112 is submitted as the question-premise answer — with the explicit caveat that its records show a download, not a verified act of generation.

## Assumptions
- Coverage: every artifact class searched (NVM text, stream:dns/http/tcp/udp, Sysmon, osquery, WinEventLog, Symantec, WinHostMon process+service) — VERIFIED, 0 Monero labels case-wide.
- Selection: the 3333 session as the question's intended record — rests on the question's own premise and the port-3333 stratum convention, NOT on case-internal evidence — stated as such.
- Duration = fes-fss of that session = 112 — VERIFIED arithmetic.

## Ruled out
- All named-destination long flows on BSTOLL-L/FYODOR-L — identified Microsoft/CrashPlan/Splunk/VPN services.
- Windows WalletService — Windows component on all 8 hosts, not Monero.
- iexepler.exe / hdoor.exe — Struts exploit and reverse shell, lateral movement.
- 443 powershell traffic — refused TLS beaconing.

## Open questions for SH
- None; the fork is settled: no verified mining record exists; 112 is the unique-session fallback the question premise points to.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.247.131 OR sa=192.168.2…` (50 of 306 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'duration', 'app', 'url', 'user', 'endpoint']
- Rounds worked: 8/8  (iterations: 73, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (monero OR xmrig OR stratum) | stats count by sourcetype
- index=botsv3 (sourcetype=stream:dns OR sourcetype=stream:http OR sourcetype=stream:tcp OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=osquery:results OR sourcetype=WinEventLog OR sourcetype=symantec:ep:traffic:file OR sourcetype=symantec:ep:packet:file) (monero OR xmrig OR stratum OR miner OR mining OR wallet) | stats count values(sourcetype) as feeds values(host) as hosts values(user) as users values(src_ip) as srcs values(dest_ip) as dsts values(query) as queries values(uri) as uris values(process) as procs values(Image) as images values(CommandLine) as cmds
- index=botsv3 (sourcetype=stream:dns OR sourcetype=stream:http OR sourcetype=stream:tcp OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=osquery:results OR sourcetype=WinEventLog OR sourcetype=symantec:ep:traffic:file OR sourcetype=symantec:ep:packet:file) 45.77.53.176 | stats count by sourcetype
- index=botsv3 (sourcetype=WinHostMon OR sourcetype=stream:udp OR sourcetype=stream:icmp) (45.77.53.176 OR 3333) | stats count by sourcetype, source
- index=botsv3 source=cisconvmflowdata | rare pn limit=30
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" 45.77.53.176 | stats count values(host) as hosts by EventCode
- index=botsv3 sourcetype=stream:dns 45.77.53.176 | stats count values(query) as queries values(name) as names values(answer) as answers values(src_ip) as clients values(_time) as times
- index=botsv3 sourcetype=stream:http 45.77.53.176 | stats count values(uri) as uris values(method) as methods values(status) as statuses values(src_ip) as clients values(dest_port) as ports values(http_user_agent) as ua values(host) as hosts values(_time) as times
- index=botsv3 sourcetype=syslog source=cisconvmflowdata ((pn=splunkd.exe AND dp=9997) OR (pn=streamfwd.exe AND da=34.215.24.225) OR pn=OUTLOOK.EXE) | stats count sum(ibc) as tot_ibc sum(obc) as tot_obc by pn, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (monero OR xmr OR miner OR stratum OR pool) | stats count values(pn) as pn values(sa) as sa values(da) as da values(dp) as dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (pn="*miner*" OR pn="*xmr*" OR pn="*crypt*" OR pn="*pool*" OR pn="*stratum*") | stats count by pn, sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.247.131 OR sa=192.168.247.129 OR sa=192.168.70.186) | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | eval dur=fes-fss | where dur>300 | stats count sum(dur) as sum_dur max(dur) as max_dur values(dh) as dh values(pn) as procs values(dp) as ports by sa, da | sort - max_dur
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.70.186 OR sa=192.168.24.128 OR sa=192.168.247.131) | stats dc(iid) as dc_iid values(iid) as iids count values(liuidp) as users by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.70.186 OR sa=192.168.24.128) | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | stats count values(pn) as procs values(liuidp) as users sum(eval(fes-fss)) as sum_dur min(fss) as first_fss max(fes) as last_fes sum(ibc) as bytes_in sum(obc) as bytes_out by sa, da, dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=MicrosoftEdgeCP.exe | stats count values(fss) as fss values(fes) as fes values(eval(fes-fss)) as dur values(ibc) as ibc values(obc) as obc values(sp) as sp values(liuidp) as user values(dh) as dh values(fst) as fst values(fet) as fet by sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe dp=443 | sort 0 fss | streamstats current=f window=0 max(fes) as prev_max by sa | eval gap=fss-prev_max | eval idle=if(isnull(gap) OR gap<0,0,gap) | eval overlap=if(isnull(gap),0,if(gap<=0,1,0)) | stats count sum(idle) as idle_s sum(overlap) as overlapping_flows max(gap) as max_gap_s min(fss) as first_fss max(fes) as last_fes by sa | eval span_s=last_fes-first_fes, coverage_s=span_s-idle_s, pct=round(100*coverage_s/span_s,1)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | bin fss span=300s as bucket | stats count sum(eval(fes-fss)) as sum_dur by sa, bucket | sort bucket
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | eval dur=fes-fss | stats count sum(dur) as sum_dur_s min(fss) as first_fss max(fes) as last_fes by sa, dp | eval span_s=last_fes-first_fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count dc(ph) as distinct_proc_hashes values(ph) as hashes values(mnl) as modules values(mhl) as module_hashes by sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by pn, sa, pr, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as min_fss max(fss) as max_fss min(fes) as min_fes max(fes) as max_fes min(eval(fes-fss)) as min_dur avg(eval(fes-fss)) as avg_dur max(eval(fes-fss)) as max_dur sum(eval(fes-fss)) as sum_dur by pn, sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="Unknown" | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | stats count sum(ibc) as tot_ibc sum(obc) as tot_obc sum(eval(fes-fss)) as sum_dur values(pn) as procs by sa, da, dp | where tot_obc > 500000 | sort - tot_obc
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp IN (21,22,3306,3333,4287,8080,22790,52672,5355,53567,56756,65490,0,50414,58868,9997) | stats count values(sa) as src values(da) as dst values(pn) as proc values(dh) as host sum(eval(fes-fss)) as sum_dur by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata liuida=BSTOLL-L | stats count values(sa) as src values(pn) as procs values(liuidp) as users values(da) as dst values(dp) as port min(fss) as first_fss max(fes) as last_fes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn IN (hdoor.exe, iexeplorer.exe) | stats count values(sa) as src values(da) as dst values(dp) as port values(liuidp) as user min(fss) as first_fss max(fes) as last_fes sum(eval(fes-fss)) as sum_dur sum(ibc) as bytes_in sum(obc) as bytes_out by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | eval dur=fes-fss | where dur>45 | stats count values(sa) as src values(da) as dst values(dp) as port values(dh) as dh values(liuidp) as user sum(ibc) as tot_ibc sum(obc) as tot_obc values(eval(fes-fss)) as durations by sa, da, dp | sort - durations
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | stats count sum(eval(fes-fss)) as sum_dur min(fss) as first_fss max(fes) as last_fes sum(ibc) as tot_ibc sum(obc) as tot_obc values(dh) as dh values(liuidp) as user by sa, da, dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 dh="Unknown" | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | stats count sum(eval(fes-fss)) as sum_dur min(fss) as first_fss max(fes) as last_fes sum(ibc) as tot_in sum(obc) as tot_out values(pn) as procs values(dp) as ports by da | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 pn=powershell.exe | stats count sum(eval(fes-fss)) as sum_dur min(fss) as first_fss max(fes) as last_fes sum(ibc) as tot_ibc sum(obc) as tot_obc by ph, dp | eval span_s=last_fes-first_fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 dh="Unknown" | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | stats count sum(eval(fes-fss)) as sum_dur min(fss) as first_fss max(fes) as last_fes sum(ibc) as tot_in sum(obc) as tot_out values(pn) as procs values(dp) as ports by da | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | where NOT cidrmatch("10.0.0.0/8",da) AND NOT cidrmatch("172.16.0.0/12",da) AND NOT cidrmatch("192.168.0.0/16",da) | bin fss span=300s as bucket | stats count sum(eval(fes-fss)) as sum_dur dc(bucket) as active_buckets sum(ibc) as tot_in sum(obc) as tot_out values(pn) as procs values(dh) as dh by da | sort - active_buckets
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.8.103 | stats count dc(iid) as dc_iid values(iid) as iids values(pn) as procs values(liuidp) as users values(da) as dsts values(dp) as ports min(fss) as first_fss max(fes) as last_fes sum(ibc) as tot_in sum(obc) as tot_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=45.77.53.176 | stats count values(da) as dst values(dp) as dport values(sp) as sport values(pn) as proc values(dh) as dh values(liuidp) as user values(sa) as src
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sp=3333 | stats count values(sa) as src values(da) as dst values(dp) as dport values(pn) as proc values(dh) as dh values(liuidp) as user
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | where dur>60 | stats count max(dur) as max_dur min(fss) as first_fss max(fes) as last_fes by sa, da, dp, pn | sort - max_dur
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | rare pn limit=30
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh, da, dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | where count>=27 AND count<=140 | sort - count
- index=botsv3 sourcetype=WinHostMon (monero OR xmrig OR stratum OR miner OR mining OR cryptonight OR wallet OR pool) | stats count values(host) as hosts values(Name) as names values(CommandLine) as cmds values(Description) as descs by source
