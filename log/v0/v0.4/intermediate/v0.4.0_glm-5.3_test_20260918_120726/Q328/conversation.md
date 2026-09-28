# Q328 — SH <-> Senior conversation

### 12:14:55 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['bash_history', 'osquery:results', 'linux_secure', 'syslog', 'access_combined', 'lsof', 'ps'] sources=- fields=['_time', 'host', 'user', 'username', 'cmd', 'command', 'path', 'filepath', 'file_name', 'cwd', '_raw']
**Technique:** content
**Reason:** This question depends on Linux host and shell evidence around privilege escalation activity and the file artifacts referenced during that sequence; one content-oriented senior with Linux history and artifact scope can establish both the file and its line-2 contents.

Identify how tomcat8 escalated privileges to root on the Linux hosts in index=botsv3, determine which file was used in that escalation, and recover the exact text displayed on line 2 of that file.

### 12:18:02 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> ESTABLISHED: (1) The tomcat8 Linux host is "hoth" — the only host with tomcat8 shell history (install, tomcat-users.xml edit, restarts). (2) sourcetypes out-3 and localhost-5 are Tomcat catalina.out-style logs containing org.apache.struts2 stack traces referencing org.apache.jsp.integration.modelDri
_full: reports/s1_round_1.md_

### 12:18:07 - SH -> s1   [COMMAND]
**continue** — The case now has the likely compromised Tomcat host, but the missing value is still the file and its second line. The next round must stay tightly on the escalation chain and recover the file content rather than revisit initial access.
**New scope:** sourcetypes=['osquery:results'] sources=['/var/log/osquery/osqueryd.results.log'] fields=['host', 'name', 'columns.cmdline', 'columns.path', 'columns.target_path', 'columns.action', 'columns.uid', 'columns.euid', 'columns.username', 'columns.parent', 'columns.cwd']

On host hoth, establish the privilege-escalation sequence from user tomcat8 to root by examining process-execution and file-modification evidence after the Tomcat compromise, identify the specific file used to gain root privileges, and then recover the exact text of line 2 from that file from any available file-content, command, or related artifact evidence. Prioritize the osquery process-monitoring and file-integrity feeds already identified, and only branch to another host if those events show tomcat8 moving off hoth before the escalation.

### 12:25:10 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> ESCALATION CHAIN FULLY ESTABLISHED on host=hoth (all as user tomcat8, uid=111, euid=111, from osquery pack_process-monitoring_proc_events, decorations.username=tomcat8): (1) base64 --decode /tmp/colonel > /tmp/colonel.c — decoded a staged base64 blob into C source; (2) gcc colonel.c -o colonelnew (p
_full: reports/s1_round_2.md_

### 12:25:15 - runner   [NOTE]
TURN REJECTED:
- s1: its report was read but no route addressed it — grade it and give it exactly one route

### 12:25:21 - SH -> s1   [RETIRE]
s1 completed the host-side attribution needed for this question: on hoth, tomcat8 decoded /tmp/colonel into /tmp/colonel.c, compiled it to /tmp/colonelnew, and used that chain for local root escalation. Its osquery-only scope cannot recover the file’s displayed contents or HTTP-delivered source text, so further rounds in the same scope would pursue a missing artifact class rather than the answer.

### 12:25:21 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 12:25:21 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:http', 'access_combined', 'syslog'] sources=['out-3', 'localhost-5', '/var/log/httpd/access_log', '/var/log/apache2/access.log', '/var/log/syslog', 'stream:http', 'stream:Splunk_HTTPURI', 'stream:Splunk_HTTPClient', 'stream:Splunk_HTTPStatus'] fields=['_raw', 'uri', 'uri_path', 'http_method', 'src', 'dest', 'request', 'response', 'useragent', 'host']
**Technique:** content
**Reason:** s1’s constraint set is limited to osquery:results process and file-event telemetry, which can identify the artifact and execution chain but cannot show file contents or command output. Recovering line 2 requires content-bearing web/application evidence from the Struts2 delivery path.

Recover the contents of /tmp/colonel.c used by tomcat8 on host hoth to escalate privileges to root by examining HTTP traffic and application/web logs around the Struts2 compromise, and report the exact text displayed on line 2 of that file.

### 12:33:30 - s2 -> SH   [REPORT - round 1 - FOUND]
> Line 2 carries a single leading space: " * Ubuntu 16.04.4 kernel priv esc". Full header: L1 "/*", L2 " * Ubuntu 16.04.4 kernel priv esc", L3 " *", L4 " * all credits to @bleidl", L5 " * - vnik", L6 " *", L7 blank. The exploit is vnik's CVE-2017-16995 eBPF priv-esc; delivery chain: Struts2 OGNL RCE (
_full: reports/s2_round_1.md_

### 12:33:35 - SH -> s2   [ANSWER]
** * Ubuntu 16.04.4 kernel priv esc** (line_text) from s2

s2 established that the file used for escalation was /tmp/colonel.c, recovered its contents from the staged base64 blob delivered in the Struts2 HTTP POST, and reported the literal line breakdown with line 2 shown as ` * Ubuntu 16.04.4 kernel priv esc`.

### 12:33:35 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

