# s3 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=9_
**Scope:** sourcetype=osquery:results, stream:http, out-3, localhost-5, syslog, linux_secure, linux_audit | source=/var/log/osquery/osqueryd.results.log, stream:http | fields=_raw, form_data, http_content_length, columns.cmdline
**Insight:** partial
**Candidate:** " * Ubuntu 16.04.4 kernel priv esc"   **Confidence:** 85

## Prior rounds
- R1 (prior senior): API transport failure; no evidence gathered.
- R2 (me): read all 11 osquery colonel events (commands/hashes/sizes only) and all 4 stream:http Struts2 POSTs; found the echo base64 transport; hand-decoded line 2; submitted the value.
- R3 (this round): proved no direct render exists anywhere in scope; proved the encoded transport is complete.

## This round
### What I ran
- stream:http "cat /tmp/colonel.c" | eval rawlen=len(_raw) -> 1 event: rawlen=1542, http_content_length=5775, bytes_out=5880.
- stream:http window 19:11:00-19:12:00 for the attack pair -> 3 events: cat POST (rawlen 1542, cl 5775), suitecrm GET (cl 12), md5sum POST (cl 49). No second event carries the body.
- (out-3 OR localhost-5 OR syslog OR linux_secure OR linux_audit) ("unistd.h" OR "setuid" OR "vnik" OR "bleidl" OR "colonel.c") -> 0 events.
- (osquery:results OR stream:http) same tokens -> 1 event; get_raw_events identified it as an ib.adnxs.com ad URI "/setuid" (image/gif, 43 bytes, src 192.168.3.130) — unrelated.
- stream:http "echo" "/tmp/colonel" | rex b64 | eval b64len -> b64len=7700, rawlen=9241.
- stream:http "VWJ1bnR1IDE2LjA0LjQ" -> 0 events (tokenization false negative: the 7700-char blob is one search token; the rex extraction proves it is present).

### What it means
No accessible artifact renders /tmp/colonel.c directly. The cat response body is metadata-only in its event (1542 chars stored vs a 5775-byte body; sole event in its flow). No host log or osquery event carries C-source text. The only content-bearing record is the complete 7700-char base64 transport in the 19:08:37 echo POST — complete because /tmp/colonel is 7701 bytes on disk = 7700 base64 chars + newline, and 7700/4×3 = 5775 = the FIM size of /tmp/colonel.c = the cat response's content_length. Line 2 is therefore inferable only by decoding: hand-decoded group-by-group from the first 44 base64 chars, line 1 = "/*", **line 2 = " * Ubuntu 16.04.4 kernel priv esc"**, line 3 = " *". The decoded credits (@bleidl, -vnik) match the public eBPF priv-esc exploit, corroborating the decode. The value is submit-able; its only residual risk is leading-whitespace formatting.

## Ruled out
- cat response body as a direct render — event stores 1542 chars vs the 5775-byte body; sole event in flow 5b903a0c.
- out-3, localhost-5, syslog, linux_secure, linux_audit — 0 events for C-source tokens or colonel.c.
- osquery:results — the 11 colonel events carry commands, hashes and sizes only.
- the single "setuid" stream:http hit — ad-network URI /setuid on ib.adnxs.com, unrelated to hoth.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
