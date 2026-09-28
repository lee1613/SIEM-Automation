# s3 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational (host MKRAEUS-L); WinHostMon source=process; whole-index keyword manifest.
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
- (Round 1 — this round; no prior rounds.)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; endpoint family includes WinHostMon, XmlWinEventLog:...Sysmon/Operational, osquery:results, PerfmonMk:Process, Script:GetEndpointInfo.
- search_keyword "ba_advertising" / "frothly_gabf_deck" -> 0 field-name matches (manifest only).
- WinHostMon source=process "ba_advertising*" and "frothly_gabf_deck*" -> 0 events.
- Sysmon "ba_advertising_code_overview.pdf" -> MKRAEUS-L, EventCode 11 (x2) + 15 (x6).
- get_raw_events on that keyword -> 8 events, all read: Chrome PID 10928 created C:\Users\MalloryKraeusen\Downloads\BA_Advertising_Code_Overview.pdf at 2018-08-20 10:31:02 UTC (+ Zone.Identifier stream); SHA256 2F08B321B72BA37481EBBF6B37882F032B8D32864020ED579E7574048B1C0023.
- Sysmon "frothly_gabf_deck" -> MKRAEUS-L, EventCode 13 (RegistryEventSetValue), 1 event — raw NOT read (cap hit).

### What it means
NOT_FOUND: I confirmed both files exist as local artifacts on MKRAEUS-L (the PDF downloaded via Chrome; the PPTX named in one registry-write event), but I never reached the files' CONTENT, which is where the oversized-font word lives. No candidate word exists yet.

## Assumptions
- Coverage: the question's concept (a word rendered in a much larger font inside one uploaded file) can show up as (a) Sysmon file events naming the files — searched, found both files' local handling but no content; (b) WinHostMon process command lines — searched, 0 events; (c) stream:http transfer bodies carrying the file bytes — NOT YET SEARCHED (UNVERIFIED); (d) osquery:results file/hash rows — NOT YET SEARCHED (UNVERIFIED); (e) pptx XML run-properties (sz=) inside any captured body — NOT YET SEARCHED (UNVERIFIED).
- Selection: MKRAEUS-L is the only host with Sysmon events for either filename (both queries returned MKRAEUS-L only) — VERIFIED.
- Premise: "uploaded by Taedonggang" files are these two Mallory documents — taken from SH's framing; the PDF's Chrome download on Mallory's host is consistent — VERIFIED as local artifact, but the upload act itself was not re-verified this round.
- Premise: the larger-font word is recoverable from telemetry, most plausibly the pptx XML in a captured HTTP body or a derivative dump — UNVERIFIED, not yet searched.

## Ruled out
- WinHostMon source=process — no command line references either filename.
- Keyword-manifest search — no field names carry these filenames.

## Open questions for SH
- Is the intended source for the file CONTENT the network capture (stream:http) of the upload/download, or an endpoint derivative (osquery file rows / registry MRU)? If a prior round already located the pptx bytes, that finding would let me go straight to the sz= run-property.
- Should scope include hosts other than MKRAEUS-L for the pptx (e.g., where Taedonggang staged the upload), given only one registry event names it locally?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
