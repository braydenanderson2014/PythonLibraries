// ==UserScript==
// @name HG Logger (CSP-compliant, SPA-aware, configurable sites)
// @namespace http://tampermonkey.net/
// @version 2.0
// @description Persist console + errors globally across all routes/paths, survives reloads, navigation to root, & console.clear, SPA-aware, with copy/download UI. CSP-compliant without eval() or unsafe-inline.
// @author Otter Logic LLC
// @match *://*/*
// @grant GM_setValue
// @grant GM_getValue
// @grant unsafeWindow
// @run-at document-start
// ==/UserScript==

(function() {
  'use strict';

  // ===== SAFE LOGGING FUNCTION (MUST BE FIRST) =====
  let safeLog = console.log.bind(console); // Initialize with original console.log

  safeLog('[HG LOGGER] Script starting...');

  // ===== CONFIG MANAGEMENT =====
  function getDomainList() {
    return GM_getValue('hg_logger_domains', []);
  }

  function setDomainList(list) {
    GM_setValue('hg_logger_domains', list);
  }

  function getBlacklist() {
    return GM_getValue('hg_logger_blacklist', []);
  }

  function setBlacklist(list) {
    GM_setValue('hg_logger_blacklist', list);
  }

  // ===== CONFIGURATION FUNCTIONS =====
  function getMaxEntries() {
    return GM_getValue('hg_logger_max_entries', 20000);
  }

  function setMaxEntries(value) {
    GM_setValue('hg_logger_max_entries', Math.max(1000, Math.min(100000, parseInt(value) || 20000)));
  }

  function getAutoSaveInterval() {
    return GM_getValue('hg_logger_autosave_ms', 1500);
  }

  function setAutoSaveInterval(value) {
    GM_setValue('hg_logger_autosave_ms', Math.max(500, Math.min(10000, parseInt(value) || 1500)));
  }

  function getUITheme() {
    return GM_getValue('hg_logger_theme', 'dark');
  }

  function setUITheme(theme) {
    GM_setValue('hg_logger_theme', theme);
  }

  // ===== COLOR CONFIGURATION =====
  function getCustomKeywords() {
    return GM_getValue('hg_logger_keywords', {
      error: '#ff6b6b',
      warning: '#ffa726',
      success: '#4caf50',
      info: '#2196f3',
      debug: '#9c27b0'
    });
  }

  function setCustomKeywords(keywords) {
    GM_setValue('hg_logger_keywords', keywords);
  }

  function getMethodColors() {
    return {
      log: '#ffffff',
      info: '#4fc3f7',
      warn: '#ffb74d',
      error: '#f44336',
      debug: '#ab47bc',
      net: '#4caf50',
      clear: '#795548'
    };
  }

  function formatLineWithColors(e, showHost = false) {
    try {
      const prefix = e.source === 'hg-logger' ? '[HG LOGGER] ' : '';
      const hostPrefix = showHost ? `[${e.host || 'unknown'}] ` : '';
      
      // Safely process args
      let args = '';
      try {
        args = (e.args || []).map(a => {
          if (typeof a === 'string') return a;
          if (a === null) return 'null';
          if (a === undefined) return 'undefined';
          try {
            return JSON.stringify(a);
          } catch {
            return String(a);
          }
        }).join(' ');
      } catch {
        args = '[formatting error]';
      }
      
      // Safely process timestamp
      let timestamp = 'unknown';
      try {
        if (e.ts && typeof e.ts === 'string') {
          const parts = e.ts.split('T');
          if (parts.length > 1) {
            timestamp = parts[1].split('.')[0];
          }
        }
      } catch {
        timestamp = 'unknown';
      }
      
      // Safely process session
      let session = 'unknown';
      try {
        if (e.session && typeof e.session === 'string') {
          session = e.session.length >= 8 ? e.session.slice(0, 8) : e.session;
        }
      } catch {
        session = 'unknown';
      }
      
      // Get base color for method
      let baseColor = '#ffffff';
      try {
        const methodColors = getMethodColors();
        baseColor = methodColors[e.method] || '#ffffff';
      } catch {
        baseColor = '#ffffff';
      }
      
      // Safely apply custom keyword highlighting
      let highlightedArgs = args;
      try {
        const customKeywords = getCustomKeywords();
        Object.entries(customKeywords).forEach(([keyword, color]) => {
          try {
            // Escape special regex characters
            const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`\\b${escapedKeyword}\\b`, 'gi');
            if (regex.test(args)) {
              highlightedArgs = highlightedArgs.replace(regex, `<span style="color: ${color}; font-weight: bold;">$&</span>`);
            }
          } catch {
            // Skip this keyword if regex fails
          }
        });
      } catch {
        // Keep original args if highlighting fails
        highlightedArgs = args;
      }
      
      return {
        html: `<span style="color: #888;">[${timestamp}]</span> <span style="color: #666;">[${session}]</span> <span style="color: ${baseColor}; font-weight: bold;">[${(e.method || 'log').toUpperCase()}]</span> <span style="color: #ccc;">${hostPrefix}${prefix}</span><span style="color: ${baseColor};">${highlightedArgs}</span>`,
        text: `[${timestamp}] [${session}] [${(e.method || 'log').toUpperCase()}] ${hostPrefix}${prefix}${args}`
      };
    } catch (error) {
      // Fallback for any unexpected errors
      return {
        html: `<span style="color: #ff6b6b;">[ERROR] Failed to format log entry: ${error.message}</span>`,
        text: `[ERROR] Failed to format log entry: ${error.message}`
      };
    }
  }

  function showConfigDialog() {
    // Remove existing dialog if any
    const existingDialog = document.getElementById('hg-config-dialog');
    if (existingDialog) existingDialog.remove();

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'hg-config-dialog';
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.7);
      z-index: 2147483647;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: monospace;
      font-size: 14px;
    `;

    // Create dialog
    const dialog = document.createElement('div');
    dialog.style.cssText = `
      background: #1a1a1a;
      color: #eee;
      border: 2px solid #333;
      border-radius: 12px;
      width: 600px;
      max-height: 80vh;
      overflow-y: auto;
      box-shadow: 0 8px 32px rgba(0,0,0,0.8);
    `;

    dialog.innerHTML = `
      <div style="padding: 20px; border-bottom: 1px solid #333;">
        <h2 style="margin: 0 0 10px 0; color: #4a9eff;">⚙️ HG Logger Configuration</h2>
        <p style="margin: 0; opacity: 0.8;">Configure logging behavior and UI settings</p>
      </div>
      
      <div style="padding: 20px;">
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: bold;">📂 UI Display Domains</label>
          <textarea id="config-domains" style="width: 100%; height: 60px; background: #2a2a2a; color: #eee; border: 1px solid #555; border-radius: 4px; padding: 8px; font-family: monospace;" placeholder="example.com, *.github.com, localhost
Leave blank to show UI on all sites"></textarea>
          <small style="opacity: 0.7;">Comma-separated. Use *.domain.com for wildcards. Empty = all sites.</small>
        </div>

        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: bold;">🚫 Blacklisted Domains</label>
          <textarea id="config-blacklist" style="width: 100%; height: 60px; background: #2a2a2a; color: #eee; border: 1px solid #555; border-radius: 4px; padding: 8px; font-family: monospace;" placeholder="company-site.com, *.internal.com
Sites where logging is completely disabled"></textarea>
          <small style="opacity: 0.7;">Comma-separated. Use wildcards. Completely disables logging on these sites.</small>
        </div>

        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
          <div style="flex: 1;">
            <label style="display: block; margin-bottom: 8px; font-weight: bold;">📊 Max Log Entries</label>
            <input type="number" id="config-max-entries" style="width: 100%; background: #2a2a2a; color: #eee; border: 1px solid #555; border-radius: 4px; padding: 8px;" min="1000" max="100000" step="1000">
            <small style="opacity: 0.7;">Per site (1,000 - 100,000)</small>
          </div>
          
          <div style="flex: 1;">
            <label style="display: block; margin-bottom: 8px; font-weight: bold;">⚡ Auto-save Interval</label>
            <input type="number" id="config-autosave" style="width: 100%; background: #2a2a2a; color: #eee; border: 1px solid #555; border-radius: 4px; padding: 8px;" min="500" max="10000" step="100">
            <small style="opacity: 0.7;">Milliseconds (500 - 10,000)</small>
          </div>
        </div>

        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: bold;">🎨 UI Theme</label>
          <select id="config-theme" style="width: 100%; background: #2a2a2a; color: #eee; border: 1px solid #555; border-radius: 4px; padding: 8px;">
            <option value="dark">🌙 Dark (Default)</option>
            <option value="light">☀️ Light</option>
            <option value="blue">🔵 Blue</option>
            <option value="green">🟢 Green</option>
          </select>
        </div>

        <div style="background: #2a2a2a; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
          <h4 style="margin: 0 0 10px 0; color: #4a9eff;">📈 Current Statistics</h4>
          <div id="config-stats" style="font-family: monospace; font-size: 12px;"></div>
        </div>
      </div>
      
      <div style="padding: 20px; border-top: 1px solid #333; display: flex; gap: 10px; justify-content: flex-end;">
        <button id="config-reset" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">🗑️ Reset All Data</button>
        <button id="config-cancel" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Cancel</button>
        <button id="config-save" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">💾 Save & Apply</button>
      </div>
    `;

    overlay.appendChild(dialog);
    document.documentElement.appendChild(overlay);

    // Populate current values
    document.getElementById('config-domains').value = getDomainList().join(', ');
    document.getElementById('config-blacklist').value = getBlacklist().join(', ');
    document.getElementById('config-max-entries').value = getMaxEntries();
    document.getElementById('config-autosave').value = getAutoSaveInterval();
    document.getElementById('config-theme').value = getUITheme();

    // Update stats
    const allLogs = getAllLogs();
    const totalSites = Object.keys(allLogs).length;
    const totalLogs = Object.values(allLogs).flat().length;
    const currentSiteLogs = (allLogs[location.host] || []).length;
    
    document.getElementById('config-stats').innerHTML = `
      <div>🌐 Total Sites Logged: <strong>${totalSites}</strong></div>
      <div>📝 Total Log Entries: <strong>${totalLogs.toLocaleString()}</strong></div>
      <div>📍 Current Site Logs: <strong>${currentSiteLogs.toLocaleString()}</strong></div>
      <div>💾 Storage Used: <strong>~${Math.round(JSON.stringify(allLogs).length / 1024)}KB</strong></div>
    `;

    // Event handlers
    document.getElementById('config-cancel').addEventListener('click', () => {
      overlay.remove();
    });

    document.getElementById('config-reset').addEventListener('click', () => {
      if (confirm('⚠️ This will permanently delete ALL logged data from ALL sites!\n\nAre you absolutely sure?')) {
        setAllLogs({});
        localStorage.clear();
        alert('✅ All data has been reset.');
        overlay.remove();
        if (window.render) window.render();
      }
    });

    document.getElementById('config-save').addEventListener('click', () => {
      // Save all settings
      const domains = document.getElementById('config-domains').value
        .split(',').map(d => d.trim().toLowerCase()).filter(d => d);
      const blacklist = document.getElementById('config-blacklist').value
        .split(',').map(d => d.trim().toLowerCase()).filter(d => d);
      
      setDomainList(domains);
      setBlacklist(blacklist);
      setMaxEntries(document.getElementById('config-max-entries').value);
      setAutoSaveInterval(document.getElementById('config-autosave').value);
      setUITheme(document.getElementById('config-theme').value);

      overlay.remove();
      alert('✅ Configuration saved! Refreshing page to apply changes...');
      location.reload();
    });

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove();
      }
    });
  }

  function promptForConfigs() {
    showConfigDialog();
  }

  function showKeywordDialog() {
    // Remove existing dialog if any
    const existingDialog = document.getElementById('hg-keyword-dialog');
    if (existingDialog) existingDialog.remove();

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'hg-keyword-dialog';
    Object.assign(overlay.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      background: 'rgba(0,0,0,0.7)',
      zIndex: '2147483647',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'monospace',
      fontSize: '14px'
    });

    // Create dialog
    const dialog = document.createElement('div');
    Object.assign(dialog.style, {
      background: '#1a1a1a',
      color: '#eee',
      border: '2px solid #333',
      borderRadius: '12px',
      width: '500px',
      maxHeight: '80vh',
      overflowY: 'auto',
      boxShadow: '0 8px 32px rgba(0,0,0,0.8)'
    });

    // Create header
    const header = document.createElement('div');
    Object.assign(header.style, {
      padding: '20px',
      borderBottom: '1px solid #333'
    });

    const title = document.createElement('h2');
    Object.assign(title.style, {
      margin: '0 0 10px 0',
      color: '#4a9eff'
    });
    title.textContent = '🎨 Color Keywords Configuration';

    const subtitle = document.createElement('p');
    Object.assign(subtitle.style, {
      margin: '0',
      opacity: '0.8'
    });
    subtitle.textContent = 'Configure custom keyword highlighting colors';

    header.appendChild(title);
    header.appendChild(subtitle);
    dialog.appendChild(header);

    // Create content
    const content = document.createElement('div');
    Object.assign(content.style, {
      padding: '20px'
    });

    const currentKeywords = getCustomKeywords();
    const keywordInputs = {};

    Object.entries(currentKeywords).forEach(([keyword, color]) => {
      const row = document.createElement('div');
      Object.assign(row.style, {
        display: 'flex',
        gap: '10px',
        alignItems: 'center',
        marginBottom: '15px'
      });

      const keywordInput = document.createElement('input');
      keywordInput.type = 'text';
      keywordInput.value = keyword;
      keywordInput.placeholder = 'keyword';
      Object.assign(keywordInput.style, {
        flex: '1',
        background: '#2a2a2a',
        color: '#eee',
        border: '1px solid #555',
        borderRadius: '4px',
        padding: '8px'
      });

      const colorInput = document.createElement('input');
      colorInput.type = 'color';
      colorInput.value = color;
      Object.assign(colorInput.style, {
        width: '50px',
        height: '35px',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      });

      const removeBtn = document.createElement('button');
      removeBtn.textContent = '✕';
      Object.assign(removeBtn.style, {
        background: '#dc3545',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        padding: '8px 12px',
        cursor: 'pointer'
      });

      removeBtn.addEventListener('click', () => {
        row.remove();
      });

      keywordInputs[keyword] = { keywordInput, colorInput, row };

      row.appendChild(keywordInput);
      row.appendChild(colorInput);
      row.appendChild(removeBtn);
      content.appendChild(row);
    });

    // Add new keyword button
    const addBtn = document.createElement('button');
    addBtn.textContent = '+ Add Keyword';
    Object.assign(addBtn.style, {
      background: '#28a745',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      padding: '10px 15px',
      cursor: 'pointer',
      marginBottom: '20px'
    });

    addBtn.addEventListener('click', () => {
      const row = document.createElement('div');
      Object.assign(row.style, {
        display: 'flex',
        gap: '10px',
        alignItems: 'center',
        marginBottom: '15px'
      });

      const keywordInput = document.createElement('input');
      keywordInput.type = 'text';
      keywordInput.placeholder = 'new keyword';
      Object.assign(keywordInput.style, {
        flex: '1',
        background: '#2a2a2a',
        color: '#eee',
        border: '1px solid #555',
        borderRadius: '4px',
        padding: '8px'
      });

      const colorInput = document.createElement('input');
      colorInput.type = 'color';
      colorInput.value = '#ff6b6b';
      Object.assign(colorInput.style, {
        width: '50px',
        height: '35px',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      });

      const removeBtn = document.createElement('button');
      removeBtn.textContent = '✕';
      Object.assign(removeBtn.style, {
        background: '#dc3545',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        padding: '8px 12px',
        cursor: 'pointer'
      });

      removeBtn.addEventListener('click', () => {
        row.remove();
      });

      row.appendChild(keywordInput);
      row.appendChild(colorInput);
      row.appendChild(removeBtn);
      content.insertBefore(row, addBtn);
    });

    content.appendChild(addBtn);
    dialog.appendChild(content);

    // Create footer
    const footer = document.createElement('div');
    Object.assign(footer.style, {
      padding: '20px',
      borderTop: '1px solid #333',
      display: 'flex',
      gap: '10px',
      justifyContent: 'flex-end'
    });

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    Object.assign(cancelBtn.style, {
      background: '#6c757d',
      color: 'white',
      border: 'none',
      padding: '10px 20px',
      borderRadius: '6px',
      cursor: 'pointer'
    });

    const saveBtn = document.createElement('button');
    saveBtn.textContent = '💾 Save';
    Object.assign(saveBtn.style, {
      background: '#28a745',
      color: 'white',
      border: 'none',
      padding: '10px 20px',
      borderRadius: '6px',
      cursor: 'pointer'
    });

    cancelBtn.addEventListener('click', () => {
      overlay.remove();
    });

    saveBtn.addEventListener('click', () => {
      const newKeywords = {};
      content.querySelectorAll('div[style*="display: flex"]').forEach(row => {
        const keywordInput = row.querySelector('input[type="text"]');
        const colorInput = row.querySelector('input[type="color"]');
        if (keywordInput && colorInput && keywordInput.value.trim()) {
          newKeywords[keywordInput.value.trim()] = colorInput.value;
        }
      });
      setCustomKeywords(newKeywords);
      overlay.remove();
      if (window.render) window.render();
    });

    footer.appendChild(cancelBtn);
    footer.appendChild(saveBtn);
    dialog.appendChild(footer);

    overlay.appendChild(dialog);
    document.documentElement.appendChild(overlay);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove();
      }
    });
  }

  function domainMatches(currentHost, list) {
    currentHost = currentHost.toLowerCase();
    
    // If no patterns specified, return true for domain whitelist (show everywhere)
    // This will be handled by the caller context
    if (list.length === 0) {
      return true;
    }

    return list.some(pattern => {
      if (pattern.startsWith('*.')) {
        const baseDomain = pattern.slice(2);
        return currentHost === baseDomain || currentHost.endsWith('.' + baseDomain);
      }
      return currentHost === pattern;
    });
  }

  function shouldShowUIOnHost(host) {
    const domainList = getDomainList();
    
    // Empty domain list = show UI everywhere
    if (domainList.length === 0) {
      return true;
    }
    // Otherwise check if host matches domain list
    const matches = domainMatches(host, domainList);
    return matches;
  }

  function isHostBlacklisted(host) {
    const blacklist = getBlacklist();
    
    // Empty blacklist = nothing is blacklisted
    if (blacklist.length === 0) {
      return false;
    }
    // Otherwise check if host matches blacklist
    const matches = domainMatches(host, blacklist);
    return matches;
  }

  // Early check for blacklist
  const isBlacklisted = isHostBlacklisted(location.host);
  if (isBlacklisted) {
    safeLog('[HG LOGGER] Blacklisted site; skipping all operations to avoid interference.');
    return; // Exit completely - no hooks, no UI, no storage writes
  }

  // Check for ad/tracking domains that should be completely skipped
  const adDomains = ['amazon-adsystem.com', 'googlesyndication.com', 'doubleclick.net', 'googletagmanager.com', 'googletagservices.com', 'google-analytics.com'];
  const isAdDomain = adDomains.some(domain => location.host.includes(domain));
  
  if (isAdDomain) {
    safeLog('[HG LOGGER] Ad/tracking domain detected - skipping to avoid interference:', location.host);
    return; // Exit completely for ad domains
  }

  // Check for CSP-strict domains that should only do logging (no UI)
  const cspStrictDomains = ['github.com', 'googleapis.com'];
  const isCSPStrict = cspStrictDomains.some(domain => location.host.includes(domain));

  // Check if we're in an iframe - only show UI in top window
  const isInIframe = window !== window.top;
  const isTopWindow = window === window.top;

  // Proceed if not blacklisted or ad domain
  safeLog('[HG LOGGER] Script initializing...');
  safeLog('[HG LOGGER] Current location - host:', location.host, 'href:', location.href);
  safeLog('[HG LOGGER] User agent:', navigator.userAgent.substring(0, 50) + '...');
  safeLog('[HG LOGGER] Frame context - top window:', isTopWindow, 'iframe:', isInIframe);
  safeLog('[HG LOGGER] Proceeding with setup for host:', location.host);

  // ===== STORAGE HELPERS =====
  function getLocalLogs() {
    const key = `hg_logger_logs_${location.host}`;
    try {
      return JSON.parse(localStorage.getItem(key)) || [];
    } catch {
      return [];
    }
  }

  function setLocalLogs(logs) {
    const key = `hg_logger_logs_${location.host}`;
    try {
      localStorage.setItem(key, JSON.stringify(logs));
    } catch (e) {
      safeLog('[HG LOGGER] localStorage write failed:', e);
    }
  }

  function getAllLogs() {
    return GM_getValue('hg_logger_logs', {});
  }

  function setAllLogs(logsMap) {
    GM_setValue('hg_logger_logs', logsMap);
  }

  function syncLogsToGM() {
    const allLogs = getAllLogs();
    allLogs[location.host] = getLocalLogs();
    setAllLogs(allLogs);
  }

  // Cookie helpers for UI state (fallback)
  function setCookie(name, value, days = 30) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
    return match ? decodeURIComponent(match[2]) : null;
  }

  // Persist/restore UI state
  function saveUIState(panel) {
    const state = {
      right: panel.style.right,
      bottom: panel.style.bottom,
      collapsed: document.getElementById('tmc-body').style.display === 'none'
    };
    try {
      localStorage.setItem('hg_logger_ui_state', JSON.stringify(state));
    } catch {}
    setCookie('hg_logger_ui_state', JSON.stringify(state));
  }

  function restoreUIState(panel) {
    let state;
    try {
      state = JSON.parse(localStorage.getItem('hg_logger_ui_state'));
    } catch {}
    if (!state) state = JSON.parse(getCookie('hg_logger_ui_state') || '{}');
    if (state) {
      panel.style.right = state.right || '12px';
      panel.style.bottom = state.bottom || '12px';
      document.getElementById('tmc-body').style.display = state.collapsed ? 'none' : 'flex';
      document.getElementById('tmc-collapse').textContent = state.collapsed ? '▼' : '▲';
    }
  }

  // ===== CONSOLE HOOKS & LOGGING =====
  const nowISO = () => new Date().toISOString();
  const uuid4 = () => ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
  const sessionId = uuid4();
  const currentHost = location.host;
  let buffer = [];
  let writeTimer = null;
  // Use existing configuration functions
  let isCapturing = true; // Global toggle to disable hooks if needed
  
  // Store original console methods globally to fix scope issues
  let origConsole = {};
  
  // Rate limiting disabled for complete capture - user can filter via Colors menu
  let captureCount = 0;
  let lastReset = Date.now();
  let CAPTURE_LIMIT_PER_SECOND = 10000; // Very high limit - essentially disabled
  
  // Common noise patterns to filter out (reduced for better capture)
  const NOISE_PATTERNS = [
    /^[A-Z0-9_]{20,}$/,  // Very long all caps constants/IDs only
    /^[a-f0-9-]{36}$/i,  // UUIDs only
    /^\d{10,}$/,         // Very long pure numbers only
  ];

  function shouldSkipCapture(args) {
    // Rate limiting
    const now = Date.now();
    if (now - lastReset > 1000) {
      captureCount = 0;
      lastReset = now;
    }
    if (captureCount >= CAPTURE_LIMIT_PER_SECOND) {
      return true; // Skip due to rate limit
    }
    
    // Skip empty or null args
    if (!args || args.length === 0) return true;
    
    // Skip noise patterns (only very specific ones)
    const firstArg = String(args[0] || '');
    if (NOISE_PATTERNS.some(pattern => pattern.test(firstArg))) {
      return true;
    }
    
    // Removed short message filter - let everything through for better capture
    
    return false;
  }

  function toPlain(x) {
    try {
      if (x instanceof Error) return { name: x.name, message: x.message, stack: x.stack };
      if (typeof x === 'string') return x;
      return JSON.parse(JSON.stringify(x, (k, v) => (typeof v === 'function' ? '[Function]' : v)));
    } catch {
      return String(x) || '[unserializable]';
    }
  }

  const scheduleWrite = () => {
    if (writeTimer || !isCapturing) return;
    writeTimer = setTimeout(() => {
      let local = getLocalLogs().concat(buffer);
      const maxEntries = getMaxEntries();
      local = local.length > maxEntries ? local.slice(local.length - maxEntries) : local;
      setLocalLogs(local);
      syncLogsToGM();
      buffer = [];
      writeTimer = null;
      
      // Refresh UI if it exists
      if (window.render) {
        window.render();
      }
      
      // Also refresh dropdown directly in case render doesn't exist yet
      if (window.refreshFilterDropdown) {
        window.refreshFilterDropdown();
      }
    }, getAutoSaveInterval());
  };

  const push = (entry) => {
    // Use the isHGLogger flag passed from capture function
    const isHGLoggerMessage = entry.isHGLogger || false;
    
    // Set host information based on message source
    if (isHGLoggerMessage) {
      entry.host = 'HG Logger';  // Show as HG Logger for internal messages
      entry.source = 'hg-logger';
    } else {
      entry.host = currentHost;  // Use website host for website messages
    }
    
    entry.actualHost = location.host; // Current actual host
    entry.origin = location.origin;   // Current origin
    entry.href = location.href;       // Current URL
    entry.ts = nowISO();
    entry.session = sessionId;
    
    // Remove the isHGLogger flag from storage (we don't need to persist it)
    delete entry.isHGLogger;
    
    if (isCapturing) {
      buffer.push(entry);
      // Debug: Track buffer size and show host info
      if (buffer.length === 1) {
        // Use safeLog instead of orig.log to avoid scope issues
        safeLog('[HG LOGGER] First entry added to buffer:', entry.args[0]);
        safeLog('[HG LOGGER] Entry host info - currentHost:', currentHost, 'location.host:', location.host, 'location.href:', location.href);
      }
      scheduleWrite();
    }
  };

  // ===== INSTALL LOGGING HOOKS =====
  safeLog('[HG LOGGER] Starting hook installation...');
  try {
    safeLog('[HG LOGGER] Step 1: Creating methods array');
    const methods = ['log', 'info', 'warn', 'error', 'debug'];
    
    safeLog('[HG LOGGER] Step 2: Binding original console methods');
    // CRITICAL: Hook the PAGE's console (unsafeWindow.console), not TamperMonkey's isolated console
    const pageConsole = typeof unsafeWindow !== 'undefined' ? unsafeWindow.console : console;
    const orig = Object.fromEntries(methods.map(m => [m, pageConsole[m].bind(pageConsole)]));
    
    safeLog('[HG LOGGER] Step 3: Storing original methods globally');
    // Store original methods globally to fix scope issues
    origConsole = orig;
    
    safeLog('[HG LOGGER] Step 4: Updating safeLog');
    // Update safeLog to use original console.log (prevents loops)
    safeLog = orig.log;
    
    safeLog('[HG LOGGER] Step 5: Defining capture function');
    function capture(method, argsArr) {
      try {
        // Detect if this is an HG Logger internal message BEFORE any processing
        const isHGLoggerMessage = argsArr.length > 0 && 
                                 typeof argsArr[0] === 'string' && 
                                 argsArr[0].includes('[HG LOGGER]');
        
        // Skip our own internal system logs to prevent infinite loops
        if (isHGLoggerMessage) {
          // Skip all HG Logger system messages except user-initiated test messages
          if (!argsArr[0].includes('[HGTEST]') && !argsArr[0].includes('TEST:')) {
            return; // Skip HG Logger internal messages
          }
        }
        
        // Skip if capturing is disabled globally
        if (!isCapturing) return;
        
        // NO FILTERING - Capture everything!
        // Colors are applied in formatLineWithColors() based on Colors menu settings
        
        captureCount++; // Increment rate limit counter
        
        // Pass the isHGLoggerMessage flag to push
        push({ method, args: argsArr.map(toPlain), isHGLogger: isHGLoggerMessage });
      } catch (e) {
        // Silent error - don't log to avoid infinite loops
        // Error details available in HGLoggerDebug if needed
      }
    }

    safeLog('[HG LOGGER] Step 6: Installing hooks for console methods');
    // Install hooks for console methods with better error handling
    methods.forEach(m => {
      const originalMethod = origConsole[m];
      
      // Define the hook function
      const hookFunction = function(...args) {
        // First try to capture (before original to ensure we don't miss anything)
        try {
          capture(m, args);
        } catch (hookError) {
          safeLog('[HG LOGGER] Hook error for', m, ':', hookError);
        }
        
        // Then call original method to ensure normal console behavior
        try {
          return originalMethod.apply(this, args);
        } catch (originalError) {
          safeLog('[HG LOGGER] Original method error for', m, ':', originalError);
        }
      };
      
      // CRITICAL: Install the hook on the PAGE's console (unsafeWindow.console), not TamperMonkey's
      try {
        pageConsole[m] = hookFunction;
        safeLog(`[HG LOGGER] Installed hook for ${m} on page console`);
      } catch (installError) {
        safeLog('[HG LOGGER] Failed to install hook for', m, ':', installError);
      }
    });

    safeLog('[HG LOGGER] Step 7: Verifying hooks are installed');
    // Verify hooks are installed (using safeLog to avoid capture)
    safeLog('[HG LOGGER] Console hooks installed for methods:', methods);
    
    // Verify the hooks are actually working by checking if page console methods were replaced
    const hookVerification = methods.map(m => {
      return `${m}: ${pageConsole[m] !== origConsole[m] ? 'HOOKED' : 'FAILED'}`;
    });
    safeLog('[HG LOGGER] Hook verification (page console):', hookVerification.join(', '));
    
    safeLog('[HG LOGGER] Step 8: Creating debug object');
    // Create debug object EARLY to ensure it's available
    // Use unsafeWindow to make it accessible from the page's console (not just TamperMonkey's isolated context)
    const targetWindow = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
    targetWindow.HGLoggerDebug = {
      getCaptureCount: () => captureCount,
      getBuffer: () => buffer.slice(), // Copy of current buffer
      getLastEntries: (count = 5) => buffer.slice(-count), // Get last N entries
      getIsCapturing: () => isCapturing,
      getRateLimit: () => CAPTURE_LIMIT_PER_SECOND,
      getOriginalMethods: () => origConsole,
      getHostInfo: () => ({
        currentHost: currentHost,
        locationHost: location.host,
        locationHref: location.href,
        locationOrigin: location.origin,
        isTopWindow: window === window.top,
        frameDepth: getFrameDepth()
      }),
      getAllStoredLogs: () => getAllLogs(),
      getCurrentSiteLogs: () => getLocalLogs(),
      testCapture: () => {
        safeLog('[HG LOGGER DEBUG] About to test console hooks...');
        console.log('Debug test from HGLoggerDebug.testCapture()');
        console.warn('Debug warning from HGLoggerDebug.testCapture()');
        console.error('Debug error from HGLoggerDebug.testCapture()');
        safeLog('[HG LOGGER DEBUG] Test complete - check capture count and buffer');
      },
      testOriginal: () => {
        safeLog('[HG LOGGER DEBUG] Testing original console methods (should NOT be captured)');
        if (origConsole.log) origConsole.log('Original console.log - should not be captured');
        if (origConsole.warn) origConsole.warn('Original console.warn - should not be captured');
        if (origConsole.error) origConsole.error('Original console.error - should not be captured');
      },
      triggerWebsiteLogs: () => {
        // Try to trigger common website console scenarios
        safeLog('[HG LOGGER DEBUG] Triggering common website log scenarios...');
        
        // Test different log types
        console.log('WEBSITE TEST: Standard log message');
        console.info('WEBSITE TEST: Info message');
        console.warn('WEBSITE TEST: Warning message');
        console.error('WEBSITE TEST: Error message');
        console.debug('WEBSITE TEST: Debug message');
        
        // Test with objects
        console.log('WEBSITE TEST: Object log', { test: true, number: 42 });
        console.log('WEBSITE TEST: Array log', [1, 2, 3, 'test']);
        
        // Test error scenarios
        try {
          throw new Error('Test error for logging');
        } catch (e) {
          console.error('WEBSITE TEST: Caught error', e);
        }
        
        safeLog('[HG LOGGER DEBUG] Website log trigger completed');
      },
      forceRender: () => {
        if (window.render) {
          window.render();
          safeLog('[HG LOGGER DEBUG] Forced render called');
        } else {
          safeLog('[HG LOGGER DEBUG] No render function available');
        }
      },
      forceCapture: (message) => {
        safeLog('[HG LOGGER DEBUG] Forcing capture of:', message);
        push({ method: 'log', args: [message || 'Forced test message'] });
        safeLog('[HG LOGGER DEBUG] Forced capture completed');
      },
      testWebsiteConsole: () => {
        safeLog('[HG LOGGER DEBUG] ========== Testing website console capture ==========');
        safeLog('[HG LOGGER DEBUG] Current state - Capturing:', isCapturing, 'Buffer size:', buffer.length);
        
        // Test basic console methods (these should be captured)
        console.log('TEST: Website console.log message');
        console.warn('TEST: Website console.warn message');
        console.error('TEST: Website console.error message');
        console.info('TEST: Website console.info message');
        
        // Test with objects
        console.log('TEST: Object message', { test: true, data: [1, 2, 3] });
        
        setTimeout(() => {
          safeLog('[HG LOGGER DEBUG] After test - Buffer size:', buffer.length);
          safeLog('[HG LOGGER DEBUG] Last 3 buffer entries:');
          buffer.slice(-3).forEach((entry, idx) => {
            safeLog(`[HG LOGGER DEBUG]   ${idx}: method=${entry.method}, host=${entry.host}, args=${JSON.stringify(entry.args).substring(0, 80)}`);
          });
          safeLog('[HG LOGGER DEBUG] Check UI for captured test messages');
          if (window.render) window.render();
        }, 500);
      },
      inspectLogs: () => {
        const allLogs = getAllLogs();
        const currentSiteLogs = getLocalLogs();
        
        safeLog('[HG LOGGER DEBUG] ========== Log Inspection ==========');
        safeLog('[HG LOGGER DEBUG] Total sites with logs:', Object.keys(allLogs).length);
        safeLog('[HG LOGGER DEBUG] Current site:', location.host);
        safeLog('[HG LOGGER DEBUG] Current site log count:', currentSiteLogs.length);
        safeLog('[HG LOGGER DEBUG] Buffer size (unsaved):', buffer.length);
        
        if (currentSiteLogs.length > 0) {
          safeLog('[HG LOGGER DEBUG] Last 5 stored logs for', location.host, ':');
          currentSiteLogs.slice(-5).forEach((entry, idx) => {
            safeLog(`  ${idx + 1}. [${entry.method}] host="${entry.host}" source="${entry.source || 'none'}" args=`, entry.args);
          });
        } else {
          safeLog('[HG LOGGER DEBUG] No stored logs found for', location.host);
        }
        
        if (buffer.length > 0) {
          safeLog('[HG LOGGER DEBUG] Buffer (not yet saved) contains', buffer.length, 'entries');
          safeLog('[HG LOGGER DEBUG] First buffer entry:', buffer[0]);
        }
        
        return {
          totalSites: Object.keys(allLogs).length,
          currentSiteLogs: currentSiteLogs.length,
          bufferSize: buffer.length,
          allSites: Object.keys(allLogs)
        };
      },
      testDevToolsSync: () => {
        safeLog('[HG LOGGER DEBUG] ========== Testing DevTools Synchronization ==========');
        safeLog('[HG LOGGER DEBUG] This test will generate logs that SHOULD appear in DevTools Console');
        safeLog('[HG LOGGER DEBUG] Check DevTools Console and compare to HG Logger captured logs');
        
        // Generate distinctive test logs
        console.log('🔵 TEST 1: Plain console.log - should appear in DevTools');
        console.warn('🟡 TEST 2: console.warn - should appear in DevTools');
        console.error('🔴 TEST 3: console.error - should appear in DevTools');
        console.info('🟢 TEST 4: console.info - should appear in DevTools');
        
        // Log with objects
        console.log('📦 TEST 5: Object log', { test: true, timestamp: Date.now() });
        
        setTimeout(() => {
          safeLog('[HG LOGGER DEBUG] ========================================');
          safeLog('[HG LOGGER DEBUG] Check both:');
          safeLog('[HG LOGGER DEBUG] 1. DevTools Console - should show 5 test messages with colored circles');
          safeLog('[HG LOGGER DEBUG] 2. HG Logger UI - should also show these 5 test messages');
          safeLog('[HG LOGGER DEBUG] If both show them: System is working correctly!');
          safeLog('[HG LOGGER DEBUG] If only HG Logger shows them: DevTools may be filtering by log level');
          safeLog('[HG LOGGER DEBUG] If only DevTools shows them: Capture is broken');
          if (window.render) window.render();
        }, 500);
      },
      checkHookStatus: () => {
        safeLog('[HG LOGGER DEBUG] ========== Hook Status Check ==========');
        const pageConsole = typeof unsafeWindow !== 'undefined' ? unsafeWindow.console : console;
        const methods = ['log', 'info', 'warn', 'error', 'debug'];
        
        methods.forEach(m => {
          const isHooked = pageConsole[m] !== origConsole[m];
          const status = isHooked ? '✅ HOOKED' : '❌ NOT HOOKED';
          safeLog(`[HG LOGGER DEBUG] ${m}: ${status}`);
          
          if (!isHooked) {
            safeLog(`[HG LOGGER DEBUG]   ⚠️ ${m} is using original method - console calls won't be captured!`);
          }
        });
        
        // Test if hooks are working
        safeLog('[HG LOGGER DEBUG] Testing hook functionality...');
        const beforeCount = captureCount;
        console.log('[HGTEST] Hook status test message');
        setTimeout(() => {
          const afterCount = captureCount;
          if (afterCount > beforeCount) {
            safeLog('[HG LOGGER DEBUG] ✅ Hooks are WORKING - test message was captured');
          } else {
            safeLog('[HG LOGGER DEBUG] ❌ Hooks are BROKEN - test message was NOT captured');
            safeLog('[HG LOGGER DEBUG] This means website console.log calls are not being intercepted');
          }
        }, 100);
        
        return {
          pageConsole: pageConsole,
          origConsole: origConsole,
          hooksInstalled: methods.map(m => ({ method: m, hooked: pageConsole[m] !== origConsole[m] }))
        };
      }
    };
    
    // Helper function to get frame depth
    function getFrameDepth() {
      let depth = 0;
      let currentWindow = window;
      try {
        while (currentWindow !== currentWindow.parent && depth < 10) {
          currentWindow = currentWindow.parent;
          depth++;
        }
      } catch (e) {
        // Cross-origin frame access blocked
        depth = -1;
      }
      return depth;
    }
    
    safeLog('[HG LOGGER] Step 9: Debug object created successfully');
    // Verify debug object was created
    safeLog('[HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()');
    
    // Removed auto-running test messages - they were confusing
    // To test manually, run: HGLoggerDebug.testWebsiteConsole() in browser console

    // Hook console.clear on the page's console
    const origClear = pageConsole.clear ? pageConsole.clear.bind(pageConsole) : null;
    pageConsole.clear = function() {
      try {
        capture('clear', [{ note: 'console.clear invoked' }]);
      } catch {}
      if (origClear) try { origClear(); } catch {}
      if (window.render) window.render();
    };

    // Hook error events on the page's window (use targetWindow if needed)
    const pageWindow = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
    pageWindow.addEventListener('error', (ev) => {
      try {
        capture('error', [{ type: 'onerror', message: ev.message, filename: ev.filename, lineno: ev.lineno, colno: ev.colno, error: toPlain(ev.error) }]);
      } catch {}
    });
    pageWindow.addEventListener('unhandledrejection', (ev) => {
      try {
        capture('error', [{ type: 'unhandledrejection', reason: toPlain(ev.reason ?? '(no reason)') }]);
      } catch {}
    });

    const of = window.fetch ? window.fetch.bind(window) : null;
    if (of) {
      window.fetch = async function(input, init) {
        try {
          const res = await of(input, init);
          try {
            if (!res.ok) capture('net', [{ type: 'fetch', status: res.status, url: res.url || String(input), method: (init && init.method) || 'GET', ms: +(performance.now() - performance.now()).toFixed(1) }]); // Note: timing fix
          } catch {}
          return res;
        } catch (e) {
          try {
            capture('net', [{ type: 'fetch-error', url: String(input), error: toPlain(e), ms: 0 }]);
          } catch {}
          throw e;
        }
      };
    }

    const X = window.XMLHttpRequest;
    if (X) {
      const open = X.prototype.open;
      const send = X.prototype.send;
      X.prototype.open = function(method, url) {
        this.__hglog = { method, url };
        return open.apply(this, arguments);
      };
      X.prototype.send = function() {
        const t0 = performance.now();
        this.addEventListener('load', () => {
          try {
            if (this.status >= 400) capture('net', [{ type: 'xhr', status: this.status, method: this.__hglog.method, url: this.__hglog.url, ms: +(performance.now() - t0).toFixed(1) }]);
          } catch {}
        });
        this.addEventListener('error', () => {
          try {
            capture('net', [{ type: 'xhr-error', method: this.__hglog.method, url: this.__hglog.url, ms: +(performance.now() - t0).toFixed(1) }]);
          } catch {}
        });
        return send.apply(this, arguments);
      };
    }

    safeLog('[HG LOGGER] Hooks installed safely for host:', currentHost);
    
    // Defensive mechanism: Re-install hooks periodically in case they get overridden
    let hookCheckInterval = setInterval(() => {
      try {
        let reinstalled = false;
        methods.forEach(m => {
          // Check if hook was overridden on the PAGE console (more robust check)
          if (typeof pageConsole[m] !== 'function' || pageConsole[m] === origConsole[m]) {
            safeLog('[HG LOGGER] Reinstalling hook for method:', m);
            
            // Reinstall the hook
            const originalMethod = origConsole[m];
            const hookFunction = function(...args) {
              try {
                capture(m, args);
              } catch {}
              
              try {
                return originalMethod.apply(this, args);
              } catch {}
            };
            
            pageConsole[m] = hookFunction;
            reinstalled = true;
          }
        });
        
        if (reinstalled) {
          safeLog('[HG LOGGER] Console hooks were overridden and have been reinstalled');
        }
      } catch (checkError) {
        safeLog('[HG LOGGER] Hook check error:', checkError);
      }
    }, 3000); // Check every 3 seconds
    
    // Stop checking after 5 minutes to avoid indefinite intervals
    setTimeout(() => {
      if (hookCheckInterval) {
        clearInterval(hookCheckInterval);
        safeLog('[HG LOGGER] Hook monitoring stopped after 5 minutes');
      }
    }, 300000);
  } catch (e) {
    safeLog('[HG LOGGER] ⚠️⚠️⚠️ CRITICAL: Hook installation failed ⚠️⚠️⚠️');
    safeLog('[HG LOGGER] Error:', e.message);
    safeLog('[HG LOGGER] Stack:', e.stack);
    safeLog('[HG LOGGER] This means console logs will NOT be captured!');
    
    // Create a minimal debug object even if hooks fail
    const targetWindow = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
    targetWindow.HGLoggerDebug = {
      error: e.message,
      stack: e.stack,
      message: 'Hook installation failed - console capture is not working'
    };
  }

  // ===== VERIFY DEBUG OBJECT EXISTS =====
  // Ensure HGLoggerDebug is accessible globally - if not created, make a minimal one
  const targetWindow = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
  if (!targetWindow.HGLoggerDebug) {
    safeLog('[HG LOGGER] ⚠️ WARNING: HGLoggerDebug was not created! Creating minimal fallback...');
    targetWindow.HGLoggerDebug = {
      status: 'Fallback - hooks may not have been installed',
      host: location.host,
      href: location.href,
      scriptRan: true,
      test: () => {
        safeLog('[HG LOGGER] HGLoggerDebug fallback test - script is running but hooks may have failed');
        console.log('Test message from HGLoggerDebug fallback');
      }
    };
  }
  safeLog('[HG LOGGER] HGLoggerDebug verification - exists:', !!targetWindow.HGLoggerDebug, 'type:', typeof targetWindow.HGLoggerDebug);

  // ===== UI FUNCTIONS (CSP-COMPLIANT) =====
  function parseContext(url = location.href) {
    const u = new URL(url, location.origin);
    const m = u.pathname.match(/(?:^|\/)(lobby|game|spectator)\/([^\/?#]+)/i);
    const kind = m ? m[1].toLowerCase() : 'page';
    const id = m ? m[2] : (u.pathname.replace(/\W+/g, '_') || '_global_');
    return { kind, id };
  }

  function formatLine(e, showHost = false) {
    const prefix = e.source === 'hg-logger' ? '[HG LOGGER] ' : '';
    const hostPrefix = showHost ? `[${e.host}] ` : '';
    const args = (e.args || []).map(a => typeof a === 'string' ? a : JSON.stringify(a) || String(a)).join(' ');
    return `[${e.ts}] [${e.session.slice(0, 8)}] [${e.method}] ${hostPrefix}${prefix}${args}`;
  }

  // Refresh dropdown options (global function)
  window.refreshFilterDropdown = function() {
    const filterSelect = document.getElementById('tmc-filter');
    if (!filterSelect) {
      return; // Silent fail - no debug logging
    }
    
    // Ensure dropdown has proper styling for visibility
    Object.assign(filterSelect.style, {
      minWidth: '120px',
      maxWidth: '200px',
      background: '#2a2a2a',
      color: '#eee',
      border: '1px solid #666',
      borderRadius: '4px',
      padding: '2px 4px',
      fontSize: '11px',
      zIndex: '2147483648' // Higher than panel
    });
    
    const currentValue = filterSelect.value;
    const allLogs = getAllLogs();
    
    // Clear and rebuild options
    filterSelect.innerHTML = '';
    
    // Add "All Sites" option
    const optAll = document.createElement('option');
    optAll.value = 'all';
    optAll.textContent = '🌐 All Sites';
    optAll.style.cssText = 'background:#2a2a2a;color:#eee;';
    filterSelect.appendChild(optAll);
    
    // Add current site first (if has logs)
    if (allLogs[location.host] && allLogs[location.host].length > 0) {
      const currentOpt = document.createElement('option');
      currentOpt.value = location.host;
      currentOpt.textContent = `📍 ${location.host} (current)`;
      currentOpt.style.cssText = 'background:#2a2a2a;color:#eee;';
      filterSelect.appendChild(currentOpt);
    }
    
    // Add separator before other sites
    const hostKeys = Object.keys(allLogs).filter(host => host !== location.host && allLogs[host].length > 0);
    if (hostKeys.length > 0) {
      const separator1 = document.createElement('option');
      separator1.disabled = true;
      separator1.textContent = '--- Other Sites ---';
      separator1.style.cssText = 'background:#1a1a1a;color:#999;font-style:italic;';
      filterSelect.appendChild(separator1);
      
      // Sort hosts by domain and subdomain
      hostKeys.sort((a, b) => {
        const aParts = a.split('.').reverse();
        const bParts = b.split('.').reverse();
        return aParts.join('.').localeCompare(bParts.join('.'));
      }).forEach(host => {
        const opt = document.createElement('option');
        opt.value = host;
        const logCount = allLogs[host].length;
        opt.textContent = `🔗 ${host} (${logCount} logs)`;
        opt.style.cssText = 'background:#2a2a2a;color:#eee;';
        filterSelect.appendChild(opt);
      });
    }
    
    // Add method filters for current host
    const currentLogs = allLogs[location.host] || [];
    const methods = [...new Set(currentLogs.map(e => e.method))];
    if (methods.length > 0) {
      const separator2 = document.createElement('option');
      separator2.disabled = true;
      separator2.textContent = '--- Current Site Methods ---';
      separator2.style.cssText = 'background:#1a1a1a;color:#999;font-style:italic;';
      filterSelect.appendChild(separator2);
      
      methods.sort().forEach(method => {
        const methodLogs = currentLogs.filter(e => e.method === method);
        const opt = document.createElement('option');
        opt.value = method;
        opt.textContent = `📝 ${method.toUpperCase()} (${methodLogs.length})`;
        opt.style.cssText = 'background:#2a2a2a;color:#eee;';
        filterSelect.appendChild(opt);
      });
    }
    
    // Restore previous selection if it still exists
    if ([...filterSelect.options].some(opt => opt.value === currentValue)) {
      filterSelect.value = currentValue;
    }
  }

  // Render function (global for access)
  window.render = function(reset = false) {
    const logDisplay = document.getElementById('tmc-text');
    if (!logDisplay) return;
    syncLogsToGM(); // Ensure GM is up-to-date
    
    // Refresh dropdown to show latest sites and counts
    if (window.refreshFilterDropdown) {
      window.refreshFilterDropdown();
    }
    
    const allLogs = getAllLogs();
    const filter = document.getElementById('tmc-filter')?.value || 'all';
    let arr = [];
    if (filter === 'all') {
      arr = Object.values(allLogs).flat().sort((a, b) => a.ts.localeCompare(b.ts));
    } else if (Object.keys(allLogs).includes(filter)) {
      arr = allLogs[filter] || [];
    } else {
      const baseArr = allLogs[location.host] || [];
      arr = baseArr.filter(e => e.method === filter);
    }
    
    // Remove debug logging to reduce noise
    
    if (reset) {
      if (logDisplay.tagName === 'TEXTAREA') {
        logDisplay.value = '';
      } else {
        logDisplay.innerHTML = '';
      }
    }
    
    if (arr.length > 0) {
      try {
        const formatted = arr.map(e => {
          try {
            return formatLineWithColors(e, filter === 'all');
          } catch (formatError) {
            // If formatting fails for one entry, show error but don't stop rendering others
            safeLog('[HG LOGGER] Format error for entry:', e, formatError);
            return {
              html: `<span style="color: #ff6b6b;">[FORMAT ERROR] ${String(e.args?.[0] || 'unknown')}</span>`,
              text: `[FORMAT ERROR] ${String(e.args?.[0] || 'unknown')}`
            };
          }
        });
        
        if (logDisplay.tagName === 'TEXTAREA') {
          // Fallback for plain text
          logDisplay.value = formatted.map(f => f.text).join('\n');
        } else {
          // Colored HTML display
          logDisplay.innerHTML = formatted.map(f => `<div class="log-line">${f.html}</div>`).join('');
        }
      } catch (renderError) {
        safeLog('[HG LOGGER] Render error:', renderError);
        logDisplay.innerHTML = `<div class="log-line" style="color: #ff6b6b;">[RENDER ERROR] ${renderError.message}</div>`;
      }
    } else {
      const noLogsMsg = `No logs for ${filter}`;
      if (logDisplay.tagName === 'TEXTAREA') {
        logDisplay.value = noLogsMsg;
      } else {
        logDisplay.innerHTML = `<div class="log-line" style="color: #888; font-style: italic;">${noLogsMsg}</div>`;
      }
    }
    
    if (document.getElementById('tmc-auto')?.checked) {
      logDisplay.scrollTop = logDisplay.scrollHeight;
    }
    document.getElementById('tmc-count').textContent = `${arr.length}`;
    document.getElementById('tmc-key').textContent = `/${parseContext().kind}/${parseContext().id}`;
  };

  // Ensure full panel
  function ensurePanel(force = false) {
    let panel = document.getElementById('tmc-panel');
    if (panel && !force) return;
    if (panel) panel.remove(); // Clean up if forcing
    panel = document.createElement('div');
    panel.id = 'tmc-panel';
    Object.assign(panel.style, {
      position: 'fixed',
      right: '12px',
      bottom: '12px',
      minWidth: '520px',
      maxWidth: '90vw',
      width: 'auto',
      maxHeight: '75vh',
      background: 'rgba(24,24,24,0.96)',
      color: '#eee',
      fontFamily: 'monospace',
      fontSize: '12px',
      border: '1px solid #333',
      borderRadius: '8px',
      zIndex: 2147483647,
      display: 'flex',
      flexDirection: 'column',
      boxSizing: 'border-box'
    });
    
    // Create header div
    const header = document.createElement('div');
    header.id = 'tmc-head';
    Object.assign(header.style, {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '6px 8px',
      borderBottom: '1px solid #333',
      cursor: 'move',
      minHeight: '40px'
    });
    
    // Left side of header
    const leftHeader = document.createElement('div');
    Object.assign(leftHeader.style, {
      display: 'flex',
      gap: '8px',
      alignItems: 'center',
      flexShrink: '0'
    });
    
    const title = document.createElement('strong');
    title.textContent = 'HG Logger';
    leftHeader.appendChild(title);
    
    const keySpan = document.createElement('span');
    keySpan.id = 'tmc-key';
    keySpan.title = 'Current context';
    Object.assign(keySpan.style, {
      opacity: '.8',
      fontSize: '11px',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      maxWidth: '200px'
    });
    leftHeader.appendChild(keySpan);
    header.appendChild(leftHeader);
    
    // Right side of header
    const rightHeader = document.createElement('div');
    Object.assign(rightHeader.style, {
      display: 'flex',
      gap: '6px',
      alignItems: 'center',
      flexWrap: 'wrap',
      justifyContent: 'flex-end'
    });
    
    // Create buttons
    const buttons = [
      { id: 'tmc-config', text: 'Config' },
      { id: 'tmc-keywords', text: 'Colors' },
      { id: 'tmc-test', text: 'Test', title: 'Generate test logs to verify capture works' },
      { id: 'tmc-reset', text: 'Reset All' },
      { id: 'tmc-copy', text: 'Copy' },
      { id: 'tmc-dl', text: 'Download' },
      { id: 'tmc-clr', text: 'Clear' },
      { id: 'tmc-collapse', text: '▲' }
    ];
    
    buttons.forEach(btn => {
      const button = document.createElement('button');
      button.id = btn.id;
      button.textContent = btn.text;
      if (btn.title) button.title = btn.title;
      rightHeader.appendChild(button);
    });
    
    // Create filter select
    const filterSelect = document.createElement('select');
    filterSelect.id = 'tmc-filter';
    filterSelect.title = 'Filter';
    Object.assign(filterSelect.style, {
      minWidth: '120px',
      maxWidth: '200px',
      background: '#2a2a2a',
      color: '#eee',
      border: '1px solid #666',
      borderRadius: '4px',
      padding: '2px 4px',
      fontSize: '11px'
    });
    rightHeader.insertBefore(filterSelect, rightHeader.children[2]); // Insert before Copy button
    
    header.appendChild(rightHeader);
    panel.appendChild(header);
    
    // Create body div
    const body = document.createElement('div');
    body.id = 'tmc-body';
    Object.assign(body.style, {
      display: 'flex',
      flexDirection: 'column',
      gap: '6px',
      padding: '6px'
    });
    
    // Create controls row
    const controlsRow = document.createElement('div');
    Object.assign(controlsRow.style, {
      display: 'flex',
      gap: '8px',
      alignItems: 'center',
      flexWrap: 'wrap'
    });
    
    // Auto-scroll checkbox
    const autoLabel = document.createElement('label');
    const autoCheckbox = document.createElement('input');
    autoCheckbox.id = 'tmc-auto';
    autoCheckbox.type = 'checkbox';
    autoCheckbox.checked = true;
    autoLabel.appendChild(autoCheckbox);
    autoLabel.appendChild(document.createTextNode(' Auto-scroll'));
    controlsRow.appendChild(autoLabel);
    
    // Capture checkbox
    const captureLabel = document.createElement('label');
    Object.assign(captureLabel.style, { marginLeft: '8px' });
    const captureCheckbox = document.createElement('input');
    captureCheckbox.id = 'tmc-live';
    captureCheckbox.type = 'checkbox';
    captureCheckbox.checked = true;
    captureLabel.appendChild(captureCheckbox);
    captureLabel.appendChild(document.createTextNode(' Capture'));
    controlsRow.appendChild(captureLabel);
    
    // Rate info span
    const rateInfo = document.createElement('span');
    rateInfo.id = 'tmc-rate-info';
    Object.assign(rateInfo.style, {
      marginLeft: '8px',
      opacity: '.7',
      fontSize: '10px'
    });
    controlsRow.appendChild(rateInfo);
    
    // Count span
    const countSpan = document.createElement('span');
    countSpan.id = 'tmc-count';
    Object.assign(countSpan.style, {
      marginLeft: 'auto',
      opacity: '.8',
      whiteSpace: 'nowrap'
    });
    controlsRow.appendChild(countSpan);
    
    body.appendChild(controlsRow);
    
    // Create log display div (supports colors)
    const logDisplay = document.createElement('div');
    logDisplay.id = 'tmc-text';
    Object.assign(logDisplay.style, {
      width: '100%',
      height: '330px',
      padding: '8px',
      background: '#111',
      color: '#eee',
      borderRadius: '6px',
      border: '1px solid #333',
      overflow: 'auto',
      boxSizing: 'border-box',
      fontFamily: 'monospace',
      fontSize: '12px',
      lineHeight: '1.4',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word'
    });
    
    // Add CSS for log lines
    const style = document.createElement('style');
    style.textContent = `
      #tmc-text .log-line {
        margin-bottom: 1px;
        padding: 1px 0;
      }
      #tmc-text .log-line:hover {
        background-color: rgba(255,255,255,0.05);
      }
    `;
    document.head.appendChild(style);
    
    body.appendChild(logDisplay);
    
    panel.appendChild(body);
    panel.querySelectorAll('button').forEach(b => {
      Object.assign(b.style, { 
        background: 'transparent', 
        color: '#ddd', 
        border: '1px solid #666', 
        padding: '4px 7px', 
        borderRadius: '5px', 
        cursor: 'pointer',
        fontSize: '11px',
        whiteSpace: 'nowrap',
        flexShrink: '0'
      });
    });
    document.documentElement.appendChild(panel);

    // Restore state
    restoreUIState(panel);

    // Drag functionality with save (responsive-aware)
    (function drag(el, handle) {
      let down = false;
      let ox = 0;
      let oy = 0;
      let r = parseInt(el.style.right) || 12;
      let b = parseInt(el.style.bottom) || 12;
      
      handle.addEventListener('mousedown', e => {
        down = true;
        ox = e.clientX;
        oy = e.clientY;
        e.preventDefault();
      });
      
      document.addEventListener('mousemove', e => {
        if (!down) return;
        r = Math.max(0, Math.min(window.innerWidth - el.offsetWidth, r + ox - e.clientX));
        b = Math.max(0, Math.min(window.innerHeight - el.offsetHeight, b + oy - e.clientY));
        el.style.right = r + 'px';
        el.style.bottom = b + 'px';
        ox = e.clientX;
        oy = e.clientY;
      });
      
      document.addEventListener('mouseup', () => {
        if (down) {
          down = false;
          saveUIState(el);
        }
      });
    })(panel, document.getElementById('tmc-head'));

    // Initialize filter dropdown
    setTimeout(() => {
      if (window.refreshFilterDropdown) {
        window.refreshFilterDropdown();
      }
    }, 100);

    // Responsive adjustments
    function adjustForScreenSize() {
      const panel = document.getElementById('tmc-panel');
      if (!panel) return;
      
      const screenWidth = window.innerWidth;
      if (screenWidth < 600) {
        // Mobile adjustments
        panel.style.minWidth = '300px';
        panel.style.maxWidth = '95vw';
        panel.style.right = '2.5vw';
        panel.style.fontSize = '11px';
        
        // Adjust header layout for mobile
        const head = document.getElementById('tmc-head');
        if (head) {
          head.style.flexWrap = 'wrap';
          head.style.minHeight = 'auto';
        }
      } else if (screenWidth < 900) {
        // Tablet adjustments
        panel.style.minWidth = '450px';
        panel.style.maxWidth = '85vw';
      } else {
        // Desktop - restore defaults
        panel.style.minWidth = '520px';
        panel.style.maxWidth = '90vw';
      }
    }
    
    // Apply responsive adjustments
    adjustForScreenSize();
    window.addEventListener('resize', adjustForScreenSize);

    // Event handlers
    document.getElementById('tmc-config').addEventListener('click', () => {
      showConfigDialog();
    });

    document.getElementById('tmc-keywords').addEventListener('click', () => {
      showKeywordDialog();
    });

    document.getElementById('tmc-test').addEventListener('click', () => {
      if (window.HGLoggerDebug && window.HGLoggerDebug.testWebsiteConsole) {
        window.HGLoggerDebug.testWebsiteConsole();
      } else {
        // Fallback: generate simple test messages
        console.log('[HGTEST] Test console.log message');
        console.warn('[HGTEST] Test console.warn message');
        console.error('[HGTEST] Test console.error message');
        setTimeout(() => {
          if (window.render) window.render();
        }, 200);
      }
    });

    document.getElementById('tmc-reset').addEventListener('click', () => {
      if (confirm('Reset all logs across all sites?')) {
        setAllLogs({});
        localStorage.clear();
        window.render();
      }
    });

    document.getElementById('tmc-filter').addEventListener('change', (e) => {
      window.render();
    });

    document.getElementById('tmc-copy').addEventListener('click', () => {
      const logDisplay = document.getElementById('tmc-text');
      let textContent;
      
      if (logDisplay.tagName === 'TEXTAREA') {
        textContent = logDisplay.value;
        logDisplay.select();
        document.execCommand('copy');
      } else {
        // Extract plain text from colored div
        textContent = Array.from(logDisplay.querySelectorAll('.log-line')).map(line => line.textContent).join('\n');
        // Use modern clipboard API
        navigator.clipboard.writeText(textContent).catch(() => {
          // Fallback: create temporary textarea
          const temp = document.createElement('textarea');
          temp.value = textContent;
          document.body.appendChild(temp);
          temp.select();
          document.execCommand('copy');
          document.body.removeChild(temp);
        });
      }
      
      const btn = document.getElementById('tmc-copy');
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = orig, 1000);
    });

    document.getElementById('tmc-dl').addEventListener('click', () => {
      const logDisplay = document.getElementById('tmc-text');
      let content;
      
      if (logDisplay.tagName === 'TEXTAREA') {
        content = logDisplay.value;
      } else {
        // Extract plain text from colored div
        content = Array.from(logDisplay.querySelectorAll('.log-line')).map(line => line.textContent).join('\n');
      }
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hg-logs-${parseContext().kind}-${parseContext().id}-${new Date().toISOString().slice(0, 16).replace(/:/g, '-')}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    });

    document.getElementById('tmc-clr').addEventListener('click', () => {
      if (confirm('Clear current filter logs?')) {
        const filter = document.getElementById('tmc-filter').value;
        if (filter === 'all') {
          setAllLogs({});
          localStorage.clear();
        } else if (Object.keys(getAllLogs()).includes(filter)) {
          const allLogs = getAllLogs();
          delete allLogs[filter];
          setAllLogs(allLogs);
          if (filter === location.host) {
            setLocalLogs([]);
          }
        } else {
          // Method filter - clear just that method
          const currentLogs = getLocalLogs();
          const filtered = currentLogs.filter(e => e.method !== filter);
          setLocalLogs(filtered);
          syncLogsToGM();
        }
        window.render();
      }
    });

    document.getElementById('tmc-collapse').addEventListener('click', () => {
      const body = document.getElementById('tmc-body');
      const btn = document.getElementById('tmc-collapse');
      const isHidden = body.style.display === 'none';
      body.style.display = isHidden ? 'flex' : 'none';
      btn.textContent = isHidden ? '▲' : '▼';
      saveUIState(panel);
    });

    document.getElementById('tmc-live').addEventListener('change', (e) => {
      isCapturing = e.target.checked;
      if (!isCapturing) {
        safeLog('[HG LOGGER] Capture disabled');
      } else {
        safeLog('[HG LOGGER] Capture enabled');
      }
    });

    // Initial render
    window.render();
    
    // Update rate limiting info display
    function updateRateInfo() {
      const rateInfo = document.getElementById('tmc-rate-info');
      if (rateInfo) {
        const pct = Math.round((captureCount / CAPTURE_LIMIT_PER_SECOND) * 100);
        if (captureCount >= CAPTURE_LIMIT_PER_SECOND * 0.8) {
          rateInfo.textContent = `⚠️ Rate: ${pct}%`;
          rateInfo.style.color = '#ff6b6b';
        } else if (captureCount > 0) {
          rateInfo.textContent = `Rate: ${pct}%`;
          rateInfo.style.color = '#4ecdc4';
        } else {
          rateInfo.textContent = `Limit: ${CAPTURE_LIMIT_PER_SECOND}/s`;
          rateInfo.style.color = '#95a5a6';
        }
      }
    }
    
    // Update rate info every second
    setInterval(updateRateInfo, 1000);
    updateRateInfo(); // Initial update
  }

  // ===== INITIALIZE UI (CSP-COMPLIANT) =====
  function initializeUI() {
    if (!document.head && !document.documentElement) return; // Ensure DOM is ready

    // CRITICAL: Only show UI in top window, not in iframes
    if (isInIframe) {
      safeLog('[HG LOGGER] Running in iframe - skipping UI (console capture still active)');
      return; // Exit early - don't create UI in iframes
    }

    // Auto-detect noisy sites and adjust capture settings
    const noisySites = ['imdb.com', 'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com', 'reddit.com'];
    const isNoisySite = noisySites.some(site => location.host.includes(site));
    
    if (isNoisySite) {
      // Reduce capture rate for known noisy sites (but not too much)
      CAPTURE_LIMIT_PER_SECOND = 25; // Increased from 10 to 25
      safeLog('[HG LOGGER] Detected noisy site - reduced capture rate to', CAPTURE_LIMIT_PER_SECOND, 'per second');
    }

    // Check if UI should be shown on this domain
    const shouldShowUI = shouldShowUIOnHost(location.host);
    
    // FAILSAFE: If we're on localhost or common development domains, always show UI
    const isDevHost = location.host.includes('localhost') || 
                     location.host.includes('127.0.0.1') || 
                     location.host.includes('0.0.0.0') ||
                     location.host.endsWith('.local');
    
    // Skip UI creation for CSP-strict domains to avoid CSP violations
    if (isCSPStrict) {
      safeLog('[HG LOGGER] CSP-strict domain detected - logging only (no UI):', location.host);
    } else if (shouldShowUI || isDevHost) {
      ensurePanel();
    } else {
      safeLog('[HG LOGGER] No UI for host (not in domain list):', location.host);
      safeLog('[HG LOGGER] To enable UI: click the TamperMonkey icon → HG Logger → Config, then add this domain or leave domain list empty');
    }

    // Navigation detection (SPA-aware)
    let lastUrl = location.href;
    function checkNavigation() {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        if (!isCSPStrict && (shouldShowUI || isDevHost) && window.render) {
          window.render(); // Update UI context
        }
      }
    }
    
    // Monitor for navigation changes
    setInterval(checkNavigation, 500);
    
    // Periodic dropdown refresh to catch new sites
    setInterval(() => {
      if (window.refreshFilterDropdown && document.getElementById('tmc-filter')) {
        window.refreshFilterDropdown();
      }
    }, 5000); // Every 5 seconds
    
    // Listen for pushstate/replacestate
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function() {
      originalPushState.apply(history, arguments);
      setTimeout(checkNavigation, 0);
    };
    
    history.replaceState = function() {
      originalReplaceState.apply(history, arguments);
      setTimeout(checkNavigation, 0);
    };
    
    window.addEventListener('popstate', checkNavigation);
  }

  // Initialize UI with proper timing
  setTimeout(initializeUI, 100); // Small delay for DOM readiness

})();


/*





[22:40:20] [5221ef3d] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:40:20] [5ddee5d2] [WARN] [www.imdb.com] [Audigent] cannot find __gpp framework
[22:40:23] [5ddee5d2] [INFO] [www.imdb.com] INFO - (Geo location) persisted cached location data
[22:40:23] [5ddee5d2] [INFO] [www.imdb.com] INFO - (Geo location) persisted cached location data
[22:41:05] [f278e3dc] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:41:25] [c9af9476] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:41:45] [ccf658e2] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:42:05] [f6c8b76b] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:42:25] [75762a8c] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:42:25] [75762a8c] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:42:25] [75762a8c] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:42:45] [63599de4] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:42:45] [63599de4] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:42:45] [63599de4] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for asinImageRender already exists.
[22:43:05] [960a6860] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:05] [960a6860] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:05] [960a6860] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:05] [960a6860] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for gridBuilderBuyBoxRender already exists.
[22:43:45] [ad1e4878] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:45] [ad1e4878] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:45] [ad1e4878] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for customImageRender already exists.
[22:43:53] [ad1e4878] [WARN] [images-na.ssl-images-amazon.com] PerformanceTracker: Timer for gridBuilderBuyBoxRender already exists.
[22:43:57] [6c61984b] [WARN] [www.imdb.com] [Audigent] cannot find __gpp framework
[22:43:58] [6c61984b] [INFO] [www.imdb.com] INFO - (Geo location) persisted cached location data
[22:43:58] [6c61984b] [INFO] [www.imdb.com] INFO - (Geo location) persisted cached location data

================ ^^^ HG LOGGER LOGS ^^^ ==================

Browser:
[Violation] 'setTimeout' handler took 318ms
content.js:66 [Violation] 'setTimeout' handler took 318ms
[Violation] Forced reflow while executing JavaScript took 140ms
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: www.imdb.com href: https://www.imdb.com/
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: true iframe: false
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: www.imdb.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: www.imdb.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: securepubads.g.doubleclick.net
framework-a909d885f472f220.js:1 [Violation] 'message' handler took 155ms
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1965 [HG LOGGER] Detected noisy site - reduced capture rate to 25 per second
[Violation] 'setTimeout' handler took 269ms
content.js:66 [Violation] 'setTimeout' handler took 270ms
[Violation] Forced reflow while executing JavaScript took 152ms
_app-bc92e859dfe8fbf5.js:136 An iframe which has both allow-scripts and allow-same-origin for its sandbox attribute can escape its sandboxing.
a @ _app-bc92e859dfe8fbf5.js:136
oB @ framework-a909d885f472f220.js:1
oY @ framework-a909d885f472f220.js:1
e @ framework-a909d885f472f220.js:1
(anonymous) @ framework-a909d885f472f220.js:1
uO @ framework-a909d885f472f220.js:1
uS @ framework-a909d885f472f220.js:1
x @ framework-a909d885f472f220.js:1
R @ framework-a909d885f472f220.js:1Understand this warning
(index):1 Access to fetch at 'https://api.rlcdn.com/api/identity/envelope?pid=13310' from origin 'https://www.imdb.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.Understand this error
apstag.js:3  GET https://api.rlcdn.com/api/identity/envelope?pid=13310 net::ERR_FAILED 401 (Unauthorized)
handler @ apstag.js:3
(anonymous) @ apstag.js:3
L @ apstag.js:3
N @ apstag.js:3
G @ apstag.js:3
(anonymous) @ apstag.js:3
K @ apstag.js:3
(anonymous) @ apstag.js:3
t @ apstag.js:3
getAccounts.forEach.e.queue.push @ apstag.js:3
(anonymous) @ apstag.js:3
recordListener @ apstag.js:3
handler @ apstag.js:3
(anonymous) @ apstag.js:3
L @ apstag.js:3
N @ apstag.js:3
G @ apstag.js:3
(anonymous) @ apstag.js:3
K @ apstag.js:3
(anonymous) @ apstag.js:3
t @ apstag.js:3
getAccounts.forEach.e.queue.push @ apstag.js:3
(anonymous) @ apstag.js:3
recordListener @ apstag.js:3
recordListenerNonBlocking @ apstag.js:3
handler @ apstag.js:3
(anonymous) @ apstag.js:3
L @ apstag.js:3
N @ apstag.js:3
G @ apstag.js:3
(anonymous) @ apstag.js:3
K @ apstag.js:3
(anonymous) @ apstag.js:3
t @ apstag.js:3
getAccounts.forEach.e.queue.push @ apstag.js:3
(anonymous) @ apstag.js:3
recordListener @ apstag.js:3
(anonymous) @ apstag.js:3
handler @ apstag.js:3
(anonymous) @ apstag.js:3
L @ apstag.js:3
N @ apstag.js:3
G @ apstag.js:3
(anonymous) @ apstag.js:3
K @ apstag.js:3
(anonymous) @ apstag.js:3
t @ apstag.js:3
getAccounts.forEach.e.queue.push @ apstag.js:3
(anonymous) @ apstag.js:5
value @ apstag.js:5
D @ apstag.js:5
yt @ apstag.js:5
(anonymous) @ apstag.js:5
(anonymous) @ apstag.js:5
makeApsAndGAMRequests @ 3775Z0lVmT83C09.js:1
runApsAuctionFlow @ 3775Z0lVmT83C09.js:1
handleAdServiceResponse @ 3775Z0lVmT83C09.js:1
e.onreadystatechange @ 3775Z0lVmT83C09.js:1
XMLHttpRequest.send
i.makeAdSlotsCall @ 3775Z0lVmT83C09.js:1
(anonymous) @ (index):1406Understand this error
content-script.js:22 Document already loaded, running initialization immediately
content-script.js:4 Attempting to initialize AdUnit
content-script.js:6 AdUnit initialized successfully
51LFWUXHkZL.js:33 window.NativeWebBridge already exists
parcelRequire.kIhC... @ 51LFWUXHkZL.js:33
f @ 51LFWUXHkZL.js:1
parcelRequire.WBRF @ 51LFWUXHkZL.js:1
(anonymous) @ 51LFWUXHkZL.js:1Understand this warning
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: s.amazon-adsystem.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: s.amazon-adsystem.com
[Violation] Forced reflow while executing JavaScript took 40ms
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:25  GET https://x.bidswitch.net/sync_a9/val=bleAE51aRMmTO-_-qzhSpA&redirect=https://s.amazon-adsystem.com/ecm3?ex=bidswitch.com&id=${UUID}&gdpr_consent=&gdpr=0 404 (Not Found)Understand this error
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: s.amazon-adsystem.com
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:9  GET https://bs.serving-sys.com/Serving?cn=cs&rtu=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dsizmek%26id%3D%5B%25tp_UserID%25%5D net::ERR_NAME_NOT_RESOLVEDUnderstand this error
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:14  GET https://tags.bluekai.com/site/36840?redir=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dbluekai.com%26id%3D%24_BK_UUID net::ERR_NAME_NOT_RESOLVEDUnderstand this error
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:19  GET https://amazon.partners.tremorhub.com/sync?UIAM&redir=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dtelaria.com%26id%3D%5BPARTNER_ID%5D net::ERR_NAME_NOT_RESOLVEDUnderstand this error
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:11  GET https://usermatch.krxd.net/um/v2?partner=amzn net::ERR_NAME_NOT_RESOLVEDUnderstand this error
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:23  GET https://beacon.krxd.net/usermatch.gif?partner=amzn&partner_uid=Clj82aUHSRG08LfyhLS8xA&redir=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dkrux.com%26id%3D net::ERR_NAME_NOT_RESOLVEDUnderstand this error
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:8  GET https://c1.adform.net/serving/cookie/match?party=1153&redirect_url=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dadform.net%26id%3D%24%7BUUID%7D 403 (Forbidden)Understand this error
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:855 [HG LOGGER] First entry added to buffer: [Audigent] cannot find __gpp framework
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:856 [HG LOGGER] Entry host info - currentHost: www.imdb.com location.host: www.imdb.com location.href: https://www.imdb.com/
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:931 [Audigent] cannot find __gpp framework
hookFunction @ userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:931
(anonymous) @ 745?_it=amazon:1
setInterval
q @ 745?_it=amazon:1
w @ 745?_it=amazon:1
(anonymous) @ 745?_it=amazon:1
(anonymous) @ 745?_it=amazon:1
(anonymous) @ 745?_it=amazon:1
(anonymous) @ 745?_it=amazon:1Understand this warning
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: s.amazon-adsystem.com
81rkcLJku5L.js:1 Uncaught TypeError: n.setup is not a function
e.default @ 81rkcLJku5L.js:1
value @ 81rkcLJku5L.js:1
script
Pi9N.e.default @ 81rkcLJku5L.js:1
value @ 81rkcLJku5L.js:1
(anonymous) @ 81rkcLJku5L.js:1
(anonymous) @ 81rkcLJku5L.js:1
P @ 81rkcLJku5L.js:1
C @ 81rkcLJku5L.js:1
(anonymous) @ 81rkcLJku5L.js:1
Pq/i @ 81rkcLJku5L.js:1
e @ 81rkcLJku5L.js:1
(anonymous) @ 81rkcLJku5L.js:1
(anonymous) @ 81rkcLJku5L.js:1Understand this error
3(index):1 Uncaught (in promise) Error: A listener indicated an asynchronous response by returning true, but the message channel closed before a response was receivedUnderstand this error
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: bh.contextweb.com href: https://bh.contextweb.com/visitormatch?p=547259,530912,534301,548607,543793,561117&rurl=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fid%3D%25%25VGUID%25%25%26ex%3DPulsepoint
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: bh.contextweb.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: bh.contextweb.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
pr?exlist=mp_af_n-sk_n-mediarithmics_kr_n-ix-HMT_bsw_bk_n-y-HMT_n-semasio-ecm_n-kg-HMT_n-gg-HMT2_n-…:1 Refused to load the image 'https://match.prod.bidr.io/cookie-sync/stv?gdpr=0&gdpr_consent=' because it violates the following Content Security Policy directive: "default-src 'self' s.amazon-adsystem.com aax-eu.amazon-adsystem.com aax-fe.amazon-adsystem.com fonts.gstatic.com *.firefox.etp *.stickyadstv.com krxd.net serving-sys.com bluekai.com *.yahoo.com tremorhub.com *.adnxs.com samplicio.us semasio.net *.doubleclick.net *.samba.tv stickyadstv.com *.mookie1.com yahoo.com *.krxd.net yahoo.net gumgum.com *.samplicio.us *.bluekai.com samba.tv *.mediarithmics.com pubmatic.com zeotap.com *.tremorhub.com *.bidswitch.net *.fwmrm.net *.adform.net *.yahoo.net adform.net *.zeotap.com fwmrm.net demdex.net *.kargo.com *.casalemedia.com casalemedia.com bidswitch.net *.serving-sys.com mookie1.com *.gumgum.com *.demdex.net *.semasio.net *.pubmatic.com kargo.com". Note that 'img-src' was not explicitly set, so 'default-src' is used as a fallback.
Understand this error
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: e79434975e57fc56665ebc0fc7e40630.safeframe.googlesyndication.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: usync.vrtcal.com href: https://usync.vrtcal.com/i?ssp=1822&surl=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dvrtcal.com%26id%3D%24%24VRTCALUSER%24%24
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: usync.vrtcal.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: usync.vrtcal.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: sync.go.sonobi.com href: https://sync.go.sonobi.com/uc.html?pubid=91e92b73fd&redirect=https%3A%2F%2Fs.amazon-adsystem.com%2Fecm3%3Fex%3Dsonobi.com%26id%3D
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: sync.go.sonobi.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: sync.go.sonobi.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
container.html:17 [Violation] Avoid using document.write(). https://developers.google.com/web/updates/2016/08/removing-document-write
(anonymous) @ container.html:17
(anonymous) @ container.html:17
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: e79434975e57fc56665ebc0fc7e40630.safeframe.googlesyndication.com
dv3.js:175 [Violation] Avoid using document.write(). https://developers.google.com/web/updates/2016/08/removing-document-write
rk @ dv3.js:175
(anonymous) @ dv3.js:185
(anonymous) @ dv3.js:125
Gh @ dv3.js:124
(anonymous) @ dv3.js:125
(anonymous) @ dv3.js:185
(anonymous) @ dv3.js:186
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: googleads.g.doubleclick.net
pixel?d=CND8eBD_yoEBGI2blKUCMAE&v=APEucNWVxYLekQ_QdxHIZVxE4H0XWSS9PITNSbrADxT0cAzvLNfwIXD7qtzxs9Jd2…:1  GET https://sync.search.spotxchange.com/partner?adv_id=7025&redir=https%3A%2F%2Fcm.g.doubleclick.net%2Fpixel%3Fgoogle_nid%3Dspotxchange_dbm%26google_hm%3D%24SPOTX_BASE64_USER_ID net::ERR_NAME_NOT_RESOLVEDUnderstand this error
ad?dbm_c=AKAmf-CQWlRM6Y2hwL8vP4djY0QmUWfJTWK9JD25wnijRIxMONoVAbpIT-LLgmEycqHAgUWz1GC80elrAC617wPWg486Q3YQYYWDU6WQNVry1mMKk2K6BgM&cry=1&dbm_d=AKAmf-Ccf9WA3z2hBrds8uG5PxIXGAAVhYsdOEyPGdJGrdNX1wR2ZXryLEU-9fGn2QLdQ2V8YArsoGlnd5NXf4XGpwR-SSaIBvNwo7ZCOSSLrWyja6tEEB-uqUHweKI-cmhHlGbJb2UaWn-yCCbLiaSXx2V1dhjUD5kvRfAyktOdz335MBmngrLC_poVer1Furbg8DYvX6QgNv_5imOYe1uzhNIzGKULOflQRGbV0p0le3W-PHLe4mlKYMy_kSosotSnfrX79RVkv5QvqabuaNv0jQhTiHv_tUMKRMmlbE5SBGrBCQdt6CFcOIo5omCLbL0riGl-2MRDCCUU2qLXSaoDQlRauML3BHPPvVBKVR29AmdsoGky9r6u8Wm3xQMWA8CNM6YWFwjn9jsoMVeildLXS1eRs45h22uMjgVOBCsQVHEpi98__pD74S0qwvaYzgaxJxAsXDRiXqSrWyjtx-vgoJV-16w4-Os2KB_KjJe7Wn8r0U4SMZhyPqaGbx1P3WCr0zix-NsxrQnvQkpZ5eRAc1f6jiUkqedVqZ0s67OCNRUnDY-THR6Vxv2Geg-rNxg-4ChRONy2Euh1gJ316xu7cKEnnNpj7Mt49_4ENMvEuUf0_6o9iken75z0I0eZkDhQ7mG88FYV5Mp8R9AinEfkr7jhFz3eJdEMcL9gczyefmN155_-kyRsSVQd3ZzXGVS4kbXvrbnEmfHykW0HC9mW5_uXKoVvFXpTotnJ9bjhOkmwkhV52Yo6qKQ3rqZTkiBDPjLDBpKqY58DfNUZECA9L2Gk7vBDBlaD-6N0PJ7G56OOOSJZAaY8GnCNvsdDOXPSwdO_jYuUA74jt7OhEeAkpd-lyP0ayoCc6UJhJxoM0K6MxHvcZM062dZ5-jhkkziImsditYep2IOSvFVNPosCfRKAB_SAhy9XKbblgUiWmhEzV642RVSz2fT9x-AQHBXiRwxNdMuwdKXENranKdrck_mq5UOCyKloBFrJOrV0H6Iq8W5NYBit_DJOf4jRWV8MEznIy3quQ76_psGbn1AcfI1pfYZaLr5XsABKBuVSdfNqNhvOv-iXYEjs_zo35upEn0agOonwZjjpyAwTxKzQlQ203noFuFObGeREOdaeZ9oJshs92inoAQMfoJpVTpTTjuPiQbjCh065hi-9Bp9HwKAPh4S6dAnic4L1lt2coX2YjA16rkzIq-1NNKjhPHLtIOHvpYQs4aTv-waH8jVwcNOFC2pwBxkoGu2EPEwuUPueyyVJQEGHoYJd6aaYvol1K9WnjsTwz6nuN56aK6kgVyA8pTDqKCqhS5NP9jyg9zKQJ6MadibM_0_tLtYUqGd0q63v4p1u10TnJTeINpsCcKzC1laGK7j-anX24Q4OM_PhbKdaYqsNgPJ-tgHRZggSD3MBtshlfKU9p5ZbBn9QUGe4x9nzP-8zKwlNix1SHhOrdERi2PUYo6fXdUOSo11Ul92ts1guxWSed2It8vt8vMq4gB0leJ0Cj99F9Q8-r0sysaytCe2G2Cx-t8DOuVvObhamNVkCnd8ZQqRBBPEkcNtFA8sGOyDGasPXiK5yFCRWtqvndTO3m3Ogch5P-uOkeLLXFf4-mPTAjWTaKl6MPNfpQURqnOiFVzrKkiAjKLnOySs0znz3tNXaJv-FLeq6V8V06AoNO4B8JuHugCgEL8rXyQT5zcPY96u2OSI5N10Fgty1Kxp6f8Vxp_Dtu22IpQqgH6L1VHXQZwuaq7NM-dFMks7Xp7uyiaTUBmC50zgO7hz9k8ezAlVORrOVo3qc_-ThQpP8rHfp59-lk28fST8ZS3YN1gHZOTMrpZAuQ_aDnGFgcabPWFB484MLgmxU7LvytF_DZkrr_bVCaAcAaU9maH0D4Bcvo2Rzvp0EJsBeGHJMlDxJEHS_sBex9RBI4-4dqxSiOn3uk3MITyvoNg51yE4TW3eX6Q4RZ8JOA6DSXUQrsknd5QKbCeiKNuJNlrXT9ns-012wBMTTxT5PJJYYBoTIY5VzTBwfOevwwSKWrYE1xmkoOU5em2nfnc4i7V8q_XtVsAUHDC4HVkhWwP3rmUA2SEwHyFwU99HU0rM-NKhPkiV2-m2q8yrL62-1KMKZicdGtVi8mCfBLsuvXisb3TFlkRBXH_JaUam1YqvzxY_9Asj9dzJ0XqcBhj0KYALnorUcwdOzlUgOisrKsETM5e5doEyAqP0u_wfFbSiTLl9kOjS1pgZoiQS_lK2ROmEyhJXyWBOlnVughEmAic199Z9GUIXdEWaUcLJXJjNqium6oGvi0-Y00-DJeSIdxkhgo4QMiNxdJrxzj5wQ0aNHFPlHWJf_1orP8ehCYu_0XhhEwuf9R6iX3wwLQ37YyCmPxLhYcG5h04Sx1E7as20EYZof2ZshTAOImSCtWautbpQjY88S3OMflNvh89QzKjSKshs-GtFKk4GYBZDJr1LIMRJXWZfEnRncGBqKlp_iL-nGN-PRIDKcsm_00el-ZY8JljcM0bK_IOrBnmSaVJ-5DrF8NClVOUKwhLCJ_qvgOBFJiAmTmpjgKAqxdF_RaYHieUddi7edJaz4V9mlcJQg3VKMN4biXxfSPjb1UL8B2-g25gi9HsdwrGOBbFcDj0Xc9WwUcT05AIkarg8CSktb1CPEJRQ9Zs5DTG9Xy0gvVfMmvYEtIvcvgTGsVL7Vfl-oD_lA7NapR42MQtp1X4mA5FbhKNMxyfKcN3LXTWoFeNeGMpCBbDnoQsAiHMUZUV8UlnjofpwJ2DDdIX54EKPEZWfZhM_3mEwXACmlwt_UGIXrZ_va1XIvIW_5MEaWOQNOD2OJwiuaGmUJYanB5qWheiRFAV3fzabFtfj8Aj4SHRs5Kdt0S0aeqx8MMBHc1AmL41Pd8QWSt7I_2xt9WepShvYqF4K9KHyFlITUlFGSx94MHCVD_rAKFfs9DGOqlT4oLswlGbAcFfOdedDl84SypUQCa92LUlF0ikX8GMdpdZJ6_jcoFyN4iAat5thcfJohYPPk4sepNARYfnVje0dd_q99GfcpaLhUuQQDPqTBo8qON9bggM4axiTAcumGeeT2j93Qws_ETttmx43L8mUjh7BYKegLgMYX7OL0VcyZsrrEp7WQbr2aubk2SHM-o2hEJKRxHDTjjNq4boVn5-q2WTKdrnUCUourbWIdUS0ZN5fRHwDpDWKD1XGemgtxmKczWyMsSkwGbWTC7TjHMIxLsB-fSTkt2qrVEifynM01eEJ2duW0YgH8bAKQnMWgbNHCdVqsqAllO4zVzhcfIY4KIEHobYOKsdc39ltwzG1-9TmKQrJRN1MWTHz1eImO_9FOlemv1bytoXgJ4w4gAr7Zigifrhf4Qae2dOLRVGgANF6hVafNQx90Ox9gJdyf-xUAicLUIpF94zHgo7vC4xsA2UIlmBN_5GS4v18e__vCSTFm8a0a2HCElFNzwHVl8ZsTYohteB2EyeARm-gjwkO9y6i02tY5DLF56D2QTMUaKnvuXEYGqGki5ckolTf7OCgxmRZLMMch5yKzUQxaWNpOvTjgo3KCHAtb3-d_PPWQewtLfhydDf-4CKrrXb06-U1wncH20MQSIpMaDwjDZZ-5dswR1uqG5rd6p9Hx7QXyzmIAtdua8a35h4h7cLGB-KolbI46p9pteADG1ldH4LrWL4QBNVSIGyNrpPM_PFz52UbSAstpNA9LhIXYMFlZEYB43bXkHmGm3zjcIIzQbOrd7kZ-iYlnA8kyPurXOMx8NU5r_MyIkZmO8e7OmRFEZXRQaN8nfAYd75qdVAXd1z1Tl7AFVfMKmBjTaDSth7xHZfB_s7GCbMxF0lu9TDBivOgG4vRG1S3xb7pT_HRnAuLSvRENiwCimUouv9QLAqBDjdrJ90jkhm41QNyV1Y0tWxEE35dyZ1wQpbB8RSl0cXykKtOm3dcpxMottfIDGN6iSFkaYTQYptGeYqVR8HTwmSc6cdxtiMYi8LAiK6lynb49Rm6wy2LF2XlHL1kFw2cCtEKkICJCvn2sbinB5ifpCmGGEctaCDNshCYXvh-U8UkpokyU1GGHTLHlRu_kpipPKGbaatA_cJmLeFVwav6O62mKEqSIF04h3IWRs1znCcc2kxTmtGY_aQZn_O9E7yVMu5Mu-4j0qF8aeC8eZzsOyEHtxdzpIMNIxql4YNZrUB3gCB8SgGZEQdH6G5Pqod-b9aPX5yWigFvMco6SfJmJ93e3PKaru2Og8dSQDSSHrRR6M6OR5MJDKI3ig8BK4dvd4511rMFkxF30b3svm1BZhAEkFhd2O7QgiMZ84rLP4zrvUD1swHEem_EmIP8o84nWjhuPAQk2n4a3glUlCUZEH0_JaKDNNZ0B4kDXs2X2V3SK423PMn5INdqo27s7YAUwh_hZVYeqydY1zcJyDDKkRxpxsQknp8I5IQcVCSeD8LBFuXpK8UG0Bl5SnZPbtiBSZxY_0R7jtgNe6pIC-k19vtgiYz1Yf-5zdslqbaVXUWB3T_GfCo_cNxZxopKl5lRZ8z9-7BI&cid=CAQSpwEAwksa0TrIhr_8UYqGYmYC_2lgLOP-hBSemmLYp-p5q5pU_zKIgHmFc1VqC8aw_zG24MANqinIB5wLhUKd78cjsIlGAU0Y3OMKInPjfa5NgX4_iDrkG6mfUvtG7coim8a-CUvjylXt-pB6gdKA01yQzIaH1BE6VCvO521d--t_IPZVt1DEmDU5v-Q5zobkFFZVndbWpad5rhu8xyhbuuaZKEdxPqd4vBgB&dv3_ver=m202510220101&nel=1&rfl=https%3A%2F%2Fwww.imdb.com%2F&ds=l&xdt=1&ct=76&iif=1&cor=7068881448103632896&adk=2228999114&idt=152&cac=0&dtd=19:1 [Violation] Avoid using document.write(). https://developers.google.com/web/updates/2016/08/removing-document-write
(anonymous) @ ad?dbm_c=AKAmf-CQWlRM6Y2hwL8vP4djY0QmUWfJTWK9JD25wnijRIxMONoVAbpIT-LLgmEycqHAgUWz1GC80elrAC617wPWg486Q3YQYYWDU6WQNVry1mMKk2K6BgM&cry=1&dbm_d=AKAmf-Ccf9WA3z2hBrds8uG5PxIXGAAVhYsdOEyPGdJGrdNX1wR2ZXryLEU-9fGn2QLdQ2V8YArsoGlnd5NXf4XGpwR-SSaIBvNwo7ZCOSSLrWyja6tEEB-uqUHweKI-cmhHlGbJb2UaWn-yCCbLiaSXx2V1dhjUD5kvRfAyktOdz335MBmngrLC_poVer1Furbg8DYvX6QgNv_5imOYe1uzhNIzGKULOflQRGbV0p0le3W-PHLe4mlKYMy_kSosotSnfrX79RVkv5QvqabuaNv0jQhTiHv_tUMKRMmlbE5SBGrBCQdt6CFcOIo5omCLbL0riGl-2MRDCCUU2qLXSaoDQlRauML3BHPPvVBKVR29AmdsoGky9r6u8Wm3xQMWA8CNM6YWFwjn9jsoMVeildLXS1eRs45h22uMjgVOBCsQVHEpi98__pD74S0qwvaYzgaxJxAsXDRiXqSrWyjtx-vgoJV-16w4-Os2KB_KjJe7Wn8r0U4SMZhyPqaGbx1P3WCr0zix-NsxrQnvQkpZ5eRAc1f6jiUkqedVqZ0s67OCNRUnDY-THR6Vxv2Geg-rNxg-4ChRONy2Euh1gJ316xu7cKEnnNpj7Mt49_4ENMvEuUf0_6o9iken75z0I0eZkDhQ7mG88FYV5Mp8R9AinEfkr7jhFz3eJdEMcL9gczyefmN155_-kyRsSVQd3ZzXGVS4kbXvrbnEmfHykW0HC9mW5_uXKoVvFXpTotnJ9bjhOkmwkhV52Yo6qKQ3rqZTkiBDPjLDBpKqY58DfNUZECA9L2Gk7vBDBlaD-6N0PJ7G56OOOSJZAaY8GnCNvsdDOXPSwdO_jYuUA74jt7OhEeAkpd-lyP0ayoCc6UJhJxoM0K6MxHvcZM062dZ5-jhkkziImsditYep2IOSvFVNPosCfRKAB_SAhy9XKbblgUiWmhEzV642RVSz2fT9x-AQHBXiRwxNdMuwdKXENranKdrck_mq5UOCyKloBFrJOrV0H6Iq8W5NYBit_DJOf4jRWV8MEznIy3quQ76_psGbn1AcfI1pfYZaLr5XsABKBuVSdfNqNhvOv-iXYEjs_zo35upEn0agOonwZjjpyAwTxKzQlQ203noFuFObGeREOdaeZ9oJshs92inoAQMfoJpVTpTTjuPiQbjCh065hi-9Bp9HwKAPh4S6dAnic4L1lt2coX2YjA16rkzIq-1NNKjhPHLtIOHvpYQs4aTv-waH8jVwcNOFC2pwBxkoGu2EPEwuUPueyyVJQEGHoYJd6aaYvol1K9WnjsTwz6nuN56aK6kgVyA8pTDqKCqhS5NP9jyg9zKQJ6MadibM_0_tLtYUqGd0q63v4p1u10TnJTeINpsCcKzC1laGK7j-anX24Q4OM_PhbKdaYqsNgPJ-tgHRZggSD3MBtshlfKU9p5ZbBn9QUGe4x9nzP-8zKwlNix1SHhOrdERi2PUYo6fXdUOSo11Ul92ts1guxWSed2It8vt8vMq4gB0leJ0Cj99F9Q8-r0sysaytCe2G2Cx-t8DOuVvObhamNVkCnd8ZQqRBBPEkcNtFA8sGOyDGasPXiK5yFCRWtqvndTO3m3Ogch5P-uOkeLLXFf4-mPTAjWTaKl6MPNfpQURqnOiFVzrKkiAjKLnOySs0znz3tNXaJv-FLeq6V8V06AoNO4B8JuHugCgEL8rXyQT5zcPY96u2OSI5N10Fgty1Kxp6f8Vxp_Dtu22IpQqgH6L1VHXQZwuaq7NM-dFMks7Xp7uyiaTUBmC50zgO7hz9k8ezAlVORrOVo3qc_-ThQpP8rHfp59-lk28fST8ZS3YN1gHZOTMrpZAuQ_aDnGFgcabPWFB484MLgmxU7LvytF_DZkrr_bVCaAcAaU9maH0D4Bcvo2Rzvp0EJsBeGHJMlDxJEHS_sBex9RBI4-4dqxSiOn3uk3MITyvoNg51yE4TW3eX6Q4RZ8JOA6DSXUQrsknd5QKbCeiKNuJNlrXT9ns-012wBMTTxT5PJJYYBoTIY5VzTBwfOevwwSKWrYE1xmkoOU5em2nfnc4i7V8q_XtVsAUHDC4HVkhWwP3rmUA2SEwHyFwU99HU0rM-NKhPkiV2-m2q8yrL62-1KMKZicdGtVi8mCfBLsuvXisb3TFlkRBXH_JaUam1YqvzxY_9Asj9dzJ0XqcBhj0KYALnorUcwdOzlUgOisrKsETM5e5doEyAqP0u_wfFbSiTLl9kOjS1pgZoiQS_lK2ROmEyhJXyWBOlnVughEmAic199Z9GUIXdEWaUcLJXJjNqium6oGvi0-Y00-DJeSIdxkhgo4QMiNxdJrxzj5wQ0aNHFPlHWJf_1orP8ehCYu_0XhhEwuf9R6iX3wwLQ37YyCmPxLhYcG5h04Sx1E7as20EYZof2ZshTAOImSCtWautbpQjY88S3OMflNvh89QzKjSKshs-GtFKk4GYBZDJr1LIMRJXWZfEnRncGBqKlp_iL-nGN-PRIDKcsm_00el-ZY8JljcM0bK_IOrBnmSaVJ-5DrF8NClVOUKwhLCJ_qvgOBFJiAmTmpjgKAqxdF_RaYHieUddi7edJaz4V9mlcJQg3VKMN4biXxfSPjb1UL8B2-g25gi9HsdwrGOBbFcDj0Xc9WwUcT05AIkarg8CSktb1CPEJRQ9Zs5DTG9Xy0gvVfMmvYEtIvcvgTGsVL7Vfl-oD_lA7NapR42MQtp1X4mA5FbhKNMxyfKcN3LXTWoFeNeGMpCBbDnoQsAiHMUZUV8UlnjofpwJ2DDdIX54EKPEZWfZhM_3mEwXACmlwt_UGIXrZ_va1XIvIW_5MEaWOQNOD2OJwiuaGmUJYanB5qWheiRFAV3fzabFtfj8Aj4SHRs5Kdt0S0aeqx8MMBHc1AmL41Pd8QWSt7I_2xt9WepShvYqF4K9KHyFlITUlFGSx94MHCVD_rAKFfs9DGOqlT4oLswlGbAcFfOdedDl84SypUQCa92LUlF0ikX8GMdpdZJ6_jcoFyN4iAat5thcfJohYPPk4sepNARYfnVje0dd_q99GfcpaLhUuQQDPqTBo8qON9bggM4axiTAcumGeeT2j93Qws_ETttmx43L8mUjh7BYKegLgMYX7OL0VcyZsrrEp7WQbr2aubk2SHM-o2hEJKRxHDTjjNq4boVn5-q2WTKdrnUCUourbWIdUS0ZN5fRHwDpDWKD1XGemgtxmKczWyMsSkwGbWTC7TjHMIxLsB-fSTkt2qrVEifynM01eEJ2duW0YgH8bAKQnMWgbNHCdVqsqAllO4zVzhcfIY4KIEHobYOKsdc39ltwzG1-9TmKQrJRN1MWTHz1eImO_9FOlemv1bytoXgJ4w4gAr7Zigifrhf4Qae2dOLRVGgANF6hVafNQx90Ox9gJdyf-xUAicLUIpF94zHgo7vC4xsA2UIlmBN_5GS4v18e__vCSTFm8a0a2HCElFNzwHVl8ZsTYohteB2EyeARm-gjwkO9y6i02tY5DLF56D2QTMUaKnvuXEYGqGki5ckolTf7OCgxmRZLMMch5yKzUQxaWNpOvTjgo3KCHAtb3-d_PPWQewtLfhydDf-4CKrrXb06-U1wncH20MQSIpMaDwjDZZ-5dswR1uqG5rd6p9Hx7QXyzmIAtdua8a35h4h7cLGB-KolbI46p9pteADG1ldH4LrWL4QBNVSIGyNrpPM_PFz52UbSAstpNA9LhIXYMFlZEYB43bXkHmGm3zjcIIzQbOrd7kZ-iYlnA8kyPurXOMx8NU5r_MyIkZmO8e7OmRFEZXRQaN8nfAYd75qdVAXd1z1Tl7AFVfMKmBjTaDSth7xHZfB_s7GCbMxF0lu9TDBivOgG4vRG1S3xb7pT_HRnAuLSvRENiwCimUouv9QLAqBDjdrJ90jkhm41QNyV1Y0tWxEE35dyZ1wQpbB8RSl0cXykKtOm3dcpxMottfIDGN6iSFkaYTQYptGeYqVR8HTwmSc6cdxtiMYi8LAiK6lynb49Rm6wy2LF2XlHL1kFw2cCtEKkICJCvn2sbinB5ifpCmGGEctaCDNshCYXvh-U8UkpokyU1GGHTLHlRu_kpipPKGbaatA_cJmLeFVwav6O62mKEqSIF04h3IWRs1znCcc2kxTmtGY_aQZn_O9E7yVMu5Mu-4j0qF8aeC8eZzsOyEHtxdzpIMNIxql4YNZrUB3gCB8SgGZEQdH6G5Pqod-b9aPX5yWigFvMco6SfJmJ93e3PKaru2Og8dSQDSSHrRR6M6OR5MJDKI3ig8BK4dvd4511rMFkxF30b3svm1BZhAEkFhd2O7QgiMZ84rLP4zrvUD1swHEem_EmIP8o84nWjhuPAQk2n4a3glUlCUZEH0_JaKDNNZ0B4kDXs2X2V3SK423PMn5INdqo27s7YAUwh_hZVYeqydY1zcJyDDKkRxpxsQknp8I5IQcVCSeD8LBFuXpK8UG0Bl5SnZPbtiBSZxY_0R7jtgNe6pIC-k19vtgiYz1Yf-5zdslqbaVXUWB3T_GfCo_cNxZxopKl5lRZ8z9-7BI&cid=CAQSpwEAwksa0TrIhr_8UYqGYmYC_2lgLOP-hBSemmLYp-p5q5pU_zKIgHmFc1VqC8aw_zG24MANqinIB5wLhUKd78cjsIlGAU0Y3OMKInPjfa5NgX4_iDrkG6mfUvtG7coim8a-CUvjylXt-pB6gdKA01yQzIaH1BE6VCvO521d--t_IPZVt1DEmDU5v-Q5zobkFFZVndbWpad5rhu8xyhbuuaZKEdxPqd4vBgB&dv3_ver=m202510220101&nel=1&rfl=https%3A%2F%2Fwww.imdb.com%2F&ds=l&xdt=1&ct=76&iif=1&cor=7068881448103632896&adk=2228999114&idt=152&cac=0&dtd=19:1
VM1062:1 [Violation] Avoid using document.write(). https://developers.google.com/web/updates/2016/08/removing-document-write
G @ VM1062:1
N @ VM1062:1
(anonymous) @ VM1062:1
(anonymous) @ VM1062:1
(anonymous) @ ad?dbm_c=AKAmf-CQWlRM6Y2hwL8vP4djY0QmUWfJTWK9JD25wnijRIxMONoVAbpIT-LLgmEycqHAgUWz1GC80elrAC617wPWg486Q3YQYYWDU6WQNVry1mMKk2K6BgM&cry=1&dbm_d=AKAmf-Ccf9WA3z2hBrds8uG5PxIXGAAVhYsdOEyPGdJGrdNX1wR2ZXryLEU-9fGn2QLdQ2V8YArsoGlnd5NXf4XGpwR-SSaIBvNwo7ZCOSSLrWyja6tEEB-uqUHweKI-cmhHlGbJb2UaWn-yCCbLiaSXx2V1dhjUD5kvRfAyktOdz335MBmngrLC_poVer1Furbg8DYvX6QgNv_5imOYe1uzhNIzGKULOflQRGbV0p0le3W-PHLe4mlKYMy_kSosotSnfrX79RVkv5QvqabuaNv0jQhTiHv_tUMKRMmlbE5SBGrBCQdt6CFcOIo5omCLbL0riGl-2MRDCCUU2qLXSaoDQlRauML3BHPPvVBKVR29AmdsoGky9r6u8Wm3xQMWA8CNM6YWFwjn9jsoMVeildLXS1eRs45h22uMjgVOBCsQVHEpi98__pD74S0qwvaYzgaxJxAsXDRiXqSrWyjtx-vgoJV-16w4-Os2KB_KjJe7Wn8r0U4SMZhyPqaGbx1P3WCr0zix-NsxrQnvQkpZ5eRAc1f6jiUkqedVqZ0s67OCNRUnDY-THR6Vxv2Geg-rNxg-4ChRONy2Euh1gJ316xu7cKEnnNpj7Mt49_4ENMvEuUf0_6o9iken75z0I0eZkDhQ7mG88FYV5Mp8R9AinEfkr7jhFz3eJdEMcL9gczyefmN155_-kyRsSVQd3ZzXGVS4kbXvrbnEmfHykW0HC9mW5_uXKoVvFXpTotnJ9bjhOkmwkhV52Yo6qKQ3rqZTkiBDPjLDBpKqY58DfNUZECA9L2Gk7vBDBlaD-6N0PJ7G56OOOSJZAaY8GnCNvsdDOXPSwdO_jYuUA74jt7OhEeAkpd-lyP0ayoCc6UJhJxoM0K6MxHvcZM062dZ5-jhkkziImsditYep2IOSvFVNPosCfRKAB_SAhy9XKbblgUiWmhEzV642RVSz2fT9x-AQHBXiRwxNdMuwdKXENranKdrck_mq5UOCyKloBFrJOrV0H6Iq8W5NYBit_DJOf4jRWV8MEznIy3quQ76_psGbn1AcfI1pfYZaLr5XsABKBuVSdfNqNhvOv-iXYEjs_zo35upEn0agOonwZjjpyAwTxKzQlQ203noFuFObGeREOdaeZ9oJshs92inoAQMfoJpVTpTTjuPiQbjCh065hi-9Bp9HwKAPh4S6dAnic4L1lt2coX2YjA16rkzIq-1NNKjhPHLtIOHvpYQs4aTv-waH8jVwcNOFC2pwBxkoGu2EPEwuUPueyyVJQEGHoYJd6aaYvol1K9WnjsTwz6nuN56aK6kgVyA8pTDqKCqhS5NP9jyg9zKQJ6MadibM_0_tLtYUqGd0q63v4p1u10TnJTeINpsCcKzC1laGK7j-anX24Q4OM_PhbKdaYqsNgPJ-tgHRZggSD3MBtshlfKU9p5ZbBn9QUGe4x9nzP-8zKwlNix1SHhOrdERi2PUYo6fXdUOSo11Ul92ts1guxWSed2It8vt8vMq4gB0leJ0Cj99F9Q8-r0sysaytCe2G2Cx-t8DOuVvObhamNVkCnd8ZQqRBBPEkcNtFA8sGOyDGasPXiK5yFCRWtqvndTO3m3Ogch5P-uOkeLLXFf4-mPTAjWTaKl6MPNfpQURqnOiFVzrKkiAjKLnOySs0znz3tNXaJv-FLeq6V8V06AoNO4B8JuHugCgEL8rXyQT5zcPY96u2OSI5N10Fgty1Kxp6f8Vxp_Dtu22IpQqgH6L1VHXQZwuaq7NM-dFMks7Xp7uyiaTUBmC50zgO7hz9k8ezAlVORrOVo3qc_-ThQpP8rHfp59-lk28fST8ZS3YN1gHZOTMrpZAuQ_aDnGFgcabPWFB484MLgmxU7LvytF_DZkrr_bVCaAcAaU9maH0D4Bcvo2Rzvp0EJsBeGHJMlDxJEHS_sBex9RBI4-4dqxSiOn3uk3MITyvoNg51yE4TW3eX6Q4RZ8JOA6DSXUQrsknd5QKbCeiKNuJNlrXT9ns-012wBMTTxT5PJJYYBoTIY5VzTBwfOevwwSKWrYE1xmkoOU5em2nfnc4i7V8q_XtVsAUHDC4HVkhWwP3rmUA2SEwHyFwU99HU0rM-NKhPkiV2-m2q8yrL62-1KMKZicdGtVi8mCfBLsuvXisb3TFlkRBXH_JaUam1YqvzxY_9Asj9dzJ0XqcBhj0KYALnorUcwdOzlUgOisrKsETM5e5doEyAqP0u_wfFbSiTLl9kOjS1pgZoiQS_lK2ROmEyhJXyWBOlnVughEmAic199Z9GUIXdEWaUcLJXJjNqium6oGvi0-Y00-DJeSIdxkhgo4QMiNxdJrxzj5wQ0aNHFPlHWJf_1orP8ehCYu_0XhhEwuf9R6iX3wwLQ37YyCmPxLhYcG5h04Sx1E7as20EYZof2ZshTAOImSCtWautbpQjY88S3OMflNvh89QzKjSKshs-GtFKk4GYBZDJr1LIMRJXWZfEnRncGBqKlp_iL-nGN-PRIDKcsm_00el-ZY8JljcM0bK_IOrBnmSaVJ-5DrF8NClVOUKwhLCJ_qvgOBFJiAmTmpjgKAqxdF_RaYHieUddi7edJaz4V9mlcJQg3VKMN4biXxfSPjb1UL8B2-g25gi9HsdwrGOBbFcDj0Xc9WwUcT05AIkarg8CSktb1CPEJRQ9Zs5DTG9Xy0gvVfMmvYEtIvcvgTGsVL7Vfl-oD_lA7NapR42MQtp1X4mA5FbhKNMxyfKcN3LXTWoFeNeGMpCBbDnoQsAiHMUZUV8UlnjofpwJ2DDdIX54EKPEZWfZhM_3mEwXACmlwt_UGIXrZ_va1XIvIW_5MEaWOQNOD2OJwiuaGmUJYanB5qWheiRFAV3fzabFtfj8Aj4SHRs5Kdt0S0aeqx8MMBHc1AmL41Pd8QWSt7I_2xt9WepShvYqF4K9KHyFlITUlFGSx94MHCVD_rAKFfs9DGOqlT4oLswlGbAcFfOdedDl84SypUQCa92LUlF0ikX8GMdpdZJ6_jcoFyN4iAat5thcfJohYPPk4sepNARYfnVje0dd_q99GfcpaLhUuQQDPqTBo8qON9bggM4axiTAcumGeeT2j93Qws_ETttmx43L8mUjh7BYKegLgMYX7OL0VcyZsrrEp7WQbr2aubk2SHM-o2hEJKRxHDTjjNq4boVn5-q2WTKdrnUCUourbWIdUS0ZN5fRHwDpDWKD1XGemgtxmKczWyMsSkwGbWTC7TjHMIxLsB-fSTkt2qrVEifynM01eEJ2duW0YgH8bAKQnMWgbNHCdVqsqAllO4zVzhcfIY4KIEHobYOKsdc39ltwzG1-9TmKQrJRN1MWTHz1eImO_9FOlemv1bytoXgJ4w4gAr7Zigifrhf4Qae2dOLRVGgANF6hVafNQx90Ox9gJdyf-xUAicLUIpF94zHgo7vC4xsA2UIlmBN_5GS4v18e__vCSTFm8a0a2HCElFNzwHVl8ZsTYohteB2EyeARm-gjwkO9y6i02tY5DLF56D2QTMUaKnvuXEYGqGki5ckolTf7OCgxmRZLMMch5yKzUQxaWNpOvTjgo3KCHAtb3-d_PPWQewtLfhydDf-4CKrrXb06-U1wncH20MQSIpMaDwjDZZ-5dswR1uqG5rd6p9Hx7QXyzmIAtdua8a35h4h7cLGB-KolbI46p9pteADG1ldH4LrWL4QBNVSIGyNrpPM_PFz52UbSAstpNA9LhIXYMFlZEYB43bXkHmGm3zjcIIzQbOrd7kZ-iYlnA8kyPurXOMx8NU5r_MyIkZmO8e7OmRFEZXRQaN8nfAYd75qdVAXd1z1Tl7AFVfMKmBjTaDSth7xHZfB_s7GCbMxF0lu9TDBivOgG4vRG1S3xb7pT_HRnAuLSvRENiwCimUouv9QLAqBDjdrJ90jkhm41QNyV1Y0tWxEE35dyZ1wQpbB8RSl0cXykKtOm3dcpxMottfIDGN6iSFkaYTQYptGeYqVR8HTwmSc6cdxtiMYi8LAiK6lynb49Rm6wy2LF2XlHL1kFw2cCtEKkICJCvn2sbinB5ifpCmGGEctaCDNshCYXvh-U8UkpokyU1GGHTLHlRu_kpipPKGbaatA_cJmLeFVwav6O62mKEqSIF04h3IWRs1znCcc2kxTmtGY_aQZn_O9E7yVMu5Mu-4j0qF8aeC8eZzsOyEHtxdzpIMNIxql4YNZrUB3gCB8SgGZEQdH6G5Pqod-b9aPX5yWigFvMco6SfJmJ93e3PKaru2Og8dSQDSSHrRR6M6OR5MJDKI3ig8BK4dvd4511rMFkxF30b3svm1BZhAEkFhd2O7QgiMZ84rLP4zrvUD1swHEem_EmIP8o84nWjhuPAQk2n4a3glUlCUZEH0_JaKDNNZ0B4kDXs2X2V3SK423PMn5INdqo27s7YAUwh_hZVYeqydY1zcJyDDKkRxpxsQknp8I5IQcVCSeD8LBFuXpK8UG0Bl5SnZPbtiBSZxY_0R7jtgNe6pIC-k19vtgiYz1Yf-5zdslqbaVXUWB3T_GfCo_cNxZxopKl5lRZ8z9-7BI&cid=CAQSpwEAwksa0TrIhr_8UYqGYmYC_2lgLOP-hBSemmLYp-p5q5pU_zKIgHmFc1VqC8aw_zG24MANqinIB5wLhUKd78cjsIlGAU0Y3OMKInPjfa5NgX4_iDrkG6mfUvtG7coim8a-CUvjylXt-pB6gdKA01yQzIaH1BE6VCvO521d--t_IPZVt1DEmDU5v-Q5zobkFFZVndbWpad5rhu8xyhbuuaZKEdxPqd4vBgB&dv3_ver=m202510220101&nel=1&rfl=https%3A%2F%2Fwww.imdb.com%2F&ds=l&xdt=1&ct=76&iif=1&cor=7068881448103632896&adk=2228999114&idt=152&cac=0&dtd=19:1
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: ep2.adtrafficquality.google href: https://ep2.adtrafficquality.google/sodar/Klz6NWr5.html
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: ep2.adtrafficquality.google
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: ep2.adtrafficquality.google
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:931 INFO - (Geo location) persisted cached location data
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:931 INFO - (Geo location) persisted cached location data
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: s0.2mdn.net href: https://s0.2mdn.net/sadbundle/349778392810416633/index.html?e=69&leftOffset=0&topOffset=0&c=SxlyAYCxXc&t=1&renderingType=2&ev=01_262
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: s0.2mdn.net
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: s0.2mdn.net
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
7[Violation] Added non-passive event listener to a scroll-blocking <some> event. Consider marking event handler as 'passive' to make the page more responsive. See <URL>
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
dvbm.js:2 [Violation] 'setTimeout' handler took 50ms
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
dvbm.js:2 [Violation] 'setTimeout' handler took 51ms
[Violation] 'setTimeout' handler took 316ms
content.js:66 [Violation] 'setTimeout' handler took 316ms
[Violation] Forced reflow while executing JavaScript took 106ms
model-viewer.js:19 [Violation] 'requestAnimationFrame' handler took 576ms
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:656 [HG LOGGER] Ad/tracking domain detected - skipping to avoid interference: s.amazon-adsystem.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:670 [HG LOGGER] Current location - host: ep2.adtrafficquality.google href: https://ep2.adtrafficquality.google/sodar/sodar2/237/runner.html
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:673 [HG LOGGER] Proceeding with setup for host: ep2.adtrafficquality.google
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:1231 [HG LOGGER] Hooks installed safely for host: ep2.adtrafficquality.google
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:21 [HG LOGGER] Script starting...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:669 [HG LOGGER] Script initializing...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:670 [HG LOGGER] Current location - host: www.google.com href: https://www.google.com/recaptcha/api2/aframe
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:671 [HG LOGGER] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:672 [HG LOGGER] Frame context - top window: false iframe: true
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:673 [HG LOGGER] Proceeding with setup for host: www.google.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:863 [HG LOGGER] Starting hook installation...
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:865 [HG LOGGER] Step 1: Creating methods array
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:868 [HG LOGGER] Step 2: Binding original console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:873 [HG LOGGER] Step 3: Storing original methods globally
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:877 [HG LOGGER] Step 4: Updating safeLog
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:881 [HG LOGGER] Step 5: Defining capture function
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:915 [HG LOGGER] Step 6: Installing hooks for console methods
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for log on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for info on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for warn on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for error on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:940 [HG LOGGER] Installed hook for debug on page console
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:946 [HG LOGGER] Step 7: Verifying hooks are installed
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:948 [HG LOGGER] Console hooks installed for methods: (5) ['log', 'info', 'warn', 'error', 'debug']
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:954 [HG LOGGER] Hook verification (page console): log: HOOKED, info: HOOKED, warn: HOOKED, error: HOOKED, debug: HOOKED
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:956 [HG LOGGER] Step 8: Creating debug object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1159 [HG LOGGER] Step 9: Debug object created successfully
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1161 [HG LOGGER] Debug object created successfully. Try: HGLoggerDebug.testCapture()
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1231 [HG LOGGER] Hooks installed safely for host: www.google.com
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1305 [HG LOGGER] HGLoggerDebug verification - exists: true type: object
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d0…:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
userscript.html?name=HG-Logger-CSP-compliant%252C-SPA-aware%252C-configurable-sites.user.js&id=66d09c0c-0c8b-4d4e-891c-621223afc404:1954 [HG LOGGER] Running in iframe - skipping UI (console capture still active)
*/