# s1 - Q308 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=Unix:UserAccounts user=tomcat7 | stats count by user, user_id, user_group_id, home, shell, host
### What it means
Intention: The Unix:UserAccounts row confirms tomcat7 on hoth with user_id=0, user_group_id=0, home=/home/tomcat7, shell=/bin/bash — corroborating the useradd -g 0. Now check for any later group-modification activity (usermod, gpasswd, addgroup, groupadd) in osquery:results on hoth, and also check config_file for /etc/group content mentioning tomcat7.


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['osquery:results', 'Unix:UserAccounts'] sources=[] fields=['columns.cmdline', 'decorations.username', 'user', 'user_id', 'user_group_id', 'home', 'shell', 'host']
- Rounds worked: 3/3  (iterations: 13, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat7" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype=linux_audit "tomcat7" | stats count by _raw | sort -count
- index=botsv3 sourcetype=linux_secure "tomcat7" | stats count by _raw | sort -count
- index=botsv3 sourcetype=osquery:results "tomcat7" | stats count by source, name | sort -count
- index=botsv3 sourcetype=osquery:results name="*group*" OR columns="*tomcat7*" | stats count by name, host | sort -count
- index=botsv3 sourcetype=Unix:UserAccounts user=tomcat7 | stats count by user, user_id, user_group_id, home, shell, host
