"""
Aurora Engine Integration Module
Provides integration between the lobby server and Aurora Engine
WITH ENHANCED EVENT BROADCASTING
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys

# Add the Engine directory to the path so we can import Aurora Engine
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

try:
    from Engine.Aurora_Engine import AuroraEngine, set_current_engine
    from Engine.event_broadcaster import EventBroadcaster
except ImportError:
    try:
        # Try importing with the actual filename
        import importlib.util
        spec = importlib.util.spec_from_file_location("Aurora_Engine", os.path.join(os.path.dirname(__file__), "Engine", "Aurora Engine.py"))
        aurora_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aurora_module)
        AuroraEngine = aurora_module.AuroraEngine
        set_current_engine = aurora_module.set_current_engine
        
        # Try to import event_broadcaster
        from Engine.event_broadcaster import EventBroadcaster
    except ImportError:
        print("Warning: Could not import AuroraEngine or EventBroadcaster. Make sure the Engine directory is properly set up.")
        AuroraEngine = None
        EventBroadcaster = None

class AuroraLobbyIntegration:
    """Integration layer between lobby server and Aurora Engine with enhanced event broadcasting"""

    def __init__(self):
        self.engine = None
        self.lobby_id = None
        self.game_active = False
        self.last_update_time = 0
        self.event_broadcaster = EventBroadcaster() if EventBroadcaster else None

    def initialize_engine(self, lobby_id: str, config_path: str = None, state_path: str = None, game_settings: Dict = None):
        """Initialize the Aurora Engine for a specific lobby"""
        if AuroraEngine is None:
            raise RuntimeError("AuroraEngine not available. Check Engine directory setup.")

        self.lobby_id = lobby_id
        # Only load state if state_path is provided (for resuming games)
        if state_path and os.path.exists(state_path):
            self.engine = AuroraEngine(config_path=config_path, state_path=state_path)
        else:
            self.engine = AuroraEngine(config_path=config_path)

        # Set game settings if provided
        if game_settings:
            event_delay = game_settings.get('event_delay_seconds', 1.0)
            self.engine.set_event_delay(event_delay)

        # Set this engine as the current engine for message sending
        set_current_engine(self.engine)
        
        # Initialize event broadcaster if available
        if EventBroadcaster and not self.event_broadcaster:
            self.event_broadcaster = EventBroadcaster()

        print(f"Aurora Engine initialized for lobby {lobby_id} with enhanced event broadcasting")

    def start_game(self, players: List[Any]) -> bool:
        """Start a game with the given players (can be Player objects or dicts)"""
        if not self.engine:
            return False

        try:
            print(f"[START_GAME] Starting game with {len(players)} total players", flush=True)
            
            # Convert lobby player format to engine format
            engine_players = []
            for i, player in enumerate(players):
                print(f"[START_GAME] Player {i}: {type(player).__name__}", flush=True)
                
                # Handle both Player objects (dataclasses) and dictionaries
                if hasattr(player, 'tribute_ready'):
                    # This is a Player dataclass object
                    print(f"[START_GAME]   - tribute_ready={player.tribute_ready}, has_tribute={player.tribute_data is not None}", flush=True)
                    if player.tribute_ready and player.tribute_data:
                        tribute_data = player.tribute_data
                        engine_player = {
                            'id': player.id,
                            'name': tribute_data.name or player.name or f"Player {player.id[:8]}",
                            'district': tribute_data.district,
                            'gender': tribute_data.gender,
                            'age': tribute_data.age,
                            'skills': tribute_data.skills,
                            'trait_scores': getattr(tribute_data, 'trait_scores', {}),
                            'conditions': getattr(tribute_data, 'conditions', ['healthy'])
                        }
                        engine_players.append(engine_player)
                        print(f"[START_GAME]   ✓ Added player: {engine_player['name']} from District {engine_player['district']}", flush=True)
                else:
                    # This is already a dictionary
                    print(f"[START_GAME]   - Dict player: {list(player.keys()) if isinstance(player, dict) else 'not a dict'}", flush=True)
                    if player.get('tribute_ready') and player.get('tribute_data'):
                        tribute_data = player['tribute_data']
                        engine_player = {
                            'id': player['id'],
                            'name': tribute_data.get('name') or player.get('name') or f"Player {player['id'][:8]}",
                            'district': tribute_data.get('district', 1),
                            'gender': tribute_data.get('gender', 'Male'),
                            'age': tribute_data.get('age', 16),
                            'skills': tribute_data.get('skills', {}),
                            'trait_scores': tribute_data.get('trait_scores', {}),
                            'conditions': tribute_data.get('conditions', ['healthy'])
                        }
                        engine_players.append(engine_player)
                        print(f"[START_GAME]   ✓ Added dict player: {engine_player['name']} from District {engine_player['district']}", flush=True)

            print(f"[START_GAME] Converted to {len(engine_players)} engine players", flush=True)
            if len(engine_players) < 2:
                print(f"[START_GAME] ✗ Not enough ready players: {len(engine_players)}", flush=True)
                return False

            print(f"[START_GAME] Calling engine.start_game with {len(engine_players)} players", flush=True)
            result = self.engine.start_game(engine_players)
            if result:
                self.game_active = True
                print(f"[START_GAME] ✓ Game started successfully with {len(engine_players)} players", flush=True)
                return True
            else:
                print(f"[START_GAME] ✗ Failed to start game", flush=True)
                return False

        except Exception as e:
            print(f"[START_GAME] ✗ Error starting game: {e}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
            return False

    def get_game_status(self) -> Dict[str, Any]:
        """Get current game status"""
        if not self.engine:
            return {'error': 'Engine not initialized'}

        try:
            status = self.engine.get_game_status()
            
            # Also get tribute scoreboards for display
            tribute_scoreboards = {}
            try:
                scoreboards = self.engine.game_state.get_tribute_scoreboards()
                tribute_scoreboards = scoreboards if scoreboards else {}
                print(f"[GET_GAME_STATUS] Got tribute_scoreboards: {len(tribute_scoreboards)} tributes", flush=True)
                if len(tribute_scoreboards) > 0:
                    for name, data in list(tribute_scoreboards.items())[:2]:  # Print first 2
                        print(f"[GET_GAME_STATUS]   - {name}: alive={data.get('alive')}, health={data.get('health')}", flush=True)
            except Exception as e:
                print(f"[GET_GAME_STATUS] Warning: Could not get tribute scoreboards: {e}", flush=True)
            
            return {
                'lobby_id': self.lobby_id,
                'game_active': self.game_active,
                'engine_status': status,
                'tribute_scoreboards': tribute_scoreboards,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[GET_GAME_STATUS] Error: {e}", flush=True)
            return {'error': str(e)}

    def get_tribute_scoreboards(self) -> Dict[str, Any]:
        """Get detailed tribute scoreboards with current stats"""
        if not self.engine:
            return {'error': 'Engine not initialized'}

        try:
            scoreboards = self.engine.game_state.get_tribute_scoreboards()
            return {
                'lobby_id': self.lobby_id,
                'tribute_scoreboards': scoreboards,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def process_game_tick(self) -> List[Dict[str, Any]]:
        """Process one game tick and return enhanced messages for broadcast"""
        if not self.engine or not self.game_active:
            return []

        try:
            # Process messages one at a time instead of batching
            all_messages = []

            # 1. Check for cornucopia updates during cornucopia phase (highest priority)
            current_phase = self.engine.phase_controller.get_current_phase_info()
            if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
                cornucopia_messages = self.engine.process_cornucopia_updates()
                if cornucopia_messages:
                    all_messages.extend(cornucopia_messages)

            # 2. Check for phase advancement
            if current_phase:
                # Don't advance phases while cornucopia countdown is still active
                should_check_advancement = True
                
                if (current_phase.get("phase_info", {}).get("type") == "cornucopia" and 
                    hasattr(self.engine, 'cornucopia_controller')):
                    if self.engine.cornucopia_controller.is_completed():
                        print(f"[CORNUCOPIA] Cornucopia completed - forcing phase advancement")
                        should_check_advancement = True
                    elif not self.engine.cornucopia_controller.is_completed():
                        timer_info = self.engine.cornucopia_controller.get_timer_info()
                        if timer_info.remaining_seconds > 0 or timer_info.phase in ["countdown", "decision", "bloodbath"]:
                            should_check_advancement = False
                            print(f"[CORNUCOPIA] Waiting for cornucopia to complete: phase={timer_info.phase}")
                
                if should_check_advancement:
                    if (current_phase.get("phase_info", {}).get("type") == "cornucopia" and 
                        hasattr(self.engine, 'cornucopia_controller') and 
                        self.engine.cornucopia_controller.is_completed()):
                        print(f"[CORNUCOPIA] Forcing phase advancement after bloodbath completion")
                        phase_message = self.engine.advance_phase()
                    else:
                        phase_message = self.engine.check_timers_and_advance()
                    
                    if phase_message:
                        all_messages.append(phase_message)

            # 3. Process pending messages from engine queue
            in_countdown = False
            if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
                if hasattr(self.engine, 'cornucopia_controller') and not self.engine.cornucopia_controller.is_completed():
                    timer_info = self.engine.cornucopia_controller.get_timer_info()
                    if timer_info.remaining_seconds > 0 or timer_info.phase in ["countdown", "decision", "bloodbath"]:
                        in_countdown = True
            
            pending_messages = self.engine.get_pending_messages()
            if pending_messages:
                if in_countdown:
                    allowed_types = ['game_started', 'cornucopia_countdown', 'cornucopia_update', 'phase_change']
                    filtered_messages = [msg for msg in pending_messages if msg.get('message_type') in allowed_types]
                    blocked_messages = [msg for msg in pending_messages if msg.get('message_type') not in allowed_types]
                    if blocked_messages:
                        print(f"[CORNUCOPIA] Dropped {len(blocked_messages)} non-essential messages during countdown")
                    pending_messages = filtered_messages
                
                all_messages.extend(pending_messages)

            # 4. Generate new event if ready
            should_generate_events = True
            if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
                if hasattr(self.engine, 'cornucopia_controller') and not self.engine.cornucopia_controller.is_completed():
                    timer_info = self.engine.cornucopia_controller.get_timer_info()
                    if timer_info.remaining_seconds > 0 or timer_info.phase == "countdown":
                        should_generate_events = False
                        
            if should_generate_events and len(all_messages) < 2:
                event_message = self._generate_event_if_ready()
                if event_message:
                    all_messages.append(event_message)

            # 4. Process any pending inputs
            if len(all_messages) < 3:
                input_responses = self.engine.process_pending_inputs()
                if input_responses:
                    all_messages.extend(input_responses[:2])

            # 5. Send phase timer update
            if current_phase:
                phase_timer_update = self._get_phase_timer_update(current_phase)
                if phase_timer_update:
                    all_messages.append(phase_timer_update)

            # ============= ENHANCED EVENT BROADCASTING =============
            # Enhance messages with rich narratives before returning
            if self.event_broadcaster:
                enhanced_messages = []
                for msg in all_messages:
                    # Try to enhance the message
                    try:
                        enhanced = self.event_broadcaster.broadcast_event(msg, self.engine.game_state)
                        enhanced_messages.append(enhanced)
                        print(f"[ENHANCED] Enhanced {msg.get('message_type')} -> {enhanced.get('category', 'unknown')}")
                    except Exception as e:
                        # If enhancement fails, use original message
                        print(f"[ENHANCE_ERROR] Failed to enhance message: {e}")
                        enhanced_messages.append(msg)
                
                all_messages = enhanced_messages
            # =======================================================

            if all_messages:
                print(f"[GAME_TICK] Sending {len(all_messages)} enhanced messages this tick")
                for i, msg in enumerate(all_messages):
                    msg_type = msg.get('message_type', 'unknown')
                    category = msg.get('category', '-')
                    priority = msg.get('priority', '-')
                    print(f"  {i+1}. {msg_type} [{category}] (priority: {priority})")

            return all_messages

        except Exception as e:
            import traceback
            print(f"Error processing game tick: {e}")
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
            return []

    def _generate_event_if_ready(self) -> Optional[Dict[str, Any]]:
        """Generate an event only if cooldowns allow it"""
        if not self.engine or not self.game_active:
            return None

        # Check if any event type is ready based on cooldowns
        current_time = datetime.now()
        event_cooldowns = self.engine.config.get('timers', {}).get('event_cooldowns', {})

        for event_type, cooldown_seconds in event_cooldowns.items():
            last_event_time = self.engine.game_state.event_timers.get(event_type)
            if last_event_time is None or (current_time - last_event_time).total_seconds() >= cooldown_seconds:
                # This event type is ready, generate an event
                event = self.engine.generate_event(event_type)
                if event:
                    # Update the timer for this event type
                    self.engine.game_state.event_timers[event_type] = current_time
                    return event

        return None

    def _get_phase_timer_update(self, current_phase: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a phase timer update for UI countdown"""
        if not self.engine or not self.engine.game_state:
            return None
        
        try:
            phase_info = current_phase.get("phase_info", {})
            phase_name = phase_info.get("name", "Unknown Phase")
            phase_type = phase_info.get("type", "unknown")
            
            # Special handling for cornucopia - use cornucopia controller timer instead
            if phase_type == "cornucopia" and hasattr(self.engine, 'cornucopia_controller'):
                # During cornucopia, don't send phase timer updates - the cornucopia timer handles this
                # This prevents confusion between the 60-second countdown and phase duration
                return None
            
            # For all other phases, use the normal phase timer
            phase_timer = self.engine.game_state.phase_timer
            if not phase_timer:
                return None
            
            now = datetime.now()
            if now >= phase_timer:
                # Phase should advance
                seconds_remaining = 0
            else:
                seconds_remaining = int((phase_timer - now).total_seconds())
            
            # Format the time remaining message
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            formatted_time = f"{minutes}m {seconds}s remaining" if minutes > 0 else f"{seconds}s remaining"
            
            return {
                "message_type": "phase_timer_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "phase_name": phase_name,
                    "phase_type": phase_type,
                    "seconds_remaining": seconds_remaining,
                    "phase_duration": phase_info.get("duration_minutes", 30) * 60,
                    "formatted_time": formatted_time
                }
            }
        except Exception as e:
            print(f"[PHASE_TIMER] Error generating timer update: {e}")
            return None

    def get_game_events_since(self, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get game events since the given timestamp"""
        if not self.engine:
            return []

        try:
            return self.engine.get_animation_events(since_timestamp)
        except Exception as e:
            print(f"Error getting game events: {e}")
            return []

    def process_player_input(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process player input through the engine"""
        if not self.engine:
            return None

        try:
            return self.engine.process_input(input_data)
        except Exception as e:
            print(f"Error processing player input: {e}")
            return None

    def save_game_state(self):
        """Save current game state"""
        if self.engine:
            self.engine.save_game_state()

    def load_game_state(self):
        """Load game state"""
        if self.engine:
            self.engine.load_game_state()

# Global integration instance
aurora_integration = AuroraLobbyIntegration()