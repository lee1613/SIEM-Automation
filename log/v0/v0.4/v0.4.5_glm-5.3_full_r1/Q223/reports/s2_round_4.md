# s2 - Q223 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Scope:** sourcetypes=WinHostMon, Script:GetEndpointInfo (both closed this round); cross-checks: aws:description/us-west-1:ec2_images, osquery:results | fields=_raw, host, Name, OS, Description, ComputerName
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: bash_history (both feeds), cloud-init, cloud-init-output — zero ami-/Ubuntu tokens.
- R2: osquery:results (46,329 proc_events, 641 shell_history rows), history-2, out-3, localhost-5 — no aws/ec2 command lines on any Frothly host.
- R3: config_file, amazon-ssm-agent, syslog (6 feeds) — only Ubuntu tokens are hoth's own apt repos.
- Established: first attempt ami-41e0b93b, 2018-08-20T09:16:22Z, web_admin/ASIAZB6TMXZ7LL6JBJQA from 139.198.18.205; 15 AMIs, all denied.

## This round
### What I ran
- WinHostMon ("ami-" OR "Ubuntu" OR "ubuntu" OR "run-instances" OR "ec2") -> 0 events; get_sources -> 8 feeds (service 52,774; driver 40,972; process 32,260; networkadapter 2,652; disk 410; computer 204; operatingsystem 204; processor 203); the unscoped token search covered all 8.
- Script:GetEndpointInfo same tokens -> 0 events; 1 feed, all 3 events read in full -> endpoint IP/MAC/geo for FYODOR-L, ABUNGST-L, BTUN-L only.
- web_lookup "ami-41e0b93b AWS AMI Ubuntu version" and "\"ami-41e0b93b\" us-west-1 Ubuntu AMI" -> no result snippets, twice.
- get_sources aws:description -> 21 feeds incl. us-west-1:ec2_images (14 events); all 14 read in full -> only ami-071fdb5b695e37666 (FrothlyWebServerAMI) and ami-055313c50737a491a (FrothlyWeb), both owner 622676721278; no ami-41e0b93b, no Ubuntu image.
- osquery shell_history "Ubuntu" -> 3 events: hoth root's Splunk_TA_nix directory names and apt-key keyserver.ubuntu.com — not image names.

### What it means
NOT_FOUND. The local-artifact wall is closed: no local artifact in my current scope names ami-41e0b93b, any of the 15 attempted AMIs, or any Ubuntu codename. WinHostMon and Script:GetEndpointInfo were the last two in-scope feeds and neither can plausibly carry AMI identity (Windows inventory/network data; the launches came from external IP 139.198.18.205). Structural finding: the dataset's only image feed (us-west-1:ec2_images) is scoped to Frothly-owned images, and ami-41e0b93b is not among them — so no Frothly feed ever names or describes that AMI. External identification via web_lookup also returned nothing. Remaining paths, all outside my current scope: the ordered list of 15 attempted AMIs from the retired CloudTrail scope (to walk first-attempt order), aws:cloudwatchlogs / WinEventLog PowerShell history / bootstrap / dmesg / dpkg / package / Unix:Version, or a differently-phrased external AMI lookup. No value is submittable: nothing read in R1–R4 names any Ubuntu image or codename.

## Ruled out
- WinHostMon (8 feeds, token search across all) - zero ami-/Ubuntu/ec2 tokens.
- Script:GetEndpointInfo (3 events read in full) - endpoint IP/MAC/geo only.
- aws:description us-west-1:ec2_images (14 events read in full) - Frothly-owned AMIs only; ami-41e0b93b absent.
- web_lookup on the AMI ID (two phrasings) - no result snippets.
- osquery shell_history "Ubuntu" matches - Splunk TA directory names and apt-key server, not image names.
- Carried forward: bash_history, cloud-init, cloud-init-output (R1); osquery:results, history-2, out-3, localhost-5 (R2); config_file, amazon-ssm-agent, syslog (R3); CloudTrail, GuardDuty, stream:http (retired scope).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
