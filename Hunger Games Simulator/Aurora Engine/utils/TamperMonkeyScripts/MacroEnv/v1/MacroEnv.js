// ==UserScript==
// @name         Macro Creator & Runner
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Create and run keyboard/mouse macros with keybindings (Logitech-style)
// @author       OtterLogic LLC
// @match        https://*/*
// @run-at       document-end
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_addValueChangeListener
// ==/UserScript==

(async function () {
    'use strict';

    /** ---------- STORAGE KEYS ---------- **/
    const MACROS_STORAGE_KEY = 'macro_env_macros_v1';
    const CONFIG_STORAGE_KEY = 'macro_env_config_v1';

    /** ---------- DEFAULT CONFIG ---------- **/
    const DEFAULT_CONFIG = {
        enabled: true,
        showNotifications: true,
        iconPosition: { x: null, y: null }, // null = use default position
        iconVisible: true,
    };

    /** ---------- STATE ---------- **/
    let config = await loadConfig();
    let macros = await loadMacros();
    let isRecording = false;
    let currentRecording = null;
    let runningMacro = null;

    /** ---------- CONFIG & MACROS MANAGEMENT ---------- **/
    async function loadConfig() {
        const raw = await GM_getValue(CONFIG_STORAGE_KEY, null);
        if (!raw) return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
        try {
            return JSON.parse(raw);
        } catch {
            return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
        }
    }

    async function saveConfig(cfg) {
        try {
            await GM_setValue(CONFIG_STORAGE_KEY, JSON.stringify(cfg));
            config = cfg;
        } catch (e) {
            console.warn('[Macro Env] Failed to save config', e);
        }
    }

    async function loadMacros() {
        const raw = await GM_getValue(MACROS_STORAGE_KEY, null);
        if (!raw) return [];
        try {
            return JSON.parse(raw);
        } catch {
            return [];
        }
    }

    async function saveMacros(m) {
        try {
            await GM_setValue(MACROS_STORAGE_KEY, JSON.stringify(m));
            macros = m;
        } catch (e) {
            console.warn('[Macro Env] Failed to save macros', e);
        }
    }

    /** ---------- MACRO STRUCTURE ---------- **/
    /*
     * Macro = {
     *   id: unique string,
     *   name: string,
     *   keybinding: { key: string, ctrl: bool, shift: bool, alt: bool },
     *   loop: boolean (true = continuous loop, false = run once),
     *   loopDelay: ms (delay between loop iterations, default 100ms),
     *   actions: [
     *     { type: 'keydown', key: string },
     *     { type: 'keyup', key: string },
     *     { type: 'click', x: number, y: number, button: 'left'|'right'|'middle' },
     *     { type: 'mousedown', x: number, y: number, button: string },
     *     { type: 'mouseup', x: number, y: number, button: string },
     *     { type: 'mousemove', x: number, y: number },
     *     { type: 'scroll', deltaY: number },
     *     { type: 'text', value: string },
     *     { type: 'wait', duration: ms },  // Use Wait actions for timing/delays
     *   ]
     * }
     */

    /** ---------- MACRO RECORDING ---------- **/
    function startRecording(macroName) {
        if (isRecording) return;
        isRecording = true;
        currentRecording = {
            id: `macro_${Date.now()}`,
            name: macroName,
            keybinding: null,
            actions: [],
            startTime: Date.now(),
        };
        showNotification(`Recording macro: ${macroName}`, 'info');
    }

    function stopRecording() {
        if (!isRecording) return null;
        isRecording = false;
        const recorded = currentRecording;
        currentRecording = null;
        showNotification(`Recording stopped: ${recorded.name}`, 'success');
        return recorded;
    }

    function recordAction(action) {
        if (!isRecording || !currentRecording) return;
        const delay = Date.now() - currentRecording.startTime;
        
        // Add wait action if there was a delay since last action
        if (delay > 50) { // Only add wait if delay is significant (>50ms)
            currentRecording.actions.push({ type: 'wait', duration: delay });
        }
        
        currentRecording.actions.push(action);
        currentRecording.startTime = Date.now();
    }

    /** ---------- EVENT CAPTURING ---------- **/
    let recordingListeners = {
        keydown: null,
        keyup: null,
        mousedown: null,
        mouseup: null,
        mousemove: null,
        wheel: null,
    };

    function enableRecordingListeners() {
        // List of special keys to ignore during recording
        const ignoredKeys = ['Meta', 'OS', 'Win', 'Command', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'];
        
        recordingListeners.keydown = (e) => {
            if (e.key === 'Escape' && isRecording) {
                stopRecording();
                return;
            }
            // Skip system keys
            if (ignoredKeys.includes(e.key)) return;
            recordAction({ type: 'keydown', key: e.key, code: e.code });
        };

        recordingListeners.keyup = (e) => {
            recordAction({ type: 'keyup', key: e.key, code: e.code });
        };

        recordingListeners.mousedown = (e) => {
            const button = ['left', 'middle', 'right'][e.button] || 'left';
            recordAction({ type: 'mousedown', x: e.clientX, y: e.clientY, button });
        };

        recordingListeners.mouseup = (e) => {
            const button = ['left', 'middle', 'right'][e.button] || 'left';
            recordAction({ type: 'mouseup', x: e.clientX, y: e.clientY, button });
        };

        let lastMouseMove = 0;
        recordingListeners.mousemove = (e) => {
            // Throttle mousemove events to every 100ms
            const now = Date.now();
            if (now - lastMouseMove < 100) return;
            lastMouseMove = now;
            recordAction({ type: 'mousemove', x: e.clientX, y: e.clientY });
        };

        recordingListeners.wheel = (e) => {
            recordAction({ type: 'scroll', deltaY: e.deltaY });
        };

        document.addEventListener('keydown', recordingListeners.keydown, true);
        document.addEventListener('keyup', recordingListeners.keyup, true);
        document.addEventListener('mousedown', recordingListeners.mousedown, true);
        document.addEventListener('mouseup', recordingListeners.mouseup, true);
        document.addEventListener('mousemove', recordingListeners.mousemove, true);
        document.addEventListener('wheel', recordingListeners.wheel, true);
    }

    function disableRecordingListeners() {
        if (recordingListeners.keydown) {
            document.removeEventListener('keydown', recordingListeners.keydown, true);
            document.removeEventListener('keyup', recordingListeners.keyup, true);
            document.removeEventListener('mousedown', recordingListeners.mousedown, true);
            document.removeEventListener('mouseup', recordingListeners.mouseup, true);
            document.removeEventListener('mousemove', recordingListeners.mousemove, true);
            document.removeEventListener('wheel', recordingListeners.wheel, true);
            recordingListeners = {
                keydown: null,
                keyup: null,
                mousedown: null,
                mouseup: null,
                mousemove: null,
                wheel: null,
            };
        }
    }

    /** ---------- MACRO PLAYBACK ---------- **/
    async function playMacro(macro) {
        if (runningMacro) {
            showNotification('Another macro is already running', 'warning');
            return;
        }
        runningMacro = macro.id;
        const loopEnabled = macro.loop || false;
        const loopDelay = macro.loopDelay || 100;
        
        console.log('[Macro] Starting playback:', macro.name, `(${macro.actions.length} actions)`);
        showNotification(`Running macro: ${macro.name}${loopEnabled ? ' (looping)' : ''}`, 'info');

        try {
            do {
                for (const action of macro.actions) {
                    if (runningMacro !== macro.id) break; // Stopped

                    // Execute action (Wait actions handle their own timing)
                    await executeAction(action);
                }
                
                // If looping, wait before next iteration
                if (loopEnabled && runningMacro === macro.id) {
                    await sleep(loopDelay);
                }
                
            } while (loopEnabled && runningMacro === macro.id);
            
            if (runningMacro === macro.id) {
                showNotification(`Macro completed: ${macro.name}`, 'success');
            }
        } catch (err) {
            console.error('[Macro Env] Playback error:', err);
            showNotification(`Macro error: ${err.message}`, 'error');
        } finally {
            runningMacro = null;
        }
    }

    function stopMacro() {
        if (runningMacro) {
            showNotification('Macro stopped', 'warning');
            runningMacro = null;
        }
    }

    async function executeAction(action) {
        console.log('[Macro] Executing:', action.type, action);
        switch (action.type) {
            case 'keydown':
            case 'keyup':
                simulateKeyEvent(action.type, action.key, action.code);
                break;
            case 'mousedown':
            case 'mouseup':
            case 'click':
                simulateMouseEvent(action.type, action.x, action.y, action.button);
                break;
            case 'mousemove':
                simulateMouseMove(action.x, action.y);
                break;
            case 'scroll':
                simulateScroll(action.deltaY);
                break;
            case 'text':
                simulateTextInput(action.value);
                break;
            case 'wait':
                await sleep(action.duration);
                break;
            default:
                console.warn('[Macro Env] Unknown action type:', action.type);
        }
    }

    /** ---------- EVENT SIMULATION ---------- **/
    // Track modifier key states
    const modifierState = {
        Meta: false,
        Control: false,
        Shift: false,
        Alt: false
    };
    
    function simulateKeyEvent(type, key, code) {
        // Map common keys to proper codes
        const keyCodeMap = {
            'Meta': 'MetaLeft',
            'Control': 'ControlLeft',
            'Shift': 'ShiftLeft',
            'Alt': 'AltLeft',
            'Enter': 'Enter',
            'Tab': 'Tab',
            'Escape': 'Escape',
            'Space': 'Space'
        };
        
        const properCode = keyCodeMap[key] || code || (key.length === 1 ? `Key${key.toUpperCase()}` : key);
        
        // Update modifier state
        if (type === 'keydown' && modifierState.hasOwnProperty(key)) {
            modifierState[key] = true;
        } else if (type === 'keyup' && modifierState.hasOwnProperty(key)) {
            modifierState[key] = false;
        }
        
        const event = new KeyboardEvent(type, {
            key: key,
            code: properCode,
            keyCode: getKeyCode(key),
            which: getKeyCode(key),
            bubbles: true,
            cancelable: true,
            metaKey: modifierState.Meta || key === 'Meta',
            ctrlKey: modifierState.Control || key === 'Control',
            shiftKey: modifierState.Shift || key === 'Shift',
            altKey: modifierState.Alt || key === 'Alt'
        });
        
        console.log(`[Macro] ${type}: ${key} (${properCode}) - Modifiers: Ctrl=${event.ctrlKey} Shift=${event.shiftKey} Alt=${event.altKey} Meta=${event.metaKey}`);
        
        // Try multiple dispatch targets
        const targets = [
            document.activeElement,
            document.body,
            document,
            window
        ];
        
        let dispatched = false;
        for (const target of targets) {
            if (target) {
                try {
                    target.dispatchEvent(event);
                    dispatched = true;
                } catch (e) {
                    console.warn('[Macro] Failed to dispatch to', target, e);
                }
            }
        }
        
        if (!dispatched) {
            console.error('[Macro] Failed to dispatch event:', type, key);
        }
    }
    
    function getKeyCode(key) {
        const keyCodes = {
            'Enter': 13,
            'Tab': 9,
            'Escape': 27,
            'Space': 32,
            'Backspace': 8,
            'Delete': 46,
            'ArrowUp': 38,
            'ArrowDown': 40,
            'ArrowLeft': 37,
            'ArrowRight': 39,
            'Home': 36,
            'End': 35,
            'PageUp': 33,
            'PageDown': 34,
            'Meta': 91,
            'Control': 17,
            'Shift': 16,
            'Alt': 18,
            'CapsLock': 20
        };
        
        if (keyCodes[key]) return keyCodes[key];
        if (key.length === 1) return key.toUpperCase().charCodeAt(0);
        return 0;
    }

    function simulateMouseEvent(type, x, y, button) {
        const buttonNum = { left: 0, middle: 1, right: 2 }[button] || 0;
        const event = new MouseEvent(type, {
            clientX: x,
            clientY: y,
            button: buttonNum,
            bubbles: true,
            cancelable: true,
        });
        const element = document.elementFromPoint(x, y);
        if (element) {
            element.dispatchEvent(event);
        }
    }

    function simulateMouseMove(x, y) {
        const event = new MouseEvent('mousemove', {
            clientX: x,
            clientY: y,
            bubbles: true,
            cancelable: true,
        });
        document.dispatchEvent(event);
    }

    function simulateScroll(deltaY) {
        window.scrollBy({ top: deltaY, behavior: 'instant' });
    }

    function simulateTextInput(text) {
        const activeElement = document.activeElement;
        console.log('[Macro] Typing text:', text, 'into', activeElement?.tagName);
        
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable)) {
            // For input/textarea
            if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
                const start = activeElement.selectionStart;
                const end = activeElement.selectionEnd;
                const currentValue = activeElement.value;
                activeElement.value = currentValue.substring(0, start) + text + currentValue.substring(end);
                activeElement.selectionStart = activeElement.selectionEnd = start + text.length;
                
                // Trigger events
                activeElement.dispatchEvent(new Event('input', { bubbles: true }));
                activeElement.dispatchEvent(new Event('change', { bubbles: true }));
            }
            // For contenteditable
            else if (activeElement.isContentEditable) {
                document.execCommand('insertText', false, text);
            }
        } else {
            console.warn('[Macro] No suitable target for text input');
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /** ---------- KEYBINDING HANDLER ---------- **/
    function setupKeybindingListener() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+M = Toggle icon visibility
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'm') {
                e.preventDefault();
                const container = document.querySelector('[title*="Macro Creator & Runner"]')?.parentElement;
                if (container) {
                    config.iconVisible = !config.iconVisible;
                    container.style.display = config.iconVisible ? 'block' : 'none';
                    saveConfig(config);
                    if (config.iconVisible) {
                        showNotification('Macro icon shown', 'info');
                    }
                }
                return;
            }
            
            if (!config.enabled) return;

            // Check if any macro matches this keybinding
            for (const macro of macros) {
                if (!macro.keybinding) continue;

                const kb = macro.keybinding;
                if (
                    e.key.toLowerCase() === kb.key.toLowerCase() &&
                    e.ctrlKey === !!kb.ctrl &&
                    e.shiftKey === !!kb.shift &&
                    e.altKey === !!kb.alt
                ) {
                    e.preventDefault();
                    e.stopPropagation();
                    playMacro(macro);
                    break;
                }
            }
        }, true);
    }

    /** ---------- NOTIFICATION SYSTEM ---------- **/
    function showNotification(message, type = 'info') {
        if (!config.showNotifications) return;

        const notification = document.createElement('div');
        const colors = {
            info: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            error: '#dc3545',
        };

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2147483647;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            font-size: 14px;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Add animation styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    /** ---------- UI SETUP ---------- **/
    function createUI() {
        // Main container (positioned to left of BadOpReporter icon)
        const container = document.createElement('div');
        const iconPos = config.iconPosition;
        const hasCustomPosition = iconPos.x !== null && iconPos.y !== null;
        
        container.style.cssText = `
            position: fixed;
            ${hasCustomPosition ? `left: ${iconPos.x}px; top: ${iconPos.y}px;` : 'top: 0; left: calc(60% - 60px); transform: translateX(-50%);'}
            z-index: 2147483646;
            font-family: Arial, sans-serif;
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
        launcher.textContent = '⚡';
        launcher.title = 'Macro Creator & Runner (Drag to move, Ctrl+Shift+M to hide/show)';
        launcher.style.cssText = `
            font-size: 20px;
            padding: 8px 12px;
            background: #6c2bd9;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
            z-index: 2147483645;
            background: rgba(0,0,0,0.4);
            display: none;
        `;
        document.body.appendChild(overlay);

        // Main Panel
        const panel = document.createElement('div');
        panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 600px;
            max-height: 80vh;
            background: #2a2a2a;
            color: #e0e0e0;
            border: 2px solid #6c2bd9;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            z-index: 2147483646;
            display: none;
            overflow-y: auto;
        `;
        document.body.appendChild(panel);

        function showPanel() {
            panel.style.display = 'block';
            overlay.style.display = 'block';
            refreshMacroList();
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

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #6c2bd9;
        `;

        const title = document.createElement('div');
        title.textContent = '⚡ Macro Creator & Runner';
        title.style.cssText = `font-weight: bold; font-size: 18px; color: #6c2bd9;`;

        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.cssText = `
            padding: 4px 10px;
            background: #444;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        `;
        closeBtn.onclick = hidePanel;

        header.appendChild(title);
        header.appendChild(closeBtn);
        panel.appendChild(header);

        // Settings row
        const settingsRow = document.createElement('div');
        settingsRow.style.cssText = `
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            padding: 10px;
            background: #333;
            border-radius: 6px;
        `;

        const enabledLabel = document.createElement('label');
        enabledLabel.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        `;

        const enabledCheckbox = document.createElement('input');
        enabledCheckbox.type = 'checkbox';
        enabledCheckbox.checked = config.enabled;
        enabledCheckbox.onchange = async () => {
            config.enabled = enabledCheckbox.checked;
            await saveConfig(config);
            showNotification(config.enabled ? 'Macros enabled' : 'Macros disabled', 'info');
        };

        const enabledText = document.createElement('span');
        enabledText.textContent = 'Enable Macros';

        enabledLabel.appendChild(enabledCheckbox);
        enabledLabel.appendChild(enabledText);

        const notifLabel = document.createElement('label');
        notifLabel.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        `;

        const notifCheckbox = document.createElement('input');
        notifCheckbox.type = 'checkbox';
        notifCheckbox.checked = config.showNotifications;
        notifCheckbox.onchange = async () => {
            config.showNotifications = notifCheckbox.checked;
            await saveConfig(config);
        };

        const notifText = document.createElement('span');
        notifText.textContent = 'Show Notifications';

        notifLabel.appendChild(notifCheckbox);
        notifLabel.appendChild(notifText);

        settingsRow.appendChild(enabledLabel);
        settingsRow.appendChild(notifLabel);
        panel.appendChild(settingsRow);
        
        // Icon controls row
        const iconControlsRow = document.createElement('div');
        iconControlsRow.style.cssText = `
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            padding: 10px;
            background: #333;
            border-radius: 6px;
            align-items: center;
        `;
        
        const iconControlsLabel = document.createElement('span');
        iconControlsLabel.textContent = 'Icon:';
        iconControlsLabel.style.cssText = `font-size: 12px; color: #888;`;
        
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
            showNotification('Position reset - reload page to apply', 'info');
        };
        
        const hideHint = document.createElement('span');
        hideHint.textContent = 'Ctrl+Shift+M to hide/show';
        hideHint.style.cssText = `font-size: 11px; color: #888; font-style: italic;`;
        
        iconControlsRow.appendChild(iconControlsLabel);
        iconControlsRow.appendChild(resetPosBtn);
        iconControlsRow.appendChild(hideHint);
        panel.appendChild(iconControlsRow);

        // Action buttons
        const actionsRow = document.createElement('div');
        actionsRow.style.cssText = `
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        `;

        const newMacroBtn = document.createElement('button');
        newMacroBtn.textContent = '+ New Macro';
        newMacroBtn.style.cssText = `
            padding: 10px 20px;
            background: #6c2bd9;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        `;
        newMacroBtn.onclick = () => showNewMacroDialog();

        const importBtn = document.createElement('button');
        importBtn.textContent = '📥 Import';
        importBtn.style.cssText = `
            padding: 10px 20px;
            background: #17a2b8;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        `;
        importBtn.onclick = () => importMacros();

        const exportBtn = document.createElement('button');
        exportBtn.textContent = '📤 Export';
        exportBtn.style.cssText = `
            padding: 10px 20px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        `;
        exportBtn.onclick = () => exportMacros();

        actionsRow.appendChild(newMacroBtn);
        actionsRow.appendChild(importBtn);
        actionsRow.appendChild(exportBtn);
        panel.appendChild(actionsRow);

        // Macro list container
        const macroList = document.createElement('div');
        macroList.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        panel.appendChild(macroList);

        // Refresh macro list
        function refreshMacroList() {
            while (macroList.firstChild) {
                macroList.removeChild(macroList.firstChild);
            }

            if (macros.length === 0) {
                const emptyMsg = document.createElement('div');
                emptyMsg.textContent = 'No macros yet. Create one to get started!';
                emptyMsg.style.cssText = `
                    text-align: center;
                    padding: 40px;
                    color: #888;
                    font-style: italic;
                `;
                macroList.appendChild(emptyMsg);
                return;
            }

            for (const macro of macros) {
                const macroCard = createMacroCard(macro);
                macroList.appendChild(macroCard);
            }
        }

        function createMacroCard(macro) {
            const card = document.createElement('div');
            card.style.cssText = `
                background: #333;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #6c2bd9;
            `;

            const cardHeader = document.createElement('div');
            cardHeader.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            `;

            const macroName = document.createElement('div');
            macroName.textContent = macro.name;
            macroName.style.cssText = `font-weight: bold; font-size: 16px;`;

            const cardButtons = document.createElement('div');
            cardButtons.style.cssText = `display: flex; gap: 8px;`;

            const playBtn = document.createElement('button');
            playBtn.textContent = '▶';
            playBtn.title = 'Play';
            playBtn.style.cssText = `
                padding: 4px 10px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            playBtn.onclick = () => playMacro(macro);

            const editBtn = document.createElement('button');
            editBtn.textContent = '✏';
            editBtn.title = 'Edit';
            editBtn.style.cssText = `
                padding: 4px 10px;
                background: #ffc107;
                color: #333;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            editBtn.onclick = () => showEditMacroDialog(macro);

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '🗑';
            deleteBtn.title = 'Delete';
            deleteBtn.style.cssText = `
                padding: 4px 10px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            deleteBtn.onclick = async () => {
                if (confirm(`Delete macro "${macro.name}"?`)) {
                    macros = macros.filter(m => m.id !== macro.id);
                    await saveMacros(macros);
                    refreshMacroList();
                }
            };

            cardButtons.appendChild(playBtn);
            cardButtons.appendChild(editBtn);
            cardButtons.appendChild(deleteBtn);

            cardHeader.appendChild(macroName);
            cardHeader.appendChild(cardButtons);
            card.appendChild(cardHeader);

            // Keybinding display
            if (macro.keybinding) {
                const kb = macro.keybinding;
                const kbDisplay = document.createElement('div');
                kbDisplay.style.cssText = `
                    display: inline-block;
                    padding: 4px 8px;
                    background: #444;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-bottom: 8px;
                `;
                const parts = [];
                if (kb.ctrl) parts.push('Ctrl');
                if (kb.shift) parts.push('Shift');
                if (kb.alt) parts.push('Alt');
                parts.push(kb.key.toUpperCase());
                kbDisplay.textContent = `🎹 ${parts.join(' + ')}`;
                card.appendChild(kbDisplay);
            }

            // Action count and loop status
            const infoRow = document.createElement('div');
            infoRow.style.cssText = `display: flex; gap: 10px; align-items: center;`;
            
            const actionCount = document.createElement('div');
            actionCount.textContent = `${macro.actions.length} action${macro.actions.length !== 1 ? 's' : ''}`;
            actionCount.style.cssText = `font-size: 12px; color: #888;`;
            infoRow.appendChild(actionCount);
            
            if (macro.loop) {
                const loopBadge = document.createElement('div');
                loopBadge.textContent = '🔄 Loop';
                loopBadge.style.cssText = `
                    font-size: 10px;
                    padding: 2px 6px;
                    background: #6c2bd9;
                    border-radius: 3px;
                    color: white;
                `;
                infoRow.appendChild(loopBadge);
            }
            
            card.appendChild(infoRow);

            return card;
        }

        // New/Edit Macro Dialog
        function showNewMacroDialog() {
            const dialog = createMacroDialog(null);
            document.body.appendChild(dialog);
        }

        function showEditMacroDialog(macro) {
            const dialog = createMacroDialog(macro);
            document.body.appendChild(dialog);
        }

        function createMacroDialog(existingMacro) {
            const dialogOverlay = document.createElement('div');
            dialogOverlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 2147483647;
                background: rgba(0,0,0,0.6);
                display: flex;
                justify-content: center;
                align-items: center;
            `;

            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: #2a2a2a;
                color: #e0e0e0;
                padding: 25px;
                border-radius: 8px;
                border: 2px solid #6c2bd9;
                width: 450px;
                max-height: 80vh;
                overflow-y: auto;
            `;

            const dialogTitle = document.createElement('h2');
            dialogTitle.textContent = existingMacro ? 'Edit Macro' : 'New Macro';
            dialogTitle.style.cssText = `margin: 0 0 20px 0; color: #6c2bd9;`;
            dialog.appendChild(dialogTitle);

            // Name input
            const nameLabel = document.createElement('div');
            nameLabel.textContent = 'Macro Name:';
            nameLabel.style.cssText = `margin-bottom: 8px; font-weight: bold;`;
            dialog.appendChild(nameLabel);

            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.value = existingMacro ? existingMacro.name : '';
            nameInput.placeholder = 'Enter macro name';
            nameInput.style.cssText = `
                width: 100%;
                padding: 8px;
                margin-bottom: 15px;
                background: #333;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                box-sizing: border-box;
            `;
            dialog.appendChild(nameInput);

            // Keybinding
            const kbLabel = document.createElement('div');
            kbLabel.textContent = 'Keybinding (optional):';
            kbLabel.style.cssText = `margin-bottom: 8px; font-weight: bold;`;
            dialog.appendChild(kbLabel);

            const kbContainer = document.createElement('div');
            kbContainer.style.cssText = `
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
                align-items: center;
            `;

            const kbInput = document.createElement('input');
            kbInput.type = 'text';
            kbInput.placeholder = 'Press key...';
            kbInput.readOnly = true;
            kbInput.style.cssText = `
                flex: 1;
                padding: 8px;
                background: #333;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
            `;

            let capturedKeybinding = existingMacro?.keybinding || null;
            if (capturedKeybinding) {
                const parts = [];
                if (capturedKeybinding.ctrl) parts.push('Ctrl');
                if (capturedKeybinding.shift) parts.push('Shift');
                if (capturedKeybinding.alt) parts.push('Alt');
                parts.push(capturedKeybinding.key.toUpperCase());
                kbInput.value = parts.join(' + ');
            }

            kbInput.addEventListener('keydown', (e) => {
                e.preventDefault();
                if (e.key === 'Escape') {
                    kbInput.value = '';
                    capturedKeybinding = null;
                    return;
                }
                capturedKeybinding = {
                    key: e.key,
                    ctrl: e.ctrlKey,
                    shift: e.shiftKey,
                    alt: e.altKey,
                };
                const parts = [];
                if (e.ctrlKey) parts.push('Ctrl');
                if (e.shiftKey) parts.push('Shift');
                if (e.altKey) parts.push('Alt');
                parts.push(e.key.toUpperCase());
                kbInput.value = parts.join(' + ');
            });

            const clearKbBtn = document.createElement('button');
            clearKbBtn.textContent = 'Clear';
            clearKbBtn.style.cssText = `
                padding: 8px 12px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            clearKbBtn.onclick = () => {
                kbInput.value = '';
                capturedKeybinding = null;
            };

            kbContainer.appendChild(kbInput);
            kbContainer.appendChild(clearKbBtn);
            dialog.appendChild(kbContainer);

            // Loop settings
            const loopLabel = document.createElement('div');
            loopLabel.textContent = 'Playback Mode:';
            loopLabel.style.cssText = `margin-bottom: 8px; font-weight: bold;`;
            dialog.appendChild(loopLabel);

            const loopContainer = document.createElement('div');
            loopContainer.style.cssText = `
                display: flex;
                gap: 15px;
                margin-bottom: 15px;
                padding: 10px;
                background: #333;
                border-radius: 4px;
                align-items: center;
            `;

            const loopCheckboxLabel = document.createElement('label');
            loopCheckboxLabel.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            `;

            const loopCheckbox = document.createElement('input');
            loopCheckbox.type = 'checkbox';
            loopCheckbox.checked = existingMacro?.loop || false;

            const loopText = document.createElement('span');
            loopText.textContent = '🔄 Loop continuously';

            loopCheckboxLabel.appendChild(loopCheckbox);
            loopCheckboxLabel.appendChild(loopText);

            const loopDelayLabel = document.createElement('span');
            loopDelayLabel.textContent = 'Loop delay:';
            loopDelayLabel.style.cssText = `font-size: 12px;`;

            const loopDelayInput = document.createElement('input');
            loopDelayInput.type = 'number';
            loopDelayInput.value = existingMacro?.loopDelay || 100;
            loopDelayInput.placeholder = 'ms';
            loopDelayInput.style.cssText = `
                width: 80px;
                padding: 4px 8px;
                background: #444;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
            `;

            const loopDelayMs = document.createElement('span');
            loopDelayMs.textContent = 'ms';
            loopDelayMs.style.cssText = `font-size: 12px;`;

            loopContainer.appendChild(loopCheckboxLabel);
            loopContainer.appendChild(loopDelayLabel);
            loopContainer.appendChild(loopDelayInput);
            loopContainer.appendChild(loopDelayMs);
            dialog.appendChild(loopContainer);

            // Recording section
            const recordLabel = document.createElement('div');
            recordLabel.textContent = 'Actions:';
            recordLabel.style.cssText = `margin-bottom: 8px; font-weight: bold;`;
            dialog.appendChild(recordLabel);

            const recordBtnContainer = document.createElement('div');
            recordBtnContainer.style.cssText = `
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            `;

            const recordBtn = document.createElement('button');
            recordBtn.textContent = '🔴 Record';
            recordBtn.style.cssText = `
                flex: 1;
                padding: 10px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
            `;

            let localRecording = existingMacro ? { ...existingMacro } : null;

            recordBtn.onclick = () => {
                if (isRecording) {
                    localRecording = stopRecording();
                    disableRecordingListeners();
                    recordBtn.textContent = '🔴 Record';
                    recordBtn.style.background = '#dc3545';
                    refreshActionList();
                } else {
                    const name = nameInput.value.trim() || 'Unnamed';
                    startRecording(name);
                    enableRecordingListeners();
                    recordBtn.textContent = '⏹ Stop Recording (ESC)';
                    recordBtn.style.background = '#ffc107';
                }
            };

            const clearActionsBtn = document.createElement('button');
            clearActionsBtn.textContent = 'Clear Actions';
            clearActionsBtn.style.cssText = `
                padding: 10px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            clearActionsBtn.onclick = () => {
                if (localRecording) {
                    localRecording.actions = [];
                    refreshActionList();
                }
            };

            recordBtnContainer.appendChild(recordBtn);
            recordBtnContainer.appendChild(clearActionsBtn);
            dialog.appendChild(recordBtnContainer);

            const actionCountDisplay = document.createElement('div');
            actionCountDisplay.style.cssText = `
                margin-bottom: 10px;
                padding: 8px;
                background: #333;
                border-radius: 4px;
                font-size: 12px;
            `;
            const actionCount = localRecording?.actions.length || 0;
            actionCountDisplay.textContent = `${actionCount} action${actionCount !== 1 ? 's' : ''} recorded`;
            dialog.appendChild(actionCountDisplay);

            // Manual action creation
            const manualSection = document.createElement('div');
            manualSection.style.cssText = `
                margin-bottom: 15px;
                padding: 10px;
                background: #333;
                border-radius: 4px;
            `;

            const manualTitle = document.createElement('div');
            manualTitle.textContent = 'Add Action Manually:';
            manualTitle.style.cssText = `margin-bottom: 8px; font-weight: bold; font-size: 12px;`;
            manualSection.appendChild(manualTitle);

            const manualForm = document.createElement('div');
            manualForm.style.cssText = `display: flex; gap: 8px; flex-wrap: wrap;`;

            const actionTypeSelect = document.createElement('select');
            actionTypeSelect.style.cssText = `
                padding: 6px;
                background: #444;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
            `;
            const actionTypes = [
                { value: 'keydown', label: 'Key Down' },
                { value: 'keyup', label: 'Key Up' },
                { value: 'keypress', label: 'Key Press (down+up)' },
                { value: 'keyseq', label: 'Key Sequence' },
                { value: 'click', label: 'Click' },
                { value: 'mousedown', label: 'Mouse Down' },
                { value: 'mouseup', label: 'Mouse Up' },
                { value: 'text', label: 'Type Text' },
                { value: 'wait', label: 'Wait' },
                { value: 'scroll', label: 'Scroll' },
            ];
            for (const type of actionTypes) {
                const option = document.createElement('option');
                option.value = type.value;
                option.textContent = type.label;
                actionTypeSelect.appendChild(option);
            }

            // Primary value selector (preset dropdown)
            const valuePresetSelect = document.createElement('select');
            valuePresetSelect.style.cssText = `
                flex: 1;
                padding: 6px;
                background: #444;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                min-width: 150px;
            `;
            
            // Preset options for different action types
            const presetGroups = {
                key: [
                    { value: 'custom', label: '-- Custom Key --' },
                    { value: '', label: '--- Navigation ---', disabled: true },
                    { value: 'Enter', label: 'Enter' },
                    { value: 'Tab', label: 'Tab' },
                    { value: 'Escape', label: 'Escape' },
                    { value: 'Backspace', label: 'Backspace' },
                    { value: 'Delete', label: 'Delete' },
                    { value: 'Space', label: 'Space' },
                    { value: 'ArrowUp', label: '↑ Arrow Up' },
                    { value: 'ArrowDown', label: '↓ Arrow Down' },
                    { value: 'ArrowLeft', label: '← Arrow Left' },
                    { value: 'ArrowRight', label: '→ Arrow Right' },
                    { value: 'Home', label: 'Home' },
                    { value: 'End', label: 'End' },
                    { value: 'PageUp', label: 'Page Up' },
                    { value: 'PageDown', label: 'Page Down' },
                    { value: '', label: '--- Modifiers ---', disabled: true },
                    { value: 'Control', label: 'Ctrl' },
                    { value: 'Shift', label: 'Shift' },
                    { value: 'Alt', label: 'Alt' },
                    { value: 'Meta', label: '⊞ Windows/Meta' },
                    { value: 'CapsLock', label: 'Caps Lock' },
                    { value: '', label: '--- Function Keys ---', disabled: true },
                    { value: 'F1', label: 'F1' },
                    { value: 'F2', label: 'F2' },
                    { value: 'F3', label: 'F3' },
                    { value: 'F4', label: 'F4' },
                    { value: 'F5', label: 'F5' },
                    { value: 'F6', label: 'F6' },
                    { value: 'F7', label: 'F7' },
                    { value: 'F8', label: 'F8' },
                    { value: 'F9', label: 'F9' },
                    { value: 'F10', label: 'F10' },
                    { value: 'F11', label: 'F11' },
                    { value: 'F12', label: 'F12' },
                ],
                mouse: [
                    { value: 'leftclick', label: '🖱️ Left Click' },
                    { value: 'rightclick', label: '🖱️ Right Click' },
                    { value: 'middleclick', label: '🖱️ Middle Click' },
                    { value: 'doubleclick', label: '🖱️ Double Click' },
                ],
                text: [
                    { value: 'custom', label: '-- Enter Text --' },
                ]
            };
            
            function updatePresetOptions(type) {
                // Clear existing options
                while (valuePresetSelect.firstChild) {
                    valuePresetSelect.removeChild(valuePresetSelect.firstChild);
                }
                
                let presets = [];
                if (type === 'keydown' || type === 'keyup' || type === 'keypress' || type === 'keyseq') {
                    presets = presetGroups.key;
                } else if (type === 'click' || type === 'mousedown' || type === 'mouseup') {
                    presets = presetGroups.mouse;
                } else if (type === 'text') {
                    presets = presetGroups.text;
                } else {
                    // For other types, show custom input
                    presets = [{ value: 'custom', label: '-- Custom Value --' }];
                }
                
                for (const preset of presets) {
                    const option = document.createElement('option');
                    option.value = preset.value;
                    option.textContent = preset.label;
                    if (preset.disabled) {
                        option.disabled = true;
                        option.style.fontWeight = 'bold';
                        option.style.color = '#888';
                    }
                    valuePresetSelect.appendChild(option);
                }
            }

            // Custom input (only shown when "custom" is selected)
            const customValueInput = document.createElement('input');
            customValueInput.type = 'text';
            customValueInput.placeholder = 'Enter custom value';
            customValueInput.style.cssText = `
                flex: 1;
                padding: 6px;
                background: #444;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                min-width: 120px;
                display: none;
            `;

            // Show/hide custom input based on preset selection
            valuePresetSelect.onchange = () => {
                const type = actionTypeSelect.value;
                if (valuePresetSelect.value === 'custom') {
                    customValueInput.style.display = 'block';
                    if (type === 'keyseq') {
                        customValueInput.placeholder = 'e.g., shift+w_r_3 or ctrl+a';
                    } else if (type === 'keydown' || type === 'keyup' || type === 'keypress') {
                        customValueInput.placeholder = 'e.g., Enter, a, 1';
                    } else if (type === 'text') {
                        customValueInput.placeholder = 'Text to type';
                    } else if (type === 'scroll') {
                        customValueInput.placeholder = 'e.g., 100';
                    } else if (type === 'wait') {
                        customValueInput.placeholder = 'e.g., 1000';
                    } else {
                        customValueInput.placeholder = 'Enter value';
                    }
                } else {
                    customValueInput.style.display = 'none';
                }
            };

            // Update preset options when action type changes
            actionTypeSelect.onchange = () => {
                const type = actionTypeSelect.value;
                updatePresetOptions(type);
                // Always reset to first option and hide custom input when changing types
                valuePresetSelect.value = valuePresetSelect.options[0]?.value || 'custom';
                // Trigger the preset change handler to show/hide custom input correctly
                valuePresetSelect.onchange();
            };
            
            // Initialize with first action type
            updatePresetOptions(actionTypeSelect.value);
            // Trigger the change handler to properly show custom input if needed
            valuePresetSelect.onchange();

            const addActionBtn = document.createElement('button');
            addActionBtn.textContent = '+ Add';
            addActionBtn.style.cssText = `
                padding: 6px 12px;
                background: #6c2bd9;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            `;
            addActionBtn.onclick = () => {
                const type = actionTypeSelect.value;
                const presetValue = valuePresetSelect.value;
                const customValue = customValueInput.value.trim();
                const value = (presetValue === 'custom') ? customValue : presetValue;

                if (!localRecording) {
                    localRecording = {
                        id: existingMacro?.id || `macro_${Date.now()}`,
                        name: nameInput.value.trim() || 'Unnamed',
                        keybinding: null,
                        actions: [],
                    };
                }

                // Handle preset mouse clicks
                if (type === 'click' || type === 'mousedown' || type === 'mouseup') {
                    const buttonMap = {
                        'leftclick': 'left',
                        'rightclick': 'right',
                        'middleclick': 'middle',
                        'doubleclick': 'left'
                    };
                    
                    if (buttonMap[value]) {
                        const clickType = type === 'click' ? 'click' : type;
                        localRecording.actions.push({
                            type: clickType,
                            x: 0,
                            y: 0,
                            button: buttonMap[value]
                        });
                        
                        // Add second click for double click with small wait
                        if (value === 'doubleclick') {
                            localRecording.actions.push({
                                type: 'wait',
                                duration: 50
                            });
                            localRecording.actions.push({
                                type: clickType,
                                x: 0,
                                y: 0,
                                button: 'left'
                            });
                        }
                        
                        customValueInput.value = '';
                        valuePresetSelect.value = valuePresetSelect.options[0]?.value;
                        refreshActionList();
                        return;
                    }
                }
                
                // Handle key sequence: modifier+key_key_key
                if (type === 'keyseq') {
                    if (!value) {
                        alert('Please enter a key sequence (e.g., shift+w_r_3)');
                        return;
                    }
                    
                    // Parse sequence: modifier+key1_key2_key3
                    let modifier = null;
                    let keys = [];
                    
                    if (value.includes('+')) {
                        const parts = value.split('+');
                        modifier = parts[0].toLowerCase();
                        const keysPart = parts.slice(1).join('+');
                        keys = keysPart.split('_').map(k => k.trim()).filter(k => k);
                    } else {
                        keys = value.split('_').map(k => k.trim()).filter(k => k);
                    }
                    
                    if (keys.length === 0) {
                        alert('No keys found in sequence');
                        return;
                    }
                    
                    // Add modifier down if present
                    if (modifier) {
                        const modKey = modifier === 'ctrl' ? 'Control' : 
                                      modifier === 'win' || modifier === 'windows' ? 'Meta' :
                                      modifier.charAt(0).toUpperCase() + modifier.slice(1);
                        localRecording.actions.push({
                            type: 'keydown',
                            key: modKey,
                            code: modKey
                        });
                    }
                    
                    // Add each key press (down + up)
                    for (let i = 0; i < keys.length; i++) {
                        const key = keys[i];
                        localRecording.actions.push({
                            type: 'keydown',
                            key: key,
                            code: key
                        });
                        localRecording.actions.push({
                            type: 'keyup',
                            key: key,
                            code: key
                        });
                    }
                    
                    // Add modifier up if present
                    if (modifier) {
                        const modKey = modifier === 'ctrl' ? 'Control' : 
                                      modifier === 'win' || modifier === 'windows' ? 'Meta' :
                                      modifier.charAt(0).toUpperCase() + modifier.slice(1);
                        localRecording.actions.push({
                            type: 'keyup',
                            key: modKey,
                            code: modKey
                        });
                    }
                    
                    customValueInput.value = '';
                    valuePresetSelect.value = valuePresetSelect.options[0]?.value;
                    refreshActionList();
                    return;
                }

                // Handle key press (both down and up)
                if (type === 'keypress') {
                    if (!value) {
                        alert('Please enter a key name');
                        return;
                    }
                    localRecording.actions.push({
                        type: 'keydown',
                        key: value,
                        code: value
                    });
                    localRecording.actions.push({
                        type: 'keyup',
                        key: value,
                        code: value
                    });
                    customValueInput.value = '';
                    valuePresetSelect.value = valuePresetSelect.options[0]?.value;
                    refreshActionList();
                    return;
                }

                let action = { type };

                switch (type) {
                    case 'keydown':
                    case 'keyup':
                        if (!value) {
                            alert('Please enter a key name');
                            return;
                        }
                        action.key = value;
                        action.code = value;
                        break;
                    case 'text':
                        if (!value) {
                            alert('Please enter text to type');
                            return;
                        }
                        action.value = value;
                        break;
                    case 'click':
                    case 'mousedown':
                    case 'mouseup':
                        action.x = 0;
                        action.y = 0;
                        action.button = 'left';
                        break;
                    case 'scroll':
                        action.deltaY = parseInt(value) || 100;
                        break;
                    case 'wait':
                        action.duration = parseInt(value) || 1000;
                        break;
                }

                localRecording.actions.push(action);
                customValueInput.value = '';
                valuePresetSelect.value = valuePresetSelect.options[0]?.value;
                refreshActionList();
            };

            manualForm.appendChild(actionTypeSelect);
            manualForm.appendChild(valuePresetSelect);
            manualForm.appendChild(customValueInput);
            manualForm.appendChild(addActionBtn);
            manualSection.appendChild(manualForm);
            
            // Help text
            const helpText = document.createElement('div');
            helpText.style.cssText = `
                margin-top: 6px;
                font-size: 10px;
                color: #888;
                line-height: 1.4;
            `;
            helpText.innerHTML = `
                <strong>💡 Tips:</strong><br>
                • Use <strong>Wait</strong> actions to add delays between events<br>
                • Key Sequences: <code>shift+w_r_3</code> = Shift+W, Shift+R, Shift+3<br>
                • Example: Win key → Wait (50ms) → L key = lock screen with 50ms pause
            `;
            manualSection.appendChild(helpText);
            dialog.appendChild(manualSection);

            // Action list display
            const actionListContainer = document.createElement('div');
            actionListContainer.style.cssText = `
                margin-bottom: 15px;
                max-height: 250px;
                overflow-y: auto;
                background: #222;
                border-radius: 4px;
                padding: 8px;
            `;
            dialog.appendChild(actionListContainer);

            function refreshActionList() {
                while (actionListContainer.firstChild) {
                    actionListContainer.removeChild(actionListContainer.firstChild);
                }

                const actions = localRecording?.actions || [];
                actionCountDisplay.textContent = `${actions.length} action${actions.length !== 1 ? 's' : ''} recorded`;

                if (actions.length === 0) {
                    const emptyMsg = document.createElement('div');
                    emptyMsg.textContent = 'No actions yet';
                    emptyMsg.style.cssText = `color: #666; font-size: 11px; text-align: center; padding: 10px;`;
                    actionListContainer.appendChild(emptyMsg);
                    return;
                }

                for (let i = 0; i < actions.length; i++) {
                    const action = actions[i];
                    const actionRow = document.createElement('div');
                    actionRow.style.cssText = `
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        padding: 6px;
                        background: #333;
                        border-radius: 4px;
                        margin-bottom: 4px;
                        font-size: 11px;
                    `;

                    const actionText = document.createElement('div');
                    actionText.style.cssText = `flex: 1; color: #e0e0e0;`;
                    
                    let desc = `${i + 1}. `;
                    switch (action.type) {
                        case 'keydown':
                            desc += `⌨️ Key Down: ${action.key}`;
                            break;
                        case 'keyup':
                            desc += `⌨️ Key Up: ${action.key}`;
                            break;
                        case 'click':
                            desc += `🖱️ Click at (${action.x}, ${action.y})`;
                            break;
                        case 'mousedown':
                            desc += `🖱️ Mouse Down at (${action.x}, ${action.y})`;
                            break;
                        case 'mouseup':
                            desc += `🖱️ Mouse Up at (${action.x}, ${action.y})`;
                            break;
                        case 'mousemove':
                            desc += `🖱️ Move to (${action.x}, ${action.y})`;
                            break;
                        case 'text':
                            desc += `📝 Type: "${action.value}"`;
                            break;
                        case 'scroll':
                            desc += `📜 Scroll: ${action.deltaY}px`;
                            break;
                        case 'wait':
                            desc += `⏱️ Wait: ${action.duration}ms`;
                            break;
                    default:
                        desc += action.type;
                    }
                    actionText.textContent = desc;                    const btnContainer = document.createElement('div');
                    btnContainer.style.cssText = `display: flex; gap: 4px;`;

                    const insertBtn = document.createElement('button');
                    insertBtn.textContent = '⬆️';
                    insertBtn.title = 'Insert action before this';
                    insertBtn.style.cssText = `
                        padding: 2px 6px;
                        background: #17a2b8;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 10px;
                    `;
                    insertBtn.onclick = () => {
                        const type = prompt('Action type (keydown/keyup/text/click/wait/scroll):', 'wait');
                        if (!type) return;
                        
                        let newAction = { type };
                        
                        if (type === 'keydown' || type === 'keyup') {
                            const key = prompt('Key name:', 'Enter');
                            if (!key) return;
                            newAction.key = key;
                            newAction.code = key;
                        } else if (type === 'text') {
                            const text = prompt('Text to type:');
                            if (!text) return;
                            newAction.value = text;
                        } else if (type === 'wait') {
                            const dur = prompt('Duration (ms):', '1000');
                            newAction.duration = parseInt(dur) || 1000;
                        } else if (type === 'scroll') {
                            const delta = prompt('Scroll amount (px):', '100');
                            newAction.deltaY = parseInt(delta) || 100;
                        } else if (type === 'click' || type === 'mousedown' || type === 'mouseup') {
                            newAction.x = 0;
                            newAction.y = 0;
                            newAction.button = 'left';
                        }
                        
                        localRecording.actions.splice(i, 0, newAction);
                        refreshActionList();
                    };

                    // Edit button for Wait actions only
                    if (action.type === 'wait') {
                        const editBtn = document.createElement('button');
                        editBtn.textContent = '✏️';
                        editBtn.title = 'Edit wait duration';
                        editBtn.style.cssText = `
                            padding: 2px 6px;
                            background: #ffc107;
                            color: #333;
                            border: none;
                            border-radius: 3px;
                            cursor: pointer;
                            font-size: 10px;
                        `;
                        editBtn.onclick = () => {
                            const newDuration = prompt('Wait duration (ms):', action.duration.toString());
                            if (newDuration !== null) {
                                action.duration = parseInt(newDuration) || 0;
                                refreshActionList();
                            }
                        };
                        btnContainer.appendChild(editBtn);
                    }

                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '🗑️';
                    deleteBtn.title = 'Delete';
                    deleteBtn.style.cssText = `
                        padding: 2px 6px;
                        background: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 10px;
                    `;
                    deleteBtn.onclick = () => {
                        localRecording.actions.splice(i, 1);
                        refreshActionList();
                    };

                    btnContainer.appendChild(insertBtn);
                    btnContainer.appendChild(deleteBtn);

                    actionRow.appendChild(actionText);
                    actionRow.appendChild(btnContainer);
                    actionListContainer.appendChild(actionRow);
                }
            }

            refreshActionList();

            // Validation: Check for unpaired keydown events
            function validateKeyPairs(actions) {
                const keyState = {}; // Track which keys are pressed
                const unpairedKeydowns = [];
                
                for (let i = 0; i < actions.length; i++) {
                    const action = actions[i];
                    if (action.type === 'keydown') {
                        if (keyState[action.key]) {
                            // Key already down, previous keydown was unpaired
                            unpairedKeydowns.push({ index: keyState[action.key].index, key: action.key });
                        }
                        keyState[action.key] = { index: i, action };
                    } else if (action.type === 'keyup') {
                        if (keyState[action.key]) {
                            delete keyState[action.key]; // Paired successfully
                        }
                    }
                }
                
                // Any remaining keys in keyState are unpaired
                for (const key in keyState) {
                    unpairedKeydowns.push({ index: keyState[key].index, key });
                }
                
                return unpairedKeydowns;
            }
            
            function autoFixKeyPairs(actions, unpairedKeydowns) {
                // Add keyup events at the end for all unpaired keys
                const keysToFix = new Set(unpairedKeydowns.map(u => u.key));
                
                for (const key of keysToFix) {
                    // Add a small wait before keyup (10ms standard delay)
                    actions.push({ type: 'wait', duration: 10 });
                    actions.push({ type: 'keyup', key: key, code: key });
                }
            }

            // Dialog buttons
            const dialogButtons = document.createElement('div');
            dialogButtons.style.cssText = `
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            `;

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.style.cssText = `
                padding: 10px 20px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            cancelBtn.onclick = () => {
                if (isRecording) {
                    stopRecording();
                    disableRecordingListeners();
                }
                dialogOverlay.remove();
            };

            const saveBtn = document.createElement('button');
            saveBtn.textContent = existingMacro ? 'Update' : 'Create';
            saveBtn.style.cssText = `
                padding: 10px 20px;
                background: #6c2bd9;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
            `;
            saveBtn.onclick = async () => {
                const name = nameInput.value.trim();
                if (!name) {
                    alert('Please enter a macro name');
                    return;
                }
                if (!localRecording || localRecording.actions.length === 0) {
                    alert('Please record some actions');
                    return;
                }

                if (isRecording) {
                    localRecording = stopRecording();
                    disableRecordingListeners();
                }
                
                // Validate key pairs
                const unpairedKeys = validateKeyPairs(localRecording.actions);
                if (unpairedKeys.length > 0) {
                    const keyList = unpairedKeys.map(u => u.key).join(', ');
                    const message = `⚠️ Warning: Found ${unpairedKeys.length} unpaired Key Down event${unpairedKeys.length > 1 ? 's' : ''}:\n\n` +
                                  `Keys: ${keyList}\n\n` +
                                  `These keys are pressed but never released.\n\n` +
                                  `Choose an option:\n` +
                                  `• OK = Auto-fix (add Key Up events with 10ms delay)\n` +
                                  `• Cancel = Go back and fix manually`;
                    
                    if (confirm(message)) {
                        // Auto-fix: add keyup events
                        autoFixKeyPairs(localRecording.actions, unpairedKeys);
                        refreshActionList();
                        showNotification('Auto-fixed unpaired keys', 'success');
                    } else {
                        // User wants to fix manually
                        return;
                    }
                }

                const macro = {
                    id: existingMacro?.id || `macro_${Date.now()}`,
                    name: name,
                    keybinding: capturedKeybinding,
                    loop: loopCheckbox.checked,
                    loopDelay: parseInt(loopDelayInput.value) || 100,
                    actions: localRecording.actions,
                };

                if (existingMacro) {
                    const index = macros.findIndex(m => m.id === existingMacro.id);
                    if (index >= 0) macros[index] = macro;
                } else {
                    macros.push(macro);
                }

                await saveMacros(macros);
                refreshMacroList();
                dialogOverlay.remove();
                showNotification(`Macro "${name}" saved!`, 'success');
            };

            dialogButtons.appendChild(cancelBtn);
            dialogButtons.appendChild(saveBtn);
            dialog.appendChild(dialogButtons);

            dialogOverlay.appendChild(dialog);
            dialogOverlay.addEventListener('click', (e) => {
                if (e.target === dialogOverlay) {
                    if (isRecording) {
                        stopRecording();
                        disableRecordingListeners();
                    }
                    dialogOverlay.remove();
                }
            });

            return dialogOverlay;
        }

        // Import/Export
        function exportMacros() {
            const data = JSON.stringify(macros, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'macros.json';
            a.click();
            URL.revokeObjectURL(url);
            showNotification('Macros exported', 'success');
        }

        function importMacros() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = async (ev) => {
                    try {
                        const imported = JSON.parse(ev.target.result);
                        if (!Array.isArray(imported)) {
                            alert('Invalid macro file format');
                            return;
                        }
                        macros = imported;
                        await saveMacros(macros);
                        refreshMacroList();
                        showNotification(`Imported ${macros.length} macro${macros.length !== 1 ? 's' : ''}`, 'success');
                    } catch (err) {
                        alert('Failed to import macros: ' + err.message);
                    }
                };
                reader.readAsText(file);
            };
            input.click();
        }
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            createUI();
            setupKeybindingListener();
        });
    } else {
        createUI();
        setupKeybindingListener();
    }

    // Cross-tab sync
    GM_addValueChangeListener(MACROS_STORAGE_KEY, async (name, oldVal, newVal) => {
        if (newVal) {
            try {
                macros = JSON.parse(newVal);
            } catch (e) {
                console.warn('[Macro Env] Failed to parse synced macros', e);
            }
        }
    });

    GM_addValueChangeListener(CONFIG_STORAGE_KEY, async (name, oldVal, newVal) => {
        if (newVal) {
            try {
                config = JSON.parse(newVal);
            } catch (e) {
                console.warn('[Macro Env] Failed to parse synced config', e);
            }
        }
    });

})();
