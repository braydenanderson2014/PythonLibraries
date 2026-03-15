// ==UserScript==
// @name         Dynamic URL Reporter (configurable, persistent)
// @namespace    http://tampermonkey.net/
// @version      2.3
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

    /** ---------- STORAGE KEYS ---------- **/

    const DATA_STORAGE_KEY = 'ol_urlReporter_data_v3';
    const CONFIG_STORAGE_KEY = 'ol_urlReporter_config_v3';
    
    /** ---------- DEFAULT CONFIG ---------- **/
    
    const DEFAULT_CONFIG = {
        categories: [
            { key: 'badFSWOps', label: 'Bad FSW Operators', keybinding: 'Ctrl+Shift+1' },
            { key: 'badAudioOps', label: 'Bad Audio Prompt Ops', keybinding: 'Ctrl+Shift+2' },
            { key: 'badAudioEval', label: 'Bad Audio Eval Ops', keybinding: 'Ctrl+Shift+3' },
        ],
        timezone: 'America/Denver',
        dailyReset: true, // Set to false to keep data indefinitely
        siteWhitelist: [], // Only run on these sites (empty = run everywhere)
        siteBlacklist: [], // Never run on these sites (takes priority)
        useTopFrameOnly: true, // Only run in top-level frame, not iframes
        exportFormat: 'txt', // 'txt' or 'md'
        iconPosition: { x: null, y: null }, // null = use default position
        iconVisible: true,
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
            // Ensure each category has a keybinding field (default to empty string)
            for (const cat of parsed.categories) {
                if (!cat.hasOwnProperty('keybinding')) {
                    cat.keybinding = '';
                }
            }
            // Ensure required fields
            if (!parsed.timezone) parsed.timezone = DEFAULT_CONFIG.timezone;
            if (typeof parsed.dailyReset !== 'boolean') parsed.dailyReset = DEFAULT_CONFIG.dailyReset;
            if (!Array.isArray(parsed.siteWhitelist)) parsed.siteWhitelist = DEFAULT_CONFIG.siteWhitelist;
            if (!Array.isArray(parsed.siteBlacklist)) parsed.siteBlacklist = DEFAULT_CONFIG.siteBlacklist;
            if (typeof parsed.useTopFrameOnly !== 'boolean') parsed.useTopFrameOnly = DEFAULT_CONFIG.useTopFrameOnly;
            if (!parsed.exportFormat || !['txt', 'md'].includes(parsed.exportFormat)) parsed.exportFormat = DEFAULT_CONFIG.exportFormat;
            if (!parsed.iconPosition) parsed.iconPosition = DEFAULT_CONFIG.iconPosition;
            if (typeof parsed.iconVisible !== 'boolean') parsed.iconVisible = DEFAULT_CONFIG.iconVisible;
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

    /** ---------- SITE FILTERING ---------- **/
    
    // Check if we should run based on frame context
    if (config.useTopFrameOnly && window.self !== window.top) {
        console.log('[URL Reporter] Running in iframe, exiting (useTopFrameOnly enabled)');
        return;
    }
    
    // Check blacklist first (takes priority)
    for (const blacklistedSite of config.siteBlacklist) {
        if (blacklistedSite && location.href.startsWith(blacklistedSite)) {
            console.log('[URL Reporter] Site is blacklisted, exiting:', blacklistedSite);
            return;
        }
    }
    
    // Check whitelist if configured
    if (config.siteWhitelist.length > 0) {
        const isWhitelisted = config.siteWhitelist.some(site => site && location.href.startsWith(site));
        if (!isWhitelisted) {
            console.log('[URL Reporter] Site not in whitelist, exiting');
            return;
        }
    }

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
    
    function buildMarkdownExport() {
        const lines = [];
        const date = data.date || todayString();
        
        // Title
        lines.push(`# URL Report - ${date}`);
        lines.push('');
        
        for (const cat of config.categories) {
            const list = data.lists[cat.key] || [];
            
            // Category heading
            lines.push(`## ${cat.label}`);
            lines.push('');
            
            if (list.length === 0) {
                lines.push('*(no URLs)*');
                lines.push('');
            } else {
                // URLs in code blocks for easy copying
                lines.push('```');
                for (const url of list) {
                    lines.push(url);
                }
                lines.push('```');
                lines.push('');
            }
        }
        
        return lines.join('\n');
    }

    function downloadReport() {
        let text, extension, mimeType;
        
        if (config.exportFormat === 'md') {
            text = buildMarkdownExport();
            extension = 'md';
            mimeType = 'text/markdown';
        } else {
            text = buildExportText();
            extension = 'txt';
            mimeType = 'text/plain';
        }
        
        const blob = new Blob([text], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const date = data.date || todayString();
        a.href = url;
        a.download = `url_report_${date}.${extension}`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /** ---------- KEYBINDING MANAGEMENT ---------- **/
    
    function parseKeybinding(binding) {
        if (!binding) return null;
        
        const parts = binding.split('+').map(p => p.trim());
        return {
            ctrl: parts.includes('Ctrl'),
            shift: parts.includes('Shift'),
            alt: parts.includes('Alt'),
            key: parts[parts.length - 1].toLowerCase(), // Last part is the key, normalized
        };
    }
    
    function matchesKeybinding(event, binding) {
        const parsed = parseKeybinding(binding);
        if (!parsed) return false;
        
        // Normalize the event key to lowercase
        const eventKey = event.key.toLowerCase();
        
        // Check modifiers match
        const modifiersMatch = event.ctrlKey === parsed.ctrl &&
                              event.shiftKey === parsed.shift &&
                              event.altKey === parsed.alt;
        
        if (!modifiersMatch) return false;
        
        // Check if key matches (try both event.key and the key without shift transformation)
        return eventKey === parsed.key || event.code.toLowerCase().replace('key', '').replace('digit', '') === parsed.key;
    }
    
    function registerKeybindings() {
        console.log('[URL Reporter] Registering keybindings:', config.categories.map(c => ({label: c.label, binding: c.keybinding})));
        
        window.addEventListener('keydown', async (e) => {
            // Debug logging
            const debugInfo = {
                key: e.key,
                code: e.code,
                ctrl: e.ctrlKey,
                shift: e.shiftKey,
                alt: e.altKey
            };
            
            // Check each category's keybinding
            for (const cat of config.categories) {
                if (cat.keybinding && matchesKeybinding(e, cat.keybinding)) {
                    console.log('[URL Reporter] Keybinding matched!', cat.label, debugInfo);
                    e.preventDefault();
                    
                    // Add current URL to this category
                    await addCurrentUrlToCategory(cat.key);
                    
                    // Show visual feedback
                    showToast(`Added to ${cat.label}!`);
                    break;
                }
            }
        });
    }
    
    function showToast(message) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 2147483647;
            font-family: Arial, sans-serif;
            font-size: 14px;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
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
        const iconPos = config.iconPosition;
        const hasCustomPosition = iconPos.x !== null && iconPos.y !== null;
        
        container.style.cssText = `
            position: fixed;
            ${hasCustomPosition ? `left: ${iconPos.x}px; top: ${iconPos.y}px;` : 'top: 0; left: calc(60% + 60px); transform: translateX(-50%);'}
            z-index: 2147483647;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: move;
            ${config.iconVisible ? '' : 'display: none;'}
        `;
        document.body.appendChild(container);

        // Make container draggable
        let isDragging = false;
        let dragOffset = { x: 0, y: 0 };
        
        container.addEventListener('mousedown', (e) => {
            // Only start drag if clicking the container itself, not children
            if (e.target === container || e.target === launcher) {
                isDragging = true;
                const rect = container.getBoundingClientRect();
                dragOffset.x = e.clientX - rect.left;
                dragOffset.y = e.clientY - rect.top;
                container.style.transform = 'none'; // Remove default transform when dragging
                e.preventDefault();
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const x = e.clientX - dragOffset.x;
                const y = e.clientY - dragOffset.y;
                container.style.left = `${x}px`;
                container.style.top = `${y}px`;
            }
        });
        
        document.addEventListener('mouseup', async (e) => {
            if (isDragging) {
                isDragging = false;
                // Save position
                const rect = container.getBoundingClientRect();
                config.iconPosition = { x: rect.left, y: rect.top };
                await saveConfig(config);
            }
        });

        // Launcher button
        const launcher = document.createElement('button');
        launcher.textContent = '📋';
        launcher.title = 'Dynamic URL Reporter (Drag to move, Ctrl+Shift+B to hide/show)';
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

        // URL List Container (replacing simple textarea)
        const listContainer = document.createElement('div');
        listContainer.style.cssText = `
            width: 100%;
            max-height: 400px;
            overflow-y: auto;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 8px;
            box-sizing: border-box;
        `;
        panel.appendChild(listContainer);
        
        // Copy All button row
        const copyAllRow = document.createElement('div');
        copyAllRow.style.cssText = `
            display: flex;
            justify-content: flex-end;
            margin-top: 8px;
            gap: 8px;
        `;
        
        const copyAllBtn = document.createElement('button');
        copyAllBtn.textContent = '📋 Copy All';
        copyAllBtn.title = 'Copy all URLs to clipboard';
        copyAllBtn.style.cssText = `
            padding: 6px 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        `;
        copyAllBtn.onmouseover = () => copyAllBtn.style.background = '#218838';
        copyAllBtn.onmouseout = () => copyAllBtn.style.background = '#28a745';
        copyAllBtn.onclick = () => {
            const text = config.exportFormat === 'md' ? buildMarkdownExport() : buildExportText();
            navigator.clipboard.writeText(text).then(() => {
                copyAllBtn.textContent = '✓ Copied!';
                setTimeout(() => copyAllBtn.textContent = '📋 Copy All', 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy to clipboard');
            });
        };
        
        copyAllRow.appendChild(copyAllBtn);
        panel.appendChild(copyAllRow);

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
            resetText.style.cssText = `
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333;
                user-select: none;
            `;

            resetLabel.appendChild(resetCheckbox);
            resetLabel.appendChild(resetText);
            resetSection.appendChild(resetLabel);
            settingsPanel.appendChild(resetSection);

            // Export Format Selection
            const exportFormatSection = document.createElement('div');
            exportFormatSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const exportFormatLabel = document.createElement('div');
            exportFormatLabel.textContent = 'Export Format:';
            exportFormatLabel.style.cssText = `font-weight: bold; margin-bottom: 8px; font-size: 12px;`;
            exportFormatSection.appendChild(exportFormatLabel);

            const formatOptions = document.createElement('div');
            formatOptions.style.cssText = `
                display: flex;
                gap: 15px;
            `;

            // TXT option
            const txtLabel = document.createElement('label');
            txtLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
            `;

            const txtRadio = document.createElement('input');
            txtRadio.type = 'radio';
            txtRadio.name = 'exportFormat';
            txtRadio.value = 'txt';
            txtRadio.checked = config.exportFormat === 'txt';
            txtRadio.onchange = async () => {
                config.exportFormat = 'txt';
                await saveConfig(config);
            };

            const txtText = document.createElement('span');
            txtText.textContent = 'Plain Text (.txt)';
            txtText.style.cssText = `font-size: 12px; color: #333;`;

            txtLabel.appendChild(txtRadio);
            txtLabel.appendChild(txtText);

            // MD option
            const mdLabel = document.createElement('label');
            mdLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
            `;

            const mdRadio = document.createElement('input');
            mdRadio.type = 'radio';
            mdRadio.name = 'exportFormat';
            mdRadio.value = 'md';
            mdRadio.checked = config.exportFormat === 'md';
            mdRadio.onchange = async () => {
                config.exportFormat = 'md';
                await saveConfig(config);
            };

            const mdText = document.createElement('span');
            mdText.textContent = 'Markdown (.md)';
            mdText.style.cssText = `font-size: 12px; color: #333;`;

            mdLabel.appendChild(mdRadio);
            mdLabel.appendChild(mdText);

            formatOptions.appendChild(txtLabel);
            formatOptions.appendChild(mdLabel);
            exportFormatSection.appendChild(formatOptions);

            const formatHelp = document.createElement('div');
            formatHelp.textContent = 'Markdown format includes headings and code blocks for easy copying in chat apps';
            formatHelp.style.cssText = `
                font-size: 10px;
                color: #666;
                margin-top: 6px;
                font-style: italic;
            `;
            exportFormatSection.appendChild(formatHelp);

            settingsPanel.appendChild(exportFormatSection);

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

            // Site Filters Section
            const filterSection = document.createElement('div');
            filterSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const filterTitle = document.createElement('div');
            filterTitle.textContent = 'Site Filters:';
            filterTitle.style.cssText = `font-weight: bold; margin-bottom: 10px; font-size: 12px;`;
            filterSection.appendChild(filterTitle);

            // Top Frame Only Toggle
            const topFrameLabel = document.createElement('label');
            topFrameLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                margin-bottom: 10px;
            `;

            const topFrameCheckbox = document.createElement('input');
            topFrameCheckbox.type = 'checkbox';
            topFrameCheckbox.checked = config.useTopFrameOnly;
            topFrameCheckbox.onchange = async () => {
                config.useTopFrameOnly = topFrameCheckbox.checked;
                await saveConfig(config);
            };

            const topFrameText = document.createElement('span');
            topFrameText.textContent = 'Only run in top-level window (not iframes)';
            topFrameText.style.cssText = `
                font-size: 11px;
                color: #333;
            `;

            topFrameLabel.appendChild(topFrameCheckbox);
            topFrameLabel.appendChild(topFrameText);
            filterSection.appendChild(topFrameLabel);

            // Whitelist
            const whitelistLabel = document.createElement('div');
            whitelistLabel.textContent = 'Whitelist (only run on these URLs):';
            whitelistLabel.style.cssText = `font-size: 11px; margin-top: 10px; margin-bottom: 5px; color: #666;`;
            filterSection.appendChild(whitelistLabel);

            const whitelistTextarea = document.createElement('textarea');
            whitelistTextarea.value = config.siteWhitelist.join('\n');
            whitelistTextarea.placeholder = 'One URL per line\nhttps://example.com/\nhttps://another.com/page';
            whitelistTextarea.style.cssText = `
                width: 100%;
                height: 60px;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10px;
                font-family: monospace;
                resize: vertical;
                box-sizing: border-box;
            `;
            whitelistTextarea.onchange = async () => {
                config.siteWhitelist = whitelistTextarea.value.split('\n').map(s => s.trim()).filter(s => s);
                await saveConfig(config);
            };
            filterSection.appendChild(whitelistTextarea);

            // Blacklist
            const blacklistLabel = document.createElement('div');
            blacklistLabel.textContent = 'Blacklist (never run on these URLs):';
            blacklistLabel.style.cssText = `font-size: 11px; margin-top: 10px; margin-bottom: 5px; color: #666;`;
            filterSection.appendChild(blacklistLabel);

            const blacklistTextarea = document.createElement('textarea');
            blacklistTextarea.value = config.siteBlacklist.join('\n');
            blacklistTextarea.placeholder = 'One URL per line\nhttps://blocked.com/\nhttps://another-blocked.com/';
            blacklistTextarea.style.cssText = `
                width: 100%;
                height: 60px;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10px;
                font-family: monospace;
                resize: vertical;
                box-sizing: border-box;
            `;
            blacklistTextarea.onchange = async () => {
                config.siteBlacklist = blacklistTextarea.value.split('\n').map(s => s.trim()).filter(s => s);
                await saveConfig(config);
            };
            filterSection.appendChild(blacklistTextarea);

            settingsPanel.appendChild(filterSection);

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
                            refreshSettingsUI();
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
                        refreshSettingsUI();
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
                config.categories.push({ key: newKey, label: newLabel, keybinding: '' });
                data.lists[newKey] = [];
                await saveConfig(config);
                await saveDataToGM(data);
                refreshSettingsUI();
                rebuildCategoryButtons();
                refreshListDisplay();
            };

            catSection.appendChild(addCatBtn);
            settingsPanel.appendChild(catSection);
            
            // Icon Controls Section
            const iconControlsSection = document.createElement('div');
            iconControlsSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const iconControlsTitle = document.createElement('div');
            iconControlsTitle.textContent = 'Icon Controls:';
            iconControlsTitle.style.cssText = `font-weight: bold; margin-bottom: 10px; font-size: 12px;`;
            iconControlsSection.appendChild(iconControlsTitle);

            const iconButtonsRow = document.createElement('div');
            iconButtonsRow.style.cssText = `
                display: flex;
                gap: 8px;
                align-items: center;
            `;

            const resetPosBtn = document.createElement('button');
            resetPosBtn.textContent = '↺ Reset Position';
            resetPosBtn.style.cssText = `
                padding: 6px 12px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            resetPosBtn.onclick = async () => {
                config.iconPosition = { x: null, y: null };
                await saveConfig(config);
                showToast('Position reset - reload page to apply');
            };

            const hideHint = document.createElement('span');
            hideHint.textContent = 'Ctrl+Shift+B to hide/show icon';
            hideHint.style.cssText = `font-size: 11px; color: #666; font-style: italic;`;

            iconButtonsRow.appendChild(resetPosBtn);
            iconButtonsRow.appendChild(hideHint);
            iconControlsSection.appendChild(iconButtonsRow);
            settingsPanel.appendChild(iconControlsSection);

            // Keybindings Section
            const keybindSection = document.createElement('div');
            keybindSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            `;

            const keybindTitle = document.createElement('div');
            keybindTitle.textContent = 'Keybindings (Quick Add URL):';
            keybindTitle.style.cssText = `font-weight: bold; margin-bottom: 10px; font-size: 12px;`;
            keybindSection.appendChild(keybindTitle);

            const keybindHelp = document.createElement('div');
            keybindHelp.textContent = 'Type manually (Ctrl+Shift+1) or click Record to capture keys';
            keybindHelp.style.cssText = `
                font-size: 10px;
                color: #666;
                margin-bottom: 8px;
                font-style: italic;
            `;
            keybindSection.appendChild(keybindHelp);

            // List keybindings for each category
            for (let i = 0; i < config.categories.length; i++) {
                const cat = config.categories[i];
                const kbRow = document.createElement('div');
                kbRow.style.cssText = `
                    display: flex;
                    gap: 6px;
                    margin-bottom: 6px;
                    align-items: center;
                `;

                const kbLabel = document.createElement('div');
                kbLabel.textContent = cat.label + ':';
                kbLabel.style.cssText = `
                    flex: 0 0 120px;
                    font-size: 11px;
                    color: #333;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                `;

                const kbInput = document.createElement('input');
                kbInput.type = 'text';
                kbInput.value = cat.keybinding || '';
                kbInput.placeholder = 'Ctrl+Shift+1';
                kbInput.style.cssText = `
                    flex: 1;
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 11px;
                    font-family: monospace;
                `;
                
                // Allow manual typing
                kbInput.oninput = (function(category, input) {
                    return async function() {
                        category.keybinding = input.value.trim();
                        await saveConfig(config);
                    };
                })(cat, kbInput);
                
                // Record button
                const recordBtn = document.createElement('button');
                recordBtn.textContent = '⏺️ Record';
                recordBtn.style.cssText = `
                    padding: 4px 8px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 10px;
                    white-space: nowrap;
                `;
                
                recordBtn.onclick = (function(category, input, btn) {
                    return function() {
                        // Enter recording mode
                        btn.textContent = '⏹️ Stop';
                        btn.style.background = '#dc3545';
                        input.value = 'Press keys...';
                        input.style.background = '#fff3cd';
                        
                        // Create one-time listener
                        const recordListener = function(e) {
                            // Ignore if ONLY modifier keys are pressed (no actual key yet)
                            if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
                                return; // Wait for the actual key
                            }
                            
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log('[URL Reporter] Recording key:', {
                                key: e.key,
                                code: e.code,
                                ctrl: e.ctrlKey,
                                shift: e.shiftKey,
                                alt: e.altKey
                            });
                            
                            // Build keybinding string from event
                            const parts = [];
                            if (e.ctrlKey) parts.push('Ctrl');
                            if (e.shiftKey) parts.push('Shift');
                            if (e.altKey) parts.push('Alt');
                            
                            // Add the actual key
                            // For numbers with shift (like !), we want the base key (1)
                            let keyToStore = e.key;
                            if (e.code.startsWith('Digit')) {
                                keyToStore = e.code.replace('Digit', '');
                            } else if (e.code.startsWith('Key')) {
                                keyToStore = e.code.replace('Key', '').toLowerCase();
                            }
                            parts.push(keyToStore);
                            
                            const binding = parts.join('+');
                            console.log('[URL Reporter] Recorded binding:', binding);
                            input.value = binding;
                            category.keybinding = binding;
                            saveConfig(config);
                            
                            // Exit recording mode
                            btn.textContent = '⏺️ Record';
                            btn.style.background = '#007bff';
                            input.style.background = 'white';
                            window.removeEventListener('keydown', recordListener, true);
                        };
                        
                        window.addEventListener('keydown', recordListener, true);
                    };
                })(cat, kbInput, recordBtn);

                const clearBtn = document.createElement('button');
                clearBtn.textContent = 'Clear';
                clearBtn.style.cssText = `
                    padding: 4px 8px;
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 10px;
                `;
                clearBtn.onclick = (function(category, input) {
                    return async function() {
                        category.keybinding = '';
                        input.value = '';
                        await saveConfig(config);
                    };
                })(cat, kbInput);

                kbRow.appendChild(kbLabel);
                kbRow.appendChild(kbInput);
                kbRow.appendChild(recordBtn);
                kbRow.appendChild(clearBtn);
                keybindSection.appendChild(kbRow);
            }

            settingsPanel.appendChild(keybindSection);
            
            // Import/Export Settings Section
            const ieSection = document.createElement('div');
            ieSection.style.cssText = `
                margin-top: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
                display: flex;
                gap: 8px;
                justify-content: center;
            `;
            
            const exportSettingsBtn = document.createElement('button');
            exportSettingsBtn.textContent = '📤 Export Settings';
            exportSettingsBtn.style.cssText = `
                padding: 8px 16px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            exportSettingsBtn.onclick = () => {
                const settingsJson = JSON.stringify(config, null, 2);
                const blob = new Blob([settingsJson], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'url_reporter_settings.json';
                a.click();
                URL.revokeObjectURL(url);
            };
            
            const importSettingsBtn = document.createElement('button');
            importSettingsBtn.textContent = '📥 Import Settings';
            importSettingsBtn.style.cssText = `
                padding: 8px 16px;
                background: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            
            const importFileInput = document.createElement('input');
            importFileInput.type = 'file';
            importFileInput.accept = '.json';
            importFileInput.style.display = 'none';
            importFileInput.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = async (evt) => {
                    try {
                        const importedConfig = JSON.parse(evt.target.result);
                        
                        // Validate required fields
                        if (!importedConfig.categories || !Array.isArray(importedConfig.categories)) {
                            alert('Invalid settings file: missing categories');
                            return;
                        }
                        
                        // Ensure all categories have required fields
                        for (const cat of importedConfig.categories) {
                            if (!cat.key || !cat.label) {
                                alert('Invalid settings file: categories missing key or label');
                                return;
                            }
                            if (!cat.hasOwnProperty('keybinding')) {
                                cat.keybinding = '';
                            }
                        }
                        
                        // Apply imported config
                        config = importedConfig;
                        await saveConfig(config);
                        
                        // Update data lists to match new categories
                        const newLists = makeEmptyLists();
                        // Preserve existing data where keys match
                        for (const key in data.lists) {
                            if (newLists.hasOwnProperty(key)) {
                                newLists[key] = data.lists[key];
                            }
                        }
                        data.lists = newLists;
                        await saveDataToGM(data);
                        
                        // Refresh UI
                        refreshSettingsUI();
                        rebuildCategoryButtons();
                        refreshListDisplay();
                        
                        alert('Settings imported successfully!');
                    } catch (err) {
                        console.error('Import error:', err);
                        alert('Failed to import settings: ' + err.message);
                    }
                };
                reader.readAsText(file);
            };
            
            importSettingsBtn.onclick = () => {
                importFileInput.click();
            };
            
            ieSection.appendChild(exportSettingsBtn);
            ieSection.appendChild(importSettingsBtn);
            ieSection.appendChild(importFileInput);
            settingsPanel.appendChild(ieSection);
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

        // Keyboard shortcut: Ctrl+Shift+O to toggle panel
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyO') {
                if (panel.style.display === 'block') hidePanel();
                else showPanel();
                e.preventDefault();
            }
            
            // Ctrl+Shift+B to toggle icon visibility
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyB') {
                e.preventDefault();
                config.iconVisible = !config.iconVisible;
                container.style.display = config.iconVisible ? 'flex' : 'none';
                saveConfig(config);
                if (config.iconVisible) {
                    showToast('URL Reporter icon shown');
                }
            }
        });

        function refresh() {
            dateBadge.textContent = config.dailyReset ? data.date : 'Persistent';
            
            // Clear the list container
            listContainer.innerHTML = '';
            
            // Build list for each category
            for (const cat of config.categories) {
                const list = data.lists[cat.key] || [];
                
                // Category header
                const categoryHeader = document.createElement('div');
                categoryHeader.style.cssText = `
                    font-weight: bold;
                    font-size: 14px;
                    color: #007bff;
                    margin-top: 12px;
                    margin-bottom: 6px;
                    padding-bottom: 4px;
                    border-bottom: 2px solid #007bff;
                `;
                categoryHeader.textContent = cat.label;
                listContainer.appendChild(categoryHeader);
                
                if (list.length === 0) {
                    const emptyMsg = document.createElement('div');
                    emptyMsg.style.cssText = `
                        font-style: italic;
                        color: #999;
                        padding: 8px;
                        font-size: 12px;
                    `;
                    emptyMsg.textContent = '(no URLs)';
                    listContainer.appendChild(emptyMsg);
                } else {
                    // Create an item for each URL
                    for (let i = 0; i < list.length; i++) {
                        const url = list[i];
                        
                        const item = document.createElement('div');
                        item.style.cssText = `
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            padding: 6px 8px;
                            margin: 4px 0;
                            background: #f8f9fa;
                            border-radius: 4px;
                            border: 1px solid #dee2e6;
                        `;
                        
                        // URL text (clickable link)
                        const urlLink = document.createElement('a');
                        urlLink.href = url;
                        urlLink.target = '_blank';
                        urlLink.textContent = url;
                        urlLink.style.cssText = `
                            flex: 1;
                            font-size: 12px;
                            color: #007bff;
                            text-decoration: none;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        `;
                        urlLink.onmouseover = () => urlLink.style.textDecoration = 'underline';
                        urlLink.onmouseout = () => urlLink.style.textDecoration = 'none';
                        
                        // Copy button
                        const copyBtn = document.createElement('button');
                        copyBtn.textContent = '📋';
                        copyBtn.title = 'Copy URL';
                        copyBtn.style.cssText = `
                            padding: 4px 8px;
                            background: #17a2b8;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            cursor: pointer;
                            font-size: 12px;
                            min-width: 32px;
                        `;
                        copyBtn.onmouseover = () => copyBtn.style.background = '#138496';
                        copyBtn.onmouseout = () => copyBtn.style.background = '#17a2b8';
                        copyBtn.onclick = () => {
                            navigator.clipboard.writeText(url).then(() => {
                                copyBtn.textContent = '✓';
                                setTimeout(() => copyBtn.textContent = '📋', 1500);
                            }).catch(err => {
                                console.error('Failed to copy:', err);
                                alert('Failed to copy to clipboard');
                            });
                        };
                        
                        // Remove button
                        const removeBtn = document.createElement('button');
                        removeBtn.textContent = '🗑️';
                        removeBtn.title = 'Remove URL';
                        removeBtn.style.cssText = `
                            padding: 4px 8px;
                            background: #dc3545;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            cursor: pointer;
                            font-size: 12px;
                            min-width: 32px;
                        `;
                        removeBtn.onmouseover = () => removeBtn.style.background = '#c82333';
                        removeBtn.onmouseout = () => removeBtn.style.background = '#dc3545';
                        removeBtn.onclick = async () => {
                            // Remove from the list
                            data.lists[cat.key].splice(i, 1);
                            await saveDataToGM(data);
                            refreshListDisplay();
                        };
                        
                        item.appendChild(urlLink);
                        item.appendChild(copyBtn);
                        item.appendChild(removeBtn);
                        listContainer.appendChild(item);
                    }
                }
            }
        }

        refreshListDisplay = refresh;
        refresh();
        
        // Register global keybindings
        registerKeybindings();
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
