# s1 - Q221 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means
Intention: The GetUser denial (requestParameters=null) renders "user web_admin" cleanly while CreateAccessKey (also requestParameters=null) renders "user nullweb_admin" — so nullity of parameters alone doesn't explain the prefix. I need to (a) check real AWS error-message format externally, (b) read both ListAccessKeys raw events and the burst structure, and (c) find where "nullweb_admin" appears across the whole dataset. These are independent, so I'll run them together.


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['aws:cloudtrail'] sources=[] fields=['userIdentity.accessKeyId', 'userIdentity.type', 'eventSource', 'eventName', 'errorCode', 'errorMessage', 'requestParameters', 'resources{}.ARN', 'resources{}.accountId', 'resources{}.type', 'userName']
- Rounds worked: 3/3  (iterations: 13, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail AKIAJOGCDXJ5NW5PXUPA errorCode=AccessDenied | stats count by eventName, errorMessage
- index=botsv3 sourcetype=aws:cloudtrail AKIAJOGCDXJ5NW5PXUPA eventName=UpdateAccessKey | stats count by errorMessage, requestParameters, responseElements
- index=botsv3 sourcetype=aws:cloudtrail AKIAJOGCDXJ5NW5PXUPA | stats count by eventName, errorCode, eventSource
- index=botsv3 sourcetype=aws:cloudtrail eventName=CreateAccessKey | stats count by errorCode, errorMessage, userName
- index=botsv3 sourcetype=aws:cloudtrail eventName=UpdateAccessKey | stats count by userName, errorCode, errorMessage
