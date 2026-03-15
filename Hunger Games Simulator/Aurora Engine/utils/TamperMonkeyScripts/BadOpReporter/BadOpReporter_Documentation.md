https://flexboxfroggy.com/

# Dynamic URL Reporter - Complete Documentation

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
- [Core Features](#core-features)
- [User Interface Components](#user-interface-components)
- [Category Management](#category-management)
- [URL Management](#url-management)
- [Pop-out Buttons](#pop-out-buttons)
- [Color Customization](#color-customization)
- [Import & Export](#import--export)
- [Settings & Configuration](#settings--configuration)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Mobile & Touch Support](#mobile--touch-support)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## Overview

**Dynamic URL Reporter** is a comprehensive TamperMonkey userscript designed to help users organize, categorize, and track URLs across multiple websites. The script provides a persistent, cross-tab synchronized system for capturing URLs with custom display names, exporting reports in multiple formats, and managing data with flexible daily or permanent storage options.

### Key Capabilities
- **Multi-Category Organization**: Create unlimited custom categories with individual colors and keybindings
- **Display Name System**: Assign readable names to URLs (like Chrome bookmarks) while preserving original URLs
- **Multi-Format Export**: Export reports as TXT, Markdown, HTML, or JSON with timezone-aware timestamps
- **Pop-out Buttons**: Floating, draggable category buttons for instant URL capture
- **Live Color Customization**: Full RGB color control for categories, buttons, text, and icons with real-time updates
- **Mobile/Touch Support**: Complete touch event handling for iOS Safari and Android browsers
- **Cross-Tab Sync**: Automatic data synchronization across all browser tabs
- **Persistent Storage**: Data stored locally via TamperMonkey's GM_setValue API

### Version Information
- **Current Version**: 2.7
- **Author**: OtterLogic LLC
- **License**: Custom (see script header)
- **Compatibility**: Chrome, Firefox, Safari (with TamperMonkey extension)
- **Supported Sites**: All HTTP/HTTPS websites

---

## Installation

### Prerequisites
1. **TamperMonkey Extension** installed in your browser:
   - Chrome: [TamperMonkey for Chrome](https://chrome.google.com/webstore/detail/tampermonkey/)
   - Firefox: [TamperMonkey for Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
   - Safari: [TamperMonkey for Safari](https://apps.apple.com/us/app/tampermonkey/id1482490089)

### Installation Steps
1. Copy the complete script code from `BadOpReporter(Dynamic).js`
2. Open TamperMonkey dashboard (click extension icon → Dashboard)
3. Click the **"+"** button to create a new script
4. Paste the code and save (Ctrl+S or File → Save)
5. Ensure the script is enabled (toggle switch should be ON)
6. Refresh any open websites to activate the script

### First Launch
On first run, the script will:
- Create default configuration with 3 sample categories
- Initialize empty URL lists
- Position the launcher icon in the top-right corner
- Set timezone to America/Denver (changeable in Settings)
- Enable daily reset by default

---

## Quick Start Guide

### Basic Workflow
1. **Open the Panel**: Click the blue 📋 icon in the top-right corner (or press `Ctrl+Shift+O`)
2. **Add a URL**: Click a category button (e.g., "+ Bad FSW Operators") to add the current page
3. **Rename URL** (optional): Click the ✏️ icon next to any URL to set a custom display name
4. **Export Report**: Click "📥 Download" and choose your format (TXT/MD/HTML/JSON)

### First-Time Setup Recommendations
1. **Set Your Timezone**: Settings → Timezone dropdown → Select your region
2. **Customize Categories**: Settings → Categories → Edit labels, colors, and keybindings
3. **Enable Pop-out Buttons** (optional): Settings → Pop-out Category Buttons → Enable checkbox
4. **Configure Daily Reset**: Settings → Daily Reset → Enable/disable based on your needs

---

## Core Features

### 1. URL Categorization
Organize URLs into custom categories with:
- **Unlimited Categories**: Create as many as needed
- **Color Coding**: Assign unique colors to each category (background + text color)
- **Quick Add**: One-click URL capture to any category
- **Keybindings**: Instant capture via keyboard shortcuts (e.g., Ctrl+Shift+1)
- **Visual Feedback**: Toast notifications confirm successful additions

### 2. Display Name System
URLs can have custom display names separate from the actual URL:
- **Editable Names**: Click ✏️ icon to set/change display name
- **Intelligent Exports**: Names formatted appropriately per export format
  - TXT: `Display Name: https://example.com`
  - Markdown: `[Display Name](https://example.com)`
  - HTML: `<a href="...">Display Name</a>`
  - JSON: Structured with both fields preserved
- **Backward Compatible**: Existing URLs without names show URL as name

### 3. Data Persistence
Two storage modes available:
- **Daily Reset Mode** (default): Clears all URLs at midnight in your timezone
- **Permanent Mode**: Keeps all URLs indefinitely until manually deleted
- **Cross-Tab Sync**: Changes immediately reflected in all open tabs
- **Local Storage**: Data stored via GM_setValue (persistent across browser sessions)

### 4. Multi-Format Export
Export your collected URLs in 4 formats:
- **Plain Text (.txt)**: Simple, readable format with category headers
- **Markdown (.md)**: Full formatting with clickable links and metadata
- **HTML (.html)**: Styled webpage with CSS, perfect for sharing
- **JSON (.json)**: Structured data for re-importing or programmatic use

All exports include:
- Timezone-aware generation timestamp
- Category organization
- Display names (where applicable)
- Total URL counts

---

## User Interface Components

### Main Launcher Icon (📋)
- **Location**: Top-right corner by default (fully draggable)
- **Size**: 50x50px with touch-optimized 44px minimum on mobile
- **Functions**:
  - Click: Opens main panel
  - Drag: Reposition anywhere on screen (works on mobile)
  - Hide: Use toggle keybinding (Ctrl+Shift+B by default)
- **Customization**:
  - Change background color via Settings → Icon Controls
  - Reset position to default via Settings
  - Persistent across sessions

### Main Panel
**Features:**
- Draggable title bar (works with mouse and touch)
- Scrollable content area (auto-scrolls on overflow)
- Responsive sizing (larger on mobile devices)
- Auto-hides when overlay clicked

**Contents:**
- Category buttons (colored, labeled)
- URL lists (grouped by category)
- Per-URL actions:
  - 📋 Copy: Copy URL to clipboard
  - ✏️ Rename: Set custom display name
  - 🗑️ Delete: Remove URL from category
- Action buttons:
  - 📥 Download: Export report
  - 📋 Copy All: Copy entire report to clipboard
  - ⚙️ Settings: Open settings panel
  - ❓ Help: Open help documentation
  - ✕ Close: Hide panel

### Settings Panel
**Features:**
- Draggable header (mouse + touch support)
- Organized into collapsible sections
- Real-time save (no "Save" button needed)
- Position persists across sessions

**Sections:**
1. Daily Reset Toggle
2. Export Format Selection
3. Timezone Dropdown (60+ timezones)
4. Site Filters (whitelist/blacklist)
5. Categories Management
6. Icon Controls
7. Pop-out Button Settings
8. Keybindings
9. Import/Export Settings

### Help Panel
**Features:**
- Draggable header (mouse + touch support)
- Comprehensive documentation
- Searchable (browser Ctrl+F)
- Organized into 12 topic sections
- Position persists across sessions

**Topics Covered:**
- Overview, Quick Start, Keyboard Shortcuts
- Categories, URL Management, Settings
- Site Filtering, Import/Export, Icon Controls
- Pop-out Buttons, Advanced Features
- Tips & Tricks, Troubleshooting

---

## Category Management

### Creating Categories
1. Open Settings → Categories section
2. Click "+ Add Category" button
3. New category appears with default values:
   - Label: "New Category"
   - Keybinding: None
   - Color: #007bff (blue)
   - Text Color: #ffffff (white)

### Editing Categories
**Label:**
- Click into the text field
- Type new name (saved automatically on blur)
- Used in UI buttons, exports, and panel headers

**Keybinding:**
- Click "⏺️ Record" button
- Press key combination (e.g., Ctrl+Shift+1)
- Combination appears in field and saves automatically
- Use keybinding anywhere on page to add current URL

**Background Color:**
- Click color picker (colored square)
- Select color from browser's color picker
- Color applies immediately to:
  - Main panel category buttons
  - Pop-out buttons (unless overridden)
  - Visual feedback elements

**Text Color:**
- Click text color picker
- Select color for button text
- Ensures readability with chosen background color
- Applies to all buttons using this category

**Reset Colors:**
- Individual reset: Click "↺" button next to category
- Global reset: Click "↺ Reset All Colors" at section top
- Resets to defaults: Background #007bff, Text #ffffff

### Deleting Categories
1. Click 🗑️ icon next to category
2. Confirm deletion prompt
3. Category and all its URLs are removed
4. Cannot undo (export data first if unsure)

### Category Properties
Each category stores:
```javascript
{
  key: 'uniqueIdentifier',      // Internal ID (lowercase, no spaces)
  label: 'Display Name',        // Shown in UI
  keybinding: 'Ctrl+Shift+1',   // Optional keyboard shortcut
  color: '#007bff',             // Background color (hex)
  textColor: '#ffffff'          // Text color (hex)
}
```

---

## URL Management

### Adding URLs
**Method 1: Main Panel Button**
1. Open main panel (click 📋 icon or Ctrl+Shift+O)
2. Click category button (e.g., "+ Bad FSW Operators")
3. Current page URL added to that category
4. Toast notification confirms: "Added to [Category]!"

**Method 2: Keyboard Shortcut**
1. Press assigned keybinding (e.g., Ctrl+Shift+1)
2. Current page URL added instantly
3. No panel opens (silent capture)
4. Works on any page where script is active

**Method 3: Pop-out Button**
1. Enable pop-out buttons in Settings
2. Enable specific category buttons
3. Click floating button to add URL
4. Success animation plays on button

### Setting Display Names
**Why Use Display Names?**
- Make URL lists readable and meaningful
- Similar to Chrome bookmark naming
- Original URL preserved for copying/clicking
- Exports look professional and organized

**How to Set:**
1. Locate URL in main panel
2. Click ✏️ (rename) icon next to URL
3. Enter desired name in prompt dialog
4. Press OK to save (or Cancel to abort)
5. Display name appears immediately

**Examples:**
- URL: `https://jira.company.com/browse/PROJ-1234`
- Display Name: "Bug Report #1234"
- Exports show: "Bug Report #1234" with link to actual URL

### Copying URLs
- Click 📋 (copy) icon next to any URL
- Copies actual URL to clipboard (not display name)
- Toast notification confirms: "Copied to clipboard!"
- Paste anywhere (Ctrl+V)

### Deleting URLs
- Click 🗑️ (delete) icon next to URL
- Confirmation prompt appears
- URL removed from category immediately
- Cannot undo (export data first if unsure)

### URL Data Structure
URLs stored as objects:
```javascript
{
  url: 'https://example.com',           // Actual URL
  displayName: 'My Custom Name'         // Optional display name
}
```

Legacy format (strings) automatically converted on load.

---

## Pop-out Buttons

### What Are Pop-out Buttons?
Floating, always-visible category buttons that:
- Appear on all pages where script runs
- Provide instant URL capture without opening panel
- Can be positioned anywhere on screen
- Fully customizable per category
- Work with mouse and touch input

### Enabling Pop-out Buttons
1. Open Settings → Pop-out Category Buttons
2. Toggle "Enable Pop-out Category Buttons" ON
3. For each category you want:
   - Check the category checkbox
   - Button appears immediately on page

### Global Settings
**Button Size:**
- Small: 32px (10px font)
- Medium: 40px (12px font) - default
- Large: 48px (14px font)

**Show Labels:**
- ON: Display category labels (if 8 chars or less)
- OFF: Show only first letter or emoji

### Per-Button Customization
Each enabled button can have:

**Custom Text:**
- Override default label
- Enter any text (emojis supported)
- Useful for abbreviations or icons

**Button Size:**
- Inherit: Use global size setting
- Small/Medium/Large: Override global setting

**Shape:**
- Circle: Round button (default)
- Square: 90° corners
- Rounded: Soft corners (8px radius)
- Pill: Extra-rounded (999px radius, wider)
- Horizontal Rectangle: 2x wider than tall
- Vertical Rectangle: 1.75x taller than wide

**Background Color:**
- Custom: Choose any color
- Default: Uses category color
- Applies gradient effect (darker at bottom-right)

**Text Color:**
- Custom: Choose any color for text
- Default: Uses category text color
- Ensures readability against background

**Text Size:**
- Range: 8-24px
- Independent from button size
- Fine-tune visibility and appearance

**Position:**
- Drag button anywhere on screen
- Position saved automatically
- Reset button moves to default location

### Pop-out Button Actions
**Click:**
- Adds current page URL to category
- Button briefly scales up (animation)
- Toast notification appears
- No panel opens (instant capture)

**Drag:**
- Click and hold button
- Move to desired position
- Release to save position
- Works on desktop and mobile

**Reset:**
- Colors: Settings → Reset Colors button
- Position: Settings → Reset Position button
- Both revert to defaults

### Pop-out Button Storage
Each button stores:
```javascript
{
  enabled: true,                        // Show this button
  buttonText: 'Custom',                 // Override label
  buttonSize: 'medium',                 // inherit/small/medium/large
  buttonShape: 'circle',                // circle/square/rounded/pill/rect-h/rect-v
  buttonColor: '#007bff',              // Background color
  buttonTextColor: '#ffffff',          // Text color
  textSize: 12,                        // Font size in pixels
  position: { x: 100, y: 200 }        // Screen coordinates
}
```

---

## Color Customization

### Live Color System
All color changes apply **immediately** without page refresh via the `refreshUIColors()` function:
- Updates main panel category buttons
- Updates pop-out buttons
- Updates launcher icon
- Synchronizes across all open tabs

### Category Colors
**Background Color:**
- Default: #007bff (blue)
- Used for category buttons in main panel
- Inherited by pop-out buttons (unless overridden)
- Provides visual organization

**Text Color:**
- Default: #ffffff (white)
- Applied to button text
- Should contrast well with background
- Separate control ensures readability

**Setting Colors:**
1. Settings → Categories
2. Click color picker next to category
3. Choose color from browser picker
4. Color applies instantly everywhere

**Color Inheritance:**
Pop-out buttons use this priority:
1. Custom button color (if set in pop-out settings)
2. Category color (set in category settings)
3. Default #007bff

Text color follows same hierarchy with #ffffff default.

### Launcher Icon Color
**Purpose:**
Customize the main 📋 icon appearance to match your theme

**Setting:**
1. Settings → Icon Controls
2. Click icon color picker
3. Choose color
4. Icon updates immediately

**Reset:**
Click "↺ Reset Icon Color" to restore default #007bff

### Reset Options
**Individual Category:**
- Resets one category to defaults
- Background: #007bff
- Text: #ffffff
- Located next to each category in Settings

**Global Reset:**
- Resets ALL categories to defaults
- Confirmation prompt appears
- Located at top of Categories section
- Use when experimenting goes wrong

**Pop-out Button Reset:**
- Resets button-specific color overrides
- Reverts to category colors
- Separate from position reset
- Located in per-button settings

### Color Best Practices
1. **Contrast**: Ensure text color contrasts with background
2. **Consistency**: Use similar color schemes across related categories
3. **Accessibility**: Avoid color combinations that are hard to read
4. **Visual Grouping**: Use colors to group related categories
5. **Testing**: Check colors in both light and dark environments

---

## Import & Export

### Export Formats

#### Plain Text (.txt)
**Structure:**
```
== Category Name ==
Display Name: https://example.com/page1
https://example.com/page2
(none)

== Another Category ==
...
```

**Features:**
- Simple, human-readable format
- Shows display names with colon separator
- URLs without names show URL only
- Empty categories show "(none)"
- Best for: Quick sharing, documentation

#### Markdown (.md)
**Structure:**
```markdown
# 📋 URL Report - 2025-11-20
==================================================

> *Generated by Dynamic URL Reporter*

## 📊 Summary
**Total Categories:** 3
**Total URLs:** 15
**Report Date:** 2025-11-20

---

## 📁 Category Name
- [Display Name](https://example.com/page1)
- [Another Link](https://example.com/page2)

---

*📅 Report generated on November 20, 2025, 3:45:30 PM MST*

> 💡 **Tip:** Use `Ctrl+F` to quickly find specific URLs
```

**Features:**
- Full markdown formatting with headers
- Clickable links in markdown viewers
- Summary statistics section
- Timezone-aware timestamp in footer
- Decorative borders and emojis
- Best for: GitHub, SharePoint, Slack, Teams

#### HTML (.html)
**Structure:**
Complete standalone webpage with:
- CSS styling (embedded in `<style>` tag)
- Responsive design
- Colored headers matching category colors
- Clickable links with hover effects
- Footer with generation timestamp

**Features:**
- Professional appearance
- Works in any browser (offline)
- Colored category sections
- Clean, modern design
- Best for: Sharing via email, presentations, archives

#### JSON (.json)
**Structure:**
```json
{
  "version": "1.0",
  "date": "2025-11-20",
  "categories": [
    {
      "key": "category1",
      "label": "Category Name",
      "keybinding": "Ctrl+Shift+1"
    }
  ],
  "lists": {
    "category1": [
      {
        "url": "https://example.com",
        "displayName": "My Link"
      }
    ]
  }
}
```

**Features:**
- Structured data format
- Preserves all metadata
- Re-importable (perfect round-trip)
- Machine-readable
- Best for: Backups, data transfer, automation

### Exporting Data

**Quick Export:**
1. Open main panel
2. Click "📥 Download" button
3. File downloads with format from Settings
4. Filename: `url_report_YYYY-MM-DD.ext`

**Change Export Format:**
1. Settings → Export Format
2. Select: TXT / Markdown / HTML / JSON
3. Selection saved automatically
4. All future exports use this format

**Copy to Clipboard:**
1. Open main panel
2. Click "📋 Copy All" button
3. Entire report copied in selected format
4. Paste anywhere (Ctrl+V)

### Import Formats

#### Import from Text (.txt)
Supports multiple text formats:

**Format 1: Category Headers**
```
== Category Name ==
https://example.com/page1
https://example.com/page2

== Another Category ==
...
```

**Format 2: Display Names**
```
== Category ==
My Link: https://example.com
Another: https://example.com/page2
```

**Import Process:**
1. Click Settings → Import → Choose File
2. Select .txt file
3. Script parses content:
   - Finds `== Category ==` headers
   - Creates category if doesn't exist
   - Extracts URLs and display names
   - Adds to existing categories (no duplicates)
4. Toast notification shows results

#### Import from Markdown (.md)
Supports markdown link format:

**Format:**
```markdown
## Category Name
- [Display Name](https://example.com)
- [Another Link](https://example.com/page2)

## Another Category
...
```

**Features:**
- Parses `[Name](URL)` syntax
- Extracts display names from brackets
- Creates missing categories automatically
- Handles multiple heading levels (##, ###)
- Ignores non-link content

#### Import from HTML
Supports HTML anchor tags:

**Format:**
```html
<h2>Category Name</h2>
<a href="https://example.com">Display Name</a>
<a href="https://example.com/page2">Another</a>
```

**Features:**
- Parses `<h2>` or `<h3>` for categories
- Extracts URLs from `href` attributes
- Gets display names from link text
- Handles HTML entities (&amp;, &lt;, etc.)
- Creates missing categories

#### Import from JSON
Directly imports exported JSON:

**Features:**
- Perfect round-trip import/export
- Preserves all metadata
- Merges with existing data
- Creates missing categories
- Avoids duplicate URLs

### Import Settings (Configuration)

**Export Settings:**
1. Settings → Import/Export Settings
2. Click "Export Settings"
3. Downloads: `url_reporter_settings.json`
4. Contains:
   - All categories (names, colors, keybindings)
   - Site filters (whitelist/blacklist)
   - Pop-out button configurations
   - UI positions
   - All preferences

**Import Settings:**
1. Settings → Import/Export Settings
2. Click "Import Settings"
3. Choose JSON file
4. Settings replaced immediately
5. Page refreshes to apply changes

**Use Cases:**
- Transfer settings between browsers
- Backup configuration before changes
- Share team configurations
- Reset to known-good state

### Auto-Category Creation
When importing files with categories that don't exist:
1. Script detects new category names
2. Creates categories automatically with:
   - Key: sanitized version of label
   - Label: as found in file
   - Color: default blue (#007bff)
   - Text Color: default white (#ffffff)
   - No keybinding
3. Imports URLs into new categories
4. Toast notification lists new categories

**Example:**
Import file has `== New Team ==` but "New Team" category doesn't exist:
- Category "New Team" created automatically
- URLs imported successfully
- Notification: "Created new categories: New Team"

---

## Settings & Configuration

### Daily Reset
**Purpose:**
Control whether URLs are cleared at midnight

**Options:**
- **Enabled** (default): All URLs deleted at midnight in your timezone
- **Disabled**: URLs kept permanently until manually deleted

**Use Cases:**
- Enabled: Daily activity tracking, temporary collections
- Disabled: Long-term bookmarking, permanent reference lists

**How It Works:**
- Script checks date on load via `todayString()`
- If date changed and reset enabled, calls `resetDailyData()`
- Preserves categories and settings
- Only clears URL lists

### Export Format
**Default:** Plain Text (TXT)

**Options:**
1. **TXT**: Simple text, human-readable
2. **Markdown**: Formatted for GitHub, SharePoint, Slack
3. **HTML**: Styled webpage, email-friendly
4. **JSON**: Structured data, re-importable

**Selection:**
- Radio button selection in Settings
- Saved automatically on change
- Affects "Download" and "Copy All" actions

### Timezone
**Purpose:**
Ensure accurate date tracking and timestamps

**Default:** America/Denver (Mountain Time)

**Selection:**
- Dropdown with 60+ timezones
- Organized by region:
  - US & Canada (9 zones)
  - Europe (16 zones)
  - Asia (12 zones)
  - Australia & Pacific (6 zones)
  - South America (6 zones)
  - Middle East & Africa (6 zones)
  - Atlantic & Other (4 zones)

**Used For:**
- Daily reset timing (midnight in your zone)
- Export timestamps
- Date-based report filenames

**How to Change:**
1. Settings → Timezone
2. Select from dropdown
3. Saves automatically
4. Affects future operations immediately

### Site Filters

#### Top Frame Only
**Purpose:**
Prevent script from running in iframes

**Options:**
- **Enabled** (default): Only runs in main page
- **Disabled**: Runs in iframes too

**Why Enable:**
- Prevents duplicate icons
- Avoids conflicts with embedded content
- Reduces resource usage
- Recommended for most users

#### Whitelist
**Purpose:**
Only run script on specified websites

**Format:**
One URL per line:
```
https://example.com/
https://jira.mycompany.com/
https://docs.google.com/
```

**Behavior:**
- Empty: Run on all sites (default)
- With entries: ONLY run on listed sites
- Exact match required for scheme (http/https)
- Path must match beginning of URL

**Use Case:**
Restrict script to work-related sites only

#### Blacklist
**Purpose:**
Never run script on specified websites

**Format:**
Same as whitelist (one URL per line)

**Behavior:**
- Takes priority over whitelist
- If URL matches blacklist, script doesn't run
- Useful for problematic sites
- Overrides whitelist settings

**Priority:**
Blacklist > Whitelist > Default (run everywhere)

### Icon Controls

#### Icon Color
- Color picker for launcher icon (📋)
- Default: #007bff (blue)
- Changes icon background
- Reset button available

#### Icon Position
- Drag icon anywhere on screen
- Position saved automatically
- Reset button in Settings
- Restores to top-right default

#### Toggle Icon Keybinding
- Default: Ctrl+Shift+B
- Hide/show launcher icon
- Recordable via "⏺️ Record" button
- Icon state persists across sessions

### Keybindings

#### Recording Keybindings
1. Click "⏺️ Record" button next to keybinding field
2. Button text changes to "Recording... (press keys)"
3. Press desired key combination
4. Combination appears in field (e.g., "Ctrl+Shift+1")
5. Saves automatically

#### Supported Modifiers
- **Ctrl**: Control/Command key
- **Shift**: Shift key
- **Alt**: Alt/Option key

**Common Patterns:**
- Ctrl+Shift+[Number]: Quick category access
- Ctrl+Shift+[Letter]: Alphabetic shortcuts
- Ctrl+Alt+[Key]: Alternative pattern

#### Conflicts
- Script checks for existing keybindings
- Warns if duplicate detected
- Browser shortcuts take priority
- Avoid: Ctrl+S, Ctrl+T, Ctrl+W, etc.

### Panel Positions
All panels remember their positions:

**Main Panel:**
- Drag title bar to reposition
- Position saved on drag end
- Reset: Not available (reopens centered)

**Settings Panel:**
- Drag header to reposition
- Position saved automatically
- Persists across sessions

**Help Panel:**
- Drag header to reposition
- Position saved automatically
- Persists across sessions

---

## Keyboard Shortcuts

### Global Shortcuts
| Shortcut | Action | Customizable |
|----------|--------|--------------|
| Ctrl+Shift+O | Toggle main panel | No (hardcoded) |
| Ctrl+Shift+B | Hide/show icon | Yes (Settings → Icon Controls) |

### Category Shortcuts
| Default | Action | Customizable |
|---------|--------|--------------|
| Ctrl+Shift+1 | Add URL to first category | Yes (per category) |
| Ctrl+Shift+2 | Add URL to second category | Yes (per category) |
| Ctrl+Shift+3 | Add URL to third category | Yes (per category) |
| (etc.) | Add to additional categories | Yes (per category) |

### Recording Custom Shortcuts
1. Settings → Categories → Find category
2. Click "⏺️ Record" next to keybinding field
3. Press desired key combination
4. Shortcut active immediately

### Shortcut Best Practices
1. **Use Ctrl+Shift**: Least likely to conflict
2. **Numbers for Categories**: Easy to remember (Ctrl+Shift+1-9)
3. **Letters for Actions**: Mnemonic (Ctrl+Shift+W for "Work")
4. **Test Before Saving**: Ensure no browser conflicts
5. **Document Your Shortcuts**: Keep a reference list

---

## Mobile & Touch Support

### Touch Event Implementation
Script includes complete touch event handling:

**Supported Gestures:**
- **Tap**: Click buttons, open panels
- **Drag**: Move panels, icons, pop-out buttons
- **Long Press**: Same as desktop click
- **Touch & Drag**: Reposition elements

**Touch Event Handlers:**
- `touchstart`: Begin interaction
- `touchmove`: Track finger movement
- `touchend`: Complete interaction
- `touchcancel`: Handle interruptions

### Drag vs. Click Detection
**Problem:**
On touch devices, dragging can trigger clicks

**Solution:**
5px movement threshold:
- Movement < 5px: Treated as click
- Movement ≥ 5px: Treated as drag
- Prevents accidental panel opening when dragging icon

**Implementation:**
```javascript
const threshold = 5; // pixels
const distance = Math.sqrt(dx*dx + dy*dy);
if (distance < threshold) {
  // Handle as click
} else {
  // Handle as drag
}
```

### Mobile-Optimized UI

**Icon Size:**
- Desktop: 50x50px
- Mobile: 50x50px with 44px minimum (iOS guidelines)
- Touch target: 44x44px minimum

**Button Size:**
- Desktop: 4px-8px padding
- Mobile: 8px-12px padding
- Font size increased on mobile

**Panel Size:**
- Desktop: Fixed width (400px/500px/600px)
- Mobile: 90% viewport width
- Height: Auto-adjusts to content

**Font Size:**
- Desktop: 12px base
- Mobile: 14px base (improved readability)

### Mobile Testing Checklist
- [ ] Icon draggable without opening panel
- [ ] Category buttons easy to tap
- [ ] Pop-out buttons draggable
- [ ] Settings inputs accessible
- [ ] Color pickers work
- [ ] Keyboard doesn't obstruct UI
- [ ] Pinch-zoom doesn't interfere
- [ ] Orientation change handled
- [ ] Touch scrolling smooth

---

## Advanced Features

### Cross-Tab Synchronization
**Mechanism:**
Uses TamperMonkey's `GM_addValueChangeListener` API

**How It Works:**
1. User makes change in Tab A (add URL, change setting, etc.)
2. Script calls `saveConfig()` which uses `GM_setValue`
3. TamperMonkey broadcasts change to all tabs
4. Tab B receives change via listener
5. Tab B updates UI via `refreshListDisplay()` or `refreshUIColors()`

**What Syncs:**
- URL additions/deletions
- Category changes (rename, color, delete)
- Display name changes
- Settings changes
- Pop-out button positions
- Icon position

**What Doesn't Sync:**
- Panel open/closed state
- Current scroll position
- Temporary UI states

### Live Color Updates
**refreshUIColors() Function:**
Called whenever colors change, updates:
1. Launcher icon background
2. Main panel category buttons (background + text)
3. All pop-out buttons (if using category colors)
4. Visual feedback elements

**No Page Reload Required:**
- Changes DOM styles directly
- Uses `element.style.background` and `element.style.color`
- Instant visual feedback
- Better user experience than full refresh

### Position Persistence
**Tracked Positions:**
- Launcher icon (x, y)
- Main panel (x, y)
- Settings panel (x, y)
- Help panel (x, y)
- Each pop-out button (x, y)

**Storage Format:**
```javascript
{
  iconPosition: { x: 100, y: 50 },
  mainPanelPosition: { x: null, y: null },  // null = centered
  settingsPanelPosition: { x: 200, y: 100 },
  helpPanelPosition: { x: 300, y: 150 },
  popoutButtons: {
    categories: {
      'catKey1': { position: { x: 50, y: 200 } }
    }
  }
}
```

**Position Calculation:**
- Uses `getBoundingClientRect()` for accuracy
- Constrains to viewport bounds (won't go off-screen)
- Saves on drag end, not during drag (performance)
- Null values trigger default positioning logic

### Boundary Detection
All draggable elements constrained to viewport:

```javascript
const maxX = window.innerWidth - element.offsetWidth;
const maxY = window.innerHeight - element.offsetHeight;
element.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
element.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
```

**Prevents:**
- Elements dragged off-screen
- Inaccessible UI components
- Need for manual position resets

### Gradient Generation
Pop-out buttons use dynamic gradients:

**Algorithm:**
```javascript
function adjustColor(hex, percent) {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.max(0, Math.min(255, (num >> 16) + percent));
  const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
  const b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}

// Usage:
const baseColor = '#007bff';
const darkerColor = adjustColor(baseColor, -20);
background = `linear-gradient(135deg, ${baseColor}, ${darkerColor})`;
```

**Result:**
Professional-looking 3D effect on buttons

### Toast Notifications
**Purpose:**
Provide non-intrusive user feedback

**Features:**
- Auto-dismiss after 2 seconds
- Fade in/out animations
- Stacks multiple notifications
- Positioned bottom-center
- Dark background, white text

**Triggered By:**
- URL added
- URL copied
- Settings saved
- Colors reset
- Import completed
- Errors encountered

### HTML Entity Escaping
All user content sanitized before export:

**Function:**
```javascript
const escaped = text
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#039;');
```

**Prevents:**
- XSS attacks in HTML exports
- Broken HTML structure
- Display issues with special characters

**Applied To:**
- Display names in HTML export
- URLs in HTML export
- Category labels in exports

---

## Troubleshooting

### Common Issues

#### Icon Appears Twice
**Cause:** Script running in main page and iframes

**Solution:**
1. Settings → Site Filters
2. Enable "Top Frame Only"
3. Refresh page

#### URLs Not Saving
**Cause:** TamperMonkey storage permissions

**Solution:**
1. TamperMonkey Dashboard → Settings
2. Ensure "Storage" tab shows green status
3. Check browser storage not full
4. Try export/reimport to reset storage

#### Keybinding Not Working
**Causes:**
- Browser shortcut conflicts
- Wrong modifier keys
- Page has focus issues

**Solutions:**
1. Try different key combination
2. Click on page before using shortcut
3. Check browser doesn't intercept shortcut
4. Use "⏺️ Record" to ensure correct entry

#### Script Not Loading in New Window
**Causes:**
- TamperMonkey not initialized
- URL doesn't match @match pattern
- Extension disabled in window

**Solutions:**
1. Refresh page after TamperMonkey loads
2. Check URL is HTTP/HTTPS
3. Verify TamperMonkey icon shows script active
4. Check Dashboard to ensure script enabled

#### Pop-out Button Not Appearing
**Causes:**
- Not enabled globally
- Category checkbox not checked
- Z-index conflict with page elements
- Position off-screen

**Solutions:**
1. Settings → Pop-out Buttons → Enable main toggle
2. Enable specific category checkbox
3. Reset button position via Settings
4. Check browser console for errors

#### Import Not Creating Categories
**Cause:** File format not recognized

**Solutions:**
1. Ensure proper format:
   - TXT: `== Category Name ==` headers
   - MD: `## Category Name` headers
   - HTML: `<h2>Category Name</h2>` tags
   - JSON: Proper structure
2. Check file encoding (UTF-8 recommended)
3. Remove extra whitespace
4. Try different format

#### Colors Not Syncing Across Tabs
**Cause:** Storage listener not initialized

**Solutions:**
1. Close all tabs and reopen
2. Check browser console for errors
3. Export settings, clear storage, reimport
4. Update TamperMonkey to latest version

#### Data Lost After Browser Restart
**Causes:**
- Browser clearing site data
- TamperMonkey storage disabled
- Browser in incognito mode

**Solutions:**
1. Check browser settings for data retention
2. Ensure TamperMonkey has storage permissions
3. Export data regularly as backup
4. Don't use in incognito if data persistence needed

### Debug Mode
**Enable Console Logging:**
Add to script (temporary):
```javascript
// At top of script after 'use strict';
const DEBUG = true;
const log = (...args) => DEBUG && console.log('[URLReporter]', ...args);

// Use throughout:
log('Config loaded:', config);
log('URL added:', url);
```

**Check Console:**
- F12 or Ctrl+Shift+I (Windows/Linux)
- Cmd+Option+I (Mac)
- Look for errors in red
- Check network tab for storage issues

### Getting Help
1. **Export Your Settings:** Helps with troubleshooting
2. **Check Browser Console:** Look for error messages
3. **Note Script Version:** Found in TamperMonkey dashboard
4. **Document Steps to Reproduce:** Helps identify issue
5. **Try Fresh Install:** Remove script, clear storage, reinstall

---

## Technical Details

### Technology Stack
- **Language:** JavaScript (ES6+)
- **Runtime:** TamperMonkey userscript
- **Storage:** GM_setValue / GM_getValue API
- **DOM Manipulation:** Vanilla JavaScript (no libraries)
- **Styling:** Inline CSS via cssText
- **Events:** Native DOM events + TamperMonkey GM_addValueChangeListener

### Browser Compatibility
| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Recommended |
| Firefox | ✅ Full | Requires TamperMonkey |
| Safari | ✅ Full | iOS/macOS via TamperMonkey extension |
| Edge | ✅ Full | Chromium-based |
| Opera | ✅ Full | Chromium-based |

### Performance Characteristics
**Memory Usage:**
- Base: ~1-2 MB
- Per category: ~1 KB
- Per URL: ~0.5 KB (with display name)
- Typical (3 cats, 50 URLs): ~3 MB

**Storage:**
- Config: ~5-20 KB (depends on categories)
- Data: ~100 bytes per URL
- Total: Usually < 100 KB

**CPU Impact:**
- Idle: Negligible
- URL Add: < 1ms
- Export (100 URLs): 10-50ms
- Import (100 URLs): 20-100ms

### Code Architecture

**Main Components:**
1. **Configuration Layer:**
   - `DEFAULT_CONFIG`: Default settings
   - `loadConfig()`: Load from storage
   - `saveConfig()`: Persist to storage
   - Validation and migration logic

2. **Data Layer:**
   - `data.lists`: URL storage by category
   - `data.date`: Current date tracking
   - `makeEmptyLists()`: Initialize structure
   - `resetDailyData()`: Clear URLs

3. **UI Layer:**
   - `createUI()`: Main initialization
   - `createLauncher()`: Icon creation
   - `panel`: Main content panel
   - `settingsPanel`: Settings UI
   - `helpPanel`: Help documentation

4. **Export Layer:**
   - `buildExportText()`: TXT format
   - `buildMarkdownExport()`: MD format
   - `buildHtmlExport()`: HTML format
   - `buildJsonExport()`: JSON format

5. **Import Layer:**
   - `importFromText()`: Parse TXT files
   - `importFromMarkdown()`: Parse MD files
   - `importFromHtml()`: Parse HTML files
   - `importFromJson()`: Parse JSON files

6. **Pop-out Layer:**
   - `createPopoutButtons()`: Generate buttons
   - `createPopoutButton()`: Single button
   - `destroyPopoutButtons()`: Cleanup
   - Per-button drag handlers

### Storage Schema

**Config Object:**
```javascript
{
  categories: [
    {
      key: string,           // Unique identifier
      label: string,         // Display name
      keybinding: string,    // Optional shortcut
      color: string,         // Hex color
      textColor: string      // Hex color
    }
  ],
  timezone: string,          // IANA timezone
  dailyReset: boolean,       // Reset at midnight
  siteWhitelist: string[],   // Allowed URLs
  siteBlacklist: string[],   // Blocked URLs
  useTopFrameOnly: boolean,  // Ignore iframes
  exportFormat: string,      // 'txt'|'md'|'html'|'json'
  iconPosition: {x, y},      // Launcher position
  iconVisible: boolean,      // Show/hide icon
  iconColor: string,         // Icon background
  toggleIconKeybinding: string,
  mainPanelPosition: {x, y},
  settingsPanelPosition: {x, y},
  helpPanelPosition: {x, y},
  popoutButtons: {
    enabled: boolean,
    categories: {
      [catKey]: {
        enabled: boolean,
        buttonText: string,
        buttonSize: string,
        buttonShape: string,
        buttonColor: string,
        buttonTextColor: string,
        textSize: number,
        position: {x, y}
      }
    },
    buttonSize: string,      // Global default
    showLabels: boolean
  }
}
```

**Data Object:**
```javascript
{
  date: string,              // YYYY-MM-DD
  lists: {
    [catKey]: [
      {
        url: string,
        displayName: string
      }
    ]
  }
}
```

### API Reference

**GM Functions Used:**
- `GM_getValue(key, defaultValue)`: Retrieve stored data
- `GM_setValue(key, value)`: Save data persistently
- `GM_addValueChangeListener(key, callback)`: Watch for changes

**Storage Keys:**
- `urlReporter_config`: Configuration object
- `urlReporter_data`: URL lists and date

### Security Considerations

**XSS Prevention:**
- All user input escaped before DOM insertion
- No `innerHTML` with user content
- HTML exports escape all entities

**Storage Security:**
- Data stored locally (not transmitted)
- TamperMonkey sandbox isolation
- No external API calls

**Privacy:**
- No analytics or tracking
- No data sent to servers
- All processing client-side

### Version History

**v2.7** (Current)
- Added timezone dropdown with 60+ zones
- Made help panel draggable
- Added footer timestamps with timezone
- Improved HTTP/HTTPS support

**v2.6**
- Added pop-out button color reset
- Added text size control for buttons
- Enhanced color customization
- Updated help documentation

**v2.5**
- Added category color system
- Implemented live color refresh
- Added global color reset
- Icon color customization

**v2.4**
- Complete mobile/touch support
- Drag vs. click detection
- Touch event handlers
- Mobile-optimized UI

**v2.3**
- Multi-format import (TXT/MD/HTML/JSON)
- Auto-category creation on import
- JSON export format
- Markdown display name parsing

**v2.2**
- Display name system
- Per-URL rename function
- Enhanced export formats
- Backward compatibility

**v2.1**
- Pop-out buttons feature
- Per-button customization
- Shape options (6 shapes)
- Button dragging

**v2.0**
- Major refactor
- Settings panel redesign
- Improved storage structure
- Cross-tab sync

---

## Conclusion

Dynamic URL Reporter is a powerful, feature-rich tool for organizing and tracking URLs across the web. With its extensive customization options, mobile support, and flexible export formats, it serves both casual users and power users effectively.

### Key Strengths
- ✅ Zero setup required (works immediately after install)
- ✅ Fully customizable (colors, positions, keybindings)
- ✅ Mobile-friendly (complete touch support)
- ✅ Data portability (multiple export/import formats)
- ✅ Privacy-focused (all data local)
- ✅ Cross-tab sync (changes propagate instantly)
- ✅ Professional exports (suitable for sharing)

### Best Use Cases
1. **Bug Report Tracking**: Capture Jira/GitHub URLs while testing
2. **Research Collections**: Organize articles by topic
3. **Code Review**: Track PRs and code links
4. **Daily Standup**: Collect work items for reporting
5. **Content Curation**: Build reading lists and references
6. **Link Sharing**: Create formatted link collections for teams

### Future Considerations
- Cloud sync (optional)
- Category folders/hierarchies
- Search/filter functionality
- URL metadata (tags, notes, dates)
- Browser extension version (non-userscript)
- Team sharing features

---

## Appendix

### SharePoint Formatting Notes
This documentation is formatted for SharePoint compatibility:
- Standard markdown syntax
- No custom HTML
- Tables using pipe syntax
- Code blocks with language hints
- Hierarchical heading structure
- Anchor links for navigation

### Additional Resources
- **TamperMonkey Documentation**: https://www.tampermonkey.net/documentation.php
- **IANA Timezone Database**: https://www.iana.org/time-zones
- **Markdown Guide**: https://www.markdownguide.org/

### Contact & Support
- **Author**: OtterLogic LLC
- **Version**: 2.7
- **Last Updated**: November 20, 2025

---

*End of Documentation*
