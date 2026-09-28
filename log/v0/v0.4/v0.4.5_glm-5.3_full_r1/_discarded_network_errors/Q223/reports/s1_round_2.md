# s1 - Q223 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** index=botsv3 sourcetypes=aws:cloudtrail, aws:config:rule, aws:cloudwatch:guardduty, cloud-init, cloud-init-output, bash_history, osquery:results | fields eventName, eventTime, imageId, responseElements, _raw
**Insight:** FOUND (partial — see caveat)
**Candidate:** Xenial Xerus   **Confidence:** 40

## Prior rounds
- Round 1: located the act — first web_admin RunInstances attempt = ami-41e0b93b at 2018-08-20T09:16:22Z, failed; aws:description feed empty; codename unresolved.
- Round 2 (this): confirmed all 576 attempts failed; exhausted every in-dataset feed that could name the AMI's OS — all empty.

## This round
### What I ran
- `eventName=RunInstances | stats count by errorCode, userIdentity.userName` → 4 rows, all web_admin: 280 InstanceLimitExceeded, 185 UnauthorizedOperation, 104 Unsupported, 7 InsufficientInstanceCapacity. Zero successes — every event is an attempt.
- `eventName=RunInstances userIdentity.userName=web_admin | stats count values(errorCode) by _time, imageId | sort _time | head 40` → first attempt 09:16:22Z on ami-41e0b93b (InstanceLimitExceeded), then ami-67973709 (09:16:23Z), ami-1157157d (09:16:24Z); the three cycle thereafter.
- `eventName=DescribeImages | stats count values(userIdentity.userName)` → 31 events (bstoll, splunk_access); raw read of 5 → all `"responseElements": null` — no image names exist in CloudTrail.
- Literal `ami-41e0b93b` searches: osquery:results → 0, cloud-init → 0, aws:config:rule → 0, aws:cloudwatch:guardduty → 0; `bash_history "ami-"` → 0.

### What it means
The act is nailed down from data: the compromised IAM user web_admin (session key ASIAZB6TMXZ7LL6JBJQA, created 10s before the first call, from 139.198.18.205) attempted RunInstances 576 times, all failing; the first attempt targeted ami-41e0b93b at 2018-08-20T09:16:22Z. The codename is NOT derivable in-dataset: every feed that could name that AMI's OS is empty (aws:description 0 events index-wide; DescribeImages responses null; no AMI strings in bash_history, osquery, cloud-init, config-rule, GuardDuty). The submitted value "Xenial Xerus" rests on external identification of ami-41e0b93b as an Ubuntu 16.04 image, with circumstantial in-dataset support (attacker host kernel 4.4.0-131-generic = Ubuntu 16.04; the question presupposes the first attempt is the Ubuntu one). Treat it as a candidate pending external confirmation, not a data-verified fact.

## Ruled out
- aws:description as AMI-name source — 0 events in the entire index.
- CloudTrail DescribeImages responseElements — null in all 31 events.
- bash_history, osquery:results, cloud-init, aws:config:rule, aws:cloudwatch:guardduty — 0 hits for ami-41e0b93b (bash_history has no "ami-" strings at all).
- Any successful launch — all 576 web_admin RunInstances events carry an errorCode.
- AWSServiceRoleForAutoScaling as the compromised actor — service role; the attempts are web_admin's.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The Ubuntu codename for the first-attempt image ami-41e0b93b could appear in-dat"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The first launch attempt by the compromised IAM user is the RunInstances call at"
- other premise not filed: you already have an open other premise p3 - amend or settle that one. The text you sent was discarded: "ami-41e0b93b (us-east-1, 8-hex 2018-era ID) is an Ubuntu 16.04 cloud image whose"
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
