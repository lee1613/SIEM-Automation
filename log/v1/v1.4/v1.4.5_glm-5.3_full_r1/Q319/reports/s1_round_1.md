# s1 - Q319 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=o365:management:activity, ms:o365:management | fields=Operation, Parameters, UserId, ClientIP
**Insight:** FOUND
**Candidate:** SOX   **Confidence:** 95

## Prior rounds
(none — first round)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; M365 feeds are o365:management:activity and ms:o365:management.
- search_keyword "inbox" -> 0 matches; "rule" -> only AWS/code42/symantec rule fields, no M365 inbox-rule fields.
- get_sourcetype_fields on both M365 feeds -> SharePoint/OneDrive/AAD/Exchange audit records with Operation and Parameters.
- `index=botsv3 sourcetype="o365:management:activity" | stats count by Operation` -> 28 rows, exactly one New-TransportRule; same query on ms:o365:management -> 38 rows, one New-TransportRule. No New-InboxRule anywhere.
- get_raw_events keyword="New-TransportRule" on both feeds -> 1 event each, same Id (f131587a-a125-4e87-4421-08d5f268e1ac): Parameters = BlindCopyTo=hyunki1984@naver.com, Name=SOX, StopRuleProcessing=False, Mode=Enforce.

### What it means
The only rule-creation event carrying a BCC parameter in the Microsoft 365 audit feeds is New-TransportRule at 2018-08-20T11:21:40Z by fyodor@froth.ly from 199.66.91.253. Its BlindCopyTo parameter points to hyunki1984@naver.com — external to froth.ly, i.e. the personal account — which is the act the question names. That same event's Parameters array sets Name="SOX". Both feed copies show identical values, so the answer is stable across feeds.

## Ruled out
- New-InboxRule — no such Operation exists in either M365 feed (full Operation listings read to completion: 28 and 38 rows).
- Other Exchange rule/admin ops (New-DistributionGroup, New-MailboxSearch, Set-Mailbox, Update-RoleGroupMember, Add-RecipientPermission) — none carry a BCC/forwarding parameter.
- The ms:o365:management copy as a second rule — same event Id, duplicate index entry, not a distinct rule.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "o365:management:activity"}` (31 of 125 rows seen); `get_sourcetype_fields: {"sourcetype": "ms:o365:management"}` (32 of 131 rows seen). A claim resting on them alone is UNVERIFIED._
