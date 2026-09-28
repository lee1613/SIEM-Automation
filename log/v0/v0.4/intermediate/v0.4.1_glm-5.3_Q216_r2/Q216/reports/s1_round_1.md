# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=18_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,pn,liuid,fss,fes,ibc,obc,dh
**Insight:** FOUND   **Candidate:** 3564   **Confidence:** 38

## Prior rounds
- Round 1 (this round): first round — no prior rounds.

## This round
### What I ran
- get_sources(sourcetype=syslog) → cisconvmflowdata confirmed, 78,459 events
- get_sourcetype_fields + sample_events → fss/fes = flow start/end epoch secs; sa/da/sp/dp; pn; liuid; ibc/obc; dh
- get_raw_events(keyword="monero") → 0 events (no literal string in feed)
- da=45.77.53.176 | top pn → powershell.exe 4,830/4,832 (99.96%)
- da=45.77.53.176 | top sa → 192.168.70.186 (3,815), 192.168.24.128 (1,015), 192.168.105.214 (2, Edge→www.frothly.com)
- dp IN (3333,4444,5555,5556,7777,9999,14444,45700) → exactly 1 flow: 192.168.70.186→45.77.53.176:3333, powershell.exe, FyodorMalteskesko, fss=1534762025, fes=1534762137
- da=45.77.53.176 | stats sum(fes-fss) by sa → 3,564 / 1,266 / 219 (all=5,049)
- per-dp stats for .70.186 → 443: 3,814 flows, 3,452s (avg 0.9s, max 31s); 3333: 1 flow, 112s

### What it means
FOUND: Monero mining traffic in the NVM feed = powershell.exe traffic to 45.77.53.176 — the only non-corporate external IP contacted almost exclusively by powershell.exe, and target of the feed's single stratum-port (3333) flow. The mining endpoint is 192.168.70.186 (FyodorMalteskesko's workstation): sole stratum connection, 3.8x the flows and 6x the bytes of the other beaconing host. Total pool-flow time = sum(fes-fss) = 3,452 (443) + 112 (3333) = 3,564 seconds.

## Assumptions
- 45.77.53.176 = Monero pool — VERIFIED indirectly (powershell-exclusive, stratum 3333); UNVERIFIED via DNS (tools withdrawn before check)
- Mining endpoint = 192.168.70.186 — VERIFIED (sole dp=3333 flow)
- "Total seconds generating" = sum(fes-fss) over that endpoint's pool flows — UNVERIFIED definition; alternates 112 / 4,830 / 5,049
- fes-fss = duration in seconds — VERIFIED (integer epochs in samples)

## Ruled out
- literal "monero" string: 0 events
- 192.168.105.214 Edge flows: browser to frothly.com, not mining
- Minesweeper.exe: MS-game CDN traffic; hdoor.exe: internal lateral movement (3s)
- wall-clock 7,070s: question forbids hand estimation

## Open questions for SH
- Does "total seconds" mean the stratum session only (112), all of 192.168.70.186's pool traffic (3,564), or both beaconing endpoints (4,830)?
- Is 192.168.24.128 (AlBungstein) a second mining endpoint or C2-only?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
