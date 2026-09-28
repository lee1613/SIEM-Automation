# s1 - Q301 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="ms:aad:signin" expired | stats count by userPrincipalName, ipAddress, status.failureReason, resultDescription
- index=botsv3 sourcetype="ms:aad:signin" | stats count by status.failureReason
- index=botsv3 sourcetype="ms:aad:signin" | stats count by failureReason, signinErrorCode
- index=botsv3 sourcetype="ms:aad:signin" signinErrorCode=50055 | stats count by userPrincipalName, ipAddress, loginStatus, appDisplayName
### What it means
Intention: Check whether klagerfield@froth.ly has any successful sign-in (loginStatus=Success) in ms:aad:signin, and from which IP.


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['linux_secure', 'osquery:results', 'Unix:UserAccounts', 'lastlog', 'who'] sources=[] fields=['src_ip', 'rhost', 'user', 'uid', '_time', 'username', 'account_expires', 'password_expires', 'shell', 'host']
- Rounds worked: 3/3  (iterations: 28, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype="aws:cloudwatch:guardduty" expired | stats count by detail.findingId, detail.type, detail.description
- index=botsv3 sourcetype="ms:aad:signin" expired | stats count by userPrincipalName, ipAddress, status.failureReason, resultDescription
- index=botsv3 sourcetype="ms:aad:signin" signinErrorCode=50055 | stats count by userPrincipalName, ipAddress, loginStatus, appDisplayName
- index=botsv3 sourcetype="ms:aad:signin" | stats count by failureReason, signinErrorCode
- index=botsv3 sourcetype="ms:aad:signin" | stats count by status.failureReason
- index=botsv3 sourcetype=linux_secure "Accepted publickey" | stats count by _raw
- index=botsv3 sourcetype=linux_secure "Accepted" | stats count by user, src_ip, host
- index=botsv3 sourcetype=linux_secure expired | stats count by user, src_ip, host
- index=botsv3 sourcetype=linux_secure | rex field=_raw "sshd\[\d+\]: (?<msgtype>[A-Za-z ]+)" | stats count by msgtype
- index=botsv3 sourcetype=linux_secure | stats count by host
- index=botsv3 sourcetype=osquery:results expired
- index=botsv3 sourcetype=osquery:results expired | stats count by name, action, host
- index=botsv3 sourcetype=osquery:results | stats count by name
