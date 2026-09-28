# s1 - Q326 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** sourcetype=stream:http, stream:dns, stream:smtp, o365:management:activity | fields: site, uri_path, uri_host, host, query, src_ip, content, Subject, ObjectId, SourceFileName, UserId
**Insight:** NOT_FOUND — no literal slogan read; candidate remains hypothesis
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1: identified Mallory Kraeusen <mkraeusen@froth.ly>; 33 SMTP events (tradeshow/brewertalk threads, bodies clipped); OneDrive upload of Frothly_GABF_Deck-2018-MK.pptx; "advertis" -> 0 in SMTP; o365 feed is metadata-only.
- Round 2 (this round): mapped Mallory's workstation and full web/DNS footprint; no advertising-research text read; tools withdrawn before content extraction.

## This round
### What I ran
- `stream:dns "mkraeus" | stats count by query` -> MKRAEUS-L (33), MKRAEUS-L.local (78).
- `stream:dns "MKRAEUS-L" | stats count by src_ip` -> 192.168.247.129 (102).
- `stream:http src_ip=192.168.247.129` -> 0 events; `stream:http "MKRAEUS"` -> 0 (attribution is by host=, not src_ip).
- `stream:http | stats count by host` -> 16 hosts, incl. MKRAEUS-L with 168 events.
- `stream:http host=MKRAEUS-L | stats count by site, uri_path` -> 71 rows, 50 read: brewertalk.com (forumdisplay.php, showthread.php, css/images), ipinfo.io/json, Splunk login 192.168.9.25:8000, weather/OCSP/CDN.
- `stream:dns src_ip=192.168.247.129 | stats count by query` -> 808 rows, top 50 read: google/play/drive, googleads.g.doubleclick.net, office365/sharepoint, brewertalk — no ad-research domain.

### What it means
Mallory's identity, host (MKRAEUS-L, 192.168.247.129) and browsing are fully mapped, but every query this round returned URL/path aggregates only — no HTTP response body, SMTP body, or document text containing "how beer is meant to be enjoyed" was ever read. The one-word phrase therefore cannot be stated from evidence; per SH's guidance the hypothesis "responsibly" is not submitted.

## Ruled out
- stream:dns as content carrier — domain names only, nothing ad-research-specific in her 808 lookups (top 50 read).
- stream:http URL/path level — her 168 events are brewertalk forum pages, ipinfo.io, Splunk login, weather/OCSP/CDN; no ad-research site.
- o365:management:activity — metadata only (Round 1).
- stream:smtp keyword "advertis" — 0 events (Round 1).

## Next (not run — tools withdrawn)
- Read brewertalk.com showthread.php/forumdisplay.php response BODIES from host=MKRAEUS-L (get_raw_events / rex on stream:http content).
- Rex-extract the 33 Mallory SMTP bodies past the 1500-char clip for "enjoy".

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:dns src_ip=192.168.247.129 | stats count by query | sort -c…` (50 of 808 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:http host=MKRAEUS-L | stats count by site, uri_path | sort …` (50 of 71 rows seen). A claim resting on them alone is UNVERIFIED._
