# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=osquery:results,bash_history,linux_audit,ps | source=/var/log/osquery/osqueryd.results.log,/home/ec2-user/.bash_history,/var/log/audit/audit.log,ps | fields=host,name,cmdline,columns.target_path,columns.path,columns.command,columns.action,decorations.username,bash_command,command,exe,msg
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 44

## Prior rounds
- Confirmed hoth and tomcat8 as the compromised Linux endpoint/user.
- Identified `colonelnew` as a suspicious process on hoth.
- Established a likely escalation script path: `/tmp/definitelydontinvestigatethisfile.sh`.
- Confirmed via FIM that the file was created/updated by tomcat8 on hoth.
- Found shell-history evidence of file interactions, including editing ` /etc/tomcat8/tomcat-users.xml`.
- Still no artifact exposing line 2 of the escalation script.

## This round
### What I ran
- `index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (columns.command="*definitelydontinvestigatethisfile.sh*" OR columns.command="*cat*" OR columns.command="*sed*" OR columns.command="*vim*" OR columns.command="*nano*" OR columns.command="*less*" OR columns.command="*more*" OR columns.command="*grep*") | stats count by decorations.username, columns.command, columns.directory, columns.history_file, columns.shell | sort -count` -> 50 rows; highlighted root/klagerfield commands including `vi /etc/tomcat8/tomcat-users.xml`, `cat /var/log/audit/audit.log`, `less /var/log/audit/audit.log`, and `more fims.conf`.
### What it means
Shell history proves file interaction on hoth but still does not expose the target script contents. No direct preview, print, or edit command for `/tmp/definitelydontinvestigatethisfile.sh` has been recovered yet, so the exact line 2 remains unavailable.

## Ruled out
- Direct bash_history content from ec2-user - irrelevant to the target script.
- linux_audit - useful for activity context, not for file text.
- ps - confirms the compromise but not the script contents.
- osquery shell history - file interaction exists, but not the target file text.

## Open questions for SH
- If another round is available, the next best scope is a command-line artifact on hoth specifically referencing `/tmp/definitelydontinvestigatethisfile.sh` or a content-bearing preview such as `cat`, `sed -n`, or editor recovery logs tied to that exact path.