# s1 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=ms:o365:reporting:messagetrace | source=ms_o365_message_trace | fields=SenderAddress,RecipientAddress,Subject,DateReceived,MessageId,UserId,Operation,ObjectId,SourceFileName,Workload
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 35

## Prior rounds
Bud confirmed as `btun@froth.ly` in message trace.
Message trace subjects narrowed to a few candidate threads.
Message trace lacks attachment metadata.
Activity logs expose file operations and Exchange operations, but not direct subject linkage.
A suspicious `.lnk` file artifact was seen, but not tied to the Bud email.
No verified attachment filename or visualization type yet.

## This round
### What I ran
- `index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress=btun@froth.ly | stats count ... by MessageId, Subject | sort 0 first_seen` -> 16 candidate message threads; `Craft Brewer Conference` had 12 recipients and the incident-aligned timestamp.
- `index=botsv3 sourcetype=o365:management:activity (Subject=... OR ObjectId=... OR SourceFileName=...)` -> no subject/file linkage for `Craft Brewer Conference`.
- `get_raw_events` on `Upload.aspx` in `o365:management:activity` -> showed OneDrive/SharePoint file access events by `fyodor` and `bgist`, but no explicit tie to Bud's message thread.
### What it means
The most plausible Bud-to-employees coin-miner communication is the full-broadcast `Craft Brewer Conference` thread. That is the right message candidate, but the evidence available in this round still does not expose the first attachment name or its visualization type.

## Ruled out
- `RE: Splunk service needs a restart on your workstations` as the relevant employee-wide coin-miner thread - it is earlier, but it is not the broad all-hands style message seen in the incident pattern.
- Unrelated file artifacts and subject-agnostic SharePoint events - not explicitly tied to the Bud thread.

## Open questions for SH
- Can you confirm whether the incident email thread to focus on is `Craft Brewer Conference`?
- If a filename from the attachment chain has already been observed in another round, provide it so I can identify the visualization type without broadening scope.

## What I'd tell my replacement
- Retired because: This senior established Bud as `btun@froth.ly`, showed message trace lacks attachment metadata, and narrowed the most plausible employee-wide thread to `Craft Brewer Conference`, but after multiple rounds inside O365 evidence it still cannot recover the first attachment or its visualization type. Handoff: carry forward Bud=`btun@froth.ly`, candidate thread=`Craft Brewer Conference`, and the need to prove the first attachment from recipient-side artifacts.
- Scope I owned: sourcetypes=['ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:o365:management'] sources=['ms_o365_message_trace'] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'MessageId', 'AttachmentCount', 'Attachments', 'Operation', 'UserId', 'ObjectId', 'CreationTime']
- Rounds worked: 3/8  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=ms:o365:management UserId=btun@froth.ly | stats count values(Operation) as ops values(Workload) as workloads values(ObjectId) as objects values(SourceFileName) as files values(Site_Url) as sites by UserId
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace (SenderAddress=*bud* OR src_user=*bud* OR orig_src=*bud*) (subject=*miner* OR Subject=*miner* OR subject=*coin* OR Subject=*coin*) | stats min(DateReceived) as first_seen values(Subject) as subjects values(SenderAddress) as senders values(RecipientAddress) as recipients values(MessageId) as msgids by SenderAddress
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress=btun@froth.ly (Subject=coin* OR subject=coin* OR Subject=miner* OR subject=miner* OR Subject=crypt* OR subject=crypt*) | stats min(DateReceived) as first_seen values(Subject) as subjects values(RecipientAddress) as recipients values(MessageId) as msgids values(Status) as status by SenderAddress
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress=btun@froth.ly | stats count as rcpt_count values(RecipientAddress) as recipients values(Subject) as subjects min(DateReceived) as first_seen by MessageId, Subject | sort 0 first_seen
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress=btun@froth.ly | stats count min(DateReceived) as first_seen max(DateReceived) as last_seen values(Subject) as subjects values(RecipientAddress) as recipients values(Status) as statuses by SenderAddress
- index=botsv3 sourcetype=o365:management:activity (Subject="Craft Brewer Conference" OR ObjectId="*Craft Brewer Conference*" OR SourceFileName="*Craft Brewer Conference*") | stats count values(UserId) as users values(Operation) as ops values(ObjectId) as objects values(SourceFileName) as files values(Workload) as workloads
- index=botsv3 sourcetype=o365:management:activity (UserId=btun@froth.ly OR UserId=bgist@froth.ly OR UserId=fyodor@froth.ly OR UserId=bstoll@froth.ly) (Operation=FileUploaded OR Operation=FileModified OR Operation=FilePreviewed OR Operation=FileAccessed) | stats count min(CreationTime) as first_seen max(CreationTime) as last_seen values(ObjectId) as objects values(Workload) as workloads values(ClientIP) as clients by UserId Operation
