# s1 - Q301 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** index=botsv3 | sourcetypes explored: Unix:UserAccounts, osquery:results, aws:cloudwatch:guardduty | fields: user, home, shell, name, detail.type
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
(none — this is round 1)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; auth-relevant: linux_secure, osquery:results, ms:aad:signin, WinEventLog, Unix:UserAccounts
- get_sourcetype_fields Unix:UserAccounts -> 571 events, /etc/passwd only; fields user/home/shell/user_id; NO expiration field
- search_keyword "expir" -> only AWS STS credential expiration fields (cloudtrail, rds:audit, s3:accesslogs)
- search_keyword "account" -> only AWS account-id fields
- get_sources osquery:results -> 4 sources (main log 219,356 events)
- osquery:results "expired" | stats count by name,action,host -> 0 events
- osquery:results | stats count by name -> 38 packs; no user/account inventory table
- guardduty "expired" | stats by findingId,type,description -> 0 events

### What it means
NOT_FOUND: the round established where account-expiration data is NOT. /etc/passwd (Unix:UserAccounts) carries no expiration field, osquery has no account table and no "expired" events, GuardDuty has no expired-account finding, and no *expir* field exists outside AWS credential semantics. The expired account must surface either as an explicit message in authentication logs (linux_secure sshd/PAM "account expired") or in cloud identity logs (ms:aad:signin), neither of which I queried for this yet.

## Ruled out
- Unix:UserAccounts as expiration source - /etc/passwd schema has no expiration field (verified via field listing)
- osquery:results - no user/account table among 38 packs; zero "expired" matches
- aws:cloudwatch:guardduty - zero findings matching "expired"
- AWS *expir* fields - all are STS/S3 credential expiry, not user-account expiry

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
