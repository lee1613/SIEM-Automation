# s1 - Q307 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=9_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | source=WinEventLog:Microsoft-Windows-Sysmon/Operational | fields=EventCode, Image, CommandLine, Hashes, TargetFilename, ParentImage, DestinationIp, host
**Insight:** FOUND
**Candidate:** 586EF56F4D8963DD546163AC31C865D7   **Confidence:** 90

## Prior rounds
- R1: Sysmon on FYODOR-L — EventCode=1 (77 command lines) and EventCode=11 (18 files) found two dropped executables: C:\Windows\Temp\hdoor.exe and unziped\lsof-master\iexeplorer.exe; hdoor.exe ran once with an IP-range sweep and MD5=586EF56F4D8963DD546163AC31C865D7; stream:http had no download record; submitted as FOUND at 82.

## This round
### What I ran
- EventCode=11 host=FYODOR-L | stats count by TargetFilename -> 18 files (control re-run, identical to R1): hdoor.exe and iexeplorer.exe both present.
- EventCode=11 | stats values(Image), values(ProcessId) by TargetFilename (post-aggregation filter) -> both files created by the SAME powershell.exe PID 6360: hdoor.exe at epoch 1534761769 (18:42:49+08:00), iexeplorer.exe at 1534762061 (18:47:41).
- EventCode=1 Image=hdoor.exe, full record -> 1 event: 18:43:10+08:00, `"C:\windows\temp\hdoor.exe" -hbs 192.168.9.1-192.168.9.50 /b /m /n`, Hashes=MD5=586EF56F4D8963DD546163AC31C865D7,SHA256=99925199059EE049F7AEDA8904C2F5BDFBA86671FD7A5989BD60B72F26EF737C, parent powershell.exe (encoded downloader), ProcessGuid={EBF7A186-CCB6-5B58-0000-00109D240102}, PID 10260, user AzureAD\FyodorMalteskesko.
- EventCode=1 Image=iexeplorer.exe | rex target | stats -> 34 runs, dc(target)=1, target=192.168.9.30:8080 only, 19:05:40–19:34:01.
- EventCode=3 ProcessGuid={EBF7A186-CCB6-5B58-0000-00109D240102} -> 19 connections to 6 distinct DestinationIp, 1534761811–1534761845 (the 34s after launch).

### What it means
The selection is settled by execution behavior, not provenance (both files came from the same powershell.exe PID 6360). hdoor.exe's single execution sweeps 192.168.9.1–192.168.9.50 and its own process GUID generated 19 connections to 6 distinct IPs immediately after — the act of scanning Frothly's network. iexeplorer.exe ran 34 times against exactly one host with shell commands — exploitation, not scanning. The selected file's execution record carries Hashes=MD5=586EF56F4D8963DD546163AC31C865D7, unchanged from round 1. The download linkage rests on the on-endpoint file-creation by the encoded PowerShell downloader (no stream:http record exists for hdoor).

## Ruled out
- iexeplorer.exe (MD5=655D76930C77B713864CD26E386F1DE7) - 34 executions, 1 distinct target (192.168.9.30:8080), post-exploitation commands; never an IP-range sweep.
- stream:http as download evidence - 0 events for "hdoor" (R1).
- Direct TargetFilename exact-match filtering on EventCode=11 - returns 0 rows despite the value existing (backslash-escaping quirk); use stats-by-TargetFilename with post-aggregation search instead.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "hdoor.exe's process (ProcessGuid {EBF7A186-CCB6-5B58-0000-00109D240102}) generat"
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
