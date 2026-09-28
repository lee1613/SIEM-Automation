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

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['yum-too_small', 'cloud-init'] sources=[] fields=['host', '_raw', 'pkg', 'summary', 'stage']
- Rounds worked: 5/5  (iterations: 30, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (sourcetype=yum-too_small OR sourcetype=cloud-init-output) | rex field=_raw "^(?<raw_ts>[A-Za-z]{3} +\d+ +\d+:\d+)" | rex field=_raw "^[A-Za-z]{3} +\d+ +\d+:\d+:\d+ +(?<action>\w+): +(?<pkg>\S+)" | rex field=_raw "running 'modules:final' at (?<final_ts>[^.]+)\. Up (?<final_up>\S+) seconds" | rex field=_raw "running 'modules:config' at (?<config_ts>[^.]+)\. Up (?<config_up>\S+) seconds" | rex max_match=0 field=_raw "Install\s+(?<install_line>[^\n]+)" | eval yum_installed=if(sourcetype=="yum-too_small" AND action=="Installed", pkg, null()) | eval yum_updated=if(sourcetype=="yum-too_small" AND action=="Updated", pkg, null()) | eval inst_minute=if(sourcetype=="yum-too_small" AND action=="Installed", raw_ts, null()) | stats dc(yum_installed) as installed_pkgs, count(yum_installed) as installed_lines, dc(inst_minute) as installed_minutes, values(inst_minute) as inst_minute, values(yum_updated) as updated_pkg, values(final_ts) as modules_final_ts, values(final_up) as final_up_secs, values(config_ts) as modules_config_ts, values(config_up) as config_up_secs, values(install_line) as install_line by host
- index=botsv3 sourc yum-too_small | stats count by host
- index=botsv3 sourcetype=cloud-init-output "gnupg2" | rex field=_raw "running '(?<stage>[^']+)' at (?<hdr>[^,]+)," | rex max_match=0 field=_raw "(?m)^(?<yumline>Updated:\s+\S+)" | stats values(host) as hosts, values(stage) as stage, values(hdr) as hdr, values(yumline) as yumlines
- index=botsv3 sourcetype=cloud-init-output "gnupg2" | rex field=_raw "running 'modules:config' at (?<cfg_ts>[^.]+)\. Up (?<cfg_up>\S+) seconds" | rex max_match=0 field=_raw "(?m)^(?<yumline>Updated:\s+\S+)" | stats values(cfg_ts) as cfg_ts, values(cfg_up) as cfg_up, values(yumline) as yumline by host
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex field=_raw "(?s)Installed:\s+(?<installed_block>.+?)Dependency Installed:" | rex field=_raw "(?s)Dependency Installed:\s+(?<depinst_block>.+?)Complete!" | rex max_match=0 field=installed_block "(?m)^\s*(?<ipkg>\S+)" | rex max_match=0 field=depinst_block "(?m)^\s*(?<dpkg>\S+)" | eval n_i=mvcount(ipkg), n_d=mvcount(dpkg) | stats values(host) as hosts, values(n_i) as n_installed, values(n_d) as n_depinst, values(ipkg) as installed_pkgs, values(dpkg) as dep_pkgs
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex field=_raw "(?s)Installing:\s+(?<primary_block>.+?)Installing for dependencies:" | rex field=_raw "(?s)Installing for dependencies:\s+(?<dep_block>.+?)Transaction Summary" | rex max_match=0 field=primary_block "(?m)^\s+(?<p_pkg>\S+)" | rex max_match=0 field=dep_block "(?m)^\s+(?<d_pkg>\S+)" | eval n_primary=mvcount(p_pkg), n_dep=mvcount(d_pkg) | stats values(host) as hosts, values(n_primary) as n_primary, values(n_dep) as n_dep, values(p_pkg) as primaries, values(d_pkg) as deps
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex field=_raw "running 'modules:final' at (?<final_ts>[^.]+)\. Up (?<up_secs>[^.]+) seconds" | rex max_match=0 field=_raw "Install\s+(?<install_line>[^\n]+)" | stats values(final_ts) as final_ts, values(up_secs) as up_secs, values(install_line) as install_line by host
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex field=_raw "running 'modules:final' at (?<final_ts>[^.]+)\. Up (?<up_secs>\S+) seconds" | rex max_match=0 field=_raw "Install\s+(?<install_line>[^\n]+)" | stats values(final_ts) as final_ts, values(up_secs) as up_secs, values(install_line) as install_line by host
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex field=_raw "running 'modules:final' at (?<ts>[^.]+)\. Up (?<up>[^.]+)\." | stats values(host) as hosts, values(ts) as final_ts, values(up) as uptime
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex max_match=0 field=_raw "(?m)^(?<cmdline>.*yum.*install.*)$" | stats values(host) as hosts, values(cmdline) as cmdlines
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex max_match=0 field=_raw "Install\s+(?<install_line>[^\n]+)" | rex max_match=0 field=_raw "yum\s+(?<yum_line>[^\n]+)" | stats values(host) as hosts, values(install_line) as install_lines, values(yum_line) as yum_lines
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex max_match=0 field=_raw "Installing:\s+(?<primary>\S+)" | rex max_match=0 field=_raw "Installing for dependencies:\s+(?<dep>\S+)" | rex max_match=0 field=_raw "Install\s+(?<install_summary>\d+ Package)" | eval n_primary=mvcount(primary), n_dep=mvcount(dep) | table host, n_primary, n_dep, install_summary
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex max_match=0 field=_raw "Installing\s*:\s+(?<primary>\S+)" | rex max_match=0 field=_raw "Installing for dependencies\s*:\s+(?<dep>\S+)" | rex field=_raw "running '(?<stage>[^']+)' at (?<hdr_ts>[^,]+)," | eval n_primary=mvcount(primary), n_dep=mvcount(dep) | stats values(host) as hosts, values(stage) as stage, values(hdr_ts) as hdr_ts, values(n_primary) as n_primary, values(n_dep) as n_dep, values(primary) as primaries, values(dep) as deps
- index=botsv3 sourcetype=cloud-init-output "Installing" | rex max_match=0 field=_raw "Installing\s*:\s+(?<primary>\S+)" | rex max_match=0 field=_raw "Installing for dependencies\s*:\s+(?<dep>\S+)" | rex field=_raw "running '(?<stage>[^']+)' at (?<hdr_ts>[^,]+)," | stats values(host) as hosts, values(stage) as stage, values(hdr_ts) as hdr_ts, mvcount(primary) as n_primary, mvcount(dep) as n_dep, values(primary) as primaries, values(dep) as deps
- index=botsv3 sourcetype=cloud-init-output "Installing" | stats count by host
- index=botsv3 sourcetype=cloud-init-output | rex max_match=0 field=_raw "running '(?<stage>[^']+)' at (?<hdr_ts>[^,]+)," | stats values(host) as hosts, values(stage) as stages, count by stage
- index=botsv3 sourcetype=yum-too_small action="" | rex field=_raw "^[A-Za-z]{3} +\d+ +\d+:\d+:\d+ +(?<action>\w+): +(?<pkg>\S+)" | stats count by action, pkg | sort action, pkg
- index=botsv3 sourcetype=yum-too_small | rex field=_raw "^(?<raw_ts>[A-Za-z]{3} +\d+ +\d+:\d+)" | rex field=_raw "^[A-Za-z]{3} +\d+ +\d+:\d+:\d+ +(?<action>[A-Za-z]+):" | stats count by host, action, raw_ts
- index=botsv3 sourcetype=yum-too_small | rex field=_raw "^(?<raw_ts>[A-Za-z]{3} +\d+ +\d+:\d+)" | rex field=_raw "^[A-Za-z]{3} +\d+ +\d+:\d+:\d+ +(?<action>\w+): +(?<pkg>\S+)" | stats dc(raw_ts) as distinct_minutes, values(raw_ts) as minutes, dc(pkg) as distinct_pkgs, count as lines by host, action
- index=botsv3 sourcetype=yum-too_small | rex field=_raw "^[A-Za-z]{3} +\d+ +\d+:\d+:\d+ +(?<action>\w+): +(?<pkg>\S+)" | stats count by action, pkg | sort action, pkg
