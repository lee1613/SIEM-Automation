# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata (78,459 events) | fields: sa, sp, da, dp, fss, fst, fes, fet, pn, ppn, liuid, ibc, obc
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 60

## Prior rounds
None — round 1.

## This round
### What I ran
- get_sources syslog -> cisconvmflowdata confirmed (78,459 events).
- get_sourcetype_fields + sample_events -> flow schema: sa/da/sp/dp, fss/fes (epoch-sec flow start/end), pn (process), ibc/obc (bytes), liuid (user).
- `| stats count by pn` (60 rows) -> mostly benign; rare oddities: iexeoler.exe (15), hdoor.exe (7).
- `| stats count by dp` (22 rows) -> 443/53/80 dominate; **3333 appears exactly once**; no 4444/5555/7777/14444/14433 anywhere.
- `dp=3333 | stats ...` -> 1 event: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, liuid=AzureAD\FyodorMalteskesko, fss=1534762025 (10:47:05), fes=1534762137 (10:48:57), ibc=5,782,875, obc=177.
- `da=45.77.53.176 | stats count dc(sa) values(sa) values(dp) values(pn) values(liuid) min(fss) max(fes) sum(eval(fes-fss))` -> 4,832 events, 3 endpoints (192.168.70.186 via powershell.exe; 192.168.105.214 and 192.168.24.128 via MicrosoftEdgeCP.exe), dp 3333/443/80, sum duration 5,049s, window 09:48:53-11:59:34.

### What it means
Port 3333 is the canonical Monero pool port and occurs exactly once in the whole feed: powershell.exe on endpoint 192.168.70.186 (FyodorMalteskesko logged in) pulling 5.7MB from 45.77.53.176:3333 — the miner's pool connection. Duration = fes-fss = 1534762137-1534762025 = 112 seconds (fst 10:47:05 -> fet 10:48:57 confirms). Formula: `index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats sum(eval(fes-fss))` -> 112.

## Ruled out
- Other Monero pool ports (4444/5555/7777/14444/14433) - absent from the full dp distribution.
- 5,049s (sum over all 4,832 flows to 45.77.53.176) - includes MicrosoftEdgeCP.exe browsing from two other endpoints/users (AlBungstein, BruceGist); not Monero generation by "the endpoint".

**Gaps (cap hit):** breakdown of the 4,832 flows by pn/dp/sa not run — if powershell.exe made further pool flows on 443/80 the total exceeds 112; dp=8080 (26 events) and hdoor.exe/iexeoler.exe destinations unchecked.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort - count` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
