# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,sp,dp,pn,ppn,fss,fes,ibc,obc
**Insight:** partial   **Candidate:** 112   **Confidence:** 60

## Prior rounds
- None; this is round 1.

## This round
### What I ran
- get_sources syslog -> cisconvmflowdata exists (78,459 events; also cisconvmsysdata 11, cisconvmifdata 8).
- get_sourcetype_fields -> flow model: sa/da, sp/dp, pn/ppn, fss/fes (epoch start/end), ibc/obc; all events Mon Aug 20 2018.
- get_field_values dp -> 22 distinct; 443/53/80 dominate; dp=3333 (Monero Stratum) = exactly 1 event; 2 values unreturned.
- rare pn (40 of 60 read) -> no named miner binary (no xmrig etc.).
- dp=3333 stats -> 1 flow: 192.168.70.186 -> 45.77.53.176, powershell.exe (parent powershell.exe), fss=1534762025, fes=1534762137, ibc=5,782,875, obc=177.
- da=45.77.53.176 by sa/pn/dp -> 4 rows: .70.186 powershell:443 (3,814 flows, 1534759304-1534766374); .24.128 powershell:443 (1,015); .105.214 EdgeCP:80 (2); .70.186 powershell:3333 (1).
- pn=powershell.exe by sa/da/dp -> 7 rows; powershell only reaches 45.77.53.176 (443+3333), two .24.128 HTTP downloads, internal 192.168.8.103->192.168.9.30.

### What it means
The only flow in the entire NVM feed on the canonical Monero pool port 3333 belongs to 192.168.70.186 running powershell.exe (the BOTSv3 macro->powershell vector), to 45.77.53.176 — the same IP carrying all powershell C2 traffic. Its duration fes-fss = 1534762137-1534762025 = 112 seconds. Candidate = 112, already an integer so rounding is moot.

## Assumptions
- Coverage: dp searched (3333 present, 1 event; 2 of 22 dp values unreturned — could hide another pool port) - PARTIALLY VERIFIED; pn searched (rarest 40 of 60 read, no miner binary) - VERIFIED for those rows; sp=3333 NOT searched; mhl/mnl module lists NOT searched for miner modules - UNVERIFIED.
- Selection: 192.168.70.186 owns the only 3333 flow; 192.168.24.128 runs powershell to the same IP on 443 only - ruled out for the 3333 act, NOT ruled out as mining host if 443 is the channel - UNVERIFIED.
- Definition premise: "generates Monero" = flow(s) to a Monero pool, duration = fes-fss. The 3333 record's byte profile (5.7MB in / 177B out) is download-like, so the record does not positively show the act - UNVERIFIED.
- fss/fes are epoch seconds (paired with fst/fet human timestamps) - VERIFIED via field listing.
- Duration arithmetic done by hand (exact integer subtraction); the eval SPL could not run before the cap.

## Ruled out
- Named miner binaries in pn - rarest-40 scan of 60 process names shows none.
- Other endpoints on port 3333 - only one 3333 flow exists in the feed.

## Open questions for SH
- Should the 3,814 powershell->45.77.53.176:443 flows (~7,070s span) be treated as the Monero channel instead of the single 3333 flow? That changes the measurement definition entirely.
- Is 45.77.53.176 established elsewhere in the case as a Monero pool vs attacker C2?

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_field_values: {"field": "dp", "source": "cisconvmflowdata", "top_n": 20}` (20 of 22 rows seen); `get_field_values: {"field": "pn", "source": "cisconvmflowdata", "top_n": 20}` (20 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
