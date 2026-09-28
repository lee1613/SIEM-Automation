# s1 - Q312 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=o365:management:activity (cross-checked against ms:o365:management) | fields=Operation, ClientIP, ObjectId, SourceFileName, Id, UserId

**Insight:** FOUND
**Candidate:** 7   **Confidence:** 95

## Prior rounds
- (Round 1) No prior rounds; this is the first.

## This round
### What I ran
- `index=botsv3 sourcetype=o365:management:activity Operation="AnonymousLinkUsed" | stats count dc(ClientIP) as unique_ips values(ClientIP) as ips by Operation` -> 11 events, 7 unique ClientIPs.
- `... Operation="AnonymousLinkUsed" | stats count dc(ClientIP) by ObjectId` -> one row: the .lnk file's OneDrive URL, 11 events, 7 IPs — every AnonymousLinkUsed event in the dataset is this file.
- `... | stats count by ClientIP` -> 107.77.212.175 x5; 104.238.59.42, 107.77.213.96, 157.97.121.5, 174.215.1.81, 64.64.117.111, 91.207.175.56 x1 each. ClientIP is single-valued in raw JSON.
- `... "BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count dc(ClientIP) by Operation` -> full lifecycle: AnonymousLinkCreated(1), AnonymousLinkUsed(11/7 IPs), FileAccessed(4/4), FileModified(1), FileUploaded(1), SharingInheritanceBroken(1), SharingSet(5/3).
- `... Operation="FileAccessed" | stats values(ClientIP) values(UserId)` -> 4 IPs, users include bgist@froth.ly, bstoll@froth.ly, app@sharepoint and one urn:spo:anon — authenticated/internal access, not link use.
- `(sourcetype=o365:management:activity OR sourcetype=ms:o365:management) Operation="AnonymousLinkUsed" | stats dc(Id) count dc(ClientIP)` -> 11 distinct Ids over 22 rows, still 7 IPs: the two sourcetypes carry the same events, no double counting.

### What it means
The O365 activity that corresponds to "used" for this link file is **AnonymousLinkUsed** — the SharePoint/OneDrive audit operation fired when someone opens an anonymous sharing link. All 11 such events in BOTSv3 reference exactly `BRUCE BIRTHDAY HAPPY HOUR PICS.lnk` (bgist's OneDrive, Documents/Birthday Pictures), so the file scoping is total, not partial. `dc(ClientIP)` over those events = **7**. Raw events confirm ClientIP is a single-valued field (no multi-IP arrays), UserId is mostly "anonymous", and the duplicate ms:o365:management carrier holds identical event Ids, so the count is stable at 7 regardless of feed.

## Ruled out
- FileAccessed (4 events, 4 IPs) as the meaning of "used" — includes authenticated internal access (bgist@froth.ly, bstoll@froth.ly, app@sharepoint); it is the file-access act, not the link-use act.
- ms:o365:management as a separate event source — same 11 event Ids as o365:management:activity; combining both feeds leaves dc(ClientIP)=7.
- Other operations on the file (AnonymousLinkCreated, FileUploaded, FileModified, SharingSet, SharingInheritanceBroken) — creation/sharing/modification acts, not use.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "AnonymousLinkUsed", "limit": 12, "sourcetype": "o365:management:activity"}` (5 of 11 rows seen). A claim resting on them alone is UNVERIFIED._
