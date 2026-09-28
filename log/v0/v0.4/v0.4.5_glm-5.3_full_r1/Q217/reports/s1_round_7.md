# s1 - Q217 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=1_
**Scope:** sourcetype=stream:smtp | fields=_raw, attach_filename, From, To, Subject, Date
**Insight:** FOUND
**Candidate:** line chart   **Confidence:** 75

## Prior rounds
R1: Email feeds enumerated; messagetrace has no attachment fields; stream:smtp holds full SMTP MIME.
R2: Bud = Bud Stoll <bstoll@froth.ly>; 4 Bud attachment emails found in stream:smtp.
R3: Ordered the 4 emails, read both thread bodies, rendered image001.jpg (column chart) and image002.jpg (line chart); submitted "line chart".
R4: Rendered image003.jpg and postmortem image002.jpg (both the quoted column chart), decoded postmortem ("coinminer"), completed 11-email Bud inventory; only 4 emails carry attachments.
R5: Consolidated three-way comparison; settled p1 and p2.
R6: Re-ran three-way comparison for verbatim quotes; p2 settled VERIFIED.
R7 (this): Re-ran the two-row comparison with Date headers; p2 settled VERIFIED with full quotes.

## This round
### What I ran
- stream:smtp "attach_filename" | rex From/Subject/Date/attach_filename/body-before-CID | search bstoll, subject="RE: Improved brewertalk.com - check it out!" -> 2 of 2 rows, complete: 21:50:47 (Date 02:38:43) [image001.jpg] "I haven't figured it out yet... metrics store search"; 21:56:27 (Date 02:44:24) [image002.jpg, image003.jpg] "I did find the issue! Look at the Splunk chart below... CPU... spiked to 100%!... some malicious code got into our forums".

### What it means
FOUND, unchanged. p2 VERIFIED from word-for-word output: the 21:50:47 email (Date 02:38:43) has one attachment and Bud's text shows the issue unidentified; the 21:56:27 email (Date 02:44:24) is the first in which Bud identifies and illustrates the issue ("Look at the Splunk chart below... spiked to 100%... malicious code"), named "coinminer" in the postmortem, and its first attachment image002.jpg renders as a Splunk line chart (timechart avg(%_Processor_Time) span=10s by instance, Chrome instances at ~100% CPU). Answer: line chart.

## Ruled out
- image001.jpg / column chart (21:50:47 email) - Bud hadn't identified the issue; single-attachment email makes "first" vacuous.
- Postmortem email's image002.jpg and image003.jpg (column charts) - quoted copies of the earlier metrics-store search; postmortem is the thread's last email.
- Birthday email image002.jpg (19:21, to Peat Cerf only) - not miner-related, single recipient.
- Billy Tun (btun@froth.ly) as "Bud" - From lines distinguish Bud Stoll from Billy Tun.
- messagetrace / o365:management:activity / ess_content_importer as attachment sources - no attachment fields / no send events / errors only.