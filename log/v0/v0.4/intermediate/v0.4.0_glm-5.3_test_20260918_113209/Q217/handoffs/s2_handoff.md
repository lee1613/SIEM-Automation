# s2 - Q217 - Round 1
_stamped by runner: rounds_remaining=0 novel_spl=12_
**Scope:** sourcetype=stream:smtp, stream:http, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, access_combined, WinHostMon | source=stream:Splunk_HTTPURI, stream:http, WinEventLog:Microsoft-Windows-Sysmon/Operational | fields=file_name, uri_path, site, TargetFilename, EventCode
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 55

## Prior rounds
- R1 (my first; retired senior's mail/HTTP text analysis is context, not my work): mapped every source touching pwned.jpg; no content-bearing artifact recovered.

## This round
### What I ran
- get_sources(keyword="pwned") -> exactly 4 sources index-wide: Sysmon (6), stream:smtp (4), stream:Splunk_HTTPURI (1), stream:http (1). Nothing else mentions the filename.
- sourcetype=stream:smtp "pwned" | stats by src_user, file_name -> 1 event: btun@froth.ly, pwned.jpg.
- get_raw_events(stream:smtp, "pwned.jpg") -> 1 event exists; _raw too large to display.
- get_sourcetype_fields(stream:smtp) -> 94 fields, all session metadata; content_type values are text/plain, text/html, multipart/alternative — no attachment-body field.
- Sysmon "pwned" | stats by EventCode, host, TargetFilename -> 6 events, all EventCode 11: OUTLOOK.EXE wrote pwned.jpg to INetCache\Content.Outlook\RDQE5QCZ on BTUN-L and M0UPC09M on PCERF-L (incl. pwned (002).jpg).
- source=stream:Splunk_HTTPURI ("pwned" OR "temp-e") -> temp-e.net /files/incoming/hoffa/pwned.jpg, status=200, dest 62.73.58.161.
- access_combined "pwned" -> 0; WinHostMon "pwned" -> 0.

### What it means
The chain is closed on names: the only web-server reference is a byte-count proxy summary with no body; the only endpoint traces are Sysmon file-create records with no content; the SMTP attachment event exists but its body is not retrievable and no parsed field carries image data. Nothing inspected literally reveals the visualization type. Two leads remain the only places the image bytes could still live.

## Ruled out
- stream:Splunk_HTTPURI - proxy summary (site/uri_path/bytes/time_taken); reference only, no payload.
- Sysmon EventCode 11 - path/process metadata only; no image content.
- access_combined, WinHostMon - zero hits.
- symantec:ep:*, code42:*, osquery:*, aws:s3:accesslogs, o365/mgmt feeds - absent from the exhaustive "pwned" source enumeration; no thumbnail/preview/quarantine copy exists under that name.

## Open questions for SH
- Should next round retry the single oversized stream:smtp _raw with narrower keywords ("image/jpeg", "Content-Disposition", "base64")? If the base64 body is indexed there, the image is preserved and decodable offline.
- get_sources counts "pwned"/"hoffa" hits in source=stream:http that SPL term search cannot see — known manifest quirk, or should next round pull stream:http events for site=temp-e.net in 10:22-10:25Z and read POST bodies directly?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: This senior is cut off, not finished: it narrowed the remaining possibilities to the single oversized SMTP artifact or a minute-scale temp-e.net web retrieval path, but did not recover the image content or a literal chart-type description. With no rounds remaining, retire with the unresolved gap recorded rather than force an unsupported answer.
- Scope I owned: sourcetypes=['aws:s3:accesslogs', 'access_combined', 'apache_error', 'stream:http', 'stream:ip', 'osquery:results', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon'] sources=[] fields=['url', 'uri', 'src', 'dest', 'filename', 'path', 'TargetFilename', 'Image', 'CommandLine', '_raw']
- Rounds worked: 1/1  (iterations: 9, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "pwned" | stats count by sourcetype, source
- index=botsv3 ("temp-e.net" OR "hoffa") | stats count by sourcetype, source
- index=botsv3 source=stream:Splunk_HTTPURI ("hoffa" OR "pwned" OR "temp-e") | stats count by site, uri_path, status, dest_ip
- index=botsv3 sourcetype=access_combined "pwned" | stats count by clientip, uri, status
- index=botsv3 sourcetype=stream:http "hoffa" | stats count by uri, status, src_ip
- index=botsv3 sourcetype=stream:http "pwned" | stats count by uri, status, src_ip
- index=botsv3 sourcetype=stream:http source=stream:http "pwned" | stats count by uri, site, method, status, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI ("hoffa" OR "pwned" OR "temp-e") | stats count by site, uri_path, status, dest_ip
- index=botsv3 sourcetype=stream:smtp "pwned" | stats count by src_user, file_name
- index=botsv3 sourcetype=stream:smtp file_name="pwned.jpg" | stats count by src_user, file_name, file_size, file_hash, content_type, file_id
- index=botsv3 sourcetype=WinHostMon "pwned" | stats count by host, Type, Name
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "pwned" | stats count by EventCode, host, Image, TargetFilename
