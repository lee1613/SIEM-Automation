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


## What I'd tell my replacement
- Retired because: This senior has produced two rounds of intentions rather than evidence and has not established any feed containing Taedonggang or any upload candidate. Another round in the same pattern risks repeating broad enumeration without a foothold.
- Scope I owned: sourcetypes=['aws:s3:accesslogs', 'stream:http', 'aws:cloudtrail', 'o365:management:activity', 'ms:o365:management', 'code42:security', 'code42:api'] sources=[] fields=['user', 'src_user', 'user_name', 'object', 'key', 'uri_path', 'url', 'requestParameters.*', 'file*', 'object*', 'bucket*']
- Rounds worked: 2/8  (iterations: 15, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Taedonggang" | stats count by sourcetype, source | head 30
- index=botsv3 sourcetype=aws:cloudtrail "Taedong*" | stats count by eventName, requestParameters.bucketName, requestParameters.key, userIdentity.arn | head 30
- index=botsv3 sourcetype=aws:cloudtrail "Taedonggang" | stats count by eventName, requestParameters.bucketName, requestParameters.key, userIdentity.arn | head 30
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutObject | stats count by requestParameters.bucketName, userIdentity.arn, requestParameters.key | head 40
- index=botsv3 sourcetype=aws:s3:accesslogs "taedonggang" | stats count by operation, bucket, key | head 30
- index=botsv3 sourcetype=o365:management:activity "Taedong*" | stats count by Operation, UserId, Site_Url | head 30
- index=botsv3 sourcetype=o365:management:activity "Taedonggang" | stats count by Operation, UserId, Site_Url | head 20
- index=botsv3 sourcetype=o365:management:activity Operation="*pload*" | stats count by Operation, UserId | head 40
