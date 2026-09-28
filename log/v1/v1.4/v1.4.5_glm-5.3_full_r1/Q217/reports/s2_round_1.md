# s2 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp | source=ms_o365_message_trace | fields=SenderAddress, DateReceived, Subject, MessageId, RecipientAddress, src_user, attach_filename, file_name, _raw

**Insight:** partial — credible candidate, one leg unverified
**Candidate:** line chart   **Confidence:** 70

## Prior rounds
- None — first round on this scope; I replace the retired stream:smtp-first approach, whose selection premise p2 is still open.

## This round
### What I ran
- `messagetrace SenderAddress="bstoll@froth.ly" | stats ... by DateReceived, Subject, MessageId | sort DateReceived` → 17 messages, all rows read. Brewertalk-thread emails to employees in order: 13:03:05Z "I'm making some great changes to brewertalk!", 13:06:47Z "Improved brewertalk.com - check it out!", 13:50:43Z "RE: Improved brewertalk.com" (reply 1), 13:56:24Z "RE: Improved brewertalk.com" (reply 2), 14:24:19Z "Postmortem on our issue with brewertalk".
- `stream:smtp src_user="bstoll@froth.ly" | stats count values(file_name) by _time, subject | sort _time` → 11 messages, all rows read. Attachment-bearing: 19:21:13+08 image002.jpg (Wild Birthday thread), 21:50:47+08 image001.jpg, 21:56:27+08 [image002.jpg, image003.jpg], 22:24:23+08 image002.jpg (postmortem).
- `get_raw_events keyword="Improved brewertalk.com - check it out!"` → 5 events; values clipped at 1500 chars — headers only, no body.
- Two rex attempts on the 21:50:47 body: `earliest=...+08:00` rejected as invalid format; `08/20/2018:13:50:00-13:51:00` bounds returned 0 events (bounds parsed in SH-local +08 = 05:50Z, missing the 13:50:47Z event).

### What it means
Ordering and attachment order are now independently established from messagetrace + stream:smtp, per SH's deviation — no reliance on the retired approach. The 21:56:27+08 reply's first file attachment is image002.jpg (attach_filename array order). What I could not do this round: read either reply's body to confirm which first illustrates the coin miner issue, or view image002.jpg to confirm its visualization type. Those two legs rest on open premise p2; "line chart" is submitted as the candidate consistent with p2 and with the ordering/attachment map verified above.

## Ruled out
- 13:03:05Z / 13:06:47Z brewertalk emails — no attachments in stream:smtp, so neither can carry "the first file attachment".
- 22:24:23+08 postmortem (image002.jpg) — third attachment-bearing brewertalk message, later than both replies; not "first".
- 19:21:13+08 image002.jpg — Wild Birthday thread, unrelated to the coin miner.
- get_raw_events for bodies — clipped at 1500 chars; rex with `earliest=+08:00` — invalid format; rex with 13:50Z bounds — 0 events (timezone trap).
- NOT ruled out: 21:50:47+08 reply (image001.jpg) — live rival for "first illustrating email"; body unread.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
