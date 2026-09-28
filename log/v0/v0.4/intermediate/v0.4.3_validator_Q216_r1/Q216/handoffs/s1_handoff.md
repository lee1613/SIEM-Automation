# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=5_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 source=cisconvmflowdata sourcetype=syslog (dh="*pool*" OR dh="*mine*" OR dh="*monero*" OR dh="*xmr*" OR dh="*stratum*" OR dh="*coin*" OR dh="*hash*") | stats count values(dh) values(da) values(dp) values(pn) values(sa)
- index=botsv3 source=cisconvmflowdata sourcetype=syslog dh="*coinhive*" | stats count values(sa) values(liuid) values(liuida) values(pn) values(ppn) values(dp) values(da) min(fss) max(fes) by dh
- index=botsv3 source=cisconvmflowdata sourcetype=syslog liuida=BSTOLL-L | stats count values(sa) values(liuid) values(pn) values(dp)
- index=botsv3 source=cisconvmflowdata sourcetype=syslog (da=104.20.208.59 OR da=217.182.164.14 OR da=37.187.165.41 OR da=37.187.166.108 OR da=37.187.167.21 OR da=37.187.167.47) | stats count values(dh) values(sa) values(pn) values(dp) values(liuid) min(fss) max(fes) by da
### What it means
Intention: The CoinHive server IPs each carry exactly one flow, all from 192.168.247.131 (BudStoll, chrome.exe). Now I need to: (B1) compute per-flow durations in SPL, (B2) compute the long-lived mining session duration, (C) sweep for other mining-service domains my first keyword set missed, (F) find all long-lived flows anywhere in the feed (mining sessions are long-lived) regardless of domain/port labels. All independent — batching.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 source=cisconvmflowdata sourcetype=syslog | stats count values(dh) values(dp)…` (25 of 2735 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Retire s1 because it moved from a concrete candidate in the named feed to an unverified CoinHive lead and did not settle whether the question's Monero-generation act is the prior dp=3333 stratum flow or something else. A fresh senior should independently test the act and selection in the same feed without re-walking the keyword/domain pivot.
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'src_port', 'dest_port', 'bytes', 'packets', 'protocol', '_time', 'duration', 'app', 'url', 'dns', 'user', 'host']
- Rounds worked: 2/8  (iterations: 18, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 45.77.53.176 | stats count values(sourcetype) values(source) values(host) by sourcetype
- index=botsv3 source=cisconvmflowdata sourcetype=syslog (da=104.20.208.59 OR da=217.182.164.14 OR da=37.187.165.41 OR da=37.187.166.108 OR da=37.187.167.21 OR da=37.187.167.47) | stats count values(dh) values(sa) values(pn) values(dp) values(liuid) min(fss) max(fes) by da
- index=botsv3 source=cisconvmflowdata sourcetype=syslog (dh="*pool*" OR dh="*mine*" OR dh="*monero*" OR dh="*xmr*" OR dh="*stratum*" OR dh="*coin*" OR dh="*hash*") | stats count values(dh) values(da) values(dp) values(pn) values(sa)
- index=botsv3 source=cisconvmflowdata sourcetype=syslog (sa=192.168.70.186 OR sa=192.168.24.128 OR sa=192.168.105.214) da=45.77.53.176 | stats count values(liuid) values(liuida) values(pa) values(dh) values(dp) by sa
- index=botsv3 source=cisconvmflowdata sourcetype=syslog da=45.77.53.176 | stats count dc(fss) min(fss) max(fes) values(dp) values(pn) values(sa) by sa
- index=botsv3 source=cisconvmflowdata sourcetype=syslog dh="*coinhive*" | stats count values(sa) values(liuid) values(liuida) values(pn) values(ppn) values(dp) values(da) min(fss) max(fes) by dh
- index=botsv3 source=cisconvmflowdata sourcetype=syslog dp=3333 | stats count values(sa) values(da) values(dh) values(pn) values(ppn) values(pa) values(fst) values(fet) values(fss) values(fes) values(ibc) values(obc) values(liuid) values(udid) by _raw
- index=botsv3 source=cisconvmflowdata sourcetype=syslog liuida=BSTOLL-L | stats count values(sa) values(liuid) values(pn) values(dp)
- index=botsv3 source=cisconvmflowdata sourcetype=syslog | rare dp limit=10
- index=botsv3 source=cisconvmflowdata sourcetype=syslog | rare pn limit=40
- index=botsv3 source=cisconvmflowdata sourcetype=syslog | stats count values(dh) values(dp) values(pn) by da | sort -count
