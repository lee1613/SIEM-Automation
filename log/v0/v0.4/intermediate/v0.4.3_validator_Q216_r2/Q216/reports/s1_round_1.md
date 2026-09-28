# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=4_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields pn, ppn, sa, da, dh, dp, fss, fes, liuid
**Insight:** FOUND (partial — candidate held, two residues unverified)
**Candidate:** 112   **Confidence:** 72

## Prior rounds
- Round 1 (this round): established the feed, ruled out process-name and keyword axes, isolated the single port-3333 mining flow.

## This round
### What I ran
- get_sources syslog -> cisconvmflowdata confirmed, 78,459 events.
- get_sourcetype_fields -> pn/ppn (process/parent), sa/da/dh/dp, fss/fes (flow start/end epoch seconds), liuid (user).
- search_keyword monero -> 0 events.
- get_field_values pn (50 of 60) + `rare pn limit=15` -> no miner-named process in the feed.
- powershell.exe `| stats by dh,dp` -> 6 groups: 4,829 flows to 443 (C2), one each to 3333, 8080, 80, plus bit.ly/leeholmes.com.
- `dp=3333 | stats ... by dh` -> exactly 1 flow: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe (parent powershell.exe), liuid=AzureAD\FyodorMalteskesko, fss=1534762025, fes=1534762137.

### What it means
The feed's only flow to port 3333 — the canonical Monero mining-pool port — is a powershell.exe flow from FyodorMalteskesko's endpoint (192.168.70.186) to 45.77.53.176. Duration = fes − fss = 1534762137 − 1534762025 = 112 seconds. Residues: the subtraction was done by hand (tool limit hit before an SPL eval ran), and other flows to 45.77.53.176 on non-3333 pool ports were not swept.

## Ruled out
- Process-name axis: all 60 pn values read (top 50 + 10 rarest); no miner process.
- Keyword "monero": 0 events in the feed.
- powershell.exe 443 flows (4,829 events, 2 endpoints): sustained C2 volume, no pool port.
- 8080 / bit.ly / leeholmes.com flows: miner download / payload fetch, not generation.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_field_values: {"field": "pn", "source": "cisconvmflowdata", "top_n": 50}` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
