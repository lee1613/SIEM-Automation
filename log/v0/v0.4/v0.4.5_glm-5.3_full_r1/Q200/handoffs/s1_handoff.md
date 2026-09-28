# s1 - Q200 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=3_
**Scope:** sourcetype=aws:cloudtrail | fields=userIdentity.type, userName, userIdentity.arn, errorCode, eventSource, eventName, eventType
**Insight:** FOUND
**Candidate:** bstoll,btun,splunk_access,web_admin   **Confidence:** 97

## Prior rounds
- R1: aws:cloudtrail (6571 events); IAMUser bucket = bstoll 615, btun 73, splunk_access 4116, web_admin 646; all four have successes, three have failures; rivals are roles/services; "nullweb_admin" is a web_admin artifact. Submitted FOUND.
- R2: Verified from result output: IAMUser events span 4–11 eventSources per user with success+failed splits (bstoll 555/60, btun 73/0, splunk_access 3765/351, web_admin 17/629); id_type partition covers all 6571 events, zero missing identity; ARNs confirm arn:aws:iam::622676721278:user/<name>. Submitted FOUND.

## This round
### What I ran
- `... | eval id_type=coalesce('userIdentity.type',"MISSING") | stats count as events, dc(userName), dc(eventSource), count(eval(errorCode="success")) as successful, count(eval(errorCode!="success")) as failed by id_type` -> 3 rows: AWSService 332/8/1/332/0; AssumedRole 789/7/13/762/27; IAMUser 5450/4/14/4410/1040.
- `... | stats count, values(userName) as userNames by id_type, userIdentity.arn` -> 17 rows: every AssumedRole ARN is arn:aws:sts::622676721278:assumed-role/<role>/<session>; every IAMUser ARN is arn:aws:iam::622676721278:user/<name>.
- `... | stats count by id_type, userName | sort id_type, userName` -> 19 rows: IAMUser = bstoll 615, btun 73, splunk_access 4116, web_admin 646; AWSService/AssumedRole rows are role and service names only.

### What it means
p1 verified: the id_type partition accounts for all 6571 events (332+789+5450=6571, no MISSING bucket), and the IAMUser bucket shows AWS service accesses (14 distinct eventSources) with both outcomes — 4410 successful and 1040 failed attempts. Its complete userName set is exactly bstoll, btun, splunk_access, web_admin. p2 verified: rival identity types in the same feed are AssumedRole (ARNs arn:aws:sts::...:assumed-role/...) and AWSService (service-linked role names) — neither carries an IAM user ARN, so userIdentity.type=IAMUser is the only bucket satisfying "IAM users". Candidate unchanged: bstoll,btun,splunk_access,web_admin.

## Ruled out
- AssumedRole identities (splunk_lambda, config-role-us-west-1, flowlogsRole, AWSServiceRoleFor*) — assumed-role ARNs, roles not IAM users.
- AWSService identities (EC2InstanceRole, AWS_InspectorEvents_Invoke_Assessment_Template) — service-linked, not IAM users.
- user_name value "nullweb_admin" — 3 events, all IAMUser web_admin AccessDenied; extraction artifact, not a 13th user.

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:cloudtrail'] sources=[] fields=['userIdentity.type', 'userIdentity.userName', 'errorCode', 'errorMessage', 'eventSource', 'eventName', 'recipientAccountId', 'awsRegion']
- Rounds worked: 3/3  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail user_name="nullweb_admin" | stats count by eventName, eventType, userIdentity.type, userName, errorCode
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count by userName
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count by userName, errorCode
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count by userName, userIdentity.arn
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats dc(eventSource) as services_accessed, count(eval(errorCode="success")) as successful, count(eval(errorCode!="success")) as failed by userName
- index=botsv3 sourcetype=aws:cloudtrail | eval id_type=coalesce('userIdentity.type', "MISSING") | eval nm=coalesce(userName, "MISSING") | stats count, count(eval(id_type="MISSING")) as missing_type, count(eval(nm="MISSING")) as missing_name by id_type
- index=botsv3 sourcetype=aws:cloudtrail | eval id_type=coalesce('userIdentity.type',"MISSING") | stats count as events, dc(userName) as distinct_userNames, dc(eventSource) as distinct_eventSources, count(eval(errorCode="success")) as successful, count(eval(errorCode!="success")) as failed by id_type
- index=botsv3 sourcetype=aws:cloudtrail | eval id_type=coalesce('userIdentity.type',"MISSING") | stats count by id_type, userName | sort id_type, userName
- index=botsv3 sourcetype=aws:cloudtrail | eval id_type=coalesce('userIdentity.type',"MISSING") | stats count, values(userName) as userNames by id_type, userIdentity.arn
- index=botsv3 sourcetype=aws:cloudtrail | stats count
- index=botsv3 sourcetype=aws:cloudtrail | stats count by user_name | sort user_name
- index=botsv3 sourcetype=aws:cloudtrail | stats count by userIdentity.type, userName
- index=botsv3 sourcetype=aws:cloudtrail | stats count, count(eval(isnull('userIdentity.type') OR 'userIdentity.type'="")) as missing_type, count(eval(isnull(userName) OR userName="")) as missing_name by 'userIdentity.type'
- index=botsv3 sourcetype=aws:cloudtrail | stats count, count(eval(isnull(userIdentity.type) OR userIdentity.type="")) as missing_type, count(eval(isnull(userName) OR userName="")) as missing_name by userIdentity.type
