# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata (78,459 events, all Mon 2018-08-20)
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_sourcetype_fields source=cisconvmflowdata -> 53 fields. Flow timing: fss/fst (start epoch/text), fes/fet (end). Identity: pn (process), ppn (parent), liuid (user). Endpoints: sa/da, sp/dp, dh.
- `| stats count by pn` sorted both directions -> all 60 distinct process names read in full. Rare/masquerading: "iexeoler.exe" (15 events, misspelling of iexplore.exe), hdoor.exe (7), putty.exe (4), ssh.exe (1).
- hdoor.exe flows -> 7 events, 192.168.8.103 -> internal 192.168.9.20/25/26/30/50 on ports 21/22/3306, user FyodorMalteskesko, span 1534761810-1534761844. Port scan, not mining.
- `pn=iexeoler.exe` -> 0; `pn=iexeoler*` -> 0; raw keyword "iexeoler" -> 0. All despite stats counting 15 events under that rendered value.

### What it means
NOT_FOUND: I established how this feed represents flows (fss/fes epochs, pn process) and read every process name, but never retrieved the miner's flow records, so no duration could be computed and no number is submitted. The 15-event process rendered "iexeoler.exe" is the prime miner lead (rare masquerade of iexplore.exe), but its stored value evidently contains a lookalike character (e.g. digit 0 for letter o): literal match, trailing wildcard, and raw keyword search all return 0. Next round: `pn=iexe*` (trailing wildcard on the verified prefix) to capture it, then compute duration in SPL from fss/fes; also check dp for mining-pool ports (3333/4444/5555/7777/14444/45700) as an independent route to the miner's records.

## Ruled out
- hdoor.exe - 7 flows from 192.168.8.103 to internal 192.168.9.x on 21/22/3306: scanning behavior, no pool port, no external mining destination.
- putty.exe / ssh.exe - interactive remote-access tools (4/1 events); not examined as miners, only deprioritized.
- 34.215.24.225 (top destination, 18,392 events) - likely C2/beacon volume, not by itself evidence of mining; not eliminated, kept as pivot.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort -count` (50 of 60 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort count` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
