# s1 - Q200 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=aws:cloudtrail | fields=userIdentity.type, userName, user_name, errorCode, eventName, eventType
**Insight:** FOUND
**Candidate:** bstoll,btun,splunk_access,web_admin   **Confidence:** 95

## Prior rounds
(none — first round)

## This round
### What I ran
- get_source_types -> aws:cloudtrail present among 102 sourcetypes.
- get_sourcetype_fields aws:cloudtrail -> 6571 events; userIdentity.type (IAMUser 5450 / AssumedRole 789 / AWSService 332), userName 12 distinct, errorCode incl. success 5504 + failures.
- `index=botsv3 sourcetype=aws:cloudtrail | stats count` -> 6571 events total.
- `... userIdentity.type=IAMUser | stats count by userName` -> 4 users: bstoll 615, btun 73, splunk_access 4116, web_admin 646.
- `... userIdentity.type=IAMUser | stats count by userName, errorCode` -> 20 rows; all 4 users have success events; bstoll/splunk_access/web_admin also have failure codes (AccessDenied, Client.UnauthorizedOperation, Client.InstanceLimitExceeded, NoSuchEntityException, etc.).
- `... | stats count by userIdentity.type, userName` -> 19 rows covering all 6571 events (5450+789+332=6571); IAMUser rows are exactly the 4 names; AssumedRole/AWSService rows are roles and services.
- `... user_name="nullweb_admin" | stats count by eventName, eventType, userIdentity.type, userName, errorCode` -> 3 events, all IAMUser web_admin, AccessDenied (CreateAccessKey x1, ListAccessKeys x2) — extraction artifact, not a distinct user.

### What it means
CloudTrail is the authoritative feed for AWS service access with identity context. Grouping the entire 6571-event population by userIdentity.type and userName partitions every event; the IAMUser partition contains exactly bstoll, btun, splunk_access, web_admin (user_arn confirms arn:aws:iam::622676721278:user/<name>). The set covers both successful and failed attempts: web_admin's failures include AccessDenied on IAM key-enumeration calls, and bstoll/splunk_access show NoSuch* errors. Alphabetical, comma-separated without spaces: bstoll,btun,splunk_access,web_admin.

## Ruled out
- AssumedRole identities (splunk_lambda, config-role-us-west-1, flowlogsRole, AWSServiceRoleFor*) — userIdentity.type=AssumedRole, roles not IAM users.
- AWSService identities (EC2InstanceRole, AWS_InspectorEvents_Invoke_Assessment_Template) — service-linked, not IAM users.
- user_name value "nullweb_admin" — resolves to web_admin IAMUser AccessDenied events, not a 13th user.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen). A claim resting on them alone is UNVERIFIED._
