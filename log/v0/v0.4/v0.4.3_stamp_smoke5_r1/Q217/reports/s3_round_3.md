# s3 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** sourcetypes=osquery:results, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinEventLog, stream:http | fields=filename, path, url, uri_path, uri_query, form_data, http_content_type, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1 (this round): endpoint/browser scope assigned after SMTP/O365 scopes were exhausted by the prior senior.

## This round
### What I ran
- osquery:results / Sysmon / WinEventLog / stream:http, each `"image00"` -> 0 events in all four feeds.
- stream:http `"brewertalk"` -> 4,754 events (GET 200=2716, 304=306, 404=49, POST 200=60); top uri_path (40 rows read) shows MyBB forum paths incl. /attachment.php (95 hits).
- stream:http `uri_path="/attachment.php"` -> 1 URL; raw read (10 events) -> MyBB portal thumbnail fetches (thumbnail=2..8, image/jpeg+png, referrer portal.php) on 2018-08-20 from external attacker IP 174.215.8.112; no filenames.
- stream:http `"miner"` -> 0 events.
- stream:http `"splunk"` -> 3 raw events: brewertalk POST /xmlhttp.php username_availability for dherrald@splunk.com (attacker recon) and two www.splunk.com root GET 301s from 172.16.197.137.

### What it means
NOT_FOUND. The attachment artifact image001.jpg/image002.jpg is absent from every endpoint and browser feed in scope — no saved copy, no download, no cached retrieval, no file path. The only attachment-naming HTTP traffic (brewertalk /attachment.php) is the MyBB forum's own portal thumbnails browsed by the attacker on Aug 20, not a shared copy of Bud's chart, and carries no filenames. No record in scope names any Splunk visualization type, so this scope cannot yield the two-word answer.

## Ruled out
- osquery:results, Sysmon, WinEventLog, stream:http as holders of image001.jpg/image002.jpg — zero events for "image00" in each.
- brewertalk /attachment.php traffic as a shared/linked copy of Bud's chart — MyBB portal thumbnails (thumbnail=N, image/jpeg/png), fetched 2018-08-20 by external attacker IP, referrer portal.php, no filenames.
- stream:http "miner" — zero events; stream:http "splunk" — only attacker recon and two 301 redirects, no visualization name.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
