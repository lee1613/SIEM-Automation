# s1 - Q203 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=2_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail | fields=userName, eventName, eventSource, eventID, eventTime, requestParameters
**Insight:** FOUND | **Candidate:** ab45689d-69cd-41e7-8705-5350402cf7ac | **Confidence:** 95

## Prior rounds
- Round 1: established the full chain — bstoll (Bud) made the only S3 write API calls in the feed (2x PutBucketAcl); the 13:01:46Z call grants AllUsers READ+WRITE on frothlywebcode; feed-wide AllUsers sweep returned exactly 1 event; no PutBucketPolicy path exists. Filed ab45689d-69cd-41e7-8705-5350402cf7ac as the enabling eventID.

## This round
### What I ran
- eventName=PutBucketAcl | eval allusers_count=mvcount(split(_raw,"AllUsers"))-1 | rex ... | stats values(allusers_permission) by eventID, eventTime, userName, allusers_count -> 2 of 2 rows: 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 (13:57:54Z, allusers_count=0) and ab45689d-69cd-41e7-8705-5350402cf7ac (13:01:46Z, allusers_count=2, permissions READ and WRITE).
- eventSource=s3.amazonaws.com (eventName=Put* OR eventName=Create* OR eventName=Delete*) | stats count by eventName, userName -> 1 row: PutBucketAcl, bstoll, count=2.

### What it means
FOUND: premise p2 is now verified by query output. The side-by-side shows the public/non-public distinction directly: only ab45689d-69cd-41e7-8705-5350402cf7ac (2018-08-20T13:01:46Z) contains AllUsers grants — public READ and WRITE on frothlywebcode — while the later 9a33d8df event contains zero AllUsers references. The feed-wide write-API sweep proves the only S3 write API in the entire CloudTrail feed is bstoll's two PutBucketAcl calls: no PutBucketPolicy, PutBucketCors, CreateBucket, or DeleteBucketPolicy path to public access exists. The enabling eventID is unchanged: ab45689d-69cd-41e7-8705-5350402cf7ac.

## Ruled out
- PutBucketAcl 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 (13:57:54Z) - allusers_count=0; no public grant, did not enable public access.
- PutBucketPolicy / PutBucketCors / CreateBucket / DeleteBucketPolicy - 0 events feed-wide (write-API sweep returned only PutBucketAcl).
- Other CloudTrail users - feed-wide AllUsers sweep (round 1) returned only bstoll's event.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:cloudtrail'] sources=[] fields=['userName', 'eventName', 'eventSource', 'requestParameters', 'eventID', 'errorCode', 'userIdentity.type']
- Rounds worked: 2/3  (iterations: 14, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail "public" | stats count by eventName, userName, eventID
- index=botsv3 sourcetype=aws:cloudtrail AllUsers | stats count by eventName, userName, eventID, eventTime
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl | eval allusers_count=mvcount(split(_raw,"AllUsers"))-1 | rex field=_raw max_match=0 "AllUsers.*?Permission.*?(?<allusers_permission>[A-Z_]+)" | stats values(allusers_permission) as allusers_permissions by eventID, eventTime, userName, allusers_count
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl | stats count by userName, eventID, eventTime, errorCode
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com (eventName=Put* OR eventName=Create* OR eventName=Delete*) | stats count by eventName, userName
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com (eventName=PutBucketPolicy OR eventName=PutBucketCors OR eventName=CreateBucket OR eventName=DeleteBucketPolicy) | stats count by userName, eventName, eventID, eventTime
- index=botsv3 sourcetype=aws:cloudtrail userName=bstoll eventSource=s3.amazonaws.com eventName=PutBucketAcl | stats count by eventID, eventTime, awsRegion, errorCode, requestParameters
- index=botsv3 sourcetype=aws:cloudtrail userName=bstoll eventSource=s3.amazonaws.com | stats count by eventName, errorCode | sort -count
- index=botsv3 sourcetype=aws:cloudtrail | stats count by userName
