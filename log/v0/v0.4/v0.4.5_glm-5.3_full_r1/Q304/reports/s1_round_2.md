# s1 - Q304 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Scope:** sourcetype=osquery:results, Unix:UserAccounts | host=hoth | fields=columns.cmdline, columns.path, decorations.username, unixTime, user, user_id, user_group_id, shell, home
**Insight:** FOUND
**Candidate:** tomcat7   **Confidence:** 97

## Prior rounds
- Round 1: get_raw_events useradd on osquery:results -> 2 hoth events, both creating tomcat7 (11:08 UTC as tomcat8, 11:24 UTC as root); hoth Unix:UserAccounts stats -> tomcat7 uid 0/gid 0//bin/bash at 2-of-5 snapshots, all other accounts 5-of-5. Submitted tomcat7.
- Clarification round: confirmed from held evidence that both cmdlines name tomcat7, tomcat7 is the only reduced-presence account, and the selection does not rest on the truncated fieldsummary.

## This round
### What I ran
- index=botsv3 (sourcetype=osquery:results columns.path="/usr/sbin/useradd") OR (Unix:UserAccounts host=hoth user=tomcat7) -> 0 events (field-filtered form not indexed that way; discarded).
- index=botsv3 sourcetype=osquery:results host=hoth "useradd" | stats count by decorations.username, columns.cmdline, columns.path, columns.pid, unixTime -> 2 rows (total 2, returned 2): root-run useradd of tomcat7 (unixTime 1534764294) and tomcat8-run useradd of tomcat7 (unixTime 1534763285), both path /usr/sbin/useradd.
- index=botsv3 sourcetype=Unix:UserAccounts host=hoth | stats count as snapshots by user, user_id, user_group_id, shell, home | sort - snapshots, user -> 34 rows (total 34, returned 34), read to the end: tomcat7 = uid 0, gid 0, /bin/bash, /home/tomcat7, snapshots=2; all 33 other accounts snapshots=5.

### What it means
Both premises are now settled by complete, quotable output. p1 (coverage): the hoth osquery proc_events carry the user-creation act (both useradd rows name tomcat7) and hoth Unix:UserAccounts corroborates the account's later appearance (2-of-5 snapshots, absent from the first collections); the unscoped useradd keyword search returned only these 2 events, both on hoth, so no cloud host in the same feed shows useradd. p2 (selection): both cmdlines name tomcat7 with the later, successful execution run by root, and tomcat7 is the only hoth account with reduced snapshot presence — every rival, including the legitimate tomcat8 service account (uid 111, /bin/false, 5-of-5), predates the window. The created username, unchanged, is tomcat7.

## Ruled out
- tomcat8 — pre-existing service account (uid 111, /bin/false, 5-of-5 snapshots); actor of the first useradd, not the created user.
- All other 33 hoth /etc/passwd accounts — 5-of-5 snapshot presence, predate the compromise.
- Cloud bootstrap user-creation on EC2 hosts (mars/gacrux) — no useradd events in osquery:results for any host but hoth.

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
