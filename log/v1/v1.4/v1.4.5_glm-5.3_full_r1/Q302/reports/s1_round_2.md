# s1 - Q302 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=5_
**Scope:** sourcetype=symantec:ep:risk:file, symantec:ep:security:file, o365:management:activity, ms:o365:reporting:messagetrace, stream:smtp, WinEventLog | fields=signature/Risk_Name, file_name, SourceFileName, SourceFileExtension, Operation, UserId

**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1 (this round): enumerated sourcetypes; queried both Symantec detection feeds and the Office 365 / SMTP / Windows feeds for macro-enabled files and malware names.

## This round
### What I ran
- get_sourcetype_fields symantec:ep:risk:file -> 1 event: Risk name "Backdoor.PsEmpire" on "Bruce Birthday Happy Hour Pics.lnk" (an .lnk shortcut, not macro-enabled), cleaned by deletion on BGIST-L.
- get_raw_events symantec:ep:risk:file -> confirmed the single event verbatim; no other detections in this feed.
- sourcetype=symantec:ep:security:file | stats count by signature, file_name -> 4 rows: "Web Attack: JSCoinminer Download 6/8" on CHROME.EXE and MICROSOFTEDGECP.EXE only; no documents.
- o365:management:activity macro-extension search -> only "Brewing.xlsm", Operation=FileAccessed by app@sharepoint (UserAgent=ExportWorker) — an automated export, no malware.
- keyword ".docm" in o365:management:activity, "docm" in stream:smtp, "macro" in WinEventLog -> 0 events each.

### What it means
NOT_FOUND: no macro-enabled file in the feeds I queried carries a malware identification. The two Symantec malware names in scope (Backdoor.PsEmpire, JSCoinminer) are attached to an .lnk shortcut and to browser processes respectively — neither to a macro-enabled document. The only macro-enabled file found (Brewing.xlsm) has a single benign automated-access record. Without a malware name tied to a macro-enabled file, the Symantec discovery date cannot be determined, and I did not guess one.

## Ruled out
- symantec:ep:risk:file as the source of a macro-enabled-file malware name — its only detection is on an .lnk file.
- symantec:ep:security:file — only JSCoinminer web-attack signatures on browser executables.
- o365:management:activity / stream:smtp / WinEventLog for macro-enabled attachments or macro warnings — zero matching events.
- Brewing.xlsm as the malicious macro-enabled file — its only record is an automated FileAccessed with no detection.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
