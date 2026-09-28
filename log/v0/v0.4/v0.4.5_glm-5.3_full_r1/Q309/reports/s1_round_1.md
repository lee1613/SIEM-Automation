# s1 - Q309 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=ms:aad:audit | source=/tenantdomains/froth.ly, AzureAD | fields=activity, actor.userPrincipalName, targets{}.userPrincipalName, targets{}.modifiedProperties{}
**Insight:** FOUND
**Candidate:** bgist@froth.ly,fyodor@froth.ly   **Confidence:** 95

## Prior rounds
- (Round 1) This is the first round; no prior rounds.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; ms:aad:audit, ms:aad:signin, ms:o365:management, o365:management:activity identified as Microsoft cloud identity/audit feeds.
- get_sourcetype_fields ms:aad:audit -> 55 events; fields include activity, actor.userPrincipalName, targets{}.userPrincipalName, targets{}.modifiedProperties{}; actors fyodor/bstoll/klagerfield@froth.ly.
- `index=botsv3 sourcetype="ms:aad:audit" "AccountEnabled" | stats count by actor.userPrincipalName, targets{}.userPrincipalName, activity` -> 3 events; one "Disable account": fyodor@froth.ly -> bgist@froth.ly.
- get_raw_events keyword="Disable account" -> 1 event: activity="Disable account", Success, actor fyodor@froth.ly, target bgist@froth.ly, AccountEnabled oldValue=[true] newValue=[false], 2018-08-20T14:47:12Z.
- `index=botsv3 sourcetype="o365:management:activity" "Disable account" OR "AccountEnabled"` -> 0 events.
- `index=botsv3 sourcetype="o365:management:activity" | stats count by Operation` -> 28 operations, all SharePoint/Exchange (FileAccessed, Set-Mailbox, etc.); no account-disable operation.
- `index=botsv3 sourcetype="WinEventLog" EventCode=4725` -> 0 events (no on-prem domain account disable).

### What it means
FOUND: the Azure AD audit feed records exactly one "Disable account" activity, with activityResultStatus=Success and the modified property AccountEnabled flipping [true]->[false]. The acting user (actor.userPrincipalName) is fyodor@froth.ly; the disabled user (targets{}.userPrincipalName) is bgist@froth.ly. Coverage checks confirm no competing disable events in o365:management:activity (no such operation exists in that feed) or in Windows security event logs (EventCode 4725 absent). Alphabetical order per the answer format: bgist@froth.ly,fyodor@froth.ly.

## Ruled out
- o365:management:activity - full operation inventory (28 ops) contains only SharePoint/Exchange operations; no user-account disable recorded there.
- WinEventLog EventCode=4725 - zero events; no on-prem AD account disable in the dataset.
- The two "Update user" events by fyodor (on bgist and klagerfield) - these are StsRefreshTokensValidFrom / property updates, not AccountEnabled=false disables; only the "Disable account" activity shows the disable act.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
