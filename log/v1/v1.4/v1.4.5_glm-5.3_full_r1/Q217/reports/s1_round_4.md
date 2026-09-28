# s1 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=stream:smtp | fields=_raw, attach_filename, attach_type, attach_size, From, To, Subject, Date
**Insight:** FOUND
**Candidate:** line chart   **Confidence:** 70

## Prior rounds
R1: Email feeds enumerated; messagetrace has no attachment fields; stream:smtp holds full SMTP MIME.
R2: Bud = Bud Stoll <bstoll@froth.ly>; 4 Bud attachment emails found in stream:smtp.
R3: Ordered the 4 emails, read both thread bodies, rendered image001.jpg (column chart) and image002.jpg (line chart); submitted "line chart" with the reading ambiguity flagged.
R4 (this): Rendered image003.jpg and the postmortem's image002.jpg (both the quoted column chart), decoded the postmortem body, and completed the attachment inventory — resolving the rival.

## This round
### What I ran
- read_image image003.jpg (21:56:27 email) -> column chart, 5 host series, 12:45–1:00 AM — same chart as image001.jpg (quoted copy).
- stream:smtp "Has-Attach" | rex From/Subject/filenames/sizes | search bstoll -> 11 Bud emails, complete: only 4 carry attachments (55K–456K bytes); the other 7 (7–16 KB, incl. both earlier brewertalk announcement emails) have none — no earlier attachment exists in the thread.
- Postmortem body (base64) decoded -> "I had a 'open public bucket' accidentally... some malicious people got into our code and added in something called a 'coinminer'... That's why some browsers were hitting 100% CPU!"
- read_image postmortem image002.jpg -> column chart (quoted metrics-store search, not a new illustration).

### What it means
FOUND. The email Bud sends to Frothly employees to illustrate the coin miner issue is the 21:56:27 (+08) "RE: Improved brewertalk.com - check it out!" to Billy Tun + allhands: "Wow Billy. I did find the issue! Look at the Splunk chart below - ... CPU of my local Chrome browser ... spiked to 100%! ... some malicious code got into our forums." The postmortem names that issue the "coinminer". That email carries two attachments — image002.jpg (first) and image003.jpg (second, the quoted prior column chart). The first file attachment, image002.jpg, is a Splunk line chart: timechart avg(%_Processor_Time) span=10s by instance, Chrome instances spiking to ~100% CPU. Answer: line chart.

Rival resolved: image001.jpg (column chart) in the 21:50:47 email is earlier, but Bud's text there — "I haven't figured it out yet... check out the metrics store search below" — shows the issue was unidentified, so it was not sent "to illustrate the coin miner issue"; and that email has a single attachment, making "first" vacuous. "First" is meaningful only in the two-attachment "I did find the issue!" email.

## Ruled out
- image001.jpg / column chart (21:50:47 email) - Bud hadn't identified the issue; single-attachment email makes "first" vacuous.
- Postmortem email's image002.jpg (column chart) - quoted copy of the earlier metrics-store search; last email in the thread.
- image003.jpg (column chart) - second attachment, quoted copy.
- Birthday email image002.jpg (19:21, to Peat Cerf only) - not miner-related, single recipient.
- Billy Tun (btun@froth.ly) as "Bud" - From lines distinguish Bud Stoll from Billy Tun.
- messagetrace / o365:management:activity / ess_content_importer as attachment sources - no attachment fields / no send events / errors only.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
