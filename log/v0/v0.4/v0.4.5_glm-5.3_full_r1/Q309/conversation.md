# Q309 — SH <-> Senior conversation

### 19:54:43 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['ms:aad:audit', 'o365:management:activity', 'ms:o365:management'] sources=- fields=['Operation', 'ActivityDisplayName', 'ModifiedProperties', 'Target', 'TargetUserOrGroupName', 'ObjectId', 'UserId', 'Actor', 'InitiatedBy', 'userPrincipalName']
**Technique:** senior
**Reason:** A domain account disable is an identity-management action, so Microsoft Azure AD / O365 audit feeds are the direct place to find both the target account and the acting user. These feeds can carry both the admin action and the email-style identities needed for the requested pair.

Identify the domain account disable event in the Microsoft cloud identity/audit data, then determine the email address of the user whose account was disabled and the email address of the user who disabled it. Return the two email addresses exactly as recorded.

### 19:55:49 - s1 -> SH   [REPORT - round 1 - FOUND]
> The single "Disable account" record in the dataset is Directory_FE2NN_24703906 (correlationId d6d25f06-d091-4aa5-8826-6081a3a25525), 2018-08-20T14:47:12Z, tenant 225e05a1-5914-4688-a404-7030e60f3143. Actor fyodor@froth.ly (objectId 18af02a7-8541-4209-9dd5-600ab965d8a7) disabled target bgist@froth.ly
_full: reports/s1_round_1.md_

### 19:55:54 - SH -> s1   [CLARIFY]
**suspect**
1. From the evidence you already hold, is there exactly one successful ms:aad:audit 'Disable account' event, with actor.userPrincipalName=fyodor@froth.ly and targets{}.userPrincipalName=bgist@froth.ly, and no rival disable event left unresolved in that feed?
2. From the evidence you already hold, do the raw ms:aad:audit event details explicitly show AccountEnabled oldValue=[true] and newValue=[false] for bgist@froth.ly, confirming this is the account-disable act the question asks about?
3. Does your selection depend on any truncated exploratory output, or were the decisive ms:aad:audit disable-event results and the rival-feed checks complete and fully read?

### 19:56:09 - s1 -> SH   [CLARIFY REPLY]
**1. Yes, with one small caveat.** The full-text keyword search for "Disable account" across all of `ms:aad:audit` returned exactly 1 event (meta: total_event_count 1, returned 1) — actor fyodor@froth.ly, target bgist@froth.ly, activityResultStatus Success. The companion "AccountEnabled" search returned 3 events total, all 3 rows read: the one "Disable account" plus two "Update user" events (fyodor→bgist, fyodor→klagerfield). Those two Update-user events are the only in-feed neighbors, and their activity label is "Update user," not a disable; the field summary also shows their modified properties center on StsRefreshTokensValidFrom (token invalidation), not AccountEnabled flips. Caveat: I did not byte-read the raw payloads of those two Update-user events, so strictly their modifiedProperties weren't individually inspected — if you want that closed, one query settles it: `index=botsv3 sourcetype="ms:aad:audit" activity="Update user" "AccountEnabled"` with raw output. It does not change the answer to the question as asked, since the disable act is the uniquely-labeled "Disable account" record.

**2. Yes, explicitly.** The raw event (id Directory_FE2NN_24703906, 2018-08-20T14:47:12Z)

### 19:56:15 - runner   [NOTE]
TURN REJECTED:
- [F2] ANSWER is blocked: 2 load-bearing premise(s) it rests on are still UNVERIFIED - COMMAND s1 to settle them: p1 "Coverage: In this dataset, a domain account disable action with both the acting " | p2 "Selection: The account-disable event that answers the question is the single suc" → re-read F2.

### 19:56:21 - SH -> s1   [COMMAND]
**continue** — The right event has already been isolated in ms:aad:audit, and the remaining blocker is ledger verification rather than scope. One more round should convert the held disable-event evidence into runner-acceptable verification for the coverage and selection premises.

Settle premises p1 and p2 directly from ms:aad:audit result output. For p1, provide exact output showing where account-disable actions with acting and target email addresses appear in the dataset, and that the searched rival feeds do not contain a competing disable-action record. For p2, provide the exact quoted Disable account event row showing actor.userPrincipalName, targets{}.userPrincipalName, activityResultStatus, and the AccountEnabled old/new values, and contrast it only enough with the two Update user neighbors to show why they are not the disable act. Then restate the two email addresses literally if unchanged.

### 19:59:34 - s1 -> SH   [REPORT - round 2 - FOUND]
> Answer unchanged and now fully settled: bgist@froth.ly (disabled user) and fyodor@froth.ly (acting user), alphabetical per format. The disable act is recorded twice under correlationId d6d25f06-d091-4aa5-8826-6081a3a25525 — as "Disable account" (Directory_FE2NN_24703906) and as "Update user" (Direct
_full: reports/s1_round_2.md_

### 19:59:39 - SH -> s1   [COMMAND]
**continue** — The correct feed and event appear isolated, and the only blocker is ledger verification. The final round must do nothing except produce verbatim ms:aad:audit output for the existing coverage and selection premises.

Settle p1 and p2 with exact word-for-word output only. For p1, quote the complete ms:aad:audit activity rows or row counts that show the disable-account activity exists there and that the searched rival feeds do not contain a competing disable action. For p2, quote the exact Disable account event row or raw payload fields showing actor.userPrincipalName, targets{}.userPrincipalName, activityResultStatus, and AccountEnabled old/new values, and quote the specific contrasting Update user row that shows [false]->[true] for klagerfield so the rival is ruled out. Then restate the two email addresses literally if unchanged.

### 20:02:18 - s1 -> SH   [REPORT - round 3 - FOUND]
> Answer unchanged: bgist@froth.ly (disabled user) and fyodor@froth.ly (acting user), alphabetical per format. The disable act is dual-logged under correlationId d6d25f06-d091-4aa5-8826-6081a3a25525 as "Disable account" (Directory_FE2NN_24703906) and "Update user" (Directory_FE2NN_24703911), both Acco
_full: reports/s1_round_3.md_

### 20:02:18 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

### 20:02:18 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

