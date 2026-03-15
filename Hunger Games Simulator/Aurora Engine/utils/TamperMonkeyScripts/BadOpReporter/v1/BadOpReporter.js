// ==UserScript==
// @name         What a Terrible Op, URL Reporter (global, daily reset)
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Save current URL into daily lists (Bad Operators, Other Issues, etc.), shared across sites & tabs, resets each day.
// @author       OtterLogic LLC
// @match        https://*/*
// @run-at       document-end
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_addValueChangeListener
// ==/UserScript==

(async function () {
    'use strict';

    // Global flag to prevent multiple versions from running simultaneously
    if (window.__OL_URL_REPORTER_ACTIVE__) {
        console.warn('[URL Reporter] Another instance is already running, exiting');
        return;
    }
    window.__OL_URL_REPORTER_ACTIVE__ = true;

    // If you want it only on a specific app, uncomment and tweak:
    if (!location.href.startsWith('https://flide.ap.tesla.services/3d/')) return;

    /** ---------- CONFIG ---------- **/

    const CATEGORIES = [
        { key: 'badFSWOps', label: 'Bad FSW Operators' },
        { key: 'badAudioOps', label: 'Bad Audio Prompt Ops' },
        { key: 'badAudioEval', label: 'Bad Audio Eval Ops' },
        // Add more here:
        // { key: 'weirdBugs',   label: 'Weird Bugs' },
    ];

    const STORAGE_KEY = 'ol_dailyUrlReporter_v2';
    const TIMEZONE = 'America/Denver';

    /** ---------- DATE & STORAGE HELPERS ---------- **/

    function todayString() {
        // YYYY-MM-DD in your timezone
        return new Date().toLocaleDateString('en-CA', { timeZone: TIMEZONE });
    }

    function makeEmptyLists() {
        const lists = {};
        for (const cat of CATEGORIES) {
            lists[cat.key] = [];
        }
        return lists;
    }

    async function loadDataFromGM() {
        const today = todayString();
        const raw = await GM_getValue(STORAGE_KEY, null);

        if (!raw) {
            return { date: today, lists: makeEmptyLists() };
        }

        let parsed;
        try {
            parsed = JSON.parse(raw);
        } catch {
            return { date: today, lists: makeEmptyLists() };
        }

        // Daily reset
        if (!parsed || parsed.date !== today) {
            return { date: today, lists: makeEmptyLists() };
        }

        if (!parsed.lists) parsed.lists = {};
        // Make sure all categories exist even if you add new ones
        for (const cat of CATEGORIES) {
            if (!Array.isArray(parsed.lists[cat.key])) {
                parsed.lists[cat.key] = [];
            }
        }

        return parsed;
    }

    async function saveDataToGM(d) {
        try {
            await GM_setValue(STORAGE_KEY, JSON.stringify(d));
        } catch (e) {
            console.warn('[OL Daily URL Reporter] Failed to save data', e);
        }
    }

    // Shared state for this tab
    let data = await loadDataFromGM();

    /** ---------- DATA ACTIONS ---------- **/

    async function addCurrentUrlToCategory(catKey) {
        // Re-check date on each add, in case tab sat open over midnight
        const today = todayString();
        if (data.date !== today) {
            data = { date: today, lists: makeEmptyLists() };
        }

        const url = location.href;
        const list = data.lists[catKey] || (data.lists[catKey] = []);
        if (!list.includes(url)) {
            list.push(url);
            await saveDataToGM(data);
            refreshListDisplay();
        }
    }

    async function clearToday() {
        data = { date: todayString(), lists: makeEmptyLists() };
        await saveDataToGM(data);
        refreshListDisplay();
    }

    function buildExportText() {
        const lines = [];
        for (const cat of CATEGORIES) {
            const list = data.lists[cat.key] || [];
            lines.push(`== ${cat.label} ==`);
            if (list.length === 0) {
                lines.push('(none)');
            } else {
                for (const url of list) {
                    lines.push(url);
                }
            }
            lines.push(''); // blank line between sections
        }
        return lines.join('\n');
    }
    function importFromText(text) {
        // Start with today’s date and empty lists
        const today = todayString();
        const newData = { date: today, lists: makeEmptyLists() };

        const lines = text.split(/\r?\n/);
        let currentCatKey = null;

        // Map labels (in file) back to category keys
        const labelToKey = {};
        for (const cat of CATEGORIES) {
            labelToKey[cat.label.toLowerCase()] = cat.key;
        }

        for (let rawLine of lines) {
            const line = rawLine.trim();
            if (!line) continue; // skip blanks

            // Heading line: == Some Label ==
            const m = line.match(/^==\s*(.+?)\s*==$/);
            if (m) {
                const label = m[1].toLowerCase();
                currentCatKey = labelToKey[label] || null;
                continue;
            }

            // Non-heading: treat as URL if we have a current category
            if (currentCatKey) {
                const list = newData.lists[currentCatKey] || (newData.lists[currentCatKey] = []);
                if (!list.includes(line)) {
                    list.push(line);
                }
            }
        }

        return newData;
    }


    function downloadReport() {
        const text = buildExportText();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const date = data.date || todayString();
        a.href = url;
        a.download = `daily_report_${date}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /** ---------- UI SETUP ---------- **/

    let refreshListDisplay = function () {};// will be wired after UI init

    function createUI() {
        // Main container
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '60%';
        container.style.transform = 'translateX(-50%)';
        container.style.zIndex = '2147483647'; // max-ish, to beat chatgpt overlays
        container.style.fontFamily = 'Arial, sans-serif';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        document.body.appendChild(container);

        // Launcher button
        const launcher = document.createElement('button');
        launcher.textContent = '📋';
        launcher.title = 'Daily URL Reporter';
        launcher.style.fontSize = '16px';
        launcher.style.padding = '3px 8px';
        launcher.style.background = '#007bff';
        launcher.style.border = '1px solid #ccc';
        launcher.style.borderRadius = '5px';
        launcher.style.cursor = 'pointer';
        container.appendChild(launcher);

        // Overlay
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.zIndex = '2147483646';
        overlay.style.background = 'rgba(0,0,0,0.25)';
        overlay.style.display = 'none';
        document.body.appendChild(overlay);

        // Panel
        const panel = document.createElement('div');
        panel.style.position = 'fixed';
        panel.style.top = '60px';
        panel.style.left = '50%';
        panel.style.transform = 'translateX(-50%)';
        panel.style.minWidth = '320px';
        panel.style.maxWidth = '600px';
        panel.style.maxHeight = '70vh';
        panel.style.background = '#f0f0f0';
        panel.style.border = '1px solid #ccc';
        panel.style.borderRadius = '6px';
        panel.style.padding = '10px';
        panel.style.boxShadow = '0 4px 16px rgba(0,0,0,0.3)';
        panel.style.zIndex = '2147483647';
        panel.style.display = 'none';
        panel.style.overflow = 'hidden';
        document.body.appendChild(panel);

        // Header
        const header = document.createElement('div');
        header.style.display = 'flex';
        header.style.alignItems = 'center';
        header.style.justifyContent = 'space-between';
        header.style.marginBottom = '8px';

        const title = document.createElement('div');
        title.textContent = 'Daily URL Reporter';
        title.style.fontWeight = 'bold';

        const dateBadge = document.createElement('div');
        dateBadge.style.fontSize = '12px';
        dateBadge.style.color = '#555';
        dateBadge.textContent = data.date;

        header.appendChild(title);
        header.appendChild(dateBadge);
        panel.appendChild(header);

        // Category buttons
        const buttonsRow = document.createElement('div');
        buttonsRow.style.display = 'flex';
        buttonsRow.style.flexWrap = 'wrap';
        buttonsRow.style.gap = '6px';
        buttonsRow.style.marginBottom = '8px';

        for (const cat of CATEGORIES) {
            const btn = document.createElement('button');
            btn.textContent = `+ ${cat.label}`;
            btn.style.fontSize = '12px';
            btn.style.padding = '4px 8px';
            btn.style.background = '#007bff';
            btn.style.color = 'white';
            btn.style.border = '1px solid #ccc';
            btn.style.borderRadius = '4px';
            btn.style.cursor = 'pointer';
            btn.addEventListener('click', () => {
                // fire and forget; the async function will save and refresh
                addCurrentUrlToCategory(cat.key);
            });
            buttonsRow.appendChild(btn);
        }
        panel.appendChild(buttonsRow);

        // Export / Clear / Close row
        const actionsRow = document.createElement('div');
        actionsRow.style.display = 'flex';
        actionsRow.style.justifyContent = 'space-between';
        actionsRow.style.alignItems = 'center';
        actionsRow.style.marginBottom = '8px';

        const leftActions = document.createElement('div');
        leftActions.style.display = 'flex';
        leftActions.style.gap = '6px';

        // Hidden file input for importing
        const importInput = document.createElement('input');
        importInput.type = 'file';
        importInput.accept = '.txt,.log,.text'; // adjust as you like
        importInput.style.display = 'none';

        // When a file is chosen, read and import its content
        importInput.addEventListener('change', async () => {
            const file = importInput.files && importInput.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (ev) => {
                try {
                    const text = String(ev.target.result || '');
                    const imported = importFromText(text);

                    // Merge imported.lists into data.lists
                    const today = todayString();
                    if (data.date !== today) {
                        data = { date: today, lists: makeEmptyLists() };
                    }

                    for (const cat of CATEGORIES) {
                        const key = cat.key;
                        const existing = data.lists[key] || [];
                        const incoming = imported.lists[key] || [];
                        for (const url of incoming) {
                            if (!existing.includes(url)) {
                                existing.push(url);
                            }
                        }
                        data.lists[key] = existing;
                    }

                    await saveDataToGM(data);

                    refreshListDisplay();
                    alert('Import completed.');
                } catch (err) {
                    console.error('Import failed:', err);
                    alert('Import failed. See console for details.');
                } finally {
                    importInput.value = ''; // reset selection
                }
            };
            reader.readAsText(file);
        });

        panel.appendChild(importInput); // keep it inside panel


        const exportBtn = document.createElement('button');
        exportBtn.textContent = 'Download report';
        exportBtn.style.fontSize = '12px';
        exportBtn.style.padding = '4px 8px';
        exportBtn.style.background = '#28a745';
        exportBtn.style.color = 'white';
        exportBtn.style.border = '1px solid #ccc';
        exportBtn.style.borderRadius = '4px';
        exportBtn.style.cursor = 'pointer';
        exportBtn.onclick = downloadReport;

        const importBtn = document.createElement('button');
        importBtn.textContent = 'Import';
        importBtn.style.fontSize = '12px';
        importBtn.style.padding = '4px 8px';
        importBtn.style.background = '#6c757d'; // gray-ish
        importBtn.style.color = 'white';
        importBtn.style.border = '1px solid #ccc';
        importBtn.style.borderRadius = '4px';
        importBtn.style.cursor = 'pointer';
        importBtn.onclick = () => {
            importInput.click();
        };


        const clearBtn = document.createElement('button');
        clearBtn.textContent = 'Clear today';
        clearBtn.style.fontSize = '12px';
        clearBtn.style.padding = '4px 8px';
        clearBtn.style.background = '#dc3545';
        clearBtn.style.color = 'white';
        clearBtn.style.border = '1px solid #ccc';
        clearBtn.style.borderRadius = '4px';
        clearBtn.style.cursor = 'pointer';
        clearBtn.onclick = () => {
            if (confirm('Clear all lists for today?')) {
                clearToday();
            }
        };

        leftActions.appendChild(exportBtn);
        leftActions.appendChild(importBtn); // <-- add this
        leftActions.appendChild(clearBtn);

        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.fontSize = '12px';
        closeBtn.style.padding = '2px 6px';
        closeBtn.style.background = '#eee';
        closeBtn.style.border = '1px solid #aaa';
        closeBtn.style.borderRadius = '4px';
        closeBtn.style.cursor = 'pointer';

        actionsRow.appendChild(leftActions);
        actionsRow.appendChild(closeBtn);
        panel.appendChild(actionsRow);

        // Preview textarea
        const textarea = document.createElement('textarea');
        textarea.readOnly = true;
        textarea.style.width = '100%';
        textarea.style.height = '240px';
        textarea.style.resize = 'vertical';
        textarea.style.fontFamily = 'monospace';
        textarea.style.fontSize = '11px';
        textarea.style.padding = '6px';
        textarea.style.boxSizing = 'border-box';
        panel.appendChild(textarea);

        function showPanel() {
            refresh(); // ensure latest data before showing
            panel.style.display = 'block';
            overlay.style.display = 'block';
        }

        function hidePanel() {
            panel.style.display = 'none';
            overlay.style.display = 'none';
        }

        launcher.addEventListener('click', (e) => {
            e.stopPropagation();
            if (panel.style.display === 'block') hidePanel();
            else showPanel();
        });

        overlay.addEventListener('click', hidePanel);
        closeBtn.addEventListener('click', hidePanel);

        // Keyboard shortcut: Ctrl+Shift+O
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyO') {
                if (panel.style.display === 'block') hidePanel();
                else showPanel();
                e.preventDefault();
            }
        });

        function refresh() {
            dateBadge.textContent = data.date;
            textarea.value = buildExportText();
        }

        refreshListDisplay = refresh;
        // initial paint (in case you never open the panel, it still reflects current day)
        refresh();
    }

    // Wait for body
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createUI);
    } else {
        createUI();
    }

    /** ---------- SYNC ACROSS TABS / SITES ---------- **/

    GM_addValueChangeListener(STORAGE_KEY, async (name, oldVal, newVal, remote) => {
        // remote === true means changed in another tab
        if (!newVal) {
            data = { date: todayString(), lists: makeEmptyLists() };
        } else {
            try {
                data = JSON.parse(newVal);
            } catch {
                data = { date: todayString(), lists: makeEmptyLists() };
            }
        }
        // ensure daily reset if another tab changed it after midnight
        const today = todayString();
        if (data.date !== today) {
            data = { date: today, lists: makeEmptyLists() };
            await saveDataToGM(data);
        }
        refreshListDisplay();
    });

})();