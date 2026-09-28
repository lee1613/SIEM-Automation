# s2 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=0_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp | source=ms_o365_message_trace | fields=SenderAddress, DateReceived, Subject, MessageId, RecipientAddress, src_user, attach_filename, file_name, _raw

**Insight:** FOUND
**Candidate:** line chart   **Confidence:** 97

## Prior rounds
- Round 1: messagetrace ordering (17 msgs read) + stream:smtp attachment map (11 msgs read) established; bodies unread (rex blocked); "line chart" at confidence 70.
- Round 2: both reply bodies read via charset=3Dus-ascii rex; image002.jpg = line chart, image001.jpg = column chart; p3 settled VERIFIED; p2/p4 quotes rejected (stitched fragments).
- Round 3: comparison query re-run with attach_order via file_name; read_image re-confirmed "Line Chart"; p2/p4 quotes rejected again (JSON-wrapped rows, not contiguous output spans).

## This round
### What I ran
- Comparison query (file_name=image001.jpg OR image003.jpg, body via rex at first MsoNormal paragraph, stats by _time) → 2 rows, both read, word-for-word:
  - 2018-08-20T21:50:47.371+08:00 | attach_order="image001.jpg" | body="Yeah. It looks like we have some issues – I ha=\r\nven't figured it out yet…but check out the metrics store search=\r\n below…. I'll figure it out! -bud"
  - 2018-08-20T21:56:27.927+08:00 | attach_order=["image002.jpg","image003.jpg"] | body="Wow Billy. I did find the issue! Look at the Splunk =\r\nchart below – I saw some instances spin up which was strange. Then I =\r\nlooked at the CPU of my local Chrome browser and noticed it spiked to 100%!=\r\n I will work on recovering now – it looks\r\n like some malicious code got into our forums." (inline cid immediately after: image002.jpg@01D4247D.2394E720)
- read_image on image002.jpg → "(image002.jpg, 3072x977) [nvidia/nemotron-3-nano-omni-30b-a3b-reasoning] line chart"

### What it means
The word-for-word rows directly support the selection: the earlier 21:50:47+08 reply's own body says Bud has NOT figured out the issue, so it does not illustrate the coin miner issue; the 21:56:27+08 reply's body says he found the issue, points to the Splunk chart, and attributes it to malicious code in the forums — the first illustration of the coin miner issue. Its MIME attachment order is [image002.jpg, image003.jpg], making image002.jpg the first file attachment, and the decoded image002.jpg is a Splunk line chart. Visualization type unchanged: **line chart**. p2 and p4 settled VERIFIED this round with contiguous single-value quotes (the prior rejections were stitched/wrapped quotes, not verbatim spans).

## Ruled out
- 21:50:47+08 reply / image001.jpg (column chart) — body: "I haven't figured it out yet"; not the illustrating email.
- 22:24:23+08 postmortem (image002.jpg) — later than the 21:56:27+08 reply; not first.
- 13:03:05Z / 13:06:47Z brewertalk emails — no attachments.
- 19:21:13+08 image002.jpg — Wild Birthday thread, unrelated.
- attach_filename in stats output — does not render on this feed; file_name used instead.