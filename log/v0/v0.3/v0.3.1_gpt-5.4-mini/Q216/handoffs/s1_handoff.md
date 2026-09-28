# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa, da, dh, dp, fst, fet, fss, fes, liuidp, pn, ppn
**Insight:** FOUND
**Candidate:** 87   **Confidence:** 98

## Prior rounds
- Confirmed Cisco NVM flow data exists as source=cisconvmflowdata under sourcetype=syslog in index=botsv3.
- Confirmed timing and endpoint fields are present: sa, liuidp, dh, fst/fet, fss/fes.
- Identified a mining candidate: 192.168.105.214 / BruceGist connecting to pool.adizio.com and pool.admedo.com.
- Established that the relevant Cisco NVM pool activity is concentrated in those two destination hostnames.

## This round
### What I ran
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.105.214 liuidp=BruceGist (dh=pool.adizio.com OR dh=pool.admedo.com) | stats min(fss) as first_seen max(fes) as last_seen count by dh` -> 2 rows: pool.adizio.com first_seen=1534770925 last_seen=1534771012; pool.admedo.com first_seen=1534770927 last_seen=1534771012.
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.105.214 liuidp=BruceGist (dh=pool.adizio.com OR dh=pool.admedo.com) | stats min(fss) as first_seen max(fes) as last_seen | eval duration_seconds=last_seen-first_seen | table first_seen last_seen duration_seconds` -> 1 row: first_seen=1534770925, last_seen=1534771012, duration_seconds=87.
### What it means
The same endpoint and user that matched the mining pools has a contiguous Cisco NVM flow window from 1534770925 to 1534771012. Subtracting those timestamps inside SPL yields 87 seconds, which is the requested Monero-generation/mining duration rounded to the nearest second.

## Ruled out
- Other destinations in cisconvmflowdata - not needed once the mining pool hosts were confirmed.
- Generic Monero keyword searches - no direct token surfaced in sample events, but pool-host evidence was sufficient.

## Open questions for SH
- None for this scope; the requested duration is now computed from Cisco NVM flow records.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src', 'dest', 'src_ip', 'dest_ip', 'bytes', 'packets', 'transport', 'app', 'url', 'dest_port']
- Rounds worked: 2/8  (iterations: 13, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata (dh=*pool* OR da=*pool* OR mnl=*monero* OR mhl=*monero*) | stats count by sa liuidp dh | sort -count | head 20
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dh=*pool* OR da=*pool* OR mnl=*monero* OR mhl=*monero*) | stats count by sa liuidp dh | sort -count | head 20
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dh=pool.adizio.com OR dh=pool.admedo.com OR dh=pool*) | stats count by sa liuidp dh | sort -count | head 20
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.105.214 liuidp=BruceGist (dh=pool.adizio.com OR dh=pool.admedo.com) | stats min(fss) as first_seen max(fes) as last_seen min(fst) as first_text max(fet) as last_text count by dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.105.214 liuidp=BruceGist (dh=pool.adizio.com OR dh=pool.admedo.com) | stats min(fss) as first_seen max(fes) as last_seen | eval duration_seconds=last_seen-first_seen | table first_seen last_seen duration_seconds
