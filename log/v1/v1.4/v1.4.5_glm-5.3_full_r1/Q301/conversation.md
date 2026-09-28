# Q301 — SH <-> Senior conversation

### 18:44:28 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['linux_secure', 'osquery:results', 'Unix:UserAccounts', 'lastlog', 'who'] sources=- fields=['src_ip', 'rhost', 'user', 'uid', '_time', 'username', 'account_expires', 'password_expires', 'shell', 'host']
**Technique:** senior
**Reason:** Successful remote logins are most likely in linux_secure or related login telemetry, while account-expiration state is more likely in Unix account inventory or osquery account tables. This combined scope can tie a specific expired account to a successful external login and its client IP.

Determine which external client IP successfully authenticated to Frothly using an expired user account. First identify the expired account from account-inventory data, then find successful login events for that account in authentication logs and return the external client IP exactly as recorded.

### 18:45:58 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> No candidate yet — the round was spent on feed discovery and ruling out the obvious expiration feeds. Key learnings for next round: (1) Unix:UserAccounts is /etc/passwd only (fields: user, home, shell, user_id, user_group_id, password=x, enabled=yes) — /etc/passwd carries NO expiration data, so expi
_full: reports/s1_round_1.md_

### 18:46:05 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] The strongest next source is linux_secure, because it can hold both explicit account-expired messages and successful SSH login records with source IPs.
[q2] If linux_secure does not show it, the next rival path is cloud identity login data such as ms:aad:signin, but no evidence from this round points there yet.

**continue** — This round narrowed the problem by showing expiration is not coming from Unix:UserAccounts or osquery inventory. The question now turns on correlating authentication-log evidence of an expired account with a successful login and its external client IP.
**New scope:** sourcetypes=['linux_secure'] sources=['/var/log/secure'] fields=['user', 'src_ip', 'rhost', 'message', '_raw']

Search linux_secure for explicit account-expired or expired-password/account-expiration messages and for successful login events from external IPs. Identify the account named as expired, then determine whether that same account also has a successful login record and return the client IP from that successful authentication. If linux_secure does not contain both pieces, say exactly which part is missing and whether ms:aad:signin or another auth feed would have to carry it.

### 18:47:30 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> linux_secure does NOT contain both pieces. MISSING PIECE: the account-expiration state — there is no "expired" message anywhere in the 350 events (verified by direct keyword search returning 0 and by enumerating all 38 distinct message patterns). PRESENT PIECE: successful logins exist, but only for 
_full: reports/s1_round_2.md_

### 18:47:37 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q3] linux_secure does not show any expired-account state at all, so it cannot answer the question by itself. It only contributes negative coverage and a ruled-out set of routine ec2-user SSH logins.
[q4] ms:aad:signin is now the strongest next feed because it can pair client IP with sign-in outcome/detail, including account-status conditions such as expired credentials or expired accounts.

**retry** — The linux_secure direction was useful for ruling out SSH as the answer path, but the question still needs a feed that records both successful sign-ins and expired-account state. With one round left, the case should move directly to Azure AD sign-in data rather than spend more effort on Linux auth logs.
**New scope:** sourcetypes=['ms:aad:signin'] sources=['/tenantdomains/froth.ly'] fields=['userPrincipalName', 'ipAddress', 'status.errorCode', 'status.failureReason', 'conditionalAccessStatus', 'appDisplayName', 'resourceDisplayName', 'createdDateTime', 'resultDescription']

Search ms:aad:signin for any sign-in records indicating an expired user account or expired credentials, and determine whether the same account also has a successful login event. Return the external client IP from the successful sign-in for that expired account, and if multiple IPs exist, decide which one fits the question's wording from the records.

### 18:48:20 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> 
_full: reports/s1_round_3.md_

### 18:48:24 - runner   [NOTE]
TURN REJECTED:
- [F2–F3] ANSWER from s1 names no premises - trace the chain from the question to the value and cite every premise it rests on in answer_premise_ids → re-read F2–F3.

### 18:48:31 - SH -> s1   [ANSWER]
**NOT_FOUND** (unknown) from s1

No senior report in this question produced a literal external client IP tied to a successful login by an expired user account. The held reports only establish negative coverage: Unix:UserAccounts has no expiration field, osquery has no relevant account-expiration evidence, linux_secure contains successful ec2-user SSH logins but no expired-account messages, and the final ms:aad:signin round did not return any results before budget ended.

**Premises it rests on:** p3, p4

### 18:48:31 - runner   [NOTE]
answered on an unverified premise (R4 = FAIL) — allowed, but dangerous ground: No senior report in this question produced a literal external client IP tied to a successful login by an expired user account. The held reports only establish negative coverage: Unix:UserAccounts has no expiration field, osquery has no relevant account-expiration evidence, linux_secure contains successful ec2-user SSH logins but no expired-account messages, and the final ms:aad:signin round did not return any results before budget ended.

### 18:48:31 - runner   [NOTE]
answered with UNVERIFIED premises in the ledger — allowed (nothing left to try), but dangerous ground: p3 Coverage: In the searched dataset paths for this question, expired-account evidence was tested in Unix:UserAccounts, osquery:results, aws:cloudwatch:guardduty, linux_secure, and ms:aad:signin; only linux_secure produced successful login events, but none of those searched reports established both account expiration and a successful login for the same account.; p4 Selection: No external client IP can be selected from the held reports because no report returned a successful login event for an account that the same or another searched report established as expired.

### 18:48:31 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

