# s1 - Q301 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=5_
**Scope:** sourcetype=linux_secure | source=/var/log/secure | fields=_raw, user, src_ip, host
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- R1: feed discovery — Unix:UserAccounts is /etc/passwd only (no expiration field); osquery:results has no account table and 0 "expired" events; GuardDuty 0 "expired"; only *expir* fields are AWS STS/S3 credential expiry.

## This round
### What I ran
- linux_secure "expired" | stats count by user,src_ip,host -> 0 events
- linux_secure | rex msgtype | stats count by msgtype -> 38 distinct patterns over all 350 events; no expiration message of any kind
- get_raw_events "Accepted publickey" -> 4 events, all ec2-user on ip-172-31-12-76 (mars.i-08e52f8b5a034012d): 166.170.40.8 (x2), 91.207.175.249, 157.97.121.132, same RSA key
- get_raw_events "pam" -> 10 events, only ec2-user session open/close and streamfwd runuser
- linux_secure "Accepted" | stats by user,src_ip,host -> 0 (no password logins)

### What it means
NOT_FOUND: linux_secure does not contain both pieces. The successful-login piece exists but only for ec2-user, and the account-expiration piece is entirely absent — no message in the feed's full 350-event, 38-pattern vocabulary mentions an expired account or expired password. Since nothing shows ec2-user as expired, none of its three source IPs is a candidate. The expiration state must come from another auth feed: ms:aad:signin is the strongest next candidate (it records client IP and sign-in status detail that can flag an expired account), then ms:aad:audit, WinEventLog, and o365:management:activity.

## Ruled out
- linux_secure as expired-account evidence - 0 "expired" events; full message-type enumeration shows no expiration message
- ec2-user logins (166.170.40.8 / 91.207.175.249 / 157.97.121.132) as answer - no record shows ec2-user expired; routine key-based AWS access
- "Accepted password" logins in linux_secure - none exist

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
