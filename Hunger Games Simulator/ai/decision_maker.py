"""
Enhanced AI Decision Making System for Hunger Games Simulator

This module provides sophisticated AI decision-making capabilities for tributes,
considering factors like threat assessment, resource management, social dynamics,
and strategic planning.
"""

import random
from typing import Dict, List, Optional, Tuple
from tributes.tribute import Tribute

class AIDecisionMaker:
    """
    Advanced AI system for tribute decision making.
    Considers multiple factors: threats, resources, relationships, strategy.
    """

    def __init__(self, tribute: Tribute, game_state):
        self.tribute = tribute
        self.game_state = game_state

    def make_decision(self, context: str, options: List[str]) -> str:
        """
        Make a strategic decision based on current game state and context.

        Args:
            context: The decision context ('combat', 'alliance', 'resource_gathering', etc.)
            options: List of available choices

        Returns:
            The chosen option
        """
        if context == 'combat_engagement':
            return self._decide_combat_engagement(options)
        elif context == 'alliance_formation':
            return self._decide_alliance_formation(options)
        elif context == 'resource_priority':
            return self._decide_resource_priority(options)
        elif context == 'camping_decision':
            return self._decide_camping(options)
        elif context == 'weapon_seeking':
            return self._decide_weapon_seeking(options)
        else:
            # Default to random choice with slight bias toward safer options
            return self._weighted_random_choice(options, self._calculate_safety_weights(options))

    def _decide_combat_engagement(self, options: List[str]) -> str:
        """Decide whether to engage in combat or avoid it."""
        threat_level = self._assess_threat_level()
        resource_status = self._assess_resource_status()
        social_standing = self._assess_social_standing()
        personality = self._get_personality_traits()

        # Calculate engagement probability
        base_engagement = 0.5  # 50% base chance

        # Adjust based on threat level (higher threat = less likely to engage)
        if threat_level == 'high':
            base_engagement -= 0.3
        elif threat_level == 'low':
            base_engagement += 0.2

        # Adjust based on resources (better resources = more confident)
        if resource_status == 'good':
            base_engagement += 0.15
        elif resource_status == 'poor':
            base_engagement -= 0.2

        # Adjust based on social standing (good alliances = more support)
        if social_standing == 'strong':
            base_engagement += 0.1
        elif social_standing == 'weak':
            base_engagement -= 0.15

        # Adjust based on aggression personality trait
        aggression_modifier = personality.get('aggressive', 0.5)
        base_engagement += (aggression_modifier - 0.5) * 0.4  # +/- 0.2 based on aggression

        # Adjust based on risk-taking personality
        risk_taking = personality.get('risk_taking', 0.5)
        base_engagement += (risk_taking - 0.5) * 0.2  # +/- 0.1 based on risk tolerance

        # Ensure probability is within bounds
        engagement_prob = max(0.1, min(0.9, base_engagement))

        # Choose based on calculated probability
        if 'engage' in options and random.random() < engagement_prob:
            return 'engage'
        elif 'avoid' in options:
            return 'avoid'
        else:
            return random.choice(options)

    def _decide_alliance_formation(self, options: List[str]) -> str:
        """Decide whether to form or break alliances."""
        social_standing = self._assess_social_standing()
        threat_level = self._assess_threat_level()
        personality = self._get_personality_traits()

        # Trusting personalities more likely to form alliances
        trust_modifier = personality.get('trusting', 0.5)

        # High threat levels make alliances more attractive
        threat_modifier = 0.5
        if threat_level == 'high':
            threat_modifier = 0.8
        elif threat_level == 'low':
            threat_modifier = 0.3

        # Deceptive personalities more likely to break alliances
        deception_modifier = personality.get('deceptive', 0.3)

        # Loyal personalities less likely to break existing alliances
        loyalty_modifier = personality.get('loyal', 0.5)

        alliance_prob = (trust_modifier + threat_modifier) / 2

        # Adjust for deception (more deceptive = less likely to form genuine alliances)
        alliance_prob = max(0.1, alliance_prob - deception_modifier * 0.3)

        # If already has allies, loyalty affects decision to break
        if social_standing in ['strong', 'moderate'] and 'break_alliance' in options:
            break_prob = deception_modifier * 0.5 - loyalty_modifier * 0.3
            if random.random() < break_prob:
                return 'break_alliance'

        if 'form_alliance' in options and random.random() < alliance_prob:
            return 'form_alliance'
        elif 'decline_alliance' in options:
            return 'decline_alliance'
        else:
            return random.choice(options)

    def _decide_resource_priority(self, options: List[str]) -> str:
        """Decide which resource to prioritize gathering."""
        resource_status = self._assess_resource_status()
        health_status = self._assess_health_status()

        # If health is poor, prioritize medical supplies
        if health_status == 'poor':
            if 'medical' in options:
                return 'medical'

        # If resources are low, prioritize food/water
        if resource_status == 'poor':
            food_options = [opt for opt in options if 'food' in opt or 'water' in opt]
            if food_options:
                return random.choice(food_options)

        # Otherwise, prioritize weapons if not well-armed
        weapon_count = len(self.tribute.weapons)
        if weapon_count < 2 and 'weapon' in options:
            return 'weapon'

        return random.choice(options)

    def _decide_camping(self, options: List[str]) -> str:
        """Decide whether to camp or move around."""
        threat_level = self._assess_threat_level()
        resource_status = self._assess_resource_status()
        shelter_level = self.tribute.shelter

        # If threat level is high and poor shelter, more likely to keep moving
        if threat_level == 'high' and shelter_level < 30:
            if 'move' in options:
                return 'move'

        # If resources are good and has good shelter, more likely to camp
        if resource_status == 'good' and shelter_level > 60:
            if 'camp' in options:
                return 'camp'

        # If shelter is very poor, prioritize finding/building shelter over camping
        if shelter_level < 20 and 'move' in options:
            return 'move'

        return random.choice(options)

    def _decide_weapon_seeking(self, options: List[str]) -> str:
        """Decide weapon-seeking behavior."""
        current_weapons = len(self.tribute.weapons)
        preferred_weapon = self.tribute.preferred_weapon
        has_preferred = preferred_weapon in self.tribute.weapons

        # High priority if no weapons or missing preferred weapon
        if current_weapons == 0 or not has_preferred:
            if 'seek_weapon' in options:
                return 'seek_weapon'

        # Medium priority if only basic weapons
        if current_weapons <= 2 and not any(w in ['Sword', 'Axe', 'Bow', 'Gun'] for w in self.tribute.weapons):
            if 'seek_weapon' in options and random.random() < 0.7:
                return 'seek_weapon'

        return random.choice(options)

    def _assess_threat_level(self) -> str:
        """Assess the current threat level to this tribute."""
        active_count = len(self.game_state.active_tributes)
        day = self.game_state.day

        # Early game: lower threat
        if day <= 3:
            return 'low'

        # Many tributes remaining: high threat
        if active_count > 8:
            return 'medium'

        # Few tributes: very high threat (final battles)
        if active_count <= 3:
            return 'high'

        return 'medium'

    def _assess_resource_status(self) -> str:
        """Assess the tribute's resource situation."""
        food = self.tribute.food
        water = self.tribute.water
        weapons = len(self.tribute.weapons)

        resource_score = (food + water) / 2

        if resource_score > 75 and weapons >= 2:
            return 'good'
        elif resource_score > 40 and weapons >= 1:
            return 'fair'
        else:
            return 'poor'

    def _assess_health_status(self) -> str:
        """Assess the tribute's health situation."""
        health = self.tribute.health
        bleeding = self.tribute.bleeding
        is_sick = self.tribute.is_sick

        if health > 70 and bleeding == 'none' and not is_sick:
            return 'good'
        elif health > 40 and bleeding != 'fatal':
            return 'fair'
        else:
            return 'poor'

    def _assess_social_standing(self) -> str:
        """Assess the tribute's social situation."""
        allies = len(self.tribute.allies)
        trust_score = sum(self.tribute.trust.values()) / max(1, len(self.tribute.trust))

        if allies >= 2 and trust_score > 60:
            return 'strong'
        elif allies >= 1 and trust_score > 30:
            return 'moderate'
        else:
            return 'weak'

    def _get_personality_traits(self) -> Dict[str, float]:
        """Get personality traits based on tribute skills and behavior."""
        # Derive personality from skills
        intelligence = self.tribute.trait_scores.get('intelligence', self.tribute.skills.get('intelligence', 5) * 1.0)
        luck = self.tribute.trait_scores.get('luck', self.tribute.skills.get('luck', 5) * 0.8)

        # Higher intelligence = more strategic/trusting
        trusting = min(0.9, intelligence / 10 + 0.3)

        # Higher luck = more risk-taking
        risk_taking = min(0.9, luck / 10 + 0.2)

        # Apply secret skill modifiers
        skill_modifiers = self._get_secret_skill_modifiers()

        return {
            'trusting': min(0.95, max(0.05, trusting + skill_modifiers.get('trusting', 0))),
            'risk_taking': min(0.95, max(0.05, risk_taking + skill_modifiers.get('risk_taking', 0))),
            'strategic': min(0.95, max(0.05, intelligence / 10 + skill_modifiers.get('strategic', 0))),
            'aggressive': skill_modifiers.get('aggressive', 0.5),
            'loyal': skill_modifiers.get('loyal', 0.5),
            'deceptive': skill_modifiers.get('deceptive', 0.3)
        }

    def _get_secret_skill_modifiers(self) -> Dict[str, float]:
        """Get personality modifiers based on secret skills."""
        modifiers = {
            'trusting': 0.0,
            'risk_taking': 0.0,
            'strategic': 0.0,
            'aggressive': 0.5,
            'loyal': 0.5,
            'deceptive': 0.3
        }

        secret_skills = getattr(self.tribute, 'secret_skills', [])

        for skill in secret_skills:
            if skill == "pack_mentality":
                modifiers['trusting'] += 0.3
                modifiers['loyal'] += 0.4
            elif skill == "career_pride":
                modifiers['aggressive'] += 0.2
                modifiers['loyal'] += 0.2
            elif skill == "combat_focused":
                modifiers['aggressive'] += 0.3
                modifiers['risk_taking'] += 0.2
            elif skill == "authority_respect":
                modifiers['trusting'] += 0.2
                modifiers['loyal'] += 0.3
            elif skill == "victory_oriented":
                modifiers['aggressive'] += 0.1
                modifiers['strategic'] += 0.2
            elif skill == "tinkerer":
                modifiers['strategic'] += 0.3
                modifiers['risk_taking'] += 0.1
            elif skill == "strategic_mind":
                modifiers['strategic'] += 0.4
                modifiers['risk_taking'] -= 0.1
            elif skill == "resourceful":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] += 0.1
            elif skill == "analytical":
                modifiers['strategic'] += 0.3
                modifiers['trusting'] -= 0.1
            elif skill == "problem_solver":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] += 0.1
            elif skill == "charismatic":
                modifiers['trusting'] += 0.4
                modifiers['deceptive'] += 0.1
            elif skill == "artistic":
                modifiers['strategic'] += 0.1
                modifiers['risk_taking'] += 0.2
            elif skill == "diplomatic":
                modifiers['trusting'] += 0.3
                modifiers['deceptive'] -= 0.1
            elif skill == "adaptable":
                modifiers['risk_taking'] += 0.2
                modifiers['strategic'] += 0.1
            elif skill == "inspirational":
                modifiers['trusting'] += 0.2
                modifiers['loyal'] += 0.2
            elif skill == "nurturing":
                modifiers['trusting'] += 0.3
                modifiers['loyal'] += 0.2
            elif skill == "patient":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] -= 0.2
            elif skill == "nature_attuned":
                modifiers['strategic'] += 0.1
                modifiers['risk_taking'] -= 0.1
            elif skill == "steadfast":
                modifiers['loyal'] += 0.3
                modifiers['trusting'] += 0.1
            elif skill == "power_hungry":
                modifiers['aggressive'] += 0.3
                modifiers['deceptive'] += 0.2
                modifiers['loyal'] -= 0.3
            elif skill == "manipulative":
                modifiers['deceptive'] += 0.4
                modifiers['strategic'] += 0.2
                modifiers['trusting'] -= 0.2
            elif skill == "intimidating":
                modifiers['aggressive'] += 0.2
                modifiers['deceptive'] += 0.1
            elif skill == "opportunistic":
                modifiers['risk_taking'] += 0.3
                modifiers['deceptive'] += 0.2
            elif skill == "ruthless":
                modifiers['aggressive'] += 0.4
                modifiers['loyal'] -= 0.4
                modifiers['trusting'] -= 0.3
            elif skill == "nomadic":
                modifiers['risk_taking'] += 0.2
                modifiers['loyal'] -= 0.1
            elif skill == "evasive":
                modifiers['risk_taking'] -= 0.2
                modifiers['strategic'] += 0.1
            elif skill == "scout":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] += 0.1
            elif skill == "fleet_footed":
                modifiers['risk_taking'] += 0.1
                modifiers['strategic'] += 0.1
            elif skill == "independent":
                modifiers['trusting'] -= 0.2
                modifiers['loyal'] -= 0.3
            elif skill == "brute_force":
                modifiers['aggressive'] += 0.3
                modifiers['strategic'] -= 0.2
            elif skill == "straightforward":
                modifiers['deceptive'] -= 0.3
                modifiers['trusting'] += 0.1
            elif skill == "protective":
                modifiers['loyal'] += 0.3
                modifiers['aggressive'] += 0.1
            elif skill == "hardy":
                modifiers['risk_taking'] += 0.1
                modifiers['strategic'] -= 0.1
            elif skill == "loyal":
                modifiers['loyal'] += 0.4
                modifiers['trusting'] += 0.2
            elif skill == "deceptive":
                modifiers['deceptive'] += 0.4
                modifiers['trusting'] -= 0.3
            elif skill == "stealthy":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] -= 0.1
            elif skill == "sneaky":
                modifiers['deceptive'] += 0.3
                modifiers['strategic'] += 0.1
            elif skill == "manipulator":
                modifiers['deceptive'] += 0.3
                modifiers['strategic'] += 0.2
            elif skill == "two_faced":
                modifiers['deceptive'] += 0.5
                modifiers['loyal'] -= 0.4
            elif skill == "cunning":
                modifiers['strategic'] += 0.3
                modifiers['deceptive'] += 0.2
            elif skill == "resource_manager":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] -= 0.1
            elif skill == "observant":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] -= 0.1
            elif skill == "patient_hunter":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] -= 0.2
            elif skill == "self_preservation":
                modifiers['risk_taking'] -= 0.3
                modifiers['loyal'] -= 0.1
            elif skill == "instinctive":
                modifiers['strategic'] -= 0.2
                modifiers['risk_taking'] += 0.2
            elif skill == "animalistic":
                modifiers['aggressive'] += 0.2
                modifiers['strategic'] -= 0.3
            elif skill == "territorial":
                modifiers['aggressive'] += 0.2
                modifiers['loyal'] -= 0.1
            elif skill == "pack_hunter":
                modifiers['trusting'] += 0.2
                modifiers['loyal'] += 0.2
            elif skill == "survival_focused":
                modifiers['risk_taking'] -= 0.2
                modifiers['strategic'] += 0.1
            elif skill == "wild_card":
                modifiers['risk_taking'] += 0.3
                modifiers['strategic'] -= 0.2
            elif skill == "rebellious":
                modifiers['loyal'] -= 0.3
                modifiers['trusting'] -= 0.2
            elif skill == "free_spirit":
                modifiers['risk_taking'] += 0.2
                modifiers['loyal'] -= 0.2
            elif skill == "innovative":
                modifiers['strategic'] += 0.2
                modifiers['risk_taking'] += 0.1
            elif skill == "unconventional":
                modifiers['strategic'] -= 0.1
                modifiers['risk_taking'] += 0.2
            elif skill == "resilient":
                modifiers['risk_taking'] += 0.1
                modifiers['strategic'] -= 0.1
            elif skill == "enduring":
                modifiers['risk_taking'] -= 0.1
                modifiers['strategic'] += 0.1
            elif skill == "stoic":
                modifiers['deceptive'] += 0.1
                modifiers['trusting'] -= 0.1
            elif skill == "team_player":
                modifiers['trusting'] += 0.3
                modifiers['loyal'] += 0.3
            elif skill == "determined":
                modifiers['risk_taking'] += 0.1
                modifiers['strategic'] += 0.1

        return modifiers

    def _weighted_random_choice(self, options: List[str], weights: List[float]) -> str:
        """Choose an option using weighted random selection."""
        if len(weights) != len(options):
            return random.choice(options)

        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(options)

        r = random.uniform(0, total_weight)
        cumulative = 0

        for option, weight in zip(options, weights):
            cumulative += weight
            if r <= cumulative:
                return option

        return options[-1]  # Fallback

    def _calculate_safety_weights(self, options: List[str]) -> List[float]:
        """Calculate weights favoring safer options."""
        weights = []
        for option in options:
            if 'safe' in option.lower() or 'avoid' in option.lower() or 'flee' in option.lower():
                weights.append(1.5)
            elif 'risk' in option.lower() or 'engage' in option.lower() or 'attack' in option.lower():
                weights.append(0.8)
            else:
                weights.append(1.0)
        return weights