# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=19_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=fss,fes,sa,da,sp,dp,pn,ppn,ph,liuid,ibc,obc
**Insight:** FOUND
**Candidate:** 3564   **Confidence:** 85

## Prior rounds
- Round 1 (this round): confirmed feed (78,459 events, Aug 20 2018); identified Monero pattern and endpoint; computed duration.

## This round
### What I ran
- get_sources/get_sourcetype_fields -> feed confirmed; fss/fes = flow start/end epoch seconds.
- `| top pn` / `| top dp` -> no miner-named process; anomalies: powershell.exe (4,835), iexepler.exe, hdoor.exe; ports 3333, 8080, 9997, 58868, 50414.
- hdoor.exe -> internal scan 192.168.8.103→192.168.9.x:21/22/3306 (lateral recon, not Monero). iexepler.exe→192.168.9.30:8080 -> internal C2, not Monero.
- External-dest survey -> 45.77.53.176:443 powershell.exe, 4,829 flows, 2 hosts; all other externals are vendor/CDN (Microsoft, Google, Dropbox, CrashPlan).
- `da=45.77.53.176 | stats by sa pn` -> 192.168.70.186: 3,815 flows, ports 443+3333, FyodorMalteskesko; 192.168.24.128: 1,015 flows, 443 only, AlBungstein.
- `da=45.77.53.176 sa=192.168.70.186 | stats sum(eval(fes-fss)) by dp` -> 443: 3,452s; 3333: 112s. Total 3,564s. Avg cross-check: 0.934s x 3,815 = 3,564.

### What it means
FOUND: Monero pattern = powershell.exe making thousands of short TLS flows (~0.9s, ~600B out/~3.9KB in) to pool 45.77.53.176. Endpoint = 192.168.70.186 — only host with a stratum port-3333 connection and the dominant flow share. Sum of per-flow durations (fes−fss) = 3,452 + 112 = **3,564 seconds**.

## Assumptions
- Selection: 192.168.70.186 over 192.168.24.128 (same binary hash, same pool) — decided by the port-3333 stratum flow and WmiPrvSE/svchost parents, present only on 192.168.70.186 - VERIFIED.
- "Total seconds generating Monero" = sum of per-flow durations, not wall-clock span (7,070s) - the flow records carry explicit per-flow start/end; question says "actually generate" - VERIFIED as computable.
- Port 3333 = Monero stratum - external knowledge; corroborated as the only non-443 port to the pool - UNVERIFIED in-dataset (NVM records carry no L7 payload).
- Binned 5m query discarded: `bin span=5m fss` overwrites fss with bucket start, inflating fes−fss - VERIFIED by contradiction with unbinned sums.

## Ruled out
- hdoor.exe, iexepler.exe - internal recon/C2, not Monero.
- svchost.exe→192.168.247.129:58868/50414 - internal, not Monero.
- splunkd.exe→34.215.24.225:9997 - Splunk infra; CrashPlan:4287, vpnagent - legitimate.
- 192.168.105.214→45.77.53.176:80 - 2 benign Edge flows.

## Open questions for SH
- Confirm the case treats 192.168.70.186 (not 192.168.24.128, which yields 1,266s) as "the" Monero endpoint.
- Should the 112s port-3333 flow be included? I included it (3,564); excluding it gives 3,452.

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
