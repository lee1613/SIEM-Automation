# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=5_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata | fields sa, da, dh, fss, fes, pn, dp, ph, ppn
**Insight:** FOUND
**Candidate:** 1667   **Confidence:** 88

## Prior rounds
R1: Found the 6 Coinhive flows in cisconvmflowdata, all from BSTOLL-L (192.168.247.131), chrome.exe:443; computed span 1534772253→1534773920 = 1667 s; coverage of BSTOLL-L's full destination profile only partially read (50 of 623 rows).

## This round
### What I ran
- (liuida=BSTOLL-L OR paa=BSTOLL-L) -> dc(sa)=1: BSTOLL-L is only ever 192.168.247.131 (765 events).
- sa=192.168.247.131 fss<=1534773920 fes>=1534772253 -> 176 (dh,da) groups overlapping the mining window; the 50 read are DNS/Splunk/AWS/Microsoft/Google traffic, no mining-looking destination.
- Whole-feed keyword sweep (monero OR xmr OR stratum OR cryptonight OR miner OR mining OR pool) -> 2 events only: pool.adizio.com / pool.admedo.com from 192.168.105.214 (MicrosoftEdgeCP.exe) — not BSTOLL-L, not mining.
- stream:dns coinhive -> 6 queries, all from 192.168.247.131: coinhive.com (104.20.209.59, 104.20.208.59), ws019 (37.187.167.47), ws001/ws005/ws011/ws014 — exactly the six hostnames in the flow records; every IP inside the ranges swept in R1.
- Raw NVM records -> all six flows share one chrome.exe process hash, parent explorer.exe, user AzureAD\BudStoll, dp=443: a single mining session.
- Final SPL: `... sa=192.168.247.131 coinhive | sort fss | streamstats current=f window=0 max(fes) as prev_max_end | eval gap_seconds=fss-prev_max_end | stats count as flows values(gap_seconds) as gaps_after_prev min(fss) as first_start max(fes) as last_end sum(eval(fes-fss)) as sum_flow_durations | eval span_seconds=last_end-first_start` -> flows=6, gaps=[-108,-123,-60,-91,-94], first_start=1534772253, last_end=1534773920, sum_flow_durations=1758, span_seconds=1667.

### What it means
Coverage is verified: the complete Monero-generating set for BSTOLL-L in this feed is exactly the six Coinhive chrome.exe:443 flows — no mining flow lacks the coinhive hostname (keyword sweep), no Coinhive IP sits outside the ranges swept (DNS cross-check), and BSTOLL-L has no second source IP. All five consecutive gaps are negative, so every flow starts before the previous ones end: the union of active intervals is one continuous stretch, and the endpoint was generating Monero traffic for every second of it. Duration = 1534773920 - 1534772253 = 1667 s, computed in SPL. Unchanged from R1; the candidate is confirmed.

## Ruled out
- 1758 (sum of per-flow durations) - flows overlap (negative gaps); adding counts the same moments twice.
- 1603 (ws019 flow alone) - all six flows are one mining session; question asks the endpoint's total generating time.
- Mining flows outside the Coinhive set - whole-feed keyword sweep returned only non-BSTOLL-L ad-pool domains; DNS shows the complete Coinhive IP set is inside the ranges already swept.
- Other source IPs for BSTOLL-L - dc(sa)=1.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 fss<=1534773920 …` (50 of 176 rows seen). A claim resting on them alone is UNVERIFIED._
