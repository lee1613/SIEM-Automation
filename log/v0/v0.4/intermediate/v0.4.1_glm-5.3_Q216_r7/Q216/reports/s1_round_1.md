# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=17_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=fss, fes, sa, da, dh, dp, pn, ppn, pa, ph, liuid
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 58

## Prior rounds
- None — first round.

## This round
### What I ran
- get_sources/get_sourcetype_fields → feed confirmed: 78,459 events, all 2018-08-20; fss/fes = flow start/end epochs.
- `| stats count by pn | sort pn` + tail query → all 60 process names; no miner-named binary; powershell.exe (4,835) the anomaly.
- `| stats count by da | sort -count` → 45.77.53.176 (4,832 events) standout non-internal public IP.
- `da=45.77.53.176 | stats count by pn,sa,dh,sp,dp,pr` → powershell.exe→45.77.53.176:443 dh=Unknown from 192.168.24.128 and 192.168.70.186; 2 benign Edge flows to www.frothly.com:80 prove 45.77.53.176 = frothly.com web server.
- `pn=powershell.exe | stats count by sa,da,dh,dp,pr` → complete destination set (7 rows): 192.168.24.128 (1,015 to pool + bit.ly + leeholmes.com download chain); 192.168.70.186 (3,814 to :443 + 1 to :3333 Stratum).
- `da=45.77.53.176 | stats count by sa,pn,ppn,pa,liuid` → 192.168.70.186 = FyodorMalteskesko, parents WmiPrvSE/svchost/powershell, SYSTEM; 192.168.24.128 = AlBungstein, parent powershell.
- `da=45.77.53.176 | stats min(fss),max(fes),count by sa` → 192.168.70.186: 1534759304→1534766374 (3,815 flows); 192.168.24.128: 1534759261→1534766363 (1,015).
- `dp IN (3333,4444,5555,7777,8888,9999,14444,45700)` → exactly one Stratum flow: 192.168.70.186→45.77.53.176:3333.

### What it means
FOUND: 45.77.53.176 is the Monero pool (compromised frothly.com server; only Stratum-3333 flow in the dataset; thousands of dh=Unknown direct-IP powershell.exe connections). Implicated endpoint = 192.168.70.186 (FyodorMalteskesko): dominant volume, WMI-deployed, SYSTEM, sole Stratum flow. Duration = max(fes)−min(fss) = 1534766374−1534759304 = **7070** seconds.

## Assumptions
- Coverage: pn/ppn — all 60 values enumerated, no miner name, powershell.exe anomalous; da — ranked, 45.77.53.176 standout; dp — Stratum ports searched, one 3333 hit; ph — compared across endpoints (same hash both); mnl/mhl module lists — UNVERIFIED (never searched).
- Selection: 192.168.70.186 over 192.168.24.128 on volume (3,815 vs 1,015), sole 3333 flow, WMI/SYSTEM deployment — VERIFIED as data; which endpoint the question means — UNVERIFIED (tools exhausted).
- Definition: "generates Monero for N seconds" = elapsed span of the miner's pool flows, max(fes)−min(fss) — values VERIFIED via SPL; the definition itself is interpretation.
- 45.77.53.176 = pool — VERIFIED (Stratum 3333 + dh=Unknown + powershell-only clients + frothly.com identity).

## Ruled out
- Any other process as the miner (all 60 names enumerated).
- Other pool IPs (powershell.exe full destination set retrieved: 7 rows, complete).
- 192.168.105.214 (BruceGist): 2 benign Edge flows to www.frothly.com:80 only.

## Open questions for SH
- Two endpoints ran the same miner

_[truncated at 400 words]_

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Coverage check (runner): 28 field(s) of syslog are never named in your Coverage line: dest, dh, ds, dvc, fes, fet, fss, fst, fv, ibc, iid, liuat, liuid, obc, pa, ppa, pph, ppuat, pr, puat, sa, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
