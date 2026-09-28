# Q216 — SH <-> Senior conversation

### 14:29:35 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src', 'dest', 'src_ip', 'dest_ip', 'bytes', 'packets', 'transport', 'app', 'url', 'dest_port']
**Technique:** metrics
**Reason:** The answer is a number that must be derived from the Cisco NVM flow feed specifically, so a single metrics senior should first establish the mining-related flow pattern and the exact start/end interval within source cisconvmflowdata.

Within Cisco NVM flow logs for the August 2018 Frothly incident, identify the endpoint traffic that evidences Monero cryptocurrency generation/mining and compute for how many seconds that endpoint generates Monero cryptocurrency, rounded to the nearest second.

### 14:30:57 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Cisco NVM flow feed confirmed at source=cisconvmflowdata, sourcetype=syslog. Fields confirmed: sa, da, dh, dp, fst, fet, fss, fes, liuidp, pn, ppn, etc. Mining-related traffic candidate is endpoint 192.168.105.214 (user BruceGist) connecting to pool.adizio.com and pool.admedo.com over 443. I did not
_full: reports/s1_round_1.md_

### 14:31:02 - SH -> s1   [COMMAND]
**continue** — This round correctly worked the Cisco NVM flow feed and surfaced a credible mining candidate, which is necessary progress. The case still lacks the exact first/last mining interval and computed duration, so the next round must finish that measurement rather than broaden scope.
**New scope:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['sa', 'da', 'dh', 'dp', 'fst', 'fet', 'fss', 'fes', 'liuidp', 'pn', 'ppn']

Establish the exact mining duration for the identified endpoint 192.168.105.214 associated with BruceGist by using Cisco NVM flow records in source cisconvmflowdata. First confirm which destination hostname(s) in the identified pool traffic belong to the same mining activity, then determine the earliest and latest relevant NVM timestamps for that activity and compute the total number of seconds, rounded to the nearest second.

### 14:31:27 - s1 -> SH   [REPORT - round 2 - FOUND]
> Confirmed mining activity for endpoint 192.168.105.214 / BruceGist in Cisco NVM flow records. Relevant pool destinations were pool.adizio.com and pool.admedo.com. Earliest relevant NVM timestamp was fss=1534770925 (Mon Aug 20 13:15:25 2018) and latest was fes=1534771012 (Mon Aug 20 13:16:52 2018). D
_full: reports/s1_round_2.md_

### 14:31:31 - runner   [NOTE]
TURN REJECTED:
- ANSWER: all three grades required (PASS/WEAK/FAIL)

### 14:31:34 - SH -> s1   [ANSWER]
**87** (count) from s1

Senior s1 established mining-related Cisco NVM flow activity for 192.168.105.214 / BruceGist to pool.adizio.com and pool.admedo.com, then computed first_seen=1534770925 and last_seen=1534771012 across that activity, yielding duration_seconds=87 in the report.

### 14:31:34 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

