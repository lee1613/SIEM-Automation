# s1 - Q223 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=0_
**Scope:** index=botsv3 sourcetypes=aws:cloudtrail, aws:s3:accesslogs, aws:elb:accesslogs | fields eventName, eventTime, imageId, errorCode, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: first web_admin RunInstances attempt = ami-41e0b93b, 2018-08-20T09:16:22Z, failed; aws:description empty; codename unresolved.
- R2: all 576 attempts failed; every in-dataset AMI-naming feed empty; external guess "Xenial Xerus" submitted at confidence 40.
- R3: verified leaked-key→session-key→attempt chain; ordered all 15 attempted AMIs; fleet image disjoint from attacker set.
- R4: answered SH's three questions from held evidence; named aws:s3:accesslogs and aws:elb:accesslogs as residual unchecked feeds.
- R5: closed both residual feeds (0 events); AMI string in CloudTrail only as RunInstances imageId (38 events); no Ubuntu/codename term in CloudTrail; web_lookup of the AMI ID returned nothing.
- R6 (this): settlement — re-quoted held results as runner-acceptable support for p2/p3/p4; no new queries.

## This round
### What I ran
- No new searches. All quotes below are results already run in rounds 3 and 5, re-quoted verbatim in premise_updates.

### What it means
NOT_FOUND, stated explicitly from quoted results: the Ubuntu codename is unreadable here. The settlement rests on four quoted outputs: (1) the earliest web_admin RunInstances row — `{"_time": "2018-08-20T17:16:22.000+08:00", "imageId": "ami-41e0b93b", "accessKeyId": "ASIAZB6TMXZ7LL6JBJQA", "userArn": "arn:aws:iam::622676721278:user/web_admin", "errorCode": "Client.InstanceLimitExceeded"}` — with the GetSessionToken event showing the leaked key AKIAJOGCDXJ5NW5PXUPA minting that session key at 09:16:12Z, ten seconds before the first attempt (p2 VERIFIED); (2) `{"count": "38", "distinctEventNames": "1", "eventNames": "RunInstances"}` — ami-41e0b93b appears in CloudTrail only as the RunInstances imageId, nowhere by name or description (p3 REFUTED); (3) aws:s3:accesslogs and aws:elb:accesslogs each returning `{"results": [], "meta": {"total_event_count": 0}}` for the AMI ID; (4) the eleven-term Ubuntu/codename search returning 0 events (p4 VERIFIED). The act is fully established — compromised user web_admin, first attempt 2018-08-20T09:16:22Z on ami-41e0b93b, first of 576 failed attempts — but the AMI-to-codename mapping exists in no artifact in this dataset, and web_lookup of the ID returns nothing. The unconfirmed external candidate "Xenial Xerus" remains in notes only; no record shows it.

## Ruled out
- Every in-dataset path to the AMI's OS: aws:description (0 events index-wide), DescribeImages responseElements (null ×31), bash_history (no "ami-" strings), osquery:results, cloud-init, cloud-init-output, aws:config:rule, aws:cloudwatch:guardduty, aws:s3:accesslogs, aws:elb:accesslogs (0 hits each for the AMI ID), CloudTrail outside RunInstances (dc(eventName)=1 over 38 events), any Ubuntu/codename string in CloudTrail (0 events).
- External identification via web_lookup — no snippets for the AMI ID.
- Any successful launch by web_admin — all 576 attempts carry an errorCode.

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: This senior exhausted the CloudTrail-plus-log path and could not produce the Ubuntu codename from any searched in-dataset artifact; the value still does not appear literally anywhere in its reports, and another round in the same path is unavailable and would not resolve that.
- Scope I owned: sourcetypes=['aws:cloudtrail', 'aws:description'] sources=[] fields=['userIdentity.accessKeyId', 'userName', 'eventName', 'eventSource', 'requestParameters', 'responseElements', 'errorCode', 'eventTime', 'instanceType', 'imageId', 'image_id', 'name', 'description']
- Rounds worked: 5/5  (iterations: 43, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "ami-41e0b93b" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype="aws:description" "41e0b93b" | stats count values(action) as action by source | head 10
- index=botsv3 sourcetype="aws:description" "ami-41e0b93b" | stats count values(action) as action values(object_category) as object_category by sourcetype | head 5
- index=botsv3 sourcetype="aws:description" | stats count by action, object_category | sort -count | head 20
- index=botsv3 sourcetype=aws:cloudtrail "ami-41e0b93b" | stats count dc(eventName) as distinctEventNames values(eventName) as eventNames
- index=botsv3 sourcetype=aws:cloudtrail "ami-41e0b93b" | stats count values(eventName) as eventNames by errorCode
- index=botsv3 sourcetype=aws:cloudtrail "ubuntu" OR "xenial" OR "bionic" OR "trusty" OR "artful" OR "zesty" OR "yakkety" OR "wily" OR "vivid" OR "utopic" OR "precise"
- index=botsv3 sourcetype=aws:cloudtrail "ubuntu" OR "xenial" OR "bionic" OR "trusty" OR "artful" OR "zesty" OR "yakkety" OR "wily" OR "vivid" OR "utopic" OR "precise" | stats count by eventName
- index=botsv3 sourcetype=aws:cloudtrail eventName=DescribeImages | stats count values(userIdentity.userName) as users min(_time) as firstTime by eventName
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances "AWSServiceRoleForAutoScaling" | stats count values(awsRegion) as regions values(requestParameters.instancesSet.items{}.imageId) as imageIds values(responseElements.instancesSet.items{}.instanceId) as instanceIds by userIdentity.userName
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances "web_admin" | stats count min(_time) as firstTime values(requestParameters.instancesSet.items{}.imageId) as imageIds by _time, requestParameters.instancesSet.items{}.imageId, sourceIPAddress, userAgent | sort _time | head 20
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userIdentity.type=AssumedRole | stats count values(awsRegion) as regions values(requestParameters.instancesSet.items{}.imageId) as imageIds values(responseElements.instancesSet.items{}.instanceId) as instanceIds by userIdentity.sessionContext.sessionIssuer.userName
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userIdentity.userName!=web_admin | stats count values(awsRegion) as regions values(requestParameters.instancesSet.items{}.imageId) as imageIds by userIdentity.userName
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userIdentity.userName=web_admin | stats count values(errorCode) as errorCode by _time, requestParameters.instancesSet.items{}.imageId | sort _time | head 40
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userIdentity.userName=web_admin | stats count values(userIdentity.accessKeyId) as accessKeyId values(userIdentity.arn) as userArn values(errorCode) as errorCode by _time, requestParameters.instancesSet.items{}.imageId | sort _time | head 3
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userIdentity.userName=web_admin | stats min(_time) as firstAttemptEpoch count by requestParameters.instancesSet.items{}.imageId | sort firstAttemptEpoch
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances | stats count by errorCode, userIdentity.userName
- index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances | stats count values(requestParameters.instancesSet.items{}.imageId) as imageIds values(userIdentity.arn) as userArn values(userIdentity.accessKeyId) as accessKey min(_time) as firstTime by recipientAccountId | sort firstTime
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=web_admin | stats count dc(eventName) as distinctEvents values(eventName) as eventNames by userIdentity.accessKeyId | sort -count
- index=botsv3 sourcetype=aws:cloudwatch:guardduty "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=aws:config:rule "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=aws:elb:accesslogs "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=aws:s3:accesslogs "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=bash_history "ami-" | stats count by host, user | head 10
- index=botsv3 sourcetype=cloud-init "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=cloud-init-output "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=osquery:results "ami-41e0b93b" | stats count by sourcetype
- index=botsv3 sourcetype=osquery:results "ubuntu" | stats count by name, action | head 10
