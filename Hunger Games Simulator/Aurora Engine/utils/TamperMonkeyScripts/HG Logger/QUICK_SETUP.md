# Quick Setup Guide - HG Logger

## 🚀 5-Minute Setup

### 1. Install TamperMonkey Extension
Choose your browser:
- **Chrome**: https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo
- **Firefox**: https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/
- **Edge**: https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd

### 2. Install Collector Script
```
1. Open HG_Logger_Collector.user.js in text editor
2. Copy all contents (Ctrl+A → Ctrl+C)
3. Click TamperMonkey icon → Dashboard
4. Click "+" button (new script)
5. Paste contents (Ctrl+V)
6. Save (Ctrl+S)
7. Close tab
```

### 3. Install Dashboard Script
```
1. Open HG_Logger_Dashboard.user.js in text editor
2. Copy all contents (Ctrl+A → Ctrl+C)
3. Click TamperMonkey icon → Dashboard
4. Click "+" button (new script)
5. Paste contents (Ctrl+V)
6. Save (Ctrl+S)
7. Close tab
```

### 4. Enable File:// Access
```
1. Click TamperMonkey icon → Dashboard
2. Click "Settings" tab
3. Scroll to "Security"
4. Check "Allow scripts to run on file:// URLs"
5. Click "Save"
```

### 5. Open Dashboard
```
Double-click hg-logger-dashboard.html
```

You should see the dashboard UI with purple gradient!

### 6. Test It
```
1. Visit any website (e.g., google.com)
2. Open browser console (F12)
3. Type: console.log('Hello HG Logger!')
4. Return to dashboard
5. Click 🔄 Refresh
6. See your log!
```

## ✅ Verification

### Check Collector is Working:
```javascript
// On any website, open console (F12) and run:
HGCollectorDebug.getStats()

// Should return something like:
// { totalSites: 2, totalLogs: 15, lastUpdate: "2025-01-01T12:00:00.000Z" }
```

### Check Dashboard is Working:
```
1. Dashboard should show gradient background (purple)
2. Top stats should show: Sites, Total Logs, Displayed
3. Dropdown should have "All Sites" at minimum
4. If you visited sites, dropdown should list them
```

## 🔧 Common Issues

### "Dashboard script not detected" warning
**Fix:**
1. Make sure HG_Logger_Dashboard.user.js is installed
2. Check it's enabled (green toggle in TamperMonkey dashboard)
3. Verify Settings → Security → Allow file:// URLs is checked
4. Refresh dashboard page (Ctrl+R)

### Dropdown says "All Sites" only
**Fix:**
1. Visit some websites with collector active
2. Open console on those sites and type something
3. Return to dashboard and click 🔄 Refresh
4. Sites should now appear in dropdown

### No logs showing
**Fix:**
1. Make sure both scripts are enabled (green toggles)
2. Visit a website and check console works
3. Run `HGCollectorDebug.getCurrentSiteLogs()` in website console
4. Should return array of log entries
5. If empty, try typing `console.log('test')` in console
6. Return to dashboard and refresh

### CSP Errors
This should NOT happen with the new architecture. If you see CSP errors:
- Make sure you're NOT using the old monolithic TamperMonkeyScript.js
- Disable any old scripts in TamperMonkey dashboard
- Only the new Collector and Dashboard scripts should be active

## 🎯 Quick Usage

### Capture Logs
Just visit websites normally. Collector runs automatically!

### View Logs
Open `hg-logger-dashboard.html` anytime to see aggregated logs.

### Filter Logs
- **Site**: Select specific website from dropdown
- **Method**: Choose log/info/warn/error/debug
- **Search**: Type keywords to search content

### Export Logs
Click 💾 Export button → Downloads JSON file

### Clear Logs
Click 🗑️ Clear All → Confirms → Deletes everything

### Auto-Refresh
Click ⚙️ Settings → Check "Auto-refresh" → Logs update every 2 seconds

## 📊 What Gets Captured

The collector captures:
- ✅ console.log()
- ✅ console.info()
- ✅ console.warn()
- ✅ console.error()
- ✅ console.debug()
- ✅ console.clear() (logs "[Console was cleared]")
- ✅ Uncaught errors (window.onerror)
- ✅ Unhandled promise rejections

It does NOT capture:
- ❌ Browser violations (not console calls)
- ❌ CSP errors (not console calls)
- ❌ Network errors shown in console (not console calls)
- ❌ DevTools-specific messages

Note: Only actual `console.*()` calls can be captured by JavaScript. Other console messages come from the browser itself and cannot be hooked.

## 🎨 Color Coding

Logs are automatically colored by type:
- **log** = Gray border
- **info** = Blue border  
- **warn** = Yellow border + yellow background
- **error** = Red border + red background
- **debug** = Purple border

Keywords are highlighted:
- "error" = Red
- "warning" = Orange
- "success" = Blue
- "info" = Green

Configure in Settings (⚙️ button).

## 💾 Storage

Logs are stored in TamperMonkey's GM storage:
- Shared across all browser tabs
- Persists after browser restart
- Survives page refreshes
- Max 1000 logs per site (oldest removed)
- All data stays local (never sent to server)

## 🎓 Pro Tips

1. **Bookmark Dashboard**: Bookmark `hg-logger-dashboard.html` for quick access
2. **Use Search**: Instead of scrolling, search for keywords
3. **Export Regularly**: Click 💾 Export to backup important logs
4. **Filter by Site**: Use dropdown to focus on one website
5. **Auto-Refresh**: Enable in Settings when actively debugging
6. **Clear Old Logs**: Click 🗑️ Clear All periodically to free space

## 🔍 Debug Commands

### On Websites (Collector):
```javascript
HGCollectorDebug.getStats()           // View stats
HGCollectorDebug.getCurrentSiteLogs() // View logs for current site
HGCollectorDebug.getAllLogs()         // View all logs (all sites)
HGCollectorDebug.clearCurrentSite()   // Clear logs for current site
HGCollectorDebug.clearAllLogs()       // Clear everything
```

### On Dashboard:
All data visible in UI. Or in console:
```javascript
// View raw data
GM_getValue('hg_logger_all_logs')  // All logs
GM_getValue('hg_logger_stats')     // Statistics
```

## 📞 Need Help?

If you're still stuck:
1. Check browser console (F12) for error messages
2. Verify both scripts are installed and enabled
3. Try disabling other TamperMonkey scripts (might conflict)
4. Test on a simple site like `example.com` first
5. Contact developer with screenshots of errors

---

**You're all set!** Visit websites, capture logs, view in dashboard. Happy logging! 🎉
