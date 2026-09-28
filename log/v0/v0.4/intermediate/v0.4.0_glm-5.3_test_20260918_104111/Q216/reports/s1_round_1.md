# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=13_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, da, dp, sa, fss, fes
**Insight:** FOUND
**Candidate:** 7113   **Confidence:** 70

## Prior rounds
- None — this is round 1; the full chain was established this round.

## This round
### What I ran
- get_sources(syslog) + get_sourcetype_fields(cisconvmflowdata) -> feed confirmed, 78,459 events; key fields fss/fes (flow start/end epochs), sa/da, sp/dp, pn (process).
- `| top pn` -> powershell.exe 4,835 events, the only anomalous process.
- `| top da` -> 45.77.53.176 4,832 events, top external destination.
- `da=45.77.53.176 | top pn / top dp` -> 4,830 powershell.exe; ports 443 (4,829) and one 3333 (Monero Stratum default).
- `pn=powershell.exe | top da` -> 99.9% of powershell traffic goes to 45.77.53.176.
- `da=45.77.53.176 pn=powershell.exe | stats min(fss), max(fes)` -> 1534759261 / 1534766374, 4,830 flows.
- Per-sa breakdown -> 192.168.70.186 (3,815 flows) and 192.168.24.128 (1,015 flows); 2 MicrosoftEdgeCP.exe flows from 192.168.105.214 are to www.frothly.com (browsing).
- web_lookup -> no external corroboration available.

### What it means
FOUND: powershell.exe is the miner process; its near-exclusive peer 45.77.53.176 is the pool (443 for stealth, one Stratum 3333 flow). Mining ran from fss=1534759261 (Aug 20 2018 10:01:01 UTC) to fes=1534766374 (11:59:34 UTC) on two hosts -> 1534766374 − 1534759261 = **7113 seconds**.

## Ruled out
- MicrosoftEdgeCP.exe flows to 45.77.53.176 (dh=www.frothly.com) — normal web browsing to the company site; including them would give 7841s.
- Other external IPs (34.215.24.225=splunk.froth.ly, 204.79.197.200, 13.107.x.x, 216.58.195.67) — no powershell association, no Stratum ports.

## Open questions for SH
- Should the window include the 2 non-mining Edge flows to the same IP (would yield 7841s instead of 7113s)?
- Is a feed-wide dp=3333 scan wanted to prove Stratum traffic is unique to this pool?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
