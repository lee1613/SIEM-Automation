# s1 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=osquery:results, stream:http | source=pack_fim_file_events, pack_process-monitoring_proc_events, pack_incident-response_shell_history | fields=columns.target_path, columns.cmdline, form_data, _raw
**Insight:** FOUND
**Candidate:** ` * Ubuntu 16.04.4 kernel priv esc`   **Confidence:** 85

## Prior rounds
- Round 1: Searched syslog, linux_audit, bash_history for tomcat8 on hoth — found nothing in syslog/linux_audit; bash_history had 4 unread keyword matches. No escalation file identified.
- Round 2 (this round): Identified the escalation file and decoded its line 2 from the Struts2 RCE command stream.

## This round
### What I ran
- osquery:results host=hoth "tomcat8" | stats count by name -> 4 packs (fim_file_events, process-monitoring, shell_history, largest_process).
- osquery:results pack_fim_file_events "tomcat8" | stats count by columns.target_path -> 7 /tmp files: colonel, colonel.c, colonelnew, definitelydontinvestigatethisfile.sh, backpipe, ccgZ61x9.o, cclBJ1WV.s.
- osquery:results pack_process-monitoring_proc_events "tomcat8" | stats count by columns.cmdline -> 39 commands showing the full escalation chain.
- stream:http host=hoth "colonel" | stats count by uri_path -> 4 POSTs to /frothlyinventory/integration/saveGangster.action.
- get_raw_events stream:http keyword=colonel -> 4 events; the echo command contains the full base64 of colonel.c.

### What it means
FOUND: The escalation chain is unambiguous from process monitoring: `echo <base64> > /tmp/colonel` → `base64 --decode /tmp/colonel > /tmp/colonel.c` → `gcc colonel.c -o colonelnew` → `chmod +x colonelnew` → `./colonelnew`. The file used to escalate tomcat8 to root is **/tmp/colonel.c**. The stream:http form_data carries the full base64 payload; decoding the first groups gives the file's comment header: line 1 = `/*`, line 2 = ` * Ubuntu 16.04.4 kernel priv esc`. This is a known Ubuntu 16.04.4 kernel privilege-escalation exploit (credits to @bleidl, -vnik).

## Ruled out
- /tmp/definitelydontinvestigatethisfile.sh - present in FIM but not in the process-monitoring escalation chain; the colonel.c compile-and-execute chain is the actual escalation.
- /tmp/colonel (base64 file) - intermediate transport, not the escalation source itself.
- /tmp/backpipe - named pipe for the reverse shell to 45.77.53.176:8088, not the escalation file.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
