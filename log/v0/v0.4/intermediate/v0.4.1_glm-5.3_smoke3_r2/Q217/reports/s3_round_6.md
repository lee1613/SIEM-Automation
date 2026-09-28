# s3 - Q217 - Round 6
_stamped by runner: rounds_remaining=2 novel_spl=11_
**Scope:** sourcetype=stream:smtp + XmlWinEventLog:Microsoft-Windows-Sysmon/Operational (host=PCERF-L) | fields: attach_filename, _raw, timestamp, Subject, From, To, TargetFilename, Image
**Insight:** partial
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops; ess_content_importer/ms:aad:signin dead ends.
- R2: stream:smtp carries full MIME; "Malware Alert Text.txt" = Bruce Gist's; Bud postmortem found with single inline image002.jpg.
- R3: Bud coverage = 4 sent messages; postmortem body unread (encoded); ms:o365:management unqueried at cap.
- R4: postmortem body decoded — names "coinminer"/100% CPU; attachment = "metrics store search" screenshot; no chart-type word in any body; ms:o365:management has no message audit.
- R5: image artifact worked — valid decodable JFIF JPEG; MIME/HTML metadata carries no description; 13:50:47Z image is 2112x598 px.

## This round
### What I ran
- Sysmon PCERF-L 14:20–14:40 UTC (epoch bounds; EDT reading of anchor) -> 13 events, all Symantec AV; no Outlook cache writes.
- Sysmon PCERF-L image/cache search over full coverage -> 3 OUTLOOK.EXE cache writes: pwned.jpg 10:24:47, pwned (002).jpg 10:25:03, ~WRD000.jpg 10:33:05 UTC — exact match to the literal-UTC anchor.
- stream:smtp "pwned.jpg" -> Billy Tun "RE: meeting with F", 10:24:29Z — the anchor message is Billy's, not Bud's.
- Bud listing re-verified with wildcard from="Bud Stoll*" -> same 4 messages; postmortem remains the only coin-miner email.

### What it means
The anchor is resolved but points at Billy Tun's "RE: meeting with F" (pwned.jpg), not Bud's postmortem; ~WRD000.jpg at 10:33:05 is a Word-rendered inline image from an unidentified second message. Bud's coin-miner email and its first attachment stand verified (postmortem, image002.jpg; thread's first illustrating attachment image001.jpg, 2112x598, "metrics store search"). No record — MIME headers, HTML img attributes, body text, cache filenames, Sysmon — names the Splunk visualization kind; it exists only in the JPEG pixels, which I cannot render. No two-word value; nothing invented.

## Assumptions
- Coverage: PCERF-L Sysmon image/cache artifacts — VERIFIED searched (3 cache writes, all in the anchor window; none names a chart). stream:smtp Bud messages — VERIFIED complete (4). JPEG pixel content — not renderable with available tooling.
- Selection: postmortem as the coin-miner email — VERIFIED (decoded body names the coinminer; only Bud message to all employees about it). First attachment = image002.jpg (postmortem) / image001.jpg (first illustrating message) — VERIFIED as the only attachments present.
- Premise: anchor identifies Bud's email — DISPROVEN this round (anchor = Billy Tun's "RE: meeting with F", pwned.jpg, 10:24:29Z).
- Premise: 2112x598 wide-short metrics screenshot implies a time-series chart — UNVERIFIED inference; line/bar/area cannot be distinguished from dimensions.

## Ruled out
- PCERF-L anchor window as identifying Bud's postmortem — matches Billy Tun's "RE: meeting with F" exactly (pwned.jpg 10:24:47, ~WRD000.jpg 10:33:05).
- EDT reading of the anchor — no PCERF-L Outlook activity in 14:20–14:40 UTC.
- Outlook cache filenames (~WRD000.jpg, pwned.jpg) as naming the visualization — generic Outlook temp names.
- MIME/HTML/body text as carriers of the chart type — no chart/graph/dashboard/visualization word in any body (R4–R5).
- "Malware Alert Text.txt" (Bruce Gist's); Bud's non-incident messages; ms:o365:management, ess_content_importer, ms:aad:signin, o365:management:activity, messagetrace as carriers.

## Open questions for SH
- Can any worker decode the base64 JPEG (image002.jpg in the postmortem event, or image001.jpg in the 13:50:47Z reply) and view/OCR it? That is the only remaining path to the two-word answer.
- Should the unidentified parent of ~WRD000.jpg (10:33:05, PCERF-L) be traced via a stream:smtp transmission listing for 10:25–10:35 UTC, in case it is a Bud message with a clearer attachment?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
