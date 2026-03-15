# Aurora Engine - Admin Controls Documentation

## Overview

The Aurora Engine now includes comprehensive admin controls accessible via Socket.IO events. These allow game administrators to:

1. **Force Next Event** - Manually trigger the next game event
2. **Force Next Phase** - Immediately advance to the next game phase
3. **Update Timing Configuration** - Modify engine timing values on-the-fly
4. **Get Tribute Stats** - Query current statistics for tributes
5. **Trigger Stat Decay** - Manually apply stat decay to all tributes

## Admin Controls API

### File Location
`Aurora Engine/admin_controls.py` - Core admin control logic
`Aurora Engine/lobby_server.py` - Socket.IO event handlers

### Socket.IO Events

#### 1. Force Next Event
**Event Name**: `admin_force_next_event`

**Request Format**:
```javascript
socket.emit('admin_force_next_event', {
    'lobby_id': 'lobby_123'
}, (response) => {
    console.log('Event forced:', response);
});
```

**Response Format**:
```json
{
    "success": true,
    "event": {
        "message_type": "combat_event",
        "data": {...},
        "timestamp": "2025-10-28T18:30:00"
    },
    "message": "Event forced: combat_event"
}
```

---

#### 2. Force Next Phase
**Event Name**: `admin_force_next_phase`

**Request Format**:
```javascript
socket.emit('admin_force_next_phase', {
    'lobby_id': 'lobby_123'
}, (response) => {
    console.log('Phase advanced:', response);
});
```

**Response Format**:
```json
{
    "success": true,
    "new_phase": "Morning Phase",
    "message": "Phase advanced successfully"
}
```

**What Happens**:
- Phase timer is set to current time (forces immediate phase check)
- `process_game_tick()` is called to process the phase transition
- Stat decay is automatically applied to all tributes
- All players receive phase change notification
- New phase information is broadcast

---

#### 3. Update Timing Configuration
**Event Name**: `admin_update_timing`

**Request Format**:
```javascript
socket.emit('admin_update_timing', {
    'timing_updates': {
        'event_cooldowns': {
            'Combat Events': 20,      // Updated from 45 seconds
            'Arena Events': 30,
            'Idle Events': 15
        },
        'phase_transitions': {
            'cornucopia': 15,         // Updated from 30 minutes
            'day_phase': 30,          // Updated from 60 minutes
            'night_phase': 90         // Updated from 180 minutes
        }
    }
}, (response) => {
    console.log('Timing updated:', response);
});
```

**Response Format**:
```json
{
    "success": true,
    "message": "Timing configuration updated",
    "updated_timings": {
        "event_cooldowns": {...},
        "phase_transitions": {...}
    }
}
```

**Configuration Values**:
- **event_cooldowns**: Seconds between event generations (default 30-60)
- **phase_transitions**: Minutes for each phase type:
  - `cornucopia`: Initial bloodbath phase (default 30 min)
  - `day_phase`: Regular day phases (default 60 min)
  - `night_phase`: Night phases (default 180 min)

---

#### 4. Get Tribute Stats
**Event Name**: `admin_get_tribute_stats`

**Request Format (All Tributes)**:
```javascript
socket.emit('admin_get_tribute_stats', {
    'lobby_id': 'lobby_123'
    // tribute_id omitted = get all tributes
}, (response) => {
    console.log('Tribute stats:', response);
});
```

**Request Format (Specific Tribute)**:
```javascript
socket.emit('admin_get_tribute_stats', {
    'lobby_id': 'lobby_123',
    'tribute_id': 'player_1'
}, (response) => {
    console.log('Tribute stats:', response);
});
```

**Response Format (All Tributes)**:
```json
{
    "success": true,
    "tributes": {
        "player_1": {
            "id": "player_1",
            "name": "Katniss",
            "district": 12,
            "health": 95,
            "sanity": 92,
            "hunger": 5,
            "thirst": 7,
            "fatigue": 4,
            "status": "alive",
            "weapons": ["Bow"],
            "inventory": [...],
            "alliances": ["player_2"],
            ...
        },
        ...
    },
    "count": 3
}
```

**Response Format (Specific Tribute)**:
```json
{
    "success": true,
    "tribute": {
        "id": "player_1",
        "name": "Katniss",
        ...
    }
}
```

---

#### 5. Trigger Stat Decay
**Event Name**: `admin_trigger_stat_decay`

**Request Format**:
```javascript
socket.emit('admin_trigger_stat_decay', {
    'lobby_id': 'lobby_123'
}, (response) => {
    console.log('Stat decay applied:', response);
});
```

**Response Format**:
```json
{
    "success": true,
    "message": "Stat decay applied to all tributes",
    "updated_tributes": 3
}
```

**What Happens**:
- `_apply_phase_end_stat_decay()` is called immediately
- All living tributes receive stat increases:
  - Hunger: +5
  - Thirst: +7
  - Fatigue: +4
  - Sanity: -2 to -8 (based on shelter/fire)
- All players receive updated stat broadcast
- Tributary scoreboards updated in real-time

---

## Implementation Details

### AdminControls Class (`admin_controls.py`)

```python
class AdminControls:
    def __init__(self, aurora_integration, sio, lobby_manager):
        # Initialize with game engine and networking

    async def force_next_event(self, lobby_id: str)
        # Forces immediate event generation

    async def force_next_phase(self, lobby_id: str)
        # Forces phase advancement

    async def update_config_timing(self, timing_updates: Dict)
        # Updates engine configuration

    async def get_tribute_stats(self, lobby_id: str, tribute_id: str = None)
        # Retrieves current tribute statistics

    async def trigger_stat_decay(self, lobby_id: str)
        # Manually applies stat decay
```

### Socket.IO Handler Functions (`lobby_server.py`)

```python
@sio.event
async def admin_force_next_event(sid, data)

@sio.event
async def admin_force_next_phase(sid, data)

@sio.event
async def admin_update_timing(sid, data)

@sio.event
async def admin_get_tribute_stats(sid, data)

@sio.event
async def admin_trigger_stat_decay(sid, data)
```

---

## Usage Example

### Test Script
```python
import socketio
import asyncio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')
    
    # Force next event
    sio.emit('admin_force_next_event', {
        'lobby_id': 'lobby_123'
    }, callback=lambda response: print('Event response:', response))

async def main():
    await sio.connect('http://localhost:8000', 
                     transports=['websocket', 'polling'])
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())
```

### Web UI Integration
```javascript
// Admin dashboard function
async function triggerPhaseAdvance() {
    const lobbyId = getCurrentLobbyId();
    
    socket.emit('admin_force_next_phase', {
        'lobby_id': lobbyId
    }, (response) => {
        if (response.success) {
            console.log('✅ Phase advanced to:', response.new_phase);
            // Update UI to show new phase
        } else {
            console.error('❌ Failed:', response.error);
        }
    });
}
```

---

## Authorization

Currently, admin controls use basic checks (presence of `lobby_id`). For production deployment, add proper authentication:

1. **Admin Token/Key**: Require admin authorization token in requests
2. **Role-Based Access**: Check user role before allowing admin commands
3. **Audit Logging**: Log all admin actions with timestamps and user IDs

Example implementation:
```python
# In Socket.IO handler
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change_me')

@sio.event
async def admin_force_next_phase(sid, data):
    if data.get('admin_key') != ADMIN_PASSWORD:
        return {'success': False, 'error': 'Unauthorized'}
    
    # Process admin command...
```

---

## Benefits

1. **Dynamic Game Control**: Adjust game pacing without restarting server
2. **Testing**: Easily test different game scenarios and timings
3. **Event Verification**: Check if events are being generated correctly
4. **Stat Monitoring**: Monitor tribute stats in real-time
5. **Admin Actions**: Force phase transitions for game demos or tournaments
6. **Configuration Adjustment**: Modify timing values for different game modes

---

## Troubleshooting

### Admin Command Returns Error
- Verify `lobby_id` is correct
- Check Aurora Engine is initialized for the lobby
- Review server console for detailed error messages

### Stats Not Updating
- Confirm Socket.IO event was received (check browser console)
- Verify tribute IDs match between engine and requests
- Check if tributes are alive (dead tributes don't update)

### Timing Changes Not Applied
- Verify new timing values are valid (in minutes or seconds)
- Check config structure matches expected format
- Restart current game to see full effect of timing changes
