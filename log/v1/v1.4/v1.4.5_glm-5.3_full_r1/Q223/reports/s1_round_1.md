# s1 - Q223 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** index=botsv3 | sourcetype=aws:cloudtrail (eventName=RunInstances) | sourcetype=aws:description source=us-west-1:ec2_images | fields: image_id, userName, userIdentity.accessKeyId, sourceIPAddress, errorCode, eventTime
**Insight:** partial — the act and the first attempt's AMI are evidenced; the Ubuntu codename is not resolvable from any feed reached this round.
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1: compromised IAM user = web_admin (temp key ASIAZB6TMXZ7LL6JBJQA, IP 139.198.18.205); 576 failed RunInstances across 15 AMIs from 2018-08-20T09:16:22Z; first attempt = ami-41e0b93b; no reachable feed maps those AMIs to an Ubuntu codename.

## This round
### What I ran
- get_source_types -> aws:cloudtrail and aws:description confirmed present.
- `index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances | stats count min(_time) values(userIdentity.arn) by userName` -> 2 rows total: web_admin (576 events, first 1534756582), AWSServiceRoleForAutoScaling (6 events, first 1534769727).
- `... eventName=RunInstances userName=web_admin | stats count min(_time) values(errorCode) by image_id` -> 15 rows, all returned: earliest ami-41e0b93b @1534756582 (2018-08-20T09:16:22Z), then ami-67973709 @...583, ami-1157157d @...584, ami-79aeae19, ami-325d2e4e, ami-f0870294, ami-1ee65166, ami-d39a02b5, ami-37df2255, ami-2581aa40, ami-4d46d534, ami-5d055232, ami-4262d53f, ami-d7aab2b3, ami-af79ebc0 (@1534757289); errorCodes Client.UnauthorizedOperation / InstanceLimitExceeded / Unsupported / Server.InsufficientInstanceCapacity.
- get_sources aws:description -> 21 sources, incl. us-west-1:ec2_images (14 events).
- get_raw_events us-west-1:ec2_images (14/14 read) -> only Frothly-owned AMIs ami-071fdb5b695e37666 (FrothlyWebServerAMI) and ami-055313c50737a491a (FrothlyWeb); no Ubuntu, none of the 15 targeted AMIs.
- get_raw_events keyword=ami-41e0b93b (3 of 38) -> request carries only imageId/instanceType/tags (my_i_key=my_i_val)/maxCount 10; responseElements null; userData redacted; userIdentity web_admin with accessKeyId ASIAZB6TMXZ7LL6JBJQA, sourceIPAddress 139.198.18.205, mfaAuthenticated false, session created 09:16:12Z.

### What it means
The act is fully evidenced: web_admin — compromised, per the temporary key, MFA false, session minted 10s before the burst, calls from 139.198.18.205 via Boto3/1.7.42 Python/2.7.12 — attempted RunInstances 576 times, all denied. The first attempt targeted ami-41e0b93b at 2018-08-20T09:16:22Z. But the question asks for that image's Ubuntu codename, and nothing I reached describes the adversary's AMIs: CloudTrail holds only the raw imageId, and the sole image-description feed lists Frothly's own two AMIs. Stating a codename now would be inventing it, so no value is submitted.

## Ruled out
- AWSServiceRoleForAutoScaling RunInstances — AWS service role, 6 events, not the compromised user.
- aws:description us-west-1:ec2_images — Frothly-owned AMIs only; none of the 15 targeted AMIs, no Ubuntu image.
- CloudTrail responseElements — null on every attempt (all failed), so no launched-instance OS data.
- requestParameters.userData — "<sensitiveDataRemoved>".

Next: hunt the adversary's tooling (stream:http, bash_history, cloud-init) for the AMI list with names; check GuardDuty findings; or resolve ami-41e0b93b externally. If it is not Ubuntu, walk the 15 AMIs in first_time order to the first Ubuntu one.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances userName=web_admin | head 1 …` (50 of 254 rows seen); `get_sourcetype_fields: {"sourcetype": "aws:description"}` (50 of 292 rows seen). A claim resting on them alone is UNVERIFIED._
