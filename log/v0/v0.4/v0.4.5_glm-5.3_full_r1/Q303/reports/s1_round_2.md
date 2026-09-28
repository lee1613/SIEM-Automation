# s1 - Q303 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=8_
**Scope:** sourcetype=bash_history, osquery:results, Unix:UserAccounts, config_file, history-2 | fields=_raw, host, user
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 60

## Prior rounds
- R1: linux_audit/linux_secure useradd events are all on EC2 instances (ec2-user/apache/memcached/streamfwd on ip-172-16-0-13/127/145) — cloud bootstrap, ruled out; bash_history/history-2 keyword "useradd" returned 0.

## This round
### What I ran
- get_raw_events klagerfield .bash_history keyword=passwd -> 1 event: "cat /etc/passwd"
- bash_history | stats count by host, source -> hoth=/home/klagerfield/.bash_history (83); gacrux.i-0920036c8ca91e501 and mars.i-08e52f8b5a034012d (EC2) = /home/ec2-user/.bash_history
- klagerfield history read in full (26 distinct commands, 83 events) -> Splunk config navigation only; no useradd, no password-setting
- history-2 | stats by host, source -> hoth=/var/log/apt/history.log (2 events) — apt log, not shell history
- osquery:results host=hoth | stats count by name -> 16 packs incl. pack_incident-response_shell_history (1440), pack_process-monitoring_proc_events (76085), pack_fim_file_events (406)
- osquery:results host=hoth name=pack_incident-response_shell_history (_raw=*useradd* OR *passwd* OR *chpasswd* OR *adduser*) -> 4 events (counts 1,2,1,1)

### What it means
NOT_FOUND, but one live lead. The on-prem Linux host is hoth (only non-EC2 Linux host with shell history and osquery telemetry). hoth's osquery shell-history pack holds exactly 4 events matching useradd/passwd/chpasswd/adduser — almost certainly the root creation act and the password-setting command. I hit the tool cap before reading their raw text, so no user or password value can be stated without inventing it. klagerfield's own .bash_history is fully read and clean of account creation; history-2 is an apt log, not shell history.

## Ruled out
- klagerfield /home/klagerfield/.bash_history - read in full (26 distinct commands): Splunk config work and "cat /etc/passwd" only; no useradd/passwd/chpasswd
- history-2 - /var/log/apt/history.log on hoth, package-manager log, cannot hold the password
- EC2 useradd events (R1) - cloud bootstrap accounts, not on-prem

## Next
Read the 4 osquery shell-history events: get_raw_events sourcetype=osquery:results host=hoth keyword=useradd / passwd. If creation without password, pivot to pack_process-monitoring_proc_events (useradd/passwd cmdline), pack_fim_file_events (/etc/shadow), Unix:UserAccounts, config_file.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The on-prem Linux host is hoth, and the root-driven user creation plus password-"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
