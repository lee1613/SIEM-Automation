# s2 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,dh,pn,liuid,fss,fes
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 85

## Prior rounds
- No prior rounds of mine. Retired senior verified p1 (.186 powershell destination coverage) and p3 (45.77.53.176:443 beacons are non-countable C2) but left selection premise p2 unsettled; this round settles it from explicit rival rows.

## This round
### What I ran
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count min(fss) as flow_start_epoch max(fes) as flow_end_epoch values(pn) as process values(liuid) as user by sa da` -> 1 event: 192.168.70.186->45.77.53.176, powershell.exe, FyodorMalteskesko, 1534762025->1534762137.
- `| stats count dc(sa) as endpoints by dp` -> dp=3333 count=1, endpoints=1; other non-standard ports: 58868, 9997, 50414, 8080, 4287, 22790, 3306, 52672, 5355, 53567, 56756, 65490.
- dh keyword search (coinhive/monero/pool/xmr/miner/cryptonight) by sa -> 9 events: .247.131 coinhive.com + ws001/005/011/014/019.coinhive.com (chrome.exe, 443, BudStoll); .105.214 pool.adizio.com/pool.admedo.com (MicrosoftEdgeCP.exe).
- `sa=192.168.24.128` profile by da -> powershell.exe->45.77.53.176:443 only (1015 flows); no 3333.
- `(dp=3333 OR dh="*coinhive*" OR pn=powershell.exe) | eval duration=fes-fss | stats count sum(duration) as total_seconds ... by sa da dp pn` -> 13 rows, all read: .186:3333 = 112s; .186:443 powershell = 3814 flows/3452s; .247.131 coinhive 443 = 1603/124/13/12/4s; .24.128 = 1266s (443) + 147/101s (80); .8.103 internal 8080/80 = 108/101s.

### What it means
FOUND. The sole flow on the canonical Monero pool port 3333 in the entire feed is 192.168.70.186->45.77.53.176:3333 by powershell.exe (the implant) under AzureAD\FyodorMalteskesko — the endpoint's act of generating Monero. Its duration, computed in SPL (eval duration=fes-fss, summed over that one flow), is 112 seconds. Every rival fails the act: .247.131's coinhive rows are browser cryptojacking over 443 HTTPS websockets (chrome.exe), six overlapping flows with no single duration; .24.128's same-destination powershell flows are 443-only beacons (p3); .105.214's "pools" are ad-tech. p2 verified from these rows.

## Ruled out
- 192.168.247.131 (coinhive) - chrome.exe:443 browser cryptojacking; 6 overlapping flows (1603/124/13/12/4s), no single duration, not a pool flow.
- 192.168.24.128 - powershell->45.77.53.176 on 443 only (1015 flows, 1266s); no 3333; p3 excludes beacons.
- 192.168.105.214 - pool.adizio.com/pool.admedo.com are advertising pools.
- 192.168.8.103 - powershell to internal 192.168.9.30:8080/80, not a pool.
- .186's 45.77.53.176:443 set (3814 flows, 3452s) - p3-verified non-countable C2.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count dc(sa) as endpoints b…` (50 of 1573 rows seen); `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 | stats count val…` (50 of 594 rows seen). A claim resting on them alone is UNVERIFIED._
