# Behavior Engine : Nemesis : NemesisBehaviorEngine.py
#!/usr/bin/env python
"""Nemesis Behavior Engine for managing tribute decision-making in the Hunger Games Simulator.

This engine handles all tribute AI decisions including:
- Combat and weapon selection
- Resource gathering and management
- Medical treatment and bleeding management
- Social interactions and alliances
- Strategic positioning and survival tactics

Decisions are based on:
- Skill scores and trait priorities from web UI
- District bonuses and characteristics
- Current health, bleeding, and infection status
- Available resources and weapons
- Environmental factors and terrain
- Social relationships and alliances
"""

import json
import random
import math
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Import weapon effectiveness calculator
try:
    from utils.weapon_effectiveness import WeaponEffectivenessCalculator
except ImportError:
    # Fallback for Aurora Engine context
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
        from weapon_effectiveness import WeaponEffectivenessCalculator
    except ImportError:
        WeaponEffectivenessCalculator = None

class ActionType(Enum):
    """Types of actions tributes can take"""
    GATHER_FOOD = "gather_food"
    GATHER_WATER = "gather_water"
    GATHER_MEDICAL = "gather_medical"
    GATHER_WEAPONS = "gather_weapons"
    TREAT_BLEEDING = "treat_bleeding"
    TREAT_INFECTION = "treat_infection"
    REST = "rest"
    HIDE = "hide"
    MOVE = "move"
    ATTACK = "attack"
    FORM_ALLIANCE = "form_alliance"
    BETRAY_ALLIANCE = "betray_alliance"
    SHARE_SUPPLIES = "share_supplies"  # NEW
    PROTECT_ALLY = "protect_ally"  # NEW
    AVOID = "avoid"  # NEW
    SCAVENGE = "scavenge"
    BUILD_SHELTER = "build_shelter"
    START_FIRE = "start_fire"
    OBSERVE = "observe"

@dataclass
class ActionOption:
    """Represents a potential action with its evaluation score"""
    action_type: ActionType
    target: Optional[str] = None
    location: Optional[str] = None
    priority_score: float = 0.0
    risk_level: float = 0.0
    resource_cost: Dict[str, int] = None
    expected_benefit: float = 0.0
    time_required: int = 1  # in game phases

    def __post_init__(self):
        if self.resource_cost is None:
            self.resource_cost = {}

class NemesisBehaviorEngine:
    """
    Advanced AI engine for tribute decision-making in the Hunger Games.

    Uses multi-factor analysis including:
    - Skill-based trait scores
    - District characteristics and bonuses
    - Medical condition assessment
    - Resource availability and needs
    - Social dynamics and relationships
    - Environmental factors
    """

    def __init__(self, config_file: str = "../../data/weapons_and_conditions.json"):
        self.weapon_calculator = WeaponEffectivenessCalculator(config_file) if WeaponEffectivenessCalculator else None
        self.district_bonuses = self._load_district_bonuses()
        self.action_weights = self._initialize_action_weights()
        
        # Relationship manager integration (injected from game engine)
        self.relationship_manager = None
    
    def set_relationship_manager(self, relationship_manager):
        """
        Inject relationship manager for relationship-aware decision making
        
        Args:
            relationship_manager: RelationshipManager instance
        """
        self.relationship_manager = relationship_manager

    def _load_district_bonuses(self) -> Dict[int, Dict[str, float]]:
        """Load district-specific bonuses from configuration"""
        try:
            with open("../../data/district_bonuses.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default district bonuses if config not found
            return {
                1: {"strength": 1.1, "combat": 1.1, "survival": 0.9},
                2: {"intelligence": 1.1, "agility": 1.1, "combat": 0.9},
                3: {"intelligence": 1.2, "survival": 0.9, "strength": 0.9},
                4: {"agility": 1.1, "strength": 1.1, "intelligence": 0.9},
                5: {"intelligence": 1.1, "survival": 1.1, "combat": 0.9},
                6: {"strength": 1.1, "survival": 1.1, "intelligence": 0.9},
                7: {"strength": 1.2, "combat": 1.1, "agility": 0.9},
                8: {"intelligence": 1.1, "agility": 1.1, "strength": 0.9},
                9: {"strength": 1.1, "survival": 1.1, "intelligence": 0.9},
                10: {"agility": 1.1, "combat": 1.1, "survival": 0.9},
                11: {"agility": 1.2, "survival": 1.1, "combat": 0.9},
                12: {"survival": 1.2, "strength": 1.1, "intelligence": 0.9}
            }

    def _initialize_action_weights(self) -> Dict[str, Dict[str, float]]:
        """Initialize weights for different action types based on tribute traits"""
        return {
            "aggressive": {
                ActionType.ATTACK.value: 2.0,
                ActionType.GATHER_WEAPONS.value: 1.5,
                ActionType.OBSERVE.value: 1.2,
                ActionType.GATHER_FOOD.value: 0.8,
                ActionType.TREAT_BLEEDING.value: 0.5
            },
            "defensive": {
                ActionType.HIDE.value: 2.0,
                ActionType.BUILD_SHELTER.value: 1.8,
                ActionType.GATHER_MEDICAL.value: 1.5,
                ActionType.TREAT_BLEEDING.value: 1.5,
                ActionType.ATTACK.value: 0.3
            },
            "survivalist": {
                ActionType.GATHER_FOOD.value: 2.0,
                ActionType.GATHER_WATER.value: 2.0,
                ActionType.SCAVENGE.value: 1.8,
                ActionType.BUILD_SHELTER.value: 1.5,
                ActionType.START_FIRE.value: 1.2
            },
            "social": {
                ActionType.FORM_ALLIANCE.value: 2.0,
                ActionType.OBSERVE.value: 1.5,
                ActionType.GATHER_FOOD.value: 1.2,
                ActionType.ATTACK.value: 0.5
            },
            "medical": {
                ActionType.TREAT_BLEEDING.value: 2.5,
                ActionType.TREAT_INFECTION.value: 2.5,
                ActionType.GATHER_MEDICAL.value: 2.0,
                ActionType.REST.value: 1.5,
                ActionType.ATTACK.value: 0.2
            }
        }

    def make_decision(self, tribute, game_state: Dict[str, Any]) -> ActionOption:
        """
        Main decision-making method for a tribute.

        Args:
            tribute: Tribute object with current state
            game_state: Current game state including other tributes, events, etc.

        Returns:
            ActionOption: The chosen action with all evaluation details
        """
        # Generate all possible action options
        action_options = self._generate_action_options(tribute, game_state)

        # Evaluate each option based on tribute's current state and personality
        evaluated_options = []
        for option in action_options:
            score = self._evaluate_action_option(tribute, option, game_state)
            option.priority_score = score
            evaluated_options.append(option)

        # Sort by priority score and select best option
        evaluated_options.sort(key=lambda x: x.priority_score, reverse=True)

        # Add some randomness to prevent predictable behavior
        if len(evaluated_options) > 1:
            # 70% chance to pick top choice, 20% second, 10% third
            weights = [0.7, 0.2, 0.1] + [0.0] * (len(evaluated_options) - 3)
            chosen_option = random.choices(evaluated_options, weights=weights[:len(evaluated_options)])[0]
        else:
            chosen_option = evaluated_options[0]

        # Record decision in tribute's history
        tribute.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": chosen_option.action_type.value,
            "score": chosen_option.priority_score,
            "reasoning": self._get_decision_reasoning(tribute, chosen_option)
        })

        return chosen_option

    def _generate_action_options(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate all possible actions the tribute could take"""
        options = []

        # Basic survival actions (always available)
        options.extend(self._generate_survival_actions(tribute, game_state))

        # Medical actions (if needed)
        options.extend(self._generate_medical_actions(tribute, game_state))

        # Combat actions (if weapons available and enemies nearby)
        options.extend(self._generate_combat_actions(tribute, game_state))

        # Social actions (if other tributes nearby)
        options.extend(self._generate_social_actions(tribute, game_state))

        # Strategic actions (movement, hiding, etc.)
        options.extend(self._generate_strategic_actions(tribute, game_state))

        return options

    def _generate_survival_actions(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate basic survival-related actions"""
        actions = []

        # Food gathering
        if tribute.hunger > 30:
            priority = min(1.0, tribute.hunger / 100.0)
            actions.append(ActionOption(
                action_type=ActionType.GATHER_FOOD,
                priority_score=priority,
                risk_level=0.3,
                expected_benefit=20,  # Reduces hunger by ~20
                time_required=2
            ))

        # Water gathering
        if tribute.thirst > 30:
            priority = min(1.0, tribute.thirst / 100.0)
            actions.append(ActionOption(
                action_type=ActionType.GATHER_WATER,
                priority_score=priority,
                risk_level=0.2,
                expected_benefit=25,  # Reduces thirst by ~25
                time_required=1
            ))

        # Rest (if fatigued)
        if tribute.fatigue > 40:
            priority = min(1.0, tribute.fatigue / 100.0)
            actions.append(ActionOption(
                action_type=ActionType.REST,
                priority_score=priority * 0.8,
                risk_level=0.1,
                expected_benefit=30,  # Reduces fatigue by ~30
                time_required=3
            ))

        # Build shelter (if no shelter and night approaching)
        if not tribute.has_shelter and self._is_night_approaching(game_state):
            actions.append(ActionOption(
                action_type=ActionType.BUILD_SHELTER,
                priority_score=0.7,
                risk_level=0.2,
                expected_benefit=50,  # Protection bonus
                time_required=4
            ))

        # Start fire (if cold or for cooking)
        if not tribute.has_fire and (tribute.fatigue > 20 or tribute.hunger > 20):
            actions.append(ActionOption(
                action_type=ActionType.START_FIRE,
                priority_score=0.6,
                risk_level=0.3,
                expected_benefit=15,  # Cooking/heating bonus
                time_required=2
            ))

        return actions

    def _generate_medical_actions(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate medical treatment actions including limb wounds"""
        actions = []

        # Treat bleeding (highest priority for severe bleeding)
        if tribute.bleeding_wounds:
            severity_score = self._calculate_bleeding_severity(tribute)
            priority = severity_score * 2.0  # Bleeding is critical

            # Check if medical supplies are available
            has_supplies = len(tribute.medical_supplies) > 0

            actions.append(ActionOption(
                action_type=ActionType.TREAT_BLEEDING,
                priority_score=priority,
                risk_level=0.1,
                resource_cost={"medical_supplies": 1} if has_supplies else {},
                expected_benefit=severity_score * 40,  # Healing benefit
                time_required=2
            ))

        # Treat infection
        if tribute.infections:
            severity_score = self._calculate_infection_severity(tribute)
            resistance_modifier = self._calculate_infection_resistance(tribute)
            priority = severity_score * 1.5 * (1.0 + resistance_modifier)  # Higher priority for resistant infections

            has_supplies = len(tribute.medical_supplies) > 0
            actions.append(ActionOption(
                action_type=ActionType.TREAT_INFECTION,
                priority_score=priority,
                risk_level=0.1,
                resource_cost={"medical_supplies": 1} if has_supplies else {},
                expected_benefit=severity_score * 30 * (1.0 - resistance_modifier),  # Lower benefit for resistant infections
                time_required=3
            ))
        
        # Treat limb wounds (if limb damage system present)
        if hasattr(tribute, 'limb_damage') and tribute.limb_damage:
            untreated_wounds = tribute.limb_damage.get_untreated_wounds()
            
            for wound in untreated_wounds:
                # Prioritize by wound severity and body part importance
                severity_priority = {
                    'minor': 0.3,
                    'moderate': 0.6,
                    'severe': 0.9,
                    'critical': 1.2
                }.get(wound['severity'], 0.5)
                
                # Head and torso wounds are more critical
                body_part_priority = 1.5 if wound['body_part'] in ['head', 'torso'] else 1.0
                
                # Bleeding and infected wounds need immediate attention
                status_priority = 1.0
                if wound.get('bleeding'):
                    status_priority += 0.5
                if wound.get('infected'):
                    status_priority += 0.3
                
                total_priority = severity_priority * body_part_priority * status_priority
                
                has_supplies = len(tribute.medical_supplies) > 0
                actions.append(ActionOption(
                    action_type=ActionType.TREAT_BLEEDING,  # Reuse TREAT_BLEEDING for limb wounds
                    target=wound['body_part'],  # Store which limb to treat
                    priority_score=total_priority,
                    risk_level=0.15,
                    resource_cost={"medical_supplies": 1} if has_supplies else {},
                    expected_benefit=severity_priority * 35,
                    time_required=2
                ))

        # Gather medical supplies (if low on supplies and injuries present)
        medical_need = (len(tribute.bleeding_wounds) + len(tribute.infections)) > 0
        
        # Also check limb wounds
        if hasattr(tribute, 'limb_damage'):
            medical_need = medical_need or len(tribute.limb_damage.get_untreated_wounds()) > 0
        
        if medical_need and len(tribute.medical_supplies) < 2:
            actions.append(ActionOption(
                action_type=ActionType.GATHER_MEDICAL,
                priority_score=0.8,
                risk_level=0.4,
                expected_benefit=25,  # Medical supply value
                time_required=3
            ))

        return actions

    def _generate_combat_actions(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate combat-related actions"""
        actions = []

        nearby_tributes = self._get_nearby_tributes(tribute, game_state)
        
        # Get high-priority enemies if relationship manager available
        high_priority_enemies = []
        if self.relationship_manager:
            enemies = self.relationship_manager.get_enemies(tribute.tribute_id, min_priority=70.0)
            high_priority_enemies = [enemy_id for enemy_id, _ in enemies]

        for other_tribute in nearby_tributes:
            # Skip allies
            if other_tribute.tribute_id in tribute.alliances:
                continue

            # Calculate combat viability
            combat_score = self._calculate_combat_viability(tribute, other_tribute)
            
            # Boost combat score for high-priority enemies
            priority_boost = 0.0
            is_high_priority_enemy = False
            
            if self.relationship_manager:
                relationship = self.relationship_manager.get_relationship(
                    tribute.tribute_id, other_tribute.tribute_id
                )
                
                if relationship and relationship.is_enemy:
                    # Enemy priority 0-100, convert to 0.0-0.4 boost
                    priority_boost = (relationship.enemy_priority / 100) * 0.4
                    is_high_priority_enemy = relationship.enemy_priority >= 70
            
            # Apply priority boost
            adjusted_score = combat_score + priority_boost

            if adjusted_score > 0.3 or is_high_priority_enemy:  # Lower threshold for high-priority enemies
                # Increase priority and expected benefit for enemies
                priority_multiplier = 1.5 if is_high_priority_enemy else 1.0
                
                actions.append(ActionOption(
                    action_type=ActionType.ATTACK,
                    target=other_tribute.tribute_id,
                    priority_score=adjusted_score * 0.8 * priority_multiplier,
                    risk_level=0.7,  # Combat is risky
                    expected_benefit=adjusted_score * 60 * priority_multiplier,
                    time_required=1
                ))

        # Gather weapons (if poorly armed)
        weapon_score = self._calculate_weapon_score(tribute)
        if weapon_score < 0.5:
            actions.append(ActionOption(
                action_type=ActionType.GATHER_WEAPONS,
                priority_score=(1.0 - weapon_score) * 0.6,
                risk_level=0.5,
                expected_benefit=(1.0 - weapon_score) * 40,
                time_required=3
            ))

        return actions

    def _generate_social_actions(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate social interaction actions based on relationships"""
        actions = []
        
        nearby_tributes = self._get_nearby_tributes(tribute, game_state)
        
        if not self.relationship_manager:
            # Fallback to old behavior if no relationship manager
            return self._generate_social_actions_fallback(tribute, nearby_tributes)
        
        tribute_id = tribute.tribute_id
        
        for other_tribute in nearby_tributes:
            other_id = other_tribute.tribute_id
            
            # Get relationship data
            relationship = self.relationship_manager.get_relationship(tribute_id, other_id)
            if not relationship:
                continue
            
            trust = relationship.trust
            is_allied = relationship.is_alliance
            rel_type = relationship.get_relationship_type()
            
            # --- ALLIANCE FORMATION ---
            # Consider forming alliance with neutral or higher trust tributes
            if not is_allied and trust >= 40:
                # Calculate alliance potential based on trust and mutual benefit
                alliance_score = self._calculate_alliance_potential_with_trust(
                    tribute, other_tribute, trust
                )
                
                if alliance_score > 0.5:
                    actions.append(ActionOption(
                        action_type=ActionType.FORM_ALLIANCE,
                        target=other_id,
                        priority_score=alliance_score * 0.6,
                        risk_level=0.2,
                        expected_benefit=alliance_score * 35,
                        time_required=1
                    ))
            
            # --- BETRAYAL CONSIDERATION ---
            # Consider betraying allies if desperate enough
            if is_allied:
                # Calculate desperation (0-100)
                desperation = self._calculate_desperation(tribute)
                
                # Get betrayal risk from relationship manager
                betrayal_risk = relationship.calculate_betrayal_risk(desperation)
                
                # Only consider if betrayal risk is moderate to high
                if betrayal_risk > 0.4:
                    # Expected benefit from betraying (eliminating competition, taking resources)
                    betrayal_benefit = self._calculate_betrayal_benefit(tribute, other_tribute)
                    
                    actions.append(ActionOption(
                        action_type=ActionType.BETRAY_ALLIANCE,
                        target=other_id,
                        priority_score=betrayal_risk * betrayal_benefit * 0.4,
                        risk_level=0.8,  # High risk
                        expected_benefit=betrayal_benefit * 50,
                        time_required=1
                    ))
            
            # --- COOPERATIVE ACTIONS WITH ALLIES ---
            if is_allied and trust > 60:
                # Share supplies if ally is in need and we have spare
                if self._should_share_with_ally(tribute, other_tribute):
                    actions.append(ActionOption(
                        action_type=ActionType.SHARE_SUPPLIES,
                        target=other_id,
                        priority_score=0.5,
                        risk_level=0.1,
                        expected_benefit=20,  # Trust increase
                        time_required=1
                    ))
                
                # Protect ally if they're in danger
                if other_tribute.health < 40:
                    actions.append(ActionOption(
                        action_type=ActionType.PROTECT_ALLY,
                        target=other_id,
                        priority_score=0.6,
                        risk_level=0.5,
                        expected_benefit=30,  # Trust increase
                        time_required=1
                    ))
            
            # --- AVOID ENEMIES ---
            if trust < 30 or relationship.is_enemy:
                # Calculate avoid priority based on enemy threat level
                avoid_priority = 0.7
                
                if relationship.is_enemy:
                    # Higher priority to avoid more dangerous enemies
                    threat_multiplier = 1.0 + (relationship.enemy_priority / 100)
                    avoid_priority = min(1.0, avoid_priority * threat_multiplier)
                
                actions.append(ActionOption(
                    action_type=ActionType.AVOID,
                    target=other_id,
                    priority_score=avoid_priority,
                    risk_level=0.3,
                    expected_benefit=25 * (relationship.enemy_priority / 50) if relationship.is_enemy else 25,
                    time_required=1
                ))
        
        return actions
    
    def _generate_social_actions_fallback(self, tribute, nearby_tributes) -> List[ActionOption]:
        """Fallback social actions when no relationship manager available"""
        actions = []

        for other_tribute in nearby_tributes:
            # Skip enemies
            if other_tribute.tribute_id in tribute.enemies:
                continue

            # Skip existing allies
            if other_tribute.tribute_id in tribute.alliances:
                continue

            # Calculate alliance potential
            alliance_score = self._calculate_alliance_potential(tribute, other_tribute)

            if alliance_score > 0.4:
                actions.append(ActionOption(
                    action_type=ActionType.FORM_ALLIANCE,
                    target=other_tribute.tribute_id,
                    priority_score=alliance_score * 0.5,
                    risk_level=0.2,
                    expected_benefit=alliance_score * 30,
                    time_required=1
                ))

        return actions
    
    def _calculate_alliance_potential_with_trust(self, tribute, other_tribute, trust: float) -> float:
        """
        Calculate potential for alliance formation based on trust and other factors
        
        Args:
            tribute: The tribute considering alliance
            other_tribute: Potential ally
            trust: Current trust level (0-100)
            
        Returns:
            Alliance potential score (0.0-1.0)
        """
        # Base score from trust (normalized to 0-1)
        trust_score = trust / 100.0
        
        # District partner bonus
        district_bonus = 0.3 if tribute.district == other_tribute.district else 0.0
        
        # Mutual benefit - do we complement each other?
        skill_complement = self._calculate_skill_complement(tribute, other_tribute)
        
        # Shared enemies increase alliance potential
        shared_enemies_bonus = 0.0
        if self.relationship_manager:
            # Check if they have common enemies
            shared_enemies_bonus = 0.15  # Placeholder
        
        # Desperation factor - more desperate = more willing to ally
        desperation = self._calculate_desperation(tribute) / 100.0
        desperation_bonus = desperation * 0.2
        
        total_score = (
            trust_score * 0.4 +
            district_bonus +
            skill_complement * 0.2 +
            shared_enemies_bonus +
            desperation_bonus
        )
        
        return min(1.0, max(0.0, total_score))
    
    def _calculate_desperation(self, tribute) -> float:
        """
        Calculate how desperate a tribute is (0-100)
        Based on health, resources, and situation
        """
        desperation = 0.0
        
        # Health factor (0-40 points)
        if tribute.health < 30:
            desperation += 40
        elif tribute.health < 50:
            desperation += 25
        elif tribute.health < 70:
            desperation += 10
        
        # Resource factor (0-30 points)
        if tribute.hunger > 70:
            desperation += 15
        if tribute.thirst > 70:
            desperation += 15
        
        # Injury factor (0-20 points)
        if hasattr(tribute, 'bleeding_wounds') and tribute.bleeding_wounds:
            desperation += 20
        
        # Isolation factor (0-10 points)
        if not hasattr(tribute, 'alliances') or not tribute.alliances:
            desperation += 10
        
        return min(100.0, desperation)
    
    def _calculate_betrayal_benefit(self, tribute, target) -> float:
        """
        Calculate expected benefit from betraying an ally (0-1)
        
        Considers:
        - Target's resources/inventory
        - Target's threat level
        - Eliminating competition
        """
        benefit = 0.0
        
        # Resource gain (0-0.3)
        if hasattr(target, 'inventory'):
            inventory_value = len(target.inventory) / 10.0  # Normalize
            benefit += min(0.3, inventory_value)
        
        # Threat elimination (0-0.4)
        threat_level = self._calculate_threat_level(target)
        benefit += threat_level * 0.4
        
        # Desperation multiplier
        desperation = self._calculate_desperation(tribute) / 100.0
        benefit = benefit * (1.0 + desperation * 0.5)
        
        return min(1.0, benefit)
    
    def _calculate_threat_level(self, tribute) -> float:
        """Calculate how threatening another tribute is (0-1)"""
        threat = 0.0
        
        # Health factor
        threat += (tribute.health / 100.0) * 0.3
        
        # Skill factor (average of combat skills)
        if hasattr(tribute, 'skills'):
            combat_skills = ['strength', 'agility', 'combat']
            avg_combat = sum(tribute.skills.get(s, 5) for s in combat_skills) / len(combat_skills)
            threat += (avg_combat / 10.0) * 0.4
        
        # Weapon factor
        if hasattr(tribute, 'inventory'):
            has_weapon = any('weapon' in item.lower() or 
                           item in ['Knife', 'Sword', 'Spear', 'Bow', 'Axe']
                           for item in tribute.inventory)
            if has_weapon:
                threat += 0.3
        
        return min(1.0, threat)
    
    def _calculate_skill_complement(self, tribute1, tribute2) -> float:
        """Calculate how well two tributes' skills complement each other (0-1)"""
        if not hasattr(tribute1, 'skills') or not hasattr(tribute2, 'skills'):
            return 0.5
        
        # Check if they have complementary strengths
        skill_types = ['strength', 'agility', 'intelligence', 'survival', 'combat']
        complement_score = 0.0
        
        for skill in skill_types:
            s1 = tribute1.skills.get(skill, 5)
            s2 = tribute2.skills.get(skill, 5)
            
            # High complement if one is strong where other is weak
            diff = abs(s1 - s2)
            if diff > 3:
                complement_score += 0.2
        
        return min(1.0, complement_score)
    
    def _should_share_with_ally(self, tribute, ally) -> bool:
        """Determine if tribute should share supplies with ally"""
        # Only share if we have spare and ally needs it
        if not hasattr(tribute, 'food_supplies') or not hasattr(ally, 'food_supplies'):
            return False
        
        # We have spare food and ally is hungry
        if tribute.food_supplies > 2 and ally.hunger > 60:
            return True
        
        # We have spare water and ally is thirsty
        if hasattr(tribute, 'water_supplies') and tribute.water_supplies > 2 and ally.thirst > 60:
            return True
        
        return False

    def _generate_strategic_actions(self, tribute, game_state: Dict[str, Any]) -> List[ActionOption]:
        """Generate strategic positioning actions"""
        actions = []

        # Hide action (if enemies nearby or low health)
        nearby_enemies = len([t for t in self._get_nearby_tributes(tribute, game_state)
                             if t.tribute_id in tribute.enemies])

        if nearby_enemies > 0 or tribute.health < 50:
            risk_modifier = 0.3 if nearby_enemies > 0 else 0.1
            health_modifier = (100 - tribute.health) / 100.0

            actions.append(ActionOption(
                action_type=ActionType.HIDE,
                priority_score=(risk_modifier + health_modifier) * 0.7,
                risk_level=0.2,
                expected_benefit=25,  # Safety benefit
                time_required=1
            ))

        # Move to better location
        current_location_score = self._evaluate_location_safety(tribute.location, game_state)
        better_locations = self._find_better_locations(tribute, game_state)

        for location, score in better_locations.items():
            if score > current_location_score + 0.2:
                actions.append(ActionOption(
                    action_type=ActionType.MOVE,
                    location=location,
                    priority_score=(score - current_location_score) * 0.6,
                    risk_level=0.4,
                    expected_benefit=(score - current_location_score) * 20,
                    time_required=2
                ))

        # Observe surroundings (intelligence gathering)
        actions.append(ActionOption(
            action_type=ActionType.OBSERVE,
            priority_score=0.3,
            risk_level=0.1,
            expected_benefit=10,  # Information benefit
            time_required=1
        ))

        # Scavenge (general resource gathering)
        if len(tribute.inventory) < 5:  # Arbitrary inventory limit
            actions.append(ActionOption(
                action_type=ActionType.SCAVENGE,
                priority_score=0.4,
                risk_level=0.3,
                expected_benefit=15,
                time_required=2
            ))

        return actions

    def _evaluate_action_option(self, tribute, option: ActionOption, game_state: Dict[str, Any]) -> float:
        """Evaluate an action option based on tribute's traits and current state"""
        base_score = option.priority_score

        # Apply trait-based modifiers
        trait_modifier = self._calculate_trait_modifier(tribute, option.action_type)

        # Apply district bonuses
        district_modifier = self._calculate_district_modifier(tribute, option.action_type)

        # Apply medical condition modifiers
        medical_modifier = self._calculate_medical_modifier(tribute, option.action_type)

        # Apply resource availability modifier
        resource_modifier = self._calculate_resource_modifier(tribute, option)

        # Apply risk tolerance modifier
        risk_modifier = self._calculate_risk_modifier(tribute, option)

        # Apply social context modifier
        social_modifier = self._calculate_social_modifier(tribute, option, game_state)

        # Combine all modifiers
        final_score = (base_score * trait_modifier * district_modifier *
                      medical_modifier * resource_modifier * risk_modifier * social_modifier)

        # Ensure score stays within reasonable bounds
        return max(0.0, min(2.0, final_score))

    def _calculate_trait_modifier(self, tribute, action_type: ActionType) -> float:
        """Calculate how well this action aligns with tribute's trait scores"""
        trait_weights = self._get_trait_weights_for_action(action_type)

        modifier = 1.0
        for trait, weight in trait_weights.items():
            if trait in tribute.trait_scores:
                # Trait scores are 0-100, convert to modifier (0.5 to 1.5)
                trait_modifier = 0.5 + (tribute.trait_scores[trait] / 200.0)
                modifier += (trait_modifier - 1.0) * weight

        return modifier

    def _calculate_district_modifier(self, tribute, action_type: ActionType) -> float:
        """Apply district bonuses to action effectiveness"""
        district = tribute.district
        if district not in self.district_bonuses:
            return 1.0

        bonuses = self.district_bonuses[district]
        trait_map = {
            ActionType.ATTACK: "combat",
            ActionType.GATHER_WEAPONS: "combat",
            ActionType.GATHER_FOOD: "survival",
            ActionType.GATHER_WATER: "survival",
            ActionType.HIDE: "agility",
            ActionType.OBSERVE: "intelligence",
            ActionType.TREAT_BLEEDING: "intelligence",
            ActionType.FORM_ALLIANCE: "intelligence"
        }

        relevant_trait = trait_map.get(action_type)
        if relevant_trait and relevant_trait in bonuses:
            return bonuses[relevant_trait]

        return 1.0

    def _calculate_medical_modifier(self, tribute, action_type: ActionType) -> float:
        """Modify action scores based on medical conditions"""
        modifier = 1.0

        # Bleeding reduces most actions
        if tribute.bleeding_wounds:
            severity = self._calculate_bleeding_severity(tribute)
            if action_type in [ActionType.ATTACK, ActionType.GATHER_FOOD, ActionType.MOVE]:
                modifier *= (1.0 - severity * 0.5)  # Up to 50% reduction for severe bleeding

        # Infections reduce physical actions (now with severity levels)
        if tribute.infections:
            infection_severity = self._calculate_infection_severity(tribute)
            if action_type in [ActionType.ATTACK, ActionType.GATHER_FOOD, ActionType.GATHER_WATER]:
                modifier *= (1.0 - infection_severity * 0.4)  # Up to 40% reduction for severe infection

        # Limb injuries affect specific actions
        limb_penalty = self._calculate_limb_penalty(tribute, action_type)
        modifier *= limb_penalty

        # Low health reduces risky actions
        if tribute.health < 30 and action_type == ActionType.ATTACK:
            modifier *= 0.3

        return modifier

    def _calculate_resource_modifier(self, tribute, option: ActionOption) -> float:
        """Check if tribute has resources needed for action"""
        for resource, amount in option.resource_cost.items():
            if resource == "medical_supplies":
                if len(tribute.medical_supplies) < amount:
                    return 0.1  # Much less likely if no supplies
            elif resource == "food_supplies":
                if tribute.food_supplies < amount:
                    return 0.3
            elif resource == "water_supplies":
                if tribute.water_supplies < amount:
                    return 0.3

        return 1.0

    def _calculate_risk_modifier(self, tribute, option: ActionOption) -> float:
        """Apply tribute's risk tolerance to action evaluation"""
        risk_tolerance = tribute.risk_tolerance  # 0.0 to 1.0

        if option.risk_level <= risk_tolerance:
            return 1.0 + (risk_tolerance - option.risk_level) * 0.5
        else:
            return 1.0 - (option.risk_level - risk_tolerance) * 2.0

    def _calculate_social_modifier(self, tribute, option: ActionOption, game_state: Dict[str, Any]) -> float:
        """Apply social context modifiers"""
        modifier = 1.0

        if option.action_type == ActionType.ATTACK and option.target:
            # Reduce likelihood if target is an ally
            if option.target in tribute.alliances:
                modifier *= 0.1

        elif option.action_type == ActionType.FORM_ALLIANCE and option.target:
            # Increase likelihood if target is an enemy of enemies
            try:
                target_tribute = game_state.get("tributes", {}).get(option.target)
                if target_tribute and hasattr(target_tribute, 'enemies'):
                    target_enemies = target_tribute.enemies
                    common_enemies = set(target_enemies) & tribute.enemies
                    if common_enemies:
                        modifier *= 1.5
            except (AttributeError, TypeError):
                # Handle mock objects or missing attributes
                pass

        return modifier

    # Helper methods for calculations

    def _calculate_bleeding_severity(self, tribute) -> float:
        """Calculate overall bleeding severity (0.0 to 1.0)"""
        if not tribute.bleeding_wounds:
            return 0.0

        severity_map = {"mild": 0.2, "medium": 0.5, "severe": 0.8, "fatal": 1.0}
        max_severity = max(severity_map.get(wound.get("level", "mild"), 0.2)
                          for wound in tribute.bleeding_wounds)

        # Factor in duration
        duration_modifier = min(1.0, tribute.bleeding_phases / 10.0)

        return max_severity * (0.5 + duration_modifier * 0.5)

    def _calculate_infection_severity(self, tribute) -> float:
        """Calculate overall infection severity (0.0 to 1.0)"""
        if not tribute.infections:
            return 0.0

        severity_map = {"mild": 0.2, "medium": 0.5, "severe": 0.8}
        max_severity = max(severity_map.get(infection.get("level", "mild"), 0.2)
                          for infection in tribute.infections)

        # Factor in duration
        duration_modifier = min(1.0, tribute.infection_phases / 10.0)

        return max_severity * (0.5 + duration_modifier * 0.5)

    def _calculate_infection_resistance(self, tribute) -> float:
        """Calculate average medication resistance of infections (0.0 to 1.0)"""
        if not tribute.infections:
            return 0.0

        # Get resistance values from config
        resistance_values = []
        for infection in tribute.infections:
            level = infection.get("level", "mild")
            condition_key = f"infected_{level}"
            if self.weapon_calculator and hasattr(self.weapon_calculator, 'conditions'):
                condition_data = self.weapon_calculator.conditions.get(condition_key)
                if condition_data and hasattr(condition_data, 'raw_data'):
                    resistance = condition_data.raw_data.get("medication_resistance", 0.1)
                    resistance_values.append(resistance)

        return sum(resistance_values) / len(resistance_values) if resistance_values else 0.1

    def _calculate_limb_penalty(self, tribute, action_type: ActionType) -> float:
        """Calculate penalty from limb injuries"""
        penalty = 1.0

        # Arm injuries affect weapon use and gathering
        arm_injuries = sum(1 for status in [tribute.extremities.get("left_arm"), tribute.extremities.get("right_arm")]
                          if status in ["injured", "severed"])

        if arm_injuries > 0:
            if action_type in [ActionType.ATTACK, ActionType.GATHER_WEAPONS, ActionType.GATHER_FOOD]:
                penalty *= (1.0 - arm_injuries * 0.3)

            # Dominant arm injury is worse
            if tribute.extremities.get(tribute.dominant_arm) in ["injured", "severed"]:
                penalty *= 0.7

        # Leg injuries affect movement
        leg_injuries = sum(1 for status in [tribute.extremities.get("left_leg"), tribute.extremities.get("right_leg")]
                          if status in ["injured", "severed"])

        if leg_injuries > 0 and action_type in [ActionType.MOVE, ActionType.GATHER_FOOD, ActionType.GATHER_WATER]:
            penalty *= (1.0 - leg_injuries * 0.4)

        return penalty

    def _calculate_combat_viability(self, tribute, target) -> float:
        """Calculate how favorable combat would be against target using weapons system"""
        # Import weapons system
        try:
            from Engine.weapons_system import get_weapons_system
            weapons_system = get_weapons_system()
        except ImportError:
            # Fallback if import fails
            return self._calculate_combat_viability_fallback(tribute, target)
        
        # Use tribute's effective combat skills (includes limb damage modifiers)
        tribute_combat_skill = tribute.get_effective_combat_skills_with_limbs()
        target_combat_skill = target.get_effective_combat_skills_with_limbs()
        
        # Get equipped weapons or best available
        tribute_weapon_id = tribute.equipped_weapon
        if not tribute_weapon_id and tribute.weapons:
            tribute_weapon_id = weapons_system.get_best_weapon(
                tribute.weapons, 
                tribute.skills.get("strength", 5)
            )
        
        target_weapon_id = target.equipped_weapon
        if not target_weapon_id and target.weapons:
            target_weapon_id = weapons_system.get_best_weapon(
                target.weapons,
                target.skills.get("strength", 5)
            )
        
        # Calculate weapon effectiveness scores
        tribute_weapon_score = 0.2  # Bare hands baseline
        if tribute_weapon_id:
            weapon_data = weapons_system.get_weapon_by_id(tribute_weapon_id)
            if weapon_data:
                tribute_weapon_score = weapon_data["damage_range"][1] / 20.0  # Normalize max damage
        
        target_weapon_score = 0.2
        if target_weapon_id:
            weapon_data = weapons_system.get_weapon_by_id(target_weapon_id)
            if weapon_data:
                target_weapon_score = weapon_data["damage_range"][1] / 20.0
        
        # Factor in health and effective skills
        health_ratio = tribute.health / max(target.health, 1)
        skill_ratio = tribute_combat_skill / max(target_combat_skill, 0.1)
        weapon_ratio = tribute_weapon_score / max(target_weapon_score, 0.1)
        
        # Check for limb disabilities that prevent combat
        if hasattr(tribute, 'limb_damage'):
            if tribute.limb_damage.count_disabled_limbs() >= 2:
                # Severely disabled, combat viability drastically reduced
                return max(0.0, min(0.2, health_ratio * 0.2))
            if not tribute.limb_damage.can_hold_weapon():
                # Can't hold weapon, reduced effectiveness
                weapon_ratio *= 0.3
        
        # Combine factors (weighted toward combat ability and weapons)
        viability = (health_ratio * 0.25 + skill_ratio * 0.35 + weapon_ratio * 0.4)
        
        return max(0.0, min(1.0, viability))
    
    def _calculate_combat_viability_fallback(self, tribute, target) -> float:
        """Fallback combat calculation if weapons system unavailable"""
    def _calculate_combat_viability_fallback(self, tribute, target) -> float:
        """Fallback combat calculation if weapons system unavailable"""
        if not self.weapon_calculator:
            return 0.5

        # Get best weapon effectiveness
        tribute_weapon_score = 0.0
        if tribute.weapons:
            best_weapon = max(tribute.weapons,
                            key=lambda w: self.weapon_calculator.get_weapon_effectiveness_score(tribute, w))
            tribute_weapon_score = self.weapon_calculator.get_weapon_effectiveness_score(tribute, best_weapon)

        target_weapon_score = 0.0
        if target.weapons:
            best_weapon = max(target.weapons,
                            key=lambda w: self.weapon_calculator.get_weapon_effectiveness_score(target, w))
            target_weapon_score = self.weapon_calculator.get_weapon_effectiveness_score(target, best_weapon)

        # Factor in health and skills
        health_ratio = tribute.health / max(target.health, 1)
        skill_ratio = (tribute.skills.get("combat", 5) + tribute.skills.get("strength", 5)) / \
                     (target.skills.get("combat", 5) + target.skills.get("strength", 5))

        weapon_ratio = tribute_weapon_score / max(target_weapon_score, 0.1)

        # Combine factors
        viability = (health_ratio * 0.3 + skill_ratio * 0.3 + weapon_ratio * 0.4)

        return max(0.0, min(1.0, viability))

    def _calculate_weapon_score(self, tribute) -> float:
        """Calculate overall weapon effectiveness score"""
        if not tribute.weapons:
            return 0.1  # Bare hands only

        if not self.weapon_calculator:
            return len(tribute.weapons) * 0.2  # Simple count-based score

        scores = [self.weapon_calculator.get_weapon_effectiveness_score(tribute, weapon)
                 for weapon in tribute.weapons]

        return max(scores) if scores else 0.1

    def _calculate_alliance_potential(self, tribute, target) -> float:
        """Calculate how beneficial an alliance would be"""
        # Base compatibility from skills
        skill_compatibility = 0.0
        for skill in ["strength", "agility", "intelligence", "survival", "combat"]:
            tribute_skill = tribute.skills.get(skill, 5)
            target_skill = target.skills.get(skill, 5)
            # Complementary skills are better than identical
            compatibility = 1.0 - abs(tribute_skill - target_skill) / 20.0
            skill_compatibility += compatibility

        skill_compatibility /= 5.0

        # Health compatibility (injured tributes might seek healthy allies)
        health_diff = abs(tribute.health - target.health) / 100.0
        health_compatibility = 1.0 - health_diff * 0.5

        # District compatibility (similar districts might be more trustworthy)
        district_compatibility = 1.0 if tribute.district == target.district else 0.7

        return (skill_compatibility * 0.5 + health_compatibility * 0.3 + district_compatibility * 0.2)

    def _get_trait_weights_for_action(self, action_type: ActionType) -> Dict[str, float]:
        """Get trait weights that influence this action type"""
        trait_map = {
            ActionType.ATTACK: {"combat": 0.8, "strength": 0.6, "agility": 0.4},
            ActionType.GATHER_FOOD: {"survival": 0.7, "strength": 0.5, "agility": 0.3},
            ActionType.GATHER_WATER: {"survival": 0.8, "intelligence": 0.3},
            ActionType.GATHER_MEDICAL: {"intelligence": 0.6, "survival": 0.5},
            ActionType.TREAT_BLEEDING: {"intelligence": 0.8, "survival": 0.4},
            ActionType.HIDE: {"agility": 0.6, "intelligence": 0.5, "survival": 0.4},
            ActionType.FORM_ALLIANCE: {"intelligence": 0.7, "survival": 0.4},
            ActionType.OBSERVE: {"intelligence": 0.8, "agility": 0.3},
            ActionType.REST: {"survival": 0.5},  # Everyone needs rest
            ActionType.BUILD_SHELTER: {"survival": 0.6, "strength": 0.5, "intelligence": 0.4}
        }

        return trait_map.get(action_type, {})

    def _get_nearby_tributes(self, tribute, game_state: Dict[str, Any]) -> List:
        """Get list of tributes near the current tribute"""
        # This would need to be implemented based on game state structure
        # For now, return all other tributes
        all_tributes = game_state.get("tributes", {})
        return [t for t_id, t in all_tributes.items() if t_id != tribute.tribute_id]

    def _is_night_approaching(self, game_state: Dict[str, Any]) -> bool:
        """Check if night is approaching (simplified)"""
        # This would check game time in a real implementation
        return random.random() < 0.3  # 30% chance for demo

    def _evaluate_location_safety(self, location: str, game_state: Dict[str, Any]) -> float:
        """Evaluate safety of a location (0.0 to 1.0)"""
        # Simplified location safety evaluation
        safety_map = {
            "forest": 0.7,
            "river": 0.6,
            "mountain": 0.8,
            "cornucopia": 0.3,
            "arena_center": 0.4
        }
        return safety_map.get(location, 0.5)

    def _find_better_locations(self, tribute, game_state: Dict[str, Any]) -> Dict[str, float]:
        """Find locations better than current one"""
        current_score = self._evaluate_location_safety(tribute.location, game_state)
        locations = ["forest", "river", "mountain", "arena_center"]

        better_locations = {}
        for loc in locations:
            if loc != tribute.location:
                score = self._evaluate_location_safety(loc, game_state)
                if score > current_score:
                    better_locations[loc] = score

        return better_locations

    def _get_decision_reasoning(self, tribute, option: ActionOption) -> str:
        """Generate human-readable reasoning for the decision"""
        reasons = []

        if option.action_type == ActionType.TREAT_BLEEDING and tribute.bleeding_wounds:
            reasons.append(f"Severe bleeding ({len(tribute.bleeding_wounds)} wounds)")

        if option.action_type == ActionType.GATHER_FOOD and tribute.hunger > 50:
            reasons.append(f"High hunger ({tribute.hunger})")

        if option.action_type == ActionType.ATTACK and option.target:
            reasons.append(f"Favorable combat opportunity against {option.target}")

        if option.action_type == ActionType.HIDE:
            nearby_enemies = len([t for t in tribute.enemies if t in ["nearby_tribute_ids"]])  # Simplified
            if nearby_enemies > 0:
                reasons.append(f"{nearby_enemies} enemies nearby")

        trait_reasons = []
        trait_weights = self._get_trait_weights_for_action(option.action_type)
        for trait, weight in trait_weights.items():
            if trait in tribute.trait_scores and tribute.trait_scores[trait] > 60:
                trait_reasons.append(f"high {trait} score ({tribute.trait_scores[trait]})")

        if trait_reasons:
            reasons.append("Personal strengths: " + ", ".join(trait_reasons))

        return "; ".join(reasons) if reasons else "General strategy"
