# Q221 — SH <-> Senior conversation

### 16:21:56 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['aws:cloudtrail'] sources=- fields=['eventSource', 'eventName', 'userIdentity.accessKeyId', 'userName', 'errorCode', 'errorMessage', 'requestParameters', 'requestParameters.userName', 'requestParameters.policyName', 'eventTime']
**Technique:** senior
**Reason:** CloudTrail is the AWS audit feed that records access keys, failed IAM API calls, and requestParameters naming the target resource. Prior case memory already points to leaked-key IAM misuse and failed CreateAccessKey-style activity, so this scope directly contains the actor key, unauthorized create-key action, and target resource name.

In Frothly's aws:cloudtrail data, identify the leaked access key's unauthorized attempt to create a key for a specific resource, determine which API call it was, and return the one-word name of the resource targeted by that create-key attempt.

### 16:24:08 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s1_round_1.md_

### 16:24:15 - SH -> s1   [COMMAND]
**continue** — This round narrowed the problem to the correct IAM create-key failure path and the likely leaked access key, which is useful progress. But the question asks for the targeted resource name, and the current report stops at an unresolved parsing artifact instead of reading that name from request data.
**New scope:** sourcetypes=['aws:cloudtrail'] sources=[] fields=['eventName', 'errorCode', 'errorMessage', 'eventTime', 'userIdentity.accessKeyId', 'requestParameters', 'requestParameters.userName', 'responseElements', 'sourceIPAddress']

For the unauthorized create-key attempt made with access key AKIAJOGCDXJ5NW5PXUPA in aws:cloudtrail, determine the exact request parameter naming the target resource on the failed CreateAccessKey call. Read the requestParameters for that event directly, resolve the 'nullweb_admin' artifact into the actual resource name if it is a parsing issue, and confirm that this key is the leaked key involved in the unauthorized IAM activity. Then restate the one-word resource name literally if unchanged.

### 16:24:22 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s1_round_2.md_

### 16:24:22 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 16:24:22 - runner   [NOTE]
s1 api_failed — retired, spawn slot refunded

### 16:24:22 - runner   [NOTE]
s1 api_failed and no operator reachable — skipping; slot already refunded, decision request at C:\dev\SIEM-Automation\log\v1\v1.4/v1.4.5_glm-5.3_full_r1\decision_request.json

### 16:24:28 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['aws:cloudtrail'] sources=- fields=['eventName', 'eventTime', 'userIdentity.accessKeyId', 'requestParameters', 'errorCode', 'errorMessage', 'userName', 'userIdentity.userName', 'userIdentity.arn', 'sourceIPAddress']
**Technique:** senior
**Reason:** The prior senior was lost to transport failure before resolving the requestParameters artifact. CloudTrail still directly holds the failed IAM create-key event, its target resource name, and the identity context needed to tie the action to the leaked key.

In Frothly's aws:cloudtrail data, isolate the failed CreateAccessKey attempt made with access key AKIAJOGCDXJ5NW5PXUPA, read the requestParameters directly, and determine the exact one-word name of the resource for which the adversary tried to create a key. Also establish from the same CloudTrail activity that this access key is the leaked key involved in the unauthorized IAM actions.

