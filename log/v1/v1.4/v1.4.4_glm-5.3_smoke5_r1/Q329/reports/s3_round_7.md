# s3 - Q329 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## This round
### What I ran
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "BRUCE BIRTHDAY" | stats count by EventCode
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "BRUCE BIRTHDAY" EventCode=11 | stats count by TargetFilename, Image
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "morebeer" OR "stout" | stats count by EventCode, TargetFilename
- index=botsv3 sourcetype=stream:smtp "BRUCE BIRTHDAY" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, subj, attaches
### What it means
NO VERIFIED WORD — value empty. WHAT THIS ROUND ESTABLISHED: (1) ACTOR NAMING TIE (behavioral, not literal): every web operation from attacker IP 104.207.83.63 carries UserAgent "NaenaraBrowser/3.5b4" with locale ko-KP — Naenara is the North Korean intranet browser. This is the strongest in-data tie to the question's name "Taedonggang" (North Korean beer brand); the literal string still appears nowhere (p1 unverified). (2) THE UPLOADED FILE SET is bgist's four from 104.207.83.63 at 09:57:17-33 on 2018-08-20: morebeer.jpg, stout-2.jpg, stout.png, BRUCE BIRTHDAY HAPPY HOUR PICS.lnk (OneDrive Documents/Birthday Pictures). (3) CONTENT UNREADABLE IN ALL REACHED FEEDS: O365 raw events are metadata-only (ObjectId/ListId/CorrelationId, no bytes); the three images appear in NO Sysmon event (0 hits)

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
