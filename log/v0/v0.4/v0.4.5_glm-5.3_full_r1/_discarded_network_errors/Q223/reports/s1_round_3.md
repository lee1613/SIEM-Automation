# s1 - Q223 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=8_
**Scope:** index=botsv3 sourcetypes=aws:cloudtrail, aws:config:rule, aws:cloudwatch:guardduty, cloud-init, cloud-init-output, bash_history, osquery:results, aws:elb:accesslogs, aws:s3:accesslogs | fields eventName, eventTime, imageId, responseElements, userIdentity.userName, errorCode, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: first web_admin RunInstances attempt = ami-41e0b93b, 2018-08-20T09:16:22Z, failed; aws:description feed empty; codename unresolved.
- R2: all 576 attempts failed (4 error codes, zero successes); every in-dataset AMI-naming feed empty; submitted external guess "Xenial Xerus" at confidence 40.
- R3: verified leaked-key→session-key→attempt chain; ordered all 15 attempted AMIs; fleet image ami-0e86606d disjoint from attacker set; still no artifact naming the AMI's OS.

## This round
### What I ran
- `eventName=RunInstances userIdentity.userName=web_admin | stats ... by _time, imageId | sort _time | head 3` → first attempt 2018-08-20T17:16:22+08:00 on ami-41e0b93b, key ASIAZB6TMXZ7LL6JBJQA, arn web_admin, errorCode Client.InstanceLimitExceeded.
- get_raw_events keyword=GetSessionToken → 1 event: 09:16:12Z, leaked key AKIAJOGCDXJ5NW5PXUPA (web_admin) minted session key ASIAZB6TMXZ7LL6JBJQA — the key used for the attempts 10s later.
- `eventName=RunInstances userIdentity.type=AssumedRole | stats ... by sessionIssuer.userName` → AWSServiceRoleForAutoScaling, 6 launches, us-west-1, ami-0e86606d, 7 instance IDs — fleet image NOT among the attacker's 15 AMIs.
- `eventName=RunInstances userIdentity.userName=web_admin | stats min(_time) count by imageId | sort min(_time)` → 15 AMIs, first-use order: ami-41e0b93b (1534756582), ami-67973709, ami-1157157d, then 12 more through ami-af79ebc0.
- `sourcetype=cloud-init-output "ami-41e0b93b"` → 0 events; `osquery:results "ubuntu"` → 6 rows, all scheduler metadata (apt_sources packs, output_size 0, no source rows; host runs as ec2-user).

### What it means
NOT_FOUND, per SH's instruction. Result-backed statement: the dataset identifies the first attempted AMI only by imageId — ami-41e0b93b, first attempted 2018-08-20T09:16:22Z by the compromised IAM user web_admin (leaked key AKIAJOGCDXJ5NW5PXUPA → GetSessionToken → session key ASIAZB6TMXZ7LL6JBJQA → 576 failed RunInstances attempts) — and does not expose its Ubuntu codename. Every feed that could name that AMI's OS was queried and is empty: aws:description (0 events index-wide), DescribeImages responseElements (null in all 31), bash_history (no "ami-" strings), osquery:results / cloud-init / cloud-init-output / aws:config:rule / aws:cloudwatch:guardduty (0 hits each). The fleet's ami-0e86606d is disjoint from the attacker's AMIs, so no fleet instance's boot logs can name an attacker image's OS. The only remaining path is external identification of the AMI ID, which SH directed me not to rely on; the external candidate (Ubuntu 16.04, "Xenial Xerus") is recorded in notes, unsubmitted.

## Ruled out
- aws:description — 0 events in the entire index.
- CloudTrail DescribeImages responseElements — null in all 31 events.
- bash_history, osquery:results, cloud-init, cloud-init-output, aws:config:rule, aws:cloudwatch:guardduty — 0 hits for ami-41e0b93b.
- osquery apt_sources as an OS-release source — scheduler metadata only, output_size 0, no source rows.
- Fleet-instance cloud-init as an AMI-OS source — fleet runs ami-0e86606d, not among the attacker's 15 AMIs.
- Any successful launch by web_admin — all 576 attempts carry an errorCode.
- External identification as the submitted answer — barred by SH's instruction this round; no in-dataset artifact points to it.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
