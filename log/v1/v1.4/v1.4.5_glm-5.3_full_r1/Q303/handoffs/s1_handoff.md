# s1 - Q303 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=5_
**Scope:** sourcetype=osquery:results, bash_history, Unix:UserAccounts, config_file, history-2 | fields=_raw, host, user, name, columns.cmdline
**Insight:** FOUND
**Candidate:** ilovedavidverve   **Confidence:** 85

## Prior rounds
- R1: linux_audit/linux_secure useradd events all on EC2 instances (ec2-user/apache/memcached/streamfwd) — cloud bootstrap, ruled out; no password artifact found.
- R2: hoth identified as the on-prem Linux host (klagerfield's history); klagerfield .bash_history read in full — no useradd/passwd; history-2 is an apt log; 4 osquery shell-history keyword matches found but unread at cap.

## This round
### What I ran
- get_raw_events osquery:results keyword=useradd -> 2 events, both pack_process-monitoring_proc_events on hoth
- osquery:results host=hoth "tomcat7" | stats by name, decorations.username, columns.cmdline -> the same 2 events with full cmdlines
- Unix:UserAccounts host=hoth -> 0 events; feed-wide -> covers only gacrux EC2 hosts
- osquery:results host=hoth "tomcat7" in last/logged_in_users/shell_history -> 0 events
- shell_history keyword matches re-extracted -> auditctl -w /etc/passwd, ausearch -f /etc/passwd (root) — not password-setting

### What it means
FOUND. On hoth, osquery process telemetry shows two useradd executions for user tomcat7: 19:08:05 by tomcat8 (uid=111, euid=111 — non-root, would fail) with -p davidverve.com, and 19:24:54 by root (uid=0, euid=0, gid=0, egid=0): `useradd -ou tomcat7 -p ilovedavidverve 0 -g 0 -M -N -r -s /bin/bash` — a UID-0 backdoor account with a bash shell. The root-run execution is the successful creation the question names, and its -p argument is the password exactly as recorded: **ilovedavidverve**.

## Ruled out
- davidverve.com - password in the 19:08:05 useradd run by tomcat8 (uid=111, non-root); that execution could not create the account
- EC2 useradd events (ec2-user/apache/memcached/streamfwd) - cloud bootstrap, not on-prem
- klagerfield .bash_history / history-2 - read in full, no account creation or password
- Unix:UserAccounts - covers only gacrux EC2 hosts, no hoth data

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The successful creation is the 19:24:54 useradd executed by root (uid=0, euid=0,"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="Unix:UserAccounts" | stats count by host, user` (50 of 173 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['linux_audit', 'bash_history', 'osquery:results', 'syslog', 'linux_secure'] sources=[] fields=['_raw', 'host', 'user', 'exe', 'cmd', 'command', 'columns.command', 'type', 'acct', 'uid', 'auid', 'msg']
- Rounds worked: 3/3  (iterations: 33, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source="/home/klagerfield/.bash_history" | stats count by _raw | sort _raw
- index=botsv3 sourcetype="Unix:UserAccounts" host=hoth | stats count by user, uid, gid, shell
- index=botsv3 sourcetype="Unix:UserAccounts" | stats count by host, user
- index=botsv3 sourcetype=bash_history source="/home/klagerfield/.bash_history" | stats count by _raw | sort - _time | head 50
- index=botsv3 sourcetype=bash_history source="/home/klagerfield/.bash_history" | stats count by _raw | sort _raw
- index=botsv3 sourcetype=bash_history source="/home/klagerfield/.bash_history" | top limit=50 _raw
- index=botsv3 sourcetype=bash_history | stats count by host, source
- index=botsv3 sourcetype=history-2 | stats count by host, source
- index=botsv3 sourcetype=linux_audit (useradd OR adduser OR "new-user" OR "ADD_USER") | stats count by _raw | sort - count
- index=botsv3 sourcetype=linux_secure (useradd OR newuser OR "new user") | stats count by _raw
- index=botsv3 sourcetype=osquery:results host=hoth "tomcat7" | stats count by name, decorations.username, columns.cmdline
- index=botsv3 sourcetype=osquery:results host=hoth (pack_incident-response_last OR pack_incident-response_logged_in_users OR pack_incident-response_shell_history) "tomcat7" | stats count by name, _time
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (_raw="*useradd*" OR _raw="*passwd*" OR _raw="*chpasswd*" OR _raw="*adduser*") | rex field=_raw "\"command\":\"(?<command>[^\"]*)\"" | stats count by command, columns.username
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (_raw="*useradd*" OR _raw="*passwd*" OR _raw="*chpasswd*" OR _raw="*adduser*") | stats count by _raw
- index=botsv3 sourcetype=osquery:results host=hoth | stats count by name
