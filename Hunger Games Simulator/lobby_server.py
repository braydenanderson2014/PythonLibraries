"""
Hunger Games Lobby Server
Example implementation using FastAPI + Socket.IO for lobby management
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import socketio
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

# Data models
@dataclass
@dataclass
class TributeData:
    name: str = ""
    district: Optional[int] = None
    gender: str = "Male"
    age: int = 16
    skills: Dict[str, int] = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = {
                "strength": 5,
                "agility": 5,
                "intelligence": 5,
                "charisma": 5,
                "survival": 5,
                "hunting": 5,
                "social": 5,
                "stealth": 5,
                "endurance": 5,
                "luck": 5
            }

@dataclass
class Player:
    id: str
    name: str
    district: Optional[int] = None
    ready: bool = False
    connected: bool = True
    health: int = 100
    hunger: int = 0
    thirst: int = 0
    alive: bool = True
    tribute_data: Optional[TributeData] = None
    tribute_ready: bool = False

    def __post_init__(self):
        if self.tribute_data is None:
            self.tribute_data = TributeData()

@dataclass
class GameState:
    day: int = 1
    status: str = 'waiting'
    players: List[Player] = None

    def __post_init__(self):
        if self.players is None:
            self.players = []

@dataclass
class Lobby:
    id: str
    name: str
    host_id: str
    players: Dict[str, Player]
    max_players: int = 24
    game_started: bool = False
    game_state: Optional[GameState] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.game_state is None:
            self.game_state = GameState()

    def to_dict(self):
        """Return a JSON-serializable dictionary representation"""
        data = asdict(self)
        # Convert datetime to timestamp
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].timestamp()
        return data

    def get_available_districts(self) -> List[int]:
        """Return list of districts that are available (have less than 2 players)"""
        # Count players per district
        district_counts = {}
        for player in self.players.values():
            if player.tribute_data and player.tribute_data.district is not None:
                district = player.tribute_data.district
                district_counts[district] = district_counts.get(district, 0) + 1

        # Return districts with less than 2 players
        available_districts = []
        for district in range(1, 13):  # Districts 1-12
            if district_counts.get(district, 0) < 2:
                available_districts.append(district)

        return available_districts

# Global state
lobbies: Dict[str, Lobby] = {}
players: Dict[str, Player] = {}
resume_codes: Dict[str, str] = {}  # resume_code -> player_id mapping

def generate_resume_code():
    """Generate a unique 6-character resume code"""
    import string
    import random
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in resume_codes:
            return code

# Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

# FastAPI app
app = FastAPI(title="Hunger Games Lobby Server")

# Templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for serving HTML/JS)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_lobby_page(request: Request):
    """Serve the lobby HTML page"""
    return templates.TemplateResponse("lobby.html", {"request": request})

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # Handle player disconnect
    if sid in players:
        player = players[sid]
        player.connected = False
        # Notify lobby if player was in one
        for lobby in lobbies.values():
            if sid in lobby.players:
                await sio.emit('lobby_updated', {
                    'lobby': lobby.to_dict(),
                    'available_districts': lobby.get_available_districts()
                }, room=lobby.id)
                break

@sio.event
async def create_lobby(sid, data):
    """Handle creating a new lobby"""
    lobby_name = data.get('name', f'Lobby by {sid[:8]}')
    max_players = min(data.get('max_players', 24), 24)  # Cap at 24

    # Generate unique lobby ID
    import uuid
    lobby_id = str(uuid.uuid4())[:8]

    # Create lobby
    lobby = Lobby(
        id=lobby_id,
        name=lobby_name,
        host_id=sid,
        players={},
        max_players=max_players
    )
    lobbies[lobby_id] = lobby

    # Send lobby created event to creator
    await sio.emit('lobby_created', {
        'lobby_id': lobby_id,
        'lobby': lobby.to_dict()
    }, room=sid)

@sio.event
async def join_lobby(sid, data):
    """Handle player joining a lobby"""
    player_name = data.get('name', f'Player_{sid[:8]}')
    lobby_id = data.get('lobby_id')

    if not lobby_id or lobby_id not in lobbies:
        await sio.emit('error', {'message': 'Lobby not found'}, room=sid)
        return

    lobby = lobbies[lobby_id]

    # Check if lobby is full
    if len(lobby.players) >= lobby.max_players:
        await sio.emit('error', {'message': 'Lobby is full'}, room=sid)
        return

    # Create player
    player = Player(id=sid, name=player_name)
    players[sid] = player
    lobby.players[sid] = player

    # Generate resume code
    resume_code = generate_resume_code()
    resume_codes[resume_code] = sid

    # Join socket room
    await sio.enter_room(sid, lobby_id)

    # Send lobby info to player
    await sio.emit('lobby_joined', {
        'player_id': sid,
        'lobby_id': lobby_id,
        'lobby': lobby.to_dict(),
        'available_districts': lobby.get_available_districts(),
        'player': asdict(player),
        'resume_code': resume_code
    }, room=sid)

    # Notify all players in lobby
    await sio.emit('lobby_updated', {
        'lobby': lobby.to_dict(),
        'available_districts': lobby.get_available_districts()
    }, room=lobby_id)

@sio.event
async def resume_lobby(sid, data):
    """Handle player resuming with a resume code"""
    resume_code = data.get('resume_code')

    if not resume_code or resume_code not in resume_codes:
        await sio.emit('error', {'message': 'Invalid resume code'}, room=sid)
        return

    old_player_id = resume_codes[resume_code]

    if old_player_id not in players:
        await sio.emit('error', {'message': 'Player no longer exists'}, room=sid)
        return

    old_player = players[old_player_id]

    # Find which lobby the player was in
    player_lobby = None
    for lobby in lobbies.values():
        if old_player_id in lobby.players:
            player_lobby = lobby
            break

    if not player_lobby:
        await sio.emit('error', {'message': 'Player lobby not found'}, room=sid)
        return

    # Remove old player connection
    if old_player_id in player_lobby.players:
        del player_lobby.players[old_player_id]
    if old_player_id in players:
        del players[old_player_id]

    # Update player ID to new socket ID
    old_player.id = sid
    players[sid] = old_player
    player_lobby.players[sid] = old_player

    # Remove old resume code and generate new one
    del resume_codes[resume_code]
    new_resume_code = generate_resume_code()
    resume_codes[new_resume_code] = sid

    # Join socket room
    await sio.enter_room(sid, player_lobby.id)

    # Send lobby info to player
    await sio.emit('lobby_joined', {
        'player_id': sid,
        'lobby_id': player_lobby.id,
        'lobby': player_lobby.to_dict(),
        'available_districts': player_lobby.get_available_districts(),
        'player': asdict(old_player),
        'resume_code': new_resume_code
    }, room=sid)

    # Notify all players in lobby
    await sio.emit('lobby_updated', {
        'lobby': player_lobby.to_dict(),
        'available_districts': player_lobby.get_available_districts()
    }, room=player_lobby.id)

@sio.event
async def list_lobbies(sid, data=None):
    """Send list of available lobbies to client"""
    print(f"list_lobbies called by client {sid}")
    lobby_list = []
    for lobby in lobbies.values():
        if not lobby.game_started and len(lobby.players) < lobby.max_players:
            lobby_list.append({
                'id': lobby.id,
                'name': lobby.name,
                'host_name': players.get(lobby.host_id, Player(id='', name='Unknown')).name,
                'player_count': len(lobby.players),
                'max_players': lobby.max_players,
                'created_at': lobby.created_at.isoformat() if lobby.created_at else None
            })

    print(f"Sending {len(lobby_list)} lobbies to client {sid}")
    await sio.emit('lobby_list', {'lobbies': lobby_list}, room=sid)

@sio.event
async def toggle_ready(sid, data=None):
    """Handle player toggling ready status"""
    if sid not in players:
        return

    player = players[sid]
    player.ready = not player.ready

    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players:
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            break

@sio.event
async def leave_lobby(sid, data=None):
    """Handle player leaving lobby"""
    if sid not in players:
        return

    # Find player's lobby
    for lobby_id, lobby in list(lobbies.items()):
        if sid in lobby.players:
            del lobby.players[sid]
            await sio.leave_room(sid, lobby.id)

            # If host left, shut down the lobby
            if lobby.host_id == sid:
                # Notify all remaining players that lobby is closing
                await sio.emit('lobby_closed', {
                    'reason': 'Host left the lobby'
                }, room=lobby.id)
                # Remove the lobby
                del lobbies[lobby_id]
            else:
                # Regular player left, update lobby
                await sio.emit('lobby_updated', {
                    'lobby': lobby.to_dict(),
                    'available_districts': lobby.get_available_districts()
                }, room=lobby.id)
            break

    # Remove player
    if sid in players:
        del players[sid]

@sio.event
async def start_game(sid, data=None):
    """Handle game start request"""
    # Find player's lobby
    lobby = None
    for l in lobbies.values():
        if sid in l.players and sid == l.host_id:
            lobby = l
            break

    if not lobby:
        return

    # Check if at least 2 players have completed tribute creation
    ready_count = sum(1 for p in lobby.players.values() if p.tribute_ready)
    if ready_count < 2:
        await sio.emit('game_start_failed', {
            'reason': f'Need at least 2 players ready to start. Currently {ready_count} players ready.'
        }, room=sid)
        return

    # Start the game
    lobby.game_started = True

    # Initialize game state with tribute data
    lobby.game_state = GameState(
        day=1,
        status='starting',
        players=[p for p in lobby.players.values()]
    )

    # Notify all players
    await sio.emit('game_started', {'lobby_id': lobby.id}, room=lobby.id)

    # Start game simulation in background
    asyncio.create_task(run_game_simulation(lobby))

@sio.event
async def player_action(sid, data):
    """Handle player action during game"""
    action = data.get('action')
    if not action:
        return

    # Find player's lobby
    lobby = None
    for l in lobbies.values():
        if sid in l.players and l.game_started:
            lobby = l
            break

    if not lobby:
        return

    # Process action (simplified - in real implementation, this would integrate with game logic)
    player = lobby.players.get(sid)
    if not player or not player.alive:
        return

    # Send action confirmation
    await sio.emit('action_processed', {
        'player_id': sid,
        'action': action,
        'message': f'{player.name} performed action: {action}'
    }, room=lobby.id)

@sio.event
async def request_game_state(sid, data=None):
    """Send current game state to player"""
    # Find player's lobby
    lobby = None
    for l in lobbies.values():
        if sid in l.players and l.game_started:
            lobby = l
            break

    if not lobby:
        return

    await sio.emit('game_state_update', {
        'game_state': asdict(lobby.game_state),
        'current_player': asdict(lobby.players.get(sid))
    }, room=sid)

@sio.event
async def join_as_spectator(sid, data=None):
    """Handle spectator joining"""
    # For now, join the main lobby as spectator
    lobby_id = 'main_lobby'
    if lobby_id in lobbies:
        lobby = lobbies[lobby_id]
        await sio.enter_room(sid, lobby_id)

        # Send current game state if game is running
        if lobby.game_started:
            await sio.emit('spectator_update', {
                'game_state': asdict(lobby.game_state)
            }, room=sid)

@sio.event
async def leave_spectator(sid, data=None):
    """Handle spectator leaving"""
    lobby_id = 'main_lobby'
    if lobby_id in lobbies:
        await sio.leave_room(sid, lobby_id)

def apply_district_modifiers(skills, district):
    """Apply district-based skill modifiers"""
    # District-based skill modifiers (+/- values)
    district_traits = {
        1: { 'social': 2, 'charisma': 2, 'survival': -1, 'hunting': -1 }, # Luxury/Commerce
        2: { 'strength': 2, 'endurance': 2, 'stealth': -1, 'charisma': -1 }, # Masonry/Stone
        3: { 'intelligence': 2, 'agility': 1, 'strength': -1, 'endurance': -1 }, # Technology
        4: { 'agility': 2, 'hunting': 1, 'intelligence': -1, 'social': -1 }, # Fishing
        5: { 'intelligence': 2, 'endurance': 1, 'social': -1, 'charisma': -1 }, # Power
        6: { 'endurance': 2, 'strength': 1, 'intelligence': -1, 'agility': -1 }, # Transportation
        7: { 'strength': 2, 'endurance': 1, 'social': -1, 'charisma': -1 }, # Lumber
        8: { 'agility': 2, 'intelligence': 1, 'strength': -1, 'endurance': -1 }, # Textiles
        9: { 'endurance': 2, 'survival': 1, 'hunting': -1, 'intelligence': -1 }, # Grain
        10: { 'survival': 2, 'endurance': 1, 'charisma': -1, 'social': -1 }, # Livestock
        11: { 'survival': 2, 'strength': 1, 'intelligence': -1, 'charisma': -1 }, # Agriculture
        12: { 'endurance': 2, 'strength': 1, 'charisma': -1, 'social': -1 } # Coal Mining
    }

    modifiers = district_traits.get(district, {})
    modified_skills = {}

    for skill, base_rating in skills.items():
        modifier = modifiers.get(skill, 0)
        modified_skills[skill] = max(1, min(10, base_rating + modifier))

    return modified_skills

@sio.event
async def update_tribute(sid, data):
    """Handle tribute data updates"""
    if sid not in players:
        return

    player = players[sid]
    tribute_data = data.get('tribute_data', {})

    # Update tribute data with validation
    if 'name' in tribute_data and tribute_data['name'] is not None:
        player.tribute_data.name = str(tribute_data['name'])
    if 'district' in tribute_data and tribute_data['district'] is not None:
        try:
            player.tribute_data.district = int(tribute_data['district'])
        except (ValueError, TypeError):
            pass  # Keep existing value
    if 'gender' in tribute_data and tribute_data['gender'] is not None:
        player.tribute_data.gender = str(tribute_data['gender'])
    if 'age' in tribute_data and tribute_data['age'] is not None:
        try:
            player.tribute_data.age = int(tribute_data['age'])
        except (ValueError, TypeError):
            pass  # Keep existing value
    if 'skills' in tribute_data and tribute_data['skills'] is not None and isinstance(tribute_data['skills'], dict):
        # Apply district modifiers to skills
        modified_skills = apply_district_modifiers(tribute_data['skills'], player.tribute_data.district)
        player.tribute_data.skills = modified_skills  # Replace entirely instead of updating

    # Notify player of successful update
    await sio.emit('tribute_updated', {
        'tribute_data': asdict(player.tribute_data)
    }, room=sid)

    # Notify all players in lobby about district availability changes
    for lobby in lobbies.values():
        if sid in lobby.players:
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            break

@sio.event
async def tribute_done(sid, data=None):
    """Handle player marking tribute creation as complete"""
    if sid not in players:
        return

    player = players[sid]
    player.tribute_ready = True

    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players:
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            break

@sio.event
async def tribute_not_done(sid, data=None):
    """Handle player unmarking tribute as ready"""
    if sid not in players:
        return

    player = players[sid]
    player.tribute_ready = False

    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players:
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            break

async def run_game_simulation(lobby: Lobby):
    """Run the Hunger Games simulation and send updates"""
    try:
        # Import and run the simulator
        import subprocess
        import sys

        # Run the simulator in web mode
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'main.py', '--tributes', str(len(lobby.players)), '--fast',
            env={**os.environ, 'HUNGER_GAMES_PROGRESSION_MODE': 'web'},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Monitor the web output file for updates
        web_output_file = 'data/web_output.json'

        last_update_time = 0
        while True:
            if os.path.exists(web_output_file):
                try:
                    # Check file modification time
                    mod_time = os.path.getmtime(web_output_file)
                    if mod_time > last_update_time:
                        with open(web_output_file, 'r') as f:
                            data = json.load(f)

                        # Update lobby game state
                        if 'day' in data:
                            lobby.game_state.day = data['day']
                        if 'status' in data:
                            lobby.game_state.status = data['status']

                        # Update player states if available
                        if 'players' in data:
                            for player_data in data['players']:
                                player_id = player_data.get('id')
                                if player_id in lobby.players:
                                    player = lobby.players[player_id]
                                    player.health = player_data.get('health', player.health)
                                    player.hunger = player_data.get('hunger', player.hunger)
                                    player.thirst = player_data.get('thirst', player.thirst)
                                    player.alive = player_data.get('alive', player.alive)

                        # Send game update to all players
                        await sio.emit('game_update', {
                            'status': data.get('status', 'running'),
                            'message': data.get('message', ''),
                            'timestamp': datetime.now().timestamp()
                        }, room=lobby.id)

                        # Send updated game state
                        for player_id in lobby.players:
                            await sio.emit('game_state_update', {
                                'game_state': asdict(lobby.game_state),
                                'current_player': asdict(lobby.players[player_id])
                            }, room=player_id)

                        last_update_time = mod_time

                except (json.JSONDecodeError, FileNotFoundError, KeyError):
                    pass

            await asyncio.sleep(0.5)  # Check every 500ms

            # Check if process is still running
            if process.returncode is not None:
                break

        # Game finished
        lobby.game_state.status = 'completed'
        await sio.emit('game_update', {
            'status': 'completed',
            'message': 'Game simulation completed!',
            'timestamp': datetime.now().timestamp()
        }, room=lobby.id)

    except Exception as e:
        print(f"Error running game simulation: {e}")
        lobby.game_state.status = 'error'
        await sio.emit('game_update', {
            'status': 'error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().timestamp()
        }, room=lobby.id)

# Mount the Socket.IO app
app.mount("/", socket_app)

if __name__ == "__main__":
    import uvicorn
    print("Starting Hunger Games Lobby Server...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)