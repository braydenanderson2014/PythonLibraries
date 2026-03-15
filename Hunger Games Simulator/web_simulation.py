#!/usr/bin/env python3
"""
Web mode runner for Hunger Games Simulator.
Runs the simulation automatically without user interaction.
"""

import sys
import os
import json
import random
from core.game_state import GameState
from tributes.tribute import Tribute
from utils.filter import work_friendly
from utils.generator import generate_random_tribute
from utils.custom_tributes import custom_tribute_manager
from combat import fight
from events import trigger_random_event
from events.idle import get_idle_event
from events.arena_events import trigger_random_arena_event, process_ongoing_environmental_effects, process_tribute_ongoing_effects

def run_web_simulation():
    """Run the Hunger Games simulation in web mode (non-interactive)."""
    print("Starting Hunger Games Simulation (Web Mode)")

    # Load custom tributes from tribute_upload.json
    try:
        with open("data/tribute_upload.json", "r") as f:
            custom_data = json.load(f)
        custom_tributes = custom_data.get("custom_tributes", [])
        print(f"Loaded {len(custom_tributes)} custom tributes")
    except FileNotFoundError:
        print("No custom tributes found, using generated tributes")
        custom_tributes = []

    # Create tributes
    tributes = []

    # Add custom tributes first
    for tribute_data in custom_tributes:
        try:
            tribute = Tribute(
                name=tribute_data["name"],
                skills=tribute_data["skills"],
                weapons=tribute_data.get("weapons", ["Fists"]),
                district=tribute_data.get("district", 1),
                speed=tribute_data.get("speed", 5)
            )

            if "preferred_weapon" in tribute_data:
                tribute.set_preferred_weapon(tribute_data["preferred_weapon"])
            if "target_weapon" in tribute_data and tribute_data["target_weapon"]:
                tribute.set_target_weapon(tribute_data["target_weapon"])

            # Set health and sanity if provided
            if "health" in tribute_data:
                tribute.health = tribute_data["health"]
            if "sanity" in tribute_data:
                tribute.sanity = tribute_data["sanity"]

            # Add relationships if provided
            if "relationships" in tribute_data:
                for rel_name, rel_type in tribute_data["relationships"].items():
                    tribute.add_relationship(rel_name, rel_type)

            tributes.append(tribute)
            print(f"Added custom tribute: {tribute.name}")
        except Exception as e:
            print(f"Error loading tribute {tribute_data.get('name', 'Unknown')}: {e}")
            continue

    # Fill remaining slots with generated tributes if needed
    while len(tributes) < 24:
        tribute = generate_random_tribute()
        # Ensure unique names
        existing_names = [t.name for t in tributes]
        attempts = 0
        while tribute.name in existing_names and attempts < 10:
            tribute = generate_random_tribute()
            attempts += 1
        tributes.append(tribute)
        print(f"Added generated tribute: {tribute.name}")

    # Limit to 24 tributes
    tributes = tributes[:24]

    print(f"Starting game with {len(tributes)} tributes")

    # Load and apply pre-game alliances and targets
    try:
        with open("data/pregame_data.json", "r") as f:
            pregame_data = json.load(f)
        
        alliances = pregame_data.get("alliances", [])
        targets = pregame_data.get("targets", [])
        
        print(f"Loaded {len(alliances)} pre-game alliances and {len(targets)} targets")
        
        # Apply alliances
        for alliance in alliances:
            initiator_name = alliance["initiator"]
            target_name = alliance["target"]
            
            # Find the tributes
            initiator = next((t for t in tributes if t.name == initiator_name), None)
            target = next((t for t in tributes if t.name == target_name), None)
            
            if initiator and target:
                # Create a positive relationship (alliance)
                game.update_tribute_relationship(initiator.tribute_id, target.tribute_id, 40)  # Strong positive relationship
                print(f"Applied alliance: {initiator_name} ↔ {target_name}")
            else:
                print(f"Warning: Could not find tributes for alliance {initiator_name} ↔ {target_name}")
        
        # Apply targets (these will be used by AI decision making)
        for target_data in targets:
            hunter_name = target_data["hunter"]
            target_name = target_data["target"]
            
            # Find the tributes
            hunter = next((t for t in tributes if t.name == hunter_name), None)
            target = next((t for t in tributes if t.name == target_name), None)
            
            if hunter and target:
                # Create a negative relationship (rivalry/targeting)
                game.update_tribute_relationship(hunter.tribute_id, target.tribute_id, -30)  # Negative relationship
                print(f"Applied targeting: {hunter_name} → {target_name}")
            else:
                print(f"Warning: Could not find tributes for targeting {hunter_name} → {target_name}")
                
    except FileNotFoundError:
        print("No pre-game data found, starting with neutral relationships")
    except Exception as e:
        print(f"Error loading pre-game data: {e}")

    # Initialize game
    game = GameState()
    game.active_tributes = tributes.copy()

    # Save initial state
    game.save()

    # Main game loop
    max_turns = 100  # Prevent infinite loops
    turn_count = 0

    while len(game.active_tributes) > 1 and turn_count < max_turns:
        turn_count += 1
        print(f"\n--- Turn {turn_count} ---")
        print(f"Active tributes: {len(game.active_tributes)}")

        # Process ongoing effects
        process_ongoing_environmental_effects(game)
        process_tribute_ongoing_effects(game)

        # Bloodbath phase (first turn only)
        if turn_count == 1:
            print("BLOODBATH PHASE")
            # Simple bloodbath - each tribute has a chance to find a weapon
            for tribute in game.active_tributes:
                if random.random() < 0.3:  # 30% chance
                    available_weapons = ["Knife", "Sword", "Axe", "Bow", "Spear", "Club"]
                    weapon = random.choice(available_weapons)
                    tribute.add_weapon(weapon)
                    print(f"WINNER: {tribute.name} finds a {weapon} in the bloodbath!")

        # Feasts and sponsor gifts (simplified)
        if random.random() < 0.1:  # 10% chance per turn
            lucky_tribute = random.choice(game.active_tributes)
            lucky_tribute.health = min(100, lucky_tribute.health + random.randint(10, 30))
            print(f"SPONSOR GIFT: {lucky_tribute.name} receives a sponsor gift!")

        # Random encounters between tributes
        active_count = len(game.active_tributes)
        if active_count >= 3 and random.random() < 0.4:  # 40% chance when 3+ tributes
            # Select 2-4 random tributes for encounter
            encounter_size = min(random.randint(2, 4), active_count)
            encounter_tributes = random.sample(game.active_tributes, encounter_size)

            print(f"RANDOM ENCOUNTER between {', '.join([t.name for t in encounter_tributes])}")

            # Simple combat resolution
            survivors = []
            for tribute in encounter_tributes:
                # Simple survival chance based on skills
                skill_values = list(tribute.skills.values())
                average_skill = sum(skill_values) / len(skill_values) if skill_values else 5
                survival_chance = (average_skill / 10) * 0.8 + 0.2  # 20-100% chance
                if random.random() < survival_chance:
                    survivors.append(tribute)
                else:
                    print(f"DEATH: {tribute.name} falls in combat!")
                    game.active_tributes.remove(tribute)

            if len(survivors) == 1:
                print(f"VICTOR: {survivors[0].name} emerges victorious from the random encounter!")
            elif len(survivors) > 1:
                print(f"The random encounter ends with {len(survivors)} tributes surviving.")

        # Environmental events and idle activities
        for tribute in game.active_tributes:
            if random.random() < 0.3:  # 30% chance per tribute per turn
                # Simple environmental damage
                damage = random.randint(5, 15)
                tribute.health -= damage
                if tribute.health <= 0:
                    print(f"DEATH: {tribute.name} succumbs to environmental hazards!")
                    game.active_tributes.remove(tribute)

        # Advance phase
        game.advance_phase()
        game.save()

        # Break if only one tribute left
        if len(game.active_tributes) <= 1:
            break

    # Determine winner
    winner = game.active_tributes[0] if game.active_tributes else None

    if winner:
        print(f"\nWINNER: {winner.name} from District {winner.district}!")
        return {
            'success': True,
            'winner': winner.name,
            'stats': {
                'total_tributes': len(tributes),
                'turns_survived': turn_count,
                'final_tributes': len(game.active_tributes)
            }
        }
    else:
        print("\nNo winner - all tributes eliminated!")
        return {
            'success': False,
            'winner': 'None',
            'stats': {
                'total_tributes': len(tributes),
                'turns_survived': turn_count,
                'final_tributes': 0
            }
        }

if __name__ == '__main__':
    result = run_web_simulation()
    print("\nSimulation Results:")
    print(json.dumps(result, indent=2))