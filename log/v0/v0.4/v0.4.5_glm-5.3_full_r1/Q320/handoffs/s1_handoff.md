# s1 - Q320 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=3_
**Scope:** sourcetype=stream:http, syslog | source=/var/log/auth.log | fields=form_data, _raw, rce_cmd, host
**Insight:** FOUND
**Candidate:** davidverve.com   **Confidence:** 95

## Prior rounds
- Round 1: osquery:results (0 "useradd" feed-wide) and Unix:UserAccounts (hoth absent) ruled out; premise value ilovedavidverve carried unverified.
- Round 2: found the Struts2 RCE POST on hoth carrying `useradd ... tomcat7 -p davidverve.com`; auth.log confirmed creation; refuted ilovedavidverve.

## This round
### What I ran
- `stream:http host=hoth | rex #cmd='...' | stats count by rce_cmd` -> 15 commands, all returned; exactly one useradd, no passwd/chpasswd/usermod/userdel.
- Full RCE event re-read -> POST /frothlyinventory/integration/saveGangster.action, 2018-08-20T19:07:04+08:00, src 192.168.8.103, status 200, `#cmd='useradd -ou 0 -g 0 -M -N -r -s /bin/bash  tomcat7 -p davidverve.com'`.
- hoth auth.log user-management scan -> 3 events: 2 benign klagerfield SSH logins + the creation.
- auth.log "new user" -> `Aug 20 11:24:44 hoth useradd[12815]: new user: name=tomcat7, UID=0, GID=0, home=/home/tomcat7, shell=/bin/bash`.
- hoth osquery shell_history user-management terms -> 2 benign commands (auditctl, splunk --seed-passwd).

### What it means
FOUND. The user-creation act on hoth is the Struts2 RCE POST whose command line literally carries `-p davidverve.com`; hoth's auth.log confirms the account was created (tomcat7, UID=0). The complete web-shell inventory (15 commands, all read) contains no passwd/chpasswd/usermod, and hoth's auth.log and shell history show no later password change. The literal password exactly as recorded is **davidverve.com**.

## Ruled out
- Any later password change on hoth - full 15-command web-shell inventory, 3-event auth.log scan, and shell-history scan all negative.
- ilovedavidverve (premise p2, already REFUTED) - the actual command carries `-p davidverve.com`.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['osquery:results', 'Unix:UserAccounts'] sources=['/var/log/osquery/osqueryd.results.log'] fields=['columns.cmdline', 'decorations.username', 'columns.path', 'columns.pid', 'unixTime', 'user', 'user_id', 'user_group_id', 'host', 'home', 'shell']
- Rounds worked: 3/5  (iterations: 28, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "useradd" | stats count by sourcetype, source
- index=botsv3 sourcetype=linux_secure "useradd" | stats count by host, _raw
- index=botsv3 sourcetype=osquery:results "useradd" | stats count by host, name, columns.cmdline, columns.username, columns.pid
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history ("passwd" OR "adduser" OR "chpasswd") | stats count by columns.command, columns.username, columns.history_file
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history ("usermod" OR "chpasswd" OR "passwd " OR "useradd" OR "adduser") | stats count by columns.command, columns.username
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_process-monitoring_proc_events "useradd" | stats count by columns.cmdline, columns.username, columns.parent, columns.path
- index=botsv3 sourcetype=osquery:results host=hoth | stats count by name
- index=botsv3 sourcetype=stream:http "tomcat7" | stats count by http_method, uri_path, form_data
- index=botsv3 sourcetype=stream:http "useradd" | stats count by host, src_ip, http_method, uri_path
- index=botsv3 sourcetype=stream:http host=hoth | rex field=form_data "#cmd='(?<rce_cmd>[^']*)" | stats count by rce_cmd
- index=botsv3 sourcetype=syslog source="/var/log/auth.log" host=hoth ("tomcat7" OR "useradd" OR "new user" OR "passwd" OR "chpasswd") | stats count by _raw
- index=botsv3 sourcetype=syslog source="/var/log/auth.log" host=hoth ("usermod" OR "chpasswd" OR "passwd" OR "userdel" OR "new user" OR "password") | stats count by _raw
- index=botsv3 sourcetype=Unix:UserAccounts host=hoth | stats count by user, group, host
- index=botsv3 sourcetype=Unix:UserAccounts | stats count by host, user
