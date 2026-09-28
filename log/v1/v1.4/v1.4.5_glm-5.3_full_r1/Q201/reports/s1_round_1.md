# s1 - Q201 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** sourcetype=aws:cloudtrail | fields=userIdentity.sessionContext.attributes.mfaAuthenticated, additionalEventData.MFAUsed, authentication_method, eventType, userIdentity.type
**Insight:** FOUND
**Candidate:** userIdentity.sessionContext.attributes.mfaAuthenticated   **Confidence:** 98

## Prior rounds
- (Round 1 — first round; no prior rounds.)

## This round
### What I ran
- search_keyword "mfa" -> manifest: aws:cloudtrail carries userIdentity.sessionContext.attributes.mfaAuthenticated; ms:aad:signin carries mfa* fields (Azure, out of scope).
- get_field_values userIdentity.sessionContext.attributes.mfaAuthenticated on aws:cloudtrail -> 1 distinct value "false", 2155 events, 100%.
- get_raw_events keyword=mfaAuthenticated -> raw JSON confirms nested path: userIdentity.sessionContext.attributes.mfaAuthenticated="false" (sibling creationDate).
- fieldsummary | search *sessionContext* OR *mfa* -> 8 rows; only MFA-bearing fields: mfaAuthenticated, additionalEventData.MFAUsed.
- mfaAuthenticated=* | stats count by eventType userIdentity.type -> 2 rows: AwsApiCall/AssumedRole=789, AwsApiCall/IAMUser=1366 (all 2155 are API calls).
- additionalEventData.MFAUsed=* | stats -> 4 events, all ConsoleLogin / AwsConsoleSignIn, MFAUsed=No, user bstoll.
- fieldsummary | search *Auth*/*MultiFactor*/*credential* -> 5 rows; extra field authentication_method -> 4 ConsoleLogin events, value "SFA".

### What it means
FOUND. The question asks for the field to alert on AWS API activity without MFA. In Frothly's CloudTrail feed, `userIdentity.sessionContext.attributes.mfaAuthenticated` is present on all 2155 AwsApiCall events and carries the value "false" — it is the field that directly states an API call was made in a session that was not MFA-authenticated. Raw event JSON confirms the exact nested path userIdentity → sessionContext → attributes → mfaAuthenticated. The two rivals (additionalEventData.MFAUsed, authentication_method) exist only on the 4 AwsConsoleSignIn ConsoleLogin events — console sign-ins, not API activity — so they are ruled out. The value is a string "false", so the alert condition is mfaAuthenticated="false".

## Ruled out
- additionalEventData.MFAUsed — appears only on 4 AwsConsoleSignIn ConsoleLogin events (bstoll), zero AwsApiCall events; marks console sign-in, not API activity.
- authentication_method — same 4 ConsoleLogin events, value "SFA"; console sign-in only.
- ms:aad:signin mfa* fields (mfaAuthDetail, mfaAuthMethod, mfaRequired, mfaResult) — Azure AD sign-in telemetry, not AWS API activity.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"min_count": 1, "sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen). A claim resting on them alone is UNVERIFIED._
