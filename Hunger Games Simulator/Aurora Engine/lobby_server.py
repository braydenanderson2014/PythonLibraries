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
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime
import json
import os
from jinja2 import Environment, FileSystemLoader
from jinja2 import Environment, FileSystemLoader

# Import admin controls
from admin_controls import AdminControls

# Custom JSON encoder for dataclasses
class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)

def serialize_for_socket(obj):
    """Convert objects to JSON-serializable format for Socket.IO"""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_socket(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_socket(item) for item in obj]
    return obj

# Load district bonuses configuration
DISTRICT_BONUSES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "district_bonuses.json")

def load_district_bonuses():
    """Load district bonuses from JSON file"""
    try:
        with open(DISTRICT_BONUSES_FILE, 'r') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load district bonuses: {e}")
        # Fallback to hardcoded values
        return {
            "district_bonuses": {
                str(i): {"bonuses": {}} for i in range(1, 13)
            },
            "trait_scoring": {}
        }

district_config = load_district_bonuses()

# Data models
@dataclass
class TributeData:
    name: str = ""
    district: int = 1
    gender: str = "Male"
    age: int = 16
    skills: Dict[str, int] = None
    skill_priority: List[str] = None  # Ordered list of skill names by priority
    preferred_weapon: str = "fists"  # Preferred weapon ID

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
        if self.skill_priority is None:
            self.skill_priority = []

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
    simulation_started: bool = False  # Flag to prevent running simulation multiple times
    game_state: Optional[GameState] = None
    client_ready_status: Optional[Dict[str, bool]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.client_ready_status is None:
            self.client_ready_status = {}
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
        # Count players per district (only count players who have completed tribute creation)
        district_counts = {}
        for player in self.players.values():
            if player.tribute_ready and player.tribute_data and player.tribute_data.district:
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

# Socket.IO server with enhanced configuration for reliability
# ALIGNED TIMEOUT VALUES: Both client and server use 30s connection timeout
# Increased from 20s to allow for game phase transitions and heavy processing
# This prevents disconnects during cornucopia countdown (60s) and phase transitions
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    cors_credentials=True,
    logger=True,
    engineio_logger=True,
    # CRITICAL: Synchronized timeout values (must match client app.js timeout: 30000)
    ping_timeout=30,  # Server waits 30s before considering connection dead (allows game processing)
    ping_interval=8,  # Send ping every 8s (~3 pings before timeout) to keep connection alive
    max_http_buffer_size=1000000,
    allow_upgrades=True,
    cookie=False,  # Disable cookies for better proxy compatibility
    # Additional stability options
    always_connect=False,
    # TRANSPORT PRIORITY: Use polling-first for proxy/tunnel stability, WebSocket as fallback
    # This gives us stable long-polling by default with WebSocket upgrade available
    transports=['polling', 'websocket'],
    allowEIO3=True,
    # IMPORTANT: Disable upgrade on proxied connections (Cloudflare Tunnel, port forwarding)
    # Only allow upgrades on localhost to prevent connection disruptions through proxies
    upgrade_mode='probe'  # Probe upgrade but don't force if it fails
)
socket_app = socketio.ASGIApp(sio)

# FastAPI app
app = FastAPI(title="Hunger Games Lobby Server")

# Add CORS middleware for better proxy compatibility
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Cloudflare Tunnel compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for WebSocket proxy headers
@app.middleware("http")
async def add_websocket_headers(request, call_next):
    response = await call_next(request)
    # Add headers that help with WebSocket connections through proxies
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    # Additional headers for Cloudflare Tunnel compatibility
    response.headers["X-Accel-Buffering"] = "no"  # Disable buffering for real-time connections
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for serving HTML/JS)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_lobby_page(request: Request):
    """Serve the lobby HTML page"""
    return templates.TemplateResponse("lobby.html", {"request": request})

@app.get("/lobby/{lobby_id}", response_class=HTMLResponse)
async def get_lobby_join_page(lobby_id: str, request: Request):
    """Serve the lobby page for joining/tribute creation
    This preserves the lobby_id in the URL for session recovery
    
    NOTE: We do NOT validate that the lobby exists on the server.
    This allows session recovery even if the lobby temporarily doesn't exist
    (e.g., during server restart or if host left). The Socket.IO connection
    will handle reconnection validation.
    """
    return templates.TemplateResponse("lobby.html", {"request": request, "lobby_id": lobby_id})

@app.get("/lobby/{lobby_id}/waiting", response_class=HTMLResponse)
async def get_lobby_waiting_page(lobby_id: str, request: Request):
    """Serve the lobby page while waiting for game to start
    This preserves the lobby_id in the URL for session recovery
    
    NOTE: We do NOT validate that the lobby exists on the server.
    This allows session recovery even if the lobby temporarily doesn't exist
    (e.g., during server restart or if host left). The Socket.IO connection
    will handle reconnection validation.
    """
    return templates.TemplateResponse("lobby.html", {"request": request, "lobby_id": lobby_id})

@app.get("/spectator", response_class=HTMLResponse)
async def get_spectator_page(request: Request):
    """Serve the spectator HTML page"""
    return templates.TemplateResponse("spectator.html", {"request": request})

@app.get("/spectator/{lobby_id}", response_class=HTMLResponse)
async def get_spectator_game_page(lobby_id: str, request: Request):
    """Serve the spectator HTML page for a specific lobby"""
    if lobby_id not in lobbies:
        # Redirect to spectator lobby selection if game lobby doesn't exist
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/spectator")
    return templates.TemplateResponse("spectator.html", {"request": request, "lobby_id": lobby_id})

@app.get("/game/{lobby_id}", response_class=HTMLResponse)
async def get_game_page(lobby_id: str, request: Request):
    """Serve the game HTML page for a specific lobby"""
    if lobby_id not in lobbies:
        # Redirect to main lobby if game lobby doesn't exist
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/")
    return templates.TemplateResponse("game.html", {"request": request, "lobby_id": lobby_id})

@app.get("/api/tribute/{player_id}")
async def get_tribute_stats(player_id: str):
    """Get current tribute stats for a player"""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players[player_id]
    if not player.tribute_data:
        raise HTTPException(status_code=404, detail="Tribute data not found")
    
    # Calculate final skill ratings with district bonuses and priority weighting
    tribute_data = player.tribute_data
    district = tribute_data.district
    skill_priority = tribute_data.skill_priority or []
    
    # Get district bonuses from loaded config
    district_data = district_config["district_bonuses"].get(str(district), {})
    bonuses = district_data.get("bonuses", {})
    
    # Calculate base ratings from priority order (10 points distributed)
    base_ratings = {}
    all_skills = ['intelligence', 'hunting', 'strength', 'social', 'stealth', 'survival', 'agility', 'endurance', 'charisma', 'luck']
    
    for skill in all_skills:
        priority_index = skill_priority.index(skill) if skill in skill_priority else -1
        if priority_index != -1:
            # Prioritized skills: 10 points distributed based on position (highest first)
            base_ratings[skill] = 10 - priority_index
        else:
            # Unprioritized skills: default rating of 5
            base_ratings[skill] = 5
    
    # Calculate final ratings with district bonuses
    final_ratings = {}
    trait_scores = {}
    
    for skill in all_skills:
        bonus = bonuses.get(skill, 0)
        final_rating = max(1, min(10, base_ratings[skill] + bonus))  # Clamp between 1-10
        final_ratings[skill] = final_rating
        
        # Calculate trait score (weighted rating)
        trait_weight = district_config["trait_scoring"].get(skill, {}).get("weight", 1.0)
        trait_scores[skill] = final_rating * trait_weight
    
    return {
        "name": tribute_data.name,
        "district": district,
        "district_name": district_data.get("name", f"District {district}"),
        "district_description": district_data.get("description", ""),
        "gender": tribute_data.gender,
        "age": tribute_data.age,
        "skill_priority": skill_priority,
        "base_ratings": base_ratings,
        "final_ratings": final_ratings,
        "trait_scores": trait_scores,
        "district_bonuses": bonuses,
        "tribute_ready": player.tribute_ready
    }

@app.get("/api/tribute/spectator/{lobby_id}")
async def get_spectator_tribute_stats(lobby_id: str):
    """Get all tribute stats for spectators in a lobby"""
    if lobby_id not in lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = lobbies[lobby_id]
    tribute_stats = {}

    # Get stats for all players in the lobby
    for player_id, player in lobby.players.items():
        if player.tribute_data:
            # Calculate final skill ratings with district bonuses and priority weighting
            tribute_data = player.tribute_data
            district = tribute_data.district
            skill_priority = tribute_data.skill_priority or []

            # Get district bonuses from loaded config
            district_data = district_config["district_bonuses"].get(str(district), {})
            bonuses = district_data.get("bonuses", {})

            # Calculate base ratings from priority order (10 points distributed)
            base_ratings = {}
            all_skills = ['intelligence', 'hunting', 'strength', 'social', 'stealth', 'survival', 'agility', 'endurance', 'charisma', 'luck']

            for skill in all_skills:
                priority_index = skill_priority.index(skill) if skill in skill_priority else -1
                if priority_index != -1:
                    # Prioritized skills: 10 points distributed based on position (highest first)
                    base_ratings[skill] = 10 - priority_index
                else:
                    # Unprioritized skills: default rating of 5
                    base_ratings[skill] = 5

            # Calculate final ratings with district bonuses
            final_ratings = {}
            trait_scores = {}

            for skill in all_skills:
                bonus = bonuses.get(skill, 0)
                final_rating = max(1, min(10, base_ratings[skill] + bonus))  # Clamp between 1-10
                final_ratings[skill] = final_rating

                # Calculate trait score (weighted rating)
                trait_weight = district_config["trait_scoring"].get(skill, {}).get("weight", 1.0)
                trait_scores[skill] = final_rating * trait_weight

            tribute_stats[player_id] = {
                "player_id": player_id,
                "name": tribute_data.name,
                "district": district,
                "district_name": district_data.get("name", f"District {district}"),
                "district_description": district_data.get("description", ""),
                "gender": tribute_data.gender,
                "age": tribute_data.age,
                "skill_priority": skill_priority,
                "base_ratings": base_ratings,
                "final_ratings": final_ratings,
                "trait_scores": trait_scores,
                "district_bonuses": bonuses,
                "tribute_ready": player.tribute_ready
            }

    return {"tributes": tribute_stats}

@app.get("/api/district-bonuses")
async def get_district_bonuses():
    """Get district bonuses configuration for client-side use"""
    return district_config

@app.get("/api/weapons")
async def get_weapons():
    """Get all available weapons for tribute creation"""
    from Engine.weapons_system import get_weapons_system
    
    weapons_system = get_weapons_system()
    weapons_dict = weapons_system.get_all_weapons()
    
    return {"weapons": weapons_dict}

@app.get("/api/connection-diagnostics")
async def get_connection_diagnostics():
    """
    Diagnostic endpoint for connection troubleshooting
    Reports current server state, Socket.IO configuration, and active connections
    """
    import psutil
    import socket as socket_module
    
    try:
        # Get current process info
        process = psutil.Process()
        
        # Get network connections related to this process
        connections = process.net_connections()
        socket_connections = [c for c in connections if c.status in ['ESTABLISHED', 'LISTEN']]
        
        # Get server configuration
        server_config = {
            "ping_timeout": 30,  # Increased to allow for game processing
            "ping_interval": 8,  # As per current config
            "transports": ['polling', 'websocket'],
            "cors_allowed_origins": "*",
            "upgrade_mode": "probe"
        }
        
        # Collect active client info
        active_clients = []
        for sid, player in players.items():
            active_clients.append({
                "socket_id": sid,
                "player_id": player.id,
                "player_name": player.name,
                "connected": player.connected,
                "in_lobby": any(sid in lobby.players for lobby in lobbies.values())
            })
        
        # Collect lobby info
        lobby_info = []
        for lobby_id, lobby in lobbies.items():
            lobby_info.append({
                "lobby_id": lobby_id,
                "lobby_name": lobby.name,
                "player_count": len(lobby.players),
                "max_players": lobby.max_players,
                "game_started": lobby.game_started,
                "host_id": lobby.host_id
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "server_status": "running",
            "server_config": server_config,
            "system": {
                "cpu_percent": process.cpu_percent(interval=1),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else "N/A",
                "socket_connections": len(socket_connections)
            },
            "socket_io": {
                "total_clients": len(players),
                "connected_clients": sum(1 for p in players.values() if p.connected),
                "active_clients": active_clients
            },
            "lobbies": {
                "total": len(lobbies),
                "active_games": sum(1 for l in lobbies.values() if l.game_started),
                "lobbies": lobby_info
            },
            "network": {
                "listening_ports": list(set(c.laddr.port for c in socket_connections if c.status == 'LISTEN')),
                "established_connections": len([c for c in socket_connections if c.status == 'ESTABLISHED'])
            }
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "note": "psutil may not be installed. Install with: pip install psutil"
        }

@app.get("/api/debug/players")
async def debug_players():
    """Debug endpoint that broadcasts player names and resume codes to console"""
    player_info = []

    # Get all players and their resume codes
    for resume_code, player_id in resume_codes.items():
        if player_id in players:
            player = players[player_id]
            player_info.append({
                'player_id': player_id,
                'name': player.name,
                'resume_code': resume_code,
                'connected': player.connected,
                'tribute_ready': player.tribute_ready if hasattr(player, 'tribute_ready') else False
            })

    # Also include players without resume codes (spectators, etc.)
    for player_id, player in players.items():
        if player_id not in [p['player_id'] for p in player_info]:
            player_info.append({
                'player_id': player_id,
                'name': player.name,
                'resume_code': None,
                'connected': player.connected,
                'tribute_ready': player.tribute_ready if hasattr(player, 'tribute_ready') else False
            })

    # Print to server console
    print("\n" + "="*50, flush=True)
    print("DEBUG: Current Players and Resume Codes", flush=True)
    print("="*50, flush=True)
    for info in player_info:
        print(f"Player: {info['name']} (ID: {info['player_id'][:8]}...)", flush=True)
        print(f"  Resume Code: {info['resume_code']}", flush=True)
        print(f"  Connected: {info['connected']}", flush=True)
        print(f"  Tribute Ready: {info['tribute_ready']}", flush=True)
        print(flush=True)

    # Broadcast to all connected clients
    await sio.emit('debug_info', {
        'players': player_info,
        'timestamp': datetime.now().isoformat()
    })

    return {"message": "Player info broadcasted to console and clients", "players": player_info}

@app.get("/api/lobby/{lobby_id}/status")
async def get_lobby_status(lobby_id: str):
    """Check if a lobby is still alive and get its status
    
    Returns:
        - status: "alive" or "gone"
        - game_status: Current game state (waiting, in_progress, ended)
        - player_count: Number of players in lobby
        - game_info: Additional game info if available
    """
    if lobby_id not in lobbies:
        return {"status": "gone", "message": "Lobby no longer exists"}
    
    lobby = lobbies[lobby_id]
    
    try:
        game_status = "waiting"
        if hasattr(lobby, 'game_state') and lobby.game_state:
            if hasattr(lobby.game_state, 'current_day'):
                game_status = "in_progress"
            if hasattr(lobby.game_state, 'ended') and lobby.game_state.ended:
                game_status = "ended"
        
        player_count = len(lobby.players) if hasattr(lobby, 'players') else 0
        
        return {
            "status": "alive",
            "game_status": game_status,
            "player_count": player_count,
            "game_info": {
                "day": getattr(lobby.game_state, 'current_day', 0) if hasattr(lobby, 'game_state') and lobby.game_state else 0,
                "ended": getattr(lobby.game_state, 'ended', False) if hasattr(lobby, 'game_state') and lobby.game_state else False
            }
        }
    except Exception as e:
        print(f"Error checking lobby status: {e}", flush=True)
        return {"status": "error", "message": str(e)}

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
        # Clean up client ready status for any lobbies this player was in
        for lobby in lobbies.values():
            if sid in lobby.players:
                if sid in lobby.client_ready_status:
                    del lobby.client_ready_status[sid]
                    print(f"Removed disconnected player {sid} from client_ready_status in lobby {lobby.id}")
                await sio.emit('lobby_updated', {
                    'lobby': lobby.to_dict(),
                    'available_districts': lobby.get_available_districts()
                }, room=lobby.id)
                break

@sio.event
async def ping(sid):
    """Handle ping from client for connection testing"""
    print(f"🏓 Received ping from client {sid}")
    await sio.emit('pong', room=sid)

@sio.event
async def create_lobby(sid, data):
    """Handle creating a new lobby"""
    lobby_name = data.get('name', f'Lobby by {sid[:8]}')
    player_name = data.get('player_name', f'Player_{sid[:8]}')  # Get player name from client
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

    # Automatically join the creator to their own lobby with their provided name
    player = Player(id=sid, name=player_name)
    players[sid] = player
    lobby.players[sid] = player

    # Generate resume code for the creator
    resume_code = generate_resume_code()
    resume_codes[resume_code] = sid

    # Join socket room
    await sio.enter_room(sid, lobby_id)

    print(f"Created lobby {lobby_id} with name '{lobby_name}' by client {sid}")
    print(f"Total lobbies in memory: {len(lobbies)}")

    # Send lobby created and joined event to creator
    await sio.emit('lobby_created', {
        'lobby_id': lobby_id,
        'lobby': lobby.to_dict(),
        'available_districts': lobby.get_available_districts(),
        'player_id': sid,
        'player': asdict(player),
        'resume_code': resume_code
    }, room=sid)

    # Broadcast updated lobby list to all connected clients
    await broadcast_lobby_list()

async def broadcast_lobby_list():
    """Broadcast updated lobby list to all connected clients"""
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

    # Send to all connected clients (not in any specific room)
    await sio.emit('lobby_list', {'lobbies': lobby_list})

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

    # If this is the first player joining an empty lobby, make them the host
    if len(lobby.players) == 1:
        lobby.host_id = sid
        print(f"Assigned {sid} as host of lobby {lobby_id} (first player to join)")

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

    # Broadcast updated lobby list to all connected clients
    await broadcast_lobby_list()

@sio.event
async def join_as_spectator(sid, data=None):
    """Handle spectator joining a lobby"""
    lobby_id = data.get('lobby_id') if data else None
    spectator_name = data.get('name', f'Spectator_{sid[:8]}') if data else f'Spectator_{sid[:8]}'

    if not lobby_id or lobby_id not in lobbies:
        await sio.emit('error', {'message': 'Lobby not found'}, room=sid)
        return

    lobby = lobbies[lobby_id]

    # Require at least one active player in the lobby before allowing spectators
    if len(lobby.players) < 1:
        await sio.emit('error', {'message': 'Cannot spectate - lobby must have at least one active player first'}, room=sid)
        return

    # If this player was in the lobby, remove them from players
    was_host = False
    if sid in lobby.players:
        was_host = (lobby.host_id == sid)
        del lobby.players[sid]
        # Clean up client ready status
        if lobby.client_ready_status and sid in lobby.client_ready_status:
            del lobby.client_ready_status[sid]
            print(f"Removed spectator {sid} from client_ready_status in lobby {lobby.id}")

    # If they were the host, reassign host to another player
    if was_host:
        remaining_players = list(lobby.players.keys())
        if remaining_players:
            lobby.host_id = remaining_players[0]  # Assign first remaining player as new host
            print(f"Host reassigned from {sid} to {lobby.host_id}")
        else:
            # This shouldn't happen since we check for at least 1 player above
            await sio.emit('error', {'message': 'Cannot become spectator - no players left to manage the lobby'}, room=sid)
            return

    # Create spectator player (doesn't count toward player limit)
    spectator = Player(id=sid, name=spectator_name)
    players[sid] = spectator
    # Note: Spectators are not added to lobby.players to avoid affecting game logic

    # Join socket room for lobby updates
    await sio.enter_room(sid, lobby_id)

    # Send spectator joined confirmation
    await sio.emit('spectator_joined', {
        'player_id': sid,
        'lobby_id': lobby_id,
        'lobby': lobby.to_dict()
    }, room=sid)

    # If game has already started, send current game state to spectator
    if lobby.game_started and lobby.game_state:
        await sio.emit('spectator_update', {
            'game_state': asdict(lobby.game_state)
        }, room=sid)

    # Notify all players in lobby about the update (new host, etc.)
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

    # Check if this player was the host and update host_id if necessary
    if player_lobby.host_id == old_player_id:
        player_lobby.host_id = sid
        print(f"Host ID updated from {old_player_id} to {sid} during resume")

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
    print(f"Current lobbies in memory: {list(lobbies.keys())}")
    lobby_list = []
    for lobby in lobbies.values():
        print(f"Checking lobby {lobby.id}: game_started={lobby.game_started}, players={len(lobby.players)}, max_players={lobby.max_players}")
        
        # Show lobby if it's waiting for players, OR if game is in progress (spectate-only)
        can_join = not lobby.game_started and len(lobby.players) < lobby.max_players
        is_spectate_only = lobby.game_started
        
        if can_join or is_spectate_only:
            lobby_info = {
                'id': lobby.id,
                'name': lobby.name,
                'host_name': players.get(lobby.host_id, Player(id='', name='Unknown')).name,
                'player_count': len(lobby.players),
                'max_players': lobby.max_players,
                'created_at': lobby.created_at.isoformat() if lobby.created_at else None,
                'game_started': lobby.game_started,
                'spectate_only': is_spectate_only
            }
            lobby_list.append(lobby_info)
            print(f"Included lobby {lobby.id} in list (game_started={lobby.game_started})")

    print(f"Sending {len(lobby_list)} lobbies to client {sid}: {[l['name'] for l in lobby_list]}")
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

    # Initialize game starting state
    lobby.game_started = True
    lobby.game_state = GameState(
        day=1,
        status='starting',
        players=[p for p in lobby.players.values()]
    )
    
    # Track client readiness
    lobby.client_ready_status = {pid: False for pid in lobby.players.keys()}

    # Notify all players that game is starting
    await sio.emit('game_starting', {
        'lobby_id': lobby.id,
        'fetch_tribute_stats': True
    }, room=lobby.id)

    # Send initial game state to players (but game hasn't actually started yet)
    for player_id in lobby.players:
        player_dict = asdict(lobby.players[player_id])
        game_state_dict = asdict(lobby.game_state)
        print(f"Sending game_state_update to {player_id}: tribute_data={player_dict.get('tribute_data')}", flush=True)
        await sio.emit('game_state_update', {
            'game_state': serialize_for_socket(game_state_dict),
            'current_player': serialize_for_socket(player_dict)
        }, room=player_id)

    # Send initial game state to spectators
    if lobby.game_state:
        await sio.emit('spectator_update', {
            'game_state': serialize_for_socket(asdict(lobby.game_state))
        }, room=lobby.id)

    # Game simulation will start in the client_ready event handler
    # after all clients have signaled they are ready

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

    # Process action through Aurora Engine
    from aurora_integration import aurora_integration

    player = lobby.players.get(sid)
    if not player or not player.alive:
        return

    # Convert action to Aurora Engine input format
    input_data = {
        'id': f'action_{sid}_{datetime.now().timestamp()}',
        'command_type': 'player_action',
        'player_id': sid,
        'action': action,
        'data': data
    }

    # Process through Aurora Engine
    response = aurora_integration.process_player_input(input_data)

    if response:
        # Send response back to player
        await sio.emit('action_processed', {
            'player_id': sid,
            'action': action,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }, room=sid)

        # Send game update to all players in lobby
        await sio.emit('game_update', {
            'lobby_id': lobby.id,
            'message': response,
            'timestamp': datetime.now().isoformat()
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
        'game_state': serialize_for_socket(asdict(lobby.game_state)),
        'current_player': serialize_for_socket(asdict(lobby.players.get(sid)))
    }, room=sid)

@sio.event
async def leave_spectator(sid, data=None):
    """Handle spectator leaving"""
    lobby_id = 'main_lobby'
    if lobby_id in lobbies:
        await sio.leave_room(sid, lobby_id)

def calculate_skills_from_priority(skill_priority, district):
    """
    Calculate final skill ratings based on priority order and district bonuses.
    Skills NOT in priority list get random ratings.
    This is SERVER-SIDE calculation to prevent client manipulation.
    """
    import random
    
    all_skills = ['intelligence', 'hunting', 'strength', 'social', 'stealth', 
                  'survival', 'agility', 'endurance', 'charisma', 'luck']
    
    # Get district modifiers
    district_traits = {
        1: { 'social': 2, 'charisma': 2, 'survival': -1, 'hunting': -1 },
        2: { 'strength': 2, 'endurance': 2, 'stealth': -1, 'charisma': -1 },
        3: { 'intelligence': 2, 'agility': 1, 'strength': -1, 'endurance': -1 },
        4: { 'agility': 2, 'hunting': 1, 'intelligence': -1, 'social': -1 },
        5: { 'intelligence': 2, 'endurance': 1, 'social': -1, 'charisma': -1 },
        6: { 'endurance': 2, 'strength': 1, 'intelligence': -1, 'agility': -1 },
        7: { 'strength': 2, 'endurance': 1, 'social': -1, 'charisma': -1 },
        8: { 'agility': 2, 'intelligence': 1, 'strength': -1, 'endurance': -1 },
        9: { 'endurance': 2, 'survival': 1, 'hunting': -1, 'intelligence': -1 },
        10: { 'survival': 2, 'endurance': 1, 'charisma': -1, 'social': -1 },
        11: { 'survival': 2, 'strength': 1, 'intelligence': -1, 'charisma': -1 },
        12: { 'endurance': 2, 'strength': 1, 'charisma': -1, 'social': -1 }
    }
    
    modifiers = district_traits.get(district, {})
    final_skills = {}
    
    for skill in all_skills:
        base_rating = 0
        
        # Check if skill is in priority list
        if skill in skill_priority:
            priority_index = skill_priority.index(skill)
            base_rating = 10 - priority_index  # 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
        else:
            # Unprioritized skills get random 1-5
            base_rating = random.randint(1, 5)
        
        # Apply district modifier
        modifier = modifiers.get(skill, 0)
        final_rating = max(1, min(10, base_rating + modifier))
        final_skills[skill] = final_rating
    
    return final_skills

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
    print(f"[UPDATE_TRIBUTE] Called for {sid}", flush=True)
    try:
        if sid not in players:
            print(f"[UPDATE_TRIBUTE] Player {sid} not in players dict", flush=True)
            return

        player = players[sid]
        tribute_data = data.get('tribute_data', {})
        print(f"[UPDATE_TRIBUTE] Updating tribute_data keys: {list(tribute_data.keys())}", flush=True)

        # Update tribute data with validation
        if 'name' in tribute_data and tribute_data['name'] is not None:
            player.tribute_data.name = str(tribute_data['name'])
        if 'district' in tribute_data and tribute_data['district'] is not None:
            try:
                district_value = int(tribute_data['district'])
                player.tribute_data.district = district_value
                player.district = district_value  # Also update player's district field
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
        
        if 'skill_priority' in tribute_data and tribute_data['skill_priority'] is not None and isinstance(tribute_data['skill_priority'], list):
            print(f"[UPDATE_TRIBUTE] Processing skill_priority: {tribute_data['skill_priority']}", flush=True)
            player.tribute_data.skill_priority = tribute_data['skill_priority']
            # Calculate final skills based on priority and district (SERVER-SIDE to prevent manipulation)
            final_skills = calculate_skills_from_priority(tribute_data['skill_priority'], player.tribute_data.district)
            player.tribute_data.skills = final_skills
            print(f"[UPDATE_TRIBUTE] Calculated skills: {final_skills}", flush=True)
        
        if 'preferred_weapon' in tribute_data and tribute_data['preferred_weapon']:
            player.tribute_data.preferred_weapon = str(tribute_data['preferred_weapon'])
            print(f"[UPDATE_TRIBUTE] Set preferred_weapon: {player.tribute_data.preferred_weapon}", flush=True)

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
        
        print(f"[UPDATE_TRIBUTE] Completed successfully for {sid}", flush=True)
        
    except Exception as e:
        print(f"[ERROR] Exception in update_tribute for {sid}: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)

@sio.event
async def update_player_name(sid, data):
    """Handle player name updates"""
    if sid not in players:
        return

    new_name = data.get('name', '').strip()
    if not new_name:
        return

    player = players[sid]
    old_name = player.name
    player.name = new_name

    print(f"Player {sid} name updated from '{old_name}' to '{new_name}'")

    # Notify all players in lobby about the name change
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

@sio.event
async def client_ready(sid, data=None):
    """Handle client signaling that it has loaded tribute data and is ready for game start"""
    if sid not in players:
        return

    player = players[sid]
    print(f"Player {sid} ({player.name}) signaled client ready")

    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players:
            # Mark this client as ready
            lobby.client_ready_status[sid] = True
            print(f"Client ready status updated for lobby {lobby.id}: {lobby.client_ready_status}")

            # Check if all CONNECTED players are ready
            connected_players = [pid for pid in lobby.players.keys() if pid in players and players[pid].connected]
            all_ready = all(lobby.client_ready_status.get(pid, False) for pid in connected_players)
            print(f"All connected clients ready for lobby {lobby.id}: {all_ready} (connected: {len(connected_players)}, total: {len(lobby.players)})")

            if all_ready and len(connected_players) > 0 and not lobby.simulation_started:
                print(f"All connected clients ready, starting game simulation for lobby {lobby.id}")
                lobby.simulation_started = True  # Prevent running simulation multiple times
                
                # Start the actual game simulation in background
                asyncio.create_task(run_game_simulation(lobby))

                # Notify all clients that the game has actually started
                await sio.emit('game_started', {
                    'message': 'The Hunger Games have begun!',
                    'lobby_id': lobby.id,
                    'lobby': lobby.to_dict()
                }, room=lobby.id)
            break

@sio.event
async def generate_remaining_tributes(sid, data):
    """Generate AI tributes for all remaining districts (admin only)"""
    if sid not in players:
        return {'success': False, 'message': 'Player not found'}

    player = players[sid]
    
    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players and sid == lobby.host_id:  # Only host can do this
            
            # Get available districts (those with < 2 tributes)
            available_districts = lobby.get_available_districts()
            
            if not available_districts:
                return {
                    'success': True,
                    'message': 'All districts are full (2 tributes each)',
                    'count': 0
                }
            
            # Generate AI tributes for remaining districts
            generated_count = 0
            ai_names = generate_ai_tribute_names()  # Pre-generate unique names
            
            for district in available_districts:
                # Check how many tributes this district already has
                current_count = sum(1 for p in lobby.players.values() 
                                  if p.tribute_ready and p.tribute_data and p.tribute_data.district == district)
                
                # Generate up to 2 tributes per district
                needed = 2 - current_count
                for i in range(needed):
                    if generated_count >= len(ai_names):
                        break  # Don't exceed our name pool
                        
                    # Create AI player
                    ai_player_id = f"ai_{district}_{i+1}_{generated_count}"
                    ai_tribute_data = generate_ai_tribute_data(district, ai_names[generated_count])
                    
                    ai_player = Player(
                        id=ai_player_id,
                        name=f"AI-{ai_tribute_data.name}",
                        district=district,
                        ready=True,
                        connected=False,  # AI players are not connected
                        tribute_data=ai_tribute_data,
                        tribute_ready=True
                    )
                    
                    # Add AI player to lobby
                    lobby.players[ai_player_id] = ai_player
                    players[ai_player_id] = ai_player  # Also add to global players dict
                    
                    generated_count += 1
                    print(f"[AI_GEN] Created AI tribute: {ai_tribute_data.name} from District {district}")
            
            # Broadcast lobby update to all players
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            
            # Return success response for callback
            return {
                'success': True,
                'message': f'Generated {generated_count} AI tribute(s) for remaining districts',
                'count': generated_count
            }
    
    return {'success': False, 'message': 'Lobby not found or not host'}

def generate_ai_tribute_names():
    """Generate a pool of unique AI tribute names"""
    import random
    
    first_names = [
        "Aiden", "Blake", "Cora", "Dex", "Echo", "Finn", "Gaia", "Hunter",
        "Iris", "Jax", "Kira", "Lux", "Maya", "Nova", "Orion", "Piper",
        "Quinn", "Raven", "Sage", "Tara", "Vale", "Wren", "Zara", "Aspen"
    ]
    last_names = [
        "Stone", "Rivers", "Cross", "Vale", "Storm", "Reed", "Fox", "Gray",
        "Woods", "Black", "White", "Green", "Silver", "Gold", "Steel", "Winter",
        "Summer", "Dawn", "Night", "Moon", "Star", "Wild", "Sharp", "Swift"
    ]
    
    # Shuffle both lists first to ensure random combinations
    random.shuffle(first_names)
    random.shuffle(last_names)
    
    # Generate unique combinations
    names = []
    used_combinations = set()
    
    while len(names) < 24 and len(used_combinations) < len(first_names) * len(last_names):
        first = random.choice(first_names)
        last = random.choice(last_names)
        combination = f"{first} {last}"
        
        if combination not in used_combinations:
            names.append(combination)
            used_combinations.add(combination)
    
    return names

def generate_ai_tribute_data(district: int, name: str) -> TributeData:
    """Generate a TributeData object for an AI tribute"""
    import random
    
    # Random gender and age
    gender = random.choice(["Male", "Female"])
    age = random.randint(12, 18)
    
    # Generate skills with some district-based tendencies
    district_skill_bonuses = {
        1: {"strength": 2, "charisma": 2},      # Luxury - strength and charisma
        2: {"intelligence": 2, "social": 1},     # Masonry - intelligence and social
        3: {"intelligence": 3},                  # Technology - high intelligence
        4: {"hunting": 2, "survival": 2},        # Fishing - hunting and survival
        5: {"agility": 2, "endurance": 2},       # Power - agility and endurance
        6: {"intelligence": 1, "social": 2},     # Transportation - intelligence and social
        7: {"survival": 2, "stealth": 2},        # Lumber - survival and stealth
        8: {"social": 2, "charisma": 2},         # Textiles - social and charisma
        9: {"hunting": 2, "survival": 1},        # Grain - hunting and survival
        10: {"endurance": 3},                    # Livestock - high endurance
        11: {"agility": 2, "hunting": 1},        # Agriculture - agility and hunting
        12: {"stealth": 2, "survival": 2}        # Mining - stealth and survival
    }
    
    # Base skills (random 1-10)
    skills = {
        "strength": random.randint(1, 10),
        "agility": random.randint(1, 10),
        "intelligence": random.randint(1, 10),
        "charisma": random.randint(1, 10),
        "survival": random.randint(1, 10),
        "hunting": random.randint(1, 10),
        "social": random.randint(1, 10),
        "stealth": random.randint(1, 10),
        "endurance": random.randint(1, 10),
        "luck": random.randint(1, 10)
    }
    
    # Apply district bonuses
    if district in district_skill_bonuses:
        for skill, bonus in district_skill_bonuses[district].items():
            skills[skill] = min(10, skills[skill] + bonus)
    
    # Generate skill priority (top 3-5 skills)
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
    skill_priority = [skill for skill, _ in sorted_skills[:random.randint(3, 5)]]
    
    # Select a random preferred weapon
    from Engine.weapons_system import get_weapons_system
    weapons_system = get_weapons_system()
    all_weapons = list(weapons_system.get_all_weapons().keys())
    preferred_weapon = random.choice(all_weapons)
    
    return TributeData(
        name=name,
        district=district,
        gender=gender,
        age=age,
        skills=skills,
        skill_priority=skill_priority,
        preferred_weapon=preferred_weapon
    )

@sio.event
async def generate_random_tribute(sid, data):
    """Generate a random tribute for a specific player (admin only)"""
    if sid not in players:
        return {'success': False, 'message': 'Player not found'}

    player = players[sid]
    player_id = data.get('player_id')
    
    # Find player's lobby
    for lobby in lobbies.values():
        if sid in lobby.players and sid == lobby.host_id:  # Only host can do this
            # Find the target player
            if player_id not in lobby.players:
                return {
                    'success': False,
                    'message': 'Player not found'
                }
            
            target_player = lobby.players[player_id]
            
            # Generate random tribute
            from utils.generator import generate_random_tribute
            target_player.tribute_data = generate_random_tribute()
            target_player.tribute_ready = False  # Auto-mark as not ready so player can review
            
            # Broadcast lobby update to all players
            await sio.emit('lobby_updated', {
                'lobby': lobby.to_dict(),
                'available_districts': lobby.get_available_districts()
            }, room=lobby.id)
            
            # Return success response for callback
            return {
                'success': True,
                'message': f'Generated tribute for {target_player.name}',
                'tribute_name': target_player.tribute_data.name
            }
    
    return {'success': False, 'message': 'Lobby not found or not host'}

# ==================== ADMIN CONTROLS ====================

# Initialize admin controls when lobby_manager is available
admin_controls_instance = None

def initialize_admin_controls(aurora_integration, lobby_manager):
    """Initialize admin controls after lobbies are set up"""
    global admin_controls_instance
    admin_controls_instance = AdminControls(aurora_integration, sio, lobby_manager)

@sio.event
async def admin_force_next_event(sid, data):
    """Admin command: Force generation of next event"""
    if admin_controls_instance is None:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Admin controls not initialized'
        }, room=sid)
        return
    
    # Verify admin authorization (basic check - in production use proper auth)
    if not data.get('lobby_id'):
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Missing lobby_id'
        }, room=sid)
        return
    
    result = await admin_controls_instance.force_next_event(data['lobby_id'])
    await sio.emit('admin_response', result, room=sid)

@sio.event
async def admin_force_next_phase(sid, data):
    """Admin command: Force advance to next phase"""
    if admin_controls_instance is None:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Admin controls not initialized'
        }, room=sid)
        return
    
    if not data.get('lobby_id'):
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Missing lobby_id'
        }, room=sid)
        return
    
    result = await admin_controls_instance.force_next_phase(data['lobby_id'])
    await sio.emit('admin_response', result, room=sid)

@sio.event
async def admin_update_timing(sid, data):
    """Admin command: Update engine timing configuration"""
    if admin_controls_instance is None:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Admin controls not initialized'
        }, room=sid)
        return
    
    timing_updates = data.get('timing_updates', {})
    result = await admin_controls_instance.update_config_timing(timing_updates)
    await sio.emit('admin_response', result, room=sid)

@sio.event
async def admin_get_tribute_stats(sid, data):
    """Admin command: Get current tribute statistics"""
    if admin_controls_instance is None:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Admin controls not initialized'
        }, room=sid)
        return
    
    lobby_id = data.get('lobby_id')
    tribute_id = data.get('tribute_id')
    
    if not lobby_id:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Missing lobby_id'
        }, room=sid)
        return
    
    result = await admin_controls_instance.get_tribute_stats(lobby_id, tribute_id)
    await sio.emit('admin_response', result, room=sid)

@sio.event
async def admin_trigger_stat_decay(sid, data):
    """Admin command: Manually trigger stat decay for all tributes"""
    if admin_controls_instance is None:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Admin controls not initialized'
        }, room=sid)
        return
    
    lobby_id = data.get('lobby_id')
    if not lobby_id:
        await sio.emit('admin_response', {
            'success': False,
            'error': 'Missing lobby_id'
        }, room=sid)
        return
    
    result = await admin_controls_instance.trigger_stat_decay(lobby_id)
    await sio.emit('admin_response', result, room=sid)

async def run_game_simulation(lobby: Lobby):
    """Run the Hunger Games simulation using Aurora Engine integration"""
    try:
        from aurora_integration import aurora_integration
        global admin_controls_instance

        print(f"[GAME_SIM] Starting game simulation for lobby {lobby.id}", flush=True)

        # Initialize Aurora Engine for this lobby (don't load state for fresh games)
        config_path = os.path.join(os.path.dirname(__file__), "Engine", "config.json")

        aurora_integration.initialize_engine(lobby.id, config_path)
        print(f"[GAME_SIM] Aurora Engine initialized", flush=True)
        
        # Initialize admin controls for this game
        if admin_controls_instance is None:
            # Create a mock lobby_manager for admin controls
            lobby_manager_obj = type('LobbyManager', (), {'lobbies': lobbies})()
            admin_controls_instance = AdminControls(aurora_integration, sio, lobby_manager_obj)

        # Start the game with lobby players
        players_list = list(lobby.players.values())
        print(f"[GAME_SIM] Starting game with {len(players_list)} players", flush=True)
        if not aurora_integration.start_game(players_list):
            print(f"[GAME_SIM] Failed to start Aurora Engine game", flush=True)
            await sio.emit('game_start_failed', {
                'reason': 'Failed to start Aurora Engine game'
            }, room=lobby.id)
            return

        # Update lobby status
        lobby.game_state.status = 'running'
        print(f"[GAME_SIM] Game status set to running", flush=True)

        # Don't send a separate game_started message here - the engine will send one
        # via its message queue that will be processed in the game loop below

        # Game simulation loop
        tick_count = 0
        while lobby.game_started and aurora_integration.game_active:
            try:
                tick_count += 1
                print(f"[GAME_SIM] Tick {tick_count} - Processing game tick", flush=True)

                # Process game tick (now returns ENHANCED messages with rich narratives)
                messages = aurora_integration.process_game_tick()
                print(f"[GAME_SIM] Tick {tick_count} - Got {len(messages)} ENHANCED messages from engine", flush=True)

                # Send any new messages to players with DRAMATIC PACING
                for i, message in enumerate(messages):
                    msg_type = message.get('message_type', 'unknown')
                    category = message.get('category', 'unknown')
                    priority = message.get('priority', 1)
                    
                    print(f"[GAME_SIM] Tick {tick_count} - Sending message {i+1}/{len(messages)}: {msg_type} [{category}] priority={priority}", flush=True)
                    
                    await sio.emit('game_update', {
                        'lobby_id': lobby.id,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }, room=lobby.id)
                    
                    # ========== DRAMATIC PACING SYSTEM ==========
                    # Variable delays based on event type and priority for better storytelling
                    if len(messages) > 1 and i < len(messages) - 1:
                        # Death events get longest pauses - let the impact sink in
                        if category == 'death' or msg_type in ['tribute_death', 'cornucopia_death']:
                            await asyncio.sleep(3.5)  # 3.5s for deaths - dramatic pause
                        
                        # Combat and high-priority events get medium pauses
                        elif category in ['combat', 'injury'] or priority >= 4:
                            await asyncio.sleep(2.0)  # 2s for combat/important events
                        
                        # Arena events and gamemaker interventions - medium-long
                        elif category in ['arena_event', 'sponsor']:
                            await asyncio.sleep(2.5)  # 2.5s for special events
                        
                        # Phase transitions - brief pause
                        elif category == 'phase':
                            await asyncio.sleep(1.5)  # 1.5s for phase changes
                        
                        # Regular survival/exploration events - short pause
                        elif category in ['survival', 'exploration', 'social']:
                            await asyncio.sleep(0.8)  # 800ms for routine events
                        
                        # Status updates and low priority - minimal pause
                        else:
                            await asyncio.sleep(0.4)  # 400ms for status updates
                    # ============================================

                # Send detailed engine status update (this also serves as a heartbeat)
                current_status = aurora_integration.get_game_status()
                tribute_data = current_status.get('tribute_scoreboards', {})
                print(f"[GAME_SIM] Tick {tick_count} - Got {len(tribute_data)} tributes in scoreboards", flush=True)
                
                # Always emit status update to keep connection alive (every 2s < 20s timeout)
                await sio.emit('engine_status_update', {
                    'lobby_id': lobby.id,
                    'engine_status': current_status.get('engine_status', {}),
                    'tribute_scoreboards': tribute_data,
                    'timestamp': datetime.now().isoformat(),
                    'tick': tick_count  # Include tick for debugging
                }, room=lobby.id)
                print(f"[GAME_SIM] Tick {tick_count} - Emitted engine_status_update (heartbeat)", flush=True)

                # Get animation events for visual updates
                events = aurora_integration.get_game_events_since()
                if events:
                    print(f"[GAME_SIM] Tick {tick_count} - Got {len(events)} animation events", flush=True)
                    await sio.emit('animation_events', {
                        'lobby_id': lobby.id,
                        'events': events,
                        'timestamp': datetime.now().isoformat()
                    }, room=lobby.id)

                # Update lobby game state
                status = aurora_integration.get_game_status()
                if 'engine_status' in status:
                    engine_status = status['engine_status']
                    lobby.game_state.day = engine_status.get('phase_info', {}).get('day', 1)
                    lobby.game_state.status = 'running' if engine_status.get('game_active') else 'ended'

                    # Check if game has ended
                    if not engine_status.get('game_active'):
                        print(f"[GAME_SIM] Game ended (game_active=False)", flush=True)
                        lobby.game_started = False
                        await sio.emit('game_ended', {
                            'lobby_id': lobby.id,
                            'final_stats': engine_status
                        }, room=lobby.id)
                        break

                # Wait before next tick (adjust timing as needed)
                print(f"[GAME_SIM] Tick {tick_count} - Sleeping 2 seconds before next tick", flush=True)
                await asyncio.sleep(2.0)  # 2 second ticks

            except Exception as e:
                print(f"[GAME_SIM] Error in game simulation loop: {e}", flush=True)
                import traceback
                print(traceback.format_exc(), flush=True)
                await sio.emit('game_error', {
                    'lobby_id': lobby.id,
                    'error': str(e)
                }, room=lobby.id)
                break

        # Save final game state
        aurora_integration.save_game_state()
        print(f"[GAME_SIM] Game simulation ended for lobby {lobby.id}", flush=True)

    except Exception as e:
        print(f"Error in game simulation: {e}")
        await sio.emit('game_start_failed', {
            'reason': f'Game simulation error: {str(e)}'
        }, room=lobby.id)

# Mount the Socket.IO app
app.mount("/", socket_app)

if __name__ == "__main__":
    import uvicorn
    print("Starting Hunger Games Lobby Server...")
    print("Open http://localhost:8000 in your browser")
    print("\n[Connection Configuration]")
    print("  - Socket.IO ping timeout: 30s (client timeout: 30s) [ALIGNED - allows game processing]")
    print("  - Socket.IO ping interval: 8s (sends ~3 pings before timeout)")
    print("  - Game simulation: 2s ticks with engine_status_update (additional heartbeat)")
    print("  - Transports: polling-first (stable), then websocket (upgrade)")
    print("  - Force polling on Cloudflare Tunnel/proxies: ENABLED")
    print("\n[Diagnostics] Available at: http://localhost:8000/api/connection-diagnostics")
    print()
    
    # OPTIMIZED UVICORN SETTINGS for long-lived WebSocket/polling connections
    # Socket.IO ping_interval=8s handles keeping connections alive at application level
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker
        limit_concurrency=1000,  # Maximum concurrent connections
        log_level="info",
        access_log=True,
    )

