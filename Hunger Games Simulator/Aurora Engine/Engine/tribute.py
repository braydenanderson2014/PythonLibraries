import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import random

# Import the send_to_game_manager function for real-time updates
try:
    from .Aurora_Engine import send_to_game_manager
except ImportError:
    # Fallback for when imported from different locations
    try:
        import Aurora_Engine
        send_to_game_manager = Aurora_Engine.send_to_game_manager
    except ImportError:
        # If import fails, create a dummy function
        def send_to_game_manager(message):
            print(f"[Tribute] Would send to game manager: {message}")

class Tribute:
    """
    Individual tribute class that manages state, behavior, and decision-making.
    This will integrate with the behavior engine once it's built.
    """

    def __init__(self, tribute_id: str, tribute_data: Dict[str, Any]):
        # Basic identification
        self.tribute_id = tribute_id
        self.name = tribute_data.get("name", f"Tribute {tribute_id}")
        self.district = tribute_data.get("district", 1)

        # Core stats (0-100 scale)
        self.health = 100
        self.sanity = 100
        self.hunger = 0  # 0 = full, 100 = starving
        self.thirst = 0  # 0 = hydrated, 100 = dehydrated
        self.fatigue = 0  # 0 = rested, 100 = exhausted

        # Skills (1-10 scale, affects behavior decisions)
        self.skills = tribute_data.get("skills", {
            "strength": 5,
            "agility": 5,
            "intelligence": 5,
            "survival": 5,
            "combat": 5
        })

        # Trait scores (weighted skill scores from web UI)
        self.trait_scores = tribute_data.get("trait_scores", {})

        # Conditions affecting performance
        self.conditions = tribute_data.get("conditions", ["healthy"])

        # Extremities and limb status
        self.extremities = {
            "left_arm": "healthy",
            "right_arm": "healthy", 
            "left_leg": "healthy",
            "right_leg": "healthy",
            "head": "healthy"
        }
        self.dominant_arm = "right_arm"  # Most tributes are right-handed

        # Limb damage system integration
        try:
            from .limb_damage_system import LimbDamageState
        except ImportError:
            from Engine.limb_damage_system import LimbDamageState
        self.limb_damage = LimbDamageState()

        # Bleeding and infection tracking (legacy, kept for compatibility)
        self.bleeding_wounds = []  # List of active bleeding wounds
        self.infections = []  # List of active infections
        self.bleeding_phases = 0  # Phases spent bleeding
        self.infection_phases = 0  # Phases spent infected

        # Resources and possessions
        self.inventory = tribute_data.get("inventory", [])
        self.weapons = tribute_data.get("weapons", [])  # List of weapon IDs
        self.equipped_weapon = None  # Currently equipped weapon ID
        self.food_supplies = 0  # Days worth of food
        self.water_supplies = 0  # Days worth of water
        self.medical_supplies = []  # Bandages, medicine, etc.
        
        # Auto-equip best weapon if any
        if self.weapons:
            from .weapons_system import get_weapons_system
            ws = get_weapons_system()
            self.equipped_weapon = ws.get_best_weapon(self.weapons, self.skills.get("strength", 5))

        # Environmental state
        self.has_shelter = False
        self.has_fire = False
        self.location = "arena"  # Current location/area
        self.terrain_type = "unknown"  # forest, river, mountain, etc.

        # Social state
        self.relationships = {}  # tribute_id -> relationship_score (-100 to 100)
        self.alliances = set()  # Set of allied tribute_ids
        self.enemies = set()  # Set of enemy tribute_ids

        # Status and conditions
        self.status = "alive"  # alive, dead, injured, unconscious, etc.
        self.status_effects = []  # bleeding, poisoned, etc.
        self.last_action_time = datetime.now()
        self.action_cooldown = 0  # seconds until next action

        # Behavior state (for future behavior engine integration)
        self.personality_traits = self._generate_personality()
        self.current_goal = "survive"  # survive, hunt, hide, attack, etc.
        self.risk_tolerance = self._calculate_risk_tolerance()
        self.social_preference = self._calculate_social_preference()

        # Decision history for behavior learning
        self.decision_history = []
        self.success_rate = 0.5  # Track decision success

    def _generate_personality(self) -> Dict[str, float]:
        """Generate personality traits based on skills and random factors"""
        base_traits = {
            "aggressive": random.uniform(0.1, 0.9),
            "cautious": random.uniform(0.1, 0.9),
            "social": random.uniform(0.1, 0.9),
            "selfish": random.uniform(0.1, 0.9),
            "intelligent": self.skills.get("intelligence", 5) / 10.0
        }

        # Normalize so they sum to 1
        total = sum(base_traits.values())
        return {k: v/total for k, v in base_traits.items()}

    def _calculate_risk_tolerance(self) -> float:
        """Calculate risk tolerance based on personality and skills"""
        # Higher intelligence and survival skills = more calculated risks
        # Higher aggression = more risk-taking
        intelligence_factor = self.skills.get("intelligence", 5) / 10.0
        survival_factor = self.skills.get("survival", 5) / 10.0
        aggression_factor = self.personality_traits.get("aggressive", 0.5)

        return (intelligence_factor + survival_factor + aggression_factor) / 3.0

    def _calculate_social_preference(self) -> float:
        """Calculate preference for social interaction (-1 to 1, negative = prefers solitude)"""
        social_trait = self.personality_traits.get("social", 0.5)
        selfish_trait = self.personality_traits.get("selfish", 0.5)

        return social_trait - selfish_trait

    # State management methods
    def update_health(self, delta: int, cause: str = "unknown"):
        """Update health with bounds checking"""
        old_health = self.health
        self.health = max(0, min(100, self.health + delta))

        if self.health <= 0:
            self.status = "dead"
        elif self.health < 30:
            self.status = "critical"
        elif self.health < 60:
            self.status = "injured"

        # Record health change
        self._record_state_change("health", old_health, self.health, {"cause": cause})

        # Send real-time update to game manager
        if old_health != self.health:
            send_to_game_manager({
                "type": "tribute_stat_update",
                "tribute_id": self.tribute_id,
                "stat": "health",
                "old_value": old_health,
                "new_value": self.health,
                "delta": delta,
                "cause": cause,
                "timestamp": datetime.now().isoformat()
            })

    def update_sanity(self, delta: int, cause: str = "unknown"):
        """Update sanity with bounds checking"""
        old_sanity = self.sanity
        self.sanity = max(0, min(100, self.sanity + delta))

        if self.sanity < 20:
            self.status_effects.append("insane") if "insane" not in self.status_effects else None

        self._record_state_change("sanity", old_sanity, self.sanity, {"cause": cause})

        # Send real-time update to game manager
        if old_sanity != self.sanity:
            send_to_game_manager({
                "type": "tribute_stat_update",
                "tribute_id": self.tribute_id,
                "stat": "sanity",
                "old_value": old_sanity,
                "new_value": self.sanity,
                "delta": delta,
                "cause": cause,
                "timestamp": datetime.now().isoformat()
            })

    def update_hunger(self, delta: int):
        """Update hunger (positive delta increases hunger)"""
        old_hunger = self.hunger
        self.hunger = max(0, min(100, self.hunger + delta))

        if self.hunger > 80:
            self.update_health(-5, "starvation")
        elif self.hunger > 60:
            self.update_health(-2, "hunger")

        self._record_state_change("hunger", old_hunger, self.hunger)

    def update_thirst(self, delta: int):
        """Update thirst (positive delta increases thirst)"""
        old_thirst = self.thirst
        self.thirst = max(0, min(100, self.thirst + delta))

        if self.thirst > 80:
            self.update_health(-5, "dehydration")
        elif self.thirst > 60:
            self.update_health(-2, "thirst")

        self._record_state_change("thirst", old_thirst, self.thirst)

    def update_fatigue(self, delta: int):
        """Update fatigue (positive delta increases fatigue)"""
        old_fatigue = self.fatigue
        self.fatigue = max(0, min(100, self.fatigue + delta))

        if self.fatigue > 80:
            self.skills = {k: max(1, v-2) for k, v in self.skills.items()}  # Reduce all skills
        elif self.fatigue < 20:
            self.skills = {k: min(10, v+1) for k, v in self.skills.items()}  # Boost skills when rested

        self._record_state_change("fatigue", old_fatigue, self.fatigue)

    # Resource management
    def add_to_inventory(self, item: str):
        """Add item to inventory"""
        if item not in self.inventory:
            self.inventory.append(item)
            self._record_state_change("inventory_add", None, item)

    def remove_from_inventory(self, item: str) -> bool:
        """Remove item from inventory, return success"""
        if item in self.inventory:
            self.inventory.remove(item)
            self._record_state_change("inventory_remove", item, None)
            return True
        return False

    def build_shelter(self) -> bool:
        """Attempt to build shelter based on skills and resources"""
        if self.has_shelter:
            return False

        # Check for required materials
        has_materials = any(item in ["wood", "rope", "cloth"] for item in self.inventory)

        if not has_materials:
            return False

        # Success based on survival skill
        survival_skill = self.skills.get("survival", 5)
        success_chance = survival_skill / 10.0

        if random.random() < success_chance:
            self.has_shelter = True
            self.update_fatigue(20)  # Building is tiring
            self._record_state_change("shelter_built", False, True)
            return True

        # Failed attempt still costs fatigue
        self.update_fatigue(10)
        return False

    def start_fire(self) -> bool:
        """Attempt to start a fire"""
        if self.has_fire:
            return False

        # Need flammable materials
        has_flammables = any(item in ["wood", "cloth", "dry_grass"] for item in self.inventory)

        if not has_flammables:
            return False

        # Success based on survival skill
        survival_skill = self.skills.get("survival", 5)
        success_chance = survival_skill / 10.0

        if random.random() < success_chance:
            self.has_fire = True
            self._record_state_change("fire_started", False, True)
            return True

        return False

    # Social methods
    def update_relationship(self, other_tribute_id: str, delta: int):
        """Update relationship with another tribute"""
        old_relationship = self.relationships.get(other_tribute_id, 0)
        new_relationship = max(-100, min(100, old_relationship + delta))
        self.relationships[other_tribute_id] = new_relationship

        # Update alliance/enemy sets based on relationship
        if new_relationship > 50:
            self.alliances.add(other_tribute_id)
            self.enemies.discard(other_tribute_id)
        elif new_relationship < -50:
            self.enemies.add(other_tribute_id)
            self.alliances.discard(other_tribute_id)
        else:
            self.alliances.discard(other_tribute_id)
            self.enemies.discard(other_tribute_id)

        self._record_state_change("relationship", old_relationship, new_relationship,
                                {"with": other_tribute_id})

    def form_alliance(self, other_tribute_id: str) -> bool:
        """Attempt to form alliance with another tribute"""
        if other_tribute_id in self.alliances:
            return True

        # Social preference affects willingness
        if self.social_preference < -0.3:  # Prefers solitude
            return False

        self.update_relationship(other_tribute_id, 30)
        return other_tribute_id in self.alliances

    # Weapon management methods
    def add_weapon(self, weapon_id: str):
        """Add weapon to inventory and auto-equip if better"""
        if weapon_id not in self.weapons:
            self.weapons.append(weapon_id)
            self._record_state_change("weapon_add", None, weapon_id)
            
            # Auto-equip if better than current
            from .weapons_system import get_weapons_system
            ws = get_weapons_system()
            best = ws.get_best_weapon(self.weapons, self.skills.get("strength", 5))
            if best != self.equipped_weapon:
                self.equip_weapon(best)
    
    def equip_weapon(self, weapon_id: str) -> bool:
        """Equip a weapon from inventory"""
        if weapon_id not in self.weapons and weapon_id != "fists":
            return False
        
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        weapon = ws.get_weapon(weapon_id)
        
        if not weapon:
            return False
        
        # Check if strong enough to use
        if not weapon.can_use(self.skills.get("strength", 5)):
            return False
        
        self.equipped_weapon = weapon_id
        self._record_state_change("weapon_equipped", None, weapon_id)
        return True
    
    def get_equipped_weapon(self) -> Optional[str]:
        """Get currently equipped weapon ID, defaults to fists"""
        return self.equipped_weapon if self.equipped_weapon else "fists"
    
    def get_effective_combat_skills(self) -> Dict[str, float]:
        """Get combat skills modified by current conditions"""
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        
        # Apply condition modifiers to all skills
        modified = ws._apply_condition_modifiers(self.skills, self.conditions)
        return modified
    
    # Injury/condition management methods
    def add_condition(self, condition_id: str):
        """Add a medical condition/injury"""
        if condition_id not in self.conditions:
            self.conditions.append(condition_id)
            self._record_state_change("condition_add", None, condition_id)
            
            from .weapons_system import get_weapons_system
            ws = get_weapons_system()
            condition = ws.get_condition(condition_id)
            
            if condition:
                # Track bleeding and infection
                if condition.bleeding:
                    if condition_id not in self.bleeding_wounds:
                        self.bleeding_wounds.append(condition_id)
                
                if condition.infection:
                    if condition_id not in self.infections:
                        self.infections.append(condition_id)
    
    def remove_condition(self, condition_id: str):
        """Remove a medical condition/injury"""
        if condition_id in self.conditions:
            self.conditions.remove(condition_id)
            self._record_state_change("condition_remove", condition_id, None)
            
            # Remove from bleeding/infection tracking
            if condition_id in self.bleeding_wounds:
                self.bleeding_wounds.remove(condition_id)
            if condition_id in self.infections:
                self.infections.remove(condition_id)
    
    def is_bleeding(self) -> bool:
        """Check if tribute has any bleeding wounds"""
        return len(self.bleeding_wounds) > 0
    
    def is_infected(self) -> bool:
        """Check if tribute has any infections"""
        return len(self.infections) > 0
    
    def is_critically_injured(self) -> bool:
        """Check if tribute has critical injuries"""
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        
        for condition_id in self.conditions:
            condition = ws.get_condition(condition_id)
            if condition and condition.severity.value >= 4:  # Severe or Critical
                return True
        return False
    
    def treat_wounds(self, medical_skill: int = None) -> Dict[str, Any]:
        """
        Attempt to treat bleeding wounds and infections
        
        Returns:
            {
                'wounds_treated': List[str],
                'infections_cured': List[str],
                'success': bool,
                'message': str
            }
        """
        if medical_skill is None:
            medical_skill = self.skills.get("intelligence", 5)
        
        result = {
            'wounds_treated': [],
            'infections_cured': [],
            'success': False,
            'message': ''
        }
        
        # Need medical supplies
        if not any(item in ["bandage", "medicine", "medical_kit"] for item in self.inventory):
            result['message'] = "No medical supplies available"
            return result
        
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        
        # Treat bleeding wounds
        for wound_id in self.bleeding_wounds[:]:  # Copy list to avoid modification during iteration
            condition = ws.get_condition(wound_id)
            if not condition:
                continue
            
            # Success chance based on medical skill and severity
            success_chance = 0.5 + (medical_skill / 20.0) - (condition.severity.value / 20.0)
            success_chance = max(0.2, min(0.95, success_chance))
            
            if random.random() < success_chance:
                # Downgrade severity or remove
                if condition.severity.value > 2:
                    # Downgrade to less severe bleeding
                    new_condition = f"bleeding_{'mild' if condition.bleeding_level == 'medium' else 'medium'}"
                    self.remove_condition(wound_id)
                    self.add_condition(new_condition)
                    result['wounds_treated'].append(wound_id)
                else:
                    # Fully treated
                    self.remove_condition(wound_id)
                    self.add_condition("bruised")
                    result['wounds_treated'].append(wound_id)
                
                result['success'] = True
        
        # Treat infections
        for infection_id in self.infections[:]:
            if random.random() < 0.6 + (medical_skill / 20.0):
                self.remove_condition(infection_id)
                result['infections_cured'].append(infection_id)
                result['success'] = True
        
        # Consume medical supplies (priority order: best first)
        if result['success']:
            medical_supplies = [
                "medical_kit", "first_aid_kit", "medkit",
                "tourniquet", "antiseptic", "medicine",
                "bandage", "bandages", "gauze",
                "herbs", "medicinal_herbs",
                "cloth", "cloth_strips", "moss"
            ]
            
            # Use first available supply
            for supply in medical_supplies:
                if supply in self.inventory:
                    self.remove_from_inventory(supply)
                    break
        
        if result['success']:
            result['message'] = f"Treated {len(result['wounds_treated'])} wounds and {len(result['infections_cured'])} infections"
        else:
            result['message'] = "Failed to treat injuries"
        
        return result
    
    def process_condition_effects(self, phases_elapsed: int = 1) -> Dict[str, Any]:
        """Process ongoing effects of conditions (bleeding damage, infection spread, etc.)"""
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        
        result = ws.process_condition_effects(self.health, self.conditions, phases_elapsed)
        
        # Apply health loss
        if result['health_loss'] > 0:
            self.update_health(-result['health_loss'], "condition_effects")
        
        # Add new infections
        for condition_id in result['new_infections']:
            self.add_condition("infected")
        
        # Update phase counters
        if self.is_bleeding():
            self.bleeding_phases += phases_elapsed
        if self.is_infected():
            self.infection_phases += phases_elapsed
        
        # Check for death
        if result['fatal']:
            self.status = "dead"
        
        return result
    
    # Limb damage methods
    def apply_limb_wound(self, body_part_name: str, weapon_type: str, damage: int) -> Dict[str, Any]:
        """
        Apply a wound to a specific body part
        
        Args:
            body_part_name: "head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"
            weapon_type: Type of weapon that caused wound
            damage: Damage dealt
            
        Returns:
            Dictionary with wound details
        """
        from .limb_damage_system import get_limb_damage_system, BodyPart
        
        lds = get_limb_damage_system()
        
        # Convert string to BodyPart enum
        body_part_map = {
            "head": BodyPart.HEAD,
            "torso": BodyPart.TORSO,
            "left_arm": BodyPart.LEFT_ARM,
            "right_arm": BodyPart.RIGHT_ARM,
            "left_leg": BodyPart.LEFT_LEG,
            "right_leg": BodyPart.RIGHT_LEG
        }
        body_part = body_part_map.get(body_part_name, BodyPart.TORSO)
        
        # Determine wound type and severity
        wound_type, severity = lds.determine_wound_type(weapon_type, damage, body_part)
        
        # Create wound
        wound = lds.create_wound(body_part, wound_type, severity, weapon_type)
        
        # Add to limb damage state
        self.limb_damage.add_wound(wound)
        
        # Update legacy tracking
        if wound.bleeding_rate > 0:
            self.bleeding_wounds.append(body_part_name)
        
        # Record state change
        self._record_state_change("limb_wound", None, 
                                 f"{body_part_name}:{wound_type}:{severity}")
        
        result = {
            'body_part': body_part_name,
            'wound_type': wound_type,
            'severity': severity,
            'bleeding_rate': wound.bleeding_rate,
            'severed': wound_type == "severed",
            'message': self._generate_wound_message(body_part_name, wound_type, severity)
        }
        
        # Check for immediate death from head trauma
        if body_part == BodyPart.HEAD and severity >= 5:
            self.status = "dead"
            result['fatal'] = True
            result['message'] = f"{self.name} dies instantly from catastrophic head trauma!"
        
        # Check if tribute can still fight
        if wound_type == "severed":
            can_hold, reason = self.limb_damage.can_hold_weapon()
            can_walk, walk_reason = self.limb_damage.can_walk()
            
            if not can_hold:
                self.equipped_weapon = None
                result['message'] += f" {self.name} can no longer hold a weapon ({reason})!"
            
            if not can_walk:
                result['message'] += f" {self.name} cannot walk ({walk_reason})!"
        
        return result
    
    def _generate_wound_message(self, body_part: str, wound_type: str, severity: int) -> str:
        """Generate descriptive message for wound"""
        part_display = body_part.replace('_', ' ')
        
        if wound_type == "severed":
            return f"{self.name}'s {part_display} has been severed!"
        elif wound_type == "broken":
            return f"{self.name}'s {part_display} is broken!"
        elif wound_type == "slash":
            if severity >= 4:
                return f"{self.name} receives a devastating slash to the {part_display}!"
            else:
                return f"{self.name} is slashed on the {part_display}."
        elif wound_type == "stab":
            if severity >= 4:
                return f"{self.name} is stabbed deeply in the {part_display}!"
            else:
                return f"{self.name} is stabbed in the {part_display}."
        elif wound_type in ["skull_fracture", "concussion"]:
            return f"{self.name} suffers a serious head injury!"
        else:
            return f"{self.name}'s {part_display} is injured."
    
    def can_hold_weapon(self) -> bool:
        """Check if tribute can hold a weapon"""
        can_hold, _ = self.limb_damage.can_hold_weapon()
        return can_hold
    
    def can_walk_normally(self) -> bool:
        """Check if tribute can walk normally"""
        can_walk, reason = self.limb_damage.can_walk()
        return can_walk and not reason
    
    def get_limb_penalties(self) -> Dict[str, float]:
        """Get skill penalties from limb wounds"""
        return self.limb_damage.get_all_skill_penalties()
    
    def get_effective_combat_skills_with_limbs(self) -> Dict[str, float]:
        """Get skills modified by conditions AND limb wounds"""
        # Start with base skills
        skills = self.skills.copy()
        
        # Apply condition modifiers
        from .weapons_system import get_weapons_system
        ws = get_weapons_system()
        skills = ws._apply_condition_modifiers(skills, self.conditions)
        
        # Apply limb damage penalties
        limb_penalties = self.get_limb_penalties()
        for skill, penalty in limb_penalties.items():
            if skill in skills:
                skills[skill] = max(0.1, skills[skill] * (1 + penalty))
        
        return skills
    
    def process_limb_damage_effects(self, phases_elapsed: int = 1) -> Dict[str, Any]:
        """Process bleeding, infection, and healing for limb wounds"""
        from .limb_damage_system import get_limb_damage_system
        
        lds = get_limb_damage_system()
        result = lds.process_wound_effects(self.limb_damage, phases_elapsed)
        
        # Apply health loss from bleeding
        if result['health_loss'] > 0:
            self.update_health(-result['health_loss'], "limb_bleeding")
        
        # Update tracking
        if self.limb_damage.get_total_bleeding_rate() > 0:
            self.bleeding_phases += phases_elapsed
        
        if self.limb_damage.get_infection_count() > 0:
            self.infection_phases += phases_elapsed
        
        # Check for death
        if result['death_from_bleeding']:
            self.status = "dead"
            result['death_message'] = f"{self.name} bleeds out from their wounds."
        
        if result['death_from_infection']:
            self.status = "dead"
            result['death_message'] = f"{self.name} succumbs to infection."
        
        return result
    
    def treat_limb_wound(self, body_part_name: str, medical_skill: int = None, 
                        medical_supply: str = None) -> Dict[str, Any]:
        """
        Treat a specific limb wound
        
        Args:
            body_part_name: Part to treat
            medical_skill: Healer's medical skill (defaults to self.intelligence)
            medical_supply: Supply used (auto-detects best available if None)
            
        Returns:
            Treatment result
        """
        from .limb_damage_system import get_limb_damage_system, BodyPart
        
        if medical_skill is None:
            medical_skill = self.skills.get("intelligence", 5)
        
        # Auto-detect best available medical supply if not specified
        if medical_supply is None:
            medical_supplies_priority = [
                "medical_kit", "first_aid_kit", "medkit",
                "tourniquet", "belt", "rope",  # Proper tourniquets
                "antiseptic", "medicine",
                "bandage", "bandages", "gauze",
                "herbs", "medicinal_herbs",
                "cloth", "cloth_strips",
                "string", "stick", "sticks", "vine", "wire",  # Improvised tourniquets
                "moss", "leaves"
            ]
            
            medical_supply = None
            for supply in medical_supplies_priority:
                if supply in self.inventory:
                    medical_supply = supply
                    break
            
            if medical_supply is None:
                return {'success': False, 'message': 'No medical supplies available'}
        
        # Convert string to BodyPart enum
        body_part_map = {
            "head": BodyPart.HEAD,
            "torso": BodyPart.TORSO,
            "left_arm": BodyPart.LEFT_ARM,
            "right_arm": BodyPart.RIGHT_ARM,
            "left_leg": BodyPart.LEFT_LEG,
            "right_leg": BodyPart.RIGHT_LEG
        }
        body_part = body_part_map.get(body_part_name, BodyPart.TORSO)
        
        # Get wounds on this body part
        wounds = self.limb_damage.get_wounds_on_part(body_part)
        if not wounds:
            return {'success': False, 'message': f"No wounds on {body_part_name}"}
        
        # Treat most severe wound
        wound = max(wounds, key=lambda w: w.severity)
        
        lds = get_limb_damage_system()
        result = lds.treat_wound(wound, medical_skill, medical_supply)
        
        # Consume medical supply if successful
        if result['success'] and medical_supply in self.inventory:
            self.remove_from_inventory(medical_supply)
        
        return result
    
    def get_limb_status_description(self) -> str:
        """Get description of limb damage status"""
        return self.limb_damage.describe_injuries()
    
    def has_severed_limbs(self) -> bool:
        """Check if any limbs are severed"""
        return len(self.limb_damage.get_severed_limbs()) > 0

    # Decision-making methods (placeholders for behavior engine)
    def make_decision(self, available_actions: List[str], context: Dict[str, Any]) -> str:
        """
        Make a decision based on personality, skills, and current state.
        This is a placeholder that will be replaced by the behavior engine.
        """
        if not available_actions:
            return "wait"

        # Simple decision logic based on current state
        if self.health < 30:
            healing_actions = [a for a in available_actions if "heal" in a.lower() or "rest" in a.lower()]
            if healing_actions:
                return random.choice(healing_actions)

        if self.hunger > 70:
            food_actions = [a for a in available_actions if "food" in a.lower() or "hunt" in a.lower() or "forage" in a.lower()]
            if food_actions:
                return random.choice(food_actions)

        if self.thirst > 70:
            water_actions = [a for a in available_actions if "water" in a.lower() or "drink" in a.lower()]
            if water_actions:
                return random.choice(water_actions)

        # Default to personality-based choice
        if self.personality_traits.get("aggressive", 0.5) > 0.7:
            combat_actions = [a for a in available_actions if "attack" in a.lower() or "fight" in a.lower()]
            if combat_actions:
                return random.choice(combat_actions)

        if self.personality_traits.get("cautious", 0.5) > 0.7:
            safe_actions = [a for a in available_actions if "hide" in a.lower() or "defend" in a.lower()]
            if safe_actions:
                return random.choice(safe_actions)

        # Random choice as fallback
        return random.choice(available_actions)

    def should_attack(self, other_tribute: 'Tribute') -> bool:
        """Decide whether to attack another tribute"""
        if other_tribute.tribute_id in self.alliances:
            return False

        # Risk assessment
        health_advantage = self.health - other_tribute.health
        skill_advantage = (self.skills.get("combat", 5) - other_tribute.skills.get("combat", 5))

        total_advantage = health_advantage + (skill_advantage * 10)

        # Risk tolerance affects decision
        risk_threshold = 20 - (self.risk_tolerance * 40)  # -20 to 20

        return total_advantage > risk_threshold

    def should_flee(self, threat_level: int) -> bool:
        """Decide whether to flee based on threat level and personality"""
        if self.personality_traits.get("cautious", 0.5) > 0.7:
            return threat_level > 30
        elif self.personality_traits.get("aggressive", 0.5) > 0.7:
            return threat_level > 70

        return threat_level > 50

    # Utility methods
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current tribute state"""
        return {
            "id": self.tribute_id,
            "name": self.name,
            "district": self.district,
            "status": self.status,
            "health": self.health,
            "sanity": self.sanity,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "fatigue": self.fatigue,
            "has_shelter": self.has_shelter,
            "has_fire": self.has_fire,
            "inventory": self.inventory,
            "alliances": list(self.alliances),
            "enemies": list(self.enemies),
            "current_goal": self.current_goal
        }

    def apply_natural_decay(self, hours_passed: int = 1):
        """Apply natural stat decay over time"""
        # Hunger increases over time
        self.update_hunger(hours_passed * 5)

        # Thirst increases over time
        self.update_thirst(hours_passed * 7)

        # Fatigue increases slightly
        self.update_fatigue(hours_passed * 2)

        # Sanity decreases if alone and in bad conditions
        if not self.alliances and (self.health < 50 or not self.has_shelter):
            self.update_sanity(-hours_passed * 2)

    def _record_state_change(self, stat_name: str, old_value: Any, new_value: Any, details: Dict = None):
        """Record a state change for tracking"""
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "stat": stat_name,
            "old_value": old_value,
            "new_value": new_value,
            "details": details or {}
        }
        self.decision_history.append(change_record)

        # Keep only last 50 changes
        if len(self.decision_history) > 50:
            self.decision_history = self.decision_history[-50:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert tribute to dictionary for serialization"""
        return {
            "tribute_id": self.tribute_id,
            "name": self.name,
            "district": self.district,
            "health": self.health,
            "sanity": self.sanity,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "fatigue": self.fatigue,
            "skills": self.skills,
            "trait_scores": self.trait_scores,
            "conditions": self.conditions,
            "extremities": self.extremities,
            "dominant_arm": self.dominant_arm,
            "bleeding_wounds": self.bleeding_wounds,
            "infections": self.infections,
            "bleeding_phases": self.bleeding_phases,
            "infection_phases": self.infection_phases,
            "inventory": self.inventory,
            "weapons": self.weapons,
            "food_supplies": self.food_supplies,
            "water_supplies": self.water_supplies,
            "medical_supplies": self.medical_supplies,
            "has_shelter": self.has_shelter,
            "has_fire": self.has_fire,
            "location": self.location,
            "terrain_type": self.terrain_type,
            "relationships": self.relationships,
            "alliances": list(self.alliances),
            "enemies": list(self.enemies),
            "status": self.status,
            "status_effects": self.status_effects,
            "personality_traits": self.personality_traits,
            "current_goal": self.current_goal,
            "risk_tolerance": self.risk_tolerance,
            "social_preference": self.social_preference,
            "decision_history": self.decision_history[-10:]  # Only save last 10 decisions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tribute':
        """Create tribute from dictionary"""
        tribute = cls(data["tribute_id"], {
            "name": data["name"],
            "district": data["district"],
            "skills": data.get("skills", {}),
            "trait_scores": data.get("trait_scores", {}),
            "conditions": data.get("conditions", ["healthy"]),
            "inventory": data.get("inventory", [])
        })

        # Restore state
        tribute.health = data.get("health", 100)
        tribute.sanity = data.get("sanity", 100)
        tribute.hunger = data.get("hunger", 0)
        tribute.thirst = data.get("thirst", 0)
        tribute.fatigue = data.get("fatigue", 0)
        tribute.has_shelter = data.get("has_shelter", False)
        tribute.has_fire = data.get("has_fire", False)
        tribute.location = data.get("location", "arena")
        tribute.terrain_type = data.get("terrain_type", "unknown")
        tribute.relationships = data.get("relationships", {})
        tribute.alliances = set(data.get("alliances", []))
        tribute.enemies = set(data.get("enemies", []))
        tribute.status = data.get("status", "alive")
        tribute.status_effects = data.get("status_effects", [])
        tribute.personality_traits = data.get("personality_traits", tribute._generate_personality())
        tribute.current_goal = data.get("current_goal", "survive")
        tribute.risk_tolerance = data.get("risk_tolerance", tribute._calculate_risk_tolerance())
        tribute.social_preference = data.get("social_preference", tribute._calculate_social_preference())
        tribute.decision_history = data.get("decision_history", [])

        # Restore resource lists
        tribute.weapons = data.get("weapons", [])
        tribute.food_supplies = data.get("food_supplies", 0)
        tribute.water_supplies = data.get("water_supplies", 0)
        tribute.medical_supplies = data.get("medical_supplies", [])

        # Restore extremities and medical data
        tribute.extremities = data.get("extremities", {
            "left_arm": "healthy",
            "right_arm": "healthy", 
            "left_leg": "healthy",
            "right_leg": "healthy",
            "head": "healthy"
        })
        tribute.dominant_arm = data.get("dominant_arm", "right_arm")
        tribute.bleeding_wounds = data.get("bleeding_wounds", [])
        tribute.infections = data.get("infections", [])
        tribute.bleeding_phases = data.get("bleeding_phases", 0)
        tribute.infection_phases = data.get("infection_phases", 0)

        return tribute