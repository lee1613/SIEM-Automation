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