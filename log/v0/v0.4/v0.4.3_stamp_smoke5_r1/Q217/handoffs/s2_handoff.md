# s2 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, content, attach_filename, attach_type, attach_size, attach_disposition
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 85

## Prior rounds
- R1: Opened SMTP; two Bud identities in feed; found 11 attachment-bearing events, read only 2 earliest (truncated); no value.
- R2: Enumerated all 11 attachment events (no truncation); Bud Stoll owns the allhands brewertalk/miner thread (image001.jpg 02:38:43, image002+003.jpg 02:44:24, Postmortem image002.jpg 03:12:19); only viz prose in feed = "Look at the Splunk chart below" (02:44:24 email); 0 matches for 11 two-word viz names; no value.

## This round
### What I ran
- `"image001.jpg" "brewertalk"` + rex after us-ascii -> full plain-text body of the 02:38:43 event: "Yeah. It looks like we have some issues - I haven't figured it out yet...but check out the metrics store search below.... I'll figure it out! -bud [cid:image001.jpg@01D4247C.58AEEAB0]".
- `"image002.jpg" "image003.jpg"` + rex -> full body of the 02:44:24 follow-up: "Wow Billy. I did find the issue! Look at the Splunk chart below - I saw some instances spin up... CPU of my local Chrome browser... spiked to 100%! ... some malicious code got into our forums. [cid:image002.jpg@...]" — it quotes the 02:38:43 message verbatim.
- Postmortem event charset/transfer-encoding rex -> base64 ×3; body unreadable via SPL.
- HTML context around cid:image001 -> no alt/title attributes on the img tag.

### What it means
NOT_FOUND, stated explicitly per SH's contingency: SMTP identifies the artifact but not the two-word visualization type. The first attachment is image001.jpg (image/jpeg, inline, 226222 bytes, base64 in attach_content) in Bud Stoll's "RE: Improved brewertalk.com - check it out!" (Mon 15 Sep 2018 02:38:43 UTC, to Billy Tun + allhands@froth.ly). Its body calls the image only "the metrics store search"; the HTML has no alt text; MIME headers carry only filename/type/size. The 02:44:24 follow-up is the SAME thread (quotes the first email verbatim, same sender/recipients), so image001.jpg is part of the coin-miner thread — but the email that explicitly illustrates the identified issue is the 02:44:24 one, and even it says only "Splunk chart" (one word). No two-word visualization name exists anywhere in stream:smtp. The type lives only in the image pixels: image-level reading of the decoded image001.jpg (or image002.jpg under the alternative reading) is what would come next, outside this feed's text.

## Ruled out
- Textual viz cues in the first email — full plain body, HTML alt/title, MIME headers, Content-ID all read; none names a visualization.
- Two-word viz names in stream:smtp — 0 matches across 11 common Splunk visualization names (R2).
- Postmortem email body as a clarifier — base64-encoded, unreadable via SPL.
- Billy Tun's attachments (pwned.jpg to one employee, non-miner subject; hire-dates xlsx) and Bruce Gist's Malware Alert Text.txt (not Bud) — wrong sender/recipients/subject.

## What I'd tell my replacement
- Retired because: This senior proved with evidence that stream:smtp can identify the first Bud attachment artifact and thread context, but cannot reveal the visualization type because no textual cue exists in MIME/body fields and the answer lives only in image pixels. Another round in the same scope would re-walk a dead end.
- Scope I owned: sourcetypes=['stream:smtp'] sources=[] fields=['src', 'dest', 'from', 'to', 'subject', 'attachment', 'filename', 'mime_type', 'content_type']
- Rounds worked: 3/8  (iterations: 30, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=stream:smtp "attach_filename" "image001.jpg" "brewertalk" | rex field=_raw "Look at the Splunk (?<viz>[A-Za-z ]{1,60})below" | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Date: (?<date>[^\\\\]{0,40})" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "\"attach_size\":\[(?<sizes>[^\]]*)\]" | stats min(_time) as cap_time values(viz) as viz values(from) as from values(filenames) as filenames values(sizes) as sizes values(date) as date by _raw | sort cap_time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filename>[^\]]*)" | rex field=_raw "\"attach_type\":\[(?<atype>[^\]]*)" | rex field=_raw "From: (?<from>[^\\r\\n]*)" | rex field=_raw "Subject: (?<subject>[^\\r\\n]*)" | stats earliest(_time) as first_time values(filename) as filename values(atype) as atype values(from) as from values(subject) as subject by _raw | sort first_time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "\"attach_type\":\[(?<atypes>[^\]]*)\]" | rex field=_raw "From: (?<from>[^\\\\]{0,80})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,120})" | rex field=_raw "Date: (?<date>[^\\\\]{0,40})" | rex field=_raw "To: (?<to>[^\\\\]{0,200})" | stats min(_time) as cap_time values(date) as date values(to) as to by from subject filenames atypes | sort cap_time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "\"attach_type\":\[(?<atypes>[^\]]*)\]" | rex field=_raw "From: [^\"<]*<(?<from>[^>]*)>" | rex field=_raw "Subject: (?<subject>.*?)Thread-Topic" | rex field=_raw "Date: (?<date>.*?)Message-ID" | rex field=_raw "To: (?<to>.*?)Subject" | stats min(_time) as cap_time values(date) as date values(to) as to by from subject filenames atypes | sort cap_time
- index=botsv3 sourcetype=stream:smtp "attach_filename" | stats count earliest(_time) as first_time latest(_time) as last_time by _raw | sort first_time
- index=botsv3 sourcetype=stream:smtp "image001.jpg" "brewertalk" | rex field=_raw "cid:image001[^\\\"]{0,40}(?<tail>.{0,600})" max_match=3 | stats values(tail) as tail by _raw
- index=botsv3 sourcetype=stream:smtp "image001.jpg" "brewertalk" | rex field=_raw "us-ascii(?<tail>.{0,1200})" | stats values(tail) as tail by _raw
- index=botsv3 sourcetype=stream:smtp "image002.jpg" "image003.jpg" | rex field=_raw "us-ascii(?<tail>.{0,1500})" | stats values(tail) as tail by _raw
- index=botsv3 sourcetype=stream:smtp "Improved brewertalk.com" | rex field=_raw "(?<before>[A-Za-z ,.]{0,80})(chart|dashboard|screenshot|graph|visualization)(?<after>[A-Za-z ,.]{0,80})" max_match=15 | stats list(before) as before list(after) as after count by _raw | sort count
- index=botsv3 sourcetype=stream:smtp "Improved brewertalk.com" | rex field=_raw "Look at the Splunk (?<vizword>[A-Za-z]+)" | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | stats min(_time) as cap_time values(vizword) as vizword values(from) as from values(filenames) as filenames by subject | sort cap_time
- index=botsv3 sourcetype=stream:smtp "Look at the Splunk" | rex field=_raw "Look at the Splunk (?<viz>[A-Za-z ]{1,60})below" | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | rex field=_raw "\"attach_filename\":\[(?<filenames>[^\]]*)\]" | rex field=_raw "Date: (?<date>[^\\\\]{0,40})" | stats min(_time) as cap_time values(viz) as viz values(from) as from values(filenames) as filenames values(date) as date by subject | sort cap_time
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "charset=(?<cs>[^\\\\\"]{0,20})" max_match=5 | rex field=_raw "Content-Transfer-Encoding: (?<cte>[^\\\\\"]{0,20})" max_match=5 | stats list(cs) as charsets list(cte) as encodings by _raw
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "quoted-printable(?<tail>.{0,2500})" | stats values(tail) as tail by _raw
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "us-ascii(?<tail>.{0,2500})" | stats values(tail) as tail by _raw
- index=botsv3 sourcetype=stream:smtp ("coin miner" OR "cryptominer" OR "miner" OR "monero" OR "cryptocurrency") | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | stats count by from subject | sort - count
- index=botsv3 sourcetype=stream:smtp ("dashboard" OR "visualization" OR "chart" OR "screenshot" OR "graph") | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | stats count by from subject | sort - count
- index=botsv3 sourcetype=stream:smtp ("line chart" OR "bar chart" OR "pie chart" OR "column chart" OR "area chart" OR "single value" OR "choropleth" OR "gauge" OR "scatter" OR "heatmap" OR "bubble chart") | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | stats count by from subject | sort - count
- index=botsv3 sourcetype=stream:smtp ("mining" OR "crypto" OR "malware" OR "Splunk" OR "CPU") | rex field=_raw "From: (?<from>[^\\\\]{0,60})" | rex field=_raw "Subject: (?<subject>[^\\\\]{0,100})" | stats count by from subject | sort - count
- index=botsv3 sourcetype=stream:smtp attach_filename=* "From: Billy Tun <btun@froth.ly>" | stats earliest(_time) as first_time values(attach_filename) as filenames values(attach_type) as types by _raw | sort first_time
- index=botsv3 sourcetype=stream:smtp attach_filename=* "From: Billy Tun <btun@froth.ly>" | table _time attach_filename attach_type attach_size attach_disposition bytes | sort _time
- index=botsv3 sourcetype=stream:smtp attach_filename=* | stats count earliest(_time) as first_time values(attach_filename) as filenames values(attach_type) as types by _raw | sort first_time
