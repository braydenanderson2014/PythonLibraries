# Game Page - Visual Layout Guide

## Current Implementation

### Player View (Non-Host)
```
┌─────────────────────────────────────────────────────────────┐
│  Hunger Games Simulator                    [Connected] ✓    │
│                    Hunger Games - Round 1                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │ Your Current Tribute │    │                          │  │
│  │ Status               │    │   Game Log (Events)      │  │
│  │ ────────────────────│    │                          │  │
│  │ Name: Katniss       │    │  [Timestamp] Event 1     │  │
│  │ District: 12        │    │  [Timestamp] Event 2     │  │
│  │ Age: 16             │    │  [Timestamp] Event 3     │  │
│  │ Gender: Female      │    │                          │  │
│  │                     │    │                          │  │
│  │ Skills:             │    │                          │  │
│  │ ├─ Hunting    [9/10]│    │                          │  │
│  │ ├─ Survival   [8/10]│    │                          │  │
│  │ ├─ Agility    [7/10]│    │                          │  │
│  │ └─ Endurance  [7/10]│    │                          │  │
│  │                     │    │                          │  │
│  │ District Bonuses:   │    │                          │  │
│  │ ├─ Hunting: +2      │    │                          │  │
│  │ └─ Survival: +1     │    │                          │  │
│  └──────────────────────┘    └──────────────────────────┘  │
│                                                              │
│                  Remaining Tributes                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ │
│  │ Tribute Card 1  │ │ Tribute Card 2  │ │ Tribute Card 3
│  │ ────────────────│ │ ────────────────│ │ ──────────────│ │
│  │ Name: Peeta     │ │ Name: Cato      │ │ Name: Clove   │ │
│  │ D01 │ 16 │ Male │ │ D02 │ 18 │ Male │ │ D02 │ 17 │ F   │ │
│  │                 │ │                 │ │                 │ │
│  │ Skills:         │ │ Skills:         │ │ Skills:         │ │
│  │ Strength: [8]  │ │ Strength: [9]   │ │ Dexterity: [9]  │ │
│  │ Agility:  [7]  │ │ Agility:  [8]   │ │ Strength:  [7]  │ │
│  │ Survival: [6]  │ │ Survival: [7]   │ │ Survival:  [8]  │ │
│  │ Charisma: [8]  │ │ Charisma: [9]   │ │ Speed:     [9]  │ │
│  │ Endurance:[7]  │ │ Endurance:[8]   │ │ Aim:       [8]  │ │
│  └─────────────────┘ └─────────────────┘ └──────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ │
│  │ Tribute Card 4  │ │ Tribute Card 5  │ │ Tribute Card 6
│  │ ────────────────│ │ ────────────────│ │ ──────────────│ │
│  │ [More tributes continue...]                              │ │
│  └─────────────────┘ └─────────────────┘ └──────────────────┘ │
│                                                              │
│  [Leave Game]                                              │
└─────────────────────────────────────────────────────────────┘
```

### Admin View (Host)
```
Same as above, PLUS:

│  ┌──────────────────────────────────────────────────────┐  │
│  │ ⚙️ Admin Controls                                    │  │
│  │ ────────────────────────────────────────────────────│  │
│  │ Complete the tributes for remaining players:        │  │
│  │                                                      │  │
│  │ [Generate Remaining Tributes]  [Generate Random]    │  │
│  │                                                      │  │
│  │ ✓ Successfully generated 3 tribute(s)!              │  │
│  └──────────────────────────────────────────────────────┘  │
```

---

## Component Breakdown

### 1. Current Player's Tribute Status (Left Sidebar)
- **Location**: Top-left of game page
- **Container**: `#scoreboards-container`
- **Content**:
  - Tribute name (large heading)
  - District, age, gender (badges)
  - All skills with 0-10 ratings
  - District bonuses (if applicable)
- **Styling**: White background, border, shadow
- **Updates**: Real-time when `game_state_update` received

### 2. Game Log (Center)
- **Location**: Center of page
- **Container**: `#game-log`
- **Content**: Arena events, phase changes, player actions
- **Updates**: Real-time as events occur

### 3. Remaining Tributes Grid (Below)
- **Location**: Full width below game log
- **Container**: `#tributes-container`
- **Layout**: Responsive grid (280px minimum per card)
- **Cards Per Row**: ~4 on desktop, 2-3 on tablet, 1 on mobile
- **Content Per Card**:
  - Name (highlighted)
  - District / Age / Gender
  - Top 5 skills with visual bars
  - Special badge for current player's tribute

### 4. Admin Controls Panel (Bottom, Host Only)
- **Location**: Bottom of page
- **Visibility**: Only if user is lobby host
- **Background**: Orange accent (warning color)
- **Buttons**:
  - Generate Remaining Tributes (blue primary)
  - Generate Random Tribute (gray secondary)
- **Status Display**: Shows success/error messages
- **Updates**: Visible after click, shows feedback

---

## Responsive Behavior

### Desktop (1200px+)
- Tributes grid: 4 columns
- Current tribute sidebar: 200px wide
- Game log: Adjusts to fill space

### Tablet (768px - 1199px)
- Tributes grid: 2-3 columns
- Layout adjusts to available width
- Sidebar may float above or beside

### Mobile (< 768px)
- Tributes grid: 1 column (full width)
- Sidebar stacked vertically
- Admin controls full width
- Buttons stack vertically

---

## Data Flow

### Initial Load
```
1. Player joins game
2. Server sends game_state_update with:
   - current_player (user's tribute)
   - game_state.players (all tributes)
3. Client receives and:
   - displayPlayerTributeStats(current_player.tribute_data)
   - displayAllTributes(game_state.players, current_player.id)
4. Admin sees admin controls (if host)
```

### Admin Generates Tributes
```
1. Admin clicks "Generate Remaining Tributes"
2. Client emits: generate_remaining_tributes
3. Server:
   - Validates admin (sid == host_id)
   - Finds players without tributes
   - Generates tributes for each
   - Broadcasts lobby_updated to all
4. All clients receive lobby_updated and refresh display
5. Admin sees success message
```

### Real-time Updates
```
Other player submits tribute:
1. Server receives tributary_done
2. Broadcasts lobby_updated
3. All clients refresh display
4. Current player's tribute status updates immediately
5. Remaining tributes grid refreshes
```

---

## Skill Bar Display

Each skill shows a visual bar from 0-10:
```
Hunting    ████████████████████░░░░░░░░░░░░░░░░░░░░░░  9
Survival   ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  8
Agility    ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  7
```

- Green gradient fill (represents proficiency)
- Rating number on right (0-10)
- Width represents percentage (rating/10 * 100)

---

## Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| Current Player Card | Yellow/Orange | #FFF5E1 to #FFE0B2 |
| Other Tribute Cards | Gray/Blue | #F5F7FA to #C3CFE2 |
| Skill Bars | Green | #4CAF50 |
| Bonus Positive | Green | rgba(76,175,80,0.1) |
| Bonus Negative | Red | rgba(244,67,54,0.1) |
| Admin Panel | Orange | #fff3e0 to #ffe0b2 |
| Buttons | Blue/Gray | var(--primary-color) |

---

## Future Enhancements

### Phase 1 (Current)
- Display tributes ✅
- Admin generate tributes ✅
- Real-time updates ✅

### Phase 2 (Next)
- Search/filter tributes by district
- Sort by skill rating
- Show total power rating (sum of all skills)
- Drag-to-compare tributes

### Phase 3
- Custom tribute editing by admin
- Batch tribute generation with progress
- Tribute elimination view (cross off as they die)
- Tribute stats over time

---

**Status**: ✅ Complete and ready for user testing
