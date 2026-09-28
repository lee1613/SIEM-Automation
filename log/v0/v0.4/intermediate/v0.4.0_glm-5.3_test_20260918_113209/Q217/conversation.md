# Q217 — SH <-> Senior conversation

### 11:32:38 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['ms:o365:management', 'ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:aad:signin', 'code42:security', 'code42:user', 'code42:computer'] sources=- fields=['sender', 'recipient', 'subject', 'attachment', 'attachments', 'file_name', 'message_id', 'user', 'operation', 'workload', 'path', 'url']
**Technique:** content
**Reason:** The question hinges on email content and an attached file; this scope covers O365/mail activity and adjacent user/file telemetry without assuming the attachment lives in a single feed.

Identify the first file attachment in emails Bud sent to Frothly employees about the coin miner issue, and establish what kind of Splunk visualization appears in that attachment. Start by locating the relevant outbound email(s), confirming the earliest attachment, and then determining whether any indexed content or related telemetry reveals the visualization type shown in that file.

### 11:35:45 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Bud = btun@froth.ly (confirmed sender in ms:o365:reporting:messagetrace). His 13 outbound subjects: "Beer bath!", "Craft Brewer Conference", "FW: Bruce Gist", "IoT brewery stuff", "Motivation... through beer", "RE: Bruce Gist", "RE: Craft Brewer Conference", "RE: Improved brewertalk.com - check it o
_full: reports/s1_round_1.md_

### 11:35:50 - SH -> s1   [COMMAND]
**continue** — The case now has Bud identified as btun@froth.ly and a likely earliest coin-miner-related outbound thread, but the attachment and visualization are still unestablished. We need the first attachment proven from mail evidence before we can name the chart type.
**New scope:** sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp', 'o365:management:activity'] sources=[] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'ObjectId', 'Operation', 'content_type']

Establish whether Bud's earliest relevant outbound message is the 2018-08-20 email with subject 'RE: Splunk service needs a restart on your workstations' by examining Bud-to-employees mail evidence first, then determine the first attached file on that message. Prioritize raw SMTP/MIME content around 2018-08-20T09:47:48Z for Bud's outbound mail to Frothly recipients to recover attachment filename or MIME parts; if that does not surface the attachment, use the Exchange-workload events within o365:management:activity to identify the same message and any attachment-related artifact. Once the first attachment is identified, establish whether its content is indexed anywhere in the mail/security/file telemetry and extract the two-word Splunk visualization type shown in that file.

### 11:39:28 - s1 -> SH   [REPORT - round 2 - FOUND]
> ANSWER TO SH'S ROUND ASK: (1) YES — Bud's earliest relevant outbound message is "RE: Splunk service needs a restart on your workstations" (btun@froth.ly, 2018-08-20T09:47:48Z, 11 recipients incl. allhands@froth.ly); it is Bud's earliest outbound email in the entire dataset. BUT it carries NO attachm
_full: reports/s1_round_2.md_

### 11:39:33 - SH -> s1   [COMMAND]
**retry** — The case now has evidence about Bud's first attachment overall, but the question asks for the first attachment in Bud's emails to Frothly employees about the coin miner issue, which may be a narrower set than Bud's mail in general. We must first establish the correct coin-miner-related employee thread before deriving the attachment and visualization.
**New scope:** sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp', 'o365:management:activity'] sources=[] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'content_type', '_raw', 'Operation', 'ObjectId']

Establish which Bud-to-Frothly-employees email thread is actually about the coin miner issue by examining Bud's outbound subjects, recipients, and any recoverable body text in mail telemetry, with priority on employee-facing messages around the Splunk-service storyline. If the 2018-08-20 'RE: Splunk service needs a restart on your workstations' thread is the relevant incident communication, determine whether a later message in that same thread carries the first attachment and identify it; if not, identify the correct employee-facing coin-miner thread and its first attachment. Once that in-scope attachment is confirmed, determine whether its content is reflected in raw MIME, file activity, or endpoint telemetry strongly enough to name the two-word Splunk visualization type shown in it.

### 11:42:35 - s1 -> SH   [REPORT - round 3 - FOUND]
> ANSWER STATE: Attachment candidate = pwned.jpg (Bud's first outbound attachment to a Frothly employee, 2018-08-20T10:24:29Z, thread "RE: meeting with F" to pcerf@froth.ly). VISUALIZATION TYPE = NOT ESTABLISHED — I could not decode or read the jpg; do not treat any chart name as found. KEY DISCOVERY 
_full: reports/s1_round_3.md_

### 11:42:42 - SH -> s1   [COMMAND]
**continue** — The senior uncovered a stronger path inside the existing scope: structured MIME attachment fields and full content in stream:smtp. The case still needs the coin-miner employee thread proven, then the attachment's visualization type established from whatever indexed representation exists.
**New scope:** sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp', 'o365:management:activity'] sources=[] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'content_type', '_raw', 'content', 'attach_filename', 'attach_type', 'attach_size', 'attach_disposition', 'attach_transfer_encoding', 'Operation', 'ObjectId']

Use the newly discovered stream:smtp attachment structures and full MIME content to establish, from Bud's outbound mail to Frothly recipients on 2018-08-20, which message chain is the employee communication about the coin miner issue and which attached file is first within that in-scope set. Start by enumerating Bud's outbound attachment-bearing employee emails with subject, recipient, timestamp, and attachment metadata recovered from the MIME structures; then read recoverable body/HTML text for those messages to confirm whether the topic is the Splunk service / coin-miner incident rather than an unrelated thread. Once the in-scope attachment is confirmed, determine whether the attachment itself or its surrounding HTML/body text names or visually implies a Splunk visualization type, and if necessary use adjacent endpoint or file-access telemetry only for that exact filename and time window to recover the two-word chart type.

### 11:46:05 - s1 -> SH   [REPORT - round 4 - FOUND]
> DELIVERABLE STATE: (1) First attachment candidate = pwned.jpg — Bud's FIRST outbound attachment to a Frothly employee (2018-08-20T10:24:29Z, thread "RE: meeting with F", to pcerf@froth.ly, image/jpeg, 87446 bytes decoded, multipart/mixed). It is structurally the ONLY possible answer: Bud sent exactl
_full: reports/s1_round_4.md_

### 11:46:12 - SH -> s1   [COMMAND]
**retry** — The case has likely identified the attachment, but this scope is no longer producing a path to the two-word visualization answer from mail evidence alone. We need to follow the exact artifact pwned.jpg into telemetry that can reveal what the image depicted.
**New scope:** sourcetypes=['osquery:results', 'symantec:ep:agent:file', 'symantec:ep:traffic:file', 'symantec:ep:packet:file', 'symantec:ep:behavior:file', 'code42:security', 'code42:user', 'o365:management:activity', 'stream:http', 'stream:smb'] sources=[] fields=['filename', 'path', 'ObjectId', 'FileName', 'dest', 'src', 'user', 'attachment', 'process', 'url']

Establish whether the attachment filename pwned.jpg appears in any indexed artifact, endpoint, or file-access telemetry tied to Bud, pcerf@froth.ly, or Fyodor-related systems around 2018-08-20, and use that to recover what the image showed. Shift focus away from general mail-thread inference: start from the exact filename pwned.jpg and the attached-message time window, then look for adjacent file handling, extraction, preview, download, endpoint inventory, or security telemetry that can expose image metadata, path, caption, or analyst-readable context sufficient to name the Splunk visualization type shown in the image. If no direct filename hit exists, establish where Bud's attachment-related artifacts would surface outside mail feeds and pursue only those sources.

### 11:48:39 - s1 -> SH   [REPORT - round 5 - NOT_FOUND]
> WHAT IS ESTABLISHED: (1) Bud = btun@froth.ly, workstation BTUN-L (192.168.3.130). (2) Bud's FIRST attachment to a Frothly employee = pwned.jpg, sent 2018-08-20T10:24:29Z in thread "RE: meeting with F" to pcerf@froth.ly (image/jpeg, 87446 bytes decoded, multipart/mixed). It is structurally the only p
_full: reports/s1_round_5.md_

### 11:48:45 - SH -> s1   [COMMAND]
**retry** — The case still lacks the two-word visualization type, and the current artifact sweep did not surface text describing the image. We now have a precise filename, host, and minute-scale window, so the investigation should pivot to endpoint and storage traces that can expose the file on disk or related analyst context.
**New scope:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon', 'osquery:results', 'aws:s3:accesslogs', 'aws:s3:accesslogs', 'stream:http'] sources=[] fields=['Image', 'TargetFilename', 'CommandLine', 'process', 'path', 'file_name', 'url', 'src', 'dest', 'user', 'ObjectId', '_raw']

Establish whether pwned.jpg left any on-disk, process, preview, browser-cache, or storage trace on BTUN-L or related Frothly systems immediately after the 2018-08-20 temp-e.net download and before or after Bud attached it. Start from the exact artifact chain already established — BTUN-L, 192.168.3.130, temp-e.net/files/incoming/hoffa/pwned.jpg, download at 2018-08-20T10:22:47Z, attachment at 10:24:29Z — and determine where that file appears in endpoint telemetry or artifact repositories strongly enough to reveal what the image showed or how it was labeled. If direct filename hits fail, establish adjacent evidence such as browser activity, file creation/access, email client temp paths, or related files in the same hoffa directory that could disclose the Splunk visualization type depicted in pwned.jpg.

### 11:51:19 - s1 -> SH   [REPORT - round 6 - NOT_FOUND]
> FINAL STATE. SOLVED HALF — first attachment: pwned.jpg. Bud (btun@froth.ly, workstation BTUN-L) sent exactly two attachments on 2018-08-20; pwned.jpg (10:24:29Z, "RE: meeting with F" to pcerf@froth.ly, image/jpeg, 87446B decoded) is the first. Full provenance: downloaded by Bud from http://temp-e.ne
_full: reports/s1_round_6.md_

### 11:51:26 - SH -> s1   [COMMAND]
**retry** — The case has the attachment and host chain, but not the visualization type, and the endpoint pivot has now stalled on that exact requirement. We need a different evidence path that can still describe the image without decoding it.
**New scope:** sourcetypes=['stream:smtp', 'stream:http', 'ms:o365:reporting:messagetrace'] sources=[] fields=['content', '_raw', 'attach_filename', 'url', 'src', 'dest', 'Subject', 'RecipientAddress', 'DateReceived']

Return to content-bearing evidence for the exact artifact chain already established: pwned.jpg on 2018-08-20 from temp-e.net/files/incoming/hoffa/, Bud on BTUN-L, recipient PCERF-L, and the outbound message at 10:24:29Z. First establish whether the full text/html or MIME structure of that specific Bud email, including any surrounding headers, adjacent MIME parts, or related messages in the same thread, contains descriptive text about the image or the coin-miner issue. If that yields nothing, use the confirmed hoffa download location and the second HTTP event around 10:23:37Z to determine whether related files, directory references, referrers, or neighboring fetched objects expose the Splunk visualization type associated with pwned.jpg. Do not extend back into generic endpoint sweeps; focus only on content or related web objects tied to this exact file and minute-scale window.

### 11:52:48 - s1 -> SH   [REPORT - round 7 - NOT_FOUND]
> FINAL STATE AFTER 7 ROUNDS. SOLVED: first attachment = pwned.jpg. Bud (btun@froth.ly, workstation BTUN-L/192.168.3.130) sent exactly two attachments on 2018-08-20; pwned.jpg (10:24:29Z, "RE: meeting with F" to pcerf@froth.ly, image/jpeg, 87446B decoded, multipart/mixed) is the first. Complete proven
_full: reports/s1_round_7.md_

### 11:52:52 - SH -> s1   [RETIRE]
This senior is done for now: it proved the attachment chain for pwned.jpg and exhausted mail, HTTP, and endpoint text evidence without recovering the two-word visualization type. The unresolved handoff is narrow and durable: any future work must target a source that can reveal the image contents or an indexed artifact derived from the image itself, because current evidence does not literally establish the chart type.

### 11:52:52 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 11:52:57 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['aws:s3:accesslogs', 'access_combined', 'apache_error', 'stream:http', 'stream:ip', 'osquery:results', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon'] sources=- fields=['url', 'uri', 'src', 'dest', 'filename', 'path', 'TargetFilename', 'Image', 'CommandLine', '_raw']
**Technique:** hunter
**Reason:** The retired senior’s constraints were centered on mail/HTTP text and nearby endpoint traces; they proved the attachment lineage but could not recover image content. A fresh senior is needed to own residual artifact-bearing sources and hunt for any indexed representation of the image itself or a derivative that can literally establish the chart type.

Using the established artifact chain for Bud’s 2018-08-20 attachment pwned.jpg, determine whether any indexed source outside the retired senior’s exhausted mail-thread analysis preserves the image itself, a thumbnail, a preview, a cached copy, a web-server reference, or any derived artifact that literally reveals what Splunk visualization type the image shows. Start from the exact filename, the temp-e.net/hoffa web path, BTUN-L, PCERF-L, and the 10:22-10:25Z window, and prove or disprove any source that can expose the image content or an explicit description of it.

### 12:01:03 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> The artifact chain is name-closed: an exhaustive index-wide enumeration for the string "pwned" returns only 4 sources, so no thumbnail, preview, AV-quarantine copy, S3 object, or DLP record exists under that filename anywhere else. What each surviving source holds: (1) stream:Splunk_HTTPURI is a byt
_full: reports/s2_round_1.md_

### 12:01:06 - SH -> s2   [RETIRE]
This senior is cut off, not finished: it narrowed the remaining possibilities to the single oversized SMTP artifact or a minute-scale temp-e.net web retrieval path, but did not recover the image content or a literal chart-type description. With no rounds remaining, retire with the unresolved gap recorded rather than force an unsupported answer.

### 12:01:06 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 12:01:06 - runner   [NOTE]
question ended: rounds — falling back to 'pwned.jpg'

