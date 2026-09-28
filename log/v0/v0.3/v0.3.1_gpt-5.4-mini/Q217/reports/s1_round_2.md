# s1 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=2_
**Scope:** sourcetype=ms:o365:management | source=none | fields=UserId,Operation,Workload,ClientIP,ObjectId,SourceFileName,Site_Url,SenderAddress,RecipientAddress,Subject,DateReceived,MessageId
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
Bud confirmed as `btun@froth.ly` in message trace.
Message trace shows Bud's subjects, including `Craft Brewer Conference` and `RE: Splunk service needs a restart on your workstations`.
Message trace does not expose attachment metadata.
Activity feed is heavily SharePoint/OneDrive; Bud is not a direct UserId hit there.
Suspicious file artifact exists: `BRUCE BIRTHDAY HAPPY HOUR PICS.lnk` with SharePoint metadata.
No verified attachment filename or visualization type yet.

## This round
### What I ran
- `index=botsv3 sourcetype=ms:o365:management UserId=btun@froth.ly | stats ...` -> no results.
- `get_field_values UserId` on `ms:o365:management` -> no Bud UserId; common users were `app@sharepoint`, `bgist@froth.ly`, `fyodor@froth.ly`, `bstoll@froth.ly`.
- `get_field_values Operation` on `ms:o365:management` -> file and Exchange operations identified.
- `get_raw_events` on `o365:management:activity` keyword `Exchange` -> showed Exchange admin events and SharePoint search events.
- `run_splunk_search` for file operations by candidate users -> revealed `bgist@froth.ly` file activity and `fyodor@froth.ly` previewed PDFs, plus the suspicious `BRUCE BIRTHDAY HAPPY HOUR PICS.lnk` object.
- `get_raw_events` on `BRUCE BIRTHDAY HAPPY HOUR PICS.lnk` -> raw event exposed `SourceFileName`, `SourceFileExtension=lnk`, `SiteUrl`, `ObjectId`, `UserId`, `Workload`.
### What it means
I have enough to say the activity logs contain a likely malicious file artifact, but I have not yet correlated it to Bud's coin-miner email or derived the visualization type from attachment metadata/content. The evidence remains incomplete for a solved answer.

## Ruled out
- `ms:o365:reporting:messagetrace` as a source of attachment metadata - only delivery fields are present.
- Direct `UserId=btun@froth.ly` in `o365:management:activity` - no hits.
- Coin/miner subject token search on Bud's sender address - no direct match returned with the available searches.

## Open questions for SH
- Is the Bud email thread expected to be `Craft Brewer Conference`, or is there another named thread already known from prior rounds?
- If the attachment filename is already known from another finding, provide it so I can connect it to O365 activity metadata in a follow-up round.

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
