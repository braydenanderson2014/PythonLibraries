#!/usr/bin/env python3
"""
Test RelationshipManager with Aurora Engine integration
Demonstrates relationship dynamics, trust decay, betrayals, and alliances
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from Engine.relationship_manager import RelationshipManager, ExperienceType
import json

print("=" * 60)
print("AURORA ENGINE - RELATIONSHIP MANAGER TEST")
print("=" * 60)

# Create relationship manager
manager = RelationshipManager()

# Define 6 tributes
tribute_ids = [
    "district1_male",
    "district1_female",
    "district2_male",
    "district2_female",
    "district7_male",
    "district12_female"
]

# Predefined relationships (from web UI)
# District partners start with high trust and alliances
predefined = {
    "district1_male|district1_female": {
        "trust": 85,
        "is_alliance": True,
        "relationship_type": "district_partner"
    },
    "district2_male|district2_female": {
        "trust": 80,
        "is_alliance": True,
        "relationship_type": "district_partner"
    },
    "district1_male|district12_female": {
        "trust": 25,
        "is_alliance": False,
        "relationship_type": "rival"
    }
}

print("\n--- INITIALIZING RELATIONSHIPS ---")
manager.initialize_relationships(tribute_ids, predefined)

print("\nInitial Relationship Summaries:")
for tid in tribute_ids[:4]:  # Show first 4
    summary = manager.get_relationship_summary(tid)
    print(f"\n{tid}:")
    print(f"  Allies: {summary['allies']}")
    print(f"  Enemies: {summary['enemies']}")
    print(f"  Acquaintances: {summary['acquaintances']}")

print("\n" + "=" * 60)
print("PHASE 1: Cornucopia - Initial Interactions")
print("=" * 60)

# District 1 partners share supplies
print("\n[EVENT] district1_male shares supplies with district1_female")
manager.update_relationship(
    "district1_male", "district1_female",
    trust_change=5,
    experience_type=ExperienceType.SHARED_SUPPLIES,
    description="Shared food from cornucopia"
)

rel = manager.get_relationship("district1_male", "district1_female")
print(f"  Trust: {rel.trust:.1f} (was 85)")

# District 2 female witnesses district 1 male kill
print("\n[EVENT] district2_female witnesses district1_male kill another tribute")
manager.update_relationship(
    "district2_female", "district1_male",
    trust_change=-15,
    experience_type=ExperienceType.WITNESSED_KILL,
    description="Witnessed brutal kill at cornucopia"
)

rel = manager.get_relationship("district2_female", "district1_male")
print(f"  Trust: {rel.trust:.1f} (brutal kill reduces trust)")

# District 7 male forms alliance with district 12 female
print("\n[EVENT] district7_male and district12_female form alliance")
manager.form_alliance("district7_male", "district12_female")

rel = manager.get_relationship("district7_male", "district12_female")
print(f"  Trust: {rel.trust:.1f} (alliance formed, +15 trust bonus)")
print(f"  Is Alliance: {rel.is_alliance}")

print("\n" + "=" * 60)
print("PHASE 5: Mid-game - Desperation and Betrayal")
print("=" * 60)

# District 2 male becomes desperate and betrays district 2 female
print("\n[SCENARIO] district2_male is at 25 health, 85 hunger - DESPERATE")
print("          Considering betraying ally district2_female...")

desperation = 75  # High desperation
betrayal_risk = manager.calculate_betrayal_risk(
    "district2_male", "district2_female",
    tribute_desperation=desperation
)

print(f"  Desperation: {desperation}/100")
print(f"  Current Trust: {manager.get_relationship('district2_male', 'district2_female').trust:.1f}")
print(f"  Betrayal Risk: {betrayal_risk:.1%}")

if betrayal_risk > 0.5:
    print("  -> BETRAYAL OCCURS!")
    manager.break_alliance("district2_male", "district2_female", is_betrayal=True)
    
    rel = manager.get_relationship("district2_male", "district2_female")
    print(f"  New Trust: {rel.trust:.1f} (massive loss)")
    print(f"  Is Alliance: {rel.is_alliance}")
    
    # Check gossip spread
    gossip = manager.get_reputation("district1_male", "district2_male")
    print(f"  Gossip Effect: Others hear about betrayal (reputation: {gossip:.1f})")

print("\n" + "=" * 60)
print("PHASE 8: Trust Decay Over Time")
print("=" * 60)

print("\n[SIMULATION] 5 phases pass with no interactions...")
print("Trust naturally decays toward neutral (50)")

# Show district 7 and district 12's relationship before decay
rel_before = manager.get_relationship("district7_male", "district12_female")
print(f"\nBefore decay: district7_male <-> district12_female")
print(f"  Trust: {rel_before.trust:.1f}")
print(f"  Is Alliance: {rel_before.is_alliance}")

# Process decay
for phase in range(5):
    manager.process_trust_decay()
    rel = manager.get_relationship("district7_male", "district12_female")
    print(f"  Phase {phase + 1}: Trust = {rel.trust:.1f}")

print(f"\nAlliance trust decays slower (toward 70 instead of 50)")

print("\n" + "=" * 60)
print("PHASE 10: Ally Protection")
print("=" * 60)

# District 1 male saves district 1 female
print("\n[EVENT] district1_male saves district1_female from danger")
manager.update_relationship(
    "district1_male", "district1_female",
    trust_change=25,
    experience_type=ExperienceType.SAVED_LIFE,
    description="Pulled from toxic gas zone"
)

rel = manager.get_relationship("district1_male", "district1_female")
print(f"  Trust: {rel.trust:.1f} (major increase from life-saving)")
print(f"  Relationship Type: {rel.get_relationship_type().value}")
print(f"  Shared Experiences: {len(rel.shared_experiences)}")

print("\n" + "=" * 60)
print("PHASE 10: ENEMY SYSTEM - DYNAMIC ENEMY CREATION")
print("=" * 60)

print("\nScenario: District 7 male witnesses District 1 male kill an ally")
print("This triggers dynamic enemy creation with high priority")

# Create enemy relationship from event
manager.create_enemy_from_event(
    "district7_male",
    "district1_male",
    "killed_ally",
    tribute1_skills={"combat": 8, "stealth": 6},
    tribute2_skills={"combat": 9, "strength": 8}
)

enemy_rel = manager.get_relationship("district7_male", "district1_male")
print(f"\nResult:")
print(f"  Enemy status: {enemy_rel.is_enemy}")
print(f"  Threat priority: {enemy_rel.enemy_priority}/100")
print(f"  Enemy reason: {enemy_rel.enemy_reason}")
print(f"  Trust after: {enemy_rel.trust:.1f}")

# Get all enemies for district7_male
enemies = manager.get_enemies("district7_male")
print(f"\nDistrict 7 male's enemies:")
for enemy_id, priority in enemies:
    print(f"  - {enemy_id}: Priority {priority:.0f}/100")

print("\n" + "=" * 60)
print("PHASE 11: ENEMY SYSTEM - PRE-DEFINED ENEMIES")
print("=" * 60)

print("\nScenario: Setting up pre-game enemies via web UI")

# Create new test with predefined enemy
predefined_with_enemies = {
    "district2_male|district7_male": {
        "trust": 15,
        "is_enemy": True,
        "enemy_priority": 75,
        "enemy_reason": "Historical district rivalry",
        "is_alliance": False,
        "relationship_type": "rival"
    }
}

# Initialize new manager to test predefined enemies
test_manager = RelationshipManager()
test_manager.initialize_relationships(
    ["district2_male", "district7_male"],
    predefined_with_enemies
)

enemy_rel = test_manager.get_relationship("district2_male", "district7_male")
print(f"\nResult from web UI:")
print(f"  Enemy status: {enemy_rel.is_enemy}")
print(f"  Threat priority: {enemy_rel.enemy_priority}/100")
print(f"  Enemy reason: {enemy_rel.enemy_reason}")
print(f"  Trust: {enemy_rel.trust:.1f}")

print("\n" + "=" * 60)
print("PHASE 12: ENEMY SYSTEM - MULTIPLE EVENT TYPES")
print("=" * 60)

print("\nTesting various event types that create enemies:")

event_types = [
    ("district1_male", "district2_male", "betrayal", "Betrayed alliance"),
    ("district1_female", "district7_male", "stole_supplies", "Stole critical supplies"),
    ("district2_female", "district12_female", "combat_attack", "Attacked in arena"),
    ("district2_male", "district1_female", "witnessed_kill", "Witnessed brutal kill"),
]

for t1, t2, event_type, desc in event_types:
    manager.create_enemy_from_event(t1, t2, event_type)
    rel = manager.get_relationship(t1, t2)
    print(f"\n{desc}:")
    print(f"  {t1} vs {t2}")
    print(f"  Priority: {rel.enemy_priority:.0f}/100")
    print(f"  Trust: {rel.trust:.1f}")
    print(f"  Reason: {rel.enemy_reason}")

print("\n" + "=" * 60)
print("PHASE 13: ENEMY SYSTEM - SKILL RIVALRY")
print("=" * 60)

print("\nScenario: Two tributes with overlapping strong skills become rivals")

# Tributes with similar skill profiles
tribute1_skills = {"combat": 9, "stealth": 8, "survival": 7}
tribute2_skills = {"combat": 8, "stealth": 9, "agility": 7}

manager.create_enemy_from_event(
    "district1_male",
    "district2_female",
    "skill_rivalry",
    tribute1_skills=tribute1_skills,
    tribute2_skills=tribute2_skills
)

rel = manager.get_relationship("district1_male", "district2_female")
print(f"\nSkill profiles:")
print(f"  District 1 Male: {tribute1_skills}")
print(f"  District 2 Female: {tribute2_skills}")
print(f"\nResult:")
print(f"  Enemy status: {rel.is_enemy}")
print(f"  Priority (based on skill overlap): {rel.enemy_priority:.0f}/100")
print(f"  Reason: {rel.enemy_reason}")
print(f"  Trust penalty: {rel.trust:.1f}")

print("\n" + "=" * 60)
print("PHASE 14: ENEMY SYSTEM - PRIORITY UPDATES")
print("=" * 60)

print("\nScenario: Enemy becomes more dangerous, update priority")

# Get initial priority
rel = manager.get_relationship("district7_male", "district1_male")
initial_priority = rel.enemy_priority

print(f"Initial threat priority: {initial_priority:.0f}/100")

# Update priority after enemy gets stronger weapon
manager.update_enemy_priority(
    "district7_male",
    "district1_male",
    95,
    "Obtained deadly weapon - now extreme threat"
)

rel = manager.get_relationship("district7_male", "district1_male")
print(f"Updated threat priority: {rel.enemy_priority:.0f}/100")
print(f"Update reason: {rel.shared_experiences[-1]['description']}")

print("\n" + "=" * 60)
print("PHASE 15: ENEMY SYSTEM - HIGH PRIORITY FILTERING")
print("=" * 60)

print("\nScenario: Get only high-priority enemies (70+)")

# District 7 male's high-priority enemies
high_priority = manager.get_enemies("district7_male", min_priority=70.0)

print(f"\nDistrict 7 male's high-priority enemies (70+):")
if high_priority:
    for enemy_id, priority in high_priority:
        rel = manager.get_relationship("district7_male", enemy_id)
        print(f"  - {enemy_id}: Priority {priority:.0f}/100")
        print(f"    Reason: {rel.enemy_reason}")
        print(f"    Trust: {rel.trust:.1f}")
else:
    print("  No high-priority enemies")

# All enemies regardless of priority
all_enemies = manager.get_enemies("district7_male", min_priority=0.0)
print(f"\nTotal enemies: {len(all_enemies)}")

print("\n" + "=" * 60)
print("PHASE 16: ENEMY SYSTEM - RECONCILIATION")
print("=" * 60)

print("\nScenario: Two enemies reconcile and become neutral")

# Get an enemy relationship
rel = manager.get_relationship("district1_male", "district2_male")
if rel and rel.is_enemy:
    print(f"Before reconciliation:")
    print(f"  Enemy status: {rel.is_enemy}")
    print(f"  Trust: {rel.trust:.1f}")
    
    # Reconcile
    manager.remove_enemy_status(
        "district1_male",
        "district2_male",
        "Formed temporary truce to fight common enemy"
    )
    
    rel = manager.get_relationship("district1_male", "district2_male")
    print(f"\nAfter reconciliation:")
    print(f"  Enemy status: {rel.is_enemy}")
    print(f"  Trust: {rel.trust:.1f} (+10 reconciliation bonus)")
    print(f"  Relationship type: {rel.get_relationship_type().value}")

print("\n" + "=" * 60)
print("PHASE 17: RELATIONSHIP SUMMARY WITH ENEMIES")
print("=" * 60)

print("\nComprehensive relationship summary for each tribute:")

for tribute_id in tribute_ids:
    summary = manager.get_relationship_summary(tribute_id)
    print(f"\n{tribute_id}:")
    print(f"  Allies: {summary['allies']}")
    print(f"  Enemies: {len(summary['enemies'])} total")
    
    if summary['enemies']:
        print(f"    Details:")
        for enemy in summary['enemies']:
            if isinstance(enemy, dict):
                print(f"      - {enemy['id']}: Priority {enemy['priority']:.0f} ({enemy['reason']})")
            else:
                print(f"      - {enemy}")
    
    if summary['high_priority_enemies']:
        print(f"  High-priority enemies (70+): {len(summary['high_priority_enemies'])}")
        for enemy in summary['high_priority_enemies']:
            print(f"      - {enemy['id']}: Priority {enemy['priority']:.0f}")
    
    print(f"  Acquaintances: {len(summary['acquaintances'])}")
    print(f"  Neutrals: {len(summary['neutrals'])}")

print("\n" + "=" * 60)
print("FINAL RELATIONSHIP DATA")
print("=" * 60)

all_relationships = manager.get_all_relationships_data()
print(f"\nTotal Relationships Tracked: {len(all_relationships)}")
print("\nKey Relationships (with enemy data):")
for rel_data in all_relationships[:10]:  # Show first 10
    if rel_data['trust'] > 60 or rel_data['trust'] < 40 or rel_data['is_alliance'] or rel_data['is_enemy']:
        print(f"\n{rel_data['tribute1_id']} <-> {rel_data['tribute2_id']}")
        print(f"  Trust: {rel_data['trust']:.1f}")
        print(f"  Type: {rel_data['relationship_type']}")
        print(f"  Alliance: {rel_data['is_alliance']}")
        print(f"  Enemy: {rel_data['is_enemy']}")
        if rel_data['is_enemy']:
            print(f"    Priority: {rel_data['enemy_priority']:.0f}/100")
            print(f"    Reason: {rel_data['enemy_reason']}")
        print(f"  Betrayals: {rel_data['betrayal_count']}")
        print(f"  Experiences: {rel_data['shared_experiences_count']}")

print("\n" + "=" * 60)
print("INTEGRATION WITH NEMESIS BEHAVIOR ENGINE")
print("=" * 60)

print("""
The RelationshipManager is now integrated into:

1. **Aurora Engine** (Engine/Aurora Engine.py):
   - Initialized on game start with predefined relationships
   - Trust decay processed every phase
   - Relationship data included in game state messages

2. **Nemesis Behavior Engine** (Nemesis Behavior Engine/NemesisBehaviorEngine.py):
   - Uses relationship data for decision-making
   - Considers trust when forming alliances
   - Calculates betrayal risk based on desperation + trust
   - Prioritizes protecting high-trust allies
   - Avoids low-trust enemies
   
3. **New Action Types Available**:
   - FORM_ALLIANCE: Based on trust >= 40 and mutual benefit
   - BETRAY_ALLIANCE: When betrayal_risk > 0.4 and desperate
   - SHARE_SUPPLIES: With allies when trust > 60
   - PROTECT_ALLY: When ally in danger and trust > 60
   - AVOID: When encountering enemies (trust < 30)

4. **Decision Factors**:
   - Trust level (0-100)
   - Desperation (health, resources, injuries)
   - District bonuses (partners have +0.3 alliance score)
   - Betrayal history (each betrayal increases future risk)
   - Gossip network (reputation affects third-party perceptions)
""")

print("\n" + "=" * 60)
print("SAVE/LOAD FUNCTIONALITY")
print("=" * 60)

# Demonstrate save/load
state = manager.save_state()
print(f"\nSaved state includes:")
print(f"  - {len(state['relationships'])} relationships")
print(f"  - {len(state['active_alliances'])} tributes with active alliances")
print(f"  - {len(state['gossip_network'])} gossip network entries")
print(f"  - Current phase: {state['current_phase']}")

print("\nRelationship state can be saved/loaded with game state")
print("Allows resume functionality with preserved social dynamics")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
