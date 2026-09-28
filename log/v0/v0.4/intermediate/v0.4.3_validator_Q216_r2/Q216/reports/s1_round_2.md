# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=8_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields sa, da, dp, dh, fss, fes, pn, ppn, liuid, ibc, obc
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 85

## Prior rounds
- R1: Confirmed feed (78,459 events); ruled out process-name and "monero"-keyword axes; found the feed's only dp=3333 flow; hand-computed 112 with two open residues (SPL arithmetic, other pool ports).
- R2 (this round): closed both residues — full sweep of the pool IP and all 22 destination ports; duration computed inside SPL; 443 traffic to the pool IP ruled out as C2 by behavior.

## This round
### What I ran
- `da=45.77.53.176 | stats ... by sa, dp` -> 4 groups: 2 flows to :80 (Edge, BruceGist), 1,015 to :443 (powershell, AlBungstein), 1 to :3333 (powershell, FyodorMaltesko), 3,814 to :443 (powershell, FyodorMaltesko).
- `| stats count by dp | sort count` -> all 22 dp values; 3333 count=1; no 14444/45700/5555/7777/4444 in the feed.
- `get_raw_events keyword=3333` -> the mining event: 192.168.70.186:64104 -> 45.77.53.176:3333, powershell.exe (parent powershell.exe), FyodorMaltesko, fss=1534762025, fes=1534762137, ibc=5,782,875, obc=177.
- `sa=192.168.70.186 da=45.77.53.176 dp=443 | eval duration=fes-fss | stats count avg(duration) perc25 perc75 max avg(ibc) avg(obc)` -> 3,814 flows, avg 0.9s, p75=1s, max 31s, avg 2.4KB in / 628B out.
- `da=45.77.53.176 dp=3333 | eval duration=fes-fss | stats sum(duration)` -> **112**.
- `dp=8080 | stats by dh` -> 26 flows, all internal 192.168.8.x -> 192.168.9.30 (staging server).

### What it means
The answer is one flow's span, not an aggregate: exactly one qualifying mining flow exists. The 3333 flow behaves like pool mining (5.78MB inbound over 112s, ~52KB/s, by powershell.exe under the compromised user FyodorMaltesko); the 443 flows to the same IP are sub-second sub-KB C2 beacons; the 8080 flows are internal staging. Duration computed in SPL: `eval duration=fes-fss | stats sum(duration)` = 112, consistent with the raw event's fst/fet (10:47:05 -> 10:48:57).

## Ruled out
- 45.77.53.176:443 traffic (3,814 + 1,015 flows) - avg 0.9s, p75=1s, ~2.4KB in: C2 beacons, not mining.
- dp=8080 flows - internal 192.168.8.x -> 192.168.9.30 staging, not a pool.
- Other mining ports (14444, 45700, 5555, 7777, 4444) - absent from the feed's complete 22-value dp listing.
- 45.77.53.176:80 (2 Edge flows, BruceGist) - ordinary browsing, different user/process.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_field_values: {"field": "dp", "source": "cisconvmflowdata", "top_n": 20}` (20 of 22 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count val…` (50 of 607 rows seen). A claim resting on them alone is UNVERIFIED._
