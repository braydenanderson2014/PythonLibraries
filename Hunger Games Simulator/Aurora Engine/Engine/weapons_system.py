#!/usr/bin/env python3
"""
Weapons and Injury System for Aurora Engine
Manages weapon stats, combat calculations, injury mechanics, and condition effects
"""

import json
import os
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class WeaponType(Enum):
    """Weapon type classification"""
    MELEE = "melee"
    RANGED = "ranged"
    THROWN = "thrown"


class InjurySeverity(Enum):
    """Injury severity levels"""
    HEALTHY = 0
    BRUISED = 1
    MINOR = 2
    MODERATE = 3
    SEVERE = 4
    CRITICAL = 5


@dataclass
class Weapon:
    """Weapon data structure"""
    name: str
    description: str
    weapon_type: WeaponType
    base_damage: int  # 1-10 base damage
    accuracy_modifier: float  # 0.5-1.0 accuracy multiplier
    speed_modifier: float  # 0.4-1.0 speed multiplier
    strength_multiplier: float  # 0.0-1.0 damage scaling with strength
    instant_kill_chance: float  # 0.0-0.25 chance of instant kill
    strength_requirement: int  # 1-10 minimum strength needed
    
    def can_use(self, strength: int) -> bool:
        """Check if tribute has enough strength to use weapon effectively"""
        return strength >= self.strength_requirement
    
    def calculate_damage(self, attacker_strength: int, attacker_combat: int, 
                        defender_agility: int) -> int:
        """
        Calculate damage dealt by weapon
        
        Args:
            attacker_strength: Attacker's strength skill (1-10)
            attacker_combat: Attacker's combat skill (1-10)
            defender_agility: Defender's agility skill (1-10)
            
        Returns:
            Damage dealt (can be 0 if missed)
        """
        # Base hit chance from combat skill
        hit_chance = 0.4 + (attacker_combat / 10) * 0.5  # 40-90% base
        
        # Apply weapon accuracy modifier
        hit_chance *= self.accuracy_modifier
        
        # Defender's agility reduces hit chance
        hit_chance -= (defender_agility / 10) * 0.2  # Up to -20%
        
        # Clamp hit chance
        hit_chance = max(0.1, min(0.95, hit_chance))
        
        # Roll for hit
        if random.random() > hit_chance:
            return 0  # Miss
        
        # Calculate damage
        damage = self.base_damage
        
        # Apply strength scaling
        if attacker_strength >= self.strength_requirement:
            strength_bonus = (attacker_strength - self.strength_requirement) * self.strength_multiplier
            damage += strength_bonus
        else:
            # Penalty for using weapon too weak
            penalty = (self.strength_requirement - attacker_strength) * 0.5
            damage = max(1, damage - penalty)
        
        # Add combat skill bonus
        damage += attacker_combat * 0.5
        
        # Random variance ±20%
        variance = random.uniform(0.8, 1.2)
        damage = int(damage * variance)
        
        return max(1, damage)
    
    def check_instant_kill(self) -> bool:
        """Roll for instant kill chance"""
        return random.random() < self.instant_kill_chance


@dataclass
class Condition:
    """Medical condition/injury"""
    name: str
    description: str
    severity: InjurySeverity
    modifiers: Dict[str, float]  # skill_name -> modifier (-1.0 to 0.0)
    bleeding: bool = False
    bleeding_level: Optional[str] = None  # mild, medium, severe, fatal
    infection_risk: float = 0.0  # 0.0-1.0 chance of infection
    infection: bool = False
    natural_healing_phases: Optional[int] = None  # Phases to heal naturally
    fatal_if_untreated: bool = False
    death_phases: Optional[int] = None  # Phases until death if untreated
    limb_affected: Optional[str] = None  # left_arm, right_arm, etc.
    
    def apply_modifiers(self, skills: Dict[str, int]) -> Dict[str, float]:
        """
        Apply condition modifiers to tribute skills
        
        Returns:
            Modified skills dict with float values
        """
        modified = {}
        for skill, value in skills.items():
            modifier = self.modifiers.get(skill, 0.0)
            # Apply percentage modifier
            modified[skill] = value * (1.0 + modifier)
        return modified
    
    def get_health_penalty(self) -> int:
        """Get health damage per phase for this condition"""
        if self.bleeding:
            if self.bleeding_level == "fatal":
                return 15
            elif self.bleeding_level == "severe":
                return 10
            elif self.bleeding_level == "medium":
                return 5
            elif self.bleeding_level == "mild":
                return 2
        return 0


class WeaponsSystem:
    """Manages weapons, combat, and injury mechanics"""
    
    def __init__(self, weapons_file: str = None, conditions_file: str = None):
        self.weapons: Dict[str, Weapon] = {}
        self.conditions: Dict[str, Condition] = {}
        
        # Load weapons and conditions data
        if weapons_file:
            self._load_weapons(weapons_file)
        if conditions_file:
            self._load_conditions(conditions_file)
        else:
            # Use embedded data if no file provided
            self._load_default_weapons()
            self._load_default_conditions()
    
    def _load_default_weapons(self):
        """Load default weapon set"""
        weapons_data = {
            "fists": {
                "name": "Fists",
                "description": "Bare hands combat",
                "type": "melee",
                "base_damage": 2,
                "accuracy_modifier": 0.9,
                "speed_modifier": 1.0,
                "strength_multiplier": 0.5,
                "instant_kill_chance": 0.02,
                "strength_requirement": 1
            },
            "knife": {
                "name": "Knife",
                "description": "Sharp bladed weapon",
                "type": "melee",
                "base_damage": 4,
                "accuracy_modifier": 0.8,
                "speed_modifier": 0.9,
                "strength_multiplier": 0.3,
                "instant_kill_chance": 0.08,
                "strength_requirement": 2
            },
            "sword": {
                "name": "Sword",
                "description": "Heavy bladed weapon",
                "type": "melee",
                "base_damage": 6,
                "accuracy_modifier": 0.7,
                "speed_modifier": 0.7,
                "strength_multiplier": 0.8,
                "instant_kill_chance": 0.12,
                "strength_requirement": 4
            },
            "axe": {
                "name": "Axe",
                "description": "Heavy chopping weapon",
                "type": "melee",
                "base_damage": 8,
                "accuracy_modifier": 0.6,
                "speed_modifier": 0.5,
                "strength_multiplier": 1.0,
                "instant_kill_chance": 0.15,
                "strength_requirement": 5
            },
            "spear": {
                "name": "Spear",
                "description": "Long reach weapon",
                "type": "melee",
                "base_damage": 5,
                "accuracy_modifier": 0.75,
                "speed_modifier": 0.8,
                "strength_multiplier": 0.6,
                "instant_kill_chance": 0.10,
                "strength_requirement": 3
            },
            "bow": {
                "name": "Bow",
                "description": "Ranged weapon requiring skill",
                "type": "ranged",
                "base_damage": 4,
                "accuracy_modifier": 0.7,
                "speed_modifier": 0.6,
                "strength_multiplier": 0.4,
                "instant_kill_chance": 0.18,
                "strength_requirement": 3
            },
            "crossbow": {
                "name": "Crossbow",
                "description": "Heavy ranged weapon",
                "type": "ranged",
                "base_damage": 6,
                "accuracy_modifier": 0.8,
                "speed_modifier": 0.4,
                "strength_multiplier": 0.7,
                "instant_kill_chance": 0.22,
                "strength_requirement": 4
            },
            "throwing_knife": {
                "name": "Throwing Knife",
                "description": "Light throwing weapon",
                "type": "thrown",
                "base_damage": 3,
                "accuracy_modifier": 0.6,
                "speed_modifier": 0.8,
                "strength_multiplier": 0.2,
                "instant_kill_chance": 0.06,
                "strength_requirement": 2
            },
            "rock": {
                "name": "Rock",
                "description": "Improvised throwing weapon",
                "type": "thrown",
                "base_damage": 2,
                "accuracy_modifier": 0.5,
                "speed_modifier": 0.9,
                "strength_multiplier": 0.3,
                "instant_kill_chance": 0.01,
                "strength_requirement": 1
            },
            "mace": {
                "name": "Mace",
                "description": "Blunt crushing weapon",
                "type": "melee",
                "base_damage": 7,
                "accuracy_modifier": 0.65,
                "speed_modifier": 0.6,
                "strength_multiplier": 0.9,
                "instant_kill_chance": 0.14,
                "strength_requirement": 5
            },
            "trident": {
                "name": "Trident",
                "description": "Three-pronged spear",
                "type": "melee",
                "base_damage": 6,
                "accuracy_modifier": 0.72,
                "speed_modifier": 0.75,
                "strength_multiplier": 0.7,
                "instant_kill_chance": 0.13,
                "strength_requirement": 4
            },
            "slingshot": {
                "name": "Slingshot",
                "description": "Light ranged weapon",
                "type": "ranged",
                "base_damage": 2,
                "accuracy_modifier": 0.6,
                "speed_modifier": 0.9,
                "strength_multiplier": 0.2,
                "instant_kill_chance": 0.03,
                "strength_requirement": 1
            },
            "blowgun": {
                "name": "Blowgun",
                "description": "Silent poisoned dart weapon",
                "type": "ranged",
                "base_damage": 1,
                "accuracy_modifier": 0.7,
                "speed_modifier": 0.9,
                "strength_multiplier": 0.0,
                "instant_kill_chance": 0.05,
                "strength_requirement": 1
            },
            "club": {
                "name": "Club",
                "description": "Heavy blunt weapon",
                "type": "melee",
                "base_damage": 5,
                "accuracy_modifier": 0.7,
                "speed_modifier": 0.65,
                "strength_multiplier": 0.8,
                "instant_kill_chance": 0.09,
                "strength_requirement": 4
            },
            "machete": {
                "name": "Machete",
                "description": "Heavy chopping blade",
                "type": "melee",
                "base_damage": 5,
                "accuracy_modifier": 0.75,
                "speed_modifier": 0.75,
                "strength_multiplier": 0.6,
                "instant_kill_chance": 0.11,
                "strength_requirement": 3
            }
        }
        
        for weapon_id, data in weapons_data.items():
            weapon_type = WeaponType.MELEE
            if data["type"] == "ranged":
                weapon_type = WeaponType.RANGED
            elif data["type"] == "thrown":
                weapon_type = WeaponType.THROWN
            
            self.weapons[weapon_id] = Weapon(
                name=data["name"],
                description=data["description"],
                weapon_type=weapon_type,
                base_damage=data["base_damage"],
                accuracy_modifier=data["accuracy_modifier"],
                speed_modifier=data["speed_modifier"],
                strength_multiplier=data["strength_multiplier"],
                instant_kill_chance=data["instant_kill_chance"],
                strength_requirement=data["strength_requirement"]
            )
    
    def _load_default_conditions(self):
        """Load default medical conditions"""
        conditions_data = {
            "healthy": {
                "name": "Healthy",
                "description": "No injuries or ailments",
                "severity": 0,
                "modifiers": {},
                "bleeding": False
            },
            "bruised": {
                "name": "Bruised",
                "description": "Minor injuries from combat",
                "severity": 1,
                "modifiers": {
                    "strength": -0.1,
                    "agility": -0.1,
                    "combat": -0.05,
                    "survival": -0.05
                },
                "bleeding": False,
                "natural_healing_phases": 2
            },
            "bleeding_mild": {
                "name": "Mild Bleeding",
                "description": "Minor wound causing slow blood loss",
                "severity": 2,
                "modifiers": {
                    "strength": -0.15,
                    "agility": -0.1,
                    "combat": -0.15,
                    "survival": -0.1
                },
                "bleeding": True,
                "bleeding_level": "mild",
                "infection_risk": 0.2,
                "natural_healing_phases": 3
            },
            "bleeding_medium": {
                "name": "Medium Bleeding",
                "description": "Moderate wound with noticeable blood loss",
                "severity": 3,
                "modifiers": {
                    "strength": -0.3,
                    "agility": -0.25,
                    "combat": -0.3,
                    "survival": -0.2
                },
                "bleeding": True,
                "bleeding_level": "medium",
                "infection_risk": 0.4,
                "natural_healing_phases": 6
            },
            "bleeding_severe": {
                "name": "Severe Bleeding",
                "description": "Major wound causing significant blood loss",
                "severity": 4,
                "modifiers": {
                    "strength": -0.5,
                    "agility": -0.4,
                    "combat": -0.5,
                    "survival": -0.4
                },
                "bleeding": True,
                "bleeding_level": "severe",
                "infection_risk": 0.6,
                "natural_healing_phases": 12,
                "fatal_if_untreated": True
            },
            "bleeding_fatal": {
                "name": "Fatal Bleeding",
                "description": "Life-threatening blood loss requiring immediate treatment",
                "severity": 5,
                "modifiers": {
                    "strength": -0.8,
                    "agility": -0.7,
                    "combat": -0.8,
                    "survival": -0.7
                },
                "bleeding": True,
                "bleeding_level": "fatal",
                "infection_risk": 0.8,
                "fatal_if_untreated": True,
                "death_phases": 3
            },
            "infected": {
                "name": "Infected",
                "description": "Wound has become infected",
                "severity": 3,
                "modifiers": {
                    "strength": -0.3,
                    "agility": -0.2,
                    "combat": -0.3,
                    "intelligence": -0.2,
                    "survival": -0.2
                },
                "bleeding": False,
                "infection": True,
                "fatal_if_untreated": True,
                "death_phases": 8
            },
            "broken_arm": {
                "name": "Broken Arm",
                "description": "Fractured arm bone",
                "severity": 4,
                "modifiers": {
                    "strength": -0.6,
                    "combat": -0.7,
                    "survival": -0.4
                },
                "bleeding": False,
                "natural_healing_phases": 20,
                "limb_affected": "arm"
            },
            "broken_leg": {
                "name": "Broken Leg",
                "description": "Fractured leg bone",
                "severity": 4,
                "modifiers": {
                    "agility": -0.8,
                    "combat": -0.5,
                    "survival": -0.5
                },
                "bleeding": False,
                "natural_healing_phases": 20,
                "limb_affected": "leg"
            },
            "concussion": {
                "name": "Concussion",
                "description": "Head injury affecting coordination",
                "severity": 3,
                "modifiers": {
                    "intelligence": -0.4,
                    "agility": -0.3,
                    "combat": -0.4
                },
                "bleeding": False,
                "natural_healing_phases": 10,
                "limb_affected": "head"
            },
            "poisoned": {
                "name": "Poisoned",
                "description": "Affected by toxins or venom",
                "severity": 4,
                "modifiers": {
                    "strength": -0.5,
                    "agility": -0.5,
                    "combat": -0.6,
                    "survival": -0.3
                },
                "bleeding": False,
                "fatal_if_untreated": True,
                "death_phases": 5
            }
        }
        
        for condition_id, data in conditions_data.items():
            severity = InjurySeverity(data["severity"])
            
            self.conditions[condition_id] = Condition(
                name=data["name"],
                description=data["description"],
                severity=severity,
                modifiers=data.get("modifiers", {}),
                bleeding=data.get("bleeding", False),
                bleeding_level=data.get("bleeding_level"),
                infection_risk=data.get("infection_risk", 0.0),
                infection=data.get("infection", False),
                natural_healing_phases=data.get("natural_healing_phases"),
                fatal_if_untreated=data.get("fatal_if_untreated", False),
                death_phases=data.get("death_phases"),
                limb_affected=data.get("limb_affected")
            )
    
    def get_weapon(self, weapon_id: str) -> Optional[Weapon]:
        """Get weapon by ID"""
        return self.weapons.get(weapon_id)
    
    def get_all_weapons(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all weapons as a dictionary suitable for JSON serialization
        
        Returns:
            Dict mapping weapon_id to weapon data dict
        """
        weapons_dict = {}
        for weapon_id, weapon in self.weapons.items():
            weapons_dict[weapon_id] = {
                "id": weapon_id,
                "name": weapon.name,
                "description": weapon.description,
                "weapon_type": weapon.weapon_type.value,
                "base_damage": weapon.base_damage,
                "accuracy_modifier": weapon.accuracy_modifier,
                "speed_modifier": weapon.speed_modifier,
                "strength_multiplier": weapon.strength_multiplier,
                "instant_kill_chance": weapon.instant_kill_chance,
                "strength_requirement": weapon.strength_requirement
            }
        return weapons_dict
    
    def get_condition(self, condition_id: str) -> Optional[Condition]:
        """Get condition by ID"""
        return self.conditions.get(condition_id)
    
    def get_best_weapon(self, weapons: List[str], strength: int) -> Optional[str]:
        """
        Get the best weapon tribute can use effectively from their inventory
        
        Args:
            weapons: List of weapon IDs tribute has
            strength: Tribute's strength skill
            
        Returns:
            Best weapon ID, or "fists" if none available
        """
        if not weapons:
            return "fists"
        
        usable = []
        for weapon_id in weapons:
            weapon = self.get_weapon(weapon_id)
            if weapon and weapon.can_use(strength):
                usable.append((weapon_id, weapon.base_damage))
        
        if not usable:
            return "fists"  # Too weak to use any weapons
        
        # Return highest damage weapon
        usable.sort(key=lambda x: x[1], reverse=True)
        return usable[0][0]
    
    def calculate_combat(self, attacker_weapon: str, attacker_skills: Dict[str, int],
                        attacker_conditions: List[str], defender_skills: Dict[str, int],
                        defender_conditions: List[str], 
                        target_body_part: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate combat result between two tributes with limb targeting
        
        Args:
            attacker_weapon: Weapon ID
            attacker_skills: Attacker's skills dict
            attacker_conditions: Attacker's conditions list
            defender_skills: Defender's skills dict
            defender_conditions: Defender's conditions list
            target_body_part: Optional specific body part to target
            
        Returns:
            {
                'hit': bool,
                'damage': int,
                'instant_kill': bool,
                'new_condition': Optional[str],
                'body_part_hit': str,  # NEW: which body part was hit
                'description': str
            }
        """
        weapon = self.get_weapon(attacker_weapon)
        if not weapon:
            weapon = self.get_weapon("fists")
        
        # Apply condition modifiers to skills
        attacker_modified = self._apply_condition_modifiers(
            attacker_skills, attacker_conditions
        )
        defender_modified = self._apply_condition_modifiers(
            defender_skills, defender_conditions
        )
        
        # Determine which body part is hit
        from .limb_damage_system import get_limb_damage_system, BodyPart
        lds = get_limb_damage_system()
        
        target_part = None
        if target_body_part:
            # Convert string to BodyPart enum
            body_part_map = {
                "head": BodyPart.HEAD,
                "torso": BodyPart.TORSO,
                "left_arm": BodyPart.LEFT_ARM,
                "right_arm": BodyPart.RIGHT_ARM,
                "left_leg": BodyPart.LEFT_LEG,
                "right_leg": BodyPart.RIGHT_LEG
            }
            target_part = body_part_map.get(target_body_part)
        
        body_part_hit = lds.select_hit_location(target_part)
        
        # Calculate damage
        damage = weapon.calculate_damage(
            attacker_modified.get("strength", 5),
            attacker_modified.get("combat", 5),
            defender_modified.get("agility", 5)
        )
        
        hit = damage > 0
        instant_kill = False
        new_condition = None
        
        if hit:
            # Check for instant kill (especially for head shots)
            instant_kill = weapon.check_instant_kill()
            
            # Head shots have higher instant kill chance
            if body_part_hit == BodyPart.HEAD:
                instant_kill_chance = weapon.instant_kill_chance * 2
                if random.random() < instant_kill_chance:
                    instant_kill = True
            
            if not instant_kill:
                # Determine injury based on damage (legacy condition system)
                new_condition = self._determine_injury(damage, weapon.weapon_type)
        
        # Generate description
        desc = self._generate_combat_description(
            weapon, hit, damage, instant_kill, new_condition, 
            body_part_hit.value if body_part_hit else "torso"
        )
        
        return {
            'hit': hit,
            'damage': damage,
            'instant_kill': instant_kill,
            'new_condition': new_condition,
            'body_part_hit': body_part_hit.value if body_part_hit else "torso",
            'description': desc
        }
    
    def _apply_condition_modifiers(self, skills: Dict[str, int], 
                                   condition_ids: List[str]) -> Dict[str, float]:
        """Apply all active conditions' modifiers to skills"""
        modified = {skill: float(value) for skill, value in skills.items()}
        
        for condition_id in condition_ids:
            condition = self.get_condition(condition_id)
            if condition:
                for skill, modifier in condition.modifiers.items():
                    if skill in modified:
                        modified[skill] *= (1.0 + modifier)
        
        return modified
    
    def _determine_injury(self, damage: int, weapon_type: WeaponType) -> Optional[str]:
        """Determine what injury occurs based on damage dealt"""
        if damage < 3:
            return "bruised"
        elif damage < 5:
            return "bleeding_mild"
        elif damage < 8:
            return "bleeding_medium"
        elif damage < 12:
            return "bleeding_severe"
        else:
            return "bleeding_fatal"
    
    def _generate_combat_description(self, weapon: Weapon, hit: bool, damage: int,
                                    instant_kill: bool, condition: Optional[str],
                                    body_part: str = "torso") -> str:
        """Generate combat description text with body part"""
        body_part_display = body_part.replace('_', ' ')
        
        if not hit:
            return f"The attack with {weapon.name} misses!"
        
        if instant_kill:
            if body_part == "head":
                return f"The {weapon.name} strikes the head, killing instantly!"
            return f"The {weapon.name} strikes a fatal blow to the {body_part_display}!"
        
        if condition:
            condition_obj = self.get_condition(condition)
            if condition_obj:
                return f"The {weapon.name} hits the {body_part_display} for {damage} damage, causing {condition_obj.name}!"
        
        return f"The {weapon.name} hits the {body_part_display} for {damage} damage!"
    
    def process_condition_effects(self, tribute_health: int, conditions: List[str],
                                  phases_elapsed: int = 1) -> Dict[str, Any]:
        """
        Process ongoing effects of conditions (bleeding, infection, etc.)
        
        Returns:
            {
                'health_loss': int,
                'conditions_healed': List[str],
                'new_infections': List[str],
                'fatal': bool,
                'messages': List[str]
            }
        """
        result = {
            'health_loss': 0,
            'conditions_healed': [],
            'new_infections': [],
            'fatal': False,
            'messages': []
        }
        
        for condition_id in conditions:
            condition = self.get_condition(condition_id)
            if not condition:
                continue
            
            # Apply bleeding damage
            if condition.bleeding:
                bleed_damage = condition.get_health_penalty() * phases_elapsed
                result['health_loss'] += bleed_damage
                result['messages'].append(
                    f"{condition.name} causes {bleed_damage} damage"
                )
            
            # Check for infection
            if condition.bleeding and not condition.infection and condition.infection_risk > 0:
                if random.random() < condition.infection_risk:
                    result['new_infections'].append(condition_id)
                    result['messages'].append(
                        f"{condition.name} has become infected!"
                    )
            
            # Check for fatal conditions
            if condition.fatal_if_untreated and condition.death_phases:
                # This would need to track phases since condition started
                pass
            
            # Natural healing
            if condition.natural_healing_phases:
                # This would need to track healing progress
                pass
        
        # Check if health loss is fatal
        if tribute_health - result['health_loss'] <= 0:
            result['fatal'] = True
        
        return result


# Global instance
_weapons_system = None

def get_weapons_system() -> WeaponsSystem:
    """Get or create global weapons system instance"""
    global _weapons_system
    if _weapons_system is None:
        _weapons_system = WeaponsSystem()
    return _weapons_system
