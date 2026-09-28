# s2 - Q217 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=stream:http,stream:tcp,XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | source=none | fields=host,src,dest,url,uri,http_user_agent,file_name,process_name,Image,CommandLine,User
**Insight:** NOT_FOUND
**Candidate:** BTUN-L   **Confidence:** 58

## Prior rounds
- Confirmed Windows/Sysmon and osquery endpoint telemetry exist in BOTSv3.
- Established BudStoll on BSTOLL-L as a prior recipient-side lead, but attachment evidence was not recovered there.
- Narrowed to browser/network telemetry for the Craft Brewer Conference thread.
- Identified BSTOLL-L and BTUN-L as employee hosts with Brewertalk traffic.
- No attachment filename/content or visualization type has yet been verified.

## This round
### What I ran
- `index=botsv3 sourcetype="stream:http" host=BSTOLL-L ...` -> multiple Brewertalk requests, but no attachment filename or file context.
- `index=botsv3 sourcetype="stream:http" site="www.brewertalk.com" ...` -> BTUN-L had the strongest thread activity among employee hosts.
- `index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BTUN-L (Image="*chrome.exe" OR ... ) | stats ...` -> 4 process-creation hits for AzureAD\BillyTun (Chrome, Outlook, Excel).
### What it means
BTUN-L is the best-validated employee endpoint for viewing the Brewertalk thread, but I still do not have proof of the first attachment being downloaded/opened/saved or the visualization type shown in it.

## Ruled out
- BSTOLL-L as the primary web-thread endpoint in this round - it had Brewertalk traffic, but BTUN-L was stronger for the thread scope.
- Sysmon alone for attachment recovery - only process launches were recovered on BTUN-L.

## Open questions for SH
- None I can answer without more telemetry queries; the attachment artifact itself is still missing.

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
