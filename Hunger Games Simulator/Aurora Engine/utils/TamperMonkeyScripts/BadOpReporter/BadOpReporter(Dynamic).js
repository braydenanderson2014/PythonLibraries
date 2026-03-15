// ==UserScript==
// @name         Dynamic URL Reporter (configurable, persistent)
// @namespace    http://tampermonkey.net/
// @version      2.8
// @description  Dynamic URL categorization with configurable categories, optional daily reset, and persistent settings across tabs. Mobile/touch support, multi-format import/export, and customizable colors!
// @author       OtterLogic LLC
// @match        https://*/*
// @match        http://*/*
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
            { key: 'badFSWOps', label: 'Bad FSW Operators', keybinding: 'Ctrl+Shift+1', color: '#007bff' },
            { key: 'badAudioOps', label: 'Bad Audio Prompt Ops', keybinding: 'Ctrl+Shift+2', color: '#28a745' },
            { key: 'badAudioEval', label: 'Bad Audio Eval Ops', keybinding: 'Ctrl+Shift+3', color: '#dc3545' },
        ],
        timezone: 'America/Denver',
        dailyReset: true, // Set to false to keep data indefinitely
        siteWhitelist: [], // Only run on these sites (empty = run everywhere)
        siteBlacklist: [], // Never run on these sites (takes priority)
        useTopFrameOnly: true, // Only run in top-level frame, not iframes
        exportFormat: 'txt', // 'txt', 'md', 'html', or 'json'
        iconPosition: { x: null, y: null }, // null = use default position
        iconVisible: true,
        iconColor: '#007bff', // Main icon background color
        iconSize: 'medium', // 'small', 'medium', 'large'
        toggleIconKeybinding: 'Ctrl+Shift+B', // Keybinding to hide/show icon
        addCategoryKeybinding: '', // Keybinding to open add category dialog
        addCustomLinkKeybinding: '', // Keybinding to open add custom link dialog
        customLinkButton: {
            color: '#17a2b8',
            textColor: '#ffffff'
        },
        mainPanelPosition: { x: null, y: null }, // null = use default centered position
        settingsPanelPosition: { x: null, y: null }, // null = use default centered position
        helpPanelPosition: { x: null, y: null }, // null = use default centered position
        popoutButtons: {
            enabled: false, // Enable/disable pop-out category buttons
            categories: {}, // Which categories have pop-out buttons enabled: { catKey: { enabled: boolean, position: {x, y}, color: string } }
            buttonSize: 'medium', // 'small', 'medium', 'large'
            showLabels: true, // Show category labels on buttons
        },
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
                if (!cat.hasOwnProperty('color')) {
                    cat.color = '#007bff'; // Default blue
                }
                if (!cat.hasOwnProperty('textColor')) {
                    cat.textColor = '#ffffff'; // Default white
                }
            }
            // Ensure required fields
            if (!parsed.timezone) parsed.timezone = DEFAULT_CONFIG.timezone;
            if (typeof parsed.dailyReset !== 'boolean') parsed.dailyReset = DEFAULT_CONFIG.dailyReset;
            if (!Array.isArray(parsed.siteWhitelist)) parsed.siteWhitelist = DEFAULT_CONFIG.siteWhitelist;
            if (!Array.isArray(parsed.siteBlacklist)) parsed.siteBlacklist = DEFAULT_CONFIG.siteBlacklist;
            if (typeof parsed.useTopFrameOnly !== 'boolean') parsed.useTopFrameOnly = DEFAULT_CONFIG.useTopFrameOnly;
            if (!parsed.exportFormat || !['txt', 'md', 'html', 'json'].includes(parsed.exportFormat)) parsed.exportFormat = DEFAULT_CONFIG.exportFormat;
            if (!parsed.iconPosition) parsed.iconPosition = DEFAULT_CONFIG.iconPosition;
            if (typeof parsed.iconVisible !== 'boolean') parsed.iconVisible = DEFAULT_CONFIG.iconVisible;
            if (!parsed.iconColor) parsed.iconColor = DEFAULT_CONFIG.iconColor;
            if (!parsed.iconSize || !['small', 'medium', 'large'].includes(parsed.iconSize)) parsed.iconSize = DEFAULT_CONFIG.iconSize;
            if (!parsed.toggleIconKeybinding) parsed.toggleIconKeybinding = DEFAULT_CONFIG.toggleIconKeybinding;
            if (!parsed.addCategoryKeybinding) parsed.addCategoryKeybinding = DEFAULT_CONFIG.addCategoryKeybinding;
            if (!parsed.addCustomLinkKeybinding) parsed.addCustomLinkKeybinding = DEFAULT_CONFIG.addCustomLinkKeybinding;
            if (!parsed.mainPanelPosition) parsed.mainPanelPosition = DEFAULT_CONFIG.mainPanelPosition;
            if (!parsed.settingsPanelPosition) parsed.settingsPanelPosition = DEFAULT_CONFIG.settingsPanelPosition;
            if (!parsed.helpPanelPosition) parsed.helpPanelPosition = DEFAULT_CONFIG.helpPanelPosition;

            // Ensure pop-out buttons config exists
            if (!parsed.popoutButtons) {
                parsed.popoutButtons = JSON.parse(JSON.stringify(DEFAULT_CONFIG.popoutButtons));
            } else {
                if (typeof parsed.popoutButtons.enabled !== 'boolean') parsed.popoutButtons.enabled = DEFAULT_CONFIG.popoutButtons.enabled;
                if (!parsed.popoutButtons.categories) parsed.popoutButtons.categories = {};
                if (!parsed.popoutButtons.buttonSize) parsed.popoutButtons.buttonSize = DEFAULT_CONFIG.popoutButtons.buttonSize;
                if (typeof parsed.popoutButtons.showLabels !== 'boolean') parsed.popoutButtons.showLabels = DEFAULT_CONFIG.popoutButtons.showLabels;
            }

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

    // Mobile detection helper
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
            || (window.matchMedia && window.matchMedia("(max-width: 768px)").matches)
            || ('ontouchstart' in window);
    }

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

        // Check if URL already exists (handle both old string format and new object format)
        const urlExists = list.some(item => {
            if (typeof item === 'string') {
                return item === url;
            } else {
                return item.url === url;
            }
        });

        if (!urlExists) {
            // Add as object with URL and display name (initially same as URL)
            list.push({ url: url, displayName: url });
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
                for (const urlItem of list) {
                    // Handle both old string format and new object format
                    if (typeof urlItem === 'string') {
                        lines.push(urlItem);
                    } else {
                        const displayName = urlItem.displayName || urlItem.url;
                        if (displayName === urlItem.url) {
                            lines.push(urlItem.url);
                        } else {
                            lines.push(`${displayName}: ${urlItem.url}`);
                        }
                    }
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
        const newCategories = []; // Track new categories found in import

        const lines = text.split(/\r?\n/);
        let currentCatKey = null;
        let currentCatLabel = null;

        // Map labels (in file) back to category keys
        const labelToKey = {};
        for (const cat of config.categories) {
            labelToKey[cat.label.toLowerCase()] = cat.key;
        }

        for (let rawLine of lines) {
            const line = rawLine.trim();
            if (!line || line === '(none)') continue; // skip blanks and empty markers

            // Heading line: == Some Label ==
            const m = line.match(/^==\s*(.+?)\s*==$/);
            if (m) {
                const label = m[1];
                const labelLower = label.toLowerCase();
                currentCatKey = labelToKey[labelLower];
                currentCatLabel = label;
                
                // If category doesn't exist, create it
                if (!currentCatKey) {
                    // Generate a unique key from the label
                    const baseKey = label.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
                    let key = baseKey;
                    let suffix = 1;
                    
                    // Ensure unique key
                    while (config.categories.some(c => c.key === key)) {
                        key = baseKey + suffix;
                        suffix++;
                    }
                    
                    currentCatKey = key;
                    labelToKey[labelLower] = key;
                    newCategories.push({ key: key, label: label, keybinding: '' });
                }
                
                continue;
            }

            // Non-heading: treat as URL if we have a current category
            if (currentCatKey) {
                const list = newData.lists[currentCatKey] || (newData.lists[currentCatKey] = []);

                // Parse line for display name format: "DisplayName: URL"
                let url = line;
                let displayName = line;
                const colonIndex = line.indexOf(': ');
                if (colonIndex > 0 && colonIndex < line.length - 2) {
                    displayName = line.substring(0, colonIndex);
                    url = line.substring(colonIndex + 2);
                }

                // Check if this URL already exists (as string or object)
                const urlExists = list.some(item => {
                    if (typeof item === 'string') {
                        return item === url;
                    } else {
                        return item.url === url;
                    }
                });

                if (!urlExists) {
                    // Import as new object format
                    list.push({ url: url, displayName: displayName });
                }
            }
        }

        return { data: newData, newCategories: newCategories };
    }

    function importFromJson(text) {
        try {
            const imported = JSON.parse(text);
            const today = todayString();
            const newData = { date: today, lists: {} };
            const newCategories = [];

            // Map existing category keys
            const existingKeys = new Set(config.categories.map(c => c.key));

            // Process each category in the JSON
            for (const [key, urls] of Object.entries(imported.lists || {})) {
                // Find the category by key or create new one
                let category = config.categories.find(c => c.key === key);
                
                if (!category) {
                    // Category doesn't exist, create it
                    // Try to find label from imported config if available
                    let label = imported.categories?.find(c => c.key === key)?.label || key;
                    newCategories.push({ key: key, label: label, keybinding: '' });
                }

                // Convert URLs to object format if needed
                newData.lists[key] = urls.map(item => {
                    if (typeof item === 'string') {
                        return { url: item, displayName: item };
                    }
                    return item;
                });
            }

            return { data: newData, newCategories: newCategories };
        } catch (e) {
            console.error('[URL Reporter] Failed to parse JSON:', e);
            return { data: { date: todayString(), lists: makeEmptyLists() }, newCategories: [] };
        }
    }

    function importFromMarkdown(text) {
        // Markdown format uses ## for headers and ```text``` blocks for URLs
        const today = todayString();
        const newData = { date: today, lists: makeEmptyLists() };
        const newCategories = [];

        const lines = text.split(/\r?\n/);
        let currentCatKey = null;
        let inCodeBlock = false;
        let lastDisplayName = null; // Track display name before code block

        // Map labels back to keys
        const labelToKey = {};
        for (const cat of config.categories) {
            labelToKey[cat.label.toLowerCase()] = cat.key;
        }

        for (let rawLine of lines) {
            const line = rawLine.trim();
            
            // Toggle code block state
            if (line.startsWith('```')) {
                inCodeBlock = !inCodeBlock;
                continue;
            }

            // Skip if in summary section or empty
            if (!line || line.startsWith('*') || line.startsWith('>') || line === '---' || line.startsWith('**Total')) continue;

            // Category header: ## 🔗 Label or ## Label
            if (line.startsWith('## ')) {
                const label = line.replace(/^##\s*🔗?\s*/, '').trim();
                const labelLower = label.toLowerCase();
                currentCatKey = labelToKey[labelLower];
                lastDisplayName = null; // Reset display name on new category
                
                // Create new category if doesn't exist
                if (!currentCatKey) {
                    const baseKey = label.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
                    let key = baseKey;
                    let suffix = 1;
                    
                    while (config.categories.some(c => c.key === key)) {
                        key = baseKey + suffix;
                        suffix++;
                    }
                    
                    currentCatKey = key;
                    labelToKey[labelLower] = key;
                    newCategories.push({ key: key, label: label, keybinding: '' });
                }
                continue;
            }

            // Check for display name line (e.g., "1. **Display Name**" or "1.")
            if (currentCatKey && !inCodeBlock && /^\d+\.\s*\*\*(.+?)\*\*/.test(line)) {
                // Extract display name from bold text
                const match = line.match(/^\d+\.\s*\*\*(.+?)\*\*/);
                if (match) {
                    lastDisplayName = match[1];
                }
                continue;
            } else if (currentCatKey && !inCodeBlock && /^\d+\.\s*$/.test(line)) {
                // Just a numbered item without display name
                lastDisplayName = null;
                continue;
            }

            // URL in code block
            if (currentCatKey && inCodeBlock && line) {
                const list = newData.lists[currentCatKey] || (newData.lists[currentCatKey] = []);
                
                const urlExists = list.some(item => item.url === line);
                if (!urlExists) {
                    const displayName = lastDisplayName || line;
                    list.push({ url: line, displayName: displayName });
                }
                lastDisplayName = null; // Reset after using it
            }
        }

        return { data: newData, newCategories: newCategories };
    }

    function importFromHtml(text) {
        // Parse HTML to extract URLs from links
        const today = todayString();
        const newData = { date: today, lists: makeEmptyLists() };
        const newCategories = [];

        const labelToKey = {};
        for (const cat of config.categories) {
            labelToKey[cat.label.toLowerCase()] = cat.key;
        }

        // Extract category headers and URLs using regex
        const h2Regex = /<h2>([^<]+)<\/h2>/gi;
        const aRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([^<]+)<\/a>/gi;
        
        let currentCatKey = null;
        let lastH2Index = 0;

        // Find all h2 tags
        let h2Match;
        const headers = [];
        while ((h2Match = h2Regex.exec(text)) !== null) {
            headers.push({ label: h2Match[1].trim(), index: h2Match.index });
        }

        // Process each header section
        for (let i = 0; i < headers.length; i++) {
            const header = headers[i];
            const label = header.label;
            const labelLower = label.toLowerCase();
            const startIndex = header.index;
            const endIndex = i + 1 < headers.length ? headers[i + 1].index : text.length;
            const section = text.substring(startIndex, endIndex);

            currentCatKey = labelToKey[labelLower];
            
            // Create new category if doesn't exist
            if (!currentCatKey) {
                const baseKey = label.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
                let key = baseKey;
                let suffix = 1;
                
                while (config.categories.some(c => c.key === key)) {
                    key = baseKey + suffix;
                    suffix++;
                }
                
                currentCatKey = key;
                labelToKey[labelLower] = key;
                newCategories.push({ key: key, label: label, keybinding: '' });
            }

            const list = newData.lists[currentCatKey] || (newData.lists[currentCatKey] = []);

            // Extract all links in this section
            let aMatch;
            const linkRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([^<]+)<\/a>/gi;
            while ((aMatch = linkRegex.exec(section)) !== null) {
                const url = aMatch[1]
                    .replace(/&amp;/g, '&')
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>')
                    .replace(/&quot;/g, '"')
                    .replace(/&#039;/g, "'");
                const displayName = aMatch[2]
                    .replace(/&amp;/g, '&')
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>')
                    .replace(/&quot;/g, '"')
                    .replace(/&#039;/g, "'");

                const urlExists = list.some(item => item.url === url);
                if (!urlExists) {
                    list.push({ url: url, displayName: displayName });
                }
            }
        }

        return { data: newData, newCategories: newCategories };
    }

    function buildJsonExport() {
        // Export complete data structure with categories for easier re-import
        const exportData = {
            version: '1.0',
            date: data.date,
            categories: config.categories.map(cat => ({
                key: cat.key,
                label: cat.label,
                keybinding: cat.keybinding || ''
            })),
            lists: data.lists
        };
        return JSON.stringify(exportData, null, 2);
    }

    function buildMarkdownExport() {
        const lines = [];
        const date = data.date || todayString();

        // Title with decorative border
        lines.push(`# 📋 URL Report - ${date}`);
        lines.push('=' .repeat(50));
        lines.push('');
        lines.push('> *Generated by Dynamic URL Reporter*');
        lines.push('');

        // Count total URLs for summary
        let totalUrls = 0;
        for (const cat of config.categories) {
            const list = data.lists[cat.key] || [];
            totalUrls += list.length;
        }

        lines.push('## 📊 Summary');
        lines.push('');
        lines.push(`**Total Categories:** ${config.categories.length}`);
        lines.push(`**Total URLs:** ${totalUrls}`);
        lines.push(`**Report Date:** ${date}`);
        lines.push('');
        lines.push('---');
        lines.push('');

        for (const cat of config.categories) {
            const list = data.lists[cat.key] || [];

            // Category heading with emoji and underline
            lines.push(`## 🔗 ${cat.label}`);
            lines.push('-'.repeat(cat.label.length + 4)); // Underline
            lines.push('');

            if (list.length === 0) {
                lines.push('> *No URLs in this category*');
                lines.push('');
            } else {
                lines.push(`**Count:** ${list.length} URL${list.length > 1 ? 's' : ''}`);
                lines.push('');

                // URLs in code blocks for easy copying from MD parsers
                for (let i = 0; i < list.length; i++) {
                    const urlItem = list[i];
                    const index = i + 1;

                    // Handle both old string format and new object format
                    if (typeof urlItem === 'string') {
                        lines.push(`${index}.`);
                        lines.push('```text');
                        lines.push(urlItem);
                        lines.push('```');
                        lines.push('');
                    } else {
                        const displayName = urlItem.displayName || urlItem.url;
                        if (displayName === urlItem.url) {
                            lines.push(`${index}.`);
                            lines.push('```text');
                            lines.push(urlItem.url);
                            lines.push('```');
                            lines.push('');
                        } else {
                            // Put display name as bold text and URL in code block for easy copying
                            lines.push(`${index}. **${displayName}**`);
                            lines.push('```text');
                            lines.push(urlItem.url);
                            lines.push('```');
                            lines.push('');
                        }
                    }
                }
                lines.push('');
            }

            // Add separator between categories
            if (config.categories.indexOf(cat) < config.categories.length - 1) {
                lines.push('---');
                lines.push('');
            }
        }

        // Footer
        lines.push('---');
        lines.push('');
        const generatedDate = new Date().toLocaleString('en-US', { 
            timeZone: config.timezone,
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        });
        lines.push('*📅 Report generated on ' + generatedDate + '*');
        lines.push('');
        lines.push('> 💡 **Tip:** Use `Ctrl+F` to quickly find specific URLs in this report');

        return lines.join('\n');
    }

    function buildHtmlExport() {
        const date = data.date || todayString();
        const lines = [];

        lines.push('<!DOCTYPE html>');
        lines.push('<html lang="en">');
        lines.push('<head>');
        lines.push('    <meta charset="UTF-8">');
        lines.push('    <meta name="viewport" content="width=device-width, initial-scale=1.0">');
        lines.push(`    <title>URL Report - ${date}</title>`);
        lines.push('    <style>');
        lines.push('        body {');
        lines.push('            font-family: Arial, sans-serif;');
        lines.push('            background: #f0f0f0;');
        lines.push('            padding: 20px;');
        lines.push('            margin: 0;');
        lines.push('        }');
        lines.push('        .container {');
        lines.push('            max-width: 900px;');
        lines.push('            margin: 0 auto;');
        lines.push('            background: white;');
        lines.push('            padding: 20px;');
        lines.push('            border-radius: 8px;');
        lines.push('            box-shadow: 0 2px 8px rgba(0,0,0,0.1);');
        lines.push('        }');
        lines.push('        h1 {');
        lines.push('            color: #333;');
        lines.push('            border-bottom: 3px solid #007bff;');
        lines.push('            padding-bottom: 10px;');
        lines.push('            margin-top: 0;');
        lines.push('        }');
        lines.push('        h2 {');
        lines.push('            color: #007bff;');
        lines.push('            margin-top: 30px;');
        lines.push('            margin-bottom: 10px;');
        lines.push('            padding-bottom: 5px;');
        lines.push('            border-bottom: 2px solid #007bff;');
        lines.push('        }');
        lines.push('        .url-list {');
        lines.push('            background: #f8f9fa;');
        lines.push('            padding: 15px;');
        lines.push('            border-radius: 4px;');
        lines.push('            margin-bottom: 20px;');
        lines.push('        }');
        lines.push('        .url-item {');
        lines.push('            display: flex;');
        lines.push('            align-items: center;');
        lines.push('            padding: 8px;');
        lines.push('            margin: 4px 0;');
        lines.push('            background: white;');
        lines.push('            border: 1px solid #ddd;');
        lines.push('            border-radius: 4px;');
        lines.push('        }');
        lines.push('        .url-item a {');
        lines.push('            color: #0066cc;');
        lines.push('            text-decoration: none;');
        lines.push('            word-break: break-all;');
        lines.push('            flex: 1;');
        lines.push('        }');
        lines.push('        .url-item a:hover {');
        lines.push('            text-decoration: underline;');
        lines.push('        }');
        lines.push('        .empty-category {');
        lines.push('            font-style: italic;');
        lines.push('            color: #999;');
        lines.push('            padding: 10px;');
        lines.push('        }');
        lines.push('        .date-badge {');
        lines.push('            display: inline-block;');
        lines.push('            background: #28a745;');
        lines.push('            color: white;');
        lines.push('            padding: 5px 12px;');
        lines.push('            border-radius: 4px;');
        lines.push('            font-size: 14px;');
        lines.push('            margin-left: 15px;');
        lines.push('        }');
        lines.push('    </style>');
        lines.push('</head>');
        lines.push('<body>');
        lines.push('    <div class="container">');
        lines.push(`        <h1>URL Report <span class="date-badge">${date}</span></h1>`);

        for (const cat of config.categories) {
            const list = data.lists[cat.key] || [];

            lines.push(`        <h2>${cat.label}</h2>`);
            lines.push('        <div class="url-list">');

            if (list.length === 0) {
                lines.push('            <div class="empty-category">(no URLs)</div>');
            } else {
                for (const urlItem of list) {
                    // Handle both old string format and new object format
                    let url, displayName;
                    if (typeof urlItem === 'string') {
                        url = urlItem;
                        displayName = urlItem;
                    } else {
                        url = urlItem.url;
                        displayName = urlItem.displayName || urlItem.url;
                    }

                    const escapedUrl = url
                        .replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/"/g, '&quot;')
                        .replace(/'/g, '&#039;');

                    const escapedDisplayName = displayName
                        .replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/"/g, '&quot;')
                        .replace(/'/g, '&#039;');

                    lines.push(`            <div class="url-item">`);
                    lines.push(`                <a href="${escapedUrl}" target="_blank">${escapedDisplayName}</a>`);
                    lines.push('            </div>');
                }
            }

            lines.push('        </div>');
        }

        // Footer with generation timestamp
        const generatedDate = new Date().toLocaleString('en-US', { 
            timeZone: config.timezone,
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        });
        lines.push('        <div class="footer">');
        lines.push(`            <p>📅 Report generated on ${generatedDate}</p>`);
        lines.push('        </div>');

        lines.push('    </div>');
        lines.push('</body>');
        lines.push('</html>');

        return lines.join('\n');
    }

    function downloadReport() {
        let text, extension, mimeType;

        if (config.exportFormat === 'md') {
            text = buildMarkdownExport();
            extension = 'md';
            mimeType = 'text/markdown';
        } else if (config.exportFormat === 'html') {
            text = buildHtmlExport();
            extension = 'html';
            mimeType = 'text/html';
        } else if (config.exportFormat === 'json') {
            text = buildJsonExport();
            extension = 'json';
            mimeType = 'application/json';
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

            // Check Add Category keybinding
            if (config.addCategoryKeybinding && matchesKeybinding(e, config.addCategoryKeybinding)) {
                console.log('[URL Reporter] Add Category keybinding matched!', debugInfo);
                e.preventDefault();
                
                const categoryName = prompt('Enter new category name:');
                if (!categoryName || !categoryName.trim()) return;
                
                const categoryKey = 'cat_' + Date.now();
                const randomColor = '#' + Math.floor(Math.random()*16777215).toString(16);
                
                config.categories.push({
                    key: categoryKey,
                    label: categoryName.trim(),
                    keybinding: '',
                    color: randomColor
                });
                
                await saveConfig();
                rebuildCategoryButtons();
                refreshListDisplay();
                showToast(`Category "${categoryName}" created!`, 'success');
                return;
            }

            // Check Add Custom Link keybinding
            if (config.addCustomLinkKeybinding && matchesKeybinding(e, config.addCustomLinkKeybinding)) {
                console.log('[URL Reporter] Add Custom Link keybinding matched!', debugInfo);
                e.preventDefault();
                
                const url = prompt('Enter the URL:');
                if (!url) return;
                
                const displayName = prompt('Enter display name (optional):');
                
                let categoryPrompt = 'Select category by number:\\n';
                config.categories.forEach((cat, idx) => {
                    categoryPrompt += `${idx + 1}. ${cat.label}\\n`;
                });
                const categoryNum = prompt(categoryPrompt);
                if (!categoryNum) return;
                
                const catIndex = parseInt(categoryNum) - 1;
                if (catIndex < 0 || catIndex >= config.categories.length) {
                    showToast('Invalid category number', 'error');
                    return;
                }
                
                const categoryKey = config.categories[catIndex].key;
                const urlObj = displayName ? { url, displayName } : url;
                
                data.lists[categoryKey] = data.lists[categoryKey] || [];
                data.lists[categoryKey].push(urlObj);
                await saveData();
                refreshListDisplay();
                showToast(`Added to ${config.categories[catIndex].label}`, 'success');
                return;
            }

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

    function showToast(message, type = 'success') {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107'
        };
        const bgColor = colors[type] || colors.success;
        
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: ${type === 'warning' ? '#000' : 'white'};
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
    let refreshUIColors = function () {}; // Function to refresh colors without reload

    function createUI() {
        console.log('[URL Reporter] createUI called');

        // Detect mobile device once at the top
        const isMobile = isMobileDevice();

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

        // Make container draggable (both mouse and touch)
        let isDragging = false;
        let dragOffset = { x: 0, y: 0 };
        let dragStartPos = { x: 0, y: 0 };
        let didActuallyDrag = false;
        const DRAG_THRESHOLD = 5; // pixels - movement less than this is considered a click

        // Helper to get coordinates from mouse or touch event
        const getEventCoords = (e) => {
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            return { x: e.clientX, y: e.clientY };
        };

        const startDrag = (e) => {
            // Only start drag if clicking the container itself, not children
            if (e.target === container || e.target === launcher) {
                isDragging = true;
                didActuallyDrag = false;
                const rect = container.getBoundingClientRect();
                const coords = getEventCoords(e);
                dragOffset.x = coords.x - rect.left;
                dragOffset.y = coords.y - rect.top;
                dragStartPos.x = coords.x;
                dragStartPos.y = coords.y;
                container.style.transform = 'none'; // Remove default transform when dragging
                e.preventDefault();
            }
        };

        const doDrag = (e) => {
            if (isDragging) {
                const coords = getEventCoords(e);

                // Check if we've moved beyond the threshold
                const moveDistance = Math.abs(coords.x - dragStartPos.x) + Math.abs(coords.y - dragStartPos.y);
                if (moveDistance > DRAG_THRESHOLD) {
                    didActuallyDrag = true;
                }

                const x = coords.x - dragOffset.x;
                const y = coords.y - dragOffset.y;
                container.style.left = `${x}px`;
                container.style.top = `${y}px`;
                e.preventDefault();
            }
        };

        const endDrag = async (e) => {
            if (isDragging) {
                isDragging = false;
                // Save position
                const rect = container.getBoundingClientRect();
                config.iconPosition = { x: rect.left, y: rect.top };
                await saveConfig(config);

                // Set a flag that will be checked by the click handler
                if (didActuallyDrag) {
                    launcher.dataset.justDragged = 'true';
                    setTimeout(() => {
                        delete launcher.dataset.justDragged;
                    }, 100);
                }
            }
        };

        // Mouse events
        container.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', endDrag);

        // Touch events for mobile
        container.addEventListener('touchstart', startDrag, { passive: false });
        document.addEventListener('touchmove', doDrag, { passive: false });
        document.addEventListener('touchend', endDrag);
        document.addEventListener('touchcancel', endDrag);

        // Launcher button
        const launcher = document.createElement('button');
        launcher.textContent = '📋';
        launcher.title = isMobile ? 'URL Bookmarker (Drag to move)' : 'Dynamic URL Bookmarker (Drag to move, Ctrl+Shift+B to hide/show)';
        
        // Icon size mapping
        const iconSizes = {
            small: { fontSize: isMobile ? '18px' : '12px', padding: isMobile ? '6px 10px' : '2px 6px' },
            medium: { fontSize: isMobile ? '24px' : '16px', padding: isMobile ? '8px 12px' : '3px 8px' },
            large: { fontSize: isMobile ? '32px' : '22px', padding: isMobile ? '10px 14px' : '4px 10px' }
        };
        const sizeConfig = iconSizes[config.iconSize || 'medium'];
        
        launcher.style.cssText = `
            font-size: ${sizeConfig.fontSize};
            padding: ${sizeConfig.padding};
            background: ${config.iconColor || '#007bff'};
            color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
            touch-action: none;
            user-select: none;
            -webkit-user-select: none;
            -webkit-tap-highlight-color: transparent;
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
        const mainPanelPos = config.mainPanelPosition;
        const hasMainPanelCustomPos = mainPanelPos.x !== null && mainPanelPos.y !== null;

        panel.style.cssText = `
            position: fixed;
            ${hasMainPanelCustomPos ? `left: ${mainPanelPos.x}px; top: ${mainPanelPos.y}px;` : 'top: 60px; left: 50%; transform: translateX(-50%);'}
            min-width: ${isMobile ? '90vw' : '400px'};
            max-width: ${isMobile ? '95vw' : '700px'};
            max-height: ${isMobile ? '80vh' : '70vh'};
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: ${isMobile ? '12px' : '10px'};
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            z-index: 2147483647;
            display: none;
            overflow: hidden;
            cursor: move;
            touch-action: none;
            user-select: none;
            -webkit-user-select: none;
        `;
        document.body.appendChild(panel);

        // Make main panel draggable (both mouse and touch)
        let mainPanelDragging = false;
        let mainPanelDragOffset = { x: 0, y: 0 };

        // Helper to get coordinates from mouse or touch event
        const getMainPanelCoords = (e) => {
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            return { x: e.clientX, y: e.clientY };
        };

        const startMainPanelDrag = (e) => {
            // Only drag if clicking header area or panel background, not buttons/inputs
            if (e.target === panel || e.target === header || e.target === title || e.target === dateBadge) {
                mainPanelDragging = true;
                const rect = panel.getBoundingClientRect();
                const coords = getMainPanelCoords(e);
                mainPanelDragOffset.x = coords.x - rect.left;
                mainPanelDragOffset.y = coords.y - rect.top;
                panel.style.transform = 'none';
                e.preventDefault();
            }
        };

        const doMainPanelDrag = (e) => {
            if (mainPanelDragging) {
                const coords = getMainPanelCoords(e);
                const x = coords.x - mainPanelDragOffset.x;
                const y = coords.y - mainPanelDragOffset.y;

                const maxX = window.innerWidth - panel.offsetWidth;
                const maxY = window.innerHeight - panel.offsetHeight;

                panel.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
                panel.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
                e.preventDefault();
            }
        };

        const endMainPanelDrag = async () => {
            if (mainPanelDragging) {
                mainPanelDragging = false;
                const rect = panel.getBoundingClientRect();
                config.mainPanelPosition = { x: rect.left, y: rect.top };
                await saveConfig(config);
            }
        };

        // Mouse events
        panel.addEventListener('mousedown', startMainPanelDrag);
        document.addEventListener('mousemove', doMainPanelDrag);
        document.addEventListener('mouseup', endMainPanelDrag);

        // Touch events for mobile
        panel.addEventListener('touchstart', startMainPanelDrag, { passive: false });
        document.addEventListener('touchmove', doMainPanelDrag, { passive: false });
        document.addEventListener('touchend', endMainPanelDrag);
        document.addEventListener('touchcancel', endMainPanelDrag);

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        `;

        const title = document.createElement('div');
        title.textContent = 'Dynamic URL Bookmarker';
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
                const btnColor = cat.color || '#007bff';
                const btnTextColor = cat.textColor || '#ffffff';
                btn.style.cssText = `
                    font-size: ${isMobile ? '14px' : '12px'};
                    padding: ${isMobile ? '8px 12px' : '4px 8px'};
                    background: ${btnColor};
                    color: ${btnTextColor};
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    cursor: pointer;
                    touch-action: manipulation;
                    min-height: ${isMobile ? '44px' : 'auto'};
                `;
                btn.addEventListener('click', async () => {
                    await addCurrentUrlToCategory(cat.key);
                    showToast(`Added to ${cat.label}!`);
                });
                buttonsRow.appendChild(btn);
            }
            
            // Add "Add Custom Link" button at the end (styled like category buttons)
            const addCustomLinkBtn = document.createElement('button');
            addCustomLinkBtn.textContent = '➕ Add Custom Link';
            const customBtnColor = config.customLinkButton?.color || '#17a2b8';
            const customBtnTextColor = config.customLinkButton?.textColor || '#ffffff';
            addCustomLinkBtn.style.cssText = `
                font-size: ${isMobile ? '14px' : '12px'};
                padding: ${isMobile ? '8px 12px' : '4px 8px'};
                background: ${customBtnColor};
                color: ${customBtnTextColor};
                border: 1px solid #ccc;
                border-radius: 4px;
                cursor: pointer;
                touch-action: manipulation;
                min-height: ${isMobile ? '44px' : 'auto'};
            `;
            addCustomLinkBtn.onmouseover = () => {
                const rgb = customBtnColor.match(/\w\w/g)?.map(x => parseInt(x, 16));
                if (rgb) {
                    const darkerColor = `rgb(${Math.max(0, rgb[0]-20)}, ${Math.max(0, rgb[1]-20)}, ${Math.max(0, rgb[2]-20)})`;
                    addCustomLinkBtn.style.background = darkerColor;
                }
            };
            addCustomLinkBtn.onmouseout = () => addCustomLinkBtn.style.background = customBtnColor;
            // Intercept to show custom link dialog instead of adding current URL
            addCustomLinkBtn.onclick = async () => {
                const url = prompt('Enter the URL:');
                if (!url) return;
                
                const displayName = prompt('Enter display name (optional):');
                
                // Build category selection prompt
                let categoryPrompt = 'Select category by number:\n';
                config.categories.forEach((cat, idx) => {
                    categoryPrompt += `${idx + 1}. ${cat.label}\n`;
                });
                const categoryNum = prompt(categoryPrompt);
                if (!categoryNum) return;
                
                const catIndex = parseInt(categoryNum) - 1;
                if (catIndex < 0 || catIndex >= config.categories.length) {
                    showToast('Invalid category number', 'error');
                    return;
                }
                
                const categoryKey = config.categories[catIndex].key;
                const urlObj = displayName ? { url, displayName } : url;
                
                data.lists[categoryKey] = data.lists[categoryKey] || [];
                data.lists[categoryKey].push(urlObj);
                await saveData();
                refreshListDisplay();
                showToast(`Added to ${config.categories[catIndex].label}`, 'success');
            };
            buttonsRow.appendChild(addCustomLinkBtn);
        };

        rebuildCategoryButtons(); // Initial build

        // Function to refresh UI colors without reloading the page
        refreshUIColors = () => {
            // Update launcher icon color
            launcher.style.background = config.iconColor || '#007bff';
            
            // Rebuild category buttons with new colors
            rebuildCategoryButtons();
            
            // Rebuild popout buttons with new colors
            createPopoutButtons();
            
            console.log('[URL Reporter] UI colors refreshed');
        };

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

        // Help button
        const helpBtn = document.createElement('button');
        helpBtn.textContent = '❓ Help';
        helpBtn.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            background: #17a2b8;
            color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        `;
        helpBtn.onclick = () => showHelpPanel();

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
        importInput.accept = '.txt,.log,.text,.md,.html,.json';
        importInput.style.display = 'none';

        importInput.addEventListener('change', async () => {
            const file = importInput.files && importInput.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (ev) => {
                try {
                    const text = String(ev.target.result || '');
                    const fileName = file.name.toLowerCase();
                    let importResult;

                    // Detect format and import accordingly
                    if (fileName.endsWith('.json')) {
                        importResult = importFromJson(text);
                    } else if (fileName.endsWith('.md')) {
                        importResult = importFromMarkdown(text);
                    } else if (fileName.endsWith('.html') || fileName.endsWith('.htm')) {
                        importResult = importFromHtml(text);
                    } else {
                        importResult = importFromText(text);
                    }

                    const imported = importResult.data;
                    const newCategories = importResult.newCategories;

                    // Add new categories to config
                    if (newCategories.length > 0) {
                        for (const newCat of newCategories) {
                            config.categories.push(newCat);
                        }
                        await saveConfig(config);
                        rebuildCategoryButtons();
                        showToast(`Added ${newCategories.length} new categor${newCategories.length === 1 ? 'y' : 'ies'}!`);
                    }

                    const today = todayString();
                    if (config.dailyReset && data.date !== today) {
                        data = { date: today, lists: makeEmptyLists() };
                    }

                    // Merge imported data with existing data
                    let urlsAdded = 0;
                    for (const key of Object.keys(imported.lists)) {
                        const existing = data.lists[key] || [];
                        const incoming = imported.lists[key] || [];
                        
                        for (const incomingItem of incoming) {
                            // Check if URL already exists
                            const urlExists = existing.some(existingItem => {
                                const existingUrl = typeof existingItem === 'string' ? existingItem : existingItem.url;
                                const incomingUrl = typeof incomingItem === 'string' ? incomingItem : incomingItem.url;
                                return existingUrl === incomingUrl;
                            });
                            
                            if (!urlExists) {
                                existing.push(incomingItem);
                                urlsAdded++;
                            }
                        }
                        data.lists[key] = existing;
                    }

                    await saveDataToGM(data);
                    refreshListDisplay();
                    
                    let message = `Import completed! Added ${urlsAdded} URL${urlsAdded === 1 ? '' : 's'}`;
                    if (newCategories.length > 0) {
                        message += ` and ${newCategories.length} categor${newCategories.length === 1 ? 'y' : 'ies'}`;
                    }
                    showToast(message);
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

        leftActions.appendChild(helpBtn);
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
            let text;
            if (config.exportFormat === 'md') {
                text = buildMarkdownExport();
            } else if (config.exportFormat === 'html') {
                text = buildHtmlExport();
            } else {
                text = buildExportText();
            }
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

        // Help Panel
        function showHelpPanel() {
            hidePanel();
            helpPanel.style.display = 'block';
            overlay.style.display = 'block';
        }

        const helpPanel = document.createElement('div');
        const helpPanelPos = config.helpPanelPosition;
        const hasHelpPanelCustomPos = helpPanelPos.x !== null && helpPanelPos.y !== null;

        helpPanel.style.cssText = `
            position: fixed;
            ${hasHelpPanelCustomPos ? `left: ${helpPanelPos.x}px; top: ${helpPanelPos.y}px;` : 'top: 60px; left: 50%; transform: translateX(-50%);'}
            width: 600px;
            max-height: 75vh;
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 15px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            z-index: 2147483647;
            display: none;
            overflow-y: auto;
            cursor: move;
        `;
        document.body.appendChild(helpPanel);

        // Build help content
        const helpHeader = document.createElement('div');
        helpHeader.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        `;

        const helpTitle = document.createElement('div');
        helpTitle.textContent = '❓ Help - Dynamic URL Bookmarker';
        helpTitle.style.cssText = `font-weight: bold; font-size: 16px;`;

        const helpCloseBtn = document.createElement('button');
        helpCloseBtn.textContent = '✕';
        helpCloseBtn.style.cssText = `
            font-size: 12px;
            padding: 2px 6px;
            background: #eee;
            border: 1px solid #aaa;
            border-radius: 4px;
            cursor: pointer;
        `;
        helpCloseBtn.onclick = () => {
            helpPanel.style.display = 'none';
            overlay.style.display = 'none';
        };

        helpHeader.appendChild(helpTitle);
        helpHeader.appendChild(helpCloseBtn);
        helpPanel.appendChild(helpHeader);

        // Help content
        const helpContent = document.createElement('div');
        helpContent.style.cssText = `
            font-size: 13px;
            line-height: 1.6;
            color: #333;
        `;

        const sections = [
            {
                title: '📋 Overview',
                content: 'Dynamic URL Bookmarker helps you track and categorize URLs across websites. Save URLs to custom categories, export reports, and use keyboard shortcuts for quick access.'
            },
            {
                title: '🎯 Quick Start',
                content: `<strong>1. Add URLs:</strong> Click the 📋 icon, then click a category button, OR use pop-out category buttons for instant access.<br>
<strong>2. View URLs:</strong> The main panel shows all saved URLs organized by category with their display names.<br>
<strong>3. Rename URLs:</strong> Click the ✏️ (rename) button next to any URL to set a custom display name (like Chrome bookmarks).<br>
<strong>4. Manage URLs:</strong> Use 📋 (copy) to copy individual URLs or 🗑️ (delete) to remove them.<br>
<strong>5. Pop-out Buttons:</strong> Enable floating category buttons in Settings for super-quick URL adding.<br>
<strong>6. Export:</strong> Click "📥 Download" to save your report as TXT, Markdown, or HTML.<br>
<strong>7. Copy All:</strong> Use "📋 Copy All" to copy the entire report to clipboard.`
            },
            {
                title: '⌨️ Keyboard Shortcuts',
                content: `<strong>Ctrl+Shift+O:</strong> Toggle main panel<br>
<strong>Ctrl+Shift+B:</strong> Hide/show icon (configurable in settings)<br>
<strong>Add Category Shortcut:</strong> Set a keybinding in Settings to quickly create new categories with a popup dialog<br>
<strong>Add Custom Link Shortcut:</strong> Set a keybinding to add URLs without visiting the site (3-step dialog: URL, category, display name)<br>
<strong>Custom Category Keybindings:</strong> Assign shortcuts to instantly add current URL to specific categories`
            },
            {
                title: '📂 Categories',
                content: `<strong>Add Category:</strong> Settings → Categories → "+ Add Category" OR use the Add Category keybinding (configurable in settings)<br>
<strong>Rename:</strong> Edit the label field and it saves automatically<br>
<strong>Delete:</strong> Click 🗑️ next to any category<br>
<strong>Copy Category:</strong> Click 📋 button next to category name in main panel to copy all URLs in that category to clipboard (respects your export format setting)<br>
<strong>Download Category:</strong> Click 📥 button next to category name to download just that category's URLs as a file (respects your export format setting)<br>
<strong>Colors:</strong> Customize background color and text color for each category independently<br>
<strong>Reset Colors:</strong> Individual reset buttons restore category colors to defaults<br>
<strong>Reset All Colors:</strong> Global reset button returns all categories to default blue (#007bff) with white text<br>
<strong>Live Color Updates:</strong> Color changes apply immediately without page refresh<br>
<strong>Color Inheritance:</strong> Category colors automatically apply to main UI buttons and pop-out buttons (unless overridden)<br>
<strong>Keybindings:</strong> Assign shortcuts (e.g., Ctrl+Shift+1) to add URLs instantly`
            },
            {
                title: '🔗 URL Management',
                content: `<strong>Display Names:</strong> Each URL can have a custom display name (like Chrome bookmarks). The actual URL remains unchanged but shows with your chosen name.<br>
<strong>✏️ Rename Button:</strong> Click to set or change the display name for any URL. Enter your desired name in the popup dialog.<br>
<strong>📋 Copy Button:</strong> Copy the actual URL (not the display name) to your clipboard for pasting elsewhere.<br>
<strong>🗑️ Delete Button:</strong> Remove the URL from the category permanently.<br>
<strong>URL Link:</strong> Click the display name to open the URL in a new tab. Hover to see the full URL.<br>
<strong>Export Behavior:</strong> TXT exports show "Display Name: URL", Markdown creates proper links [Display Name](URL), HTML creates clickable links.`
            },
            {
                title: '➕ Add Custom Link Button',
                content: `<strong>Location:</strong> Light blue "➕ Add Custom Link" button in main panel, positioned above category list<br>
<strong>Purpose:</strong> Add URLs to any category WITHOUT needing to visit the website first<br>
<strong>3-Step Process:</strong> Click the button and enter: 1) URL to add, 2) Select target category from dropdown, 3) Optional display name<br>
<strong>Keybinding:</strong> Set a keyboard shortcut in Settings → General Settings → "Add Custom Link Keybinding" to trigger the dialog instantly<br>
<strong>Pop-out Version:</strong> Enable in Settings → Pop-out Category Buttons → Custom Link Button section for a floating version you can position anywhere<br>
<strong>Customization:</strong> Settings → Pop-out Category Buttons → Custom Link Button lets you customize:<br>
  • Button text (default "➕ Add Custom Link")<br>
  • Button size: Inherit global size, or override with Small (32px), Medium (40px), Large (48px)<br>
  • Button shape: Circle, Square, Rounded, Pill, Horizontal Rectangle, Vertical Rectangle<br>
  • Button color and text color (independent from category colors)<br>
<strong>Use Cases:</strong> Perfect for batch adding URLs from documents, email lists, or planning ahead without browser navigation<br>
<strong>Smart Workflow:</strong> Combine with category keybindings for super-fast URL collection from any source`
            },
            {
                title: '⚙️ Settings',
                content: `<strong>Daily Reset:</strong> Enable to clear URLs at midnight, or disable to keep permanently<br>
<strong>Export Format:</strong> Choose TXT (plain text), MD (markdown), or HTML (styled webpage)<br>
<strong>Timezone:</strong> Set your timezone for accurate date tracking<br>
<strong>Site Filters:</strong> Control which websites run the script<br>
<strong>Keybindings:</strong> Set up keyboard shortcuts for quick URL capture`
            },
            {
                title: '🌐 Site Filtering',
                content: `<strong>Top Frame Only:</strong> Only run in main window, not iframes (prevents duplicates)<br>
<strong>Whitelist:</strong> Only run on specified URLs (leave empty for all sites)<br>
<strong>Blacklist:</strong> Never run on specified URLs (takes priority over whitelist)<br>
<strong>Format:</strong> One URL per line, e.g., https://example.com/`
            },
            {
                title: '📥 Import/Export',
                content: `<strong>Download Report:</strong> Export URLs with display names in your chosen format (TXT/MD/HTML/JSON)<br>
<strong>Import URLs:</strong> Load from TXT, Markdown (.md), HTML, or JSON files to add URLs to existing categories<br>
<strong>Auto-Category Creation:</strong> Import automatically creates missing categories found in imported files<br>
<strong>Multi-Format Support:</strong> Import from plain text, Markdown with links [Name](URL), HTML links, or JSON exports<br>
<strong>Export Settings:</strong> Save configuration as JSON file<br>
<strong>Import Settings:</strong> Load configuration from JSON file<br>
<strong>Copy All:</strong> Copy entire report to clipboard with display names in selected format<br>
<strong>Display Name Exports:</strong> TXT shows "Name: URL", Markdown creates [Name](URL), HTML creates named links, JSON preserves structure`
            },
            {
                title: '🎨 Icon Controls',
                content: `<strong>Drag to Move:</strong> Click and drag the 📋 icon anywhere on screen (works on mobile/touch devices)<br>
<strong>Icon Size:</strong> Choose Small, Medium, or Large icon size in Settings - changes apply instantly without page reload<br>
<strong>Icon Color:</strong> Customize the main launcher icon color with color picker<br>
<strong>Reset Icon Color:</strong> Reset launcher icon to default blue (#007bff)<br>
<strong>Reset Position:</strong> Settings → Icon Controls → "↺ Reset Position"<br>
<strong>Hide/Show:</strong> Use toggle keybinding (default Ctrl+Shift+B)<br>
<strong>Mobile/Touch Support:</strong> Full touch event support for dragging on mobile devices<br>
<strong>Persistent:</strong> Position, size, color, and visibility saved across sessions<br>
<strong>Size Options:</strong> Small (desktop: 16px/24px icon/panel, mobile: 20px/28px), Medium (default - 20px/28px desktop, 24px/32px mobile), Large (24px/32px desktop, 28px/36px mobile)`
            },
            {
                title: '🔘 Pop-out Category Buttons',
                content: `<strong>Enable Feature:</strong> Settings → Pop-out Category Buttons → Enable checkbox<br>
<strong>Individual Buttons:</strong> Create floating buttons for quick URL adding to specific categories<br>
<strong>Button Sizing:</strong> Choose from Small (32px), Medium (40px), or Large (48px) button sizes globally, or set per-button size to override<br>
<strong>Button Shapes:</strong> Select shape for each button: Circle, Square, Rounded, Pill, Horizontal Rectangle, or Vertical Rectangle<br>
<strong>Custom Text:</strong> Override default label with custom text per button<br>
<strong>Colors:</strong> Set custom background color and text color for each button independently<br>
<strong>Text Size:</strong> Adjust font size (8-24px) for each button separately from button size<br>
<strong>Show Labels:</strong> Display category names on buttons (when short enough)<br>
<strong>Drag to Move:</strong> Each button can be positioned anywhere on screen (touch-enabled on mobile)<br>
<strong>Click to Add:</strong> Click any pop-out button to add current URL to that category<br>
<strong>Visual Feedback:</strong> Buttons show hover effects and success animations<br>
<strong>Per-Category Control:</strong> Enable/disable pop-out buttons for individual categories<br>
<strong>Reset Colors:</strong> Reset button and text colors to category defaults with one click<br>
<strong>Position Reset:</strong> Reset any button to its default position<br>
<strong>Persistent Settings:</strong> All customizations (position, colors, text, size, shape) are saved across browser sessions<br>
<strong>➕ Add Custom Link Button:</strong> Special button that opens a 3-step dialog to add URLs without visiting the site (URL → Category → Display Name). Fully customizable with its own text, size, shape, and colors in Settings → Pop-out Category Buttons → Custom Link Button section`
            },
            {
                title: '🔧 Advanced Features',
                content: `<strong>Display Names:</strong> Set custom names for URLs (like Chrome bookmarks) while preserving original URLs<br>
<strong>Per-URL Actions:</strong> Each URL has ✏️ rename, 📋 copy, and 🗑️ remove buttons<br>
<strong>Smart Export:</strong> Display names are intelligently formatted in TXT/Markdown/HTML/JSON exports<br>
<strong>Color Customization:</strong> Full color control for categories, buttons, text, and icons with live updates<br>
<strong>Mobile/Touch Support:</strong> Full touch event handling for dragging UI elements on mobile Safari and other touch devices<br>
<strong>Drag Detection:</strong> Smart 5px movement threshold prevents accidental panel opening when dragging on mobile<br>
<strong>Shape Options:</strong> 6 button shapes (Circle, Square, Rounded, Pill, Horizontal/Vertical Rectangle) for pop-out buttons<br>
<strong>Backward Compatibility:</strong> Existing URLs and settings automatically work with new features<br>
<strong>Cross-Tab Sync:</strong> Data, colors, and display names sync automatically across all browser tabs<br>
<strong>Safe Export:</strong> HTML exports escape special characters for security<br>
<strong>Keybinding Recording:</strong> Click "⏺️ Record" to capture key combinations<br>
<strong>Live UI Refresh:</strong> All color and customization changes apply instantly without page reload<br>
<strong>Per-Button Customization:</strong> Each pop-out button can have unique text, size, color, and shape settings<br>
<strong>Auto-Save:</strong> All changes (including renames, colors, positions) save automatically - no manual save needed`
            },
            {
                title: '💡 Tips & Tricks',
                content: `• Set keybindings for categories you use most frequently<br>
• Use the "Add Category" keybinding to quickly create new categories without opening settings<br>
• Use the "Add Custom Link" button or keybinding to batch-add URLs from documents, emails, or planning sessions<br>
• Click 📋 next to category names in main panel to copy all URLs in that category (respects export format)<br>
• Click 📥 next to category names to download just that category as a file (perfect for sharing specific collections)<br>
• Use display names to create meaningful, readable URL lists<br>
• Rename URLs with descriptive names like "Bug Report #123" instead of long URLs<br>
• Adjust icon size (Small/Medium/Large) to match your visual preference - changes apply instantly<br>
• Customize category colors to visually organize your workflow (e.g., red for urgent, green for completed)<br>
• Match text colors to background colors for optimal readability<br>
• Enable pop-out buttons for your most-used categories for super quick access<br>
• Position pop-out buttons near areas where you frequently work<br>
• Use small pop-out buttons if you have many categories enabled<br>
• Customize the "Add Custom Link" popout button with unique text/size/shape/colors to match your workflow<br>
• Customize individual pop-out button colors to match your UI or site theme<br>
• Adjust text size on pop-out buttons independently from button size for perfect visibility<br>
• Use rectangle shapes for buttons with longer text labels<br>
• Use circle/pill shapes for single-letter or emoji button labels<br>
• Reset colors quickly if experimenting - individual and global reset buttons available<br>
• Import JSON format when transferring settings between browsers/devices<br>
• Use HTML export to create shareable reports with clickable, named links<br>
• Use Markdown export for chat apps and documentation that support MD formatting<br>
• Enable Daily Reset if tracking daily activities<br>
• Disable Daily Reset for long-term URL collections<br>
• Add sites to blacklist if they interfere with the script<br>
• Use whitelist mode to only run on specific work sites<br>
• All UI elements are draggable on desktop AND mobile - position them where they won't interfere<br>
• Display names make exported reports much more readable and professional<br>
• Pop-out buttons provide instant visual feedback when URLs are added<br>
• Color coding helps distinguish categories at a glance in both main panel and pop-out buttons<br>
• Combine category copy/download with custom link button for powerful URL collection workflows`
            },
            {
                title: '❗ Troubleshooting',
                content: `<strong>Icon appears twice:</strong> Enable "Top Frame Only" in site filters<br>
<strong>URLs not saving:</strong> Check browser's TamperMonkey permissions<br>
<strong>Keybinding conflicts:</strong> Change conflicting shortcuts in settings<br>
<strong>Data not syncing:</strong> Ensure TamperMonkey storage permissions are enabled<br>
<strong>Import fails:</strong> Verify file format matches export format (TXT with == headers ==)`
            }
        ];

        sections.forEach(section => {
            const sectionDiv = document.createElement('div');
            sectionDiv.style.cssText = `
                margin-bottom: 20px;
                padding: 12px;
                background: white;
                border-radius: 4px;
                border-left: 4px solid #007bff;
            `;

            const sectionTitle = document.createElement('div');
            sectionTitle.textContent = section.title;
            sectionTitle.style.cssText = `
                font-weight: bold;
                font-size: 14px;
                color: #007bff;
                margin-bottom: 8px;
            `;

            const sectionContent = document.createElement('div');
            sectionContent.innerHTML = section.content;
            sectionContent.style.cssText = `
                font-size: 12px;
                color: #555;
                line-height: 1.8;
            `;

            sectionDiv.appendChild(sectionTitle);
            sectionDiv.appendChild(sectionContent);
            helpContent.appendChild(sectionDiv);
        });

        helpPanel.appendChild(helpContent);

        // Make help panel draggable (both mouse and touch)
        let helpPanelDragging = false;
        let helpPanelDragOffset = { x: 0, y: 0 };
        let helpPanelDragStartEl = null;

        const getHelpPanelCoords = (e) => {
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            return { x: e.clientX, y: e.clientY };
        };

        const startHelpPanelDrag = (e) => {
            // Only drag if clicking the header area
            if (e.target.textContent?.includes('Help - Dynamic URL Bookmarker') || 
                e.target.parentElement?.textContent?.includes('Help - Dynamic URL Bookmarker')) {
                helpPanelDragging = true;
                helpPanelDragStartEl = e.target;
                const rect = helpPanel.getBoundingClientRect();
                const coords = getHelpPanelCoords(e);
                helpPanelDragOffset.x = coords.x - rect.left;
                helpPanelDragOffset.y = coords.y - rect.top;
                helpPanel.style.transform = 'none';
                e.preventDefault();
            }
        };

        const doHelpPanelDrag = (e) => {
            if (helpPanelDragging) {
                const coords = getHelpPanelCoords(e);
                const x = coords.x - helpPanelDragOffset.x;
                const y = coords.y - helpPanelDragOffset.y;

                const maxX = window.innerWidth - helpPanel.offsetWidth;
                const maxY = window.innerHeight - helpPanel.offsetHeight;

                helpPanel.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
                helpPanel.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
                e.preventDefault();
            }
        };

        const endHelpPanelDrag = async () => {
            if (helpPanelDragging) {
                helpPanelDragging = false;
                const rect = helpPanel.getBoundingClientRect();
                config.helpPanelPosition = { x: rect.left, y: rect.top };
                await saveConfig(config);
            }
        };

        // Mouse events
        helpPanel.addEventListener('mousedown', startHelpPanelDrag);
        document.addEventListener('mousemove', doHelpPanelDrag);
        document.addEventListener('mouseup', endHelpPanelDrag);

        // Touch events for mobile
        helpPanel.addEventListener('touchstart', startHelpPanelDrag, { passive: false });
        document.addEventListener('touchmove', doHelpPanelDrag, { passive: false });
        document.addEventListener('touchend', endHelpPanelDrag);
        document.addEventListener('touchcancel', endHelpPanelDrag);

        // Settings Panel
        function showSettingsPanel() {
            hidePanel();
            settingsPanel.style.display = 'block';
            overlay.style.display = 'block';
            refreshSettingsUI();
        }

        const settingsPanel = document.createElement('div');
        const settingsPanelPos = config.settingsPanelPosition;
        const hasSettingsPanelCustomPos = settingsPanelPos.x !== null && settingsPanelPos.y !== null;

        settingsPanel.style.cssText = `
            position: fixed;
            ${hasSettingsPanelCustomPos ? `left: ${settingsPanelPos.x}px; top: ${settingsPanelPos.y}px;` : 'top: 60px; left: 50%; transform: translateX(-50%);'}
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
            cursor: move;
        `;
        document.body.appendChild(settingsPanel);

        // Make settings panel draggable (both mouse and touch)
        let settingsPanelDragging = false;
        let settingsPanelDragOffset = { x: 0, y: 0 };
        let settingsPanelDragStartEl = null;

        // Helper to get coordinates from mouse or touch event
        const getSettingsPanelCoords = (e) => {
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            return { x: e.clientX, y: e.clientY };
        };

        const startSettingsPanelDrag = (e) => {
            // Only drag if clicking the header area
            if (e.target.textContent === '⚙️ Settings' || e.target.parentElement?.textContent?.startsWith('⚙️ Settings')) {
                settingsPanelDragging = true;
                settingsPanelDragStartEl = e.target;
                const rect = settingsPanel.getBoundingClientRect();
                const coords = getSettingsPanelCoords(e);
                settingsPanelDragOffset.x = coords.x - rect.left;
                settingsPanelDragOffset.y = coords.y - rect.top;
                settingsPanel.style.transform = 'none';
                e.preventDefault();
            }
        };

        const doSettingsPanelDrag = (e) => {
            if (settingsPanelDragging) {
                const coords = getSettingsPanelCoords(e);
                const x = coords.x - settingsPanelDragOffset.x;
                const y = coords.y - settingsPanelDragOffset.y;

                const maxX = window.innerWidth - settingsPanel.offsetWidth;
                const maxY = window.innerHeight - settingsPanel.offsetHeight;

                settingsPanel.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
                settingsPanel.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
                e.preventDefault();
            }
        };

        const endSettingsPanelDrag = async () => {
            if (settingsPanelDragging) {
                settingsPanelDragging = false;
                const rect = settingsPanel.getBoundingClientRect();
                config.settingsPanelPosition = { x: rect.left, y: rect.top };
                await saveConfig(config);
            }
        };

        // Mouse events
        settingsPanel.addEventListener('mousedown', startSettingsPanelDrag);
        document.addEventListener('mousemove', doSettingsPanelDrag);
        document.addEventListener('mouseup', endSettingsPanelDrag);

        // Touch events for mobile
        settingsPanel.addEventListener('touchstart', startSettingsPanelDrag, { passive: false });
        document.addEventListener('touchmove', doSettingsPanelDrag, { passive: false });
        document.addEventListener('touchend', endSettingsPanelDrag);
        document.addEventListener('touchcancel', endSettingsPanelDrag);

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
            settingsTitle.style.cssText = `font-weight: bold; font-size: 16px; cursor: move;`;

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

            // Make header draggable (both mouse and touch)
            settingsHeader.style.cursor = 'move';

            const headerDragStart = (e) => {
                if (e.target !== settingsCloseBtn && (!e.button || e.button === 0)) {
                    settingsPanelDragging = true;
                    const rect = settingsPanel.getBoundingClientRect();
                    const coords = getSettingsPanelCoords(e);
                    settingsPanelDragOffset.x = coords.x - rect.left;
                    settingsPanelDragOffset.y = coords.y - rect.top;
                    settingsPanel.style.transform = 'none';
                    e.preventDefault();
                }
            };

            settingsHeader.addEventListener('mousedown', headerDragStart);
            settingsHeader.addEventListener('touchstart', headerDragStart, { passive: false });

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

            // HTML option
            const htmlLabel = document.createElement('label');
            htmlLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
            `;

            const htmlRadio = document.createElement('input');
            htmlRadio.type = 'radio';
            htmlRadio.name = 'exportFormat';
            htmlRadio.value = 'html';
            htmlRadio.checked = config.exportFormat === 'html';
            htmlRadio.onchange = async () => {
                config.exportFormat = 'html';
                await saveConfig(config);
            };

            const htmlText = document.createElement('span');
            htmlText.textContent = 'HTML (.html)';
            htmlText.style.cssText = `font-size: 12px; color: #333;`;

            htmlLabel.appendChild(htmlRadio);
            htmlLabel.appendChild(htmlText);

            // JSON option
            const jsonLabel = document.createElement('label');
            jsonLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
            `;

            const jsonRadio = document.createElement('input');
            jsonRadio.type = 'radio';
            jsonRadio.name = 'exportFormat';
            jsonRadio.value = 'json';
            jsonRadio.checked = config.exportFormat === 'json';
            jsonRadio.onchange = async () => {
                config.exportFormat = 'json';
                await saveConfig(config);
            };

            const jsonText = document.createElement('span');
            jsonText.textContent = 'JSON (.json)';
            jsonText.style.cssText = `font-size: 12px; color: #333;`;

            jsonLabel.appendChild(jsonRadio);
            jsonLabel.appendChild(jsonText);

            formatOptions.appendChild(txtLabel);
            formatOptions.appendChild(mdLabel);
            formatOptions.appendChild(htmlLabel);
            formatOptions.appendChild(jsonLabel);
            exportFormatSection.appendChild(formatOptions);

            const formatHelp = document.createElement('div');
            formatHelp.textContent = 'HTML format creates a styled webpage with clickable links';
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

            const tzSelect = document.createElement('select');
            tzSelect.style.cssText = `
                width: 100%;
                padding: 6px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            `;
            
            // Common timezones grouped by region
            const timezones = [
                { group: 'US & Canada', zones: [
                    'America/New_York',
                    'America/Chicago',
                    'America/Denver',
                    'America/Phoenix',
                    'America/Los_Angeles',
                    'America/Anchorage',
                    'Pacific/Honolulu',
                    'America/Toronto',
                    'America/Vancouver'
                ]},
                { group: 'Europe', zones: [
                    'Europe/London',
                    'Europe/Paris',
                    'Europe/Berlin',
                    'Europe/Rome',
                    'Europe/Madrid',
                    'Europe/Amsterdam',
                    'Europe/Brussels',
                    'Europe/Vienna',
                    'Europe/Warsaw',
                    'Europe/Stockholm',
                    'Europe/Oslo',
                    'Europe/Copenhagen',
                    'Europe/Helsinki',
                    'Europe/Athens',
                    'Europe/Moscow',
                    'Europe/Istanbul'
                ]},
                { group: 'Asia', zones: [
                    'Asia/Dubai',
                    'Asia/Karachi',
                    'Asia/Kolkata',
                    'Asia/Bangkok',
                    'Asia/Singapore',
                    'Asia/Hong_Kong',
                    'Asia/Shanghai',
                    'Asia/Tokyo',
                    'Asia/Seoul',
                    'Asia/Manila',
                    'Asia/Jakarta',
                    'Asia/Taipei'
                ]},
                { group: 'Australia & Pacific', zones: [
                    'Australia/Sydney',
                    'Australia/Melbourne',
                    'Australia/Brisbane',
                    'Australia/Perth',
                    'Pacific/Auckland',
                    'Pacific/Fiji'
                ]},
                { group: 'South America', zones: [
                    'America/Sao_Paulo',
                    'America/Buenos_Aires',
                    'America/Santiago',
                    'America/Lima',
                    'America/Bogota',
                    'America/Caracas'
                ]},
                { group: 'Middle East & Africa', zones: [
                    'Africa/Cairo',
                    'Africa/Johannesburg',
                    'Africa/Lagos',
                    'Africa/Nairobi',
                    'Asia/Jerusalem',
                    'Asia/Riyadh'
                ]},
                { group: 'Atlantic & Other', zones: [
                    'Atlantic/Reykjavik',
                    'Atlantic/Azores',
                    'GMT',
                    'UTC'
                ]}
            ];
            
            timezones.forEach(region => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = region.group;
                region.zones.forEach(tz => {
                    const option = document.createElement('option');
                    option.value = tz;
                    option.textContent = tz.replace(/_/g, ' ');
                    if (tz === config.timezone) {
                        option.selected = true;
                    }
                    optgroup.appendChild(option);
                });
                tzSelect.appendChild(optgroup);
            });
            
            tzSelect.onchange = async () => {
                config.timezone = tzSelect.value;
                await saveConfig(config);
                refreshListDisplay();
            };

            tzSection.appendChild(tzLabel);
            tzSection.appendChild(tzSelect);
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
            catTitle.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            `;
            
            const catTitleText = document.createElement('span');
            catTitleText.textContent = 'Categories:';
            catTitleText.style.cssText = `font-weight: bold; font-size: 12px;`;
            
            const resetAllColorsBtn = document.createElement('button');
            resetAllColorsBtn.textContent = '↺ Reset All Colors';
            resetAllColorsBtn.title = 'Reset all category colors to defaults';
            resetAllColorsBtn.style.cssText = `
                padding: 4px 8px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 11px;
            `;
            resetAllColorsBtn.onclick = async () => {
                if (confirm('Reset all category colors to default blue?')) {
                    for (const cat of config.categories) {
                        cat.color = '#007bff';
                        cat.textColor = '#ffffff';
                    }
                    await saveConfig(config);
                    refreshSettingsUI();
                    refreshUIColors();
                    showToast('All category colors reset!');
                }
            };
            
            catTitle.appendChild(catTitleText);
            catTitle.appendChild(resetAllColorsBtn);
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

                const colorInput = document.createElement('input');
                colorInput.type = 'color';
                colorInput.value = cat.color || '#007bff';
                colorInput.title = 'Button Background Color';
                colorInput.style.cssText = `
                    width: 40px;
                    height: 30px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    cursor: pointer;
                `;
                // Capture cat reference to avoid closure issue
                colorInput.onchange = (function(category) {
                    return async function() {
                        category.color = colorInput.value;
                        await saveConfig(config);
                        refreshUIColors(); // Refresh UI without reload
                        showToast(`Color updated for ${category.label}!`);
                    };
                })(cat);

                const textColorInput = document.createElement('input');
                textColorInput.type = 'color';
                textColorInput.value = cat.textColor || '#ffffff';
                textColorInput.title = 'Button Text Color';
                textColorInput.style.cssText = `
                    width: 40px;
                    height: 30px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    cursor: pointer;
                `;
                // Capture cat reference to avoid closure issue
                textColorInput.onchange = (function(category) {
                    return async function() {
                        category.textColor = textColorInput.value;
                        await saveConfig(config);
                        refreshUIColors(); // Refresh UI without reload
                        showToast(`Text color updated for ${category.label}!`);
                    };
                })(cat);

                const resetColorBtn = document.createElement('button');
                resetColorBtn.textContent = '↺';
                resetColorBtn.title = 'Reset colors to default';
                resetColorBtn.style.cssText = `
                    padding: 4px 8px;
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                `;
                // Capture cat reference to avoid closure issue
                resetColorBtn.onclick = (function(category) {
                    return async function() {
                        category.color = '#007bff';
                        category.textColor = '#ffffff';
                        colorInput.value = '#007bff';
                        textColorInput.value = '#ffffff';
                        await saveConfig(config);
                        refreshUIColors();
                        showToast(`Colors reset for ${category.label}!`);
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
                catRow.appendChild(colorInput);
                catRow.appendChild(textColorInput);
                catRow.appendChild(resetColorBtn);
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
                // Generate a random color for variety
                const randomColor = '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
                config.categories.push({ key: newKey, label: newLabel, keybinding: '', color: randomColor });
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

            iconButtonsRow.appendChild(resetPosBtn);
            
            // Icon color picker
            const iconColorLabel = document.createElement('span');
            iconColorLabel.textContent = 'Icon Color:';
            iconColorLabel.style.cssText = `font-size: 12px; margin-left: 10px;`;
            
            const iconColorInput = document.createElement('input');
            iconColorInput.type = 'color';
            iconColorInput.value = config.iconColor || '#007bff';
            iconColorInput.style.cssText = `
                padding: 2px;
                border: 1px solid #ccc;
                border-radius: 3px;
                height: 32px;
                width: 50px;
                cursor: pointer;
            `;
            iconColorInput.onchange = async () => {
                config.iconColor = iconColorInput.value;
                await saveConfig(config);
                refreshUIColors(); // Refresh UI without reload
                showToast('Icon color updated!');
            };
            
            const resetIconColorBtn = document.createElement('button');
            resetIconColorBtn.textContent = '↺';
            resetIconColorBtn.title = 'Reset to default color';
            resetIconColorBtn.style.cssText = `
                padding: 4px 8px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            resetIconColorBtn.onclick = async () => {
                config.iconColor = '#007bff';
                iconColorInput.value = '#007bff';
                await saveConfig(config);
                refreshUIColors();
                showToast('Icon color reset to default!');
            };
            
            iconButtonsRow.appendChild(iconColorLabel);
            iconButtonsRow.appendChild(iconColorInput);
            iconButtonsRow.appendChild(resetIconColorBtn);
            iconControlsSection.appendChild(iconButtonsRow);

            // Icon size control
            const iconSizeRow = document.createElement('div');
            iconSizeRow.style.cssText = `
                display: flex;
                gap: 8px;
                align-items: center;
                margin-top: 10px;
            `;

            const iconSizeLabel = document.createElement('span');
            iconSizeLabel.textContent = 'Icon Size:';
            iconSizeLabel.style.cssText = `font-size: 12px;`;

            const iconSizeSelect = document.createElement('select');
            iconSizeSelect.style.cssText = `
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            `;
            
            ['small', 'medium', 'large'].forEach(size => {
                const option = document.createElement('option');
                option.value = size;
                option.textContent = size.charAt(0).toUpperCase() + size.slice(1);
                if (config.iconSize === size) option.selected = true;
                iconSizeSelect.appendChild(option);
            });

            iconSizeSelect.onchange = async () => {
                config.iconSize = iconSizeSelect.value;
                await saveConfig(config);
                
                // Destroy and recreate UI to apply new icon size
                if (container && container.parentNode) {
                    container.parentNode.removeChild(container);
                }
                if (panel && panel.parentNode) {
                    panel.parentNode.removeChild(panel);
                }
                if (settingsPanel && settingsPanel.parentNode) {
                    settingsPanel.parentNode.removeChild(settingsPanel);
                }
                if (helpPanel && helpPanel.parentNode) {
                    helpPanel.parentNode.removeChild(helpPanel);
                }
                destroyPopoutButtons();
                createUI();
                showToast('Icon size changed!', 'success');
            };

            iconSizeRow.appendChild(iconSizeLabel);
            iconSizeRow.appendChild(iconSizeSelect);
            iconControlsSection.appendChild(iconSizeRow);

            // Toggle Icon Keybinding
            const toggleKbRow = document.createElement('div');
            toggleKbRow.style.cssText = `
                display: flex;
                gap: 6px;
                margin-top: 10px;
                align-items: center;
            `;

            const toggleKbLabel = document.createElement('div');
            toggleKbLabel.textContent = 'Toggle Icon:';
            toggleKbLabel.style.cssText = `
                flex: 0 0 100px;
                font-size: 11px;
                color: #333;
            `;

            const toggleKbInput = document.createElement('input');
            toggleKbInput.type = 'text';
            toggleKbInput.value = config.toggleIconKeybinding || '';
            toggleKbInput.placeholder = 'Ctrl+Shift+B';
            toggleKbInput.style.cssText = `
                flex: 1;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
            `;

            toggleKbInput.oninput = async function() {
                config.toggleIconKeybinding = toggleKbInput.value.trim();
                await saveConfig(config);
            };

            const toggleRecordBtn = document.createElement('button');
            toggleRecordBtn.textContent = '⏺️ Record';
            toggleRecordBtn.style.cssText = `
                padding: 4px 8px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
                white-space: nowrap;
            `;

            toggleRecordBtn.onclick = function() {
                toggleRecordBtn.textContent = 'Press keys...';
                toggleRecordBtn.style.background = '#dc3545';
                toggleKbInput.style.background = '#fff3cd';
                toggleKbInput.value = '';
                toggleKbInput.focus();

                const recordListener = function(e) {
                    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
                        return; // Wait for the actual key
                    }

                    e.preventDefault();

                    const parts = [];
                    if (e.ctrlKey) parts.push('Ctrl');
                    if (e.shiftKey) parts.push('Shift');
                    if (e.altKey) parts.push('Alt');

                    if (!['Control', 'Shift', 'Alt'].includes(e.key)) {
                        parts.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);
                    }

                    if (parts.length > 0) {
                        const binding = parts.join('+');
                        toggleKbInput.value = binding;
                        config.toggleIconKeybinding = binding;
                        saveConfig(config);

                        toggleRecordBtn.textContent = '⏺️ Record';
                        toggleRecordBtn.style.background = '#007bff';
                        toggleKbInput.style.background = 'white';

                        window.removeEventListener('keydown', recordListener, true);
                    }
                };

                window.addEventListener('keydown', recordListener, true);
            };

            const toggleClearBtn = document.createElement('button');
            toggleClearBtn.textContent = 'Clear';
            toggleClearBtn.style.cssText = `
                padding: 4px 8px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
            `;
            toggleClearBtn.onclick = async function() {
                config.toggleIconKeybinding = '';
                toggleKbInput.value = '';
                await saveConfig(config);
            };

            toggleKbRow.appendChild(toggleKbLabel);
            toggleKbRow.appendChild(toggleKbInput);
            toggleKbRow.appendChild(toggleRecordBtn);
            toggleKbRow.appendChild(toggleClearBtn);
            iconControlsSection.appendChild(toggleKbRow);

            // Add Category Keybinding Row
            const addCatKbRow = document.createElement('div');
            addCatKbRow.style.cssText = `
                display: flex;
                gap: 6px;
                margin-top: 10px;
                align-items: center;
            `;

            const addCatKbLabel = document.createElement('div');
            addCatKbLabel.textContent = 'Add Category:';
            addCatKbLabel.style.cssText = `
                flex: 0 0 100px;
                font-size: 11px;
                color: #333;
            `;

            const addCatKbInput = document.createElement('input');
            addCatKbInput.type = 'text';
            addCatKbInput.value = config.addCategoryKeybinding || '';
            addCatKbInput.placeholder = 'Ctrl+Shift+N';
            addCatKbInput.readOnly = true;
            addCatKbInput.style.cssText = `
                flex: 1;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
            `;

            const addCatRecordBtn = document.createElement('button');
            addCatRecordBtn.textContent = '⏺️ Record';
            addCatRecordBtn.style.cssText = `
                padding: 4px 8px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
                white-space: nowrap;
            `;

            const addCatClearBtn = document.createElement('button');
            addCatClearBtn.textContent = 'Clear';
            addCatClearBtn.style.cssText = `
                padding: 4px 8px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
            `;

            let addCatRecording = false;
            addCatRecordBtn.onclick = () => {
                if (addCatRecording) return;
                addCatRecording = true;
                addCatRecordBtn.textContent = 'Press keys...';
                addCatRecordBtn.style.background = '#dc3545';
                addCatKbInput.style.background = '#fff3cd';
                addCatKbInput.value = '';

                const handler = async (e) => {
                    e.preventDefault();
                    const kb = captureKeybinding(e);
                    addCatKbInput.value = kb;
                    config.addCategoryKeybinding = kb;
                    await saveConfig();
                    registerKeybindings();
                    addCatRecordBtn.textContent = '⏺️ Record';
                    addCatRecordBtn.style.background = '#007bff';
                    addCatKbInput.style.background = 'white';
                    addCatRecording = false;
                    window.removeEventListener('keydown', handler, true);
                };
                window.addEventListener('keydown', handler, true);
            };

            addCatClearBtn.onclick = async () => {
                config.addCategoryKeybinding = '';
                addCatKbInput.value = '';
                await saveConfig();
                registerKeybindings();
            };

            addCatKbRow.appendChild(addCatKbLabel);
            addCatKbRow.appendChild(addCatKbInput);
            addCatKbRow.appendChild(addCatRecordBtn);
            addCatKbRow.appendChild(addCatClearBtn);
            iconControlsSection.appendChild(addCatKbRow);

            // Add Custom Link Keybinding Row
            const addLinkKbRow = document.createElement('div');
            addLinkKbRow.style.cssText = `
                display: flex;
                gap: 6px;
                margin-top: 10px;
                align-items: center;
            `;

            const addLinkKbLabel = document.createElement('div');
            addLinkKbLabel.textContent = 'Add Link:';
            addLinkKbLabel.style.cssText = `
                flex: 0 0 100px;
                font-size: 11px;
                color: #333;
            `;

            const addLinkKbInput = document.createElement('input');
            addLinkKbInput.type = 'text';
            addLinkKbInput.value = config.addCustomLinkKeybinding || '';
            addLinkKbInput.placeholder = 'Ctrl+Shift+L';
            addLinkKbInput.readOnly = true;
            addLinkKbInput.style.cssText = `
                flex: 1;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 11px;
                font-family: monospace;
            `;

            const addLinkRecordBtn = document.createElement('button');
            addLinkRecordBtn.textContent = '⏺️ Record';
            addLinkRecordBtn.style.cssText = `
                padding: 4px 8px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
                white-space: nowrap;
            `;

            const addLinkClearBtn = document.createElement('button');
            addLinkClearBtn.textContent = 'Clear';
            addLinkClearBtn.style.cssText = `
                padding: 4px 8px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
            `;

            let addLinkRecording = false;
            addLinkRecordBtn.onclick = () => {
                if (addLinkRecording) return;
                addLinkRecording = true;
                addLinkRecordBtn.textContent = 'Press keys...';
                addLinkRecordBtn.style.background = '#dc3545';
                addLinkKbInput.style.background = '#fff3cd';
                addLinkKbInput.value = '';

                const handler = async (e) => {
                    e.preventDefault();
                    const kb = captureKeybinding(e);
                    addLinkKbInput.value = kb;
                    config.addCustomLinkKeybinding = kb;
                    await saveConfig();
                    registerKeybindings();
                    addLinkRecordBtn.textContent = '⏺️ Record';
                    addLinkRecordBtn.style.background = '#007bff';
                    addLinkKbInput.style.background = 'white';
                    addLinkRecording = false;
                    window.removeEventListener('keydown', handler, true);
                };
                window.addEventListener('keydown', handler, true);
            };

            addLinkClearBtn.onclick = async () => {
                config.addCustomLinkKeybinding = '';
                addLinkKbInput.value = '';
                await saveConfig();
                registerKeybindings();
            };

            addLinkKbRow.appendChild(addLinkKbLabel);
            addLinkKbRow.appendChild(addLinkKbInput);
            addLinkKbRow.appendChild(addLinkRecordBtn);
            addLinkKbRow.appendChild(addLinkClearBtn);
            iconControlsSection.appendChild(addLinkKbRow);

            settingsPanel.appendChild(iconControlsSection);

            // Pop-out Buttons Section
            const popoutSection = document.createElement('div');
            popoutSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
                border: 1px solid #ddd;
            `;

            const popoutTitle = document.createElement('div');
            popoutTitle.textContent = '🔘 Pop-out Category Buttons';
            popoutTitle.style.cssText = `
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            `;
            popoutSection.appendChild(popoutTitle);

            // Enable/Disable Pop-out Buttons
            const popoutEnabledRow = document.createElement('div');
            popoutEnabledRow.style.cssText = `
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            `;

            const popoutEnabledCheckbox = document.createElement('input');
            popoutEnabledCheckbox.type = 'checkbox';
            popoutEnabledCheckbox.checked = config.popoutButtons.enabled;
            popoutEnabledCheckbox.style.marginRight = '8px';

            const popoutEnabledLabel = document.createElement('label');
            popoutEnabledLabel.textContent = 'Enable pop-out category buttons';
            popoutEnabledLabel.style.fontSize = '13px';

            popoutEnabledCheckbox.onchange = async () => {
                config.popoutButtons.enabled = popoutEnabledCheckbox.checked;
                await saveConfig(config);
                createPopoutButtons(); // Recreate buttons based on new setting
                refreshSettingsUI(); // Refresh to show/hide other options
            };

            popoutEnabledRow.appendChild(popoutEnabledCheckbox);
            popoutEnabledRow.appendChild(popoutEnabledLabel);
            popoutSection.appendChild(popoutEnabledRow);

            if (config.popoutButtons.enabled) {
                // Button Size Setting
                const sizeRow = document.createElement('div');
                sizeRow.style.cssText = `
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                `;

                const sizeLabel = document.createElement('label');
                sizeLabel.textContent = 'Button Size: ';
                sizeLabel.style.cssText = `font-size: 13px; margin-right: 8px;`;

                const sizeSelect = document.createElement('select');
                sizeSelect.style.cssText = `
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 13px;
                `;

                ['small', 'medium', 'large'].forEach(size => {
                    const option = document.createElement('option');
                    option.value = size;
                    option.textContent = size.charAt(0).toUpperCase() + size.slice(1);
                    option.selected = config.popoutButtons.buttonSize === size;
                    sizeSelect.appendChild(option);
                });

                sizeSelect.onchange = async () => {
                    config.popoutButtons.buttonSize = sizeSelect.value;
                    await saveConfig(config);
                    createPopoutButtons(); // Recreate buttons with new size
                };

                sizeRow.appendChild(sizeLabel);
                sizeRow.appendChild(sizeSelect);
                popoutSection.appendChild(sizeRow);

                // Show Labels Setting
                const labelsRow = document.createElement('div');
                labelsRow.style.cssText = `
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                `;

                const labelsCheckbox = document.createElement('input');
                labelsCheckbox.type = 'checkbox';
                labelsCheckbox.checked = config.popoutButtons.showLabels;
                labelsCheckbox.style.marginRight = '8px';

                const labelsLabel = document.createElement('label');
                labelsLabel.textContent = 'Show category labels on buttons (when short enough)';
                labelsLabel.style.fontSize = '13px';

                labelsCheckbox.onchange = async () => {
                    config.popoutButtons.showLabels = labelsCheckbox.checked;
                    await saveConfig(config);
                    createPopoutButtons(); // Recreate buttons with new labels
                };

                labelsRow.appendChild(labelsCheckbox);
                labelsRow.appendChild(labelsLabel);
                popoutSection.appendChild(labelsRow);

                // Individual Category Controls
                const catControlsTitle = document.createElement('div');
                catControlsTitle.textContent = 'Category Button Controls:';
                catControlsTitle.style.cssText = `
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 13px;
                    color: #555;
                `;
                popoutSection.appendChild(catControlsTitle);

                for (const category of config.categories) {
                    const catRow = document.createElement('div');
                    catRow.style.cssText = `
                        margin-bottom: 6px;
                        padding: 6px;
                        background: #f8f9fa;
                        border-radius: 4px;
                    `;

                    const catCheckbox = document.createElement('input');
                    catCheckbox.type = 'checkbox';
                    catCheckbox.checked = config.popoutButtons.categories[category.key]?.enabled || false;
                    catCheckbox.style.marginRight = '8px';

                    const catLabel = document.createElement('span');
                    catLabel.textContent = category.label;
                    catLabel.style.cssText = `font-size: 12px; font-weight: bold; margin-right: 8px;`;

                    const catHeader = document.createElement('div');
                    catHeader.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                    catHeader.appendChild(catCheckbox);
                    catHeader.appendChild(catLabel);

                    // Customization fields (shown when enabled)
                    const customFields = document.createElement('div');
                    customFields.style.display = catCheckbox.checked ? 'block' : 'none';
                    customFields.style.marginLeft = '20px';
                    customFields.style.marginTop = '6px';
                    customFields.style.padding = '8px';
                    customFields.style.background = '#ffffff';
                    customFields.style.border = '1px solid #dee2e6';
                    customFields.style.borderRadius = '4px';

                    // Button text input
                    const textRow = document.createElement('div');
                    textRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                    const textLabel = document.createElement('span');
                    textLabel.textContent = 'Button Text:';
                    textLabel.style.cssText = `font-size: 11px; width: 80px;`;

                    const textInput = document.createElement('input');
                    textInput.type = 'text';
                    textInput.placeholder = category.label;
                    textInput.value = config.popoutButtons.categories[category.key]?.buttonText || '';
                    textInput.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    `;
                    textInput.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].buttonText = textInput.value;
                        await saveConfig(config);
                        createPopoutButtons();
                    };

                    textRow.appendChild(textLabel);
                    textRow.appendChild(textInput);

                    // Button size dropdown
                    const sizeRow = document.createElement('div');
                    sizeRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                    const sizeLabel = document.createElement('span');
                    sizeLabel.textContent = 'Size:';
                    sizeLabel.style.cssText = `font-size: 11px; width: 80px;`;

                    const sizeSelect = document.createElement('select');
                    sizeSelect.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    `;
                    const sizeOptions = [
                        { value: 'inherit', label: 'Inherit from Global' },
                        { value: 'small', label: 'Small (32px)' },
                        { value: 'medium', label: 'Medium (40px)' },
                        { value: 'large', label: 'Large (48px)' }
                    ];
                    for (const opt of sizeOptions) {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.label;
                        sizeSelect.appendChild(option);
                    }
                    sizeSelect.value = config.popoutButtons.categories[category.key]?.buttonSize || 'inherit';
                    sizeSelect.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].buttonSize = sizeSelect.value;
                        await saveConfig(config);
                        createPopoutButtons();
                    };

                    sizeRow.appendChild(sizeLabel);
                    sizeRow.appendChild(sizeSelect);

                    // Button shape dropdown
                    const shapeRow = document.createElement('div');
                    shapeRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                    const shapeLabel = document.createElement('span');
                    shapeLabel.textContent = 'Shape:';
                    shapeLabel.style.cssText = `font-size: 11px; width: 80px;`;

                    const shapeSelect = document.createElement('select');
                    shapeSelect.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    `;
                    const shapeOptions = [
                        { value: 'circle', label: '● Circle' },
                        { value: 'rounded', label: '◆ Rounded' },
                        { value: 'square', label: '■ Square' },
                        { value: 'pill', label: '▬ Pill' },
                        { value: 'rect-h', label: '▬ Rectangle (Horizontal)' },
                        { value: 'rect-v', label: '▮ Rectangle (Vertical)' }
                    ];
                    for (const opt of shapeOptions) {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.label;
                        shapeSelect.appendChild(option);
                    }
                    shapeSelect.value = config.popoutButtons.categories[category.key]?.buttonShape || 'circle';
                    shapeSelect.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].buttonShape = shapeSelect.value;
                        await saveConfig(config);
                        createPopoutButtons();
                    };

                    shapeRow.appendChild(shapeLabel);
                    shapeRow.appendChild(shapeSelect);

                    // Button color input
                    const colorRow = document.createElement('div');
                    colorRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                    
                    const colorLabel = document.createElement('span');
                    colorLabel.textContent = 'Color:';
                    colorLabel.style.cssText = `font-size: 11px; width: 80px;`;
                    
                    const colorInput = document.createElement('input');
                    colorInput.type = 'color';
                    colorInput.value = config.popoutButtons.categories[category.key]?.buttonColor || '#007bff';
                    colorInput.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        height: 28px;
                        cursor: pointer;
                    `;
                    colorInput.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].buttonColor = colorInput.value;
                        await saveConfig(config);
                        createPopoutButtons();
                    };
                    
                    colorRow.appendChild(colorLabel);
                    colorRow.appendChild(colorInput);

                    // Button text color input
                    const textColorRow = document.createElement('div');
                    textColorRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                    
                    const textColorLabel = document.createElement('span');
                    textColorLabel.textContent = 'Text Color:';
                    textColorLabel.style.cssText = `font-size: 11px; width: 80px;`;
                    
                    const textColorInput = document.createElement('input');
                    textColorInput.type = 'color';
                    textColorInput.value = config.popoutButtons.categories[category.key]?.buttonTextColor || '#ffffff';
                    textColorInput.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        height: 28px;
                        cursor: pointer;
                    `;
                    textColorInput.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].buttonTextColor = textColorInput.value;
                        await saveConfig(config);
                        createPopoutButtons();
                    };
                    
                    textColorRow.appendChild(textColorLabel);
                    textColorRow.appendChild(textColorInput);

                    // Reset colors button
                    const resetColorsBtn = document.createElement('button');
                    resetColorsBtn.textContent = '↺ Reset Colors';
                    resetColorsBtn.style.cssText = `
                        padding: 3px 8px;
                        background: #6c757d;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 11px;
                        margin-top: 6px;
                        width: 100%;
                    `;
                    resetColorsBtn.onclick = async () => {
                        if (config.popoutButtons.categories[category.key]) {
                            delete config.popoutButtons.categories[category.key].buttonColor;
                            delete config.popoutButtons.categories[category.key].buttonTextColor;
                            colorInput.value = category.color || '#007bff';
                            textColorInput.value = category.textColor || '#ffffff';
                            await saveConfig(config);
                            createPopoutButtons();
                            showToast(`Colors reset for ${category.label} popout!`);
                        }
                    };

                    // Text size input
                    const textSizeRow = document.createElement('div');
                    textSizeRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                    
                    const textSizeLabel = document.createElement('span');
                    textSizeLabel.textContent = 'Text Size:';
                    textSizeLabel.style.cssText = `font-size: 11px; width: 80px;`;
                    
                    const textSizeInput = document.createElement('input');
                    textSizeInput.type = 'number';
                    textSizeInput.min = '8';
                    textSizeInput.max = '24';
                    textSizeInput.value = config.popoutButtons.categories[category.key]?.textSize || '12';
                    textSizeInput.style.cssText = `
                        flex: 1;
                        padding: 3px 6px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        height: 28px;
                    `;
                    textSizeInput.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].textSize = parseInt(textSizeInput.value);
                        await saveConfig(config);
                        createPopoutButtons();
                    };
                    
                    const textSizeUnit = document.createElement('span');
                    textSizeUnit.textContent = 'px';
                    textSizeUnit.style.cssText = `font-size: 11px; margin-left: 4px;`;
                    
                    textSizeRow.appendChild(textSizeLabel);
                    textSizeRow.appendChild(textSizeInput);
                    textSizeRow.appendChild(textSizeUnit);

                    // Reset position button
                    const resetPosBtn = document.createElement('button');
                    resetPosBtn.textContent = '↺ Reset Position';
                    resetPosBtn.style.cssText = `
                        padding: 3px 8px;
                        background: #ffc107;
                        color: #333;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 11px;
                        margin-top: 6px;
                        width: 100%;
                    `;
                    resetPosBtn.onclick = async () => {
                        if (config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key].position = null;
                            await saveConfig(config);
                            createPopoutButtons(); // Recreate buttons with default positions
                        }
                    };

                    // Show/hide custom fields based on checkbox
                    catCheckbox.onchange = async () => {
                        if (!config.popoutButtons.categories[category.key]) {
                            config.popoutButtons.categories[category.key] = {};
                        }
                        config.popoutButtons.categories[category.key].enabled = catCheckbox.checked;
                        customFields.style.display = catCheckbox.checked ? 'block' : 'none';
                        await saveConfig(config);
                        createPopoutButtons(); // Recreate buttons
                    };

                    customFields.appendChild(textRow);
                    customFields.appendChild(sizeRow);
                    customFields.appendChild(shapeRow);
                    customFields.appendChild(colorRow);
                    customFields.appendChild(textColorRow);
                    customFields.appendChild(textSizeRow);
                    customFields.appendChild(resetColorsBtn);
                    customFields.appendChild(resetPosBtn);

                    catRow.appendChild(catHeader);
                    catRow.appendChild(customFields);
                    popoutSection.appendChild(catRow);
                }

                // Add Custom Link Button Controls
                const customLinkRow = document.createElement('div');
                customLinkRow.style.cssText = `
                    margin-bottom: 6px;
                    padding: 6px;
                    background: #f8f9fa;
                    border-radius: 4px;
                `;

                const customLinkCheckbox = document.createElement('input');
                customLinkCheckbox.type = 'checkbox';
                customLinkCheckbox.checked = config.popoutButtons.categories['__customLink__']?.enabled || false;
                customLinkCheckbox.style.marginRight = '8px';

                const customLinkLabel = document.createElement('span');
                customLinkLabel.textContent = '➕ Add Custom Link';
                customLinkLabel.style.cssText = `font-size: 12px; font-weight: bold; margin-right: 8px;`;

                const customLinkHeader = document.createElement('div');
                customLinkHeader.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                customLinkHeader.appendChild(customLinkCheckbox);
                customLinkHeader.appendChild(customLinkLabel);

                // Customization fields for custom link button
                const customLinkFields = document.createElement('div');
                customLinkFields.style.display = customLinkCheckbox.checked ? 'block' : 'none';
                customLinkFields.style.marginLeft = '20px';
                customLinkFields.style.marginTop = '6px';
                customLinkFields.style.padding = '8px';
                customLinkFields.style.background = '#ffffff';
                customLinkFields.style.border = '1px solid #dee2e6';
                customLinkFields.style.borderRadius = '3px';

                // Button text input
                const clTextRow = document.createElement('div');
                clTextRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                const clTextLabel = document.createElement('span');
                clTextLabel.textContent = 'Button Text:';
                clTextLabel.style.cssText = `font-size: 11px; width: 80px;`;

                const clTextInput = document.createElement('input');
                clTextInput.type = 'text';
                clTextInput.placeholder = '➕ Add Custom Link';
                clTextInput.value = config.popoutButtons.categories['__customLink__']?.buttonText || '';
                clTextInput.style.cssText = `
                    flex: 1;
                    padding: 3px 6px;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                `;
                clTextInput.onchange = async () => {
                    if (!config.popoutButtons.categories['__customLink__']) {
                        config.popoutButtons.categories['__customLink__'] = {};
                    }
                    config.popoutButtons.categories['__customLink__'].buttonText = clTextInput.value;
                    await saveConfig(config);
                    createPopoutButtons();
                };

                clTextRow.appendChild(clTextLabel);
                clTextRow.appendChild(clTextInput);

                // Button size dropdown
                const clSizeRow = document.createElement('div');
                clSizeRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                const clSizeLabel = document.createElement('span');
                clSizeLabel.textContent = 'Size:';
                clSizeLabel.style.cssText = `font-size: 11px; width: 80px;`;

                const clSizeSelect = document.createElement('select');
                clSizeSelect.style.cssText = `
                    flex: 1;
                    padding: 3px 6px;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                `;
                const clSizeOptions = [
                    { value: 'inherit', label: 'Inherit from Global' },
                    { value: 'small', label: 'Small (32px)' },
                    { value: 'medium', label: 'Medium (40px)' },
                    { value: 'large', label: 'Large (48px)' }
                ];
                clSizeOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    if (config.popoutButtons.categories['__customLink__']?.buttonSize === opt.value) {
                        option.selected = true;
                    }
                    clSizeSelect.appendChild(option);
                });

                clSizeSelect.onchange = async () => {
                    if (!config.popoutButtons.categories['__customLink__']) {
                        config.popoutButtons.categories['__customLink__'] = {};
                    }
                    config.popoutButtons.categories['__customLink__'].buttonSize = clSizeSelect.value;
                    await saveConfig(config);
                    createPopoutButtons();
                };

                clSizeRow.appendChild(clSizeLabel);
                clSizeRow.appendChild(clSizeSelect);

                // Button shape dropdown
                const clShapeRow = document.createElement('div');
                clShapeRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;

                const clShapeLabel = document.createElement('span');
                clShapeLabel.textContent = 'Shape:';
                clShapeLabel.style.cssText = `font-size: 11px; width: 80px;`;

                const clShapeSelect = document.createElement('select');
                clShapeSelect.style.cssText = `
                    flex: 1;
                    padding: 3px 6px;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                `;
                const clShapeOptions = [
                    { value: 'circle', label: 'Circle' },
                    { value: 'square', label: 'Square' },
                    { value: 'rounded', label: 'Rounded Square' },
                    { value: 'pill', label: 'Pill' },
                    { value: 'rect-h', label: 'Horizontal Rectangle' },
                    { value: 'rect-v', label: 'Vertical Rectangle' }
                ];
                clShapeOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    if (config.popoutButtons.categories['__customLink__']?.buttonShape === opt.value) {
                        option.selected = true;
                    }
                    clShapeSelect.appendChild(option);
                });

                clShapeSelect.onchange = async () => {
                    if (!config.popoutButtons.categories['__customLink__']) {
                        config.popoutButtons.categories['__customLink__'] = {};
                    }
                    config.popoutButtons.categories['__customLink__'].buttonShape = clShapeSelect.value;
                    await saveConfig(config);
                    createPopoutButtons();
                };

                clShapeRow.appendChild(clShapeLabel);
                clShapeRow.appendChild(clShapeSelect);

                // Color settings
                const clColorRow = document.createElement('div');
                clColorRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                
                const clColorLabel = document.createElement('span');
                clColorLabel.textContent = 'Color:';
                clColorLabel.style.cssText = `font-size: 11px; width: 80px;`;
                
                const clColorInput = document.createElement('input');
                clColorInput.type = 'color';
                clColorInput.value = config.customLinkButton?.color || '#17a2b8';
                clColorInput.style.cssText = `
                    flex: 1;
                    padding: 3px 6px;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    height: 28px;
                    cursor: pointer;
                `;
                clColorInput.onchange = async () => {
                    if (!config.customLinkButton) config.customLinkButton = {};
                    config.customLinkButton.color = clColorInput.value;
                    await saveConfig(config);
                    rebuildCategoryButtons();
                };
                
                clColorRow.appendChild(clColorLabel);
                clColorRow.appendChild(clColorInput);

                const clTextColorRow = document.createElement('div');
                clTextColorRow.style.cssText = `display: flex; align-items: center; margin-bottom: 6px;`;
                
                const clTextColorLabel = document.createElement('span');
                clTextColorLabel.textContent = 'Text Color:';
                clTextColorLabel.style.cssText = `font-size: 11px; width: 80px;`;
                
                const clTextColorInput = document.createElement('input');
                clTextColorInput.type = 'color';
                clTextColorInput.value = config.customLinkButton?.textColor || '#ffffff';
                clTextColorInput.style.cssText = `
                    flex: 1;
                    padding: 3px 6px;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    height: 28px;
                    cursor: pointer;
                `;
                clTextColorInput.onchange = async () => {
                    if (!config.customLinkButton) config.customLinkButton = {};
                    config.customLinkButton.textColor = clTextColorInput.value;
                    await saveConfig(config);
                    rebuildCategoryButtons();
                };
                
                clTextColorRow.appendChild(clTextColorLabel);
                clTextColorRow.appendChild(clTextColorInput);

                // Reset colors button
                const clResetColorsBtn = document.createElement('button');
                clResetColorsBtn.textContent = '🔄 Reset Colors';
                clResetColorsBtn.style.cssText = `
                    padding: 4px 8px;
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 11px;
                    margin-bottom: 6px;
                    width: 100%;
                `;
                clResetColorsBtn.onclick = async () => {
                    config.customLinkButton = { color: '#17a2b8', textColor: '#ffffff' };
                    clColorInput.value = '#17a2b8';
                    clTextColorInput.value = '#ffffff';
                    await saveConfig(config);
                    rebuildCategoryButtons();
                    showToast('Custom Link colors reset!', 'success');
                };

                customLinkCheckbox.onchange = async () => {
                    if (!config.popoutButtons.categories['__customLink__']) {
                        config.popoutButtons.categories['__customLink__'] = {};
                    }
                    config.popoutButtons.categories['__customLink__'].enabled = customLinkCheckbox.checked;
                    customLinkFields.style.display = customLinkCheckbox.checked ? 'block' : 'none';
                    await saveConfig(config);
                    createPopoutButtons();
                };

                customLinkFields.appendChild(clTextRow);
                customLinkFields.appendChild(clSizeRow);
                customLinkFields.appendChild(clShapeRow);
                customLinkFields.appendChild(clColorRow);
                customLinkFields.appendChild(clTextColorRow);
                customLinkFields.appendChild(clResetColorsBtn);

                customLinkRow.appendChild(customLinkHeader);
                customLinkRow.appendChild(customLinkFields);
                popoutSection.appendChild(customLinkRow);
            }

            settingsPanel.appendChild(popoutSection);

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
            // Don't open panel if we just finished dragging
            if (launcher.dataset.justDragged === 'true') {
                return;
            }

            e.stopPropagation();
            if (panel.style.display === 'block') hidePanel();
            else showPanel();
        });

        overlay.addEventListener('click', () => {
            hidePanel();
            settingsPanel.style.display = 'none';
            helpPanel.style.display = 'none';
        });

        closeBtn.addEventListener('click', hidePanel);

        // Keyboard shortcut: Ctrl+Shift+O to toggle panel
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyO') {
                if (panel.style.display === 'block') hidePanel();
                else showPanel();
                e.preventDefault();
            }

            // Configurable keybinding to toggle icon visibility
            if (config.toggleIconKeybinding && matchesKeybinding(e, config.toggleIconKeybinding)) {
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

                // Category header row with copy button
                const categoryHeaderRow = document.createElement('div');
                categoryHeaderRow.style.cssText = `
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-top: 20px;
                    margin-bottom: 8px;
                    padding-bottom: 6px;
                    border-bottom: 2px solid #007bff;
                `;

                const categoryHeader = document.createElement('div');
                categoryHeader.style.cssText = `
                    font-weight: bold;
                    font-size: 14px;
                    color: #007bff;
                `;
                categoryHeader.textContent = cat.label;

                const copyCategoryBtn = document.createElement('button');
                copyCategoryBtn.textContent = '\u{1F4CB}';
                copyCategoryBtn.title = 'Copy all URLs from this category';
                copyCategoryBtn.style.cssText = `
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    cursor: pointer;
                    font-size: 14px;
                    margin-left: 4px;
                `;
                copyCategoryBtn.onmouseover = () => copyCategoryBtn.style.background = '#0056b3';
                copyCategoryBtn.onmouseout = () => copyCategoryBtn.style.background = '#007bff';
                copyCategoryBtn.onclick = async () => {
                    const categoryUrls = list.map(item => typeof item === 'string' ? item : item.url);
                    if (categoryUrls.length === 0) {
                        showToast('No URLs to copy', 'warning');
                        return;
                    }
                    const textToCopy = `== ${cat.label} ==\\n${categoryUrls.join('\\n')}`;
                    await navigator.clipboard.writeText(textToCopy);
                    copyCategoryBtn.textContent = '\u2713';
                    showToast(`Copied ${categoryUrls.length} URL(s) from ${cat.label}`, 'success');
                    setTimeout(() => {
                        copyCategoryBtn.textContent = '\u{1F4CB}';
                    }, 1500);
                };

                const downloadCategoryBtn = document.createElement('button');
                downloadCategoryBtn.textContent = '\u{1F4E5}';
                downloadCategoryBtn.title = 'Download this category';
                downloadCategoryBtn.style.cssText = `
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    cursor: pointer;
                    font-size: 14px;
                    margin-left: 4px;
                `;
                downloadCategoryBtn.onmouseover = () => downloadCategoryBtn.style.background = '#218838';
                downloadCategoryBtn.onmouseout = () => downloadCategoryBtn.style.background = '#28a745';
                downloadCategoryBtn.onclick = async () => {
                    if (list.length === 0) {
                        showToast('No URLs to download', 'warning');
                        return;
                    }
                    
                    // Build category export data
                    const categoryData = {
                        category: cat.label,
                        date: new Date().toLocaleString('en-US', { timeZone: config.timezone || 'UTC' }),
                        urls: list.map(item => typeof item === 'string' ? item : item.url),
                        displayNames: list.map(item => typeof item === 'string' ? item : (item.displayName || item.url))
                    };
                    
                    let content, filename, mimeType;
                    const format = config.exportFormat || 'txt';
                    
                    if (format === 'json') {
                        content = JSON.stringify(categoryData, null, 2);
                        filename = `${cat.label.replace(/[^a-z0-9]/gi, '_')}_${data.date}.json`;
                        mimeType = 'application/json';
                    } else if (format === 'md') {
                        content = `# ${cat.label}\\n\\n**Date:** ${categoryData.date}\\n\\n`;
                        categoryData.displayNames.forEach((name, idx) => {
                            content += `- [${name}](${categoryData.urls[idx]})\\n`;
                        });
                        filename = `${cat.label.replace(/[^a-z0-9]/gi, '_')}_${data.date}.md`;
                        mimeType = 'text/markdown';
                    } else if (format === 'html') {
                        content = `<!DOCTYPE html>\\n<html>\\n<head>\\n<title>${cat.label}</title>\\n</head>\\n<body>\\n<h1>${cat.label}</h1>\\n<p><strong>Date:</strong> ${categoryData.date}</p>\\n<ul>\\n`;
                        categoryData.displayNames.forEach((name, idx) => {
                            content += `<li><a href="${categoryData.urls[idx]}">${name}</a></li>\\n`;
                        });
                        content += `</ul>\\n</body>\\n</html>`;
                        filename = `${cat.label.replace(/[^a-z0-9]/gi, '_')}_${data.date}.html`;
                        mimeType = 'text/html';
                    } else {
                        content = `== ${cat.label} ==\\nDate: ${categoryData.date}\\n\\n`;
                        categoryData.urls.forEach(url => {
                            content += url + '\\n';
                        });
                        filename = `${cat.label.replace(/[^a-z0-9]/gi, '_')}_${data.date}.txt`;
                        mimeType = 'text/plain';
                    }
                    
                    const blob = new Blob([content], { type: mimeType });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    a.click();
                    URL.revokeObjectURL(url);
                    showToast(`Downloaded ${cat.label}`, 'success');
                };

                const buttonGroup = document.createElement('div');
                buttonGroup.style.cssText = 'display: flex; gap: 4px;';
                buttonGroup.appendChild(copyCategoryBtn);
                buttonGroup.appendChild(downloadCategoryBtn);

                categoryHeaderRow.appendChild(categoryHeader);
                categoryHeaderRow.appendChild(buttonGroup);
                listContainer.appendChild(categoryHeaderRow);

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
                        const urlItem = list[i];

                        // Handle both old string format and new object format for backward compatibility
                        let url, displayName;
                        if (typeof urlItem === 'string') {
                            url = urlItem;
                            displayName = urlItem;
                            // Migrate old format to new format
                            list[i] = { url: url, displayName: displayName };
                        } else {
                            url = urlItem.url;
                            displayName = urlItem.displayName || url;
                        }

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

                        // URL text (clickable link with display name)
                        const urlLink = document.createElement('a');
                        urlLink.href = url;
                        urlLink.target = '_blank';
                        urlLink.textContent = displayName;
                        urlLink.title = url; // Show full URL on hover
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

                        // Rename button
                        const renameBtn = document.createElement('button');
                        renameBtn.textContent = '✏️';
                        renameBtn.title = 'Rename display name';
                        renameBtn.style.cssText = `
                            padding: 4px 8px;
                            background: #6f42c1;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            cursor: pointer;
                            font-size: 12px;
                            min-width: 32px;
                        `;
                        renameBtn.onmouseover = () => renameBtn.style.background = '#5a32a3';
                        renameBtn.onmouseout = () => renameBtn.style.background = '#6f42c1';
                        renameBtn.onclick = async () => {
                            const newDisplayName = prompt('Enter display name for this URL:', displayName);
                            if (newDisplayName !== null && newDisplayName.trim() !== '') {
                                list[i].displayName = newDisplayName.trim();
                                await saveDataToGM(data);
                                refreshListDisplay();
                            }
                        };

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
                        item.appendChild(renameBtn);
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

        // Create pop-out category buttons if enabled
        createPopoutButtons();
    }

    /** ---------- POP-OUT CATEGORY BUTTONS ---------- **/

    let popoutButtons = {}; // Store button elements by category key

    function createPopoutButtons() {
        // Remove any existing pop-out buttons first
        destroyPopoutButtons();

        if (!config.popoutButtons.enabled) {
            return;
        }

        console.log('[URL Reporter] Creating pop-out category buttons');

        for (const category of config.categories) {
            const catConfig = config.popoutButtons.categories[category.key];

            if (catConfig && catConfig.enabled) {
                createPopoutButton(category);
            }
        }

        // Create Add Custom Link popout button if enabled
        const customLinkConfig = config.popoutButtons.categories['__customLink__'];
        if (customLinkConfig && customLinkConfig.enabled) {
            const customLinkCategory = {
                key: '__customLink__',
                label: '➕ Add Custom Link',
                color: config.customLinkButton?.color || '#17a2b8',
                textColor: config.customLinkButton?.textColor || '#ffffff'
            };
            createPopoutButton(customLinkCategory, true); // true flag indicates it's the custom link button
        }
    }

    function destroyPopoutButtons() {
        for (const [catKey, button] of Object.entries(popoutButtons)) {
            if (button && button.parentNode) {
                button.parentNode.removeChild(button);
            }
        }
        popoutButtons = {};
    }

    // Helper function to adjust color brightness for gradient
    function adjustColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const r = Math.max(0, Math.min(255, (num >> 16) + percent));
        const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
        const b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
        return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
    }

    function createPopoutButton(category, isCustomLink = false) {
        const button = document.createElement('div');
        const catConfig = config.popoutButtons.categories[category.key];

        // Determine button size (use per-category override or global default)
        const sizeStyles = {
            small: { size: '32px', fontSize: '10px', padding: '4px' },
            medium: { size: '40px', fontSize: '12px', padding: '6px' },
            large: { size: '48px', fontSize: '14px', padding: '8px' }
        };

        let selectedSize = config.popoutButtons.buttonSize; // Global default
        if (catConfig?.buttonSize && catConfig.buttonSize !== 'inherit') {
            selectedSize = catConfig.buttonSize; // Per-category override
        }
        const size = sizeStyles[selectedSize] || sizeStyles.medium;

        // Determine shape (per-category or default to circle)
        const shape = catConfig?.buttonShape || 'circle';
        const shapeStyles = {
            square: '0',
            rounded: '8px',
            circle: '50%',
            pill: '999px',
            'rect-h': '4px',  // Horizontal rectangle with slight rounding
            'rect-v': '4px'   // Vertical rectangle with slight rounding
        };
        const borderRadius = shapeStyles[shape] || shapeStyles.circle;

        // Determine dimensions based on shape
        let buttonWidth = size.size;
        let buttonHeight = size.size;

        // Pills should be wider than they are tall
        if (shape === 'pill') {
            buttonWidth = `calc(${size.size} * 1.75)`; // 1.75x wider for pill shape
        }
        // Horizontal rectangle: wider than tall (similar to pill but more rectangular)
        else if (shape === 'rect-h') {
            buttonWidth = `calc(${size.size} * 2.0)`;  // 2x wider
        }
        // Vertical rectangle: taller than wide
        else if (shape === 'rect-v') {
            buttonHeight = `calc(${size.size} * 1.75)`; // 1.75x taller
        }

        // Determine button color (use custom, category color, or default blue)
        const baseColor = catConfig?.buttonColor || category.color || '#007bff';
        // Create darker shade for gradient (reduce lightness by ~20%)
        const darkerColor = adjustColor(baseColor, -20);
        const textColor = catConfig?.buttonTextColor || category.textColor || '#ffffff';
        
        // Determine text size (use per-category override or default from size preset)
        const textSize = catConfig?.textSize ? `${catConfig.textSize}px` : size.fontSize;

        button.style.cssText = `
            position: fixed;
            width: ${buttonWidth};
            height: ${buttonHeight};
            background: linear-gradient(135deg, ${baseColor}, ${darkerColor});
            border: 2px solid #fff;
            border-radius: ${borderRadius};
            cursor: move;
            z-index: 2147483646;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
            transition: all 0.2s ease;
            font-family: Arial, sans-serif;
            font-size: ${textSize};
            font-weight: bold;
            color: ${textColor};
            text-align: center;
            user-select: none;
        `;

        // Set button content - use custom text if provided, otherwise use label logic
        let displayText = '';
        if (catConfig?.buttonText) {
            // Use custom text from settings
            displayText = catConfig.buttonText;
        } else if (config.popoutButtons.showLabels && category.label.length <= 8) {
            // Use full label if it's short enough
            displayText = category.label;
        } else {
            // Use first letter or emoji if label is too long
            displayText = category.label.charAt(0).toUpperCase();
        }
        button.textContent = displayText;

        // Tooltip
        button.title = `Add current URL to "${category.label}"\nClick to add • Drag to move`;

        // Position the button
        if (catConfig.position) {
            button.style.left = catConfig.position.x + 'px';
            button.style.top = catConfig.position.y + 'px';
        } else {
            // Default positions in a vertical line to the left
            const index = config.categories.findIndex(c => c.key === category.key);
            button.style.left = '20px';
            button.style.top = (80 + index * 60) + 'px';
        }

        // Hover effects
        button.onmouseenter = () => {
            if (!button.isDragging) {
                button.style.transform = 'scale(1.1)';
                button.style.boxShadow = '0 6px 16px rgba(0,123,255,0.5)';
            }
        };

        button.onmouseleave = () => {
            if (!button.isDragging) {
                button.style.transform = 'scale(1)';
                button.style.boxShadow = '0 4px 12px rgba(0,123,255,0.3)';
            }
        };

        // Click handler for adding URLs or showing custom link dialog
        button.addEventListener('click', async (e) => {
            if (button.isDragging) return; // Don't add if we were dragging

            e.preventDefault();
            e.stopPropagation();

            if (isCustomLink) {
                // Show custom link dialog
                const url = prompt('Enter the URL:');
                if (!url) return;
                
                const displayName = prompt('Enter display name (optional):');
                
                // Build category selection prompt
                let categoryPrompt = 'Select category by number:\n';
                config.categories.forEach((cat, idx) => {
                    categoryPrompt += `${idx + 1}. ${cat.label}\n`;
                });
                const categoryNum = prompt(categoryPrompt);
                if (!categoryNum) return;
                
                const catIndex = parseInt(categoryNum) - 1;
                if (catIndex < 0 || catIndex >= config.categories.length) {
                    showToast('Invalid category number', 'error');
                    return;
                }
                
                const categoryKey = config.categories[catIndex].key;
                const urlObj = displayName ? { url, displayName } : url;
                
                data.lists[categoryKey] = data.lists[categoryKey] || [];
                data.lists[categoryKey].push(urlObj);
                await saveData();
                refreshListDisplay();
                showToast(`Added to ${config.categories[catIndex].label}`, 'success');
            } else {
                await addCurrentUrlToCategory(category.key);
                showToast(`Added to ${category.label}!`);
            }

            // Visual feedback
            button.style.background = 'linear-gradient(135deg, #28a745, #1e7e34)';
            button.style.transform = 'scale(1.2)';

            setTimeout(() => {
                button.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
                button.style.transform = 'scale(1)';
            }, 300);
        });

        // Drag functionality (both mouse and touch)
        let isDragging = false;
        let dragStart = { x: 0, y: 0 };
        let dragOffset = { x: 0, y: 0 };

        // Helper to get coordinates from mouse or touch event
        const getPopoutCoords = (e) => {
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            return { x: e.clientX, y: e.clientY };
        };

        const startPopoutDrag = (e) => {
            // Only left mouse button or touch
            if (e.button && e.button !== 0) return;

            isDragging = true;
            button.isDragging = false; // Will be set to true if we actually move
            const coords = getPopoutCoords(e);
            dragStart.x = coords.x;
            dragStart.y = coords.y;

            const rect = button.getBoundingClientRect();
            dragOffset.x = coords.x - rect.left;
            dragOffset.y = coords.y - rect.top;

            button.style.transition = 'none';
            button.style.zIndex = '2147483647';

            e.preventDefault();
        };

        const doPopoutDrag = (e) => {
            if (!isDragging) return;

            const coords = getPopoutCoords(e);
            const moveDistance = Math.abs(coords.x - dragStart.x) + Math.abs(coords.y - dragStart.y);
            if (moveDistance > 5) {
                button.isDragging = true;
            }

            const x = coords.x - dragOffset.x;
            const y = coords.y - dragOffset.y;

            // Keep button within viewport
            const maxX = window.innerWidth - button.offsetWidth;
            const maxY = window.innerHeight - button.offsetHeight;

            button.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
            button.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
            e.preventDefault();
        };

        const endPopoutDrag = async () => {
            if (!isDragging) return;

            isDragging = false;
            button.style.transition = 'all 0.2s ease';
            button.style.zIndex = '2147483646';

            // Save the new position
            const newX = parseInt(button.style.left);
            const newY = parseInt(button.style.top);

            config.popoutButtons.categories[category.key].position = { x: newX, y: newY };
            await saveConfig(config);

            // Reset dragging flag after a short delay to prevent click events
            setTimeout(() => {
                button.isDragging = false;
            }, 100);
        };

        // Mouse events
        button.addEventListener('mousedown', startPopoutDrag);
        document.addEventListener('mousemove', doPopoutDrag);
        document.addEventListener('mouseup', endPopoutDrag);

        // Touch events for mobile
        button.addEventListener('touchstart', startPopoutDrag, { passive: false });
        document.addEventListener('touchmove', doPopoutDrag, { passive: false });
        document.addEventListener('touchend', endPopoutDrag);
        document.addEventListener('touchcancel', endPopoutDrag);

        // Add to DOM and store reference
        document.body.appendChild(button);
        popoutButtons[category.key] = button;
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

        // Also initialize pop-out buttons
        createPopoutButtons();
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