from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random
import uuid
import uuid

@dataclass
class Tribute:
    name: str
    skills: Dict[str, int]
    trait_scores: Dict[str, float] = field(default_factory=dict)  # Weighted trait scores from web UI
    conditions: List[str] = field(default_factory=lambda: ["healthy"])  # Current conditions affecting performance
    weapons: List[str] = field(default_factory=lambda: ["Fists"])
    district: int = 1
    gender: str = "male"  # "male" or "female"
    secret_skills: List[str] = field(default_factory=list)  # Hidden personality traits that affect AI behavior
    health: int = 100
    sanity: int = 100
    status: str = 'active'
    kills: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    trust: Dict[str, int] = field(default_factory=dict)
    has_camp: bool = False
    speed: int = 5  # New speed trait, 1-10
    bleeding: str = 'none'  # 'none', 'mild', 'severe', 'fatal'
    infection: bool = False  # Whether bleeding has caused infection
    bleeding_days: int = 0  # Days bleeding has persisted
    total_bleeding_phases: int = 0  # Total phases with any bleeding
    preferred_weapon: str = "Sword"  # Weapon the tribute prefers to use
    target_weapon: Optional[str] = None  # Specific weapon the tribute is actively seeking
    relationships: Dict[str, Dict] = field(default_factory=dict)  # Relationships with other tributes
    # Weapon durability and ammunition
    weapon_durability: Dict[str, int] = field(default_factory=dict)  # Durability for each weapon (0-100)
    ammunition: Dict[str, int] = field(default_factory=dict)  # Ammunition count for ranged weapons
    # Resource management
    food: int = 100  # Food level (0-100, starts at 100)
    water: int = 100  # Water level (0-100, starts at 100)
    shelter: int = 100  # Shelter quality (0-100, starts at 100)
    # Sickness system
    is_sick: bool = False  # Whether the tribute is currently sick
    sickness_type: str = 'none'  # Type of sickness ('none', 'flu', 'infection', 'poisoning', 'dysentery')
    sickness_days: int = 0  # Days the tribute has been sick
    sickness_curable: bool = False  # Whether the sickness can be cured by medicine
    # Ongoing effects from environmental events
    ongoing_effects: List[Dict] = field(default_factory=list)  # Ongoing effects like damage over time
    # Weight and inventory management
    weight: float = 0.0  # Current weight burden (0-100, affects speed and damage)
    max_weight: float = 50.0  # Maximum weight before penalties
    camp_inventory: Dict[str, int] = field(default_factory=dict)  # Items stored at camp
    # Trap system
    traps: List[Dict] = field(default_factory=list)  # List of traps set by this tribute
    # Damage tracking for consolidated messages
    damage_sources: List[Dict] = field(default_factory=list)  # Damage sources for current phase
    # Phase combat tracking for retaliation system
    phase_combatants: List[str] = field(default_factory=list)  # Tributes fought this phase (for retaliation)
    unarmed_combatants: List[str] = field(default_factory=list)  # Unarmed tributes fought this phase
    # Limb and head system for advanced combat
    limbs: Dict[str, str] = field(default_factory=lambda: {'left_arm': 'healthy', 'right_arm': 'healthy', 'left_leg': 'healthy', 'right_leg': 'healthy'})  # Limb status: healthy, injured, disabled
    head: str = 'healthy'  # Head status: healthy, injured
    # Torch system
    has_torch: bool = False  # Whether tribute has a torch
    torch_lit: bool = False  # Whether torch is currently lit
    torch_duration: int = 0  # Phases torch has been lit (max 2)
    # Death timers for starvation/dehydration
    starvation_timer: int = 0  # Phases until death from starvation (starts when food = 0)
    dehydration_timer: int = 0  # Phases until death from dehydration (starts when water = 0)
    # Personality traits (calculated from skills)
    personality: Dict[str, float] = field(default_factory=lambda: {'bravery': 0.5, 'trusting': 0.5, 'risk_taking': 0.5})
    # AI Behavior Tree
    behavior_tree: Optional[object] = None
    # Unique ID for web UI updates
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Unique ID for web UI updates
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def gather_food(self) -> bool:
        """Attempt to gather food. Returns True if successful."""
        from utils.skills import resource_gathering_chance
        
        # Use hunting and survival skills for food gathering
        hunting_skill = self.skills.get('hunting', 5)
        survival_skill = self.skills.get('survival', 5)
        luck_skill = self.skills.get('luck', 5)
        
        # Combine skills for better success chance
        effective_skill = (hunting_skill + survival_skill + luck_skill) / 3
        success_chance = resource_gathering_chance(effective_skill)
        
        if random.random() < success_chance:
            # Gain food based on skills
            base_gain = random.randint(15, 30)
            skill_bonus = int((effective_skill - 5) * 2)  # Bonus based on skill level
            food_gain = base_gain + skill_bonus
            self.food = min(100, self.food + food_gain)
            self.reset_starvation_timer()  # Reset starvation timer when food is obtained
            return True
        return False

    def gather_water(self) -> bool:
        """Attempt to gather water. Returns True if successful."""
        from utils.skills import resource_gathering_chance
        
        # Use survival and endurance skills for water gathering
        survival_skill = self.skills.get('survival', 5)
        endurance_skill = self.skills.get('endurance', 5)
        luck_skill = self.skills.get('luck', 5)
        
        # Combine skills for better success chance
        effective_skill = (survival_skill + endurance_skill + luck_skill) / 3
        success_chance = resource_gathering_chance(effective_skill)
        
        if random.random() < success_chance:
            # Gain water based on skills
            base_gain = random.randint(20, 40)
            skill_bonus = int((effective_skill - 5) * 2)  # Bonus based on skill level
            water_gain = base_gain + skill_bonus
            self.water = min(100, self.water + water_gain)
            self.reset_dehydration_timer()  # Reset dehydration timer when water is obtained
            return True
        return False

    def update_personality(self):
        """Update personality traits based on current skills."""
        intelligence = self.skills.get('intelligence', 5)
        luck = self.skills.get('luck', 5)
        bravery_skill = self.skills.get('strength', 5)  # Use strength as proxy for bravery
        
        # Higher intelligence = more strategic/trusting
        self.personality['trusting'] = min(0.9, intelligence / 10 + 0.3)
        
        # Higher luck = more risk-taking
        self.personality['risk_taking'] = min(0.9, luck / 10 + 0.2)
        
        # Higher strength/bravery = more brave
        self.personality['bravery'] = min(0.9, bravery_skill / 10 + 0.4)

    @property
    def current_weapon(self) -> str:
        """Get the currently equipped weapon (first in weapons list)"""
        return self.weapons[0] if self.weapons else "Fists"

    @current_weapon.setter
    def current_weapon(self, weapon: str):
        """Set the currently equipped weapon by moving it to the front of the weapons list"""
        if weapon in self.weapons:
            # Move the weapon to the front
            self.weapons.remove(weapon)
            self.weapons.insert(0, weapon)
        else:
            # If weapon not in list, add it to the front
            self.weapons.insert(0, weapon)

    def add_weapon(self, weapon: str) -> bool:
        """Add a weapon to the tribute's inventory. Returns True if added, False if already owned."""
        if weapon not in self.weapons:
            self.weapons.append(weapon)
            # Initialize weapon durability
            import json
            with open('data/weapons.json', 'r') as f:
                weapons_data = json.load(f)
            if weapon in weapons_data:
                weapon_stats = weapons_data[weapon]
                self.weapon_durability[weapon] = weapon_stats.get("durability", 100)
                # Initialize ammunition for ranged weapons
                if weapon_stats.get("type") == "ranged" and "ammunition_type" in weapon_stats:
                    ammo_type = weapon_stats["ammunition_type"]
                    max_ammo = weapon_stats.get("max_ammunition", 0)
                    self.ammunition[ammo_type] = self.ammunition.get(ammo_type, 0) + max_ammo
            return True
        return False

    def remove_weapon(self, weapon: str) -> bool:
        """Remove a weapon from the tribute's inventory. Returns True if removed, False if not found."""
        if weapon in self.weapons and weapon != "Fists":
            self.weapons.remove(weapon)
            return True
        return False

    def switch_weapon(self, weapon: str) -> bool:
        """Switch to a different weapon as primary. Returns True if switched, False if weapon not owned."""
        if weapon in self.weapons:
            self.weapons.remove(weapon)
            self.weapons.insert(0, weapon)
            return True
        return False

    def get_weapon_count(self) -> int:
        """Get the number of weapons the tribute owns."""
        return len(self.weapons)

    def use_weapon(self, weapon: str) -> tuple[bool, str]:
        """
        Use a weapon, handling durability and ammunition.
        Returns (success, message) where success indicates if weapon can still be used.
        """
        import json
        with open('data/weapons.json', 'r') as f:
            weapons_data = json.load(f)
        
        if weapon not in weapons_data:
            return False, f"Unknown weapon: {weapon}"
        
        weapon_stats = weapons_data[weapon]
        
        # Check ammunition for ranged weapons
        if weapon_stats.get("type") == "ranged" and "ammunition_type" in weapon_stats:
            ammo_type = weapon_stats["ammunition_type"]
            if self.ammunition.get(ammo_type, 0) <= 0:
                return False, f"No {ammo_type} left for {weapon}"
            self.ammunition[ammo_type] -= 1
        
        # Degrade weapon durability
        degradation_rate = weapon_stats.get("degradation_rate", 0.0)
        if random.random() < degradation_rate:
            current_durability = self.weapon_durability.get(weapon, 100)
            self.weapon_durability[weapon] = max(0, current_durability - random.randint(1, 5))
            
            # Check if weapon breaks
            if self.weapon_durability[weapon] <= 0:
                self.remove_weapon(weapon)
                return False, f"{weapon} broke from overuse!"
        
        return True, ""

    def get_weapon_status(self, weapon: str) -> str:
        """Get status information about a weapon including durability and ammunition."""
        import json
        with open('data/weapons.json', 'r') as f:
            weapons_data = json.load(f)
        
        if weapon not in weapons_data:
            return f"Unknown weapon: {weapon}"
        
        weapon_stats = weapons_data[weapon]
        durability = self.weapon_durability.get(weapon, 100)
        
        status = f"{weapon} (Durability: {durability}%)"
        
        if weapon_stats.get("type") == "ranged" and "ammunition_type" in weapon_stats:
            ammo_type = weapon_stats["ammunition_type"]
            ammo_count = self.ammunition.get(ammo_type, 0)
            status += f" - {ammo_type}: {ammo_count}"
        
        return status

    def set_preferred_weapon(self, weapon: str) -> None:
        """Set the tribute's preferred weapon."""
        self.preferred_weapon = weapon

    def set_target_weapon(self, weapon: Optional[str]) -> None:
        """Set a specific weapon the tribute is actively seeking."""
        self.target_weapon = weapon

    def has_preferred_weapon(self) -> bool:
        """Check if tribute has their preferred weapon."""
        return self.preferred_weapon in self.weapons

    def has_target_weapon(self) -> bool:
        """Check if tribute has their target weapon."""
        return self.target_weapon is not None and self.target_weapon in self.weapons

    def should_seek_weapon(self) -> bool:
        """Determine if tribute should actively seek weapons."""
        # Seek weapons if they don't have their preferred weapon or are seeking a specific target
        return not self.has_preferred_weapon() or self.target_weapon is not None

    def get_best_weapon(self) -> str:
        """Get the best available weapon based on preferences and strength."""
        import json
        with open('data/weapons.json', 'r') as f:
            weapons_data = json.load(f)
        
        # Priority: target weapon > preferred weapon > strength-appropriate weapon > current weapon
        if self.target_weapon is not None and self.target_weapon in self.weapons:
            return self.target_weapon
        elif self.has_preferred_weapon():
            return self.preferred_weapon
        else:
            # Choose weapon based on strength - stronger tributes can handle heavier weapons
            strength = self.skills.get('strength', 5)
            
            # Filter weapons the tribute actually has
            available_weapons = [w for w in self.weapons if w in weapons_data]
            
            if not available_weapons:
                return self.current_weapon
            
            # Score weapons based on strength suitability
            best_weapon = None
            best_score = -1
            
            for weapon in available_weapons:
                weapon_stats = weapons_data[weapon]
                weight = weapon_stats.get('weight', 1)
                damage = weapon_stats.get('damage', 0)
                
                # Score based on how well strength matches weapon weight
                if strength >= weight * 2:  # Much stronger than needed
                    strength_score = 0.8
                elif strength >= weight:  # Adequate strength
                    strength_score = 1.0
                elif strength >= weight * 0.5:  # Can manage but strained
                    strength_score = 0.6
                else:  # Too weak for this weapon
                    strength_score = 0.2
                
                # Also consider damage output
                damage_score = min(damage / 50.0, 1.0)  # Normalize to 0-1
                
                total_score = (strength_score * 0.7) + (damage_score * 0.3)
                
                if total_score > best_score:
                    best_score = total_score
                    best_weapon = weapon
            
            return best_weapon if best_weapon else self.current_weapon

    def auto_equip_best_weapon(self) -> bool:
        """Automatically equip the best weapon based on preferences. Returns True if switched."""
        best_weapon = self.get_best_weapon()
        if best_weapon != self.current_weapon:
            return self.switch_weapon(best_weapon)
        return False

    def add_relationship(self, other_tribute_name: str, relationship_type: str, bias_factor: float = 1.0, description: str = "") -> None:
        """Add or update a relationship with another tribute."""
        self.relationships[other_tribute_name] = {
            "type": relationship_type,
            "bias_factor": bias_factor,
            "description": description
        }

    def get_relationship_bias(self, other_tribute_name: str) -> float:
        """Get the bias factor for interactions with another tribute."""
        if other_tribute_name in self.relationships:
            return self.relationships[other_tribute_name]["bias_factor"]
        return 1.0  # Neutral bias

    def get_relationship_type(self, other_tribute_name: str) -> str:
        """Get the relationship type with another tribute."""
        if other_tribute_name in self.relationships:
            return self.relationships[other_tribute_name]["type"]
        return "neutral"

    def is_ally(self, other_tribute_name: str) -> bool:
        """Check if another tribute is considered an ally."""
        return self.get_relationship_type(other_tribute_name) == "ally"

    def is_enemy(self, other_tribute_name: str) -> bool:
        """Check if another tribute is considered an enemy."""
        return self.get_relationship_type(other_tribute_name) == "enemy"

    def get_relationship_description(self, other_tribute_name: str) -> str:
        """Get the description of the relationship with another tribute."""
        if other_tribute_name in self.relationships:
            return self.relationships[other_tribute_name]["description"]
        return ""

    def apply_resource_decay(self) -> Dict[str, int]:
        """Apply daily resource decay. Returns dict of decay amounts."""
        decay = {'food': 0, 'water': 0, 'shelter': 0, 'sanity': 0}
        
        # Food decay: 12-20 per day, less if they have shelter
        food_decay = random.randint(12, 20)
        if self.shelter > 50:
            food_decay = int(food_decay * 0.7)  # 30% reduction with good shelter
        self.food = max(0, self.food - food_decay)
        decay['food'] = food_decay
        
        # Water decay: 15-25 per day, less if they have shelter
        water_decay = random.randint(15, 25)
        if self.shelter > 50:
            water_decay = int(water_decay * 0.8)  # 20% reduction with good shelter
        self.water = max(0, self.water - water_decay)
        decay['water'] = water_decay
        
        # Shelter decay: 3-8 per day (slower decay)
        shelter_decay = random.randint(3, 8)
        self.shelter = max(0, self.shelter - shelter_decay)
        decay['shelter'] = shelter_decay
        
        # Sanity decay: 5-15 per day, affected by various factors
        sanity_decay = random.randint(5, 15)
        
        # Reduce decay if they have allies (social support)
        if len(self.allies) > 0:
            sanity_decay = int(sanity_decay * 0.7)  # 30% reduction with allies
        
        # Reduce decay if they have good shelter
        if self.shelter > 70:
            sanity_decay = int(sanity_decay * 0.8)  # 20% reduction with excellent shelter
        
        # Increase decay significantly if they lack shelter (exposure, lack of rest)
        if self.shelter <= 20:
            if self.shelter <= 0:
                sanity_decay = int(sanity_decay * 2.0)  # Double decay with no shelter
            else:
                sanity_decay = int(sanity_decay * 1.5)  # 50% increase with poor shelter
        
        # Increase decay if they're injured
        if self.health < 50:
            sanity_decay = int(sanity_decay * 1.3)  # 30% increase when injured
        
        # Increase decay if they're bleeding
        if self.bleeding != 'none':
            sanity_decay = int(sanity_decay * 1.2)  # 20% increase when bleeding
        
        self.sanity = max(0, self.sanity - sanity_decay)
        decay['sanity'] = sanity_decay
        
        # Add sanity damage to tracking system
        if sanity_decay > 0:
            self.add_damage("sanity_decay", sanity_decay, "survival stress")
        
        # Handle death timers
        self._update_death_timers()
        
        return decay

    def _update_death_timers(self):
        """Update death timers based on resource levels."""
        # Start starvation timer when food reaches 0
        if self.food <= 0 and self.starvation_timer == 0:
            self.starvation_timer = 6  # 6 phases until death (about 2 days)
        
        # Start dehydration timer when water reaches 0
        if self.water <= 0 and self.dehydration_timer == 0:
            self.dehydration_timer = 4  # 4 phases until death (about 1.5 days)
        
        # Decrement timers if active
        if self.starvation_timer > 0:
            self.starvation_timer -= 1
            if self.starvation_timer <= 0:
                # Death from starvation
                self.status = 'eliminated'
                self.health = 0
        
        if self.dehydration_timer > 0:
            self.dehydration_timer -= 1
            if self.dehydration_timer <= 0:
                # Death from dehydration
                self.status = 'eliminated'
                self.health = 0

    def reset_starvation_timer(self):
        """Reset starvation timer when food is obtained."""
        self.starvation_timer = 0

    def reset_dehydration_timer(self):
        """Reset dehydration timer when water is obtained."""
        self.dehydration_timer = 0

    def get_performance_modifier(self) -> float:
        """Calculate performance modifier based on current conditions. Returns multiplier (0.1 to 2.0)."""
        modifier = 1.0
        
        # Massive penalty during death timers
        if self.starvation_timer > 0:
            # Performance drops significantly as death approaches
            timer_ratio = self.starvation_timer / 6.0  # Max 6 phases
            modifier *= (0.2 + timer_ratio * 0.3)  # 0.2 to 0.5 multiplier
        
        if self.dehydration_timer > 0:
            # Even worse penalty for dehydration
            timer_ratio = self.dehydration_timer / 4.0  # Max 4 phases
            modifier *= (0.15 + timer_ratio * 0.25)  # 0.15 to 0.4 multiplier
        
        # Penalty for lack of shelter
        if self.shelter <= 0:
            modifier *= 0.7  # 30% reduction without shelter
        elif self.shelter <= 20:
            modifier *= 0.85  # 15% reduction with poor shelter
        
        # Bonus for having allies
        if len(self.allies) > 0:
            ally_bonus = min(len(self.allies) * 0.1, 0.3)  # Up to 30% bonus
            modifier *= (1.0 + ally_bonus)
        
        # Penalty for low health
        if self.health < 30:
            modifier *= 0.8  # 20% reduction when critically injured
        
        # Penalty for bleeding
        if self.bleeding != 'none':
            if self.bleeding == 'mild':
                modifier *= 0.9
            elif self.bleeding == 'severe':
                modifier *= 0.75
            elif self.bleeding == 'fatal':
                modifier *= 0.5
        
        return max(0.1, min(2.0, modifier))  # Clamp between 0.1 and 2.0

    def get_effective_speed(self) -> int:
        """Get effective speed including all performance modifiers."""
        base_speed = self.speed
        modifier = self.get_performance_modifier()
        return max(1, int(base_speed * modifier))

    def improve_shelter(self) -> bool:
        """Attempt to improve shelter. Returns True if successful."""
        from utils.skills import resource_gathering_chance
        
        # Use survival skill for shelter building
        survival_skill = self.skills.get('survival', 5)
        success_chance = resource_gathering_chance(survival_skill, difficulty=1.5)  # Harder task
        
        if random.random() < success_chance:
            # Gain 20-45 shelter quality
            shelter_gain = random.randint(20, 45)
            self.shelter = min(100, self.shelter + shelter_gain)
            return True
        return False

    def is_resource_critical(self, resource: str) -> bool:
        """Check if a resource is at critical levels."""
        level = getattr(self, resource, 100)
        return level < 20  # Critical when below 20

    def get_resource_status(self) -> Dict[str, str]:
        """Get status of all resources."""
        status = {}
        for resource in ['food', 'water', 'shelter']:
            level = getattr(self, resource, 100)
            if level > 80:
                status[resource] = 'abundant'
            elif level > 50:
                status[resource] = 'good'
            elif level > 20:
                status[resource] = 'low'
            else:
                status[resource] = 'critical'
        return status

    def has_protection(self, protection_type: str) -> bool:
        """Check if tribute has protection against a specific hazard."""
        if protection_type == "shelter":
            return self.has_camp
        elif protection_type == "gas_mask":
            # Could be added as sponsor gift later
            return False
        elif protection_type == "net":
            # Could be added as sponsor gift later
            return False
        elif protection_type == "high_ground":
            # Higher chance if they have good shelter (represents being in a defensible position)
            return self.shelter > 60 and random.random() < 0.4  # 40% chance with good shelter
        elif protection_type == "insulated_gloves":
            # Could be added as sponsor gift later
            return False
        elif protection_type == "warm_clothing":
            # Could be added as sponsor gift later
            return False
        elif protection_type == "weapon":
            return len(self.weapons) > 1  # Has more than just fists
        elif protection_type == "distance_from_cornucopia":
            # Could track position later, for now assume some are safe
            return random.random() < 0.3  # 30% chance of being far enough
        return False

    def contract_sickness(self, sickness_type: Optional[str] = None) -> None:
        """Make the tribute sick with a specific or random sickness type."""
        if self.is_sick:
            return  # Already sick
        
        sickness_types = {
            'flu': {'curable': True, 'description': 'a bad flu'},
            'infection': {'curable': True, 'description': 'a severe infection'},
            'poisoning': {'curable': True, 'description': 'food poisoning'},
            'dysentery': {'curable': False, 'description': 'dysentery'},
            'pneumonia': {'curable': False, 'description': 'pneumonia'}
        }
        
        if sickness_type is None:
            sickness_type = random.choice(list(sickness_types.keys()))
        
        sickness_info = sickness_types[sickness_type]
        self.is_sick = True
        self.sickness_type = sickness_type
        self.sickness_days = 0
        self.sickness_curable = sickness_info['curable']

    def progress_sickness(self) -> tuple[str, str]:
        """Progress the sickness and return what happened and the sickness type. Returns (result, sickness_type)."""
        if not self.is_sick:
            return 'none', 'none'
        
        self.sickness_days += 1
        sickness_type = self.sickness_type  # Capture before potential reset
        
        # Different sicknesses have different progression
        if self.sickness_type == 'flu':
            # Flu: 40% chance to recover each day, 10% chance to die after 3+ days
            if random.random() < 0.4:
                self.is_sick = False
                self.sickness_type = 'none'
                self.sickness_days = 0
                self.sickness_curable = False
                return 'recovered', sickness_type
            elif self.sickness_days >= 3 and random.random() < 0.1:
                self.status = 'eliminated'
                self.sanity = 0
                return 'died', sickness_type
                
        elif self.sickness_type == 'infection':
            # Infection: 30% chance to recover each day, 15% chance to die after 2+ days
            if random.random() < 0.3:
                self.is_sick = False
                self.sickness_type = 'none'
                self.sickness_days = 0
                self.sickness_curable = False
                return 'recovered', sickness_type
            elif self.sickness_days >= 2 and random.random() < 0.15:
                self.status = 'eliminated'
                self.sanity = 0
                return 'died', sickness_type
                
        elif self.sickness_type == 'poisoning':
            # Poisoning: 50% chance to recover each day, 5% chance to die after 1+ days
            if random.random() < 0.5:
                self.is_sick = False
                self.sickness_type = 'none'
                self.sickness_days = 0
                self.sickness_curable = False
                return 'recovered', sickness_type
            elif self.sickness_days >= 1 and random.random() < 0.05:
                self.status = 'eliminated'
                self.sanity = 0
                return 'died', sickness_type
                
        elif self.sickness_type == 'dysentery':
            # Dysentery: Incurable, 20% chance to die each day after 1 day
            if self.sickness_days >= 1 and random.random() < 0.2:
                self.status = 'eliminated'
                self.sanity = 0
                return 'died', sickness_type
                
        elif self.sickness_type == 'pneumonia':
            # Pneumonia: Incurable, 25% chance to die each day after 2 days
            if self.sickness_days >= 2 and random.random() < 0.25:
                self.status = 'eliminated'
                self.sanity = 0
                return 'died', sickness_type
        
        return 'persists', sickness_type

    def cure_sickness(self) -> bool:
        """Attempt to cure the tribute's sickness with medicine. Returns True if cured."""
        if not self.is_sick or not self.sickness_curable:
            return False
        
        self.is_sick = False
        self.sickness_type = 'none'
        self.sickness_days = 0
        self.sickness_curable = False
        return True

    def calculate_weight(self) -> float:
        """Calculate current weight based on inventory and supplies."""
        weight = 0.0
        
        # Weight from weapons (each weapon adds weight)
        weapon_weights = {
            'Fists': 0, 'Stick': 1, 'Rock': 2, 'Knife': 1, 'Sword': 3, 'Axe': 4,
            'Mace': 4, 'Spear': 3, 'Staff': 2, 'Club': 3, 'Bow': 2, 'Crossbow': 4,
            'Throwing Star': 0.5, 'Whip': 1, 'Dagger': 1
        }
        for weapon in self.weapons:
            weight += weapon_weights.get(weapon, 2)
        
        # Weight from supplies (food and water add minimal weight)
        weight += (self.food / 100.0) * 2  # Food adds up to 2 weight units
        weight += (self.water / 100.0) * 1  # Water adds up to 1 weight unit
        
        # Weight from ammunition
        for ammo_count in self.ammunition.values():
            weight += ammo_count * 0.1
        
        self.weight = weight
        return weight

    def is_overweight(self) -> bool:
        """Check if tribute is carrying too much weight."""
        return self.calculate_weight() > self.max_weight

    def get_speed_penalty(self) -> float:
        """Get speed penalty from weight (0-1 multiplier)."""
        if not self.is_overweight():
            return 1.0
        weight_ratio = self.weight / self.max_weight
        return max(0.5, 1.0 - (weight_ratio - 1.0) * 0.5)  # Min 50% speed

    def get_damage_penalty(self) -> float:
        """Get damage penalty from weight (0-1 multiplier)."""
        if not self.is_overweight():
            return 1.0
        weight_ratio = self.weight / self.max_weight
        return max(0.7, 1.0 - (weight_ratio - 1.0) * 0.3)  # Min 70% damage

    def store_at_camp(self, item_type: str, amount: int = 1) -> bool:
        """Store items at camp to reduce weight. Returns success."""
        if not self.has_camp:
            return False
        
        # Can only store food and water at camp
        if item_type not in ['food', 'water']:
            return False
        
        if item_type == 'food' and self.food >= amount:
            self.food -= amount
            self.camp_inventory[item_type] = self.camp_inventory.get(item_type, 0) + amount
            return True
        elif item_type == 'water' and self.water >= amount:
            self.water -= amount
            self.camp_inventory[item_type] = self.camp_inventory.get(item_type, 0) + amount
            return True
        
        return False

    def retrieve_from_camp(self, item_type: str, amount: int = 1) -> bool:
        """Retrieve items from camp. Returns success."""
        if not self.has_camp:
            return False
        
        if self.camp_inventory.get(item_type, 0) >= amount:
            self.camp_inventory[item_type] -= amount
            if item_type == 'food':
                self.food = min(100, self.food + amount)
            elif item_type == 'water':
                self.water = min(100, self.water + amount)
            return True
        
        return False

    def set_trap(self, trap_type: str = "basic", location: str = "general") -> bool:
        """Set a trap. Returns True if successful."""
        # Check if tribute has materials to make a trap
        if self.calculate_weight() > self.max_weight * 0.9:
            return False  # Too burdened to set traps
        
        # Different trap types with different requirements
        trap_requirements = {
            "basic": {"materials": 5, "skill_required": 3},
            "pit": {"materials": 15, "skill_required": 5},
            "spear": {"materials": 10, "skill_required": 4},
            "net": {"materials": 8, "skill_required": 4}
        }
        
        if trap_type not in trap_requirements:
            trap_type = "basic"
        
        req = trap_requirements[trap_type]
        
        # Check survival skill
        survival_skill = self.skills.get('survival', 5)
        if survival_skill < req["skill_required"]:
            return False
        
        # Create trap
        trap = {
            "type": trap_type,
            "location": location,
            "setter": self.name,
            "durability": random.randint(1, 3),  # How many times it can trigger
            "damage": random.randint(10, 30) if trap_type == "basic" else 
                     random.randint(20, 50) if trap_type == "pit" else
                     random.randint(30, 60) if trap_type == "spear" else
                     random.randint(5, 20),  # Net traps immobilize rather than damage
            "effect": "damage" if trap_type != "net" else "immobilize",
            "created_day": 0  # Will be set when trap is placed
        }
        
        self.traps.append(trap)
        return True

    def trigger_trap(self, trap: Dict) -> Dict:
        """Trigger a trap and return the effect. Returns trap effect dict."""
        trap["durability"] -= 1
        
        effect = {
            "damage": trap["damage"],
            "effect": trap["effect"],
            "trap_type": trap["type"],
            "setter": trap["setter"]
        }
        
        # Remove trap if durability is exhausted
        if trap["durability"] <= 0:
            if trap in self.traps:
                self.traps.remove(trap)
        
        return effect

    def add_damage(self, source: str, amount: int, description: str = ""):
        """Add damage to the damage sources list for consolidated reporting."""
        self.damage_sources.append({
            "source": source,
            "amount": amount,
            "description": description
        })
        self.health -= amount
        self.health = max(0, self.health)

    def get_total_damage(self) -> int:
        """Get total damage taken this phase."""
        return sum(damage["amount"] for damage in self.damage_sources)

    def display_damage_summary(self) -> str:
        """Display consolidated damage summary for this phase."""
        if not self.damage_sources:
            return ""
        
        total_damage = self.get_total_damage()
        
        # Group by source
        source_groups = {}
        for damage in self.damage_sources:
            source = damage["source"]
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(damage)
        
        # Build summary message
        parts = []
        for source, damages in source_groups.items():
            source_total = sum(d["amount"] for d in damages)
            if len(damages) == 1:
                desc = damages[0]["description"]
                if desc:
                    parts.append(f"{source_total} damage from {desc}")
                else:
                    parts.append(f"{source_total} damage from {source}")
            else:
                parts.append(f"{source_total} damage from {source} ({len(damages)} instances)")
        
        summary = f"{self.name} took {total_damage} total damage this phase ({', '.join(parts)})"
        
        # Clear damage sources for next phase
        self.damage_sources.clear()
        
        return summary

    def apply_trap_effect(self, trap: Dict, setter_name: str) -> str:
        """Apply trap effect to this tribute and return description string."""
        damage = trap["damage"]
        effect = trap["effect"]
        trap_type = trap["type"]
        
        # Add damage to tracking system
        self.add_damage("trap", damage, f"{setter_name}'s {trap_type} trap")
        
        # Apply special effects
        if effect == "immobilize":
            # Immobilize effect - reduce movement for next turn
            sanity_damage = random.randint(5, 15)
            self.sanity -= sanity_damage
            self.sanity = max(0, self.sanity)
            self.add_damage("trap_fear", sanity_damage, f"{setter_name}'s {trap_type} trap (fear)")
            
            if self.health <= 0:
                self.status = 'eliminated'
                return f"{self.name} triggers {setter_name}'s {trap_type} trap and dies from the immobilization!"
        
        elif effect == "damage":
            # Standard damage
            sanity_damage = random.randint(3, 8)
            self.sanity -= sanity_damage
            self.sanity = max(0, self.sanity)
            self.add_damage("trap_pain", sanity_damage, f"{setter_name}'s {trap_type} trap (pain)")
            
            if self.health <= 0:
                self.status = 'eliminated'
                return f"{self.name} triggers {setter_name}'s {trap_type} trap and dies from the injuries!"
        
        # Return brief description for immediate feedback
        if self.health <= 0:
            return f"{self.name} triggers {setter_name}'s {trap_type} trap and dies!"
        else:
            return f"{self.name} triggers {setter_name}'s {trap_type} trap!"

    def raid_camp(self, target_tribute) -> Dict:
        """Attempt to raid another tribute's camp. Returns raid results."""
        if not target_tribute.has_camp:
            return {"success": False, "reason": "no_camp"}
        
        # Check if target is at camp (simplified - assume 30% chance they're home)
        target_at_camp = random.random() < 0.3
        
        if target_at_camp:
            # Combat encounter
            return {"success": False, "reason": "defender_present", "defender": target_tribute}
        
        # Successful raid
        stolen_items = {}
        total_value = 0
        
        # Steal from camp inventory
        for item_type, amount in target_tribute.camp_inventory.items():
            if amount > 0:
                steal_amount = min(amount, random.randint(1, amount // 2 + 1))
                stolen_items[item_type] = steal_amount
                target_tribute.camp_inventory[item_type] -= steal_amount
                total_value += steal_amount * (10 if item_type in ['food', 'water'] else 5)
        
        # Chance to destroy camp
        if random.random() < 0.4:  # 40% chance
            target_tribute.has_camp = False
            target_tribute.camp_inventory.clear()
            return {"success": True, "stolen": stolen_items, "camp_destroyed": True, "value": total_value}
        
        return {"success": True, "stolen": stolen_items, "camp_destroyed": False, "value": total_value}

    def perform_camp_raid(self, target_tribute) -> str:
        """Perform a camp raid and return description string."""
        raid_result = self.raid_camp(target_tribute)
        
        if not raid_result["success"]:
            if raid_result["reason"] == "no_camp":
                return f"{self.name} attempts to raid {target_tribute.name}'s camp but finds no camp to raid."
            elif raid_result["reason"] == "defender_present":
                # This would trigger combat, but for now just return that they encountered the defender
                defender = raid_result["defender"]
                return f"{self.name} attempts to raid {target_tribute.name}'s camp but encounters {defender.name} defending it!"
        
        # Successful raid
        stolen_items = raid_result["stolen"]
        camp_destroyed = raid_result["camp_destroyed"]
        
        if not stolen_items and not camp_destroyed:
            return f"{self.name} raids {target_tribute.name}'s camp but finds nothing of value."
        
        description_parts = [f"{self.name} successfully raids {target_tribute.name}'s camp"]
        
        if stolen_items:
            stolen_list = []
            for item_type, amount in stolen_items.items():
                stolen_list.append(f"{amount} {item_type}")
            description_parts.append(f"stealing {', '.join(stolen_list)}")
        
        if camp_destroyed:
            description_parts.append("and destroys the camp")
        
        return f"{', '.join(description_parts)}!"

    def get_detection_risk_modifier(self) -> float:
        """Calculate detection risk modifier based on shelter and survival skills.
        Returns multiplier for detection chance (lower is better)."""
        modifier = 1.0
        
        # Base penalty for lack of shelter (easier to spot when exposed)
        if self.shelter <= 0:
            modifier *= 1.5  # 50% more likely to be detected without shelter
        elif self.shelter <= 20:
            modifier *= 1.2  # 20% more likely with poor shelter
        
        # Survival skill reduces detection risk
        survival_skill = self.skills.get('survival', 5)
        skill_modifier = max(0.5, 1.0 - (survival_skill - 5) * 0.1)  # 10% reduction per skill point above 5
        modifier *= skill_modifier
        
        # Stealth skill also helps
        stealth_skill = self.skills.get('stealth', 5)
        stealth_modifier = max(0.7, 1.0 - (stealth_skill - 5) * 0.08)  # 8% reduction per skill point above 5
        modifier *= stealth_modifier
        
        # Luck affects detection - unlucky tributes are more likely to be found
        luck_skill = self.skills.get('luck', 5)
        luck_modifier = max(0.8, 1.0 - (luck_skill - 5) * 0.06)  # 6% reduction per luck point above 5, minimum 0.8x
        modifier *= luck_modifier
        
        return modifier

    def get_shelter_status(self) -> str:
        """Get a descriptive status of the tribute's shelter situation."""
        if self.shelter > 80:
            return "well-sheltered"
        elif self.shelter > 50:
            return "adequately sheltered"
        elif self.shelter > 20:
            return "poorly sheltered"
        elif self.shelter > 0:
            return "minimally sheltered"
        else:
            return "exposed (no shelter)"

    def track_combat(self, opponent: 'Tribute'):
        """Track that this tribute fought another tribute this phase."""
        if opponent.name not in self.phase_combatants:
            self.phase_combatants.append(opponent.name)
            # Track if opponent was unarmed during the fight
            if len(opponent.weapons) <= 1:  # Only fists or no weapons
                if opponent.name not in self.unarmed_combatants:
                    self.unarmed_combatants.append(opponent.name)

    def clear_phase_combat_data(self):
        """Clear combat tracking data at the end of each phase."""
        self.phase_combatants.clear()
        self.unarmed_combatants.clear()

    def can_retaliate_against(self, target_name: str) -> bool:
        """Check if this tribute can retaliate against a target they fought unarmed this phase."""
        return target_name in self.unarmed_combatants

    def initialize_behavior_tree(self):
        """Initialize the tribute's behavior tree for AI decision making."""
        if self.behavior_tree is None:
            from ai import TributeBehaviorTree
            self.behavior_tree = TributeBehaviorTree(self)

    def make_decision(self, game_state) -> str:
        """Make a decision using the behavior tree."""
        if self.behavior_tree is None:
            self.initialize_behavior_tree()
        return self.behavior_tree.make_decision(game_state)


# Secret Skills System
# District-based secret skills that affect AI behavior and decision making

DISTRICT_SECRET_SKILLS = {
    1: [  # Career District - Aggressive, team-oriented
        "pack_mentality",      # Prefers forming alliances, loyal to district partners
        "career_pride",        # Highly motivated by victory, less likely to surrender
        "combat_focused",      # Prioritizes combat training and weapon seeking
        "authority_respect",   # Respects strong leaders, follows district hierarchy
        "victory_oriented",    # Will sacrifice for team victory
    ],
    2: [  # Tech/Weapon District - Innovative, strategic
        "tinkerer",            # Can modify weapons, interested in technology
        "strategic_mind",      # Plans ahead, considers long-term consequences
        "resourceful",         # Good at finding and repurposing items
        "analytical",          # Makes decisions based on data/logic
        "problem_solver",      # Good at overcoming environmental challenges
    ],
    3: [  # Luxury/Artisan District - Creative, social
        "charismatic",         # Naturally forms alliances, persuasive
        "artistic",            # Creates distractions, camouflage, or art
        "diplomatic",          # Skilled at negotiation and mediation
        "adaptable",           # Quickly adjusts to changing situations
        "inspirational",       # Can motivate others, boost morale
    ],
    4: [  # Agriculture District - Nurturing, survival-focused
        "survivalist",         # Expert at finding food/water, camping
        "nurturing",           # Takes care of allies, shares resources
        "patient",             # Waits for right opportunities, doesn't rush
        "nature_attuned",      # Good at reading environmental signs
        "steadfast",           # Reliable, keeps promises
    ],
    5: [  # Power/Energy District - Ambitious, power-hungry
        "power_hungry",        # Seeks control and dominance
        "manipulative",        # Uses deception and manipulation
        "intimidating",        # Can scare others into submission
        "opportunistic",       # Takes advantage of others' weaknesses
        "ruthless",            # Will betray allies for personal gain
    ],
    6: [  # Transportation District - Mobile, evasive
        "nomadic",             # Prefers moving around, avoids staying in one place
        "evasive",             # Good at avoiding detection and pursuit
        "scout",               # Explores areas, gathers intelligence
        "fleet_footed",        # Fast and agile in movement
        "independent",         # Prefers solo operation, distrusts groups
    ],
    7: [  # Lumber District - Strong, direct
        "brute_force",         # Relies on physical strength and intimidation
        "straightforward",     # Honest and direct, doesn't scheme
        "protective",          # Defends allies fiercely
        "hardy",               # Resists environmental effects well
        "loyal",               # Once allied, stays loyal
    ],
    8: [  # Textile District - Deceptive, stealthy
        "deceptive",           # Skilled at lying and misdirection
        "stealthy",            # Moves quietly, avoids detection
        "sneaky",              # Good at ambushes and surprise attacks
        "manipulator",         # Influences others subtly
        "two_faced",           # Can switch allegiances easily
    ],
    9: [  # Grain District - Cunning, resourceful
        "cunning",             # Uses intelligence and wit over brute force
        "resource_manager",    # Good at rationing and managing supplies
        "observant",           # Notices details others miss
        "patient_hunter",      # Waits for perfect moment to strike
        "self_preservation",   # Prioritizes personal survival
    ],
    10: [ # Livestock District - Animal-like, instinctive
        "instinctive",         # Relies on gut feelings and instincts
        "animalistic",         # Behaves more like wild animal than human
        "territorial",         # Defends claimed areas aggressively
        "pack_hunter",         # Works well in small coordinated groups
        "survival_focused",    # Pure survival instincts dominate decisions
    ],
    11: [ # Agriculture 2 - Wild, unpredictable
        "wild_card",           # Unpredictable behavior, random decisions
        "rebellious",          # Resists authority and control
        "free_spirit",         # Follows own path, ignores group pressure
        "innovative",          # Thinks outside the box, creative solutions
        "unconventional",      # Does things differently than expected
    ],
    12: [ # Coal Mining District - Tough, resilient
        "resilient",           # Handles pain and hardship well
        "enduring",            # Can continue fighting when others give up
        "stoic",               # Doesn't show emotions, hard to read
        "team_player",         # Works well in established groups
        "determined",          # Once committed to goal, won't give up
    ]
}

def assign_secret_skills(tribute: Tribute, num_skills: int = 2) -> None:
    """
    Assign random secret skills to a tribute based on their district.
    
    Args:
        tribute: The tribute to assign skills to
        num_skills: Number of secret skills to assign (default 2)
    """
    if tribute.district in DISTRICT_SECRET_SKILLS:
        district_skills = DISTRICT_SECRET_SKILLS[tribute.district]
        # Randomly select skills without replacement
        selected_skills = random.sample(district_skills, min(num_skills, len(district_skills)))
        tribute.secret_skills = selected_skills
    else:
        # Fallback for unknown districts
        tribute.secret_skills = ["adaptable", "resourceful"]