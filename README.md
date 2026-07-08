# SIEM Automation - BOTS V3 Dataset Project

## Project Overview

This project is designed to build and test a SIEM (Security Information and Event Management) automation agent using the **BOTS V3 (Boss of the SOC v3)** dataset from Splunk.

**Goal:** Create an AI agent that can analyze, correlate, and detect security incidents across multiple log sources.

---

## Current Status

✅ **BOTS V3 Dataset Downloaded & Extracted**
- Dataset size: 320MB (pre-indexed Splunk format)
- MD5 verified: `d7ccca99a01cff070dff3c139cdc10eb`
- Location: `./botsv3/botsv3_data_set/`
- Event types: 50+ sourcetypes (Windows, Linux, AWS, Network, Web, etc.)

### What's Included

| File | Purpose |
|------|---------|
| `docs/BOTS_V3_SETUP.md` | Complete installation guide for Splunk Enterprise |
| `docs/DATASET_EXPLORATION_GUIDE.md` | 50+ example queries to understand the dataset |
| `botsv3/` | Cloned repository + extracted dataset |

---

## Quick Start

### 1. Install Splunk Enterprise
Follow the steps in `docs/BOTS_V3_SETUP.md`:
- Download Splunk Enterprise 7.1.7 (free trial)
- Install required add-ons
- Copy the dataset app to `$SPLUNK_HOME/etc/apps/botsv3`
- Restart Splunk

### 2. Explore the Data
Once Splunk is running, open `docs/DATASET_EXPLORATION_GUIDE.md` and run the queries to understand:
- Log sources and data types
- Attack patterns and anomalies
- Field structures and relationships
- Timeline of events

### 3. Design Your Agent
With data understanding, plan your SIEM agent:
- Event correlation logic
- Attack pattern detection
- Incident classification
- Automated response workflows

---

## Dataset Overview

### Data Sources (50+ types)
- **Windows:** Event logs, Sysmon, process execution
- **Linux:** Auth logs, audit logs, syslog
- **Network:** DNS, HTTP, TCP, UDP, SMB, SSH
- **Cloud:** AWS CloudTrail, CloudWatch, O365
- **Web:** Apache, IIS access logs
- **Endpoint:** Symantec, Code42, Tenable
- **Infrastructure:** AWS, Azure, network streams

### Key Statistics
- **Total Events:** Millions of events
- **Time Period:** Multi-day timespan
- **Sourcetypes:** 50+ different log types
- **Key Fields:** src, dest, host, user, sourcetype, _time
- **Format:** Pre-indexed Splunk (no parsing needed)

---

## Architecture

```
Project Root
├── README.md (this file)
├── docs/BOTS_V3_SETUP.md (installation guide)
├── docs/DATASET_EXPLORATION_GUIDE.md (query examples)
└── botsv3/
    ├── README.md (original BOTS V3 docs)
    ├── botsv3_data_set/ (extracted dataset)
    │   ├── default/ (Splunk config)
    │   ├── lookups/ (reference data)
    │   └── var/lib/ (index data - 601MB)
    └── botsv3_data_set.tgz (original download)
```

---

## Next Steps

### Phase 1: Environment Setup
1. [ ] Download Splunk Enterprise 7.1.7
2. [ ] Install Splunk on local machine
3. [ ] Install required add-ons
4. [ ] Deploy BOTS V3 dataset
5. [ ] Verify access with test query

### Phase 2: Data Exploration
1. [ ] Run 20+ exploration queries
2. [ ] Document interesting patterns
3. [ ] Identify attack signatures
4. [ ] Map field relationships
5. [ ] Create baseline statistics

### Phase 3: Agent Design
1. [ ] Define detection rules
2. [ ] Design correlation logic
3. [ ] Plan incident classification
4. [ ] Build proof-of-concept detections
5. [ ] Document architecture

### Phase 4: Implementation
1. [ ] Code core agent logic
2. [ ] Implement detections
3. [ ] Build correlation engine
4. [ ] Add incident classification
5. [ ] Test against BOTS V3

### Phase 5: Evaluation
1. [ ] Measure detection accuracy
2. [ ] Evaluate false positive rate
3. [ ] Test performance at scale
4. [ ] Document findings
5. [ ] Optimize agent

---

## Important Notes

### System Requirements
- **OS:** Windows 10/11
- **Disk Space:** ~2GB (Splunk + dataset)
- **Memory:** 4GB+ recommended
- **Java:** Required by Splunk (auto-installed)

### Splunk License
- Using **free Splunk Enterprise trial** (no volume limits for this dataset)
- No licensing costs for BOTS V3 analysis
- Pre-indexed data = fast queries

### Data Sensitivity
⚠️ The BOTS V3 dataset contains realistic security incident data and may contain:
- Profanity and offensive language
- Real attack signatures
- Simulated malware artifacts
- Educational content only

---

## Resources

### Documentation
- [BOTS V3 GitHub Repository](https://github.com/splunk/botsv3)
- [Splunk Documentation](https://docs.splunk.com)
- [Splunk Community Forums](https://community.splunk.com)
- [BOTS CTF Platform](https://github.com/splunk/SA-ctf_scoreboard)

### Learning
- BOTS V3 includes realistic attack scenarios
- Designed for SIEM training and CTF competitions
- Great for learning incident detection and response
- Multiple hours of security incident data

### Tools
- **Splunk Enterprise:** SIEM platform and query engine
- **SPL:** Splunk Processing Language (SQL-like query language)
- **Lookups:** Reference data for enrichment
- **Dashboards:** Visualization and exploration

---

## License

BOTS V3 Dataset: Public Domain (CC0)
- See `botsv3/LICENSE` for details
- Original authors: Splunk (2018)

Project Documentation: Open Source
- Use freely for educational/research purposes

---

## Git Workflow

```bash
# View setup guides
cat docs/BOTS_V3_SETUP.md
cat docs/DATASET_EXPLORATION_GUIDE.md

# Check dataset status
ls -lh botsv3/botsv3_data_set/

# Later: commit agent code
git add src/
git commit -m "Add SIEM agent implementation"
```

---

## Contact & Support

- **Questions about BOTS V3?** Check `botsv3/README.md`
- **Splunk help?** Visit community.splunk.com
- **Project issues?** Document in commit messages

---

**Project Created:** 2026-06-16  
**Dataset Version:** BOTS V3  
**Status:** Ready for Splunk installation and exploration  

Next: Follow `docs/BOTS_V3_SETUP.md` to install Splunk Enterprise.
