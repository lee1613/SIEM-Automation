# s1 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata (78,459 events)
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 85

## Prior rounds
- R1: Mapped feed (fss/fes epochs, pn, sa/da, dp); read all 60 pn values; masquerade lead "iexeoler.exe" unretrievable literally; hdoor.exe ruled out (internal scan).
- R2: Stored name iexepler.exe -> internal 192.168.9.30:8080 (C2/staging). Complete dp enumeration: only stratum port 3333, exactly 1 flow, powershell.exe, 192.168.70.186 -> 45.77.53.176. Computed fes-fss = 112.
- R3: Tested other pool ports on dp and sp (0 events); dh regex found Coinhive browser flows (6, different host); full destination map of .70.186 confirmed 45.77.53.176 is its only attacker destination; recomputed duration = 112.

## This round
### What I ran
- `| regex "(?i)(monero|xmr|stratum)"` -> 0 events: no event text names Monero (last coverage hole closed).
- `| stats dc(dp) dc(sp) dc(dh) dc(da) dc(pn)` -> 22 / 16,265 / 1,573 / 2,735 / 60 distinct values: the full indicator space tested.
- `dp=3333 OR dh="*coinhive*" | stats ... by dp, dh` -> 7 rows, both candidates side by side with identity, timing, and byte volumes.
- `dp=3333 | stats count values(fss) values(fst) values(fes) values(fet) values(ibc) values(obc) | eval duration_seconds=fes-fss` -> count=1, fss=1534762025, fes=1534762137, fst="Mon Aug 20 10:47:05 2018", fet="Mon Aug 20 10:48:57 2018", ibc=5782875, obc=177, **duration_seconds=112**.

### What it means
FOUND. (1) Coverage — every Monero-generation representation in this feed was tested: complete dp enumeration (22 values, only 3333 is a pool port, 1 flow), 11 other pool ports on both dp and sp (0 events), dh regex over pool/xmr/monero/stratum/mine/coin/hash (10 rows: Coinhive family plus four non-mining keyword matches — game, ad networks, Skype), raw-text regex monero/xmr/stratum (0 events), complete pn enumeration (60 values, no miner name). Nothing appeared besides the dp=3333 stratum flow and the six Coinhive browser flows. (2) Selection — the stratum flow is the APT mining act: only flow on the Monero stratum port in the feed, from compromised endpoint 192.168.70.186 (powershell.exe, FyodorMalteskesko) to 45.77.53.176 (same IP as its 95-byte C2 beacons and the watering hole), 5,782,875 bytes in / 177 out. The Coinhive flows are a different host (192.168.247.131, chrome.exe, BudStoll) on ordinary 443 with kilobyte volumes, six fragmented flows (2/4/12/13/124/1603s) — browser cryptojacking with no single duration; 1603, 1667 and 1758 are its numbers and none fits a single-endpoint single-duration reading. (3) Definition — "for how many seconds" is the duration of the mining flow itself, from the Cisco NVM timing fields on that flow: fes-fss = 1534762137-1534762025 = 112, corroborated by fst/fet (10:47:05 -> 10:48:57 = 1m52s); with exactly one mining flow, flow-duration and sum-across-flows coincide.

## Ruled out
- Coinhive flows on 192.168.247.131 (durations 1603/1667/1758) - different endpoint, browser cryptojacking on 443, six fragmented flows, no single duration.
- 443 flows to 45.77.53.176 - 95-byte C2 beacons (ibc=0, obc=95), not mining.
- iexepler.exe -> 192.168.9.30:8080 - internal C2/staging host, not a pool.
- Other pool ports on dp/sp (4444,5555,7777,9999,14433,14441,14442,14444,45700,8333,8899,3334) - 0 events.
- minesweeperonline.com / pool.adizio.com / pool.admedo.com / webpoolblu3a16.infra.lync.com - game, ad networks, Skype infra: keyword matches only.