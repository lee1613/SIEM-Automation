# s1 - Q218 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=2_
**Scope:** index=botsv3 sourcetype=aws:cloudtrail eventSource=iam.amazonaws.com userIdentity.type=IAMUser | fields userIdentity.accessKeyId, userName, eventName, errorCode, errorMessage
**Insight:** FOUND
**Candidate:** AKIAJOGCDXJ5NW5PXUPA   **Confidence:** 70

## Prior rounds
- R1: Key field is userIdentity.accessKeyId. Strict iam.amazonaws.com scope: 3 erroring IAMUser keys tied at 1 distinct errorCode. Broad IAMUser scope: ASIAZB6TMXZ7FWTIS4NJ led with 6 distinct errorCodes (all S3 NoSuch*). resources{}.type=AWS::IAM::Role: 332 events, all AWSService.
- R2: STS/signin carry zero error events; IAM-Role resources carry no access key. errorMessage discovered: web_admin's key has 5 distinct on iam.amazonaws.com vs 1 and 1. Broad-scope leader's records shown to be S3 bucket-config enumeration, not IAM access — refuted as the answer.

## This round
### What I ran
- `eventSource=iam.amazonaws.com userIdentity.type=IAMUser errorCode!="success" | stats count dc(errorCode) as distinct_errorCodes dc(errorMessage) as distinct_errorMessages dc(eventName) as distinct_denied_ops by userIdentity.accessKeyId, userName | sort - distinct_errorMessages` → 3 rows (complete): AKIAJOGCDXJ5NW5PXUPA (web_admin) 6 events / 1 distinct errorCode (AccessDenied) / 5 distinct errorMessages / 5 distinct denied ops; AKIAIGKL572SFDPOKLHA (splunk_access) 9 / 1 (NoSuchEntityException) / 1 / 1; ASIAZB6TMXZ7MJUJJK6X (bstoll) 2 / 1 (NoSuchEntityException) / 1 / 1.
- `eventSource=iam.amazonaws.com userIdentity.accessKeyId=AKIAJOGCDXJ5NW5PXUPA errorCode!="success" | stats count values(eventName) by errorMessage` → 5 rows (complete), one per distinct message: iam:CreateAccessKey on user nullweb_admin; iam:CreateUser on arn:aws:iam::622676721278:user/my_db_user; iam:DeleteAccessKey on user nullweb_admin; iam:GetUser on user web_admin; iam:ListAccessKeys on user nullweb_admin (2 events).

### What it means
If "distinct errors" is compelled to mean distinct errorCode VALUES, the strict reading has NO unique winner: all three erroring IAMUser keys tie at exactly 1. The records support distinct errors as the distinct IAM access failures themselves: web_admin's key generated 5 distinct error messages, each a distinct denied iam: operation against a distinct IAM user resource — five distinct IAM access failures, not one — while splunk_access generated 1 distinct error repeated 9 times and bstoll 1 repeated twice. SH's discriminator ("distinct error count rather than total event count") only functions under this measure: web_admin has fewer IAM error events (6) than splunk_access (9) yet more distinct errors (5 vs 1); under distinct errorCode the hint is inoperative since all tie at 1. AKIAJOGCDXJ5NW5PXUPA is therefore the unique winner, and its records positively show the act named: repeated unauthorized attempts to access IAM user resources (including creating a user my_db_user and creating/deleting access keys) from the compromised web_admin account.

## Ruled out
- Distinct-errorCode-values as the measure on the strict scope — 3-way tie at 1, no unique winner.
- AKIAIGKL572SFDPOKLHA — most IAM-service error events (9) but 1 distinct error (GetAccountPasswordPolicy, one message).
- ASIAZB6TMXZ7MJUJJK6X — 2 IAM error events, 1 distinct error.
- ASIAZB6TMXZ7FWTIS4NJ (broad-scope leader) — 6 distinct errorCodes but all S3 GetBucket* NoSuch* responses, not IAM resource access (refuted R2).