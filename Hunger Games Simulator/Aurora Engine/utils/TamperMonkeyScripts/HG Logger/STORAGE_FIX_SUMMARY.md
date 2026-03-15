# HG Logger - Storage Architecture Fix (November 14, 2025)

## The Problem

The original system had a **storage scope isolation issue**:
- **Collector** (running on `https://hungergames.com`) stored logs to that domain's `localStorage`
- **Dashboard** (running on `localhost`) could only access `localhost`'s `localStorage`
- These are **completely separate storage partitions** — no cross-access possible

This meant logs captured on HTTPS pages were invisible to the Dashboard on localhost.

## The Solution

Switch from **origin-specific localStorage** to **TamperMonkey's shared storage**:

### Before (Broken):
```javascript
// Collector (on https://hungergames.com)
const storage = localStorage;  // → https://hungergames.com's storage only
storage.setItem(key, value);

// Dashboard (on http://localhost)
const storage = localStorage;  // → http://localhost's storage only (can't see collector's data)
storage.getItem(key);
```

### After (Fixed):
```javascript
// Collector (on https://hungergames.com)
GM_setValue(key, value);  // → TamperMonkey's SHARED storage (accessible everywhere)

// Dashboard (on http://localhost)
GM_getValue(key);  // → TamperMonkey's SHARED storage (sees collector's data)
```

## Files Changed

### 1. HG_Logger_Collector.user.js (Version 1.1)
**Changes:**
- Changed from `localStorage` → `GM_getValue/GM_setValue`
- All log storage now goes to TamperMonkey's shared storage
- Added `@grant GM_setValue` and `@grant GM_getValue` permissions
- Created `window.HGCollectorBridge` object to pass logs from page context to TamperMonkey context
- Updated all storage operations: `saveLogs()`, `loadLogs()`, `updateStats()`

**Key improvement:** Data stored here is now accessible to Dashboard regardless of origin.

### 2. HG_Logger_Dashboard.user.js (Version 1.1)
**Changes:**
- Added `@grant GM_getValue` permission
- Created helper functions: `loadLogsFromGMStorage()`, `loadStatsFromGMStorage()`, `loadConfigFromGMStorage()`
- Updated `loadLogs()` to read from `GM_getValue()` instead of `localStorage.getItem()`
- Now reads from same TamperMonkey shared storage as Collector

**Key improvement:** Dashboard now pulls data from the shared storage where Collector stores it.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         HTTPS Websites (HTTPS)          │
│     (e.g., https://hungergames.com)     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   HG Logger Collector Script    │   │
│  │  (@match *:///* on all sites)   │   │
│  │                                 │   │
│  │  - Hooks console.log/info/etc   │   │
│  │  - Captures all output          │   │
│  │  - Stores via: GM_setValue()    │── │
│  │                                 │   │
│  └─────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
                   │ GM_setValue/GM_getValue
                   │ (TamperMonkey Shared Storage)
                   │
                   ▼
    ┌──────────────────────────────┐
    │   TamperMonkey Storage       │
    │  (Shared Across All Origins) │
    │                              │
    │ hg_logger_all_logs: {        │
    │   "site1.com": [...],        │
    │   "site2.com": [...]         │
    │ }                            │
    │ hg_logger_stats: {...}       │
    └──────────────────────────────┘
                   ▲
                   │ GM_getValue()
                   │
    ┌──────────────────────────────┐
    │   HG Logger Dashboard        │
    │  (@match localhost/file://)  │
    │                              │
    │  - Reads via: GM_getValue()  │
    │  - Renders log UI            │
    │  - Filters by site           │
    │                              │
    └──────────────────────────────┘
```

## How to Use

### 1. Update Collector Script
```
1. Open HG_Logger_Collector.user.js in TamperMonkey
2. Copy entire contents
3. Paste into new TamperMonkey script
4. Save (Ctrl+S)
5. Make sure it's enabled (toggle switch green)
```

### 2. Update Dashboard Script
```
1. Open HG_Logger_Dashboard.user.js in TamperMonkey
2. Copy entire contents
3. Paste into new TamperMonkey script
4. Save (Ctrl+S)
5. Make sure it's enabled (toggle switch green)
```

### 3. Use Dashboard
```
Option A: File URL (with TamperMonkey)
- Open hg-logger-dashboard.html directly in browser
- TamperMonkey dashboard script runs automatically

Option B: HTTP via XAMPP
- Open http://localhost/...path.../hg-logger-dashboard.html
- TamperMonkey dashboard script runs automatically
```

### 4. Capture Logs
```
1. Visit any HTTPS website
2. Collector automatically hooks console
3. When you console.log(), it's captured
4. Data stored via GM_setValue() to shared storage
5. Return to Dashboard
6. Click Refresh or wait 2 seconds (auto-refresh)
7. Logs appear grouped by site
```

## Verification

### Check Collector is working:
1. Visit any HTTPS website
2. Open DevTools (F12) → Console
3. Look for: `[HG COLLECTOR] Initializing on domain.com`
4. When console.log is called: `[HG COLLECTOR] CAPTURED log with X args`
5. When saved: `[HG COLLECTOR] Saved X logs for domain.com`

### Check Dashboard can see logs:
1. Open Dashboard (`hg-logger-dashboard.html`)
2. Check stats at top:
   - **Sites** should show > 0 (number of visited sites)
   - **Logs** should show > 0 (total captured entries)
3. Check Site filter dropdown populates with visited domains
4. Logs should appear in list, grouped and filterable by site

### Debug:
```javascript
// In console on any website:
HGCollectorDebug.getStats()         // Get capture statistics
HGCollectorDebug.getAllLogs()       // Get all captured logs
HGCollectorDebug.getCurrentSiteLogs() // Get logs for this site

// In Dashboard console:
// Data now comes from TamperMonkey shared storage via GM_getValue()
```

## Advantages of This Approach

✅ **Origin-independent** - Logs from HTTPS pages visible in localhost Dashboard
✅ **TamperMonkey native** - Uses native storage system both scripts already required
✅ **No workarounds** - No need for complex cross-origin hacks
✅ **Simple** - Both scripts use same storage keys and format
✅ **Shared** - If multiple Dashboard instances open, all see same data
✅ **Persistent** - Survives page reloads and browser refreshes
✅ **Automatic** - No manual sync needed between scripts

## Limitations

⚠️ **TamperMonkey only** - Both scripts must be installed as TamperMonkey scripts
⚠️ **Browser local** - Data doesn't sync across different browsers
⚠️ **Per-profile** - Each browser profile has separate TamperMonkey storage
⚠️ **Manual clear** - Must click "Clear All" to delete logs (not automatic)

## Files

- `HG_Logger_Collector.user.js` (v1.1) - Captures logs, stores to GM storage
- `HG_Logger_Dashboard.user.js` (v1.1) - Reads from GM storage, displays UI
- `hg-logger-dashboard.html` - HTML placeholder (UI injected by TamperMonkey script)
- `hg-logger-dashboard-standalone.html` - Alternative standalone version (for localhost)

---

**Status:** ✅ Fixed
**Date:** November 14, 2025
**Problem:** Storage scope isolation
**Solution:** Use TamperMonkey's shared GM storage instead of origin-specific localStorage
