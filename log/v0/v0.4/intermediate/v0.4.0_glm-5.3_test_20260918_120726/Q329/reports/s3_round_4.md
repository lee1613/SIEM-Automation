# s3 - Q329 - Round 4
_stamped by runner: rounds_remaining=0 novel_spl=12_
**Scope:** sourcetype=stream:http | source=stream:http, stream:Splunk_HTTPURI, stream:Splunk_HTTPStatus | fields=_raw, uri, uri_path, url, host, site, status, src, dest, http_content_type, http_referrer
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- R1: mapped 102 sourcetypes; ess_content_importer = 2 daemon-error events; "taedonggang" absent in plaintext across 9 feeds; stream:smtp holds 185 DATA-bearing MIME sessions.
- R2: stream:smtp token map — bgist=27, stout=4, font-size=54, h1=19; all named filenames zero in plaintext; font-size outliers 41/36/34/31/28px.
- R3: outliers mapped to Groupon/Dropbox/O365-quarantine templates; 4 attacker-IP (45.77.53.176) "Quarentined email" phishing notifications; found pastebin.com/sdBUkwsE in a Segoe-UI-styled email.
- R4: pastebin email fully read — Taedonggang persona = HyunKi Kim <hyunki1984@naver.com>, Subject "All your datas belong to us" (2018-07-26), "We brought your data and imported it: https://pastebin.com/sdBUkwsE"; word not recovered.
- R5 (this round): stream:http swept — no pastebin traffic at all; found pwned.jpg on temp-e.net exfil server.

## This round
### What I ran
- index=botsv3 sourcetype=stream:http pastebin -> 0; sdBUkwsE -> 0.
- Token map (font-size/h1/hacked/pwned/pastebin/froth/beer) -> font-size=0, h1=4, pwned=2, pastebin=0.
- pwned-context rex -> 2 events: GET temp-e.net/files/incoming/hoffa/pwned.jpg, 200, image/jpeg, 53022 bytes, src 192.168.3.130, dest 62.73.58.161, referrer bing.com.
- dest/src=62.73.58.161 full sweep -> exactly 1 event: that single pwned.jpg GET.

### What it means
NOT_FOUND for the word, but the artifact is now identified: pwned.jpg is the Taedonggang-uploaded file on the exfil server (temp-e.net/62.73.58.161), fetched once by endpoint 192.168.3.130. The delivery path IS preserved in web-content evidence. The word cannot come from this scope: stream:http carries no response bodies (no HTML content anywhere in the feed), and the artifact is a JPEG whose content no HTTP event preserves. The pastebin paste was never fetched over cleartext HTTP.

## Ruled out
- pastebin.com/sdBUkwsE in stream:http - zero events; never fetched over HTTP (HTTPS-only).
- stream:http as a source of HTML body content - font-size=0 hits; the feed preserves request/response metadata only, no bodies.
- brewertalk.com defacement as the oversized-word carrier - all h1 hits are in request metadata, not page content.

## Open questions for SH
- Can I get scope on endpoint evidence (WinHostMon, osquery:results, bash_history, PowerShell logs) for host 192.168.3.130 to find how pwned.jpg was created/rendered and what text it contains?
- Should I use web_lookup on pastebin.com/sdBUkwsE to see if the paste (and its large-rendered title) is still publicly retrievable?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
