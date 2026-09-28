# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,sp,dp,pn,ppn,fss,fes,ibc,obc
**Insight:** partial   **Candidate:** 112   **Confidence:** 70

## Prior rounds
- R1: Located the feed (78,459 events); mapped fields (sa/da, sp/dp, pn/ppn, fss/fes, ibc/obc); found the feed's only dp=3333 flow (192.168.70.186 -> 45.77.53.176, powershell.exe, fss=1534762025, fes=1534762137); flagged unverified: 2 unread dp values, sp=3333, pn coverage, 443-vs-3333 mining definition.

## This round
### What I ran
- | rare dp limit=22 -> all 22 dp values read; 3333 is the ONLY Monero pool port; no 4444/14444/45700/7777.
- sp=3333 -> 0 events.
- | eval dur=fes-fss | stats by sa,da,dp,pn | sort - max(dur) | head 15 -> longest flows are idle keepalives/backups (Edge 154,416s; CrashPlan 29,111s; OneDrive; WinStore; streamfwd) — none mining-shaped.
- get_raw_events "45.77.53.176" -> 443 powershell flows are ibc=0/obc=95 beacons, parents svchost.exe/WmiPrvSE.exe, user FyodorMalteskesko.
- get_raw_events "3333" -> candidate raw event: sa=192.168.70.186, sp=64104, da=45.77.53.176, dp=3333, fss=1534762025, fes=1534762137, pn=ppn=powershell.exe (self-parented), liuid=FyodorMalteskesko, ibc=5,782,875, obc=177, dh=Unknown, mnl/mhl empty.
- | stats count by pn | search count>=60 count<=76 -> Dropbox 67, WinStore 67, splunkd 76 — pn coverage complete (60/60 names), no miner binary.
- 443 powershell | eval dur=fes-fss | stats by sa -> .70.186: 3,814 flows, sum 3,452s, avg 0.91s, perc75 1s, max 31s; .24.128: 1,015 flows, sum 1,266s, avg 1.25s, max 12s.
- Full unusual-port sweep (dp not in 443/53/80/5353/67/68), 27/27 rows read -> only the 3333 row touches a pool port; rest is splunkd:9997 (2.05GB out, Splunk forwarding), CrashPlan:4287 backups, internal 192.168.8.x hdoor/putty/ssh, svchost ephemeral.

### What it means
The feed's only Monero-pool-port record is the single 3333 flow; its SPL-computed duration fes-fss = 112 seconds (sum(dur)=112, max(dur)=112), already an integer. The 443 flows to the same IP fail every mining test SH set: ~1s beacons (not sustained sessions), ibc=0/obc=95 per flow, two endpoints, service/WMI parents — C2 check-ins. No other endpoint, port, or process in the feed can carry the act.

## Assumptions
- Coverage: dp — all 22 values read, only 3333 is a pool port - VERIFIED; sp — sp=3333 zero events - VERIFIED; pn — all 60 names seen, no miner binary - VERIFIED; mhl/mnl — candidate flow's own lists are empty (read in raw event); not exhaustively searched feed-wide - UNVERIFIED.
- Selection: 3333 flow is the only pool-port record; 443 set ruled out by beacon profile; 192.168.24.128 ruled out (no 3333, only beacons + two one-off HTTP downloads) - VERIFIED.
- Definition: duration = fes-fss of the Monero-generation flow, computed in SPL - VERIFIED (112).
- Port 3333 = Monero Stratum is external knowledge; the flow's byte profile (5.78MB in/177B out) is transfer-like, so the feed alone does not positively show share submission - UNVERIFIED, flagged.

## Ruled out
- 443 powershell flows as mining (beacon duration/volume/parents); other pool ports (full dp list); miner binaries (full pn list); long-duration flows as mining (top-15 all benign keepalive/backup); splunkd:9997 (Splunk forwarding infrastructure); 192.168.24.128 (staging/download only).

## Open questions for SH
- Does the case file elsewhere establish 45.77.53.176:3333 as the Monero pool (e.g. proxy/pcap evidence)? That would convert this partial to FOUND at 112.
- If SH intends the 443 beacon set as the act, candidates would be 3,452s (.70.186) or 1,266s (.24.128) — but both fail the behavior test.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
