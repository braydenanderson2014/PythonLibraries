"""
Behavior Tree System for Hunger Games Simulator

This module implements a sophisticated behavior tree system for tribute AI,
providing complex decision-making capabilities that go beyond simple state machines.
"""

import random
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from tributes.tribute import Tribute
from utils.weapon_effectiveness import WeaponEffectivenessCalculator

class NodeStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"

class BehaviorNode:
    """Base class for all behavior tree nodes."""

    def __init__(self, name: str = ""):
        self.name = name
        self.status = NodeStatus.RUNNING

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        """Execute this node. Must be implemented by subclasses."""
        raise NotImplementedError

    def reset(self):
        """Reset the node's state."""
        self.status = NodeStatus.RUNNING

class CompositeNode(BehaviorNode):
    """Base class for nodes that have children."""

    def __init__(self, name: str = "", children: List[BehaviorNode] = None):
        super().__init__(name)
        self.children = children or []

    def add_child(self, child: BehaviorNode):
        self.children.append(child)

class SequenceNode(CompositeNode):
    """Executes children in order until one fails or all succeed."""

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        for child in self.children:
            status = child.execute(tribute, game_state, blackboard)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS

class SelectorNode(CompositeNode):
    """Executes children until one succeeds."""

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        for child in self.children:
            status = child.execute(tribute, game_state, blackboard)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE

class DecoratorNode(BehaviorNode):
    """Base class for decorator nodes that modify child behavior."""

    def __init__(self, name: str = "", child: BehaviorNode = None):
        super().__init__(name)
        self.child = child

class InverterNode(DecoratorNode):
    """Inverts the result of its child."""

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        if not self.child:
            return NodeStatus.FAILURE

        status = self.child.execute(tribute, game_state, blackboard)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return NodeStatus.RUNNING

class SucceederNode(DecoratorNode):
    """Always returns success, regardless of child result."""

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        if self.child:
            self.child.execute(tribute, game_state, blackboard)
        return NodeStatus.SUCCESS

class LeafNode(BehaviorNode):
    """Base class for leaf nodes that perform actions or checks."""

    def __init__(self, name: str = "", action: Callable = None):
        super().__init__(name)
        self.action = action

class ConditionNode(LeafNode):
    """Node that checks a condition."""

    def __init__(self, name: str = "", condition_func: Callable[[Tribute, Any, Dict], bool] = None):
        super().__init__(name)
        self.condition_func = condition_func

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        if self.condition_func and self.condition_func(tribute, game_state, blackboard):
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

class ActionNode(LeafNode):
    """Node that performs an action."""

    def __init__(self, name: str = "", action_func: Callable[[Tribute, Any, Dict], NodeStatus] = None):
        super().__init__(name)
        self.action_func = action_func

    def execute(self, tribute: Tribute, game_state, blackboard: Dict[str, Any]) -> NodeStatus:
        if self.action_func:
            return self.action_func(tribute, game_state, blackboard)
        return NodeStatus.SUCCESS

class BehaviorTree:
    """Main behavior tree class."""

    def __init__(self, root: BehaviorNode):
        self.root = root
        self.blackboard: Dict[str, Any] = {}

    def execute(self, tribute: Tribute, game_state) -> NodeStatus:
        """Execute the behavior tree."""
        return self.root.execute(tribute, game_state, self.blackboard)

    def reset(self):
        """Reset the entire tree."""
        def reset_node(node: BehaviorNode):
            node.reset()
            if hasattr(node, 'children'):
                for child in node.children:
                    reset_node(child)
            elif hasattr(node, 'child') and node.child:
                reset_node(node.child)

        reset_node(self.root)

class TributeBehaviorTree:
    """Behavior tree system for tributes."""

    def __init__(self, tribute: Tribute):
        self.tribute = tribute
        self.weapon_calculator = WeaponEffectivenessCalculator()
        self.tree = self._build_behavior_tree()

    def _build_behavior_tree(self) -> BehaviorTree:
        """Build the behavior tree for this tribute."""

        # Root selector - try different behaviors in priority order
        root = SelectorNode("Root")

        # Cornucopia decision branch (only during initial phase)
        cornucopia_branch = SequenceNode("Cornucopia Decision")
        cornucopia_branch.add_child(ConditionNode("Is Initial Phase",
            lambda t, gs, bb: gs.day == 1 and gs.phase == "morning"))
        cornucopia_branch.add_child(self._build_cornucopia_subtree())

        # Emergency survival branch (highest priority)
        emergency_branch = SequenceNode("Emergency Survival")
        emergency_branch.add_child(ConditionNode("Health Critical",
            lambda t, gs, bb: t.health < 30))
        emergency_branch.add_child(SelectorNode("Emergency Actions"))
        # Add emergency actions...

        # Combat branch
        combat_branch = SequenceNode("Combat")
        combat_branch.add_child(ConditionNode("Enemies Nearby",
            lambda t, gs, bb: len([other for other in gs.active_tributes if other != t and (other.district != t.district or other.name not in t.allies)]) > 0))
        combat_branch.add_child(self._build_combat_subtree())

        # Resource gathering branch
        resource_branch = SequenceNode("Resource Gathering")
        resource_branch.add_child(ConditionNode("Resources Low",
            lambda t, gs, bb: t.food < 50 or t.water < 50))
        resource_branch.add_child(self._build_resource_subtree())

        # Alliance management branch - higher priority when enemies are nearby
        alliance_branch = SequenceNode("Alliance Management")
        alliance_branch.add_child(ConditionNode("Has Allies",
            lambda t, gs, bb: len([ally for ally in t.allies if ally in [trib.name for trib in gs.active_tributes]]) > 0))
        alliance_branch.add_child(self._build_alliance_subtree())

        # Hunting branch - proactive hunting for individuals or groups
        hunting_branch = SequenceNode("Hunting")
        hunting_branch.add_child(ConditionNode("Should Hunt",
            lambda t, gs, bb: self._should_hunt(t, gs)))
        hunting_branch.add_child(self._build_hunting_subtree())

        # Default idle branch
        idle_branch = ActionNode("Idle",
            lambda t, gs, bb: self._perform_idle_action(t, gs, bb))

        root.add_child(cornucopia_branch)
        root.add_child(emergency_branch)
        root.add_child(alliance_branch)
        root.add_child(hunting_branch)
        root.add_child(combat_branch)
        root.add_child(resource_branch)
        root.add_child(idle_branch)

        return BehaviorTree(root)

    def _build_combat_subtree(self) -> BehaviorNode:
        """Build the combat decision subtree."""
        combat_selector = SelectorNode("Combat Actions")

        # Flee if outnumbered or weak
        flee_sequence = SequenceNode("Flee")
        flee_sequence.add_child(ConditionNode("Should Flee",
            lambda t, gs, bb: self._should_flee(t, gs)))
        flee_sequence.add_child(ActionNode("Flee Action",
            lambda t, gs, bb: self._flee(t, gs, bb)))

        # Attack if strong
        attack_sequence = SequenceNode("Attack")
        attack_sequence.add_child(ConditionNode("Should Attack",
            lambda t, gs, bb: self._should_attack(t, gs)))
        attack_sequence.add_child(ActionNode("Attack Action",
            lambda t, gs, bb: self._attack(t, gs, bb)))

        # Hide if neutral
        hide_action = ActionNode("Hide",
            lambda t, gs, bb: self._hide(t, gs, bb))

        combat_selector.add_child(flee_sequence)
        combat_selector.add_child(attack_sequence)
        combat_selector.add_child(hide_action)

        return combat_selector

    def _build_cornucopia_subtree(self) -> BehaviorNode:
        """Build the Cornucopia approach decision subtree."""
        cornucopia_selector = SelectorNode("Cornucopia Actions")

        # Approach Cornucopia
        approach_sequence = SequenceNode("Approach Cornucopia")
        approach_sequence.add_child(ConditionNode("Should Approach Cornucopia",
            lambda t, gs, bb: self._should_approach_cornucopia(t, gs)))
        approach_sequence.add_child(ActionNode("Approach Action",
            lambda t, gs, bb: self._approach_cornucopia(t, gs, bb)))

        # Flee from Cornucopia
        flee_action = ActionNode("Flee Cornucopia",
            lambda t, gs, bb: self._flee_cornucopia(t, gs, bb))

        cornucopia_selector.add_child(approach_sequence)
        cornucopia_selector.add_child(flee_action)

        return cornucopia_selector

    def _build_resource_subtree(self) -> BehaviorNode:
        """Build the resource gathering subtree."""
        resource_selector = SelectorNode("Resource Actions")

        # Hunt/forage
        hunt_action = ActionNode("Hunt/Forage",
            lambda t, gs, bb: self._hunt_forage(t, gs, bb))

        # Request sponsor gift
        sponsor_action = ActionNode("Request Sponsor",
            lambda t, gs, bb: self._request_sponsor(t, gs, bb))

        resource_selector.add_child(hunt_action)
        resource_selector.add_child(sponsor_action)

        return resource_selector

    def _build_alliance_subtree(self) -> BehaviorNode:
        """Build the alliance management subtree."""
        alliance_selector = SelectorNode("Alliance Actions")

        # Hunt with allies (coordinated attack) - highest priority when enough allies
        hunt_with_allies = SequenceNode("Hunt with Allies")
        hunt_with_allies.add_child(ConditionNode("Should Hunt with Allies",
            lambda t, gs, bb: self._should_hunt_with_allies(t, gs)))
        hunt_with_allies.add_child(ActionNode("Execute Hunt",
            lambda t, gs, bb: self._hunt_with_allies(t, gs, bb)))

        # Help ally
        help_ally = ActionNode("Help Ally",
            lambda t, gs, bb: self._help_ally(t, gs, bb))

        # Betray ally (low probability, influenced by secret skills)
        betray_ally = SequenceNode("Betray Ally")
        betray_ally.add_child(ConditionNode("Should Betray Ally",
            lambda t, gs, bb: self._should_betray_ally(t, gs)))
        betray_ally.add_child(ActionNode("Execute Betrayal",
            lambda t, gs, bb: self._betray_ally(t, gs, bb)))

        alliance_selector.add_child(hunt_with_allies)
        alliance_selector.add_child(help_ally)
        alliance_selector.add_child(betray_ally)

        return alliance_selector

    def make_decision(self, game_state) -> str:
        """Make a decision using the behavior tree."""
        status = self.tree.execute(self.tribute, game_state)

        # Extract the chosen action from the blackboard
        return self.tree.blackboard.get('chosen_action', 'idle')

    # Condition check methods
    def _should_flee(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should flee."""
        nearby_enemies = len([t for t in game_state.active_tributes
                             if t != tribute and t.district != tribute.district])
        health_ratio = tribute.health / 100.0
        weapon_advantage = len(tribute.weapons) > 0

        # Base flee conditions
        should_flee = (health_ratio < 0.4 or
                      nearby_enemies > 2 or
                      (nearby_enemies > 1 and not weapon_advantage))

        # Apply secret skill modifiers
        secret_skills = getattr(tribute, 'secret_skills', [])

        # Cowardly or evasive skills make fleeing more likely
        if any(skill in ['evasive', 'self_preservation', 'survival_focused'] for skill in secret_skills):
            should_flee = should_flee or (nearby_enemies > 0 and health_ratio < 0.6)

        # Aggressive skills make fleeing less likely
        if any(skill in ['combat_focused', 'brute_force', 'ruthless', 'power_hungry'] for skill in secret_skills):
            should_flee = should_flee and health_ratio < 0.2  # Only flee if critically injured

        # Stealthy skills make fleeing more viable
        if any(skill in ['stealthy', 'sneaky', 'fleet_footed'] for skill in secret_skills):
            should_flee = should_flee or nearby_enemies > 0  # More willing to flee when outnumbered

        return should_flee

    def _should_attack(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should attack."""
        health_ratio = tribute.health / 100.0
        has_weapons = len(tribute.weapons) > 1  # More than just fists
        nearby_enemies = len([t for t in game_state.active_tributes
                             if t != tribute and t.district != tribute.district])
        unarmed_targets = len([t for t in game_state.active_tributes
                              if t != tribute and len(t.weapons) <= 1])  # Targets with only fists

        base_chance = 0.0
        
        # Much more aggressive logic
        if game_state.day == 1:
            # Day 1 bloodbath - very aggressive
            if unarmed_targets > 0:
                base_chance = 0.9  # 90% chance to attack unarmed targets on day 1
            elif has_weapons:
                base_chance = 0.7  # 70% chance if armed
            else:
                base_chance = 0.5  # 50% chance even if unarmed
        else:
            # Later days - still aggressive but more cautious
            if unarmed_targets > 0 and not has_weapons:
                base_chance = 0.8  # High chance to attack unarmed if you're also unarmed (need weapons)
            elif has_weapons and health_ratio > 0.3:
                base_chance = 0.6  # Moderate chance if armed and not too injured
            elif health_ratio > 0.7:
                base_chance = 0.4  # Low chance if healthy but unarmed
        
        # Weight penalty - overweight tributes less likely to attack
        if tribute.is_overweight():
            base_chance -= 0.2

        # Strength bonus - stronger tributes more confident
        strength_score = tribute.trait_scores.get('strength', tribute.skills.get('strength', 5) * 1.0)
        if strength_score > 7:
            base_chance += 0.2
        elif strength_score < 4:
            base_chance -= 0.2

        # Weapon effectiveness bonus
        if tribute.weapons:
            weapon_effectiveness = self.weapon_calculator.calculate_weapon_effectiveness(tribute, tribute.weapons[0].lower())
            weapon_score = weapon_effectiveness["damage"] * 0.4 + weapon_effectiveness["accuracy"] * 0.4 + weapon_effectiveness["speed"] * 0.2
            if weapon_score > 5:
                base_chance += 0.3  # Significant bonus for good weapons
            elif weapon_score < 2:
                base_chance -= 0.2  # Penalty for poor weapons

        # Agility bonus - agile tributes more likely to attack
        agility = tribute.skills.get('agility', 5)
        if agility > 7:
            base_chance += 0.15
        elif agility < 4:
            base_chance -= 0.1

        # Endurance bonus - enduring tributes can sustain longer fights
        endurance = tribute.skills.get('endurance', 5)
        if endurance > 7:
            base_chance += 0.1

        # Intelligence penalty - smarter tributes more cautious
        intelligence = tribute.skills.get('intelligence', 5)
        if intelligence > 7:
            base_chance -= 0.1

        # Charisma bonus - charismatic tributes more confident in social situations
        charisma = tribute.skills.get('charisma', 5)
        if charisma > 7:
            base_chance += 0.05

        # Luck factor - lucky tributes get small random bonus
        luck = tribute.skills.get('luck', 5)
        luck_modifier = (luck - 5) * 0.02  # Small luck influence
        base_chance += luck_modifier

        # Apply secret skill modifiers
        secret_skills = getattr(tribute, 'secret_skills', [])
        if any(skill in ['combat_focused', 'brute_force', 'ruthless', 'power_hungry', 'aggressive'] for skill in secret_skills):
            base_chance += 0.3  # More aggressive
        if any(skill in ['evasive', 'self_preservation', 'survival_focused'] for skill in secret_skills):
            base_chance -= 0.2  # More cautious
        if any(skill in ['strategic_mind', 'analytical', 'patient_hunter'] for skill in secret_skills):
            base_chance += 0.1  # More calculated aggression
        if any(skill in ['instinctive', 'animalistic'] for skill in secret_skills):
            base_chance += 0.2  # More instinctive aggression

        # Add some randomness
        random_factor = random.uniform(-0.2, 0.2)
        final_chance = max(0.05, min(0.95, base_chance + random_factor))

        return random.random() < final_chance

    def _should_betray_ally(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should betray an ally."""
        secret_skills = getattr(tribute, 'secret_skills', [])

        # Base betrayal chance is low (5%)
        base_chance = 0.05

        # Deceptive and ruthless skills increase betrayal chance
        if any(skill in ['deceptive', 'two_faced', 'manipulative', 'ruthless', 'opportunistic'] for skill in secret_skills):
            base_chance += 0.15  # +15% for deceptive skills

        # Loyal skills decrease betrayal chance
        if any(skill in ['loyal', 'pack_mentality', 'steadfast', 'nurturing'] for skill in secret_skills):
            base_chance -= 0.04  # -4% for loyal skills

        # Check if tribute has allies to potentially betray
        has_allies = len([ally for ally in tribute.allies if ally in [trib.name for trib in game_state.active_tributes]]) > 0

        return has_allies and random.random() < base_chance

    def _should_hunt_with_allies(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should hunt with allies."""
        secret_skills = getattr(tribute, 'secret_skills', [])

        # Check if tribute has allies available
        available_allies = len([ally for ally in tribute.allies if ally in [trib.name for trib in game_state.active_tributes]])

        if available_allies < 1:
            return False

        # Base chance depends on number of allies (more allies = higher chance)
        base_chance = min(0.8, available_allies * 0.4)  # 40% per ally, max 80%

        # Loyal and pack mentality skills increase cooperation chance
        if any(skill in ['pack_mentality', 'loyal', 'team_player', 'protective'] for skill in secret_skills):
            base_chance += 0.2  # +20% for cooperative skills

        # Independent and deceptive skills decrease cooperation chance
        if any(skill in ['independent', 'deceptive', 'two_faced', 'self_preservation'] for skill in secret_skills):
            base_chance -= 0.15  # -15% for independent/deceptive skills

        return random.random() < base_chance

    def _should_approach_cornucopia(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should approach the Cornucopia."""
        # Random decision with some personality-based weighting
        base_chance = 0.5  # 50% base chance

        # Adjust based on tribute personality (if available)
        if hasattr(tribute, 'personality'):
            if tribute.personality.get('bravery', 0.5) > 0.7:
                base_chance += 0.2  # Brave tributes more likely to approach
            elif tribute.personality.get('bravery', 0.5) < 0.3:
                base_chance -= 0.2  # Cowardly tributes less likely to approach

        # Adjust based on physical attributes (skills)
        strength = tribute.skills.get('strength', 5)
        if strength > 7:
            base_chance += 0.1  # Strong tributes more confident
        elif strength < 4:
            base_chance -= 0.1  # Weak tributes more cautious

        # Agility bonus for Cornucopia approach
        agility = tribute.skills.get('agility', 5)
        if agility > 7:
            base_chance += 0.15  # Agile tributes can move quickly
        elif agility < 4:
            base_chance -= 0.1

        # Endurance consideration
        endurance = tribute.skills.get('endurance', 5)
        if endurance > 7:
            base_chance += 0.1  # Can handle the chaos better

        # Adjust based on intelligence (smarter tributes more cautious)
        intelligence = tribute.skills.get('intelligence', 5)
        if intelligence > 7:
            base_chance -= 0.15  # Smart tributes think twice
        elif intelligence < 4:
            base_chance += 0.1  # Less intelligent tributes more impulsive

        # Charisma - confident tributes more likely to approach
        charisma = tribute.skills.get('charisma', 5)
        if charisma > 7:
            base_chance += 0.05

        # Adjust based on weight (overweight tributes less likely to approach)
        if tribute.is_overweight():
            base_chance -= 0.2

        # Day 1 violence boost - much more likely to approach on first day
        if game_state.day == 1:
            base_chance += 0.3  # 30% more likely to be violent on day 1

        # Add randomness to make decisions varied
        random_factor = random.uniform(-0.5, 0.5)  # Increased range for more unpredictability
        final_chance = max(0.1, min(0.9, base_chance + random_factor))

        return random.random() < final_chance

    def _should_hunt(self, tribute: Tribute, game_state) -> bool:
        """Determine if tribute should go hunting (for animals or tributes)."""
        # Base chance depends on hunting and survival skills
        hunting_skill = tribute.skills.get('hunting', 5)
        survival_skill = tribute.skills.get('survival', 5)
        strength_skill = tribute.skills.get('strength', 5)

        # Average of relevant skills
        avg_skill = (hunting_skill + survival_skill + strength_skill) / 3.0

        # Base chance: 20-60% depending on skills
        base_chance = 0.2 + (avg_skill - 3) * 0.1  # 20% at skill 3, 60% at skill 9

        # Alliance bonus: +20% if has allies (group hunting is safer/more effective)
        if len([ally for ally in tribute.allies if ally in [t.name for t in game_state.active_tributes]]) > 0:
            base_chance += 0.2

        # Resource consideration: more likely if resources are moderate (not full, not critical)
        food_level = tribute.food / 100.0
        water_level = tribute.water / 100.0
        avg_resources = (food_level + water_level) / 2.0

        if avg_resources < 0.3:  # Low resources
            base_chance += 0.15  # More urgent hunting
        elif avg_resources > 0.8:  # High resources
            base_chance -= 0.1   # Less need to hunt

        # Health consideration: injured tributes less likely to hunt aggressively
        if tribute.health < 50:
            base_chance -= 0.1

        # Time of day: more likely during certain phases
        if game_state.phase == 'morning':
            base_chance += 0.1  # Good hunting time
        elif game_state.phase == 'evening':
            base_chance -= 0.05  # Getting dark

        # Game progression: more hunting as game goes on (desperation)
        desperation_factor = min(0.15, (game_state.day - 1) * 0.03)
        base_chance += desperation_factor

        # Add randomness
        random_factor = random.uniform(-0.2, 0.2)
        final_chance = max(0.05, min(0.8, base_chance + random_factor))

        return random.random() < final_chance

    def _build_hunting_subtree(self) -> BehaviorNode:
        """Build the hunting decision subtree."""
        hunting_selector = SelectorNode("Hunting Actions")

        # Hunt animals for resources
        hunt_animals = ActionNode("Hunt Animals",
            lambda t, gs, bb: self._hunt_animals(t, gs, bb))

        # Scavenge for weapons
        scavenge_weapons = ActionNode("Scavenge Weapons",
            lambda t, gs, bb: self._scavenge_weapons(t, gs, bb))

        # Hunt tributes (aggressive hunting)
        hunt_tributes = SequenceNode("Hunt Tributes")
        hunt_tributes.add_child(ConditionNode("Enemies Available",
            lambda t, gs, bb: len([other for other in gs.active_tributes
                                   if other != t and other.name not in t.allies]) > 0))
        hunt_tributes.add_child(ActionNode("Hunt Tributes Action",
            lambda t, gs, bb: self._hunt_tributes(t, gs, bb)))

        hunting_selector.add_child(hunt_animals)
        hunting_selector.add_child(scavenge_weapons)
        hunting_selector.add_child(hunt_tributes)

        return hunting_selector

    # Action methods
    def _flee(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'idle'  # Map flee to idle (hiding/resting)
        return NodeStatus.SUCCESS

    def _attack(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'fight'
        return NodeStatus.SUCCESS

    def _hide(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'idle'
        return NodeStatus.SUCCESS

    def _hunt_forage(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'idle'  # Hunting/foraging is part of idle
        return NodeStatus.SUCCESS

    def _request_sponsor(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'sponsor'
        return NodeStatus.SUCCESS

    def _hunt_with_allies(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Coordinate a hunt/raid with allies."""
        # Find available allies
        available_allies = []
        for ally_name in tribute.allies:
            ally = next((t for t in game_state.active_tributes if t.name == ally_name), None)
            if ally and ally != tribute:
                available_allies.append(ally)

        if len(available_allies) >= 1:  # Need at least 1 ally for coordinated hunt
            # Choose 1-2 allies to join the hunt
            num_allies = min(len(available_allies), random.randint(1, 2))
            hunting_party = [tribute] + random.sample(available_allies, num_allies)

            # Store hunting party in tribute for main loop access
            tribute.hunting_party = hunting_party
            blackboard['hunting_party'] = hunting_party
            blackboard['chosen_action'] = 'alliance_hunt'
            return NodeStatus.SUCCESS

        # Not enough allies available
        return NodeStatus.FAILURE

    def _help_ally(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'alliance'
        return NodeStatus.SUCCESS

    def _betray_ally(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        blackboard['chosen_action'] = 'fight'  # Betrayal leads to fighting
        return NodeStatus.SUCCESS

    def _approach_cornucopia(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Action to approach the Cornucopia."""
        blackboard['chosen_action'] = 'cornucopia_approach'
        return NodeStatus.SUCCESS

    def _flee_cornucopia(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Action to flee from the Cornucopia."""
        blackboard['chosen_action'] = 'cornucopia_flee'
        return NodeStatus.SUCCESS

    def _hunt_animals(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Action to hunt animals for food/water resources."""
        blackboard['chosen_action'] = 'hunt_animals'
        return NodeStatus.SUCCESS

    def _hunt_tributes(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Action to aggressively hunt other tributes."""
        blackboard['chosen_action'] = 'hunt_tributes'
        return NodeStatus.SUCCESS

    def _scavenge_weapons(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        """Action to scavenge for weapons in the environment."""
        # Find the best available weapon for this tribute
        best_weapon = self.weapon_calculator.get_best_weapon_for_tribute(tribute)

        # Check if tribute already has this weapon or better
        current_weapons = [w.lower() for w in tribute.weapons]
        if best_weapon not in current_weapons:
            # Calculate effectiveness of current best weapon vs new weapon
            current_effectiveness = 0
            if tribute.weapons:
                current_weapon = tribute.weapons[0].lower()
                if current_weapon in self.weapon_calculator.weapons:
                    current_stats = self.weapon_calculator.calculate_weapon_effectiveness(tribute, current_weapon)
                    current_effectiveness = current_stats["damage"] * 0.5 + current_stats["accuracy"] * 0.3 + current_stats["speed"] * 0.2

            new_effectiveness = 0
            if best_weapon in self.weapon_calculator.weapons:
                new_stats = self.weapon_calculator.calculate_weapon_effectiveness(tribute, best_weapon)
                new_effectiveness = new_stats["damage"] * 0.5 + new_stats["accuracy"] * 0.3 + new_stats["speed"] * 0.2

            if new_effectiveness > current_effectiveness * 1.2:  # 20% improvement threshold
                blackboard['target_weapon'] = best_weapon
                blackboard['chosen_action'] = 'scavenge_weapon'
                return NodeStatus.SUCCESS

        blackboard['chosen_action'] = 'scavenge'
        return NodeStatus.SUCCESS

    def _perform_idle_action(self, tribute: Tribute, game_state, blackboard: Dict) -> NodeStatus:
        actions = ['idle', 'alliance', 'sponsor']  # Don't include fight as primary idle action
        
        # Add torch burning if tribute has a torch
        if tribute.has_torch:
            actions.append('torch_burn')
        
        blackboard['chosen_action'] = random.choice(actions)
        return NodeStatus.SUCCESS