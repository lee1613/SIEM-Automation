# Q328 — SH <-> Senior conversation

### 19:17:08 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'bash_history', 'ps', 'lsof', 'linux_audit', 'syslog', 'access_combined'] sources=- fields=['cmdline', 'path', 'name', 'uid', 'euid', 'pid', 'parent', 'cwd', '_raw']
**Technique:** senior
**Reason:** This question is about a local privilege-escalation artifact and file contents, so the senior should own Linux endpoint/process/file telemetry where command history, file access, and script content may appear.

Determine how tomcat8 escalated privileges to root on Frothly systems, identify the specific file used in that escalation, and report the exact text displayed on line 2 of that file. Establish the host, process or script chain that ties tomcat8 to the file, then read the file contents from available endpoint telemetry rather than inferring from naming alone.

### 19:19:30 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> What I learned (no candidate value found): Host "hoth" is the Tomcat server — 595 ps events match "tomcat", all on hoth; the ps rows themselves were not yet read (result truncated at 50 of 595), so the tomcat8 process command line, PID, and parent are still unknown. klagerfield's bash_history contai
_full: reports/s1_round_1.md_

### 19:19:36 - SH -> s1   [COMMAND]
SH's answers to your open questions:
1. Prioritize reading the tomcat process details first, then pivot into osquery and other host-local file telemetry on hoth using the exact executable path, user context, parent/child clues, and any referenced script or file names you uncover.
2. Assume local-disk artifact first, not an uploaded web payload, until host telemetry says otherwise. Use stream:http only if the host-side chain points to a file delivered through the web server rather than created or modified locally.

**continue** — The case needs the escalation chain tied to a concrete file before file contents matter. ps is the shortest route to the exact tomcat8 execution context on hoth, and then host-local file/process feeds can prove which file was used and where its contents can be read.
**New scope:** sourcetypes=['ps', 'osquery:results', 'lsof', 'bash_history', 'history-2', 'config_file'] sources=[] fields=['host', 'user', 'process', 'cmdline', 'path', 'cwd', 'parent', 'pid', '_raw']

Work only on host hoth and establish the local privilege-escalation chain from tomcat8 to root. First, fully read the tomcat-related ps/process evidence to identify the running command line, user, executable path, working directory, parent/child behavior, and any script or file references tied to tomcat8. Then pivot on those concrete paths, process names, users, and directories into host-local telemetry that can show file creation, modification, open-file use, or captured file contents: osquery:results, lsof, history-2, bash_history, config_file if present, and any other endpoint feed already in your scope that can expose script text or file lines. If you find multiple candidate files, establish which one was actually used to escalate privileges to root, not merely present on disk, and then report the exact contents of line 2 from the telemetry that shows the file text.

### 19:24:17 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> ESCALATION CHAIN ESTABLISHED (host hoth, all times UTC 2018-08-20, actor tomcat8 uid 111, osquery decorations.username=tomcat8): 11:08-11:09 /tmp/colonel written (base64 transport, 7701 bytes, md5 ed52a04285a94f503d3fa37d0243d06b, sha256 ba42b279f26adebbf8f0ec8230b0c70889ddd81f7841186d78e27e3a8d8600
_full: reports/s1_round_2.md_

### 19:24:25 - SH -> s1   [COMMAND]
SH's answers to your open questions:
1. Yes: search beyond host=hoth and look for the web interaction or any captured content that shows either the base64 body for /tmp/colonel or the displayed contents of /tmp/colonel.c. Prioritize feeds that can carry request or response bodies or uploaded content, but keep the search anchored on the established names, sizes, hashes, timestamps, tomcat8, and hoth so you are proving this chain rather than chasing generic web traffic.
2. Treat /tmp/colonel.c as the leading candidate because it is the text file directly compiled into the executed exploit, but do not assume it yet. Establish which artifact the question calls 'the file used to escalate tomcat8's permissions to root' by showing whether the telemetry ties execution to the compiled source file, the uploaded base64 container, or another file in the same chain.

**continue** — The case now has the local escalation chain, but not the file text the question asks for. We need proof of which artifact is the operative 'file' and a feed that actually exposes its contents.
**New scope:** sourcetypes=['ps', 'osquery:results', 'lsof', 'bash_history', 'history-2', 'config_file', 'stream:http', 'stream:tcp', 'stream:smtp'] sources=[] fields=['host', 'user', 'process', 'cmdline', 'path', 'pid', '_raw', 'uri', 'method', 'status', 'src', 'dest']

Keep the investigation anchored to host hoth, user tomcat8, PID 1313 context, and the colonel/colonel.c/colonelnew chain already established. First, prove which artifact in that chain is the file 'used to escalate tomcat8's permissions to root' by tying execution and transformation steps together: uploaded/created object, decoded source, compiled binary, executed binary. Then search only for telemetry that can expose file text or displayed content for those exact artifacts and adjacent commands, including broader stream:http without the host filter, any mail/content-transfer feeds, and any endpoint feed that may capture command output, file reads, or echoed source text. Use the known filenames, sizes, hashes, timestamps, user tomcat8, gcc activity, cat activity, and /tmp paths as anchors. If you recover text for more than one candidate artifact, report line 2 for each and state which one the execution chain shows is the file named by the question; otherwise report the single line 2 once proven.

### 19:27:36 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> NO VALUE RECOVERED — line 2 text not yet read from telemetry. FULLY VERIFIED CHAIN (host hoth, actor tomcat8 uid 111, times UTC 2018-08-20): Struts2 OGNL RCE via POST /frothlyinventory/integration/saveGangster.action (192.168.9.30:8080) from 192.168.8.103 with python-requests/2.18.4, form_data name=
_full: reports/s1_round_3.md_

### 19:27:41 - SH -> s1   [COMMAND]
SH's answers to your open questions:
1. Yes. Read the raw saveGangster.action transaction at 2018-08-20T11:11:27 UTC first for the displayed source text, and use the 2018-08-20T11:08:37 request body only as fallback if the response does not expose the file cleanly.

**continue** — The case has the local privilege-escalation chain and a narrowed file candidate, but not the line text itself. We now need the exact HTTP transaction content that displayed or transferred the file, because size-based inference is not enough to answer.
**New scope:** sourcetypes=['stream:http', 'osquery:results', 'ps'] sources=[] fields=['_raw', 'uri_path', 'form_data', 'bytes_in', 'bytes_out', 'src', 'dest', 'status', 'host', 'user', 'process', 'cmdline', 'path', 'pid']

Stay anchored to host hoth, the saveGangster.action OGNL RCE sequence, and the colonel/colonel.c/colonelnew chain already established. Read the raw HTTP transaction content for the 2018-08-20T11:11:27 UTC saveGangster.action event with bytes_out=5880 and determine whether it contains the displayed contents of /tmp/colonel.c; if it does, extract line 2 exactly as shown. If that response does not carry the file text cleanly, read the 2018-08-20T11:08:37 UTC saveGangster.action event with bytes_in=9200 to recover the transferred body for /tmp/colonel as fallback, decode or otherwise interpret it only if the telemetry itself supports doing so, and then determine line 2 of the file that the execution chain proves was used to escalate tomcat8 to root. If both artifacts' text are visible, distinguish the transport file from the operative escalation file and report the exact line 2 for the operative one.

### 19:41:51 - s1 -> SH   [REPORT - round 4 - FOUND]
> ANSWER: line 2 of /tmp/colonel.c is " * Ubuntu 16.04.4 kernel priv esc" (leading space, asterisk, space, then the text). VERIFIED CHAIN (host hoth, actor tomcat8 uid 111, 2018-08-20 UTC): Struts2 OGNL RCE via POST /frothlyinventory/integration/saveGangster.action (192.168.8.103 -> 192.168.9.30:8080,
_full: reports/s1_round_4.md_

### 19:42:01 - runner   [NOTE]
TURN REJECTED:
- s1 asked 1 open question(s) and you answered 0 — answer each one, in order, in open_question_answers

### 19:42:09 - SH -> s1   [ANSWER]
SH's answers to your open questions:
1. No further confirmation is required to answer: the reported line-2 text is already tied to /tmp/colonel.c by the upload, decode, and matching 5775-byte size; a full end-to-end decode would only be extra confirmation.

** * Ubuntu 16.04.4 kernel priv esc** (line_text) from s1

s1 round 4 states the exact decoded line text literally: 'Decoding the captured prefix gives: line 1 `/*`, line 2 ` * Ubuntu 16.04.4 kernel priv esc`'. It also ties that decoded content to /tmp/colonel.c via the observed upload, decode, file size, compile, and execution chain.

**Premise audit (SH):**
- premise="Coverage: The file used to escalate tomcat8's permissions to root could show up as local process/file telemetry on hoth, as HTTP-carried content from the OGNL RCE session, or as payload in stream:tcp/smtp/config-style feeds. s1 covered local process/file telemetry enough to establish the chain, then found the actual text-bearing artifact in stream:http; stream:tcp/smtp/config_file/osquery packs were checked and ruled out as text carriers." status='VERIFIED' source='s1 round 4' quote='Coverage: file text carriers — (a) stream:http form_data of the 11:08:37 upload: READ, contains the full base64 - VERIFIED; (b) stream:http 11:11:27 cat response: content_length=5775 confirms the body carried the file, body itself not stored in the event - VERIFIED as to size; (c) osquery packs, shell histories, stream:tcp/smtp, config_file: eliminated in R2-R3 - VERIFIED empty.' evidence='This quote names the text-bearing feed actually used, and records that the other plausible carriers were checked and eliminated for file text. That covers the main ways the requested line could appear in the dataset.'
- premise='The operative file named by the question is /tmp/colonel.c, not /tmp/colonel or /tmp/colonelnew.' status='VERIFIED' source='s1 round 4' quote='The execution chain (upload → decode → cat → gcc → chmod +x → ./colonelnew as uid 111 → uid-0 rm) proves /tmp/colonel.c is the file used to escalate tomcat8 to root; /tmp/colonel is single-line base64 transport (no line 2), colonelnew the compiled binary.' evidence='This finding explicitly chooses among the candidate artifacts in the chain and explains why /tmp/colonel.c is the relevant line-oriented file for the question.'
- premise='The uploaded base64 recovered from stream:http is the content of /tmp/colonel.c.' status='VERIFIED' source='s1 round 4' quote="The uploaded base64 IS the file: 7700 base64 chars decode to exactly 5775 bytes — the FIM-reported size of /tmp/colonel.c and the cat response's http_content_length." evidence='The size match links the recovered uploaded payload to the specific file /tmp/colonel.c observed elsewhere in the host-side chain.'
- premise="Line 2 of that file is exactly ' * Ubuntu 16.04.4 kernel priv esc'." status='VERIFIED' source='s1 round 4' quote='Decoding the captured prefix gives: line 1 `/*`, line 2 ` * Ubuntu 16.04.4 kernel priv esc`, then ` *`, ` * all credits to @bleidl`, ` * - vnik`, ` *`, blank, `// Te...`.' evidence='This quote contains the exact line text as extracted from the decoded file prefix, directly answering the question.'
- premise='The leading space, asterisk, and trailing text are part of the line and must be preserved in the answer.' status='VERIFIED' source='s1 round 4' quote='Premise: line 2 includes the leading " * " — the decoded bytes are 0x20 0x2A 0x20 before "Ubuntu" - VERIFIED.' evidence='This establishes that the formatting characters are part of the file line and should appear in the submitted answer exactly as shown.'

### 19:42:09 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

