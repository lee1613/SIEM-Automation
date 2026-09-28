# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, fss, fes
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_sources keyword=cisconvmflowdata -> 0; get_sources sourcetype=syslog -> source=cisconvmflowdata, 78,459 events, all Mon Aug 20 2018.
- get_sourcetype_fields -> fss/fes = flow start/end epoch seconds; pn/sa/da/dp = process/src/dst/port.
- `pn="*miner*" OR "*xmr*" OR "*crypt*" OR "*pool*" OR "*stratum*"` -> 0 events; `rare pn limit=30` -> no miner-like names.
- `stats count by dh,da,dp` -> 45.77.53.176:443, dh=Unknown, 4,829 events: the only large unattributed external destination.
- `da=45.77.53.176 | stats count by pn,sa,pr,dp` -> 4 rows: powershell.exe 192.168.70.186:443 x3814 and :3333 x1; powershell.exe 192.168.24.128:443 x1015; MicrosoftEdgeCP.exe 192.168.105.214:80 x2.
- `stats count by dp | sort count` (all 22 rows read) -> exactly one dp=3333 flow feed-wide; no 4444/5555/7777/14444/45700.

### What it means
NOT_FOUND for the number. The representation of Monero generation is now established — powershell.exe flows to unattributed 45.77.53.176, including the feed's single port-3333 (Monero stratum) flow from 192.168.70.186 — but I exhausted iterations before reading fss/fes for those flows, so no duration was computed and no value can be submitted. Next round's first query is in notes.

## Assumptions
- Coverage: Monero generation in this feed could show as (a) miner-named process — searched, 0 events; (b) pool destination port — all 22 dp values read, only 3333 (1 flow); (c) unattributed external destination with heavy traffic — 45.77.53.176, powershell.exe only. VERIFIED. fss/fes exist as epoch seconds — VERIFIED via field listing, but NOT yet read for the mining flows: UNVERIFIED.
- Selection: 45.77.53.176 chosen as the only external IP with no hostname and thousands of flows; powershell.exe the only process reaching it. Whether the 443 flows to it are pool traffic or C2 — UNVERIFIED.
- Definition premise: "generates Monero" = flow(s) to the pool; duration = fes-fss per flow, but whether the answer is the single 3333 flow's duration, the sum, or the span across all mining flows — UNVERIFIED, needs SH's ruling plus the fss/fes values.

## Ruled out
- Miner-named process (xmrig etc.) — wildcard search returned 0 events.
- Other classic pool ports (4444, 5555, 7777, 14444, 45700) — full 22-row dp listing shows none.
- MicrosoftEdgeCP.exe → 45.77.53.176:80 from 192.168.105.214 (2 events) — browser on port 80, third host; likely unrelated, not deeply checked.

## Open questions for SH
- Does "generate Monero" mean only the single dp=3333 stratum flow, or all powershell.exe flows to 45.77.53.176 (ports 443+3333)?
- Is the duration one flow's fes-fss, a sum over flows, or the min(fss)→max(fes) span?
- Both endpoints reach 45.77.53.176 via powershell.exe (192.168.70.186 and 192.168.24.128) — is "the endpoint" restricted to the one holding the 3333 flow?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_field_values: {"field": "pn", "source": "cisconvmflowdata", "top_n": 15}` (15 of 60 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh, da, dp | sort …` (50 of 3742 rows seen); `get_field_values: {"field": "dp", "source": "cisconvmflowdata", "top_n": 15}` (15 of 22 rows seen). A claim resting on them alone is UNVERIFIED._
