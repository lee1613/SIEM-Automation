# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.name, columns.cmdline
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_incident-response_shell_history" columns.username="tomcat8" | stats count by columns.command
- index=botsv3 sourquery:results host=hoth name="pack_fim_file_events" "colonel" | stats count by columns.target_path, columns.action, decorations.username
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "colonel" | stats count by columns.target_path, columns.action, decorations.username
### What it means
Intention: tomcat8 created /tmp/colonel.c and compiled it to /tmp/colonel. Now find where the file contents are recorded — check the bash_history sourcetype on hoth for the escalation commands and file content.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: This senior's current chain depends on an unsupported claim that tomcat8 created /tmp/colonel.c and compiled it to /tmp/colonel; the report shows no result establishing that premise, and another round in the same unsupported scope would just extend an unverified lead.
- Scope I owned: sourcetypes=['osquery:results', 'bash_history', 'ps', 'syslog', 'linux_audit'] sources=[] fields=['username', 'uid', 'path', 'target_path', 'cmdline', 'command', 'name', 'parent', 'cwd', '_raw']
- Rounds worked: 2/8  (iterations: 21, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat8" | stats count by sourcetype
- index=botsv3 sourcetype=bash_history "tomcat8" | stats count by host, source
- index=botsv3 sourcetype=linux_audit "tomcat8" | stats count by host
- index=botsv3 sourcetype=linux_secure "tomcat8" | stats count by host
- index=botsv3 sourcetype=osquery:results "tomcat8" | stats count by host
- index=botsv3 sourcetype=osquery:results "tomcat8" | stats count by name, action
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "colonel" | stats count by columns.target_path, columns.action, decorations.username
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_fim_file_events" "tomcat8" | stats count by columns.target_path, columns.action
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_incident-response_shell_history" "tomcat8" | stats count by columns.username, columns.command, columns.time
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_incident-response_shell_history" columns.username="tomcat8" | stats count by columns.command
- index=botsv3 sourcetype=osquery:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.name, columns.cmdline
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" "tomcat8" | stats count by columns.path
- index=botsv3 sourcetype=ostmp:results host=hoth name="pack_process-monitoring_proc_events" "tomcat8" | stats count by columns.name, columns.cmdline
- index=botsv3 sourquery:results host=hoth name="pack_fim_file_events" "colonel" | stats count by columns.target_path, columns.action, decorations.username
