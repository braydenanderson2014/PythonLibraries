"""
Skill-based probability calculations for balanced gameplay.
Provides diminishing returns and random chance elements.
"""
import random
import math

def skill_modifier(skill_value, neutral_value=5, max_modifier=2.0, curve_steepness=0.5):
    """
    Calculate skill modifier with diminishing returns.
    skill_value: Current skill (1-10)
    neutral_value: Skill value with no modifier (usually 5)
    max_modifier: Maximum multiplier (e.g., 2.0 = 200% at skill 10)
    curve_steepness: How quickly returns diminish (higher = more diminishing)
    """
    diff = skill_value - neutral_value
    if diff == 0:
        return 1.0

    # Diminishing returns using tanh function
    normalized_diff = diff / 5.0  # Normalize to -1 to 1 range
    modifier = math.tanh(normalized_diff * curve_steepness) * (max_modifier - 1.0) + 1.0

    return max(0.1, min(max_modifier, modifier))

def skill_chance(base_chance, skill_value, skill_name=None, tribute=None, random_factor=0.2):
    """
    Calculate success chance based on skill with random variation.
    base_chance: Base probability (0.0-1.0)
    skill_value: Skill level (1-10)
    random_factor: How much pure randomness to add (0.0-1.0)
    """
    # Get skill modifier
    modifier = skill_modifier(skill_value)

    # Apply modifier to base chance
    modified_chance = base_chance * modifier

    # Add random variation
    random_variation = random.uniform(-random_factor, random_factor)
    final_chance = modified_chance + random_variation

    # Clamp to valid range
    return max(0.05, min(0.95, final_chance))

def opposed_skill_check(attacker_skill, defender_skill, base_chance=0.5, random_factor=0.3):
    """
    Check between two opposing skills (e.g., speed vs speed for outrunning).
    Returns True if attacker succeeds.
    """
    # Calculate relative skill difference
    skill_diff = attacker_skill - defender_skill
    adjusted_chance = base_chance + (skill_diff * 0.1)  # ±10% per skill point difference

    # Add diminishing returns
    if skill_diff > 0:
        adjusted_chance *= skill_modifier(attacker_skill, neutral_value=defender_skill)
    elif skill_diff < 0:
        adjusted_chance *= (1.0 / skill_modifier(defender_skill, neutral_value=attacker_skill))

    # Add random factor
    random_variation = random.uniform(-random_factor, random_factor)
    final_chance = adjusted_chance + random_variation

    return random.random() < max(0.05, min(0.95, final_chance))

def resource_gathering_chance(skill_value, difficulty=1.0, environmental_factor=1.0):
    """
    Calculate chance of successfully gathering resources.
    skill_value: Relevant skill (e.g., hunting for food)
    difficulty: How hard the task is (1.0 = normal)
    environmental_factor: Environmental modifiers (0.5-2.0)
    """
    base_chance = 0.6  # 60% base success rate
    skill_mod = skill_modifier(skill_value)
    difficulty_mod = 1.0 / difficulty

    final_chance = base_chance * skill_mod * difficulty_mod * environmental_factor

    # Add random element
    random_factor = random.uniform(-0.2, 0.2)
    return max(0.1, min(0.9, final_chance + random_factor))

def combat_evasion_chance(speed, intelligence, weapon_penalty=0, terrain_factor=1.0):
    """
    Calculate chance to evade or outrun in combat.
    Includes chance of tripping/fumbling even for high skill.
    """
    # Base chance depends on speed
    base_chance = skill_chance(0.25, speed, random_factor=0.3)

    # Intelligence helps with strategy
    int_modifier = skill_modifier(intelligence, max_modifier=1.5)

    # Weapon penalty (heavier weapons harder to run with)
    weapon_mod = max(0.5, 1.0 - weapon_penalty)

    # Terrain affects movement
    terrain_mod = terrain_factor

    final_chance = base_chance * int_modifier * weapon_mod * terrain_mod

    # Even high skill characters can trip (minimum failure chance)
    if random.random() < 0.05:  # 5% chance of critical fumble
        final_chance *= 0.3

    return max(0.05, min(0.6, final_chance))