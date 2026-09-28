# s1 - Q308 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=Unix:UserAccounts user=tomcat7 | stats count by user, user_id, user_group_id, home, shell, host
### What it means
Intention: The Unix:UserAccounts row confirms tomcat7 on hoth with user_id=0, user_group_id=0, home=/home/tomcat7, shell=/bin/bash — corroborating the useradd -g 0. Now check for any later group-modification activity (usermod, gpasswd, addgroup, groupadd) in osquery:results on hoth, and also check config_file for /etc/group content mentioning tomcat7.
