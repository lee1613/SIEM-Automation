# Q304 — SH <-> Senior conversation

### 19:03:15 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['osquery:results', 'linux_audit', 'linux_secure', 'bash_history'] sources=- fields=['host', 'decorations.username', 'columns.cmdline', '_raw', 'user']
**Technique:** senior
**Reason:** Q303 already established that hoth is the on-prem Linux host and that osquery proc_events there captured root-run useradd activity creating a backdoor account. This scope contains the host-side creation evidence needed to name the created user directly and distinguish it from cloud-bootstrap service-account creation elsewhere.

Determine the name of the user account that was created after the endpoint was compromised. Start from the on-prem Linux host evidence on hoth, identify the successful user-creation event after compromise, and return the created username exactly as recorded.

### 19:08:55 - s1 -> SH   [REPORT - round 1 - FOUND]
> The successful creation is the root-run useradd at 11:24:54 UTC (unixTime 1534764294); the 11:08 attempt ran as the tomcat8 service account (uid 111) and likely failed for lack of privilege, then was retried as root with a different -p value. The -p arguments (davidverve.com, ilovedavidverve) are pa
_full: reports/s1_round_1.md_

### 19:09:00 - SH -> s1   [CLARIFY]
**suspect**
1. From the evidence you already hold, do the two hoth osquery raw events both name tomcat7 as the user being added, with the later one executed by root and no other created username appearing in those useradd cmdlines?
2. From the evidence you already hold, is tomcat7 the only hoth account whose Unix:UserAccounts snapshot presence is reduced (2 of 5) while pre-existing accounts appear in all 5 snapshots, so there is no rival newly created username in that feed?
3. Does your selection of tomcat7 depend at all on the truncated get_sourcetype_fields output, or is it fully supported by the complete get_raw_events useradd results and the hoth Unix:UserAccounts stats rows you already read?

### 19:09:08 - s1 -> SH   [CLARIFY REPLY]
1. **Yes.** Both raw events name tomcat7 in the cmdline — `"useradd" "-ou" "tomcat7" ...` — and the get_raw_events call returned the complete set (meta: total 2, returned 2), so there are no other useradd events I didn't read. The later event (11:24:54 UTC) has decorations.username=root with uid/euid=0; the earlier one (11:08:05 UTC) ran as tomcat8. No other created username appears in either cmdline — the remaining tokens are flags and the `-p` password material ("davidverve.com" / "ilovedavidverve"), not account names.

2. **Yes.** The hoth Unix:UserAccounts stats returned all 34 rows (meta: total 34, returned 34), and I read them to the end. tomcat7 is the only account with count=2; every other account — root, klagerfield, tomcat8, and all system accounts — has count=5. So no rival newly created username exists in that feed; nothing else shows reduced snapshot presence at all.

3. **No, it doesn't depend on the truncated output.** The get_sourcetype_fields call (which showed only 38 of 153 rows and didn't even list a cmdline field) was used only to probe field naming, and it contributed nothing to the conclusion. The selection of tomcat7 rests entirely on two complete, fully-rea

### 19:09:15 - runner   [NOTE]
TURN REJECTED:
- [F2] ANSWER is blocked: 2 load-bearing premise(s) it rests on are still UNVERIFIED - COMMAND s1 to settle them: p1 "Coverage: On the on-prem Linux host hoth, a user created after compromise would " | p2 "Selection: The created user is tomcat7 because both complete hoth useradd proc_e" → re-read F2.

### 19:09:21 - SH -> s1   [COMMAND]
**continue** — The right host and account have already been isolated, and the remaining blocker is ledger verification rather than where to look. One more round should convert the held hoth evidence into runner-acceptable verification for the two load-bearing premises.

Settle premises p1 and p2 directly from hoth result output. For p1, provide exact output showing that user creation after compromise on hoth is evidenced in the hoth osquery proc_events useradd rows and corroborated by the hoth Unix:UserAccounts snapshot listing. For p2, provide exact quoted rows showing both tomcat7 useradd cmdlines, the later root-run row, and the hoth Unix:UserAccounts row for tomcat7, so the record directly supports tomcat7 as the created user and rules out rivals. Then restate the username literally if unchanged.

### 19:11:40 - s1 -> SH   [REPORT - round 2 - FOUND]
> Both cmdlines name tomcat7 as the created user; the later execution (unixTime 1534764294, 11:24:54 UTC) is the root-run one, the earlier (1534763285, 11:08:05 UTC) ran as the tomcat8 service account. The -p tokens (davidverve.com / ilovedavidverve) are password material, not usernames. tomcat7's UID
_full: reports/s1_round_2.md_

### 19:11:45 - SH -> s1   [COMMAND]
**continue** — The right host and user are already isolated, and the only blocker is that p1 and p2 still lack exact quoted output acceptable to the runner. The final round must do nothing except produce verbatim rows for those premises.

Settle p1 and p2 with exact word-for-word output only. For p1, quote the complete osquery proc_events rows on hoth showing the useradd activity and the Unix:UserAccounts row set detail that makes tomcat7 the only later-appearing account. For p2, quote the exact root-run and tomcat8-run useradd cmdline rows and the exact Unix:UserAccounts row for tomcat7, so the record directly supports that tomcat7 is the created user and not tomcat8 or any pre-existing account. Then restate the username literally if unchanged.

### 19:14:02 - s1 -> SH   [REPORT - round 3 - FOUND]
> Both cmdlines name tomcat7 as the created user; the later execution (unixTime 1534764294, 11:24:54 UTC) is the root-run one, the earlier (1534763285, 11:08:05 UTC) ran as the tomcat8 service account. The -p tokens (davidverve.com / ilovedavidverve) are password material, not usernames. tomcat7's UID
_full: reports/s1_round_3.md_

### 19:14:02 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

### 19:14:02 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

