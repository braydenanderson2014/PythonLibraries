import random
import json
from typing import Tuple, Optional, List
from tributes.tribute import Tribute
from utils.custom_tributes import custom_tribute_manager
from utils.skills import combat_evasion_chance

def select_combat_target(attacker: Tribute, available_targets: List[Tribute]) -> Optional[Tribute]:
    """
    Select a combat target based on relationship biases and other factors.
    Returns the selected target or None if no valid targets.
    """
    if not available_targets:
        return None

    # Filter out allies (unless betrayal chance)
    valid_targets = []
    weights = []

    for target in available_targets:
        if target == attacker:
            continue

        weight = 1.0

        # Relationship bias
        relationship_bias = custom_tribute_manager.get_relationship_bias(attacker.name, target.name, attacker)
        weight *= relationship_bias

        # Don't attack allies unless betrayal
        if attacker.is_ally(target.name):
            betrayal_chance = 0.1  # 10% chance to betray allies
            if random.random() > betrayal_chance:
                continue  # Skip this ally
            else:
                weight *= 0.5  # Reduce weight even for betrayal

        # Tributes with allies are more aggressive toward non-allies
        if len(attacker.allies) > 0 and not attacker.is_ally(target.name):
            weight *= 2.0  # Double the chance to attack non-allies when you have allies

        # Prefer targets WITHOUT weapons (easier to kill, less threatening)
        if len(target.weapons) <= 1:  # Only fists
            weight *= 1.5  # Much more likely to attack unarmed targets

        # Prefer injured targets (easier to kill)
        if target.health < 50:
            weight *= 1.3

        # Avoid targets that are much stronger
        strength_diff = attacker.skills.get('strength', 5) - target.skills.get('strength', 5)
        if strength_diff < -3:
            weight *= 0.7  # Less likely to attack much stronger opponents

        valid_targets.append(target)
        weights.append(weight)

    if not valid_targets:
        return None

    # Weighted random selection
    total_weight = sum(weights)
    if total_weight == 0:
        return random.choice(valid_targets)

    pick = random.uniform(0, total_weight)
    current_weight = 0

    for i, weight in enumerate(weights):
        current_weight += weight
        if pick <= current_weight:
            return valid_targets[i]

    return valid_targets[-1]  # Fallback

def apply_weapon_effects(attacker: Tribute, defender: Tribute, weapon_data: dict, distance: int, get_message) -> bool:
    """
    Apply bleeding and instant kill effects for all weapons.
    Returns True if instant kill occurred.
    """
    bleeding_chance = weapon_data.get("bleeding_chance", 0.0)
    instant_kill_chance = weapon_data.get("instant_kill_chance", 0.0)
    
    # For ranged weapons, adjust chances based on distance
    if weapon_data.get("type") == "ranged":
        close_range_multiplier = weapon_data.get("close_range_multiplier", 1.0)
        if distance == 1:  # Close range
            bleeding_chance *= close_range_multiplier
            instant_kill_chance *= close_range_multiplier
        else:
            # Reduce chances dramatically at longer range
            distance_penalty = 1.0 / (distance * distance)  # Inverse square law approximation
            bleeding_chance *= distance_penalty
            instant_kill_chance *= distance_penalty
    
    # Check for instant kill first
    if random.random() < instant_kill_chance:
        print(f"CRITICAL HIT! {attacker.current_weapon} instantly kills {defender.name}!")
        defender.health = 0
        defender.status = 'eliminated'
        attacker.kills.append(defender.name)
        attacker.sanity = max(0, attacker.sanity - random.randint(10, 20))  # Higher sanity loss for instant kill
        return True
    
    # Check for bleeding - now sets bleeding status instead of immediate damage
    if random.random() < bleeding_chance and defender.bleeding == 'none':
        # Determine bleeding severity based on weapon and random chance
        severity_roll = random.random()
        weapon_bleeding_power = weapon_data.get("bleeding_chance", 0.0) * 100  # Convert to percentage
        
        if severity_roll < 0.1:  # 10% chance of fatal bleeding
            defender.bleeding = 'fatal'
            defender.bleeding_days = 0  # Reset counter for new bleeding
            print(get_message("bleeding", "fatal_wound", name=defender.name, weapon=attacker.current_weapon))
        elif severity_roll < 0.4 or weapon_bleeding_power > 20:  # 30% chance or high-bleeding weapons
            defender.bleeding = 'severe'
            defender.bleeding_days = 0  # Reset counter for new bleeding
            print(get_message("bleeding", "severe_wound", name=defender.name, weapon=attacker.current_weapon))
        else:  # 60% chance of mild bleeding
            defender.bleeding = 'mild'
            defender.bleeding_days = 0  # Reset counter for new bleeding
            print(get_message("bleeding", "mild_wound", name=defender.name, weapon=attacker.current_weapon))
        
        # Chance of infection for any bleeding
        if random.random() < 0.15:  # 15% chance
            defender.infection = True
            print(get_message("bleeding", "infection", name=defender.name))
    
    return False

def apply_bleeding_effects(tribute: Tribute, allies: List[Tribute], get_message) -> bool:
    """
    Apply ongoing bleeding effects each phase.
    Returns True if tribute died from bleeding.
    """
    if tribute.bleeding == 'none':
        return False
    
    tribute.bleeding_days += 1
    tribute.total_bleeding_phases += 1
    
    # Check for infection based on total bleeding phases (3 days = 9 phases)
    if not tribute.infection and tribute.total_bleeding_phases >= 9:
        if random.random() < 0.3:  # 30% chance after 3 days
            tribute.infection = True
            print(get_message("bleeding", "infection", name=tribute.name))
            # Infection from bleeding causes sickness
            tribute.contract_sickness('infection')
    
    # Base damage and effects vary by severity
    if tribute.bleeding == 'fatal':
        # Fatal bleeding causes death within 1 phase
        damage = random.randint(30, 50)
        tribute.health -= damage
        print(get_message("bleeding", "fatal_bleeding", name=tribute.name, damage=damage))
        
        if tribute.health <= 0 or tribute.bleeding_days >= 1:
            tribute.status = 'eliminated'
            print(get_message("bleeding", "fatal_death", name=tribute.name))
            return True
            
    elif tribute.bleeding == 'severe':
        damage = random.randint(8, 18)
        tribute.health -= damage
        print(get_message("bleeding", "severe_bleeding", name=tribute.name, damage=damage))
        
        # Severe bleeding can become fatal if untreated for too long (up to 1.5 days = 4-5 phases)
        if tribute.bleeding_days >= 5:
            tribute.bleeding = 'fatal'
            print(get_message("bleeding", "severe_to_fatal", name=tribute.name))
        elif tribute.bleeding_days >= 3 and random.random() < 0.4:  # Chance to become fatal after 1 day
            tribute.bleeding = 'fatal'
            print(get_message("bleeding", "severe_to_fatal", name=tribute.name))
            
        # Chance for self-treatment or ally help
        treatment_chance = 0.1  # 10% base chance for self-treatment
        treatment_chance += tribute.skills.get('intelligence', 5) * 0.01  # Intelligence helps
        
        # Allies can help
        ally_help = False
        for ally in allies:
            if ally.status == 'active' and ally.name in tribute.allies:
                treatment_chance += 0.15  # 15% bonus per active ally
                ally_help = True
                ally_name = ally.name
                break  # One ally helping is enough
                
        if random.random() < treatment_chance:
            tribute.bleeding = 'mild'
            tribute.bleeding_days = 0
            tribute.total_bleeding_phases = 0  # Reset total when treated
            if ally_help:
                print(get_message("bleeding", "ally_treatment", name=tribute.name, ally=ally_name))
            else:
                print(get_message("bleeding", "self_treatment", name=tribute.name))
            
    elif tribute.bleeding == 'mild':
        damage = random.randint(2, 6)
        tribute.health -= damage
        print(get_message("bleeding", "mild_bleeding", name=tribute.name, damage=damage))
        
        # Mild bleeding lasts only 1 phase, then heals
        if tribute.bleeding_days >= 1:
            tribute.bleeding = 'none'
            tribute.bleeding_days = 0
            tribute.total_bleeding_phases = 0  # Reset total when fully healed
            print(get_message("bleeding", "natural_healing", name=tribute.name))
    
    # Infection effects
    if tribute.infection:
        infection_damage = random.randint(3, 8)
        tribute.health -= infection_damage
        sanity_loss = random.randint(5, 15)
        tribute.sanity -= sanity_loss
        print(get_message("bleeding", "infection_effect", name=tribute.name, damage=infection_damage, sanity=sanity_loss))
        
        # Infection can spread or worsen bleeding
        if random.random() < 0.2:  # 20% chance
            if tribute.bleeding == 'mild':
                tribute.bleeding = 'severe'
                print(get_message("bleeding", "infection_worsens", name=tribute.name))
            elif tribute.bleeding == 'severe' and random.random() < 0.5:
                tribute.bleeding = 'fatal'
                print(get_message("bleeding", "infection_fatal", name=tribute.name))
    
    # Check for death from accumulated damage
    if tribute.health <= 0:
        tribute.status = 'eliminated'
        print(get_message("bleeding", "bleeding_death", name=tribute.name))
        return True
        
    return False

def pickup_weapon(tribute: Tribute, weapon: str, get_message, print_message: bool = True) -> bool:
    """
    Allow a tribute to pick up a weapon from the environment.
    Automatically equips the weapon if it's better than current weapon based on preferences.
    Returns True if weapon was picked up.
    """
    if tribute.add_weapon(weapon):
        if print_message:
            print(get_message("combat", "pickup_weapon", tribute=tribute.name, weapon=weapon))

        # Automatically equip if this weapon is better than current based on preferences
        if weapon == tribute.get_best_weapon() and weapon != tribute.current_weapon:
            tribute.switch_weapon(weapon)
            if print_message:
                print(f"{tribute.name} equips the {weapon} as their new primary weapon!")

        return True
    else:
        if print_message:
            print(get_message("combat", "already_has_weapon", tribute=tribute.name, weapon=weapon))
        return False

def steal_weapon(thief: Tribute, victim: Tribute, weapon: str, get_message) -> bool:
    """
    Allow one tribute to steal a weapon from another.
    Returns True if weapon was stolen.
    """
    if weapon in victim.weapons and weapon != "Fists":
        if victim.remove_weapon(weapon):
            thief.add_weapon(weapon)
            print(get_message("combat", "steal_weapon", thief=thief.name, victim=victim.name, weapon=weapon))
            return True
    print(get_message("combat", "steal_weapon_fail", thief=thief.name, victim=victim.name, weapon=weapon))
    return False

def disarm_tribute(attacker: Tribute, defender: Tribute, get_message) -> bool:
    """
    Attempt to disarm a tribute, forcing them to drop their current weapon.
    Returns True if disarmed.
    """
    # Success based on attacker's strength vs defender's strength and weapon hands
    with open('data/weapons.json', 'r') as f:
        weapons_data = json.load(f)
    
    def_weapon = weapons_data.get(defender.current_weapon, {"hands": 1})
    weapon_hands = def_weapon.get("hands", 1)
    
    # Harder to disarm two-handed weapons
    disarm_chance = 0.3 + (attacker.skills['strength'] - defender.skills['strength']) * 0.05
    disarm_chance /= weapon_hands  # Divide by number of hands (harder for 2-handed weapons)
    
    if random.random() < disarm_chance and defender.current_weapon != "Fists":
        dropped_weapon = defender.current_weapon
        defender.remove_weapon(dropped_weapon)
        print(get_message("combat", "disarm_success", attacker=attacker.name, defender=defender.name, weapon=dropped_weapon))
        return True
    else:
        print(get_message("combat", "disarm_fail", attacker=attacker.name, defender=defender.name))
        return False

def conjugate_verb_present_continuous(verb: str) -> str:
    """
    Conjugate a verb to present continuous tense (e.g., 'poke' -> 'poking').
    Handles basic English conjugation rules.
    """
    verb = verb.lower()
    if verb.endswith('e'):
        # Drop the 'e' and add 'ing' (hope -> hoping, poke -> poking)
        return verb[:-1] + 'ing'
    elif verb.endswith(('sh', 'ch', 's', 'x', 'z', 'o')):
        # Don't double these endings
        return verb + 'ing'
    elif len(verb) >= 3 and verb[-1] not in 'aeiouy' and verb[-2] in 'aeiouy' and verb[-3] not in 'aeiouy':
        # Double the final consonant for CVC pattern (run -> running, begin -> beginning)
        # But skip if it's already a proper noun or special case
        return verb + verb[-1] + 'ing'
    else:
        # Default: just add 'ing'
        return verb + 'ing'

def fight(attacker: Tribute, defender: Tribute, get_message, distance: int = 1, initial_phase: bool = False, game_config: dict = None) -> Tuple[Optional[Tribute], Optional[Tribute], str]:
    """
    Simulates a fight between two tributes.
    Returns (winner, loser) if someone dies, else (None, None) if both survive
    distance: 1 = close range, higher numbers = longer range
    """
    with open('data/weapons.json', 'r') as f:
        weapons_data = json.load(f)
    
    # Speed/intelligence check: defender can outrun or outsmart attacker
    # Calculate weapon penalty based on hands (2-handed weapons harder to run with)
    def_weapon_hands = weapons_data.get(defender.current_weapon, {"hands": 1}).get("hands", 1)
    weapon_penalty = (def_weapon_hands - 1) * 0.2  # 0 for 1-handed, 0.2 for 2-handed
    
    evasion_chance = combat_evasion_chance(defender.get_effective_speed(), defender.skills['intelligence'], weapon_penalty)
    if random.random() < evasion_chance:
        print(get_message("combat", "outrun", defender=defender.name, attacker=attacker.name))
        return None, None, "evasion"  # Evasion occurred, no fight
    
    # SANITY LOSS: Getting into a fight reduces sanity for both participants
    attacker.sanity = max(0, attacker.sanity - random.randint(3, 8))  # 3-8 sanity loss for fighting
    defender.sanity = max(0, defender.sanity - random.randint(3, 8))  # 3-8 sanity loss for fighting
    
    # Track combat for retaliation system
    attacker.track_combat(defender)
    defender.track_combat(attacker)
    
    att_weapon = weapons_data.get(attacker.current_weapon, {"damage": 10})
    def_weapon = weapons_data.get(defender.current_weapon, {"damage": 10})
    
    # Attacker strikes first - check for miss
    miss_chance = att_weapon.get("miss_chance", 0.0)
    att_use_types = att_weapon.get("use_types", ["attacks"])
    att_verb = conjugate_verb_present_continuous(random.choice(att_use_types))
    
    if random.random() < miss_chance:
        # Check for near miss - slight hit causing minor bleeding
        near_miss_bleeding_chance = miss_chance * 0.3  # 30% of miss chance becomes near miss bleeding chance
        if random.random() < near_miss_bleeding_chance and defender.bleeding == 'none':
            defender.bleeding = 'mild'
            defender.health -= random.randint(1, 5)  # Minor damage from near miss
            print(get_message("combat", "near_miss_bleeding", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, damage=random.randint(1, 5), health=defender.health))
        else:
            print(get_message("combat", "miss", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb))
    else:
        # Calculate damage with bleeding chance modifier
        strength_modifier = 1.0 + (attacker.skills.get('strength', 5) - 5) * 0.1  # 10% damage per strength point above 5
        base_damage = int((att_weapon["damage"] + random.randint(0, 10)) * strength_modifier)
        bleeding_modifier = att_weapon.get("bleeding_chance", 0.0) * 0.5  # Bleeding chance increases damage by up to 50% of its value
        
        # Apply weight penalties
        weight_damage_penalty = attacker.get_damage_penalty()
        weight_speed_penalty = attacker.get_speed_penalty()
        
        damage = int(base_damage * (1 + bleeding_modifier) * weight_damage_penalty)
        defender.health -= damage
        # SANITY LOSS: Losers (those taking damage) lose more sanity than winners
        defender.sanity = max(0, defender.sanity - random.randint(5, 10))  # Loser: 5-10 sanity loss
        attacker.sanity = max(0, attacker.sanity - random.randint(2, 5))   # Winner: 2-5 sanity loss
        
        # Use weapon (degrade durability and consume ammunition)
        weapon_success, weapon_message = attacker.use_weapon(attacker.current_weapon)
        if weapon_message:
            print(f"  {attacker.name}'s {attacker.current_weapon} {weapon_message}")
        
        # Determine weapon effects
        bleeding_chance = att_weapon.get("bleeding_chance", 0.0)
        instant_kill_chance = att_weapon.get("instant_kill_chance", 0.0)
        
        # Apply initial phase multiplier to instant kill chance
        if initial_phase:
            weapon_type = att_weapon.get("type", "melee")
            if weapon_type == "melee":
                instant_kill_chance *= 3.0  # 3x multiplier for melee in initial phase
            elif weapon_type == "ranged":
                if distance == 1:  # Close range ranged weapons
                    instant_kill_chance *= 2.5  # 2.5x multiplier for close-range ranged
                else:
                    instant_kill_chance *= 2.0  # 2x multiplier for long-range ranged
            else:
                instant_kill_chance *= 2.5  # Default boost
        
        # For ranged weapons, adjust chances based on distance
        if att_weapon.get("type") == "ranged":
            close_range_multiplier = att_weapon.get("close_range_multiplier", 1.0)
            if distance == 1:  # Close range
                bleeding_chance *= close_range_multiplier
                instant_kill_chance *= close_range_multiplier
            else:
                # Reduce chances dramatically at longer range
                distance_penalty = 1.0 / (distance * distance)  # Inverse square law approximation
                bleeding_chance *= distance_penalty
                instant_kill_chance *= distance_penalty
        
        # Check for instant kill first
        # Fists cannot deliver fatal blows unless defender health is below 20%
        if attacker.current_weapon == "Fists" and defender.health > 20:
            instant_kill_chance = 0.0
        if random.random() < instant_kill_chance:
            defender.health = 0
            defender.status = 'eliminated'
            attacker.kills.append(defender.name)
            attacker.sanity = max(0, attacker.sanity - random.randint(10, 20))  # Higher sanity loss for instant kill
            print(get_message("combat", "attack_instant_kill", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb))
            return attacker, defender, "kill"
        
        # HEAD SHOT MECHANICS: Chance for head shots (separate from instant kill)
        head_shot_chance = att_weapon.get("head_shot_chance", 0.0)
        if random.random() < head_shot_chance:
            head_damage_roll = random.random()
            if head_damage_roll < 0.3:  # 30% chance of instant death from head shot
                defender.health = 0
                defender.status = 'eliminated'
                attacker.kills.append(defender.name)
                attacker.sanity = max(0, attacker.sanity - random.randint(15, 25))  # High sanity loss for head shot kill
                print(get_message("combat", "head_shot_kill", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb))
                return attacker, defender, "kill"
            else:  # 70% chance of head injury
                if defender.head == 'healthy':
                    defender.head = 'injured'
                    defender.health -= random.randint(10, 20)  # Additional damage from head injury
                    print(get_message("combat", "head_shot_injury", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, damage=random.randint(10, 20), health=defender.health, sanity=defender.sanity))
        
        # LIMB DAMAGE MECHANICS: Chance to damage limbs
        limb_damage_chance = att_weapon.get("limb_damage_chance", 0.0)
        if random.random() < limb_damage_chance:
            # Select random limb to damage
            available_limbs = [limb for limb, status in defender.limbs.items() if status == 'healthy']
            if available_limbs:
                damaged_limb = random.choice(available_limbs)
                limb_damage_roll = random.random()
                
                if limb_damage_roll < 0.4:  # 40% chance of disabling the limb
                    defender.limbs[damaged_limb] = 'disabled'
                    defender.health -= random.randint(5, 15)  # Damage from limb loss
                    
                    # Special effects for disabled limbs
                    if 'arm' in damaged_limb:
                        # Drop weapon if arm is disabled and they have one
                        if defender.current_weapon != "Fists":
                            defender.weapons = [w for w in defender.weapons if w != defender.current_weapon]
                            defender.current_weapon = "Fists"
                            print(get_message("combat", "limb_damage_arm_disabled", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=defender.health, sanity=defender.sanity))
                        else:
                            print(get_message("combat", "limb_damage_arm_disabled_no_weapon", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=defender.health, sanity=defender.sanity))
                    else:  # leg disabled
                        print(get_message("combat", "limb_damage_leg_disabled", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=defender.health, sanity=defender.sanity))
                        
                else:  # 60% chance of injuring the limb
                    attacker.limbs[damaged_limb] = 'injured'
                    attacker.health -= random.randint(3, 10)  # Lesser damage from injury
                    print(get_message("combat", "limb_damage_injury", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=att_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(3, 10), health=attacker.health, sanity=attacker.sanity))
        
        # DISARM/DISLEG MECHANICS: Strength-based chance to disarm or disleg opponent
        attacker_strength = attacker.skills.get('strength', 5)
        defender_strength = defender.skills.get('strength', 5)
        strength_difference = attacker_strength - defender_strength
        
        # Disarm chance: Higher if attacker is much stronger
        if strength_difference >= 3 and defender.current_weapon != "Fists":
            disarm_chance = min(0.3, 0.1 + (strength_difference - 3) * 0.1)  # Max 30% chance
            if random.random() < disarm_chance:
                defender.weapons = [w for w in defender.weapons if w != defender.current_weapon]
                defender.current_weapon = "Fists"
                defender.health -= random.randint(2, 8)  # Minor damage from being disarmed
                print(get_message("combat", "disarm", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, damage=random.randint(2, 8), health=defender.health))
        
        # Disleg chance: Can disable legs if strength difference is significant
        if strength_difference >= 4:
            disleg_chance = min(0.2, 0.05 + (strength_difference - 4) * 0.05)  # Max 20% chance
            if random.random() < disleg_chance:
                # Find a healthy leg to disable
                healthy_legs = [limb for limb, status in defender.limbs.items() if status == 'healthy' and 'leg' in limb]
                if healthy_legs:
                    disabled_leg = random.choice(healthy_legs)
                    defender.limbs[disabled_leg] = 'disabled'
                    defender.health -= random.randint(8, 15)  # Significant damage from leg being disabled
                    print(get_message("combat", "disleg", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, verb=att_verb, limb=disabled_leg.replace('_', ' '), damage=random.randint(8, 15), health=defender.health))
        
        # Check for bleeding
        bleeding_occurred = False
        bleeding_type = None
        if random.random() < bleeding_chance and defender.bleeding == 'none':
            # Determine bleeding severity
            severity_roll = random.random()
            weapon_bleeding_power = att_weapon.get("bleeding_chance", 0.0) * 100  # Convert to percentage
            
            if severity_roll < 0.1:  # 10% chance of fatal bleeding
                defender.bleeding = 'fatal'
                bleeding_type = 'FATAL'
            elif severity_roll < 0.4 or weapon_bleeding_power > 20:  # 30% chance or high-bleeding weapons
                defender.bleeding = 'severe'
                bleeding_type = 'SEVERE'
            else:  # 60% chance of mild bleeding
                defender.bleeding = 'mild'
                bleeding_type = 'MILD'
            bleeding_occurred = True
        
        # Print appropriate message
        if bleeding_occurred:
            print(get_message("combat", "attack_with_bleeding", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, damage=damage, health=defender.health, sanity=defender.sanity, verb=att_verb, bleeding_type=bleeding_type))
        else:
            print(get_message("combat", "attack", attacker=attacker.name, defender=defender.name, weapon=attacker.current_weapon, damage=damage, health=defender.health, sanity=defender.sanity, verb=att_verb))
    
    if defender.health <= 0:
        defender.status = 'eliminated'
        attacker.kills.append(defender.name)
        attacker.sanity = max(0, attacker.sanity - random.randint(5, 10))  # Sanity loss for killing/witnessing death
        return attacker, defender, "kill"
    
    # Defender counterattacks if alive - check for miss
    miss_chance = def_weapon.get("miss_chance", 0.0)
    def_use_types = def_weapon.get("use_types", ["attacks"])
    def_verb = conjugate_verb_present_continuous(random.choice(def_use_types))
    
    if random.random() < miss_chance:
        # Check for near miss - slight hit causing minor bleeding
        near_miss_bleeding_chance = miss_chance * 0.3  # 30% of miss chance becomes near miss bleeding chance
        if random.random() < near_miss_bleeding_chance and attacker.bleeding == 'none':
            attacker.bleeding = 'mild'
            attacker.health -= random.randint(1, 5)  # Minor damage from near miss
            print(get_message("combat", "near_miss_bleeding", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, damage=random.randint(1, 5), health=attacker.health))
        else:
            print(get_message("combat", "miss", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb))
    else:
        # Calculate damage with bleeding chance modifier
        strength_modifier = 1.0 + (defender.skills.get('strength', 5) - 5) * 0.1  # 10% damage per strength point above 5
        base_damage = int((def_weapon["damage"] + random.randint(0, 10)) * strength_modifier)
        bleeding_modifier = def_weapon.get("bleeding_chance", 0.0) * 0.5  # Bleeding chance increases damage by up to 50% of its value
        damage = int(base_damage * (1 + bleeding_modifier))
        attacker.health -= damage
        # SANITY LOSS: Losers (those taking damage) lose more sanity than winners
        attacker.sanity = max(0, attacker.sanity - random.randint(5, 10))  # Loser: 5-10 sanity loss
        defender.sanity = max(0, defender.sanity - random.randint(2, 5))   # Winner: 2-5 sanity loss
        
        # Use weapon (degrade durability and consume ammunition)
        weapon_success, weapon_message = defender.use_weapon(defender.current_weapon)
        if weapon_message:
            print(f"  {defender.name}'s {defender.current_weapon} {weapon_message}")
        
        # Determine weapon effects
        bleeding_chance = def_weapon.get("bleeding_chance", 0.0)
        instant_kill_chance = def_weapon.get("instant_kill_chance", 0.0)
        
        # Apply initial phase multiplier to instant kill chance
        if initial_phase:
            weapon_type = def_weapon.get("type", "melee")
            if weapon_type == "melee":
                instant_kill_chance *= 3.0  # 3x multiplier for melee in initial phase
            elif weapon_type == "ranged":
                if distance == 1:  # Close range ranged weapons
                    instant_kill_chance *= 2.5  # 2.5x multiplier for close-range ranged
                else:
                    instant_kill_chance *= 2.0  # 2x multiplier for long-range ranged
            else:
                instant_kill_chance *= 2.5  # Default boost
        
        # For ranged weapons, adjust chances based on distance
        if def_weapon.get("type") == "ranged":
            close_range_multiplier = def_weapon.get("close_range_multiplier", 1.0)
            if distance == 1:  # Close range
                bleeding_chance *= close_range_multiplier
                instant_kill_chance *= close_range_multiplier
            else:
                # Reduce chances dramatically at longer range
                distance_penalty = 1.0 / (distance * distance)  # Inverse square law approximation
                bleeding_chance *= distance_penalty
                instant_kill_chance *= distance_penalty
        
        # Check for instant kill first
        # Fists cannot deliver fatal blows unless attacker health is below 20%
        if defender.current_weapon == "Fists" and attacker.health > 20:
            instant_kill_chance = 0.0
        if random.random() < instant_kill_chance:
            attacker.health = 0
            attacker.status = 'eliminated'
            defender.kills.append(attacker.name)
            defender.sanity = max(0, defender.sanity - random.randint(10, 20))  # Higher sanity loss for instant kill
            print(get_message("combat", "counterattack_instant_kill", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb))
            return defender, attacker, "kill"
        
        # HEAD SHOT MECHANICS: Chance for head shots (separate from instant kill)
        head_shot_chance = def_weapon.get("head_shot_chance", 0.0)
        if random.random() < head_shot_chance:
            head_damage_roll = random.random()
            if head_damage_roll < 0.3:  # 30% chance of instant death from head shot
                attacker.health = 0
                attacker.status = 'eliminated'
                defender.kills.append(attacker.name)
                defender.sanity = max(0, defender.sanity - random.randint(15, 25))  # High sanity loss for head shot kill
                print(get_message("combat", "head_shot_kill", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb))
                return defender, attacker, "kill"
            else:  # 70% chance of head injury
                if attacker.head == 'healthy':
                    attacker.head = 'injured'
                    attacker.health -= random.randint(10, 20)  # Additional damage from head injury
                    print(get_message("combat", "head_shot_injury", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, damage=random.randint(10, 20), health=attacker.health, sanity=attacker.sanity))
        
        # LIMB DAMAGE MECHANICS: Chance to damage limbs
        limb_damage_chance = def_weapon.get("limb_damage_chance", 0.0)
        if random.random() < limb_damage_chance:
            # Select random limb to damage
            available_limbs = [limb for limb, status in attacker.limbs.items() if status == 'healthy']
            if available_limbs:
                damaged_limb = random.choice(available_limbs)
                limb_damage_roll = random.random()
                
                if limb_damage_roll < 0.4:  # 40% chance of disabling the limb
                    attacker.limbs[damaged_limb] = 'disabled'
                    attacker.health -= random.randint(5, 15)  # Damage from limb loss
                    
                    # Special effects for disabled limbs
                    if 'arm' in damaged_limb:
                        # Drop weapon if arm is disabled and they have one
                        if attacker.current_weapon != "Fists":
                            attacker.weapons = [w for w in attacker.weapons if w != attacker.current_weapon]
                            attacker.current_weapon = "Fists"
                            print(get_message("combat", "limb_damage_arm_disabled", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=attacker.health))
                        else:
                            print(get_message("combat", "limb_damage_arm_disabled_no_weapon", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=attacker.health))
                    else:  # leg disabled
                        print(get_message("combat", "limb_damage_leg_disabled", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(5, 15), health=attacker.health, sanity=attacker.sanity))
                        
                else:  # 60% chance of injuring the limb
                    attacker.limbs[damaged_limb] = 'injured'
                    attacker.health -= random.randint(3, 10)  # Lesser damage from injury
                    print(get_message("combat", "limb_damage_injury", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, limb=damaged_limb.replace('_', ' '), damage=random.randint(3, 10), health=attacker.health, sanity=attacker.sanity))
        
        # DISARM/DISLEG MECHANICS: Strength-based chance to disarm or disleg opponent
        defender_strength = defender.skills.get('strength', 5)
        attacker_strength = attacker.skills.get('strength', 5)
        strength_difference = defender_strength - attacker_strength
        
        # Disarm chance: Higher if defender is much stronger
        if strength_difference >= 3 and attacker.current_weapon != "Fists":
            disarm_chance = min(0.3, 0.1 + (strength_difference - 3) * 0.1)  # Max 30% chance
            if random.random() < disarm_chance:
                attacker.weapons = [w for w in attacker.weapons if w != attacker.current_weapon]
                attacker.switch_weapon("Fists")
                attacker.health -= random.randint(2, 8)  # Minor damage from being disarmed
                print(get_message("combat", "disarm_success", attacker=defender.name, defender=attacker.name, weapon=attacker.current_weapon))
        
        # Disleg chance: Can disable legs if strength difference is significant
        if strength_difference >= 4:
            disleg_chance = min(0.2, 0.05 + (strength_difference - 4) * 0.05)  # Max 20% chance
            if random.random() < disleg_chance:
                # Find a healthy leg to disable
                healthy_legs = [limb for limb, status in attacker.limbs.items() if status == 'healthy' and 'leg' in limb]
                if healthy_legs:
                    disabled_leg = random.choice(healthy_legs)
                    attacker.limbs[disabled_leg] = 'disabled'
                    attacker.health -= random.randint(8, 15)  # Significant damage from leg being disabled
                    print(get_message("combat", "disleg", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, verb=def_verb, limb=disabled_leg.replace('_', ' '), damage=random.randint(8, 15), health=attacker.health, sanity=attacker.sanity))
        
        # Check for bleeding
        bleeding_occurred = False
        bleeding_type = None
        if random.random() < bleeding_chance and attacker.bleeding == 'none':
            # Determine bleeding severity
            severity_roll = random.random()
            weapon_bleeding_power = def_weapon.get("bleeding_chance", 0.0) * 100  # Convert to percentage
            
            if severity_roll < 0.1:  # 10% chance of fatal bleeding
                attacker.bleeding = 'fatal'
                bleeding_type = 'FATAL'
            elif severity_roll < 0.4 or weapon_bleeding_power > 20:  # 30% chance or high-bleeding weapons
                attacker.bleeding = 'severe'
                bleeding_type = 'SEVERE'
            else:  # 60% chance of mild bleeding
                attacker.bleeding = 'mild'
                bleeding_type = 'MILD'
            bleeding_occurred = True
        
        # Print appropriate message
        if bleeding_occurred:
            print(get_message("combat", "counterattack_with_bleeding", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, damage=damage, health=attacker.health, sanity=attacker.sanity, verb=def_verb, bleeding_type=bleeding_type))
        else:
            print(get_message("combat", "counterattack", attacker=defender.name, defender=attacker.name, weapon=defender.current_weapon, damage=damage, health=attacker.health, sanity=attacker.sanity, verb=def_verb))
    
    if attacker.health <= 0:
        attacker.status = 'eliminated'
        defender.kills.append(attacker.name)
        defender.sanity = max(0, defender.sanity - random.randint(5, 10))  # Sanity loss for killing/witnessing death
        return defender, attacker, "kill"
    
    # LUCK-BASED ESCAPE: Defender can miraculously escape if they're losing badly
    defender_luck = defender.skills.get('luck', 5)
    attacker_speed = attacker.get_effective_speed()
    attacker_strength = attacker.skills.get('strength', 5)
    defender_speed = defender.get_effective_speed()
    defender_strength = defender.skills.get('strength', 5)
    
    # Calculate if defender is in a bad situation
    health_disadvantage = max(0, attacker.health - defender.health) / 100.0  # 0-1 scale
    speed_advantage = max(0, attacker_speed - defender_speed) / 10.0  # 0-1 scale (assuming max speed ~10)
    strength_advantage = max(0, attacker_strength - defender_strength) / 10.0  # 0-1 scale
    
    # Combined disadvantage score (0-3, where higher = defender is in worse shape)
    disadvantage_score = health_disadvantage + speed_advantage + strength_advantage
    
    # Base escape chance increases with luck and disadvantage
    base_escape_chance = 0.02  # 2% base chance
    luck_modifier = (defender_luck - 5) * 0.02  # ±2% per luck point from 5
    disadvantage_modifier = disadvantage_score * 0.1  # 10% per point of disadvantage
    
    escape_chance = base_escape_chance + luck_modifier + disadvantage_modifier
    escape_chance = max(0.005, min(0.15, escape_chance))  # Clamp between 0.5% and 15%
    
    if random.random() < escape_chance:
        print(get_message("combat", "lucky_escape", defender=defender.name, attacker=attacker.name))
        return None, None, "escape"
    
    # Both alive, chance to agree not to kill
    agree_chance = game_config["event_probabilities"]["combat"]["agree_stop"] if game_config else 0.3
    if random.random() < agree_chance:
        print(get_message("combat", "agree_stop", name1=attacker.name, name2=defender.name))
        
        # LUCK-BASED BETRAYAL: After agreeing to stop, one tribute might betray the other
        # High luck tributes are more likely to betray, but also better at surviving betrayal
        attacker_luck = attacker.skills.get('luck', 5)
        defender_luck = defender.skills.get('luck', 5)
        
        # Calculate betrayal chances - higher luck = more likely to betray
        attacker_betrayal_chance = 0.1 + (attacker_luck - 5) * 0.02  # Base 10%, ±2% per luck point
        defender_betrayal_chance = 0.1 + (defender_luck - 5) * 0.02  # Base 10%, ±2% per luck point
        
        # Clamp chances between 5% and 25%
        attacker_betrayal_chance = max(0.05, min(0.25, attacker_betrayal_chance))
        defender_betrayal_chance = max(0.05, min(0.25, defender_betrayal_chance))
        
        betrayal_occurred = False
        traitor = None
        victim = None
        
        # Check if attacker betrays defender
        if random.random() < attacker_betrayal_chance:
            betrayal_occurred = True
            traitor = attacker
            victim = defender
        # Check if defender betrays attacker (only if attacker didn't betray)
        elif random.random() < defender_betrayal_chance:
            betrayal_occurred = True
            traitor = defender
            victim = attacker
        
        if betrayal_occurred:
            # The victim gets a luck-based chance to survive the betrayal
            victim_luck = victim.skills.get('luck', 5)
            survival_chance = 0.3 + (victim_luck - 5) * 0.05  # Base 30%, ±5% per luck point
            survival_chance = max(0.1, min(0.7, survival_chance))  # Clamp between 10% and 70%
            
            if random.random() < survival_chance:
                # Victim survives the betrayal attempt
                print(get_message("combat", "betrayal_attempt", traitor=traitor.name, victim=victim.name))
                # Both survive but the truce is broken
                return None, None, "betrayal_attempt"
            else:
                # Victim dies from betrayal
                victim.health = 0
                victim.status = 'eliminated'
                traitor.kills.append(victim.name)
                traitor.sanity = max(0, traitor.sanity - random.randint(15, 25))  # High sanity loss for betrayal
                print(get_message("combat", "betrayal_death", killer=traitor.name, victim=victim.name))
                return traitor, victim, "betrayal_kill"
        
        # No betrayal occurred, peaceful resolution
        return None, None, "agree"
    else:
        # Random winner, but since both alive, perhaps no kill, or chance
        # For now, no kill
        print(get_message("combat", "fight_no_death", name1=attacker.name, name2=defender.name))
        return None, None, "fight"
