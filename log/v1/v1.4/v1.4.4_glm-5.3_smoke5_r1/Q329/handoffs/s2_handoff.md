# s2 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=0_
**Scope:** sourcetypes=ms:o365:management, access_combined, aws:elb:accesslogs, stream:http, stream:smtp, code42:api, code42:computer, code42:org, code42:user, symantec:ep:behavior:file, symantec:ep:packet:file, symantec:ep:risk:file, symantec:ep:traffic:file, symantec:ep:security:file, symantec:ep:scm_system:file | fields=source,_raw,uri,url,http_method,form_data,filename,file_name,name,subject,recipient,sender,object,key,path
**Insight:** NOT_FOUND   **Candidate:** none   **Confidence:** 0

## Prior rounds
- R1 (s1): literal "taedonggang" absent from o365:management:activity and ms:o365:reporting:messagetrace.
- R2 (me): direct sweeps of code42:security, aws:s3:accesslogs, stream:http, stream:smtp, aws:cloudtrail, symantec:ep:agent:file — all 0; filed p3 (absence ⇒ unswept feed or encoded) and p4 (encoded MIME/POST bodies).

## This round
### What I ran
- get_sources keyword="taedonggang" -> 0 sources (sid 1790147963.565)
- get_sources keyword="frothly" (control) -> 5 sources, all network/syslog: cisco:asa/udp:514 (80192), aws:rds:audit/lambda:RDSAuditLogs (23976), stream:mysql/stream:mysql (2357), stream:mysql/stream:Splunk_MySql (1680), syslog/cisconvmflowdata (917)
- get_sources keyword="Taedonggang" -> 0 sources (sid 1790148123.570)
- get_sources keyword="taedong" (prefix) -> 0 sources (sid 1790148168.572)

### What it means
NOT_FOUND — no candidate file, therefore no word. Two things this round:
1. The control proves get_sources keyword mode searches event content (source names like "udp:514" do not contain "frothly"), so its zeros are genuine content zeros, not name misses. Both common casings of the target string, plus the lowercase prefix, return zero sources.
2. The same control exposes a coverage limit: "frothly" matched only 5 sources, all network/syslog feeds — no o365, WinEventLog, stream:http or stream:dns sources, even though o365 events carry @frothly.com in _raw. Keyword mode therefore does not visibly scan every feed, and its zero cannot clear ms:o365:management, access_combined, aws:elb:accesslogs, the code42 variants, or the five non-agent symantec feeds. Those in-scope feeds have NOT yet been swept directly with run_splunk_search — that is the immediate next step, together with a bare-token "taedong" search to catch "Taedong-gang"/"Taedong Gang" spellings that exact-string searches miss. If those come back empty, the string is encoded (p4) and the pivot is raw MIME/POST-body inspection via get_raw_events on stream:smtp and stream:http upload events.

## Ruled out
- get_sources keyword mode as an index-wide clear — control shows real content search but matched only 5 network-feed sources for a ubiquitous term, so feeds it does not scan stay live.
- Plaintext "taedonggang" (both common casings) and lowercase "taedong*" in: the 8 feeds swept in R1-R2, plus every source keyword mode does scan.
- NOT yet ruled out: hyphenated/space spellings ("Taedong-gang", "Taedong Gang") — no bare-token search run yet; encoded bodies in stream:smtp/stream:http.

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "The Taedonggang-uploaded file can surface in my scope in one of three ways, each"


## What I'd tell my replacement
- Retired because: This round made no direct search of the live feeds and the report itself shows keyword-source mode cannot clear them. After two rounds on the same indirect string-probing approach, the scope should be handed over to a replacement on a different direction.
- Scope I owned: sourcetypes=['stream:http', 'stream:smtp', 'aws:s3:accesslogs', 'aws:cloudtrail', 'code42:security', 'code42:api', 'code42:user', 'code42:computer', 'access_combined', 'aws:elb:accesslogs'] sources=[] fields=['uri', 'url', 'http_method', 'form_data', 'file_name', 'file', 'filename', 'path', 'object', 'Key', 'requestParameters.key', 'Subject', 'src_user', 'dest_user', 'user', 'email', '_raw']
- Rounds worked: 2/8  (iterations: 17, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype, source | sort - count
- index=botsv3 sourcetype=aws:cloudtrail "taedonggang" | stats count
- index=botsv3 sourcetype=aws:s3:accesslogs "taedonggang" | stats count
- index=botsv3 sourcetype=code42:security "taedonggang" | stats count
- index=botsv3 sourcetype=stream:http "taedonggang" | stats count
- index=botsv3 sourcetype=stream:smtp "taedonggang" | stats count
- index=botsv3 sourcetype=symantec:ep:agent:file "taedonggang" | stats count
