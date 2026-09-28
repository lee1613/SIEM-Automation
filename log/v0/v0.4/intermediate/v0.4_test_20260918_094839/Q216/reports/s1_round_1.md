# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=12_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count min(fss) as first_start max(fes) as last_end values(dp) as ports by sa, liuid, sp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(sp) as srcports by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end values(sp) as srcports by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=443 | stats count min(fss) as first_start max(fes) as last_end values(liuid) as user values(pn) as proc
### What it means

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
