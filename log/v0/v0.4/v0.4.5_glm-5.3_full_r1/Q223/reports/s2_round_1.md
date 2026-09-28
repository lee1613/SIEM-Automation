# s2 - Q223 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** sourcetype=bash_history, cloud-init, cloud-init-output | source=/home/klagerfield/.bash_history, /home/ec2-user/.bash_history | fields=_raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Retired scope (prior worker): CloudTrail/GuardDuty/aws:description/stream:http do not expose the AMI codename. Established: first RunInstances attempt ami-41e0b93b at 2018-08-20T09:16:22Z by web_admin (ASIAZB6TMXZ7LL6JBJQA, 139.198.18.205); 15 AMIs attempted, all denied.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; local-artifact candidates: bash_history, cloud-init, cloud-init-output, history-2, out-3, localhost-5, config_file, bootstrap, osquery:results, WinHostMon, Script:GetEndpointInfo, amazon-ssm-agent, syslog, dmesg, dpkg, package, Unix:Version.
- get_sources sourcetype=bash_history -> 2 feeds: /home/klagerfield/.bash_history (83 events), /home/ec2-user/.bash_history (17 events).
- get_raw_events /home/klagerfield/.bash_history (first 20 of 83) -> Splunk forwarder config commands only.
- get_raw_events keyword="aws" on /home/klagerfield/.bash_history -> 0 events (keyword search spans all 83 lines).
- get_raw_events /home/ec2-user/.bash_history (all 17) -> s3-upload.py to frothlywebcode, pip install boto3, cd AWS_SCENARIOS; no EC2/AMI commands.
- index=botsv3 sourcetype=bash_history "ami-" -> 0 events.
- index=botsv3 sourcetype=cloud-init-output "Ubuntu" -> 0 events.
- index=botsv3 sourcetype=cloud-init "Ubuntu" -> 0 events.

### What it means
NOT_FOUND. No shell-history or cloud-init artifact names any AMI or Ubuntu image, so the codename is not in the first local-artifact feeds checked. Tools were withdrawn before the sweep finished: osquery:results (process/cmdline capture — the most likely place an attacker-run `aws ec2 run-instances` command line would land), history-2, out-3, localhost-5, config_file, bootstrap, amazon-ssm-agent, syslog, dmesg, dpkg/package, Unix:Version, WinHostMon, Script:GetEndpointInfo, and Windows PowerShell/console history are all unsearched and are the next scope. The question's wording implies the first attempt (ami-41e0b93b) is itself the Ubuntu image; if it is not, the 15 attempted AMIs must be walked in first-attempt order to the first Ubuntu one. No value is submittable yet — no record read this round names any Ubuntu image or codename.

## Ruled out
- bash_history (both feeds, all 100 events) - no "ami-" token anywhere in the sourcetype; klagerfield's file has no aws commands; ec2-user's file is S3-upload work only.
- cloud-init, cloud-init-output - zero "Ubuntu" mentions.
- aws:cloudtrail, aws:cloudwatch:guardduty, aws:description, stream:http - retired scope per SH; not rebuilt on.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
