# Q212 — SH <-> Senior conversation

### 14:09:08 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['symantec:ep:risk:file', 'symantec:ep:security:file', 'symantec:ep:behavior:file', 'symantec:ep:traffic:file'] sources=- fields=['signature_id', 'sig_id', 'rule_id', 'event_time', '_time', 'risk_name', 'virus', 'threat_name', 'computer_name', 'host', 'severity']
**Technique:** metrics
**Reason:** The question binds to SEP data and asks for a signature ID chosen by first-seen event order, which is a computed result best handled as a metrics task. The relevant evidence should sit in SEP threat/risk/security feeds that carry threat names, signature identifiers, timestamps, and endpoint identifiers.

Using Frothly's Symantec Endpoint Protection data, identify the coin miner threat detection(s), then determine the first seen signature ID by event order and return that signature ID exactly as recorded. Use BSTOLL-L as a carried-forward lead to test, but also verify whether any other SEP-recorded endpoint has coin miner detections relevant to the question.

### 14:11:11 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> The coin miner threat in SEP data is fully identified: "Web Attack: JSCoinminer Download" IDS detections, 46 events, ALL on BTUN-L (user BillyTun, browser Edge/Chrome, blocked inbound from 54.67.127.227 = brewertalk.com pages). Exactly TWO signature IDs exist: 30356 ("Web Attack: JSCoinminer Downloa
_full: reports/s1_round_1.md_

### 14:11:17 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Use SEP event-order evidence to decide between 30356 and 30358. Because your own report notes a conflict between only 2 distinct _time values and 15 distinct Begin_Times, you must establish which timestamp field the first-seen calculation should use in this SEP feed, then return the first signature ID on that basis.

**continue** — The right SEP feed and candidate signature IDs are now known, but the question explicitly asks for the first seen signature ID using event order functions, and that computation has not been done. The ordering field ambiguity is load-bearing and must be resolved from the SEP records before any answer is possible.
**New scope:** sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:traffic:file', 'symantec:ep:packet:file', 'symantec:ep:agent:file', 'symantec:ep:agt_system:file', 'symantec:ep:scm_system:file'] sources=[] fields=['signature_id', 'CIDS_Signature_ID', 'signature', 'Host_Name', 'Begin_Time', '_time', 'Intrusion_URL']

Establish the correct event-order basis inside sourcetype=symantec:ep:security:file for the JSCoinminer detections on BTUN-L. Determine whether first-seen must be taken from Begin_Time, _time, or another SEP event-time field in this feed, and then use event-order logic to identify which of signature IDs 30356 or 30358 appears first. Also confirm whether any other SEP feed or endpoint contains coin-miner detections that would rival BTUN-L in this question’s scope.

### 14:13:44 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s1_round_2.md_

### 14:13:50 - SH -> s1   [COMMAND]
**retry** — The SEP security feed already contains the coin-miner detections and the two candidate signature IDs, so the case now turns on event ordering within that feed. A broad sweep of unexamined SEP feeds is secondary; the last round must first resolve the ordering field and first signature directly from the known detections.
**New scope:** sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:agent:file', 'symantec:ep:agt_system:file', 'symantec:ep:packet:file', 'symantec:ep:scm_system:file', 'symantec:ep:traffic:file'] sources=[] fields=['signature_id', 'CIDS_Signature_ID', 'signature', 'Host_Name', 'Begin_Time', '_time', 'Intrusion_URL']

In sourcetype=symantec:ep:security:file, read the earliest JSCoinminer detection events themselves and determine which signature ID appears first by the feed’s own event-time field. Explicitly compare ordering by Begin_Time versus _time and state which one correctly represents first seen in SEP for these detections. Then state whether any other SEP feed actually contains coin-miner detections that would rival BTUN-L; if not, say so briefly after resolving the first signature ID.

### 14:13:58 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> 
_full: reports/s1_round_3.md_

### 14:13:58 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 14:13:58 - runner   [NOTE]
s1 api_failed — retired, spawn slot refunded

### 14:13:58 - runner   [NOTE]
s1 api_failed and no operator reachable — skipping; slot already refunded, decision request at C:\dev\SIEM-Automation\log\v1\v1.4/v1.4.5_glm-5.3_full_r1\decision_request.json

### 14:14:04 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file'] sources=- fields=['signature_id', 'CIDS_Signature_ID', 'signature', 'Host_Name', 'Begin_Time', '_time', 'Intrusion_URL']
**Technique:** metrics
**Reason:** The prior senior was lost to transport failure, not disproven on scope. The remaining task is confined to SEP event ordering within the known JSCoinminer detections, so a replacement in the same SEP scope is the cheapest honest path.

In Frothly's SEP data, determine the first seen signature ID for the coin miner threat using event-order logic. Start from the established JSCoinminer detections on BTUN-L in symantec:ep:security:file, decide which SEP time field correctly represents first seen for these detections, and then return whether 30356 or 30358 is first. Also verify briefly that no other SEP feed in scope contains a rival coin-miner detection that changes the answer.

### 14:19:28 - s2 -> SH   [REPORT - round 1 - FOUND]
> Answer is 30356 (Web Attack: JSCoinminer Download 6, CIDS Signature SubID 70471), first seen at Begin_Time 2018-08-18 20:51:13 on BTUN-L (user BillyTun, src 54.67.127.227, Intrusion URL www.brewertalk.com). 30358 (JSCoinminer Download 8) first appears one second later at 20:51:14. Margin is one seco
_full: reports/s2_round_1.md_

### 14:19:33 - runner   [NOTE]
TURN REJECTED:
- [REFERENCE: GATES] ANSWER is blocked: s2's last round was cut off at the iteration cap — CLARIFY it (costs no round; its reply clears this block) or COMMAND one more round before answering from it → re-read REFERENCE: GATES.
- [F2] ANSWER is blocked: 4 load-bearing premise(s) it rests on are still UNVERIFIED - COMMAND s2 to settle them: p1 "The coin miner threat in Frothly's SEP data manifests as JSCoinminer web-attack " | p2 "BTUN-L is the only SEP-recorded endpoint with coin miner detections; the carried" | p3 "The coin miner threat in Frothly's SEP data can appear only as coin-miner-named " | p4 "Begin_Time is the SEP time field that correctly represents first seen for the JS" → re-read F2.

### 14:19:33 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

### 14:19:33 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

