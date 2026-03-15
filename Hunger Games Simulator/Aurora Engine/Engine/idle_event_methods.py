"""
Enhanced Idle Event Generation System
Rich, dramatic narratives for tribute survival activities
"""

import random
from typing import Dict, List, Any, Optional


# ========== RICH SURVIVAL NARRATIVES ==========

HUNTING_SUCCESS_NARRATIVES = [
    "{name} spots fresh tracks leading through the underbrush. Moving with predatory grace, they stalk their prey with unwavering focus. The kill is clean and swift—survival for another day.",
    "Hours of patient waiting pay off as {name} catches sight of a rabbit. Their throw is perfect, the makeshift spear finding its mark. Fresh meat is a luxury in the arena.",
    "Drawing on years of experience from District {district}, {name} sets a series of clever snares. By evening, they've caught enough game to ease the gnawing hunger.",
    "{name} discovers a pristine fishing spot, hidden from other tributes. Using improvised tackle, they pull up fish after fish, securing valuable protein.",
    "The forest yields its bounty to {name}'s skilled hands. Berries, edible roots, and eventually a grouse—tonight they'll eat well.",
]

HUNTING_FAILURE_NARRATIVES = [
    "{name} pursues prey for hours, but every sound sends their quarry fleeing. Exhausted and empty-handed, they must conserve their dwindling energy.",
    "Despite {name}'s best efforts, the wildlife seems to sense their desperation. Every trap comes up empty. Hunger gnaws deeper.",
    "A promising hunt turns sour when {name}'s weapon breaks at the crucial moment. The prey escapes, leaving only frustration.",
    "{name} tracks an animal to the river's edge, but loses the trail in the rocks. Hours wasted, energy depleted, nothing to show for it.",
    "The arena's ecosystem works against {name} today. Every potential food source has been claimed by others or scared away by arena hazards.",
]

WATER_SUCCESS_NARRATIVES = [
    "{name} follows the sound of running water to a crystal-clear stream hidden in a ravine. They drink deeply, filling every container they have.",
    "Using survival training from home, {name} constructs a water collection system from leaves and bark. By morning, they'll have clean water.",
    "After searching all day, {name} finally discovers a spring bubbling up from between rocks. The water tastes like salvation.",
    "{name} remembers lessons from their district and digs where the earth is damp. Three feet down, they strike water. It's murky but life-saving.",
    "A recent rainstorm left pools of water in the hollows of trees. {name} carefully collects every drop, knowing dehydration is as deadly as any tribute.",
]

WATER_FAILURE_NARRATIVES = [
    "{name}'s throat burns with thirst, but every water source they find is contaminated or dried up. Time is running out.",
    "The stream {name} remembered from yesterday has disappeared—diverted or evaporated by the Gamemakers. Panic begins to set in.",
    "{name} tries to extract moisture from plants, but lacks the knowledge. Their efforts only waste precious energy.",
    "Every promising water source leads to disappointment. {name} realizes the Gamemakers are deliberately making survival harder.",
    "Desperation drives {name} to drink from a questionable source. Within hours, they're sick, worse off than before.",
]

SHELTER_SUCCESS_NARRATIVES = [
    "As darkness approaches, {name} works frantically to construct a shelter. Using branches, leaves, and vines, they create a hidden refuge that might keep them alive through the night.",
    "{name} discovers a cave partially hidden by vegetation. After checking for predators, they claim it as their base. It's defensible and concealed—perfect.",
    "Drawing on ingenuity and determination, {name} builds a platform high in a tree. From this vantage point, they can see threats coming and stay above ground predators.",
    "{name} finds the ruins of an old Gamemaker structure and adapts it into livable space. The metal walls will protect them from wind and rain.",
    "Using a tarp scavenged from the cornucopia, {name} creates a waterproof shelter tucked against a cliff face. They can finally rest in relative safety.",
]

SHELTER_FAILURE_NARRATIVES = [
    "{name} attempts to build shelter, but their construction collapses in the wind. They'll spend another night exposed to the elements.",
    "Darkness falls before {name} can complete their shelter. They huddle under a tree, vulnerable and cold.",
    "The shelter {name} builds attracts attention—too obvious, too visible. They abandon it, realizing stealth matters more than comfort.",
    "{name}'s chosen campsite floods during a sudden rainstorm. Everything is soaked. This night will be miserable.",
    "Exhaustion defeats {name} before they can finish their shelter. They slump against a tree, too tired to care about the danger.",
]

EXPLORATION_NARRATIVES = [
    "{name} ventures into unexplored territory, discovering a cache of supplies half-buried in the undergrowth. Someone's loss is their gain.",
    "Climbing to high ground, {name} scouts the arena's layout, noting tribute positions and strategic locations. Knowledge is power.",
    "{name} finds evidence of other tributes—a discarded wrapper, trampled grass, blood on the rocks. They make note of the direction and proceed cautiously.",
    "The arena's landscape shifts before {name}'s eyes—a Gamemaker manipulation. They quickly reorient themselves, adapting to the new terrain.",
    "{name} discovers a area rich with resources: medicinal plants, fresh water, and game trails. They memorize the location for future use.",
    "While exploring, {name} narrowly avoids a trap—either set by the Gamemakers or another tribute. Death lurks everywhere in the arena.",
]

MEDICAL_SUCCESS_NARRATIVES = [
    "{name} finds medicinal plants growing near the stream. Using knowledge from home, they create a poultice for their wounds. The pain eases.",
    "Desperation breeds innovation. {name} fashions bandages from torn fabric and cleans their wounds with boiled water. It's not medicine, but it helps.",
    "{name} remembers training and treats their injuries methodically: clean, bind, elevate. Their body begins to heal.",
    "A sponsor gift drifts down on a silver parachute—medical supplies! {name} gratefully applies antibiotics and fresh bandages. Someone is watching out for them.",
    "Using honey found in a tree hollow, {name} creates natural antiseptic for their wounds. Old survival knowledge proves invaluable.",
]

MEDICAL_FAILURE_NARRATIVES = [
    "{name}'s wounds worsen without proper treatment. Infection is setting in. They need real medical supplies soon, or consequences will be dire.",
    "Attempting to treat themselves, {name} accidentally makes things worse. The pain is excruciating, and they've wasted precious supplies.",
    "{name} searches desperately for medicinal plants but can't identify them safely. Using the wrong plant could be as deadly as the injury.",
    "Without antiseptic, {name} can only watch as their injuries fester. Every movement brings agony. They need help they won't receive.",
    "The makeshift bandages {name} applied come loose and get dirty. The infection spreads. Time is running out.",
]

FIRE_SUCCESS_NARRATIVES = [
    "After countless attempts, {name} finally coaxes flames from friction. The fire catches, grows, becomes a beacon of warmth and hope. They can cook food and purify water now.",
    "{name} uses a trick learned in training: focusing sunlight through a piece of ice. Soon, they have fire—warmth, safety, and a psychological victory.",
    "Finding matches in a supply pack, {name} carefully starts a small, controlled fire. They keep it low to avoid smoke—no sense advertising their position.",
    "{name}'s fire-starting skills serve them well. Within minutes, flames crackle to life. The night won't be so cold after all.",
    "Using flint and steel from the cornucopia, {name} builds a fire with practiced efficiency. The warmth is heavenly.",
]

CHARACTER_MOMENT_NARRATIVES = [
    "{name} sits alone, staring at the night sky, thinking of home. Tears threaten, but they push them back. Weakness is death in the arena.",
    "A wave of homesickness washes over {name}. They clutch a token from home, drawing strength from the memory of loved ones.",
    "{name} talks to themselves, maintaining sanity through the isolation. \"Just one more day. I can survive one more day.\"",
    "Watching the sun set, {name} wonders how many sunsets they have left. The thought is quickly suppressed—survival requires focus.",
    "{name} finds a moment of peace, a brief respite from the constant terror. They know it won't last, but they savor it.",
    "The weight of taking a life settles on {name}'s shoulders. They tell themselves it was necessary, survival, but the guilt remains.",
    "{name} strategizes their next move, planning, adapting. The games are as much mental as physical.",
]


def _generate_context_aware_idle_event(self, tribute_id: str, tribute) -> Optional[Dict[str, Any]]:
    """Generate idle events based on tribute's current needs and situation"""
    # Analyze tribute's most pressing needs
    needs = []
    
    hunger_val = getattr(tribute, 'hunger', 0)
    thirst_val = getattr(tribute, 'thirst', 0)
    health_val = getattr(tribute, 'health', 100)
    fatigue_val = getattr(tribute, 'fatigue', 0)
    has_shelter = getattr(tribute, 'has_shelter', False)
    has_fire = getattr(tribute, 'has_fire', False)
    
    if hunger_val > 60:
        needs.append(('hunger', hunger_val))
    if thirst_val > 65:
        needs.append(('thirst', thirst_val))
    if health_val < 50:
        needs.append(('health', 100 - health_val))
    if fatigue_val > 70:
        needs.append(('fatigue', fatigue_val))
    if not has_shelter:
        needs.append(('shelter', 50))
    if not has_fire:
        needs.append(('fire', 40))
        
    # Sort by urgency
    needs.sort(key=lambda x: x[1], reverse=True)
    
    # 20% chance for character moment regardless of needs
    if random.random() < 0.20:
        return self._generate_character_moment(tribute_id, tribute)
    
    if not needs:
        # No pressing needs, generate exploration/strategic event
        return self._generate_exploration_event(tribute_id, tribute)
    
    # Address most urgent need
    primary_need = needs[0][0]
    
    if primary_need == 'hunger':
        return self._generate_hunting_event(tribute_id, tribute)
    elif primary_need == 'thirst':
        return self._generate_water_search_event(tribute_id, tribute)
    elif primary_need == 'health':
        return self._generate_medical_event(tribute_id, tribute)
    elif primary_need == 'fatigue':
        return self._generate_rest_event(tribute_id, tribute)
    elif primary_need == 'shelter':
        return self._generate_shelter_building_event(tribute_id, tribute)
    elif primary_need == 'fire':
        return self._generate_fire_building_event(tribute_id, tribute)
        
    return None


def _generate_hunting_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate hunting/gathering event with rich narratives"""
    survival_skill = tribute.skills.get('survival', 5)
    strength = tribute.skills.get('strength', 5)
    luck = tribute.skills.get('luck', 5)
    
    # Success calculation based on skills
    success_chance = (survival_skill * 0.5 + strength * 0.3 + luck * 0.2) / 10
    success_chance = max(0.2, min(0.8, success_chance))  # Cap between 20% and 80%
    
    success = random.random() < success_chance
    
    # Get tribute details for narrative personalization
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    if success:
        food_gained = random.randint(2, 5)
        hunger_reduction = -random.randint(25, 45)
        
        narrative = random.choice(HUNTING_SUCCESS_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏹 {name} successfully hunts for food"
        
        consequences = [
            {"type": "resource_add", "resource": "food", "amount": food_gained, "target": tribute_id},
            {"type": "stat_effect", "stat": "hunger", "value": hunger_reduction, "target": tribute_id}
        ]
        intensity = "medium"
    else:
        fatigue_increase = random.randint(10, 25)
        hunger_increase = random.randint(5, 15)
        
        narrative = random.choice(HUNTING_FAILURE_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏹 {name} hunts unsuccessfully"
        
        consequences = [
            {"type": "stat_effect", "stat": "fatigue", "value": fatigue_increase, "target": tribute_id},
            {"type": "stat_effect", "stat": "hunger", "value": hunger_increase, "target": tribute_id}
        ]
        intensity = "low"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": intensity,
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_water_search_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate water searching event with rich narratives"""
    survival_skill = tribute.skills.get('survival', 5)
    intelligence = tribute.skills.get('intelligence', 5)
    luck = tribute.skills.get('luck', 5)
    
    success_chance = (survival_skill * 0.4 + intelligence * 0.4 + luck * 0.2) / 10
    success_chance = max(0.25, min(0.75, success_chance))
    
    success = random.random() < success_chance
    
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    if success:
        thirst_reduction = -random.randint(40, 70)
        health_boost = random.randint(5, 10)
        
        narrative = random.choice(WATER_SUCCESS_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"💧 {name} finds clean water"
        
        consequences = [
            {"type": "stat_effect", "stat": "thirst", "value": thirst_reduction, "target": tribute_id},
            {"type": "stat_effect", "stat": "health", "value": health_boost, "target": tribute_id}
        ]
        intensity = "medium"
    else:
        fatigue_increase = random.randint(15, 30)
        thirst_increase = random.randint(10, 20)
        
        narrative = random.choice(WATER_FAILURE_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"💧 {name} fails to find water"
        
        consequences = [
            {"type": "stat_effect", "stat": "fatigue", "value": fatigue_increase, "target": tribute_id},
            {"type": "stat_effect", "stat": "thirst", "value": thirst_increase, "target": tribute_id}
        ]
        intensity = "medium"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": intensity,
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_shelter_building_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate shelter building event"""
    survival_skill = tribute.skills.get('survival', 5)
    intelligence = tribute.skills.get('intelligence', 5)
    
    success_chance = (survival_skill * 0.6 + intelligence * 0.4) / 10
    success_chance = max(0.3, min(0.8, success_chance))
    
    success = random.random() < success_chance
    
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    if success:
        narrative = random.choice(SHELTER_SUCCESS_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏕️ {name} builds a shelter"
        
        consequences = [
            {"type": "shelter_gained", "target": tribute_id},
            {"type": "stat_effect", "stat": "fatigue", "value": 20, "target": tribute_id}
        ]
        intensity = "medium"
    else:
        narrative = random.choice(SHELTER_FAILURE_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏕️ {name} fails to build adequate shelter"
        
        consequences = [
            {"type": "stat_effect", "stat": "fatigue", "value": 30, "target": tribute_id}
        ]
        intensity = "low"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": intensity,
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_fire_building_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate fire building event"""
    survival_skill = tribute.skills.get('survival', 5)
    intelligence = tribute.skills.get('intelligence', 5)
    
    success_chance = (survival_skill * 0.7 + intelligence * 0.3) / 10
    success_chance = max(0.2, min(0.7, success_chance))
    
    success = random.random() < success_chance
    
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    if success:
        narrative = random.choice(FIRE_SUCCESS_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🔥 {name} successfully starts a fire"
        
        consequences = [
            {"type": "fire_gained", "target": tribute_id},
            {"type": "stat_effect", "stat": "hunger", "value": -15, "target": tribute_id}
        ]
        intensity = "low"
    else:
        narrative = f"{name} struggles for hours trying to start a fire. Their hands are raw, their energy depleted, but no spark catches. They'll have to endure the cold."
        description = f"🔥 {name} fails to start a fire"
        
        consequences = [
            {"type": "stat_effect", "stat": "fatigue", "value": 25, "target": tribute_id}
        ]
        intensity = "low"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": intensity,
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_exploration_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate exploration event"""
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    narrative = random.choice(EXPLORATION_NARRATIVES).format(
        name=name,
        district=district
    )
    description = f"🔍 {name} explores the arena"
    
    # Small chance of finding something useful
    if random.random() < 0.3:
        consequences = [
            {"type": "resource_add", "resource": "supplies", "amount": 1, "target": tribute_id}
        ]
    else:
        consequences = [
            {"type": "stat_effect", "stat": "fatigue", "value": 10, "target": tribute_id}
        ]
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": "low",
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_medical_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate medical treatment event"""
    intelligence = tribute.skills.get('intelligence', 5)
    survival_skill = tribute.skills.get('survival', 5)
    
    success_chance = (intelligence * 0.5 + survival_skill * 0.5) / 10
    success_chance = max(0.2, min(0.7, success_chance))
    
    success = random.random() < success_chance
    
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    if success:
        healing = random.randint(15, 30)
        narrative = random.choice(MEDICAL_SUCCESS_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏥 {name} treats their injuries"
        
        consequences = [
            {"type": "stat_effect", "stat": "health", "value": healing, "target": tribute_id}
        ]
        intensity = "medium"
    else:
        damage = random.randint(5, 15)
        narrative = random.choice(MEDICAL_FAILURE_NARRATIVES).format(
            name=name,
            district=district
        )
        description = f"🏥 {name}'s injuries worsen"
        
        consequences = [
            {"type": "stat_effect", "stat": "health", "value": -damage, "target": tribute_id}
        ]
        intensity = "medium"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": intensity,
        "participants": [tribute_id],
        "consequences": consequences
    }


def _generate_rest_event(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate rest/recovery event"""
    name = getattr(tribute, 'name', 'A tribute')
    
    fatigue_reduction = -random.randint(20, 40)
    health_bonus = random.randint(5, 10)
    
    narratives = [
        f"{name} finds a secure hiding spot and allows themselves to rest. Sleep comes quickly, exhaustion claiming them. They wake hours later, slightly refreshed.",
        f"Taking a calculated risk, {name} stops to recuperate. Their body desperately needs the break. The gamble pays off—they rest undisturbed.",
        f"{name} climbs high into a tree and wedges themselves into the branches. It's not comfortable, but it's safe. They doze fitfully, regaining some strength.",
    ]
    
    narrative = random.choice(narratives)
    description = f"😴 {name} rests and recovers"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": "low",
        "participants": [tribute_id],
        "consequences": [
            {"type": "stat_effect", "stat": "fatigue", "value": fatigue_reduction, "target": tribute_id},
            {"type": "stat_effect", "stat": "health", "value": health_bonus, "target": tribute_id}
        ]
    }


def _generate_character_moment(self, tribute_id: str, tribute) -> Dict[str, Any]:
    """Generate introspective character moment"""
    name = getattr(tribute, 'name', 'A tribute')
    district = getattr(tribute, 'district', '?')
    
    narrative = random.choice(CHARACTER_MOMENT_NARRATIVES).format(
        name=name,
        district=district
    )
    description = f"💭 {name} reflects on their situation"
    
    return {
        "description": description,
        "narrative": narrative,
        "intensity": "low",
        "participants": [tribute_id],
        "consequences": []
    }
