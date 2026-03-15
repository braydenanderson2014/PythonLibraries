#!/usr/bin/env python
"""Test script for the Nemesis Behavior Engine"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from NemesisBehaviorEngine import NemesisBehaviorEngine, ActionType
from Engine.tribute import Tribute

def create_test_tribute():
    """Create a test tribute with various conditions"""
    tribute_data = {
        "name": "Test Tribute",
        "district": 1,
        "skills": {
            "strength": 7,
            "agility": 6,
            "intelligence": 8,
            "survival": 5,
            "combat": 7
        },
        "trait_scores": {
            "combat": 75,
            "survival": 60,
            "intelligence": 80,
            "strength": 70,
            "agility": 65
        }
    }

    tribute = Tribute("test_tribute_1", tribute_data)

    # Add some medical conditions for testing
    tribute.bleeding_wounds = [
        {"level": "medium", "location": "arm", "duration": 2},
        {"level": "mild", "location": "leg", "duration": 1}
    ]
    tribute.infections = [
        {"level": "severe", "location": "arm", "duration": 3},  # High resistance
        {"level": "mild", "location": "leg", "duration": 1}    # Low resistance
    ]
    tribute.extremities["left_arm"] = "injured"
    tribute.health = 65
    tribute.hunger = 45
    tribute.thirst = 30
    tribute.fatigue = 25

    # Add some resources
    tribute.medical_supplies = ["bandage", "antibiotic"]
    tribute.weapons = ["knife", "bow"]
    tribute.food_supplies = 1

    return tribute

def create_game_state():
    """Create a mock game state"""
    # Create proper mock tribute objects
    MockTribute = type('MockTribute', (), {
        'tribute_id': None,
        'health': 80,
        'weapons': [],
        'skills': {"combat": 5, "strength": 5},
        'district': 2,
        'trait_scores': {},
        'alliances': set(),
        'enemies': set()
    })

    enemy = MockTribute()
    enemy.tribute_id = "enemy_1"
    enemy.health = 80
    enemy.weapons = []  # No weapons to avoid combat calculation
    enemy.skills = {"combat": 6, "strength": 6}
    enemy.district = 2
    enemy.conditions = ["healthy"]

    ally = MockTribute()
    ally.tribute_id = "ally_1"
    ally.health = 90
    ally.weapons = []  # No weapons to avoid combat calculation
    ally.skills = {"combat": 5, "survival": 8}
    ally.district = 1
    ally.conditions = ["healthy"]

    return {
        "tributes": {
            "enemy_1": enemy,
            "ally_1": ally
        },
        "current_phase": 5,
        "time_of_day": "day",
        "events": []
    }

def test_behavior_engine():
    """Test the behavior engine with a sample tribute"""
    print("=== Nemesis Behavior Engine Test ===\n")

    # Initialize the behavior engine
    engine = NemesisBehaviorEngine()

    # Create test tribute
    tribute = create_test_tribute()
    game_state = create_game_state()

    print(f"Tribute: {tribute.name} (District {tribute.district})")
    print(f"Health: {tribute.health}%, Hunger: {tribute.hunger}%, Thirst: {tribute.thirst}%")
    print(f"Bleeding wounds: {len(tribute.bleeding_wounds)}, Infections: {len(tribute.infections)}")
    print(f"Weapons: {tribute.weapons}, Medical supplies: {tribute.medical_supplies}")
    print(f"Trait scores: {tribute.trait_scores}")
    print()

    # Make a decision
    decision = engine.make_decision(tribute, game_state)

    print("=== Decision Made ===")
    print(f"Action: {decision.action_type.value}")
    if decision.target:
        print(f"Target: {decision.target}")
    if decision.location:
        print(f"Location: {decision.location}")
    print(".2f")
    print(".2f")
    print(f"Time required: {decision.time_required} phases")
    print(f"Resource cost: {decision.resource_cost}")
    print()

    # Show reasoning
    reasoning = engine._get_decision_reasoning(tribute, decision)
    print(f"Reasoning: {reasoning}")
    print()

    # Show decision history
    print("=== Decision History ===")
    for entry in tribute.decision_history[-3:]:  # Show last 3 decisions
        print(f"- {entry['action']} (score: {entry['score']:.2f})")
        print(f"  Reasoning: {entry['reasoning']}")

if __name__ == "__main__":
    test_behavior_engine()