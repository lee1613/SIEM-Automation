# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=3_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa, da, dh, dp, fst, fet, fss, fes, liuidp, pn, ppn
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 41

## Prior rounds
- Confirmed Cisco NVM flow data exists as source=cisconvmflowdata under sourcetype=syslog in index=botsv3.
- Confirmed key timing fields are present: fst/fet and fss/fes, plus endpoint/user fields sa and liuidp.
- Sampled flow structure and saw destination hostnames in dh, including pool-like domains.
- Identified candidate mining endpoint traffic from 192.168.105.214 / BruceGist to pool.adizio.com and pool.admedo.com.

## This round
### What I ran
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata (dh=pool.adizio.com OR dh=pool.admedo.com OR dh=pool*) | stats count by sa liuidp dh | sort -count | head 20` -> 2 rows returned: 192.168.105.214/BruceGist to pool.adizio.com (2) and pool.admedo.com (2).
### What it means
The Cisco NVM feed does show pool-related traffic consistent with mining activity, but I did not get to the fss/fes interval aggregation needed to compute the number of seconds. The evidence is credible for a mining candidate, but not enough to verify the exact duration requested.

## Ruled out
- Generic Monero string search in Cisco NVM sample events - no direct monero token surfaced.
- Leading-wildcard pool search - rejected by SPL rules, so I switched to exact pool hostnames.

## Open questions for SH
- If the duration must be exact, this scope needs another round to aggregate the candidate host's first/last NVM timestamps from cisconvmflowdata.

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
