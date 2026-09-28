# s1 - Q326 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=8_
**Scope:** sourcetype=stream:http, stream:smtp (content-bearing feeds) | fields: content, _raw, site, uri_path, Subject, host, src_ip
**Insight:** partial — no literal phrase found; value empty
**Candidate:** none   **Confidence:** 10

## Prior rounds
- Round 1: Mallory = Mallory Kraeusen <mkraeusen@froth.ly>; 33 SMTP events (bodies clipped); OneDrive upload of Frothly_GABF_Deck-2018-MK.pptx; "advertis" -> 0 in SMTP; o365 feed is metadata-only.
- Round 2: Mallory's host MKRAEUS-L (192.168.247.129) mapped; 168 HTTP events are brewertalk forum pages, ipinfo.io, Splunk login; no ad-research site; no bodies read.
- Round 3 (this round): literal-phrase and keyword probes eliminate both content feeds; only "enjoy" text is Billy Tun's quote email, not Mallory's.

## This round
### What I ran
- `stream:smtp "meant to be enjoyed" | stats count` -> 0; `stream:http "meant to be enjoyed" | stats count` -> 0.
- sample_events stream:http host=MKRAEUS-L keyword=brewertalk -> 3 events, all aggregated summaries (site/uri_path/bytes/status), no request or response bodies.
- `stream:smtp "enjoy" | stats count by source` -> 1 event; get_raw_events + rex -> Billy Tun to allhands, Subject "Motivation... through beer": quotes brainyquote.com/topics/beer, favorite "Beer makes you feel the way you ought to feel without beer" - Henry Lawson, ends "Enjoy!".
- `stream:smtp "responsibly"` -> 0; `stream:http "responsibly"` -> 0.

### What it means
The literal phrase "meant to be enjoyed" appears nowhere in either content feed, and — because Splunk keyword search matches the full _raw including clipped portions — the round-1 hypothesis "responsibly" is refuted in every content-bearing feed in scope. The only "enjoy" text is Billy Tun's, not Mallory's advertising research. No value can be submitted from evidence read so far.

## Ruled out
- stream:smtp as carrier — "meant to be enjoyed", "responsibly", "advertis" all 0 across the feed; only "enjoy" hit is Billy Tun's quote email (not Mallory's).
- stream:http as carrier — "meant to be enjoyed" and "responsibly" 0 across the feed; MKRAEUS-L events carry no bodies at all (aggregated summaries only).
- o365:management:activity — metadata only (Rounds 1-2).
- stream:dns — domain names only (Round 2).

## Next (not run — tools withdrawn)
- Probe alternative one-word phrasings ("moderation", "fresh", "cold", "together") in both feeds.
- Extend scope to aws:cloudwatchlogs (brewertalk server logs), access_combined query strings, code42/WinEventLog file-content feeds for the GABF deck text.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
