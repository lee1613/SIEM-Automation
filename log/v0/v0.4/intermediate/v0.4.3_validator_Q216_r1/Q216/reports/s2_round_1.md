# s2 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,sp,pn,ppn,pa,fss,fes,ibc,obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 82

## Prior rounds
- R1-R2 (s1, path retired): established the 192.168.70.186 -> 45.77.53.176 dp=3333 powershell.exe flow (112s) via a CoinHive/domain-keyword route, then pivoted to a different mining hypothesis without resolving the candidate; SH retired that path and filed p1-p3.

## This round
### What I ran
- get_sourcetype_fields (cisconvmflowdata) -> 78,459 events; flow fields sa/da/dp/sp/pn, epoch flow start fss / end fes, byte counts ibc/obc.
- `| stats count by dp` -> 22 distinct ports, all rows returned; dp=3333 appears exactly once; no other stratum port (e.g. 45700) exists in the feed.
- `dp=3333 | stats values(...) by dp` -> 1 event: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe (user AzureAD\FyodorMalteskesko), fss=1534762025 (10:47:05), fes=1534762137 (10:48:57), ibc=5,782,875, obc=177.
- `da=45.77.53.176 | stats count, min(fss), max(fes), sum(ibc), sum(obc) by sa, pn, dp` -> 4 competing patterns (see Ruled out).
- get_raw_events keyword=45.77.53.176 (5 events) -> dp=443 flows are 1-2s beacons, ibc=0, obc=95, powershell.exe under WmiPrvSE.exe/svchost.exe parents.
- get_raw_events keyword=dp="3333" / sp="64104" -> 0 results (keyword-match limitation; values already captured via stats).

### What it means
The feed's only stratum-port flow is a single 112-second connection from compromised endpoint 192.168.70.186 running powershell.exe to 45.77.53.176, pulling 5,782,875 bytes in with 177 out — the Monero-generation act. Every competing pattern to the same IP is a C2-style beacon train (dp=443, ibc=0/obc=95, ~1s flows) or browser traffic (Edge, dp=80); neither shows mining. Duration = fes − fss = 1534762137 − 1534762025 = 112 seconds, already integral (human timestamps 10:47:05 → 10:48:57 = 1m52s confirm). Caveat: the subtraction was not executed inside SPL — tools were withdrawn at the iteration cap; both operands come from the same single-row stats output.

## Ruled out
- dp=443 powershell.exe flows to 45.77.53.176 from 192.168.70.186 (3,814) and 192.168.24.128 (1,015) - beacon pattern (raw samples ibc=0, obc=95, 1-2s), C2 check-ins not mining; overlapping short flows, not a generation duration.
- 192.168.105.214 MicrosoftEdgeCP.exe dp=80 to 45.77.53.176 (2 flows, 21KB) - browser fetch of the pool web page.
- All other 21 dp values in the feed - no mining/stratum ports (443, 53, 80, 5353, 67/68, 8080, 22, 21, 3306, 9997, ephemerals).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
