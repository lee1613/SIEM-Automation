# s2 - Q321 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=6_
**Scope:** sourcetype=stream:mysql | access_combined | bash_history | fields: query, result_row_count, affected_tables{}, dbname, uri, clientip
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 55

## Prior rounds
- R1 (mine): naver.com exfil channel = 84 messagetrace rows, all internal Frothly subjects via the SOX BCC rule — no customer population; paste id sdBUkwsE appears only in Grace's SMTP forward carrying base64 PNG 1534778082419.png; stream:http holds no pastebin upload.
- Retired senior: brag email body states no count; the screenshot's visible number may be internal Bruce Gist mail only.

## This round
### What I ran
- get_sourcetype_fields stream:mysql -> 42,541 events; dbname BREWERTALK (4,714), mybb_users in affected_tables{} (2,524); query/result_row_count/login fields present.
- stream:mysql "mybb_users" | stats by query -> 1,246 events (50 rows read): all routine MyBB SQL — session/post/thread joins and the memberlist query.
- stream:mysql query="*email*" -> 15 distinct queries; the only mybb_users email SQL is per-address registration checks (SELECT COUNT(email) ... WHERE email = 'bgist@froth.ly'; also fyodor@froth.ly, filip@wijnholds.com, Trojaan@gmail.com, trojaan@gmail.com), each result_row_count=1. No bulk SELECT of email.
- stream:mysql | stats max(result_row_count) by query -> feed-wide maximum result set is 20 rows (memberlist LIMIT 0, 20; 17 runs). No dump-scale query exists.
- stream:mysql "u.regdate" -> sorted memberlist query ran once, src 172.16.0.178 at 1534770977 (Aug 20 14:22:57Z), 20 rows.
- bash_history keyword "dump" -> 0 events; no mysqldump/export command.
- access_combined "memberlist" -> 11 URIs, all from client 172.16.0.149, status 200: /memberlist.php ×15, plus ?sort=regdate&order=ascending&perpage=20 and the same with &page=2.

### What it means
NOT_FOUND. The brewertalk customer-data source is the BREWERTALK MyBB database, and its query stream shows the adversary browsing the member list — the query returns u.* (email column included) 20 rows per page and page 2 was requested, so >20 member records were viewable — but no artifact states or permits counting the exposed customer emails: no dump, no bulk email SELECT, no row total. The only number in evidence remains the screenshot's 29, which SH's framing excludes and prior analysis ties to internal Bruce Gist mail; not submitted. Unchecked: aws:rds:audit, o365:management:activity, and the raw result payloads of the memberlist query (which could enumerate the actual member rows).

## Ruled out
- stream:mysql as a count source — full query inventory: max result_row_count 20, no dump or bulk-email query.
- bash_history export commands — 0 events for "dump".
- COUNT(email) queries — per-address registration checks returning 1 row each, not a population count.
- memberlist browsing as the count — proves 21–40 members viewable, not an exposure count.
- search_keyword "brewertalk" as an absence test — returns 0 although brewertalk data exists in messagetrace subjects and mysql dbname.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="stream:mysql" "mybb_users" | stats count, values(result_row_count…` (25 of 1246 rows seen). A claim resting on them alone is UNVERIFIED._
