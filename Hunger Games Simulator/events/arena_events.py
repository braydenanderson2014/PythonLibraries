import random
import json
from typing import List, Dict, Any
from core.game_state import GameState
from tributes.tribute import Tribute

def load_arena_events():
    """Load arena events from JSON file"""
    try:
        with open('data/arena_events.json', 'r') as f:
            data = json.load(f)
            return data.get('arena_events', [])
    except FileNotFoundError:
        # Return empty list if file doesn't exist
        return []

arena_events_data = load_arena_events()

def trigger_random_arena_event(game: GameState, get_message) -> List[str]:
    """
    Trigger a random arena event that affects tributes.
    Returns a list of event descriptions.
    """
    if not arena_events_data:
        return []

    # Only trigger arena events rarely (10% chance per phase instead of 2%)
    if random.random() > 0.10:
        return []

    # Select random arena event
    event_data = random.choice(arena_events_data)
    event_name = event_data["name"]
    event_description = event_data["description"]
    event_type = event_data.get("type", "hazard")
    duration = event_data.get("duration", 1)
    effects = event_data.get("effects", [])

    event_messages = []
    event_messages.append(f"Arena Event: {event_description}")

    # Handle different event types
    if event_type == "weather":
        # Weather events persist for multiple phases
        game.active_weather_events.append({
            "name": event_name,
            "description": event_description,
            "effects": effects,
            "duration": duration,
            "remaining": duration
        })
        event_messages.append(f"This weather event will last for {duration} phases.")
        
    elif event_type == "danger_zone":
        # Danger zones require immediate evacuation
        game.active_danger_zones.append({
            "name": event_name,
            "description": event_description,
            "effects": effects,
            "duration": duration,
            "remaining": duration
        })
        event_messages.append("All tributes must evacuate the danger zone immediately!")
        
    elif event_type == "time_based":
        # Time-based events are triggered by time of day
        trigger_time = event_data.get("trigger_time")
        if game.current_phase == trigger_time:
            game.active_environmental_effects.append({
                "name": event_name,
                "description": event_description,
                "effects": effects,
                "duration": duration,
                "remaining": duration
            })
        
    elif event_type == "environmental":
        # Environmental events have lasting effects
        game.active_environmental_effects.append({
            "name": event_name,
            "description": event_description,
            "effects": effects,
            "duration": duration,
            "remaining": duration
        })
        
    else:
        # Standard hazard events - apply immediately
        affected_tributes = []

        for effect in effects:
            effect_type = effect["type"]
            severity = effect.get("severity", "moderate")
            protection_required = effect.get("protection_required", None)

            # Determine which tributes are affected
            if effect_type == "area_damage":
                # Affects all tributes in certain areas
                affected_tributes = game.active_tributes[:]  # All active tributes

            elif effect_type == "random_affected":
                # Affects random subset of tributes
                num_affected = effect.get("count", len(game.active_tributes) // 2)
                affected_tributes = random.sample(game.active_tributes, min(num_affected, len(game.active_tributes)))

            elif effect_type == "all_tributes":
                # Affects all tributes
                affected_tributes = game.active_tributes[:]

            # Apply the effect
            for tribute in affected_tributes:
                if _apply_effect_to_tribute(tribute, effect, protection_required):
                    event_messages.append(_get_tribute_effect_message(tribute, effect))

    return event_messages

def _apply_effect_to_tribute(tribute: Tribute, effect: Dict[str, Any], protection_required: str = None) -> bool:
    """
    Apply an effect to a tribute.
    Returns True if the tribute was affected, False if protected or immune.
    """
    effect_type = effect["type"]

    # Check for protection
    if protection_required and not tribute.has_protection(protection_required):
        # Tribute has required protection, effect doesn't apply
        return False

    if effect_type == "damage":
        damage = effect.get("damage", 10)
        if isinstance(damage, list):
            damage = random.randint(damage[0], damage[1])

        tribute.add_damage("arena_event", damage, effect.get("description", "arena hazard"))
        if tribute.health <= 0:
            tribute.status = 'eliminated'
            tribute.sanity = 0

    elif effect_type == "animal_attack":
        # Animal attacks are extremely dangerous and skill-dependent
        base_damage = effect.get("damage", [25, 55])
        if isinstance(base_damage, list):
            base_damage = random.randint(base_damage[0], base_damage[1])

        # Calculate survival chance based on skills
        survival_skill = tribute.skills.get('survival', 5)
        strength_skill = tribute.skills.get('strength', 5)
        agility_skill = tribute.skills.get('agility', 5)
        luck_skill = tribute.skills.get('luck', 5)

        avg_skill = (survival_skill + strength_skill + agility_skill) / 3.0
        survival_chance = 0.15 + (avg_skill - 3) * 0.08  # 15% at skill 3, 47% at skill 9

        # Luck modifier - lucky tributes have better survival chances
        luck_modifier = (luck_skill - 5) * 0.03  # ±3% per luck point from 5
        survival_chance += luck_modifier

        # Health and weapon bonuses
        survival_chance += (tribute.health / 100.0 - 0.5) * 0.1
        if len(tribute.weapons) > 1:
            survival_chance += 0.15

        survival_chance = max(0.05, min(0.7, survival_chance))

        if random.random() < survival_chance:
            # Survived with reduced damage
            actual_damage = int(base_damage * 0.6)  # 40% damage reduction if survived
            tribute.add_damage("animal_attack", actual_damage, "wolf pack attack")

            # Chance of bleeding
            if random.random() < 0.6:
                if not tribute.bleeding or tribute.bleeding == 'none':
                    tribute.bleeding = 'severe' if random.random() < 0.3 else 'mild'
                    tribute.bleeding_days = 0
        else:
            # Didn't survive - fatal damage
            actual_damage = base_damage + random.randint(20, 40)  # Extra damage
            tribute.add_damage("animal_attack", actual_damage, "fatal wolf pack attack")
            tribute.status = 'eliminated'
            tribute.sanity = 0

    elif effect_type == "damage_over_time":
        # Apply damage over multiple phases
        damage = effect.get("damage", [1, 3])
        if isinstance(damage, list):
            damage = random.randint(damage[0], damage[1])
        duration = effect.get("duration", 1)
        
        # Add to tribute's ongoing effects
        if not hasattr(tribute, 'ongoing_effects'):
            tribute.ongoing_effects = []
        
        tribute.ongoing_effects.append({
            "type": "damage_over_time",
            "damage": damage,
            "remaining": duration
        })

    elif effect_type == "sanity_damage":
        sanity_loss = effect.get("sanity_loss", 10)
        if isinstance(sanity_loss, list):
            sanity_loss = random.randint(sanity_loss[0], sanity_loss[1])

        tribute.add_damage("arena_fear", sanity_loss, effect.get("description", "terrifying event"))
        tribute.sanity = max(0, tribute.sanity)

    elif effect_type == "bleeding":
        if tribute.bleeding == 'none':
            severity_roll = random.random()
            if severity_roll < 0.6:  # 60% mild
                tribute.bleeding = 'mild'
            elif severity_roll < 0.9:  # 30% severe
                tribute.bleeding = 'severe'
            else:  # 10% fatal
                tribute.bleeding = 'fatal'

    elif effect_type == "speed_penalty":
        penalty = effect.get("penalty", 1)
        tribute.speed = max(1, tribute.speed - penalty)

    elif effect_type == "resource_decay":
        decay_rate = effect.get("decay_rate", 1.0)
        resource_type = effect.get("resource_type", "food")
        
        if resource_type == "food":
            tribute.food = max(0, tribute.food - int(tribute.food * (decay_rate - 1.0) / 100))
        elif resource_type == "water":
            # Assuming water is tracked separately, for now affect food
            tribute.food = max(0, tribute.food - int(tribute.food * (decay_rate - 1.0) / 100))

    elif effect_type == "forced_movement":
        # Could implement movement between areas if we add area system
        penalty_damage = effect.get("penalty_damage", [5, 15])
        if isinstance(penalty_damage, list):
            penalty_damage = random.randint(penalty_damage[0], penalty_damage[1])
        tribute.add_damage("forced_movement", penalty_damage, "forced to move through dangerous terrain")

    elif effect_type == "supply_destruction":
        # Destroy random supplies/weapons
        if tribute.weapons and random.random() < 0.5:
            lost_weapon = random.choice(tribute.weapons)
            tribute.weapons.remove(lost_weapon)
            # Set current weapon directly
            tribute.current_weapon = "Fists" if not tribute.weapons else tribute.weapons[0]

    elif effect_type == "structure_destruction":
        destruction_chance = effect.get("destruction_chance", 0.5)
        if random.random() < destruction_chance:
            tribute.has_camp = False

    return True

def process_ongoing_environmental_effects(game: GameState) -> List[str]:
    """
    Process ongoing environmental effects (weather, danger zones, etc.)
    Returns list of messages about effects that occurred.
    """
    messages = []

    # Process weather events
    for weather_event in game.active_weather_events[:]:
        # Group effects by type for consolidated messages
        effect_groups = {}

        # Apply weather effects to all active tributes
        for tribute in game.active_tributes:
            for effect in weather_event["effects"]:
                if _apply_effect_to_tribute(tribute, effect):
                    effect_type = effect["type"]
                    if effect_type not in effect_groups:
                        effect_groups[effect_type] = []
                    effect_groups[effect_type].append(tribute.name)

        # Generate consolidated messages
        for effect_type, affected_tributes in effect_groups.items():
            if effect_type == "resource_decay":
                if len(affected_tributes) <= 3:
                    tribute_list = ", ".join(affected_tributes)
                else:
                    tribute_list = f"{len(affected_tributes)} tributes"
                messages.append(f"Weather: {tribute_list}'s supplies are decaying rapidly!")
            elif effect_type == "damage_over_time":
                if len(affected_tributes) <= 3:
                    tribute_list = ", ".join(affected_tributes)
                else:
                    tribute_list = f"{len(affected_tributes)} tributes"
                messages.append(f"Weather: {tribute_list} begin suffering ongoing damage!")

        # Decrement duration
        weather_event["remaining"] -= 1
        if weather_event["remaining"] <= 0:
            game.active_weather_events.remove(weather_event)
            messages.append(f"The {weather_event['name']} has ended.")

    # Process danger zones
    for danger_zone in game.active_danger_zones[:]:
        # Danger zones affect tributes who haven't evacuated
        for tribute in game.active_tributes:
            for effect in danger_zone["effects"]:
                if _apply_effect_to_tribute(tribute, effect):
                    messages.append(f"Danger Zone: {_get_tribute_effect_message(tribute, effect)}")

        danger_zone["remaining"] -= 1
        if danger_zone["remaining"] <= 0:
            game.active_danger_zones.remove(danger_zone)
            messages.append(f"The danger zone has been deactivated.")

    # Process environmental effects
    for env_effect in game.active_environmental_effects[:]:
        # Apply environmental effects
        for tribute in game.active_tributes:
            for effect in env_effect["effects"]:
                if _apply_effect_to_tribute(tribute, effect):
                    messages.append(f"Environment: {_get_tribute_effect_message(tribute, effect)}")

        env_effect["remaining"] -= 1
        if env_effect["remaining"] <= 0:
            game.active_environmental_effects.remove(env_effect)
            messages.append(f"The {env_effect['name']} effect has dissipated.")

    return messages

def process_tribute_ongoing_effects(game: GameState) -> List[str]:
    """
    Process ongoing effects on individual tributes (damage over time, etc.)
    Returns list of messages about effects that occurred.
    """
    messages = []
    
    for tribute in game.active_tributes:
        if hasattr(tribute, 'ongoing_effects') and tribute.ongoing_effects:
            # Process each ongoing effect
            for effect in tribute.ongoing_effects[:]:
                if effect["type"] == "damage_over_time":
                    was_alive = tribute.health > 0
                    tribute.add_damage("ongoing_effect", effect["damage"], f"ongoing {effect.get('description', 'arena effect')}")
                    
                    if was_alive and tribute.health <= 0:
                        tribute.status = 'eliminated'
                        messages.append(f"{tribute.name} has died from ongoing damage!")
                    
                    effect["remaining"] -= 1
                    if effect["remaining"] <= 0:
                        tribute.ongoing_effects.remove(effect)
    
    return messages

def _get_tribute_effect_message(tribute: Tribute, effect: Dict[str, Any]) -> str:
    """Generate a message describing the effect on a tribute."""
    effect_type = effect["type"]

    if effect_type == "damage":
        if tribute.health <= 0:
            return f"{tribute.name} dies from the arena hazard!"
        else:
            return f"{tribute.name} takes damage and has {tribute.health} health remaining!"

    elif effect_type == "damage_over_time":
        return f"{tribute.name} begins suffering ongoing damage!"

    elif effect_type == "sanity_damage":
        return f"{tribute.name} is terrified by the event!"

    elif effect_type == "bleeding":
        bleeding_type = tribute.bleeding
        if bleeding_type == 'fatal':
            return f"{tribute.name} suffers fatal bleeding from the hazard!"
        elif bleeding_type == 'severe':
            return f"{tribute.name} suffers severe bleeding!"
        else:
            return f"{tribute.name} suffers minor bleeding!"

    elif effect_type == "speed_penalty":
        return f"{tribute.name}'s movement speed is reduced!"

    elif effect_type == "resource_decay":
        return f"{tribute.name}'s supplies are decaying rapidly!"

    elif effect_type == "forced_movement":
        return f"{tribute.name} is forced to move and takes damage!"

    elif effect_type == "supply_destruction":
        return f"{tribute.name} loses supplies to the hazard!"

    elif effect_type == "structure_destruction":
        return f"{tribute.name}'s shelter is destroyed!"

    return f"{tribute.name} is affected by the arena event!"