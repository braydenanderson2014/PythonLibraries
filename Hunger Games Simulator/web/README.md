# Hunger Games Simulator - Web Interface

A web-based lobby system for the Hunger Games Simulator that allows players to create lobbies, upload custom tribute JSONs, and run games collaboratively.

## Features

- **Tribute-First Flow**: Players must create their tribute before accessing lobby features
- **Lobby System**: Create and join lobbies with unique codes
- **Admin Controls**: Lobby admins can start games (regular players cannot)
- **Custom Tributes**: Players can upload their own tribute JSON configurations
- **Tribute Creator**: User-friendly form to create tributes with:
  - Custom skill values (1-10) with sliders
  - Weapon selection from all available weapons
  - Automatic target weapon assignment
  - Relationship management with other players
- **Relationship Editing**: Modal-based editing of relationships with first name matching
- **Real-time Updates**: Live lobby status and game progress
- **Multiplayer**: Support for 2-24 players per lobby

## Setup

### Prerequisites

- Python 3.8+
- The main Hunger Games Simulator project

### Installation

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

```bash
python run_server.py
```

The server will start on `http://localhost:5000` with proper logging and error handling.

## API Endpoints

### Lobby Management

- `POST /api/lobby/create` - Create a new lobby
- `POST /api/lobby/<code>/join` - Join an existing lobby
- `GET /api/lobby/<code>` - Get lobby information
- `POST /api/lobby/<code>/upload-tribute` - Upload a custom tribute JSON
- `POST /api/lobby/<code>/start` - Start the game (admin only)

### Game Management

- `GET /api/game/<id>/status` - Get game status
- `POST /api/lobby/cleanup` - Clean up old lobbies

## Usage

### Player Flow

1. **Create Your Tribute** (Required First Step)
   - Customize your tribute's name, district, and skills using sliders
   - Select your preferred weapon from all available options
   - Target weapon is automatically assigned based on your preference

2. **Join or Create a Lobby**
   - After creating your tribute, choose to create a new lobby (as admin) or join an existing one
   - Enter your player name and lobby details

3. **Customize Relationships** (Optional)
   - In the lobby, click "Edit Tribute" to set relationships with other players
   - You can enter just a first name and the system will try to match it to players in the lobby
   - Choose from: Ally, Enemy, Rival, Neutral, Family

4. **Start Game** (Admin Only)
   - Only the lobby admin can start the game
   - All players must have uploaded their tributes before the game can begin

### Tribute Creation Features

#### Skills System
Adjust 10 different skills using intuitive sliders (1-10 scale):
- Intelligence, Hunting, Strength, Social, Stealth, Survival
- Agility, Endurance, Charisma, Luck

#### Weapon Selection
Choose from 18 different weapons:
- Melee: Sword, Axe, Hammer, Knife, Spear, Club, Machete, Dagger, Mace
- Ranged: Bow, Crossbow, Gun, Throwing Star
- Other: Staff, Whip, Stick, Rock, Fists

#### Automatic Features
- **Target Weapon**: Automatically assigned based on preferred weapon
- **Speed Calculation**: Computed from Agility + Endurance skills
- **Health/Sanity**: Start with 100 each

### Creating a Lobby

1. Open the web interface
2. First create your tribute using the form
3. Click "Create Lobby"
4. Enter your name and select max players
5. Share the lobby code with other players

### Joining a Lobby

1. Open the web interface
2. First create your tribute using the form
3. Click "Join Lobby"
4. Enter the lobby code and your name
5. Wait for the admin to start the game

### Uploading Tributes

In the lobby, players have two options for creating tributes:

#### Option 1: Tribute Creator Form
Use the user-friendly form to create tributes with:
- **Skills**: Adjust sliders for Intelligence, Hunting, Strength, Social, Stealth, Survival, Agility, Endurance, Charisma, and Luck (1-10 scale)
- **Weapons**: Select preferred weapon from all available weapons (Sword, Axe, Bow, Hammer, Knife, Spear, Club, Fists, Staff, Machete, Gun, Crossbow, Dagger, Whip, Throwing Star, Stick, Mace, Rock)
- **Relationships**: Set relationships with other players (Ally, Enemy, Rival, Neutral, Family)
- **Automatic Features**: Target weapon is automatically set based on preferred weapon, speed is calculated from skills

#### Option 2: Raw JSON Upload
Paste your tribute JSON data directly using the format shown in the placeholder.

### Starting a Game

The lobby admin can click "Start Game" when ready. The game will run in the background and players can monitor progress.

## Integration with Main Simulator

The web interface integrates with the main Hunger Games simulator by:

1. Collecting tribute JSONs from all players
2. Combining them into the `data/tribute_upload.json` file
3. Running the simulation using the existing game logic
4. Returning results to the web interface

## File Structure

```
web/
├── app.py              # Main Flask application
├── game_runner.py      # Game execution logic
├── run_server.py      # Server launcher with logging
├── test_web_interface.py # Test script for validation
├── requirements.txt    # Python dependencies
└── templates/
    └── index.html      # Web interface
```

## Development

To modify the web interface:

1. Edit `templates/index.html` for UI changes
2. Edit `app.py` for backend API changes
3. Edit `game_runner.py` for game integration logic

## Testing

Run the validation script to test tribute creation and interface components:

```bash
python validate_components.py
```

This validates:
- Weapon availability and selection
- Relationship type validation
- Target weapon assignment logic
- Tribute data structure validation

Run the full web interface test (requires server to be running):

```bash
python test_web_interface.py
```