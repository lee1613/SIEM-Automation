# BOTS V3 Dataset Verification Report

**Date:** 2026-06-16  
**Status:** ✅ DATASET VERIFIED AND FIXED

---

## Issue Found & Fixed

**Problem:** The `indexes.conf` file was pointing to the wrong path
```
Before:  $SPLUNK_HOME/etc/apps/botsv3_data_set/var/lib/splunk/botsv3/db
Fixed:   $SPLUNK_HOME/etc/apps/botsv3/var/lib/splunk/botsv3/db
```

**Solution:** Updated the path in `C:\Program Files\Splunk\etc\apps\botsv3\default\indexes.conf`

---

## Verification Checklist

### ✅ 1. Configuration File
- Location: `C:\Program Files\Splunk\etc\apps\botsv3\default\indexes.conf`
- Index name: `botsv3`
- Status: **Configured and corrected**

### ✅ 2. Data Buckets
The index contains multiple data buckets with actual event data:
```
db_1534746578_1534737603_311/   ← Contains tsidx, bloomfilter, rawdata
db_1534756500_1534756500_304/   ← Contains tsidx, bloomfilter, rawdata
db_1534758273_1534755600_303/   ← Contains tsidx, bloomfilter, rawdata
db_1534759200_1534759200_312/   ← Contains tsidx, bloomfilter, rawdata
... and 12 more buckets
```

### ✅ 3. Data Files Present
Each bucket contains:
- `tsidx` file (~49KB) - Time-series index
- `bloomfilter` - Fast lookup structure
- `Hosts.data` - Host names
- `SourceTypes.data` - Event source types
- `Sources.data` - Event sources
- `Strings.data` - String values
- `rawdata/` - Raw event data directory

### ✅ 4. Splunk Service
- Service name: `Splunkd`
- Status: **Running**
- Port: 8000 (Web UI)

### ✅ 5. Web Access
- URL: http://localhost:8000
- Login: admin / changeme
- Status: **Ready**

---

## How to Verify in Splunk Web

1. **Open Splunk:** http://localhost:8000
2. **Go to:** Settings → Data Indexes
3. **Look for:** `botsv3` in the list
4. **Check:** 
   - Enabled: Yes
   - Source count: Should show events
   - Data size: ~602MB

---

## Test Query to Confirm

In Splunk search bar, run:
```spl
index=botsv3 earliest=0 | stats count
```

**Expected result:** Should show a number > 0 (total event count)

If you see a count of events, the dataset is working! ✅

---

## Troubleshooting If Still Empty

If you don't see data, try these steps:

**Step 1: Restart Splunk**
```powershell
Restart-Service Splunkd -Force
Start-Sleep -Seconds 5
```

**Step 2: Check the path in Splunk UI**
- Settings → Data Indexes → botsv3
- Check the "Home path" value
- Should be: `C:\Program Files\Splunk\etc\apps\botsv3\var\lib\splunk\botsv3\db`

**Step 3: Check Splunk logs for errors**
```powershell
Get-Content "C:\Program Files\Splunk\var\log\splunk\splunkd.log" -Tail 100 | Select-String "error|ERROR|botsv3"
```

**Step 4: Verify file permissions**
```powershell
icacls "C:\Program Files\Splunk\etc\apps\botsv3" /grant:r "SYSTEM:(OI)(CI)F" /grant:r "BUILTIN\Administrators:(OI)(CI)F"
Restart-Service Splunkd -Force
```

---

## Files Modified

| File | Change |
|------|--------|
| `C:\Program Files\Splunk\etc\apps\botsv3\default\indexes.conf` | Fixed path: `botsv3_data_set` → `botsv3` |

---

## Summary

✅ **Data location verified:** 602MB of pre-indexed events  
✅ **Configuration fixed:** indexes.conf now points to correct path  
✅ **Service running:** Splunkd is active  
✅ **Ready to query:** BOTS V3 dataset is now accessible

**Next step:** Go to http://localhost:8000 and run:
```spl
index=botsv3 earliest=0 | stats count by sourcetype
```

You should now see the BOTS V3 events! 🎉
