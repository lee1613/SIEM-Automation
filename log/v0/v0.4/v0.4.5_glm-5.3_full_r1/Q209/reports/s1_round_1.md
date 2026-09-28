# s1 - Q209 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=cloud-init-output | source=/var/log/cloud-init-output.log | fields=_raw, host
**Insight:** FOUND
**Candidate:** 7,13   **Confidence:** 92

## Prior rounds
- (Round 1) None — this is the first round.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; cloud-init-output identified as the launch-time init log feed.
- get_sources(sourcetype=cloud-init-output) -> single source /var/log/cloud-init-output.log, 23 events.
- get_raw_events -> Cloud-init v. 0.7.6 runs on gacrux hosts; yum output visible inside modules:config and modules:final stages.
- `index=botsv3 sourcetype=cloud-init-output "Dependent" | rex field=_raw "(?<line>.*Dependent.*)" | stats count by line` -> 3 events, all "Install  7 Packages (+13 Dependent packages)".
- Same feed, rex for cloud-init module -> the Install line sits in `modules:final` on gacrux.i-06fea586f3d3c8ce8, gacrux.i-09cbc261e84259b54, gacrux.i-0cc93bade2b3cba63 (3/3 rows read).
- rex "Installing:" section -> exactly 7 packages per host: httpd, libmemcached, memcached, osquery, php, php-mysql, php-pecl-memcached.
- rex "Installing for dependencies:" section -> dependency list (apr, apr-util, apr-util-ldap, compat-gmp4, httpd-tools, mysql55-libs, php-cli, php-common, php-pdo, php-pear, php-pecl-igbinary, …) consistent with the stated +13.

### What it means
When a gacrux web-server EC2 instance launches, cloud-init v. 0.7.6 runs its `modules:final` stage, whose yum transaction summary reads verbatim "Install  7 Packages (+13 Dependent packages)". The enumerated Installing section independently lists exactly 7 packages, corroborating the first count; the dependency section corroborates the second. All three fleet instances show the identical transaction, consistent with one shared auto-scaling launch configuration. Answer: 7 installed packages, 13 dependent packages.

## Ruled out
- gnupg2 transaction in cloud-init modules:config ("Upgrade 1 Package") — an upgrade of one already-present package, not the bootstrap install set.
- Splunk forwarder deployment steps in the same log (tar extraction / file listing) — not yum package installs.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"limit": 20, "sourcetype": "cloud-init-output"}` (10 of 20 rows seen). A claim resting on them alone is UNVERIFIED._
