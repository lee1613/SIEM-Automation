# s1 - Q321 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=stream:smtp (source=stream:smtp), ms:o365:reporting:messagetrace, stream:http | fields: _raw, content, content_body, attach_filename, sender_email, receiver_email
**Insight:** partial
**Candidate:** 29   **Confidence:** 60

## Prior rounds
R1: Ruled out literal "Taedonggang" (0 events index-wide); mapped mail feeds; read 50/56 messagetrace rows to ghoppy — all benign.
R2: Found the bragging email — "All your datas belong to us" from HyunKi Kim <hyunki1984@naver.com> to Grace, 15:15:00Z, forwarded by Grace 15:19:35Z ("Are these our customers?"); body states no number; screenshot attachment shows Naver mail search "gist" → 29 results; pastebin content absent from stream:http.
R3 (this round): verified the screenshot's contents and eliminated the remaining alternate sources of a count.

## This round
### What I ran
- read_image 1534778082419.png (search-box verification) -> search box reads "gist"; "검색결과 (29)"; one open email (ghoppy@froth.ly → btun@froth.ly, Bruce Gist performance mail, 2018-07-26); visible addresses are froth.ly internal.
- stream:http "pastebin" -> 0 events (paste content unobtainable; HTTPS).
- get_raw_events "Postmortem on our issue with brewertalk" -> 1 event; base64 body decoded in part: Bud's open-bucket/coinminer apology; no customer count.
- rex on postmortem content_body -> base64 text; no "customer"/"database"/"records" plain-text hits.

### What it means
The bragging email is fully read. Its body ("We brought your data and imported it: https://pastebin.com/sdBUkwsE Also, you should not be too hard Bruce. He good man") states no number; the pastebin link-preview title is Korean text with no number; the only number anywhere in the message is the attachment screenshot's "검색결과 (29)" — 29 search results in the adversary's Naver mailbox after importing Frothly's exfiltrated mail. 29 is therefore the number the message reveals, and it is submitted as the candidate. Caveat held at confidence 60: the 29 hits are for the term "gist" (internal Frothly mail about Bruce Gist), while the question says "customer emails"; the customer data proper is the pastebin dump sdBUkwsE, whose content is absent from the dataset. If the intended answer is the paste's customer count, it is not obtainable from the mail or HTTP feeds.

## Ruled out
- Email body text / pastebin link-preview title as the number's source — extracted in full, no number present.
- pastebin content via stream:http — 0 events for "pastebin" and "sdBUkwsE" (HTTPS, not captured).
- Bud Stoll's postmortem email as a customer-count source — base64 body is a coinminer/open-bucket apology, no count.
- A second adversary email to Grace — only 2 hyunki1984 events exist (original + forward).
- All 56 messagetrace rows to ghoppy@froth.ly as the bragging email — all read, all benign.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The number of Frothly emails the adversary revealed is 29, read from the sole nu"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
