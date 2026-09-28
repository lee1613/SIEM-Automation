# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http host=hoth "root:x:0:0" | stats count by uri_path, status
### What it means
Intention: Test whether stream:http captures HTTP response bodies at all — the `cat /etc/passwd` RCE wrote its output to the response stream, so if bodies were captured, "root:x:0:0" would appear; this decides whether the `cat /tmp/colonel colonel.c` output could exist anywhere in the feed.

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: This senior is circling the same hoth HTTP lead without producing a readable line-2 artifact. Round 3 added no settled evidence and did not close the key gap around whether any dataset artifact renders /tmp/colonel.c text.
- Scope I owned: sourcetypes=['stream:http', 'osquery:results', 'bash_history', 'linux_audit', 'syslog', 'ps', 'lsof'] sources=[] fields=['host', '_raw', 'form_data', 'uri_path', 'columns.cmdline', 'columns.path', 'TargetFilename', 'file_path', 'name', 'process', 'user']
- Rounds worked: 3/8  (iterations: 25, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "tomcat_root" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype=bash_history "tomcat_root" | stats count by host, source
- index=botsv3 sourcetype=bash_history host=hoth | stats count by source, user
- index=botsv3 sourcetype=bash_history | stats count by host, source, user
- index=botsv3 sourcetype=osquery:results host=hoth "colonel" | stats count by name, columns.time, columns.cmdline | sort -columns.time
- index=botsv3 sourcetype=stream:http host=hoth "kernel priv esc" | stats count by uri_path, status, http_method
- index=botsv3 sourcetype=stream:http host=hoth "root:x:0:0" | stats count by uri_path, status
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*echo*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval b64len=len(b64) | stats count by b64len
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*echo*" | rex field=form_data "#cmd='echo\s+(?<b64>[A-Za-z0-9+/=]+)\s*'?\s*>" | rex field=form_data "#cmd='echo\s+(?<b64full>[A-Za-z0-9+/=]+)" | eval decoded=base64decode(b64full) | rex field=decoded "^(?<line1>[^\n]*)\n(?<line2>[^\n]*)\n(?<line3>[^\n]*)\n(?<line4>[^\n]*)\n(?<line5>[^\n]*)" | stats count by line1, line2, line3, line4, line5
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" form_data="*echo*" | rex field=form_data "#cmd='echo\s+[A-Za-z0-9+/=]+(?<rest>[^']{0,60})" | stats count by rest
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" | rex field=form_data "#cmd='(?<rce_cmd>[^']{0,120})" | stats count by rce_cmd | sort rce_cmd
- index=botsv3 sourcetype=stream:http host=hoth uri_path="/frothlyinventory/integration/saveGangster.action" | stats count by form_data
- index=botsv3 sourcetype=stream:http host=hoth | stats count by http_method, status, uri_path | sort -count
- index=botsv3 sourcetype=syslog source="/var/log/syslog" host=hoth "tomcat8" | stats count by _time, _raw | sort _time
