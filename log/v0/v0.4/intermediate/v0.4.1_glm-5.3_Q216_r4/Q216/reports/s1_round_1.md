# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=20_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn,ppn,da,sa,dp,fss,fes,liuid
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 60

## Prior rounds
- Round 1 (this round): confirmed feed (78,459 events, all Aug 20 2018); enumerated pn/dp/da/mnl; found powershell.exe→45.77.53.176 from two endpoints; isolated the feed's only dp=3333 (Monero stratum) flow.

## This round
### What I ran
- get_sources(syslog) → cisconvmflowdata confirmed, 78,459 events.
- top pn / top dp / top da → no miner-named process; ports 443/53/80 dominate; 45.77.53.176 = 4,832 events.
- da=45.77.53.176 | stats by sa dp pn → powershell.exe from 192.168.24.128 (AlBungstein, 1015 flows :443) and 192.168.70.186 (FyodorMalteskesko, 3814 flows :443 + 1 flow :3333).
- dp=3333 | stats → exactly 1 flow in the whole feed: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, fss=1534762025, fes=1534762137.
- match(pn,"(?i)(miner|xmr|monero|cryptonight|stratum|pool)") → 0; top mnl → only Windows system DLLs.

### What it means
FOUND: Port 3333 is the canonical Monero stratum port and the only such flow in the feed, uniquely identifying one endpoint (192.168.70.186) with a clean window: 1534762137 − 1534762025 = 112 seconds. The much larger :443 traffic to the same IP spans two endpoints over ~2 hours, consistent with C2 rather than a mining-only window.

## Assumptions
- Coverage: Monero could appear as (a) process name — searched via top pn + regex → 0; (b) dest port 3333 — searched → 1 flow; (c) module list mnl — top mnl → system DLLs only; (d) dest IP reputation — 45.77.53.176 flagged, pool status UNVERIFIED; (e) masquerade process iexepler.exe — appeared in top pn (15 events) but exact/regex/like/raw searches all returned 0 — UNVERIFIED anomaly.
- Selection: port 3333 chosen over dest-IP because it is Monero-canonical and isolates one endpoint; the :443 hypothesis was not ruled out (7070s/7102s alternatives).
- Premise: fss/fes are flow start/end epoch seconds — VERIFIED (fst/fet human-readable twins present).
- Premise: final subtraction done on SPL outputs, not inside eval — UNVERIFIED as SPL-computed.

## Ruled out
- Miner-named processes (miner/xmr/monero/cryptonight/stratum/pool) — 0 events.
- mnl module lists — Windows system DLLs only.

## Open questions for SH
- Is the intended indicator port 3333 (→112s) or destination 45.77.53.176 (→7070s for 192.168.70.186, 7102s for 192.168.24.128)?
- Is the unretrievable "iexepler.exe" (15 events in top pn) a known data quirk, and could it be the miner process?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
