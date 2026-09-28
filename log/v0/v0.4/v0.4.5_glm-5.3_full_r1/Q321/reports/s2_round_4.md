# s2 - Q321 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=6_
**Scope:** sourcetype=stream:mysql | aws:rds:audit | fields: _raw, query, result_row_count, result_column_count, dbname, affected_tables{}
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 60

## Prior rounds
- R1: naver.com exfil channel = 84 messagetrace rows, all internal Frothly subjects via the SOX BCC rule; paste id sdBUkwsE appears only in Grace's SMTP forward carrying base64 PNG 1534778082419.png; no pastebin traffic in stream:http.
- R2: stream:mysql full query inventory — max result set 20 rows (memberlist LIMIT 0,20 ×17); only per-address COUNT(email) registration checks; bash_history has no dump; access log shows memberlist page=2 from 172.16.0.149.
- R3: aws:rds:audit mirrors the same SQL text; its "email" hits are MyBB template names; COUNT(u.uid) absent from both feeds.
- R4 (this round): raw payloads read — SQL text + metadata only, no row values; the memberlist COUNT(*) query found but its result is uncaptured.

## This round
### What I ran
- get_raw_events stream:mysql "mybb_userfields" (5) and "u.regdate" (3) -> raw payloads hold query text, bytes, result_column_count, affected_tables, timing — no returned row values.
- stream:mysql query="*LIMIT 20*" -> page-2 memberlist query (LIMIT 20, 20) exists, 1 event at 1534770819.
- query="*LIMIT 20, 20*" stats -> result_row_count ABSENT on that event; bytes_out=6773 (page 1: 12502 for 20 rows).
- Time window 1534770819–1534770820 (11 events) -> includes "SELECT COUNT(*) AS users FROM mybb_users u WHERE 1=1 AND u.usergroup NOT IN (1) AND CONCAT(',',u.additionalgroups,',') NOT LIKE '%,1,%'" — the MyBB memberlist total-count query — run with the page-2 request (session location '/memberlist.php?...&page=2', ip 172.16.0.149, Chrome/64). Its result value is in no event.

### What it means
NOT_FOUND (partial: database side exhausted). The database computed the member total at 1534770819, but the dataset captures only the query text — no row values exist in stream:mysql or aws:rds:audit, verified by reading raw events. Bounds only: page 1 = 20 rows; page 2 requested (total >20); page-2 bytes_out 6773 vs 12502 for 20 rows implies ~10–11 rows → ~30–31 members — a byte-proportionality estimate, not a count, and mybb_users includes internal Frothly addresses (bgist@, fyodor@), so members ≠ customer emails. Closest unread values: (1) the result of the COUNT(*) query at 1534770819 — text present, value uncaptured; (2) base64 PNG 1534778082419.png; (3) external Pastebin page sdBUkwsE. The screenshot's 29 reaches me second-hand, was contested by its own author, and nothing I hold ties it to customer emails — not submitted.

## Ruled out
- stream:mysql / aws:rds:audit raw payloads as a row-value source — read directly: SQL text + metadata only.
- result_row_count as the total — absent on the page-2 event; a COUNT query returns 1 row, and the value lives in the row, not the metadata.
- bytes_out proportionality as a count — yields only an estimate (~10–11 rows), not a direct count.
- 29 as a customer-email count — unsupported by any artifact I hold.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
