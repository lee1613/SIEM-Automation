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

## What I'd tell my replacement
- Retired because: This senior established the likely escalation script on hoth as `/tmp/definitelydontinvestigatethisfile.sh` and exhausted the available Linux process/history/FIM path without recovering line 2. Handoff: preserve hoth, tomcat8, suspicious `colonelnew`, and the likely escalation file path for a new evidence family.
- Scope I owned: sourcetypes=['osquery:results', 'bash_history', 'linux_audit', 'syslog', 'lsof', 'ps'] sources=[] fields=['host', 'name', 'path', 'columns.path', 'columns.target_path', 'columns.content', 'columns.cmdline', 'cmdline', 'process', 'process_name', 'parent', 'uid', 'euid', 'user', 'message', '_raw']
- Rounds worked: 4/8  (iterations: 29, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=linux_audit (tomcat8 OR tomcat* OR sudo OR su OR chmod OR chown OR setuid OR setcap OR pwnkit OR pkexec) | stats count by host, user_name, command, exe, type, op, msg | sort -count
- index=botsv3 sourcetype=linux_audit host=hoth ("definitelydontinvestigatethisfile.sh" OR "colonelnew" OR "/tmp/colonelnew" OR "/tmp/colonel" OR "/tmp/definitelydontinvestigatethisfile.sh") | stats count by type, op, command, exe, user_name, msg | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth ("/tmp/definitelydontinvestigatethisfile.sh" OR "definitelydontinvestigatethisfile.sh") | stats count by name, columns.action, columns.target_path, columns.command, columns.path, columns.cmdline, decorations.username | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth (tomcat8 OR colonelnew OR bash OR sh OR sudo OR root) | stats count by name, action, columns.path, columns.cmdline, columns.name, columns.target_path, columns.filename, columns.uid, columns.gid, decorations.username | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events | stats count by columns.action, columns.target_path, columns.category, decorations.username, columns.mode, columns.size | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history ("definitelydontinvestigatethisfile.sh" OR "/tmp/definitelydontinvestigatethisfile.sh" OR cat OR sed OR vim OR vi OR less OR more OR grep OR nano) | stats count by decorations.username, columns.command, columns.cmdline, columns.path, columns.target_path, columns.action | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (columns.command="*/tmp/definitelydontinvestigatethisfile.sh*" OR columns.command="*definitelydontinvestigatethisfile.sh*" OR columns.command="*cat*" OR columns.command="*sed*" OR columns.command="*vi *" OR columns.command="*vim *" OR columns.command="*less *" OR columns.command="*more *" OR columns.command="*cp *" OR columns.command="*>*" OR columns.command="*tee*") | stats count by decorations.username, columns.command, columns.directory, columns.history_file, columns.shell | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history (columns.command="*definitelydontinvestigatethisfile.sh*" OR columns.command="*colonelnew*" OR columns.command="*cat*" OR columns.command="*sed*" OR columns.command="*vim*" OR columns.command="*nano*" OR columns.command="*less*" OR columns.command="*more*" OR columns.command="*grep*") | stats count by decorations.username, columns.command, columns.directory, columns.history_file, columns.shell | sort -count
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history | stats count by decorations.username, columns.command, columns.cmdline, columns.path, columns.target_path | sort -count
- index=botsv3 sourcetype=ps (COMMAND=tomcat8 OR process_name=tomcat8 OR process_exec=tomcat8 OR app=tomcat8 OR process=tomcat8 OR USER=tomcat8 OR user=tomcat8 OR process_name=sh OR process_exec=sh) | stats count by host, USER, process_name, process_exec, app, ARGS | sort -count
- index=botsv3 sourcetype=ps host=hoth ("definitelydontinvestigatethisfile.sh" OR "colonelnew" OR "tomcat8" OR "vim" OR "vi" OR "cat" OR "sed" OR "cp" OR "gcc" OR "sh -c") | stats count by USER, process_name, process_exec, app, ARGS | sort -count
