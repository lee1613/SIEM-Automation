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

## What I'd tell my replacement
- Retired because: This senior is circling the same stream:smtp lead without getting p2 verified in a runner-acceptable way. The value may still be right, but another round in the same approach is unlikely to change the ledger state.
- Scope I owned: sourcetypes=['ms:o365:reporting:messagetrace', 'o365:management:activity', 'symantec:ep:traffic:file', 'symantec:ep:packet:file', 'stream:smtp'] sources=[] fields=['SenderAddress', 'RecipientAddress', 'Attachment*', 'Message*', 'Subject', 'file_name', 'attachment', 'url', '_raw']
- Rounds worked: 7/8  (iterations: 49, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 ("coin miner" OR "crypto miner" OR "cryptocurrency miner" OR "miner issue") | stats count by sourcetype, source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace (Subject="*miner*" OR Subject="*coin*" OR Subject="*crypto*" OR Subject="*Miner*" OR Subject="*Coin*" OR Subject="*Crypto*") | stats count by MessageTraceId, SenderAddress, Subject, DateReceived, Size | sort DateReceived
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | stats count by Subject, DateReceived, RecipientAddress | sort DateReceived
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace | stats count by MessageTraceId, SenderAddress, Subject, DateReceived, Size | sort DateReceived
- index=botsv3 sourcetype=o365:management:activity "btun@froth.ly" | stats count by Operation, Workload | sort -count
- index=botsv3 sourcetype=o365:management:activity | stats count by Operation, Workload | sort -count
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | rex field=_raw "To: (?<to_line>[^\\\\]+)" | rex field=_raw "Date: (?<date_hdr>[^\\\\]+)" | stats count values(filenames) as attach_filenames by _time, subject, to_line, date_hdr | sort _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\r]+)" | rex field=_raw "To: (?<to_line>[^\r]+)" | stats count values(filenames) as attach_filenames values(to_line) as to by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | stats count values(filenames) as attach_filenames values(attach_type) as types by from_name, from_addr | sort from_name
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | eval has_miner=if(match(_raw,"(?i)miner"),"yes","no"), has_splunk=if(match(_raw,"(?i)splunk"),"yes","no"), has_chart=if(match(_raw,"(?i)chart"),"yes","no"), has_cpu=if(match(_raw,"(?i)cpu"),"yes","no") | stats count values(has_miner) as miner values(has_splunk) as splunk values(has_chart) as chart values(has_cpu) as cpu by _time, subject
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="Postmortem on our issue with brewertalk" | rex field=_raw "(?s)(?<ctx>.{0,600})cid:image002" | stats list(ctx) as context by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="Postmortem on our issue with brewertalk" | rex field=_raw "(?s)quoted-printable\\\\r\\\\n\\\\r\\\\n(?<body>.{0,2000})" | stats list(body) as body_text by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="Postmortem on our issue with brewertalk" | rex field=_raw "(?s)text/plain[^\"]*\\\\\"[^\\\\]*\\\\\"\\\\r\\\\n[^\\\\]*\\\\r\\\\n\\\\r\\\\n(?<body>.{0,2500})" | stats list(body) as body_text by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" OR subject="Postmortem on our issue with brewertalk" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "(?s)(?<body_snip>.{0,260})\[cid:image00" | stats count values(filenames) as attach_filenames list(body_snip) as body_before_cid by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" OR subject="Postmortem on our issue with brewertalk" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "(?s)(?<body_snip>.{0,300})\[cid:image00" | stats count values(filenames) as attach_filenames list(body_snip) as body_before_cid by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" | rex field=_raw "(?s)(?<before_chart>.{0,300})chart" | rex field=_raw "(?s)chart(?<after_chart>.{0,300})" | stats list(before_chart) as before, list(after_chart) as after by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" | rex field=_raw "(?s)(?<before_chart>.{300})chart" | rex field=_raw "(?s)chart(?<after_chart>.{300})" | table _time, before_chart, after_chart
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" | rex field=_raw "(?s)quoted-printable\\\\r\\\\n\\\\r\\\\n(?<body>.{0,1500})" | stats list(body) as body_text by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" | rex field=_raw "(?s)quoted-printable\r\n\r\n(?<body>.{0,1200})" | stats list(body) as body_text by _time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | search subject="RE: Improved brewertalk.com - check it out!" | rex field=_raw "Date: (?<date_hdr>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "(?s)(?<body_snip>.{0,320})\[cid:image00" | stats count values(date_hdr) as Date values(filenames) as attach_filenames list(body_snip) as body_before_cid by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | stats count by content_type
- index=botsv3 sourcetype=stream:smtp "From: Bud Stoll" "attach_filename" | stats count by _time, attach_filename, attach_type, bytes | sort _time
- index=botsv3 sourcetype=stream:smtp "From: Bud Stoll" attach_filename=* | stats count values(attach_filename) as filenames values(attach_type) as types by _time | sort _time
- index=botsv3 sourcetype=stream:smtp "From: Bud Stoll" | stats count
- index=botsv3 sourcetype=stream:smtp "Has-Attach" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "\"attach_size\":\[(?<sizes>[^\]]*)\]" | stats count values(filenames) as filenames values(sizes) as attach_sizes values(bytes) as email_bytes by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "Has-Attach" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | stats count values(filenames) as attach_filenames by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp "X-MS-Has-Attach: yes" | rex field=_raw "From: (?<from_name>[^<]+)<(?<from_addr>[^>]+)>" | search from_addr="bstoll@froth.ly" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | rex field=_raw "\"attach_size\":\[(?<sizes>[^\]]*)\]" | stats count values(sizes) as attach_sizes by _time, subject | sort _time
- index=botsv3 sourcetype=stream:smtp attach_filename=* | stats count
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "filename=\"?(?<att_filename>[^\"\r\n;]+)\"?" | stats count by att_filename | sort -count
