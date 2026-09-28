# s3 - Q217 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=6_
**Scope:** sourcetype=stream:smtp (Bud coin-miner thread images only) | fields: attach_filename, _raw, timestamp, Subject, From, To
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops; ess_content_importer/ms:aad:signin dead ends.
- R2: stream:smtp carries full MIME; "Malware Alert Text.txt" = Bruce Gist's; Bud postmortem found with single inline image002.jpg.
- R3: Bud coverage = 4 sent messages; postmortem body unread (encoded) at cap.
- R4: postmortem body decoded — names "coinminer"/100% CPU; attachment = "metrics store search" screenshot; no chart-type word in any body.
- R5: image artifact worked — valid decodable JFIF; MIME/HTML metadata carries no description.
- R6: anchor disproved as Bud's path — PCERF-L 10:24:46–10:33:05 UTC = Billy Tun's "RE: meeting with F" (pwned.jpg); EDT ruled out.
- R7: SOF0 dimensions decoded (image001 3072x870; image002 1088x980; image003 2371x857); no embedded text metadata; web lookups empty.

## This round
### What I ran
- Postmortem HTML img tag decoded from base64 -> `<img width="2113" height="598" ... id="Picture_x0020_1" src="cid:image002.jpg@01D42481.0AB60870">` — no alt/title.
- 13:56:27Z HTML img tags (quoted-printable) -> width/height/id/src only, no alt/o:title.
- Base64 search of postmortem HTML for chart/graph/line/bar/column/area/pie/timechart/Splunk fragments -> only CSS "line;}" false positives.

### What it means
Every in-scope avenue is exhausted: MIME headers, HTML img attributes, body text, JPEG payload structure, dimensions, and embedded-metadata searches carry no visualization name; the pixels cannot be rendered with this tooling. The two-word Splunk visualization type is not recoverable from the available evidence. The strongest defensible conclusion is: the attachments are screenshots of a Splunk metrics store search (image001.jpg 3072x870 being the first illustrating attachment; image002.jpg the postmortem's only attachment). The wide-short aspect is consistent with a time-series chart but does not distinguish line/bar/area — an inference, not evidence, and not submitted. No value; nothing invented.

## Assumptions
- Coverage: stream:smtp Bud-thread image payloads — VERIFIED exhausted (SOF0 dimensions decoded; EOI confirms completeness; no XMP/comment text; no alt/title in HTML; no chart-type vocabulary in any base64 or plain text). JPEG pixel content — not renderable with available tooling; the only carrier of the answer.
- Selection: postmortem as the coin-miner email — VERIFIED (decoded body names the coinminer; only Bud message to all employees about it). First attachment = image002.jpg (postmortem) / image001.jpg (first illustrating message) — VERIFIED as the only attachments present.
- Premise: wide-short 3.5:1 metrics screenshot implies a time-series chart — UNVERIFIED inference; explicitly not submitted.

## Ruled out
- HTML img alt/title attributes as carriers — none exist in either encoding.
- Embedded JPEG metadata (XMP/comments) — no fragments found.
- MIME Content-Description — filename only.
- Body text — only "metrics store search".
- PCERF-L anchor as Bud's postmortem path — Billy Tun's "RE: meeting with F" (pwned.jpg), literal UTC.
- "Malware Alert Text.txt" (Bruce Gist's); Bud's non-incident messages; ms:o365:management, ess_content_importer, ms:aad:signin, o365:management:activity, messagetrace as carriers.

## Open questions for SH
- None. The case can stop here: the two-word visualization type is not recoverable from the available evidence without image-rendering/OCR capability on the base64 JPEG payloads (image001.jpg in the 13:50:47Z event, or image002.jpg in the postmortem event).