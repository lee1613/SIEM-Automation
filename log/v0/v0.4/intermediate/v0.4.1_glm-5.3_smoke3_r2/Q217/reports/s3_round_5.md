# s3 - Q217 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=12_
**Scope:** sourcetype=stream:smtp | fields: attach_filename, _raw, timestamp, Subject, From, To
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops; ess_content_importer/ms:aad:signin dead ends.
- R2: stream:smtp carries full MIME; "Malware Alert Text.txt" belongs to Bruce Gist; Bud's postmortem found with single inline attachment image002.jpg.
- R3: exhaustive Bud coverage (4 sent messages); postmortem body unread (encoded); ms:o365:management unqueried at cap.
- R4: postmortem body decoded — names "coinminer"/100% CPU; attachment = "metrics store search" screenshot; ms:o365:management has no message audit; no body names a chart type.

## This round
### What I ran
- Postmortem image part header rex -> Content-Description is just "image002.jpg"; size 162526; cid image002.jpg@01D42481.0AB60870; blob starts /9j/4AAQSkZJRg (valid decodable JFIF JPEG).
- 13:50:47Z reply (Bud's first attachment illustrating the issue) HTML img markup -> width=2112 height=598 (21.99in x 6.23in), id "Picture_x0020_1", no alt/o:title; MIME header: image001.jpg, size 165314, cid ...58AEEAB0.
- cid context extraction in both events -> plain "[cid:...]" and img src only; no descriptive text anywhere around the images.

### What it means
The artifact is a valid, decodable JPEG, but nothing readable in the SMTP event — MIME headers, HTML img attributes, or body text — names the visualization kind. The narrowest evidence-supported description is: a very wide (2112x598) screenshot of a Splunk metrics store search. The two-word kind lives only in the image pixels, which my tooling cannot render. Per instruction, no value is invented.

## Assumptions
- Coverage: stream:smtp image artifact properties — VERIFIED searched (MIME part headers, Content-Description, Content-ID, HTML img width/height/id/alt, surrounding body text in both the postmortem and the 13:50:47Z/13:56:27Z replies). Image pixel content — NOT searchable with available tooling (base64 blob cannot be rendered/OCR'd).
- Selection: postmortem as the target email — VERIFIED (decoded body names the coinminer; only Bud message to all employees about it). image002.jpg as its first attachment — VERIFIED (only MIME filename in the event).
- Premise: JPEG is decodable — VERIFIED (JFIF magic bytes present). Premise: wide-short aspect implies a time-series chart — UNVERIFIED lead, not evidence; line/bar/area cannot be distinguished from dimensions.

## Ruled out
- MIME/HTML metadata as a carrier of the visualization name — Content-Description = filename only; img tag has no alt/o:title.
- Body text as a carrier — only "metrics store search"; no chart/graph/dashboard/visualization word in any body.
- ms:o365:management as a carrier — no message-level Exchange audit (R4).
- "Malware Alert Text.txt" and Bud's non-incident messages (R2/R3).

## Open questions for SH
- Can any scope render or OCR the image002.jpg base64 blob from the postmortem event (or image001.jpg from the 13:50:47Z reply), or find the same screenshot in a PCERF-L endpoint cache where a filename/EXIF may name the chart?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
