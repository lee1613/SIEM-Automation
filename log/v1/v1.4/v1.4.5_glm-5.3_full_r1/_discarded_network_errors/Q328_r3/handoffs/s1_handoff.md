# s1 - Q328 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means
Intention: auth.log holds only routine cron session records, no escalation trace. Check the localhost-5 tomcat log for any record of the file contents.

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"min_count": 1, "sourcetype": "stream:http"}` (28 of 57 rows seen); `get_raw_events: {"limit": 15, "sourcetype": "out-3"}` (7 of 15 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: s1 is circling the same colonel.c lead without producing a dataset-readable text artifact for line 2, and this round added no new search. Another round in the same hands is unlikely to settle the blocked premises.
- Scope I owned: sourcetypes=['stream:http', 'osquery:results', 'bash_history', 'linux_audit', 'linux_secure', 'config_file', 'history-2'] sources=[] fields=['host', '_raw', 'columns.cmdline', 'columns.path', 'columns.target_path', 'columns.content', 'file_path', 'command', 'uri_path', 'form_data']
- Rounds worked: 4/8  (iterations: 34, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "kernel priv esc" | stats count by sourcetype, source, host
- index=botsv3 sourcetype=bash_history (sudo OR chmod OR chown OR setuid OR sudoers OR tomcat OR passwd OR root) | stats count by _raw | sort - count
- index=botsv3 sourcetype=bash_history (sudo OR chmod OR chown OR setuid OR sudoers OR tomcat OR passwd OR root) | table _time _raw source
- index=botsv3 sourcetype=osquery:results colonel | stats count by name, columns.path, columns.cmdline
- index=botsv3 sourcetype=stream:http "kernel priv esc" | stats count by uri_path, host
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*echo*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)(?<tail>[^']{0,40})" | eval b64len=len(b64) | stats count by b64len, tail
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval decoded=base64decode(b64) | eval lines=split(decoded,"
") | eval line2=mvindex(lines,1) | stats count by line2
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval l1=len(b64) | eval withnl=b64."\n" | eval l2=len(withnl) | eval m_plain=md5(b64) | eval m_nl=md5(withnl) | stats count by l1, l2, m_plain, m_nl
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval withnl=b64."\n" | eval md5colonel=md5(withnl) | eval b64len=len(b64) | stats count by md5colonel, b64len
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]{1,120})" | stats count by b64
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]{1,200})" | stats count by b64
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*LyoK*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]{1,400})" | stats count by b64
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" | rex field=form_data "#cmd='(?<cmd>[^']{0,130})" | stats count by cmd | sort - count
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" | stats count by form_data
- index=botsv3 sourcetype=stream:http host=hoth | stats count by uri_path
