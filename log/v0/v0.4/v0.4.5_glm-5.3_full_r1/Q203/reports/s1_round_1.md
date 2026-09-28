# s1 - Q203 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail | fields=userName, eventName, eventSource, eventID, eventTime, requestParameters
**Insight:** FOUND | **Candidate:** ab45689d-69cd-41e7-8705-5350402cf7ac | **Confidence:** 92

## Prior rounds
- Round 1 (this round): full chain established from feed discovery to the enabling eventID.

## This round
### What I ran
- get_sourcetype_fields aws:cloudtrail -> feed confirmed (6571 events) with userName/eventName/eventID/requestParameters.
- userName=bstoll eventSource=s3.amazonaws.com | stats count by eventName, errorCode -> 16 eventNames; only write API is PutBucketAcl (2 successes), rest are read-only Get*/List*.
- eventName=PutBucketAcl | stats count by userName, eventID, eventTime, errorCode -> exactly 2 events feed-wide, both bstoll: ab45689d-... @ 2018-08-20T13:01:46Z and 9a33d8df-... @ 13:57:54Z.
- get_raw_events PutBucketAcl -> read both raw events in full: the 13:01:46Z call grants AllUsers (http://acs.amazonaws.com/groups/global/AllUsers) READ and WRITE on bucket frothlywebcode; the 13:57:54Z call grants only bstoll FULL_CONTROL and LogDelivery (no AllUsers).
- eventSource=s3.amazonaws.com (PutBucketPolicy OR PutBucketCors OR CreateBucket OR DeleteBucketPolicy) -> 0 events feed-wide.
- sourcetype=aws:cloudtrail AllUsers | stats count by eventName, userName, eventID, eventTime -> exactly 1 event feed-wide across all users: the bstoll PutBucketAcl ab45689d-69cd-41e7-8705-5350402cf7ac.
- | stats count by userName -> 12 identities; bstoll is the only Bud-matching user.

### What it means
FOUND: Bud (bstoll) made exactly two access-changing S3 calls in the entire CloudTrail feed. Only the 13:01:46Z PutBucketAcl (eventID ab45689d-69cd-41e7-8705-5350402cf7ac) adds AllUsers grants — public READ and WRITE on frothlywebcode — so it is the call that changed the bucket from non-public to publicly accessible. The later 13:57:54Z PutBucketAcl contains no AllUsers grants (likely the revert) and is ruled out as the enabling call. No bucket-policy route exists (0 PutBucketPolicy events feed-wide), and no other user granted AllUsers anywhere in the feed.

## Ruled out
- PutBucketAcl 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 (13:57:54Z) - grant list has no AllUsers entries; did not enable public access.
- PutBucketPolicy / PutBucketCors / CreateBucket / DeleteBucketPolicy - 0 events feed-wide.
- Other CloudTrail users (btun, web_admin, splunk_access, roles) - feed-wide AllUsers sweep returned only bstoll's event.
- Canned-ACL "public-read" route - both PutBucketAcl events carry acl=[""] with explicit AccessControlPolicy grants; the AllUsers sweep is the definitive public-grant pattern and returned one event.

**Residual:** a "public" keyword sweep returned 256 rows (50 read, all config-rule polling noise by splunk_access); the unseen rows cannot change the answer because the AllUsers sweep and zero PutBucketPolicy results already cover every route to public S3 access.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen); `run_splunk_search: index=botsv3 sourcetype=aws:cloudtrail "public" | stats count by eventName, userName, even…` (50 of 256 rows seen). A claim resting on them alone is UNVERIFIED._
