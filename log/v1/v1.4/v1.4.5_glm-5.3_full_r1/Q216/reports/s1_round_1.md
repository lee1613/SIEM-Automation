# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** index=botsv3 sourcetype=syslog source=cisconvmflowdata | fields sa, da, dh, fss, fes, pn, dp, ibc, obc
**Insight:** FOUND
**Candidate:** 1667   **Confidence:** 78

## Prior rounds
None — round 1.

## This round
### What I ran
- get_sources sourcetype=syslog -> cisconvmflowdata exists, 78,459 events, all Aug 20 2018.
- get_sourcetype_fields -> fss/fes are epoch flow start/end seconds; sa/da/dh/pn/dp carry endpoint, destination, process, port.
- sa=192.168.247.131 da IN (37.187.167.47, 104.20.208.59, 104.20.209.59) -> 2 flows (coinhive.com, ws019.coinhive.com).
- `coinhive` over the whole feed -> 6 events, all sa=192.168.247.131 (BSTOLL-L), all chrome.exe/443.
- sa=192.168.247.131 (da=37.187.* OR 104.20.* OR 217.182.*) -> same 6 flows; no Coinhive-range flow lacking the hostname.
- BSTOLL-L destination profile (first 50 of 623 rows) -> corporate/AWS/Microsoft traffic; no other mining-looking destination in rows read.

Per-flow fss->fes: coinhive.com 104.20.208.59 1534772253-1534772377; ws014 37.187.167.21 1534772254-1534772267; ws001 217.182.164.14 1534772269-1534772273; ws011 37.187.166.108 1534772283-1534772285; ws005 37.187.165.41 1534772286-1534772298; ws019 37.187.167.47 1534772317-1534773920.

### What it means
min(fss)=1534772253, max(fes)=1534773920 -> 1667 s. The six intervals chain with no gap: the five short flows sit inside 1534772253-1534772377 and ws019 starts at 1534772317, before the coinhive.com flow ends, so the union of active intervals is the continuous span [1534772253, 1534773920] = 1667 s. Summing per-flow durations (1758) would count the same moments twice.

Final SPL: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 coinhive | stats min(fss) as first_start max(fes) as last_end | eval duration_seconds=last_end-first_start -> 1667. Tool budget closed before the closing eval ran; min/max are SPL-returned and the subtraction is shown.

## Ruled out
- 1758 (sum of the six per-flow durations) - flows overlap in time; adding double-counts the same moments.
- 1603 (ws019 flow alone) - question asks the endpoint's total generating time; all six Coinhive flows are the mining activity.
- 104.20.209.59 - zero flows (resolved, never contacted).
- Other endpoints as miners - all six Coinhive flows have sa=192.168.247.131 only.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_field_values: {"field": "da", "source": "cisconvmflowdata", "top_n": 20}` (20 of 2735 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 | stats count mi…` (50 of 623 rows seen). A claim resting on them alone is UNVERIFIED._
