# s1 - Q304 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** sourcetype=osquery:results, Unix:UserAccounts | host=hoth | fields=columns.cmdline, columns.path, decorations.username, user, user_id, user_group_id, shell, home
**Insight:** FOUND
**Candidate:** tomcat7   **Confidence:** 95

## Prior rounds
- None (round 1).

## This round
### What I ran
- get_source_types -> confirmed osquery:results and Unix:UserAccounts feeds exist.
- index=botsv3 sourcetype=osquery:results host=hoth "useradd" | stats ... -> 0 events (cmdline not a searchable token in that form).
- get_raw_events sourcetype=osquery:results keyword=useradd -> 2 events, both on hoth: 11:08:05 UTC run by tomcat8 (uid 111) and 11:24:54 UTC run by root, each `useradd ... tomcat7 ... -g 0 -M -N -r -s /bin/bash`.
- index=botsv3 sourcetype=Unix:UserAccounts host=hoth | stats count by user, user_id, user_group_id, shell, home -> 34 accounts; tomcat7 = uid 0, gid 0, /bin/bash, /home/tomcat7, count=2; all other accounts count=5.

### What it means
The osquery proc_events directly record the creation act: user `tomcat7` created on hoth, first attempted by the compromised tomcat8 service account, then successfully by root, with UID 0/GID 0 and a bash shell — a root-equivalent backdoor. Unix:UserAccounts independently confirms tomcat7 exists on hoth and appears in only 2 of 5 /etc/passwd snapshots while every pre-existing account appears in all 5, placing its creation mid-window after the earlier collections. The created username, exactly as recorded, is tomcat7.

## Ruled out
- tomcat8 — pre-existing service account (uid 111, /bin/false, present in all 5 snapshots); it is the actor of the first useradd, not the created user.
- klagerfield and all other hoth /etc/passwd accounts — present in all 5 snapshots, predating the compromise.
- Cloud service-account creation (AWS IAM / Azure AAD) — out of scope for this host-side question; not needed given direct host evidence.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen). A claim resting on them alone is UNVERIFIED._
