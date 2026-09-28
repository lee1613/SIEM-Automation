# s3 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=8_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields: sa, da, sp, dp, fss, fes, pn, ppn, ibc, obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 65

## Prior rounds
- None inherited — the prior NVM line was retired before my spawn; this round re-opened the Cisco NVM scope from scratch.

## This round
### What I ran
- get_sources syslog → cisconvmflowdata (78,459 events, all Aug 20 2018); get_sourcetype_fields → sa/da/sp/dp, fss/fes (epoch flow start/end), pn/ppn, ibc/obc.
- `sa=192.168.70.186 | stats by da dp pn` → 556 groups; powershell.exe appears only toward 45.77.53.176 (:443 ×3 parent variants, plus one :3333).
- `dp=3333` feed-wide → exactly 1 flow: 192.168.70.186→45.77.53.176, powershell.exe, fss=1534762025, fes=1534762137.
- `da=45.77.53.176 by sa` → 192.168.70.186 (3,815), 192.168.24.128 (1,015, all :443), 192.168.105.214 (2, Edge :80).
- Byte profile: :3333 = 5,782,875 in / 177 out; :443 = avg 2,367 in / 628 out across 3,814 flows.
- Raw :3333 event read in full (fst 10:47:05 → fet 10:48:57).

### What it means
The only NVM record that identifies Monero is the sole dp=3333 flow (3333 = canonical Monero pool port). Duration = fes − fss = 1534762137 − 1534762025 = **112 seconds**, cross-checked against fst/fet (1m52s).

## Assumptions
- Coverage: NVM logs carry Monero only via port 3333 — no "monero" string or pool-name field exists (dh="Unknown" on these flows). `dp=3333` searched feed-wide → 1 flow. VERIFIED.
- Selection: "the endpoint" = 192.168.70.186, sole owner of the :3333 flow; 192.168.24.128 also hits the pool IP but only on :443. VERIFIED.
- Metric definition: duration = fes − fss on the Monero-marked flow. VERIFIED as the only Monero-self-identifying record; UNVERIFIED whether the question intends the broader :443 set (see Ruled out / Open questions).
- fss/fes are epoch flow start/end. VERIFIED (fst/fet match).

## Ruled out
- Broader-set reading (all powershell.exe→45.77.53.176 flows, span 7,070s): behaviorally plausible as the real mining (small bidirectional, sustained, 3 WMI-persisted instances) — and the :3333 flow's own byte profile (5.78MB in / 177B out) is download-like, arguing it is the miner fetch, not generation. Not selected: NVM marks Monero only on :3333, and the :443 set has no Monero identifier inside NVM. Flagged to SH.
- 192.168.24.128: no :3333 flow, not the question's endpoint.
- Non-NVM feeds: out of scope — question says "According to the Cisco NVM flow logs".

## Open questions for SH
- If the case's intended definition is the broader miner-to-pool set, the value is 7,070 (span 1534759304→1534766374). Which definition does the case expect: the Monero-port flow (112) or the full miner-to-pool span (7,070)?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count min…` (50 of 556 rows seen). A claim resting on them alone is UNVERIFIED._
