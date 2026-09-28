# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, ppn, sa, da, dh, dp, fss, fes, ibc, obc, liuid
**Insight:** partial   **Candidate:** 112   **Confidence:** 55

## Prior rounds
- R1: Feed confirmed (78,459 events); fields mapped (fss/fes epoch start/end, pn, sa, dp, ibc/obc); 60-process and 22-port censuses read in full; leads: iexepler.exe (15), hdoor.exe (7), dp=3333 (1); every pn filter returned 0.
- R2: hdoor.exe recovered and ruled out (internal port scan); the dp=3333 flow recovered — powershell.exe on 192.168.70.186 → 45.77.53.176, 112 s; iexepler.exe proven homoglyph-named, its 15 records still unretrieved.

## This round
### What I ran
- get_raw_events keyword "iexepler" -> 0 events; `| where pn="iexepler.exe"` and `pn=iexepler*` -> 0 each. Raw text lacks ASCII "iexepler" although the census lists 15 events → the pn value is homoglyph-disguised.
- Per-pn aggregation `| stats count min(fss)... by pn | sort count | head 25` -> 12 of 25 rows returned (too large); hdoor/iexepler rows not among them.
- `| stats ... by pn | search pn IN ("hdoor.exe","iexepler.exe")` -> hdoor.exe only: 7 flows, sa=192.168.8.103 → 192.168.9.20/25/26/30/50, dp=21/22/3306, 296 B in / 0 B out, parent powershell.exe, user FyodorMalteskesko.
- `| stats count min(fss) as first_start max(fes) as last_end ... by dp | search dp=3333` -> 1 flow: pn=powershell.exe, parent=powershell.exe, sa=192.168.70.186, da=45.77.53.176, dh=Unknown, ibc=5,782,875, obc=177, liuid=AzureAD\FyodorMalteskesko, fss=1534762025, fes=1534762137.

### What it means
The only record in the entire feed on a canonical Monero pool port (3333) is a 112-second flow (fes−fss = 1534762137−1534762025 = 112) from endpoint 192.168.70.186 (FyodorMalteskesko) to external 45.77.53.176, run by powershell.exe under powershell.exe. That is the candidate. It is not yet confirmed as generation rather than setup: 5.78 MB in vs 177 B out resembles a miner-binary download more than pool share submission, and the homoglyph-named process's 15 flows — unreachable by ASCII filters — remain an unexamined alternative record set. Hence partial, not FOUND.

## Ruled out
- hdoor.exe — 7 flows to internal 192.168.9.x on 21/22/3306, 296 B in / 0 B out: a port scan, not mining.
- All 58 other process names and all 21 other destination ports (full censuses read).
- Sources /var/log/syslog, /var/log/messages, /var/log/auth.log, cisconvmsysdata, cisconvmifdata — not the NVM flow feed.

## Next round
- Retrieve the homoglyph process's flows without typing its name: `| stats count min(fss) as s max(fes) as e values(sa) values(da) values(dp) sum(ibc) sum(obc) by pn | search count=15` (only WWAHost.exe shares count=15).
- Check other flows to the pool IP: `| stats ... by da | search da=45.77.53.176`.
- If those show pool traffic, recompute duration as their span; otherwise confirm 112 with `| eval duration=round(fes-fss)`.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count min(fss) as first_sta…` (12 of 25 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort -count` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
