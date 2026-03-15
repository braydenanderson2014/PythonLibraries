# Admin Controls - Quick Test Guide

## 🚀 Quick Start (2 minutes)

### Step 1: Start Server
```bash
cd "h:\Hunger Games Simulator\Aurora Engine"
python lobby_server.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
SocketIO connected: /socket.io
```

### Step 2: Create Game
1. Open browser: `http://localhost:8000`
2. Click "Create Lobby"
3. Add 2-3 tributes
4. Click "Start Game"

### Step 3: Open Browser Console
- Press `F12` to open Developer Tools
- Click "Console" tab
- Ready to run commands

---

## 🧪 Test Commands

### Test 1: Force Next Phase
```javascript
// Command
socket.emit('admin_force_next_phase', {
    'lobby_id': 'lobby_1'
}, (response) => {
    console.log('✅ Response:', response);
});

// Expected output
// ✅ Response: {
//     "success": true,
//     "new_phase": "Morning Phase",
//     "message": "Phase advanced successfully"
// }
```

**What to verify:**
- ✅ Response shows `success: true`
- ✅ Phase name shows new phase
- ✅ Game display updates with new phase
- ✅ Tribute stats increase (hunger, thirst, fatigue)

---

### Test 2: Force Next Event
```javascript
// Command
socket.emit('admin_force_next_event', {
    'lobby_id': 'lobby_1'
}, (response) => {
    console.log('✅ Response:', response);
});

// Expected output
// ✅ Response: {
//     "success": true,
//     "event": {
//         "message_type": "combat_event",
//         "data": {...},
//         "timestamp": "2025-10-28T18:30:00"
//     },
//     "message": "Event forced: combat_event"
// }
```

**What to verify:**
- ✅ Response shows `success: true`
- ✅ Event type is one of: combat_event, arena_event, idle_event
- ✅ Game log updates with new event
- ✅ Event is displayed to all players

---

### Test 3: Get Tribute Stats (All)
```javascript
// Command
socket.emit('admin_get_tribute_stats', {
    'lobby_id': 'lobby_1'
}, (response) => {
    console.log('✅ All Tributes:', response);
    console.table(response.tributes);
});

// Expected output (simplified)
// ✅ All Tributes: {
//     "success": true,
//     "tributes": {
//         "player_1": {
//             "name": "Katniss",
//             "health": 95,
//             "hunger": 12,
//             "thirst": 14,
//             "fatigue": 8,
//             "status": "alive"
//         },
//         "player_2": { ... }
//     },
//     "count": 2
// }
```

**What to verify:**
- ✅ Response shows `success: true`
- ✅ All tributes listed
- ✅ Stats are numbers (not null)
- ✅ Stats match game display

---

### Test 4: Get Specific Tribute Stats
```javascript
// Command
socket.emit('admin_get_tribute_stats', {
    'lobby_id': 'lobby_1',
    'tribute_id': 'player_1'
}, (response) => {
    console.log('✅ Player 1 Stats:', response.tribute);
    console.table(response.tribute);
});

// Expected output
// ✅ Player 1 Stats: {
//     "id": "player_1",
//     "name": "Katniss",
//     "district": 12,
//     "health": 95,
//     "sanity": 92,
//     "hunger": 12,
//     "thirst": 14,
//     "fatigue": 8,
//     "status": "alive"
// }
```

**What to verify:**
- ✅ Response shows correct tribute
- ✅ All stat fields present
- ✅ Stats are reasonable values (0-100)
- ✅ Status is "alive" or "dead"

---

### Test 5: Trigger Stat Decay
```javascript
// Command
socket.emit('admin_trigger_stat_decay', {
    'lobby_id': 'lobby_1'
}, (response) => {
    console.log('✅ Stat Decay Applied:', response);
});

// Expected output
// ✅ Stat Decay Applied: {
//     "success": true,
//     "message": "Stat decay applied to all tributes",
//     "updated_tributes": 2
// }
```

**What to verify:**
- ✅ Response shows `success: true`
- ✅ `updated_tributes` matches number of alive tributes
- ✅ Get tribute stats again and verify stats increased:
  - Hunger: +5
  - Thirst: +7
  - Fatigue: +4

**Verification Script:**
```javascript
// Get stats before decay
let statsBefore = null;
socket.emit('admin_get_tribute_stats', {
    'lobby_id': 'lobby_1',
    'tribute_id': 'player_1'
}, (response) => {
    statsBefore = response.tribute;
    console.log('Before:', statsBefore.hunger, statsBefore.thirst, statsBefore.fatigue);
});

// Wait 2 seconds, then trigger decay
setTimeout(() => {
    socket.emit('admin_trigger_stat_decay', {'lobby_id': 'lobby_1'}, () => {
        // Wait 1 second for update
        setTimeout(() => {
            socket.emit('admin_get_tribute_stats', {
                'lobby_id': 'lobby_1',
                'tribute_id': 'player_1'
            }, (response) => {
                let statsAfter = response.tribute;
                console.log('After:', statsAfter.hunger, statsAfter.thirst, statsAfter.fatigue);
                console.log('Changes:');
                console.log('  Hunger:', statsAfter.hunger - statsBefore.hunger, '(expected +5)');
                console.log('  Thirst:', statsAfter.thirst - statsBefore.thirst, '(expected +7)');
                console.log('  Fatigue:', statsAfter.fatigue - statsBefore.fatigue, '(expected +4)');
            });
        }, 1000);
    });
}, 2000);
```

---

### Test 6: Update Timing Configuration
```javascript
// Command - Update event cooldowns
socket.emit('admin_update_timing', {
    'timing_updates': {
        'event_cooldowns': {
            'Combat Events': 10,      // Changed from default
            'Arena Events': 15,
            'Idle Events': 5
        }
    }
}, (response) => {
    console.log('✅ Timing Updated:', response);
});

// Expected output
// ✅ Timing Updated: {
//     "success": true,
//     "message": "Timing configuration updated",
//     "updated_timings": {
//         "event_cooldowns": {...},
//         "phase_transitions": {...}
//     }
// }
```

**What to verify:**
- ✅ Response shows `success: true`
- ✅ Cooldowns are updated in response
- ✅ Events generate more frequently (check game log)
- ✅ Can update phase transitions (day_phase, night_phase, etc.)

---

## 📋 Complete Test Sequence

Run this sequence to test all admin commands:

```javascript
console.log('=== ADMIN CONTROLS TEST SEQUENCE ===');

// Store lobby ID (adjust if different)
const LOBBY_ID = 'lobby_1';

// Test 1: Get initial stats
console.log('\n📊 Test 1: Get Initial Stats');
socket.emit('admin_get_tribute_stats', {'lobby_id': LOBBY_ID}, (r) => {
    console.log('✅ Got stats for', r.count, 'tributes');
    console.log('Sample tribute:', r.tributes[Object.keys(r.tributes)[0]]);
});

// Wait 1 second, then test force event
setTimeout(() => {
    console.log('\n🎲 Test 2: Force Next Event');
    socket.emit('admin_force_next_event', {'lobby_id': LOBBY_ID}, (r) => {
        console.log('✅ Event forced:', r.event.message_type);
    });
}, 1000);

// Wait 3 seconds, then test trigger decay
setTimeout(() => {
    console.log('\n💔 Test 3: Trigger Stat Decay');
    socket.emit('admin_trigger_stat_decay', {'lobby_id': LOBBY_ID}, (r) => {
        console.log('✅ Decay applied to', r.updated_tributes, 'tributes');
    });
}, 4000);

// Wait 3 seconds, then test force phase
setTimeout(() => {
    console.log('\n⏭️ Test 4: Force Next Phase');
    socket.emit('admin_force_next_phase', {'lobby_id': LOBBY_ID}, (r) => {
        console.log('✅ Phase advanced to:', r.new_phase);
    });
}, 7000);

// Wait 2 seconds, then test update timing
setTimeout(() => {
    console.log('\n⏱️ Test 5: Update Timing');
    socket.emit('admin_update_timing', {
        'timing_updates': {
            'event_cooldowns': {'Combat Events': 10}
        }
    }, (r) => {
        console.log('✅ Timing updated');
    });
}, 9000);

// Wait 2 seconds, then done
setTimeout(() => {
    console.log('\n✅ ALL TESTS COMPLETE');
}, 11000);
```

---

## ❌ Troubleshooting

### Error: "Lobby not found"
**Solution**: 
1. Get correct lobby_id from URL: `http://localhost:8000/game/lobby_X`
2. Use that lobby_id in commands

### Error: "Game engine not initialized"
**Solution**:
1. Make sure game has started (not just created)
2. Wait a few seconds after starting before running admin commands

### Command doesn't respond
**Solution**:
1. Check browser console for errors (F12)
2. Check server console for error messages
3. Verify Socket.IO connection is active (check browser Network tab)

### Stats not updating in game display
**Solution**:
1. Refresh game page (F5)
2. Check if stats updating in console (run `admin_get_tribute_stats`)
3. Restart server and game

---

## 🔍 Verification Checklist

After running all tests, verify:

- [ ] Phase advancement works (`admin_force_next_phase`)
- [ ] Events generate (`admin_force_next_event`)
- [ ] Stats are queryable (`admin_get_tribute_stats`)
- [ ] Stat decay applies correctly (hunger +5, thirst +7, fatigue +4)
- [ ] Timing can be updated (`admin_update_timing`)
- [ ] All players see updates in real-time
- [ ] No errors in browser console
- [ ] No errors in server console
- [ ] Game remains stable after admin commands
- [ ] All responses have correct format

---

## 📞 Support

If tests fail:
1. Check error messages in console
2. Review `ADMIN_CONTROLS_DOCUMENTATION.md` for API details
3. Check `ADMIN_CONTROLS_STATUS.md` for known limitations
4. Review server console for detailed error information

---

**Ready to test!** 🚀
