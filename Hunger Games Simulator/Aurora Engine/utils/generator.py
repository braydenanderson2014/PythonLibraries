import random
import json
from tributes.tribute import Tribute

def generate_random_tribute(district: int = None) -> Tribute:
    with open('data/tribute_names.json', 'r') as f:
        first_names = json.load(f)
    
    with open('data/last_names.json', 'r') as f:
        last_names = json.load(f)
    
    with open('data/weapons.json', 'r') as f:
        weapons_data = json.load(f)
    
    with open('data/skills.json', 'r') as f:
        skills_config = json.load(f)
    
    weapons = list(weapons_data.keys())
    skill_names = skills_config["skills"]
    
    # Generate unique full name
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    name = f"{first_name} {last_name}"
    
    # Generate skills with weighted randomization based on attribute ratings
    skills = generate_weighted_skills(skill_names, skills_config["range"])
    
    weapon = random.choice(weapons)
    district_num = district if district is not None else random.randint(1, 12)
    speed = random.randint(1, 10)
    gender = random.choice(["male", "female"])

    # Assign preferred weapon (different from starting weapon sometimes)
    preferred_weapon = random.choice(weapons)
    # Make sure preferred weapon is different from starting weapon 70% of the time
    if random.random() < 0.7 and len(weapons) > 1:
        while preferred_weapon == weapon:
            preferred_weapon = random.choice(weapons)
    
    tribute = Tribute(name, skills, ["Fists"], district_num, gender=gender, speed=speed)
    tribute.set_preferred_weapon(preferred_weapon)
    
    # Assign secret skills based on district
    from tributes.tribute import assign_secret_skills
    assign_secret_skills(tribute)
    
    return tribute

def generate_weighted_skills(skill_names: list, skill_range: dict) -> dict:
    """
    Generate skills with weighted randomization based on attribute ratings.
    Each tribute gets a "rating profile" that determines their general strengths.
    """
    min_val = skill_range["min"]
    max_val = skill_range["max"]
    range_size = max_val - min_val + 1
    
    # Define possible rating profiles (high-low attribute distributions)
    profiles = [
        {"name": "balanced", "weights": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]},  # All skills average
        {"name": "warrior", "weights": [0.8, 0.3, 0.9, 0.4, 0.6, 0.7, 0.8, 0.9, 0.5, 0.6]},   # Strength, agility, endurance high
        {"name": "hunter", "weights": [0.6, 0.9, 0.7, 0.5, 0.8, 0.8, 0.9, 0.7, 0.4, 0.7]},    # Hunting, stealth, survival, agility high
        {"name": "thinker", "weights": [0.9, 0.4, 0.5, 0.8, 0.7, 0.6, 0.5, 0.6, 0.9, 0.5]},    # Intelligence, social, charisma high
        {"name": "social", "weights": [0.5, 0.6, 0.4, 0.9, 0.8, 0.5, 0.6, 0.5, 0.9, 0.7]},     # Social, stealth, charisma high
        {"name": "weakling", "weights": [0.3, 0.4, 0.2, 0.6, 0.5, 0.4, 0.3, 0.3, 0.7, 0.4]},   # Generally weak but social
        {"name": "beast", "weights": [0.4, 0.8, 0.9, 0.3, 0.7, 0.8, 0.9, 0.8, 0.4, 0.6]},       # Strength, hunting, agility, endurance high
    ]
    
    # Choose a random profile for this tribute
    profile = random.choice(profiles)
    
    skills = {}
    for i, skill in enumerate(skill_names):
        # Get base value based on profile weight
        weight = profile["weights"][i]
        
        # Add some randomization around the weighted value
        # Higher weight = higher average skill, but still with variation
        base_value = min_val + (weight * range_size)
        
        # Add random variation (±30% of range)
        variation = (range_size * 0.3) * (random.random() - 0.5) * 2
        final_value = base_value + variation
        
        # Clamp to valid range
        final_value = max(min_val, min(max_val, round(final_value)))
        skills[skill] = int(final_value)
    
    return skills