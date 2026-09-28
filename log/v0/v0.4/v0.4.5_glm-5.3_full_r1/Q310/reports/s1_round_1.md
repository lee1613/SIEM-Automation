# s1 - Q310 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=symantec:ep:risk:file, symantec:ep:security:file, symantec:ep:behavior:file, symantec:ep:agent:file, symantec:ep:packet:file, symantec:ep:traffic:file, symantec:ep:scm_system:file | fields=file_name, Risk_Name, user, Computer_Name, Event_Time, file_path, action
**Insight:** partial (credible candidate, one linkage unverified)   **Candidate:** Bruce Birthday Happy Hour Pics.lnk   **Confidence:** 80

## Prior rounds
- Round 1 (this round): enumerated all 102 sourcetypes; queried every Symantec feed; found the single file-based malware detection.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; Symantec feeds plus o365/stream:smtp email feeds identified.
- get_sourcetype_fields symantec:ep:risk:file -> the feed's ONLY file_name: "Bruce Birthday Happy Hour Pics.lnk", Risk_Name Backdoor.PsEmpire, BGIST-L/BruceGist, 2018-08-20 09:58:20, path c:\users\brucegist\onedrive - frothly\birthday pictures\..., action Cleaned by deletion/Quarantined, SHA2 7A13...A405, 5732 bytes.
- get_sourcetype_fields symantec:ep:behavior:file -> only Splunk forwarder script blocks (splunkd.exe, getendpointinfo.exe, cmd.exe); noise.
- run_splunk_search symantec:ep:security:file | stats count by signature,file_name,user -> 4 rows, JSCoinminer web-attack signatures on CHROME.EXE/MICROSOFTEDGECP.EXE (BillyTun) only.
- run_splunk_search symantec:ep:agent:file / :packet:file / :traffic:file / :scm_system:file -> 0 events each.

### What it means
The only detection of malicious content that names a file anywhere in the Symantec telemetry is "Bruce Birthday Happy Hour Pics.lnk" (Backdoor.PsEmpire, quarantined on BGIST-L, Aug 20). Its OneDrive "birthday pictures" path, lure-style name, Empire signature and late-campaign date all fit an emailed .lnk from a post-foothold phishing wave. What I could NOT verify within the tool budget: the second phishing wave itself in the email feeds (o365:management:activity, ms:o365:reporting:messagetrace, stream:smtp) and any Sysmon record of the file's arrival. The candidate is submitted as partial for that reason.

## Ruled out
- symantec:ep:security:file JSCoinminer detections - browser-process web attacks (coinminer storyline), no phishing file artifact.
- symantec:ep:behavior:file - application-control blocks on Splunk forwarder scripts; administrative noise.
- symantec:ep:agent:file, :packet:file, :traffic:file, :scm_system:file - 0 events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
