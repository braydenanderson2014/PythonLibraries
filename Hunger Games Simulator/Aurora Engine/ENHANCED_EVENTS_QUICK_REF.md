# Aurora Engine - Enhanced Events Quick Reference

## 🚀 Getting Started

```bash
# Start the enhanced server
cd "Aurora Engine"
python lobby_server.py

# Test the enhancement system
python test_enhanced_events.py
```

## 📡 Client Integration

### Receiving Enhanced Events

```javascript
// Client-side Socket.IO handler
socket.on('game_update', (data) => {
    const message = data.message;
    
    // Event metadata
    const category = message.category;        // "death", "combat", "survival", etc
    const priority = message.priority;        // 1-5 (5 = critical)
    const messageType = message.message_type; // "enhanced_game_event", etc
    
    // Rich content
    const title = message.data.title;           // Short, punchy headline
    const narrative = message.data.narrative;   // Full dramatic description
    const consequences = message.data.consequences; // ["Player X killed", etc]
    
    // Display hints
    const hints = message.data.style_hints;
    const duration = hints.display_duration;    // Milliseconds to show
    const color = hints.highlight_color;        // Hex color code
    const sound = hints.sound_effect;           // "cannon", "gong", etc
    
    // Display the event based on category/priority
    displayEvent(title, narrative, {category, priority, hints});
});
```

### Example Enhanced Event

```json
{
  "message_type": "enhanced_game_event",
  "category": "death",
  "priority": 5,
  "data": {
    "title": "💀 Katniss Everdeen has fallen",
    "narrative": "Eyes lock across the clearing...",
    "participants": [...],
    "consequences": ["💀 Katniss Everdeen was killed"],
    "style_hints": {
      "importance": "critical",
      "display_duration": 5000,
      "highlight_color": "#cc0000",
      "sound_effect": "cannon"
    }
  }
}
```

## 📋 Event Categories Reference

| Category | Icon | Priority | Description | Display Time |
|----------|------|----------|-------------|--------------|
| **death** | 💀 | Critical (5) | Tribute eliminated | 5000ms |
| **combat** | ⚔️ | High (4) | Fight encounters | 3000ms |
| **injury** | 🩹 | High (4) | Significant wounds | 3000ms |
| **alliance** | 🤝 | High (4) | Partnerships formed | 3000ms |
| **arena_event** | 🎬 | High (4) | Gamemaker intervention | 4000ms |
| **sponsor** | 🎁 | High (4) | Supply drops | 3000ms |
| **survival** | 🏹 | Medium (3) | Hunting, foraging | 2000ms |
| **exploration** | 🔍 | Medium (3) | Discovery, travel | 2000ms |
| **phase** | 🌅 | Medium (3) | Time transitions | 3000ms |
| **social** | 💭 | Low (2) | Character moments | 2000ms |
| **status** | 📊 | Minimal (1) | Technical updates | 2000ms |

## 🎨 UI Display Recommendations

### Critical Events (Deaths)
```css
.event-death {
  background: linear-gradient(to right, #660000, #cc0000);
  color: white;
  font-size: 1.2em;
  padding: 20px;
  animation: dramatic-entrance 1s ease-out;
  display-duration: 5s;
}
```

### High Priority (Combat/Arena)
```css
.event-high-priority {
  background: linear-gradient(to right, #ff6600, #ffaa00);
  border: 2px solid #ff0000;
  font-size: 1.1em;
  padding: 15px;
}
```

### Medium Priority (Survival)
```css
.event-medium-priority {
  background: rgba(100, 150, 100, 0.2);
  border-left: 4px solid #66cc66;
  padding: 10px;
}
```

## 🔊 Sound Effects Mapping

```javascript
const SOUND_EFFECTS = {
  'cannon': 'boom.mp3',      // Death announcement
  'gong': 'gong.mp3',        // Cornucopia start
  'gift': 'parachute.mp3',   // Sponsor drop
  'alarm': 'alert.mp3',      // Arena event
};

function playSound(effect) {
  if (SOUND_EFFECTS[effect]) {
    new Audio(SOUND_EFFECTS[effect]).play();
  }
}
```

## ⏱️ Server Pacing System

The server automatically spaces events based on importance:

| Event Type | Delay | Purpose |
|------------|-------|---------|
| Death | 3.5s | Let impact sink in |
| Combat | 2.0s | Build tension |
| Arena Event | 2.5s | Emphasize drama |
| Phase Change | 1.5s | Mark transition |
| Survival | 0.8s | Keep flow |
| Status | 0.4s | Quick updates |

## 🎯 Filtering Events

```javascript
// Filter by category
const deathEvents = events.filter(e => e.category === 'death');
const combatEvents = events.filter(e => e.category === 'combat');

// Filter by priority
const criticalEvents = events.filter(e => e.priority >= 4);

// Create death feed
const deathFeed = events
  .filter(e => e.category === 'death')
  .map(e => e.data.title);

// Create highlight reel
const highlights = events
  .filter(e => e.priority >= 4)
  .sort((a, b) => b.priority - a.priority);
```

## 🎬 Example Display Implementations

### Simple Event Log
```javascript
function addToGameLog(message) {
  const category = message.category || 'status';
  const title = message.data?.title || 'Event';
  const narrative = message.data?.narrative || '';
  
  const eventDiv = document.createElement('div');
  eventDiv.className = `game-event event-${category}`;
  eventDiv.innerHTML = `
    <h4>${title}</h4>
    <p>${narrative}</p>
  `;
  
  gameLog.prepend(eventDiv);
  
  // Auto-scroll to new event
  eventDiv.scrollIntoView({behavior: 'smooth'});
  
  // Play sound if specified
  const sound = message.data?.style_hints?.sound_effect;
  if (sound) playSound(sound);
}
```

### Dramatic Announcement Overlay
```javascript
function showDramaticEvent(message) {
  if (message.priority < 4) return; // Only for high/critical
  
  const overlay = document.createElement('div');
  overlay.className = 'dramatic-overlay';
  overlay.innerHTML = `
    <div class="dramatic-content ${message.category}">
      <h1>${message.data.title}</h1>
      <p class="narrative">${message.data.narrative}</p>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Fade in
  setTimeout(() => overlay.classList.add('show'), 100);
  
  // Auto-dismiss after display duration
  const duration = message.data.style_hints?.display_duration || 3000;
  setTimeout(() => {
    overlay.classList.remove('show');
    setTimeout(() => overlay.remove(), 1000);
  }, duration);
}
```

### Death Counter/Tracker
```javascript
const deathTracker = {
  deaths: [],
  
  addDeath(message) {
    if (message.category !== 'death') return;
    
    const victim = message.data.victim;
    this.deaths.push({
      name: victim.name,
      district: victim.district,
      killer: message.data.killer,
      timestamp: message.timestamp
    });
    
    this.updateDisplay();
  },
  
  updateDisplay() {
    document.getElementById('death-count').textContent = this.deaths.length;
    document.getElementById('remaining-count').textContent = 
      24 - this.deaths.length;
  }
};
```

## 🔥 Advanced: Event Animation

```css
@keyframes dramatic-entrance {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(-50px);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes cannon-flash {
  0%, 100% { background: #cc0000; }
  50% { background: #ff0000; }
}

.event-death {
  animation: dramatic-entrance 1s ease-out,
             cannon-flash 0.5s ease-in-out 3;
}
```

## 📝 Notes

- All events are **enhanced automatically** by the server
- **No client-side processing** needed for narratives
- **Backward compatible** - old message types still work
- **Extensible** - easy to add new display styles
- **Performance optimized** - events pre-formatted server-side

## 🐛 Debugging

```javascript
// Log all events for debugging
socket.on('game_update', (data) => {
  console.log('Event:', {
    type: data.message.message_type,
    category: data.message.category,
    priority: data.message.priority,
    title: data.message.data?.title
  });
});

// Monitor pacing
let lastEventTime = Date.now();
socket.on('game_update', (data) => {
  const now = Date.now();
  const delay = now - lastEventTime;
  console.log(`Event delay: ${delay}ms`);
  lastEventTime = now;
});
```

## 💡 Best Practices

1. **Use categories for styling** - Different colors/icons per category
2. **Respect display durations** - Don't dismiss events too quickly
3. **Play appropriate sounds** - Enhance immersion
4. **Highlight critical events** - Deaths should be unmissable
5. **Maintain event history** - Let users review past events
6. **Smooth animations** - Make transitions feel polished
7. **Mobile-friendly** - Ensure events display well on all screens

---

For full documentation, see [ENHANCEMENT_SUMMARY.md](./ENHANCEMENT_SUMMARY.md)
