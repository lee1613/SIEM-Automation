# s3 - Q329 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** sourcetypes=stream:http, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinHostMon (also stream:smb, stream:smtp as content routes); fields=uri, http_method, status, TargetFilename, Image, Details, CommandLine.
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 5

## Prior rounds
- R1: Sysmon located both files on MKRAEUS-L — PDF downloaded via Chrome (hash captured), PPTX named in one unread registry event; no content reached.
- R2 (this round): read the PPTX registry event (opened from SharePoint in PowerPoint); swept all content-bearing network feeds — empty; enumerated every FileCreate under Mallory's profile — no derivative artifacts.

## This round
### What I ran
- get_raw_events "frothly_gabf_deck" (Sysmon) -> 1 event read: POWERPNT.EXE PID 4776 wrote TrustRecords for https://frothly-my.sharepoint.com/personal/mkraeusen_froth_ly/Documents/Frothly_GABF_Deck-2018-MK.pptx at 09:58:44 UTC.
- stream:http "frothly_gabf_deck" / "ba_advertising_code_overview.pdf" / "*.pptx" / "*.pdf" -> 0 events each.
- stream:smb and stream:smtp for both filenames -> 0 events each.
- Sysmon host=MKRAEUS-L EventCode=11 TargetFilename="*MalloryKraeusen*" -> 6 rows, all read: PDF + Zone.Identifier, two Chrome .tmp downloads (10:30:56, 11:16:31, chrome.exe PID 10928), two Edge .lnk partials.
- get_raw_events on both .tmp files -> read: both created by chrome.exe PID 10928 (Chrome temp-download naming; no evidence they are the documents).

### What it means
NOT_FOUND: the PPTX was opened straight from SharePoint and never written to local disk; the PDF exists only as a hash in a FileCreate event. No network feed carries either file's bytes, and Mallory's profile contains no unpacked/derivative artifact. The oversized-font word lives in file content that no tested source exposes.

## Assumptions
- Coverage: content could appear via (a) stream:http bodies — searched both filenames plus any *.pdf/*.pptx, 0 events; (b) stream:smb — searched, 0; (c) stream:smtp — searched, 0; (d) Sysmon local file/registry events — searched exhaustively (6 FileCreate rows, all read), only hash + SharePoint URL; (e) osquery:results, aws:s3:accesslogs, o365:management:activity — NOT SEARCHED (outside this round's scope) - UNVERIFIED.
- Selection: MKRAEUS-L is the only host with Sysmon events for either filename (both filename queries returned MKRAEUS-L only) - VERIFIED.
- Premise: the PPTX was handled locally on MKRAEUS-L — DISPROVEN: it was opened from a SharePoint URL, never saved locally.
- Premise: the oversized word is recoverable from telemetry — UNVERIFIED: no content-bearing artifact found in any tested feed.

## Ruled out
- stream:http — no events for either filename, nor for any .pdf/.pptx at all.
- stream:smb, stream:smtp — no events for either filename.
- WinHostMon process — no command lines naming either file (R1).
- Local PPTX copy on MKRAEUS-L — never written to disk (only a Trusted Documents registry write for the SharePoint URL).
- Chrome .tmp files in Downloads — created by chrome.exe as ordinary temp downloads; no link shown to either document.

## Open questions for SH
- Should next round widen to osquery:results, aws:s3:accesslogs, and o365:management:activity for these filenames/hashes (the upload path and any SharePoint preview), or to Sysmon on other hosts where Taedonggang may have staged the upload?
- Is there a known artifact in the case holding the actual file bytes (e.g., an S3 object body or email attachment) that a prior round identified?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
