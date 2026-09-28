# s1 - Q308 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** sourcetype=osquery:results | source=/var/log/osquery/osqueryd.results.log | fields=cmdline, name, hostIdentifier, decorations.username, columns.* (cross-checked bash_history, linux_audit, linux_secure, Unix:UserAccounts)
**Insight:** FOUND
**Candidate:** root   **Confidence:** 60

## Prior rounds
Round 1 (this round): located the tomcat7 useradd evidence on hoth; candidate group = root (GID 0).

## This round
### What I ran
- get_source_types -> 102 sourcetypes; picked osquery:results, bash_history, linux_audit, linux_secure, Unix:UserAccounts as group-evidence candidates.
- get_sourcetype_fields Unix:UserAccounts -> /etc/passwd inventory (user, user_id, user_group_id); all 571 events dated 2018-08-20; no group-name field.
- get_raw_events bash_history keyword=tomcat7 -> 0 events; keyword=useradd -> 0 events.
- index=botsv3 sourcetype=osquery:results "tomcat7" | stats count by source, name -> 1 row, 2 events, pack_process-monitoring_proc_events on hoth.
- get_raw_events osquery:results tomcat7 -> both events read in full (see below).
- index=botsv3 sourcetype=osquery:results name="*group*" OR columns="*tomcat7*" -> only the 2 useradd events; no osquery group tables exist.
- index=botsv3 sourcetype=linux_audit "tomcat7" -> 0 events; sourcetype=linux_secure "tomcat7" -> 0 events.

### What it means
The only records showing group assignment for the Q304 user tomcat7 on hoth are two /usr/sbin/useradd process events: 2018-08-20T19:08:05+08:00 run by tomcat8 (uid 111) and 2018-08-20T19:24:54+08:00 run by root, both with cmdline `useradd -ou tomcat7 -p <password> 0 -g 0 -M -N -r -s /bin/bash` (passwords davidverve.com then ilovedavidverve). The `-g 0` flag assigns primary group GID 0 = root; `-N` means no user private group was created and no `-G` supplementary groups appear. So the evidenced group assignment is **root**. Confidence is held at 60 because the question's plural "groups" plus the comma-separated answer format leaves room for supplementary groups in feeds I could not reach before the cap.

## Ruled out
- bash_history (all hosts) - 0 events for tomcat7 and 0 for useradd.
- linux_audit - 0 events for tomcat7.
- linux_secure - 0 events for tomcat7 (no useradd/auth-log record of the account).
- osquery:results group inventory - no pack name matches *group*; columns="*tomcat7*" matches only the 2 useradd events, so no usermod/addgroup/gpasswd for tomcat7 in osquery.
- NOT yet ruled out (cap reached): ps, stream:http, stream:tcp, config_file, syslog, cloud-init-output, history-2, out-3, localhost-5; and tomcat7's user_group_id row in Unix:UserAccounts.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
