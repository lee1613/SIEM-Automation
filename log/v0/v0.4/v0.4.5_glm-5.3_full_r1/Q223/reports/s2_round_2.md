# s2 - Q223 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=6_
**Scope:** sourcetypes=osquery:results, history-2, out-3, localhost-5 (searched); WinHostMon, Script:GetEndpointInfo, amazon-ssm-agent, syslog, config_file (in scope, unsearched) | fields=_raw, name, columns.command, columns.username, host
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: bash_history (both feeds, 100 events), cloud-init, cloud-init-output eliminated — no "ami-"/"Ubuntu" tokens. Retired scope: CloudTrail/GuardDuty/aws:description/stream:http carry no codename; established ami-41e0b93b first attempt 2018-08-20T09:16:22Z by web_admin (ASIAZB6TMXZ7LL6JBJQA, 139.198.18.205), 15 AMIs all denied.

## This round
### What I ran
- index=botsv3 sourcetype=osquery:results "ami-" -> 0 events (spans all osquery queries, incl. 46,329 proc_events rows and 641 shell_history rows).
- sourcetype=osquery:results ("run-instances" OR "ec2" OR "Ubuntu") | stats count by name -> 15 query names (shell_history, proc_events, process_env, system_profile among them).
- name="pack_incident-response_shell_history" | stats count by host, columns.command -> 641 rows, 50 returned; narrowed with aws/ec2/ami/instance filter -> 2 rows: "whoami" (klagerfield@hoth) and root's add-apt-repository line ".../osquery-packages.s3.amazonaws.com/xenial xenial main".
- get_sources history-2 -> /var/log/apt/history.log; both events read -> apt-get install netcat (2018-08-20 11:26 UTC); no AMI data.
- get_sources out-3 -> catalina.out; "Ubuntu"/"ami-" -> 0. get_sources localhost-5 -> tomcat localhost.2018-07-25.log; "Ubuntu"/"ami-" -> 0.

### What it means
NOT_FOUND. No process, shell-history, or package artifact records any AMI ID or Ubuntu image name. The attacker's RunInstances calls came from external IP 139.198.18.205, and no Frothly host shows an aws/ec2 command line — so command-capture feeds are unlikely to name the AMIs at all. The single "xenial" token in scope is the osquery package repository configured on host hoth: it evidences hoth's own OS (Ubuntu 16.04), not the adversary's attempted AMI, and cannot answer the question. Five in-scope feeds remain unsearched — config_file is the highest-value next target (file contents could hold copied AMI names or a launch script), then amazon-ssm-agent, syslog, WinHostMon, Script:GetEndpointInfo. No value is submittable: no record read in R1 or R2 names any Ubuntu image or codename.

## Ruled out
- osquery:results, entire sourcetype - "ami-" -> 0 events; shell_history aws/ec2/ami filter -> only "whoami" and the osquery apt-repo line.
- history-2 (/var/log/apt/history.log, 2 events read in full) - netcat install only.
- out-3 (catalina.out), localhost-5 (tomcat localhost log) - zero Ubuntu/AMI tokens.
- "xenial" on hoth as the answer - names the osquery package repo distro for hoth's own OS, not the attempted AMI.
- Carried forward: bash_history, cloud-init, cloud-init-output (R1); CloudTrail, GuardDuty, aws:description, stream:http (retired scope).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=osquery:results name="pack_incident-response_shell_history" | stat…` (50 of 641 rows seen). A claim resting on them alone is UNVERIFIED._
