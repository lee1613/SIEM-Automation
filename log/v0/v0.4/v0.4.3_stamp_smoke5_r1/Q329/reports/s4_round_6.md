# s4 - Q329 - Round 6
_stamped by runner: rounds_remaining=2 novel_spl=9_
**Scope:** sourcetype=stream:smtp | fields=_raw read via substr windows, attachment names via rex
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: literal "taedonggang"/"taedong" absent in o365/smtp; O365 FileUploaded = 7 Frothly-user uploads to own OneDrive.
- R2: code42 UPLOAD set enumerated via mvzip (ba_advertising_code_overview.pdf, frothly_gabf_deck-2018-mk.pptx, frothly_html_memcached.tar.gz); SMTP attachment names listed.
- R3: filename absent from web logs (field-name errors); critic flagged a pivot to unrelated POST traffic.
- R4: upload channel found — 3 anonymous S3 PUTs to frothlywebcode (tarball twice, OPEN_BUCKET_PLEASE_FIX.txt); no content carrier in web feeds.
- R5: downstream traced — EC2 instances pulled the tarball 13:33:34 (defacement live on brewertalk.com), bstoll restored 14:19:19; pwned.jpg email located.

## This round
### What I ran
- Field-filter attempts (attach_filename=, quoted phrases, mvindex(content)) -> all 0; only rex on _raw works on this feed.
- substr windows on the pwned.jpg raw event (offsets 1300–12500, read to the base64 boundary) -> full readable text: btun→pcerf "RE: meeting with F"; the ONLY body text is Peat Cerf's quoted joke about Fyodor's Russian accent and "shrimpchips"; then "Content-Type: image/jpeg; name=\"pwned.jpg\"... base64" and pure image data. No defacement wording.
- substr windows on the "Malware Alert Text.txt" email -> bgist→bstoll/fyodor/ghoppy/abungstein, "Draft Financial Plan for Brewery FY2019", body: "Here is a financial model we can use for FY2019 planning. For the worksheet to operate properly, you will need to enable macros." — the macro lure; attachment is base64 beyond.

### What it means
The two most promising mail artifacts are read to their content boundaries and neither carries the defaced page's wording: pwned.jpg is a bare image with an empty covering message, and the Malware Alert Text.txt attachment is the macro lure document. No feed I could reach exposes the tarball's HTML, and per SH's explicit instruction I do not infer the word from common defacement vocabulary. The word cannot be stated from evidence I hold; the mail path in my scope is exhausted, and the remaining unsearched feeds (messagetrace, endpoint, cloudtrail, two unread emails) are outside what I could still query.

## Ruled out
- pwned.jpg email as a textual source — read in full; only the Fyodor joke, then base64 image.
- "Malware Alert Text.txt" email — macro lure from compromised bgist, not a Taedonggang S3 upload; content base64.
- stream:http / aws:elb:accesslogs / access_combined / aws:s3:accesslogs as content carriers (R4–R5).
- OPEN_BUCKET_PLEASE_FIX.txt — plain text, no font sizing.
- attach_filename / content as search-time fields on stream:smtp — all such filters return 0; rex on _raw is required.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "The mail-content path for the defacement word is exhausted: the pwned.jpg email "
