# s1 - Q216 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means



## What I'd tell my replacement
- Retired because: Retiring due to anti-thrash: this senior has two consecutive rounds with coded R2 FAIL and produced no answer candidate. Handoff: stay in sourcetype=syslog, source=cisconvmflowdata; determine what Monero mining looks like in raw Cisco NVM events first, then identify the responsible endpoint and bracket earliest flow start and latest flow end for that same pattern.
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'duration', 'app', 'action', '_time']
- Rounds worked: 4/8  (iterations: 13, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | stats count by dp | sort -count
- index=botsv3 source=cisconvmflowdata | stats count by pn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports by sa, liuid, sp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports values(liuid) as users by sa, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports values(pn) as procs values(sa) as srcs values(liuid) as users
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp IN (3333,8080,58868,9997,50414,4287,22790,52672,53567,56756,65490) | stats count min(fss) as start max(fes) as end values(sa) as src values(da) as dst values(pn) as proc values(liuid) as user by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count min(fss) as first_start max(fes) as last_end values(da) as dsts values(dp) as ports values(sa) as srcs by liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(sp) as srcports by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=443 | stats count min(fss) as first_start max(fes) as last_end values(liuid) as user values(pn) as proc
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(sp) as srcports by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count values(dh) as hostname values(dp) as ports values(pn) as procs values(sa) as srcs by da | sort -count
