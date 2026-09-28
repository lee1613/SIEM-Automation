# Q302 — SH <-> Senior conversation

### 18:48:48 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['symantec:ep:risk:file', 'symantec:ep:security:file', 'symantec:ep:behavior:file', 'symantec:ep:agent:file', 'o365:management:activity', 'ms:o365:management'] sources=- fields=['Risk name', 'Signature', 'SourceFileName', 'SourceFileExtension', 'file_name', 'ObjectId', 'UserAgent', 'Host_Name', 'Computer name']
**Technique:** senior
**Reason:** The question depends first on naming the malware from endpoint or file-related telemetry around a macro-enabled document, then on obtaining the vendor-stated discovery date for that exact malware. Symantec endpoint feeds are the likely place to identify the malware name, while Office 365 file activity may help pinpoint the macro-enabled file if needed.

Identify the malware associated with the macro-enabled file in Frothly's records, then determine what discovery date Symantec assigns to that exact malware according to Symantec's website, and return the date in MM/DD/YY format exactly as evidenced.

### 18:49:37 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s1_round_1.md_

### 18:49:43 - SH -> s1   [COMMAND]
**retry** — The direction toward Symantec and O365 file activity is right, but the first pass did not isolate the macro-enabled file or any malware name. The case must first connect a specific macro-enabled document to a Symantec malware identification before looking for a discovery date.

Determine which macro-enabled file in the dataset is associated with a malware detection, and identify the exact malware name from the record that names it. Search the O365 activity data for macro-enabled file operations and the Symantec endpoint feeds for detections tied to document files or macro-enabled Office artifacts; once the malware name is established, determine whether any Symantec-provided artifact in scope records its discovery date and return that date if it does.

### 18:51:25 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> What I learned: the Symantec endpoint feeds in scope contain exactly two malware families — Backdoor.PsEmpire (risk:file, detected on an .lnk shortcut, not a macro-enabled document) and JSCoinminer (security:file, detected on browser processes). Neither is tied to a macro-enabled Office file. The on
_full: reports/s1_round_2.md_

### 18:51:34 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] No searched feed yet ties a malware name to a macro-enabled file. The only macro-enabled file found so far is Brewing.xlsm, and its only record is a benign FileAccessed event by app@sharepoint.
[q2] The remaining useful path is to search other malware/file-identifying endpoint feeds for document-linked detections or evidence around the macro-enabled file itself; without a malware name, the Symantec website discovery date cannot be determined.

**retry** — The current feeds established a negative result for the obvious Symantec and O365 paths, but the question still turns on identifying a malware name from a macro-enabled file record. With one round left, the work must focus on any remaining endpoint/security feed that can associate malware with a document file rather than re-running the same searches.
**New scope:** sourcetypes=['symantec:ep:agent:file', 'symantec:ep:packet:file', 'symantec:ep:traffic:file', 'symantec:ep:behavior:file', 'WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'o365:management:activity'] sources=[] fields=['file_name', 'signature', 'Risk name', 'TargetFilename', 'Image', 'SourceFileName', 'SourceFileExtension', 'Operation', 'UserId', '_raw']

Search the remaining endpoint/security feeds that can associate malware or file activity with Office documents, and determine whether any record names malware for a macro-enabled file such as Brewing.xlsm or another .xlsm/.docm/.dotm artifact. If no such feed names malware for a macro-enabled file, state explicitly that the dataset supports a macro-enabled file artifact and separate malware detections, but not a linkage between them, so no Symantec discovery date can be read from evidence.

### 18:55:18 - s1 -> SH   [REPORT - round 3 - FOUND]
> Chain established from data: macro-enabled file = Frothly-Brewery-Financial-Planning-FY2019-Draft[66].xlsm (email attachment saved by Windows Mail HxTsr.exe into BruceGist's profile, Sysmon EventCode 11), quarantined by Symantec as AP4D3C539B.xlsm at 2018-08-20T17:55:54+08:00 (09:55:54 UTC). Malware
_full: reports/s1_round_3.md_

### 18:55:25 - runner   [NOTE]
TURN REJECTED:
- [REFERENCE: GATES] ANSWER is blocked: s1's last round was cut off at the iteration cap — CLARIFY it (costs no round; its reply clears this block) or COMMAND one more round before answering from it → re-read REFERENCE: GATES.
- [F2–F3] ANSWER from s1 names no premises - trace the chain from the question to the value and cite every premise it rests on in answer_premise_ids → re-read F2–F3.

### 18:55:30 - runner   [NOTE]
TURN REJECTED:
- [C5] s1 is waiting on q3, q4 - answer each by id in open_question_answers → re-read C5.

### 18:55:30 - runner   [NOTE]
question ended: turns — no ANSWER from SH; submitting 'SH retired without answering'

### 18:55:30 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

