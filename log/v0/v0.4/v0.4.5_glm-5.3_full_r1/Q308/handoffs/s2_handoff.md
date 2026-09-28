# s2 - Q308 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=bash_history "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=linux_audit "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=linux_secure "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=osquery:results hostIdentifier=hoth (cmdline="*usermod*" OR cmdline="*gpasswd*" OR cmdline="*groupadd*" OR cmdline="*addgroup*" OR cmdline="*groupmod*") | stats count by name, cmdline
### What it means
Intention: Check the osquery:results feed for any group-membership table (e.g. "groups" query) on hoth that might show tomcat7's group memberships, and also check the Unix:UserAccounts feed for tomcat7.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['osquery:results', 'Unix:UserAccounts', 'config_file'] sources=[] fields=['columns.cmdline', 'decorations.username', 'user', 'user_id', 'user_group_id', 'home', 'shell', '_raw']
- Rounds worked: 1/3  (iterations: 10, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat7" | stats count by sourcetype, source
- index=botsv3 sourcetype=bash_history "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=linux_audit "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=linux_secure "tomcat7" | stats count by source, host
- index=botsv3 sourcetype=osquery:results "tomcat7" | stats count by source, name
- index=botsv3 sourcetype=osquery:results hostIdentifier=hoth (cmdline="*usermod*" OR cmdline="*gpasswd*" OR cmdline="*groupadd*" OR cmdline="*addgroup*" OR cmdline="*groupmod*") | stats count by name, cmdline
