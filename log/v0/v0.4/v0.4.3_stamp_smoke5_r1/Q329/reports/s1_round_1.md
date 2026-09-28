# s1 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=o365:management:activity "Taedonggang" | stats count by Operation, UserId, Site_Url | head 20
- index=botsv3 "Taedonggang" | stats count by sourcetype, source | head 30
- index=botsv3 sourcetype=o365:management:activity "taedonggang" | stats count by Operation, UserId, Site_Url | head 20
### What it means
Intention: Search for Taedonggang in aws:cloudtrail, which carries S3 PutObject upload events and user identities.
