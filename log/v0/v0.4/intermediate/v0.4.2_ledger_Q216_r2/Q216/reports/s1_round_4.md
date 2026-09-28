# s1 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa, da, pn, ppn, dp, fss, fes, ibc, obc, liuid
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 80

## Prior rounds
- R1: Feed confirmed (78,459 events); 60-process and 22-port censuses read in full; leads iexepler.exe (15), hdoor.exe (7), dp=3333 (1); ASCII pn filters fail (homoglyph value).
- R2: hdoor.exe ruled out (internal 21/22/3306 scan); dp=3333 flow recovered — powershell.exe, 192.168.70.186 → 45.77.53.176, 112 s.
- R3: iexepler.exe's 15 flows recovered via count=15 — internal C2 (192.168.9.30:8080), ruled out; 45.77.53.176 also carries 4,829 one-second powershell:443 beacons from two endpoints; "monero" keyword → 0.
- R4: candidate row re-queried with SPL-computed duration; phase comparison of adjacent powershell flows run.

## This round
### What I ran
- `| stats count min(fss) as fss max(fes) as fes sum(ibc) sum(obc) values(liuid) values(ppn) by sa da pn dp | search dp=3333 | eval duration_seconds=round(fes-fss)` -> 1 row: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, ppn=powershell.exe, liuid=AzureAD\FyodorMalteskesko, fss=1534762025, fes=1534762137, ibc=5,782,875, obc=177, **duration_seconds=112**.
- `sa=192.168.70.186 da=45.77.53.176 pn=powershell.exe | eval phase=case(fes<1534762025,"before", fss>=1534762025 AND fes<=1534762137,"during", fss>1534762137,"after") | stats count min(fss) max(fes) sum(ibc) sum(obc) by phase dp` -> before/443: 1,485 flows (1534759304–1534762024); during/3333: the candidate; during/443: 75 flows; after/443: 2,251 flows (1534762364–1534766374).

### What it means
The 3333 session is embedded in a 443 beacon channel that predates it by ~45 minutes and outlives it by ~74 minutes (resuming after a 227-second pause). The beacons are therefore not a product of the 3333 session, and the session is not their setup — it is a distinct, one-off, 112-second connection on the canonical Monero pool port, the only flow on that port in all 78,459 events, from the only endpoint that has it. Per the decision rule, the 3333 row is the mining act: duration = fes−fss = 1534762137−1534762025 = **112 s**, computed in SPL as `round(fes-fss)`. Residual caveat kept in confidence: the flow's byte direction (5.78 MB in / 177 B out) is download-shaped, but no other act in this feed is mining-shaped and the 443 channel is C2 (two endpoints, 1-second beacons, IP also serves www.frothly.com).

## Ruled out
- powershell:443 beaconing as the mining record set — independent of the 3333 session (before/during/after), present on two endpoints, C2-shaped; its span would be 7,070 s (.70.186) if ever reinstated.
- iexepler.exe (15 flows) — internal 192.168.8.103 → 192.168.9.30:8080, 9 KB in / 53 KB out: C2/exfil.
- hdoor.exe (7 flows) — internal scan of 192.168.9.x on 21/22/3306.
- 58 other process names, 21 other ports, all other destinations (censuses read); non-NVM sources.