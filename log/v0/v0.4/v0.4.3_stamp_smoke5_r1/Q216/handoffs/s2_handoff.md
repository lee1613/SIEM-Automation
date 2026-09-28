# s2 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=4_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dp,dh,pn,liuid,fss,fes
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 92

## Prior rounds
- Round 1: rival comparison from explicit rows — sole dp=3333 flow is 192.168.70.186→45.77.53.176 (powershell.exe, 112s); coinhive rival on .247.131 is browser cryptojacking over 443; .24.128/.105.214 eliminated; p2 verified; p4 axis (d) left open.
- This round: closed p4's open branch and the full port census; p4 and p5 both verified; 112 stands.

## This round
### What I ran
- `(dp=58868 OR dp=50414 OR dp=4287 OR dp=22790 OR dp=52672 OR dp=53567 OR dp=56756 OR dp=65490) | eval duration=fes-fss | stats ... by da dp` -> 10 rows, all returned: 58868/50414 internal svchost (192.168.10.x→192.168.247.129, MalloryKraeusen, 2s/3s); 4287 CrashPlanService.exe→crashplan.com/code42.com; 22790 Edge→auth.svcs.verizon.com; 52672/53567/56756/65490 internal ephemeral svchost, 0s.
- `(dp=9997 OR dp=8080 OR dp=0 OR dp=22 OR dp=21 OR dp=3306 OR dp=5355) | stats ... by da dp` -> 16 rows, all returned: 9997 splunkd→splunk.froth.ly; 8080/22/21/3306 internal 192.168.8.103→192.168.9.x (putty/hdoor/chrome/powershell); 0/5355 office/mDNS.
- `(dp=5353 OR dp=67 OR dp=68) | stats ... by da dp` -> 21 rows, all returned: mDNS/DHCP/office, svchost/chrome.
- `da=45.77.53.176 | eval duration=fes-fss | stats ... by sa dp` -> 4 rows, all returned: .186:443 (3814 flows, 3452s, p3-excluded), .24.128:443 (1015, 1266s, p3-excluded), .105.214:80 (www.frothly.com, Edge), and .186:3333 (1 flow, 112s).

### What it means
FOUND. Every destination port in the feed is now covered by an explicit, fully-returned row, and no flow on any port other than 192.168.70.186's single dp=3333 flow constitutes Monero generation: the non-standard ports carry backup (CrashPlan), internal svchost/mDNS/DHCP, SSH/putty/hdoor to internal 192.168.9.x, and Splunk forwarding; the attacker server 45.77.53.176 receives only the two p3-excluded 443 beacon sets, one Edge HTTP fetch, and the single 3333 pool flow. The selected endpoint's countable Monero-generation set is exactly one flow — fss=1534762025 to fes=1534762137 — whose SPL-computed duration (eval duration=fes-fss, summed over that flow) is 112 seconds. p4 and p5 verified; no rival endpoint or duration remains.

## Ruled out
- All eight SH-named ports (58868, 50414, 4287, 22790, 52672, 53567, 56756, 65490) - internal svchost / CrashPlan / Verizon auth / 0s ephemeral; not mining.
- 9997, 8080, 0, 22, 21, 3306, 5355 - splunkd forwarding, internal 192.168.8.103 putty/hdoor/chrome, office/mDNS; not mining.
- 5353/67/68 - mDNS/DHCP/office; not mining.
- 45.77.53.176:443 on .186 and .24.128 - p3-verified non-countable C2 beacons.
- .247.131 coinhive (443, chrome.exe) and .105.214 ad pools - eliminated round 1.

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p4 - amend or settle that one. The text you sent was discarded: "Full port census of source=cisconvmflowdata is closed with explicit rows: every "


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['sa', 'da', 'dp', 'pn', 'liuid', 'dh', 'fss', 'fes', 'ibc', 'obc']
- Rounds worked: 2/8  (iterations: 16, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata dp=3333 | stats count min(fss) as flow_start_epoch max(fes) as flow_end_epoch values(pn) as process values(liuid) as user by sa da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dh="*coinhive*" OR dh="*monero*" OR dh="*pool*" OR dh="*xmr*" OR dh="*miner*" OR dh="*cryptonight*") | stats count min(fss) as flow_start max(fes) as flow_end values(dp) as ports values(pn) as process by sa dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=3333 OR dh="*coinhive*" OR pn=powershell.exe) | eval duration=fes-fss | stats count sum(duration) as total_seconds min(fss) as first_start max(fes) as last_end values(liuid) as user by sa da dp pn | sort - total_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=5353 OR dp=67 OR dp=68) | eval duration=fes-fss | stats count sum(duration) as total_seconds dc(sa) as endpoints values(pn) as process values(dh) as hostname by da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=58868 OR dp=50414 OR dp=4287 OR dp=22790 OR dp=52672 OR dp=53567 OR dp=56756 OR dp=65490) | eval duration=fes-fss | stats count sum(duration) as total_seconds dc(sa) as endpoints values(sa) as endpoint values(pn) as process values(liuid) as user values(dh) as hostname by da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=9997 OR dp=8080 OR dp=0 OR dp=22 OR dp=21 OR dp=3306 OR dp=5355) | eval duration=fes-fss | stats count sum(duration) as total_seconds dc(sa) as endpoints values(sa) as endpoint values(pn) as process values(liuid) as user values(dh) as hostname by da dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval duration=fes-fss | stats count sum(duration) as total_seconds values(pn) as process values(liuid) as user values(dh) as hostname by sa dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count min(fss) as flow_start_epoch max(fes) as flow_end_epoch values(pn) as process values(liuid) as user by sa da
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 | stats count values(dp) as ports values(pn) as processes values(liuid) as users min(fss) as first_flow max(fes) as last_flow by da dh | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count dc(sa) as endpoints by dh | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count dc(sa) as endpoints by dp | sort - count
