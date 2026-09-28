# s2 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, content, attach_filename, attach_type, attach_size, attach_disposition
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 85

## Prior rounds
- R1: Opened SMTP; two Bud identities in feed; found 11 attachment-bearing events, read only 2 earliest (truncated); no value.
- R2: Enumerated all 11 attachment events (no truncation); Bud Stoll owns the allhands brewertalk/miner thread (image001.jpg 02:38:43, image002+003.jpg 02:44:24, Postmortem image002.jpg 03:12:19); only viz prose in feed = "Look at the Splunk chart below" (02:44:24 email); 0 matches for 11 two-word viz names; no value.

## This round
### What I ran
- `"image001.jpg" "brewertalk"` + rex after us-ascii -> full plain-text body of the 02:38:43 event: "Yeah. It looks like we have some issues - I haven't figured it out yet...but check out the metrics store search below.... I'll figure it out! -bud [cid:image001.jpg@01D4247C.58AEEAB0]".
- `"image002.jpg" "image003.jpg"` + rex -> full body of the 02:44:24 follow-up: "Wow Billy. I did find the issue! Look at the Splunk chart below - I saw some instances spin up... CPU of my local Chrome browser... spiked to 100%! ... some malicious code got into our forums. [cid:image002.jpg@...]" — it quotes the 02:38:43 message verbatim.
- Postmortem event charset/transfer-encoding rex -> base64 ×3; body unreadable via SPL.
- HTML context around cid:image001 -> no alt/title attributes on the img tag.

### What it means
NOT_FOUND, stated explicitly per SH's contingency: SMTP identifies the artifact but not the two-word visualization type. The first attachment is image001.jpg (image/jpeg, inline, 226222 bytes, base64 in attach_content) in Bud Stoll's "RE: Improved brewertalk.com - check it out!" (Mon 15 Sep 2018 02:38:43 UTC, to Billy Tun + allhands@froth.ly). Its body calls the image only "the metrics store search"; the HTML has no alt text; MIME headers carry only filename/type/size. The 02:44:24 follow-up is the SAME thread (quotes the first email verbatim, same sender/recipients), so image001.jpg is part of the coin-miner thread — but the email that explicitly illustrates the identified issue is the 02:44:24 one, and even it says only "Splunk chart" (one word). No two-word visualization name exists anywhere in stream:smtp. The type lives only in the image pixels: image-level reading of the decoded image001.jpg (or image002.jpg under the alternative reading) is what would come next, outside this feed's text.

## Ruled out
- Textual viz cues in the first email — full plain body, HTML alt/title, MIME headers, Content-ID all read; none names a visualization.
- Two-word viz names in stream:smtp — 0 matches across 11 common Splunk visualization names (R2).
- Postmortem email body as a clarifier — base64-encoded, unreadable via SPL.
- Billy Tun's attachments (pwned.jpg to one employee, non-miner subject; hire-dates xlsx) and Bruce Gist's Malware Alert Text.txt (not Bud) — wrong sender/recipients/subject.