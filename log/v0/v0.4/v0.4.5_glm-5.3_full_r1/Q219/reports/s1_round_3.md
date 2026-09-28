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