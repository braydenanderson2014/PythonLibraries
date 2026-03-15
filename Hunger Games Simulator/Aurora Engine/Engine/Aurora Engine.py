#!/usr/bin/env python3
"""
Aurora Engine - Core Engine for Hunger Games Simulator
Generates JSON messages for the web game manager system.
"""

import json
import os
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from Phase_Controller.phase_controller import PhaseController
from game_state import GameState
from cornucopia_controller import CornucopiaController
from relationship_manager import RelationshipManager
from weapons_system import WeaponsSystem, get_weapons_system
from limb_damage_system import LimbDamageSystem, BodyPart


class EngineStatus(Enum):
    """Detailed status states for the Aurora Engine"""
    INITIALIZING = "initializing"
    LOBBY_CREATED = "lobby_created"
    AWAITING_PLAYERS = "awaiting_players"
    GAME_STARTING = "game_starting"
    CORNUCOPIA_ACTIVE = "cornucopia_active"
    GENERATING_EVENTS = "generating_events"
    PVP_ACTIVE = "pvp_active"
    PHASE_TRANSITION = "phase_transition"
    GAME_ENDED = "game_ended"
    ERROR = "error"


class AuroraEngine:
    """Main Aurora Engine that manages game phases and generates events"""

    def __init__(self, config_path: str = None, state_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Load event messages
        messages_path = os.path.join(os.path.dirname(__file__), "event_messages.json")
        with open(messages_path, 'r') as f:
            self.event_messages = json.load(f)

        self.config_path = config_path
        self.state_path = state_path
        self.phase_controller = PhaseController(config_path)
        self.game_state = GameState(self.config)
        self.cornucopia_controller = CornucopiaController(self.config)

        # Detailed status tracking
        self.current_status = EngineStatus.INITIALIZING
        self.status_details = {
            "message": "Engine initializing...",
            "timestamp": datetime.now().isoformat(),
            "active_processes": [],
            "last_activity": None
        }

        # Only load existing game state if state_path was explicitly provided
        if state_path is not None:
            self.load_game_state()

        self.game_active = False
        self.message_queue = []
        self.event_log = []
        
        # Event persistence tracking
        self.active_environmental_effects = []  # Multi-phase weather/hazards
        self.last_event_by_category = {}  # Track event cooldowns for preventing repetition
        
        # Relationship manager for trust and social dynamics
        self.relationship_manager = RelationshipManager()
        
        # Weapons and combat systems
        self.weapons_system = get_weapons_system()
        self.limb_damage_system = LimbDamageSystem()

        # Configurable event delay
        self.event_delay_seconds = 1.0

        # Update status after initialization
        self._update_status(EngineStatus.LOBBY_CREATED, "Lobby created and ready for players")

    def _update_status(self, status: EngineStatus, message: Optional[str] = None, active_processes: Optional[List[str]] = None):
        """Update the engine's detailed status"""
        self.current_status = status
        self.status_details.update({
            "message": message or f"Status: {status.value}",
            "timestamp": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        })

        if active_processes is not None:
            self.status_details["active_processes"] = active_processes

    def set_event_delay(self, delay_seconds: float):
        """Set the delay between events in seconds"""
        self.event_delay_seconds = max(0.0, delay_seconds)  # Prevent negative delays

    def start_game(self, players: List[Dict[str, Any]], predefined_relationships: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a new game with the given players
        
        Args:
            players: List of player/tribute data
            predefined_relationships: Optional dict of pre-defined relationships from web UI
                Format: {
                    "tribute1_id|tribute2_id": {
                        "trust": 75,
                        "is_alliance": true,
                        "relationship_type": "district_partner"
                    }
                }
        """
        self._update_status(EngineStatus.GAME_STARTING, f"Starting game with {len(players)} players")

        self.game_active = True

        # Initialize phase controller
        phase_data = self.phase_controller.start_game()

        # Initialize game state with tributes
        tribute_ids = []
        for player in players:
            tribute_id = player.get("id", player.get("tribute_id", f"player_{len(self.game_state.tributes)}"))
            is_resume = player.get("is_resume", False)
            self.game_state.add_tribute(tribute_id, player, is_resume)
            tribute_ids.append(tribute_id)
        
        # Initialize relationship system
        self.relationship_manager.initialize_relationships(tribute_ids, predefined_relationships)
        
        # Inject relationship manager into Nemesis Behavior Engine if available
        try:
            from Nemesis_Behavior_Engine.NemesisBehaviorEngine import NemesisBehaviorEngine
            # This will be used during cornucopia and event generation
            print("[Aurora Engine] Relationship manager ready for Nemesis Behavior Engine integration")
        except ImportError:
            print("[Aurora Engine] Nemesis Behavior Engine not available")

        # Start cornucopia countdown if this is cornucopia phase
        current_phase = self.phase_controller.get_current_phase_info()
        if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
            # Gather tribute data for early step-off calculations
            tributes = []
            for tribute_id, tribute_obj in self.game_state.tributes.items():
                if self.game_state.tribute_statuses.get(tribute_id) == "alive":
                    tributes.append({
                        "id": tribute_id,
                        "name": tribute_obj.name,
                        "skills": tribute_obj.skills,
                        "district": tribute_obj.district
                    })
            
            countdown_message = self.cornucopia_controller.start_countdown(tributes)
            self.message_queue.append(countdown_message)
            self.event_log.append(countdown_message)
            self._update_status(EngineStatus.CORNUCOPIA_ACTIVE, "Cornucopia countdown in progress")

        # Create start game message
        start_message = {
            "message_type": "game_started",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "players": players,
                "phase_info": phase_data,
                "game_state": self.game_state.get_game_status(),
                "relationships": self.relationship_manager.get_all_relationships_data(),
                "cornucopia_timer": self.cornucopia_controller.get_timer_info().__dict__ if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia" else None
            }
        }

        self.message_queue.append(start_message)
        self.event_log.append(start_message)

        # Update status based on current phase
        if not (current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia"):
            self._update_status(EngineStatus.GENERATING_EVENTS, "Game active - generating events")

        return start_message

    def generate_event(self, force_event_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Generate an event appropriate for the current phase"""
        if not self.game_active:
            return None

        self._update_status(EngineStatus.GENERATING_EVENTS, "Generating game events", ["event_generation"])

        # Get current phase information first
        current_phase = self.phase_controller.get_current_phase_info()
        if current_phase is None:
            return None
        
        phase_type = current_phase.get("phase_info", {}).get("type", "")
        
        # During cornucopia phase, prioritize cornucopia events over random encounters
        if phase_type == "cornucopia":
            # 70% chance to generate cornucopia-specific events, 30% for encounters
            if random.random() < 0.7:
                allowed_events = current_phase['phase_info']['allowed_events']
                if allowed_events:
                    event_type = self._weighted_choice(allowed_events)
                    if self.game_state.can_generate_event(event_type):
                        event_data = self._generate_event_data(event_type, current_phase)
                        if event_data:
                            self.game_state.record_event({
                                "event_category": event_type,
                                "description": event_data["description"],
                                "participants": event_data["participants"],
                                "consequences": event_data["consequences"],
                                "intensity": event_data["intensity"],
                                "narrative": event_data["narrative"]
                            })
                            return {
                                "message_type": "game_event",
                                "timestamp": datetime.now().isoformat(),
                                "data": {
                                    "event_type": event_type,
                                    "phase_info": current_phase,
                                    "event_data": event_data,
                                    "game_state": self.game_state.get_game_status(),
                                    "tribute_scoreboards": self.game_state.get_tribute_scoreboards()
                                }
                            }

        # Check for random encounters
        random_encounter = self.game_state.generate_random_encounter()
        if random_encounter:
            return self._generate_random_encounter_event(random_encounter)

        # Occasionally generate flavor events for atmosphere (15% chance)
        if random.random() < 0.15:
            flavor_event = self._generate_flavor_event()
            if flavor_event:
                return flavor_event

        allowed_events = current_phase['phase_info']['allowed_events']
        if not allowed_events:
            return None

        # Select event type
        if force_event_type and force_event_type in allowed_events:
            event_type = force_event_type
        else:
            # Dynamic difficulty scaling based on remaining tributes
            alive_tributes = sum(1 for status in self.game_state.tribute_statuses.values() if status == "alive")
            total_tributes = len(self.game_state.tributes)
            
            # As fewer tributes remain, reduce chance of skipping events and increase intensity
            survival_rate = alive_tributes / max(total_tributes, 1)
            skip_chance = max(0.1, 0.25 * survival_rate)  # Less skipping when few tributes remain
            
            if random.random() < skip_chance:
                return None
            event_type = self._weighted_choice(allowed_events)

        # Check if we can generate this event type based on timers
        if not self.game_state.can_generate_event(event_type):
            return None
        
        # Context validation - ensure tributes are capable of this event type
        if not self._validate_event_context(event_type):
            return None

        # Generate event based on type
        event_data = self._generate_event_data(event_type, current_phase)

        # Record event in game state
        self.game_state.record_event({
            "event_category": event_type,
            "description": event_data["description"],
            "participants": event_data["participants"],
            "consequences": event_data["consequences"],
            "intensity": event_data["intensity"],
            "narrative": event_data["narrative"]
        })

        # Create JSON message
        event_message = {
            "message_type": "game_event",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "event_type": event_type,
                "phase_info": current_phase,
                "event_data": event_data,
                "game_state": self.game_state.get_game_status(),
                "tribute_scoreboards": self.game_state.get_tribute_scoreboards()
            }
        }

        # DON'T add to message_queue - we're returning it directly
        # self.message_queue.append(event_message)
        self.event_log.append(event_message)

        # Apply configurable delay between events
        time.sleep(self.event_delay_seconds)

        return event_message

    def process_cornucopia_updates(self) -> List[Dict[str, Any]]:
        """Process cornucopia countdown and decision-making"""
        if not self.game_active:
            return []
            
        current_phase = self.phase_controller.get_current_phase_info()
        if not current_phase or current_phase.get("phase_info", {}).get("type") != "cornucopia":
            return []
            
        if self.cornucopia_controller.is_completed():
            print(f"[CORNUCOPIA DEBUG] Cornucopia already completed, returning empty")
            return []
            
        messages = []
        
        # Log current cornucopia phase
        print(f"[CORNUCOPIA DEBUG] Processing cornucopia updates - Current phase: {self.cornucopia_controller.current_phase.value}")
        
        # Update countdown timer
        countdown_update = self.cornucopia_controller.update_countdown()
        if countdown_update:
            print(f"[CORNUCOPIA DEBUG] Countdown update: {countdown_update.get('message_type')}")
            messages.append(countdown_update)
            # Don't add to message_queue - we're returning it directly
            self.event_log.append(countdown_update)
            
            # Check if this is an early step-off death event
            if countdown_update.get("message_type") == "early_step_off":
                tribute_id = countdown_update.get("data", {}).get("tribute_id")
                if tribute_id and tribute_id in self.game_state.tributes:
                    # Kill the tribute
                    tribute = self.game_state.tributes[tribute_id]
                    tribute.status = "dead"
                    tribute.death_time = datetime.now().isoformat()
                    tribute.cause_of_death = "Landmine detonation (stepped off platform early)"
                    self.game_state.tribute_statuses[tribute_id] = "dead"
                    self.game_state.fallen_tributes.append({
                        "tribute_id": tribute_id,
                        "tribute_name": tribute.name,
                        "district": tribute.district,
                        "day": self.game_state.current_day,
                        "cause_of_death": tribute.cause_of_death,
                        "timestamp": tribute.death_time
                    })
                    print(f"[EARLY STEP-OFF] {tribute.name} killed by landmine before the gong")
            
        # Handle decision phase
        if self.cornucopia_controller.current_phase.value == "decision":
            # Get current tributes
            tributes = []
            for tribute_id, tribute_obj in self.game_state.tributes.items():
                if self.game_state.tribute_statuses.get(tribute_id) == "alive":
                    tributes.append({
                        "id": tribute_id,
                        "name": tribute_obj.name,
                        "skills": tribute_obj.skills,
                        "district": tribute_obj.district
                    })
            
            # Use Nemesis Engine if available
            nemesis_engine = None
            try:
                from Nemesis_Behavior_Engine.NemesisBehaviorEngine import NemesisBehaviorEngine
                nemesis_engine = NemesisBehaviorEngine()
            except ImportError:
                pass  # Fallback to basic decision making
                
            # Make tribute decisions
            print(f"[CORNUCOPIA DEBUG] Calling make_tribute_decisions for {len(tributes)} tributes")
            decision_messages = self.cornucopia_controller.make_tribute_decisions(tributes, nemesis_engine)
            print(f"[CORNUCOPIA DEBUG] make_tribute_decisions returned {len(decision_messages)} messages, phase now: {self.cornucopia_controller.current_phase.value}")
            messages.extend(decision_messages)
            # Only log these, don't queue them (we're already returning them)
            for msg in decision_messages:
                self.event_log.append(msg)
        
        # Handle bloodbath phase
        elif self.cornucopia_controller.current_phase.value == "bloodbath":
            # Get current tributes for bloodbath
            tributes = []
            for tribute_id, tribute_obj in self.game_state.tributes.items():
                if self.game_state.tribute_statuses.get(tribute_id) == "alive":
                    tributes.append({
                        "id": tribute_id,
                        "name": tribute_obj.name,
                        "skills": tribute_obj.skills,
                        "district": tribute_obj.district
                    })
                    
            print(f"[CORNUCOPIA DEBUG] Calling execute_bloodbath for {len(tributes)} tributes")
            bloodbath_messages = self.cornucopia_controller.execute_bloodbath(tributes)
            print(f"[CORNUCOPIA DEBUG] execute_bloodbath returned {len(bloodbath_messages)} messages, phase now: {self.cornucopia_controller.current_phase.value}")
            messages.extend(bloodbath_messages)
            
            # Process bloodbath events and kill tributes
            for msg in bloodbath_messages:
                self.event_log.append(msg)
                
                # Handle death events
                if msg.get("message_type") == "cornucopia_death":
                    victim_id = msg.get("data", {}).get("victim_id")
                    victim_name = msg.get("data", {}).get("victim_name")
                    killer_id = msg.get("data", {}).get("killer_id")
                    killer_name = msg.get("data", {}).get("killer_name")
                    
                    if victim_id and victim_id in self.game_state.tributes:
                        # Kill the tribute
                        tribute = self.game_state.tributes[victim_id]
                        tribute.status = "dead"
                        tribute.death_time = datetime.now().isoformat()
                        tribute.cause_of_death = f"Killed by {killer_name} at the cornucopia"
                        self.game_state.tribute_statuses[victim_id] = "dead"
                        self.game_state.fallen_tributes.append({
                            "tribute_id": victim_id,
                            "tribute_name": victim_name,
                            "district": tribute.district,
                            "day": self.game_state.current_day,
                            "cause_of_death": tribute.cause_of_death,
                            "killer_id": killer_id,
                            "killer_name": killer_name,
                            "timestamp": tribute.death_time
                        })
                        print(f"[CORNUCOPIA DEATH] {victim_name} killed by {killer_name}")
                
                # Store supply distribution data
                if msg.get("message_type") == "cornucopia_bloodbath":
                    supplies_claimed = msg.get("data", {}).get("supplies_claimed", 0)
                    participants = msg.get("data", {}).get("participants", 0)
                    
                    # Store for later distribution
                    self.cornucopia_controller.store_supply_distribution_data(
                        tributes, supplies_claimed, participants
                    )
                    print(f"[CORNUCOPIA] Bloodbath complete - supplies will be distributed after phase ends")
                
        # Send timer updates for UI
        timer_info = self.cornucopia_controller.get_timer_info()
        timer_message = {
            "message_type": "cornucopia_timer_update",
            "timestamp": datetime.now().isoformat(),
            "data": timer_info.__dict__
        }
        messages.append(timer_message)
        
        return messages

    def advance_phase(self) -> Optional[Dict[str, Any]]:
        """Advance to the next phase"""
        if not self.game_active:
            return None

        self._update_status(EngineStatus.PHASE_TRANSITION, "Advancing to next game phase", ["phase_transition"])

        # Check if we're leaving cornucopia phase - if so, distribute supplies now
        current_phase = self.phase_controller.get_current_phase_info()
        if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
            if self.cornucopia_controller.is_completed():
                print("[CORNUCOPIA] Phase completed - distributing supplies now")
                self._distribute_cornucopia_supplies()

        next_phase = self.phase_controller.advance_phase()

        if next_phase is None:
            # Game over
            self._update_status(EngineStatus.GAME_ENDED, "Game completed - all phases finished")
            end_message = {
                "message_type": "game_ended",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "reason": "All phases completed",
                    "final_stats": self.get_game_stats(),
                    "final_game_state": self.game_state.get_game_status(),
                    "final_tribute_scoreboards": self.game_state.get_tribute_scoreboards()
                }
            }
            self.message_queue.append(end_message)
            self.event_log.append(end_message)
            self.game_active = False
            self.save_game_state()  # Save final game state
            return end_message

        # Sync game state phase
        self.game_state.advance_phase()

        # Apply stat decay to all tributes at phase end
        # This represents the passage of time and environmental effects
        self._apply_phase_end_stat_decay()
        
        # Process trust decay for all relationships
        self.relationship_manager.process_trust_decay()

        # Phase change message
        phase_message = {
            "message_type": "phase_changed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                **next_phase,
                "game_state": self.game_state.get_game_status(),
                "tribute_scoreboards": self.game_state.get_tribute_scoreboards(),
                "relationships": self.relationship_manager.get_all_relationships_data()
            }
        }

        # DON'T add to message_queue - we're returning it directly
        # self.message_queue.append(phase_message)
        self.event_log.append(phase_message)

        # Update status based on new phase
        current_phase_info = self.phase_controller.get_current_phase_info()
        if current_phase_info and current_phase_info.get("type") == "cornucopia":
            self._update_status(EngineStatus.CORNUCOPIA_ACTIVE, "Cornucopia bloodbath in progress")
        else:
            self._update_status(EngineStatus.GENERATING_EVENTS, f"Phase {current_phase_info.get('day', 1)} active - generating events")

        self.save_game_state()  # Save state after phase change
        return phase_message

    def get_pending_messages(self) -> List[Dict[str, Any]]:
        """Get all pending messages and clear the queue"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages

    def process_input(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process external input commands"""
        self.game_state.add_input(input_data)

        command_type = input_data.get("command_type")
        response_message = None

        if command_type == "pvp_request":
            pvp_settings = self.config.get('pvp_settings', {})
            if not pvp_settings.get('allow_player_initiated_pvp', False):
                response_message = {
                    "message_type": "input_response",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "command_type": "pvp_request",
                        "success": False,
                        "reason": "Player-initiated PvP is disabled. Random encounters only.",
                        "input_id": input_data.get("id")
                    }
                }
            else:
                success = self._handle_pvp_request(input_data)
                response_message = {
                    "message_type": "input_response",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "command_type": "pvp_request",
                        "success": success,
                        "input_id": input_data.get("id"),
                        "game_state": self.game_state.get_game_status()
                    }
                }

        elif command_type == "status_request":
            response_message = {
                "message_type": "status_response",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "game_state": self.game_state.get_game_status(),
                    "animation_events": self.game_state.get_animation_events(input_data.get("since_timestamp"))
                }
            }

        elif command_type == "force_event":
            event_msg = self.generate_event(input_data.get("event_type"))
            if event_msg:
                response_message = {
                    "message_type": "input_response",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "command_type": "force_event",
                        "success": True,
                        "event_generated": event_msg,
                        "input_id": input_data.get("id")
                    }
                }
            else:
                response_message = {
                    "message_type": "input_response",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "command_type": "force_event",
                        "success": False,
                        "reason": "Event generation failed (timer or phase restrictions)",
                        "input_id": input_data.get("id")
                    }
                }

        elif command_type == "register_tribute":
            success = self._handle_tribute_registration(input_data)
            response_message = {
                "message_type": "input_response",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "command_type": "register_tribute",
                    "success": success,
                    "input_id": input_data.get("id"),
                    "tribute_id": input_data.get("tribute_id"),
                    "game_state": self.game_state.get_game_status()
                }
            }

        elif command_type == "update_tribute_status":
            success = self._handle_tribute_status_update(input_data)
            response_message = {
                "message_type": "input_response",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "command_type": "update_tribute_status",
                    "success": success,
                    "input_id": input_data.get("id"),
                    "game_state": self.game_state.get_game_status()
                }
            }

        # Clear processed input
        if response_message:
            self.game_state.clear_processed_inputs([input_data])

        if response_message:
            self.message_queue.append(response_message)

        return response_message

    def _handle_pvp_request(self, input_data: Dict[str, Any]) -> bool:
        """Handle a PvP battle request"""
        initiator_id = input_data.get("initiator_id")
        target_id = input_data.get("target_id")

        if not initiator_id or not target_id:
            return False

        success = self.game_state.add_pvp_request(initiator_id, target_id)

        if success:
            # Process the PvP request immediately if possible
            pending_requests = self.game_state.pending_pvp_requests
            for i, request in enumerate(pending_requests):
                if (request["initiator_id"] == initiator_id and
                    request["target_id"] == target_id):
                    pvp_battle = self.game_state.process_pvp_request(i)
                    if pvp_battle:
                        # Update status for PvP activity
                        self._update_status(EngineStatus.PVP_ACTIVE, f"PvP battle active: {initiator_id} vs {target_id}", ["pvp_battle"])
                        # Generate PvP event
                        self.generate_event("PvP Events")
                        self.save_game_state()  # Save after PvP event
                        # Reset status after PvP
                        self._update_status(EngineStatus.GENERATING_EVENTS, "PvP completed, resuming normal events")
                    break

        return success

    def _handle_tribute_registration(self, input_data: Dict[str, Any]) -> bool:
        """Handle tribute registration from web interface"""
        tribute_id = input_data.get("tribute_id")
        tribute_data = input_data.get("tribute_data", {})
        is_resume = input_data.get("is_resume", False)

        if not tribute_id:
            return False

        try:
            self.game_state.add_tribute(tribute_id, tribute_data, is_resume)
            self.save_game_state()  # Save after tribute registration
            return True
        except Exception as e:
            print(f"Error registering tribute {tribute_id}: {e}")
            return False

    def _handle_tribute_status_update(self, input_data: Dict[str, Any]) -> bool:
        """Handle tribute status updates from web interface"""
        tribute_identifier = input_data.get("tribute_id") or input_data.get("tribute_name")
        status = input_data.get("status")
        details = input_data.get("details", {})

        if not tribute_identifier or not status:
            return False

        try:
            self.game_state.update_tribute_status_by_identifier(tribute_identifier, status, details)
            self.save_game_state()  # Save after tribute status update
            return True
        except Exception as e:
            print(f"Error updating tribute status for {tribute_identifier}: {e}")
            return False

    def check_timers_and_advance(self) -> Optional[Dict[str, Any]]:
        """Check if phase should advance based on timers"""
        # Special handling for cornucopia - don't advance until countdown completes
        current_phase = self.phase_controller.get_current_phase_info()
        if current_phase and current_phase.get("phase_info", {}).get("type") == "cornucopia":
            # Only advance if cornucopia is fully completed (countdown + bloodbath)
            is_completed = self.cornucopia_controller.is_completed()
            print(f"[CORNUCOPIA DEBUG] check_timers_and_advance - is_completed: {is_completed}, current_phase: {self.cornucopia_controller.current_phase.value}")
            if is_completed:
                print("[CORNUCOPIA DEBUG] Countdown completed - advancing phase")
                return self.advance_phase()
            else:
                # Still in countdown - don't advance yet
                print(f"[CORNUCOPIA DEBUG] Still in cornucopia phase ({self.cornucopia_controller.current_phase.value}), not advancing")
                return None
        
        # For all other phases, use normal timer-based advancement
        if self.game_state.should_advance_phase():
            return self.advance_phase()
        return None

    def get_game_status(self) -> Dict[str, Any]:
        """Get comprehensive game status"""
        return {
            "game_active": self.game_active,
            "engine_status": {
                "status": self.current_status.value,
                "message": self.status_details["message"],
                "timestamp": self.status_details["timestamp"],
                "active_processes": self.status_details["active_processes"],
                "last_activity": self.status_details["last_activity"]
            },
            "phase_info": self.phase_controller.get_current_phase_info(),
            "game_state": self.game_state.get_game_status(),
            "tribute_scoreboards": self.game_state.get_tribute_scoreboards(),
            "pending_messages": len(self.message_queue),
            "total_events": len(self.event_log)
        }

    def get_animation_events(self, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get events suitable for web animations"""
        return self.game_state.get_animation_events(since_timestamp)

    def process_pending_inputs(self) -> List[Dict[str, Any]]:
        """Process all pending inputs and return responses"""
        pending_inputs = self.game_state.get_pending_inputs()
        responses = []

        for input_data in pending_inputs:
            response = self.process_input(input_data)
            if response:
                responses.append(response)

        return responses

    def _generate_event_data(self, event_type: str, phase_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate event data based on event type using structured message system and context-aware generators"""
        
        # === CONTEXT-AWARE EVENT ROUTING ===
        # Check for special event types that use specialized generators
        
        # 1. Combat Events - Use weapon-based combat system
        if event_type == "Combat Events":
            alive_tributes = [
                self.game_state.tributes[tid] 
                for tid, status in self.game_state.tribute_statuses.items() 
                if status == "alive"
            ]
            
            if len(alive_tributes) >= 2:
                # 40% chance to use advanced combat system
                if random.random() < 0.4:
                    # Select combatants (prefer enemies if available)
                    attacker = random.choice(alive_tributes)
                    potential_targets = [t for t in alive_tributes if t.tribute_id != attacker.tribute_id]
                    
                    # Prioritize enemies
                    if self.relationship_manager:
                        enemies = self.relationship_manager.get_enemies(attacker.tribute_id)
                        enemy_ids = [e_id for e_id, _ in enemies]
                        enemy_targets = [t for t in potential_targets if t.tribute_id in enemy_ids]
                        if enemy_targets:
                            potential_targets = enemy_targets
                    
                    if potential_targets:
                        defender = random.choice(potential_targets)
                        combat_event = self._generate_combat_event(attacker, defender)
                        if combat_event:
                            return combat_event
        
        # 2. Medical Events - Check for tributes needing treatment
        if event_type == "Idle Events" or event_type == "Custom Events":
            # 20% chance to generate medical event if tributes have untreated wounds
            if random.random() < 0.2:
                injured_tributes = []
                for tid, status in self.game_state.tribute_statuses.items():
                    if status == "alive":
                        tribute = self.game_state.tributes[tid]
                        if hasattr(tribute, 'limb_damage'):
                            if tribute.limb_damage.get_untreated_wounds():
                                injured_tributes.append(tribute)
                
                if injured_tributes:
                    tribute_to_treat = random.choice(injured_tributes)
                    medical_event = self._generate_medical_event(tribute_to_treat)
                    if medical_event:
                        return medical_event
        
        # 3. Betrayal Events - Check for betrayal opportunities
        if event_type == "Combat Events" or event_type == "Custom Events":
            # 15% chance to check for betrayal
            if random.random() < 0.15 and self.relationship_manager:
                alive_tributes = [
                    self.game_state.tributes[tid] 
                    for tid, status in self.game_state.tribute_statuses.items() 
                    if status == "alive"
                ]
                
                for tribute in alive_tributes:
                    relationships = self.relationship_manager.get_all_relationships_for_tribute(
                        tribute.tribute_id
                    )
                    allies = [r for r in relationships if r.is_alliance]
                    
                    if allies:
                        for ally_rel in allies:
                            ally_id = ally_rel.tribute_b if ally_rel.tribute_a == tribute.tribute_id else ally_rel.tribute_a
                            ally = self.game_state.tributes.get(ally_id)
                            if ally and ally.status == "alive":
                                betrayal_event = self._generate_betrayal_event(tribute, ally)
                                if betrayal_event:
                                    return betrayal_event
        
        # 4. Alliance Events - Check for alliance formation opportunities
        if event_type == "Idle Events" or event_type == "Custom Events":
            # 10% chance to form alliance
            if random.random() < 0.1 and self.relationship_manager:
                alive_tributes = [
                    self.game_state.tributes[tid] 
                    for tid, status in self.game_state.tribute_statuses.items() 
                    if status == "alive"
                ]
                
                if len(alive_tributes) >= 2:
                    tribute1 = random.choice(alive_tributes)
                    potential_allies = [t for t in alive_tributes if t.tribute_id != tribute1.tribute_id]
                    
                    if potential_allies:
                        tribute2 = random.choice(potential_allies)
                        alliance_event = self._generate_alliance_event(tribute1, tribute2)
                        if alliance_event:
                            return alliance_event
        
        # === FALLBACK TO STANDARD EVENT GENERATION ===
        
        # Get available events for this type - Fix the naming conversion
        if event_type == "Combat Events":
            event_category = "combat_events"
        elif event_type == "Arena Events":
            event_category = "arena_events"
        elif event_type == "Idle Events":
            event_category = "idle_events"
        elif event_type == "Custom Events":
            event_category = "custom_events"
        else:
            # Fallback to original logic for other event types
            event_category = event_type.lower().replace(" ", "_") + "s"
            
        available_events = self.event_messages.get("events", {}).get(event_category, {})

        if not available_events:
            # Fallback to old system if no structured events available
            return self._generate_fallback_event(event_type)
        
        # Special logic for cornucopia phase - prioritize cornucopia events
        current_phase_type = phase_info.get("phase_info", {}).get("type", "")
        
        if current_phase_type == "cornucopia":
            # During cornucopia phase, strongly prefer cornucopia-related events
            cornucopia_events = {k: v for k, v in available_events.items() 
                               if "cornucopia" in v.get("id", "").lower() or 
                                  "cornucopia" in v.get("name", "").lower() or
                                  "cornucopia" in v.get("description", "").lower()}
            
            # 80% chance to use cornucopia event if available, 20% chance for other combat/arena events
            if cornucopia_events and random.random() < 0.8:
                available_events = cornucopia_events

        # Anti-repetition: exclude events that happened recently
        recent_event_names = set()
        for recent_event in self.game_state.recent_events[-3:]:  # Check last 3 events
            if isinstance(recent_event, dict) and 'name' in recent_event:
                recent_event_names.add(recent_event['name'])
        
        # Filter out recently used events if possible
        filtered_events = {k: v for k, v in available_events.items() 
                          if v.get('name', '') not in recent_event_names}
        
        # Use filtered events if available, otherwise use all events (to prevent infinite loops)
        if filtered_events:
            available_events = filtered_events

        # Select random event from available events
        event_key = random.choice(list(available_events.keys()))
        event_data = available_events[event_key].copy()

        # Generate participants based on event requirements
        participants = self._generate_participants_for_event(event_data, event_type)

        # Apply stat effects to participants
        consequences = self._generate_consequences_for_event(event_data, participants)

        # Personalize the narrative with tribute names and districts
        personalized_narrative = self._personalize_narrative(event_data["narrative"], participants)
        personalized_description = self._personalize_narrative(event_data["description"], participants)

        return {
            "description": personalized_description,
            "narrative": personalized_narrative,
            "intensity": event_data["intensity"],
            "participants": participants,
            "consequences": consequences
        }

    def _generate_participants_for_event(self, event_data: Dict[str, Any], event_type: str) -> List[str]:
        """Generate participants list based on event requirements"""
        participant_rule = event_data.get("participants", "none")

        if participant_rule == "none":
            return []
        elif participant_rule == "all":
            return list(self.game_state.tribute_statuses.keys())
        elif participant_rule == "random_1":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            return random.sample(alive_tributes, min(1, len(alive_tributes)))
        elif participant_rule == "random_2":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            return random.sample(alive_tributes, min(2, len(alive_tributes)))
        elif participant_rule == "random_3":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            return random.sample(alive_tributes, min(3, len(alive_tributes)))
        elif participant_rule == "district_pair":
            # Try to find two tributes from the same district who are both alive
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            
            # Group tributes by district
            district_groups = {}
            for tid in alive_tributes:
                tribute = self.game_state.tributes.get(tid)
                if tribute and hasattr(tribute, 'district'):
                    district = tribute.district
                    if district not in district_groups:
                        district_groups[district] = []
                    district_groups[district].append(tid)
            
            # Find districts with 2+ alive tributes
            valid_districts = [tributes for tributes in district_groups.values() if len(tributes) >= 2]
            
            if valid_districts:
                # Pick a random district with multiple tributes
                chosen_district = random.choice(valid_districts)
                return random.sample(chosen_district, 2)
            else:
                # Fallback to random pair if no district pairs available
                return random.sample(alive_tributes, min(2, len(alive_tributes)))
        elif participant_rule == "random_1_2":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(1, min(2, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "random_1_3":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(1, min(3, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "random_1_4":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(1, min(4, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "random_2_4":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(2, min(4, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "random_3_5":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(3, min(5, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "random_2_5":
            alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
            count = random.randint(2, min(5, len(alive_tributes)))
            return random.sample(alive_tributes, count)
        elif participant_rule == "encounter_participants":
            # For PvP events, participants are already determined
            return event_data.get("current_participants", [])
        else:
            return []

    def _generate_consequences_for_event(self, event_data: Dict[str, Any], participants: List[str]) -> List[Dict[str, Any]]:
        """Generate consequences with stat effects for the event"""
        consequences = []

        # Add stat effects
        stat_effects = event_data.get("stat_effects", {})
        for stat, effect_data in stat_effects.items():
            if participants:
                # Apply to all participants or random subset
                target_participants = participants
                if effect_data.get("target") == "random":
                    count = effect_data.get("count", 1)
                    target_participants = random.sample(participants, min(count, len(participants)))

                for participant_id in target_participants:
                    # Calculate random effect within min/max range
                    min_effect = effect_data["min"]
                    max_effect = effect_data["max"]
                    
                    # Ensure min is actually smaller than max for randint
                    actual_min = min(min_effect, max_effect)
                    actual_max = max(min_effect, max_effect)
                    effect_value = random.randint(actual_min, actual_max)

                    # Apply dynamic difficulty scaling based on remaining tributes
                    alive_tributes = sum(1 for status in self.game_state.tribute_statuses.values() if status == "alive")
                    total_tributes = len(self.game_state.tributes)
                    survival_rate = alive_tributes / max(total_tributes, 1)
                    
                    # Events become more intense as fewer tributes remain
                    intensity_multiplier = 1.0 + (1.0 - survival_rate) * 0.5  # Up to 50% more intense late game
                    effect_value = int(effect_value * intensity_multiplier)

                    consequences.append({
                        "type": "stat_effect",
                        "stat": stat,
                        "value": effect_value,
                        "target": participant_id,
                        "description": effect_data.get("description", f"{stat} effect")
                    })

        # Add status effects
        status_effects = event_data.get("status_effects", {})
        for status_name, status_data in status_effects.items():
            if participants:
                # Apply to all participants or random subset
                target_participants = participants
                if status_data.get("target") == "random":
                    count = status_data.get("count", 1)
                    target_participants = random.sample(participants, min(count, len(participants)))

                for participant_id in target_participants:
                    consequences.append({
                        "type": "status_effect",
                        "status_name": status_name,
                        "duration_phases": status_data.get("duration_phases", 1),
                        "stat_modifiers": status_data.get("stat_modifiers", {}),
                        "target": participant_id,
                        "description": status_data.get("description", f"Status effect: {status_name}")
                    })

        # Add winner effects (for events with a single winner)
        winner_effects = event_data.get("winner_effects", {})
        if winner_effects and participants:
            winner_id = random.choice(participants)

            # Add inventory items
            inventory_items = winner_effects.get("inventory", [])
            for item in inventory_items:
                consequences.append({
                    "type": "inventory_add",
                    "item": item,
                    "target": winner_id,
                    "description": winner_effects.get("description", "Winner receives item")
                })

            # Add resources
            resources = winner_effects.get("resources", {})
            for resource, amount_data in resources.items():
                min_amount = amount_data["min"]
                max_amount = amount_data["max"]
                amount = random.randint(min_amount, max_amount)
                consequences.append({
                    "type": "resource_add",
                    "resource": resource,
                    "amount": amount,
                    "target": winner_id,
                    "description": winner_effects.get("description", "Winner receives resources")
                })

        # Add relationship effects
        relationship_effects = event_data.get("relationship_effects", {})
        if relationship_effects and len(participants) > 1:
            relationship_change = relationship_effects.get("relationship_change", {})
            if relationship_change:
                min_change = relationship_change["min"]
                max_change = relationship_change["max"]
                change_value = random.randint(min_change, max_change)

                # Apply to all pairs
                for i, p1 in enumerate(participants):
                    for j, p2 in enumerate(participants):
                        if i != j:
                            consequences.append({
                                "type": "relationship_change",
                                "target1": p1,
                                "target2": p2,
                                "value": change_value,
                                "description": "Event affects tribute relationships"
                            })

            # Handle alliances
            if relationship_effects.get("alliance", False):
                alliance_participants = random.sample(participants, min(2, len(participants)))
                for tribute_id in alliance_participants:
                    consequences.append({
                        "type": "alliance_form",
                        "target": tribute_id,
                        "allies": [aid for aid in alliance_participants if aid != tribute_id],
                        "description": "New alliance formed"
                    })

        return consequences

    def _process_ongoing_environmental_effects(self):
        """Process multi-phase environmental effects like weather, hazards"""
        effects_to_remove = []
        
        for i, effect in enumerate(self.active_environmental_effects):
            # Decrement duration
            effect['remaining_phases'] -= 1
            
            # Apply effect to tributes
            if effect['type'] == 'weather':
                self._apply_weather_effect(effect)
            elif effect['type'] == 'hazard':
                self._apply_hazard_effect(effect)
            elif effect['type'] == 'arena_mutation':
                self._apply_arena_mutation(effect)
                
            # Remove if duration expired
            if effect['remaining_phases'] <= 0:
                effects_to_remove.append(i)
                # Send end message
                end_message = {
                    "message_type": "environmental_effect_ended",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "effect_name": effect['name'],
                        "effect_type": effect['type'],
                        "description": f"The {effect['name']} has ended"
                    }
                }
                self.message_queue.append(end_message)
                self.event_log.append(end_message)
        
        # Remove expired effects (reverse order to maintain indices)
        for i in reversed(effects_to_remove):
            self.active_environmental_effects.pop(i)
    
    def _apply_weather_effect(self, effect: Dict[str, Any]):
        """Apply weather effect to all tributes"""
        for tribute_id, tribute in self.game_state.tributes.items():
            if tribute.status != "alive":
                continue
                
            # Apply stat changes from weather
            stat_effects = effect.get('stat_effects', {})
            
            # Check for protection (shelter, special items)
            has_protection = tribute.has_shelter or any(
                item in tribute.inventory for item in ['Rain Gear', 'Shelter', 'Tent']
            )
            
            # Reduced effects if protected
            multiplier = 0.3 if has_protection else 1.0
            
            for stat, value in stat_effects.items():
                adjusted_value = int(value * multiplier)
                if stat == 'health':
                    tribute.update_health(adjusted_value, f"{effect['name']} damage")
                elif stat == 'fatigue':
                    tribute.update_fatigue(adjusted_value)
                elif stat == 'sanity':
                    tribute.update_sanity(adjusted_value, effect['name'])
                elif stat == 'thirst':
                    tribute.update_thirst(adjusted_value)
    
    def _apply_hazard_effect(self, effect: Dict[str, Any]):
        """Apply arena hazard to nearby tributes"""
        # Hazards affect tributes in specific zones
        affected_tributes = self._get_tributes_in_zone(effect.get('zone', 'all'))
        
        for tribute_id in affected_tributes:
            tribute = self.game_state.tributes.get(tribute_id)
            if not tribute or tribute.status != "alive":
                continue
                
            stat_effects = effect.get('stat_effects', {})
            for stat, value in stat_effects.items():
                if stat == 'health':
                    tribute.update_health(value, f"{effect['name']} hazard")
                elif stat == 'fatigue':
                    tribute.update_fatigue(value)
    
    def _apply_arena_mutation(self, effect: Dict[str, Any]):
        """Apply arena-wide mutation effects"""
        # Arena mutations affect all tributes
        for tribute_id, tribute in self.game_state.tributes.items():
            if tribute.status != "alive":
                continue
            
            # Apply mutation effects
            stat_effects = effect.get('stat_effects', {})
            for stat, value in stat_effects.items():
                if stat == 'health':
                    tribute.update_health(value, f"{effect['name']}")
                elif stat == 'sanity':
                    tribute.update_sanity(value, effect['name'])
    
    def _get_tributes_in_zone(self, zone: str) -> List[str]:
        """Get tribute IDs in a specific zone"""
        if zone == 'all':
            return [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
        
        # For now, randomly select ~50% of tributes to be in hazard zone
        alive_tributes = [tid for tid, status in self.game_state.tribute_statuses.items() if status == "alive"]
        affected_count = max(1, len(alive_tributes) // 2)
        return random.sample(alive_tributes, min(affected_count, len(alive_tributes)))
    
    def _add_environmental_effect(self, effect_type: str, name: str, duration_phases: int, 
                                  stat_effects: Dict[str, int], zone: str = 'all'):
        """Add a new environmental effect to track"""
        effect = {
            'type': effect_type,
            'name': name,
            'remaining_phases': duration_phases,
            'stat_effects': stat_effects,
            'zone': zone,
            'started_at': datetime.now().isoformat()
        }
        self.active_environmental_effects.append(effect)
        
        # Send start message
        start_message = {
            "message_type": "environmental_effect_started",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "effect_name": name,
                "effect_type": effect_type,
                "duration_phases": duration_phases,
                "description": f"{name} has begun and will last for {duration_phases} phases"
            }
        }
        self.message_queue.append(start_message)
        self.event_log.append(start_message)

    def _distribute_cornucopia_supplies(self):
        """
        Distribute cornucopia supplies after the bloodbath phase completes.
        This is called when transitioning away from cornucopia phase to ensure
        supplies are only given AFTER events are displayed.
        """
        supply_data = self.cornucopia_controller.get_pending_supply_distribution()
        if not supply_data:
            print("[CORNUCOPIA] No pending supply distribution")
            return
        
        tributes = supply_data.get("tributes", [])
        supplies_claimed = supply_data.get("supplies_claimed", 0)
        
        # Determine which tributes survived and participated
        survived_participants = []
        for tribute_data in tributes:
            tribute_id = tribute_data["id"]
            if tribute_id in self.game_state.tributes and self.game_state.tributes[tribute_id].status == "alive":
                survived_participants.append(tribute_id)
        
        # Distribute supplies to random survivors
        if supplies_claimed > 0 and survived_participants:
            supply_recipients = random.sample(
                survived_participants, 
                min(supplies_claimed, len(survived_participants))
            )
            
            # Initialize cornucopia inventory if available
            cornucopia_inventory = None
            if hasattr(self.cornucopia_controller, 'inventory') and self.cornucopia_controller.inventory:
                cornucopia_inventory = self.cornucopia_controller.inventory
                # Generate inventory based on tribute count
                cornucopia_inventory.generate_inventory(len(tributes))
                print(f"[CORNUCOPIA] Generated inventory for {len(tributes)} tributes")
            
            for tribute_id in supply_recipients:
                tribute_obj = self.game_state.tributes[tribute_id]
                
                if cornucopia_inventory:
                    # Use the advanced inventory system
                    supply_type = random.choice(["weapon", "food", "water", "medical", "survival"])
                    
                    if supply_type == "weapon":
                        available_weapons = cornucopia_inventory.get_available_weapons()
                        if available_weapons:
                            weapon = random.choice(available_weapons)
                            if cornucopia_inventory.remove_weapon(weapon):
                                tribute_obj.weapons.append(weapon)
                                print(f"[CORNUCOPIA] {tribute_obj.name} claimed weapon: {weapon}")
                            
                    elif supply_type in ["food", "water", "medical", "survival"]:
                        item_name, effect_data = cornucopia_inventory.get_supply_item(supply_type)
                        if item_name:
                            tribute_obj.inventory.append(item_name)
                            
                            # Apply supply effects
                            if supply_type == "food":
                                food_amount = random.randint(2, 5)
                                tribute_obj.food_supplies += food_amount
                                print(f"[CORNUCOPIA] {tribute_obj.name} claimed food: {item_name} (+{food_amount} supplies)")
                                
                            elif supply_type == "water":
                                water_amount = random.randint(3, 7)
                                tribute_obj.water_supplies += water_amount
                                print(f"[CORNUCOPIA] {tribute_obj.name} claimed water: {item_name} (+{water_amount} supplies)")
                                
                            elif supply_type == "medical":
                                health_boost = random.randint(5, 15)
                                tribute_obj.health = min(100, tribute_obj.health + health_boost)
                                print(f"[CORNUCOPIA] {tribute_obj.name} claimed medical: {item_name} (+{health_boost} health)")
                                
                            elif supply_type == "survival":
                                print(f"[CORNUCOPIA] {tribute_obj.name} claimed survival item: {item_name}")
                else:
                    # Fallback to simple supply distribution
                    supply_type = random.choice(["weapon", "food", "water", "medicine", "tool"])
                    
                    if supply_type == "weapon":
                        weapons = ["Knife", "Sword", "Spear", "Bow", "Axe", "Mace"]
                        weapon = random.choice(weapons)
                        tribute_obj.weapons.append(weapon)
                        print(f"[CORNUCOPIA] {tribute_obj.name} found weapon: {weapon}")
                        
                    elif supply_type == "food":
                        food_amount = random.randint(2, 5)
                        tribute_obj.food_supplies += food_amount
                        tribute_obj.inventory.append(f"Food Rations ({food_amount})")
                        print(f"[CORNUCOPIA] {tribute_obj.name} found food: {food_amount} rations")
                        
                    elif supply_type == "water":
                        water_amount = random.randint(3, 7)
                        tribute_obj.water_supplies += water_amount
                        tribute_obj.inventory.append(f"Water ({water_amount})")
                        print(f"[CORNUCOPIA] {tribute_obj.name} found water: {water_amount} units")
                        
                    elif supply_type == "medicine":
                        medicine = random.choice(["First Aid Kit", "Bandages", "Pain Relief", "Antiseptic"])
                        tribute_obj.inventory.append(medicine)
                        print(f"[CORNUCOPIA] {tribute_obj.name} found medicine: {medicine}")
                        
                    elif supply_type == "tool":
                        tools = ["Rope", "Backpack", "Sleeping Bag", "Fire Starter", "Compass"]
                        tool = random.choice(tools)
                        tribute_obj.inventory.append(tool)
                        print(f"[CORNUCOPIA] {tribute_obj.name} found tool: {tool}")
                
                # Update game state
                self.game_state.update_tribute_status(tribute_id, tribute_obj.status)
        
        print(f"[CORNUCOPIA] Supply distribution complete: {len(supply_recipients)} tributes received supplies")

    def _apply_phase_end_stat_decay(self):
        """Apply stat decay and environmental effects when a phase ends"""
        # First process ongoing environmental effects
        self._process_ongoing_environmental_effects()
        
        decay_rates = self.config.get("stat_decay_rates", {
            "hunger": 5,
            "thirst": 7,
            "fatigue": 4,
            "sanity_floor": 50  # Environmental stress causes sanity loss if below this
        })

        hunger_decay = decay_rates.get("hunger", 5)
        thirst_decay = decay_rates.get("thirst", 7)
        fatigue_decay = decay_rates.get("fatigue", 4)
        sanity_floor = decay_rates.get("sanity_floor", 50)

        # Track stat updates for logging
        stat_updates = []

        for tribute_id, tribute in self.game_state.tributes.items():
            if tribute.status != "alive":
                continue  # Dead tributes don't need stat updates

            old_hunger = tribute.hunger
            old_thirst = tribute.thirst
            old_fatigue = tribute.fatigue
            old_sanity = tribute.sanity

            # Increase hunger (simulates time passing)
            tribute.update_hunger(hunger_decay)

            # Increase thirst (simulates time and exposure)
            tribute.update_thirst(thirst_decay)

            # Increase fatigue from lack of rest
            tribute.update_fatigue(fatigue_decay)

            # Environmental stress - sanity slowly decreases (unless they have shelter and fire)
            if tribute.has_shelter and tribute.has_fire:
                # Safe and comfortable - minimal sanity loss
                tribute.update_sanity(-2, "Anxiety of being hunted")
            elif tribute.has_shelter:
                # Sheltered but no fire/comfort - moderate sanity loss
                tribute.update_sanity(-5, "Cold, fear, and isolation")
            else:
                # Exposed to elements - significant sanity loss
                tribute.update_sanity(-8, "Exposed to harsh environment and fear")

            # Check if tribute died from stat extremes
            if tribute.health <= 0:
                tribute.status = "dead"
                self.game_state.tribute_statuses[tribute_id] = "dead"
                stat_updates.append({
                    "tribute_id": tribute_id,
                    "cause": "Environmental effects",
                    "status_change": "alive -> dead"
                })
                continue

            # Log significant stat changes (for debugging/animation)
            if tribute.hunger != old_hunger or tribute.thirst != old_thirst or tribute.fatigue != old_fatigue or tribute.sanity != old_sanity:
                stat_updates.append({
                    "tribute_id": tribute_id,
                    "hunger": (old_hunger, tribute.hunger),
                    "thirst": (old_thirst, tribute.thirst),
                    "fatigue": (old_fatigue, tribute.fatigue),
                    "sanity": (old_sanity, tribute.sanity)
                })

        # If any tributes died or had significant updates, log it
        if stat_updates:
            status_message = {
                "message_type": "phase_stat_updates",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "phase": self.game_state.current_day,
                    "stat_updates": stat_updates,
                    "deaths": [u for u in stat_updates if "status_change" in u]
                }
            }
            self.message_queue.append(status_message)
            self.event_log.append(status_message)
            print(f"[Phase End] Updated stats for {len(stat_updates)} tributes")

    def _weighted_choice(self, event_types: List[str]) -> str:
        """Select an event type using weighted probabilities from config"""
        weights = []
        event_probabilities = self.config.get("event_probabilities", {})
        
        for event_type in event_types:
            # Use configured weight, default to 1.0 if not specified
            weight = event_probabilities.get(event_type, 1.0)
            weights.append(weight)
        
        # If all weights are 0, fall back to uniform selection
        if sum(weights) == 0:
            return random.choice(event_types)
        
        # Weighted random selection
        total_weight = sum(weights)
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for i, weight in enumerate(weights):
            cumulative_weight += weight
            if r <= cumulative_weight:
                return event_types[i]
        
        # Fallback (should not reach here)
        return random.choice(event_types)

    def _personalize_narrative(self, narrative: str, participants: List[str]) -> str:
        """Replace placeholders in narrative with actual tribute names and districts"""
        personalized = narrative

        # Get tribute info for each participant
        tribute_info = {}
        for i, participant_id in enumerate(participants):
            tribute_obj = self.game_state.tributes.get(participant_id)
            if tribute_obj:
                name = tribute_obj.name
                district = tribute_obj.district
                tribute_info[f'tribute{i+1}'] = f"{name} from District {district}"
                tribute_info[f'name{i+1}'] = name
                tribute_info[f'district{i+1}'] = f"District {district}"

        # Replace placeholders
        for placeholder, value in tribute_info.items():
            personalized = personalized.replace(f'{{{placeholder}}}', value)

        # If no specific placeholders, add some variety for generic terms
        # Only use generic "tributes" for 4+ participants, otherwise name them specifically
        if 'tributes' in personalized.lower() and len(participants) <= 5:
            if len(participants) == 1:
                tribute_names = tribute_info.get('name1', 'a tribute')
                personalized = personalized.replace('tributes', tribute_names).replace('Tributes', tribute_names.capitalize())
            elif len(participants) == 2:
                name1 = tribute_info.get('name1', 'one tribute')
                name2 = tribute_info.get('name2', 'another tribute')
                personalized = personalized.replace('tributes', f'{name1} and {name2}')
            elif len(participants) == 3:
                name1 = tribute_info.get('name1', 'one tribute')
                name2 = tribute_info.get('name2', 'another tribute')
                name3 = tribute_info.get('name3', 'a third tribute')
                personalized = personalized.replace('tributes', f'{name1}, {name2}, and {name3}')
            elif len(participants) == 4:
                # For 4 tributes, name them all specifically to avoid vague "multiple tributes"
                name1 = tribute_info.get('name1', 'one tribute')
                name2 = tribute_info.get('name2', 'another tribute')
                name3 = tribute_info.get('name3', 'a third tribute')
                name4 = tribute_info.get('name4', 'a fourth tribute')
                personalized = personalized.replace('tributes', f'{name1}, {name2}, {name3}, and {name4}')
            elif len(participants) == 5:
                # For 5 tributes, still name them all
                name1 = tribute_info.get('name1', 'one tribute')
                name2 = tribute_info.get('name2', 'another tribute')
                name3 = tribute_info.get('name3', 'a third tribute')
                name4 = tribute_info.get('name4', 'a fourth tribute')
                name5 = tribute_info.get('name5', 'a fifth tribute')
                personalized = personalized.replace('tributes', f'{name1}, {name2}, {name3}, {name4}, and {name5}')

        # Occasionally add contextual information (20% chance for events with participants)
        if participants and random.random() < 0.20:
            alive_count = sum(1 for status in self.game_state.tribute_statuses.values() if status == "alive")
            current_phase = self.phase_controller.get_current_phase_info()
            day = current_phase.get('day', 1) if current_phase else 1

            context_additions = [
                f" With only {alive_count} tributes remaining, every confrontation carries immense weight.",
                f" On day {day} of the Games, survival becomes increasingly desperate.",
                f" The arena has claimed many lives, leaving just {alive_count} competitors standing.",
                f" As the Games progress into day {day}, alliances shift and betrayals multiply."
            ]

            if context_additions:
                personalized += random.choice(context_additions)

        return personalized

    def _generate_fallback_event(self, event_type: str) -> Dict[str, Any]:
        """Fallback event generation for when structured events aren't available"""
        base_events = {
            "Arena Events": [
                "A mysterious fog rolls into the arena",
                "The ground begins to shake violently",
                "Strange sounds echo through the forest",
                "The temperature suddenly drops",
                "Blood rain begins to fall from the sky"
            ],
            "Combat Events": [
                "Two tributes engage in fierce combat",
                "A tribute ambushes another from hiding",
                "A weapon is discovered and claimed",
                "A tribute falls from a great height",
                "Poisonous berries are found and consumed"
            ],
            "Idle Events": [
                "Tributes rest and recover their strength",
                "A tribute finds a source of clean water",
                "The sun beats down mercilessly",
                "Night falls, bringing cooler temperatures",
                "A tribute successfully hunts for food"
            ],
            "Custom Events": [
                "A sponsor gift arrives from the Capitol",
                "The Gamemakers announce a rule change",
                "A tribute receives medical supplies",
                "The Cornucopia restocks with supplies",
                "A tribute finds an alliance partner"
            ]
        }

        if event_type in base_events:
            description = random.choice(base_events[event_type])
        else:
            description = f"An unknown {event_type} event occurred"

        return {
            "description": description,
            "narrative": f"The arena comes alive as {description.lower()}. The tributes must adapt to this new challenge.",
            "intensity": "medium",
            "participants": [],
            "consequences": []
        }

        if event_type in base_events:
            description = random.choice(base_events[event_type])
        else:
            description = f"An unknown {event_type} event occurred"

        return {
            "description": description,
            "intensity": phase_info['phase_info']['intensity'],
            "participants": [],  # Would be populated with actual tribute IDs
            "consequences": [],  # Would be populated with event outcomes
            "narrative": self._generate_narrative(description, event_type)
        }

    def _generate_flavor_event(self) -> Optional[Dict[str, Any]]:
        """Generate an atmospheric flavor event with minimal consequences"""
        flavor_events = self.event_messages.get("events", {}).get("flavor_events", {})
        if not flavor_events:
            return None

        event_key = random.choice(list(flavor_events.keys()))
        event_data = flavor_events[event_key].copy()

        # Generate minimal participants (usually none for flavor events)
        participants = self._generate_participants_for_event(event_data, "flavor")

        # Apply minimal stat effects
        consequences = self._generate_consequences_for_event(event_data, participants)

        # Personalize the narrative (though flavor events usually have no participants)
        personalized_narrative = self._personalize_narrative(event_data["narrative"], participants)
        personalized_description = self._personalize_narrative(event_data["description"], participants)

        return {
            "description": personalized_description,
            "narrative": personalized_narrative,
            "intensity": event_data["intensity"],
            "participants": participants,
            "consequences": consequences
        }

    def _generate_random_encounter_event(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an event for a random multi-tribute encounter using structured message system"""
        participants = encounter_data["participants"]
        num_participants = len(participants)

        # Get participant names for narrative
        participant_names = []
        for pid in participants:
            tribute = self.game_state.tributes.get(pid)
            if tribute:
                name = tribute.name
            else:
                name = f"Tribute {pid}"
            participant_names.append(name)

        # Get the multi_tribute_encounter event from structured messages
        pvp_events = self.event_messages.get("events", {}).get("pvp_events", {})
        event_template = pvp_events.get("multi_tribute_encounter", {})

        # Generate encounter description based on number of participants
        if num_participants == 2:
            description = f"{participant_names[0]} and {participant_names[1]} encounter each other!"
        elif num_participants == 3:
            description = f"{participant_names[0]}, {participant_names[1]}, and {participant_names[2]} cross paths!"
        else:
            description = f"A group of {num_participants} tributes encounter each other!"

        # Use narrative from template or generate custom one
        narrative = event_template.get("narrative", self._generate_multi_tribute_narrative(participants, participant_names))

        # Generate structured consequences using the event template
        consequences = self._generate_consequences_for_event(event_template, participants)

        # Get current phase info
        current_phase = self.phase_controller.get_current_phase_info()

        # Record event in game state with structured consequences
        self.game_state.record_event({
            "event_category": "PvP Events",
            "description": description,
            "participants": participants,
            "consequences": consequences,
            "intensity": event_template.get("intensity", "high"),
            "narrative": narrative
        })

        # Create event data with structured consequences
        event_data = {
            "description": description,
            "intensity": event_template.get("intensity", "high"),
            "participants": participants,
            "consequences": consequences,
            "narrative": narrative,
            "encounter_type": "random_multi_tribute"
        }

        # Create JSON message
        event_message = {
            "message_type": "game_event",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "event_type": "PvP Events",
                "phase_info": current_phase,
                "event_data": event_data,
                "game_state": self.game_state.get_game_status()
            }
        }

        self.message_queue.append(event_message)
        self.event_log.append(event_message)

        return event_message

    def _generate_multi_tribute_narrative(self, participants: List[str], participant_names: List[str]) -> str:
        """Generate narrative for multi-tribute encounters"""
        num_participants = len(participants)

        if num_participants == 2:
            tribute1 = self.game_state.tributes.get(participants[0])
            tribute2 = self.game_state.tributes.get(participants[1])
            district1 = tribute1.district if tribute1 else "Unknown"
            district2 = tribute2.district if tribute2 else "Unknown"
            return f"The arena grows tense as {participant_names[0]} from District {district1} and {participant_names[1]} from District {district2} find themselves face to face. The air crackles with tension as they size each other up."

        elif num_participants == 3:
            return f"A dangerous triangle forms as {participant_names[0]}, {participant_names[1]}, and {participant_names[2]} converge in the same area. Alliances could form, or chaos could erupt - the next few moments will determine their fates."

        elif num_participants == 4:
            return f"Four tributes - {', '.join(participant_names[:3])}, and {participant_names[3]} - find themselves in close proximity. The group dynamic shifts unpredictably as survival instincts take over."

        else:  # 5 or more
            return f"A large group of {num_participants} tributes including {', '.join(participant_names[:3])}, and others converge. The crowded encounter creates opportunities and dangers for everyone involved."

    def _generate_narrative(self, description: str, event_type: str) -> str:
        """Generate narrative text for the event"""
        # Placeholder narrative generation
        intensity_descriptors = {
            "low": ["quietly", "gently", "subtly"],
            "medium": ["noticeably", "significantly", "markedly"],
            "high": ["dramatically", "violently", "intensely"]
        }

        # This would be enhanced with actual AI/ML generation in the future
        return f"The arena comes alive as {description.lower()}. The tributes must adapt to this new challenge."
    
    def _validate_event_context(self, event_type: str) -> bool:
        """
        Validate that tributes are capable of participating in this event type.
        Prevents inappropriate events (e.g., combat for severely disabled tributes).
        """
        alive_tributes = [
            self.game_state.tributes[tid] 
            for tid, status in self.game_state.tribute_statuses.items() 
            if status == "alive"
        ]
        
        if not alive_tributes:
            return False
        
        # Combat Events - need at least one tribute capable of combat
        if event_type == "Combat Events":
            combat_capable = []
            for tribute in alive_tributes:
                if hasattr(tribute, 'limb_damage'):
                    # Can't fight if can't hold weapon or too many disabled limbs
                    if not tribute.limb_damage.can_hold_weapon():
                        continue
                    if tribute.limb_damage.count_disabled_limbs() >= 3:
                        continue
                
                # Too injured to fight
                if tribute.health < 20:
                    continue
                
                combat_capable.append(tribute)
            
            # Need at least 2 combat-capable tributes
            return len(combat_capable) >= 2
        
        # Arena Events - generally always possible
        if event_type == "Arena Events":
            return True
        
        # Idle Events - need tributes with enough health to act
        if event_type == "Idle Events":
            active_tributes = [t for t in alive_tributes if t.health > 10]
            return len(active_tributes) > 0
        
        # Custom Events - generally always possible
        return True
    
    # ========== SPECIALIZED EVENT GENERATORS (Context-Aware) ==========
    
    def _generate_combat_event(self, attacker, defender) -> Optional[Dict[str, Any]]:
        """
        Generate a context-aware combat event using weapons system and limb damage.
        Considers relationships, equipped weapons, and tribute conditions.
        """
        # Check if attacker is capable of combat
        if hasattr(attacker, 'limb_damage'):
            if not attacker.limb_damage.can_hold_weapon():
                # Attacker can't hold weapon - combat unlikely
                return None
            if attacker.limb_damage.count_disabled_limbs() >= 2:
                # Severely disabled - combat extremely unlikely
                if random.random() > 0.1:
                    return None
        
        # Get relationship context
        relationship_context = ""
        is_enemy = False
        trust_level = 50
        
        if self.relationship_manager:
            rel = self.relationship_manager.get_relationship(
                attacker.tribute_id, defender.tribute_id
            )
            if rel:
                is_enemy = rel.is_enemy
                trust_level = rel.trust
                if is_enemy and rel.enemy_priority >= 70:
                    relationship_context = f" (high-priority enemy, threat: {rel.enemy_priority})"
                elif rel.is_alliance:
                    # This could be a betrayal
                    relationship_context = " (betraying ally!)"
        
        # Get weapons
        attacker_weapon_id = attacker.equipped_weapon
        if not attacker_weapon_id and attacker.weapons:
            attacker_weapon_id = self.weapons_system.get_best_weapon(
                attacker.weapons, attacker.skills.get("strength", 5)
            )
        
        defender_weapon_id = defender.equipped_weapon
        if not defender_weapon_id and defender.weapons:
            defender_weapon_id = self.weapons_system.get_best_weapon(
                defender.weapons, defender.skills.get("strength", 5)
            )
        
        # Calculate combat outcome
        combat_result = self.weapons_system.calculate_combat(
            attacker_weapon_id or "bare_hands",
            defender_weapon_id or "bare_hands",
            attacker.skills,
            defender.skills
        )
        
        attacker_weapon = self.weapons_system.get_weapon_by_id(attacker_weapon_id) if attacker_weapon_id else None
        defender_weapon = self.weapons_system.get_weapon_by_id(defender_weapon_id) if defender_weapon_id else None
        
        attacker_weapon_name = attacker_weapon["name"] if attacker_weapon else "bare hands"
        defender_weapon_name = defender_weapon["name"] if defender_weapon else "bare hands"
        
        # Determine body part hit
        body_parts = [BodyPart.HEAD, BodyPart.TORSO, BodyPart.LEFT_ARM, 
                     BodyPart.RIGHT_ARM, BodyPart.LEFT_LEG, BodyPart.RIGHT_LEG]
        body_part_hit = random.choice(body_parts)
        
        # Apply damage and create wound
        damage_dealt = combat_result["damage_dealt"]
        defender.health -= damage_dealt
        
        wound_created = None
        if hasattr(defender, 'limb_damage') and damage_dealt > 0:
            # Determine wound type and severity
            wound_type, severity = self.limb_damage_system.determine_wound_type(
                attacker_weapon_name, damage_dealt, body_part_hit
            )
            
            # Create wound object
            from limb_damage_system import LimbWound
            limb_wound = self.limb_damage_system.create_wound(
                body_part_hit, wound_type, severity, attacker_weapon_name
            )
            
            # Add wound to defender
            defender.limb_damage.add_wound(limb_wound)
            
            # Store wound data for narrative
            wound_created = {
                "severity": wound_type,
                "severity_level": severity,
                "bleeding": limb_wound.bleeding_rate,
                "dismembered": wound_type == "severed",
                "wound_type": wound_type
            }
        
        # Build narrative
        outcome = combat_result["outcome"]
        body_part_name = body_part_hit.value.replace("_", " ")
        
        if outcome == "attacker_wins":
            if wound_created and wound_created.get("dismembered"):
                narrative = f"{attacker.name} attacks {defender.name}{relationship_context} with {attacker_weapon_name}, " \
                           f"dealing a devastating blow that severs their {body_part_name}! " \
                           f"{defender.name} suffers {damage_dealt} damage and loses their {body_part_name}."
            else:
                narrative = f"{attacker.name} attacks {defender.name}{relationship_context} with {attacker_weapon_name}, " \
                           f"striking their {body_part_name} for {damage_dealt} damage. " \
                           f"{defender.name} tries to defend with {defender_weapon_name} but fails."
        elif outcome == "defender_wins":
            counter_damage = combat_result.get("counter_damage", 0)
            attacker.health -= counter_damage
            narrative = f"{attacker.name} attacks {defender.name} with {attacker_weapon_name}, " \
                       f"but {defender.name} counters brilliantly with {defender_weapon_name}, " \
                       f"dealing {counter_damage} damage back to {attacker.name}!"
        else:  # draw
            narrative = f"{attacker.name} and {defender.name} clash violently with " \
                       f"{attacker_weapon_name} and {defender_weapon_name}, but neither gains the upper hand."
        
        # Check for deaths
        consequences = []
        if defender.health <= 0:
            defender.status = "dead"
            self.game_state.update_tribute_status(defender.tribute_id, "dead")
            consequences.append({
                "tribute_id": defender.tribute_id,
                "type": "death",
                "cause": f"Killed by {attacker.name} with {attacker_weapon_name}"
            })
            narrative += f" {defender.name} has been eliminated from the Games."
            
            # Create enemy relationship if this was an ally kill
            if self.relationship_manager:
                self.relationship_manager.create_enemy_from_event(
                    defender.tribute_id, attacker.tribute_id, "killed_ally"
                )
        elif attacker.health <= 0:
            attacker.status = "dead"
            self.game_state.update_tribute_status(attacker.tribute_id, "dead")
            consequences.append({
                "tribute_id": attacker.tribute_id,
                "type": "death",
                "cause": f"Killed in combat with {defender.name}"
            })
            narrative += f" {attacker.name} has been eliminated from the Games."
        else:
            # Both survived - add injury consequences
            if wound_created:
                consequences.append({
                    "tribute_id": defender.tribute_id,
                    "type": "injury",
                    "body_part": body_part_name,
                    "severity": wound_created["severity"],
                    "dismembered": wound_created.get("dismembered", False)
                })
            
            # Combat creates enemies
            if self.relationship_manager and not is_enemy:
                self.relationship_manager.create_enemy_from_event(
                    defender.tribute_id, attacker.tribute_id, "combat_attack"
                )
        
        return {
            "description": f"Combat: {attacker.name} vs {defender.name}",
            "narrative": narrative,
            "intensity": "high",
            "participants": [attacker.tribute_id, defender.tribute_id],
            "consequences": consequences,
            "combat_details": {
                "attacker_weapon": attacker_weapon_name,
                "defender_weapon": defender_weapon_name,
                "damage": damage_dealt,
                "body_part_hit": body_part_name,
                "wound": wound_created,
                "outcome": outcome
            }
        }
    
    def _generate_medical_event(self, tribute) -> Optional[Dict[str, Any]]:
        """Generate medical treatment event for tribute with injuries"""
        if not hasattr(tribute, 'limb_damage'):
            return None
        
        untreated_wounds = tribute.limb_damage.get_untreated_wounds()
        if not untreated_wounds:
            return None
        
        # Select wound to treat (prioritize severe/critical)
        wound_priorities = []
        for wound in untreated_wounds:
            priority = {
                'minor': 1,
                'moderate': 2,
                'severe': 3,
                'critical': 4
            }.get(wound['severity'], 1)
            
            if wound.get('bleeding'):
                priority += 2
            if wound.get('infected'):
                priority += 1
            
            wound_priorities.append((wound, priority))
        
        wound_priorities.sort(key=lambda x: x[1], reverse=True)
        wound_to_treat = wound_priorities[0][0]
        
        # Check if has medical supplies
        has_supplies = len(tribute.medical_supplies) > 0
        
        # Treat the wound
        success = tribute.treat_wounds(
            body_part=wound_to_treat['body_part'],
            treatment_quality=0.8 if has_supplies else 0.4
        )
        
        if has_supplies:
            tribute.medical_supplies.pop(0)  # Use one supply
        
        body_part_name = wound_to_treat['body_part'].replace("_", " ")
        
        if success:
            narrative = f"{tribute.name} carefully treats their {wound_to_treat['severity']} {body_part_name} wound" \
                       f"{' with medical supplies' if has_supplies else ' as best they can without proper supplies'}. " \
                       f"The wound is cleaned and bandaged, reducing infection risk."
            
            if wound_to_treat.get('bleeding'):
                narrative += f" The bleeding has been stopped."
        else:
            narrative = f"{tribute.name} attempts to treat their {body_part_name} wound but struggles " \
                       f"{'without proper medical supplies' if not has_supplies else 'due to the wound severity'}. " \
                       f"The treatment is only partially effective."
        
        return {
            "description": f"Medical: {tribute.name} treats wounds",
            "narrative": narrative,
            "intensity": "low",
            "participants": [tribute.tribute_id],
            "consequences": [{
                "tribute_id": tribute.tribute_id,
                "type": "medical_treatment",
                "body_part": body_part_name,
                "success": success
            }]
        }
    
    def _generate_betrayal_event(self, betrayer, victim) -> Optional[Dict[str, Any]]:
        """Generate betrayal event with relationship consequences"""
        if not self.relationship_manager:
            return None
        
        rel = self.relationship_manager.get_relationship(betrayer.tribute_id, victim.tribute_id)
        if not rel or not rel.is_alliance:
            return None  # Can only betray allies
        
        # Calculate desperation
        desperation = 100 - betrayer.health
        if betrayer.hunger > 60:
            desperation += 20
        if betrayer.thirst > 60:
            desperation += 20
        desperation = min(100, desperation)
        
        betrayal_risk = rel.calculate_betrayal_risk(desperation)
        
        if betrayal_risk < 0.3:
            return None  # Not desperate enough
        
        # Execute betrayal - attack victim
        combat_event = self._generate_combat_event(betrayer, victim)
        
        if combat_event:
            # Modify narrative for betrayal context
            combat_event["narrative"] = f"{betrayer.name} betrays their ally {victim.name}! " + combat_event["narrative"]
            combat_event["description"] = f"Betrayal: {betrayer.name} betrays {victim.name}"
            
            # Spread gossip about betrayal
            self.relationship_manager.spread_reputation_gossip(
                betrayer.tribute_id, -30, f"betrayed {victim.name}"
            )
            
            # Create enemy
            self.relationship_manager.create_enemy_from_event(
                victim.tribute_id, betrayer.tribute_id, "betrayal"
            )
            
            # Break alliance
            self.relationship_manager.break_alliance(betrayer.tribute_id, victim.tribute_id)
        
        return combat_event
    
    def _generate_alliance_event(self, tribute1, tribute2) -> Optional[Dict[str, Any]]:
        """Generate alliance formation event with trust tracking"""
        if not self.relationship_manager:
            return None
        
        rel = self.relationship_manager.get_relationship(tribute1.tribute_id, tribute2.tribute_id)
        
        if rel and rel.is_alliance:
            return None  # Already allies
        
        if rel and rel.trust < 40:
            return None  # Not enough trust
        
        # Form alliance
        self.relationship_manager.form_alliance(tribute1.tribute_id, tribute2.tribute_id)
        
        # Spread positive gossip
        self.relationship_manager.spread_reputation_gossip(
            tribute1.tribute_id, 10, f"formed alliance with {tribute2.name}"
        )
        self.relationship_manager.spread_reputation_gossip(
            tribute2.tribute_id, 10, f"formed alliance with {tribute1.name}"
        )
        
        narrative = f"{tribute1.name} and {tribute2.name} form an alliance. " \
                   f"They agree to watch each other's backs and share resources. " \
                   f"Trust level: {rel.trust if rel else 50}/100"
        
        return {
            "description": f"Alliance: {tribute1.name} & {tribute2.name}",
            "narrative": narrative,
            "intensity": "low",
            "participants": [tribute1.tribute_id, tribute2.tribute_id],
            "consequences": [{
                "tribute_id": tribute1.tribute_id,
                "type": "alliance_formed",
                "with": tribute2.tribute_id
            }, {
                "tribute_id": tribute2.tribute_id,
                "type": "alliance_formed",
                "with": tribute1.tribute_id
            }]
        }

    def _get_event_type_counts(self) -> Dict[str, int]:
        """Count events by type"""
        counts = {}
        for event in self.event_log:
            if event['message_type'] == 'game_event':
                event_type = event['data']['event_type']
                counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    def save_game_state(self, filepath: Optional[str] = None) -> None:
        """Save current game state to file"""
        if filepath is None:
            filepath = self.state_path
        
        # Skip saving if no filepath specified
        if filepath is None:
            print("[SAVE_STATE] No state_path configured, skipping save")
            return

        # Use GameState's save_game_state method for proper serialization
        self.game_state.save_game_state(filepath)

    def load_game_state(self, filepath: Optional[str] = None) -> bool:
        """Load game state from file"""
        if filepath is None:
            filepath = self.state_path

        if not os.path.exists(filepath):
            return False

        try:
            # Load the game state data into the GameState object
            self.game_state.load_game_state(filepath)

            # Restore Aurora Engine specific state from the file
            with open(filepath, 'r') as f:
                saved_state = json.load(f)

            self.game_active = saved_state.get('game_active', False)

            # Restore phase controller if it was saved separately
            pc_state = saved_state.get('phase_controller_state', {})
            if pc_state:
                self.phase_controller.current_day = pc_state.get('current_day', 1)
                self.phase_controller.current_phase = pc_state.get('current_phase', 0)
                self.phase_controller.cornucopia_completed = pc_state.get('cornucopia_completed', False)
                self.phase_controller.game_started = pc_state.get('game_started', False)

            # Restore event log if available
            event_log = saved_state.get('event_log', [])
            if event_log:
                self.event_log = event_log

            print(f"Loaded game state from {filepath}")
            return True

        except Exception as e:
            print(f"Error loading game state: {e}")
            return False


# Global reference to current engine instance for send_to_game_manager
_current_engine = None

def set_current_engine(engine):
    """Set the current engine instance for message sending"""
    global _current_engine
    _current_engine = engine

# Web interface integration functions
def send_to_game_manager(message: Dict[str, Any]) -> None:
    """Send a JSON message to the game manager (web system)"""
    global _current_engine
    if _current_engine:
        # Add message to engine's message queue for processing by integration layer
        _current_engine.message_queue.append(message)
    else:
        # Fallback: just print to console
        print(f"[Aurora Engine] Sending to Game Manager: {json.dumps(message, indent=2)}")


def process_game_messages(engine: AuroraEngine) -> None:
    """Process and send pending messages to the game manager"""
    messages = engine.get_pending_messages()
    for message in messages:
        send_to_game_manager(message)


# Example usage
if __name__ == "__main__":
    print("Aurora Engine - Hunger Games Simulator")
    print("=" * 40)

    # Create engine
    engine = AuroraEngine()

    # Sample players with detailed tribute data
    players = [
        {
            "id": "player1",
            "tribute_id": "player1",
            "name": "Tribute 1",
            "district": 1,
            "skills": {"strength": 8, "agility": 6, "intelligence": 7},
            "inventory": []
        },
        {
            "id": "player2",
            "tribute_id": "player2",
            "name": "Tribute 2",
            "district": 2,
            "skills": {"strength": 5, "agility": 9, "intelligence": 8},
            "inventory": []
        },
        {
            "id": "player3",
            "tribute_id": "player3",
            "name": "Tribute 3",
            "district": 3,
            "skills": {"strength": 7, "agility": 7, "intelligence": 6},
            "inventory": []
        },
        {
            "id": "player4",
            "tribute_id": "player4",
            "name": "Tribute 4",
            "district": 4,
            "skills": {"strength": 6, "agility": 8, "intelligence": 9},
            "inventory": []
        }
    ]

    # Start game
    print("Starting game...")
    start_msg = engine.start_game(players)
    process_game_messages(engine)

    # Demonstrate tribute registration (like from web interface)
    print("\nRegistering additional tribute (resume scenario)...")
    resume_input = {
        "id": "reg_001",
        "command_type": "register_tribute",
        "tribute_id": "player1_resume",
        "tribute_data": {
            "name": "Tribute 1",
            "district": 1,
            "skills": {"strength": 8, "agility": 6, "intelligence": 7}
        },
        "is_resume": True
    }
    resume_response = engine.process_input(resume_input)
    if resume_response:
        process_game_messages(engine)
        print(f"Tribute resume registered - ID mapping: {engine.game_state.tribute_id_mapping}")

    # Demonstrate status update by name
    print("\nUpdating tribute status by name...")
    status_input = {
        "id": "status_001",
        "command_type": "update_tribute_status",
        "tribute_name": "Tribute 2",
        "status": "injured",
        "details": {"cause": "fall", "severity": "medium"}
    }
    status_response = engine.process_input(status_input)
    if status_response:
        process_game_messages(engine)

    # Generate some events
    print("\nGenerating events...")
    for i in range(3):
        event_msg = engine.generate_event()
        if event_msg:
            process_game_messages(engine)
        time.sleep(0.5)  # Simulate time passing

    # Process a PvP request (should fail since PvP input is disabled)
    print("\nTesting PvP request (should be disabled)...")
    pvp_input = {
        "id": "input_001",
        "command_type": "pvp_request",
        "initiator_id": "player1",
        "target_id": "player2"
    }
    pvp_response = engine.process_input(pvp_input)
    if pvp_response:
        process_game_messages(engine)

    # Generate events to trigger random encounters
    print("\nGenerating events (may include random encounters)...")
    for i in range(8):  # Generate more events to increase chance of random encounters
        event_msg = engine.generate_event()
        if event_msg:
            process_game_messages(engine)
            event_type = event_msg['data']['event_type']
            if event_type == "PvP Events":
                print(f"  -> Random encounter generated!")
        time.sleep(0.2)  # Simulate time passing

    # Advance phase
    print("\nAdvancing phase...")
    phase_msg = engine.advance_phase()
    if phase_msg:
        process_game_messages(engine)

    # Get game status
    print("\nCurrent Game Status:")
    status = engine.get_game_status()
    print(json.dumps(status, indent=2))

    # Get animation events
    print("\nRecent Animation Events:")
    animations = engine.get_animation_events()
    for event in animations[-3:]:  # Show last 3
        print(f"- {event.get('event_category', 'Unknown')}: {event.get('description', 'No description')}")

    print("\nAurora Engine test completed!")