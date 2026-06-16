# BOTS V3 Dataset Setup Guide

## Overview
BOTS V3 (Boss of the SOC v3) is a 320MB pre-indexed Splunk dataset containing realistic security incident data with 50+ different log types including:
- Windows Event Logs & Sysmon
- Web server logs (Apache, IIS)
- Network traffic (DNS, HTTP, SMB, SSH)
- Cloud logs (AWS CloudTrail, AWS CloudWatch, O365)
- Endpoint protection (Symantec, Code42)
- System logs (Linux, Unix, Windows)

**Status:** ✅ Dataset downloaded and extracted at: `botsv3/botsv3_data_set/`

---

## Installation Steps

### Step 1: Download Splunk Enterprise 7.1.7

1. Visit https://www.splunk.com/en_us/download/splunk-enterprise.html
2. Create a free account using: `budgetingautomation@gmail.com`
3. Download **Splunk Enterprise 7.1.7** for Windows
4. Save to: `C:\Users\Lee023\Downloads\splunk-7.1.7-standalone-windows.msi` (or similar)

**Alternative - Download via Command Line:**
```powershell
# You'll need to login to Splunk and copy the direct download URL
# Then use:
Invoke-WebRequest -Uri "<SPLUNK_DOWNLOAD_URL>" -OutFile "$env:USERPROFILE\Downloads\splunk-enterprise.msi"
```

### Step 2: Install Splunk Enterprise

1. Run the MSI installer
2. Choose installation path: `C:\Program Files\Splunk` (default is fine)
3. During setup:
   - Username: `admin`
   - Password: Create a strong password (save this!)
   - Start Splunk service on boot: ✅ (recommended)
4. Complete the installation
5. Start Splunk Enterprise (should auto-start)

**Verify Installation:**
```powershell
# Test Splunk is running
Start-Process "http://localhost:8000"
# You should see the Splunk login page
```

### Step 3: Install Required Add-ons

After Splunk starts, install these add-ons via the Splunk UI or by downloading them:

#### Via Splunk UI (Easiest):
1. Go to http://localhost:8000
2. Login with admin credentials
3. Click **Settings** → **Apps** → **Browse more apps**
4. Search and install:
   - Splunk Common Information Model (CIM) v4.11.0
   - Splunk Add-on for Unix and Linux v5.2.4
   - Splunk Add-on for Microsoft Windows v4.8.4
   - Splunk Stream Add-on v7.1.2
   - Splunk Security Essentials v2.2.0
   - (Additional add-ons as listed in the README.md)

**Critical Add-ons List:**
| Add-on | Version | Purpose |
|--------|---------|---------|
| Splunk Common Information Model | 4.11.0 | Data model definitions |
| Splunk Add-on for Unix and Linux | 5.2.4 | Linux/Unix log parsing |
| Splunk Add-on for Microsoft Windows | 4.8.4 | Windows event log parsing |
| Splunk Stream Add-on | 7.1.2 | Network traffic analysis |
| Splunk Security Essentials | 2.2.0 | Security analytics framework |
| Splunk Add-on for AWS | 4.5.0 | AWS log parsing |
| Splunk Add-on for Microsoft Cloud Services | 2.1.0 | Azure/O365 parsing |

### Step 4: Install BOTS V3 Dataset App

1. Find your Splunk `etc/apps` directory:
   ```
   C:\Program Files\Splunk\etc\apps\
   ```

2. Move the extracted dataset there:
   ```powershell
   Move-Item -Path "C:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\SIEM Automation\botsv3\botsv3_data_set" `
             -Destination "C:\Program Files\Splunk\etc\apps\botsv3"
   ```

3. Set proper permissions (run as Admin):
   ```powershell
   icacls "C:\Program Files\Splunk\etc\apps\botsv3" /grant:r "SYSTEM:(OI)(CI)F" /grant:r "BUILTIN\Administrators:(OI)(CI)F"
   ```

### Step 5: Restart Splunk

```powershell
# As Administrator
Restart-Service SplunkWeb
Restart-Service SplunkD
```

Or restart from Splunk UI:
- Settings → System Settings → Restart Splunk

### Step 6: Verify Dataset Access

1. Go to http://localhost:8000
2. Search for:
   ```
   index=botsv3 earliest=0
   ```
3. You should see events from the dataset

---

## Dataset Overview

Once loaded, explore the dataset with these searches:

### Data Sourcetypes Available:
```spl
index=botsv3 | stats count by sourcetype
```

### Sample Attack Scenarios:
```spl
# Web attacks
index=botsv3 sourcetype=stream:http status=404

# Windows authentication failures
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational EventCode=1

# Network reconnaissance
index=botsv3 sourcetype=stream:dns query=*

# AWS suspicious activity
index=botsv3 sourcetype=aws:cloudtrail errorCode=*
```

### Data Timeline:
```spl
index=botsv3 earliest=0 | stats min(_time) as min, max(_time) as max
| eval min_human=strftime(min,"%Y-%m-%d %H:%M:%S"), max_human=strftime(max,"%Y-%m-%d %H:%M:%S")
```

---

## Troubleshooting

**Issue: Can't find botsv3 index**
- Ensure add-ons are installed
- Restart Splunk (Settings → System Settings → Restart Splunk)
- Check app permissions

**Issue: Missing events**
- Verify app was copied to correct location: `$SPLUNK_HOME/etc/apps/botsv3`
- Check Splunk logs: `$SPLUNK_HOME/var/log/splunk/splunkd.log`

**Issue: Slow searches**
- This is normal with large datasets
- Use time range constraints in searches
- Use `| head 1000` to limit results

---

## Next Steps for Agent Design

Now that you have the dataset set up, you can:

1. **Explore Event Patterns:**
   - Query different event types
   - Identify attack signatures
   - Map data relationships

2. **Design Detection Rules:**
   - Create alerts based on specific patterns
   - Build saved searches for threats

3. **Build SIEM Agent Logic:**
   - Parse multi-source logs
   - Correlate events across sourcetypes
   - Classify incidents by severity

4. **Export Data for Analysis:**
   - Export search results as CSV
   - Use Python/APIs for further analysis
   - Build automation workflows

---

## File Locations

```
C:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\SIEM Automation\
├── botsv3/
│   ├── botsv3_data_set.tgz (320MB - original download)
│   ├── botsv3_data_set/ (extracted)
│   │   ├── bin/
│   │   ├── default/ (Splunk app configuration)
│   │   ├── lookups/ (reference data)
│   │   └── var/ (index data files)
│   ├── README.md (setup instructions)
│   └── LICENSE
└── BOTS_V3_SETUP.md (this file)
```

---

## Resources

- **BOTS V3 GitHub:** https://github.com/splunk/botsv3
- **Splunk Documentation:** https://docs.splunk.com
- **Splunk Community:** https://community.splunk.com
- **BOTS CTF Scoreboard:** https://github.com/splunk/SA-ctf_scoreboard

---

**Created:** 2026-06-16  
**Dataset Version:** 3  
**Status:** Ready for exploration
