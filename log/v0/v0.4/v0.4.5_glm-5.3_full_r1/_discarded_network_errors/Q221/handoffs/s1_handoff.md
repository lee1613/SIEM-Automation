# s1 - Q221 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudtrail eventName="CreateAccessKey" OR eventName="CreateKey" | stats count by eventName, errorCode, errorMessage
- index=botsv3 sourcetype=aws:cloudtrail eventName="CreateAccessKey" | stats count by requestParameters, responseElements, user_identity_arn, sourceIPAddress, eventTime
- index=botsv3 sourcetype=aws:cloudtrail eventName="Create*" errorCode="*" | stats count by eventName, errorCode
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.accessKeyId="AKIAJOGCDXJ5NW5PXUPA" | stats count by eventName, errorCode, eventTime
### What it means
Intention: The CreateAccessKey error shows "user nullweb_admin" — an odd artifact. Let me check the attacker's HTTP requests to IAM to see the actual UserName parameter passed, and verify this key is the leaked one.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['aws:cloudtrail'] sources=[] fields=['eventSource', 'eventName', 'userIdentity.accessKeyId', 'userName', 'errorCode', 'errorMessage', 'requestParameters', 'requestParameters.userName', 'requestParameters.policyName', 'eventTime']
- Rounds worked: 2/3  (iterations: 10, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail eventName="Create*" errorCode="*" | stats count by eventName, errorCode
- index=botsv3 sourcetype=aws:cloudtrail eventName="CreateAccessKey" OR eventName="CreateKey" | stats count by eventName, errorCode, errorMessage
- index=botsv3 sourcetype=aws:cloudtrail eventName="CreateAccessKey" | stats count by requestParameters, responseElements, user_identity_arn, sourceIPAddress, eventTime
- index=botsv3 sourcetype=aws:cloudtrail userIdentity.accessKeyId="AKIAJOGCDXJ5NW5PXUPA" | stats count by eventName, errorCode, eventTime
