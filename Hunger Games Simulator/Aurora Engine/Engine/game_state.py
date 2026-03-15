import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random
from tribute import Tribute

class GameState:
    """Tracks comprehensive game state for the Aurora Engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_day = 1
        self.current_phase = 0  # 0 = Cornucopia, 1-3 = Day phases
        self.game_start_time = datetime.now()
        self.last_event_time = None
        self.phase_start_time = datetime.now()

        # Tribute tracking with ID mapping
        self.tributes = {}  # tribute_id -> Tribute object
        self.tribute_statuses = {}  # tribute_id -> status (for quick access, mirrors tribute.status)
        self.tribute_relationships = {}  # tribute_id -> {other_tribute_id: relationship_score} (for quick access)
        self.tribute_id_mapping = {}  # tribute_name -> list of associated IDs (for resume scenarios)
        self.primary_tribute_ids = {}  # tribute_name -> primary tribute_id
        self.fallen_tributes = []  # List of tributes who have died (for death tracking)

        # Event history for animations
        self.event_history = []  # List of events with detailed data
        self.recent_events = []  # Last 10 events for quick access

        # Timer management
        self.event_timers = {}  # event_type -> next_available_time
        self.phase_timer = None
        self.pvp_cooldowns = {}  # tribute_id -> next_pvp_time

        # PvP tracking
        self.active_pvp_battles = []  # List of ongoing PvP battles
        self.pending_pvp_requests = []  # Queue of PvP requests

        # Input queue for external commands
        self.input_queue = []

        # Initialize timers
        self._initialize_timers()

    def _initialize_timers(self):
        """Initialize all event timers based on config"""
        timers = self.config.get('timers', {})
        event_cooldowns = timers.get('event_cooldowns', {})

        current_time = datetime.now()
        for event_type, cooldown_seconds in event_cooldowns.items():
            self.event_timers[event_type] = current_time

    def add_tribute(self, tribute_id: str, tribute_data: Dict[str, Any], is_resume: bool = False):
        """Add a tribute to the game state"""
        tribute_name = tribute_data.get("name", f"Tribute {tribute_id}")

        # Handle ID mapping for resume scenarios
        if is_resume and tribute_name in self.primary_tribute_ids:
            # This is a resume - associate new ID with existing tribute
            primary_id = self.primary_tribute_ids[tribute_name]
            if tribute_name not in self.tribute_id_mapping:
                self.tribute_id_mapping[tribute_name] = []
            if primary_id not in self.tribute_id_mapping[tribute_name]:
                self.tribute_id_mapping[tribute_name].append(primary_id)
            if tribute_id not in self.tribute_id_mapping[tribute_name]:
                self.tribute_id_mapping[tribute_name].append(tribute_id)

            # Create new Tribute object that inherits state from primary tribute
            primary_tribute = self.tributes[primary_id]
            new_tribute = Tribute(tribute_id, tribute_data)

            # Copy key state from primary tribute
            new_tribute.health = primary_tribute.health
            new_tribute.sanity = primary_tribute.sanity
            new_tribute.hunger = primary_tribute.hunger
            new_tribute.thirst = primary_tribute.thirst
            new_tribute.fatigue = primary_tribute.fatigue
            new_tribute.status = primary_tribute.status
            new_tribute.status_effects = primary_tribute.status_effects.copy()
            new_tribute.relationships = primary_tribute.relationships.copy()
            new_tribute.alliances = primary_tribute.alliances.copy()
            new_tribute.enemies = primary_tribute.enemies.copy()
            new_tribute.has_shelter = primary_tribute.has_shelter
            new_tribute.has_fire = primary_tribute.has_fire
            new_tribute.inventory = primary_tribute.inventory.copy()

            self.tributes[tribute_id] = new_tribute
            self.tribute_statuses[tribute_id] = new_tribute.status
            self.tribute_relationships[tribute_id] = new_tribute.relationships

            # Copy PvP cooldown
            if primary_id in self.pvp_cooldowns:
                self.pvp_cooldowns[tribute_id] = self.pvp_cooldowns[primary_id]
        else:
            # New tribute or first registration
            self.primary_tribute_ids[tribute_name] = tribute_id
            if tribute_name not in self.tribute_id_mapping:
                self.tribute_id_mapping[tribute_name] = []
            if tribute_id not in self.tribute_id_mapping[tribute_name]:
                self.tribute_id_mapping[tribute_name].append(tribute_id)

            # Create new Tribute object
            tribute = Tribute(tribute_id, tribute_data)
            self.tributes[tribute_id] = tribute
            self.tribute_statuses[tribute_id] = tribute.status
            self.tribute_relationships[tribute_id] = tribute.relationships

            # Initialize PvP cooldown
            pvp_settings = self.config.get('pvp_settings', {})
            cooldown_seconds = pvp_settings.get('pvp_cooldown_seconds', 300)
            self.pvp_cooldowns[tribute_id] = datetime.now() + timedelta(seconds=cooldown_seconds)

    def resolve_tribute_id(self, identifier: str) -> Optional[str]:
        """Resolve a tribute identifier (ID or name) to a primary tribute ID"""
        # First check if it's already a valid ID
        if identifier in self.tributes:
            return identifier

        # Check if it's a tribute name
        if identifier in self.primary_tribute_ids:
            return self.primary_tribute_ids[identifier]

        # Check if it's an associated ID
        for name, ids in self.tribute_id_mapping.items():
            if identifier in ids:
                return self.primary_tribute_ids[name]

        return None

    def get_tribute_by_identifier(self, identifier: str) -> Optional[Tribute]:
        """Get tribute object by ID or name"""
        tribute_id = self.resolve_tribute_id(identifier)
        if tribute_id:
            return self.tributes.get(tribute_id)
        return None

    def update_tribute_status(self, tribute_id: str, status: str, details: Optional[Dict] = None):
        """Update a tribute's status"""
        if tribute_id in self.tributes:
            old_status = self.tributes[tribute_id].status
            self.tributes[tribute_id].status = status
            self.tribute_statuses[tribute_id] = status

            # Record status change in event history
            event_data = {
                "event_type": "status_change",
                "timestamp": datetime.now().isoformat(),
                "tribute_id": tribute_id,
                "old_status": old_status,
                "new_status": status,
                "details": details or {}
            }
            self._add_to_event_history(event_data)

    def update_tribute_status_by_identifier(self, identifier: str, status: str, details: Optional[Dict] = None):
        """Update tribute status using ID or name"""
        tribute_id = self.resolve_tribute_id(identifier)
        if tribute_id:
            self.update_tribute_status(tribute_id, status, details)

    def get_all_tribute_ids_for_name(self, tribute_name: str) -> List[str]:
        """Get all associated IDs for a tribute name"""
        return self.tribute_id_mapping.get(tribute_name, [])

    def sync_tribute_status_across_ids(self, tribute_name: str, status: str):
        """Sync status across all IDs associated with a tribute name"""
        if tribute_name in self.tribute_id_mapping:
            for tribute_id in self.tribute_id_mapping[tribute_name]:
                if tribute_id in self.tributes:
                    self.tributes[tribute_id].status = status
                    self.tribute_statuses[tribute_id] = status

    # Tribute state management methods
    def apply_natural_decay_to_all_tributes(self, hours_passed: int = 1):
        """Apply natural stat decay to all living tributes"""
        for tribute in self.tributes.values():
            if tribute.status == "alive":
                tribute.apply_natural_decay(hours_passed)

    def get_tribute_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get state summaries for all tributes"""
        summaries = {}
        for tribute_id, tribute in self.tributes.items():
            summaries[tribute_id] = tribute.get_state_summary()
        return summaries

    def get_living_tributes(self) -> List[Tribute]:
        """Get all living tributes"""
        return [tribute for tribute in self.tributes.values() if tribute.status == "alive"]

    def get_tribute_by_location(self, location: str) -> List[Tribute]:
        """Get all tributes in a specific location"""
        return [tribute for tribute in self.tributes.values() if tribute.location == location]

    def update_tribute_health(self, identifier: str, delta: int, cause: str = "unknown"):
        """Update a tribute's health"""
        tribute = self.get_tribute_by_identifier(identifier)
        if tribute:
            tribute.update_health(delta, cause)

    def update_tribute_sanity(self, identifier: str, delta: int, cause: str = "unknown"):
        """Update a tribute's sanity"""
        tribute = self.get_tribute_by_identifier(identifier)
        if tribute:
            tribute.update_sanity(delta, cause)

    def tribute_build_shelter(self, identifier: str) -> bool:
        """Have a tribute attempt to build shelter"""
        tribute = self.get_tribute_by_identifier(identifier)
        if tribute:
            return tribute.build_shelter()
        return False

    def tribute_start_fire(self, identifier: str) -> bool:
        """Have a tribute attempt to start a fire"""
        tribute = self.get_tribute_by_identifier(identifier)
        if tribute:
            return tribute.start_fire()
        return False

    def update_tribute_relationship(self, tribute1_id: str, tribute2_id: str, delta: int):
        """Update relationship between two tributes"""
        tribute1 = self.get_tribute_by_identifier(tribute1_id)
        tribute2 = self.get_tribute_by_identifier(tribute2_id)

        if tribute1 and tribute2:
            tribute1.update_relationship(tribute2.tribute_id, delta)
            tribute2.update_relationship(tribute1.tribute_id, delta)

            # Update cached relationships
            self.tribute_relationships[tribute1.tribute_id] = tribute1.relationships
            self.tribute_relationships[tribute2.tribute_id] = tribute2.relationships

    def get_tribute_decision(self, identifier: str, available_actions: List[str], context: Dict[str, Any]) -> str:
        """Get a decision from a tribute based on available actions and context"""
        tribute = self.get_tribute_by_identifier(identifier)
        if tribute:
            return tribute.make_decision(available_actions, context)
        return "wait"

    def should_tributes_attack(self, tribute1_id: str, tribute2_id: str) -> bool:
        """Check if one tribute should attack another"""
        tribute1 = self.get_tribute_by_identifier(tribute1_id)
        tribute2 = self.get_tribute_by_identifier(tribute2_id)

        if tribute1 and tribute2:
            return tribute1.should_attack(tribute2)
        return False

    def record_event(self, event_data: Dict[str, Any]):
        """Record an event in the game history for animations"""
        event_data["timestamp"] = datetime.now().isoformat()
        event_data["day"] = self.current_day
        event_data["phase"] = self.current_phase

        # Resolve participant identifiers to IDs
        resolved_participants = []
        if "participants" in event_data:
            for participant in event_data["participants"]:
                resolved_id = self.resolve_tribute_id(participant)
                if resolved_id:
                    resolved_participants.append(resolved_id)
                else:
                    resolved_participants.append(participant)  # Keep original if can't resolve
            event_data["resolved_participants"] = resolved_participants

        # Apply event consequences to specific tributes
        if "consequences" in event_data:
            self._apply_event_consequences(event_data["consequences"], resolved_participants)

        # Update tribute relationships based on event
        self._update_relationships_from_event(event_data)

        self._add_to_event_history(event_data)
        self.last_event_time = datetime.now()

        # Update timer for this event type
        event_type = event_data.get("event_category", "Custom Events")
        if event_type in self.event_timers:
            cooldown_seconds = self.config.get('timers', {}).get('event_cooldowns', {}).get(event_type, 30)
            self.event_timers[event_type] = datetime.now() + timedelta(seconds=cooldown_seconds)

    def _apply_event_consequences(self, consequences: List[Dict[str, Any]], participants: List[str]):
        """Apply event consequences to tributes"""
        for consequence in consequences:
            consequence_type = consequence.get("type")

            if consequence_type == "stat_effect":
                self._apply_stat_effect_consequence(consequence)
            elif consequence_type == "inventory_add":
                self._apply_inventory_consequence(consequence)
            elif consequence_type == "resource_add":
                self._apply_resource_add_consequence(consequence)
            elif consequence_type == "relationship_change":
                self._apply_relationship_change_consequence(consequence)
            elif consequence_type == "alliance_form":
                self._apply_alliance_consequence(consequence)
            elif consequence_type == "status_effect":
                self._apply_status_effect_consequence(consequence)
            # Legacy consequence types
            elif consequence_type == "damage":
                self._apply_damage_consequence(consequence, participants)
            elif consequence_type == "status_change":
                self._apply_status_consequence(consequence, participants)
            elif consequence_type == "relationship_change":
                self._apply_relationship_consequence(consequence, participants)
            elif consequence_type == "resource_gain":
                self._apply_resource_consequence(consequence, participants)

    def _apply_damage_consequence(self, consequence: Dict[str, Any], participants: List[str]):
        """Apply damage to tributes"""
        target = consequence.get("target", "all_participants")
        amount = consequence.get("amount", "low")

        if target == "all_participants":
            targets = participants
        elif target == "random":
            count = consequence.get("count", 1)
            targets = random.sample(participants, min(count, len(participants)))
        elif target in participants:
            targets = [target]
        else:
            return

        # Apply damage effects using tribute methods
        damage_amounts = {
            "low": -10,
            "medium": -25,
            "high": -50
        }

        for tribute_id in targets:
            tribute = self.tributes.get(tribute_id)
            if tribute and amount in damage_amounts:
                tribute.update_health(damage_amounts[amount], "event_damage")

    def _apply_status_consequence(self, consequence: Dict[str, Any], participants: List[str]):
        """Apply status changes to tributes"""
        target = consequence.get("target", "all_participants")
        status = consequence.get("status")
        chance = consequence.get("chance", 1.0)

        if not status or random.random() > chance:
            return

        if target == "all_participants":
            targets = participants
        elif target == "random":
            targets = [random.choice(participants)] if participants else []
        elif target in participants:
            targets = [target]
        else:
            return

        for tribute_id in targets:
            self.update_tribute_status(tribute_id, status, {"cause": "event_consequence"})

    def _apply_relationship_consequence(self, consequence: Dict[str, Any], participants: List[str]):
        """Apply relationship changes between tributes"""
        participants_list = consequence.get("participants", "all_pairs")
        change = consequence.get("change", 0)

        if participants_list == "all_pairs":
            # Update relationships between all pairs using tribute methods
            for i, tribute1_id in enumerate(participants):
                for j, tribute2_id in enumerate(participants):
                    if i != j:
                        self.update_tribute_relationship(tribute1_id, tribute2_id, change)
        elif participants_list == "all_others":
            # This would be handled in the calling context
            pass

    def _apply_resource_consequence(self, consequence: Dict[str, Any], participants: List[str]):
        """Apply resource changes to tributes"""
        target = consequence.get("target", "all_participants")
        resource = consequence.get("resource")

        if target == "winner":
            # Determine winner (simplified - first participant)
            winner_id = participants[0] if participants else None
            if winner_id:
                tribute = self.tributes.get(winner_id)
                if tribute:
                    tribute.add_to_inventory(resource)

    def _apply_stat_effect_consequence(self, consequence: Dict[str, Any]):
        """Apply stat effect to a tribute"""
        target_id = consequence.get("target")
        stat = consequence.get("stat")
        value = consequence.get("value", 0)

        if not target_id or not stat:
            return

        tribute = self.tributes.get(target_id)
        if not tribute:
            return

        # Apply stat change based on stat type
        if stat == "health":
            tribute.update_health(value, consequence.get("description", "event"))
        elif stat == "sanity":
            tribute.update_sanity(value, consequence.get("description", "event"))
        elif stat == "hunger":
            tribute.update_hunger(value)
        elif stat == "thirst":
            tribute.update_thirst(value)
        elif stat == "fatigue":
            tribute.update_fatigue(value)

    def _apply_inventory_consequence(self, consequence: Dict[str, Any]):
        """Add item to tribute inventory"""
        target_id = consequence.get("target")
        item = consequence.get("item")

        if not target_id or not item:
            return

        tribute = self.tributes.get(target_id)
        if tribute:
            tribute.add_to_inventory(item)

    def _apply_resource_add_consequence(self, consequence: Dict[str, Any]):
        """Add resources to tribute"""
        target_id = consequence.get("target")
        resource = consequence.get("resource")
        amount = consequence.get("amount", 0)

        if not target_id or not resource or amount <= 0:
            return

        tribute = self.tributes.get(target_id)
        if tribute:
            if resource == "food_supplies":
                tribute.food_supplies += amount
            elif resource == "water_supplies":
                tribute.water_supplies += amount
            elif resource == "medical_supplies":
                tribute.medical_supplies.append(f"medical_pack_{amount}")

    def _apply_status_effect_consequence(self, consequence: Dict[str, Any]):
        """Apply temporary status effect to tribute"""
        target_id = consequence.get("target")
        status_name = consequence.get("status_name")
        duration_phases = consequence.get("duration_phases", 1)
        stat_modifiers = consequence.get("stat_modifiers", {})

        if not target_id or not status_name:
            return

        tribute = self.tributes.get(target_id)
        if tribute:
            # Add status effect to tribute's ongoing effects
            status_effect = {
                "name": status_name,
                "duration_remaining": duration_phases,
                "stat_modifiers": stat_modifiers,
                "description": consequence.get("description", f"Status: {status_name}")
            }
            
            if not hasattr(tribute, 'status_effects'):
                tribute.status_effects = []
            
            tribute.status_effects.append(status_effect)

    def _apply_relationship_change_consequence(self, consequence: Dict[str, Any]):
        """Update relationship between tributes"""
        target1 = consequence.get("target1")
        target2 = consequence.get("target2")
        value = consequence.get("value", 0)

        if target1 and target2:
            self.update_tribute_relationship(target1, target2, value)

    def _apply_alliance_consequence(self, consequence: Dict[str, Any]):
        """Form alliance between tributes"""
        target_id = consequence.get("target")
        allies = consequence.get("allies", [])

        if not target_id or not allies:
            return

        tribute = self.tributes.get(target_id)
        if tribute:
            for ally_id in allies:
                tribute.form_alliance(ally_id)

    def _add_to_event_history(self, event_data: Dict[str, Any]):
        """Add event to history and maintain recent events list"""
        self.event_history.append(event_data)
        self.recent_events.append(event_data)

        # Keep only last 50 events in recent list
        if len(self.recent_events) > 50:
            self.recent_events = self.recent_events[-50:]

    def _update_relationships_from_event(self, event_data: Dict[str, Any]):
        """Update tribute relationships based on event interactions"""
        participants = event_data.get("participants", [])
        event_type = event_data.get("event_category", "")

        if event_type == "Combat Events" or event_type == "PvP Events":
            # Combat events affect relationships negatively
            for i, tribute1_id in enumerate(participants):
                for j, tribute2_id in enumerate(participants):
                    if i != j:
                        self.update_tribute_relationship(tribute1_id, tribute2_id, -10)  # Combat reduces relationship

        elif event_type == "Arena Events":
            # Arena events might create alliances or rivalries
            if len(participants) > 1:
                # Small positive boost for working together
                for i, tribute1_id in enumerate(participants):
                    for j, tribute2_id in enumerate(participants):
                        if i != j:
                            self.update_tribute_relationship(tribute1_id, tribute2_id, 2)

    def can_generate_event(self, event_type: str) -> bool:
        """Check if an event of the given type can be generated based on timers"""
        if event_type not in self.event_timers:
            return True

        current_time = datetime.now()
        next_available = self.event_timers[event_type]

        # Check minimum time between events
        min_time = self.config.get('timers', {}).get('minimum_time_between_events', 5)
        if self.last_event_time and (current_time - self.last_event_time).seconds < min_time:
            return False

        return current_time >= next_available

    def get_next_event_time(self, event_type: str) -> Optional[datetime]:
        """Get the next time an event of this type can be generated"""
        return self.event_timers.get(event_type)

    def advance_phase(self):
        """Advance to the next game phase"""
        phases_per_day = self.config.get('settings', {}).get('phases_per_day', 3)

        if self.current_phase == 0:  # Cornucopia -> Phase 1
            self.current_phase = 1
        elif self.current_phase < phases_per_day:
            self.current_phase += 1
        else:  # End of day
            self.current_day += 1
            self.current_phase = 1

        self.phase_start_time = datetime.now()

        # Set phase timer - durations in config are in minutes, convert to seconds
        # Cornucopia phase has no maximum time - it lasts until manually advanced
        if self.current_phase == 0 and not self.cornucopia_completed:
            # Cornucopia phase - no timer
            self.phase_timer = None
        else:
            # Regular day phases
            phase_duration_minutes = self.config.get('timers', {}).get('phase_transitions', {}).get('day_phase', 60)
            phase_duration_seconds = phase_duration_minutes * 60
            self.phase_timer = datetime.now() + timedelta(seconds=phase_duration_seconds)

        # Process status effects - reduce duration and remove expired ones
        self._process_status_effects()

    def _process_status_effects(self):
        """Process and update status effects for all tributes"""
        for tribute in self.tributes.values():
            if hasattr(tribute, 'status_effects') and tribute.status_effects:
                # Reduce duration of all status effects
                expired_effects = []
                for effect in tribute.status_effects:
                    effect['duration_remaining'] -= 1
                    if effect['duration_remaining'] <= 0:
                        expired_effects.append(effect)
                
                # Remove expired effects
                for expired_effect in expired_effects:
                    tribute.status_effects.remove(expired_effect)

    def should_advance_phase(self) -> bool:
        """Check if it's time to advance to the next phase"""
        if not self.phase_timer:
            return False
        return datetime.now() >= self.phase_timer

    def add_pvp_request(self, initiator_id: str, target_id: str, is_random_encounter: bool = False) -> bool:
        """Add a PvP battle request to the queue"""
        pvp_settings = self.config.get('pvp_settings', {})

        # Check if PvP is allowed at all
        if not pvp_settings.get('allow_player_initiated_pvp', False) and not is_random_encounter:
            return False

        # For random encounters, skip cooldown and target validation
        if not is_random_encounter:
            # Check if initiator is on cooldown
            if initiator_id in self.pvp_cooldowns and datetime.now() < self.pvp_cooldowns[initiator_id]:
                return False

            # Check if target is valid and alive
            if target_id not in self.tribute_statuses or self.tribute_statuses[target_id] != "alive":
                return False

        # Check max concurrent battles
        max_concurrent = pvp_settings.get('max_concurrent_pvp_battles', 3)
        if len(self.active_pvp_battles) >= max_concurrent:
            return False

        # Add to pending requests
        request = {
            "initiator_id": initiator_id,
            "target_id": target_id,
            "request_time": datetime.now(),
            "status": "pending",
            "is_random_encounter": is_random_encounter
        }
        self.pending_pvp_requests.append(request)

        return True

    def generate_random_encounter(self) -> Optional[Dict[str, Any]]:
        """Generate a random encounter between 2-5 tributes"""
        pvp_settings = self.config.get('pvp_settings', {})

        if not pvp_settings.get('allow_random_encounters', False):
            return None

        # Check random encounter chance
        encounter_chance = pvp_settings.get('random_encounter_chance', 0.3)
        if random.random() > encounter_chance:
            return None

        # Get all alive tributes
        alive_tributes = [tid for tid, status in self.tribute_statuses.items() if status == "alive"]
        if len(alive_tributes) < 2:
            return None

        # Determine number of participants (2-5, but not more than available)
        min_participants = min(pvp_settings.get('min_tributes_per_encounter', 2), len(alive_tributes))
        max_participants = min(pvp_settings.get('max_tributes_per_encounter', 5), len(alive_tributes))

        num_participants = random.randint(min_participants, max_participants)

        # Select random participants
        participants = random.sample(alive_tributes, num_participants)

        # Create encounter request
        encounter_request = {
            "participants": participants,
            "encounter_type": "random_multi_tribute",
            "request_time": datetime.now(),
            "status": "active"
        }

        # Add to active battles
        self.active_pvp_battles.append(encounter_request)

        return encounter_request

    def get_random_encounter_participants(self, count: int) -> List[str]:
        """Get a list of random tribute IDs for an encounter"""
        alive_tributes = [tid for tid, status in self.tribute_statuses.items() if status == "alive"]
        if len(alive_tributes) < count:
            return alive_tributes  # Return all available if fewer than requested

        return random.sample(alive_tributes, count)

    def add_input(self, input_data: Dict[str, Any]):
        """Add external input to the processing queue"""
        input_data["received_time"] = datetime.now().isoformat()
        self.input_queue.append(input_data)

    def get_pending_inputs(self) -> List[Dict[str, Any]]:
        """Get all pending inputs for processing"""
        return self.input_queue.copy()

    def clear_processed_inputs(self, processed_inputs: List[Dict[str, Any]]):
        """Remove processed inputs from the queue"""
        for processed in processed_inputs:
            if processed in self.input_queue:
                self.input_queue.remove(processed)

    def get_game_status(self) -> Dict[str, Any]:
        """Get comprehensive game status for web interface"""
        return {
            "current_day": self.current_day,
            "current_phase": self.current_phase,
            "phase_start_time": self.phase_start_time.isoformat(),
            "next_phase_time": self.phase_timer.isoformat() if self.phase_timer else None,
            "active_tributes": {tid: status for tid, status in self.tribute_statuses.items() if status == "alive"},
            "total_tributes": len(self.tributes),
            "recent_events": self.recent_events[-5:],  # Last 5 events
            "active_pvp_battles": len(self.active_pvp_battles),
            "pending_pvp_requests": len(self.pending_pvp_requests),
            "next_event_timers": {event_type: timer.isoformat() for event_type, timer in self.event_timers.items()}
        }

    def get_tribute_scoreboards(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed tribute data for scoreboards"""
        scoreboards = {}

        for tribute_id, tribute in self.tributes.items():
            # Get equipped weapon (first weapon in list, or None)
            equipped_weapon = tribute.weapons[0] if tribute.weapons else None

            scoreboards[tribute_id] = {
                "id": tribute_id,
                "name": tribute.name,
                "district": tribute.district,
                "status": tribute.status,
                "health": tribute.health,
                "sanity": tribute.sanity,
                "hunger": tribute.hunger,
                "thirst": tribute.thirst,
                "fatigue": tribute.fatigue,
                "equipped_weapon": equipped_weapon,
                "weapons": tribute.weapons,
                "inventory": tribute.inventory,
                "food_supplies": tribute.food_supplies,
                "water_supplies": tribute.water_supplies,
                "has_shelter": tribute.has_shelter,
                "has_fire": tribute.has_fire,
                "location": tribute.location,
                "alliances": list(tribute.alliances),
                "enemies": list(tribute.enemies),
                "skills": tribute.skills,
                "status_effects": tribute.status_effects
            }

        return scoreboards

    def get_animation_events(self, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get events suitable for animations since a given timestamp"""
        if not since_timestamp:
            return self.recent_events

        try:
            since_time = datetime.fromisoformat(since_timestamp)
            return [event for event in self.event_history if datetime.fromisoformat(event["timestamp"]) > since_time]
        except:
            return self.recent_events

    def save_game_state(self, filename: str):
        """Save the complete game state to a file"""
        # Helper function to serialize datetime objects
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        state_data = {
            "config": self.config,
            "current_day": self.current_day,
            "current_phase": self.current_phase,
            "game_start_time": self.game_start_time.isoformat(),
            "last_event_time": self.last_event_time.isoformat() if self.last_event_time else None,
            "phase_start_time": self.phase_start_time.isoformat(),
            "tribute_id_mapping": self.tribute_id_mapping,
            "primary_tribute_ids": self.primary_tribute_ids,
            "fallen_tributes": self.fallen_tributes,
            "event_history": self.event_history,
            "recent_events": self.recent_events,
            "event_timers": {k: v.isoformat() for k, v in self.event_timers.items()},
            "phase_timer": self.phase_timer.isoformat() if self.phase_timer else None,
            "pvp_cooldowns": {k: v.isoformat() for k, v in self.pvp_cooldowns.items()},
            "active_pvp_battles": [serialize_datetime(battle) for battle in self.active_pvp_battles],
            "pending_pvp_requests": self.pending_pvp_requests,
            "input_queue": self.input_queue,
            # Serialize tributes
            "tributes": {tid: tribute.to_dict() for tid, tribute in self.tributes.items()},
            # Cache status and relationships for quick access
            "tribute_statuses": {tid: tribute.status for tid, tribute in self.tributes.items()},
            "tribute_relationships": {tid: tribute.relationships for tid, tribute in self.tributes.items()}
        }

        with open(filename, 'w') as f:
            json.dump(state_data, f, indent=2)

    def load_game_state(self, filename: str):
        """Load game state from a file"""
        with open(filename, 'r') as f:
            state_data = json.load(f)

        # Helper function to deserialize datetime objects
        def deserialize_datetime(obj):
            if isinstance(obj, dict) and "request_time" in obj:
                obj["request_time"] = datetime.fromisoformat(obj["request_time"])
            return obj

        # Restore basic state
        self.config = state_data.get("config", {})
        self.current_day = state_data.get("current_day", 1)
        self.current_phase = state_data.get("current_phase", 0)
        self.game_start_time = datetime.fromisoformat(state_data["game_start_time"])
        self.last_event_time = datetime.fromisoformat(state_data["last_event_time"]) if state_data.get("last_event_time") else None
        self.phase_start_time = datetime.fromisoformat(state_data["phase_start_time"])
        self.tribute_id_mapping = state_data.get("tribute_id_mapping", {})
        self.primary_tribute_ids = state_data.get("primary_tribute_ids", {})
        self.fallen_tributes = state_data.get("fallen_tributes", [])
        self.event_history = state_data.get("event_history", [])
        self.recent_events = state_data.get("recent_events", [])
        self.event_timers = {k: datetime.fromisoformat(v) for k, v in state_data.get("event_timers", {}).items()}
        self.phase_timer = datetime.fromisoformat(state_data["phase_timer"]) if state_data.get("phase_timer") else None
        self.pvp_cooldowns = {k: datetime.fromisoformat(v) for k, v in state_data.get("pvp_cooldowns", {}).items()}
        self.active_pvp_battles = [deserialize_datetime(battle) for battle in state_data.get("active_pvp_battles", [])]
        self.pending_pvp_requests = state_data.get("pending_pvp_requests", [])
        self.input_queue = state_data.get("input_queue", [])

        # Restore tributes
        self.tributes = {}
        for tid, tribute_data in state_data.get("tributes", {}).items():
            self.tributes[tid] = Tribute.from_dict(tribute_data)

        # Restore cached data
        self.tribute_statuses = state_data.get("tribute_statuses", {})
        self.tribute_relationships = state_data.get("tribute_relationships", {})