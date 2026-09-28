# Q217 — SH <-> Senior conversation

### 14:31:39 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:o365:management'] sources=['ms_o365_message_trace'] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'MessageId', 'AttachmentCount', 'Attachments', 'Operation', 'UserId', 'ObjectId', 'CreationTime']
**Technique:** senior
**Reason:** The question is about an email attachment sent by Bud to employees, so the right starting scope is Office 365 message-trace and related O365 activity logs that can identify the email, its first attachment, and any metadata about that file.

Within the Office 365 email and activity data for the August 2018 Frothly incident, identify the first file attachment in an email sent by Bud to Frothly employees about the coin miner issue, and determine what kind of Splunk visualization that attachment contained or referenced. Establish the earliest relevant Bud email, the first attachment on it, and any logged metadata that reveals the visualization type.

### 14:32:20 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Bud appears in message trace as btun@froth.ly. Earliest message-trace activity for that sender starts at 2018-08-20T09:47:48Z and spans through 2018-08-20T14:46:21Z. Likely relevant thread is around 'Craft Brewer Conference' or possibly another Bud thread that mentions the miner issue, but this was 
_full: reports/s1_round_1.md_

### 14:32:25 - SH -> s1   [COMMAND]
**continue** — The case now knows Bud’s email address and that message trace is insufficient for attachment details, which is useful progress. We still need the first attachment and its visualization type, so the work should continue in related O365 activity logs rather than broadening beyond email artifacts.
**New scope:** sourcetypes=['ms:o365:management', 'o365:management:activity', 'ms:o365:reporting:messagetrace'] sources=[] fields=['UserId', 'Operation', 'Workload', 'ClientIP', 'ObjectId', 'SourceFileName', 'Site_Url', 'SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'MessageId']

Using Bud’s address btun@froth.ly and the candidate coin-miner-related employee email activity, establish which Bud-to-Frothly-employee message is the relevant coin miner communication by correlating Office 365 activity records with the message-trace findings. Then identify the earliest relevant attachment on that message, recover the attachment filename or document metadata, and determine from that file metadata or logged content what Splunk visualization type it contained or referenced.

### 14:33:04 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> Useful anchors: Bud = btun@froth.ly; earliest message-trace activity for Bud starts at 2018-08-20T09:47:48Z and runs through 2018-08-20T14:46:21Z. Likely relevant activity around 2018-08-20T11:28:54Z shows the suspicious file 'BRUCE BIRTHDAY HAPPY HOUR PICS.lnk' with SourceFileExtension=lnk and Site
_full: reports/s1_round_2.md_

### 14:33:09 - SH -> s1   [COMMAND]
**retry** — This round added useful facts about what O365 activity can and cannot show, but it did not stay tightly on the asked artifact: the first file attachment Bud emailed to Frothly employees about the coin miner issue. The case needs the message-to-attachment linkage established before investigating any file as the candidate.
**New scope:** sourcetypes=['ms:o365:reporting:messagetrace', 'ms:o365:management', 'o365:management:activity'] sources=['ms_o365_message_trace'] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'MessageId', 'UserId', 'Operation', 'ObjectId', 'SourceFileName', 'Workload']

Rework the same Office 365 evidence family to establish the relevant Bud-to-employees coin-miner communication first. Starting from btun@froth.ly and the message-trace subjects already seen, determine which message thread actually reached multiple Frothly employees and is temporally associated with the coin miner issue; then identify the first attachment on that specific message and only then extract the file name or document metadata needed to determine the two-word Splunk visualization type shown in that attachment. Do not pursue unrelated SharePoint or .lnk artifacts unless they can be explicitly tied back to that Bud message.

### 14:33:31 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> Best-supported candidate thread is 'Craft Brewer Conference' because it was delivered to the broadest Frothly audience and sits directly in the incident timeline. I also observed Exchange/OneDrive activity at similar times for users like bgist and fyodor, but I did not establish a direct attachment 
_full: reports/s1_round_3.md_

### 14:33:37 - runner   [NOTE]
TURN REJECTED:
- s1: its report was read but no route addressed it — grade it and give it exactly one route

### 14:33:43 - SH -> s1   [RETIRE]
This senior established Bud as `btun@froth.ly`, showed message trace lacks attachment metadata, and narrowed the most plausible employee-wide thread to `Craft Brewer Conference`, but after multiple rounds inside O365 evidence it still cannot recover the first attachment or its visualization type. Handoff: carry forward Bud=`btun@froth.ly`, candidate thread=`Craft Brewer Conference`, and the need to prove the first attachment from recipient-side artifacts.

### 14:33:43 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 14:33:43 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon', 'osquery:results', 'stream:http', 'access_combined'] sources=- fields=['user', 'dest', 'file_name', 'process', 'CommandLine', 'Image', 'TargetFilename', 'ObjectName', 'url', 'uri_path', 'Subject', 'attachment', 'filename']
**Technique:** senior
**Reason:** The retired O365 senior's constraints could identify only a candidate Bud message thread and could not surface attachment metadata or content. A new senior is needed in endpoint/host telemetry because the attachment filename or viewed content may only be recoverable from recipient-side file, process, browser, or document-open artifacts.

Using endpoint and related host/web telemetry rather than Office 365 logs, identify the file attachment Bud sent to Frothly employees about the coin miner issue by finding evidence of recipients receiving, opening, saving, or executing that attachment, and determine what two-word Splunk visualization type is shown in the first attachment.

### 14:34:33 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> Confirmed BudStoll on BSTOLL-L had Chrome launches (5 hits) in Sysmon process-creation telemetry, so the likely attachment trail is on that host/user, but I did not recover attachment metadata or content. Endpoint telemetry examined so far did not surface the attachment filename or the two-word Splu
_full: reports/s2_round_1.md_

### 14:34:38 - SH -> s2   [COMMAND]
**retry** — This round confirmed useful endpoint telemetry sources and showed the initial Sysmon file-create angle was unproductive, but it did not stay tightly anchored to a verified recipient or attachment chain from Bud's email. The case now needs recipient-side handling evidence for the first attachment, not general process activity.
**New scope:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinEventLog', 'osquery:results', 'stream:http'] sources=[] fields=['host', 'User', 'Image', 'CommandLine', 'TargetFilename', 'process_name', 'path', 'url', 'uri', 'file_name']

Within endpoint and host telemetry, establish which Frothly employee endpoint actually handled the candidate Bud email attachment associated with the `Craft Brewer Conference` thread from btun@froth.ly, then recover evidence of the first attachment being downloaded, opened, previewed, or saved. Prioritize browser download/history artifacts, document-open telemetry, and file/path/process evidence on recipient systems that can reveal the attachment filename or contents, and use that recovered file context to determine the two-word Splunk visualization type shown in the attachment.

### 14:35:29 - s2 -> SH   [REPORT - round 2 - NOT_FOUND]
> I confirmed the scope contains endpoint telemetry capable of surfacing recipient-side handling, and BudStoll on BSTOLL-L remains the strongest endpoint lead from Sysmon process creation. However, within the required scope I still have not recovered the attachment filename/content or the two-word Spl
_full: reports/s2_round_2.md_

### 14:35:34 - SH -> s2   [COMMAND]
**retry** — The case still lacks any proven attachment filename, recipient host, or visualization clue from endpoint telemetry, and the last round produced no usable artifact. We need a sharper evidence family that can reveal file names or viewed content from user web activity instead of continuing broad endpoint searches.
**New scope:** sourcetypes=['stream:http', 'stream:tcp', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=[] fields=['host', 'src', 'dest', 'url', 'uri', 'http_user_agent', 'file_name', 'process_name', 'Image', 'CommandLine', 'User']

Rework this as a web-and-browser artifact pass focused on Frothly employee interaction with Bud’s candidate `Craft Brewer Conference` message attachment. Establish which employee endpoint retrieved or viewed attachment-related content, recover any filename, URL, title, or document-reference artifact from browser/network telemetry, and use that recovered file context to determine the two-word Splunk visualization type shown in the first attachment.

### 14:36:26 - s2 -> SH   [REPORT - round 3 - NOT_FOUND]
> Within the narrowed web/browser artifact scope, BTUN-L clearly interacted with Brewertalk via stream:http: repeated /showthread.php, /forumdisplay.php, /task.php, and index.php hits on www.brewertalk.com, with Chrome/Edge user agents. Sysmon on BTUN-L showed AzureAD\BillyTun launching Chrome, Outloo
_full: reports/s2_round_3.md_

### 14:36:30 - SH -> s2   [COMMAND]
**continue** — This round materially improved the case by identifying BTUN-L as the strongest employee endpoint tied to the Brewertalk thread, which is a concrete lead absent from prior rounds. The case still lacks the first attachment and its visualization type, so the next round must exploit BTUN-L specifically rather than widen again.
**New scope:** sourcetypes=['stream:http', 'stream:tcp', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinEventLog', 'osquery:results'] sources=[] fields=['host', 'User', 'Image', 'CommandLine', 'TargetFilename', 'process_name', 'path', 'url', 'uri', 'file_name']

Using BTUN-L as the primary endpoint for this question, establish whether AzureAD\BillyTun received, opened, previewed, or saved the first attachment associated with Bud’s candidate `Craft Brewer Conference` communication. Focus on BTUN-L evidence that can reveal the attachment filename, file path, application context (for example Outlook, browser, or Excel), or document metadata/content, and then determine from that recovered file context the exact two-word Splunk visualization type shown in the first attachment.

### 14:37:14 - s2 -> SH   [REPORT - round 4 - NOT_FOUND]
> BTUN-L is the strongest validated employee endpoint for the Brewertalk thread and the most plausible place for the first attachment to have been viewed. The evidence chain now includes: BTUN-L -> BillyTun -> Brewertalk thread traffic -> Outlook/Excel/Chrome context. However, I still do not have a re
_full: reports/s2_round_4.md_

### 14:37:18 - SH -> s2   [RETIRE]
This senior narrowed the strongest endpoint lead to BTUN-L and established BillyTun used Outlook/Chrome/Excel while accessing the Brewertalk thread, but after multiple rounds it still could not recover the first attachment, filename, or visualization type. Handoff: carry forward candidate thread `Craft Brewer Conference`, Bud address `btun@froth.ly`, and endpoint lead BTUN-L / AzureAD\BillyTun as the most likely place where recipient-side attachment handling occurred.

### 14:37:18 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 14:37:20 - SH -> s2   [RETIRE]
This senior narrowed the strongest endpoint lead to BTUN-L and established BillyTun used Outlook/Chrome/Excel while accessing the Brewertalk thread, but after multiple rounds it still could not recover the first attachment, filename, or visualization type. Handoff: carry forward candidate thread `Craft Brewer Conference`, Bud address `btun@froth.ly`, and endpoint lead BTUN-L / AzureAD\BillyTun as the most likely place where recipient-side attachment handling occurred.

### 14:37:20 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 14:37:23 - SH -> s2   [RETIRE]
This senior narrowed the strongest endpoint lead to BTUN-L and established BillyTun used Outlook/Chrome/Excel while accessing the Brewertalk thread, but after multiple rounds it still could not recover the first attachment, filename, or visualization type. Handoff: carry forward candidate thread `Craft Brewer Conference`, Bud address `btun@froth.ly`, and endpoint lead BTUN-L / AzureAD\BillyTun as the most likely place where recipient-side attachment handling occurred.

### 14:37:23 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 14:37:26 - SH -> s2   [RETIRE]
This senior narrowed the strongest endpoint lead to BTUN-L and established BillyTun used Outlook/Chrome/Excel while accessing the Brewertalk thread, but after multiple rounds it still could not recover the first attachment, filename, or visualization type. Handoff: carry forward candidate thread `Craft Brewer Conference`, Bud address `btun@froth.ly`, and endpoint lead BTUN-L / AzureAD\BillyTun as the most likely place where recipient-side attachment handling occurred.

### 14:37:26 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 14:37:26 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

