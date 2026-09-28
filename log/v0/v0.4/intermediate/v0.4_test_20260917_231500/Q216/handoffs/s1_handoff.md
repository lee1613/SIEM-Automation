# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means



## What I'd tell my replacement
- Retired because: This senior is stalled and cannot be continued after two consecutive R2 FAIL rounds. Handoff: remain in sourcetype=syslog, source=cisconvmflowdata; first establish the Monero-mining flow signature from raw Cisco NVM events, then identify the internal endpoint using that signature, and finally measure the observed activity window from first confirmed flow start to last confirmed flow end.
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'app', 'url', 'bytes', 'packets', '_time', 'duration']
- Rounds worked: 2/8  (iterations: 9, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata | top limit=50 dp
- index=botsv3 source=cisconvmflowdata | top limit=50 pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, values(pn) as procs by sa, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, min(fss), max(fes), values(dp), values(pn) by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count by sa, da, dp, pn, fss, fes
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler* | stats count by sa, da, dp, pn, liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler.exe | stats count by sa, da, dp, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count, sum(eval(fes-fss)) as total_secs by sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, sum(eval(fes-fss)) as total_flow_secs, dc(liuid) as users, values(liuid) as user_names
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, sum(eval(fes-fss)) as total_flow_secs, values(liuid) as users
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 pn=powershell.exe | stats count, min(fss) as first_start, max(fes) as last_end, values(da) as dest_ips, values(dp) as ports by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=50 dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=50 pn
