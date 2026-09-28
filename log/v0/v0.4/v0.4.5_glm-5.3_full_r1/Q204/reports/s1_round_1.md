# s1 - Q204 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=3_
**Scope:** sourcetype=aws:cloudtrail | fields: _raw (requestParameters.bucketName, AccessControlList), eventName, userName, eventID, eventTime
**Insight:** FOUND
**Candidate:** frothlywebcode   **Confidence:** 97

## Prior rounds
- (Round 1) No prior rounds of mine; Q203 context carried in: bstoll's PutBucketAcl eventID ab45689d-69cd-41e7-8705-5350402cf7ac enabled public access.

## This round
### What I ran
- get_raw_events sourcetype=aws:cloudtrail keyword="ab45689d-69cd-41e7-8705-5350402cf7ac" -> 1 event: PutBucketAcl, userName=bstoll, 2018-08-20T13:01:46Z, requestParameters.bucketName="frothlywebcode", grants to group URI .../groups/global/AllUsers with READ and WRITE.
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl userName=bstoll | rex bucketName | stats count by bucket_name, eventID, eventTime -> 2 rows, both frothlywebcode (ab45689d @13:01:46Z; 9a33d8df @13:57:54Z).
- get_raw_events keyword="9a33d8df-1e16-4d58-b36d-8e80ce68f8a3" -> 1 event: same bucket, but grants only bstoll FULL_CONTROL + LogDelivery — no AllUsers, not public-enabling.
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com AllUsers | rex bucketName | stats count by eventName, userName, bucket_name -> exactly 1 row: PutBucketAcl / bstoll / frothlywebcode.

### What it means
The enabling event's own CloudTrail content names the bucket: requestParameters.bucketName = "frothlywebcode", and the same event's ACL grants the AllUsers group READ and WRITE — the act of making the bucket publicly accessible. The only other PutBucketAcl by bstoll targets the same bucket but carries no public grant, so the answer is invariant across both. A feed-wide AllUsers sweep confirms no other S3 event by any user made any bucket public. Value is submit-ready.

## Ruled out
- 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 (bstoll PutBucketAcl 13:57:54Z) - read in full; ACL contains no AllUsers grant, so it is not the public-enabling call (and it names the same bucket anyway).
- Any other bucket / any other user - feed-wide search for AllUsers in s3.amazonaws.com events returned only the single bstoll/frothlywebcode event.

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"min_count": 1, "sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen). A claim resting on them alone is UNVERIFIED._
