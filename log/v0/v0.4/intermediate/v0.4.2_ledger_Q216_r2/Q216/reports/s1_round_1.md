# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dh, dp, fss, fes, ibc, obc, liuid
**Insight:** NOT_FOUND   **Candidate:** none   **Confidence:** 0

## Prior rounds
- (Round 1 — this is the first round.)

## This round
### What I ran
- get_sources(sourcetype=syslog) -> cisconvmflowdata confirmed, 78,459 events (also cisconvmsysdata 11, cisconvmifdata 8 exist but are not the flow feed).
- get_sourcetype_fields(cisconvmflowdata) -> 53 fields; fss/fes = flow start/end epochs, pn = process, sa = endpoint IP, dp = dest port, ibc/obc = bytes.
- `| stats count by pn | sort -count` -> 60 distinct processes; read 50 of 60 rows plus the 10 rarest via `rare limit=60 pn` (which re-listed the tail), so all 60 names were seen. Anomalies: iexepler.exe (15, typo-squat of iexplore.exe), hdoor.exe (7).
- `| stats count by dp | sort -count` -> 22 distinct ports, all read. dp=3333 (classic Monero pool port) has exactly 1 event.
- `pn="iexepler.exe" | stats count min(fss) ... max(fes) ...` (quoted and unquoted) -> count=0 both times, contradicting the 15-event listing.

### What it means
NOT_FOUND: the mining activity is almost certainly pinned — iexepler.exe and/or hdoor.exe, with dp=3333 corroborating a pool connection — but the pivot to the actual flow records failed (0 events on a field filter that the aggregation says holds 15), so no start/end epochs were ever retrieved and no duration exists to report. Inventing one is not an option.

## Ruled out
- All 58 other process names in the feed — enumerated in full (60 total via stats-by-pn + rare); none is a plausible miner (svchost, chrome, streamfwd, powershell, etc.).
- All ports except 3333 as the pool-port lead — full 22-value dp list read; 443/53/80/5353 dominate and are generic.
- source=/var/log/syslog, /var/log/messages, /var/log/auth.log, cisconvmsysdata, cisconvmifdata — not the Cisco NVM flow feed the question names.

## Next round
Fix the pn filter (try `| where pn="iexepler.exe"`, `pn=iexepler*`, or get_raw_events on one of the 15 events found via `stats count by pn, sa, dp`), decide iexepler.exe vs hdoor.exe vs the dp=3333 flow by their records' behaviour (destination, bytes, duration), then `| stats min(fss) as start max(fes) as end | eval duration=round(end-start)`.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort -count` (50 of 60 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | rare limit=60 pn` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
