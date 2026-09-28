# s2 - Q221 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** sourcetype=aws:cloudtrail | keyword=AKIAJOGCDXJ5NW5PXUPA, CreateAccessKey | fields=eventName, errorMessage, errorCode, userIdentity.accessKeyId, eventTime, sourceIPAddress, userAgent
**Insight:** FOUND
**Candidate:** nullweb_admin   **Confidence:** 80

## Prior rounds
- Round 1 (this round): located the denied CreateAccessKey event and the full sibling burst; resolved the resource-name string.

## This round
### What I ran
- get_source_types / get_sources aws:cloudtrail -> single CloudTrail feed (s3://cloudtrail-622676721278/...), no separate IAM feed.
- `index=botsv3 sourcetype=aws:cloudtrail eventName=CreateAccessKey | stats count by ... requestParameters_userName ...` -> 0 rows (that field is not extracted).
- `sourcetype=aws:cloudtrail "CreateAccessKey" | stats count by eventName, eventSource, errorCode` -> 1 event: iam.amazonaws.com, AccessDenied.
- get_raw_events keyword=CreateAccessKey -> the denial: errorMessage "...iam:CreateAccessKey on resource: user nullweb_admin", eventTime 2018-08-20T09:16:12Z, src 35.153.154.221.
- `userIdentity.accessKeyId=AKIAJOGCDXJ5NW5PXUPA eventSource=iam.amazonaws.com | stats count by eventName, errorCode, _time` -> 6 denials: CreateAccessKey, CreateUser, DeleteAccessKey, ListAccessKeys x2, GetUser.
- get_raw_events keyword=AKIAJOGCDXJ5NW5PXUPA -> 10 events: the whole burst plus the later GetUser and the defender's UpdateAccessKey.

### What it means
FOUND. The CreateAccessKey denial names its target resource as "user nullweb_admin". Every same-burst sibling key-management denial (ListAccessKeys at 09:16:12Z and 09:16:18Z, DeleteAccessKey at 09:16:12Z) reads the identical string "user nullweb_admin". The only "user web_admin" reading is the GetUser denial at 09:27:07Z — a separate session 11 minutes later, from a different IP (82.102.18.111 vs 35.153.154.221) and tool (ElasticWolf vs Boto3), where GetUser with no parameters names the caller's own user; it is not the CreateAccessKey target. requestParameters is null in all burst denials, so errorMessage is the sole carrier of the name. The exact resource-name string for the CreateAccessKey attempt is nullweb_admin.

## Ruled out
- web_admin as the CreateAccessKey target — appears only as the calling identity and as the later GetUser denial's resource (different session, different IP/tool); the CreateAccessKey event and its same-burst siblings all read nullweb_admin.
- my_db_user — target of the CreateUser denial in the same burst, a different act than CreateAccessKey.
- requestParameters as a name source — null in every burst denial event.
- Separate IAM feed — aws:cloudtrail is one S3-bucket feed; no other source carries these events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
