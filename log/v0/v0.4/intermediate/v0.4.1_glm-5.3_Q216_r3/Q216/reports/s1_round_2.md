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