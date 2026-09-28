# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=3_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational,WinEventLog,osquery:results,stream:http | source=none | fields=host,User,Image,CommandLine,TargetFilename,process_name,path,url,uri,file_name
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
- Confirmed Windows/Sysmon endpoint telemetry exists in BOTSv3 and is queryable.
- Established BudStoll on BSTOLL-L as the strongest recipient-side endpoint lead from Sysmon process creation.
- The initial Sysmon EventCode=11 file-create angle on BSTOLL-L was unproductive.
- No attachment filename or content has yet been recovered from endpoint telemetry.
- FYODOR-L malicious activity was identified as unrelated to Bud's attachment handling.

## This round
### What I ran
- `index=botsv3 sourcetype="osquery:results"` fieldsummary -> showed host-level Linux/mac telemetry and columns.path coverage, but not a direct Bud attachment hit.
- `index=botsv3 sourcetype="osquery:results" host=BSTOLL-L (columns.path=download* OR columns.path=Downloads* OR columns.path=Document* OR columns.path=Chrome* OR columns.path=Office*) | stats ...` -> 0 results.
- `index=botsv3 sourcetype IN (...) "Craft Brewer Conference" | stats ...` -> 0 results.
### What it means
The scoped endpoint telemetry still does not expose the attachment chain or the visualization type. The searches did not validate a saved/opened file on BSTOLL-L, but they also did not eliminate BSTOLL-L as the likely recipient endpoint.

## Ruled out
- Generic thread-text search in host telemetry - no direct evidence.
- BSTOLL-L osquery path/download/Office-style filters in the attempted form - no results.
- FYODOR-L - unrelated to the Bud email attachment chain.

## Open questions for SH
- Which endpoint artifact family should I prioritize next on BSTOLL-L: browser history, downloads, or document execution/opening artifacts?
- Is there another Frothly employee host associated with the Bud thread besides BSTOLL-L?