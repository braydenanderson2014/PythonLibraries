// ==UserScript==
// @name HG Logger (global per-domain, SPA-aware)
// @namespace http://tampermonkey.net/
// @version 2.1
// @description Persist console + errors globally across all routes/paths under the domain, survives reloads, navigation to root, & console.clear, SPA-aware, with copy/download UI.
// @author You
// @match https://hungergames.monkeybusinesspreschool-ut.com/*
// @match https://*.hungergames.monkeybusinesspreschool-ut.com/*
// @grant none
// @run-at document-start
// ==/UserScript==

(function() {
'use strict';

const injected = function() {
// ===== CONFIG =====
const MAX_ENTRIES = 10000;
const STORAGE_PREFIX = 'tm_console_';
const AUTOSAVE_MS = 1500;
const ROUTE_RE = /(?:^|\/)(lobby|game|spectator)\/([^\/?#]+)/i; // captures kind + id; ignores trailing segments like /wait
const GLOBAL_KEY = `${STORAGE_PREFIX}${location.host}_global`; // Single global key for all paths

// ===== UTIL =====
const nowISO = () => new Date().toISOString();
const uuid4 = () => ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g,c=>(c^crypto.getRandomValues(new Uint8Array(1))[0]&15>>c/4).toString(16));

function parseContext(url = location.href) {
const u = new URL(url, location.origin);
const m = u.pathname.match(ROUTE_RE);
const kind = m ? m[1].toLowerCase() : 'page';
const id = m ? m[2] : (u.pathname.replace(/\W+/g,'_') || '_global_');
return { kind, id, path: u.pathname };
}

function circularReplacer() {
const seen = new WeakSet();
return (k,v) => {
if (typeof v === 'object' && v !== null) {
if (seen.has(v)) return '[Circular]';
seen.add(v);
}
if (typeof v === 'function') return `[Function: ${v.name || 'anonymous'}]`;
return v;
};
}

const toPlain = (x) => {
try {
if (x instanceof Error) return { name: x.name, message: x.message, stack: x.stack };
if (typeof x === 'string') return x;
return JSON.parse(JSON.stringify(x, circularReplacer()));
} catch {
try { return String(x); } catch { return '[unserializable]'; }
}
};

// ===== STATE =====
let currentKey = GLOBAL_KEY; // Always global
let buffer = [];
let writeTimer = null;
let isCapturing = true; // Global flag for capturing (toggled by UI)
const sessionId = uuid4();

const readAll = (k = currentKey) => { try { return JSON.parse(localStorage.getItem(k) || '[]'); } catch { return []; } };
const scheduleWrite = () => {
if (writeTimer) return;
writeTimer = setTimeout(() => {
try {
const existing = readAll();
const merged = existing.concat(buffer);
const cut = merged.length > MAX_ENTRIES ? merged.slice(merged.length - MAX_ENTRIES) : merged;
localStorage.setItem(currentKey, JSON.stringify(cut));
} catch (e) { console.error('[HG LOGGER] Failed to save logs', e); }
buffer = [];
writeTimer = null;
render();
}, AUTOSAVE_MS);
};
const push = (entry) => { if (isCapturing) { buffer.push(entry); scheduleWrite(); } };
const flush = () => {
if (!buffer.length) return;
try {
const existing = readAll();
const merged = existing.concat(buffer);
const cut = merged.length > MAX_ENTRIES ? merged.slice(merged.length - MAX_ENTRIES) : merged;
localStorage.setItem(currentKey, JSON.stringify(cut));
} catch {}
buffer = [];
render();
};

// ===== UI =====
function ensurePanel() {
if (document.getElementById('tmc-panel')) return;
console.log('[HG LOGGER] Ensuring panel'); // Debug log
const panel = document.createElement('div');
panel.id = 'tmc-panel';
Object.assign(panel.style, {
position: 'fixed', right: '12px', bottom: '12px',
width: '520px', maxHeight: '75vh',
background: 'rgba(24,24,24,0.96)', color: '#eee',
fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
fontSize: '12px', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px',
zIndex: 2147483647, display: 'flex', flexDirection: 'column', boxShadow: '0 6px 22px rgba(0,0,0,0.55)'
});
panel.innerHTML = `
<div id="tmc-head" style="display:flex;align-items:center;justify-content:space-between;padding:6px 8px;border-bottom:1px solid rgba(255,255,255,0.06);cursor:move;">
<div style="display:flex;gap:8px;align-items:center;">
<strong>HG Logger</strong>
<span id="tmc-key" style="opacity:.8;font-size:11px;"></span>
</div>
<div style="display:flex;gap:6px;align-items:center;">
<select id="tmc-filter" title="Filter">
<option value="">all</option>
<option>log</option><option>info</option><option>warn</option><option>error</option><option>debug</option>
<option value="clear">clear</option><option value="net">net</option>
</select>
<button id="tmc-copy">Copy</button>
<button id="tmc-dl">Download</button>
<button id="tmc-clr">Clear</button>
<button id="tmc-collapse">▲</button>
</div>
</div>
<div id="tmc-body" style="display:flex;flex-direction:column;gap:6px;padding:6px;">
<div style="display:flex;gap:8px;align-items:center;">
<label><input id="tmc-auto" type="checkbox" checked> Auto-scroll</label>
<label style="margin-left:8px;"><input id="tmc-live" type="checkbox" checked> Capture</label> <!-- Renamed to Capture -->
<span id="tmc-count" style="margin-left:auto;opacity:.8;"></span>
</div>
<textarea id="tmc-text" readonly
style="width:100%;height:330px;padding:8px;background:#0b0b0b;color:#e6e6e6;border-radius:6px;border:1px solid rgba(255,255,255,0.07);resize:vertical;overflow:auto;"></textarea>
</div>
`;
panel.querySelectorAll('button').forEach(b => {
Object.assign(b.style, { background:'transparent', color:'#ddd', border:'1px solid rgba(255,255,255,0.14)', padding:'4px 7px', borderRadius:'5px', cursor:'pointer' });
});
document.documentElement.appendChild(panel);

// drag
(function drag(el, handle){
let down=false, ox=0, oy=0, r=12, b=12;
handle.addEventListener('mousedown', e => { down=true; ox=e.clientX; oy=e.clientY; e.preventDefault(); });
window.addEventListener('mousemove', e => {
if (!down) return;
r = Math.max(6, r + (e.clientX - ox) * -1);
b = Math.max(6, b + (e.clientY - oy) * -1);
ox=e.clientX; oy=e.clientY;
el.style.right = r + 'px'; el.style.bottom = b + 'px';
});
window.addEventListener('mouseup', ()=> down=false);
})(panel, document.getElementById('tmc-head'));

// actions
document.getElementById('tmc-copy').onclick = () => { const ta = document.getElementById('tmc-text'); ta.select(); try { document.execCommand('copy'); } catch {} };
document.getElementById('tmc-dl').onclick = () => {
const blob = new Blob([document.getElementById('tmc-text').value], {type:'text/plain'});
const url = URL.createObjectURL(blob); const a = document.createElement('a');
const ctx = parseContext();
a.href = url; a.download = `console_${location.host}_${ctx.kind}_${ctx.id}_${new Date().toISOString().replace(/[:.]/g,'-')}.log`; a.click();
URL.revokeObjectURL(url);
};
document.getElementById('tmc-clr').onclick = () => { if (!confirm('Clear stored log for this key?')) return; try { localStorage.removeItem(currentKey); } catch {}; render(true); };
document.getElementById('tmc-collapse').onclick = (e) => { const body = document.getElementById('tmc-body'); const c = body.style.display === 'none'; body.style.display = c ? 'flex' : 'none'; e.target.textContent = c ? '▲' : '▼'; };
document.getElementById('tmc-filter').onchange = () => render();

// Toggle capturing
document.getElementById('tmc-live').onchange = (e) => {
  isCapturing = e.target.checked;
  flush(); // Flush any buffer before pausing
  render();
};
}

function keyBadgeText() {
const ctx = parseContext();
return `/${ctx.kind}/${ctx.id}`;
}

function formatLine(e) {
const prefix = e.source === 'hg-logger' ? '[HG LOGGER] ' : '';
const args = (e.args || []).map(a => {
if (typeof a === 'string') return a;
try { return JSON.stringify(a); } catch { return String(a); }
}).join(' ');
return `[${e.ts}] [${(e.session||'').slice(0,8)}] [${e.method}] ${prefix}${args}`;
}

function render(reset=false) {
const ta = document.getElementById('tmc-text');
const countEl = document.getElementById('tmc-count');
const filter = document.getElementById('tmc-filter')?.value || '';
const keyEl = document.getElementById('tmc-key');
if (keyEl) keyEl.textContent = keyBadgeText();
if (!ta) return;
const arr = readAll(currentKey);
if (reset) ta.value = '';
const filtered = filter ? arr.filter(e => e.method === filter) : arr;
ta.value = filtered.map(formatLine).join('\n');
if (document.getElementById('tmc-auto')?.checked) ta.scrollTop = ta.scrollHeight;
if (countEl) countEl.textContent = `${filtered.length}/${arr.length}`;
}

// Log context changes (but don't switch keys)
(function hookHistory(){
const origPush = history.pushState;
const origReplace = history.replaceState;
const onChange = (url) => {
push({ ts: nowISO(), method: 'info', session: sessionId, source: 'hg-logger', args: [{event:'context-switch', url: String(url)}] });
render(); // Refresh without reset
console.log('[HG LOGGER] Context switch detected (logs persist globally)', url); // Debug log
};
history.pushState = function(s,t,u){ const r = origPush.apply(this, arguments); if (u) onChange(u); return r; };
history.replaceState = function(s,t,u){ const r = origReplace.apply(this, arguments); if (u) onChange(u); return r; };
window.addEventListener('popstate', () => onChange(location.href));
})();

// ===== LOG/ERROR/NET HOOKS =====
(function installHooks(){
if (window.__hglog_installed__) return; window.__hglog_installed__ = true;

console.log('[HG LOGGER] Installing hooks'); // Debug log

setTimeout(() => { // Slight delay for DOM readiness
  ensurePanel();
  render(true); // Force initial render
}, 100);

// Periodic check to re-ensure panel if removed by site DOM changes
setInterval(() => {
  if (!document.getElementById('tmc-panel')) {
    console.log('[HG LOGGER] Re-ensuring panel (was missing)'); // Debug log
    ensurePanel();
    render(true);
  }
}, 5000);

const methods = ['log','info','warn','error','debug'];
const orig = Object.fromEntries(methods.map(m => [m, console[m].bind(console)]));
function capture(method, argsArr) { push({ ts: nowISO(), method, session: sessionId, args: argsArr.map(toPlain) }); }

methods.forEach(m => {
console[m] = function(...args) {
if (isCapturing) try { capture(m, args); } catch {}
try { orig[m](...args); } catch {}
};
});

const origClear = console.clear ? console.clear.bind(console) : null;
console.clear = function() {
if (isCapturing) capture('clear', [{note:'console.clear invoked'}]);
if (origClear) try { origClear(); } catch {}
render();
};

window.addEventListener('error', (ev) => {
if (isCapturing) capture('error', [{ type:'onerror', message: ev.message, filename: ev.filename, lineno: ev.lineno, colno: ev.colno, error: ev.error ? toPlain(ev.error) : undefined }]);
});
window.addEventListener('unhandledrejection', (ev) => {
if (isCapturing) capture('error', [{ type:'unhandledrejection', reason: toPlain(ev.reason ?? '(no reason)') }]);
});

// fetch
if (!window.__hglog_fetch__) {
window.__hglog_fetch__ = true;
const of = window.fetch.bind(window);
window.fetch = async function(input, init) {
const t0 = performance.now();
try {
const res = await of(input, init);
if (isCapturing && !res.ok) capture('net', [{ type:'fetch', status: res.status, url: res.url || String(input), method: (init && init.method) || 'GET', ms:+(performance.now()-t0).toFixed(1)}]);
return res;
} catch (e) {
if (isCapturing) capture('net', [{ type:'fetch-error', url: input && input.url ? input.url : String(input), error: toPlain(e), ms:+(performance.now()-t0).toFixed(1)}]);
throw e;
}
};
}
// XHR
(function wrapXHR(){
const X = window.XMLHttpRequest;
if (!X || X.__hglog_wrapped__) return;
X.__hglog_wrapped__ = true;
const open = X.prototype.open, send = X.prototype.send;
X.prototype.open = function(method, url){ this.__hglog = {method, url}; return open.apply(this, arguments); };
X.prototype.send = function() {
const t0 = performance.now();
this.addEventListener('load', () => { if (isCapturing && this.status >= 400) capture('net', [{type:'xhr', status:this.status, method:this.__hglog?.method, url:this.__hglog?.url, ms:+(performance.now()-t0).toFixed(1)}]); });
this.addEventListener('error', () => { if (isCapturing) capture('net', [{type:'xhr-error', method:this.__hglog?.method, url:this.__hglog?.url, ms:+(performance.now()-t0).toFixed(1)}]); });
return send.apply(this, arguments);
};
})();

push({ ts: nowISO(), method: 'info', session: sessionId, source: 'hg-logger', args: [{event:'logger-installed', url: location.href, route: parseContext()}] });
document.addEventListener('DOMContentLoaded', () => { render(true); }); // Fallback render
setInterval(() => { if (document.getElementById('tmc-live')?.checked) render(); }, 2000); // Only render live if capturing
window.addEventListener('beforeunload', flush);
window.addEventListener('pagehide', flush);
})();

// quick toggle
window.addEventListener('keydown', (e) => {
if (e.ctrlKey && e.shiftKey && e.code === 'KeyL') {
const body = document.getElementById('tmc-body'); const btn = document.getElementById('tmc-collapse');
if (body && btn) { btn.click(); e.preventDefault(); }
}
});
};

console.log('[HG LOGGER] Script injected'); // Initial debug log (outside page context)

// inject into page context
const s = document.createElement('script');
s.textContent = `(${injected})();`;
(document.documentElement || document.head || document.body).appendChild(s);
s.remove();
})();