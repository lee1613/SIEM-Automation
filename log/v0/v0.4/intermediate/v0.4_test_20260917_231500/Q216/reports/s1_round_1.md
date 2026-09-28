# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=13_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, sum(eval(fes-fss)) as total_flow_secs, dc(liuid) as users, values(liuid) as user_names
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, sum(eval(fes-fss)) as total_flow_secs, values(liuid) as users
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count, sum(eval(fes-fss)) as total_secs by sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler* | stats count by sa, da, dp, pn, liuid
### What it means

