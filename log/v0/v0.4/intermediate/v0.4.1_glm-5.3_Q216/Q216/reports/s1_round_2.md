# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=11_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | stats count as flows sum(eval(fes-fss)) as total_monero_generation_seconds values(fss) as fss values(fes) as fes values(fst) as fst values(fet) as fet values(ibc) as bytes_in values(obc) as bytes_out
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 dp=443 | stats count as flows avg(eval(fes-fss)) as avg_dur_s avg(ibc) as avg_in avg(obc) as avg_out min(fss) as first_fss max(fes) as last_fes | eval span_s=last_fes-first_fss
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | eval dur=fes-fss | where dur>60 | stats count values(pn) values(ph) sum(dur) as total_dur values(fst) as fst values(fet) as fet by da dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | eval dur=fes-fss | where ibc>1000000 | stats count values(pn) values(dp) sum(ibc) as inb sum(obc) as outb sum(dur) as total_dur by da
### What it means

