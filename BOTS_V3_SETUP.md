# BOTSv3 Dataset Setup Guide

> **Your operating system matters.**
> Splunk behaves differently on Windows and macOS — installation paths, service management, and the KV Store (MongoDB) all work differently. Steps that work on Windows may fail on macOS, and vice versa. Read the section that matches your OS before proceeding.

---

## Overview

BOTSv3 (Boss of the SOC v3) is a pre-indexed Splunk dataset (~320MB compressed, ~600MB extracted) containing realistic security incident data with 100+ sourcetypes including:

- Windows Event Logs & Sysmon
- Web server logs (Apache, IIS)
- Network traffic (DNS, HTTP, SMB, SSH)
- Cloud logs (AWS CloudTrail, AWS CloudWatch, O365)
- Endpoint protection (Symantec, Code42)
- System logs (Linux, Unix, Windows)

**Dataset location in this project:** `botsv3/botsv3_data_set.tgz`  
**CTF content (questions, answers, hints):** `botsv3content/`

---

## Part 1 — Windows Setup

> This is the primary supported platform. The `agent/setup_scoreboard.py` script was written and tested on Windows.

### Step 1: Install Splunk Enterprise

1. Download Splunk Enterprise from the [Splunk website](https://www.splunk.com/en_us/download/splunk-enterprise.html)
2. Run the MSI installer
3. Use the default installation path: `C:\Program Files\Splunk\`
4. Set an admin username and password — **save these, you will need them in `.env`**
5. Let the installer start the Splunk service

Verify it is running by visiting `http://localhost:8000`.

### Step 2: Install Required Add-ons

In Splunk Web: **Settings → Apps → Browse more apps**, search and install:

| Add-on | Version |
|--------|---------|
| Splunk Common Information Model (CIM) | 4.11.0 |
| Splunk Add-on for Unix and Linux | 5.2.4 |
| Splunk Add-on for Microsoft Windows | 4.8.4 |
| Splunk Stream Add-on | 7.1.2 |
| Splunk Security Essentials | 2.2.0 |
| Splunk Add-on for AWS | 4.5.0 |
| Splunk Add-on for Microsoft Cloud Services | 2.1.0 |

### Step 3: Install the BOTSv3 Dataset App

The Splunk apps directory on a typical Windows machine is:
```
C:\Program Files\Splunk\etc\apps\
```

Extract the dataset archive into the apps directory (run PowerShell as Administrator):
```powershell
tar -xzf botsv3\botsv3_data_set.tgz -C "C:\Program Files\Splunk\etc\apps\"
```

This creates `botsv3_data_set\` inside the apps directory, containing the pre-built index data under `var\lib\splunk\botsv3\`.

Set permissions:
```powershell
icacls "C:\Program Files\Splunk\etc\apps\botsv3_data_set" /grant:r "SYSTEM:(OI)(CI)F" /grant:r "BUILTIN\Administrators:(OI)(CI)F"
```

### Step 4: Install the CTF Scoreboard Apps

Clone both apps into the Splunk apps directory:
```powershell
cd "C:\Program Files\Splunk\etc\apps"
git clone https://github.com/splunk/SA-ctf_scoreboard.git
git clone https://github.com/splunk/SA-ctf_scoreboard_admin.git
```

### Step 5: Restart Splunk

```powershell
Restart-Service SplunkD
```

Or from Splunk Web: **Settings → System Settings → Restart Splunk**

After restart, Splunk should recognise the `botsv3`, `scoreboard`, and `scoreboard_admin` indexes.

### Step 6: Run the Automated Setup Script

Configure `agent/.env`:
```
SPLUNK_HOST=https://localhost:8089
SPLUNK_USER=admin
SPLUNK_PASS=<your password>
NIM_API_KEY=<your NIM key>
```

Then run from the project root:
```powershell
python agent/setup_scoreboard.py --skip-restart
```

This script:
- Writes `scoreboard_controller.config` with your credentials and a random VKEY
- Creates the scoreboard log directory under the Splunk install
- Loads 58 questions into the `ctf_questions` KV store
- Loads 58 answers into the `ctf_answers` KV store
- Loads hints into the `ctf_hints` KV store
- Creates a default EULA record and marks it accepted for your admin user
- Creates a `ctf_users` entry so the scoreboard can track your score

> **Note on the scoreboard web controller:** The CherryPy controller at `/en-US/custom/SA-ctf_scoreboard/submit_question` does not load on Splunk 9/10 Windows due to a `No module named 'splunklib.six.moves'` error. The `ScoreboardClient` in `agent/scoreboard_client.py` bypasses this by talking directly to the KV store REST API and writing events to `index=scoreboard`.

### Step 7: Verify

```spl
index=botsv3 | stats count
```
Expected: ~2,083,056 events

Scoreboard UI: `http://localhost:8000/en-US/app/SA-ctf_scoreboard/`

---

## Part 2 — macOS Setup

> **macOS has important differences from Windows — especially around the KV Store. Read this section fully before starting.**

### Key differences at a glance

| Area | Windows | macOS |
|------|---------|-------|
| Splunk install path | `C:\Program Files\Splunk\` | `/Applications/Splunk/` |
| Apps directory | `...\etc\apps\` | `/Applications/Splunk/etc/apps/` |
| Start/stop Splunk | `Restart-Service SplunkD` | `/Applications/Splunk/bin/splunk restart` |
| KV Store on Splunk 10.x | Works normally | **Crashes splunkd on startup** |
| `setup_scoreboard.py` | Works as-is | `SPLUNK_HOME` path must be updated |

### Step 1: Install Splunk Enterprise

Download the macOS `.dmg` or `.tgz` from the Splunk website and install it. On a typical Mac, Splunk is installed at `/Applications/Splunk/`.

Start it for the first time:
```bash
/Applications/Splunk/bin/splunk start --accept-license
```

Set an admin password when prompted. Verify at `http://localhost:8000`.

### Step 2: Install the BOTSv3 Dataset App

The Splunk apps directory on a typical Mac is:
```
/Applications/Splunk/etc/apps/
```

Extract the archive:
```bash
tar -xzf botsv3/botsv3_data_set.tgz -C /Applications/Splunk/etc/apps/
```

This creates `botsv3_data_set/` (~600MB extracted) including the full index data under `var/lib/splunk/botsv3/`.

### Step 3: Install the CTF Scoreboard Apps

```bash
cd /Applications/Splunk/etc/apps
git clone https://github.com/splunk/SA-ctf_scoreboard.git
git clone https://github.com/splunk/SA-ctf_scoreboard_admin.git
```

### Step 4: KV Store on macOS — Critical Known Issue

> **On Splunk 10.x for macOS, enabling the KV Store causes `splunkd` to crash immediately on every startup** with:
> ```
> ERROR MongodRunner - Failed to import PFX file into Keychain
> ERROR MongodRunner - Failed to add PFX to certificate store
> ```
> This is a Splunk 10.x macOS bug with MongoDB SSL certificates and the macOS Keychain. There is no simple in-place fix without downgrading Splunk.

**Required workaround — keep KV Store disabled:**

Edit `/Applications/Splunk/etc/system/local/server.conf` and ensure it contains:
```ini
[kvstore]
disabled = true
```

If the `[kvstore]` stanza is absent, add it. This allows `splunkd` to start normally.

**What this means:**
- The CTF KV collections (`ctf_questions`, `ctf_answers`, `ctf_hints`) cannot be populated
- `agent/run_all.py` and `agent/scoreboard_client.py` will not work on macOS Splunk 10.x
- The core SIEM agent (`agent/splunk_agent.py`) and all Splunk search queries work perfectly

**If you need the KV Store:** Use Splunk 9.x on macOS (the bug is absent there), or run Splunk in Docker.

### Step 5: Restart Splunk

```bash
/Applications/Splunk/bin/splunk restart
```

Confirm the indexes are recognised in the startup output:
```
Validated: ... botsv3 ... scoreboard scoreboard_admin scoreboard_admin_kv ...
```

### Step 6: Run the Setup Script (macOS-adjusted)

`agent/setup_scoreboard.py` has `SPLUNK_HOME` hardcoded for Windows. Before running on macOS, change **line 34** from:
```python
SPLUNK_HOME = r"C:\Program Files\Splunk"
```
to:
```python
SPLUNK_HOME = "/Applications/Splunk"
```

Then run (only relevant when KV Store is enabled, i.e. on Splunk 9.x):
```bash
python agent/setup_scoreboard.py --skip-restart
```

If KV Store is disabled (the default macOS 10.x workaround), skip this step — the agent runs directly against `index=botsv3` without the scoreboard KV data.

### Step 7: Verify

```bash
python3 - << 'EOF'
import sys
sys.path.insert(0, "agent")
from splunk_client import SplunkClient
c = SplunkClient("https://localhost:8089", "admin", "yourpassword")
r = c.search("index=botsv3 | stats count", earliest="0", latest="now", max_results=1)
print("Event count:", r["results"][0]["count"])
EOF
```

Expected: `Event count: 2083056`

---

## Part 3 — Running the Agent

Once Splunk is up and `index=botsv3` has data, the agent works on both platforms:

```bash
# Single question (CLI)
cd agent/
python splunk_agent.py "List out the IAM users that accessed an AWS service in Frothly's AWS environment?"

# All 58 questions via scoreboard (Windows only — requires KV Store)
python run_all.py
```

See `CLAUDE.md` for the full architecture, canonical run workflow, and scoreboard details.

---

## Project File Structure

```
<project root>/
├── agent/
│   ├── splunk_agent.py          # Main SIEM agent
│   ├── splunk_client.py         # Splunk REST API client
│   ├── scoreboard_client.py     # CTF scoreboard submission
│   ├── run_all.py               # Runs agent on all 58 questions
│   ├── setup_scoreboard.py      # One-time scoreboard KV store setup
│   └── botsv3_fields.json       # Local field manifest (102 sourcetypes)
├── botsv3/
│   ├── botsv3_data_set.tgz      # BOTSv3 dataset archive (~320MB)
│   └── botsv3_data_set/         # Extracted Splunk app (config + index data)
├── botsv3content/
│   ├── ctf_questions.csv        # 58 BOTSv3 questions
│   ├── ctf_answers.csv          # 58 correct answers
│   └── ctf_hints.csv            # Hints for each question
└── datasets/
    ├── botsv3_questions.json    # Questions in JSON format (used by run_all.py)
    └── botsv3_answers.json      # Answers in JSON (reference only)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `401 Unauthorized` on port 8089 | Wrong password in `.env` | Update `SPLUNK_PASS` |
| `Connection refused` on port 8089 | Splunk not running | Run `splunk start` |
| `splunkd` crashes immediately on macOS | KV Store PFX Keychain bug (Splunk 10.x) | Add `disabled = true` under `[kvstore]` in `system/local/server.conf` |
| `index=botsv3` returns 0 events | `.tgz` not fully extracted | Re-extract the full `.tgz` — the app skeleton alone (~1MB) contains no index data |
| KV store returns 500 / "Unsupported Operation" | KV Store disabled | Enable on Windows; accept the limitation on macOS Splunk 10.x |
| `No module named 'langchain_openai'` | Missing Python deps | `pip install langchain-openai langchain-core langgraph` |

---

## Resources

- [BOTSv3 GitHub](https://github.com/splunk/botsv3)
- [SA-ctf_scoreboard GitHub](https://github.com/splunk/SA-ctf_scoreboard)
- [SA-ctf_scoreboard_admin GitHub](https://github.com/splunk/SA-ctf_scoreboard_admin)
- [Splunk Documentation](https://docs.splunk.com)

---

**Dataset Version:** BOTSv3  
**Splunk tested on:** 10.4.0 (Windows ✅ full support · macOS ✅ search only, KV Store disabled)
