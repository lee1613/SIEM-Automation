# s1 - Q219 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=4_
**Scope:** index=botsv3 sourcetype=stream:smtp (single Amazon event); corroborated by ms:o365:reporting:messagetrace
**Insight:** FOUND   **Candidate:** 5244329601   **Confidence:** 95

## Prior rounds
- R1: Found the only Amazon-originating email in stream:smtp (2018-08-20T09:16:54Z, SPF/DKIM/DMARC pass); rex-extracted case ID 5244329601; messagetrace initially ruled out on sender-list evidence.
- R2: Verified recipient (bstoll@froth.ly, TO), compromise text ("Your AWS Account is compromised!"), and subject ("Amazon Web Services: New Support case: 5244329601") from the same event; filed premises p1/p2.
- R3 (this round): Consolidated single-query verification of all three elements; discovered messagetrace ALSO carries the same message, corroborating the case ID from a second feed.

## This round
### What I ran
- Consolidated rex query on the Amazon stream:smtp event -> one row: receiver_email=bstoll@froth.ly, receiver_type=TO, subject="Amazon Web Services: New Support case: 5244329601", compromise_notice="Your AWS Account is compromised! Please review the following notice and take immediate action to secure your account."
- messagetrace search for the case ID / amazon / compromised -> 3 events from no-reply-aws@amazon.com, same subject
- messagetrace recipient breakdown -> bstoll@froth.ly Delivered 2018-08-20T09:16:53Z (plus attacker-forwarded copies to hyunki1984@naver.com Failed and ubuntu@ec2-52-38-112-145 Delivered)

### What it means
p1 VERIFIED: the stream:smtp event is the AWS compromise notification to Bud (bstoll@froth.ly, TO), with authenticated amazon.com origin and compromise text naming account 622676721278. The coverage clause is amended, not broken: messagetrace also carries the identical message and independently confirms the same case ID. p2 VERIFIED: the subject line labels 5244329601 as the "New Support case"; the only other long digit string (622676721278) is labeled as the AWS account ID. The support case ID Amazon opened on Bud's behalf is 5244329601, unchanged across all rounds.

## Ruled out
- AWS account ID 622676721278 - labeled as the account ID in the body, not the support case
- hyunki1984@naver.com and ubuntu@ec2-52-38-112-145 recipients of the same message - attacker forwarding targets, not Bud; bstoll@froth.ly is the Frothly recipient
- All other stream:smtp events - internal Frothly traffic; only 1 of 879 mentions amazon

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp'] sources=[] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'MessageTraceId', 'src_user', '_raw', 'content', 'attach_filename']
- Rounds worked: 3/3  (iterations: 27, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "5244329601" | stats count by sourcetype, source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "5244329601" OR "amazon" OR "compromised" | stats count by SenderAddress, Subject
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="bstoll@froth.ly" OR RecipientAddress="bstoll@froth.ly" | stats count by SenderAddress, RecipientAddress, Subject | sort - count
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="no-reply-aws@amazon.com" | stats count by RecipientAddress, Subject, DateReceived, Status
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?<all_emails>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})" max_match=100 | stats values(all_emails) as emails, count by _time
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?<body_text>Dear[^\\\\]{0,300})" | stats values(body_text)
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?<comp_text>[^\\\\]{0,250}compromis[^\\\\]{0,250})" max_match=5 | stats values(comp_text)
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?<context>[^\\\\]{0,200}5244329601[^\\\\]{0,200})" | stats values(context)
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?<to_context>[^\\\\]{0,120}bstoll@froth\.ly[^\\\\]{0,80})" max_match=10 | stats values(to_context)
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "(?i)case\s*(?:id|number|#)?\s*[:=]?\s*(?<case_id>[0-9]{7,12})" | stats count by case_id
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "\"receiver_email\":\[\"(?<receiver_email>[^\"]+)\"\],\"receiver_type\":\[\"(?<receiver_type>[^\"]+)\"\]" | rex field=_raw "Subject:\\\\r\\\\n\s*(?<subject>[^\\\\\"]+)" | rex field=_raw "(?<compromise_notice>[^\\\\]{0,150}Account is compromised[^\\\\]{0,150})" | stats values(receiver_email) as receiver_email, values(receiver_type) as receiver_type, values(subject) as subject, values(compromise_notice) as compromise_notice
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "Subject:\\\\r\\\\n\s*(?<subject>[^\\\\\"]+)" | rex field=_raw "Subject:\s*(?<subject2>[A-Za-z0-9 .:'!()\-]+)" | stats values(subject) as s1, values(subject2) as s2
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "To:\\\\r\\\\n\s*(?<to_line>[^\\\\]+)" | rex field=_raw "To:\s+(?<to_addr>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})" | stats count by to_addr
- index=botsv3 sourcetype=stream:smtp "amazon" | rex field=_raw "To:\s*(?<recipient>[^\\\\\"]+)" | stats count by recipient
- index=botsv3 sourcetype=stream:smtp "amazon" | stats count by src_ip, bytes | sort - count
- index=botsv3 sourcetype=stream:smtp "bstoll" | rex field=_raw "\"sender_alias\":\s*\"(?<sender_alias>[^\"]+)\"" | rex field=_raw "\"receiver_alias\":\s*\"(?<receiver_alias>[^\"]+)\"" | stats count by sender_alias, receiver_alias | sort - count
