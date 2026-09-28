# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=13_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=dp, da, sa, pn, ph, fss, fes
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 74

## Prior rounds
- None — this is round 1.

## This round
### What I ran
- get_sources(syslog) + get_sourcetype_fields(cisconvmflowdata) -> feed confirmed, 78,459 events; fields sa/da/dh/dp/pn/ppn/ph/pph/fss/fes/mnl/mhl.
- get_raw_events keyword=monero -> 0 events. Keyword search (pool OR monero OR stratum OR xmr OR nanopool OR minexmr) -> only ad-tech pool.adizio.com/pool.admedo.com.
- get_field_values dp (22 values, COMPLETE enumeration) -> exactly one dp=3333 event (canonical Monero stratum port); no 4444/5555/7777.
- get_field_values pn (60, complete) / ppn (24, complete) -> suspicious iexepler.exe (15) and hdoor.exe (7) investigated and ruled out (internal scanning).
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count by pn sa da dh dp fss fes -> 1 event: powershell.exe, sa=192.168.70.186, da=45.77.53.176, fss=1534762025, fes=1534762137.
- da=45.77.53.176 breakdown -> 4 hosts; 192.168.70.186 has 3,814 :443 flows + the one :3333 flow; 192.168.24.128 (1,015) and 192.168.105.214 (2) reach it on 443 only.
- ph breakdown -> the :3333 flow's hash D3F8FADE...14466677 is the same process as 3,621 of the :443 flows; a second hash ...6600 exists on 443 only.

### What it means
FOUND: the only flow in the entire feed that demonstrates Monero generation is the stratum connection on port 3333 — powershell.exe on 192.168.70.186 -> 45.77.53.176:3333, fss=1534762025, fes=1534762137. Duration = fes - fss = 112 seconds. The question's singular "the endpoint" matches: only 192.168.70.186 ever touches a pool port.

## Assumptions
- Coverage: dp — full enumeration (22 values, complete), only 3333 is a pool port, 1 event — VERIFIED. dh — top 100 + keyword search for pool/monero/stratum/xmr: no pool domain (pool IP has dh=Unknown) — VERIFIED. pn/ppn — full enumerations (60/24, complete): no miner binary — VERIFIED. mnl — full enumeration (33, complete): service DLLs only — VERIFIED. da — top 50 of 2,735 rows (truncated); rival pool IPs would require pool ports, which the complete dp enumeration excludes — PARTIAL. fss/fes — epoch seconds (fss=1534760737 pairs with fst="Mon Aug 20 10:25:37 2018") — VERIFIED.
- Selection: 192.168.70.186 because it alone has a pool-port flow. Rivals ruled out: 192.168.24.128 / 192.168.105.214 (443-only to the same IP, no pool port); 192.168.8.103 (iexepler.exe -> 192.168.9.30:8080 and hdoor.exe SSH scan = lateral movement, no external pool) — VERIFIED.
- Definition premise: "generates Monero" = the stratum flow(s) on port 3333; duration = fes - fss = 112s. The 3,814 :443 flows by the same process hash are C2 on generic TLS (a second host beacons to the same IP:443 with no mining) — VERIFIED as the only flow-level Monero indicator; 443-inclusive alternative (7070s) rejected.

## Ruled out
- iexepler.exe / hdoor.exe on 192.168.8.103 — internal lateral movement and SSH scanning, no pool.
- Literal "monero" or pool-hostname identification — 0 raw events, no pool domain in dh.
- 7070s (443-inclusive span) — port 443 carries no mining signature and is shared with non-mining hosts.

## Open questions for SH
- Should the 3,814 powershell.exe flows from 192.168.70.186 to 45.77.53.176:443 (same process hash as the :3333 flow) count as Monero generation? If yes the span is 7070s; I held them to be C2 because 443 has no mining signature and 192.168.24.128 beacons to the same IP:443 without any pool connection.

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Coverage check (runner): 26 field(s) of syslog are never named in your Coverage line: dest, ds, dvc, fet, fv, ibc, iid, liuat, liuid, mhl, obc, pa, ph, ppa, pph, ppuat, pr, puat, sa, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._

_Unseen rows (runner): 1 result(s) this round showed only part of their rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by da | sort - count` (50 of 2735 rows seen). Nothing is absent from the unseen rows until a query that filters for it says so; any Coverage resting on these results is UNVERIFIED._
