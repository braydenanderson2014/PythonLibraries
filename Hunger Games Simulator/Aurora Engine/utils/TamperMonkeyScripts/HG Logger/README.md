# HG Logger - Two-Script Architecture

A powerful TamperMonkey-based console logger that captures logs from all websites and displays them in a centralized dashboard.

## 🎯 Overview

The HG Logger system consists of two separate scripts:

1. **Collector Script** - Lightweight script that runs on all websites to capture console logs
2. **Dashboard Script** - Full-featured UI that displays aggregated logs from all sites

This architecture solves several problems:
- ✅ No CSP (Content Security Policy) issues
- ✅ Minimal performance impact on websites
- ✅ Centralized view of all logs
- ✅ Easy dropdown population
- ✅ No duplicate panels in iframes

## 📦 Files

```
HG Logger/
├── HG_Logger_Collector.user.js   # Lightweight collector (runs on all sites)
├── HG_Logger_Dashboard.user.js   # Dashboard UI (runs on dashboard page)
├── hg-logger-dashboard.html      # Dashboard page
└── README.md                     # This file
```

## 🚀 Installation

### Step 1: Install TamperMonkey

If you don't have TamperMonkey installed:
- Chrome: https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/
- Edge: https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd

### Step 2: Install Both Scripts

1. **Install Collector Script:**
   - Open `HG_Logger_Collector.user.js` in a text editor
   - Copy all contents
   - Click TamperMonkey icon → Dashboard
   - Click "+" tab to create new script
   - Paste contents and save (Ctrl+S or Cmd+S)

2. **Install Dashboard Script:**
   - Open `HG_Logger_Dashboard.user.js` in a text editor
   - Copy all contents
   - Click TamperMonkey icon → Dashboard
   - Click "+" tab to create new script
   - Paste contents and save (Ctrl+S or Cmd+S)

### Step 3: Enable Scripts

Make sure both scripts are enabled (toggle switch should be green) in the TamperMonkey dashboard.

### Step 4: Grant Permissions

- **Collector**: Should have permission to run on `*://*/*` (all websites)
- **Dashboard**: Should have permission to run on `file:///*` URLs

If you get permission errors, check TamperMonkey settings → Security → Allow scripts to run on `file://` URLs

## 📊 Usage

### 1. Open Dashboard

Open `hg-logger-dashboard.html` in your browser:
- Double-click the file, OR
- Drag and drop into browser window, OR
- Use browser's File → Open menu

You should see the dashboard UI with gradient background and controls.

### 2. Capture Logs

Visit any website with the collector script active. The collector will automatically:
- Hook into `console.log`, `console.info`, `console.warn`, `console.error`, `console.debug`
- Capture all console output
- Store logs in TamperMonkey storage (shared across all pages)
- Track stats (number of sites, total logs)

### 3. View Logs in Dashboard

Return to the dashboard page (`hg-logger-dashboard.html`) to see all captured logs:

**Filters:**
- **Site dropdown** - Filter by specific website (e.g., "www.imdb.com")
- **Method dropdown** - Filter by log type (log, info, warn, error, debug)
- **Search box** - Search log content and URLs

**Controls:**
- 🔄 **Refresh** - Manually refresh logs
- ⚙️ **Settings** - Configure auto-refresh, max logs, timestamps
- 💾 **Export** - Download all logs as JSON file
- 🗑️ **Clear All** - Delete all captured logs

### 4. Color Coding

Logs are automatically color-coded by type:
- **log** - Gray
- **info** - Blue
- **warn** - Yellow (with yellow background)
- **error** - Red (with red background)
- **debug** - Purple

Keywords like "error", "warning", "success", "info" are highlighted in the log content.

## 🔧 Configuration

Click the ⚙️ **Settings** button in the dashboard to configure:

### Display Options
- **Auto-refresh** - Automatically reload logs every N milliseconds
- **Refresh interval** - How often to refresh (default: 2000ms = 2 seconds)
- **Max logs to display** - Limit displayed logs to prevent performance issues (default: 500)
- **Color coding** - Enable/disable keyword highlighting

### Timestamp Format
- **ISO** - `2025-01-01T12:00:00.000Z` (precise, sortable)
- **Local** - `1/1/2025, 12:00:00 PM` (readable, localized)

## 🛠️ Advanced Features

### Debug Console

Both scripts expose debug interfaces:

**Collector (on any website):**
```javascript
// Open browser console and run:
HGCollectorDebug.getStats()              // View capture statistics
HGCollectorDebug.getCurrentSiteLogs()    // View logs for current site
HGCollectorDebug.getAllLogs()            // View all captured logs
HGCollectorDebug.clearCurrentSite()      // Clear logs for current site
HGCollectorDebug.clearAllLogs()          // Clear all logs
```

**Dashboard (on dashboard page):**
- All data is visible in the UI
- Use browser console to inspect `GM_getValue('hg_logger_all_logs')`

### Storage Format

Logs are stored in TamperMonkey GM storage with this structure:

```javascript
{
  "www.imdb.com": [
    {
      "id": "abc123xyz",
      "method": "log",
      "args": ["Hello", "world"],
      "host": "www.imdb.com",
      "href": "https://www.imdb.com/title/tt0133093/",
      "origin": "https://www.imdb.com",
      "timestamp": "2025-01-01T12:00:00.000Z",
      "userAgent": "Mozilla/5.0..."
    },
    // ... more logs
  ],
  "www.youtube.com": [
    // ... logs from YouTube
  ]
}
```

### Blacklist

The collector has a built-in blacklist to skip ad/tracking domains:
- `amazon-adsystem.com`
- `googlesyndication.com`
- `doubleclick.net`
- `googletagmanager.com`
- `googletagservices.com`
- `google-analytics.com`
- `facebook.net`
- `fbcdn.net`

Edit `HG_Logger_Collector.user.js` line 20-28 to customize.

### Log Limits

- **Per-site limit**: 1000 logs per site (oldest are discarded)
- **Display limit**: 500 logs shown in dashboard (configurable)

These limits prevent excessive memory usage.

## 🐛 Troubleshooting

### Dashboard not showing
1. Check that `HG_Logger_Dashboard.user.js` is installed and enabled
2. Verify TamperMonkey has permission for `file:///*` URLs
3. Try refreshing the page (Ctrl+R or Cmd+R)
4. Check browser console for errors

### Logs not being captured
1. Check that `HG_Logger_Collector.user.js` is installed and enabled
2. Open website's console and run `HGCollectorDebug.getStats()` to verify
3. Check if site is blacklisted (see blacklist section above)
4. Try a simple site like `example.com` first

### Dropdown not populating
1. Make sure you've visited some websites with collector active
2. Click 🔄 Refresh button in dashboard
3. Check stats at top of dashboard (should show "Sites: X")
4. Try `HGCollectorDebug.getAllLogs()` in collector to verify data exists

### Performance issues
1. Reduce "Max logs to display" in settings (try 100 or 200)
2. Clear old logs with 🗑️ Clear All button
3. Use filters to narrow down displayed logs
4. Disable auto-refresh if not needed

### CSP errors
The two-script architecture should prevent CSP errors. If you still see them:
- Make sure you're using the dashboard script on `hg-logger-dashboard.html`, NOT on random websites
- The collector has no UI and should never trigger CSP errors

## 📝 Differences from Old Monolithic Script

### Old Script (TamperMonkeyScript.js)
- ❌ 2447 lines in one file
- ❌ UI runs on every website (CSP issues)
- ❌ Dropdown struggles with multi-site data
- ❌ Iframe detection needed
- ❌ Performance overhead on all sites

### New Two-Script Architecture
- ✅ Separated concerns (200 line collector + 1000 line dashboard)
- ✅ No UI on websites (no CSP issues)
- ✅ Dropdown naturally populated from storage
- ✅ No iframe problems (collector has no UI)
- ✅ Minimal performance impact

## 🔄 Migration from Old Script

If you were using the old `TamperMonkeyScript.js`:

1. Export your old logs (if you want to keep them):
   - Open the old script's UI
   - Click "Export Logs" button
   - Save JSON file

2. Disable the old script in TamperMonkey dashboard

3. Install both new scripts (Collector + Dashboard)

4. (Optional) Import old logs:
   - Currently no automated import
   - Contact developer if you need migration assistance

The new system will start fresh and capture logs going forward.

## 📄 License

Copyright © 2025 Otter Logic LLC. All rights reserved.

## 🤝 Support

For issues, questions, or feature requests, contact the developer.

---

**Version:** 1.0  
**Last Updated:** January 2025  
**Architecture:** Two-Script Collector/Dashboard Pattern
