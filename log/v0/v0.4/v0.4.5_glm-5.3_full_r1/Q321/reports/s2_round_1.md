# s2 - Q321 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=5_
**Scope:** sourcetype=ms:o365:reporting:messagetrace | stream:smtp | stream:http | fields: recipient, sender, subject, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- Retired senior: the brag email body to ghoppy@froth.ly states no customer-email count; the screenshot's visible number may refer only to internal Bruce Gist-related mail.
- Established entities carried in: hyunki1984@naver.com, "All your datas belong to us", paste sdBUkwsE, SOX BCC transport rule.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; candidate feeds for a customer-data artifact: stream:mysql, aws:rds:audit, o365:management:activity, ms:o365:management, messagetrace, stream:smtp, stream:http.
- search_keyword "brewertalk" -> 0 events — unreliable: messagetrace subjects contain "brewertalk", so this tool misses data; not evidence of absence.
- messagetrace recipient="hyunki1984@naver.com" | stats count, values(subject) -> 84 rows, Aug 20 09:15:59Z–15:10:25Z; every subject is internal Frothly correspondence (anniversaries, RE: threads, GitHub/asterisk notifications, "New Customer") BCC'd by the SOX transport rule. No brewertalk-customer population.
- stream:http "sdBUkwsE" -> 0 events.
- stream:smtp "sdBUkwsE" -> 1 event: 2018-08-20T15:19:34Z, From ghoppy@froth.ly, "Fw: All your datas belong to us", attachment 1534778082419.png (image/png, 87446 bytes decoded, base64). The paste id lives only inside this forward.
- stream:http "pastebin" -> 0 events; the Pastebin upload is not captured in http stream data.

### What it means
NOT_FOUND: no database, mail, or audit artifact I reached states or permits counting exposed customer emails. The naver.com channel carries only internal mail (84 rows, all internal subjects). The paste id appears only in the SMTP forward with the screenshot; the upload itself is invisible in stream:http. The only artifact that could show the paste contents is the base64 PNG, unreadable via SPL, and prior analysis ties its visible number to internal Bruce Gist mail — so I did not submit a number. Unsearched: stream:mysql, aws:rds:audit (brewertalk DB queries), o365:management:activity (transport-rule/mailbox audit).

## Ruled out
- ms:o365:reporting:messagetrace to hyunki1984@naver.com as the customer-data artifact — 84 rows all internal Frothly mail via the SOX BCC rule.
- stream:http as the exfil-upload record — 0 pastebin.com events, 0 sdBUkwsE.
- The SMTP forward body as a count source — carries only the screenshot attachment.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
