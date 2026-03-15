// ==UserScript==
// @name HG Logger - Collector (Lightweight)
// @namespace otter.hg-logger-system
// @version 1.2
// @description Lightweight console logger that captures logs from all websites and stores them for the dashboard
// @author Otter Logic LLC
// @match *://*/*
// @grant GM_setValue
// @grant GM_getValue
// @grant unsafeWindow
// @run-at document-start
// ==/UserScript==

(function() {
  'use strict';

  // ===== CONFIGURATION =====
  const MAX_LOGS_PER_SITE = 1000;
  const STORAGE_KEY = 'hg_logger_all_logs';
  const STATS_KEY = 'hg_logger_stats';
  
  // Blacklist for sites to skip (ads, tracking, etc.)
  const BLACKLIST = [
    'amazon-adsystem.com',
    'googlesyndication.com', 
    'doubleclick.net',
    'googletagmanager.com',
    'googletagservices.com',
    'google-analytics.com',
    'facebook.net',
    'fbcdn.net'
  ];

  // ===== SAFE LOGGING =====
  const origLog = console.log.bind(console);
  function safeLog(...args) {
    origLog('[HG COLLECTOR]', ...args);
  }

  // Check if current site is blacklisted
  const isBlacklisted = BLACKLIST.some(domain => location.host.includes(domain));
  if (isBlacklisted) {
    safeLog('Skipped (blacklisted domain)');
    return;
  }

  safeLog('Initializing on', location.host);

  // ===== HELPER FUNCTIONS =====
  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  }

  function serializeArgs(args) {
    return args.map(arg => {
      try {
        if (arg instanceof Error) {
          return {
            type: 'error',
            name: arg.name,
            message: arg.message,
            stack: arg.stack
          };
        }
        if (typeof arg === 'string') return arg;
        if (typeof arg === 'number' || typeof arg === 'boolean') return arg;
        if (arg === null || arg === undefined) return String(arg);
        
        // Try to serialize objects
        return JSON.parse(JSON.stringify(arg, (k, v) => {
          if (typeof v === 'function') return '[Function]';
          if (v instanceof Error) return { error: v.message };
          return v;
        }));
      } catch (e) {
        return String(arg) || '[unserializable]';
      }
    });
  }

  function saveLogs(logs) {
    try {
      GM_setValue(STORAGE_KEY, JSON.stringify(logs));
    } catch (e) {
      safeLog('Failed to save logs:', e.message);
    }
  }

  function loadLogs() {
    try {
      const data = GM_getValue(STORAGE_KEY);
      return data ? JSON.parse(data) : {};
    } catch (e) {
      safeLog('Failed to load logs:', e.message);
      return {};
    }
  }

  function updateStats() {
    try {
      const allLogs = loadLogs();
      const stats = {
        totalSites: Object.keys(allLogs).length,
        totalLogs: Object.values(allLogs).flat().length,
        lastUpdate: new Date().toISOString(),
        siteBreakdown: {}
      };
      
      Object.keys(allLogs).forEach(host => {
        stats.siteBreakdown[host] = allLogs[host].length;
      });
      
      GM_setValue(STATS_KEY, JSON.stringify(stats));
    } catch (e) {
      safeLog('Failed to update stats:', e.message);
    }
  }

  // ===== INJECT INTO PAGE CONTEXT =====
  const injectedCode = function() {
    'use strict';

    // ===== SAFE LOGGING (in page context) =====
    const origLog = console.log.bind(console);
    function safeLog(...args) {
      origLog('[HG COLLECTOR]', ...args);
    }

    safeLog('Page context hooks initializing on', location.host);

    // ===== HELPER FUNCTIONS (duplicated in page context) =====
    function generateId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    function serializeArgs(args) {
      return args.map(arg => {
        try {
          if (arg instanceof Error) {
            return {
              type: 'error',
              name: arg.name,
              message: arg.message,
              stack: arg.stack
            };
          }
          if (typeof arg === 'string') return arg;
          if (typeof arg === 'number' || typeof arg === 'boolean') return arg;
          if (arg === null || arg === undefined) return String(arg);
          
          // Try to serialize objects
          return JSON.parse(JSON.stringify(arg, (k, v) => {
            if (typeof v === 'function') return '[Function]';
            if (v instanceof Error) return { error: v.message };
            return v;
          }));
        } catch (e) {
          return String(arg) || '[unserializable]';
        }
      });
    }

    // Communication with outer TamperMonkey context
    function notifyLogCaptured(logEntry) {
      // Send message to TamperMonkey script via window object
      if (window.HGCollectorBridge) {
        window.HGCollectorBridge.addLog(logEntry);
      } else {
        safeLog('ERROR: HGCollectorBridge not found! Cannot save log.');
      }
    }

    // ===== CONSOLE HOOKS =====
    const methods = ['log', 'info', 'warn', 'error', 'debug'];
    const originalMethods = {};

    // Save original methods BEFORE modification
    methods.forEach(method => {
      if (console[method]) {
        originalMethods[method] = console[method].bind(console);
      }
    });

    safeLog('Installing hooks for:', methods);

    // Create wrapper function for capturing logs
    function createLogCapture(method) {
      return function(...args) {
        // Skip HG Logger's own debug messages
        if (args.length > 0 && typeof args[0] === 'string' && args[0].includes('[HG COLLECTOR]')) {
          return originalMethods[method].apply(this, args);
        }

        // DEBUG: Log that capture was called
        origLog('[HG COLLECTOR] CAPTURED', method, 'with', args.length, 'args');

        // Capture the log
        try {
          const entry = {
            id: generateId(),
            method: method,
            args: serializeArgs(args),
            host: location.host,
            href: location.href,
            origin: location.origin,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent.substring(0, 100)
          };

          // Notify TamperMonkey context
          notifyLogCaptured(entry);
        } catch (e) {
          safeLog('Capture error:', e.message);
        }

        // Call original console method
        if (originalMethods[method]) {
          return originalMethods[method].apply(this, args);
        }
      };
    }

    // Install hooks by direct replacement
    methods.forEach(method => {
      try {
        console[method] = createLogCapture(method);
      } catch (e) {
        safeLog('Failed to hook', method, ':', e.message);
      }
    });

    // Hook console.clear
    const originalClear = console.clear ? console.clear.bind(console) : null;
    if (originalClear) {
      console.clear = function() {
        try {
          const entry = {
            id: generateId(),
            method: 'clear',
            args: ['[Console was cleared]'],
            host: location.host,
            href: location.href,
            origin: location.origin,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent.substring(0, 100)
          };
          notifyLogCaptured(entry);
        } catch (e) {
          safeLog('Clear capture error:', e.message);
        }

        return originalClear.apply(this, arguments);
      };
    }

    // Hook unhandled errors
    window.addEventListener('error', (event) => {
      try {
        const entry = {
          id: generateId(),
          method: 'error',
          args: [{
            type: 'uncaught-error',
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error ? {
              name: event.error.name,
              message: event.error.message,
              stack: event.error.stack
            } : null
          }],
          host: location.host,
          href: location.href,
          origin: location.origin,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent.substring(0, 100)
        };
        notifyLogCaptured(entry);
      } catch (e) {
        safeLog('Error event capture failed:', e.message);
      }
    });

    window.addEventListener('unhandledrejection', (event) => {
      try {
        const entry = {
          id: generateId(),
          method: 'error',
          args: [{
            type: 'unhandled-rejection',
            reason: event.reason ? String(event.reason) : 'Unknown reason'
          }],
          host: location.host,
          href: location.href,
          origin: location.origin,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent.substring(0, 100)
        };
        notifyLogCaptured(entry);
      } catch (e) {
        safeLog('Rejection event capture failed:', e.message);
      }
    });

    safeLog('Hooks installed successfully');
  };

  // ===== BRIDGE BETWEEN PAGE CONTEXT AND TAMPERMONKEY =====
  // CRITICAL: Expose bridge to page's window using unsafeWindow
  // This makes it accessible from the injected page context code
  unsafeWindow.HGCollectorBridge = {
    addLog: function(entry) {
      try {
        safeLog('Bridge received log from', entry.host, '- method:', entry.method);
        
        const allLogs = loadLogs();
        
        // Initialize array for this host if needed
        if (!allLogs[entry.host]) {
          allLogs[entry.host] = [];
        }

        // Add new entry
        allLogs[entry.host].push(entry);

        // Keep only last MAX_LOGS_PER_SITE entries per site
        if (allLogs[entry.host].length > MAX_LOGS_PER_SITE) {
          allLogs[entry.host] = allLogs[entry.host].slice(-MAX_LOGS_PER_SITE);
        }

        // Save back to TamperMonkey storage
        saveLogs(allLogs);
        origLog('[HG COLLECTOR] Saved', allLogs[entry.host].length, 'logs for', entry.host);

        // Update stats on every save
        updateStats();
      } catch (e) {
        safeLog('Bridge error:', e.message);
      }
    }
  };
  
  safeLog('Bridge exposed to page context');

  // Inject page context script using a safer method for CSP/Trusted Types
  try {
    const script = document.createElement('script');
    
    // Try modern Trusted Types-compatible approach first
    if (window.trustedTypes && window.trustedTypes.createPolicy) {
      try {
        const policy = window.trustedTypes.createPolicy('hg-collector-injection', {
          createScript: (code) => code
        });
        script.text = policy.createScript(`(${injectedCode})();`);
      } catch (e) {
        // Fallback: use .text instead of .textContent
        script.text = `(${injectedCode})();`;
      }
    } else {
      // Fallback for older browsers
      script.text = `(${injectedCode})();`;
    }
    
    (document.documentElement || document.head || document.body).appendChild(script);
    script.remove();
    safeLog('Collector initialized - page hooks injected');
  } catch (e) {
    safeLog('Failed to inject page hooks:', e.message);
  }

  // Update stats on load
  updateStats();

  // Expose debug interface
  window.HGCollectorDebug = {
    getStats: () => {
      try {
        return JSON.parse(GM_getValue(STATS_KEY) || '{}');
      } catch { return {}; }
    },
    getCurrentSiteLogs: () => {
      const allLogs = loadLogs();
      return allLogs[location.host] || [];
    },
    getAllLogs: () => loadLogs(),
    clearCurrentSite: () => {
      const allLogs = loadLogs();
      delete allLogs[location.host];
      saveLogs(allLogs);
      updateStats();
      safeLog('Cleared logs for', location.host);
    },
    clearAllLogs: () => {
      GM_setValue(STORAGE_KEY, '{}');
      GM_setValue(STATS_KEY, JSON.stringify({ totalSites: 0, totalLogs: 0 }));
      safeLog('Cleared all logs');
    }
  };

})();
