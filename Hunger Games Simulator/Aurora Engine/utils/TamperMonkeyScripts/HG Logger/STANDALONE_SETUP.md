# HG Logger - Standalone Dashboard Setup Guide

## ✅ What's Working

The **standalone dashboard** (`hg-logger-dashboard-standalone.html`) is now fully functional and requires:
- ✅ Collector script running on websites
- ✅ XAMPP (or any local HTTP server) serving the dashboard
- ✅ No TamperMonkey script needed for the dashboard
- ✅ Direct localStorage access (no scope isolation issues)

## 🚀 Quick Start

### 1. Start XAMPP
- Launch XAMPP Control Panel
- Start Apache
- Verify it's running on `http://localhost` (default port 80) or `http://localhost:PORT`

### 2. Access the Dashboard
Open in your browser:
```
http://localhost/Aurora Engine/utils/TamperMonkeyScripts/HG Logger/hg-logger-dashboard-standalone.html
```

**Note:** If you moved files to a different location in htdocs, adjust the path accordingly.

### 3. Verify Collector is Running
- Visit any HTTPS website (e.g., https://www.example.com, https://www.imdb.com)
- Open DevTools (F12) → Console
- You should see messages like:
  ```
  [HG COLLECTOR] Initializing on example.com
  [HG COLLECTOR] CAPTURED log with 2 args
  [HG COLLECTOR] Saved X logs for example.com
  ```

### 4. View Logs in Dashboard
- Return to the dashboard page (refresh it)
- You should see:
  - ✅ Total sites count
  - ✅ Total logs count
  - ✅ Log entries in the list
  - ✅ Site/method filters populated

## 📊 Dashboard Features

### Statistics Panel (Top)
- **Sites** - Number of websites with captured logs
- **Logs** - Total number of console entries captured
- **Last Update** - When logs were last recorded

### Controls
- 🔄 **Refresh** - Manually reload logs from storage
- 📥 **Export** - Download all logs as JSON file
- 🗑️ **Clear All** - Delete all logs (cannot be undone)

### Filters
- **Site** - Filter by specific website domain
- **Method** - Filter by console method (log, info, warn, error, debug)
- **Search** - Search across all log content

### Display
- Logs shown newest first (reverse chronological)
- Color-coded by method type
- Auto-refreshes every 2 seconds
- Shows up to 500 logs at a time

### Debug Info (Bottom)
Click "Show Raw Storage Data" to inspect:
- All localStorage keys
- Site breakdown
- Stats data
- Storage access status

## 🔍 Troubleshooting

### Dashboard shows "No logs captured yet"
1. **Check Collector is running:**
   - Visit a website with Collector installed
   - Open DevTools console
   - Look for `[HG COLLECTOR]` messages
   - If you see `[HG COLLECTOR] Initialized on` → ✅ Collector is working

2. **Check localStorage has data:**
   - In Dashboard, click "Show Raw Storage Data"
   - Look for `"hg_logger_all_logs"` key
   - If missing or empty, logs haven't been captured yet

3. **Wait for auto-refresh:**
   - Dashboard auto-refreshes every 2 seconds
   - Give it a moment after visiting a website
   - Or click 🔄 Refresh button manually

### Dashboard shows stats but no log entries
- This means localStorage has data but it's not displaying
- Check browser console for JavaScript errors
- Try clicking 🔄 Refresh button
- Check Debug Info section for storage access status

### XAMPP not serving files correctly
- Verify XAMPP Apache is running (green indicator)
- Check correct port in browser URL (default: 80)
- Verify file path is correct in URL
- Try accessing a simple file first (e.g., `http://localhost/`)

### Collector not capturing logs
- Verify `HG_Logger_Collector.user.js` is installed in TamperMonkey
- Check TamperMonkey icon shows script is enabled (green)
- Try on different websites (some sites may block scripts)
- Check website's Content Security Policy (CSP) isn't blocking the script

## 📝 How It Works

### Collector Script Flow
```
1. Website loads (HTTPS page)
   ↓
2. Collector script injects into page context
   ↓
3. Hooks console.log, console.info, console.warn, console.error, console.debug
   ↓
4. When console method is called:
   - Serializes arguments
   - Creates log entry with metadata (timestamp, host, method, etc.)
   - Stores to page's localStorage: hg_logger_all_logs
   - Updates stats: hg_logger_stats
   ↓
5. Logs persist in browser's localStorage
```

### Standalone Dashboard Flow
```
1. Dashboard HTML served via XAMPP (HTTP)
   ↓
2. Page loads, JavaScript executes
   ↓
3. Reads localStorage keys: hg_logger_all_logs, hg_logger_stats
   ↓
4. Can access logs because:
   - Both running in same browser context (HTTP localhost)
   - No scope isolation (not file:// vs HTTPS issue)
   - Direct localStorage access works
   ↓
5. Displays logs in UI with filtering/search
```

### Storage Structure
```json
{
  "hg_logger_all_logs": {
    "example.com": [
      {
        "id": "timestamp+random",
        "method": "log|info|warn|error|debug",
        "args": ["serialized", "arguments"],
        "host": "example.com",
        "timestamp": "ISO-8601 string",
        "href": "full URL",
        "origin": "https://example.com"
      }
    ]
  },
  "hg_logger_stats": {
    "totalSites": 1,
    "totalLogs": 150,
    "lastUpdate": "ISO-8601 string",
    "siteBreakdown": { "example.com": 150 }
  }
}
```

## 🎯 Key Differences: Standalone vs TamperMonkey Dashboard

| Feature | Standalone | TamperMonkey |
|---------|-----------|------------|
| Requires TamperMonkey | ❌ No | ✅ Yes |
| Access Method | HTTP via XAMPP | File:// or Localhost |
| Storage Scope | Direct localStorage | unsafeWindow.localStorage |
| UI Loading | Instant | Waits for TamperMonkey |
| Initialization | Immediate on load | 3-second loading delay |
| Setup Complexity | Low (just open URL) | Medium (needs script install) |

## 💾 Storage Persistence

- Logs persist in browser localStorage
- Cleared when browser data is cleared
- Survives page reload
- Does NOT survive incognito/private mode (separate storage)
- Each domain has separate storage (https://example.com vs https://another.com)

## 🛡️ Privacy Notes

- All logs stored in **browser localStorage only**
- No data sent to external servers
- No cookies created
- Logs automatically cleared if you:
  - Click "🗑️ Clear All" in dashboard
  - Clear browser cache/cookies
  - Switch to private/incognito mode

## ⚙️ Configuration

Current defaults in `hg-logger-dashboard-standalone.html`:
- Auto-refresh interval: 2000ms (2 seconds)
- Max logs per site: 1000
- Max logs displayed: 500
- Refresh on load: Yes

To change these, edit the JavaScript in the HTML file around line 500+.

## 📁 Files

```
HG Logger/
├── HG_Logger_Collector.user.js          # Install in TamperMonkey (all sites)
├── HG_Logger_Dashboard.user.js          # (Optional, for TamperMonkey dashboard)
├── hg-logger-dashboard.html             # (Legacy, requires TamperMonkey script)
├── hg-logger-dashboard-standalone.html  # ✅ USE THIS ONE (works with XAMPP)
└── README.md                            # Original documentation
```

## 🎓 Next Steps

### To use the Dashboard
1. ✅ Keep XAMPP running
2. ✅ Keep Collector script installed in TamperMonkey
3. ✅ Access dashboard via `http://localhost/...`
4. ✅ Visit websites to capture logs
5. ✅ View in dashboard

### To export logs
1. Click 📥 **Export** button
2. JSON file downloads automatically
3. Contains all logs with metadata

### To clear everything
1. Click 🗑️ **Clear All** button
2. Confirm when prompted
3. All logs deleted from storage

---

**Setup Date:** November 14, 2025
**Working Configuration:** Standalone Dashboard + XAMPP + Collector Script
**Status:** ✅ Fully Functional
