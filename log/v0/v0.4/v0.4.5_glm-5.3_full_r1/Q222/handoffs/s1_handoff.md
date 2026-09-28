# s1 - Q222 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=aws:cloudtrail | fields=userAgent, eventName, eventSource, errorCode, userIdentity.accessKeyId, sourceIPAddress
**Insight:** FOUND
**Candidate:** ElasticWolf/5.1.6   **Confidence:** 98

## Prior rounds
- (Round 1) No prior rounds; this is the first round on Q-leaked-key DescribeAccount userAgent.

## This round
### What I ran
- `index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*DescribeAccount*" | stats count by eventName, userAgent, errorCode` -> 1 event: DescribeAccountAttributes, userAgent=ElasticWolf/5.1.6, errorCode=Client.UnauthorizedOperation
- `get_raw_events sourcetype=aws:cloudtrail keyword=AKIAJOGCDXJ5NW5PXUPA` -> 10 raw events; the DescribeAccountAttributes event (2018-08-20T09:27:06Z, ec2.amazonaws.com, web_admin, 82.102.18.111) carries userAgent "ElasticWolf/5.1.6" verbatim
- `index=botsv3 sourcetype=aws:cloudtrail eventName="*DescribeAccount*" | stats count by eventName, errorCode, userAgent, user, sourceIPAddress` -> 2 groups: the unauthorized leaked-key event + 8 successful bstoll signin.amazonaws.com events (legitimate console)
- `index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*Account*"` -> only DescribeAccountAttributes
- `index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" | stats count by eventName, eventSource, errorCode, userAgent` -> all 10 leaked-key events enumerated; no other account-description call

### What it means
Exactly one unauthorized account-description attempt exists with leaked key AKIAJOGCDXJ5NW5PXUPA: DescribeAccountAttributes (ec2.amazonaws.com) at 2018-08-20T09:27:06Z from 82.102.18.111, denied with Client.UnauthorizedOperation. Its userAgent field, read verbatim from the raw event, is "ElasticWolf/5.1.6" — the full string, with no additional components. The separate IAM denial burst (CreateAccessKey/CreateUser/DeleteAccessKey/ListAccessKeys at 09:16:12Z from 35.153.154.221, userAgent Boto3/1.7.44 Python/2.7.12 Linux/4.4.0-1063-aws Botocore/1.10.44) is a different event set and does not describe an account; iam:GetUser at 09:27:07Z shares the ElasticWolf agent but is not a DescribeAccount* call. The successful DescribeAccountAttributes events belong to bstoll via the AWS console and are not adversary activity.

## Ruled out
- IAM denial burst (Boto3/1.7.44 Python/2.7.12 Linux/4.4.0-1063-aws Botocore/1.10.44, 35.153.154.221, 09:16:12Z) - eventNames are CreateAccessKey/CreateUser/DeleteAccessKey/ListAccessKeys, none is a describe-account call
- iam:GetUser denial (ElasticWolf/5.1.6, 09:27:07Z) - a GetUser call, not DescribeAccount*
- bstoll's 8 successful DescribeAccountAttributes events (signin.amazonaws.com) - successful, legitimate console activity, not the leaked key
- ListAccessKeys denial from 209.107.196.112 (Boto3/1.6.3 Windows/2012ServerR2) - not a describe-account call

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:cloudtrail'] sources=[] fields=['userIdentity.accessKeyId', 'eventName', 'eventSource', 'errorCode', 'errorMessage', 'userAgent', 'sourceIPAddress', 'eventTime']
- Rounds worked: 1/3  (iterations: 10, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*Account*" | stats count by eventName, errorCode, userAgent, eventSource
- index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*DescribeAccount*" | stats count by _raw | top limit=5 _raw
- index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*DescribeAccount*" | stats count by eventName, userAgent, errorCode
- index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" eventName="*DescribeAccount*" | stats count by eventName, userAgent, errorCode, eventName
- index=botsv3 sourcetype=aws:cloudtrail "AKIAJOGCDXJ5NW5PXUPA" | stats count by eventName, eventSource, errorCode, userAgent
- index=botsv3 sourcetype=aws:cloudtrail eventName="*DescribeAccount*" | stats count by eventName, errorCode, userAgent, user, sourceIPAddress
