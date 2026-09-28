# s2 - Q223 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=9_
**Scope:** sourcetypes=aws:cloudtrail, aws:cloudwatch:guardduty, aws:description (us-west-1:ec2_images), stream:http | fields=requestParameters.instancesSet.items{}.imageId, eventTime, detail.resource.instanceDetails.imageDescription, uri_path, url
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: bash_history (both feeds), cloud-init, cloud-init-output — zero ami-/Ubuntu tokens.
- R2: osquery:results (46,329 proc_events, 641 shell_history rows), history-2, out-3, localhost-5 — no aws/ec2 command lines on any Frothly host.
- R3: config_file, amazon-ssm-agent, syslog (6 feeds) — only Ubuntu tokens are hoth's own apt repos.
- R4: WinHostMon (8 feeds), Script:GetEndpointInfo closed; us-west-1:ec2_images holds only Frothly's 2 AMIs; web_lookup on the AMI ID returned nothing.

## This round
### What I ran
- RunInstances | stats min(_time) by imageId, sorted -> 16 distinct AMIs; first-attempt order established: ami-41e0b93b (1534756582 = 09:16:22Z), then ami-67973709, ami-1157157d, ami-79aeae19, ami-325d2e4e, ami-f0870294, ami-1ee65166, ami-d39a02b5, ami-37df2255, ami-2581aa40, ami-4d46d534, ami-5d055232, ami-4262d53f, ami-d7aab2b3, ami-af79ebc0 (09:28:09Z); 16th ami-0e86606d (12:48:47Z) is AutoScaling's successful launch, not the attacker's.
- GuardDuty imageDescription=* -> 1 value: "Amazon Linux AMI 2018.03.0.20180622 x86_64 HVM GP2" — not Ubuntu, and not tied to any attempted AMI.
- CloudTrail "ubuntu" (case-insensitive) -> 0 events across the whole sourcetype.
- DescribeImages events naming ami-0e86606d (bstoll, splunk_access) read raw -> responseElements: null; requests carry only the imageId, no names.
- stream:http for all 15 attacker AMI IDs and "RunInstances" -> 0 events.

### What it means
NOT_FOUND. Explicitly, as instructed: the dataset establishes only the first attempted AMI ID (ami-41e0b93b) and not any Ubuntu codename. Walking the 15 attempted AMIs in first-attempt order finds no evidence naming any of them as Ubuntu: CloudTrail carries only imageIds (DescribeImages responses are null), GuardDuty's single imageDescription is Amazon Linux, the only image feed (us-west-1:ec2_images) lists Frothly-owned AMIs only, stream:http carries none of the IDs, and 12 local artifact feeds (R1–R4) hold no aws/ec2 command lines or image names. The attacker launched from external IP 139.198.18.205, so no host-side capture names the AMIs. No value is submittable: nothing read in R1–R5 names any Ubuntu image, version, or codename.

## Ruled out
- GuardDuty imageDescription path - only value is "Amazon Linux AMI 2018.03.0.20180622 x86_64 HVM GP2".
- CloudTrail DescribeImages responses - responseElements: null; no image names recorded.
- stream:http - zero occurrences of any of the 15 attacker AMI IDs or RunInstances.
- ami-0e86606d as an attacker attempt - launched successfully by AWSServiceRoleForAutoScaling (autoscaling.amazonaws.com), not web_admin.
- aws:description us-west-1:ec2_images - Frothly-owned AMIs only (R4).
- Carried forward: 12 local feeds (R1–R4); web_lookup on the AMI ID (R4).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "ami-0e86606d", "limit": 10, "sourcetype": "aws:cloudtrail"}` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
