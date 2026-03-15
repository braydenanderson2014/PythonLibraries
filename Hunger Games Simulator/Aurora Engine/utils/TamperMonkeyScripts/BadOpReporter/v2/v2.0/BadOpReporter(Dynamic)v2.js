// ==UserScript==
// @name         Dynamic URL Reporter (configurable, persistent)
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Dynamic URL categorization with configurable categories, optional daily reset, and persistent settings across tabs.
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

    /** ---------- SITE FILTERS ---------- **/

    // Whitelist: Only run on specific sites (leave empty array to run everywhere)
    const SITE_WHITELIST = [
        // 'https://flide.ap.tesla.services/3d/',
    ];

    // Blacklist: Never run on these sites (takes priority over whitelist)
    const SITE_BLACKLIST = [
        'https://tclips.ap.tesla.services/',
    ];

    // Check blacklist first
    for (const blacklistedSite of SITE_BLACKLIST) {
        if (location.href.startsWith(blacklistedSite)) {
            console.log('[URL Reporter] Site is blacklisted, exiting');
            return;
        }
    }

    // Check whitelist if configured
    if (SITE_WHITELIST.length > 0) {
        const isWhitelisted = SITE_WHITELIST.some(site => location.href.startsWith(site));
        if (!isWhitelisted) {
            console.log('[URL Reporter] Site not in whitelist, exiting');
            return;
        }
    }

    /** ---------- STORAGE KEYS ---------- **/

    const DATA_STORAGE_KEY = 'ol_urlReporter_data_v3';
    const CONFIG_STORAGE_KEY = 'ol_urlReporter_config_v3';

    /** ---------- DEFAULT CONFIG ---------- **/

    const DEFAULT_CONFIG = {
        categories: [
            { key: 'badFSWOps', label: 'Bad FSW Operators' },
            { key: 'badAudioOps', label: 'Bad Audio Prompt Ops' },
            { key: 'badAudioEval', label: 'Bad Audio Eval Ops' },
        ],
        timezone: 'America/Denver',
        dailyReset: true, // Set to false to keep data indefinitely
    };

    /** ---------- CONFIG & DATA MANAGEMENT ---------- **/

    // Load or initialize config
    async function loadConfig() {
        const raw = await GM_getValue(CONFIG_STORAGE_KEY, null);
        if (!raw) return JSON.parse(JSON.stringify(DEFAULT_CONFIG));

        try {
            const parsed = JSON.parse(raw);
            // Ensure categories array exists
            if (!Array.isArray(parsed.categories)) {
                parsed.categories = DEFAULT_CONFIG.categories;
            }
            // Ensure required fields
            if (!parsed.timezone) parsed.timezone = DEFAULT_CONFIG.timezone;
            if (typeof parsed.dailyReset !== 'boolean') parsed.dailyReset = DEFAULT_CONFIG.dailyReset;
            return parsed;
        } catch {
            return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
        }
    }

    async function saveConfig(cfg) {
        try {
            await GM_setValue(CONFIG_STORAGE_KEY, JSON.stringify(cfg));
            config = cfg; // update local reference
        } catch (e) {
            console.warn('[URL Reporter] Failed to save config', e);
        }
    }

    let config = await loadConfig();

    /** ---------- DATE & STORAGE HELPERS ---------- **/

    function todayString() {
        // YYYY-MM-DD in configured timezone
        return new Date().toLocaleDateString('en-CA', { timeZone: config.timezone });
    }

    function makeEmptyLists() {
        const lists = {};
        for (const cat of config.categories) {
            lists[cat.key] = [];
        }
        return lists;
    }

    async function loadDataFromGM() {
        const today = todayString();
        const raw = await GM_getValue(DATA_STORAGE_KEY, null);

        if (!raw) {
            return { date: today, lists: makeEmptyLists() };
        }

        let parsed;
        try {
            parsed = JSON.parse(raw);
        } catch {
            return { date: today, lists: makeEmptyLists() };
        }

        // Daily reset (only if enabled)
        if (config.dailyReset && (!parsed || parsed.date !== today)) {
            return { date: today, lists: makeEmptyLists() };
        }

        if (!parsed.lists) parsed.lists = {};

        // Make sure all current categories exist, preserve data for existing ones
        for (const cat of config.categories) {
            if (!Array.isArray(parsed.lists[cat.key])) {
                parsed.lists[cat.key] = [];
            }
        }

        // Update date if not set
        if (!parsed.date) parsed.date = today;

        return parsed;
    }

    async function saveDataToGM(d) {
        try {
            await GM_setValue(DATA_STORAGE_KEY, JSON.stringify(d));
        } catch (e) {
            console.warn('[URL Reporter] Failed to save data', e);
        }
    }

    // Shared state for this tab
    let data = await loadDataFromGM();

    /** ---------- DATA ACTIONS ---------- **/

    async function addCurrentUrlToCategory(catKey) {
        // Re-check date on each add if daily reset is enabled
        if (config.dailyReset) {
            const today = todayString();
            if (data.date !== today) {
                data = { date: today, lists: makeEmptyLists() };
            }
        }

        const url = location.href;
        const list = data.lists[catKey] || (data.lists[catKey] = []);
        if (!list.includes(url)) {
            list.push(url);
            await saveDataToGM(data);
            refreshListDisplay();
        }
    }

    async function clearAllData() {
        data = { date: todayString(), lists: makeEmptyLists() };
        await saveDataToGM(data);
        refreshListDisplay();
    }

    function buildExportText() {
        const lines = [];
        for (const cat of config.categories) {
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
        // Start with current date and empty lists
        const today = todayString();
        const newData = { date: today, lists: makeEmptyLists() };

        const lines = text.split(/\r?\n/);
        let currentCatKey = null;

        // Map labels (in file) back to category keys
        const labelToKey = {};
        for (const cat of config.categories) {
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
        a.download = `url_report_${date}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /** ---------- UI SETUP ---------- **/

    let refreshListDisplay = function () {};
    let rebuildCategoryButtons = function () {};

    function createUI() {
        console.log('[URL Reporter] createUI called');

        // Check if document.body is available
        if (!document.body) {
            console.error('[URL Reporter] document.body not available yet!');
            return;
        }

        // Check if UI already exists in DOM
        const existingContainer = document.querySelector('[data-url-reporter="container"]');
        if (existingContainer) {
            console.warn('[URL Reporter] UI already exists in DOM, skipping creation');
            return;
        }

        console.log('[URL Reporter] Creating new UI...');

        // Main container
        const container = document.createElement('div');
        container.setAttribute('data-url-reporter', 'container');
        container.style.cssText = `
            position: fixed;
            top: 0;
            left: calc(60% + 70px);
            transform: translateX(-50%);
            z-index: 2147483647;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        `;
        document.body.appendChild(container);

        // Launcher button
        const launcher = document.createElement('button');
        launcher.textContent = '📋';
        launcher.title = 'Dynamic URL Reporter';
        launcher.style.cssText = `
            font-size: 16px;
            padding: 3px 8px;
            background: #007bff;
            color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
        `;
        container.appendChild(launcher);

        // Overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 2147483646;
            background: rgba(0,0,0,0.25);
            display: none;
        `;
        document.body.appendChild(overlay);

        // Main Panel
        const panel = document.createElement('div');
        panel.style.cssText = `
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            min-width: 400px;
            max-width: 700px;
            max-height: 70vh;
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            z-index: 2147483647;
            display: none;
            overflow: hidden;
        `;
        document.body.appendChild(panel);

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        `;

        const title = document.createElement('div');
        title.textContent = 'Dynamic URL Reporter';
        title.style.cssText = `font-weight: bold; font-size: 14px;`;

        const dateBadge = document.createElement('div');
        dateBadge.style.cssText = `font-size: 12px; color: #555;`;
        dateBadge.textContent = config.dailyReset ? data.date : 'Persistent';

        header.appendChild(title);
        header.appendChild(dateBadge);
        panel.appendChild(header);

        // Category buttons container
        const buttonsRow = document.createElement('div');
        buttonsRow.style.cssText = `
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;
        `;
        panel.appendChild(buttonsRow);

        // Function to rebuild category buttons
        rebuildCategoryButtons = () => {
            // Use proper DOM methods instead of innerHTML to avoid Trusted Types errors
            while (buttonsRow.firstChild) {
                buttonsRow.removeChild(buttonsRow.firstChild);
            }
            for (const cat of config.categories) {
                const btn = document.createElement('button');
                btn.textContent = `+ ${cat.label}`;
                btn.style.cssText = `
                    font-size: 12px;
                    padding: 4px 8px;
                    background: #007bff;
                    color: white;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    cursor: pointer;
                `;
                btn.addEventListener('click', () => {
                    addCurrentUrlToCategory(cat.key);
                });
                buttonsRow.appendChild(btn);
            }
        };

        rebuildCategoryButtons(); // Initial build

        // Action buttons row
        const actionsRow = document.createElement('div');
        actionsRow.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        `;

        const leftActions = document.createElement('div');
        leftActions.style.cssText = `display: flex; gap: 6px;`;

        // Settings button
        const settingsBtn = document.createElement('button');
        settingsBtn.textContent = '⚙️ Settings';
        settingsBtn.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            background: #6c757d;
            color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        `;
        settingsBtn.onclick = () => showSettingsPanel();

        // Export button
        const exportBtn = document.createElement('button');
        exportBtn.textContent = '📥 Download';
        exportBtn.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            background: #28a745;
            color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        `;
        exportBtn.onclick = downloadReport;

        // Import hidden input
        const importInput = document.createElement('input');
        importInput.type = 'file';
        importInput.accept = '.txt,.log,.text';
        importInput.style.display = 'none';

        importInput.addEventListener('change', async () => {
            const file = importInput.files && importInput.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (ev) => {
                try {
                    const text = String(ev.target.result || '');
                    const imported = importFromText(text);

                    const today = todayString();
                    if (config.dailyReset && data.date !== today) {
                        data = { date: today, lists: makeEmptyLists() };
                    }

                    for (const cat of config.categories) {
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
                    importInput.value = '';
                }
            };
            reader.readAsText(file);
        });

        panel.appendChild(importInput);

        // Import button
        const importBtn = document.createElement('button');
        importBtn.textContent = '📤 Import';
        importBtn.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            background: #17a2b8;
            color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        `;
        importBtn.onclick = () => importInput.click();

        // Clear button
        const clearBtn = document.createElement('button');
        clearBtn.textContent = '🗑️ Clear All';
        clearBtn.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            background: #dc3545;
            color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        `;
        clearBtn.onclick = () => {
            if (confirm('Clear all URL lists?')) {
                clearAllData();
            }
        };

        leftActions.appendChild(settingsBtn);
        leftActions.appendChild(exportBtn);
        leftActions.appendChild(importBtn);
        leftActions.appendChild(clearBtn);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.cssText = `
            font-size: 12px;
            padding: 2px 6px;
            background: #eee;
            border: 1px solid #aaa;
            border-radius: 4px;
            cursor: pointer;
        `;

        actionsRow.appendChild(leftActions);
        actionsRow.appendChild(closeBtn);
        panel.appendChild(actionsRow);

        // Preview textarea
        const textarea = document.createElement('textarea');
        textarea.readOnly = true;
        textarea.style.cssText = `
            width: 100%;
            height: 240px;
            resize: vertical;
            font-family: monospace;
            font-size: 11px;
            padding: 6px;
            box-sizing: border-box;
        `;
        panel.appendChild(textarea);

        // Settings Panel
        function showSettingsPanel() {
            hidePanel();
            settingsPanel.style.display = 'block';
            overlay.style.display = 'block';
            refreshSettingsUI();
        }

        const settingsPanel = document.createElement('div');
        settingsPanel.style.cssText = `
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            width: 500px;
            max-height: 70vh;
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 15px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            z-index: 2147483647;
            display: none;
            overflow-y: auto;
        `;
        document.body.appendChild(settingsPanel);

        function refreshSettingsUI() {
            // Use proper DOM methods instead of innerHTML to avoid Trusted Types errors
            while (settingsPanel.firstChild) {
                settingsPanel.removeChild(settingsPanel.firstChild);
            }

            // Header
            const settingsHeader = document.createElement('div');
            settingsHeader.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            `;

            const settingsTitle = document.createElement('div');
            settingsTitle.textContent = '⚙️ Settings';
            settingsTitle.style.cssText = `font-weight: bold; font-size: 16px;`;

            const settingsCloseBtn = document.createElement('button');
            settingsCloseBtn.textContent = '✕';
            settingsCloseBtn.style.cssText = `
                font-size: 12px;
                padding: 2px 6px;
                background: #eee;
                border: 1px solid #aaa;
                border-radius: 4px;
                cursor: pointer;
            `;
            settingsCloseBtn.onclick = () => {
                settingsPanel.style.display = 'none';
                overlay.style.display = 'none';
            };

            settingsHeader.appendChild(settingsTitle);
            settingsHeader.appendChild(settingsCloseBtn);
            settingsPanel.appendChild(settingsHeader);

            // Daily Reset Toggle
            const resetSection = document.createElement('div');
            resetSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const resetLabel = document.createElement('label');
            resetLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            `;

            const resetCheckbox = document.createElement('input');
            resetCheckbox.type = 'checkbox';
            resetCheckbox.checked = config.dailyReset;
            resetCheckbox.onchange = async () => {
                config.dailyReset = resetCheckbox.checked;
                await saveConfig(config);
                refreshListDisplay();
            };

            const resetText = document.createElement('span');
            resetText.textContent = 'Daily Reset (clear data each day)';

            resetLabel.appendChild(resetCheckbox);
            resetLabel.appendChild(resetText);
            resetSection.appendChild(resetLabel);
            settingsPanel.appendChild(resetSection);

            // Timezone
            const tzSection = document.createElement('div');
            tzSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const tzLabel = document.createElement('div');
            tzLabel.textContent = 'Timezone:';
            tzLabel.style.cssText = `font-weight: bold; margin-bottom: 5px; font-size: 12px;`;

            const tzInput = document.createElement('input');
            tzInput.type = 'text';
            tzInput.value = config.timezone;
            tzInput.style.cssText = `
                width: 100%;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
            `;
            tzInput.onchange = async () => {
                config.timezone = tzInput.value;
                await saveConfig(config);
                refreshListDisplay();
            };

            tzSection.appendChild(tzLabel);
            tzSection.appendChild(tzInput);
            settingsPanel.appendChild(tzSection);

            // Categories
            const catSection = document.createElement('div');
            catSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const catTitle = document.createElement('div');
            catTitle.textContent = 'Categories:';
            catTitle.style.cssText = `font-weight: bold; margin-bottom: 10px; font-size: 12px;`;
            catSection.appendChild(catTitle);

            // List existing categories
            for (let i = 0; i < config.categories.length; i++) {
                const cat = config.categories[i];
                const catRow = document.createElement('div');
                catRow.style.cssText = `
                    display: flex;
                    gap: 6px;
                    margin-bottom: 6px;
                    align-items: center;
                `;

                const keyInput = document.createElement('input');
                keyInput.type = 'text';
                keyInput.value = cat.key;
                keyInput.placeholder = 'key';
                keyInput.style.cssText = `
                    flex: 1;
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 11px;
                `;
                // Capture cat reference to avoid closure issue
                keyInput.onchange = (function(category) {
                    return async function() {
                        const oldKey = category.key;
                        const newKey = keyInput.value.trim();
                        if (newKey && newKey !== oldKey) {
                            // Rename in data lists
                            if (data.lists[oldKey]) {
                                data.lists[newKey] = data.lists[oldKey];
                                delete data.lists[oldKey];
                                await saveDataToGM(data);
                            }
                            category.key = newKey;
                            await saveConfig(config);
                            rebuildCategoryButtons();
                            refreshListDisplay();
                        }
                    };
                })(cat);

                const labelInput = document.createElement('input');
                labelInput.type = 'text';
                labelInput.value = cat.label;
                labelInput.placeholder = 'label';
                labelInput.style.cssText = `
                    flex: 2;
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 11px;
                `;
                // Capture cat reference to avoid closure issue
                labelInput.onchange = (function(category) {
                    return async function() {
                        category.label = labelInput.value.trim() || category.key;
                        await saveConfig(config);
                        rebuildCategoryButtons();
                        refreshListDisplay();
                    };
                })(cat);

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = '🗑️';
                deleteBtn.style.cssText = `
                    padding: 4px 8px;
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                `;
                // Capture both cat and i to avoid closure issue
                deleteBtn.onclick = (function(category, index) {
                    return async function() {
                        if (confirm(`Delete category "${category.label}"?`)) {
                            config.categories.splice(index, 1);
                            delete data.lists[category.key];
                            await saveConfig(config);
                            await saveDataToGM(data);
                            refreshSettingsUI();
                            rebuildCategoryButtons();
                            refreshListDisplay();
                        }
                    };
                })(cat, i);

                catRow.appendChild(keyInput);
                catRow.appendChild(labelInput);
                catRow.appendChild(deleteBtn);
                catSection.appendChild(catRow);
            }

            // Add new category button
            const addCatBtn = document.createElement('button');
            addCatBtn.textContent = '+ Add Category';
            addCatBtn.style.cssText = `
                width: 100%;
                margin-top: 8px;
                padding: 6px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            addCatBtn.onclick = async () => {
                const newKey = `category${Date.now()}`;
                const newLabel = 'New Category';
                config.categories.push({ key: newKey, label: newLabel });
                data.lists[newKey] = [];
                await saveConfig(config);
                await saveDataToGM(data);
                refreshSettingsUI();
                rebuildCategoryButtons();
                refreshListDisplay();
            };

            catSection.appendChild(addCatBtn);
            settingsPanel.appendChild(catSection);
        }

        // Panel visibility controls
        function showPanel() {
            refresh();
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

        overlay.addEventListener('click', () => {
            hidePanel();
            settingsPanel.style.display = 'none';
        });

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
            dateBadge.textContent = config.dailyReset ? data.date : 'Persistent';
            textarea.value = buildExportText();
        }

        refreshListDisplay = refresh;
        refresh();
    }

    // Wait for body - since @run-at is document-end, DOM is already loaded
    // Use a flag to prevent double-initialization
    let uiCreated = false;

    function initUI() {
        console.log('[URL Reporter] initUI called, uiCreated:', uiCreated, 'readyState:', document.readyState);
        if (uiCreated) {
            console.warn('[URL Reporter] UI already created, skipping duplicate initialization');
            return;
        }
        uiCreated = true;
        createUI();
    }

    console.log('[URL Reporter] Script starting, readyState:', document.readyState);
    if (document.readyState === 'loading') {
        console.log('[URL Reporter] Adding DOMContentLoaded listener');
        document.addEventListener('DOMContentLoaded', initUI);
    } else {
        console.log('[URL Reporter] DOM already loaded, calling initUI immediately');
        initUI();
    }

    /** ---------- SYNC ACROSS TABS / SITES ---------- **/

    GM_addValueChangeListener(DATA_STORAGE_KEY, async (name, oldVal, newVal, remote) => {
        if (!newVal) {
            data = { date: todayString(), lists: makeEmptyLists() };
        } else {
            try {
                data = JSON.parse(newVal);
            } catch {
                data = { date: todayString(), lists: makeEmptyLists() };
            }
        }

        // Ensure daily reset if another tab changed it after midnight
        if (config.dailyReset) {
            const today = todayString();
            if (data.date !== today) {
                data = { date: today, lists: makeEmptyLists() };
                await saveDataToGM(data);
            }
        }
        refreshListDisplay();
    });

    // Listen for config changes from other tabs
    GM_addValueChangeListener(CONFIG_STORAGE_KEY, async (name, oldVal, newVal, remote) => {
        if (newVal) {
            try {
                config = JSON.parse(newVal);
                rebuildCategoryButtons();
                refreshListDisplay();
            } catch (e) {
                console.warn('[URL Reporter] Failed to parse config update', e);
            }
        }
    });

})();
