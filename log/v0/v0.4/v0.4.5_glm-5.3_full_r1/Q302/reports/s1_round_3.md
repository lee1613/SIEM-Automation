# s1 - Q302 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=4_
**Scope:** sourcetype=symantec:ep:risk:file, symantec:ep:security:file, symantec:ep:behavior:file, symantec:ep:agent:file, symantec:ep:packet:file, symantec:ep:scm_system:file, symantec:ep:agt_system:file, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, o365:management:activity | fields=Risk_Name/signature, file_name, TargetFilename, Image, SourceFileName, SourceFileExtension

**Insight:** partial
**Candidate:** 07/20/18   **Confidence:** 55

## Prior rounds
- Round 1: Enumerated all sourcetypes. symantec:ep:risk:file held one detection (Backdoor.PsEmpire on Bruce Birthday Happy Hour Pics.lnk); symantec:ep:security:file held JSCoinminer on browsers; only macro-enabled file found was benign Brewing.xlsm. Filed NOT_FOUND.

## This round
### What I ran
- get_sourcetype_fields on symantec:ep:behavior:file, agent:file, packet:file, scm_system:file, agt_system:file (5 calls) -> application-control blocks on Splunk scripts, client management logs, network traffic, LiveUpdate messages, IPS submissions. No malware names, no documents.
- search_keyword "macro" -> 0 events index-wide.
- Sysmon TargetFilename="*.xlsm" OR "*.docm" OR "*.dotm" OR "*.xlam" -> 2 events: (1) C:\Users\BruceGist\AppData\Local\Packages\microsoft.windowscommunicationsapps_...\Files\S0\3\Frothly-Brewery-Financial-Planning-FY2019-Draft[66].xlsm created by HxTsr.exe (Windows Mail); (2) C:\ProgramData\Symantec\Symantec Endpoint Protection\14.2.760.0000.105\SRTSP\Quarantine\AP4D3C539B.xlsm created by System at 2018-08-20T17:55:54+08:00.
- Sysmon "Frothly-Brewery-Financial-Planning" and "AP4D3C539B" -> 1 event each, confirming the two records above.
- symantec:ep:risk:file | stats count by Risk_Name, file_name, file_path, _time -> 1 event: Backdoor.PsEmpire, Bruce Birthday Happy Hour Pics.lnk, BGIST-L, BruceGist, Event time 2018-08-20 09:58:20.

### What it means
The macro-enabled file is Frothly-Brewery-Financial-Planning-FY2019-Draft[66].xlsm — a macro-enabled workbook emailed to BruceGist, saved by the Windows Mail app, and quarantined by Symantec (AP4D3C539B.xlsm, 09:55:54 UTC). The malware Symantec identifies in this intrusion is Backdoor.PsEmpire — its only risk detection, on the same host (BGIST-L) and user (BruceGist) 2.5 minutes after the .xlsm quarantine; the .lnk it names is the payload the macro-enabled file's campaign delivers. Symantec's security-center writeup for Backdoor.PsEmpire lists its discovery date as July 20, 2018, i.e. 07/20/18. Caveat, stated plainly: the malware name is evidenced in the dataset; the date is from Symantec's published writeup recalled from memory — web_lookup was unavailable this round, so the date could not be re-verified against the live site. Treat 07/20/18 as a candidate pending that verification.

## Ruled out
- Brewing.xlsm — only other macro-enabled file in O365 activity; single benign FileAccessed by app@sharepoint (ExportWorker), no detection, no quarantine.
- JSCoinminer (symantec:ep:security:file) — web-attack signatures on CHROME.EXE/MICROSOFTEDGECP.EXE only; unrelated to any document.
- symantec:ep:behavior:file, agent:file, packet:file, scm_system:file, agt_system:file — administrative, traffic, and IPS-submission content; no malware names tied to documents.
- Bruce Birthday Happy Hour Pics.lnk as "the macro-enabled file" — it is a shortcut, not a macro-enabled document; it is the detected payload.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The malware identified in association with the macro-enabled file is Backdoor.Ps"
