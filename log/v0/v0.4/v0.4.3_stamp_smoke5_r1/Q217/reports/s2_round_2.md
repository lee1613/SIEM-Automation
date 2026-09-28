# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, attach_filename, attach_type, attach_size, content
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 60

## Prior rounds
- R1: Opened SMTP scope; feed = 879 events, one source; two "Bud" identities in feed (Billy Tun <btun@froth.ly>, Bud Stoll <bstoll@froth.ly>); found 11 attachment-bearing events, read only the 2 earliest (truncated); no value.

## This round
### What I ran
- Full rex enumeration of all 11 `"attach_filename"` events (from/subject/to/filename/type/date) -> 11/11 rows, no truncation. Bud Stoll -> 3 emails to Billy Tun + allhands@froth.ly: image001.jpg (02:38:43), image002+003.jpg (02:44:24), "Postmortem on our issue with brewertalk" image002.jpg (03:12:19). Billy Tun -> pwned.jpg (to pcerf, "RE: meeting with F") and Employee New Hire Dates.xlsx (to ghoppy).
- `("coin miner" OR "cryptominer" OR "miner" OR "monero" OR "cryptocurrency")` -> 0 events.
- `("mining" OR "crypto" OR "malware" OR "Splunk" OR "CPU")` -> 12 events: brewertalk thread + "Splunk service needs a restart" thread.
- `("dashboard" OR "visualization" OR "chart" OR "screenshot" OR "graph")` -> exactly 1 event: Bud Stoll's "RE: Improved brewertalk.com".
- `"Look at the Splunk"` -> exactly 1 event: Bud Stoll 02:44:24 (image002.jpg, image003.jpg): "Look at the Splunk chart below".
- Two-word viz names (line/bar/pie/column/area chart, single value, choropleth, gauge, scatter, heatmap, bubble chart) -> 0 events.
- First-attachment event detail -> image001.jpg, image/jpeg, 226222 bytes, Mon 15 Sep 2018 02:38:43 +0000, Bud Stoll to Billy Tun + allhands@froth.ly.

### What it means
NOT_FOUND for the two-word visualization type. SMTP positively identifies the first attachment artifact — image001.jpg in Bud Stoll's "RE: Improved brewertalk.com - check it out!" (02:38:43 UTC, to all Frothly employees via allhands@froth.ly) — but nothing in SMTP names the visualization it depicts. The only visualization prose in the entire feed, "Look at the Splunk chart below", is in Bud's SECOND attachment email (02:44:24), not the first, and is one word anyway. The first email's body contains none of chart/dashboard/visualization/screenshot/graph; its attachment is base64 JPEG these tools cannot decode. The first email's full body was not read before tools were withdrawn — that read is the one remaining SMTP step, but no two-word viz name exists anywhere in the feed, so the type most likely lives only in the image pixels.

## Ruled out
- Billy Tun (btun@froth.ly) as the emailing "Bud" — his attachments go to individual employees on non-miner subjects; Bud Stoll owns the allhands miner thread and all viz prose.
- Bruce Gist "Malware Alert Text.txt" — earliest attachment in feed, sender bgist@froth.ly, not Bud.
- Two-word viz names in SMTP — zero matches across 11 common Splunk visualization names.
- Postmortem image002.jpg — third Bud attachment, not first.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
