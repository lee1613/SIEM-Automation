# Q219 — SH <-> Senior conversation

### 16:50:16 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp'] sources=- fields=['SenderAddress', 'RecipientAddress', 'Subject', 'DateReceived', 'MessageTraceId', 'src_user', '_raw', 'content', 'attach_filename']
**Technique:** senior
**Reason:** The question asks for a support case ID opened by Amazon on Bud's behalf after compromise notification, which is most likely recorded in email metadata or SMTP message content. Message trace can identify candidate AWS-to-Bud messages by sender/subject/time, and stream:smtp can provide the body text needed to read the case ID literally.

Identify the AWS notification email Bud received shortly after exposing AWS access keys, then determine the Amazon support case ID named in that message and return it exactly as recorded.

### 16:51:12 - s1 -> SH   [REPORT - round 1 - FOUND]
> The single Amazon-authenticated email in the dataset is the AWS notification; its content contains exactly one case-ID-shaped token, 5244329601 (10 digits, AWS support case format). Not yet visually confirmed: the full email body text around the case ID, the recipient address (expected btun@froth.ly
_full: reports/s1_round_1.md_

### 16:51:18 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Use the same authenticated Amazon SMTP event to settle both identity and value: confirm it is addressed to Bud and that its subject/body is the compromise notification, then read the support case ID literally from that message.

**continue** — This round found the only Amazon email in the captured SMTP traffic and a candidate labeled case ID, which is strong progress in the right feed. But the answer chain still needs the message itself to tie that case ID to Bud and to the AWS compromise notification described in the question.

From the single Amazon-originating stream:smtp event, establish three things from result output: that Bud is the recipient, that the message is the AWS compromise notification sent shortly after the exposed-key incident, and that the support case ID is the labeled value in that same message. Restate the case ID literally if unchanged.

### 16:53:11 - s1 -> SH   [REPORT - round 2 - FOUND]
> All three required elements verified from the single Amazon-authenticated stream:smtp event (2018-08-20T09:16:54Z): (1) RECIPIENT — receiver_email=bstoll@froth.ly, receiver_type=TO; bstoll@froth.ly is the only froth.ly address anywhere in the message, and Bud Stoll is the Frothly persona for that ma
_full: reports/s1_round_2.md_

### 16:53:16 - SH -> s1   [COMMAND]
**continue** — The right SMTP artifact has been found and linked to Bud plus the compromise-notification context, but the answer is still blocked by the cut-off round and the two unverified premises in the ledger. The final round should do nothing broader than quote the exact message fields that identify the notification and its support case ID.

From the same Amazon-authenticated stream:smtp message, provide exact word-for-word result output that verifies p1 and p2: the recipient field showing bstoll@froth.ly as TO, the compromise-notification text naming the account as compromised, and the subject line containing the labeled support case value. Then restate the support case ID literally if unchanged.

### 16:54:02 - s1 -> SH   [REPORT - round 3 - FOUND]
> Both premises settled this round with word-for-word output. p1 VERIFIED: the stream:smtp event shows receiver_email=bstoll@froth.ly with receiver_type=TO, body text "Your AWS Account is compromised! Please review the following notice and take immediate action to secure your account.", subject "Amazo
_full: reports/s1_round_3.md_

### 16:54:09 - SH -> s1   [ANSWER]
**5244329601** (case_id) from s1

The report gives one consolidated result row from the Amazon-authenticated stream:smtp message showing receiver_email=bstoll@froth.ly, receiver_type=TO, subject="Amazon Web Services: New Support case: 5244329601", and compromise-notice text stating the AWS account is compromised. messagetrace independently corroborates the same message and subject, so 5244329601 is the support case ID Amazon opened on Bud's behalf.

**Premises it rests on:** p1, p2

### 16:54:09 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

