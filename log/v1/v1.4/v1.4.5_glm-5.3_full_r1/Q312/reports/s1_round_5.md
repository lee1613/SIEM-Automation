# s1 - Q312 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=0_
**Scope:** sourcetype=o365:management:activity | fields=Operation, ClientIP, ObjectId, ListItemUniqueId, Id, UserId

**Insight:** FOUND
**Candidate:** 7   **Confidence:** 96

## Prior rounds
- Round 1: Established AnonymousLinkUsed as the "use" act; 11 events, all on the .lnk ObjectId, 7 unique ClientIPs; per-IP breakdown fully read; ms:o365:management is a duplicate carrier; FileAccessed ruled out.
- Round 2: Settled p1 via ListItemUniqueId lifecycle query (7 of 7 operations returned); consolidated AnonymousLinkUsed aggregation (1 ObjectId, 11 Ids, 7 IPs); FileAccessed contrast.
- Round 3: Ran the two file-scoped aggregations whose literal rows settle p2: AnonymousLinkUsed (11/11/7) and FileAccessed (4/4/4) on ListItemUniqueId 0aa10299-8655-4f7e-b293-965cc699f48a.
- Round 4: Quoted the round-3 literal rows verbatim in the p2 premise update; no new queries.

## This round
### What I ran
- `index=botsv3 sourcetype=o365:management:activity ListItemUniqueId="0aa10299-8655-4f7e-b293-965cc699f48a" Operation="AnonymousLinkUsed" | stats count as event_count dc(Id) as distinct_event_ids dc(ClientIP) as unique_client_ips values(ObjectId) as objectid` -> 1 of 1 row: `{"event_count": "11", "distinct_event_ids": "11", "unique_client_ips": "7", "objectid": "https://frothly-my.sharepoint.com/personal/bgist_froth_ly/Documents/Birthday Pictures/BRUCE BIRTHDAY HAPPY HOUR PICS.lnk"}`.
- `... ListItemUniqueId="..." Operation="FileAccessed" | stats count as event_count dc(Id) as distinct_event_ids dc(ClientIP) as unique_client_ips values(UserId) as userids` -> 1 of 1 row: `{"event_count": "4", "distinct_event_ids": "4", "unique_client_ips": "4", "userids": ["app@sharepoint", "bgist@froth.ly", "bstoll@froth.ly", "urn:spo:anon#21096b8a536a4443b9fd1b1f1b7d2f29970780b623b56525ab599d5c5bb7d2f3"]}`.

### What it means
Both rows are literal, complete (1 of 1 each), and identical to prior rounds. The AnonymousLinkUsed row on the .lnk's immutable ListItemUniqueId shows 11 events, 11 distinct Ids (no duplicates), and 7 distinct ClientIPs, with the ObjectId resolving to the .lnk's OneDrive URL — the anonymous sharing-link use act the question names. The FileAccessed row on the same file shows 4 events / 4 Ids / 4 IPs with an authenticated user population (app@sharepoint, bgist@froth.ly, bstoll@froth.ly, one urn:spo:anon) — a different act, not the measure asked for. The count is unchanged: **7**.

## Ruled out
- FileAccessed as the measure of "used" — 4 events / 4 IPs, authenticated user population: file access, not anonymous link use.
- Other lifecycle operations (AnonymousLinkCreated, FileUploaded, FileModified, SharingSet, SharingInheritanceBroken) — creation/upload/modification/sharing acts, none is the use act.

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
