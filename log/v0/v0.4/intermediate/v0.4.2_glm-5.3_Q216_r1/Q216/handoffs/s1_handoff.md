# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=5_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,sp,dp,pn,ppn,fss,fes,ibc,obc
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 90

## Prior rounds
- R1: Located feed (78,459 events), mapped fields, found the feed's only dp=3333 flow (192.168.70.186 -> 45.77.53.176, powershell.exe, fss=1534762025, fes=1534762137); flagged coverage gaps.
- R2: Closed all gaps — all 22 dp values read (3333 only pool port), sp=3333 zero, all 60 pn values read (no miner binary), 443 powershell flows shown as ~1s beacons (C2), full unusual-port sweep 27/27 rows; SPL-computed duration 112s.

## This round
### What I ran
- dp=3333 | eval duration_seconds=fes-fss | stats ... -> 1 event: 192.168.70.186:64104 -> 45.77.53.176:3333, powershell.exe (parent powershell.exe), user AzureAD\FyodorMalteskesko, fss=1534762025, fes=1534762137, duration_seconds=112, ibc=5,782,875, obc=177.
- dp IN (3333,4444,14444,45700,7777,14433,14477,14443,3355,5555) | stats by dp -> exactly 1 row: dp=3333, count=1, dc(sa)=1.
- da=45.77.53.176 | eval dur=fes-fss | stats by sa -> 3 endpoints: .70.186 (3,815 flows, ports 3333+443, longest 112s); .24.128 (1,015, 443 only, longest 12s); .105.214 (2, EdgeCP:80).
- da=45.77.53.176 dp=443 pn=powershell.exe | eval dur=fes-fss | stats by sa -> .70.186: 3,814 flows, 3,452s total, avg 0.905s, perc75 1s, max 31s; .24.128: 1,015 flows, 1,266s, avg 1.247s, max 12s.
- pn=powershell.exe | where dur>60 -> 5 flows: the 112s 3333 flow plus four ~100s one-off HTTP transfers (104.31.76.227:80, 67.199.248.10:80, 192.168.9.30:8080).

### What it means
FOUND. The Cisco NVM feed contains exactly one flow on any Monero Stratum port: 192.168.70.186 -> 45.77.53.176:3333 by powershell.exe (self-parented, FyodorMalteskesko). Its SPL-computed duration fes-fss = 112 seconds, already an integer. No competing candidate exists: no other pool port in the feed, no other endpoint on 3333, the 443 traffic to the same IP is sub-second C2 beaconing (avg ~1s, perc75 1s, max 31s, ibc=0/obc=95 per flow, parents svchost/WmiPrvSE), and the only other >60s powershell flows are one-off HTTP downloads. External corroboration of this flow as the Monero-generation act was established by SH; the NVM chain above is complete and closed.

## Assumptions
- Coverage: dp — all 22 values enumerated, 3333 the only pool port - VERIFIED; sp — sp=3333 zero events - VERIFIED; pn — all 60 values enumerated, no miner binary - VERIFIED; mhl/mnl — candidate flow's lists empty (read in raw event) - VERIFIED for that flow.
- Selection: 192.168.70.186 — only endpoint with pool-port contact; .24.128 and .105.214 ruled out by port set and flow profile - VERIFIED.
- Definition: duration = fes-fss of the Monero-generation flow, computed in SPL - VERIFIED (112).
- External premise (45.77.53.176:3333 = Monero pool) — established by SH outside this feed; not re-tested in NVM per instruction.

## Ruled out
- 443 powershell flows as the act (sub-second beacons, C2 profile); other pool ports (none in feed); miner binaries (none in 60 process names); other >60s powershell flows (HTTP downloads, not pool ports); 192.168.24.128 and 192.168.105.214 (no pool-port contact).

## Open questions for SH
- None. The NVM chain is answer-ready; value 112 seconds is submitted as-is.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'starttime', 'endtime', 'duration']
- Rounds worked: 3/8  (iterations: 28, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | rare pn limit=40
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 dp=443 pn=powershell.exe | eval dur=fes-fss | stats count sum(dur) as total_seconds avg(dur) as avg_seconds perc75(dur) as p75_seconds max(dur) as max_seconds by sa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 dp=443 pn=powershell.exe | eval dur=fes-fss | stats count sum(dur) avg(dur) max(dur) perc75(dur) sum(ibc) sum(obc) by sa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval dur=fes-fss | stats count sum(dur) as total_flow_seconds avg(dur) as avg_flow_seconds max(dur) as longest_flow_seconds sum(ibc) as bytes_in sum(obc) as bytes_out values(pn) values(dp) by sa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count dc(fss) min(fss) max(fes) sum(ibc) sum(obc) by sa pn dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count dc(fss) min(fss) max(fes) values(pn) values(sa) values(dp) sum(ibc) sum(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp IN (3333,4444,14444,45700,7777,14433,14477,14443,3355,5555) | stats count dc(sa) values(sa) values(da) values(pn) by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp!=443 dp!=53 dp!=80 dp!=5353 dp!=67 dp!=68 | eval dur=fes-fss | stats count sum(dur) as total_dur max(dur) as max_dur sum(ibc) sum(obc) values(sa) values(pn) by da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | eval duration_seconds=fes-fss | stats count values(sa) as src_ip values(sp) as src_port values(da) as dst_ip values(pn) as process values(ppn) as parent_process values(liuid) as user min(fss) as flow_start_epoch max(fes) as flow_end_epoch values(duration_seconds) as duration_seconds values(ibc) as bytes_in values(obc) as bytes_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(sa) values(da) values(pn) values(ppn) values(fss) values(fes) values(ibc) values(obc) values(sp) values(dh)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | eval dur=fes-fss | where dur>60 | stats count values(sa) values(da) values(dp) values(dur) values(ibc) values(obc) values(ppn)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count dc(fss) min(fss) max(fes) sum(ibc) sum(obc) by sa da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sp=3333 | stats count values(sa) values(da) values(pn) values(dp) values(fss) values(fes) values(ibc) values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | stats count dc(fss) sum(dur) max(dur) min(fss) max(fes) sum(ibc) sum(obc) by sa da dp pn | sort - max(dur) | head 15
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | rare dp limit=22
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | rare pn limit=40
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | search count>=60 count<=76 | sort count
