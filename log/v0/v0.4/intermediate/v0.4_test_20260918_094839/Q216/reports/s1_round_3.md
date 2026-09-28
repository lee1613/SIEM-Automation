# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count values(dh) as hostname values(dp) as ports values(pn) as procs values(sa) as srcs by da | sort -count
### What it means

