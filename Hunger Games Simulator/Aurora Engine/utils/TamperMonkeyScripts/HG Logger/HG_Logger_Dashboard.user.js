// ==UserScript==
// @name HG Logger - Dashboard
// @namespace otter.hg-logger-system
// @version 1.1
// @description Centralized dashboard for viewing logs captured across all websites
// @author Otter Logic LLC
// @match file:///*hg-logger-dashboard.html*
// @match file:///*test-dashboard.html*
// @match http://localhost*/hg-logger-dashboard.html*
// @match http://127.0.0.1*/hg-logger-dashboard.html*
// @grant unsafeWindow
// @grant GM_getValue
// @run-at document-start
// ==/UserScript==

(function() {
  'use strict';

  console.log('[HG DASHBOARD] Initializing...');
  
  // Use TamperMonkey's shared GM storage (same as Collector)
  // This way we read from the same storage location regardless of origin
  const STORAGE_KEY = 'hg_logger_all_logs';
  const STATS_KEY = 'hg_logger_stats';
  const CONFIG_KEY = 'hg_logger_config';

  // Helper to read from shared storage
  function loadLogsFromGMStorage() {
    try {
      const data = GM_getValue(STORAGE_KEY);
      return data ? JSON.parse(data) : {};
    } catch (e) {
      console.log('[HG DASHBOARD] Failed to load from GM storage:', e.message);
      return {};
    }
  }

  function loadStatsFromGMStorage() {
    try {
      const data = GM_getValue(STATS_KEY);
      return data ? JSON.parse(data) : {};
    } catch (e) {
      console.log('[HG DASHBOARD] Failed to load stats:', e.message);
      return {};
    }
  }

  function loadConfigFromGMStorage() {
    try {
      const data = GM_getValue(CONFIG_KEY);
      return data ? JSON.parse(data) : DEFAULT_CONFIG;
    } catch (e) {
      return DEFAULT_CONFIG;
    }
  }

  // Use unsafeWindow.localStorage for UI state only (settings, filters)
  const storage = unsafeWindow.localStorage;

  // ===== DEFAULT CONFIG =====
  const DEFAULT_CONFIG = {
    autoRefresh: true,
    refreshInterval: 2000,
    maxLogsDisplay: 500,
    colorCoding: true,
    timestampFormat: 'ISO',
    keywords: {
      error: { color: '#ff6b6b', enabled: true },
      warning: { color: '#feca57', enabled: true },
      success: { color: '#48dbfb', enabled: true },
      info: { color: '#1dd1a1', enabled: true }
    }
  };

  // ===== STATE =====
  let currentConfig = { ...DEFAULT_CONFIG };
  let currentFilter = { host: 'all', method: 'all', search: '' };
  let autoRefreshInterval = null;
  let allLogs = {};
  let stats = {};

  // ===== INJECT STYLES =====
  const styleContent = `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }
    
    #hg-dashboard {
      max-width: 1600px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      overflow: hidden;
    }
    
    /* Header */
    .dashboard-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .dashboard-title {
      font-size: 32px;
      font-weight: 700;
      text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .dashboard-stats {
      display: flex;
      gap: 30px;
      font-size: 14px;
    }
    
    .stat-item {
      text-align: center;
      background: rgba(255,255,255,0.2);
      padding: 10px 20px;
      border-radius: 8px;
    }
    
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      display: block;
    }
    
    .stat-label {
      font-size: 11px;
      text-transform: uppercase;
      opacity: 0.9;
    }
    
    /* Controls */
    .dashboard-controls {
      display: flex;
      gap: 15px;
      padding: 25px 40px;
      background: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
      flex-wrap: wrap;
      align-items: center;
    }
    
    .control-group {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    
    .control-label {
      font-size: 13px;
      font-weight: 600;
      color: #495057;
    }
    
    select, input[type="search"] {
      padding: 8px 15px;
      border: 2px solid #dee2e6;
      border-radius: 6px;
      font-size: 14px;
      transition: all 0.2s;
      background: white;
    }
    
    select:focus, input[type="search"]:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    select {
      cursor: pointer;
      min-width: 200px;
    }
    
    input[type="search"] {
      min-width: 300px;
    }
    
    .btn {
      padding: 8px 20px;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .btn-secondary {
      background: #6c757d;
      color: white;
    }
    
    .btn-secondary:hover {
      background: #5a6268;
    }
    
    .btn-danger {
      background: #dc3545;
      color: white;
    }
    
    .btn-danger:hover {
      background: #c82333;
    }
    
    .btn-success {
      background: #28a745;
      color: white;
    }
    
    .btn-success:hover {
      background: #218838;
    }
    
    /* Logs Display */
    .logs-container {
      padding: 30px 40px;
      background: white;
      max-height: calc(100vh - 400px);
      overflow-y: auto;
    }
    
    .log-entry {
      padding: 12px 16px;
      margin-bottom: 8px;
      border-left: 4px solid #dee2e6;
      background: #f8f9fa;
      border-radius: 4px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      transition: all 0.2s;
    }
    
    .log-entry:hover {
      background: #e9ecef;
      transform: translateX(4px);
    }
    
    .log-entry.log-log { border-left-color: #6c757d; }
    .log-entry.log-info { border-left-color: #17a2b8; }
    .log-entry.log-warn { border-left-color: #ffc107; background: #fff9e6; }
    .log-entry.log-error { border-left-color: #dc3545; background: #ffe6e6; }
    .log-entry.log-debug { border-left-color: #6f42c1; }
    
    .log-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 11px;
      color: #6c757d;
    }
    
    .log-method {
      font-weight: bold;
      text-transform: uppercase;
      padding: 2px 8px;
      border-radius: 3px;
      background: white;
    }
    
    .log-timestamp {
      opacity: 0.7;
    }
    
    .log-content {
      word-wrap: break-word;
      white-space: pre-wrap;
    }
    
    .log-url {
      font-size: 11px;
      color: #007bff;
      margin-top: 6px;
      opacity: 0.8;
    }
    
    .no-logs {
      text-align: center;
      padding: 60px 20px;
      color: #6c757d;
      font-size: 18px;
    }
    
    .no-logs-icon {
      font-size: 64px;
      margin-bottom: 20px;
      opacity: 0.3;
    }
    
    /* Modal */
    .modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.7);
      z-index: 10000;
      align-items: center;
      justify-content: center;
    }
    
    .modal.active {
      display: flex;
    }
    
    .modal-content {
      background: white;
      padding: 30px;
      border-radius: 12px;
      max-width: 600px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    .modal-title {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 20px;
      color: #333;
    }
    
    .modal-footer {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #dee2e6;
    }
    
    .config-section {
      margin-bottom: 25px;
    }
    
    .config-section-title {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 12px;
      color: #495057;
    }
    
    .config-option {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      margin-bottom: 8px;
    }
    
    .config-option label {
      font-size: 14px;
      color: #333;
    }
    
    input[type="checkbox"] {
      width: 20px;
      height: 20px;
      cursor: pointer;
    }
    
    input[type="number"] {
      width: 100px;
      padding: 6px 12px;
      border: 2px solid #dee2e6;
      border-radius: 4px;
      font-size: 14px;
    }
    
    /* Auto-refresh indicator */
    .refresh-indicator {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: rgba(102, 126, 234, 0.95);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 13px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }
    
    /* Scrollbar */
    .logs-container::-webkit-scrollbar {
      width: 10px;
    }
    
    .logs-container::-webkit-scrollbar-track {
      background: #f1f1f1;
    }
    
    .logs-container::-webkit-scrollbar-thumb {
      background: #667eea;
      border-radius: 5px;
    }
    
    .logs-container::-webkit-scrollbar-thumb:hover {
      background: #764ba2;
    }
  `;
  
  // Apply styles to document
  function injectStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = styleContent;
    if (document.head) {
      document.head.appendChild(styleElement);
    } else {
      document.documentElement.appendChild(styleElement);
    }
  }

  // ===== HELPER FUNCTIONS =====
  function loadConfig() {
    try {
      const saved = storage.getItem(CONFIG_KEY);
      if (saved) {
        currentConfig = { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.error('[HG DASHBOARD] Failed to load config:', e);
      currentConfig = { ...DEFAULT_CONFIG };
    }
  }

  function saveConfig() {
    try {
      storage.setItem(CONFIG_KEY, JSON.stringify(currentConfig));
    } catch (e) {
      console.error('[HG DASHBOARD] Failed to save config:', e);
    }
  }

  function loadLogs() {
    try {
      // Load from TamperMonkey's shared GM storage (where Collector stores data)
      allLogs = loadLogsFromGMStorage();
      stats = loadStatsFromGMStorage();
    } catch (e) {
      console.error('[HG DASHBOARD] Failed to load logs:', e);
      allLogs = {};
      stats = {};
    }
  }

  function formatTimestamp(isoString) {
    const date = new Date(isoString);
    if (currentConfig.timestampFormat === 'ISO') {
      return isoString;
    }
    return date.toLocaleString();
  }

  function highlightKeywords(text) {
    if (!currentConfig.colorCoding || typeof text !== 'string') return text;
    
    let result = text;
    Object.entries(currentConfig.keywords).forEach(([keyword, config]) => {
      if (config.enabled) {
        const regex = new RegExp(`(${keyword})`, 'gi');
        result = result.replace(regex, `<span style="color: ${config.color}; font-weight: bold;">$1</span>`);
      }
    });
    return result;
  }

  function formatLogArgs(args) {
    return args.map(arg => {
      if (typeof arg === 'object' && arg !== null) {
        if (arg.type === 'error') {
          return `Error: ${arg.message}\n${arg.stack || ''}`;
        }
        if (arg.type === 'uncaught-error') {
          return `Uncaught Error: ${arg.message} at ${arg.filename}:${arg.lineno}:${arg.colno}`;
        }
        if (arg.type === 'unhandled-rejection') {
          return `Unhandled Promise Rejection: ${arg.reason}`;
        }
        return JSON.stringify(arg, null, 2);
      }
      return String(arg);
    }).join(' ');
  }

  // ===== UI BUILDING =====
  function buildDashboard() {
    const container = document.createElement('div');
    container.id = 'hg-dashboard';
    
    container.innerHTML = `
      <div class="dashboard-header">
        <div class="dashboard-title">🔍 HG Logger Dashboard</div>
        <div class="dashboard-stats">
          <div class="stat-item">
            <span class="stat-value" id="stat-sites">0</span>
            <span class="stat-label">Sites</span>
          </div>
          <div class="stat-item">
            <span class="stat-value" id="stat-logs">0</span>
            <span class="stat-label">Total Logs</span>
          </div>
          <div class="stat-item">
            <span class="stat-value" id="stat-filtered">0</span>
            <span class="stat-label">Displayed</span>
          </div>
        </div>
      </div>
      
      <div class="dashboard-controls">
        <div class="control-group">
          <label class="control-label">Site:</label>
          <select id="filter-host">
            <option value="all">All Sites</option>
          </select>
        </div>
        
        <div class="control-group">
          <label class="control-label">Method:</label>
          <select id="filter-method">
            <option value="all">All Methods</option>
            <option value="log">log</option>
            <option value="info">info</option>
            <option value="warn">warn</option>
            <option value="error">error</option>
            <option value="debug">debug</option>
          </select>
        </div>
        
        <div class="control-group">
          <label class="control-label">Search:</label>
          <input type="search" id="filter-search" placeholder="Search logs...">
        </div>
        
        <button class="btn btn-primary" id="btn-refresh">🔄 Refresh</button>
        <button class="btn btn-secondary" id="btn-config">⚙️ Settings</button>
        <button class="btn btn-success" id="btn-export">💾 Export</button>
        <button class="btn btn-danger" id="btn-clear">🗑️ Clear All</button>
      </div>
      
      <div class="logs-container" id="logs-container">
        <div class="no-logs">
          <div class="no-logs-icon">📋</div>
          <div>No logs captured yet. Visit websites with the HG Logger Collector active.</div>
        </div>
      </div>
    `;
    
    document.body.innerHTML = '';
    document.body.appendChild(container);
    
    // Auto-refresh indicator
    if (currentConfig.autoRefresh) {
      const indicator = document.createElement('div');
      indicator.className = 'refresh-indicator';
      indicator.innerHTML = '🔄 Auto-refresh active';
      document.body.appendChild(indicator);
    }
    
    attachEventListeners();
  }

  function attachEventListeners() {
    document.getElementById('filter-host').addEventListener('change', (e) => {
      currentFilter.host = e.target.value;
      renderLogs();
    });
    
    document.getElementById('filter-method').addEventListener('change', (e) => {
      currentFilter.method = e.target.value;
      renderLogs();
    });
    
    document.getElementById('filter-search').addEventListener('input', (e) => {
      currentFilter.search = e.target.value;
      renderLogs();
    });
    
    document.getElementById('btn-refresh').addEventListener('click', () => {
      loadLogs();
      renderLogs();
    });
    
    document.getElementById('btn-config').addEventListener('click', showConfigModal);
    document.getElementById('btn-export').addEventListener('click', exportLogs);
    document.getElementById('btn-clear').addEventListener('click', clearAllLogs);
  }

  function updateHostDropdown() {
    const select = document.getElementById('filter-host');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="all">All Sites</option>';
    
    const hosts = Object.keys(allLogs).sort();
    hosts.forEach(host => {
      const option = document.createElement('option');
      option.value = host;
      option.textContent = `${host} (${allLogs[host].length})`;
      select.appendChild(option);
    });
    
    // Restore selection if still valid
    if (hosts.includes(currentValue)) {
      select.value = currentValue;
    }
  }

  function getFilteredLogs() {
    let filtered = [];
    
    // Collect logs from selected host(s)
    if (currentFilter.host === 'all') {
      Object.values(allLogs).forEach(hostLogs => {
        filtered = filtered.concat(hostLogs);
      });
    } else if (allLogs[currentFilter.host]) {
      filtered = allLogs[currentFilter.host].slice();
    }
    
    // Filter by method
    if (currentFilter.method !== 'all') {
      filtered = filtered.filter(log => log.method === currentFilter.method);
    }
    
    // Filter by search term
    if (currentFilter.search) {
      const searchLower = currentFilter.search.toLowerCase();
      filtered = filtered.filter(log => {
        const content = formatLogArgs(log.args).toLowerCase();
        const url = log.href.toLowerCase();
        return content.includes(searchLower) || url.includes(searchLower);
      });
    }
    
    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Limit display
    if (filtered.length > currentConfig.maxLogsDisplay) {
      filtered = filtered.slice(0, currentConfig.maxLogsDisplay);
    }
    
    return filtered;
  }

  function renderLogs() {
    updateHostDropdown();
    
    const filtered = getFilteredLogs();
    const container = document.getElementById('logs-container');
    
    // Update stats
    document.getElementById('stat-sites').textContent = Object.keys(allLogs).length;
    const totalLogs = Object.values(allLogs).reduce((sum, logs) => sum + logs.length, 0);
    document.getElementById('stat-logs').textContent = totalLogs;
    document.getElementById('stat-filtered').textContent = filtered.length;
    
    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="no-logs">
          <div class="no-logs-icon">🔍</div>
          <div>No logs match your filters.</div>
        </div>
      `;
      return;
    }
    
    container.innerHTML = '';
    
    filtered.forEach(log => {
      const entry = document.createElement('div');
      entry.className = `log-entry log-${log.method}`;
      
      const content = formatLogArgs(log.args);
      const highlightedContent = highlightKeywords(content);
      
      entry.innerHTML = `
        <div class="log-header">
          <span class="log-method">${log.method.toUpperCase()}</span>
          <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
        </div>
        <div class="log-content">${highlightedContent}</div>
        <div class="log-url">🌐 ${log.host} - ${log.href}</div>
      `;
      
      container.appendChild(entry);
    });
  }

  function showConfigModal() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'config-modal';
    
    const timestampIsoChecked = currentConfig.timestampFormat === 'ISO' ? 'checked' : '';
    const timestampLocalChecked = currentConfig.timestampFormat === 'Local' ? 'checked' : '';
    const autoRefreshChecked = currentConfig.autoRefresh ? 'checked' : '';
    const colorCodingChecked = currentConfig.colorCoding ? 'checked' : '';
    
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-title">⚙️ Dashboard Settings</div>
        
        <div class="config-section">
          <div class="config-section-title">Display Options</div>
          
          <div class="config-option">
            <label>Auto-refresh</label>
            <input type="checkbox" id="cfg-auto-refresh" ${autoRefreshChecked}>
          </div>
          
          <div class="config-option">
            <label>Refresh interval (ms)</label>
            <input type="number" id="cfg-refresh-interval" value="${currentConfig.refreshInterval}" min="500" step="500">
          </div>
          
          <div class="config-option">
            <label>Max logs to display</label>
            <input type="number" id="cfg-max-logs" value="${currentConfig.maxLogsDisplay}" min="50" step="50">
          </div>
          
          <div class="config-option">
            <label>Color coding</label>
            <input type="checkbox" id="cfg-color-coding" ${colorCodingChecked}>
          </div>
        </div>
        
        <div class="config-section">
          <div class="config-section-title">Timestamp Format</div>
          
          <div class="config-option">
            <label>
              <input type="radio" name="timestamp" value="ISO" ${timestampIsoChecked}> ISO (2025-01-01T12:00:00.000Z)
            </label>
          </div>
          
          <div class="config-option">
            <label>
              <input type="radio" name="timestamp" value="Local" ${timestampLocalChecked}> Local (1/1/2025, 12:00:00 PM)
            </label>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" id="btn-cancel-config">Cancel</button>
          <button class="btn btn-primary" id="btn-save-config">Save Settings</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
    
    document.getElementById('btn-cancel-config').addEventListener('click', () => modal.remove());
    
    document.getElementById('btn-save-config').addEventListener('click', () => {
      currentConfig.autoRefresh = document.getElementById('cfg-auto-refresh').checked;
      currentConfig.refreshInterval = parseInt(document.getElementById('cfg-refresh-interval').value);
      currentConfig.maxLogsDisplay = parseInt(document.getElementById('cfg-max-logs').value);
      currentConfig.colorCoding = document.getElementById('cfg-color-coding').checked;
      
      const timestampRadios = document.getElementsByName('timestamp');
      timestampRadios.forEach(radio => {
        if (radio.checked) currentConfig.timestampFormat = radio.value;
      });
      
      saveConfig();
      modal.remove();
      
      // Restart auto-refresh if needed
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
      }
      
      if (currentConfig.autoRefresh) {
        startAutoRefresh();
      }
      
      // Remove old indicator
      const oldIndicator = document.querySelector('.refresh-indicator');
      if (oldIndicator) oldIndicator.remove();
      
      // Add new indicator if enabled
      if (currentConfig.autoRefresh) {
        const indicator = document.createElement('div');
        indicator.className = 'refresh-indicator';
        indicator.innerHTML = '🔄 Auto-refresh active';
        document.body.appendChild(indicator);
      }
      
      renderLogs();
      
      alert('Settings saved successfully!');
    });
  }

  function exportLogs() {
    const dataStr = JSON.stringify(allLogs, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `hg-logger-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert('Logs exported successfully!');
  }

  function clearAllLogs() {
    if (!confirm('Are you sure you want to clear ALL logs from ALL sites? This cannot be undone.')) {
      return;
    }
    
    storage.setItem(STORAGE_KEY, JSON.stringify({}));
    storage.setItem(STATS_KEY, JSON.stringify({ totalSites: 0, totalLogs: 0 }));
    
    allLogs = {};
    stats = {};
    renderLogs();
    
    alert('All logs cleared!');
  }

  function startAutoRefresh() {
    if (autoRefreshInterval) return;
    
    autoRefreshInterval = setInterval(() => {
      loadLogs();
      renderLogs();
    }, currentConfig.refreshInterval);
  }

  // ===== INITIALIZATION =====
  function init() {
    console.log('[HG DASHBOARD] Starting initialization...');
    console.log('[HG DASHBOARD] Document ready state:', document.readyState);
    
    // Wait for DOM
    if (document.readyState === 'loading') {
      console.log('[HG DASHBOARD] Waiting for DOM...');
      document.addEventListener('DOMContentLoaded', init);
      return;
    }
    
    console.log('[HG DASHBOARD] Injecting styles...');
    injectStyles();
    
    console.log('[HG DASHBOARD] Loading config...');
    loadConfig();
    
    console.log('[HG DASHBOARD] Loading logs from storage...');
    loadLogs();
    console.log('[HG DASHBOARD] Logs loaded:', Object.keys(allLogs).length, 'sites');
    console.log('[HG DASHBOARD] Storage keys:', Object.keys(localStorage));
    
    console.log('[HG DASHBOARD] Building dashboard...');
    buildDashboard();
    
    console.log('[HG DASHBOARD] Rendering logs...');
    renderLogs();
    
    if (currentConfig.autoRefresh) {
      console.log('[HG DASHBOARD] Starting auto-refresh...');
      startAutoRefresh();
    }
    
    console.log('[HG DASHBOARD] Initialization complete!');
    console.log('[HG DASHBOARD] Stats:', stats);
    console.log('[HG DASHBOARD] All logs:', allLogs);
  }

  // Start - run immediately and also wait for DOM as fallback
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM already loaded
    setTimeout(init, 0);
  }

})();
