# s2 - Q209 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=5_
**Scope:** sourcetype=yum-too_small source=/var/log/yum.log; sourcetype=cloud-init-output | fields: _raw, host, action, pkg, raw_ts
**Insight:** partial (credible candidate; 20-package total and transaction boundary directly verified, 7/13 split rests on p2 + package-name inference)
**Candidate:** 7,13   **Confidence:** 85

## Prior rounds
- R1 (s1): cloud-init-output on all 3 gacrux hosts; yum install in modules:final = 7 pkgs + 13 deps; gnupg2 update in modules:config is separate. Premises p1/p2 filed, unsettled; bootstrap feed belongs to hoth, not web tier.

## This round
### What I ran
- get_sources / get_sourcetype_fields yum-too_small -> one source /var/log/yum.log, 63 events, 3 gacrux hosts; _time is ingestion (Aug 20), real ts inside _raw.
- get_raw_events (20 rows) -> "Jul 26 01:37:28 Installed: httpd-2.2.34-1.16.amzn1.x86_64" style lines.
- `index=botsv3 sourcetype=yum-too_small | rex field=_raw "^(?<raw_ts>[A-Za-z]{3} +\d+ +\d+:\d+)" | rex ...(?<action>[A-Za-z]+): | stats count by host, action, raw_ts` -> 6 rows: each host 20 Installed + 1 Updated at Jul 26 00:45 / 01:35 / 01:37.
- `... | rex ...(?<action>\w+): +(?<pkg>\S+) | stats count by action, pkg | sort action, pkg` -> 21 rows, complete: 20 distinct Installed (count 3 each) + Updated: gnupg2-2.0.28-2.32.amzn1.x86_64 (count 3). All 63 feed events accounted.
- `index=botsv3 sourcetype=cloud-init-output "Installing" | stats count by host` -> 1 multi-line event per gacrux host.
- get_raw_events keyword=Installing -> "Cloud-init v. 0.7.6 running 'modules:final' at Thu, 26 Jul 2018 01:37:21 +0000. Up 11.07 seconds." + curl/PGP/yum output; clipped at 1500 chars.
- rex max_match extraction of Installing vs Installing-for-dependencies counts -> rejected (| table without stats); round ended before re-run.

### What it means
yum.log is the package-manager artifact for the launch transaction: exactly 20 packages Installed per gacrux host at launch (raw ts Jul 26, ~11 s after boot per cloud-init "Up 11.07 seconds"), and the only other yum event is the gnupg2 Update — an Upgrade, not an Install, so excluded. 20 = 7 primary + 13 dependent (p2): the names split as 7 bootstrap primaries (httpd, php, php-mysql, php-pecl-memcached, memcached, osquery, php-pear) and 13 deps (httpd-tools, apr, apr-util, apr-util-ldap, php-cli, php-common, php-pdo, php-process, php-xml, php-pecl-igbinary, libmemcached, mysql55-libs, compat-gmp4). cloud-init-output anchors the transaction as the launch-time automation (modules:final, matching Jul 26 timestamps). The 7/13 split itself was not re-extracted from cloud-init-output this round (raw clipped, extraction query rejected); it rests on p2 plus the package-name split, with the 20 total directly verified. p1 is now VERIFIED (premise_updates).

## Ruled out
- gnupg2-2.0.28-2.32.amzn1.x86_64 — "Updated:" not "Installed:", the modules:config upgrade, excluded from the install count.
- sourcetype=bootstrap — hoth fleet, not web tier (prior round).
- Any second install transaction — all 63 yum-too_small events are the 20-package install + 1 update per host; nothing else in the feed.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
