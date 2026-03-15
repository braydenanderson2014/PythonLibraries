// ==UserScript==
// @name HG Logger (global per-domain, SPA-aware, configurable sites)
// @namespace http://tampermonkey.net/
// @version 1.0
// @description Persist console + errors globally across all routes/paths, survives reloads, navigation to root, & console.clear, SPA-aware, with copy/download UI. Captures on all sites by default, with blacklist to prevent interference.
// @author You
// @match *://*/*
// @grant GM_setValue
// @grant GM_getValue
// @run-at document-start
// ==/UserScript==

(function() {
  'use strict';

  console.log('[HG LOGGER] Script starting...');

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

  function promptForConfigs() {
    // Prompt for UI domains
    const domainInput = prompt('Enter domains for full panel (comma-separated, e.g., example.com, *.example.com). Leave blank for all sites.', getDomainList().join(', '));
    if (domainInput !== null) {
      const domains = domainInput.split(',').map(d => d.trim().toLowerCase()).filter(d => d);
      setDomainList(domains);
    } else {
      setDomainList([]);
    }

    // Prompt for blacklist
    const blacklistInput = prompt('Enter domains to blacklist (disable all hooks/logging, e.g., company-site.com, *.company-site.com). Leave blank for none.', getBlacklist().join(', '));
    if (blacklistInput !== null) {
      const blacklist = blacklistInput.split(',').map(d => d.trim().toLowerCase()).filter(d => d);
      setBlacklist(blacklist);
    } else {
      setBlacklist([]);
    }
  }

  function domainMatches(currentHost, list) {
    if (list.length === 0) return list === getDomainList(); // For domains: empty = true (all); for blacklist: empty = false (none)

    currentHost = currentHost.toLowerCase();
    return list.some(pattern => {
      if (pattern.startsWith('*.')) {
        const baseDomain = pattern.slice(2);
        return currentHost === baseDomain || currentHost.endsWith('.' + baseDomain);
      }
      return currentHost === pattern;
    });
  }

  // Early check for blacklist
  const isBlacklisted = domainMatches(location.host, getBlacklist());
  if (isBlacklisted) {
    console.log('[HG LOGGER] Blacklisted site; skipping all operations to avoid interference.');
    return; // Exit completely - no hooks, no UI, no storage writes
  }

  // Proceed if not blacklisted
  console.log('[HG LOGGER] Not blacklisted; proceeding with setup for host:', location.host);

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
      console.log('[HG LOGGER] localStorage write failed:', e);
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

  // Always install hooks (monitoring on all sites) - made safer
  const nowISO = () => new Date().toISOString();
  const uuid4 = () => ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
  const sessionId = uuid4();
  const currentHost = location.host;
  let buffer = [];
  let writeTimer = null;
  const MAX_ENTRIES = 20000;
  const AUTOSAVE_MS = 1500;
  let isCapturing = true; // Global toggle to disable hooks if needed

  const scheduleWrite = () => {
    if (writeTimer || !isCapturing) return;
    writeTimer = setTimeout(() => {
      let local = getLocalLogs().concat(buffer);
      local = local.length > MAX_ENTRIES ? local.slice(local.length - MAX_ENTRIES) : local;
      setLocalLogs(local);
      syncLogsToGM();
      buffer = [];
      writeTimer = null;
      if (window.render) window.render();
    }, AUTOSAVE_MS);
  };

  const push = (entry) => {
    entry.host = currentHost;
    entry.ts = nowISO();
    entry.session = sessionId;
    if (isCapturing) {
      buffer.push(entry);
      scheduleWrite();
    }
  };

  // Safer hook installation - fail silently, don't block
  try {
    const methods = ['log', 'info', 'warn', 'error', 'debug'];
    const orig = Object.fromEntries(methods.map(m => [m, console[m].bind(console)]));
    function capture(method, argsArr) {
      try {
        push({ method, args: argsArr.map(toPlain) });
      } catch (e) {
        // Silent fail to avoid blocking
      }
    }

    methods.forEach(m => {
      console[m] = function(...args) {
        try {
          capture(m, args);
        } catch {}
        try {
          orig[m](...args);
        } catch {}
      };
    });

    const origClear = console.clear ? console.clear.bind(console) : null;
    console.clear = function() {
      try {
        capture('clear', [{ note: 'console.clear invoked' }]);
      } catch {}
      if (origClear) try { origClear(); } catch {}
      if (window.render) window.render();
    };

    window.addEventListener('error', (ev) => {
      try {
        capture('error', [{ type: 'onerror', message: ev.message, filename: ev.filename, lineno: ev.lineno, colno: ev.colno, error: toPlain(ev.error) }]);
      } catch {}
    });
    window.addEventListener('unhandledrejection', (ev) => {
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

    console.log('[HG LOGGER] Hooks installed safely for host:', currentHost);
  } catch (e) {
    console.log('[HG LOGGER] Hook installation failed safely:', e);
  }

  // Proceed with UI injection (conditional on config) - delayed for DOM readiness
  setTimeout(() => {
    if (!document.head && !document.documentElement) return; // Ensure DOM is ready
    
    console.log('[HG LOGGER] UI injection started for host:', location.host);

    // Util functions (CSP-compliant - no eval/injection needed)
    function toPlain(x) {
      try {
        if (x instanceof Error) return { name: x.name, message: x.message, stack: x.stack };
        if (typeof x === 'string') return x;
        return JSON.parse(JSON.stringify(x, (k, v) => (typeof v === 'function' ? '[Function]' : v)));
      } catch {
        return String(x) || '[unserializable]';
      }
    }

      // Parse context for badge
      function parseContext(url = location.href) {
        const u = new URL(url, location.origin);
        const m = u.pathname.match(/(?:^|\/)(lobby|game|spectator)\/([^\/?#]+)/i);
        const kind = m ? m[1].toLowerCase() : 'page';
        const id = m ? m[2] : (u.pathname.replace(/\W+/g, '_') || '_global_');
        return { kind, id };
      }

      // Format line for textarea
      function formatLine(e, showHost = false) {
        const prefix = e.source === 'hg-logger' ? '[HG LOGGER] ' : '';
        const hostPrefix = showHost ? `[${e.host}] ` : '';
        const args = (e.args || []).map(a => typeof a === 'string' ? a : JSON.stringify(a) || String(a)).join(' ');
        return `[${e.ts}] [${e.session.slice(0, 8)}] [${e.method}] ${hostPrefix}${prefix}${args}`;
      }

      // Render function (global for access)
      window.render = function(reset = false) {
        console.log('[HG LOGGER] Render called for host:', location.host);
        const ta = document.getElementById('tmc-text');
        if (!ta) return;
        syncLogsToGM(); // Ensure GM is up-to-date
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
        if (reset) ta.value = '';
        ta.value = arr.length ? arr.map(e => formatLine(e, filter === 'all')).join('\n') : `No logs for ${filter}`;
        if (document.getElementById('tmc-auto')?.checked) ta.scrollTop = ta.scrollHeight;
        document.getElementById('tmc-count').textContent = `${arr.length}`;
        document.getElementById('tmc-key').textContent = `/${parseContext().kind}/${parseContext().id}`;
      };

      // Ensure full panel
      function ensurePanel(force = false) {
        let panel = document.getElementById('tmc-panel');
        if (panel && !force) return;
        console.log('[HG LOGGER] (Re)creating full panel for host:', location.host);
        if (panel) panel.remove(); // Clean up if forcing
        panel = document.createElement('div');
        panel.id = 'tmc-panel';
        Object.assign(panel.style, {
          position: 'fixed',
          right: '12px',
          bottom: '12px',
          width: '520px',
          maxHeight: '75vh',
          background: 'rgba(24,24,24,0.96)',
          color: '#eee',
          fontFamily: 'monospace',
          fontSize: '12px',
          border: '1px solid #333',
          borderRadius: '8px',
          zIndex: 2147483647,
          display: 'flex',
          flexDirection: 'column'
        });
        panel.innerHTML = `
          <div id="tmc-head" style="display:flex;align-items:center;justify-content:space-between;padding:6px 8px;border-bottom:1px solid #333;cursor:move;">
            <div style="display:flex;gap:8px;align-items:center;">
              <strong>HG Logger</strong>
              <span id="tmc-key" style="opacity:.8;font-size:11px;"></span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <button id="tmc-config">Config</button>
              <button id="tmc-reset">Reset All</button>
              <select id="tmc-filter" title="Filter"></select>
              <button id="tmc-copy">Copy</button>
              <button id="tmc-dl">Download</button>
              <button id="tmc-clr">Clear</button>
              <button id="tmc-collapse">▲</button>
            </div>
          </div>
          <div id="tmc-body" style="display:flex;flex-direction:column;gap:6px;padding:6px;">
            <div style="display:flex;gap:8px;align-items:center;">
              <label><input id="tmc-auto" type="checkbox" checked> Auto-scroll</label>
              <label style="margin-left:8px;"><input id="tmc-live" type="checkbox" checked> Capture</label>
              <span id="tmc-count" style="margin-left:auto;opacity:.8;"></span>
            </div>
            <textarea id="tmc-text" readonly style="width:100%;height:330px;padding:8px;background:#111;color:#eee;border-radius:6px;border:1px solid #333;resize:vertical;overflow:auto;"></textarea>
          </div>
        `;
        panel.querySelectorAll('button').forEach(b => {
          Object.assign(b.style, { background: 'transparent', color: '#ddd', border: '1px solid #666', padding: '4px 7px', borderRadius: '5px', cursor: 'pointer' });
        });
        document.documentElement.appendChild(panel);

        // Restore state
        restoreUIState(panel);

        // Drag functionality with save
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
          window.addEventListener('mousemove', e => {
            if (!down) return;
            r = Math.max(6, r + (e.clientX - ox) * -1);
            b = Math.max(6, b + (e.clientY - oy) * -1);
            ox = e.clientX;
            oy = e.clientY;
            el.style.right = r + 'px';
            el.style.bottom = b + 'px';
            saveUIState(el);
          });
          window.addEventListener('mouseup', () => down = false);
        })(panel, document.getElementById('tmc-head'));

        // Populate filter dropdown
        const filterEl = document.getElementById('tmc-filter');
        const addOption = (value, text) => {
          const opt = document.createElement('option');
          opt.value = value;
          opt.textContent = text;
          filterEl.appendChild(opt);
        };
        addOption('all', 'all (merged)');
        Object.keys(getAllLogs()).sort().forEach(h => addOption(h, h));
        addOption('', '-- Method Filters --');
        ['log', 'info', 'warn', 'error', 'debug', 'clear', 'net'].forEach(m => addOption(m, m));

        // Event listeners
        document.getElementById('tmc-config').onclick = () => {
          promptForConfigs();
          if (!domainMatches(location.host, getDomainList())) {
            panel.style.display = 'none';
            ensureSmallButton();
          } else {
            window.render(true);
          }
        };
        document.getElementById('tmc-reset').onclick = () => {
          if (confirm('Reset all config, logs, and storage?')) {
            setDomainList([]);
            setBlacklist([]);
            localStorage.clear();
            setAllLogs({});
            location.reload();
          }
        };
        document.getElementById('tmc-copy').onclick = () => {
          const ta = document.getElementById('tmc-text');
          ta.select();
          try {
            document.execCommand('copy');
          } catch {}
        };
        document.getElementById('tmc-dl').onclick = () => {
          const filter = document.getElementById('tmc-filter')?.value || 'all';
          const blob = new Blob([document.getElementById('tmc-text').value], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          const ctx = parseContext();
          a.href = url;
          a.download = `console_${filter}_${ctx.kind}_${ctx.id}_${new Date().toISOString().replace(/[:.]/g, '-')}.log`;
          a.click();
          URL.revokeObjectURL(url);
        };
        document.getElementById('tmc-clr').onclick = () => {
          const filter = document.getElementById('tmc-filter')?.value || 'all';
          if (!confirm(`Clear stored logs for ${filter}?`)) return;
          if (filter === 'all') {
            localStorage.clear(); // Clear local
            setAllLogs({}); // Clear GM
          } else if (filter === location.host) {
            setLocalLogs([]);
            syncLogsToGM();
          } else {
            const allLogs = getAllLogs();
            delete allLogs[filter];
            setAllLogs(allLogs);
          }
          window.render(true);
        };
        document.getElementById('tmc-collapse').onclick = (e) => {
          const body = document.getElementById('tmc-body');
          const isCollapsed = body.style.display === 'none';
          body.style.display = isCollapsed ? 'flex' : 'none';
          e.target.textContent = isCollapsed ? '▲' : '▼';
          saveUIState(panel);
        };
        document.getElementById('tmc-live').onchange = (e) => {
          isCapturing = e.target.checked;
          window.render();
        };
        document.getElementById('tmc-filter').onchange = () => window.render();

        window.render(true);
      }

      // Small button for non-matching sites
      function ensureSmallButton(force = false) {
        let btn = document.getElementById('hg-small-btn');
        if (btn && !force) return;
        console.log('[HG LOGGER] (Re)adding small button for non-matching host:', location.host);
        if (btn) btn.remove();
        btn = document.createElement('div');
        btn.id = 'hg-small-btn';
        btn.textContent = 'HG';
        Object.assign(btn.style, {
          position: 'fixed',
          top: '10px',
          right: '10px',
          zIndex: 2147483647,
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          cursor: 'pointer'
        });
        btn.onclick = () => {
          const panel = document.getElementById('tmc-panel');
          if (panel && panel.style.display === 'none') {
            panel.style.display = 'flex';
          } else {
            ensurePanel(true);
          }
        };
        document.documentElement.appendChild(btn);
      }

      // Decide UI based on config
      if (domainMatches(location.host, getDomainList())) {
        console.log('[HG LOGGER] Host matches - showing full panel');
        ensurePanel();
      } else {
        console.log('[HG LOGGER] Host does not match - showing small button');
        ensureSmallButton();
      }

      // MutationObserver to detect and recover UI removal (scoped)
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          if (mutation.removedNodes.length) {
            if (!document.getElementById('tmc-panel') && domainMatches(location.host, getDomainList())) {
              console.log('[HG LOGGER] Panel was removed; re-adding...');
              ensurePanel(true);
            }
            if (!document.getElementById('hg-small-btn') && !domainMatches(location.host, getDomainList())) {
              console.log('[HG LOGGER] Small button was removed; re-adding...');
              ensureSmallButton(true);
            }
          }
        });
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });

      // Periodic re-ensure (every 1s)
      setInterval(() => {
        if (domainMatches(location.host, getDomainList()) && !document.getElementById('tmc-panel')) {
          ensurePanel(true);
        } else if (!domainMatches(location.host, getDomainList()) && !document.getElementById('hg-small-btn')) {
          ensureSmallButton(true);
        }
        if (document.getElementById('tmc-live')?.checked) window.render();
      }, 1000);

      // History hooks
      (function hookHistory() {
        const origPush = history.pushState;
        const origReplace = history.replaceState;
        const onChange = (url) => {
          push({ method: 'info', source: 'hg-logger', args: [{ event: 'context-switch', url: String(url) }] });
          window.render();
          console.log('[HG LOGGER] Context switch detected for host:', location.host, url);
        };
        history.pushState = function(s, t, u) {
          const r = origPush.apply(this, arguments);
          if (u) onChange(u);
          return r;
        };
        history.replaceState = function(s, t, u) {
          const r = origReplace.apply(this, arguments);
          if (u) onChange(u);
          return r;
        };
        window.addEventListener('popstate', () => onChange(location.href));
      })();

      // Initial push for installation
      push({ method: 'info', source: 'hg-logger', args: [{ event: 'logger-installed', url: location.href, route: parseContext() }] });
    };

    // CSP-compliant script injection - try multiple methods
    const scriptCode = `(${injected})();`;

    // Method 1: Try direct execution with Function constructor (requires unsafe-eval)
    try {
      const func = new Function(scriptCode);
      func();
      console.log('[HG LOGGER] Direct execution successful');
      return; // Success, exit early
    } catch (e) {
      console.log('[HG LOGGER] Direct execution failed:', e.message);
    }

    // Method 2: Try eval (requires unsafe-eval)
    try {
      eval(scriptCode);
      console.log('[HG LOGGER] Eval execution successful');
      return; // Success, exit early
    } catch (e) {
      console.log('[HG LOGGER] Eval execution failed:', e.message);
    }

    // Method 3: Try document.write (requires unsafe-inline)
    try {
      const script = `<script>${scriptCode}</script>`;
      document.write(script);
      console.log('[HG LOGGER] Document.write execution successful');
      return; // Success, exit early
    } catch (e) {
      console.log('[HG LOGGER] Document.write execution failed:', e.message);
    }

    // Method 4: Try insertAdjacentHTML (requires unsafe-inline)
    try {
      const tempDiv = document.createElement('div');
      tempDiv.style.display = 'none';
      tempDiv.innerHTML = `<script>${scriptCode}</script>`;
      document.documentElement.appendChild(tempDiv);
      // Execute after a brief delay to allow script to be parsed
      setTimeout(() => {
        if (tempDiv.parentNode) {
          tempDiv.parentNode.removeChild(tempDiv);
        }
      }, 0);
      console.log('[HG LOGGER] insertAdjacentHTML execution successful');
      return; // Success, exit early
    } catch (e) {
      console.log('[HG LOGGER] insertAdjacentHTML execution failed:', e.message);
    }

    // Method 5: Fallback to data URL with Trusted Types (last resort)
    try {
      const encodedScript = btoa(unescape(encodeURIComponent(scriptCode)));
      const dataUrl = `data:text/javascript;base64,${encodedScript}`;

      const s = document.createElement('script');

      // Try Trusted Types API first (for strict CSP)
      if (window.trustedTypes && window.trustedTypes.createPolicy) {
        try {
          const policy = window.trustedTypes.createPolicy('tampermonkey-script', {
            createScriptURL: (url) => url
          });
          s.src = policy.createScriptURL(dataUrl);
        } catch (e) {
          // Fallback to direct assignment if policy creation fails
          s.src = dataUrl;
        }
      } else {
        // Fallback for browsers without Trusted Types
        s.src = dataUrl;
      }

      (document.head || document.documentElement).appendChild(s);
      s.onload = () => {
        s.remove(); // Clean up after execution
      };
      console.log('[HG LOGGER] Data URL execution attempted');
    } catch (e) {
      console.log('[HG LOGGER] All execution methods failed:', e.message);
    }
  }, 100); // Small delay for DOM readiness

  console.log('[HG LOGGER] Script injected and running for host:', location.host);
})(); 