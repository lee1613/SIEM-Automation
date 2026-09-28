# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn,sa,da,dp,dh,fss,fes,liuid
**Insight:** FOUND
**Candidate:** 1758   **Confidence:** 55

## Prior rounds
- R1: Feed mapped (78,459 events; fss/fes epochs, pn, 5-tuple, liuid); no literal "monero"; all 60 pn names enumerated, no miner; Minesweeper.exe = real Xbox game; dp census: 3333 x1, 8080 x26, 4287 x17, no 4444/5555/7777.
- R2: dp=3333 = one 112s powershell.exe flow 192.168.70.186→45.77.53.176 (dh=Unknown); same endpoint has 3,814 flows to that IP on 443 (C2-like). Coinhive flows found from 192.168.247.131 (BSTOLL-L, BudStoll, chrome.exe). hdoor/iexepler/8080 = internal scanning of 192.168.9.x; dp=4287 = CrashPlan.

## This round
### What I ran
- `dp=3333 | stats ... by _time` -> 1 event: sa=192.168.70.186, da=45.77.53.176, dh=Unknown, pn=powershell.exe, liuid=FyodorMalteskesko, fss=1534762025, fes=1534762137 (112s).
- `da=45.77.53.176 | stats ... by sa,pn,dp,liuid` -> 4 rows: two powershell.exe endpoints on 443 (3,814 + 1,015 flows) plus one incidental Edge flow; only 192.168.70.186 has the 3333 flow.
- `(pool OR xmr OR stratum OR minergate OR nanopool OR supportxmr OR coinhive OR mining)` -> 8 rows; 6 Coinhive flows, all sa=192.168.247.131, chrome.exe, BudStoll, dp=443.
- `(da=37.187.* OR da=217.182.* OR da=104.20.208.59) | eval dur=fes-fss | stats sum(dur) ... by da,dh,sa` -> coinhive.com 124s, ws001 4s, ws005 12s, ws011 2s, ws014 13s, ws019 1603s.
- web_lookup "45.77.53.176 Monero mining pool stratum 3333" -> no results.
- `(pn=iexepler.exe OR pn=hdoor.exe OR dp=8080 OR dp=4287) | eval dur=fes-fss | stats ...` -> hdoor.exe = internal scans (192.168.8.103→192.168.9.x, ports 21/22/3306/8080); dp=4287 = CrashPlanService.exe to crashplan/code42.

### What it means
The endpoint generating Monero is BSTOLL-L (192.168.247.131, BudStoll, chrome.exe): its traffic to Coinhive — a Monero mining service — is the only traffic in this feed positively classified as Monero generation. Six flows, durations 124+4+12+2+13+1603 = 1758 seconds. Every per-flow duration came from SPL `eval dur=fes-fss`; the final single aggregation could not be run (tools withdrawn at cap).

## Ruled out
- dp=3333 flow (192.168.70.186, powershell.exe, 112s) — destination 45.77.53.176 unclassified (dh=Unknown), web_lookup found no pool evidence, single flow, and 3,814 C2-like 443 flows to the same IP.
- hdoor.exe / iexepler.exe / dp=8080 — internal lateral movement/scanning (192.168.8.103→192.168.9.x), not cryptocurrency.
- dp=4287 — CrashPlan/code42 backup traffic.
- Minesweeper.exe, dp=9997 — real game / Splunk management (R1).

## Caveats
The six Coinhive flows overlap in time (coinhive.com's 124s window contains the four short ws* flows and overlaps ws019 by 60s): the wall-clock span is 1667s, the ws*-only total is 1634s. I submitted the sum (1758) as total generation time; open question filed for SH to settle sum vs span.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The endpoint generating Monero is 192.168.247.131 (BSTOLL-L, BudStoll, chrome.ex"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The measured duration is the total of the six Coinhive flow durations (fes-fss):"

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count, dc(sa) as endpoints,…` (50 of 3602 rows seen). A claim resting on them alone is UNVERIFIED._
