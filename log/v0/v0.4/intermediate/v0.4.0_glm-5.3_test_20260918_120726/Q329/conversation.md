# Q329 — SH <-> Senior conversation

### 12:33:39 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:http', 'o365:management:activity', 'aws:s3:accesslogs', 'access_combined', 'osquery:results'] sources=- fields=['user', 'src', 'dest', 'uri', 'uri_path', 'http_method', 'form_data', 'object', 'file', 'path', '_raw']
**Technique:** content
**Reason:** This question depends on locating Taedonggang’s upload activity and then examining content-bearing artifacts that may preserve or point to document contents and formatting.

Identify files uploaded by Taedonggang in index=botsv3, determine which uploaded file contains a word displayed in a much larger font than the rest of the file, and report that word exactly.

### 12:37:02 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> No candidate value yet — the round was spent locating the upload feed, and the literal string "Taedonggang" appears nowhere in the feeds I checked. KEY LEAD for next round: o365:management:activity contains exactly 7 FileUploaded + 1 FileSyncUploadedFull events. Next queries should be: (1) index=bot
_full: reports/s1_round_1.md_

### 12:37:08 - SH -> s1   [COMMAND]
**continue** — The case now knows O365 upload activity exists, but the question is about a specific uploaded file and a word inside it. We need the upload population opened and attributed to the Taedonggang persona, then the candidate file must be traced into a content-bearing artifact.
**New scope:** sourcetypes=['o365:management:activity'] sources=[] fields=['Operation', 'UserId', 'SourceFileName', 'SiteUrl', 'ObjectId', 'SourceRelativeUrl', 'ClientIP', 'Workload']

Within sourcetype o365:management:activity, enumerate the FileUploaded and FileSyncUploadedFull events and establish, for each, the uploader identity, site or object path, and source filename. Determine which uploader or site maps to the Taedonggang persona even if the literal string Taedonggang is absent, then identify the specific uploaded file that must be examined for oversized text. If O365 only gives metadata, name the exact file and storage path or service needed next so we can recover its contents.

### 12:43:10 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> TAEDONGGANG PERSONA IDENTIFIED: bgist@froth.ly account operated via NaenaraBrowser/3.5b4 (ko-KP locale, North Korean Red Star OS) from IPs 104.207.83.63, 23.101.160.30, 157.97.121.5. TAEDONGGANG'S UPLOADED FILES (4, to https://frothly-my.sharepoint.com/personal/bgist_froth_ly/Documents/Birthday Pict
_full: reports/s1_round_2.md_

### 12:43:17 - SH -> s1   [RETIRE]
s1 completed the O365 metadata work: it identified the Taedonggang persona as bgist@froth.ly, enumerated the four uploaded files, and established that O365 contains no file content or rendering clues. Further progress now requires a different artifact class, so this senior should hand off rather than continue in a metadata-only scope.

### 12:43:17 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 12:43:17 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:http', 'aws:s3:accesslogs', 'code42:security', 'stream:smtp', 'access_combined'] sources=- fields=['uri_path', 'form_data', 'http_content_length', 'status', 'site', 'url', 'object', 'key', 'filename', 'attachment', 'subject', 'src_ip', 'dest_ip']
**Technique:** content
**Reason:** s1's scope is confined to o365:management:activity metadata and cannot recover uploaded file bytes or rendered content. A new senior is required to inspect content-bearing network, storage, or mail artifacts that may contain the uploaded files or their delivery path.

Recover the content of the files uploaded by the Taedonggang persona (bgist@froth.ly using NaenaraBrowser) — specifically morebeer.jpg, stout-2.jpg, stout.png, and any linked retrieval path associated with BRUCE BIRTHDAY HAPPY HOUR PICS.lnk — and determine which uploaded file contains a word rendered in a much larger font size than the rest of the file. Report that word exactly.

### 12:46:40 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> Established: the four artifacts live in OneDrive folder Documents/Birthday Pictures under bgist@froth.ly (morebeer.jpg ListItemUniqueId=376718d6-8add-427f-96ef-06cce8a1565c; stout.png=be00759e-1d6c-413f-83c9-d6763812edb0; BRUCE BIRTHDAY HAPPY HOUR PICS.lnk=0aa10299-8655-4f7e-b293-965cc699f48a). The 
_full: reports/s2_round_1.md_

### 12:46:46 - SH -> s2   [COMMAND]
**retry** — The case no longer needs more confirmation that O365 is metadata-only or that simple filename hits are absent in HTTP/SMTP. We need evidence sources that can retain the downloaded file bytes or reconstructed content from the recipient endpoints.
**New scope:** sourcetypes=['symantec:ep:packet:file', 'symantec:ep:behavior:file', 'symantec:ep:risk:file', 'symantec:ep:traffic:file', 'code42:api', 'code42:security', 'WinEventLog'] sources=[] fields=['file', 'path', 'filename', 'computer_name', 'user', 'destination', 'application', 'risk_name', 'ObjectId', 'SourceFileName']

Establish whether the Taedonggang-uploaded files downloaded to MKRAEUS-L or BSTOLL-L are recoverable from endpoint-side content-bearing evidence. Prioritize Symantec packet/file/behavior artifacts and Code42 endpoint-backup evidence for the known files BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, morebeer.jpg, stout-2.jpg, and stout.png, and determine which one contains rendered text with one word much larger than the rest. Then report that word exactly.

### 12:51:05 - s2 -> SH   [REPORT - round 2 - NOT_FOUND]
> Endpoint-side evidence does NOT retain the uploaded file bytes or rendered content. Definitive findings: (1) BRUCE BIRTHDAY HAPPY HOUR PICS.lnk = Backdoor.PsEmpire, SHA256 7A1367EFBA05B09E317909B040C3CDA972544212B4F9DB639237492351A3A405, 5732 bytes, cleaned by deletion on every endpoint that touched
_full: reports/s2_round_2.md_

### 12:51:11 - SH -> s2   [RETIRE]
s2 exhausted the endpoint-recovery angle and established a durable negative: the image-named files are not recoverable from the scoped Symantec, Code42, or WinEventLog evidence, while the .lnk alone was retained as malware metadata. Further progress requires a different artifact class, so this senior should hand off rather than continue on a second weak round.

### 12:51:11 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 12:51:11 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['ess_content_importer', 'ms:o365:reporting:messagetrace', 'stream:smtp'] sources=- fields=['subject', 'sender', 'recipient', 'attachment', 'message content', 'quarantine-related fields']
**Technique:** content
**Reason:** The active senior's endpoint and network metadata scopes cannot recover the cloud-only file contents. A new senior is needed for content-bearing mail and imported message evidence, which the retired senior could not cover.

Determine whether the Taedonggang-uploaded artifacts or their delivery path were preserved in email or imported message-content evidence, identify the file whose content contains one word rendered much larger than the rest, and report that word exactly.

### 12:54:44 - s3 -> SH   [REPORT - round 1 - NOT_FOUND]
> The email delivery path IS preserved: stream:smtp holds 879 events on host matar, 185 full DATA-carrying SMTP sessions (method=DATA, response 354 "End data"), with content_type fields proving bodies/attachments were captured. All mail flows from Microsoft O365 outbound IPs (104.47.32.79, 104.47.33.7
_full: reports/s3_round_1.md_

### 12:54:49 - SH -> s3   [COMMAND]
**continue** — The case now has a concrete content-bearing source with preserved MIME bodies, which is closer to the uploaded artifact than the prior dead ends. We still lack the actual word, so the next step must extract and inspect message content rather than scan for plaintext tokens.
**New scope:** sourcetypes=['stream:smtp'] sources=[] fields=['_raw', 'content_type', 'method', 'src', 'dest', 'src_ip', 'dest_ip']

Within sourcetype stream:smtp, decode the 185 DATA-bearing MIME messages and establish whether any contain attachment names, HTML bodies, or linked content corresponding to the Taedonggang persona, bgist@froth.ly, the OneDrive/Birthday Pictures delivery chain, or the files BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, morebeer.jpg, stout-2.jpg, and stout.png. Identify the specific file or message content that preserves formatting or HTML/CSS large-text markup, then recover the exact word rendered much larger than the rest.

### 12:57:36 - s3 -> SH   [REPORT - round 2 - NOT_FOUND]
> The oversized-word carrier is narrowed to two unextracted candidates. (1) Two SMTP bodies carry large font-size (34/36/28px) with font-family 'Open Sans' and colors #404040 / #FFFFFF — my rex failed because quoted-printable soft line breaks ("=\r\n") split the style attribute mid-string; a regex tol
_full: reports/s3_round_2.md_

### 12:57:40 - SH -> s3   [COMMAND]
**continue** — The case now has a sharply reduced target set inside stream:smtp, which is genuine progress toward the oversized-word artifact. We still need the literal word, so the remaining effort should focus on full MIME/body decoding of the specific candidate emails.
**New scope:** sourcetypes=['stream:smtp'] sources=['stream:smtp'] fields=['_raw', 'content_type', 'method', 'src', 'dest', 'src_ip', 'dest_ip']

Within sourcetype stream:smtp, decode the exact candidate messages already isolated this round: first the four STOUT-sent bulk emails to ghoppy@froth.ly, bgist@froth.ly, bstoll@froth.ly, and fyodor@froth.ly around 2018-09-15T01:14:16Z, and also the two Open Sans large-font HTML bodies with 34–36px styling that resisted extraction due to quoted-printable line breaks. Establish which message preserves the uploaded artifact or rendered content with a single word displayed much larger than the rest, and report that word exactly.

### 13:06:36 - s3 -> SH   [REPORT - round 3 - NOT_FOUND]
> DELIVERY PATH ESTABLISHED: The Taedonggang persona is HyunKi Kim <hyunki1984@naver.com>. His extortion email, Subject "All your datas belong to us" (2018-07-26 12:08), told Grace Hoppy "We brought your data and imported it: https://pastebin.com/sdBUkwsE" — the uploaded artifacts were preserved/impor
_full: reports/s3_round_3.md_

### 13:06:40 - SH -> s3   [COMMAND]
**retry** — The case now has a specific target artifact, but the active SMTP-only scope cannot recover web page content. One final round should shift this senior to web-content evidence and test whether the pastebin page or its title was observed in HTTP traffic.
**New scope:** sourcetypes=['stream:http'] sources=['stream:http'] fields=['_raw', 'uri', 'uri_path', 'url', 'host', 'http_user_agent', 'site', 'status', 'src', 'dest']

Establish whether any web-content evidence in index=botsv3 captured access to pastebin.com/sdBUkwsE or related pastebin retrievals tied to the Taedonggang extortion chain, and if so recover the page title or body element containing the word rendered much larger than the rest. Prioritize HTTP sources that preserve URI, host, and any content-bearing fields or raw payloads around the extortion timeframe and involved users, and report the exact oversized word if present.

### 13:11:43 - s3 -> SH   [REPORT - round 4 - NOT_FOUND]
> THE ARTIFACT IS IDENTIFIED: pwned.jpg at http://temp-e.net/files/incoming/hoffa/pwned.jpg (exfil server 62.73.58.161, Taedonggang's server) — the only file on that server in stream:http, fetched once by 192.168.3.130 (a Frothly endpoint) on 2018-08-20T10:23:37Z with a bing.com referrer. This is a Ta
_full: reports/s3_round_4.md_

### 13:11:51 - SH -> s3   [RETIRE]
s3 exhausted the available rounds while establishing the strongest surviving leads: the Taedonggang extortion message references pastebin.com/sdBUkwsE, and stream:http shows a single retrieval of pwned.jpg from temp-e.net by 192.168.3.130, but neither SMTP nor HTTP in this dataset preserves the response body or image content needed to read the oversized word. With no rounds left and no literal answer in hand, this senior must retire with the unresolved target artifact and host for follow-up.

### 13:11:52 - s3 -> SH   [HANDOFF]
_full: handoffs/s3_handoff.md_

### 13:11:52 - runner   [NOTE]
question ended: rounds — falling back to ''

