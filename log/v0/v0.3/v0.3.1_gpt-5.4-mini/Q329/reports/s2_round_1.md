# s2 - Q329 - Round 1
_stamped by runner: rounds_remaining=6 novel_spl=2_
**Scope:** sourcetype=code42:security,access_combined | source=code42://frothly_code42_input,/var/log/httpd/access_log,/var/log/apache2/access.log | fields=files.fileName,files.fullPath,files.fileEventType,files.md5,processName,deviceRemoteAddress,uri,uri_path,referer,clientip,host
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
Code42 confirms frothly_html_memcached.tar.gz was downloaded to BudStoll's Downloads and uploaded from BudStoll's Desktop via chrome.exe.
Archive contents were not available in Code42 scope, so the oversized word still required downstream file/render telemetry.
access_combined fields were mapped, but no confirmed search hit tied the archive name or extracted HTML to web access.
HTTP telemetry exists under /var/log/httpd/access_log and /var/log/apache2/access.log, but the needed content-bearing artifact was not identified.
I did not find a safe candidate word; reporting partial rather than inventing an answer.

## This round
### What I ran
- `get_source_types()` -> confirmed BOTSv3 has access_combined, code42:security, stream:http, and other feeds.
- `get_sources(keyword="frothly_html_memcached")` -> surfaced `code42://frothly_code42_input` plus relevant web sources.
- `sample_events(source="code42://frothly_code42_input", keyword="frothly_html_memcached", count=3)` -> showed the archive was downloaded and uploaded by BudStoll; no file contents.
- `get_sourcetype_fields(sourcetype="access_combined")` -> mapped HTTP fields like uri, uri_path, file, referer, clientip, host.
- `run_splunk_search(...)` was attempted but exact archive-token search returned 0 results; subsequent search capacity was withdrawn before a stronger pivot.
### What it means
The archive is confirmed, but the oversized word cannot be derived from the evidence reached in this round. The task needs either archive-extraction telemetry or a page-render / file-access trail beyond the current scope.

## Ruled out
- access_combined as the direct answer source - no confirmed archive-name hit or extracted-file hit found.
- Code42 alone - it identifies transfer of the tar.gz, not the internal HTML/content.

## Open questions for SH
- If the intended answer is from downstream browser or file-render telemetry, which host or user should I prioritize next?
- If there is a known extracted filename or web path from the archive, that would narrow the next search.

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
