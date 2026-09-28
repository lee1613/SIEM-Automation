# s3 - Q329 - Round 4
_stamped by runner: rounds_remaining=0 novel_spl=12_
**Scope:** sourcetype=stream:http | source=stream:http, stream:Splunk_HTTPURI, stream:Splunk_HTTPStatus | fields=_raw, uri, uri_path, url, host, site, status, src, dest, http_content_type, http_referrer
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- R1: mapped 102 sourcetypes; ess_content_importer = 2 daemon-error events; "taedonggang" absent in plaintext across 9 feeds; stream:smtp holds 185 DATA-bearing MIME sessions.
- R2: stream:smtp token map — bgist=27, stout=4, font-size=54, h1=19; all named filenames zero in plaintext; font-size outliers 41/36/34/31/28px.
- R3: outliers mapped to Groupon/Dropbox/O365-quarantine templates; 4 attacker-IP (45.77.53.176) "Quarentined email" phishing notifications; found pastebin.com/sdBUkwsE in a Segoe-UI-styled email.
- R4: pastebin email fully read — Taedonggang persona = HyunKi Kim <hyunki1984@naver.com>, Subject "All your datas belong to us" (2018-07-26), "We brought your data and imported it: https://pastebin.com/sdBUkwsE"; word not recovered.
- R5 (this round): stream:http swept — no pastebin traffic at all; found pwned.jpg on temp-e.net exfil server.

## This round
### What I ran
- index=botsv3 sourcetype=stream:http pastebin -> 0; sdBUkwsE -> 0.
- Token map (font-size/h1/hacked/pwned/pastebin/froth/beer) -> font-size=0, h1=4, pwned=2, pastebin=0.
- pwned-context rex -> 2 events: GET temp-e.net/files/incoming/hoffa/pwned.jpg, 200, image/jpeg, 53022 bytes, src 192.168.3.130, dest 62.73.58.161, referrer bing.com.
- dest/src=62.73.58.161 full sweep -> exactly 1 event: that single pwned.jpg GET.

### What it means
NOT_FOUND for the word, but the artifact is now identified: pwned.jpg is the Taedonggang-uploaded file on the exfil server (temp-e.net/62.73.58.161), fetched once by endpoint 192.168.3.130. The delivery path IS preserved in web-content evidence. The word cannot come from this scope: stream:http carries no response bodies (no HTML content anywhere in the feed), and the artifact is a JPEG whose content no HTTP event preserves. The pastebin paste was never fetched over cleartext HTTP.

## Ruled out
- pastebin.com/sdBUkwsE in stream:http - zero events; never fetched over HTTP (HTTPS-only).
- stream:http as a source of HTML body content - font-size=0 hits; the feed preserves request/response metadata only, no bodies.
- brewertalk.com defacement as the oversized-word carrier - all h1 hits are in request metadata, not page content.

## Open questions for SH
- Can I get scope on endpoint evidence (WinHostMon, osquery:results, bash_history, PowerShell logs) for host 192.168.3.130 to find how pwned.jpg was created/rendered and what text it contains?
- Should I use web_lookup on pastebin.com/sdBUkwsE to see if the paste (and its large-rendered title) is still publicly retrievable?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: s3 exhausted the available rounds while establishing the strongest surviving leads: the Taedonggang extortion message references pastebin.com/sdBUkwsE, and stream:http shows a single retrieval of pwned.jpg from temp-e.net by 192.168.3.130, but neither SMTP nor HTTP in this dataset preserves the response body or image content needed to read the oversized word. With no rounds left and no literal answer in hand, this senior must retire with the unresolved target artifact and host for follow-up.
- Scope I owned: sourcetypes=['ess_content_importer', 'ms:o365:reporting:messagetrace', 'stream:smtp'] sources=[] fields=['subject', 'sender', 'recipient', 'attachment', 'message content', 'quarantine-related fields']
- Rounds worked: 4/4  (iterations: 32, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype, source
- index=botsv3 (sourcetype=stream:dns OR sourcetype=aws:s3:accesslogs OR sourcetype=WinHostMon OR sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational OR sourcetype=stream:http) taedonggang | stats count by sourcetype, source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace taedonggang | stats count
- index=botsv3 sourcetype=o365:management:activity taedonggang | stats count by Operation, UserId, Workload
- index=botsv3 sourcetype=stream:http dest=54.67.127.227 | stats count by uri_path, site | sort -count | head 25
- index=botsv3 sourcetype=stream:http dest=62.73.58.161 OR src=62.73.58.161 | stats count by uri_path, site, http_method, status, http_content_type
- index=botsv3 sourcetype=stream:http froth | rex field=_raw max_match=2 "(?s)(?<frothctx>.{0,200})froth" | stats count by frothctx | head 10
- index=botsv3 sourcetype=stream:http pastebin | stats count by uri, site, src, dest
- index=botsv3 sourcetype=stream:http pwned | rex field=_raw max_match=3 "(?s)(?<pwnctx>.{0,300})pwned" | stats count by pwnctx
- index=botsv3 sourcetype=stream:http pwned | rex field=_raw max_match=3 "(?s)pwned(?<pwnpost>.{0,300})" | stats count by pwnpost
- index=botsv3 sourcetype=stream:http sdBUkwsE | stats count by uri, site, src, dest
- index=botsv3 sourcetype=stream:http site=temp-e.net | stats count by uri_path, http_method, status | sort -count
- index=botsv3 sourcetype=stream:http taedonggang | stats count
- index=botsv3 sourcetype=stream:http | rex field=_raw max_match=3 "(?i)<h1(?<h1ctx>.{0,300})" | search h1ctx=* | stats count by h1ctx
- index=botsv3 sourcetype=stream:http | stats count by uri | sort - count | head 25
- index=botsv3 sourcetype=stream:http | stats count(eval(searchmatch("font-size"))) as fontsize, count(eval(searchmatch("h1"))) as h1, count(eval(searchmatch("hacked"))) as hacked, count(eval(searchmatch("pwned"))) as pwned, count(eval(searchmatch("Pastebin"))) as pastebin, count(eval(searchmatch("Froth"))) as froth, count(eval(searchmatch("beer"))) as beer
- index=botsv3 sourcetype=stream:http | top limit=25 site by src
- index=botsv3 sourcetype=stream:smtp "45.77.53.176" | rex field=_raw max_match=1 "(?i)Subject:\s*(?<subj>.{0,130})" | stats count by subj
- index=botsv3 sourcetype=stream:smtp "45.77.53.176" | rex field=_raw max_match=1 "(?i)Subject:\s*(?<subj>[^\r\n]{0,130})" | stats count by subj
- index=botsv3 sourcetype=stream:smtp "45.77.53.176" | rex field=_raw max_match=1 "(?i)Subject:\s+(?<subj>[A-Z][^\r\n]{0,120})" | stats count by subj
- index=botsv3 sourcetype=stream:smtp "font-size: 36px" | rex field=_raw max_match=2 "(?s)font-size: 36px.{0,250}?>\s*(?<h1text>.{0,180})" | stats count by h1text
- index=botsv3 sourcetype=stream:smtp "Open Sans" | rex field=_raw max_match=1 "(?s)font-family: 'Open Sans'(?<osbody>.{0,1500})" | stats count by osbody
- index=botsv3 sourcetype=stream:smtp font-size | rex field=_raw max_match=50 "font-size:\s*(?<pxsize>\d+)" | mvexpand pxsize | stats count by pxsize | sort - pxsize
- index=botsv3 sourcetype=stream:smtp h1 | rex field=_raw max_match=10 "(?i)<h1[^>]*>\s*(?<h1text>[^<]{1,60})" | stats count by h1text
- index=botsv3 sourcetype=stream:smtp pastebin | rex field=_raw max_match=1 "(?s)(?<pre>.{0,400})pastebin" | stats count by pre
- index=botsv3 sourcetype=stream:smtp pastebin | rex field=_raw max_match=1 "(?s)sdBUkwsE(?<post>.{0,1200})" | stats count by post
- index=botsv3 sourcetype=stream:smtp stout | rex field=_raw max_match=3 "(?i)stout(?<stoutctx>.{0,150})" | stats count by stoutctx
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=10 "font-size:\s*(?:41|36|34|31|28)px(?<bigctx>.{0,200})" | search bigctx=* | stats count by bigctx
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=10 "font-size:\s*(?:41|36|34|31|28)px[^>]*>\s*(?<bigword>[^<]{1,80})" | search bigword=* | stats count by bigword
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=10 "font-size:\s*(?:4[0-9]|3[0-9]|2[89])px(?s)(?:(?!>).){0,900}>\s*(?<bigword>.{0,200})" | search bigword=* | stats count by bigword
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=2 "(?i)<h1[^>]*>\s*(?<h1full>.{0,300})" | search h1full="Also*" | stats count by h1full
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=3 "font-size:\s*(?:36|34|28)px; font-family: 'Open Sans'[^>]*>(?<osctx>.{0,800})" | search osctx=* | stats count by osctx
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=5 "font-size:\s*(?:34|31|28|24|22|21)px(?<bigctx>.{0,260})" | search bigctx=* | stats count by bigctx
- index=botsv3 sourcetype=stream:smtp | rex field=_raw max_match=5 "Quarantined Email(?<qctx>.{0,600})" | search qctx=* | stats count by qctx
- index=botsv3 sourcetype=stream:smtp | stats count(eval(searchmatch("bgist"))) as bgist, count(eval(searchmatch("morebeer"))) as morebeer, count(eval(searchmatch("stout"))) as stout, count(eval(searchmatch("Birthday"))) as birthday, count(eval(searchmatch("OneDrive"))) as onedrive, count(eval(searchmatch("taedonggang"))) as taedonggang, count(eval(searchmatch("lnk"))) as lnk, count(eval(searchmatch("font"))) as font, count(eval(searchmatch("font-size"))) as fontsize, count(eval(searchmatch("<h1"))) as h1, count(eval(searchmatch("font size"))) as fontsize_attr
- index=botsv3 sourcetype=stream:smtp | stats count(eval(searchmatch("bgist"))) as bgist, count(eval(searchmatch("morebeer"))) as morebeer, count(eval(searchmatch("stout"))) as stout, count(eval(searchmatch("irthday"))) as birthday, count(eval(searchmatch("OneDrive"))) as onedrive, count(eval(searchmatch("taedonggang"))) as taedonggang, count(eval(searchmatch("lnk"))) as lnk, count(eval(searchmatch("font"))) as font, count(eval(searchmatch("font-size"))) as fontsize, count(eval(searchmatch("h1"))) as h1, count(eval(searchmatch("base64"))) as base64, count(eval(searchmatch("Content-Disposition"))) as contentdisposition, count(eval(searchmatch("Content-Transfer-Encoding"))) as cte
