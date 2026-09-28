# s1 - Q223 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail | fields eventName, requestParameters.instancesSet.items{}.imageId, userIdentity.{userName,accessKeyId,arn}, sourceIPAddress, userAgent, errorCode, eventTime
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: located the act (first launch attempt = ami-41e0b93b, 2018-08-20T09:16:22Z, by web_admin, failed UnauthorizedOperation); Ubuntu codename unresolved — no feed checked yet names the AMI's OS.

## This round
### What I ran
- get_source_types → 102 sourcetypes, incl. aws:cloudtrail and aws:description.
- `index=botsv3 sourcetype=aws:cloudtrail eventName=RunInstances | stats count values(imageId) values(userArn) ... by recipientAccountId` → 582 events, 16 AMI IDs, exactly two actors: web_admin and the AWSServiceRoleForAutoScaling assumed role; earliest epoch 1534756582.
- `... eventName=RunInstances "web_admin" | stats count by _time, imageId, sourceIPAddress, userAgent | sort _time | head 20` → earliest web_admin attempt 2018-08-20T17:16:22+08:00 (09:16:22Z) on ami-41e0b93b; then ami-67973709 (09:16:23Z), ami-1157157d (09:16:24Z); all from 139.198.18.205, UA Boto3/1.7.42.
- get_raw_events keyword=ami-41e0b93b → 3 RunInstances events by web_admin, all errorCode Client.UnauthorizedOperation, session key ASIAZB6TMXZ7LL6JBJQA with sessionContext.creationDate 2018-08-20T09:16:12Z (10s before first attempt), instanceTypes m4.2xlarge/t2.2xlarge/m3.2xlarge, maxCount 10, us-east-1.
- `index=botsv3 sourcetype="aws:description" "ami-41e0b93b"` → 0; `"41e0b93b"` → 0; unfiltered `| stats count by action, object_category` → 0 — the aws:description feed holds no events in this index.
- get_sources keyword=aws → sources are s3 CloudTrail/ELB logs, stream:*, ssm agent logs; no description source exists.

### What it means
NOT_FOUND. The act is pinned: the compromised IAM user web_admin's first launch attempt is RunInstances on ami-41e0b93b at 2018-08-20T09:16:22Z, ten seconds after its session key was created, from external IP 139.198.18.205, and it failed with Client.UnauthorizedOperation — a genuine attempt, not a successful launch. What I do not hold is the answer itself: the Ubuntu codename for that image. Nothing checked so far names ami-41e0b93b's operating system, and the aws:description feed that would carry DescribeImages output is empty in this index. Next round: (1) CloudTrail DescribeImages responseElements, (2) per-sourcetype literal search for ami-41e0b93b (bash_history, osquery:results, cloud-init, GuardDuty, aws:config:rule), (3) web_lookup of the AMI ID as external corroboration, (4) confirm ami-41e0b93b is Ubuntu at all — if not, the first Ubuntu-targeting attempt is a later event.

## Ruled out
- aws:description as the AMI-name source — 0 events in index=botsv3 across three queries (AMI filter, AMI substring, unfiltered).
- AWSServiceRoleForAutoScaling RunInstances as the compromised user's attempts — service role, not the IAM user; the earliest RunInstances in the dataset (min _time 1534756582) is web_admin's.
- Whole-index search for ami-41e0b93b — rejected by the search tool (sourcetype filter required); the per-sourcetype pass has not been run.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The first launch attempt is the RunInstances at 2018-08-20T09:16:22Z targeting a"
