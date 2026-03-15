# Custom Tribute Configuration System

The Hunger Games Simulator now supports custom tribute configurations with predefined relationships, biases, and strategic targeting.

## Features

- **Custom Tribute Definitions**: Pre-define tributes with specific attributes, skills, weapons, and preferences
- **Relationship System**: Define alliances, rivalries, and enmities between tributes
- **Bias Factors**: Relationships influence combat targeting, alliance formation, and event probabilities
- **Weapon Preferences**: Tributes can have preferred weapons they actively seek
- **Strategic Gameplay**: More realistic tribute behavior based on predefined motivations

## Configuration File: `data/tribute_upload.json`

### Structure

```json
{
    "description": "Custom tribute configurations and relationships",
    "version": "1.0",
    "custom_tributes": [
        {
            "name": "Tribute Name",
            "district": 1,
            "skills": {
                "strength": 8,
                "stealth": 7,
                "intelligence": 6,
                "survival": 9,
                "combat": 8
            },
            "weapons": ["Sword"],
            "preferred_weapon": "Sword",
            "target_weapon": "Gun",
            "health": 100,
            "sanity": 95,
            "speed": 8,
            "has_camp": false,
            "relationships": {
                "Other Tribute": {
                    "type": "ally",
                    "bias_factor": 2.0,
                    "description": "Close hunting partner"
                }
            }
        }
    ],
    "relationship_types": {
        "ally": {
            "description": "Trusted partners who help each other",
            "combat_bias": -0.8,
            "alliance_chance": 3.0,
            "attack_chance": 0.1
        },
        "enemy": {
            "description": "Active targets for elimination",
            "combat_bias": 2.5,
            "alliance_chance": 0.1,
            "attack_chance": 2.0
        },
        "rival": {
            "description": "Competitive relationships",
            "combat_bias": 1.2,
            "alliance_chance": 0.5,
            "attack_chance": 1.5
        }
    },
    "global_settings": {
        "relationship_influence": 1.0,
        "bias_randomization": 0.2,
        "enable_custom_tributes": true
    }
}
```

### Tribute Fields

- `name`: Tribute's full name
- `district`: District number (1-12)
- `skills`: Object with skill values (1-10)
- `weapons`: Array of starting weapons
- `preferred_weapon`: Weapon the tribute prefers to use
- `target_weapon`: Specific weapon the tribute is hunting for
- `health`: Starting health (default: 100)
- `sanity`: Starting sanity (default: 100)
- `speed`: Speed stat (default: 5)
- `has_camp`: Whether they start with a camp
- `relationships`: Object mapping other tribute names to relationship data

### Relationship Fields

- `type`: Relationship type (defined in `relationship_types`)
- `bias_factor`: Multiplier for interaction probabilities
- `description`: Human-readable relationship description

### Relationship Types

- **ally**: Low combat bias, high alliance chance
- **enemy**: High combat bias, low alliance chance
- **rival**: Moderate combat bias
- **neutral**: Default behavior
- **family**: Very low combat bias, high alliance chance

## How It Works

1. **Loading**: The system checks for `tribute_upload.json` on startup
2. **Selection**: Prompts user to use custom configuration or generate random tributes
3. **Bias Application**:
   - Combat targeting favors enemies and avoids allies
   - Alliance formation prefers allies and avoids enemies
   - Weapon interactions consider relationship biases
4. **Dynamic Behavior**: Tributes behave according to their predefined relationships

## Example Scenarios

### The Hunger Games (Katniss, Gale, Snow)

```json
{
    "name": "Katniss Everdeen",
    "relationships": {
        "Gale Hawthorne": {"type": "ally", "bias_factor": 2.0},
        "President Snow": {"type": "enemy", "bias_factor": 3.0}
    }
}
```

This creates a simulation where:
- Katniss and Gale are likely to ally and avoid fighting each other
- Katniss will preferentially target Snow in combat
- Gale will help Katniss and may also target Snow

### District Rivalries

```json
{
    "name": "District 1 Tribute",
    "relationships": {
        "District 2 Tribute": {"type": "rival", "bias_factor": 1.5},
        "District 11 Tribute": {"type": "neutral", "bias_factor": 1.0}
    }
}
```

## Usage

1. Create or edit `data/tribute_upload.json`
2. Run the simulator
3. Choose "y" when prompted to use custom configuration
4. Watch as tributes behave according to their predefined relationships!

## Advanced Features

- **Bias Randomization**: Adds variability to prevent predictable behavior
- **Weapon Targeting**: Tributes seek specific weapons based on preferences
- **Dynamic Alliances**: Relationships can change based on events (betrayal, etc.)
- **Strategic Depth**: Creates more engaging, story-driven gameplay