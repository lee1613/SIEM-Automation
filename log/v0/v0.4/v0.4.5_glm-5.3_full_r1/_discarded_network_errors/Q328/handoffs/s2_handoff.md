# s2 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=osquery:results (pack_fim_file_events, pack_process-monitoring_proc_events) + stream:http | host=hoth
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1 (this round): identified the escalation file as /tmp/colonel.c on hoth via osquery FIM + process events; file contents not yet recovered.

## This round
### What I ran
- get_source_types -> 102 sourcetypes available.
- keyword search "colonel" and "definitelydontinvestigatethisfile" -> 0 events each.
- `index=botsv3 sourcetype=osquery:results (colonel OR definitelydontinvestigatethisfile) | stats count by sourcetype, source, name` -> 2 rows: 9 FIM + 5 process events, all hoth/tomcat8.
- get_raw_events keyword=colonel sourcetype=osquery:results -> 11 events (full chain, read to end).
- `sourcetype=stream:http colonel host=hoth` and without host -> 0 events both.
- `sourcetype=stream:http host=hoth | stats count` -> 1035 events; `| stats count by uri,http_method,status` -> 0 rows (uri not a populated field here).

### What it means
NOT_FOUND for the line-2 text: the escalation file is positively identified, but no feed read this round returned its contents. The osquery chain proves /tmp/colonel.c is the file: /tmp/colonel (7701-byte base64 blob) is decoded by `base64 --decode /tmp/colonel` into /tmp/colonel.c (5775 bytes — 7701 base64 chars ≈ 5775 decoded bytes, exact match), which tomcat8 then `cat`s and compiles with `gcc colonel.c -o colonelnew`. The content itself must come from the HTTP body that delivered the base64 blob; the literal string "colonel" appears in no stream:http event, so the body is encoded and needs a field-level search (uri-based stats returned nothing, so stream:http field names must be learned first via get_sourcetype_fields).

## Ruled out
- osquery:results FIM as a content source — records only hashes/sizes/metadata, never file contents.
- stream:http keyword "colonel" — 0 events despite 1035 hoth stream:http events existing.
- /tmp/definitelydontinvestigatethisfile.sh — 0 events dataset-wide (keyword and osquery searches).
- /tmp/colonel as "the file" — it is the base64 transport, decoded to produce colonel.c.
- /tmp/colonelnew — compiled binary, no displayable text lines.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['osquery:results', 'stream:http'] sources=[] fields=['host', 'name', 'columns.target_path', 'columns.cmdline', 'form_data', '_raw']
- Rounds worked: 2/8  (iterations: 11, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=osquery:results (colonel OR definitelydontinvestigatethisfile) | stats count by sourcetype, source, name
- index=botsv3 sourcetype=stream:http colonel host=hoth | stats count by http_method, uri, status
- index=botsv3 sourcetype=stream:http colonel | stats count by host, src_ip, dest_ip, uri
- index=botsv3 sourcetype=stream:http host=hoth | stats count
- index=botsv3 sourcetype=stream:http host=hoth | stats count by uri, http_method, status
