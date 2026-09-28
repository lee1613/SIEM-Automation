# s1 - Q218 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=9_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail | fields userIdentity.accessKeyId, userIdentity.type, userName, eventSource, eventName, errorCode, errorMessage
**Insight:** partial
**Candidate:** AKIAJOGCDXJ5NW5PXUPA   **Confidence:** 60

## Prior rounds
- R1: aws:cloudtrail confirmed; key field is userIdentity.accessKeyId. Strict iam.amazonaws.com scope: 3 erroring keys tied at 1 distinct errorCode. Broad IAMUser scope: ASIAZB6TMXZ7FWTIS4NJ led with 6 distinct errorCodes (all S3 NoSuch*). resources{}.type=AWS::IAM::Role: 332 events, all AWSService.

## This round
### What I ran
- `eventSource=iam.amazonaws.com | stats by accessKeyId, userName` → 6 keys / 118 events, all IAMUser; 3 with errors.
- `eventSource IN ("sts.amazonaws.com","signin.amazonaws.com") errorCode!="success"` → 0 events.
- `errorCode!="success" | stats dc(errorCode) by key, type` (all identities) → two AssumedRole config-role keys also at 6 distinct; IAMUser leader FWTIS4NJ at 6.
- Key profiles → FWTIS4NJ=bstoll, LL6JBJQA=web_admin, AKIAIGKL572SFDPOKLHA=splunk_access (all IAMUser).
- `eventSource=iam.amazonaws.com errorCode!="success" | stats dc(errorMessage) by key` → AKIAJOGCDXJ5NW5PXUPA=5 distinct messages; AKIAIGKL572SFDPOKLHA=1; ASIAZB6TMXZ7MJUJJK6X=1.
- Full profile of the 3 erroring IAM keys → web_admin: 5 distinct denied ops (CreateAccessKey, CreateUser, DeleteAccessKey, GetUser, ListAccessKeys), 3 source IPs, ElasticWolf+boto3; others: 1 op each (GetAccountPasswordPolicy).
- `userIdentity.accessKeyId=AKIAJOGCDXJ5NW5PXUPA` → 9 events, IAMUser, arn:aws:iam::622676721278:user/web_admin.
- `resources{}.type="AWS::IAM::Role"` → 332 events, all AWSService, no access key.

### What it means
Reading (1), IAM service calls only: under distinct errorCode the three erroring keys tie at 1 — no unique winner. Under distinct errors as recorded (errorMessage / distinct denied operations), AKIAJOGCDXJ5NW5PXUPA wins uniquely with 5 vs 1 vs 1. Reading (2), IAM-governed access via non-IAM services: empty — STS/signin have zero errors, IAM-Role resources carry no key, S3/EC2 errors carry no IAM semantics. So reading (2) supports nothing, and reading (1) yields a unique answer when "distinct errors" is measured as the distinct error messages/operations generated. The verbatim question says "most distinct errors", not "distinct errorCode values", and only web_admin's records positively show the act named: five distinct AccessDenied messages, each naming an IAM user resource (arn:aws:iam::622676721278:user/my_db_user, user web_admin) — attacker persistence attempts from 3 IPs. The broad-scope leader's records (S3 GetBucket* NoSuch* responses, a profile shared with two AssumedRole config-role keys) show routine config enumeration, not IAM resource access. SH's "distinct rather than total" hint also fits the strict scope: web_admin has fewer IAM error events (6) than splunk_access (9) but more distinct errors (5 vs 1). Submitted AKIAJOGCDXJ5NW5PXUPA.

## Ruled out
- ASIAZB6TMXZ7FWTIS4NJ — 6 distinct errorCodes but all S3 bucket-config lookups, not IAM resources; same profile as two AssumedRole config-role keys (add-on enumeration artifact).
- AKIAIGKL572SFDPOKLHA — most IAM-service error events (9) but 1 distinct error.
- ASIAZB6TMXZ7MJUJJK6X — 2 IAM errors, 1 distinct.
- resources{}.type=AWS::IAM::Role as scope — 332 events, all AWSService, no access key.
- STS/signin as IAM-role access — zero error events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: ""Attempting to access IAM resources" surfaces in aws:cloudtrail four ways, all n"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The winning IAM user access key is AKIAJOGCDXJ5NW5PXUPA (web_admin), which produ"
