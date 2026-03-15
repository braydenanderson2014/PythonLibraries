"""
Enhanced Relationship Dynamics System for Hunger Games Simulator

Provides sophisticated relationship modeling with decay, betrayal mechanics,
trust dynamics, and social influence systems.
"""

import random
from typing import Dict, List, Tuple, Optional
from enum import Enum
from collections import defaultdict
from tributes.tribute import Tribute

class RelationshipType(Enum):
    ALLY = "ally"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    TRUSTING = "trusting"
    SUSPICIOUS = "suspicious"
    BETRAYED = "betrayed"

class RelationshipManager:
    """
    Manages complex relationship dynamics between tributes.
    """

    def __init__(self):
        self.relationships = defaultdict(lambda: defaultdict(dict))
        self.trust_history = defaultdict(lambda: defaultdict(list))
        self.betrayal_events = defaultdict(list)

    def initialize_relationships(self, tributes: List[Tribute]):
        """Initialize relationship data for all tributes."""
        for tribute in tributes:
            for other in tributes:
                if tribute != other:
                    # Initialize with existing trust values
                    trust = tribute.trust.get(other.name, 50)
                    self.relationships[tribute.name][other.name] = {
                        'trust': trust,
                        'relationship_type': self._classify_relationship(trust),
                        'interaction_count': 0,
                        'last_interaction': None,
                        'shared_experiences': [],
                        'betrayal_count': 0
                    }

    def update_relationship(self, tribute1: Tribute, tribute2: Tribute,
                          action: str, context: Dict = None):
        """
        Update relationship based on an action between tributes.

        Args:
            tribute1: The tribute performing the action
            tribute2: The tribute being affected
            action: Type of action ('help', 'attack', 'share', 'betray', etc.)
            context: Additional context about the action
        """
        rel_data = self.relationships[tribute1.name][tribute2.name]
        rel_data['interaction_count'] += 1
        rel_data['last_interaction'] = action

        # Update trust based on action
        trust_change = self._calculate_trust_change(action, context or {})
        old_trust = rel_data['trust']
        rel_data['trust'] = max(0, min(100, rel_data['trust'] + trust_change))

        # Record trust history
        self.trust_history[tribute1.name][tribute2.name].append(rel_data['trust'])

        # Update relationship type
        rel_data['relationship_type'] = self._classify_relationship(rel_data['trust'])

        # Handle betrayal mechanics
        if action == 'betray':
            rel_data['betrayal_count'] += 1
            rel_data['relationship_type'] = RelationshipType.BETRAYED
            self.betrayal_events[tribute1.name].append({
                'victim': tribute2.name,
                'time': context.get('time', 'unknown')
            })

        # Update shared experiences
        if action in ['share_resources', 'fight_together', 'save_life']:
            rel_data['shared_experiences'].append(action)

        # Update tribute's trust dictionary
        tribute1.trust[tribute2.name] = rel_data['trust']

    def process_relationship_decay(self, tributes: List[Tribute], days_passed: int = 1):
        """Process natural decay of relationships over time."""
        decay_rate = 0.02  # 2% trust decay per day

        for tribute in tributes:
            for other_name in list(tribute.trust.keys()):
                if other_name in [t.name for t in tributes]:  # Only decay for active tributes
                    current_trust = tribute.trust[other_name]
                    # Decay towards 50 (neutral)
                    if current_trust > 50:
                        decay_amount = (current_trust - 50) * decay_rate * days_passed
                        tribute.trust[other_name] = max(50, current_trust - decay_amount)
                    elif current_trust < 50:
                        decay_amount = (50 - current_trust) * decay_rate * days_passed
                        tribute.trust[other_name] = min(50, current_trust + decay_amount)

                    # Update relationship data
                    rel_data = self.relationships[tribute.name][other_name]
                    rel_data['trust'] = tribute.trust[other_name]
                    rel_data['relationship_type'] = self._classify_relationship(rel_data['trust'])

    def calculate_betrayal_risk(self, tribute1: Tribute, tribute2: Tribute) -> float:
        """Calculate the risk of betrayal in a relationship."""
        if tribute2.name not in tribute1.trust:
            return 0.5  # Neutral risk

        trust = tribute1.trust[tribute2.name]
        rel_data = self.relationships[tribute1.name][tribute2.name]

        # Base risk from trust (lower trust = higher betrayal risk)
        base_risk = (100 - trust) / 100

        # Increase risk based on betrayal history
        betrayal_multiplier = 1 + (rel_data['betrayal_count'] * 0.5)

        # Increase risk in desperate situations
        desperation_multiplier = 1.0
        if tribute1.health < 30 or tribute1.food < 20:
            desperation_multiplier = 1.3

        # Decrease risk for strong alliances
        alliance_multiplier = 1.0
        if tribute2.name in tribute1.allies and len(rel_data['shared_experiences']) > 2:
            alliance_multiplier = 0.7

        risk = base_risk * betrayal_multiplier * desperation_multiplier * alliance_multiplier
        return min(0.95, max(0.05, risk))  # Clamp between 5% and 95%

    def get_relationship_status(self, tribute1: Tribute, tribute2: Tribute) -> Dict:
        """Get comprehensive relationship status between two tributes."""
        rel_data = self.relationships[tribute1.name].get(tribute2.name, {
            'trust': 50,
            'relationship_type': RelationshipType.NEUTRAL,
            'interaction_count': 0,
            'betrayal_count': 0,
            'shared_experiences': []
        })

        return {
            'trust_level': rel_data['trust'],
            'relationship_type': rel_data['relationship_type'],
            'interaction_count': rel_data['interaction_count'],
            'betrayal_risk': self.calculate_betrayal_risk(tribute1, tribute2),
            'shared_experiences': len(rel_data['shared_experiences']),
            'betrayal_count': rel_data['betrayal_count'],
            'is_ally': tribute2.name in tribute1.allies,
            'is_enemy': rel_data['relationship_type'] == RelationshipType.ENEMY
        }

    def find_potential_allies(self, tribute: Tribute, tributes: List[Tribute],
                            min_trust: int = 60) -> List[Tribute]:
        """Find potential allies for a tribute based on trust and relationships."""
        potential_allies = []

        for other in tributes:
            if other == tribute or other.status != 'active':
                continue

            trust = tribute.trust.get(other.name, 50)
            rel_status = self.get_relationship_status(tribute, other)

            # Must have sufficient trust and not be enemies
            if (trust >= min_trust and
                rel_status['relationship_type'] != RelationshipType.ENEMY and
                rel_status['betrayal_risk'] < 0.7):  # Not too high betrayal risk

                potential_allies.append((other, trust, rel_status['betrayal_risk']))

        # Sort by trust (highest first), then by betrayal risk (lowest first)
        potential_allies.sort(key=lambda x: (x[1], -x[2]), reverse=True)

        return [ally[0] for ally in potential_allies]

    def simulate_social_dynamics(self, tributes: List[Tribute]):
        """Simulate complex social dynamics and relationship changes."""
        # Process relationship decay
        self.process_relationship_decay(tributes)

        # Simulate gossip and information spread
        self._simulate_gossip_network(tributes)

        # Process betrayal opportunities
        self._process_betrayal_opportunities(tributes)

        # Update alliance stability
        self._update_alliance_stability(tributes)

    def _simulate_gossip_network(self, tributes: List[Tribute]):
        """Simulate how information and opinions spread through gossip."""
        # Simplified gossip simulation
        for tribute in tributes:
            if tribute.status != 'active':
                continue

            # Tributes occasionally learn about others through gossip
            known_tributes = list(tribute.trust.keys())
            unknown_tributes = [t.name for t in tributes
                              if t != tribute and t.name not in known_tributes]

            if unknown_tributes and random.random() < 0.1:  # 10% chance per phase
                # Learn about a random unknown tribute
                new_tribute = random.choice(unknown_tributes)
                # Start with neutral trust
                tribute.trust[new_tribute] = 50
                self.relationships[tribute.name][new_tribute] = {
                    'trust': 50,
                    'relationship_type': RelationshipType.NEUTRAL,
                    'interaction_count': 0,
                    'last_interaction': 'gossip',
                    'shared_experiences': [],
                    'betrayal_count': 0
                }

    def _process_betrayal_opportunities(self, tributes: List[Tribute]):
        """Process potential betrayal opportunities."""
        for tribute in tributes:
            if tribute.status != 'active':
                continue

            allies = [t for t in tributes if t.name in tribute.allies and t.status == 'active']

            for ally in allies:
                betrayal_risk = self.calculate_betrayal_risk(tribute, ally)

                if random.random() < betrayal_risk * 0.1:  # Small chance of betrayal
                    # Execute betrayal
                    self.update_relationship(tribute, ally, 'betray',
                                           {'time': 'opportunistic'})
                    tribute.allies.remove(ally.name)

                    # The betrayed tribute becomes suspicious/enemy
                    self.update_relationship(ally, tribute, 'betrayed')

                    print(f"{tribute.name} betrays {ally.name}!")

    def _update_alliance_stability(self, tributes: List[Tribute]):
        """Update stability of existing alliances."""
        for tribute in tributes:
            if tribute.status != 'active':
                continue

            unstable_allies = []
            for ally_name in tribute.allies:
                ally = next((t for t in tributes if t.name == ally_name), None)
                if ally and ally.status == 'active':
                    rel_status = self.get_relationship_status(tribute, ally)

                    # Alliance becomes unstable if trust drops or betrayal risk is high
                    if (rel_status['trust_level'] < 40 or
                        rel_status['betrayal_risk'] > 0.8 or
                        rel_status['betrayal_count'] > 0):

                        unstable_allies.append(ally_name)

            # Random chance of breaking unstable alliances
            for ally_name in unstable_allies:
                if random.random() < 0.2:  # 20% chance per unstable alliance
                    tribute.allies.remove(ally_name)
                    print(f"Alliance between {tribute.name} and {ally_name} dissolves!")

    def _calculate_trust_change(self, action: str, context: Dict) -> int:
        """Calculate trust change based on action type."""
        trust_changes = {
            'help': 15,
            'share_resources': 10,
            'save_life': 25,
            'fight_together': 12,
            'attack': -20,
            'steal': -15,
            'betray': -40,
            'abandon': -10,
            'ignore': -5
        }

        base_change = trust_changes.get(action, 0)

        # Modify based on context
        if context.get('under_threat', False):
            base_change *= 1.5  # More valuable actions under threat

        if context.get('public', False):
            base_change *= 1.2  # Public actions have more impact

        return int(base_change)

    def _classify_relationship(self, trust: int) -> RelationshipType:
        """Classify relationship type based on trust level."""
        if trust >= 80:
            return RelationshipType.TRUSTING
        elif trust >= 60:
            return RelationshipType.ALLY
        elif trust <= 20:
            return RelationshipType.ENEMY
        elif trust <= 40:
            return RelationshipType.SUSPICIOUS
        else:
            return RelationshipType.NEUTRAL