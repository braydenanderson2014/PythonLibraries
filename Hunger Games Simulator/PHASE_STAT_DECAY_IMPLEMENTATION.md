# Phase-End Stat Decay Implementation

## What Was Added

### Location: `Engine/Aurora Engine.py`

#### New Method: `_apply_phase_end_stat_decay()`
This method is called at the end of each phase and applies realistic stat changes to all alive tributes:

**Stat Decay Rates (from config):**
- Hunger: +5 per phase (simulates need for food over time)
- Thirst: +7 per phase (simulates need for water, higher than hunger)
- Fatigue: +4 per phase (simulates lack of rest)

**Sanity Loss (environmental effects):**
- Tribute with shelter + fire: -2 sanity (safe, but still anxious)
- Tribute with shelter only: -5 sanity (cold and scared)
- Tribute exposed: -8 sanity (harsh conditions + fear)

**Health Damage from Starvation/Dehydration:**
- High hunger (>80) causes health loss via `update_hunger()` (already implemented)
- High thirst (>85) causes health loss via `update_thirst()` (already implemented)

**Death Detection:**
- If a tribute's health drops to 0 or below, they're marked as dead
- Death is recorded with cause: "Environmental effects"
- Dead tributes are removed from active events

**Logging:**
- Each phase end generates a "phase_stat_updates" message
- Contains all stat changes and any deaths
- Logged to message queue for web UI consumption

---

## Integration Points

### Called From: `advance_phase()`
When a new phase begins, stat decay is applied BEFORE the phase_changed message is sent.

This means:
1. Phase timer expires
2. Stats are updated (tributes get hungrier, thirstier, more tired, more traumatized)
3. Updated scoreboards are included in the phase_changed message
4. Web UI receives fresh stat data

### Message Type: `phase_stat_updates`
```json
{
  "message_type": "phase_stat_updates",
  "timestamp": "2025-10-28T...",
  "data": {
    "phase": 1,
    "stat_updates": [
      {
        "tribute_id": "player_1",
        "hunger": [0, 5],
        "thirst": [0, 7],
        "fatigue": [0, 4],
        "sanity": [100, 92]
      }
    ],
    "deaths": []
  }
}
```

---

## Web UI Impact

### What Players Will See:
1. **Your Tribute Stats** (left sidebar)
   - Health decreasing from starvation/thirst
   - Sanity decreasing from exposure/fear
   - Hunger/Thirst/Fatigue increasing each phase

2. **Remaining Tributes** (right sidebar)
   - Live stat updates for all tributes
   - See which tributes are dying from environmental effects
   - Track who's doing well (low hunger/thirst = survived better)

3. **Game Log**
   - Eventually: messages about tributes dying from starvation
   - Messages about environmental challenges

---

## Future Enhancements

### Easy Next Steps:
1. **Combat Stat Updates** - When PvP events occur, apply damage to losers
2. **Supply Events** - Food/water finds reduce hunger/thirst
3. **Medical Events** - Medical supplies reduce bleeding/poison damage
4. **Shelter Benefits** - Add bonus items for having shelter/fire

### Config Customization:
Edit `Engine/config.json` to adjust:
```json
{
  "stat_decay_rates": {
    "hunger": 5,
    "thirst": 7,
    "fatigue": 4,
    "sanity_floor": 50
  }
}
```

---

## Testing

To verify this is working:
1. Start a game with multiple tributes
2. Observe stats in left/right sidebars
3. Advance phases and watch stats change
4. Keep game running to see tributes eventually die from starvation
5. Check browser console for phase_stat_updates messages

---

## Files Modified
- `Engine/Aurora Engine.py`
  - Added `_apply_phase_end_stat_decay()` method
  - Modified `advance_phase()` to call stat decay before emitting phase message
