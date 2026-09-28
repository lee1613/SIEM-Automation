# s3 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=4_
**Scope:** sourcetype=stream:http, osquery:results, out-3, localhost-5, syslog, linux_secure, linux_audit | source=stream:http, /var/log/osquery/osqueryd.results.log | fields=_raw, form_data, http_content_length, columns.cmdline
**Insight:** FOUND
**Candidate:** " * Ubuntu 16.04.4 kernel priv esc"   **Confidence:** 85

## Prior rounds
- R1 (prior senior): API transport failure; no evidence.
- R2 (me): read all 11 osquery colonel events (commands/hashes/sizes only) and all 4 stream:http Struts2 POSTs; found the echo base64 transport; hand-decoded line 2; submitted.
- R3 (me): proved no direct render exists (cat body not stored; host logs carry no C-source tokens); proved the transport is complete (b64len=7700).
- R4 (this round): proved no in-scope capability decodes/renders the transport; enumerated the full command set; ruled out the only other large base64 echo.

## This round
### What I ran
- base64decode(b64) eval on the echo POST -> FATAL: "The 'base64decode' function is unsupported or undefined."
- read_image on the echo event, extract_spl isolating the blob -> "No image found. What the event does hold: JSON event (read 1 of 1 matching events.)"
- Full #cmd enumeration on the attack channel (14 distinct commands) -> only the echo carries file content; stats values(cmd) returned the COMPLETE 7700-char blob unclipped.
- Large-base64 echo scan -> 2 events: the colonel blob (7700 chars) and a 19:09:50 blob (8169 chars, head "/9j/4AAQSkZJRg..." = JPEG magic) — an image upload, not a duplicate transport.

### What it means
The wall is established from exact output: the dataset preserves only the complete encoded transport plus size/hash metadata for /tmp/colonel.c. No in-scope capability renders it — base64decode() is FATAL-unsupported, read_image finds no image (the decoded content is C source text, not image data), the cat response body is not stored (rawlen 1542 vs cl 5775), and no host log carries C-source tokens. The thing holding the line-2 text is the 19:08:37 echo POST's 7700-char base64 blob (readable in full via stats values(cmd); the 1500-char clip is only the raw-events display limit). Line 2 is hand-decoded from its 88-char head, verified group-by-group across all 22 base64 groups: line 1 "/*", **line 2 " * Ubuntu 16.04.4 kernel priv esc"**, line 3 " * all credits to @bleidl". Byte arithmetic seals completeness: 7701-byte /tmp/colonel = 7700 base64 chars + newline; 7700/4×3 = 5775 = FIM size of colonel.c = cat response content_length. The value is final; its only residual risk is leading-whitespace formatting, still unanswered by SH.

## Ruled out
- base64decode() render path — FATAL unsupported on this Splunk instance.
- read_image render path — no image in the event; decoded content is C text.
- cat /tmp/colonel.c response body — not stored (1542-char event vs 5775-byte body; sole event in flow).
- 19:09:50 large base64 echo — JPEG image upload, not a duplicate of the source.
- out-3, localhost-5, syslog, linux_secure, linux_audit, osquery:results — no literal C-source text anywhere (prior rounds).

_Premise updates refused by the runner:_
- p5 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
