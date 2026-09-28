# s3 - Q329 - Round 3
_stamped by runner: rounds_remaining=1 novel_spl=10_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, content_type, method, src, dest, src_ip, dest_ip
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 25

## Prior rounds
- R1: mapped 102 sourcetypes; ess_content_importer = 2 daemon-error events; "taedonggang" absent in plaintext across 9 feeds; stream:smtp holds 185 DATA-bearing MIME sessions.
- R2: token map — bgist=27, stout=4, font-size=54, h1=19; all named filenames zero in plaintext; font-size outliers 41/36/34/31/28px; 4 STOUT-host bulk emails to all four Frothly users.
- R3: outliers mapped to Groupon/Dropbox/O365-quarantine templates; 4 attacker-IP (45.77.53.176) emails = "Quarentined email" phishing notifications; found pastebin.com/sdBUkwsE in a Segoe-UI-styled email.
- R4 (this round): pastebin email fully read — Taedonggang extortion email identified; word not recovered.

## This round
### What I ran
- rex around "pastebin" and "sdBUkwsE" in stream:smtp -> 1 event: full extortion email chain.
- Subject extraction on 45.77.53.176 emails -> all four are "Quarentined email" phishing notifications from it@frothly.com.
- h1 and 21-34px context extraction -> all accounted for as Groupon/Dropbox/quarantine/pastebin-link markup.

### What it means
NOT_FOUND for the word, but the delivery path is now proven: HyunKi Kim <hyunki1984@naver.com> (Taedonggang persona) emailed "All your datas belong to us" to Grace Hoppy on 2018-07-26 stating "We brought your data and imported it: https://pastebin.com/sdBUkwsE". The artifacts were preserved at that pastebin; the email evidencing it is in stream:smtp. The oversized word lives in the pastebin page content (title renders large), which is external to this sourcetype — the paste title appears to be "( ) ) )" but I cannot confirm the word from stream:smtp alone.

## Ruled out
- All stream:smtp large font-size outliers (41/36/34/31/28px) - benign template markup (Groupon logo, Dropbox h1, O365 quarantine), not a single oversized word.
- Plaintext filenames morebeer.jpg / stout-2.jpg / stout.png / BRUCE BIRTHDAY HAPPY HOUR PICS.lnk in stream:smtp - zero hits; not carried as plaintext in any SMTP body.
- ess_content_importer - 2 daemon-error events only.

## Open questions for SH
- Can I get scope on stream:http to look for a fetch of pastebin.com/sdBUkwsE (the paste page HTML would carry the large-rendered word)?
- Is the pastebin paste at sdBUkwsE confirmed as where the Taedonggang artifacts were "imported", so the paste title/body is the target content?