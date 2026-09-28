# s1 - Q328 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=osquery:results,linux_audit,ps,bash_history | source=/var/log/osquery/osqueryd.results.log,/var/log/audit/audit.log,ps,/home/ec2-user/.bash_history | fields=host,name,cmdline,columns.target_path,columns.path,columns.command,columns.action,decorations.username,bash_command,command,exe,msg
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 52

## Prior rounds
- Established hoth/tomcat8 as the compromise context.
- Identified `/tmp/definitelydontinvestigatethisfile.sh` as the likely escalation script via osquery FIM.
- Confirmed tomcat8 reverse-shell and `colonelnew` process activity in ps telemetry.
- Found shell-history evidence of file interactions, including editing `/etc/tomcat8/tomcat-users.xml`.
- Searched for exact-path and content-bearing commands in shell history without finding the target script text.
- No artifact in the narrowed scope exposed line 2 of the script.

## This round
### What I ran
- `index=botsv3 sourcetype=osquery:results host=hoth ("/tmp/definitelydontinvestigatethisfile.sh" OR "definitelydontinvestigatethisfile.sh") | stats count by name, columns.action, columns.target_path, columns.command, columns.path, columns.cmdline, decorations.username | sort -count` -> 0 results.
- `sample_events(sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log", keyword="definitelydontinvestigatethisfile.sh", count=10)` -> 3 FIM events; created then updated by tomcat8.
- `index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (...) | stats count by decorations.username, columns.command, columns.directory, columns.history_file, columns.shell | sort -count` -> 50 rows; commands referenced other files but not the target script.
- `index=botsv3 sourcetype=ps host=hoth (...) | stats count by USER, process_name, process_exec, app, ARGS | sort -count` -> 5 rows; showed tomcat8 reverse-shell and `colonelnew`, but no file text.
### What it means
The file path is still the best-supported escalation artifact, but within the requested scope I did not recover a printed excerpt, editor session, redirect, or other content-bearing log for `/tmp/definitelydontinvestigatethisfile.sh`. Therefore the exact line 2 text is still unavailable.

## Ruled out
- `linux_audit` - no direct file-content evidence.
- `ps` - process context only, no file body.
- `bash_history` - target file not present in sampled history.
- `osquery shell history` - no exact-path content artifact found.

## Open questions for SH
- If another round is possible, we should pivot to any other hoth telemetry outside this narrowed scope that may preserve file contents, such as file previews or editor recovery artifacts.