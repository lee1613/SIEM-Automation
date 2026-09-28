# s1 - Q216 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=1_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata (78,459 events)
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 85

## Prior rounds
- R1: Mapped feed (fss/fes, pn, sa/da, dp); all 60 pn values read; masquerade lead unretrievable literally; hdoor.exe ruled out (internal scan).
- R2: Stored name iexepler.exe -> internal 192.168.9.30:8080 (C2/staging). Complete dp enumeration: only stratum port 3333, exactly 1 flow, powershell.exe, 192.168.70.186 -> 45.77.53.176. fes-fss = 112.
- R3: Other pool ports on dp/sp (0 events); dh regex found Coinhive browser flows (6, different host); .70.186 destination map confirmed 45.77.53.176 is its only attacker destination; duration recomputed = 112.
- R4: Closed last coverage hole (raw-text monero/xmr/stratum -> 0 events); side-by-side selection table of stratum flow vs Coinhive flows; timing-field result restated verbatim.

## This round
### What I ran
- `dp=3333 | stats count values(fss) values(fst) values(fes) values(fet) values(sa) values(pn) values(ibc) values(obc) | eval duration_seconds=fes-fss` -> count=1, fss=1534762025, fst="Mon Aug 20 10:47:05 2018", fes=1534762137, fet="Mon Aug 20 10:48:57 2018", endpoint=192.168.70.186, process=powershell.exe, ibc=5782875, obc=177, duration_seconds=112.

### What it means
FOUND — the answer chain, restated from query results:

**Coverage.** Every representation of Monero generation this feed can carry was checked: (1) destination ports — complete dp enumeration (22 values, all returned): only Monero pool port is 3333, carrying exactly 1 flow, powershell.exe; (2) other pool ports on both dp and sp (4444,5555,7777,9999,14433,14441,14442,14444,45700,8333,8899,3334) — 0 events; (3) destination hostnames — dh regex (pool|xmr|monero|stratum|mine|coin|hash) — 10 rows: the Coinhive family (6 flows) plus four non-mining keyword matches (game, ad networks, Skype); (4) raw event text (monero|xmr|stratum) — 0 events; (5) process names — all 60 pn values read: no miner name, only the iexepler.exe masquerade going to internal 192.168.9.30:8080 (C2/staging). Only one candidate mining flow matched: the single dp=3333 flow.

**Selection.** The reportable duration comes from that flow because it is the APT mining act: the only flow on the Monero stratum port in the entire feed, from the compromised endpoint 192.168.70.186 (powershell.exe as SYSTEM, user FyodorMalteskesko) to 45.77.53.176 — the same IP carrying that host's 95-byte 443 C2 beacons and the www.frothly.com watering hole — moving 5,782,875 bytes in / 177 out. The Coinhive-derived durations (1603 longest flow, 1667 span, 1758 sum) belong to a different endpoint (192.168.247.131, chrome.exe, BudStoll) doing browser cryptojacking on ordinary port 443 in six fragmented flows with kilobyte volumes — no single duration, not "the endpoint" of this attack.

**Definition.** "For how many seconds does the endpoint generate Monero" is satisfied by the Cisco NVM flow-duration calculation on that one mining flow, because the feed contains exactly one mining flow, so its own timing fields are the whole session: fes-fss = 1534762137-1534762025 = 112, corroborated verbatim by fst="Mon Aug 20 10:47:05 2018" -> fet="Mon Aug 20 10:48:57 2018" (1m52s). With one flow, flow-duration and sum-across-flows coincide.

## Ruled out
- Coinhive flows on 192.168.247.131 (durations 1603/1667/1758) - different endpoint, browser cryptojacking on 443, six fragmented flows, no single duration.
- 443 flows to 45.77.53.176 - 95-byte C2 beacons (ibc=0, obc=95), not mining.
- iexepler.exe -> 192.168.9.30:8080 - internal C2/staging, not a pool.
- Other pool ports on dp/sp - 0 events. minesweeperonline.com / pool.adizio.com / pool.admedo.com / webpoolblu3a16.infra.lync.com - keyword matches only. Raw-text monero/xmr/stratum - 0 events.

## What I'd tell my replacement
- Retired because: Done on substance: this senior established a stable candidate of 112 from Cisco NVM timing fields and exhausted the direct verification loop. Retiring avoids another same-senior repetition on the same settled lead.
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'duration', 'app', 'action']
- Rounds worked: 5/8  (iterations: 40, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | stats count by pn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp IN (4444,5555,7777,9999,14433,14441,14442,14444,45700,8333,8899,3334) OR sp IN (4444,5555,7777,9999,14433,14441,14442,14444,45700,8333,8899,3334)) | stats count values(pn) as processes values(sa) as endpoints values(da) as destinations
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=3333 OR dp=8080) | stats count min(fss) as first_start max(fes) as last_end values(da) as dest_ips values(sa) as src_ips values(liuid) as users values(ppn) as parents by pn, dp, da, sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (pn=iexeoler.exe OR pn=hdoor.exe) | stats count min(fss) as first_start max(fes) as last_end values(da) as dest_ips values(dp) as dest_ports values(sa) as src_ips values(liuid) as users by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sp=3333 OR dp=3333) | stats count values(sa) as src values(da) as dst values(pn) as processes values(liuid) as users min(fss) as first_start max(fes) as last_end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 OR dh="*coinhive*" | stats count min(fss) as first_start max(fes) as last_end values(ibc) as in_bytes values(obc) as out_bytes values(sa) as endpoints values(liuid) as users values(sp) as src_ports by dh, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports by pn, sa, liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(pn) as processes values(dp) as ports values(sa) as endpoints values(dh) as dest_host values(liuid) as users
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | stats count min(fss) as first_start max(fes) as last_end values(ibc) as in_bytes values(obc) as out_bytes values(sa) as endpoints values(liuid) as users values(da) as dest_ips values(pn) as processes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dh="*coinhive*" | stats values(fss) as start values(fes) as end values(ibc) as in_bytes values(obc) as out_bytes values(sp) as src_port by dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 OR dh="*coinhive*" | stats count min(fss) as first_start max(fes) as last_end values(sa) as endpoint values(pn) as process values(liuid) as user values(da) as dest_ips values(ibc) as bytes_in values(obc) as bytes_out by dp, dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count min(fss) as flow_start max(fes) as flow_end values(fst) as start_text values(fet) as end_text values(dh) as dest_host values(pn) as process values(sa) as endpoint values(da) as dest_ip values(liuid) as user | eval duration_seconds=flow_end-flow_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(fss) as flow_start_epoch values(fst) as flow_start_text values(fes) as flow_end_epoch values(fet) as flow_end_text values(sa) as endpoint values(da) as pool_ip values(pn) as process values(liuid) as user values(ibc) as bytes_in values(obc) as bytes_out | eval duration_seconds=fes-fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(fss) as fss values(fst) as fst values(fes) as fes values(fet) as fet values(ibc) as ibc values(obc) as obc | eval duration_seconds=fes-fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(fss) as fss values(fst) as fst values(fes) as fes values(fet) as fet values(sa) as endpoint values(pn) as process values(ibc) as ibc values(obc) as obc | eval duration_seconds=fes-fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count values(ibc) as inbound_bytes values(obc) as outbound_bytes values(sp) as src_port values(pr) as protocol values(fss) as start values(fes) as end | eval duration_seconds=fes-fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats min(fss) as s max(fes) as e | eval duration_seconds=round(e-s)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexe* | stats count min(fss) as first_start max(fes) as last_end values(da) as dest_ips values(dp) as dest_ports values(sa) as src_ips values(liuid) as users values(ppn) as parent by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexeoler* | stats count min(fss) as first_start max(fes) as last_end values(da) as dest_ips values(dp) as dest_ports values(sa) as src_ips values(liuid) as users values(ppn) as parent
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexeoler.exe | stats count min(fss) as first_start max(fes) as last_end values(da) as dest_ips values(dp) as dest_ports values(sa) as src_ips values(liuid) as users values(ppn) as parent
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports values(pn) as processes values(dh) as dest_hosts by da | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | regex "(?i)(monero|xmr|stratum)" | stats count values(dh) as dest_hosts values(pn) as processes values(sa) as endpoints
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count dc(sa) as endpoints values(pn) as processes by dp | sort dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count values(dp) as ports by dh | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count values(dp) as ports values(pn) as processes dc(sa) as endpoints by da | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats dc(dp) as distinct_dest_ports dc(sp) as distinct_src_ports dc(dh) as distinct_dest_hosts dc(da) as distinct_dest_ips dc(pn) as distinct_processes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats min(fss) as feed_first_start max(fes) as feed_last_end count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | where match(dh, "(?i)(pool|xmr|monero|stratum|mine|coin|hash)") | stats count values(dp) as ports values(pn) as processes values(sa) as endpoints by dh
