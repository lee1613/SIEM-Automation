# s1 - Q200 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=5_
**Scope:** sourcetype=aws:cloudtrail | fields=userIdentity.type, userName, userIdentity.arn, errorCode, eventSource, eventName, eventType
**Insight:** FOUND
**Candidate:** bstoll,btun,splunk_access,web_admin   **Confidence:** 97

## Prior rounds
- R1: Found aws:cloudtrail (6571 events); IAMUser bucket = bstoll 615, btun 73, splunk_access 4116, web_admin 646; all four have success events, three have failures; AssumedRole/AWSService names are roles/services; "nullweb_admin" is a web_admin parsing artifact. Submitted FOUND.

## This round
### What I ran
- `... userIdentity.type=IAMUser | stats dc(eventSource) as services_accessed, count(eval(errorCode="success")) as successful, count(eval(errorCode!="success")) as failed by userName` -> 4 rows: bstoll 7 services/555 success/60 failed; btun 5/73/0; splunk_access 11/3765/351; web_admin 4/17/629.
- `... | eval id_type=coalesce('userIdentity.type',"MISSING") | eval nm=coalesce(userName,"MISSING") | stats count, count(eval(id_type="MISSING")) as missing_type, count(eval(nm="MISSING")) as missing_name by id_type` -> 3 rows: AWSService 332/0/0, AssumedRole 789/0/0, IAMUser 5450/0/0.
- `... userIdentity.type=IAMUser | stats count by userName, userIdentity.arn` -> 4 rows, each arn:aws:iam::622676721278:user/<name>.

### What it means
Coverage premise p1 is now settled from result output, not fieldsummary metadata. (1) The feed records IAM users' AWS service access with identity context: each of the four names accessed between 4 and 11 distinct eventSources, with both outcomes represented — bstoll, splunk_access and web_admin have failed attempts (60/351/629) alongside successes; btun is success-only (73). (2) Exhaustiveness: the id_type partition accounts for every one of the 6571 events (332+789+5450=6571, zero events with missing identity type or name), so no event — and no IAM user — escapes the IAMUser bucket. (3) userIdentity.arn confirms all four are IAM users of Frothly's account 622676721278. The complete set, alphabetical, comma-separated without spaces: bstoll,btun,splunk_access,web_admin.

## Ruled out
- AssumedRole identities (splunk_lambda, config-role-us-west-1, flowlogsRole, AWSServiceRoleFor*) — userIdentity.type=AssumedRole, roles not IAM users.
- AWSService identities (EC2InstanceRole, AWS_InspectorEvents_Invoke_Assessment_Template) — service-linked, not IAM users.
- user_name value "nullweb_admin" — 3 events, all IAMUser web_admin AccessDenied (CreateAccessKey/ListAccessKeys); extraction artifact, not a 13th user.

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
