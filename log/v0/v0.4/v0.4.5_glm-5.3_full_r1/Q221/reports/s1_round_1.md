# s1 - Q221 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** sourcetype=aws:cloudtrail | fields: eventName, errorCode, errorMessage, requestParameters, userIdentity.accessKeyId, userName
**Insight:** FOUND
**Candidate:** web_admin   **Confidence:** 70

## Prior rounds
- None — this is round 1.

## This round
### What I ran
- `index=botsv3 sourcetype=aws:cloudtrail AKIAJOGCDXJ5NW5PXUPA | stats count by eventName, errorCode, eventSource` -> 9 events: CreateAccessKey, CreateUser, DeleteAccessKey, GetUser, ListAccessKeys (x2) all AccessDenied on iam.amazonaws.com; GetCallerIdentity/GetSessionToken success on sts; DescribeAccountAttributes Client.UnauthorizedOperation on ec2; UpdateAccessKey success on iam.
- `get_raw_events keyword=CreateAccessKey` -> exactly 1 event: 2018-08-20T09:16:12Z, sourceIPAddress 35.153.154.221, userAgent Boto3/1.7.44, accessKeyId AKIAJOGCDXJ5NW5PXUPA (IAMUser web_admin), errorCode AccessDenied, requestParameters null, errorMessage "...not authorized to perform: iam:CreateAccessKey on resource: user nullweb_admin".
- `... AKIAJOGCDXJ5NW5PXUPA errorCode=AccessDenied | stats count by eventName, errorMessage` -> 5 denied events; CreateAccessKey/DeleteAccessKey/ListAccessKeys all name "user nullweb_admin"; CreateUser names arn:aws:iam::622676721278:user/my_db_user; GetUser names "user web_admin".
- `index=botsv3 sourcetype=aws:cloudtrail eventName=CreateAccessKey | stats count by errorCode, errorMessage, userName` -> 1 event dataset-wide: the denied web_admin event. No rivals.
- `get_raw_events keyword=UpdateAccessKey` and `keyword=DeleteAccessKey` -> UpdateAccessKey is defender bstoll (signin.amazonaws.com) setting the leaked key Inactive at 09:36:12Z; DeleteAccessKey is the same 09:16:12Z adversary burst.

### What it means
FOUND. The only CreateAccessKey event in aws:cloudtrail is the unauthorized attempt: the leaked key AKIAJOGCDXJ5NW5PXUPA (IAM user web_admin), used from 35.153.154.221 via Boto3 at 2018-08-20T09:16:12Z, was denied iam:CreateAccessKey with the errorMessage naming the target resource "user nullweb_admin". The "null" prefix is an artifact of requestParameters being null — it appears identically in the sibling ListAccessKeys and DeleteAccessKey denials for the same user, whereas the GetUser denial (parameters logged) renders cleanly as "user web_admin". The resource's name is therefore web_admin, consistent with userIdentity.userName and the account's user inventory (no user "nullweb_admin" exists).

## Ruled out
- CreateUser event (resource arn:aws:iam::622676721278:user/my_db_user) — creates a user, not a key; the question names key creation (CreateAccessKey).
- UpdateAccessKey success event — defender bstoll deactivating the leaked key at 09:36Z, not adversary activity.
- Any other CreateAccessKey candidates — eventName field search and raw-text keyword search both return exactly 1 event dataset-wide.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
