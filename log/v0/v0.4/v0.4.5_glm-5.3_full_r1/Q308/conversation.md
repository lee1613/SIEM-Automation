# Q308 — SH <-> Senior conversation

### 19:32:24 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'Unix:UserAccounts'] sources=- fields=['columns.cmdline', 'decorations.username', 'user', 'user_id', 'user_group_id', 'home', 'shell', 'host']
**Technique:** senior
**Reason:** Q304 already narrowed the entity to the created Linux user tomcat7 on hoth. Group assignment can be evidenced either directly in the root-run useradd command or in host account/group inventory for that same user, so this scope is the direct path.

On host hoth, using the user identified in Q304 as tomcat7, determine what groups that user was assigned to after compromise and return the group names exactly as evidenced, comma separated without spaces in alphabetical order.

### 19:41:04 - s1 -> SH   [REPORT - round 1 - FOUND]
> Both useradd invocations for tomcat7 on hoth carry identical group-relevant flags: -g 0 (primary group GID 0, i.e. root) and -N (no user private group). The user was also made UID 0 (-o -u 0) with shell /bin/bash, -M -r. First run at 11:08:05 UTC by tomcat8 (uid 111 — likely the pre-existing Tomcat 
_full: reports/s1_round_1.md_

### 19:41:12 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] The strongest evidenced group assignment is the primary group from the useradd command: `-g 0`, which maps to group ID 0. What remains to settle is whether a host account row or any later group-modification artifact adds supplementary groups.
[q2] The question’s plural wording means you should check for both primary and supplementary group assignment. Use the hoth account row for tomcat7 and any host artifact naming later `usermod`, `gpasswd`, or `addgroup` activity before treating `root` as complete.

**continue** — The right host and user are already established from Q304, and the useradd command gives a concrete primary-group lead. What blocks answering is not the entity but whether the records show only that primary group or any later supplementary-group assignment as well.
**New scope:** sourcetypes=['osquery:results', 'Unix:UserAccounts', 'linux_audit', 'linux_secure', 'bash_history', 'config_file'] sources=[] fields=['columns.cmdline', 'decorations.username', 'user', 'user_group_id', 'home', 'shell', '_raw']

On hoth, settle group assignment for tomcat7 from host-side account evidence. First read the Unix:UserAccounts row for tomcat7 to confirm its user_group_id and whether any group name can be tied to it. Then check for any later group-modification activity for tomcat7 in the same host-side evidence path—such as usermod, gpasswd, addgroup, or equivalent command/process records. If no supplementary-group evidence exists, state explicitly that the only evidenced group assignment after compromise is the primary group implied by `-g 0` and return the group name exactly as supported.

### 19:41:25 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s1_round_2.md_

### 19:41:30 - SH -> s1   [COMMAND]
**continue** — The host, user, and primary-group lead are already in scope, but this round stopped at intention and left the plural 'groups' issue unresolved. The last round must determine whether tomcat7 had only primary group 0 or any supplementary groups were assigned later.
**New scope:** sourcetypes=['osquery:results', 'config_file', 'Unix:UserAccounts'] sources=[] fields=['columns.cmdline', '_raw', 'user', 'user_group_id', 'host']

On hoth, search the held host-side evidence paths for any later group-modification activity for tomcat7, including usermod, gpasswd, addgroup, groupadd, or equivalent command/process traces, and inspect any config/account artifact that could show group membership text for tomcat7. If none exists, state explicitly that the only evidenced group assignment after compromise is primary group ID 0 from the useradd and Unix:UserAccounts row, and return the corresponding group name exactly as supported.

### 19:52:37 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> 
_full: reports/s1_round_3.md_

### 19:52:37 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 19:52:37 - runner   [NOTE]
s1 api_failed — retired, spawn slot refunded

### 19:52:37 - runner   [NOTE]
s1 api_failed and no operator reachable — skipping; slot already refunded, decision request at C:\dev\SIEM-Automation\log\v1\v1.4/v1.4.5_glm-5.3_full_r1\decision_request.json

### 19:52:44 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'Unix:UserAccounts', 'config_file'] sources=- fields=['columns.cmdline', 'decorations.username', 'user', 'user_id', 'user_group_id', 'home', 'shell', '_raw']
**Technique:** senior
**Reason:** The retired senior already narrowed the entity to tomcat7 on hoth and found the direct `-g 0` group-assignment lead, but transport failure prevented settling whether any supplementary groups exist. The remaining answer depends on the same host-side account/process/config evidence, not a different feed family.

On host hoth, for the user created after compromise (tomcat7), determine what groups that user was assigned to after compromise. Use host-side evidence to confirm the primary group from the root-run useradd and check whether any later group-modification or group-membership artifact shows supplementary groups; return the final group-name set exactly as evidenced, comma separated without spaces in alphabetical order.

### 19:54:16 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s2_round_1.md_

### 19:54:21 - SH -> s2   [CLARIFY]
**suspect**
1. From the evidence you already hold, do you have any completed result on hoth that shows tomcat7's Unix:UserAccounts row or any direct group-membership artifact, or did this round end before producing any such output?
2. From the evidence you already hold, do you have any completed result showing zero later usermod/gpasswd/groupadd/addgroup/groupmod activity for tomcat7 on hoth, or was that only intended and not returned?
3. Does any conclusion about group name 'root' already rest on held complete output from Q304/Q303-style useradd evidence, or would that require a new search result not yet obtained in this question?

### 19:54:30 - s2 -> SH   [CLARIFY REPLY]
1. **This round ended before producing it.** I did not run any Unix:UserAccounts or group-membership query this round — my last intended search (osquery group tables) was cut off by the round ending. The Unix:UserAccounts row (user_group_id=0, user_id=0, shell=/bin/bash, home=/home/tomcat7) is carried forward from the retired senior's prior-round work, not from any output I hold this round.

2. **Yes, completed.** I ran `index=botsv3 sourcetype=osquery:results hostIdentifier=hoth (cmdline="*usermod*" OR "*gpasswd*" OR "*groupadd*" OR "*addgroup*" OR "*groupmod*")` and it returned zero events (total_event_count 0). Additionally, bash_history, linux_audit, and linux_secure each returned zero records mentioning "tomcat7" at all — so any group-mod command naming tomcat7 in those feeds would have been caught. Caveat: the osquery cmdline search covers only osquery:results; a group-mod not naming tomcat7 in another feed is untested, but would be irrelevant to tomcat7's membership.

3. **Split.** The GID assignment rests on held complete output: both useradd events (2 of 2 returned, read in full) show `-g 0 -N` with no `-G` flag, run as root (euid 0). But the group **name** "root" for GID

### 19:54:30 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

### 19:54:30 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

