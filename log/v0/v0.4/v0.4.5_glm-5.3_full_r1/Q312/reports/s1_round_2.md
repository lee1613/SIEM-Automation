# s1 - Q312 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=3_
**Scope:** sourcetype=o365:management:activity | fields=Operation, ClientIP, ObjectId, ListItemUniqueId, Id, UserId

**Insight:** FOUND
**Candidate:** 7   **Confidence:** 96

## Prior rounds
- Round 1: Established AnonymousLinkUsed as the "use" act; 11 events, all on the .lnk ObjectId, 7 unique ClientIPs; per-IP breakdown fully read (5+1+1+1+1+1+1); ms:o365:management is a duplicate carrier (same 11 Ids); FileAccessed ruled out (authenticated internal access).

## This round
### What I ran
- `index=botsv3 sourcetype=o365:management:activity ListItemUniqueId="0aa10299-8655-4f7e-b293-965cc699f48a" | stats count dc(ClientIP) as unique_ips by Operation` -> 7 of 7 rows: AnonymousLinkCreated(1/1), AnonymousLinkUsed(11/7), FileAccessed(4/4), FileModified(1/1), FileUploaded(1/1), SharingInheritanceBroken(1/1), SharingSet(5/3).
- `... Operation="AnonymousLinkUsed" | stats dc(ObjectId) dc(Id) count dc(ClientIP) values(UserId)` -> 1 ObjectId, 11 distinct Ids, 11 events, 7 unique IPs, userids=[anonymous, bgist@froth.ly, bstoll@froth.ly].
- `... ListItemUniqueId="..." Operation="FileAccessed" | stats count dc(ClientIP) values(UserId)` -> 4 events, 4 IPs, userids=[app@sharepoint, bgist@froth.ly, bstoll@froth.ly, urn:spo:anon#...].

### What it means
Both load-bearing premises are now settled with complete, fully-read aggregations. p1 (coverage): scoping by the file's immutable SharePoint ListItemUniqueId — independent of filename string matching — returns the file's entire operation set in one result with no truncation; the only ClientIP-bearing use activity in that lifecycle is AnonymousLinkUsed (11 events, 7 IPs), while the other six operations are creation, access, upload, modification, and sharing acts. p2 (selection): the consolidated AnonymousLinkUsed aggregation shows exactly one ObjectId, 11 distinct event Ids over 11 events (no duplicates), and 7 distinct ClientIPs, with UserId including "anonymous" — the link-use act. FileAccessed on the same file yields 4 events / 4 IPs with a different user population (authenticated internal users plus one anon principal), so it is not the measure the question asks for. The count is unchanged: **7**.

## Ruled out
- FileAccessed as the measure of "used" — 4 events / 4 IPs, user population is app@sharepoint, bgist@froth.ly, bstoll@froth.ly, one urn:spo:anon: authenticated file access, not anonymous link use.
- Other lifecycle operations (AnonymousLinkCreated, FileUploaded, FileModified, SharingSet, SharingInheritanceBroken) — creation/upload/modification/sharing acts, none is the use act.

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
