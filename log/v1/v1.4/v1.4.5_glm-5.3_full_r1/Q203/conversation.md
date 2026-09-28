# Q203 — SH <-> Senior conversation

### 12:33:44 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['aws:cloudtrail'] sources=- fields=['userName', 'eventName', 'eventSource', 'requestParameters', 'eventID', 'errorCode', 'userIdentity.type']
**Technique:** senior
**Reason:** This is an AWS control-plane question about who made an S3 bucket public and which API call did it. CloudTrail is the established Frothly feed for AWS API actions and contains actor identity, API name, request parameters, and eventID needed to name the enabling call.

In Frothly's aws:cloudtrail data, identify the API call by user Bud that changed an S3 bucket from non-public to publicly accessible, and return the exact eventID of that call. Establish both the actor selection (Bud) and the access-changing action from CloudTrail evidence, and distinguish the enabling call from later access or unrelated S3 activity.

### 12:35:47 - s1 -> SH   [REPORT - round 1 - FOUND]
> Bud = bstoll (arn arn:aws:iam::622676721278:user/bstoll), the only Bud-matching userName of 12 CloudTrail identities; btun is a separate user with no S3 ACL writes. Bucket made public: frothlywebcode, us-west-1, via AWS console (userAgent signin.amazonaws.com, invokedBy signin.amazonaws.com, sourceI
_full: reports/s1_round_1.md_

### 12:35:53 - SH -> s1   [COMMAND]
**continue** — The candidate aligns well with the question's actor, act, and unit, but the answer is blocked by the cut-off report and an unverified selection premise. The next round should settle p2 directly from report-backed output showing why this event, and not the other PutBucketAcl, enabled public access.

Provide exact result output that verifies the selection premise: show both PutBucketAcl events by bstoll with their eventID, eventTime, and the public/non-public distinction in the grant content, and show the feed-wide result that no PutBucketPolicy path exists. Then restate the exact enabling eventID literally if unchanged.

### 12:36:56 - s1 -> SH   [REPORT - round 2 - FOUND]
> Premise p2 settled this round with two new queries. (1) Side-by-side of both PutBucketAcl events: ab45689d-69cd-41e7-8705-5350402cf7ac (13:01:46Z) carries 2 AllUsers grants (READ and WRITE) on frothlywebcode; 9a33d8df-1e16-4d58-b36d-8e80ce68f8a3 (13:57:54Z) carries 0 AllUsers references — non-public
_full: reports/s1_round_2.md_

### 12:37:02 - SH -> s1   [ANSWER]
**ab45689d-69cd-41e7-8705-5350402cf7ac** (event_id) from s1

s1 showed that bstoll's two PutBucketAcl events are the only S3 write APIs in scope, and only eventID ab45689d-69cd-41e7-8705-5350402cf7ac at 2018-08-20T13:01:46Z contains AllUsers grants with READ and WRITE permissions. The later PutBucketAcl event has allusers_count=0, and the feed-wide write-API sweep returned no PutBucketPolicy or other rival public-enabling path.

**Premises it rests on:** p1, p2

### 12:37:02 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

