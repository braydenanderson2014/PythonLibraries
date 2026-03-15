# Mobile Touch Support - BadOpReporter v2.5

## Summary
Added comprehensive mobile and touch support to the BadOpReporter TamperMonkey script, making it fully functional on mobile Safari and other touch-enabled browsers.

## Changes Made (November 19, 2025)

### 1. Mobile Detection Utility
Added `isMobileDevice()` helper function that detects:
- Mobile user agents (iOS, Android, etc.)
- Small screen sizes (< 768px)
- Touch capability (`ontouchstart` in window)

### 2. Touch Event Support
All draggable elements now support both mouse and touch events:

#### Launcher Icon (📋)
- **Mouse**: `mousedown`, `mousemove`, `mouseup`
- **Touch**: `touchstart`, `touchmove`, `touchend`, `touchcancel`

#### Main Panel
- **Mouse**: `mousedown`, `mousemove`, `mouseup`
- **Touch**: `touchstart`, `touchmove`, `touchend`, `touchcancel`

#### Settings Panel
- **Mouse**: `mousedown`, `mousemove`, `mouseup`
- **Touch**: `touchstart`, `touchmove`, `touchend`, `touchcancel`

#### Pop-out Category Buttons
- **Mouse**: `mousedown`, `mousemove`, `mouseup`
- **Touch**: `touchstart`, `touchmove`, `touchend`, `touchcancel`

### 3. Mobile-Optimized UI

#### Launcher Button
- **Desktop**: 16px font, 3px/8px padding
- **Mobile**: 24px font, 8px/12px padding (easier to tap)
- Added touch-specific CSS properties:
  - `touch-action: none` (prevents browser gestures during drag)
  - `user-select: none` (prevents text selection)
  - `-webkit-tap-highlight-color: transparent` (removes tap highlight)

#### Main Panel
- **Desktop**: 400-700px width, 70vh max height
- **Mobile**: 90-95vw width, 80vh max height (adapts to screen size)
- Larger padding on mobile (12px vs 10px)
- Added `touch-action: none` and `user-select: none`

#### Category Buttons
- **Desktop**: 12px font, 4px/8px padding
- **Mobile**: 14px font, 8px/12px padding, 44px min-height
- Added `touch-action: manipulation` (prevents double-tap zoom)

### 4. Coordinate Helper Functions
Created unified coordinate extraction functions for each draggable element:
- `getEventCoords(e)` - Launcher icon
- `getMainPanelCoords(e)` - Main panel
- `getSettingsPanelCoords(e)` - Settings panel
- `getPopoutCoords(e)` - Pop-out buttons

These functions automatically detect and extract coordinates from either:
- Mouse events: `e.clientX`, `e.clientY`
- Touch events: `e.touches[0].clientX`, `e.touches[0].clientY`

### 5. Event Handler Structure
Refactored drag handlers into separate named functions:
- `startDrag()`, `doDrag()`, `endDrag()` - for consistent behavior
- Both mouse and touch events call the same handlers
- Touch events use `{ passive: false }` to allow `preventDefault()`

## Testing Recommendations

1. **iOS Safari**: Test on iPhone/iPad with Safari
2. **Android Chrome**: Test on Android device
3. **Desktop**: Verify mouse functionality still works
4. **Hybrid devices**: Test on touchscreen laptops

## Key Features Preserved

✅ All existing functionality intact
✅ Drag and drop with mouse (desktop)
✅ Drag and drop with touch (mobile)
✅ Position persistence across sessions
✅ Multi-panel dragging
✅ Pop-out button dragging
✅ Click detection vs drag detection
✅ Keyboard shortcuts (desktop only)

## Browser Compatibility

- ✅ Safari (iOS) - via TamperMonkey extension
- ✅ Chrome (Android) - via TamperMonkey/Kiwi Browser
- ✅ Desktop browsers (unchanged)
- ✅ Touchscreen laptops

## Known Limitations

- Keyboard shortcuts (`Ctrl+Shift+B`, category shortcuts) only work on desktop
- Title text adjusted for mobile to reflect touch-only controls
- Some gestures may conflict with browser navigation on mobile (edge swipes)

---

**Version**: 2.5  
**Last Updated**: November 19, 2025  
**Maintained By**: OtterLogic LLC
