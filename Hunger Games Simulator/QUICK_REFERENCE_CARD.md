# 📖 Quick Reference Card - Aurora Engine Admin Controls

## 🚀 Quick Start (2 min)

**Start Server**:
```bash
cd "h:\Hunger Games Simulator\Aurora Engine"
python lobby_server.py
```

**Open Browser**: `http://localhost:8000`

**Create Game** → **Start Game** → **Open Console (F12)** → **Test Commands**

---

## 🧪 5 Admin Commands

### 1️⃣ Force Next Event
```javascript
socket.emit('admin_force_next_event', {'lobby_id': 'lobby_1'})
```
- Generates event immediately
- Updates all players

### 2️⃣ Force Next Phase
```javascript
socket.emit('admin_force_next_phase', {'lobby_id': 'lobby_1'})
```
- Advances to next phase instantly
- Applies stat decay automatically

### 3️⃣ Get Tribute Stats
```javascript
socket.emit('admin_get_tribute_stats', {'lobby_id': 'lobby_1'})
```
- Returns all tributes with stats
- Or add `'tribute_id': 'player_1'` for single tribute

### 4️⃣ Trigger Stat Decay
```javascript
socket.emit('admin_trigger_stat_decay', {'lobby_id': 'lobby_1'})
```
- Manually applies decay
- Hunger +5, Thirst +7, Fatigue +4

### 5️⃣ Update Timing
```javascript
socket.emit('admin_update_timing', {
    'timing_updates': {
        'event_cooldowns': {'Combat Events': 10}
    }
})
```
- Updates config values on-the-fly
- Takes effect immediately

---

## 📊 Expected Stat Decay

| Stat | Increase | Per |
|------|----------|-----|
| Hunger | +5 | Phase |
| Thirst | +7 | Phase |
| Fatigue | +4 | Phase |

---

## 📚 Documentation Map

| Need | File |
|------|------|
| Quick test | `ADMIN_CONTROLS_QUICK_TEST.md` |
| API details | `ADMIN_CONTROLS_DOCUMENTATION.md` |
| Status check | `ADMIN_CONTROLS_STATUS.md` |
| Architecture | `COMPLETE_IMPLEMENTATION_FLOW.md` |
| Overview | `IMPLEMENTATION_COMPLETE_SUMMARY.md` |
| Navigation | `DOCUMENTATION_INDEX.md` |

---

## ✅ Test Checklist

- [ ] Start server (shows Uvicorn running)
- [ ] Create lobby and add tributes
- [ ] Start game
- [ ] Open browser console (F12)
- [ ] Run: Force Next Phase
- [ ] Verify: Phase advances, stats increase
- [ ] Run: Get Tribute Stats
- [ ] Verify: Stats show increases
- [ ] Run: Force Next Event
- [ ] Verify: Event generates, all players see it
- [ ] Run: Trigger Stat Decay
- [ ] Verify: Stats increase by expected amounts

---

## 🔧 Files Modified/Created

```
✅ admin_controls.py               (NEW - 209 lines)
✅ lobby_server.py                 (UPDATED - +120 lines)
✅ config.json                     (UPDATED - stat_decay_rates)
✅ aurora_integration.py           (FIXED - phase logic)
✅ test_aurora_integration.py      (NEW - passing ✅)
✅ test_phase_debug.py             (NEW - passing ✅)
✅ test_complete_game.py           (NEW - passing ✅)
```

---

## 🎯 Key Numbers

| Metric | Value |
|--------|-------|
| Admin Commands | 5 |
| Test Files | 3 (all passing) |
| Documentation Files | 7 |
| Total New Code | 350+ lines |
| Documentation Lines | 1700+ |

---

## ❌ Troubleshooting

**"Lobby not found"**
→ Check lobby_id in URL (http://localhost:8000/game/lobby_X)

**Stats not updating**
→ Verify game started (not just created)
→ Wait a few seconds before testing

**Command doesn't respond**
→ Open F12 to check console errors
→ Check server console for errors
→ Restart server and try again

---

## 📞 Where to Get Help

| Question | Answer |
|----------|--------|
| "How do I test?" | Read: `ADMIN_CONTROLS_QUICK_TEST.md` |
| "What's the API?" | Read: `ADMIN_CONTROLS_DOCUMENTATION.md` |
| "What was fixed?" | Read: `IMPLEMENTATION_COMPLETE_SUMMARY.md` |
| "How does it work?" | Read: `COMPLETE_IMPLEMENTATION_FLOW.md` |
| "Where's the code?" | Check: `Aurora Engine/admin_controls.py` |

---

## 🚀 Next Steps

1. ✅ Test admin controls (15 min)
2. ⬜ Implement admin authorization (30 min)
3. ⬜ Add Event Narrative Display (1 hour)
4. ⬜ Create admin dashboard (2 hours)

---

**Status**: ✅ READY FOR TESTING

**Last Updated**: [Current Session]

Quick reference for Aurora Engine Admin Control System
