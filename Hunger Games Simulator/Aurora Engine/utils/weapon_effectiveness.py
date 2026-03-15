"""
Weapon Effectiveness and Condition Modifiers System

This module handles weapon performance calculations based on tribute strength,
conditions, and weapon characteristics.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class WeaponStats:
    name: str
    type: str
    strength_requirement: int
    base_damage: int
    accuracy_modifier: float
    speed_modifier: float
    strength_multiplier: float

@dataclass
class ConditionModifiers:
    name: str
    modifiers: Dict[str, float]
    raw_data: Dict = None

    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}

class WeaponEffectivenessCalculator:
    """Calculates weapon effectiveness based on tribute stats and conditions"""

    def __init__(self, config_file: str = "../../data/weapons_and_conditions.json"):
        self.config_file = config_file
        self.weapons: Dict[str, WeaponStats] = {}
        self.conditions: Dict[str, ConditionModifiers] = {}
        self._load_config()

    def _load_config(self):
        """Load weapon and condition data from JSON"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

            # Load weapons
            for weapon_id, weapon_data in data.get("weapons", {}).items():
                self.weapons[weapon_id] = WeaponStats(
                    name=weapon_data["name"],
                    type=weapon_data["type"],
                    strength_requirement=weapon_data["strength_requirement"],
                    base_damage=weapon_data["base_damage"],
                    accuracy_modifier=weapon_data["accuracy_modifier"],
                    speed_modifier=weapon_data["speed_modifier"],
                    strength_multiplier=weapon_data["strength_multiplier"]
                )

            # Load conditions
            for condition_id, condition_data in data.get("conditions", {}).items():
                self.conditions[condition_id] = ConditionModifiers(
                    name=condition_data["name"],
                    modifiers=condition_data["modifiers"],
                    raw_data=condition_data
                )

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load weapon/condition config: {e}")
            self._load_fallback_data()

    def _load_fallback_data(self):
        """Fallback weapon and condition data"""
        self.weapons = {
            "fists": WeaponStats("Fists", "melee", 1, 2, 0.9, 1.0, 0.5),
            "knife": WeaponStats("Knife", "melee", 2, 4, 0.8, 0.9, 0.3),
            "sword": WeaponStats("Sword", "melee", 4, 6, 0.7, 0.7, 0.8),
        }
        self.conditions = {
            "healthy": ConditionModifiers("Healthy", {"strength": 0, "agility": 0, "endurance": 0, "speed": 0, "accuracy": 0}, {}),
            "wounded": ConditionModifiers("Wounded", {"strength": -0.3, "agility": -0.3, "endurance": -0.4, "speed": -0.3, "accuracy": -0.2}, {}),
        }

    def calculate_weapon_effectiveness(self, tribute, weapon_id: str) -> Dict[str, float]:
        """
        Calculate weapon effectiveness for a tribute with a specific weapon

        Args:
            tribute: Tribute object with trait_scores and conditions
            weapon_id: ID of the weapon to calculate for

        Returns:
            Dict with effectiveness metrics: damage, accuracy, speed
        """
        if weapon_id not in self.weapons:
            return {"damage": 1.0, "accuracy": 0.5, "speed": 0.5}

        weapon = self.weapons[weapon_id]

        # Get tribute's strength trait score
        strength_score = tribute.trait_scores.get('strength', tribute.skills.get('strength', 5) * 1.0)
        agility_score = tribute.trait_scores.get('agility', tribute.skills.get('agility', 5) * 1.0)
        endurance_score = tribute.trait_scores.get('endurance', tribute.skills.get('endurance', 5) * 1.0)

        # Calculate strength penalty/bonus
        strength_diff = strength_score - weapon.strength_requirement
        strength_modifier = 1.0 + (strength_diff * weapon.strength_multiplier * 0.1)

        # Apply condition modifiers
        condition_modifier = self._calculate_condition_modifier(tribute.conditions)

        # Calculate final effectiveness
        damage = weapon.base_damage * strength_modifier * (1.0 + condition_modifier.get("strength", 0))
        accuracy = weapon.accuracy_modifier * (1.0 + condition_modifier.get("accuracy", 0)) * (agility_score / 10.0)
        speed = weapon.speed_modifier * (1.0 + condition_modifier.get("speed", 0)) * (agility_score / 10.0) * (endurance_score / 10.0)

        # Clamp values to reasonable ranges
        damage = max(0.1, min(20.0, damage))
        accuracy = max(0.1, min(1.0, accuracy))
        speed = max(0.1, min(2.0, speed))

        return {
            "damage": damage,
            "accuracy": accuracy,
            "speed": speed,
            "strength_penalty": max(0, weapon.strength_requirement - strength_score) * 0.1
        }

    def _calculate_condition_modifier(self, conditions: List[str]) -> Dict[str, float]:
        """Calculate total modifier from all active conditions"""
        total_modifiers = {
            "strength": 0.0,
            "agility": 0.0,
            "endurance": 0.0,
            "speed": 0.0,
            "accuracy": 0.0
        }

        for condition_id in conditions:
            if condition_id in self.conditions:
                condition_mods = self.conditions[condition_id].modifiers
                for stat, modifier in condition_mods.items():
                    total_modifiers[stat] += modifier

        return total_modifiers

    def get_weapon_info(self, weapon_id: str) -> Optional[WeaponStats]:
        """Get weapon information"""
        return self.weapons.get(weapon_id)

    def get_condition_info(self, condition_id: str) -> Optional[ConditionModifiers]:
        """Get condition information"""
        return self.conditions.get(condition_id)

    def get_best_weapon_for_tribute(self, tribute) -> str:
        """Find the best weapon for a tribute based on their stats"""
        best_weapon = "fists"
        best_score = 0

        for weapon_id, weapon in self.weapons.items():
            effectiveness = self.calculate_weapon_effectiveness(tribute, weapon_id)
            # Score based on damage + accuracy + speed
            score = effectiveness["damage"] * 0.5 + effectiveness["accuracy"] * 0.3 + effectiveness["speed"] * 0.2
            if score > best_score:
                best_score = score
                best_weapon = weapon_id

        return best_weapon

    def get_weapon_effectiveness_score(self, tribute, weapon_id: str) -> float:
        """
        Get an overall effectiveness score for a weapon (0.0 to 1.0)

        Args:
            tribute: Tribute object
            weapon_id: ID of the weapon

        Returns:
            Float effectiveness score
        """
        effectiveness = self.calculate_weapon_effectiveness(tribute, weapon_id)

        # Combine metrics into overall score (weighted average)
        # Damage is most important, then accuracy, then speed
        score = (effectiveness["damage"] * 0.5 +
                effectiveness["accuracy"] * 0.3 +
                effectiveness["speed"] * 0.2)

        # Normalize to 0-1 range (assuming max damage ~10, accuracy 1.0, speed 2.0)
        return min(1.0, score / 5.0)