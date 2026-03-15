#!/usr/bin/env python3
"""
Quick test script to verify that combat is happening and tributes are dying.
"""

import sys
import os
sys.path.append('.')

from core.game_state import GameState
from tributes.tribute import Tribute
from utils.generator import generate_random_tribute
from combat import fight
import random

def test_combat_frequency():
    """Test that combat happens and tributes die."""
    print("Testing combat frequency and deaths...")

    # Create a small game with 6 tributes
    game = GameState()
    tributes = []

    # Generate 6 random tributes
    for i in range(6):
        tribute = generate_random_tribute()
        tributes.append(tribute)

    game.active_tributes = tributes

    print(f"Starting with {len(game.active_tributes)} tributes:")
    for t in game.active_tributes:
        print(f"  {t.name} (District {t.district}) - Health: {t.health}")

    # Simulate 10 phases
    phases_simulated = 0
    max_phases = 10

    while len(game.active_tributes) > 1 and phases_simulated < max_phases:
        phases_simulated += 1
        print(f"\n--- Phase {phases_simulated} ---")

        # Random encounters (like the new system)
        if len(game.active_tributes) >= 3:
            encounter_chance = 0.3  # 30% chance for testing
            if random.random() < encounter_chance:
                num_in_encounter = min(3, len(game.active_tributes))
                encounter_tributes = random.sample(game.active_tributes, num_in_encounter)

                print(f"Random Encounter! {len(encounter_tributes)} tributes:")
                for t in encounter_tributes:
                    print(f"  - {t.name}")

                # Force fights
                if len(encounter_tributes) >= 2:
                    for i in range(len(encounter_tributes) - 1):
                        attacker = encounter_tributes[i]
                        defender = encounter_tributes[i + 1]

                        if random.random() < 0.6:  # 60% chance to fight
                            print(f"{attacker.name} attacks {defender.name}!")

                            # Simple fight simulation
                            attacker_damage = random.randint(10, 30)
                            defender_damage = random.randint(5, 20)

                            defender.health -= attacker_damage
                            if defender.health <= 0:
                                print(f"{defender.name} dies!")
                                game.eliminated_tributes.append(defender)
                                game.active_tributes.remove(defender)
                            else:
                                attacker.health -= defender_damage
                                if attacker.health <= 0:
                                    print(f"{attacker.name} dies in the counterattack!")
                                    game.eliminated_tributes.append(attacker)
                                    game.active_tributes.remove(attacker)
                                else:
                                    print(f"Both survive but are injured.")

        # Apply resource decay
        for tribute in game.active_tributes[:]:
            # Realistic decay for testing (12-20 food, 15-25 water per evening)
            tribute.food = max(0, tribute.food - random.randint(12, 20))
            tribute.water = max(0, tribute.water - random.randint(15, 25))

            if tribute.food <= 0:
                print(f"{tribute.name} dies from starvation!")
                game.eliminated_tributes.append(tribute)
                game.active_tributes.remove(tribute)
            elif tribute.water <= 0:
                print(f"{tribute.name} dies from dehydration!")
                game.eliminated_tributes.append(tribute)
                game.active_tributes.remove(tribute)

        print(f"Active tributes remaining: {len(game.active_tributes)}")

    print("\nFinal result:")
    print(f"Phases simulated: {phases_simulated}")
    print(f"Tributes remaining: {len(game.active_tributes)}")
    print(f"Tributes eliminated: {len(game.eliminated_tributes)}")

    if game.active_tributes:
        winner = game.active_tributes[0]
        print(f"Winner: {winner.name}")
    else:
        print("All tributes died!")

if __name__ == "__main__":
    test_combat_frequency()