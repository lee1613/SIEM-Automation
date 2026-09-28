# s1 - Q218 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=5_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail | fields userIdentity.accessKeyId, userIdentity.type, eventSource, errorCode
**Insight:** partial
**Candidate:** ASIAZB6TMXZ7FWTIS4NJ   **Confidence:** 60

## Prior rounds
(none — first round)

## This round
### What I ran
- get_sources cloudtrail → aws:cloudtrail confirmed (s3://cloudtrail-622676721278/... .json.gz).
- get_sourcetype_fields aws:cloudtrail → errorCode populated on all 6571 events (5504 "success"); userIdentity.type IAMUser=5450; access-key field not in the 50 rows shown.
- search_keyword accessKeyId → field is userIdentity.accessKeyId.
- `eventSource=iam.amazonaws.com | stats count by userIdentity.accessKeyId, userIdentity.type, errorCode` → 8 rows / 118 events, all IAMUser; 3 keys carry errors.
- `eventSource=iam.amazonaws.com userIdentity.type=IAMUser errorCode!="success" | stats dc(errorCode) ... by userIdentity.accessKeyId` → 3 keys, ALL tied at 1 distinct error.
- `| stats dc(errorCode) by eventSource` → 18 eventSources; iam.amazonaws.com = 118 events.
- search_keyword resource → resources{}.ARN / resources{}.type exist.
- `| stats count dc(errorCode) by resources{}.type` → only AWS::IAM::Role (332) and AWS::KMS::Key (292); IAM::Role events carry no IAMUser identity.
- `userIdentity.type=IAMUser errorCode!="success" | stats dc(errorCode) as distinct_errors count values(errorCode) by userIdentity.accessKeyId | sort - distinct_errors` → 28 keys, all rows returned: ASIAZB6TMXZ7FWTIS4NJ = 6 distinct / 25 events; ASIAZB6TMXZ7LL6JBJQA = 5 / 622; AKIAIGKL572SFDPOKLHA = 4 / 351.

### What it means
The literal reading — "IAM resources" = eventSource=iam.amazonaws.com — cannot answer the question: its three erroring keys tie at exactly 1 distinct errorCode each (AKIAIGKL572SFDPOKLHA 9 NoSuchEntityException; AKIAJOGCDXJ5NW5PXUPA 6 AccessDenied; ASIAZB6TMXZ7MJUJJK6X 2 NoSuchEntityException), so there is no "most". The resources{}.type route is empty for IAMUser (all AWS::IAM::Role events are AWSService). The only reading with a unique maximum — and the one matching SH's "distinct error count rather than total event count" — is IAMUser identity + error events across services: ASIAZB6TMXZ7FWTIS4NJ with 6 distinct errorCodes (NoSuchBucketPolicy, NoSuchCORSConfiguration, NoSuchLifecycleConfiguration, NoSuchTagSet, NoSuchWebsiteConfiguration, ReplicationConfigurationNotFoundError). It beats the key with by far the most error events (ASIAZB6TMXZ7LL6JBJQA, 622 events, 5 distinct) and AKIAIGKL572SFDPOKLHA (4 distinct). All 28 IAMUser keys with errors were read in full (28 of 28 returned), so the ranking is complete. errorCode is populated on every event, so errorCode!="success" captures all error events.

## Ruled out
- eventSource=iam.amazonaws.com as the whole scope — 3-way tie at 1 distinct error, no unique winner.
- resources{}.type=AWS::IAM::Role as "IAM resources" — 332 events, all AWSService identity, zero IAMUser.
- ASIAZB6TMXZ7LL6JBJQA — most error events (622) but only 5 distinct errorCodes.
- AKIAIGKL572SFDPOKLHA — most IAM-service error events (9) but 1 distinct on IAM service, 4 overall.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sources: {"keyword": "cloudtrail"}` (31 of 62 rows seen); `get_sourcetype_fields: {"sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen). A claim resting on them alone is UNVERIFIED._
