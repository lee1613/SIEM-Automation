# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=4_
**Scope:** sourcetype=bash_history,linux_audit,osquery:results,ps | source=/home/ec2-user/.bash_history,/var/log/audit/audit.log,/var/log/osquery/osqueryd.results.log,ps | fields=host,user,USER,process_name,process_exec,app,ARGS,command,exe,type,op,msg,bash_command,path,target_path,filename,name,cmdline
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 47

## Prior rounds
- Confirmed hoth is the impacted Linux host and tomcat8 is the compromised user.
- Saw tomcat8-associated reverse-shell behavior in ps telemetry.
- Identified the suspicious process name `colonelnew` on hoth.
- Established osquery file-integrity telemetry exists on hoth and includes file-path evidence.
- Confirmed a likely escalation artifact path: `/tmp/definitelydontinvestigatethisfile.sh`.
- Could not recover the actual line-2 text before tool access ended.

## This round
### What I ran
- `get_sourcetype_fields(sourcetype="osquery:results")` -> revealed `pack_fim_file_events`, `pack_incident-response_shell_history`, and other packs in osquery results.
- `sample_events(sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log", keyword="pack_fim_file_events")` -> showed hoth FIM entries including `/tmp/definitelydontinvestigatethisfile.sh`, `/tmp/colonelnew`, `/tmp/colonel`, `/tmp/colonel.c`.
- `index=botsv3 sourcetype=osquery:results host=hoth name=pack_fim_file_events | stats count by columns.action, columns.target_path, columns.category, decorations.username, columns.mode, columns.size | sort -count` -> 50 rows, top entries included `/tmp/backpipe`, `/tmp/loot.txt`, `/tmp/colonelnew`, `/tmp/colonel`, `/tmp/colonel.c`, and `/tmp/definitelydontinvestigatethisfile.sh`.
- `sample_events(sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log", keyword="definitelydontinvestigatethisfile.sh")` -> 3 events, including a CREATED entry at size 0 and UPDATED entry at size 21857, both by tomcat8 on hoth.
### What it means
The escalation file was very likely `/tmp/definitelydontinvestigatethisfile.sh` on hoth, authored by tomcat8. I still do not have the contents or line 2, so the requested exact line cannot be submitted yet.

## Ruled out
- `bash_history` - sampled history was routine and did not expose the file text.
- `linux_audit` - showed privilege-related activity but no filename or file contents.
- `ps` - confirmed compromise context and `colonelnew`, but not the line text.
- `osquery shell history` - I attempted to pivot, but no usable result was returned before tool access ended.

## Open questions for SH
- If another round is available, the best next scope is osquery shell-history/command-line artifacts on hoth to catch a `cat`, `sed`, `vim`, or `less` invocation on `/tmp/definitelydontinvestigatethisfile.sh`.

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
