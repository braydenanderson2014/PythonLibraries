from core.game_state import GameState
from tributes.tribute import Tribute
from utils.filter import work_friendly
from utils.generator import generate_random_tribute
from utils.custom_tributes import custom_tribute_manager
from utils.settings_manager import settings_manager
from utils.output_manager import output_manager
from combat import fight
from events import trigger_random_event
from events.idle import get_idle_event
from events.arena_events import trigger_random_arena_event, process_ongoing_environmental_effects, process_tribute_ongoing_effects
import random
import json
import os
import sys
import argparse
import time

def get_phase_delay(game, phase_delay_config):
    """Get variable phase delay based on game state and phase."""
    base_delay = settings_manager.get_phase_delay('base_delay')

    # Shorter delays for web mode
    if settings_manager.is_web_mode():
        base_delay = min(base_delay, settings_manager.get('web_settings.update_interval', 0.1))

    # Variable delays based on phase
    phase_multipliers = {
        'morning': settings_manager.get_phase_delay('morning'),
        'afternoon': settings_manager.get_phase_delay('afternoon'),
        'evening': settings_manager.get_phase_delay('evening'),
        'environmental': settings_manager.get_phase_delay('environmental')
    }

    multiplier = phase_multipliers.get(game.phase, 1.0)

    # Add some randomness
    randomness = settings_manager.get_phase_delay('randomness')
    random_factor = random.uniform(1.0 - randomness, 1.0 + randomness)

    # Shorter delays as game progresses (gets more intense)
    progression_factor = settings_manager.get_phase_delay('progression_factor')
    day_factor = max(0.5, 1.0 - (game.day - 1) * progression_factor)

    return base_delay * multiplier * random_factor * day_factor

def save_initial_tributes(tributes, filename="data/initial_tributes.json"):
    """Save initial tribute data for future sessions."""
    data = []
    for t in tributes:
        data.append({
            "name": t.name,
            "skills": t.skills,
            "weapons": t.weapons,
            "district": t.district,
            "preferred_weapon": t.preferred_weapon
        })
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_initial_tributes(filename="data/initial_tributes.json"):
    """Load initial tribute data from file."""
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        tributes = []
        for item in data:
            # Always start tributes with only Fists - weapons must be acquired during the games
            tribute = Tribute(
                name=item["name"],
                skills=item["skills"],
                weapons=["Fists"],  # Always start unarmed
                district=item["district"]
            )
            # Set preferred weapon if specified
            if "preferred_weapon" in item:
                tribute.set_preferred_weapon(item["preferred_weapon"])
            tributes.append(tribute)
        return tributes
    except FileNotFoundError:
        return None

def validate_name(name, existing_names=None):
    """Validate tribute name."""
    if not name or not name.strip():
        return False, "Name cannot be empty"
    if len(name.strip()) > 50:
        return False, "Name too long (max 50 characters)"
    if existing_names and name.strip().lower() in [n.lower() for n in existing_names]:
        return False, "Name already exists"
    return True, ""

def validate_skill(skill_name, value, skills_config):
    """Validate a skill value."""
    if skill_name not in skills_config["skills"]:
        return False, f"Unknown skill: {skill_name}"
    min_val = skills_config["range"]["min"]
    max_val = skills_config["range"]["max"]
    if not isinstance(value, int) or value < min_val or value > max_val:
        return False, f"{skill_name} must be between {min_val} and {max_val}"
    return True, ""

def validate_weapon(weapon, weapons_data):
    """Validate weapon exists."""
    if weapon not in weapons_data:
        return False, f"Unknown weapon: {weapon}. Available: {', '.join(weapons_data.keys())}"
    return True, ""

def validate_rating(value, max_rating=5):
    """Validate a rating value (1-max_rating)."""
    try:
        val = int(value)
        if 1 <= val <= max_rating:
            return True, val
        return False, f"Rating must be between 1 and {max_rating}"
    except ValueError:
        return False, "Rating must be a number"

def generate_skills_from_priorities(priorities, skills_config):
    """Generate actual skill values (1-10) based on priority order (1 = highest priority)."""
    skills = {}
    
    for skill_name, priority in priorities.items():
        if priority == 1:  # Highest priority
            # Priority 1 gets 8-10
            skills[skill_name] = random.randint(8, 10)
        elif priority == 2:  # Second highest
            # Priority 2 gets 7-9
            skills[skill_name] = random.randint(7, 9)
        elif priority == 3:  # Third highest
            # Priority 3 gets 6-8
            skills[skill_name] = random.randint(6, 8)
        elif priority == 4:  # Fourth highest
            # Priority 4 gets 5-7
            skills[skill_name] = random.randint(5, 7)
        elif priority == 5:  # Fifth highest
            # Priority 5 gets 4-6
            skills[skill_name] = random.randint(4, 6)
        elif priority == 6:  # Sixth highest
            # Priority 6 gets 3-5
            skills[skill_name] = random.randint(3, 5)
        elif priority == 7:  # Seventh highest
            # Priority 7 gets 2-4
            skills[skill_name] = random.randint(2, 4)
        elif priority == 8:  # Eighth highest
            # Priority 8 gets 1-3
            skills[skill_name] = random.randint(1, 3)
        elif priority == 9:  # Ninth highest
            # Priority 9 gets 1-2
            skills[skill_name] = random.randint(1, 2)
        else:  # Priority 10 (lowest)
            # Priority 10 gets 1
            skills[skill_name] = 1
    
    return skills

def validate_district(district, districts_mode):
    """Validate district number."""
    # Handle string input from user
    if isinstance(district, str):
        try:
            district = int(district)
        except ValueError:
            return False, "District must be a number"
    
    if districts_mode:
        if not isinstance(district, int) or district < 1 or district > 12:
            return False, "District must be between 1 and 12"
    else:
        if district != 0:
            return False, "District must be 0 when not using districts"
    return True, ""

def create_tribute_with_relationships(tributes, custom_config=None):
    """Create a new tribute with optional relationships."""
    # Load validation data
    with open("data/weapons.json", "r") as f:
        weapons_data = json.load(f)
    with open("data/skills.json", "r") as f:
        skills_config = json.load(f)
    
    print("\nTribute Creation Mode:")
    print("1. Basic Mode (Rate attributes 1-5)")
    print("2. Advanced Mode (Manual skill values 1-10)")
    
    mode_choice = input("Choose mode (1-2): ").strip()
    
    # Get basic info
    existing_names = [t.name for t in tributes]
    name = get_valid_input("Enter tribute name (first and last): ", validate_name, existing_names)
    
    skills = {}
    
    if mode_choice == "1":  # Basic mode
        print("\nPriority System: Order skills by importance (1 = highest priority, 10 = lowest priority)")
        print("Available skills:", ", ".join(skills_config["skills"]))
        print("\nAssign a priority number (1-10) to each skill. Each number can only be used once.")
        
        priorities = {}
        used_priorities = set()
        
        for skill in skills_config["skills"]:
            while True:
                try:
                    priority = int(input(f"Priority for {skill} (1-10, unused numbers: {[n for n in range(1, 11) if n not in used_priorities]}): "))
                    if priority < 1 or priority > 10:
                        print("Priority must be between 1 and 10")
                        continue
                    if priority in used_priorities:
                        print("That priority number is already used")
                        continue
                    
                    priorities[skill] = priority
                    used_priorities.add(priority)
                    break
                except ValueError:
                    print("Please enter a valid number")
        
        # Generate actual skills from priorities
        skills = generate_skills_from_priorities(priorities, skills_config)
        print(f"\nGenerated skills: {skills}")
        
    else:  # Advanced mode (default)
        print("\nEnter skill values (1-10):")
        for skill in skills_config["skills"]:
            while True:
                try:
                    val = int(input(f"{skill} (1-10): "))
                    valid, error = validate_skill(skill, val, skills_config)
                    if valid:
                        skills[skill] = val
                        break
                    else:
                        print(f"Error: {error}")
                except ValueError:
                    print("Invalid number")
    
    # Get weapon and district
    weapon = get_valid_input("Weapon: ", validate_weapon, weapons_data)
    district = int(get_valid_input("District (1-12): ", validate_district, True))
    
    # Create tribute
    speed = random.randint(1, 10)
    tribute = Tribute(name, skills, ["Fists"], district, speed=speed)
    tribute.set_preferred_weapon(weapon)
    
    # Ask if they want to set this as their target weapon (actively seek it)
    set_target = input(f"Set {weapon} as target weapon (actively seek it)? (y/n): ").lower().strip()
    if set_target == 'y':
        tribute.set_target_weapon(weapon)
    
    # Handle relationships
    relationships = {}
    print("\nRelationship Management:")
    print("You can add relationships to other tributes.")
    print("Available relationship types: ally, enemy, rival, neutral, family")
    
    while True:
        add_rel = input("Add a relationship? (y/n): ").lower().strip()
        if add_rel != 'y':
            break
        
        rel_name = input("Enter tribute name for relationship: ").strip()
        
        # Check if tribute exists
        existing_tribute = None
        for t in tributes:
            if t.name.lower() == rel_name.lower():
                existing_tribute = t
                rel_name = t.name  # Use exact case
                break
        
        if not existing_tribute:
            print(f"Tribute '{rel_name}' doesn't exist.")
            create_new = input("Create this tribute now? (y/n): ").lower().strip()
            if create_new == 'y':
                # Recursively create the new tribute
                print(f"\nCreating relationship tribute: {rel_name}")
                new_tribute = create_tribute_with_relationships(tributes, custom_config)
                if new_tribute:
                    tributes.append(new_tribute)
                    existing_tribute = new_tribute
                    rel_name = new_tribute.name
                else:
                    continue
            else:
                continue
        
        # Get relationship type
        print("Relationship types:")
        print("1. ally - Trustworthy partner")
        print("2. enemy - Actively hostile")
        print("3. rival - Competitive but not deadly")
        print("4. neutral - No strong feelings")
        print("5. family - Blood relatives")
        
        rel_choice = input("Choose relationship type (1-5): ").strip()
        rel_types = ["ally", "enemy", "rival", "neutral", "family"]
        
        if rel_choice in ["1", "2", "3", "4", "5"]:
            rel_type = rel_types[int(rel_choice) - 1]
        else:
            print("Invalid choice, defaulting to neutral")
            rel_type = "neutral"
        
        bias_factor = 1.0
        if rel_type == "ally":
            bias_factor = 2.0
        elif rel_type == "enemy":
            bias_factor = 3.0
        elif rel_type == "rival":
            bias_factor = 1.5
        
        description = input("Brief description (optional): ").strip()
        if not description:
            description = f"{rel_type.capitalize()} relationship"
        
        relationships[rel_name] = {
            "type": rel_type,
            "bias_factor": bias_factor,
            "description": description
        }
        
        print(f"Added {rel_type} relationship with {rel_name}")
    
    # Set relationships on the tribute
    for rel_name, rel_data in relationships.items():
        tribute.add_relationship(rel_name, rel_data["type"], rel_data["bias_factor"], rel_data["description"])
    
    # Save to tribute_upload.json if custom_config provided
    if custom_config is not None:
        tribute_data = {
            "name": tribute.name,
            "district": tribute.district,
            "skills": tribute.skills,
            "weapons": tribute.weapons,
            "preferred_weapon": tribute.preferred_weapon or weapon,
            "target_weapon": tribute.target_weapon,
            "health": tribute.health,
            "sanity": tribute.sanity,
            "speed": tribute.speed,
            "has_camp": tribute.has_camp,
            "relationships": relationships
        }
        
        if "custom_tributes" not in custom_config:
            custom_config["custom_tributes"] = []
        
        custom_config["custom_tributes"].append(tribute_data)
        
        # Save to file
        with open("data/tribute_upload.json", "w") as f:
            json.dump(custom_config, f, indent=2)
        
        print(f"\nTribute '{tribute.name}' saved to tribute_upload.json")
    
    return tribute

def get_valid_input(prompt, validator, *validator_args):
    """Get input with validation."""
    while True:
        value = input(prompt).strip()
        valid, error = validator(value, *validator_args)
        if valid:
            return value
        print(f"Error: {error}")

def modify_tributes(tributes):
    """Allow user to modify the list of tributes."""
    # Load validation data
    with open("data/weapons.json", "r") as f:
        weapons_data = json.load(f)
    with open("data/skills.json", "r") as f:
        skills_config = json.load(f)
    
    while True:
        print("\nCurrent Tributes:")
        for i, t in enumerate(tributes):
            print(f"{i+1}. {t.name} (District {t.district}) - Skills: {t.skills}, Weapons: {', '.join(t.weapons)} (Current: {t.current_weapon})")
        
        print("\nOptions:")
        print("1. Add new tribute")
        print("2. Remove tribute")
        print("3. Edit tribute")
        print("4. Generate random tributes (no districts)")
        print("5. Generate tributes by districts (2 per district)")
        print("6. Generate specific number of tributes")
        print("7. Remove all tributes")
        print("8. Save current tributes to tribute_upload.json")
        print("9. Done")
        
        choice = input("Choose an option (1-9): ").strip()
        
        if choice == "1":
            # Add new tribute
            # Load custom config for saving
            custom_config = None
            try:
                with open("data/tribute_upload.json", "r") as f:
                    custom_config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                custom_config = {
                    "description": "Custom tribute configurations and relationships for Hunger Games simulation",
                    "version": "1.0",
                    "custom_tributes": [],
                    "relationship_types": {
                        "ally": {"description": "Tributes who trust and help each other", "combat_bias": -0.8, "alliance_chance": 3.0, "attack_chance": 0.1},
                        "enemy": {"description": "Tributes who actively target each other", "combat_bias": 2.5, "alliance_chance": 0.1, "attack_chance": 2.0},
                        "rival": {"description": "Competitive relationship with occasional conflicts", "combat_bias": 1.2, "alliance_chance": 0.5, "attack_chance": 1.5},
                        "neutral": {"description": "No strong feelings either way", "combat_bias": 1.0, "alliance_chance": 1.0, "attack_chance": 1.0},
                        "family": {"description": "Blood relatives", "combat_bias": 0.3, "alliance_chance": 2.5, "attack_chance": 0.2}
                    },
                    "global_settings": {"relationship_influence": 1.0, "bias_randomization": 0.2, "enable_custom_tributes": True}
                }
            
            tribute = create_tribute_with_relationships(tributes, custom_config)
            if tribute:
                tributes.append(tribute)
                print(f"Added tribute: {tribute.name}")
            
        elif choice == "2":
            # Remove tribute
            try:
                idx = int(input("Enter tribute number to remove: ")) - 1
                if 0 <= idx < len(tributes):
                    removed = tributes.pop(idx)
                    print(f"Removed {removed.name}")
                    
                    # Also remove from tribute_upload.json
                    try:
                        with open("data/tribute_upload.json", "r") as f:
                            custom_config = json.load(f)
                        
                        if "custom_tributes" in custom_config:
                            # Find and remove the tribute by name
                            custom_config["custom_tributes"] = [
                                t for t in custom_config["custom_tributes"] 
                                if t["name"] != removed.name
                            ]
                            
                            # Save back to file
                            with open("data/tribute_upload.json", "w") as f:
                                json.dump(custom_config, f, indent=2)
                            
                            print(f"Removed {removed.name} from tribute_upload.json")
                        else:
                            print("Warning: Could not find custom_tributes in tribute_upload.json")
                    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Could not remove from tribute_upload.json: {e}")
                        
                else:
                    print("Invalid number")
            except ValueError:
                print("Invalid input")
                
        elif choice == "3":
            # Edit tribute
            try:
                idx = int(input("Enter tribute number to edit: ")) - 1
                if 0 <= idx < len(tributes):
                    t = tributes[idx]
                    original_name = t.name  # Store original name for JSON lookup
                    print(f"Editing {t.name}")
                    # Edit name
                    current_name = t.name
                    existing_names = [tr.name for tr in tributes if tr != t]
                    name = input(f"Name (first and last, current {current_name}): ").strip()
                    if name and name != current_name:
                        valid, error = validate_name(name, existing_names)
                        if valid:
                            t.name = name
                        else:
                            print(f"Keeping current name. Error: {error}")
                    # Edit skills
                    for skill in skills_config["skills"]:
                        current = t.skills.get(skill, 5)
                        try:
                            val = int(input(f"{skill} (1-10, current {current}): "))
                            valid, error = validate_skill(skill, val, skills_config)
                            if valid:
                                t.skills[skill] = val
                            else:
                                print(f"Keeping current value. Error: {error}")
                        except ValueError:
                            pass  # Keep current
                    # Edit weapons
                    while True:
                        print(f"\nCurrent weapons for {t.name}: {', '.join(t.weapons)} (Current: {t.current_weapon})")
                        print("Weapon options:")
                        print("1. Add weapon")
                        print("2. Remove weapon")
                        print("3. Switch current weapon")
                        print("4. Done editing weapons")
                        
                        weapon_choice = input("Choose option (1-4): ").strip()
                        
                        if weapon_choice == "1":
                            weapon = input("Weapon to add: ").strip()
                            if weapon:
                                valid, error = validate_weapon(weapon, weapons_data)
                                if valid:
                                    if t.add_weapon(weapon):
                                        print(f"Added {weapon} to {t.name}'s inventory")
                                    else:
                                        print(f"{t.name} already has {weapon}")
                                else:
                                    print(f"Error: {error}")
                        
                        elif weapon_choice == "2":
                            if len(t.weapons) > 1:  # Don't allow removing the last weapon
                                weapon = input("Weapon to remove: ").strip()
                                if t.remove_weapon(weapon):
                                    print(f"Removed {weapon} from {t.name}'s inventory")
                                else:
                                    print(f"{t.name} doesn't have {weapon} or can't remove it")
                            else:
                                print("Cannot remove the last weapon")
                        
                        elif weapon_choice == "3":
                            weapon = input("Switch to weapon: ").strip()
                            if t.switch_weapon(weapon):
                                print(f"Switched {t.name} to {weapon}")
                            else:
                                print(f"{t.name} doesn't have {weapon}")
                        
                        elif weapon_choice == "4":
                            break
                        
                        else:
                            print("Invalid choice")
                    # Edit district
                    try:
                        district = int(input(f"District (1-12, current {t.district}): "))
                        valid, error = validate_district(district, True)
                        if valid:
                            t.district = district
                        else:
                            print(f"Keeping current district. Error: {error}")
                    except ValueError:
                        pass
                    
                    # Save changes to tribute_upload.json
                    try:
                        with open("data/tribute_upload.json", "r") as f:
                            custom_config = json.load(f)
                        
                        # Find the tribute in custom_tributes by original name
                        if "custom_tributes" in custom_config:
                            for tribute_data in custom_config["custom_tributes"]:
                                if tribute_data["name"] == original_name:
                                    # Update the tribute data
                                    tribute_data["name"] = t.name
                                    tribute_data["district"] = t.district
                                    tribute_data["skills"] = t.skills
                                    tribute_data["weapons"] = t.weapons
                                    tribute_data["preferred_weapon"] = t.preferred_weapon
                                    tribute_data["target_weapon"] = t.target_weapon
                                    tribute_data["health"] = t.health
                                    tribute_data["sanity"] = t.sanity
                                    tribute_data["speed"] = t.speed
                                    tribute_data["has_camp"] = t.has_camp
                                    # Note: relationships are not updated here as they're complex
                                    break
                            
                            # Save back to file
                            with open("data/tribute_upload.json", "w") as f:
                                json.dump(custom_config, f, indent=2)
                            
                            print(f"Changes saved to tribute_upload.json")
                        else:
                            print("Warning: Could not find custom_tributes in tribute_upload.json")
                    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Could not save changes to tribute_upload.json: {e}")
                        
                else:
                    print("Invalid number")
            except ValueError:
                print("Invalid input")
                
        elif choice == "4":
            # Generate random tributes (no districts)
            try:
                current_count = len(tributes)
                if current_count >= 24:
                    print("Already have 24 or more tributes. Cannot generate more.")
                else:
                    remaining = 24 - current_count
                    print(f"Current tributes: {current_count}. Need {remaining} more for a full 24-tribute games.")
                    
                    # Ask if they want to fill to 24 or specify a number
                    fill_to_24 = input("Fill to 24 tributes automatically? (y/n): ").lower().strip() == 'y'
                    
                    if fill_to_24:
                        num = remaining
                        print(f"Generating {num} random tributes to reach 24 total...")
                    else:
                        num_input = input(f"How many random tributes to generate? (1-{remaining}): ")
                        num = min(int(num_input), remaining) if num_input.isdigit() else 0
                    
                    for _ in range(num):
                        tribute = generate_random_tribute(district=0)  # No district assignment
                        tributes.append(tribute)
                    print(f"Generated {num} random tributes (no districts). Total: {len(tributes)}")
            except ValueError:
                print("Invalid number")
                
        elif choice == "5":
            # Generate tributes by districts (2 per district)
            current_count = len(tributes)
            if current_count >= 24:
                print("Already have 24 or more tributes. Cannot generate more.")
            else:
                remaining = 24 - current_count
                needed_for_full = 24  # 2 per district = 24 total
                
                if current_count == 0:
                    # No tributes yet, offer full generation
                    confirm = input("This will generate 24 tributes (2 per district). Continue? (y/n): ").lower().strip()
                    if confirm == 'y':
                        # Clear existing tributes first
                        tributes.clear()
                        # Generate 2 tributes per district
                        for district in range(1, 13):
                            for _ in range(2):
                                tribute = generate_random_tribute(district=district)
                                tributes.append(tribute)
                        print("Generated 24 tributes (2 per district)")
                else:
                    # Have some tributes, offer to fill districts or specify number
                    print(f"Current tributes: {current_count}. Need {remaining} more for a full 24-tribute games.")
                    print("Options:")
                    print("1. Fill remaining slots with district-balanced tributes")
                    print("2. Specify exact number to generate")
                    
                    sub_choice = input("Choose option (1-2): ").strip()
                    
                    if sub_choice == "1":
                        # Fill districts that are missing tributes
                        district_counts = {}
                        for t in tributes:
                            district_counts[t.district] = district_counts.get(t.district, 0) + 1
                        
                        added = 0
                        for district in range(1, 13):
                            current_in_district = district_counts.get(district, 0)
                            needed = max(0, 2 - current_in_district)
                            for _ in range(min(needed, remaining - added)):
                                tribute = generate_random_tribute(district=district)
                                tributes.append(tribute)
                                added += 1
                        
                        print(f"Added {added} tributes to balance districts. Total: {len(tributes)}")
                    
                    elif sub_choice == "2":
                        try:
                            num_input = input(f"How many tributes to generate? (1-{remaining}): ")
                            num = min(int(num_input), remaining) if num_input.isdigit() else 0
                            
                            for _ in range(num):
                                # Assign to districts that need more tributes first
                                district_counts = {}
                                for t in tributes:
                                    district_counts[t.district] = district_counts.get(t.district, 0) + 1
                                
                                # Find district with fewest tributes
                                best_district = min(range(1, 13), key=lambda d: district_counts.get(d, 0))
                                tribute = generate_random_tribute(district=best_district)
                                tributes.append(tribute)
                            
                            print(f"Generated {num} tributes. Total: {len(tributes)}")
                        except ValueError:
                            print("Invalid number")
                
        elif choice == "6":
            # Generate specific number of tributes
            current_count = len(tributes)
            if current_count >= 24:
                print("Already have 24 or more tributes. Cannot generate more.")
            else:
                remaining = 24 - current_count
                try:
                    num_input = input(f"How many tributes to generate? (1-{remaining}): ")
                    num = min(int(num_input), remaining) if num_input.isdigit() else 0
                    
                    if num > 0:
                        for _ in range(num):
                            tribute = generate_random_tribute()
                            tributes.append(tribute)
                        print(f"Generated {num} random tributes. Total: {len(tributes)}")
                    else:
                        print("Invalid number or zero specified.")
                except ValueError:
                    print("Invalid number")
                
        elif choice == "7":
            # Remove all tributes
            confirm = input(f"Are you sure you want to remove all {len(tributes)} tributes? (y/n): ").lower().strip()
            if confirm == 'y':
                tributes.clear()
                print("All tributes removed")
                
        elif choice == "8":
            # Save current tributes to tribute_upload.json
            if not tributes:
                print("No tributes to save.")
            else:
                try:
                    # Load existing config or create new one
                    custom_config = None
                    try:
                        with open("data/tribute_upload.json", "r") as f:
                            custom_config = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        custom_config = {
                            "description": "Custom tribute configurations and relationships for Hunger Games simulation",
                            "version": "1.0",
                            "custom_tributes": [],
                            "relationship_types": {
                                "ally": {"description": "Tributes who trust and help each other", "combat_bias": -0.8, "alliance_chance": 3.0, "attack_chance": 0.1},
                                "enemy": {"description": "Tributes who actively target each other", "combat_bias": 2.5, "alliance_chance": 0.1, "attack_chance": 2.0},
                                "rival": {"description": "Competitive relationship with occasional conflicts", "combat_bias": 1.2, "alliance_chance": 0.5, "attack_chance": 1.5},
                                "neutral": {"description": "No strong feelings either way", "combat_bias": 1.0, "alliance_chance": 1.0, "attack_chance": 1.0},
                                "family": {"description": "Blood relatives", "combat_bias": 0.3, "alliance_chance": 2.5, "attack_chance": 0.2}
                            },
                            "global_settings": {"relationship_influence": 1.0, "bias_randomization": 0.2, "enable_custom_tributes": True}
                        }
                    
                    # Clear existing custom_tributes and replace with current tributes
                    custom_config["custom_tributes"] = []
                    
                    for tribute in tributes:
                        tribute_data = {
                            "name": tribute.name,
                            "district": tribute.district,
                            "skills": tribute.skills,
                            "weapons": tribute.weapons,
                            "preferred_weapon": tribute.preferred_weapon,
                            "target_weapon": tribute.target_weapon,
                            "health": tribute.health,
                            "sanity": tribute.sanity,
                            "speed": tribute.speed,
                            "has_camp": tribute.has_camp,
                            "relationships": {}  # Relationships would need to be extracted from tribute object
                        }
                        custom_config["custom_tributes"].append(tribute_data)
                    
                    # Save to file
                    with open("data/tribute_upload.json", "w") as f:
                        json.dump(custom_config, f, indent=2)
                    
                    print(f"Saved {len(tributes)} current tributes to tribute_upload.json")
                    
                except Exception as e:
                    print(f"Error saving tributes: {e}")
                
        elif choice == "9":
            break
        else:
            print("Invalid choice")

def get_tribute_action_type(tribute, phase, day, active_tributes, game_state):
    """
    Determine what action a tribute should take this phase using behavior tree AI.
    Returns: action string from behavior tree
    """
    # Initialize behavior tree if not already done
    if tribute.behavior_tree is None:
        tribute.initialize_behavior_tree()

    # Make decision using behavior tree
    return tribute.make_decision(game_state)

def choose_tribute_activity(tribute, game):
    """Choose an activity for a tribute based on their current needs and situation."""
    # Priority-based activity selection
    if tribute.food < 30:
        return "gather_food"
    elif tribute.water < 30:
        return "gather_water"
    elif tribute.health < 50 and random.random() < 0.7:
        return "rest"
    elif tribute.should_seek_weapon() and random.random() < 0.6:
        return "search_weapon"
    elif len(game.active_tributes) > 1 and random.random() < 0.9:
        return "hunt"
    elif random.random() < 0.3:
        return "explore"
    else:
        return "rest"

def execute_tribute_activity(tribute, activity, game):
    """Execute a tribute's chosen activity and return the result message."""
    if activity == "gather_food":
        if tribute.gather_food():
            return f"[+] {tribute.name} successfully gathers food!"
        else:
            return f"[-] {tribute.name} fails to find food."
    
    elif activity == "gather_water":
        if tribute.gather_water():
            return f"[+] {tribute.name} finds a water source!"
        else:
            return f"[-] {tribute.name} cannot find water."
    
    elif activity == "rest":
        # Resting recovers health and sanity
        health_gain = random.randint(5, 15)
        sanity_gain = random.randint(5, 10)
        tribute.health = min(100, tribute.health + health_gain)
        tribute.sanity = min(100, tribute.sanity + sanity_gain)
        return f"[+] {tribute.name} rests and recovers (Health +{health_gain}, Sanity +{sanity_gain})."
    
    elif activity == "search_weapon":
        # Simple weapon search
        if random.random() < 0.3:  # 30% chance
            weapons = ["Knife", "Sword", "Axe", "Bow", "Spear"]
            weapon = random.choice(weapons)
            if tribute.add_weapon(weapon):
                return f"[+] {tribute.name} finds a {weapon}!"
        return f"[-] {tribute.name} searches for weapons but finds nothing."
    
    elif activity == "hunt":
        # Attempt to hunt another tribute
        if len(game.active_tributes) > 1:
            # Find a suitable target
            potential_targets = [t for t in game.active_tributes if t != tribute and t.health > 20]
            if potential_targets:
                target = random.choice(potential_targets)
                # Simple combat resolution
                tribute_skill = tribute.skills.get('combat', 5) + tribute.skills.get('strength', 5)
                target_skill = target.skills.get('combat', 5) + target.skills.get('strength', 5)
                if random.random() < (tribute_skill / (tribute_skill + target_skill)):
                    # Successful hunt
                    damage = random.randint(20, 50)
                    target.health -= damage
                    if target.health <= 0:
                        game.active_tributes.remove(target)
                        game.eliminated_tributes.append(target)
                        return f"[KILL] {tribute.name} hunts down and eliminates {target.name}!"
                    else:
                        return f"[ATTACK] {tribute.name} ambushes {target.name} (Health: {target.health})!"
                else:
                    # Failed hunt - possible injury
                    if random.random() < 0.4:
                        damage = random.randint(10, 25)
                        tribute.health -= damage
                        return f"[BACKFIRE] {tribute.name}'s hunting attempt backfires! (Health: {tribute.health})"
                    else:
                        return f"[MISS] {tribute.name} attempts to hunt but {target.name} escapes."
        return f"[-] {tribute.name} searches for prey but finds no one."
    
    elif activity == "explore":
        # Exploration can lead to discoveries or dangers
        rand = random.random()
        if rand < 0.2:  # 20% chance of finding supplies
            supply_type = random.choice(["food", "water", "medical supplies"])
            if supply_type == "food":
                tribute.food = min(100, tribute.food + random.randint(20, 40))
                return f"[+] {tribute.name} discovers food while exploring!"
            elif supply_type == "water":
                tribute.water = min(100, tribute.water + random.randint(20, 40))
                return f"[+] {tribute.name} finds water while exploring!"
            else:
                tribute.health = min(100, tribute.health + random.randint(15, 30))
                return f"[+] {tribute.name} finds medical supplies while exploring!"
        
        elif rand < 0.3:  # 10% chance of danger
            damage = random.randint(10, 30)
            tribute.health -= damage
            if tribute.health <= 0:
                game.active_tributes.remove(tribute)
                game.eliminated_tributes.append(tribute)
                return f"[DEATH] {tribute.name} encounters danger while exploring and dies!"
            else:
                return f"[INJURY] {tribute.name} encounters danger while exploring! (Health: {tribute.health})"
        
        else:  # 70% chance of nothing interesting
            return f"[-] {tribute.name} explores the arena but finds nothing of interest."
    
    return f"[?] {tribute.name} spends the phase undecided."

def resolve_random_encounter(participants, game):
    """Resolve a random encounter between multiple tributes."""
    messages = []
    
    if len(participants) == 2:
        # Simple 1v1 combat
        t1, t2 = participants
        # Simple damage exchange instead of complex fight
        damage1 = random.randint(10, 30)
        damage2 = random.randint(10, 30)
        
        t1.health -= damage2
        t2.health -= damage1
        
        if t1.health <= 0 and t2.health <= 0:
            messages.append(f"[BOTH DIE] Both {t1.name} and {t2.name} die in the encounter!")
            game.active_tributes.remove(t1)
            game.active_tributes.remove(t2)
            game.eliminated_tributes.extend([t1, t2])
        elif t1.health <= 0:
            messages.append(f"[DEFEAT] {t1.name} is defeated by {t2.name}!")
            game.active_tributes.remove(t1)
            game.eliminated_tributes.append(t1)
        elif t2.health <= 0:
            messages.append(f"[DEFEAT] {t2.name} is defeated by {t1.name}!")
            game.active_tributes.remove(t2)
            game.eliminated_tributes.append(t2)
        else:
            messages.append(f"[DRAW] {t1.name} and {t2.name} fight but both survive. ({t1.name}: {t1.health}HP, {t2.name}: {t2.health}HP)")
    
    else:
        # Multi-tribute encounter - more chaotic
        messages.append("The encounter turns into a chaotic brawl!")
        
        # Each participant has a chance to fight
        survivors = participants[:]
        for tribute in participants:
            if tribute not in survivors:
                continue
                
            # Chance to engage in combat
            if random.random() < 0.7:  # 70% chance
                other_participants = [t for t in survivors if t != tribute]
                if other_participants:
                    target = random.choice(other_participants)
                    
                    # Simple damage exchange
                    damage = random.randint(10, 30)
                    target.health -= damage
                    
                    if target.health <= 0:
                        survivors.remove(target)
                        game.active_tributes.remove(target)
                        game.eliminated_tributes.append(target)
                        messages.append(f"[BRAWL KILL] {tribute.name} eliminates {target.name} in the brawl!")
                    else:
                        messages.append(f"[BRAWL WOUND] {tribute.name} wounds {target.name} (Health: {target.health})!")
        
        if len(survivors) == 1:
            messages.append(f"[BRAWL VICTOR] {survivors[0].name} emerges victorious from the brawl!")
        elif len(survivors) < len(participants):
            messages.append(f"The brawl leaves {len(survivors)} tributes standing.")
    
    return messages

def process_sponsor_gifts(game):
    """Process sponsor gifts for tributes."""
    messages = []
    
    # Chance of sponsor gifts each phase
    gift_chance = 0.15  # 15% chance per phase
    
    if random.random() < gift_chance:
        # Select a tribute to receive a gift
        eligible_tributes = [t for t in game.active_tributes if t.health > 10]  # Don't gift dying tributes
        
        if eligible_tributes:
            recipient = random.choice(eligible_tributes)
            
            # Determine gift type
            gift_types = [
                ("food", lambda t: setattr(t, 'food', min(100, t.food + random.randint(30, 50)))),
                ("water", lambda t: setattr(t, 'water', min(100, t.water + random.randint(30, 50)))),
                ("medical supplies", lambda t: setattr(t, 'health', min(100, t.health + random.randint(20, 40)))),
                ("weapon", lambda t: t.add_weapon(random.choice(["Knife", "Sword", "Axe", "Bow"]))),
            ]
            
            gift_name, gift_effect = random.choice(gift_types)
            gift_effect(recipient)
            
            messages.append(f"[GIFT] {recipient.name} receives a sponsor gift: {gift_name}!")
    
    return messages

def main():
    """Main simulation function using the core GameState engine."""
    print("DEBUG: main() called")
    output_mode = settings_manager.get_game_mode()
    print(f"DEBUG: output_mode = {output_mode}")

    # Read game settings from environment variables
    phase_delay_config = {
        'base_delay': float(os.environ.get('HUNGER_GAMES_PHASE_DELAY', '3' if output_mode == 'console' else '0.05'))
    }

    # Initialize game state
    game = GameState()
    
    # Load configuration files
    with open("data/messages.json", "r") as f:
        messages = json.load(f)
    
    with open("data/game_config.json", "r") as f:
        game_config = json.load(f)
    
    # Clear web output at start
    if output_mode == 'web':
        output_manager.clear_web_output()
        output_manager.output_message("Initializing Hunger Games Simulation...", {'status': 'initializing'})
    
    # Skip tribute setup in web mode - assume tributes are already configured
    if output_mode == 'console':
        # Interactive tribute setup for console mode
        tributes = setup_tributes_console()
    else:
        # Load tributes for web mode
        tributes = load_tributes_web()
    
    # Initialize game with tributes
    game.active_tributes = tributes.copy()
    
    # Run the core simulation
    run_simulation(game, messages, game_config, phase_delay_config)

def setup_tributes_console():
    """Set up tributes for console mode (interactive)."""
    # This would contain the interactive tribute setup logic
    # For now, just generate random tributes
    tributes = []
    for _ in range(24):
        tribute = generate_random_tribute()
        tributes.append(tribute)
    return tributes

def load_tributes_web():
    """Load tributes for web mode (non-interactive)."""
    tributes = []
    
    # Try to load saved tributes first
    saved_tributes = load_initial_tributes()
    if saved_tributes:
        tributes = saved_tributes
    else:
        # Generate fresh random tributes
        for _ in range(24):
            tribute = generate_random_tribute()
            tributes.append(tribute)
    
    return tributes

def run_simulation(game, messages, game_config, phase_delay_config):
    """Run the core simulation loop using the GameState engine."""
    output_mode = settings_manager.get_game_mode()

    # Simulation parameters
    max_turns = 100  # Reduced from 200 to make games shorter
    turn_count = 0

    # Helper functions
    def get_scaled_probability(base_key, phase=None, default=0.0):
        """Get a probability scaled by day progression."""
        if phase:
            base_prob = game_config["event_probabilities"].get(phase, {}).get(base_key, default)
        else:
            base_prob = game_config["event_probabilities"].get(base_key, default)
        
        # Apply day-based scaling
        scaling_start = game_config["scaling"]["day_scaling_start"]
        if game.day >= scaling_start:
            days_scaled = game.day - scaling_start + 1
            scaling_factor = game_config["scaling"]["event_frequency_multiplier"] ** (days_scaled - 1)
            base_prob = min(0.95, base_prob * scaling_factor)  # Cap at 95%
        
        return base_prob
    
    def get_message(category, key, **kwargs):
        msg = messages[category][key]
        if isinstance(msg, list):
            msg = random.choice(msg)
        return msg.format(**kwargs)
    
    def build_comprehensive_game_data(game, turn_count):
        """Build comprehensive game data for web output including detailed tribute information."""
        # Build detailed tribute data
        active_tributes_data = []
        for tribute in game.active_tributes:
            tribute_data = {
                'id': tribute.id,
                'name': tribute.name,
                'district': tribute.district,
                'gender': tribute.gender,
                'health': tribute.health,
                'sanity': tribute.sanity,
                'status': tribute.status,
                'kills': tribute.kills,
                'weapons': tribute.weapons,
                'preferred_weapon': tribute.preferred_weapon,
                'skills': tribute.skills,
                'allies': tribute.allies,
                'has_camp': tribute.has_camp,
                'speed': tribute.speed,
                'bleeding': tribute.bleeding,
                'infection': tribute.infection,
                'food': tribute.food,
                'water': tribute.water,
                'shelter': tribute.shelter,
                'is_sick': tribute.is_sick,
                'sickness_type': tribute.sickness_type,
                'weight': tribute.weight,
                'max_weight': tribute.max_weight,
                'camp_inventory': tribute.camp_inventory,
                'traps': len(tribute.traps),  # Just count for now
                'ongoing_effects': len(tribute.ongoing_effects)  # Just count for now
            }
            active_tributes_data.append(tribute_data)
        
        # Build eliminated tributes summary
        eliminated_tributes_data = []
        for tribute in game.eliminated_tributes:
            tribute_data = {
                'name': tribute.name,
                'district': tribute.district,
                'cause_of_death': getattr(tribute, 'cause_of_death', 'Unknown'),
                'day_eliminated': getattr(tribute, 'day_eliminated', game.day),
                'kills': len(tribute.kills)
            }
            eliminated_tributes_data.append(tribute_data)
        
        # Build environmental data
        environmental_data = {
            'active_weather_events': game.active_weather_events,
            'active_danger_zones': game.active_danger_zones,
            'active_environmental_effects': game.active_environmental_effects
        }
        
        # Build comprehensive game data
        game_data = {
            'day': game.day,
            'phase': game.phase,
            'current_phase': game.current_phase,
            'turn': turn_count,
            'active_tributes_count': len(game.active_tributes),
            'eliminated_tributes_count': len(game.eliminated_tributes),
            'total_tributes': len(game.active_tributes) + len(game.eliminated_tributes),
            'active_tributes': active_tributes_data,
            'eliminated_tributes': eliminated_tributes_data,
            'environmental_effects': environmental_data,
            'game_status': 'running'
        }
        
        return game_data
    
    # Main simulation loop
    while len(game.active_tributes) > 1 and turn_count < max_turns and game.day <= 20:  # Cap at 20 days
        turn_count += 1
        
        # Update web output with current status
        active_tribute_names = [t.name for t in game.active_tributes]
        game_data = build_comprehensive_game_data(game, turn_count)
        
        if output_mode == 'console':
            print(f"\nDay {game.day}, Phase: {game.phase}")
            print(f"Active Tributes ({len(game.active_tributes)}):")
            for tribute in game.active_tributes:
                print(f"  {tribute.name} (District {tribute.district}) - Health: {tribute.health}")
        else:
            output_manager.output_message(f'Day {game.day}, Phase: {game.phase} - {len(game.active_tributes)} tributes remaining', game_data)
        
        # Process phase activities (simplified version)
        process_phase_activities(game, messages, game_config, get_message, get_scaled_probability)
        
        # Check for winner after phase activities
        if len(game.active_tributes) == 1:
            winner = game.active_tributes[0]
            result = {
                'success': True,
                'winner': winner.name,
                'stats': {
                    'total_tributes': len(game.active_tributes) + len(game.eliminated_tributes),
                    'turns_survived': turn_count,
                    'final_tributes': len(game.active_tributes)
                }
            }
            
            if output_mode == 'console':
                print(f"\n*** WINNER: {winner.name} from District {winner.district}! ***")
                print(json.dumps(result, indent=2))
            else:
                output_manager.write_game_state({'status': 'completed', 'message': f'Game finished! Winner: {winner.name}', 'result': result})
            
            return result
        
        # Advance phase
        game.advance_phase()
        game.save()
        
        # Phase delay
        delay = get_phase_delay(game, phase_delay_config)
        if delay > 0:
            time.sleep(delay)
    
    # No winner - game ended due to turn limit or day limit
    result = {
        'success': False,
        'winner': 'None',
        'stats': {
            'total_tributes': len(game.active_tributes) + len(game.eliminated_tributes),
            'turns_survived': turn_count,
            'final_tributes': len(game.active_tributes)
        }
    }
    
    if output_mode == 'console':
        print("\nNo winner - game ended due to time limit!")
        print(json.dumps(result, indent=2))
    else:
        output_manager.write_game_state({'status': 'completed', 'message': 'Game ended due to time limit - no winner', 'result': result})
    
    return result

def process_phase_activities(game, messages, game_config, get_message, get_scaled_probability):
    """Process activities for the current phase (simplified version)."""
    # Tribute activities
    for tribute in game.active_tributes[:]:  # Copy to avoid modification issues
        if tribute.health <= 0:
            if tribute in game.active_tributes:
                game.active_tributes.remove(tribute)
                game.eliminated_tributes.append(tribute)
            continue
            
        # Simple activity selection
        activity = choose_tribute_activity(tribute, game)
        result = execute_tribute_activity(tribute, activity, game)
        
        if result:
            if settings_manager.get_game_mode() == 'console':
                print(result)
            else:
                output_manager.output_message(result)
    
    # Random encounters
    if len(game.active_tributes) >= 2 and random.random() < 0.3:  # 30% chance
        if settings_manager.get_game_mode() == 'console':
            print(f"\n=== **RANDOM ENCOUNTER** ===")
        
        num_participants = min(len(game.active_tributes), random.randint(2, 3))
        participants = random.sample(game.active_tributes, num_participants)
        
        if settings_manager.get_game_mode() == 'console':
            print(f"A confrontation breaks out between {len(participants)} tributes:")
            for tribute in participants:
                print(f"  - {tribute.name}")
        
        # Resolve encounter
        messages = resolve_random_encounter(participants, game)
        for message in messages:
            if settings_manager.get_game_mode() == 'console':
                print(message)
            else:
                output_manager.output_message(message)
        
        if settings_manager.get_game_mode() == 'console':
            print(f"=== **RANDOM ENCOUNTER ENDS** ===")
    
    # Arena events (simplified)
    if random.random() < 0.1:  # 10% chance
        if settings_manager.get_game_mode() == 'console':
            print(f"\n--- **ARENA EVENT** ---")
        
        event_messages = trigger_random_event(game)
        if event_messages:
            if settings_manager.get_game_mode() == 'console':
                print(event_messages)
            else:
                output_manager.output_message(event_messages)
        
        if settings_manager.get_game_mode() == 'console':
            print(f"--- **ARENA EVENT ENDS** ---")
    
    # Sponsor gifts
    sponsor_messages = process_sponsor_gifts(game)
    if sponsor_messages:
        if settings_manager.get_game_mode() == 'console':
            print(f"\n+++ **SPONSOR GIFTS** +++")
        for message in sponsor_messages:
            if settings_manager.get_game_mode() == 'console':
                print(message)
            else:
                output_manager.output_message(message)
        if settings_manager.get_game_mode() == 'console':
            print(f"+++ **SPONSOR GIFTS END** +++")

if __name__ == '__main__':
    main()


