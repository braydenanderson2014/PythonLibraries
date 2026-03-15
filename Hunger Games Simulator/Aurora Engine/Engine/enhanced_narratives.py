"""
Enhanced Combat and Arena Event Narratives
Dramatic fight scenes, deaths, and environmental dangers
"""

import random
from typing import Dict, List, Any

# ========== COMBAT NARRATIVES ==========

COMBAT_INITIATION = [
    "{attacker} spots {defender} across the clearing. Eyes lock. There's a moment of terrible understanding—only one can walk away.",
    "The forest erupts in violence as {attacker} launches a surprise attack on {defender}. There's no time for words, only survival.",
    "{attacker} and {defender} circle each other warily. Both know this encounter will end in blood.",
    "Fate brings {attacker} and {defender} face-to-face. The arena demands death. Only one will provide it.",
    "{attacker} makes their move, weapon raised. {defender} barely has time to react. The fight for survival begins.",
]

COMBAT_CLOSE = [
    "The fight is brutal and desperate. {attacker}'s {weapon} clashes against {defender}'s defense.",
    "{attacker} presses the attack relentlessly. {defender} fights back with everything they have.",
    "Blood flows as {attacker} and {defender} trade blows. Neither willing to yield, both knowing death waits for the loser.",
    "The combatants move like dancers in a deadly ballet, {attacker}'s {weapon} seeking an opening.",
    "{attacker} channels rage and desperation into every strike. {defender} counters with skill born of survival instinct.",
]

KILL_NARRATIVES_WEAPON = {
    "Sword": [
        "{attacker}'s blade finds its mark. {defender} gasps, eyes wide with shock, before crumpling to the ground.",
        "With a practiced strike, {attacker} drives their sword through {defender}'s defenses. The end is swift.",
        "Steel flashes in the sunlight. {defender}'s blood stains the arena floor. {attacker} stands victorious, but there's no joy in it.",
    ],
    "Knife": [
        "{attacker} moves with deadly speed, knife finding vital areas. {defender} doesn't stand a chance.",
        "The knife is quick and silent. {defender} falls without a sound, another victim of the arena.",
        "{attacker}'s blade work is expert, brutal, final. {defender}'s life ends in a flash of steel.",
    ],
    "Spear": [
        "{attacker}'s spear thrust is true. {defender} is impaled, the shock of death written across their face.",
        "Distance is no defense. {attacker}'s spear flies across the space between them, finding {defender}'s heart.",
        "The spear strike is clean and lethal. {defender} drops instantly, {attacker}'s skill undeniable.",
    ],
    "Axe": [
        "{attacker}'s axe descends with terrible force. {defender}'s end is brutal and quick.",
        "The heavy blade cleaves through {defender}'s guard. There's no recovering from this wound.",
        "Brutal and effective, {attacker}'s axe swing ends the fight—and {defender}'s life—in one blow.",
    ],
    "Bow": [
        "{attacker}'s arrow flies true, finding {defender} before they even see it coming. A sniper's kill.",
        "From the shadows, {attacker} takes careful aim. The arrow strikes, and {defender} falls.",
        "{attacker} proves their marksmanship. {defender} is struck down from a distance, never knowing what hit them.",
    ],
    "Fists": [
        "{attacker} fights with raw brutality, fists becoming weapons. {defender}'s resistance crumbles under the onslaught.",
        "In savage close combat, {attacker} bludgeons {defender} into submission. The kill is primal, desperate.",
        "{attacker}'s hands find {defender}'s throat. It's ugly, personal, and final.",
    ],
    "Trident": [
        "{attacker}'s trident pierces {defender} with three fatal points. The career training shows.",
        "Like a shark in water, {attacker} strikes with the trident. {defender} is caught, helpless.",
        "The trident's points find flesh. {defender}'s struggles weaken, then stop. {attacker} pulls the weapon free, expression grim.",
    ]
}

INJURY_NARRATIVES = [
    "{attacker} lands a vicious blow. {defender} staggers back, blood streaming from a deep wound.",
    "{defender} cries out as {attacker}'s weapon cuts deep. The injury is serious but not fatal—this time.",
    "{attacker} draws first blood. {defender} is hurt, vulnerable, but still fighting.",
    "A glancing blow from {attacker} opens a nasty gash on {defender}. Pain and fear war in their expression.",
]

COMBAT_ESCAPE = [
    "{defender} sees an opening and takes it, fleeing into the forest. {attacker} doesn't pursue, satisfied with the injury dealt.",
    "Bloodied and desperate, {defender} breaks away from the fight and runs. Survival beats pride.",
    "{defender} uses the terrain to their advantage, escaping {attacker}'s reach. They live to fight another day.",
    "Common sense prevails. {defender} retreats from the losing fight, leaving {attacker} victorious but without a kill.",
]

# ========== ARENA EVENT NARRATIVES ==========

WEATHER_EVENTS = {
    "Storm": {
        "start": [
            "⛈️ Thunder rumbles across the arena. A massive storm system moves in, bringing torrential rain and lightning. Tributes scramble for shelter.",
            "⛈️ The sky darkens ominously. Within minutes, the arena is lashed by violent winds and driving rain. This is the Gamemakers' doing.",
            "⛈️ A storm of unprecedented fury descends on the arena. Lightning strikes ignite fires. Thunder shakes the ground. Chaos reigns.",
        ],
        "effects": [
            "{name} is caught in the open when lightning strikes nearby. The blast throws them to the ground, ears ringing.",
            "{name} struggles through the storm, soaked and shivering. Hypothermia becomes a real threat.",
            "{name}'s shelter is destroyed by the wind. They're exposed to the elements, in serious danger.",
        ]
    },
    "Heatwave": {
        "start": [
            "🌡️ The temperature soars to dangerous levels. The sun beats down mercilessly. Water becomes more precious than gold.",
            "🌡️ A brutal heatwave settles over the arena. The very air seems to shimmer with heat. Survival becomes a race against dehydration.",
            "🌡️ The Gamemakers turn up the heat—literally. The arena becomes a furnace. Tributes wilt under the oppressive conditions.",
        ],
        "effects": [
            "{name} collapses from heat exhaustion. They desperately need water and shade.",
            "{name} suffers from the heat, their vision blurring. Dehydration sets in rapidly.",
            "{name}'s water supplies evaporate in the extreme heat. Desperation grows with each passing hour.",
        ]
    },
    "Fog": {
        "start": [
            "🌫️ Thick fog rolls into the arena, reducing visibility to near zero. Tributes become disoriented, vulnerable.",
            "🌫️ An unnatural mist blankets the arena. Within the fog, shapes move. The Gamemakers have unleashed something.",
            "🌫️ Poisonous fog creeps through the arena. Tributes flee before it, but the toxic cloud seems to follow them.",
        ],
        "effects": [
            "{name} breathes in the toxic fog. Their lungs burn, their vision swims. They must escape or die.",
            "{name} loses all sense of direction in the fog. They stumble blindly, hoping to find clear air.",
            "{name} hears screams in the fog but can't tell which direction they're coming from. The fear is overwhelming.",
        ]
    }
}

ANIMAL_ATTACKS = [
    "🐺 Mutant wolves appear from the treeline, eyes glowing with unnatural intelligence. {name} recognizes them as fallen tributes. The Gamemakers' cruelty knows no bounds.",
    "🦅 Tracker jackers—the Capitol's genetically engineered wasps—swarm {name}. The venom causes hallucinations and agony.",
    "🐻 A massive bear, far larger than any natural animal, crashes through the underbrush. {name} runs for their life.",
    "🐍 Venomous snakes drop from the trees above. {name} frantically dodges the strikes, knowing one bite could be fatal.",
]

GAMEMAKER_INTERVENTIONS = [
    "🎬 The Gamemakers decide things are too quiet. Fireballs rain from the sky, driving tributes toward each other.",
    "🎬 The arena shifts and changes. Walls rise from the ground, blocking escape routes. The Gamemakers are forcing confrontation.",
    "🎬 A sponsor gift appears—but it's boobytrapped. {name} narrowly avoids the explosion.",
    "🎬 The Gamemakers release a pack of mutations. The message is clear: give them a show or die trying.",
]

SPONSOR_GIFTS = [
    "🎁 A silver parachute drifts down from the sky. {name} rushes to claim it—medicine, food, or perhaps a weapon. Someone is rooting for them.",
    "🎁 The gleam of a parachute catches {name}'s eye. Inside: precious supplies from a sponsor. Hope renewed.",
    "🎁 A gift from the Capitol descends. {name} opens it with trembling hands, finding exactly what they needed most.",
    "🎁 {name}'s performance has earned favor. The sponsor gift contains life-saving supplies.",
]


def get_combat_kill_narrative(attacker_name: str, defender_name: str, 
                               weapon: str = "weapon",
                               attacker_district: str = "?",
                               defender_district: str = "?") -> str:
    """Generate a complete combat death narrative"""
    
    # Initiation
    intro = random.choice(COMBAT_INITIATION).format(
        attacker=f"{attacker_name} (District {attacker_district})",
        defender=f"{defender_name} (District {defender_district})"
    )
    
    # Combat
    fight = random.choice(COMBAT_CLOSE).format(
        attacker=attacker_name,
        defender=defender_name,
        weapon=weapon
    )
    
    # Death
    weapon_key = weapon if weapon in KILL_NARRATIVES_WEAPON else "Fists"
    kill = random.choice(KILL_NARRATIVES_WEAPON[weapon_key]).format(
        attacker=attacker_name,
        defender=defender_name
    )
    
    # Combine
    full_narrative = f"{intro}\n\n{fight}\n\n{kill}"
    
    return full_narrative


def get_combat_injury_narrative(attacker_name: str, defender_name: str,
                                weapon: str = "weapon",
                                attacker_district: str = "?",
                                defender_district: str = "?") -> str:
    """Generate a combat narrative ending in injury, not death"""
    
    intro = random.choice(COMBAT_INITIATION).format(
        attacker=f"{attacker_name} (District {attacker_district})",
        defender=f"{defender_name} (District {defender_district})"
    )
    
    fight = random.choice(COMBAT_CLOSE).format(
        attacker=attacker_name,
        defender=defender_name,
        weapon=weapon
    )
    
    injury = random.choice(INJURY_NARRATIVES).format(
        attacker=attacker_name,
        defender=defender_name
    )
    
    escape = random.choice(COMBAT_ESCAPE).format(
        attacker=attacker_name,
        defender=defender_name
    )
    
    full_narrative = f"{intro}\n\n{fight}\n\n{injury}\n\n{escape}"
    
    return full_narrative


def get_weather_event_narrative(weather_type: str, affected_tribute_name: str = None) -> str:
    """Generate weather event narrative"""
    
    if weather_type not in WEATHER_EVENTS:
        weather_type = "Storm"
    
    event_data = WEATHER_EVENTS[weather_type]
    start_narrative = random.choice(event_data["start"])
    
    if affected_tribute_name:
        effect = random.choice(event_data["effects"]).format(name=affected_tribute_name)
        return f"{start_narrative}\n\n{effect}"
    
    return start_narrative


def get_animal_attack_narrative(tribute_name: str) -> str:
    """Generate animal/mutation attack narrative"""
    return random.choice(ANIMAL_ATTACKS).format(name=tribute_name)


def get_gamemaker_intervention_narrative() -> str:
    """Generate Gamemaker interference narrative"""
    return random.choice(GAMEMAKER_INTERVENTIONS)


def get_sponsor_gift_narrative(tribute_name: str, gift_type: str = "supplies") -> str:
    """Generate sponsor gift narrative"""
    base = random.choice(SPONSOR_GIFTS).format(name=tribute_name)
    
    if gift_type == "medicine":
        base += " Medical supplies—lifesaving in every sense."
    elif gift_type == "food":
        base += " Food and water—survival for another day."
    elif gift_type == "weapon":
        base += " A weapon—a chance to fight back."
    
    return base
