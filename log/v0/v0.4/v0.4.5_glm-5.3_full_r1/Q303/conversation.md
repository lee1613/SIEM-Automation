# Q303 — SH <-> Senior conversation

### 18:55:47 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['linux_audit', 'bash_history', 'osquery:results', 'syslog', 'linux_secure'] sources=- fields=['_raw', 'host', 'user', 'exe', 'cmd', 'command', 'columns.command', 'type', 'acct', 'uid', 'auid', 'msg']
**Technique:** senior
**Reason:** Successful Linux user creation and any password-setting command or artifact should be in Linux audit/auth logs, shell history, or process-command telemetry on the relevant on-prem host. This scope covers both the account-creation act and the likely places where the password could have been recorded or passed.

Determine which user was successfully created by root on an on-premises Linux system, then identify the password that was set for that user from the host evidence and return it exactly as recorded.

### 18:57:04 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> What I learned: (1) All useradd activity in linux_audit and linux_secure is on EC2 instances ip-172-16-0-13, ip-172-16-0-127, ip-172-16-0-145, creating ec2-user, apache, memcached, streamfwd — cloud bootstrap accounts, not the on-prem creation the question names. (2) bash_history has two feeds: /hom
_full: reports/s1_round_1.md_

### 18:57:11 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] The cloud bootstrap useradd events are not the target because they are on EC2 hosts and create AWS/service accounts, not an on-prem Linux user. The next best path is full shell/history and local account artifacts that could record both the user creation and the password-setting act.

**continue** — This round narrowed the user-creation evidence by ruling out the obvious audit/auth events as AWS bootstrap noise, which is useful progress. The question now turns on finding the on-prem Linux creation path and the password-setting artifact rather than repeating useradd keyword searches in the same cloud-bootstrap logs.
**New scope:** sourcetypes=['bash_history', 'osquery:results', 'Unix:UserAccounts', 'config_file', 'history-2'] sources=[] fields=['_raw', 'host', 'user']

Read the full /home/klagerfield/.bash_history and any other local history/account artifacts for root-driven user creation and password setting on the on-prem Linux host. Specifically establish which user root created outside the EC2 bootstrap pattern, then find the password-setting command or artifact for that user in bash_history, osquery:results, Unix:UserAccounts, or config_file if present, and return the password exactly as recorded.

### 18:58:36 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> WHERE THE ANSWER ALMOST CERTAINLY IS: index=botsv3 sourcetype=osquery:results host=hoth name=pack_incident-response_shell_history with _raw containing useradd/passwd/chpasswd/adduser — 4 events (counts 1,2,1,1) exist there; read them with get_raw_events (sourcetype=osquery:results, keyword=useradd /
_full: reports/s1_round_2.md_

### 18:58:42 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q2] The live lead is the 4 matching osquery shell-history events on host hoth from pack_incident-response_shell_history. They are the first evidence path likely to contain the created username and plaintext password exactly as entered.

**continue** — The cloud bootstrap noise has been ruled out and the on-prem host is now narrowed to hoth. The answer depends on reading the four matched osquery shell-history events themselves, because that is the first artifact in scope likely to contain the literal password-setting command.
**New scope:** sourcetypes=['osquery:results', 'bash_history', 'Unix:UserAccounts', 'config_file', 'history-2'] sources=[] fields=['_raw', 'host', 'user', 'name', 'columns.command', 'columns.username']

On host hoth, read the 4 osquery shell-history events that matched useradd, adduser, passwd, or chpasswd, and determine which command successfully created the user as root and what password was set. If the shell-history rows do not themselves show the password, use the paired proc_events or file-monitoring evidence already present for hoth to settle the exact command line or artifact, then restate the password literally if found.

### 19:02:35 - s1 -> SH   [REPORT - round 3 - FOUND]
> Answer: ilovedavidverve — the -p argument of the root-executed useradd that created user tomcat7 on hoth. Chain: hoth is the only non-EC2 Linux host with shell history and osquery telemetry (bash_history host breakdown: hoth=/home/klagerfield/.bash_history; gacrux/mars EC2 hosts=ec2-user histories).
_full: reports/s1_round_3.md_

### 19:02:42 - SH -> s1   [CLARIFY]
**suspect**
1. From the evidence you already hold, do the two hoth proc_events rows show only two tomcat7 useradd attempts, with exactly one executed by root (uid=0,euid=0) and one executed by tomcat8 (uid=111,euid=111), so there is no unresolved rival successful creation event?
2. From the evidence you already hold, is the full cmdline of the root-run useradd row literally `useradd -ou tomcat7 -p ilovedavidverve 0 -g 0 -M -N -r -s /bin/bash`, with `ilovedavidverve` the exact recorded `-p` argument and no truncation affecting that string?
3. Does your selection of ilovedavidverve depend at all on the partial Unix:UserAccounts result, or is it fully supported by the complete hoth osquery proc_events rows and the ruled-out non-root attempt?

### 19:02:53 - s1 -> SH   [CLARIFY REPLY]
1. **Yes.** The query `index=botsv3 sourcetype=osquery:results host=hoth "tomcat7" | stats count by name, decorations.username, columns.cmdline` returned exactly 2 events (meta: total 2, returned 2 — complete, not truncated), both `pack_process-monitoring_proc_events` on hoth: one with `decorations.username=root` (uid=0, euid=0, gid=0, egid=0) and one with `decorations.username=tomcat8` (uid=111, euid=111, gid=117). No third tomcat7 useradd row exists in that feed, so there is no unresolved rival successful creation event there. (Caveat I already flagged: this completeness holds for osquery:results on hoth; no other feed was searched for tomcat7 by name.)

2. **Yes.** The raw event I read (get_raw_events, osquery:results, keyword=useradd) carried the cmdline as a full JSON token array: `"useradd" "-ou" "tomcat7" "-p" "ilovedavidverve" "0" "-g" "0" "-M" "-N" "-r" "-s" "/bin/bash"` — i.e. literally `useradd -ou tomcat7 -p ilovedavidverve 0 -g 0 -M -N -r -s /bin/bash`. The token immediately following `"-p"` is exactly `ilovedavidverve`, and the raw JSON was returned whole, so nothing was truncated around that string.

3. **No, it does not depend on Unix:UserAccounts at all.** That fee

### 19:03:00 - SH -> s1   [ANSWER]
**ilovedavidverve** (password) from s1

Complete hoth osquery proc_events results showed exactly two tomcat7 useradd attempts and only one executed by root. Clarification confirms the raw cmdline token array for that root-run event contains `"-p" "ilovedavidverve"`, so ilovedavidverve is the exact password recorded for the user successfully created by root on the on-prem Linux system.

**Premises it rests on:** p3, p4

### 19:03:00 - runner   [NOTE]
answered on an unverified premise (R4 = FAIL) — allowed, but dangerous ground: Complete hoth osquery proc_events results showed exactly two tomcat7 useradd attempts and only one executed by root. Clarification confirms the raw cmdline token array for that root-run event contains `"-p" "ilovedavidverve"`, so ilovedavidverve is the exact password recorded for the user successfully created by root on the on-prem Linux system.

### 19:03:00 - runner   [NOTE]
answered with UNVERIFIED premises in the ledger — allowed (nothing left to try), but dangerous ground: p3 Coverage: The successful root-created user on the on-prem Linux system is evidenced in hoth osquery proc_events, and the decisive password value is carried in the root-run useradd cmdline there; Unix:UserAccounts on hoth contributes no confirming row.; p4 Selection: The successful creation is the hoth proc_events row where decorations.username=root and uid/euid are 0 on `useradd ... -p ilovedavidverve ... tomcat7`, not the earlier tomcat8 uid=111 row with `-p davidverve.com`, because only the root execution can successfully create the account.

### 19:03:00 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

