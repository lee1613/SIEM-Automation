# s4 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=8_
**Scope:** sourcetype=stream:smtp flow_id=8ff70a37-b52e-4810-8203-b00a8d9d8aeb | fields=content{}, _raw, attach_filename, attach_size_decoded
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1 (s2/s3): thread mapped; 13:50:47Z email off-topic → first qualifying attachment is image002.jpg at 13:56:27Z; body references "the Splunk chart".
- R2 (retired senior): osquery/Symantec/o365 cannot hold the answer.
- R3 (me): literal "image002" absent from all five code42:* feeds and WinEventLog/Sysmon/WinHostMon.
- R4 (me): Code42 file inventory (13 names/14 paths, read in full) zero JPGs; Sysmon only pwned.jpg/~WRD000.jpg, earlier and unattributed.
- R5 (me): artifact quoted (flow 8ff70a37, image002.jpg first, 158,643 bytes); body prose quoted; attach_content{} shown not to exist.
- R6 (this): payload located in content{} elements 16–143; verified-clean 211,524-char base64 extracted; read_image rejected it twice.

## This round
### What I ran
- mvcount/len on flow 8ff70a37 -> main event: 285 content{} elements, raw 481,070 chars; 4 small sibling events (502–721 chars)
- mvfind -> image002.jpg part header at content{} index 15; image003.jpg header at index 144
- substr of elements 15/16 -> header "Content-Type: image/jpeg; name=\"image002.jpg\" ... size=158643; Content-ID: <image002.jpg@01D4247D.2394E720>"; element 16 begins "/9j/4AAQSkZJRg..." (JPEG magic)
- read_image with extract_spl mvjoin(mvindex('content{}',16,143)) -> "No image found. What the event does hold: JSON event"
- length check -> 211,587 cleaned chars but tail carried MIME-boundary junk; element 143 tail shows payload ends at "//Z" then "--_005_BN7PR17MB2257..."
- read_image with boundary-stripped extraction -> "No image found. What the event does hold: JSON event"
- final verification -> 211,524 chars, head "/9j/4AAQSkZJRgABAQEAjACMAAD/2w" (SOI), tail "oAKKKKACoL3/jxuP8Ark38qKKAP//Z" (EOI) — complete clean JPEG base64

### What it means
NOT_FOUND, but the wall is now precisely characterized. The JPEG payload is NOT under attach_content{} (that field does not exist) — it lives in content{} elements 16–143 of the main event, and I extracted it as verified-clean base64: 211,524 characters, correct JPEG SOI and EOI markers, matching the 158,643-byte decoded size. So the payload IS fully recoverable from the indexed data. What fails is rendering: read_image rejected the isolated payload twice with "No image found. What the event does hold: JSON event". One variant is untried — my extract_spl returned all 5 flow events (4 with null img), and the tool's reply suggests it inspected a sibling JSON event; appending "| where isnotnull(img)" so only the payload row returns is the single remaining call. I never saw the image, so I hold no two-word kind and did not guess one.

## Ruled out
- attach_content{} as the payload field — does not exist; payload is in content{} elements 16–143
- Body prose as the kind's source — read in full; says "the Splunk chart", names no type
- Code42 (all five feeds) — complete file inventory, zero JPGs/attachments
- WinEventLog .jpg activity — 0 events; Sysmon — only pwned.jpg/~WRD000.jpg, earlier unattributed email
- osquery:*/symantec:ep:*/o365 — closed by prior seniors
- read_image with a multi-event extract_spl — failed twice; suspected cause: sibling events in the result set

Residual gap: one read_image retry with "| where isnotnull(img)" appended to the extract_spl.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
