# s1 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="bstoll@froth.ly" | stats count by Subject, DateReceived, Size
- index=botsv3 sourcetype=code42:api | stats count by user
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" Subject="*Splunk*" | stats count by Subject, SenderAddress, DateReceived, Size
- index=botsv3 sourcetype="ms:o365:reporting:" (Subject="*restart*" OR Subject="*workstation*") | stats count by Subject, SenderAddress, DateReceived, Size
### What it means



## What I'd tell my replacement
- Retired because: Unproductive handoff. Round 3 produced no findings and no usable argument, and the email/O365 line has not surfaced the attachment after ruling out message-trace and ms:o365:management as direct carriers.
- Scope I owned: sourcetypes=['ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:o365:management'] sources=[] fields=['sender', 'recipient', 'subject', 'attachments', 'MessageTraceId', 'Operation', 'ObjectId', 'UserId', 'ClientIP']
- Rounds worked: 3/8  (iterations: 34, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "coin miner" | stats count by sourcetype, source
- index=botsv3 sourcetype="ms:o365:management" (ObjectId="*.pdf" OR ObjectId="*.png" OR ObjectId="*.jpg" OR ObjectId="*.jpeg" OR ObjectId="*.csv" OR ObjectId="*.xlsx" OR ObjectId="*.pptx" OR ObjectId="*.docx" OR ObjectId="*.xml" OR ObjectId="*.dll" OR ObjectId="*.pptm" OR ObjectId="*.txt" OR ObjectId="*.zip") | stats count by ObjectId
- index=botsv3 sourcetype="ms:o365:management" (ObjectId="*.pdf" OR ObjectId="*.png" OR ObjectId="*.jpg" OR ObjectId="*.jpeg" OR ObjectId="*.csv" OR ObjectId="*.xlsx" OR ObjectId="*.pptx" OR ObjectId="*.docx" OR ObjectId="*.xml" OR ObjectId="*.pdf.dll") | stats count by ObjectId, Operation, UserId, CreationTime
- index=botsv3 sourcetype="ms:o365:management" (ObjectId="*btun*" OR ObjectId="*Attachments*") | stats count by ObjectId, Operation, UserId, CreationTime
- index=botsv3 sourcetype="ms:o365:management" (ObjectId="*miner*" OR ObjectId="*coin*" OR ObjectId="*splunk*" OR ObjectId="*crypto*") | stats count by ObjectId, UserId, Operation
- index=botsv3 sourcetype="ms:o365:management" (SourceFileName="*miner*" OR SourceFileName="*coin*" OR SourceFileName="*splunk*" OR SourceFileName="*crypto*" OR SourceFileName="*monero*" OR SourceFileName="*cpu*") | stats count by SourceFileName, ObjectId, UserId, Operation, CreationTime
- index=botsv3 sourcetype="ms:o365:management" ObjectId="*bstoll*" | stats count by ObjectId, Operation, UserId, CreationTime
- index=botsv3 sourcetype="ms:o365:management" Workload="Exchange" | stats count by Operation, UserId, ObjectId, CreationTime
- index=botsv3 sourcetype="ms:o365:management" | stats count by ObjectId
- index=botsv3 sourcetype="ms:o365:management" | stats count by ObjectId, UserId, Operation, CreationTime
- index=botsv3 sourcetype="ms:o365:management" | stats count by SourceFileName
- index=botsv3 sourcetype="ms:o365:management" | stats count by Workload
- index=botsv3 sourcetype="ms:o365:reporting:" (Subject="*restart*" OR Subject="*workstation*") | stats count by Subject, SenderAddress, DateReceived, Size
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" (Subject="*miner*" OR Subject="*coin*" OR Subject="*crypto*" OR Subject="*monero*" OR Subject="*CPU*") | stats count by Subject, SenderAddress, DateReceived
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="bstoll@froth.ly" | stats count by Subject, DateReceived, Size
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="btun@froth.ly" | stats count by Subject, MessageId, DateReceived
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" Subject="*Splunk*" | stats count by Subject, SenderAddress, DateReceived, Size
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" | stats count by Subject, SenderAddress
- index=botsv3 sourcetype="o365:management:activity" (UserId="btun@froth.ly" OR UserId="Bud" OR Sender="btun@froth.ly") | stats count by Operation, Workload
- index=botsv3 sourcetype="o365:management:activity" UserId="btun@froth.ly" | stats count by Operation
- index=botsv3 sourcetype="o365:management:activity" | stats count by UserId, Operation
- index=botsv3 sourcetype="stream:smtp" (search "miner" OR search "coin" OR search "monero" OR search "cryptocurrency") | stats count by src_ip, timestamp
- index=botsv3 sourcetype=code42:api | stats count by user
