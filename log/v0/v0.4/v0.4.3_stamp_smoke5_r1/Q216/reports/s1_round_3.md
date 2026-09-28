# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=4_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata | fields sa, da, dp, pn, ph, ppn, liuid, fss, fst, fes, fet, ibc, obc, dh
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 80

## Prior rounds
- R1: Feed confirmed (78,459 events). dp distribution: 3333 appears exactly once, no other pool ports. That flow: 192.168.70.186 → 45.77.53.176:3333, powershell.exe, FyodorMalteskesko, 112s, 5.78MB in. Filed 112 @ conf 60.
- R2: Rival flows to 45.77.53.176 fully enumerated (4 rows); 45.77.53.176 = www.frothly.com (compromised web server); mining-token dh search found only coinhive from a different endpoint. Filed 112 @ conf 70.

## This round
### What I ran
- `sa=192.168.70.186 pn=powershell.exe | stats ... by da dp` -> **2 of 2 rows, untruncated**: 45.77.53.176:443 (3,814 flows, 3,452s, 9.03MB in/2.39MB out) and 45.77.53.176:3333 (1 flow, 112s, 5.78MB in/177B out). These are the endpoint's ONLY powershell destinations.
- get_raw_events keyword=1534762025 -> full 3333 event: self-spawned powershell (ph=pph=D3F8FADE...6677), 10:47:05→10:48:57, ibc=5,782,875, obc=177.
- get_raw_events keyword=45.77.53.176 -> 443-flow samples are ibc=0/obc=95-255B beacons.
- `dp=443 ... | stats avg/perc50/max(fes-fss), avg/max(ibc), avg(obc), zero-byte count` -> 3,814 flows: avg dur 0.905s, median 1s, max 31s, avg in 2,367B, max in 54,545B, 9 zero-byte check-ins.
- `dp=8080 | stats ... by sa pn da` -> 4 rows: all from 192.168.8.103/.111 to internal 192.168.9.30 — different endpoints, internal destination. Last round-1 gap closed.
- `sa=192.168.70.186 pn=powershell.exe dp=3333 | stats sum(eval(fes-fss))` -> **112** (fst 10:47:05, fet 10:48:57 confirms).

### What it means
Complete, untruncated coverage: powershell.exe on 192.168.70.186 touches exactly two destination/port pairs, both on 45.77.53.176. The 3333 record is the only one in the entire feed that shows Monero pool communication (canonical stratum port, sole occurrence in 78,459 events; 5.78MB sustained download over 112s). The 3,814 443 flows are C2 beacons — sub-second (avg 0.9s, max 31s), tiny (avg 2.4KB in), periodic, 9 zero-byte check-ins — to www.frothly.com, Frothly's own compromised web server: malware staging/C2, not mining. No other destination, port, or mining-token host involves this endpoint. Total countable Monero-generation seconds = **112**.

## Ruled out
- 45.77.53.176:443 powershell flows (3,452s) - C2 beacons to Frothly's own compromised web server; sub-second, tiny, periodic; no Monero evidence. (Summing them would give 3,564s — the only alternative reading, rejected.)
- 192.168.24.128 (1,015 flows, 1,266s) and 192.168.105.214 (2 flows, 219s) - different endpoints, same www.frothly.com staging/browsing pattern.
- coinhive.com flows (192.168.247.131, chrome.exe) - Monero mining but a different endpoint.
- dp=8080 flows - different endpoints (192.168.8.103/.111), internal destination 192.168.9.30.
- Other pool ports (4444/5555/7777/14444/14433) - zero events feed-wide.