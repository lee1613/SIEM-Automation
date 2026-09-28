# s1 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcestype="o365:management:activity" "taedong" | stats count
- index=botsv3 sourcetype="o365:management:activity" "taedong" | stats count
- index=botsv3 sourcetype="aws:cloudtrail" "taedular" OR "taedong" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" | stats count by http_method | sort -count
### What it means

