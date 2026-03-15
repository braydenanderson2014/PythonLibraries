# Debug Session: Cornucopia Phase Skip & Live Stats Not Updating

**Date**: November 7, 2025  
**Issues**: 
1. Cornucopia phase being completely skipped (goes straight to Morning Phase)
2. Tribute stats sidebar greyed out and never updating

## What I've Added

### 1. Comprehensive Cornucopia Phase Logging

Added detailed logging to track the cornucopia phase execution flow in `Engine/Aurora Engine.py`:

**Location: `process_cornucopia_updates()` (line ~306)**
- Logs when cornucopia is already completed
- Logs current cornucopia phase on every update
- Logs countdown updates when received
- Logs when `make_tribute_decisions()` is called and completed (with phase transition)
- Logs when `execute_bloodbath()` is called and completed (with phase transition)

**Location: `check_timers_and_advance()` (line ~660)**
- Logs when checking if cornucopia is completed
- Logs current cornucopia phase value
- Logs whether advancing or waiting

### 2. Live Stats Debug Logging

Added detailed logging to track why tribute stats aren't updating in `static/js/game.js`:

**Location: `engine_status_update` handler (line ~412)**
- Logs all tribute IDs received in scoreboards
- Logs the currentPlayer.id being searched for
- Logs whether the ID was found in scoreboards
- Logs data types of IDs (to catch string vs number mismatches)

**Location: `displayPlayerTributeStats()` (line ~1042)**
- Logs old vs new currentPlayer.id
- Logs the data type of the new ID
- Logs which field the ID came from (data.id vs data.tribute_id)

## What to Look For When Testing

### For Cornucopia Phase Issue:

Start the game and watch the server console. You should see a sequence like this:

```
[CORNUCOPIA DEBUG] Processing cornucopia updates - Current phase: countdown
[CORNUCOPIA DEBUG] Countdown update: cornucopia_timer_update
[CORNUCOPIA DEBUG] check_timers_and_advance - is_completed: False, current_phase: countdown
[CORNUCOPIA DEBUG] Still in cornucopia phase (countdown), not advancing
...
[CORNUCOPIA DEBUG] Processing cornucopia updates - Current phase: decision
[CORNUCOPIA DEBUG] Calling make_tribute_decisions for 24 tributes
[CORNUCOPIA DEBUG] make_tribute_decisions returned 24 messages, phase now: bloodbath
[CORNUCOPIA DEBUG] check_timers_and_advance - is_completed: False, current_phase: bloodbath
[CORNUCOPIA DEBUG] Still in cornucopia phase (bloodbath), not advancing
...
[CORNUCOPIA DEBUG] Processing cornucopia updates - Current phase: bloodbath
[CORNUCOPIA DEBUG] Calling execute_bloodbath for 24 tributes
[CORNUCOPIA DEBUG] execute_bloodbath returned 2 messages, phase now: completed
[CORNUCOPIA DEBUG] Cornucopia already completed, returning empty
[CORNUCOPIA DEBUG] check_timers_and_advance - is_completed: True, current_phase: completed
[CORNUCOPIA DEBUG] Countdown completed - advancing phase
```

**If the phase is being skipped**, you'll likely see:
- `check_timers_and_advance` reporting `is_completed: True` immediately
- `process_cornucopia_updates` never getting called, OR
- The phase value changing unexpectedly, OR
- `advance_phase` being called before the countdown finishes

### For Live Stats Issue:

Open the browser console (F12) and watch for these messages when the game starts:

```
[DISPLAY_STATS] currentPlayer.id updated: {old: undefined, new: "1", type: "string", ...}
📊 Received tribute scoreboards: 24 tributes
[DEBUG_STATS] All tribute IDs: ["1", "2", "3", ...]
[DEBUG_STATS] Looking for currentPlayer.id: "1" in scoreboards
[ENGINE_UPDATE] ✓ Found stats for currentPlayer, updating
```

**If stats aren't updating**, you'll see:
- `currentPlayer.id NOT FOUND in tribute_scoreboards!` - ID mismatch
- Type mismatch errors (e.g., looking for string "1" but scoreboards use number 1)
- `No currentPlayer or currentPlayer.id not set` - ID never got set

## Expected Root Causes

### Cornucopia Skip Issue - Hypotheses:

1. **Phase Timer Conflict**: The 30-second phase timer (from config) expires before the 60-second cornucopia countdown finishes, causing premature advancement
   - **Evidence**: Previous fix to `_get_phase_timer_update()` suggests timer confusion
   - **Check**: Look for phase_timer being set when it should be None

2. **is_completed() Called Too Early**: Something is calling `is_completed()` before the bloodbath executes
   - **Evidence**: We modified `check_timers_and_advance()` to check `is_completed()`
   - **Check**: See if `is_completed()` returns True during countdown

3. **Missing Tick Execution**: `process_cornucopia_updates()` might not be getting called at all
   - **Evidence**: No cornucopia events are appearing
   - **Check**: Look for "Processing cornucopia updates" logs

### Live Stats Issue - Hypotheses:

1. **ID Type Mismatch**: currentPlayer.id is a string but scoreboards use numbers (or vice versa)
   - **Evidence**: JavaScript object key lookup is type-sensitive
   - **Check**: Compare types in debug logs

2. **ID Never Set**: currentPlayer.id is undefined/null when scoreboards arrive
   - **Evidence**: Stats display calls happen before tribute selection
   - **Check**: Look for "No currentPlayer or currentPlayer.id not set"

3. **Scoreboard Key Mismatch**: The ID format is different (e.g., "tribute_1" vs "1")
   - **Evidence**: Game state uses tribute_id but scoreboards might use different format
   - **Check**: Compare actual keys in debug logs

## Next Steps

1. **Start a test game** with the server console and browser console open
2. **Copy ALL the debug logs** from both consoles
3. **Share the logs** so we can trace the exact execution flow
4. **Based on the logs**, we'll identify:
   - Where the cornucopia phase execution breaks
   - Why the currentPlayer.id isn't matching scoreboards

## Files Modified

- `Engine/Aurora Engine.py` - Added cornucopia phase execution logging
- `static/js/game.js` - Added tribute stats matching debug logging

---

**Status**: Debug logging in place, ready for test run
