# s1 - Q204 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Scope:** sourcetype=aws:cloudtrail | fields: _raw (requestParameters.bucketName, AccessControlList), eventName, userName, eventID
**Insight:** FOUND
**Candidate:** frothlywebcode   **Confidence:** 98

## Prior rounds
- (Round 1) Read event ab45689d-69cd-41e7-8705-5350402cf7ac raw: bstoll PutBucketAcl 2018-08-20T13:01:46Z, requestParameters.bucketName="frothlywebcode", AllUsers READ+WRITE grants; feed-wide AllUsers sweep found only this event; second PutBucketAcl (9a33d8df) had no AllUsers grant.

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName -> 15 rows: all Get*/List* read-only except PutBucketAcl (count=2). No PutBucketPolicy or any other mutating S3 API exists in the feed.
- index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl | rex "\"bucketName\":\s*\"(?<bucket_name>[^\"]+)" | stats count by userName, bucket_name, eventID -> 2 rows, both userName=bstoll, both bucket_name=frothlywebcode (ab45689d and 9a33d8df).
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com (public-read OR public-read-write OR AuthenticatedUsers) | ... -> 0 results.

### What it means
Both premises are now settled from query output. Coverage (p1): the bucket made publicly accessible is named inside the public-enabling event itself — requestParameters.bucketName="frothlywebcode" on ab45689d, sitting beside the AllUsers READ/WRITE grants — and the feed-wide AllUsers sweep returns exactly that one event, with no other mutating S3 API and no canned public-ACL string anywhere, so no rival public-enabling vector exists. Selection (p2): the enabling event names frothlywebcode, and the only other PutBucketAcl in the feed (the later non-enabling 9a33d8df) names the same bucket, not a different one. The exact bucket name is unchanged: frothlywebcode. Value is submit-ready.

## Ruled out
- Any other bucket via any other S3 control-plane call - the complete S3 API inventory in aws:cloudtrail contains no mutating call except PutBucketAcl (no PutBucketPolicy, no PutBucketCors/Website/Encryption).
- Any other user - both PutBucketAcl events in the feed are by bstoll; no other user issued a PutBucketAcl.
- Canned public ACLs (public-read, public-read-write, AuthenticatedUsers) - 0 matching S3 events.
- 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 - read in full round 1; no AllUsers grant, not public-enabling; names the same bucket anyway.