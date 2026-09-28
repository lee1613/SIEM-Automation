# s1 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** sourcetype=stream:smtp | fields=_raw, attach_filename, attach_type, content, From, To, Subject, Date
**Insight:** FOUND
**Candidate:** line chart   **Confidence:** 70

## Prior rounds
R1: Email feeds enumerated; messagetrace has no attachment fields (Aug 20 only); o365:management:activity has no send events; stream:smtp holds full SMTP MIME — unread.
R2: Bud = Bud Stoll <bstoll@froth.ly> (not Billy Tun); stream:smtp _raw carries attach_filename/attach_type + full MIME; 4 Bud attachment emails found; "Postmortem on our issue with brewertalk" (image002.jpg) confirmed.
R3: Ordered all 4 Bud attachment emails, read both thread bodies, viewed both candidate attachments.

## This round
### What I ran
- stream:smtp "attach_filename" | rex From/Subject/To/Date | search bstoll@froth.ly -> 4 complete events: 19:21 "RE: FW: Wild Birthday Extravaganza!!!"→Peat Cerf only (image002.jpg); 21:50:47 "RE: Improved brewertalk.com - check it out!"→Billy Tun+allhands (image001.jpg); 21:56:27 same subject→Billy Tun+allhands (image002.jpg, image003.jpg); 22:24:23 "Postmortem on our issue with brewertalk"→Billy Tun+allhands (image002.jpg).
- Keyword flags per email -> only the 21:56:27 email mentions Splunk + chart + CPU.
- Body extraction -> 21:50:47: "Yeah. It looks like we have some issues - I haven't figured it out yet...but check out the metrics store search below.... I'll figure it out! -bud [cid:image001.jpg]"; 21:56:27: "Wow Billy. I did find the issue! Look at the Splunk chart below - ...CPU of my local Chrome browser...spiked to 100%!...some malicious code got into our forums. [cid:image002.jpg]".
- read_image image001.jpg (21:50:47 email) -> column chart: mstats avg(processor.%_processor_time) by host | timechart avg(CPU) by host, 12:45–1:00 AM Jul 26.
- read_image image002.jpg (21:56:27 email, FIRST of its two attachments) -> line chart: timechart avg(%_Processor_Time) span=10s by instance, Chrome instances spiking to ~100% CPU.

### What it means
FOUND. The email in which Bud illustrates the coin miner issue to Frothly employees is the 21:56:27 (+08) "RE: Improved brewertalk.com - check it out!" reply to Billy Tun + allhands@froth.ly: "I did find the issue! Look at the Splunk chart below... CPU of my local Chrome browser spiked to 100%!... some malicious code got into our forums." Its first file attachment is image002.jpg, which renders as a Splunk line chart — timechart of % Processor Time by Chrome instance, spiking to 100% (the miner). Answer: line chart.

Ambiguity flagged to SH: the 21:50:47 email (6 min earlier) carries image001.jpg, a column chart of CPU by host — but Bud's own text there is "I haven't figured it out yet... check out the metrics store search below" (unidentified issue; single attachment, making "first file attachment" vacuous). The question's "first file attachment" fits the two-attachment "I did find the issue!" email.

## Ruled out
- Billy Tun (btun@froth.ly) as "Bud" — From lines distinguish Bud Stoll from Billy Tun.
- Birthday email (19:21, image002.jpg to Peat Cerf only) — not miner-related, single recipient.
- Postmortem email's image — last email in the thread, not first.
- image001.jpg (column chart) as the answer — sits in the earlier "some issues / metrics store search" email where Bud had not identified the issue; not sent "to illustrate the coin miner issue".

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\…` (2 of 4 rows seen). A claim resting on them alone is UNVERIFIED._
