# s1 - Q201 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=1_
**Scope:** sourcetype=aws:cloudtrail | fields=userIdentity.sessionContext.attributes.mfaAuthenticated, additionalEventData.MFAUsed, authentication_method, eventType, eventName, userIdentity.type
**Insight:** FOUND
**Candidate:** userIdentity.sessionContext.attributes.mfaAuthenticated   **Confidence:** 99

## Prior rounds
- R1: Manifest + fieldsummary + raw JSON established userIdentity.sessionContext.attributes.mfaAuthenticated ("false", 2155 AwsApiCall events); rivals additionalEventData.MFAUsed and authentication_method found only on 4 ConsoleLogin events; submitted field path.

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudtrail (mfaAuthenticated=* OR MFAUsed=* OR authentication_method=*) | stats count dc(eventName) values(...) by eventType -> 2 rows, quotable cross-tab.

### What it means
FOUND, premises settled. The cross-tab shows in one output: AwsApiCall (2155 events, 96 distinct eventNames) carries ONLY userIdentity.sessionContext.attributes.mfaAuthenticated, value "false" — the field that directly expresses the no-MFA state for AWS API activity. AwsConsoleSignIn (4 events, ConsoleLogin only) carries additionalEventData.MFAUsed="No" and authentication_method="SFA" — console sign-in fields, absent from every API call. Both coverage (only three MFA-bearing fields exist in the feed, split exactly this way) and selection (mfaAuthenticated is the only one on API records) are verified. The exact full JSON path is unchanged: userIdentity.sessionContext.attributes.mfaAuthenticated.

## Ruled out
- additionalEventData.MFAUsed — AwsConsoleSignIn/ConsoleLogin only (4 events, bstoll), never on AwsApiCall.
- authentication_method — same 4 ConsoleLogin events, value "SFA", never on AwsApiCall.
- ms:aad:signin mfa* fields — Azure AD sign-in telemetry, not AWS API activity.