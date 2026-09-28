# s2 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=aws:cloudtrail "taedonggang" | stats count by eventName, requestParameters.bucketName
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "taedonggang" | stats count by SenderAddress, RecipientAddress
- index=botsv3 sourcetype=stream:smtp "taedonggang" | stats count by src_ip, mailfrom
- index=botsv3 sourcetype=code42:api "taedonggang" | stats count by sourcetype, source
### What it means
Intention: code42 has no hit; check the remaining file-bearing feeds (symantec file events, osquery results, WinHostMon) for "Taedonggang" as a file name or path.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
