# s1 - Q303 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=2_
**Scope:** sourcetype=linux_audit, linux_secure, bash_history, history-2 | fields=_raw, host, user
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 75

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_source_types / get_sources -> linux_audit = /var/log/audit/audit.log (112 evts); bash_history = /home/klagerfield/.bash_history (83) + /home/ec2-user/.bash_history (17)
- sourcetype=linux_audit (useradd OR adduser OR "new-user" OR "ADD_USER") -> 27 events
- get_raw_events linux_audit keyword=useradd (20 read) -> all uid=0 (root), hosts are EC2 instances; users: ec2-user (UID 500), apache (48), memcached (498), streamfwd (497)
- get_raw_events bash_history keyword=useradd -> 0 events
- get_raw_events history-2 keyword=useradd -> 0 events
- linux_secure useradd search -> 24 events; get_raw_events linux_secure keyword=useradd (20 read) -> hosts ip-172-16-0-13, ip-172-16-0-127, ip-172-16-0-145, same four users

### What it means
NOT_FOUND. Every useradd record I can read is on AWS EC2 instances (ip-172-16-0-x, creating the AWS-specific ec2-user plus service accounts apache/memcached/streamfwd during instance bootstrap). None of that is an on-prem Linux host, so it does not answer the question, and no password artifact has been located. The on-prem creation act and its password are still unsearched in the most likely places: klagerfield's 83-event bash_history (only a keyword search for "useradd" was run against it — passwd/chpasswd/echo user:pass variants were not), osquery:results, Unix:UserAccounts, config_file (/etc/passwd, /etc/shadow), and stream:http command telemetry.

## Ruled out
- linux_audit + linux_secure useradd events (ec2-user, apache, memcached, streamfwd on ip-172-16-0-13/127/145) - cloud EC2 bootstrap account creation, not on-prem; ec2-user is AWS-specific
- bash_history / history-2 keyword "useradd" - 0 events (keyword-level only; full histories not yet read)

## Next
Read /home/klagerfield/.bash_history in full (83 events) for useradd/passwd/chpasswd; search passwd|chpasswd index-wide; check osquery:results, Unix:UserAccounts, config_file for /etc/shadow; identify the on-prem Linux host.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
