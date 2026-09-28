# s2 - Q326 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** o365:management:activity, stream:smtp (source=stream:smtp), keyword index; fields Operation, Workload, ObjectId, UserId, attach_filename, content
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- (Round 1 — this is my first round; no prior rounds of mine. Retired senior's work carried forward: Mallory SMTP threads, MKRAEUS-L HTTP/DNS, messagetrace, O365 upload metadata all searched negative for literal text.)

## This round
### What I ran
- get_source_types -> 102 sourcetypes mapped; artifact-relevant candidates identified: o365:management:activity, code42:*, WinHostMon, osquery:results, aws:s3:accesslogs, ess_content_importer.
- index=botsv3 sourcetype=o365:management:activity "Frothly_GABF_Deck" | stats count by Operation, Workload -> 2 events.
- get_raw_events keyword=Frothly_GABF_Deck sourcetype=o365:management:activity -> full metadata for both events (upload + export-worker access), no content.
- search_keyword "advertising" -> 0 results.
- get_sources sourcetype=stream:smtp -> single source stream:smtp, 879 events.
- index=botsv3 sourcetype=stream:smtp mkraeusen -> 0 events.
- sample_events stream:smtp -> confirmed field structure (attach_filename, attach_type, content[]).

### What it means
NOT_FOUND: the only Mallory-linked artifact events in O365 are pure metadata — a FileUploaded by mkraeusen@froth.ly (2018-08-20 09:58:42Z, client 107.77.212.175) and a FileAccessed by app@sharepoint "ExportWorker"/"Protection Center" from Azure IP 104.209.132.239 (11:28:56Z). Neither carries document text, so the literal phrase is not in this feed. Mallory has zero events in stream:smtp, eliminating that feed for her entirely. The artifact path is now precisely mapped (full SharePoint ObjectId/ListItemUniqueId) but no readable content surface has been reached yet; the round ended at the tool cap before I could query code42, WinHostMon/osquery on MKRAEUS-L, or the DLP/ExportWorker companion events.

## Ruled out
- o365:management:activity for the deck filename - only 2 events, both metadata-only; no document content fields exist in them.
- stream:smtp for Mallory - 0 events match "mkraeusen"; her mail is not in this feed.
- Keyword "advertising" across the index - 0 results.

## Ruled out (feeds/hypotheses)
- stream:smtp as a Mallory content source - zero mkraeusen events.
- o365:management:activity deck events as content - metadata only (ObjectId, Site, UserAgent), no body/preview text.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
