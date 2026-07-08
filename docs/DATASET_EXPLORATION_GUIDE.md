# BOTS V3 Dataset Exploration Guide

## Quick Start Queries

Once your Splunk instance is running with BOTS V3 installed, use these queries to understand the dataset.

### 1. Basic Data Overview

**Count all events:**
```spl
index=botsv3 earliest=0 | stats count
```

**See data timeline:**
```spl
index=botsv3 earliest=0 
| stats min(_time) as start, max(_time) as end 
| eval start=strftime(start, "%Y-%m-%d %H:%M:%S"), end=strftime(end, "%Y-%m-%d %H:%M:%S")
```

**List all available sourcetypes:**
```spl
index=botsv3 earliest=0 | stats count by sourcetype | sort - count
```

### 2. Log Sources by Category

#### Windows & Endpoint Security
```spl
# Windows Event Logs
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational earliest=0 | head 20

# Process execution
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational EventCode=1 earliest=0 | head 20

# Network connections
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational EventCode=3 earliest=0 | head 20
```

#### Network Traffic
```spl
# DNS queries
index=botsv3 sourcetype=stream:dns earliest=0 | head 20

# HTTP traffic
index=botsv3 sourcetype=stream:http earliest=0 | head 20

# SMB network activity
index=botsv3 sourcetype=stream:smb earliest=0 | head 20

# SSH connections
index=botsv3 sourcetype=stream:tcp dest_port=22 earliest=0 | head 20
```

#### Web Server Logs
```spl
# Apache access logs
index=botsv3 sourcetype=access_combined earliest=0 | head 20

# Web errors
index=botsv3 sourcetype=apache_error earliest=0 | head 20
```

#### Cloud & Infrastructure
```spl
# AWS CloudTrail activity
index=botsv3 sourcetype=aws:cloudtrail earliest=0 | head 20

# AWS CloudWatch logs
index=botsv3 sourcetype=aws:cloudwatch earliest=0 | head 20

# Office 365 activity
index=botsv3 sourcetype=o365:management:activity earliest=0 | head 20
```

#### Linux/Unix System Logs
```spl
# Linux secure logs (SSH, sudo)
index=botsv3 sourcetype=linux_secure earliest=0 | head 20

# Linux audit
index=botsv3 sourcetype=linux_audit earliest=0 | head 20

# System logs
index=botsv3 sourcetype=syslog earliest=0 | head 20
```

### 3. Common Attack Patterns

#### Reconnaissance Activity
```spl
# Port scanning (multiple connections to different ports)
index=botsv3 sourcetype=stream:tcp earliest=0 
| stats count by src, dest_port 
| where count > 10 
| stats count by src
```

**DNS reconnaissance:**
```spl
index=botsv3 sourcetype=stream:dns query=* earliest=0 
| stats count by src, query 
| sort - count
```

#### Credential Attacks
```spl
# Failed SSH login attempts
index=botsv3 sourcetype=linux_secure invalid_user earliest=0 | head 20

# Failed Windows logins
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational EventCode=4625 earliest=0 | head 20
```

#### Data Exfiltration
```spl
# Large data transfers
index=botsv3 sourcetype=stream:tcp bytes_out > 1000000 earliest=0 | head 20

# HTTP uploads
index=botsv3 sourcetype=stream:http method=POST earliest=0 | head 20
```

#### Web Attacks
```spl
# SQL injection patterns
index=botsv3 sourcetype=access_combined OR sourcetype=stream:http 
| regex request="(union|select|insert|update|delete|drop)" 
| head 20

# Directory traversal
index=botsv3 sourcetype=access_combined OR sourcetype=stream:http 
| regex request="\.\." 
| head 20

# HTTP error responses
index=botsv3 sourcetype=stream:http status=4* OR status=5* earliest=0 | head 20
```

### 4. Host & User Analysis

**Hosts in dataset:**
```spl
index=botsv3 earliest=0 | stats count by host | sort - count
```

**Users in dataset:**
```spl
index=botsv3 earliest=0 | stats count by user | sort - count
```

**User-host relationships:**
```spl
index=botsv3 earliest=0 | stats count by user, host | sort - count
```

**Failed authentication by user:**
```spl
index=botsv3 (sourcetype=linux_secure OR sourcetype=xmlwineventlog) 
(failed OR failure OR "invalid user" OR EventCode=4625) 
| stats count by user 
| sort - count
```

### 5. Data Field Examples

**See all fields in an event type:**
```spl
index=botsv3 sourcetype=stream:http earliest=0 | head 1 | fields *
```

**Network event fields:**
```spl
index=botsv3 sourcetype=stream:tcp earliest=0 | head 1 | fields *
```

**Windows event fields:**
```spl
index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational earliest=0 | head 1 | fields *
```

### 6. Timeline Analysis

**Events per hour:**
```spl
index=botsv3 earliest=0 
| timechart count by sourcetype span=1h
```

**Peak activity times:**
```spl
index=botsv3 earliest=0 
| eval hour=strftime(_time, "%H") 
| stats count by hour 
| sort - count
```

**Activity by day of week:**
```spl
index=botsv3 earliest=0 
| eval day=strftime(_time, "%a") 
| stats count by day
```

### 7. Statistical Summaries

**Top source IPs:**
```spl
index=botsv3 earliest=0 | stats count by src | sort - count | head 20
```

**Top destination IPs:**
```spl
index=botsv3 earliest=0 | stats count by dest | sort - count | head 20
```

**Top domains contacted:**
```spl
index=botsv3 earliest=0 | stats count by query | sort - count | head 20
```

**Top URLs accessed:**
```spl
index=botsv3 sourcetype=stream:http earliest=0 | stats count by uri | sort - count | head 20
```

---

## Key Concepts for Agent Design

### 1. **Multi-Source Event Correlation**
The dataset contains events from 50+ sources. A good SIEM agent should:
- Correlate events across different sourcetypes
- Link related events by user, host, IP, or session
- Identify attack patterns across sources

### 2. **Timeline-Based Analysis**
- Events span multiple hours/days
- Look for sequences of events that form attack chains
- Use timing to identify related activities

### 3. **Common Fields for Correlation**
- `src` / `dest` - Source and destination IPs
- `host` - Host generating the event
- `user` - User account involved
- `sourcetype` - Log source type
- `_time` - Event timestamp

### 4. **Attack Signature Recognition**
Common patterns in BOTS V3:
- Port scanning → Connection attempts → Intrusion
- Reconnaissance (DNS/network scans) → Exploitation → Data exfiltration
- Failed logins → Successful login → Malicious activity
- Lateral movement (host-to-host connections)

### 5. **Data Enrichment Opportunities**
Consider implementing:
- GeoIP lookups for IP addresses
- Domain reputation checks
- User and host baseline analysis
- Threat intelligence correlations

---

## Exporting Data for Further Analysis

**Export to CSV:**
```spl
index=botsv3 earliest=0 sourcetype=stream:http 
| table _time, src, dest, uri, status 
| outputlookup /tmp/http_events.csv
```

**Export for Python analysis:**
```spl
index=botsv3 earliest=0 
| table _time, host, user, sourcetype, src, dest 
| stats count by host, sourcetype
| outputlookup /tmp/analysis.csv
```

---

## Next Steps

1. **Start querying** - Run the queries above to understand the data
2. **Identify patterns** - Look for attack signatures and behavioral anomalies
3. **Build detections** - Create saved searches for suspicious activities
4. **Design agent logic** - Map detection rules to agent decision trees
5. **Test at scale** - Build your SIEM agent and run it against this dataset

