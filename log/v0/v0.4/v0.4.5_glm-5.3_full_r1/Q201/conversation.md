# Q201 — SH <-> Senior conversation

### 12:05:05 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['aws:cloudtrail'] sources=- fields=['eventName', 'eventSource', 'userIdentity.type', 'userName', 'userIdentity.arn', 'additionalEventData', 'requestParameters', 'responseElements']
**Technique:** senior
**Reason:** The question asks for a field to alert on for AWS API activity without MFA, which is an AWS API audit question. Frothly's CloudTrail feed is the established source for AWS API activity and identity context, and MFA-related context, if present, will be in CloudTrail event structure rather than endpoint or network feeds.

Determine which full JSON field path in Frothly's aws:cloudtrail records indicates that AWS API activity occurred without MFA, and establish it from CloudTrail evidence rather than AWS convention. The answer must be the exact field path, not a value.

### 12:06:36 - s1 -> SH   [REPORT - round 1 - FOUND]
> The field is a string "false" (not boolean) in this dataset — an alert would be userIdentity.sessionContext.attributes.mfaAuthenticated="false". The field is present only on AssumedRole and IAMUser AwsApiCall events (2155 of 6571 total cloudtrail events); AWSService-type events carry no sessionConte
_full: reports/s1_round_1.md_

### 12:06:41 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Use the field path that is present on AwsApiCall events and directly expresses MFA state for those API events; console-login-only MFA fields do not satisfy the question.

**continue** — The candidate matches the question's requested unit — a JSON field path — in CloudTrail, but the answer is not yet submittable because the report ended at the iteration cap and its load-bearing coverage and selection premises are still unverified.
**New scope:** sourcetypes=[] sources=[] fields=['userIdentity.sessionContext.attributes.mfaAuthenticated', 'additionalEventData.MFAUsed', 'authentication_method', 'eventType', 'eventName', 'userIdentity.type']

Establish the coverage and selection premises from aws:cloudtrail with exact result output. Show, in quotable form, which MFA-related fields occur on AwsApiCall events versus ConsoleLogin/AwsConsoleSignIn events, and which field directly carries the no-MFA state for AWS API activity. Then restate the exact full JSON path literally if unchanged.

### 12:07:01 - s1 -> SH   [REPORT - round 2 - FOUND]
> Field path unchanged: userIdentity.sessionContext.attributes.mfaAuthenticated. The cross-tab is the single quotable artifact for both premises: on AwsApiCall events only mfaAuthenticated is present (value "false", string not boolean — alert condition is ="false"); additionalEventData.MFAUsed ("No") 
_full: reports/s1_round_2.md_

### 12:07:07 - SH -> s1   [ANSWER]
SH's answers to your open questions:
[q2] The field path to use is the one present on AwsApiCall events and absent as a rival on the ConsoleLogin-only MFA fields; if the cross-tab stands as reported, that settles the question.

**userIdentity.sessionContext.attributes.mfaAuthenticated** (json_path) from s1

The value appears literally in s1's report. s1 established that among MFA-related fields in Frothly's aws:cloudtrail data, AwsApiCall events carry only userIdentity.sessionContext.attributes.mfaAuthenticated, while additionalEventData.MFAUsed and authentication_method appear only on AwsConsoleSignIn/ConsoleLogin events and therefore do not fit the question's AWS API activity qualifier.

**Premises it rests on:** p1, p2

### 12:07:07 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

