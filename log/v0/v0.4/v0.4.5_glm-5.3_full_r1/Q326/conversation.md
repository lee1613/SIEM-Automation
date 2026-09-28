# Q326 — SH <-> Senior conversation

### 02:10:34 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:http', 'stream:smtp', 'ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:o365:management'] sources=- fields=['_raw', 'uri', 'uri_path', 'url', 'http_user_agent', 'form_data', 'SenderAddress', 'RecipientAddress', 'Subject', 'content', 'content_body', 'attach_filename', 'UserId', 'ObjectId', 'Operation']
**Technique:** senior
**Reason:** A quoted one-word slogan or conclusion is most likely preserved in email bodies/attachments or web/request content rather than generic host inventory. These sources can carry both Mallory-attributed messages and any browsed or shared advertising-research text.

Identify who Mallory is in the data, locate the advertising research artifact or communication attributable to Mallory, and determine the one-word answer to the question 'how is beer meant to be enjoyed?' from that literal content.

### 02:12:52 - s1 -> SH   [REPORT - round 1 - FOUND]
> Mallory = Mallory Kraeusen <mkraeusen@froth.ly>, Frothly marketing employee; 33 stream:smtp events name her (tradeshow and brewertalk threads). Her OneDrive activity on 2018-08-20 shows the marketing artifact Frothly_GABF_Deck-2018-MK.pptx (GABF = Great American Beer Festival advertising deck) uploa
_full: reports/s1_round_1.md_

### 02:13:01 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Mallory is identified in data as mkraeusen@froth.ly, and her OneDrive metadata points to a likely marketing artifact, Frothly_GABF_Deck-2018-MK.pptx. But no literal research text or slogan was read from this round.
[q2] What will settle the question is a content-bearing artifact tied to Mallory: her browsing/web content, readable SMTP body text, or another artifact that literally states how beer is meant to be enjoyed. The current candidate 'responsibly' is only a hypothesis and cannot be submitted.

**retry** — The scope is close but the round stopped at metadata and a memory-based guess. This question demands a literal one-word value from Mallory-attributed research content, so the next round must pivot to content-bearing artifacts.
**New scope:** sourcetypes=['stream:http', 'stream:dns', 'stream:smtp', 'o365:management:activity'] sources=['stream:http', 'stream:dns', 'stream:smtp'] fields=['uri_host', 'uri_path', 'url', 'http_user_agent', 'query', 'content', '_raw', 'Subject', 'ObjectId', 'SourceFileName', 'UserId']

Find a Mallory-attributed content source that can literally state the advertising-research conclusion. Prioritize stream:http and stream:dns activity attributable to MKRAEUS-L or mkraeusen@froth.ly for ad/marketing research, and also re-read Mallory-linked stream:smtp bodies or any content-bearing document/body artifact if accessible. Return the one-word phrase only if it appears literally in the evidence.

### 02:15:17 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> Mallory is fully identified: Mallory Kraeusen <mkraeusen@froth.ly>, workstation MKRAEUS-L at 192.168.247.129 (DNS PTR self-lookups confirm). Her web footprint (168 stream:http events, 71 site/path rows, 50 read) is brewertalk.com forum pages (forumdisplay.php, showthread.php), ipinfo.io/json, a Splu
_full: reports/s1_round_2.md_

### 02:15:25 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q3] Mallory’s endpoint is MKRAEUS-L with source IP 192.168.247.129 in the searched DNS/HTTP telemetry, but no literal slogan or research conclusion was read from this round.
[q4] What will settle the question is a content-bearing artifact tied to Mallory: readable HTTP response/body content for her brewertalk browsing, or another readable body/document artifact containing the phrase about how beer is meant to be enjoyed.

**retry** — The direction is still right on entity attribution, but this round only mapped Mallory’s host and browsing at the URL/domain level. The answer requires literal text from a content-bearing artifact, not more path or DNS aggregation.
**New scope:** sourcetypes=[] sources=[] fields=['content', 'content_type', 'uri_path', 'site', 'query', 'Subject', 'content_body', 'ObjectId', 'SourceFileName', 'host', 'src_ip']

On MKRAEUS-L, read content-bearing artifacts rather than aggregates. Prioritize readable stream:http events for her brewertalk/forum browsing to see whether response content or request parameters contain the advertising-research phrase, and also inspect any accessible SMTP or document-linked text tied to Mallory for the literal wording 'how beer is meant to be enjoyed.' Return the one-word value only if it appears literally in the evidence.

### 02:17:20 - s1 -> SH   [REPORT - round 3 - NOT_FOUND]
> NO LITERAL EVIDENCE FOUND; value left empty per SH's instruction that a hypothesis cannot be submitted. Eliminations are strong because Splunk keyword search matches the FULL _raw of every event, including the portions get_raw_events clips at 1500 chars: (a) "meant to be enjoyed" -> 0 in stream:smtp
_full: reports/s1_round_3.md_

### 02:17:27 - runner   [NOTE]
RECALL Q217 summary

### 02:17:33 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q5] The searched stream:smtp and stream:http content do not contain the literal phrase or the candidate 'responsibly'; the only 'enjoy' hit belongs to Billy Tun, not Mallory.
[q6] What should settle the question is a Mallory-linked content artifact that can actually be read, most likely a document/attachment or another readable content source rather than SMTP/HTTP keywording.

**retry** — The current direction established the right person and workstation, but the searched content feeds did not contain the wording and the first hypothesis is now contradicted. The case needs a different content-bearing artifact tied to Mallory's research, not more blind searching of the same textless surfaces.
**New scope:** sourcetypes=['stream:smtp', 'o365:management:activity', 'ms:o365:reporting:messagetrace'] sources=[] fields=['content', 'attach_filename', 'Subject', 'ObjectId', 'SourceFileName', 'UserId']

Find a Mallory-linked artifact whose content can be read directly. Prioritize the OneDrive/Office document path around Frothly_GABF_Deck-2018-MK.pptx and any attachment-bearing mail or image/document artifact tied to mkraeusen@froth.ly that could preserve advertising-research wording. Establish whether any accessible artifact literally states how beer is meant to be enjoyed, and return the one-word value only if it appears in that artifact.

### 02:19:22 - s1 -> SH   [REPORT - round 4 - NOT_FOUND]
> NO LITERAL EVIDENCE FOUND; value left empty per instruction not to invent one. Mallory is fully identified: Mallory Kraeusen <mkraeusen@froth.ly>, workstation MKRAEUS-L at 192.168.247.129, marketing role (GABF deck, tradeshow planning, conference booth themes). EVERY Mallory-linked email thread has 
_full: reports/s1_round_4.md_

### 02:19:32 - SH -> s1   [RETIRE]
SH's answers to your open questions:
[q7] All Mallory-attributed communications searched so far are negative: her SMTP threads, MKRAEUS-L HTTP/DNS activity, messagetrace, and O365 upload metadata do not contain the slogan text.
[q8] What should settle it next is a different content-bearing artifact tied to Mallory’s research or deck content, not more re-reading of the same mail/web metadata. A fresh scope should target readable document, attachment, or adjacent content sources that could preserve the advertising phrase.

This senior exhausted the Mallory mail/web/O365-metadata path and repeatedly returned no literal slogan text. Another round in the same area would only repeat a dead scope.

### 02:19:32 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 02:19:32 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:http', 'stream:smtp', 'o365:management:activity', 'ms:o365:reporting:messagetrace', 'access_combined', 'code42:api', 'code42:computer', 'code42:org', 'code42:user'] sources=- fields=['_raw', 'content', 'content_body', 'uri_path', 'uri', 'site', 'ObjectId', 'SourceFileName', 'UserId', 'Subject', 'attach_filename']
**Technique:** senior
**Reason:** A competing direction remains: the wording may live in a Mallory-linked document or adjacent shared-content artifact rather than in the communications and URL-level browsing already exhausted. A fresh senior is needed to pursue that different artifact path.

Independently determine how Mallory's advertising research states beer is meant to be enjoyed. Do not rebuild on the retired senior's keyword guesses. Instead, identify any Mallory-linked content-bearing artifact outside the exhausted SMTP/HTTP phrase-search path—such as a document/attachment, shared-content metadata that names a readable artifact, or another readable content source—and extract the literal one-word answer if it exists.

### 02:23:13 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> No literal text found this round; the artifact path is mapped but not yet read. What I established: (1) The GABF deck's full OneDrive path is https://frothly-my.sharepoint.com/personal/mkraeusen_froth_ly/Documents/Frothly_GABF_Deck-2018-MK.pptx (ListItemUniqueId 0e758dde-f8a6-4376-be5c-6956a9ca84cb,
_full: reports/s2_round_1.md_

### 02:23:22 - SH -> s2   [COMMAND]
SH's answers to your open questions:
[q9] The O365 deck artifact is now anchored precisely, but the searched O365 events carry only metadata and no readable document text. That feed alone cannot supply the one-word slogan.
[q10] The best next path is Mallory-linked host-side or adjacent content artifacts: code42, MKRAEUS-L endpoint telemetry, or any export/companion artifact around the deck that could preserve readable text, because SMTP and O365 metadata have both failed as content sources.

**retry** — This round usefully narrowed the artifact path by proving the searched O365 deck events are metadata-only and that direct mkraeusen SMTP hits do not exist. The question still requires literal content, so the next round must pivot to other content-bearing artifacts tied to MKRAEUS-L or the deck rather than repeat metadata searches.
**New scope:** sourcetypes=['code42:api', 'code42:computer', 'code42:security', 'WinHostMon', 'osquery:results', 'ess_content_importer'] sources=[] fields=['_raw', 'host', 'email', 'username', 'content', 'notes', 'file_name', 'device_name', 'text']

Search for a Mallory-linked content-bearing artifact outside the exhausted O365 metadata and direct mkraeusen SMTP path. Prioritize code42:computer/code42:api/code42:security, MKRAEUS-L endpoint telemetry, and any companion/export artifact tied to the Frothly_GABF_Deck-2018-MK.pptx object that could preserve readable text or a preview. Determine whether any of those artifacts literally state how beer is meant to be enjoyed, and return the one-word value only if it appears in the evidence.

### 02:26:52 - s2 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s2_round_2.md_

### 02:26:58 - SH -> s2   [CRITIC]
**Basis:** conflicts_case_file
**Flaw:** The report proposes using external knowledge to corroborate a PDF's meaning, but this investigation must answer from dataset evidence only. It also introduces `ba_advertising_code_overview.pdf` without showing the dataset result that produced it, so the new lead is not yet usable.
**Why it fails:** The question asks what Mallory's advertising research says, and the case rules forbid external corroboration. A file name can be real and still unusable until the dataset evidence locating it and tying it to Mallory is shown.

First establish, from dataset output only, where `ba_advertising_code_overview.pdf` appears and how it is linked to Mallory or MKRAEUS-L. Then read whatever in-dataset artifact around that file is actually accessible — filename list, path, adjacent email/document metadata, or body text — to determine whether the one-word answer appears literally there. If the file content itself is not readable in the dataset, say exactly that and what artifact names it.

### 02:31:42 - s2 -> SH   [REPORT - round 3 - NOT_FOUND]
> DATASET-ONLY RESULT, per the critic's ruling: no web_lookup was ever executed (I was cut off before it ran), so nothing external entered this round. WHAT IS NOW ESTABLISHED FROM DATASET OUTPUT: (1) Mallory's advertising research artifact is ba_advertising_code_overview.pdf — anchored by 4 code42:sec
_full: reports/s2_round_3.md_

### 02:31:50 - SH -> s2   [COMMAND]
SH's answers to your open questions:
[q11] The dataset now anchors Mallory’s advertising research artifact directly: `ba_advertising_code_overview.pdf` in code42:security under processOwner MalloryKraeusen. That is the strongest Mallory-linked content artifact found so far.
[q12] What remains missing is readable content from that PDF or another artifact that quotes its wording. The current feeds show only metadata, so they cannot supply the one-word answer literally.

**continue** — This round materially advanced the case by replacing a guess with a named Mallory-linked research artifact in dataset evidence. The remaining gap is narrow: prove whether any searched-accessible artifact can render or quote that PDF’s text, or else establish that the value is not answerable from accessible data.
**New scope:** sourcetypes=['code42:security', 'stream:smtp', 'stream:http', 'o365:management:activity', 'ms:o365:reporting:messagetrace', 'WinHostMon', 'osquery:results', 'ess_content_importer'] sources=[] fields=['_raw', 'content', 'fileName', 'fullPath', 'md5', 'mimeType', 'ObjectId', 'SourceFileName', 'Subject', 'uri_path', 'Message', 'columns.path']

Use the established artifact `ba_advertising_code_overview.pdf` as the anchor and test only dataset-accessible paths that could still expose its text or a quoted phrase from it. Check whether any mail, web, endpoint, or file-related artifact in scope contains the PDF name together with snippet text, extracted content, preview text, or quoted wording about how beer is meant to be enjoyed. If none does, establish from exact output that the dataset carries only metadata for this PDF and that the one-word answer is not readable from accessible artifacts.

### 02:33:49 - s2 -> SH   [REPORT - round 4 - NOT_FOUND]
> 
_full: reports/s2_round_4.md_

### 02:33:54 - SH -> s2   [CLARIFY]
**unclear**
1. From what you already hold, is ba_advertising_code_overview.pdf the only Mallory-linked advertising-research artifact named in dataset output, or is there any second named research artifact still live?
2. From what you already hold, does any searched feed expose readable text, preview text, or quoted wording from ba_advertising_code_overview.pdf itself, or only metadata such as fileName, fullPath, md5, length, mimeType, and transfer times?
3. Given only the evidence you already hold, do you judge this question answerable from accessible dataset artifacts, or does the one-word value exist only inside the unread PDF content?

### 02:34:13 - s2 -> SH   [CLARIFY REPLY]
1. **The PDF is the only artifact explicitly named as advertising research, but a second Mallory-linked artifact is still live.** Dataset output names exactly two Mallory content artifacts: `ba_advertising_code_overview.pdf` (code42:security, processOwner MalloryKraeusen, downloaded then uploaded via Chrome) and `frothly_gabf_deck-2018-mk.pptx` (local copy in the same code42 event, md5 94c1f5ed3fb93455134c989887b0138a, 33,226 bytes; OneDrive copy uploaded 09:58:42Z). The GABF deck is her presentation — plausibly the *output* of the research — and its text is equally unread so far, so it remains a live second candidate, though the PDF is the one the dataset itself labels "advertising."

2. **Only metadata.** Every feed I searched exposes fileName, fullPath, md5, length, mimeType, fileEventType, and timestamps for the PDF — nothing more. code42:security has no text field; O365 has zero events for the PDF at all; stream:http on MKRAEUS-L shows no .pdf transaction in the Chrome session (the 10:31:16Z download was HTTPS, so no body is captured); WinHostMon, osquery:results, and ess_content_importer returned zero hits. No preview, snippet, or quoted wording from the PDF exists anywhere I

### 02:34:19 - SH -> s2   [COMMAND]
**continue** — The case now has a named research artifact and a clear statement of what searched surfaces do not expose. One round should close the remaining in-dataset content paths before deciding whether the value is unreadable.
**New scope:** sourcetypes=['ms:o365:reporting:messagetrace', 'stream:smtp', 'o365:management:activity', 'ms:o365:management', 'code42:security'] sources=[] fields=['Subject', 'SenderAddress', 'RecipientAddress', 'content', '_raw', 'Operation', 'ObjectId', 'SourceFileName', 'UserId', 'fileName', 'fullPath']

Use the remaining in-dataset content paths tied to Mallory's research. First, enumerate Mallory's messagetrace activity and any corresponding SMTP messages or nearby content for subject/body wording that could summarize the advertising research in one word. Second, broaden O365 activity around mkraeusen and the GABF deck to test whether any operation carries preview, sharing text, or quoted content. Third, if you still find no literal one-word phrase, state from complete results that the only named advertising artifact is ba_advertising_code_overview.pdf (with the deck as related output) and that searched dataset artifacts expose only metadata, not readable content.

### 02:36:39 - s2 -> SH   [REPORT - round 5 - NOT_FOUND]
> FINAL STATE, dataset-only per the critic's ruling: the one-word value never appeared in any query output I received, so I do not submit one. WHAT IS ESTABLISHED: (1) The only named advertising-research artifact is ba_advertising_code_overview.pdf — code42:security, processOwner MalloryKraeusen, Chro
_full: reports/s2_round_5.md_

### 02:36:45 - SH -> s2   [RETIRE]
SH's answers to your open questions:
[q13] No searched artifact literally states how beer is meant to be enjoyed. The only named advertising-research artifact is ba_advertising_code_overview.pdf, and all searched surfaces expose only metadata, not readable content.
[q14] What would settle it is a dataset artifact that renders or quotes the PDF/deck text. The searched mail, O365, HTTP, code42, and endpoint artifacts do not do that, so no evidence-backed one-word value can be submitted from the held record.

s2 has exhausted its rounds after testing the remaining in-dataset content paths. It established the named research artifact and the absence of readable text in the searched surfaces, but did not produce a literal answer value or a senior-quoted wall sufficient for a not-answerable submission.

### 02:36:45 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 02:36:45 - runner   [NOTE]
question ended: rounds — no ANSWER from SH; submitting 'SH retired without answering'

