# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=3_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata | fields sa, da, dh, fss, fes, pn, dp, ph, ppn
**Insight:** FOUND
**Candidate:** 1667   **Confidence:** 92

## Prior rounds
R1: Found the 6 Coinhive flows in cisconvmflowdata, all from BSTOLL-L (192.168.247.131), chrome.exe:443; span 1534772253→1534773920 = 1667 s; BSTOLL-L destination profile only partially read.
R2: Verified coverage — BSTOLL-L has one source IP; whole-feed mining keyword sweep clean (only non-BSTOLL-L ad-pool domains); DNS shows the complete Coinhive IP set inside the ranges swept; all six flows one chrome.exe session; SPL computed span 1667, sum 1758, all gaps negative.

## This round
### What I ran
- `... sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds=fss-prev_max_end, flow_duration=fes-fss | stats count as flows dc(ph) as distinct_process_hashes values(pn) as process_names values(dp) as ports values(ppn) as parent_processes list(dh) as hostnames list(fss) as starts list(fes) as ends list(flow_duration) as durations list(gap_seconds) as gaps min(fss) as first_start max(fes) as last_end sum(flow_duration) as sum_flow_durations | eval span_seconds=last_end-first_start` -> 1 row: flows=6, distinct_process_hashes=1, process=chrome.exe, port=443, parent=explorer.exe; starts=[1534772253, 1534772254, 1534772269, 1534772283, 1534772286, 1534772317]; ends=[1534772377, 1534772267, 1534772273, 1534772285, 1534772298, 1534773920]; durations=[124, 13, 4, 2, 12, 1603]; gaps=[-123, -108, -94, -91, -60]; first_start=1534772253, last_end=1534773920, sum_flow_durations=1758, span_seconds=1667.

### What it means
The six flows in time order: coinhive.com 1534772253-1534772377; ws014 1534772254-1534772267; ws001 1534772269-1534772273; ws011 1534772283-1534772285; ws005 1534772286-1534772298; ws019 1534772317-1534773920. Every gap is negative: each later flow begins before the running max end of the prior active flows (1534772377), so the union of the six intervals is the single continuous interval [1534772253, 1534773920] — the endpoint was generating Monero traffic for every second of it. Duration = 1534773920 - 1534772253 = 1667 s, computed in SPL. Premise p2 settled VERIFIED with this output.

## Ruled out
- 1758 (sum of per-flow durations) - negative gaps prove overlap (e.g. 1534772317-1534772377 has both coinhive.com and ws019 live); the sum counts those moments twice.
- 1603 (ws019 flow alone) - all six flows are one session (single chrome.exe process hash, parent explorer.exe, port 443); the session began 64 s before ws019 started, and the question asks for the endpoint's total generating time.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src', 'dest', 'src_ip', 'dest_ip', 'dest_port', 'bytes', 'duration', 'starttime', 'endtime', 'hostname', 'host', 'application', 'url', 'domain']
- Rounds worked: 3/8  (iterations: 24, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata sa=192.168.247.131 (da=37.187.167.47 OR da=104.20.208.59 OR da=104.20.209.59) | stats count dc(dp) as ports min(fss) as first_start max(fes) as last_end values(pn) as processes values(dp) as dest_ports
- index=botsv3 sourcetype=stream:dns coinhive | stats count values(src_ip) as src_ips values(record_type) as record_types by dest_ip query | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (liuida=BSTOLL-L OR paa=BSTOLL-L) | stats dc(sa) as num_src_ips values(sa) as src_ips count as events
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (monero OR xmr OR stratum OR cryptonight OR miner OR mining OR pool) | stats count values(sa) as src_ips values(pn) as pn values(dp) as dp by dh da | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata coinhive | stats count dc(sa) as num_srcs values(sa) as src_ips min(fss) as first_start max(fes) as last_end by da dh | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 (da=37.187.* OR da=104.20.* OR da=217.182.*) | stats count min(fss) as fss max(fes) as fes values(dh) as dh values(pn) as pn values(dp) as dp values(ibc) as ibc values(obc) as obc by da | sort da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 (da=37.187.167.47 OR da=104.20.208.59 OR da=104.20.209.59) | stats count dc(dp) as ports min(fss) as first_start max(fes) as last_end values(pn) as processes values(dp) as dest_ports
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 (da=37.187.167.47 OR da=104.20.208.59 OR da=104.20.209.59) | stats count min(fss) as fss max(fes) as fes values(da) as da values(dh) as dh values(ibc) as ibc values(obc) as obc by _time | sort _time
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds = fss - prev_max_end | stats count as flows values(gap_seconds) as gaps_after_prev min(fss) as first_start max(fes) as last_end sum(eval(fes-fss)) as sum_flow_durations | eval span_seconds = last_end - first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds = fss - prev_max_end, flow_duration = fes - fss | stats count as flows dc(ph) as distinct_process_hashes values(pn) as process_names values(dp) as ports values(ppn) as parent_processes list(dh) as hostnames list(fss) as starts list(fes) as ends list(flow_duration) as durations list(gap_seconds) as gaps min(fss) as first_start max(fes) as last_end sum(flow_duration) as sum_flow_durations | eval span_seconds = last_end - first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds = fss - prev_max_end, flow_duration = fes - fss | stats count as flows values(dh) as hostnames list(fss) as starts list(fes) as ends list(flow_duration) as durations list(prev_max_end) as prior_max_ends list(gap_seconds) as gaps min(fss) as first_start max(fes) as last_end sum(flow_duration) as sum_flow_durations | eval span_seconds = last_end - first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds = fss - prev_max_end, flow_duration = fes - fss | table dh da fss fes flow_duration prev_max_end gap_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 fss<=1534773920 fes>=1534772253 | stats count min(fss) as fss max(fes) as fes values(pn) as pn values(dp) as dp by dh da | sort -count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 | stats count min(fss) as first_start max(fes) as last_end values(pn) as pn by dh da | sort -count
