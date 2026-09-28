# s2 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=1_
**Scope:** sourcetype=code42:api, code42:computer, code42:org, code42:security, code42:user | source=code42://frothly_code42_input | fields=files{}.fileName, files{}.fileEventType, files{}.fullPath, files{}.md5, processOwner, userUid
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 60

## Prior rounds
- None — first round on this scope.

## This round
### What I ran
- get_source_types -> 5 Code42 sourcetypes, all under source=code42://frothly_code42_input: api(88), computer(51), org(17), security(30), user(192).
- search_keyword "taedonggang" -> 0; search_keyword "code42" -> 0. The second null proves the tool blind (Code42 data exists), so neither result is evidence of absence.
- get_sourcetype_fields code42:security -> carries files{}.fileName/fullPath/md5/length/mimeType, files{}.fileEventType (DOWNLOAD/UPLOAD/SCAN), processOwner, userUid; eventTypes FILE_OPENED(17), PERSONAL_CLOUD_SCAN_RESULT(7), DEVICE_APPEARED(5); ruleName com.code42.rules.AWSPEMKeyMatch(1). No content-bearing field anywhere.
- `index=botsv3 sourcetype=code42:security | stats count by files{}.fileName files{}.fileEventType processOwner userUid` -> 18 rows, read in full (meta 18 of 18).

### What it means
Code42:security records file metadata only — name, path, md5, size, mime — never file content, so the much-larger-font word is not recoverable from this feed. What it does give is the upload set. UPLOAD events name two actors: MalloryKraeusen (userUid 858501800121238378) uploaded ba_advertising_code_overview.pdf, edb00006.log, edb00007.log, frothly_gabf_deck-2018-mk.pptx, schema.txt, spartan.edb, spartan.pat; BudStoll (858527737266971219) uploaded frothly_html_memcached.tar.gz (10 events, path c:\users\budstoll\downloads\, md5 218dd64994af34fdd8a96d99529ee30f, 3076532 bytes). All events 2018-08-20. Document-type candidates for a font-size anomaly: ba_advertising_code_overview.pdf and frothly_gabf_deck-2018-mk.pptx (schema.txt and the .log/.edb/.pat files unlikely but not excluded). Handoff: next scope must read file content from a content-bearing feed.

## Assumptions
- Coverage: code42:security searched for upload events and filenames — VERIFIED (18-row stats, read in full). code42:api, code42:user, code42:computer, code42:org NOT yet searched for a Taedonggang identity/username/email — UNVERIFIED (tool budget exhausted this round).
- Selection: which actor is Taedonggang is unresolved. Only two processOwners exist in code42:security. MalloryKraeusen is the BOTSv3 insider/attacker and so the likely mapping, but no Code42 record read this round ties the string "taedonggang" to either userUid — UNVERIFIED.
- "Uploaded" = files{}.fileEventType=UPLOAD — VERIFIED (UPLOAD values present in the 18-row result).
- Premise that the word requires file content, absent from Code42 — VERIFIED via fieldsummary (no content fields in code42:security).

## Ruled out
- code42:security as the source of the word itself — metadata-only feed.
- search_keyword nulls as evidence of absence — tool returned 0 for "code42", which demonstrably exists.
- BudStoll's upload set as the answer set — his only upload is a tar.gz archive; its sibling frothly_html_memcached.txt appears as DOWNLOAD only (18 events).

## Open questions for SH
- Is Taedonggang = MalloryKraeusen (userUid 858501800121238378)? code42:user (192 events) likely resolves userUids to usernames/emails — confirm, or should the next round check it?
- Which scope should read file content next: stream:http bodies, o365:management:activity email attachments, or endpoint file-creation telemetry for ba_advertising_code_overview.pdf / frothly_gabf_deck-2018-mk.pptx?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
