#!/usr/bin/env python3
"""
RelationshipManager - Manages trust, alliances, and social dynamics between tributes

Features:
- Trust tracking (0-100 scale, 50 = neutral)
- Trust decay (2% per phase toward neutral)
- Betrayal tracking and history
- Shared experiences that strengthen bonds
- Gossip network effects
- Pre-defined relationships from web UI
- Alliance formation and breaking
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(Enum):
    """Types of relationships between tributes"""
    ENEMY = "enemy"  # Trust < 20
    RIVAL = "rival"  # Trust 20-35
    NEUTRAL = "neutral"  # Trust 35-65
    ACQUAINTANCE = "acquaintance"  # Trust 65-80
    ALLY = "ally"  # Trust 80-90
    CLOSE_ALLY = "close_ally"  # Trust 90+


class ExperienceType(Enum):
    """Types of shared experiences"""
    FOUGHT_TOGETHER = "fought_together"
    SHARED_SUPPLIES = "shared_supplies"
    SAVED_LIFE = "saved_life"
    BETRAYED = "betrayed"
    WITNESSED_KILL = "witnessed_kill"
    FORMED_ALLIANCE = "formed_alliance"
    BROKE_ALLIANCE = "broke_alliance"
    SHARED_SHELTER = "shared_shelter"
    PROTECTED_FROM_DANGER = "protected_from_danger"


@dataclass
class Relationship:
    """Represents relationship between two tributes"""
    tribute1_id: str
    tribute2_id: str
    trust: float = 50.0  # 0-100, 50 = neutral
    is_alliance: bool = False
    alliance_formed_phase: Optional[int] = None
    shared_experiences: List[Dict[str, Any]] = field(default_factory=list)
    betrayal_history: List[Dict[str, Any]] = field(default_factory=list)
    gossip_reputation: float = 0.0  # -50 to +50, affects third-party perceptions
    last_interaction_phase: int = 0
    
    # Enemy tracking
    is_enemy: bool = False
    enemy_priority: float = 0.0  # 0-100, how much of a threat/priority target this enemy is
    enemy_reason: Optional[str] = None  # Why they became enemies
    enemy_created_phase: Optional[int] = None
    
    def get_relationship_type(self) -> RelationshipType:
        """Determine relationship type based on trust level"""
        if self.trust < 20:
            return RelationshipType.ENEMY
        elif self.trust < 35:
            return RelationshipType.RIVAL
        elif self.trust < 65:
            return RelationshipType.NEUTRAL
        elif self.trust < 80:
            return RelationshipType.ACQUAINTANCE
        elif self.trust < 90:
            return RelationshipType.ALLY
        else:
            return RelationshipType.CLOSE_ALLY
    
    def calculate_betrayal_risk(self, betrayer_desperation: float) -> float:
        """
        Calculate probability of betrayal based on trust and desperation
        
        Args:
            betrayer_desperation: 0-100, how desperate the tribute is (low health, resources)
            
        Returns:
            Probability of betrayal (0.0-1.0)
        """
        # Base betrayal risk inversely related to trust
        base_risk = (100 - self.trust) / 100
        
        # Desperation multiplier (0.5 to 2.0)
        desperation_mult = 0.5 + (betrayer_desperation / 100) * 1.5
        
        # Alliance modifier (less likely to betray active alliance)
        alliance_mult = 0.3 if self.is_alliance else 1.0
        
        # Betrayal history makes future betrayals more likely
        history_mult = 1.0 + (len(self.betrayal_history) * 0.2)
        
        betrayal_risk = base_risk * desperation_mult * alliance_mult * history_mult
        
        return min(1.0, max(0.0, betrayal_risk))


class RelationshipManager:
    """
    Manages all relationships, trust, and social dynamics between tributes
    """
    
    def __init__(self):
        # Dict of (tribute1_id, tribute2_id) -> Relationship
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        
        # Track active alliances
        self.active_alliances: Dict[str, Set[str]] = {}  # tribute_id -> set of ally IDs
        
        # Gossip network - what tributes know about others
        self.gossip_network: Dict[str, Dict[str, float]] = {}  # observer_id -> {subject_id -> reputation}
        
        # Trust decay rate per phase (toward neutral 50)
        self.trust_decay_rate = 0.02  # 2% per phase
        
        # Current phase counter
        self.current_phase = 0
    
    def initialize_relationships(self, tribute_ids: List[str], 
                                predefined_relationships: Optional[Dict[str, Any]] = None):
        """
        Initialize relationships between all tributes
        
        Args:
            tribute_ids: List of all tribute IDs
            predefined_relationships: Dict from web UI with pre-defined relationships
                Format: {
                    "tribute1_id|tribute2_id": {
                        "trust": 75,
                        "is_alliance": true,
                        "relationship_type": "district_partner"
                    }
                }
        """
        # Create neutral relationships for all pairs
        for i, t1 in enumerate(tribute_ids):
            for t2 in tribute_ids[i+1:]:
                key = self._make_key(t1, t2)
                self.relationships[key] = Relationship(
                    tribute1_id=t1,
                    tribute2_id=t2,
                    trust=50.0,  # Start neutral
                    last_interaction_phase=0
                )
        
        # Apply predefined relationships from web UI
        if predefined_relationships:
            for key, rel_data in predefined_relationships.items():
                parts = key.split('|')
                if len(parts) == 2:
                    t1, t2 = parts
                    rel_key = self._make_key(t1, t2)
                    
                    if rel_key in self.relationships:
                        rel = self.relationships[rel_key]
                        rel.trust = rel_data.get('trust', 50.0)
                        rel.is_alliance = rel_data.get('is_alliance', False)
                        
                        # Handle enemy relationships
                        rel.is_enemy = rel_data.get('is_enemy', False)
                        if rel.is_enemy:
                            rel.enemy_priority = rel_data.get('enemy_priority', 50.0)
                            rel.enemy_reason = rel_data.get('enemy_reason', 'Pre-defined enemy')
                            rel.enemy_created_phase = 0
                        
                        # Add special experience for district partners
                        if rel_data.get('relationship_type') == 'district_partner':
                            rel.shared_experiences.append({
                                'type': ExperienceType.FORMED_ALLIANCE.value,
                                'phase': 0,
                                'description': 'District partners',
                                'trust_change': 0
                            })
                            
                            # Track alliance
                            if rel.is_alliance:
                                self._add_alliance(t1, t2)
                        
                        # Add special experience for rivals
                        elif rel_data.get('relationship_type') == 'rival':
                            rel.shared_experiences.append({
                                'type': 'rivalry_established',
                                'phase': 0,
                                'description': 'Pre-game rivalry',
                                'trust_change': 0
                            })

    
    def _make_key(self, tribute1_id: str, tribute2_id: str) -> Tuple[str, str]:
        """Create consistent key for relationship dict (ordered pair)"""
        return tuple(sorted([tribute1_id, tribute2_id]))
    
    def get_relationship(self, tribute1_id: str, tribute2_id: str) -> Optional[Relationship]:
        """Get relationship between two tributes"""
        key = self._make_key(tribute1_id, tribute2_id)
        return self.relationships.get(key)
    
    def update_relationship(self, tribute1_id: str, tribute2_id: str, 
                          trust_change: float, experience_type: ExperienceType,
                          description: str = ""):
        """
        Update relationship after an interaction
        
        Args:
            tribute1_id: First tribute
            tribute2_id: Second tribute
            trust_change: Change in trust (-100 to +100)
            experience_type: Type of shared experience
            description: Optional description of what happened
        """
        key = self._make_key(tribute1_id, tribute2_id)
        rel = self.relationships.get(key)
        
        if not rel:
            return
        
        # Update trust (clamped to 0-100)
        old_trust = rel.trust
        rel.trust = max(0, min(100, rel.trust + trust_change))
        rel.last_interaction_phase = self.current_phase
        
        # Record experience
        experience = {
            'type': experience_type.value,
            'phase': self.current_phase,
            'description': description,
            'trust_change': trust_change,
            'trust_before': old_trust,
            'trust_after': rel.trust
        }
        rel.shared_experiences.append(experience)
        
        # Special handling for betrayals
        if experience_type == ExperienceType.BETRAYED:
            rel.betrayal_history.append({
                'betrayer': tribute1_id,
                'victim': tribute2_id,
                'phase': self.current_phase,
                'trust_lost': trust_change
            })
            
            # Break alliance if active
            if rel.is_alliance:
                self._break_alliance(tribute1_id, tribute2_id)
            
            # Update gossip network - others hear about betrayal
            self._spread_gossip(tribute1_id, -30, f"Betrayed {tribute2_id}")
        
        # Positive experiences spread good gossip
        elif trust_change > 20:
            self._spread_gossip(tribute1_id, 10, "Cooperative behavior")
            self._spread_gossip(tribute2_id, 10, "Cooperative behavior")
    
    def form_alliance(self, tribute1_id: str, tribute2_id: str):
        """Form an alliance between two tributes"""
        key = self._make_key(tribute1_id, tribute2_id)
        rel = self.relationships.get(key)
        
        if rel and not rel.is_alliance:
            rel.is_alliance = True
            rel.alliance_formed_phase = self.current_phase
            self._add_alliance(tribute1_id, tribute2_id)
            
            # Boost trust when forming alliance
            self.update_relationship(
                tribute1_id, tribute2_id,
                trust_change=15,
                experience_type=ExperienceType.FORMED_ALLIANCE,
                description="Formed alliance"
            )
    
    def break_alliance(self, tribute1_id: str, tribute2_id: str, is_betrayal: bool = False):
        """Break an alliance"""
        key = self._make_key(tribute1_id, tribute2_id)
        rel = self.relationships.get(key)
        
        if rel and rel.is_alliance:
            rel.is_alliance = False
            self._remove_alliance(tribute1_id, tribute2_id)
            
            trust_loss = -40 if is_betrayal else -20
            exp_type = ExperienceType.BETRAYED if is_betrayal else ExperienceType.BROKE_ALLIANCE
            
            self.update_relationship(
                tribute1_id, tribute2_id,
                trust_change=trust_loss,
                experience_type=exp_type,
                description="Betrayed alliance" if is_betrayal else "Ended alliance"
            )
    
    def _add_alliance(self, tribute1_id: str, tribute2_id: str):
        """Track active alliance"""
        if tribute1_id not in self.active_alliances:
            self.active_alliances[tribute1_id] = set()
        if tribute2_id not in self.active_alliances:
            self.active_alliances[tribute2_id] = set()
        
        self.active_alliances[tribute1_id].add(tribute2_id)
        self.active_alliances[tribute2_id].add(tribute1_id)
    
    def _remove_alliance(self, tribute1_id: str, tribute2_id: str):
        """Remove active alliance"""
        if tribute1_id in self.active_alliances:
            self.active_alliances[tribute1_id].discard(tribute2_id)
        if tribute2_id in self.active_alliances:
            self.active_alliances[tribute2_id].discard(tribute1_id)
    
    def _break_alliance(self, tribute1_id: str, tribute2_id: str):
        """Internal method to break alliance (called during betrayals)"""
        self._remove_alliance(tribute1_id, tribute2_id)
    
    def get_allies(self, tribute_id: str) -> Set[str]:
        """Get all current allies of a tribute"""
        return self.active_alliances.get(tribute_id, set())
    
    def is_allied(self, tribute1_id: str, tribute2_id: str) -> bool:
        """Check if two tributes are currently allied"""
        return tribute2_id in self.active_alliances.get(tribute1_id, set())
    
    def mark_as_enemy(self, tribute1_id: str, tribute2_id: str, 
                     priority: float = 50.0, reason: str = "",
                     trust_penalty: float = -30.0):
        """
        Mark two tributes as enemies with threat priority
        
        Args:
            tribute1_id: First tribute
            tribute2_id: Second tribute (enemy from tribute1's perspective)
            priority: Threat priority 0-100 (higher = greater threat)
            reason: Why they became enemies (e.g., "Killed ally", "Skill rivalry")
            trust_penalty: Trust reduction when enemy relationship forms
        """
        rel = self.get_relationship(tribute1_id, tribute2_id)
        if not rel:
            return
        
        # Mark as enemies
        rel.is_enemy = True
        rel.enemy_priority = min(100.0, max(0.0, priority))
        rel.enemy_reason = reason
        rel.enemy_created_phase = self.current_phase
        
        # Apply trust penalty
        rel.trust = max(0.0, rel.trust + trust_penalty)
        
        # Break alliance if existed
        if rel.is_alliance:
            self._break_alliance(tribute1_id, tribute2_id)
            rel.is_alliance = False
        
        # Record in shared experiences
        rel.shared_experiences.append({
            'type': 'became_enemies',
            'phase': self.current_phase,
            'description': reason,
            'trust_change': trust_penalty
        })
        
        rel.last_interaction_phase = self.current_phase
    
    def update_enemy_priority(self, tribute1_id: str, tribute2_id: str, 
                             new_priority: float, reason: str = ""):
        """
        Update threat priority of an enemy
        
        Args:
            tribute1_id: Tribute whose enemy list to update
            tribute2_id: Enemy whose priority to update
            new_priority: New priority 0-100
            reason: Reason for priority change
        """
        rel = self.get_relationship(tribute1_id, tribute2_id)
        if not rel or not rel.is_enemy:
            return
        
        old_priority = rel.enemy_priority
        rel.enemy_priority = min(100.0, max(0.0, new_priority))
        
        # Log priority change
        if reason:
            rel.shared_experiences.append({
                'type': 'enemy_priority_updated',
                'phase': self.current_phase,
                'description': f"{reason} (Priority {old_priority:.0f} → {rel.enemy_priority:.0f})",
                'trust_change': 0
            })
    
    def get_enemies(self, tribute_id: str, min_priority: float = 0.0) -> List[Tuple[str, float]]:
        """
        Get all enemies of a tribute, optionally filtered by minimum priority
        
        Args:
            tribute_id: Tribute whose enemies to get
            min_priority: Only return enemies with priority >= this value
            
        Returns:
            List of (enemy_id, priority) tuples, sorted by priority descending
        """
        enemies = []
        
        for rel in self.relationships.values():
            # Check if this relationship involves the tribute
            if tribute_id not in (rel.tribute1_id, rel.tribute2_id):
                continue
            
            # Check if marked as enemy
            if not rel.is_enemy:
                continue
            
            # Check priority threshold
            if rel.enemy_priority < min_priority:
                continue
            
            # Get the enemy ID (the other tribute)
            enemy_id = rel.tribute2_id if rel.tribute1_id == tribute_id else rel.tribute1_id
            enemies.append((enemy_id, rel.enemy_priority))
        
        # Sort by priority descending (highest threat first)
        enemies.sort(key=lambda x: x[1], reverse=True)
        return enemies
    
    def is_enemy(self, tribute1_id: str, tribute2_id: str) -> bool:
        """Check if two tributes are marked as enemies"""
        rel = self.get_relationship(tribute1_id, tribute2_id)
        return rel.is_enemy if rel else False
    
    def remove_enemy_status(self, tribute1_id: str, tribute2_id: str, reason: str = ""):
        """
        Remove enemy status between tributes (reconciliation)
        
        Args:
            tribute1_id: First tribute
            tribute2_id: Second tribute
            reason: Reason for reconciliation
        """
        rel = self.get_relationship(tribute1_id, tribute2_id)
        if not rel or not rel.is_enemy:
            return
        
        rel.is_enemy = False
        rel.enemy_priority = 0.0
        
        # Slight trust boost for reconciliation
        rel.trust = min(100.0, rel.trust + 10.0)
        
        rel.shared_experiences.append({
            'type': 'reconciliation',
            'phase': self.current_phase,
            'description': reason or "Reconciled",
            'trust_change': 10.0
        })
        
        rel.last_interaction_phase = self.current_phase
    
    def create_enemy_from_event(self, tribute1_id: str, tribute2_id: str,
                                event_type: str, tribute1_skills: Dict[str, int] = None,
                                tribute2_skills: Dict[str, int] = None):
        """
        Dynamically create enemy relationship based on game events
        
        Args:
            tribute1_id: First tribute
            tribute2_id: Second tribute
            event_type: Type of event that triggered enemy status
            tribute1_skills: Tribute1's skills for threat calculation
            tribute2_skills: Tribute2's skills for threat calculation
        """
        priority = 50.0  # Default medium priority
        reason = ""
        trust_penalty = -30.0
        
        if event_type == "killed_ally":
            priority = 90.0
            reason = "Killed my ally"
            trust_penalty = -60.0
        elif event_type == "betrayal":
            priority = 85.0
            reason = "Betrayed me"
            trust_penalty = -50.0
        elif event_type == "witnessed_kill":
            priority = 70.0
            reason = "Witnessed them kill"
            trust_penalty = -40.0
        elif event_type == "stole_supplies":
            priority = 60.0
            reason = "Stole my supplies"
            trust_penalty = -35.0
        elif event_type == "combat_attack":
            priority = 75.0
            reason = "Attacked me"
            trust_penalty = -40.0
        elif event_type == "skill_rivalry":
            # Calculate priority based on skill comparison
            if tribute1_skills and tribute2_skills:
                # Find overlapping strong skills
                overlap_score = 0
                for skill in tribute1_skills:
                    if skill in tribute2_skills:
                        overlap_score += min(tribute1_skills[skill], tribute2_skills[skill])
                
                priority = min(80.0, 30.0 + (overlap_score / 10))
            else:
                priority = 50.0
            reason = "Skill rivalry detected"
            trust_penalty = -20.0
        elif event_type == "resource_competition":
            priority = 55.0
            reason = "Competing for resources"
            trust_penalty = -25.0
        
        # Mark as enemy
        self.mark_as_enemy(tribute1_id, tribute2_id, priority, reason, trust_penalty)
    
    def process_trust_decay(self):
        """
        Process trust decay toward neutral (50) for all relationships
        Called once per phase
        """
        self.current_phase += 1
        
        for rel in self.relationships.values():
            # Skip if interaction was recent (within 3 phases)
            if self.current_phase - rel.last_interaction_phase <= 3:
                continue
            
            # Decay toward 50 (neutral)
            if rel.trust > 50:
                # Decay down
                decay = (rel.trust - 50) * self.trust_decay_rate
                rel.trust = max(50, rel.trust - decay)
            elif rel.trust < 50:
                # Decay up
                decay = (50 - rel.trust) * self.trust_decay_rate
                rel.trust = min(50, rel.trust + decay)
            
            # Alliances decay slower toward 70 instead of 50
            if rel.is_alliance:
                if rel.trust > 70:
                    decay = (rel.trust - 70) * self.trust_decay_rate * 0.5
                    rel.trust = max(70, rel.trust - decay)
    
    def calculate_betrayal_risk(self, tribute_id: str, target_id: str,
                               tribute_desperation: float) -> float:
        """
        Calculate risk of tribute betraying target
        
        Args:
            tribute_id: ID of potential betrayer
            target_id: ID of potential victim
            tribute_desperation: 0-100, how desperate tribute is
            
        Returns:
            Probability of betrayal (0.0-1.0)
        """
        rel = self.get_relationship(tribute_id, target_id)
        if not rel:
            return 0.5  # Unknown relationship
        
        return rel.calculate_betrayal_risk(tribute_desperation)
    
    def _spread_gossip(self, subject_id: str, reputation_change: float, reason: str):
        """
        Spread gossip about a tribute through the network
        Affects how other tributes perceive the subject
        """
        # All tributes hear gossip with decay based on "distance"
        for observer_id in self.active_alliances.keys():
            if observer_id == subject_id:
                continue
            
            if observer_id not in self.gossip_network:
                self.gossip_network[observer_id] = {}
            
            if subject_id not in self.gossip_network[observer_id]:
                self.gossip_network[observer_id][subject_id] = 0.0
            
            # Update reputation (clamped to -50 to +50)
            old_rep = self.gossip_network[observer_id][subject_id]
            new_rep = old_rep + reputation_change
            self.gossip_network[observer_id][subject_id] = max(-50, min(50, new_rep))
    
    def get_reputation(self, observer_id: str, subject_id: str) -> float:
        """
        Get observer's perception of subject based on gossip
        Returns -50 to +50, 0 = neutral
        """
        if observer_id not in self.gossip_network:
            return 0.0
        return self.gossip_network[observer_id].get(subject_id, 0.0)
    
    def get_relationship_summary(self, tribute_id: str) -> Dict[str, Any]:
        """
        Get summary of tribute's relationships for UI/logging
        """
        allies = list(self.get_allies(tribute_id))
        
        enemies = []
        high_priority_enemies = []
        neutrals = []
        acquaintances = []
        
        for key, rel in self.relationships.items():
            if tribute_id not in key:
                continue
            
            other_id = key[0] if key[1] == tribute_id else key[1]
            rel_type = rel.get_relationship_type()
            
            # Track enemies separately with priority
            if rel.is_enemy:
                enemy_info = {
                    'id': other_id,
                    'priority': rel.enemy_priority,
                    'reason': rel.enemy_reason
                }
                enemies.append(enemy_info)
                if rel.enemy_priority >= 70:
                    high_priority_enemies.append(enemy_info)
            elif rel_type in [RelationshipType.ENEMY, RelationshipType.RIVAL]:
                enemies.append({'id': other_id, 'priority': 0, 'reason': 'Low trust'})
            elif rel_type == RelationshipType.NEUTRAL:
                neutrals.append(other_id)
            elif rel_type == RelationshipType.ACQUAINTANCE:
                acquaintances.append(other_id)
        
        return {
            'tribute_id': tribute_id,
            'allies': allies,
            'enemies': enemies,
            'high_priority_enemies': high_priority_enemies,
            'acquaintances': acquaintances,
            'neutrals': neutrals,
            'total_relationships': len(allies) + len(enemies) + len(acquaintances) + len(neutrals)
        }
    
    def get_all_relationships_data(self) -> List[Dict[str, Any]]:
        """Get all relationships for saving/API"""
        data = []
        for rel in self.relationships.values():
            data.append({
                'tribute1_id': rel.tribute1_id,
                'tribute2_id': rel.tribute2_id,
                'trust': rel.trust,
                'relationship_type': rel.get_relationship_type().value,
                'is_alliance': rel.is_alliance,
                'is_enemy': rel.is_enemy,
                'enemy_priority': rel.enemy_priority if rel.is_enemy else 0,
                'enemy_reason': rel.enemy_reason if rel.is_enemy else None,
                'betrayal_count': len(rel.betrayal_history),
                'shared_experiences_count': len(rel.shared_experiences),
                'last_interaction_phase': rel.last_interaction_phase
            })
        return data
    
    def save_state(self) -> Dict[str, Any]:
        """Save relationship manager state"""
        return {
            'relationships': [
                {
                    'tribute1_id': rel.tribute1_id,
                    'tribute2_id': rel.tribute2_id,
                    'trust': rel.trust,
                    'is_alliance': rel.is_alliance,
                    'alliance_formed_phase': rel.alliance_formed_phase,
                    'shared_experiences': rel.shared_experiences,
                    'betrayal_history': rel.betrayal_history,
                    'gossip_reputation': rel.gossip_reputation,
                    'last_interaction_phase': rel.last_interaction_phase,
                    'is_enemy': rel.is_enemy,
                    'enemy_priority': rel.enemy_priority,
                    'enemy_reason': rel.enemy_reason,
                    'enemy_created_phase': rel.enemy_created_phase
                }
                for rel in self.relationships.values()
            ],
            'active_alliances': {
                k: list(v) for k, v in self.active_alliances.items()
            },
            'gossip_network': self.gossip_network,
            'current_phase': self.current_phase
        }
    
    def load_state(self, state: Dict[str, Any]):
        """Load relationship manager state"""
        self.relationships = {}
        for rel_data in state.get('relationships', []):
            key = self._make_key(rel_data['tribute1_id'], rel_data['tribute2_id'])
            self.relationships[key] = Relationship(
                tribute1_id=rel_data['tribute1_id'],
                tribute2_id=rel_data['tribute2_id'],
                trust=rel_data['trust'],
                is_alliance=rel_data['is_alliance'],
                alliance_formed_phase=rel_data.get('alliance_formed_phase'),
                shared_experiences=rel_data.get('shared_experiences', []),
                betrayal_history=rel_data.get('betrayal_history', []),
                gossip_reputation=rel_data.get('gossip_reputation', 0.0),
                last_interaction_phase=rel_data.get('last_interaction_phase', 0),
                is_enemy=rel_data.get('is_enemy', False),
                enemy_priority=rel_data.get('enemy_priority', 0.0),
                enemy_reason=rel_data.get('enemy_reason'),
                enemy_created_phase=rel_data.get('enemy_created_phase')
            )
        
        self.active_alliances = {
            k: set(v) for k, v in state.get('active_alliances', {}).items()
        }
        self.gossip_network = state.get('gossip_network', {})
        self.current_phase = state.get('current_phase', 0)


# Example usage and testing
if __name__ == "__main__":
    print("RelationshipManager Test")
    print("=" * 50)
    
    # Create manager
    manager = RelationshipManager()
    
    # Initialize with 4 tributes
    tribute_ids = ["tribute1", "tribute2", "tribute3", "tribute4"]
    
    # Predefined relationships (from web UI)
    predefined = {
        "tribute1|tribute2": {
            "trust": 75,
            "is_alliance": True,
            "relationship_type": "district_partner"
        },
        "tribute1|tribute3": {
            "trust": 20,
            "is_alliance": False,
            "relationship_type": "rival"
        }
    }
    
    manager.initialize_relationships(tribute_ids, predefined)
    
    print("\nInitial Relationships:")
    for tribute_id in tribute_ids:
        summary = manager.get_relationship_summary(tribute_id)
        print(f"{tribute_id}: {summary}")
    
    print("\n--- Interaction: tribute1 shares supplies with tribute2 ---")
    manager.update_relationship(
        "tribute1", "tribute2",
        trust_change=10,
        experience_type=ExperienceType.SHARED_SUPPLIES,
        description="Shared food and water"
    )
    
    print("\n--- Interaction: tribute1 betrays tribute2 ---")
    manager.break_alliance("tribute1", "tribute2", is_betrayal=True)
    
    print("\n--- Process trust decay (5 phases) ---")
    for i in range(5):
        manager.process_trust_decay()
        print(f"Phase {manager.current_phase}: tribute1-tribute2 trust = {manager.get_relationship('tribute1', 'tribute2').trust:.2f}")
    
    print("\n--- Calculate betrayal risks ---")
    for t1 in tribute_ids[:2]:
        for t2 in tribute_ids[2:]:
            risk = manager.calculate_betrayal_risk(t1, t2, tribute_desperation=60)
            print(f"{t1} betraying {t2}: {risk:.2%} risk")
    
    print("\n--- Final Relationship Data ---")
    import json
    print(json.dumps(manager.get_all_relationships_data(), indent=2))
