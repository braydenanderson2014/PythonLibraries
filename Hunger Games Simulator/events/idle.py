import random
import json
from typing import List
from core.game_state import GameState
from tributes.tribute import Tribute
from combat import pickup_weapon

def load_idle_events():
    """Load idle events from JSON file"""
    with open('data/idle_events.json', 'r') as f:
        data = json.load(f)
        return data

idle_events_data = load_idle_events()

def get_idle_event(tribute: Tribute, phase: str = "morning", game_state: GameState = None) -> str:
    # Weapon-seeking behavior: tributes without preferred weapons are more likely to seek weapons
    weapon_seeking_bonus = 0
    if tribute.should_seek_weapon():
        weapon_seeking_bonus = 0.3  # 30% more likely to seek weapons if they need them

    # Get events for current phase plus shared events
    phase_events = idle_events_data.get(phase, [])
    shared_events = idle_events_data.get("shared", [])
    available_events = phase_events + shared_events

    # If tribute should seek weapons, increase chance of weapon-related events
    if tribute.should_seek_weapon():
        # Find weapon-seeking events
        weapon_events = [e for e in available_events if e.get("special_effect") in ["find_weapon", "seek_weapon"]]
        if weapon_events:
            # Temporarily boost the selection weight for weapon events
            for event in weapon_events:
                # Add multiple copies to increase selection chance
                for _ in range(int(weapon_seeking_bonus * 10)):
                    available_events.append(event)

    # Select random idle event
    event_data = random.choice(available_events)
    event_desc = event_data["description"]
    
    # Calculate sanity change - randomly positive or negative within the range
    sanity_min = event_data["sanity_min"]
    sanity_max = event_data["sanity_max"]
    
    # Randomly decide if the event helps or hurts sanity
    if random.random() < 0.5:
        # Positive effect (use positive part of range)
        sanity_change = random.randint(max(0, sanity_min), max(0, sanity_max))
    else:
        # Negative effect (use negative part of range)
        sanity_change = random.randint(min(0, sanity_min), min(0, sanity_max))
    
    tribute.sanity += sanity_change
    tribute.sanity = max(0, min(100, tribute.sanity))
    
    # Special handling for suicide when questioning life
    if event_desc == "starts to question life":
        if tribute.sanity < 20 and random.random() < 0.3:  # High chance suicide if very low sanity
            tribute.status = 'eliminated'
            return f"{tribute.name} starts to question life and commits suicide!"
    
    # Additional check for sanity <= 0 suicide (near guarantee)
    if tribute.sanity <= 0:
        suicide_chance = 0.95  # 95% chance of suicide when sanity hits 0
        if random.random() < suicide_chance:
            suicide_events = [
                f"{tribute.name} loses all hope and takes their own life!",
                f"{tribute.name} can no longer bear the mental torment and commits suicide!",
                f"{tribute.name}'s mind breaks completely and they end their suffering!",
                f"{tribute.name} succumbs to despair and commits suicide!",
                f"{tribute.name}'s sanity shatters and they choose death over madness!"
            ]
            tribute.status = 'eliminated'
            return random.choice(suicide_events)
    
    # Handle special effects
    special_effect = event_data.get("special_effect")
    
    if special_effect == "build_camp":
        tribute.has_camp = True
        return f"{tribute.name} {event_desc}."
    
    elif special_effect == "animal_attack":
        # Animal attack - extremely dangerous, survival depends on skills
        # Calculate survival chance based on relevant skills
        survival_skill = tribute.skills.get('survival', 5)
        strength_skill = tribute.skills.get('strength', 5)
        agility_skill = tribute.skills.get('agility', 5)

        # Average of relevant skills
        avg_skill = (survival_skill + strength_skill + agility_skill) / 3.0

        # Base survival chance: 10-40% depending on skills (much lower than before)
        base_survival_chance = 0.1 + (avg_skill - 3) * 0.075  # 10% at skill 3, 40% at skill 9

        # Health bonus: healthier tributes have better chance
        health_bonus = (tribute.health / 100.0 - 0.5) * 0.1  # ±10% based on health
        base_survival_chance += health_bonus

        # Weapon bonus: armed tributes have advantage
        if len(tribute.weapons) > 1:  # Has more than just fists
            base_survival_chance += 0.15

        # Clamp survival chance
        survival_chance = max(0.05, min(0.6, base_survival_chance))

        if random.random() < survival_chance:
            # Survived, but with severe damage
            damage = random.randint(25, 60)  # Much higher damage range
            tribute.health -= damage

            # High chance of bleeding from animal attack
            if random.random() < 0.7:  # 70% chance of bleeding
                if not tribute.bleeding or tribute.bleeding == 'none':
                    tribute.bleeding = 'severe' if random.random() < 0.4 else 'mild'
                    tribute.bleeding_days = 0

            if tribute.health <= 0:
                tribute.status = 'eliminated'
                return f"{tribute.name} {event_desc} and succumbed to the injuries!"
            else:
                bleeding_desc = f" and is now bleeding" if tribute.bleeding != 'none' else ""
                return f"{tribute.name} {event_desc} and barely survives with {tribute.health} health remaining{bleeding_desc}!"
        else:
            # Didn't survive - instant death or near-fatal damage
            tribute.health = max(1, tribute.health - random.randint(70, 100))
            tribute.status = 'eliminated'
            return f"{tribute.name} {event_desc} and was killed by the animal!"
    
    elif special_effect == "tracker_jackers":
        # Tracker jackers - always cause some damage but rarely fatal
        damage = random.randint(5, 15)
        tribute.health -= damage
        if tribute.health <= 0:
            tribute.status = 'eliminated'
            return f"{tribute.name} {event_desc} and died from the stings!"
        else:
            return f"{tribute.name} {event_desc} and survives with {tribute.health} health remaining!"
    
    elif special_effect == "seek_weapon":
        # Load weapons data
        with open('data/weapons.json', 'r') as f:
            weapons_data = json.load(f)

        # Get available weapons (exclude Fists and weapons they already have)
        available_weapons = [w for w in weapons_data.keys() if w != "Fists" and w not in tribute.weapons]
        
        if not available_weapons:
            # No new weapons available
            return f"{tribute.name} searches for weapons but finds nothing useful."

        # Determine how many weapons to potentially find (1-3 based on luck and survival skills)
        luck_skill = tribute.skills.get('luck', 5)
        survival_skill = tribute.skills.get('survival', 5)
        max_finds = min(3, max(1, (luck_skill + survival_skill) // 6))
        
        found_weapons = []
        messages = []
        
        for _ in range(max_finds):
            if not available_weapons:
                break
                
            # Prioritize target weapon, then preferred weapon, then any weapon
            if tribute.target_weapon and tribute.target_weapon in available_weapons:
                sought_weapon = tribute.target_weapon
                tribute.set_target_weapon(None)  # Clear target once found
            elif tribute.preferred_weapon in available_weapons:
                sought_weapon = tribute.preferred_weapon
            else:
                sought_weapon = random.choice(available_weapons)

            # Higher chance of success when actively seeking vs stumbling upon
            success_chance = 0.6 if tribute.should_seek_weapon() else 0.3
            
            # Luck modifier - lucky tributes have better chances of finding weapons
            luck_skill = tribute.skills.get('luck', 5)
            luck_modifier = (luck_skill - 5) * 0.05  # ±5% per luck point from 5
            success_chance += luck_modifier
            success_chance = max(0.1, min(0.9, success_chance))  # Clamp between 10% and 90%
            
            if random.random() < success_chance:  # Success rate when seeking
                def dummy_get_message(category, key, **kwargs):
                    return f"{kwargs.get('tribute', 'Tribute')} finds and picks up a {kwargs.get('weapon', 'weapon')}!"

                if pickup_weapon(tribute, sought_weapon, dummy_get_message, print_message=False):
                    found_weapons.append(sought_weapon)
                    available_weapons.remove(sought_weapon)  # Remove from available list
                    
                    if sought_weapon == tribute.preferred_weapon:
                        messages.append(f"their preferred {sought_weapon}")
                    else:
                        messages.append(f"a {sought_weapon}")
                else:
                    # Already has this weapon
                    available_weapons.remove(sought_weapon)
            
            # Lucky bonus: High luck tributes have a chance to find rare weapons they weren't seeking
            if luck_skill >= 7 and random.random() < (luck_skill - 6) * 0.1:  # 10% chance per luck point above 6
                rare_weapons = [w for w in available_weapons if weapons_data.get(w, {}).get('rarity') == 'rare']
                if rare_weapons:
                    lucky_find = random.choice(rare_weapons)
                    def dummy_get_message(category, key, **kwargs):
                        return f"{kwargs.get('tribute', 'Tribute')} luckily stumbles upon a {kwargs.get('weapon', 'weapon')}!"
                    
                    if pickup_weapon(tribute, lucky_find, dummy_get_message, print_message=False):
                        found_weapons.append(lucky_find)
                        available_weapons.remove(lucky_find)
                        messages.append(f"a rare {lucky_find} (lucky find!)")
        
        if found_weapons:
            if len(found_weapons) == 1:
                weapon_desc = messages[0]
                return f"{tribute.name} finds and picks up {weapon_desc} while searching!"
            else:
                weapon_list = ", ".join(messages[:-1]) + f" and {messages[-1]}" if len(messages) > 1 else messages[0]
                return f"{tribute.name} finds and picks up {weapon_list} while searching!"
        else:
            # Failed search
            return f"{tribute.name} searches for weapons but comes up empty-handed."
    
    elif special_effect == "find_weapon":
        # Load weapons data
        with open('data/weapons.json', 'r') as f:
            weapons_data = json.load(f)

        # Get available weapons (exclude Fists and weapons they already have)
        available_weapons = [w for w in weapons_data.keys() if w != "Fists" and w not in tribute.weapons]
        
        if not available_weapons:
            # No new weapons available
            return f"{tribute.name} finds a weapon but it's something they already have."
        
        # Randomly select a weapon to find
        found_weapon = random.choice(available_weapons)
        
        def dummy_get_message(category, key, **kwargs):
            return f"{kwargs.get('tribute', 'Tribute')} finds and picks up a {kwargs.get('weapon', 'weapon')}!"

        if pickup_weapon(tribute, found_weapon, dummy_get_message, print_message=False):
            return f"{tribute.name} finds and picks up a {found_weapon}!"
        else:
            return f"{tribute.name} finds a {found_weapon} but already has too many weapons."
    
    elif special_effect == "gather_resources":
        # Resource gathering opportunity
        resource_types = ["food", "water", "shelter"]
        resource_type = random.choice(resource_types)
        
        success = False
        if resource_type == "food":
            success = tribute.gather_food()
            # Luck modifier for gathering success
            if not success:
                luck_skill = tribute.skills.get('luck', 5)
                luck_bonus_chance = (luck_skill - 5) * 0.1  # 10% bonus chance per luck point above 5
                if random.random() < luck_bonus_chance:
                    success = tribute.gather_food()  # Try again with luck
            
            if success:
                return f"{tribute.name} successfully hunts/forages and gains food (now at {tribute.food})!"
            else:
                return f"{tribute.name} tries to hunt/forage but comes back empty-handed."
        elif resource_type == "water":
            success = tribute.gather_water()
            # Luck modifier for gathering success
            if not success:
                luck_skill = tribute.skills.get('luck', 5)
                luck_bonus_chance = (luck_skill - 5) * 0.1  # 10% bonus chance per luck point above 5
                if random.random() < luck_bonus_chance:
                    success = tribute.gather_water()  # Try again with luck
            
            if success:
                return f"{tribute.name} finds a water source and replenishes supplies (now at {tribute.water})!"
            else:
                return f"{tribute.name} searches for water but finds no safe sources."
        elif resource_type == "shelter":
            success = tribute.improve_shelter()
            if success:
                # Determine if this is building or repairing based on current shelter level
                if tribute.shelter < 30:
                    action = "builds"
                else:
                    action = "repairs"
                return f"{tribute.name} {action} their shelter and feels more secure (shelter now at {tribute.shelter})!"
            else:
                # Determine if this is attempting to build or repair
                if tribute.shelter < 30:
                    action = "build"
                else:
                    action = "repair"
                return f"{tribute.name} attempts to {action} shelter but makes little progress."
    
    elif special_effect == "set_trap":
        # Determine trap type based on location and skills
        trap_types = ["basic", "pit", "spear", "net"]
        trap_type = random.choice(trap_types)
        
        # Prefer certain traps based on skills
        survival_skill = tribute.skills.get('survival', 5)
        if survival_skill >= 7:
            trap_type = random.choice(["pit", "spear", "net"])
        elif survival_skill >= 6:
            trap_type = random.choice(["basic", "pit", "spear"])
        
        # Determine location - prefer camp if they have one
        location = "camp" if tribute.has_camp and random.random() < 0.7 else "general"
        
        if tribute.set_trap(trap_type, location):
            location_desc = "near their camp" if location == "camp" else "in the area"
            return f"{tribute.name} sets a {trap_type} trap {location_desc}."
        else:
            return f"{tribute.name} attempts to set a trap but lacks the materials or skill."
    
    elif special_effect == "sponsor_gift":
        # Sponsor gift - can provide resources or items
        # Luck influences sponsor gift chances and quality
        luck_skill = tribute.skills.get('luck', 5)
        base_chance = 0.3  # Base 30% chance
        luck_modifier = (luck_skill - 5) * 0.05  # ±5% per luck point from 5
        gift_chance = max(0.1, min(0.8, base_chance + luck_modifier))
        
        if random.random() > gift_chance:
            return f"{tribute.name} hopes for a sponsor gift but receives nothing."
        
        gift_types = ["food", "water", "medicine", "weapon"]
        # Lucky tributes get better gift distributions
        if luck_skill >= 8:
            gift_weights = [0.2, 0.2, 0.3, 0.3]  # More weapons and medicine for very lucky
        elif luck_skill >= 6:
            gift_weights = [0.25, 0.25, 0.25, 0.25]  # Balanced for moderately lucky
        else:
            gift_weights = [0.4, 0.4, 0.1, 0.1]  # Mostly food/water for unlucky
        
        gift_type = random.choices(gift_types, weights=gift_weights)[0]
        
        if gift_type == "food":
            amount = random.randint(20, 40)
            tribute.food = min(100, tribute.food + amount)
            # Reset starvation timer if they were starving
            if tribute.starvation_timer > 0:
                tribute.starvation_timer = 0
                return f"A sponsor sends {tribute.name} a gift of food! They gain {amount} food and their starvation timer is reset!"
            else:
                return f"A sponsor sends {tribute.name} a gift of food! They gain {amount} food."
        
        elif gift_type == "water":
            amount = random.randint(20, 40)
            tribute.water = min(100, tribute.water + amount)
            # Reset dehydration timer if they were dehydrated
            if tribute.dehydration_timer > 0:
                tribute.dehydration_timer = 0
                return f"A sponsor sends {tribute.name} a gift of water! They gain {amount} water and their dehydration timer is reset!"
            else:
                return f"A sponsor sends {tribute.name} a gift of water! They gain {amount} water."
        
        elif gift_type == "medicine":
            healing = random.randint(20, 40)
            old_health = tribute.health
            tribute.health = min(100, tribute.health + healing)
            actual_healing = tribute.health - old_health
            return f"A sponsor sends {tribute.name} medicine! They heal {actual_healing} health points."
        
        elif gift_type == "weapon":
            # Load weapons data
            with open('data/weapons.json', 'r') as f:
                weapons_data = json.load(f)
            
            # Get available weapons (exclude Fists and weapons they already have)
            available_weapons = [w for w in weapons_data.keys() if w != "Fists" and w not in tribute.weapons]
            
            if available_weapons:
                # Prefer sponsor's choice or random good weapon
                sponsor_weapon = random.choice(available_weapons)
                
                def dummy_get_message(category, key, **kwargs):
                    return f"{kwargs.get('tribute', 'Tribute')} receives a {kwargs.get('weapon', 'weapon')} from a sponsor!"
                
                if pickup_weapon(tribute, sponsor_weapon, dummy_get_message, print_message=False):
                    return f"A sponsor sends {tribute.name} a {sponsor_weapon}! They now have this powerful weapon."
                else:
                    return f"A sponsor tries to send {tribute.name} a weapon, but they already have too many weapons."
            else:
                # No new weapons available, give resources instead
                tribute.food = min(100, tribute.food + 15)
                return f"A sponsor sends {tribute.name} a gift basket with food! They gain 15 food."
    
    # Default case - just return the event description
    result = f"{tribute.name} {event_desc}."
    
    # Check for trap triggers during exploration activities
    if event_desc == "explores the arena" or "searches" in event_desc or "scavenges" in event_desc:
        if game_state is None:
            # Can't check for traps without game state
            pass
        else:
            # Check if tribute triggers any traps while moving around
            triggered_trap = None
            trap_setter = None
            
            # Look for traps set by other tributes (not allies)
            for other_tribute in game_state.active_tributes:
                if other_tribute == tribute or other_tribute.name in tribute.allies:
                    continue
                
                for trap in other_tribute.traps[:]:  # Use slice copy in case trap is removed
                    if random.random() < 0.2:  # 20% chance to trigger trap during exploration
                        triggered_trap = trap
                        trap_setter = other_tribute
                        break
                if triggered_trap:
                    break
            
            if triggered_trap and trap_setter:
                # Apply the trap effect
                trap_result = tribute.apply_trap_effect(triggered_trap, trap_setter.name)
                
                # Remove the trap after triggering (one-time use)
                if triggered_trap in trap_setter.traps:
                    trap_setter.traps.remove(triggered_trap)
                
                # Add trap result to the event description
                result += f" {trap_result}"
    
    return result