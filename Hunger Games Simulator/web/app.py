from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import uuid
import threading
import time
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from game_runner import game_runner

# Import Aurora Engine integration
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Aurora Engine'))
    from aurora_integration import AuroraLobbyIntegration
except ImportError:
    print("Warning: Aurora Engine integration not available")
    AuroraLobbyIntegration = None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable Socket.IO with CORS

# In-memory storage for lobbies and games
lobbies: Dict[str, dict] = {}
active_games: Dict[str, dict] = {}
aurora_integrations: Dict[str, object] = {}  # Store Aurora integration instances

class LobbyManager:
    """Manages game lobbies and player connections."""

    @staticmethod
    def create_lobby(admin_name: str, max_players: int = 24) -> str:
        """Create a new lobby and return the lobby code."""
        lobby_code = str(uuid.uuid4())[:8].upper()

        lobbies[lobby_code] = {
            'code': lobby_code,
            'admin': admin_name,
            'players': [admin_name],
            'max_players': max_players,
            'status': 'waiting',  # waiting, starting, active
            'created_at': datetime.now(),
            'tribute_jsons': [],  # List of uploaded tribute JSON data
            'alliances': [],  # List of alliance formations [{'initiator': str, 'target': str, 'timestamp': datetime}]
            'targets': [],  # List of targeting decisions [{'hunter': str, 'target': str, 'timestamp': datetime}]
            'game_settings': {
                'custom_tributes_only': False,
                'allow_custom_uploads': True,
                'phase_delay_seconds': 3,  # Time between phases in seconds
                'event_delay_seconds': 1.0,  # Delay between events in seconds
                'progression_mode': 'auto'  # 'auto' or 'manual'
            }
        }

        return lobby_code

    @staticmethod
    def join_lobby(lobby_code: str, player_name: str) -> bool:
        """Add a player to a lobby. Returns True if successful."""
        if lobby_code not in lobbies:
            return False

        lobby = lobbies[lobby_code]
        if len(lobby['players']) >= lobby['max_players']:
            return False

        if player_name not in lobby['players']:
            lobby['players'].append(player_name)

        return True

    @staticmethod
    def get_lobby(lobby_code: str) -> Optional[dict]:
        """Get lobby information."""
        return lobbies.get(lobby_code)

    @staticmethod
    def update_game_settings(lobby_code: str, settings: dict) -> bool:
        """Update game settings for a lobby. Returns True if successful."""
        if lobby_code not in lobbies:
            return False
        
        lobby = lobbies[lobby_code]
        
        # Update only allowed settings
        allowed_settings = ['phase_delay_seconds', 'event_delay_seconds', 'progression_mode', 'custom_tributes_only', 'allow_custom_uploads']
        for key, value in settings.items():
            if key in allowed_settings:
                lobby['game_settings'][key] = value
        
        return True

    @staticmethod
    def add_tribute_json(lobby_code: str, tribute_data: dict, player_name: str) -> bool:
        """Add a tribute JSON to the lobby."""
        if lobby_code not in lobbies:
            return False

        lobby = lobbies[lobby_code]

        # Validate tribute data structure
        if not LobbyManager._validate_tribute_data(tribute_data):
            return False

        # Add metadata
        tribute_entry = {
            'data': tribute_data,
            'uploaded_by': player_name,
            'uploaded_at': datetime.now(),
            'id': str(uuid.uuid4())
        }

        lobby['tribute_jsons'].append(tribute_entry)
        return True

    @staticmethod
    def _validate_tribute_data(data: dict) -> bool:
        """Validate tribute JSON structure."""
        required_fields = ['name', 'district', 'skills']
        if not all(field in data for field in required_fields):
            return False

        # Validate skills structure
        if not isinstance(data['skills'], dict):
            return False

        required_skills = ['intelligence', 'hunting', 'strength', 'social',
                          'stealth', 'survival', 'agility', 'endurance', 'charisma', 'luck']
        if not all(skill in data['skills'] for skill in required_skills):
            return False

        return True

    @staticmethod
    def start_game(lobby_code: str, admin_name: str, generate_missing: bool = False) -> tuple[bool, Optional[str]]:
        """Start the game if the admin requests it. Returns (success, game_id)."""
        print(f"LobbyManager.start_game: code={lobby_code}, admin={admin_name}, generate={generate_missing}")

        if lobby_code not in lobbies:
            print(f"Lobby {lobby_code} not found")
            return False, None

        lobby = lobbies[lobby_code]
        print(f"Lobby found: players={len(lobby['players'])}, tributes={len(lobby['tribute_jsons'])}, admin={lobby['admin']}")

        if lobby['admin'] != admin_name:
            print(f"Admin check failed: expected {lobby['admin']}, got {admin_name}")
            return False, None

        if len(lobby['players']) < 2:  # Need at least 2 players
            print(f"Not enough players: {len(lobby['players'])}")
            return False, None

        # Check if we need to generate missing tributes
        total_tributes = len(lobby['tribute_jsons'])
        print(f"Total tributes: {total_tributes}")

        if total_tributes < 24 and not generate_missing:
            missing = 24 - total_tributes
            print(f"Need generation: {missing} missing tributes")
            return False, f"need_generation:{missing}"

        # If we need to generate missing tributes, do it here
        if total_tributes < 24 and generate_missing:
            generated_count = LobbyManager._generate_missing_tributes(lobby, 24 - total_tributes)
            print(f"Generated {generated_count} tributes")
            if generated_count != (24 - total_tributes):
                return False, f"Failed to generate {24 - total_tributes} tributes, only generated {generated_count}"

        print("Starting game...")
        # Mark lobby as starting
        lobby['status'] = 'starting'

        # Create game session
        game_id = str(uuid.uuid4())
        active_games[game_id] = {
            'id': game_id,
            'lobby_code': lobby_code,
            'players': lobby['players'].copy(),
            'tribute_jsons': lobby['tribute_jsons'].copy(),
            'alliances': lobby['alliances'].copy(),  # Include pre-game alliances
            'targets': lobby['targets'].copy(),  # Include pre-game targets
            'game_settings': lobby['game_settings'].copy(),  # Include game settings
            'status': 'initializing',
            'created_at': datetime.now(),
            'game_thread': None,
            'output_stream': []  # Store streamed output
        }

        # Initialize Aurora Engine if available
        if AuroraLobbyIntegration:
            try:
                aurora_integration = AuroraLobbyIntegration()
                config_path = os.path.join(os.path.dirname(__file__), '..', 'Aurora Engine', 'Engine', 'config.json')
                aurora_integration.initialize_engine(game_id, config_path=config_path, game_settings=lobby['game_settings'])
                aurora_integrations[game_id] = aurora_integration
                print(f"Aurora Engine initialized for game {game_id}")
            except Exception as e:
                print(f"Failed to initialize Aurora Engine: {e}")

        # Start game in background thread
        game_thread = threading.Thread(target=LobbyManager._run_game, args=(game_id,))
        game_thread.daemon = True
        active_games[game_id]['game_thread'] = game_thread
        game_thread.start()

        return True, game_id

    @staticmethod
    def _generate_missing_tributes(lobby: dict, count: int) -> int:
        """Generate missing tributes to reach the target count. Returns number generated."""
        try:
            generated = 0
            for i in range(count):
                # Generate a random tribute
                tribute_data = {
                    'name': f'Generated Tribute {len(lobby["tribute_jsons"]) + 1}',
                    'district': (len(lobby["tribute_jsons"]) % 12) + 1,  # Cycle through districts
                    'skills': {
                        'intelligence': 5,
                        'hunting': 5,
                        'strength': 5,
                        'social': 5,
                        'stealth': 5,
                        'survival': 5,
                        'agility': 5,
                        'endurance': 5,
                        'charisma': 5,
                        'luck': 5
                    },
                    'weapons': ['Fists'],
                    'preferred_weapon': 'Sword',
                    'target_weapon': 'Sword',
                    'health': 100,
                    'sanity': 100,
                    'speed': 5,
                    'has_camp': False,
                    'relationships': {}
                }

                # Add to lobby
                lobby['tribute_jsons'].append({
                    'player': f'Generated Player {len(lobby["tribute_jsons"]) + 1}',
                    'data': tribute_data
                })
                generated += 1

            return generated
        except Exception as e:
            print(f"Error generating tributes: {e}")
            return 0

    @staticmethod
    def _run_game(game_id: str):
        """Run the Hunger Games simulation in a background thread."""
        try:
            game_data = active_games[game_id]
            game_data['status'] = 'running'

            # Check if Aurora Engine is available for this game
            if game_id in aurora_integrations:
                # Use Aurora Engine
                aurora_integration = aurora_integrations[game_id]
                
                # Convert tribute_jsons to players format for Aurora
                players = []
                for tribute_json in game_data['tribute_jsons']:
                    tribute_data = tribute_json.get('data', {})
                    player = {
                        'id': str(uuid.uuid4()),
                        'tribute_ready': True,
                        'tribute_data': tribute_data
                    }
                    players.append(player)
                
                # Start the game with Aurora Engine
                if aurora_integration.start_game(players):
                    # Run the game loop
                    LobbyManager._run_aurora_game(game_id, aurora_integration)
                else:
                    game_data['status'] = 'error'
                    game_data['error'] = 'Failed to start Aurora game'
            else:
                # Fallback to old simulation
                result = game_runner.run_simulation_streaming(game_id, game_data['tribute_jsons'], game_data['game_settings'], active_games, game_data['alliances'], game_data['targets'])

                if result['success']:
                    game_data['status'] = 'completed'
                    game_data['results'] = {
                        'winner': result['winner'],
                        'stats': result['stats']
                    }
                else:
                    game_data['status'] = 'error'
                    game_data['error'] = result.get('error', 'Unknown error')

        except Exception as e:
            game_data['status'] = 'error'
            game_data['error'] = str(e)

    @staticmethod
    def _run_aurora_game(game_id: str, aurora_integration):
        """Run the Aurora Engine game loop."""
        try:
            game_data = active_games[game_id]
            
            while aurora_integration.game_active:
                # Process one game tick
                aurora_integration.engine.run_game_tick()
                
                # Process pending messages and emit to Socket.IO
                messages = aurora_integration.engine.get_pending_messages()
                for message in messages:
                    # Emit to all clients in the game room
                    socketio.emit('game_update', message, room=game_id)
                    
                    # Also add to output_stream for API compatibility
                    game_data['output_stream'].append({
                        'timestamp': message.get('timestamp', time.time()),
                        'message': message.get('message', ''),
                        'status': message.get('status', 'update'),
                        'game_data': message
                    })
                
                # Check if game is completed
                if aurora_integration.engine.current_status == aurora_integration.engine.EngineStatus.GAME_ENDED:
                    game_data['status'] = 'completed'
                    game_data['results'] = {
                        'winner': 'Unknown',  # TODO: Get from engine
                        'stats': {}
                    }
                    break
                
                # Small delay to prevent busy waiting
                time.sleep(0.1)
                
        except Exception as e:
            game_data['status'] = 'error'
            game_data['error'] = str(e)

    @staticmethod
    def get_game_status(game_id: str) -> Optional[dict]:
        """Get the status of a running game."""
        return active_games.get(game_id)

    @staticmethod
    def cleanup_old_lobbies():
        """Clean up lobbies that are older than 24 hours."""
        cutoff = datetime.now() - timedelta(hours=24)
        to_remove = []

        for code, lobby in lobbies.items():
            if lobby['created_at'] < cutoff:
                to_remove.append(code)

        for code in to_remove:
            del lobbies[code]

    @staticmethod
    def create_alliance(lobby_code: str, initiator_name: str, target_name: str) -> tuple[bool, Optional[str]]:
        """Create an alliance between two players. Returns (success, message)."""
        if lobby_code not in lobbies:
            return False, "Lobby not found"

        lobby = lobbies[lobby_code]

        if lobby['status'] != 'waiting':
            return False, "Cannot create alliances after game has started"

        if initiator_name not in lobby['players'] or target_name not in lobby['players']:
            return False, "Both players must be in the lobby"

        if initiator_name == target_name:
            return False, "Cannot create alliance with yourself"

        # Check if alliance already exists
        for alliance in lobby['alliances']:
            if ((alliance['initiator'] == initiator_name and alliance['target'] == target_name) or
                (alliance['initiator'] == target_name and alliance['target'] == initiator_name)):
                return False, "Alliance already exists between these players"

        # Create alliance
        alliance = {
            'initiator': initiator_name,
            'target': target_name,
            'timestamp': datetime.now()
        }

        lobby['alliances'].append(alliance)
        return True, f"Alliance formed between {initiator_name} and {target_name}"

    @staticmethod
    def set_target(lobby_code: str, hunter_name: str, target_name: str) -> tuple[bool, Optional[str]]:
        """Set a target for hunting. Returns (success, message)."""
        if lobby_code not in lobbies:
            return False, "Lobby not found"

        lobby = lobbies[lobby_code]

        if lobby['status'] != 'waiting':
            return False, "Cannot set targets after game has started"

        if hunter_name not in lobby['players'] or target_name not in lobby['players']:
            return False, "Both players must be in the lobby"

        if hunter_name == target_name:
            return False, "Cannot target yourself"

        # Check if target already exists (allow updating)
        existing_target = None
        for i, target in enumerate(lobby['targets']):
            if target['hunter'] == hunter_name:
                existing_target = i
                break

        target_data = {
            'hunter': hunter_name,
            'target': target_name,
            'timestamp': datetime.now()
        }

        if existing_target is not None:
            lobby['targets'][existing_target] = target_data
            return True, f"Updated target for {hunter_name} to {target_name}"
        else:
            lobby['targets'].append(target_data)
            return True, f"Set target for {hunter_name} to {target_name}"

    @staticmethod
    def get_alliances_and_targets(lobby_code: str) -> Optional[dict]:
        """Get alliances and targets for a lobby."""
        if lobby_code not in lobbies:
            return None

        lobby = lobbies[lobby_code]
        return {
            'alliances': lobby['alliances'],
            'targets': lobby['targets']
        }

    @staticmethod
    def generate_alliance_narrative(initiator_name: str, target_name: str) -> str:
        """Generate a narrative description for an alliance formation."""
        narratives = [
            f"{initiator_name} extends a hand of friendship to {target_name}, hoping to form a powerful alliance.",
            f"In the tense atmosphere of the lobby, {initiator_name} approaches {target_name} with talk of cooperation.",
            f"{initiator_name} and {target_name} exchange knowing glances, silently agreeing to watch each other's backs.",
            f"Amidst the uncertainty, {initiator_name} finds common ground with {target_name} and proposes an alliance.",
            f"{initiator_name} recognizes {target_name}'s potential and suggests they team up against the others.",
            f"The first sparks of strategy emerge as {initiator_name} and {target_name} form a tentative partnership.",
            f"In this game of survival, {initiator_name} chooses to trust {target_name}... for now.",
            f"{initiator_name} and {target_name} huddle together, their alliance a small beacon of hope in the coming storm."
        ]
        return random.choice(narratives)

    @staticmethod
    def generate_target_narrative(hunter_name: str, target_name: str) -> str:
        """Generate a narrative description for target setting."""
        narratives = [
            f"{hunter_name}'s eyes narrow as they mark {target_name} as their first target.",
            f"In the shadows of the lobby, {hunter_name} silently vows to eliminate {target_name} when the time comes.",
            f"{hunter_name} sizes up {target_name}, seeing them as the first obstacle to victory.",
            f"The games haven't even begun, but {hunter_name} already has {target_name} in their crosshairs.",
            f"{hunter_name} identifies {target_name} as a potential threat and decides to keep a close eye on them.",
            f"Strategy begins early as {hunter_name} marks {target_name} for elimination.",
            f"{hunter_name} and {target_name} may seem friendly now, but {hunter_name} has other plans.",
            f"The first tactical decision is made: {hunter_name} will target {target_name} when blood is spilled."
        ]
        return random.choice(narratives)

# API Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lobby/create', methods=['POST'])
def create_lobby():
    data = request.get_json()
    admin_name = data.get('admin_name', '').strip()
    max_players = data.get('max_players', 24)

    if not admin_name:
        return jsonify({'error': 'Admin name is required'}), 400

    lobby_code = LobbyManager.create_lobby(admin_name, max_players)
    return jsonify({
        'lobby_code': lobby_code,
        'message': f'Lobby created successfully. Code: {lobby_code}'
    })

@app.route('/api/lobby/<lobby_code>/join', methods=['POST'])
def join_lobby(lobby_code):
    data = request.get_json()
    player_name = data.get('player_name', '').strip()

    if not player_name:
        return jsonify({'error': 'Player name is required'}), 400

    if LobbyManager.join_lobby(lobby_code, player_name):
        lobby = LobbyManager.get_lobby(lobby_code)
        if lobby:
            return jsonify({
                'message': f'Successfully joined lobby {lobby_code}',
                'lobby': {
                    'code': lobby['code'],
                    'admin': lobby['admin'],
                    'players': lobby['players'],
                    'max_players': lobby['max_players'],
                    'status': lobby['status']
                }
            })
        else:
            return jsonify({'error': 'Lobby not found after joining'}), 500
    else:
        return jsonify({'error': 'Could not join lobby'}), 400

@app.route('/api/lobby/<lobby_code>', methods=['GET'])
def get_lobby_info(lobby_code):
    lobby = LobbyManager.get_lobby(lobby_code)
    if not lobby:
        return jsonify({'error': 'Lobby not found'}), 404

    # Check if there's an active game for this lobby
    active_game = None
    for game_id, game_data in active_games.items():
        if game_data.get('lobby_code') == lobby_code:
            active_game = {
                'id': game_id,
                'status': game_data['status'],
                'players': game_data['players']
            }
            break

    return jsonify({
        'lobby': {
            'code': lobby['code'],
            'admin': lobby['admin'],
            'players': lobby['players'],
            'max_players': lobby['max_players'],
            'status': lobby['status'],
            'tribute_count': len(lobby['tribute_jsons']),
            'tributes': [{'name': entry['data']['name'], 'district': entry['data']['district'], 'uploaded_by': entry['uploaded_by']} for entry in lobby['tribute_jsons']],
            'game_settings': lobby.get('game_settings', {}),
            'alliances': [{'initiator': a['initiator'], 'target': a['target'], 'timestamp': a['timestamp'].isoformat()} for a in lobby.get('alliances', [])],
            'targets': [{'hunter': t['hunter'], 'target': t['target'], 'timestamp': t['timestamp'].isoformat()} for t in lobby.get('targets', [])]
        },
        'active_game': active_game
    })

@app.route('/api/lobby/<lobby_code>/upload-tribute', methods=['POST'])
def upload_tribute(lobby_code):
    data = request.get_json()
    player_name = data.get('player_name', '').strip()
    tribute_data = data.get('tribute_data')

    if not player_name or not tribute_data:
        return jsonify({'error': 'Player name and tribute data are required'}), 400

    if LobbyManager.add_tribute_json(lobby_code, tribute_data, player_name):
        return jsonify({'message': 'Tribute uploaded successfully'})
    else:
        return jsonify({'error': 'Invalid tribute data or lobby not found'}), 400

@app.route('/api/lobby/<lobby_code>/settings', methods=['POST'])
def update_game_settings(lobby_code):
    data = request.get_json()
    admin_name = data.get('admin_name', '').strip()
    
    if not admin_name:
        return jsonify({'error': 'Admin name is required'}), 400
    
    # Check if user is admin
    lobby = LobbyManager.get_lobby(lobby_code)
    if not lobby or lobby['admin'] != admin_name:
        return jsonify({'error': 'Only lobby admin can update settings'}), 403
    
    # Update settings
    settings = data.get('settings', {})
    if LobbyManager.update_game_settings(lobby_code, settings):
        return jsonify({'message': 'Game settings updated successfully'})
    else:
        return jsonify({'error': 'Failed to update settings'}), 400

@app.route('/api/lobby/<lobby_code>/alliance', methods=['POST'])
def create_alliance(lobby_code):
    data = request.get_json()
    initiator_name = data.get('initiator_name', '').strip()
    target_name = data.get('target_name', '').strip()

    if not initiator_name or not target_name:
        return jsonify({'error': 'Both initiator and target names are required'}), 400

    success, message = LobbyManager.create_alliance(lobby_code, initiator_name, target_name)
    if success:
        # Generate narrative for the alliance
        narrative = LobbyManager.generate_alliance_narrative(initiator_name, target_name)
        return jsonify({
            'message': message,
            'narrative': narrative
        })
    else:
        return jsonify({'error': message}), 400

@app.route('/api/lobby/<lobby_code>/target', methods=['POST'])
def set_target(lobby_code):
    data = request.get_json()
    hunter_name = data.get('hunter_name', '').strip()
    target_name = data.get('target_name', '').strip()

    if not hunter_name or not target_name:
        return jsonify({'error': 'Both hunter and target names are required'}), 400

    success, message = LobbyManager.set_target(lobby_code, hunter_name, target_name)
    if success:
        # Generate narrative for the targeting
        narrative = LobbyManager.generate_target_narrative(hunter_name, target_name)
        return jsonify({
            'message': message,
            'narrative': narrative
        })
    else:
        return jsonify({'error': message}), 400

@app.route('/api/lobby/<lobby_code>/alliances-targets', methods=['GET'])
def get_alliances_and_targets(lobby_code):
    data = LobbyManager.get_alliances_and_targets(lobby_code)
    if data is None:
        return jsonify({'error': 'Lobby not found'}), 404

    return jsonify(data)

@app.route('/api/lobby/<lobby_code>/generate-tributes', methods=['POST'])
def generate_tributes(lobby_code):
    data = request.get_json()
    admin_name = data.get('admin_name', '').strip()
    count = data.get('count', 0)  # Number to generate, or 0 for remaining to 24

    if not admin_name:
        return jsonify({'error': 'Admin name is required'}), 400

    # Check if user is admin
    lobby = LobbyManager.get_lobby(lobby_code)
    if not lobby or lobby['admin'] != admin_name:
        return jsonify({'error': 'Only lobby admin can generate tributes'}), 403

    current_count = len(lobby['tribute_jsons'])
    if count == 0:
        count = 24 - current_count
    elif current_count + count > 24:
        count = max(0, 24 - current_count)

    if count <= 0:
        return jsonify({'error': 'No tributes to generate'}), 400

    generated = LobbyManager._generate_missing_tributes(lobby, count)
    if generated == count:
        return jsonify({'message': f'Successfully generated {generated} tributes'})
    else:
        return jsonify({'error': f'Failed to generate tributes, only generated {generated}'}), 500

@app.route('/api/lobby/<lobby_code>/start', methods=['POST'])
def start_game(lobby_code):
    data = request.get_json()
    admin_name = data.get('admin_name', '').strip()
    generate_missing = data.get('generate_missing', False)

    print(f"Start game request: lobby={lobby_code}, admin={admin_name}, generate_missing={generate_missing}")

    success, result = LobbyManager.start_game(lobby_code, admin_name, generate_missing)

    print(f"Start game result: success={success}, result={result}")

    if success:
        return jsonify({
            'message': 'Game started successfully',
            'game_id': result
        })
    else:
        if result and result.startswith('need_generation:'):
            missing_count = int(result.split(':')[1])
            return jsonify({
                'error': f'Not enough tributes. Need {missing_count} more. Would you like to generate them?',
                'need_generation': True,
                'missing_count': missing_count
            }), 400
        else:
            return jsonify({'error': result or 'Could not start game'}), 400

@app.route('/api/game/<game_id>/status', methods=['GET'])
def get_game_status(game_id):
    game = LobbyManager.get_game_status(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    return jsonify({
        'game': {
            'id': game['id'],
            'status': game['status'],
            'players': game['players'],
            'game_settings': game.get('game_settings', {}),
            'results': game.get('results'),
            'error': game.get('error'),
            'output_stream': game.get('output_stream', [])
        }
    })

@app.route('/api/game/<game_id>/tributes', methods=['GET'])
def get_game_tributes(game_id):
    game = LobbyManager.get_game_status(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # Check if Aurora integration is available for this game
    if game_id in aurora_integrations:
        integration = aurora_integrations[game_id]
        try:
            scoreboards = integration.get_tribute_scoreboards()
            return jsonify(scoreboards)
        except Exception as e:
            return jsonify({'error': f'Failed to get tribute stats: {str(e)}'}), 500
    else:
        # Return basic tribute info from game data
        tributes = []
        for tribute_json in game.get('tribute_jsons', []):
            tribute_data = tribute_json.get('data', {})
            tributes.append({
                'name': tribute_data.get('name', 'Unknown'),
                'district': tribute_data.get('district', 1),
                'uploaded_by': tribute_json.get('uploaded_by', 'Unknown'),
                'health': tribute_data.get('health', 100),  # Default values
                'sanity': tribute_data.get('sanity', 100),
                'hunger': 100,
                'thirst': 100,
                'fatigue': 0
            })
        
        return jsonify({
            'game_id': game_id,
            'tributes': tributes,
            'message': 'Using basic tribute data - Aurora integration not active'
        })

@app.route('/api/lobby/cleanup', methods=['POST'])
def cleanup_lobbies():
    LobbyManager.cleanup_old_lobbies()
    return jsonify({'message': 'Old lobbies cleaned up'})

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data.get('game_id')
    if game_id and game_id in active_games:
        # Join the game's room
        socketio.server.enter_room(request.sid, game_id)
        emit('joined_game', {'game_id': game_id, 'message': f'Joined game {game_id}'})

if __name__ == '__main__':
    # Clean up old lobbies on startup
    LobbyManager.cleanup_old_lobbies()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)