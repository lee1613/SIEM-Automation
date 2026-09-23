# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn,sa,da,dp,dh,fss,fes,liuid
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_sourcetype_fields cisconvmflowdata -> 78,459 events, all 2018-08-20; carries fss/fes (flow start/end epochs), pn, sa/da/dp/dh, liuid; no application-classification field.
- `| search monero` -> 0 events; no literal Monero token in the feed.
- `| stats count by pn` (full 60-name coverage via `rare pn` plus an s–z filtered listing) -> no miner-named process; suspicious names: iexepler.exe (15), hdoor.exe (7).
- `pn=Minesweeper.exe | stats ... by sa,da,dp,dh,liuid` -> 11 rows, all Xbox/game/ad destinations from 172.16.133.131 — real game, ruled out.
- `| stats count, dc(sa) by dp` -> 22 ports; dp=3333 (1 event, 1 endpoint — classic Monero Stratum port), dp=8080 (26/2), dp=4287 (17/2); no 4444/5555/7777.

### What it means
NOT_FOUND: the feed's duration mechanism is established (fes−fss, epoch seconds, computable in SPL), but I ran out of iterations before isolating which records are the Monero-classified ones, so no number can be honestly reported. The single dp=3333 flow is the strongest lead and was one query away.

## Ruled out
- Literal "monero" text in cisconvmflowdata — 0 events.
- Minesweeper.exe as the miner — traffic is xboxlive/msgamestudios/vungle ad endpoints.
- Miner-named processes (xmrig/minerd/etc.) — full 60-name pn enumeration shows none.
- dp=9997 (76 events) — Splunk management port, benign.

## Next round
Pull the dp=3333 flow (sa, da, dh, pn, liuid, fss, fes) and compute fes−fss; if it is not the miner, check iexepler.exe and hdoor.exe flows, then dp=8080/4287 endpoints, then dest-host pool naming.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
