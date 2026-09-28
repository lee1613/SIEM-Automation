# s1 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudtrail "Taedong*" | stats count by eventName, requestParameters.bucketName, requestParameters.key, userIdentity.arn | head 30
- index=botsv3 sourcetype=o365:management:activity "Taedong*" | stats count by Operation, UserId, Site_Url | head 30
- index=botsv3 sourcetype=o365:management:activity Operation="*pload*" | stats count by Operation, UserId | head 40
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutObject | stats count by requestParameters.bucketName, userIdentity.arn, requestParameters.key | head 40
### What it means
Intention: List all eventNames in aws:cloudtrail to see what upload-capable operations exist and which identities appear.
