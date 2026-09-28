# s3 - Q329 - Round 1
_stamped by runner: rounds_remaining=0 novel_spl=1_
**Scope:** sourcetype=osquery:results | source=/var/log/osquery/osqueryd.results.log | fields=columns.path, columns.cmdline, columns.command, columns.directory, columns.history_file, host
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 20

## Prior rounds
No prior evidence in this scope. 
Discovered mars telemetry lives in osquery:results, not a separate obvious archive feed.
Confirmed file/path/history fields exist, but not the target artifact yet.
Shell-history top values are generic admin commands, not archive handling.
Keyword search for the tarball name returned no hit.

## This round
### What I ran
- `get_source_types()` -> confirmed osquery:results available among BOTSv3 feeds.
- `get_sources(keyword="mars")` -> found `/var/log/osquery/osqueryd.results.log` on `mars.i-08e52f8b5a034012d`.
- `get_sourcetype_fields(sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log", index="botsv3")` -> exposed path/cmdline/command/history fields.
- `get_field_values(field="columns.command", ...)` -> top values were ls, pwd, vi inputs.conf, cd, etc.
- `search_keyword(keyword="frothly_html_memcached")` -> no results.
### What it means
I have confirmed the relevant host feed but have not yet isolated the archive members or rendered HTML artifacts. The current scope is too broad for a reliable answer.

## Ruled out
- Direct keyword hit on `frothly_html_memcached.tar.gz` - no manifest match.
- Shell-history top commands as direct evidence of extraction/viewing - too generic to identify the archive or displayed word.

## Open questions for SH
- Which other mars content-access feed should I prioritize if there is one beyond osquery telemetry?
- Is the archive name possibly represented only through file paths or generated filenames rather than the literal tarball name?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
