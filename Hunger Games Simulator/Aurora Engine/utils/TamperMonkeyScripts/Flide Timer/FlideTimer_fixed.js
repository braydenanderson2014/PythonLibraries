// ==UserScript==
// @name         Flide Timer
// @namespace    http://tampermonkey.net/
// @version      v1.10
// @description  try to take over the world!
// @author       @connobrown, OtterLogic
// @match        https://*/*
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// ==/UserScript==

(function() {
'use strict';

// Only run in top-level window (not iframes) to prevent duplicates
if (window.self !== window.top) return;

// Check if URL starts with the base path (though @match already filters this)
if (!window.location.href.startsWith('https://flide.ap.tesla.services/3d/')) return;

// Create container for the UI
const container = document.createElement('div');
container.style.position = 'fixed';
container.style.top = '0'; // At top of page
container.style.left = '60%'; // Shifted right to 60%
container.style.transform = 'translateX(-50%)';
container.style.zIndex = '10000'; // Increased for visibility over site elements
container.style.textAlign = 'center';
container.style.fontFamily = 'Arial, sans-serif'; // For consistency
container.style.display = 'flex'; // Flex for centering
container.style.flexDirection = 'column'; // Stack vertically
container.style.alignItems = 'center'; // Center horizontally
container.style.cursor = 'move'; // Indicate draggable
document.body.appendChild(container);

// NEW: Load saved position from localStorage
const savedPosition = localStorage.getItem('flideTimerPosition');
if (savedPosition) {
    const { top, left } = JSON.parse(savedPosition);
    container.style.top = top + 'px';
    container.style.left = left + 'px';
    container.style.transform = 'none'; // Remove transform when using saved position
}

// NEW: Draggable logic for container
let isDragging = false;
let dragOffset = { x: 0, y: 0 };

function getDragCoords(e) {
    if (e.touches && e.touches.length > 0) {
        return { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    return { x: e.clientX, y: e.clientY };
}

function startDrag(e) {
    // Don't drag if clicking on interactive elements
    if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' ||
        e.target.tagName === 'SELECT' || e.target.tagName === 'A') return;

    if (e.button && e.button !== 0) return; // Only left mouse button

    isDragging = true;
    const rect = container.getBoundingClientRect();
    const coords = getDragCoords(e);
    dragOffset.x = coords.x - rect.left;
    dragOffset.y = coords.y - rect.top;
    container.style.transform = 'none'; // Remove transform during drag
    e.preventDefault();
}

function doDrag(e) {
    if (!isDragging) return;
    const coords = getDragCoords(e);
    let newLeft = coords.x - dragOffset.x;
    let newTop = coords.y - dragOffset.y;

    // Keep within viewport bounds
    const maxX = window.innerWidth - container.offsetWidth;
    const maxY = window.innerHeight - container.offsetHeight;
    newLeft = Math.max(0, Math.min(newLeft, maxX));
    newTop = Math.max(0, Math.min(newTop, maxY));

    container.style.left = newLeft + 'px';
    container.style.top = newTop + 'px';

    // Save position
    localStorage.setItem('flideTimerPosition', JSON.stringify({ left: newLeft, top: newTop }));
    e.preventDefault();
}

function endDrag() {
    isDragging = false;
}

// Mouse events
container.addEventListener('mousedown', startDrag);
document.addEventListener('mousemove', doDrag);
document.addEventListener('mouseup', endDrag);

// Touch events for mobile
container.addEventListener('touchstart', startDrag, { passive: false });
document.addEventListener('touchmove', doDrag, { passive: false });
document.addEventListener('touchend', endDrag);
document.addEventListener('touchcancel', endDrag);

// Create overlay for click-outside handling
const overlay = document.createElement('div');
overlay.style.position = 'fixed';
overlay.style.top = '0';
overlay.style.left = '0';
overlay.style.width = '100%';
overlay.style.height = '100%';
overlay.style.zIndex = '9999'; // Below container but above page
overlay.style.display = 'none'; // Hidden by default
document.body.appendChild(overlay);

// Gear button (minimized state, slimmer padding)
const gearButton = document.createElement('button');
gearButton.innerHTML = '🐒'; // Monkey emoji
gearButton.style.fontSize = '18px';
gearButton.style.padding = '3px 8px'; // Reduced padding
gearButton.style.background = '#007bff'; // Blue background
gearButton.style.border = '1px solid #ccc';
gearButton.style.borderRadius = '5px';
gearButton.style.cursor = 'pointer';
gearButton.style.display = 'none'; // Hidden by default, shown only on TCLP/apviz pages
container.appendChild(gearButton);

// Expanded menu (hidden by default)
const menu = document.createElement('div');
menu.style.display = 'none';
menu.style.background = '#f0f0f0';
menu.style.padding = '15px';
menu.style.border = '1px solid #ccc';
menu.style.borderRadius = '5px';
menu.style.marginBottom = '5px'; // Reduced gap
menu.style.fontSize = '16px'; // Base font size for menu
menu.style.maxWidth = '600px'; // Widened for two columns
container.insertBefore(menu, gearButton); // Menu above gear

// Timer toggle (centered in the menu)
const timerLabel = document.createElement('label');
timerLabel.innerText = 'Show Timer ';
timerLabel.style.margin = '0 10px';
timerLabel.style.fontSize = '18px';

const timerToggle = document.createElement('input');
timerToggle.type = 'checkbox';
timerToggle.checked = localStorage.getItem('timerToggle') !== 'false'; // On by default, persist with localStorage
timerToggle.style.transform = 'scale(1.5)'; // Slightly enlarge checkbox for usability

timerToggle.addEventListener('change', () => {
localStorage.setItem('timerToggle', timerToggle.checked);
updateTimerVisibility();
});

timerLabel.appendChild(timerToggle);
menu.appendChild(timerLabel);

// Alert toggle
const alertLabel = document.createElement('label');
alertLabel.innerText = 'Enable Alert ';
alertLabel.style.margin = '10px 10px 0';
alertLabel.style.fontSize = '18px';
alertLabel.style.display = 'block'; // New line for better spacing

const alertToggle = document.createElement('input');
alertToggle.type = 'checkbox';
alertToggle.checked = localStorage.getItem('alertToggle') === 'true'; // Off by default, persist with localStorage
alertToggle.style.transform = 'scale(1.5)';

alertToggle.addEventListener('change', () => {
localStorage.setItem('alertToggle', alertToggle.checked);
reevaluateAlertState(); // Dynamically start/stop blinking
});

alertLabel.appendChild(alertToggle);
menu.appendChild(alertLabel);

// Alert threshold input
const thresholdLabel = document.createElement('label');
thresholdLabel.innerText = 'Alert Threshold (XX:XX): ';
thresholdLabel.style.margin = '10px 5px 0 0';
thresholdLabel.style.fontSize = '16px';

const thresholdInput = document.createElement('input');
thresholdInput.type = 'text';
thresholdInput.placeholder = 'MM:SS';
thresholdInput.value = localStorage.getItem('alertThreshold') || '05:00'; // Default 5 minutes as MM:SS
thresholdInput.style.width = '60px';
thresholdInput.style.margin = '10px 0 0';
thresholdInput.style.fontSize = '16px';

thresholdInput.addEventListener('change', () => {
let inputVal = thresholdInput.value.trim();
let mins = 0, secs = 0;
let isValid = false;

// If purely numeric (no colon), parse based on length
if (/^\d+$/.test(inputVal)) {
const len = inputVal.length;
if (len === 1) {
// 1 digit: "M" -> "0M:00"
mins = parseInt(inputVal);
secs = 0;
} else if (len === 2) {
// 2 digits: "MM" -> "MM:00"
mins = parseInt(inputVal);
secs = 0;
} else if (len === 3) {
// 3 digits: "MSS" -> "0M:SS"
mins = parseInt(inputVal[0]);
secs = parseInt(inputVal.slice(1));
} else if (len === 4) {
// 4 digits: "MMSS" -> "MM:SS"
mins = parseInt(inputVal.slice(0, 2));
secs = parseInt(inputVal.slice(2));
}
isValid = !isNaN(mins) && !isNaN(secs) && mins >= 0 && secs >= 0 && secs < 60;
} else {
// Existing logic for MM:SS format
const parts = inputVal.split(':');
if (parts.length === 2) {
mins = parseInt(parts[0]);
secs = parseInt(parts[1]);
isValid = !isNaN(mins) && !isNaN(secs) && mins >= 0 && secs >= 0 && secs < 60;
}
}

// Store and format if valid, else reset to default
let valueToStore = '05:00';
if (isValid) {
valueToStore = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
localStorage.setItem('alertThreshold', valueToStore);
thresholdInput.value = valueToStore; // Update display
reevaluateAlertState(); // Dynamically check if should blink
});

thresholdLabel.appendChild(thresholdInput);
menu.appendChild(thresholdLabel);

// Alert color dropdown
const colorLabel = document.createElement('label');
colorLabel.innerText = 'Alert Color: ';
colorLabel.style.margin = '10px 5px 0';
colorLabel.style.fontSize = '16px';

const colorSelect = document.createElement('select');
colorSelect.style.fontSize = '16px';
colorSelect.style.margin = '10px 0 0';
const colors = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'cyan', 'black', 'gray'];
colors.forEach(color => {
const option = document.createElement('option');
option.value = color;
option.text = color.charAt(0).toUpperCase() + color.slice(1);
colorSelect.appendChild(option);
});
colorSelect.value = localStorage.getItem('alertColor') || 'red'; // Default red

colorSelect.addEventListener('change', () => {
localStorage.setItem('alertColor', colorSelect.value);
if (isBlinking) {
stopBlinking();
startBlinking(); // Restart to apply new color immediately
}
});

colorLabel.appendChild(colorSelect);
menu.appendChild(colorLabel);

// Blink speed slider
const blinkSpeedLabel = document.createElement('label');
blinkSpeedLabel.innerText = 'Blink Speed (s): ';
blinkSpeedLabel.style.margin = '10px 5px 0';
blinkSpeedLabel.style.fontSize = '16px';
blinkSpeedLabel.style.display = 'block'; // New line

const blinkSpeedSlider = document.createElement('input');
blinkSpeedSlider.type = 'range';
blinkSpeedSlider.min = '1';
blinkSpeedSlider.max = '5';
blinkSpeedSlider.step = '1';
blinkSpeedSlider.value = localStorage.getItem('blinkSpeed') || '3'; // Default middle (1s)
blinkSpeedSlider.style.width = '200px';
blinkSpeedSlider.style.margin = '10px 0';

// Datalist for marks
const datalist = document.createElement('datalist');
datalist.id = 'blinkMarks';
for (let i = 1; i <= 5; i++) {
const option = document.createElement('option');
option.value = i;
datalist.appendChild(option);
}
menu.appendChild(datalist);
blinkSpeedSlider.setAttribute('list', 'blinkMarks');

// Dynamic label for current interval
const blinkSpeedValue = document.createElement('span');
blinkSpeedValue.style.marginLeft = '10px';
blinkSpeedValue.style.fontSize = '16px';

const updateBlinkSpeedValue = () => {
const intervals = [0.2, 0.5, 1, 1.5, 2]; // in seconds
const index = parseInt(blinkSpeedSlider.value) - 1;
blinkSpeedValue.innerText = `${intervals[index]}s`;
};
updateBlinkSpeedValue(); // Initial

blinkSpeedSlider.addEventListener('input', () => {
localStorage.setItem('blinkSpeed', blinkSpeedSlider.value);
updateBlinkSpeedValue();
if (isBlinking) {
stopBlinking();
startBlinking(); // Restart with new speed immediately
}
});

blinkSpeedLabel.appendChild(blinkSpeedSlider);
blinkSpeedLabel.appendChild(blinkSpeedValue);
menu.appendChild(blinkSpeedLabel);

// Timer size slider
const sizeLabel = document.createElement('label');
sizeLabel.innerText = 'Timer Size: ';
sizeLabel.style.margin = '10px 5px 0';
sizeLabel.style.fontSize = '16px';
sizeLabel.style.display = 'block'; // New line

const sizeSlider = document.createElement('input');
sizeSlider.type = 'range';
sizeSlider.min = '1';
sizeSlider.max = '3';
sizeSlider.step = '1';
sizeSlider.value = localStorage.getItem('timerSize') || '1'; // Default small (1)
sizeSlider.style.width = '200px';
sizeSlider.style.margin = '10px 0';

// Datalist for marks (3 ticks)
const sizeDatalist = document.createElement('datalist');
sizeDatalist.id = 'sizeMarks';
for (let i = 1; i <= 3; i++) {
const option = document.createElement('option');
option.value = i;
sizeDatalist.appendChild(option);
}
menu.appendChild(sizeDatalist);
sizeSlider.setAttribute('list', 'sizeMarks');

// Dynamic label for current size
const sizeValue = document.createElement('span');
sizeValue.style.marginLeft = '10px';
sizeValue.style.fontSize = '16px';

const updateSizeValue = () => {
const labels = ['Small', 'Medium', 'Large'];
const index = parseInt(sizeSlider.value) - 1;
sizeValue.innerText = labels[index];
};
updateSizeValue(); // Initial

// Prompt text (shown on slider movement)
const sizePrompt = document.createElement('div');
sizePrompt.innerText = 'Close this menu to apply size changes.';
sizePrompt.style.display = 'none';
sizePrompt.style.fontSize = '14px';
sizePrompt.style.color = 'gray';
sizePrompt.style.marginTop = '5px';

sizeSlider.addEventListener('input', () => {
localStorage.setItem('timerSize', sizeSlider.value);
updateSizeValue();
sizePrompt.style.display = 'block';
});

sizeLabel.appendChild(sizeSlider);
sizeLabel.appendChild(sizeValue);
menu.appendChild(sizeLabel);
menu.appendChild(sizePrompt);

// Stats header
const statsHeader = document.createElement('div');
statsHeader.style.marginTop = '15px';
statsHeader.style.fontSize = '14px';
statsHeader.style.color = 'gray';
statsHeader.style.textAlign = 'center';
statsHeader.style.textDecoration = 'underline';
menu.appendChild(statsHeader);

// Stat readout for average clip speed
const statReadout = document.createElement('div');
statReadout.style.marginTop = '5px';
statReadout.style.fontSize = '14px';
statReadout.style.color = 'gray';
statReadout.style.textAlign = 'center';
menu.appendChild(statReadout);

// Clip count readout
const clipCountReadout = document.createElement('div');
clipCountReadout.style.marginTop = '5px';
clipCountReadout.style.fontSize = '14px';
clipCountReadout.style.color = 'gray';
clipCountReadout.style.textAlign = 'center';
menu.appendChild(clipCountReadout);

// Expand button for cache list
const expandButton = document.createElement('button');
expandButton.innerHTML = '▼';
expandButton.style.margin = '5px auto 0'; // Reduced top margin for tighter spacing
expandButton.style.display = 'flex'; // Flex for centering content
expandButton.style.width = '16px'; // ~30% smaller
expandButton.style.height = '16px'; // ~30% smaller
expandButton.style.borderRadius = '50%';
expandButton.style.background = '#007bff'; // Match gear color
expandButton.style.color = 'white';
expandButton.style.border = 'none';
expandButton.style.cursor = 'pointer';
expandButton.style.fontSize = '9px';
expandButton.style.alignItems = 'center';
expandButton.style.justifyContent = 'center';
expandButton.style.lineHeight = '0'; // Eliminate line spacing for perfect centering
menu.appendChild(expandButton);

// Disclaimer text (under expand button)
const disclaimer = document.createElement('div');
disclaimer.innerText = '*Stats may not accurately match Flide. These are helpful trends, not gospel.';
disclaimer.style.marginTop = '5px';
disclaimer.style.fontSize = '12px'; // Slightly smaller than stats (14px)
disclaimer.style.color = 'gray';
disclaimer.style.fontStyle = 'italic';
disclaimer.style.textAlign = 'center';
menu.appendChild(disclaimer);

// Cache list container (hidden by default)
const cacheList = document.createElement('div');
cacheList.style.display = 'none';
cacheList.style.marginTop = '5px'; // Reduced for tighter spacing
cacheList.style.maxHeight = '200px'; // Limit height for scrolling
cacheList.style.overflowY = 'auto';
cacheList.style.padding = '10px';
cacheList.style.background = '#e0e0e0';
cacheList.style.borderRadius = '5px';
cacheList.style.fontSize = '12px';
cacheList.style.textAlign = 'left';
menu.appendChild(cacheList);

// Function to populate and show cache list
function showCacheList() {
cacheList.innerHTML = ''; // Clear previous content
if (cache.length === 0) {
cacheList.innerHTML = 'No cached clips.';
return;
}
const ul = document.createElement('ul');
ul.style.listStyleType = 'none';
ul.style.padding = '0';
cache.forEach(item => {
if (!item || !item.url) return; // Skip invalid entries to prevent errors
const li = document.createElement('li');
li.style.marginBottom = '5px';

const idFull = item.url.replace('https://flide.ap.tesla.services/3d/', '');
const idAbbrev = `TCLIP...${idFull.slice(-8)}`;
const time = formatTime(item.seconds || 0);
const date = item.dateAdded || 'N/A';

// Create hyperlink for ID if fullUrl exists
if (item.fullUrl) {
const link = document.createElement('a');
link.href = item.fullUrl;
link.innerText = idAbbrev;
link.style.color = 'blue'; // Styling for visibility
link.style.textDecoration = 'underline';
link.style.cursor = 'pointer';
link.target = '_blank'; // Open in new tab
li.appendChild(link);
} else {
li.appendChild(document.createTextNode(idAbbrev));
}

li.appendChild(document.createTextNode(` - ${time} - ${date}`));
ul.appendChild(li);
});
cacheList.appendChild(ul);
}

// Toggle cache list on button click
expandButton.onclick = (event) => {
event.stopPropagation(); // Prevent menu close
const isExpanded = cacheList.style.display === 'block';
if (!isExpanded) {
showCacheList(); // Populate dynamically
}
cacheList.style.display = isExpanded ? 'none' : 'block';
expandButton.innerHTML = isExpanded ? '▼' : '▲'; // Toggle arrow
};

// Function to update stats
function updateStats() {
const today = new Date();
const mm = (today.getMonth() + 1).toString().padStart(2, '0');
const dd = today.getDate().toString().padStart(2, '0');
const yyyy = today.getFullYear();
const todayFormatted = `${mm}-${dd}-${yyyy}`; // MM-DD-YYYY
const todayYMD = today.toLocaleDateString('en-CA', { timeZone: 'America/Denver' }); // YYYY-MM-DD for filtering
const todayClips = cache.filter(item => item.dateAdded === todayYMD);
const clipCount = todayClips.length;

// Update header
statsHeader.innerText = `${todayFormatted} Stats:`;

// Update clip speed
if (clipCount === 0) {
statReadout.innerText = `approx. clip speed: N/A`;
} else {
const totalSeconds = todayClips.reduce((sum, item) => sum + (item.seconds || 0), 0);
const avgSeconds = Math.floor(totalSeconds / clipCount);
const mins = Math.floor(avgSeconds / 60).toString().padStart(2, '0');
const secs = (avgSeconds % 60).toString().padStart(2, '0');
statReadout.innerText = `approx. clip speed: ${mins}:${secs}`;
}

// Update clip count
clipCountReadout.innerText = `approx. clip count: ${clipCount}`;
}

// Toggle menu on gear click
gearButton.onclick = (event) => {
event.stopPropagation(); // Prevent any bubbling issues
const isOpening = menu.style.display === 'none';
menu.style.display = isOpening ? 'block' : 'none';
overlay.style.display = isOpening ? 'block' : 'none'; // Show/hide overlay with menu
if (isOpening) {
if (currentUrlKey) {
updateTimerInCache(currentUrlKey, seconds, cache);
saveCache(cache);
}
updateStats(); // Update stats when opening
sizePrompt.style.display = 'none'; // Reset prompt on open
cacheList.style.display = 'none'; // Reset cache list
expandButton.innerHTML = '▼'; // Reset arrow
} else {
applyChanges(); // Apply on close
}
};

// Minimize menu on overlay click (handles clicks outside the menu reliably)
overlay.addEventListener('click', () => {
menu.style.display = 'none';
overlay.style.display = 'none';
applyChanges(); // Apply on close
});

// Timer element
const timerDisplay = document.createElement('div');
timerDisplay.style.marginBottom = '1px'; // Tighter gap
timerDisplay.style.display = 'none';
timerDisplay.style.color = 'black'; // Default color
container.insertBefore(timerDisplay, menu); // Timer above menu

let timerInterval;
let saveInterval;
let blinkInterval;
let seconds = 0;
let lastURL = window.location.href; // Track initial URL
let currentUrlKey = null;
let isBlinking = false;
let blinkState = false; // Toggle for blink
let cache = loadCache();

function loadCache() {
const stored = localStorage.getItem('timerCache');
return stored ? JSON.parse(stored) : [];
}

function saveCache(updatedCache) {
localStorage.setItem('timerCache', JSON.stringify(updatedCache));
}

function getTimerForUrl(urlKey, updatedCache, fullUrl) {
const index = updatedCache.findIndex(item => item.url === urlKey);
if (index !== -1) {
const [entry] = updatedCache.splice(index, 1);
updatedCache.unshift(entry);
return entry.seconds || 0;
} else {
const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Denver' }); // YYYY-MM-DD in Mountain Time
updatedCache.unshift({ url: urlKey, seconds: 0, dateAdded: today, fullUrl: fullUrl });
if (updatedCache.length > 500) updatedCache.pop();
return 0;
}
}

function updateTimerInCache(urlKey, newSeconds, updatedCache) {
const index = updatedCache.findIndex(item => item.url === urlKey);
if (index !== -1) {
updatedCache[index].seconds = newSeconds;
const [entry] = updatedCache.splice(index, 1);
updatedCache.unshift(entry);
}
}

function formatTime(sec) {
const hrs = Math.floor(sec / 3600).toString().padStart(2, '0');
const mins = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
const secs = (sec % 60).toString().padStart(2, '0');
return `${hrs}:${mins}:${secs}`;
}

function startTimer() {
if (timerInterval) clearInterval(timerInterval);
timerInterval = setInterval(() => {
// NEW: Only increment if tab is visible
if (!document.hidden) {
seconds++;
timerDisplay.innerText = formatTime(seconds);
reevaluateAlertState();
}
}, 1000);
}

function startSaveInterval() {
if (saveInterval) clearInterval(saveInterval);
saveInterval = setInterval(() => {
// NEW: Only save if tab is visible
if (currentUrlKey && !document.hidden) {
updateTimerInCache(currentUrlKey, seconds, cache);
saveCache(cache);
}
}, 5000);
}

function reevaluateAlertState() {
const thresholdStr = localStorage.getItem('alertThreshold') || '05:00';
const [mins, secs] = thresholdStr.split(':').map(Number);
const thresholdSeconds = (isNaN(mins) || isNaN(secs)) ? 300 : (mins * 60) + secs;
const alertEnabled = localStorage.getItem('alertToggle') === 'true';

if (alertEnabled && seconds > thresholdSeconds) {
if (!isBlinking) startBlinking();
} else {
if (isBlinking) {
stopBlinking();
timerDisplay.style.color = 'black'; // Reset
}
}
}

function startBlinking() {
stopBlinking(); // Clear any existing
isBlinking = true;
const speedValue = parseInt(localStorage.getItem('blinkSpeed') || '3');
const intervals = [200, 500, 1000, 1500, 2000]; // ms
const intervalMs = intervals[speedValue - 1];
const alertColor = localStorage.getItem('alertColor') || 'red';
const lightGrey = '#c0c0c0'; // Halfway between white and gray

blinkInterval = setInterval(() => {
blinkState = !blinkState;
timerDisplay.style.color = blinkState ? lightGrey : alertColor;
}, intervalMs);
}

function stopBlinking() {
if (blinkInterval) clearInterval(blinkInterval);
isBlinking = false;
blinkState = false;
}

function updateTimerVisibility() {
const currentURL = window.location.href;
// NEW: Support both TCLP and apviz endpoints
const isTCLP = currentURL.startsWith('https://flide.ap.tesla.services/3d/TCLP');
const isApviz = currentURL.includes('apviz');
const isValidPage = isTCLP || isApviz;
const urlKey = isValidPage ? currentURL.split(/[?&]/)[0] : null;

// Handle URL key changes
if (currentUrlKey && urlKey !== currentUrlKey) {
// Save previous
updateTimerInCache(currentUrlKey, seconds, cache);
saveCache(cache);
stopBlinking();
}
if (urlKey && urlKey !== currentUrlKey) {
// Load new (pass full currentURL for potential new entry)
seconds = getTimerForUrl(urlKey, cache, currentURL);
timerDisplay.innerText = formatTime(seconds);
timerDisplay.style.color = 'black';
stopBlinking();
}
currentUrlKey = urlKey;

if (isValidPage) {
gearButton.style.display = 'block'; // Always show gear on valid pages

// Always start save interval on valid pages if currentUrlKey exists
if (currentUrlKey) {
startSaveInterval();
}

if (timerToggle.checked) {
timerDisplay.style.display = 'block';
startTimer();
reevaluateAlertState(); // Immediate check for alert
} else {
timerDisplay.style.display = 'none';
if (timerInterval) clearInterval(timerInterval);
stopBlinking();
// Do not reset seconds here; it's preserved for the current URL key
// Note: saveInterval continues running
}
} else {
timerDisplay.style.display = 'none';
gearButton.style.display = 'none'; // Hide gear off valid pages
if (timerInterval) clearInterval(timerInterval);
if (saveInterval) clearInterval(saveInterval);
stopBlinking();
}

lastURL = currentURL; // Update after check
}

function applyChanges() {
const sizeIndex = parseInt(localStorage.getItem('timerSize') || '1') - 1;
const sizes = ['20px', '30px', '40px']; // Small, Medium, Large
timerDisplay.style.fontSize = sizes[sizeIndex];
}

// NEW: Handle tab visibility changes (pause when hidden, resume when visible)
document.addEventListener('visibilitychange', () => {
if (document.hidden) {
// Tab is hidden - save current state immediately
if (currentUrlKey) {
updateTimerInCache(currentUrlKey, seconds, cache);
saveCache(cache);
}
// Timer will automatically pause due to document.hidden check in startTimer
// Blinking will continue but that's okay
} else {
// Tab is visible again - timer will automatically resume
// Re-evaluate alert state in case threshold was crossed while hidden
if (currentUrlKey && timerToggle.checked) {
reevaluateAlertState();
}
}
});

// Initial setup
applyChanges(); // Set initial timer size
updateTimerVisibility();

// Poll for URL changes (e.g., SPA navigation) every 1 second
setInterval(() => {
  const current = window.location.href;
  if (current !== lastURL) {
    updateTimerVisibility();
  }
}, 1000);

// Re-check on manual navigation (fallback)
window.addEventListener('popstate', updateTimerVisibility);

// Save timer on page unload/reload to prevent loss of unsaved progress
window.addEventListener('beforeunload', () => {
if (currentUrlKey) {
updateTimerInCache(currentUrlKey, seconds, cache);
saveCache(cache);
}
});

// Optional debug logs (uncomment to test)
// console.log('Timer script loaded. Initial cache:', cache);
// window.addEventListener('beforeunload', () => console.log('Saving on unload:', { url: currentUrlKey, seconds }));

})();
