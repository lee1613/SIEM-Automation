# s1 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=4_
**Scope:** sourcetype=ms:o365:reporting:messagetrace source=ms_o365_message_trace; sourcetype=o365:management:activity | fields=SenderAddress, Subject, RecipientAddress, Operation, ObjectId
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_source_types / get_sources / get_sourcetype_fields on messagetrace -> 711 events, one source; fields are Sender/Recipient/Subject/Size/MessageId/Status only — NO attachment field in this feed.
- `SenderAddress="bstoll@froth.ly" | stats count by Subject, RecipientAddress | sort Subject` -> 74 rows, 50 returned. Bud's subjects read A–"RE: Craft Brewer Conference": automatic replies, kombucha <EOM>, "I'm making some great changes to brewertalk!", "Improved brewertalk.com - check it out!", "Postmortem on our issue with brewertalk" (to allhands@froth.ly + all 12 employees), "RE: Craft Brewer Conference". 24 rows after "RE: Craft Brewer Conference" unread.
- Subject wildcard miner/coin/crypto/monero/CPU/Splunk -> only "RE: Splunk service needs a restart on your workstations", all replies from other users.
- o365:management:activity "bstoll" -> 9 events, incl. OneDrive FileAccessed on personal/bstoll_froth_ly/Documents/Attachments/"New Beer Styles - Draft.pptm".
- search_keyword miner / coin -> no such fields exist.

### What it means
NOT_FOUND: the attachment has not been located, so the visualization type cannot be read. The messagetrace feed cannot name attachments at all; the attachment must be found in stream:smtp MIME parts, o365:management:activity object paths, or endpoint file logs. Bud's subject list is also incomplete (24 of 74 rows unread, all alphabetically after "RE: Craft Brewer Conference"), so I cannot yet assert which email is his first about the coin miner issue.

## Ruled out
- ms:o365:reporting:messagetrace as the attachment source - carries no attachment-name field (verified via field list).
- "miner"/"coin" as indexed fields or keywords - zero hits.
- "Improved brewertalk.com - check it out!" as the coin-miner-issue email - it is the malware-delivery phish to employees, not an illustration of the miner issue (still the named rival to the Postmortem email).

## Next round
1. `SenderAddress="bstoll@froth.ly" | stats count by Subject | sort Subject` — completes Bud's subject list in one return.
2. o365:management:activity ObjectId="*bstoll*Attachments*" — enumerate Bud's OneDrive attachment files.
3. stream:smtp From bstoll — read MIME attachment filenames via get_raw_events.
4. Pivot on any attachment filename to endpoint file logs to read the visualization type.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="bstoll@froth.ly" |…` (50 of 74 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:reporting:messagetrace" | stats count by Subject | sort S…` (50 of 99 rows seen). A claim resting on them alone is UNVERIFIED._
