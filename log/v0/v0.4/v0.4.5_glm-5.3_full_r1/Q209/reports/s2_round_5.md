# s2 - Q209 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=1_
**Scope:** sourcetype=yum-too_small source=/var/log/yum.log; sourcetype=cloud-init-output | fields: _raw, host, action, pkg, raw_ts, final_ts, config_ts, install_line
**Insight:** FOUND
**Candidate:** 7,13   **Confidence:** 97

## Prior rounds
- R1 (s1): cloud-init-output on 3 gacrux hosts; modules:final install = 7 pkgs + 13 deps; gnupg2 modules:config update separate. p1/p2 filed.
- R2 (mine): yum.log = 20 "Installed:" + 1 "Updated: gnupg2" per gacrux host at raw ts Jul 26 00:45/01:35/01:37; p1 verified; 7/13 split rested on p2 + name inference.
- R3 (mine): split verified directly — modules:final "Installed:" block = 7, "Dependency Installed:" = 13, Transaction Summary "7 Packages (+13 Dependent packages)"; gnupg2 = modules:config "Updated:"; p2/p3/p5 verified.
- R4 (mine): per-host rows quoted — one 20-pkg Installed transaction per host in a single minute; modules:final starts same minute, 11-14 s uptime, same summary.
- R5 (mine): modules:config rows quoted — gnupg2 "Updated:" at 00:45:20/01:35:12/01:37:17 (Up 6.55-7.41 s), preceding modules:final.

## This round
### What I ran
- Unified per-host query joining both feeds (yum-too_small + cloud-init-output, rex on _raw for raw_ts/action/pkg, modules:final and modules:config headers, and the Install summary line; stats by host) -> 3 rows, complete, one per gacrux host.

### What it means
p4 is settled by one contiguous, word-for-word output. Each row shows, per host: exactly ONE Installed transaction (installed_minutes=1, 20 distinct packages, 20 lines) at Jul 26 00:45 / 01:35 / 01:37; the only non-Install action is the gnupg2 Update (updated_pkg=gnupg2-2.0.28-2.32.amzn1.x86_64); the modules:final launch event starts in that same minute (modules_final_ts 00:45:24 / 01:35:19 / 01:37:21 +0000, Up 11.83/13.56/11.07 s) carrying the literal summary "7 Packages (+13 Dependent packages)"; and the contrasting modules:config stage (modules_config_ts 00:45:20 / 01:35:12 / 01:37:17 +0000, Up 7.41/7.30/6.55 s) is where the gnupg2 upgrade sits — an Update of 1 package, not part of the 20-package launch install set. All 63 yum-too_small events are accounted for (20 Installed + 1 Updated per host), so no rival install transaction exists. The measured act is the modules:final launch-time install transaction, split 7 primary + 13 dependent. Answer unchanged: 7,13.

## Ruled out
- gnupg2-2.0.28-2.32.amzn1.x86_64 — "Updated:" in modules:config (Up 6.55-7.41 s), an upgrade of 1 package, not part of the modules:final install set.
- Any rival install transaction in yum.log — per-host stats: exactly one 20-package Installed transaction per host; all 63 events accounted.
- Line-based "Installing:" listing extraction (R3) — regex artifacts; superseded by the Transaction Summary and end-of-run blocks, which agree with each other and with yum.log's 20.