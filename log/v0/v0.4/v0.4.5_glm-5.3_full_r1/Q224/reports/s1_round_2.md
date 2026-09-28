# s1 - Q224 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=8_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval parts=split(qname,".") | where mvcount(parts)>=3 | eval third=mvindex(parts,-3) | stats count by third | eval l=len(third) | stats count as distinct_labels, avg(l) as avg_len | eval avg_len=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval parts=split(qname,".") | where mvcount(parts)==3 | eval third=mvindex(parts,0) | stats count by third | eval l=len(third) | stats count as distinct_labels, avg(l) as avg_len | eval avg_len=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval parts=split(qname,".") | eval has_upper=if(match(qname,"[A-Z]"),"yes","no") | stats count as events, dc(qname) as distinct_qnames by has_upper
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval parts=split(qname,".") | eval thirdA=if(mvcount(parts)>=3, mvindex(parts,-3), null()) | eval thirdB=if(mvcount(parts)==3, mvindex(parts,0), null()) | stats count by thirdA | eval l=len(thirdA) | stats count as nA, avg(l) as avgA | eval avgA=round(avgA,4)
### What it means
Interpretation A: 100,393 distinct labels, avg 8.0994 → 8.10. Now interpretation B at higher precision.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=…` (50 of 10000 rows seen). A claim resting on them alone is UNVERIFIED._
