# s3 - Q329 - Round 1
_stamped by runner: rounds_remaining=3 novel_spl=5_
**Scope:** sourcetype=ess_content_importer, stream:smtp, o365:management:activity, ms:o365:reporting:messagetrace, stream:http, stream:dns, aws:s3:accesslogs, WinHostMon, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | fields=content_type, method, src_ip, dest_ip, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
- Round 1 (this round): mapped all 102 sourcetypes; confirmed ess_content_importer exists but holds only 2 Splunkd daemon-error events — no imported message content.
- Swept "taedonggang" across stream:smtp, o365:management:activity, stream:http, ms:o365:reporting:messagetrace, stream:dns, aws:s3:accesslogs, WinHostMon, Sysmon — zero plaintext hits anywhere.
- Confirmed stream:smtp preserves the email delivery path: 879 events, 185 full DATA sessions, content_type on 137 events (text/plain, text/html, multipart/alternative).

## This round
### What I ran
- get_raw_events(ess_content_importer) -> 2 events, both "Splunkd daemon is not responding" errors; no message content.
- get_raw_events(stream:smtp, keyword=taedonggang) -> 0 events.
- run_splunk_search o365:management:activity + taedonggang -> 0 rows; same for stream:http, messagetrace, and a combined dns/s3/WinHostMon/Sysmon sweep -> 0.
- get_sourcetype_fields(stream:smtp) -> 879 events; 185 method=DATA; all src 104.47.32.79/33.77/33.79 (Microsoft O365 outbound) to dest 172.31.38.181:25 (internal Postfix, AWS us-west-2); content_type present on 137 events.

### What it means
NOT_FOUND for the word itself, but the delivery path question is answered: email content IS preserved in stream:smtp — 185 complete DATA-carrying sessions with MIME content types. The absence of the literal "taedonggang" string is expected if the artifact rode as a base64-encoded attachment, which keyword search cannot see. I ran out of iterations before decoding the DATA bodies.

## Ruled out
- ess_content_importer - only 2 daemon-error events; carries no imported message content at all.
- Plaintext "taedonggang" in stream:smtp, stream:http, o365:management:activity, ms:o365:reporting:messagetrace, stream:dns, aws:s3:accesslogs, WinHostMon, Sysmon - zero hits in all.

## Open questions for SH
- Should the next round decode the 185 stream:smtp DATA bodies (base64/MIME) to enumerate attachment filenames and locate the file with oversized-font markup?
- Is the Taedonggang artifact known to have been emailed (vs. uploaded via HTTP/S3), so I can prioritize the SMTP decode over the upload-path feeds?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
