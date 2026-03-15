#!/usr/bin/env python3
"""
Limb Damage and Dismemberment System for Aurora Engine
Manages body part targeting, limb wounds, dismemberment, and disabilities
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class BodyPart(Enum):
    """Body parts that can be targeted"""
    HEAD = "head"
    TORSO = "torso"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"


class LimbStatus(Enum):
    """Status of a limb"""
    HEALTHY = "healthy"
    WOUNDED = "wounded"          # Cut, bruised, bleeding
    BROKEN = "broken"             # Broken bone
    SEVERED = "severed"           # Cut off completely
    INFECTED = "infected"         # Infected wound
    MANGLED = "mangled"           # Severely damaged but attached


class BleedingSeverity(Enum):
    """Bleeding severity classifications"""
    NONE = "none"                 # No bleeding
    MILD = "mild"                 # 1-3 HP/phase, 15% infection risk, treatable
    MODERATE = "moderate"         # 4-7 HP/phase, 30% infection risk, treatable
    SEVERE = "severe"             # 8-14 HP/phase, 50% infection risk, treatable with difficulty
    FATAL = "fatal"               # 15-25 HP/phase, 70% infection risk, death in 1-3 phases, often untreatable


@dataclass
class LimbWound:
    """Represents a wound on a specific body part"""
    body_part: BodyPart
    wound_type: str  # "cut", "slash", "stab", "bruise", "broken", "severed"
    severity: int  # 1-5 (1=minor, 5=critical/severed)
    bleeding_rate: int  # HP lost per phase (0-25)
    bleeding_severity: BleedingSeverity  # Classification of bleeding
    infection_risk: float  # 0.0-1.0 chance of infection per phase
    pain_level: int  # 1-10 affects skill penalties
    phases_since_injury: int = 0
    is_infected: bool = False
    is_treated: bool = False
    is_fatal_bleeding: bool = False  # True if fatal bleeding that cannot be treated
    
    def get_bleeding_severity_name(self) -> str:
        """Get human-readable bleeding severity"""
        return self.bleeding_severity.value.title()
    
    def can_be_treated(self) -> bool:
        """Check if wound can be treated"""
        if self.is_fatal_bleeding and self.bleeding_severity == BleedingSeverity.FATAL:
            # Fatal bleeding from catastrophic wounds (severed major arteries)
            return False
        return True
    
    def get_skill_penalties(self) -> Dict[str, float]:
        """Get skill penalties from this wound"""
        penalties = {}
        
        # Severity multiplier
        severity_mult = self.severity / 5.0
        
        # Pain adds to penalties
        pain_mult = self.pain_level / 10.0
        
        if self.body_part == BodyPart.HEAD:
            penalties['intelligence'] = -(0.2 + severity_mult * 0.3)
            penalties['perception'] = -(0.3 + severity_mult * 0.4)
            penalties['combat'] = -(0.2 + severity_mult * 0.3)
            
        elif self.body_part == BodyPart.TORSO:
            penalties['strength'] = -(0.15 + severity_mult * 0.25)
            penalties['endurance'] = -(0.2 + severity_mult * 0.3)
            penalties['agility'] = -(0.15 + severity_mult * 0.25)
            
        elif self.body_part in [BodyPart.LEFT_ARM, BodyPart.RIGHT_ARM]:
            penalties['strength'] = -(0.2 + severity_mult * 0.4)
            penalties['combat'] = -(0.25 + severity_mult * 0.45)
            if self.wound_type == "severed":
                penalties['strength'] = -0.5  # Per arm
                penalties['combat'] = -0.6
                
        elif self.body_part in [BodyPart.LEFT_LEG, BodyPart.RIGHT_LEG]:
            penalties['agility'] = -(0.3 + severity_mult * 0.5)
            penalties['stealth'] = -(0.2 + severity_mult * 0.3)
            penalties['combat'] = -(0.15 + severity_mult * 0.25)
            if self.wound_type == "severed":
                penalties['agility'] = -0.7  # Per leg
                penalties['stealth'] = -0.5
                penalties['combat'] = -0.4
        
        # Infection makes everything worse
        if self.is_infected:
            for skill in penalties:
                penalties[skill] *= 1.5
        
        return penalties


@dataclass
class LimbDamageState:
    """Tracks the damage state of all body parts"""
    head_status: LimbStatus = LimbStatus.HEALTHY
    torso_status: LimbStatus = LimbStatus.HEALTHY
    left_arm_status: LimbStatus = LimbStatus.HEALTHY
    right_arm_status: LimbStatus = LimbStatus.HEALTHY
    left_leg_status: LimbStatus = LimbStatus.HEALTHY
    right_leg_status: LimbStatus = LimbStatus.HEALTHY
    
    wounds: List[LimbWound] = field(default_factory=list)
    
    def get_limb_status(self, body_part: BodyPart) -> LimbStatus:
        """Get status of specific body part"""
        if body_part == BodyPart.HEAD:
            return self.head_status
        elif body_part == BodyPart.TORSO:
            return self.torso_status
        elif body_part == BodyPart.LEFT_ARM:
            return self.left_arm_status
        elif body_part == BodyPart.RIGHT_ARM:
            return self.right_arm_status
        elif body_part == BodyPart.LEFT_LEG:
            return self.left_leg_status
        elif body_part == BodyPart.RIGHT_LEG:
            return self.right_leg_status
    
    def set_limb_status(self, body_part: BodyPart, status: LimbStatus):
        """Set status of specific body part"""
        if body_part == BodyPart.HEAD:
            self.head_status = status
        elif body_part == BodyPart.TORSO:
            self.torso_status = status
        elif body_part == BodyPart.LEFT_ARM:
            self.left_arm_status = status
        elif body_part == BodyPart.RIGHT_ARM:
            self.right_arm_status = status
        elif body_part == BodyPart.LEFT_LEG:
            self.left_leg_status = status
        elif body_part == BodyPart.RIGHT_LEG:
            self.right_leg_status = status
    
    def add_wound(self, wound: LimbWound):
        """Add a wound to the body"""
        self.wounds.append(wound)
        
        # Update limb status
        if wound.wound_type == "severed":
            self.set_limb_status(wound.body_part, LimbStatus.SEVERED)
        elif wound.severity >= 4:
            self.set_limb_status(wound.body_part, LimbStatus.MANGLED)
        elif wound.wound_type == "broken":
            self.set_limb_status(wound.body_part, LimbStatus.BROKEN)
        else:
            self.set_limb_status(wound.body_part, LimbStatus.WOUNDED)
    
    def get_wounds_on_part(self, body_part: BodyPart) -> List[LimbWound]:
        """Get all wounds on a specific body part"""
        return [w for w in self.wounds if w.body_part == body_part]
    
    def is_limb_severed(self, body_part: BodyPart) -> bool:
        """Check if limb is severed"""
        return self.get_limb_status(body_part) == LimbStatus.SEVERED
    
    def can_hold_weapon(self) -> Tuple[bool, str]:
        """Check if tribute can hold a weapon"""
        left_severed = self.is_limb_severed(BodyPart.LEFT_ARM)
        right_severed = self.is_limb_severed(BodyPart.RIGHT_ARM)
        
        if left_severed and right_severed:
            return False, "both arms severed"
        
        # Check if remaining arm(s) are too damaged
        if not left_severed:
            left_wounds = self.get_wounds_on_part(BodyPart.LEFT_ARM)
            left_severity = sum(w.severity for w in left_wounds)
        else:
            left_severity = 999  # Severed
        
        if not right_severed:
            right_wounds = self.get_wounds_on_part(BodyPart.RIGHT_ARM)
            right_severity = sum(w.severity for w in right_wounds)
        else:
            right_severity = 999  # Severed
        
        # Need at least one arm with severity < 8
        if left_severity >= 8 and right_severity >= 8:
            return False, "arms too damaged"
        
        return True, ""
    
    def can_walk(self) -> Tuple[bool, str]:
        """Check if tribute can walk"""
        left_severed = self.is_limb_severed(BodyPart.LEFT_LEG)
        right_severed = self.is_limb_severed(BodyPart.RIGHT_LEG)
        
        if left_severed and right_severed:
            return False, "both legs severed"
        
        if left_severed or right_severed:
            return True, "hobbling on one leg"
        
        # Check if legs are too damaged
        left_wounds = self.get_wounds_on_part(BodyPart.LEFT_LEG)
        right_wounds = self.get_wounds_on_part(BodyPart.RIGHT_LEG)
        
        left_severity = sum(w.severity for w in left_wounds)
        right_severity = sum(w.severity for w in right_wounds)
        
        if left_severity >= 8 or right_severity >= 8:
            return True, "limping badly"
        
        return True, ""
    
    def get_total_bleeding_rate(self) -> int:
        """Get total HP loss per phase from all bleeding wounds"""
        return sum(w.bleeding_rate for w in self.wounds if not w.is_treated)
    
    def get_all_skill_penalties(self) -> Dict[str, float]:
        """Get combined skill penalties from all wounds"""
        penalties = {}
        
        for wound in self.wounds:
            wound_penalties = wound.get_skill_penalties()
            for skill, penalty in wound_penalties.items():
                penalties[skill] = penalties.get(skill, 0.0) + penalty
        
        # Cap penalties at -95%
        for skill in penalties:
            penalties[skill] = max(-0.95, penalties[skill])
        
        return penalties
    
    def get_infection_count(self) -> int:
        """Count infected wounds"""
        return sum(1 for w in self.wounds if w.is_infected)
    
    def get_severed_limbs(self) -> List[BodyPart]:
        """Get list of severed limbs"""
        severed = []
        for part in BodyPart:
            if self.is_limb_severed(part):
                severed.append(part)
        return severed
    
    def count_disabled_limbs(self) -> int:
        """Count limbs that are severed, mangled, or severely damaged"""
        count = 0
        for part in BodyPart:
            status = self.get_limb_status(part)
            if status in [LimbStatus.SEVERED, LimbStatus.MANGLED]:
                count += 1
            elif status == LimbStatus.BROKEN:
                # Broken limbs count as half-disabled
                count += 0.5
        return int(count)
    
    def get_untreated_wounds(self) -> List[Dict[str, Any]]:
        """Get list of untreated wounds as dictionaries"""
        untreated = []
        for wound in self.wounds:
            if not wound.is_treated:
                untreated.append({
                    'body_part': wound.body_part.value,
                    'severity': self._severity_to_string(wound.severity),
                    'weapon_used': wound.weapon_used,
                    'bleeding': wound.bleeding_rate > 0,
                    'infected': wound.is_infected
                })
        return untreated
    
    def _severity_to_string(self, severity: int) -> str:
        """Convert severity number to string"""
        if severity <= 1:
            return 'minor'
        elif severity <= 2:
            return 'moderate'
        elif severity <= 3:
            return 'severe'
        else:
            return 'critical'
    
    def describe_injuries(self) -> str:
        """Generate description of injuries"""
        descriptions = []
        
        severed = self.get_severed_limbs()
        if severed:
            limb_names = [p.value.replace('_', ' ') for p in severed]
            descriptions.append(f"Missing: {', '.join(limb_names)}")
        
        bleeding_wounds = [w for w in self.wounds if w.bleeding_rate > 0 and not w.is_treated]
        if bleeding_wounds:
            total_bleeding = sum(w.bleeding_rate for w in bleeding_wounds)
            descriptions.append(f"Bleeding: {total_bleeding} HP/phase")
        
        infected = self.get_infection_count()
        if infected > 0:
            descriptions.append(f"{infected} infected wound(s)")
        
        if not descriptions:
            return "No serious injuries"
        
        return " | ".join(descriptions)


class LimbDamageSystem:
    """Manages limb damage, dismemberment, and wound mechanics"""
    
    def __init__(self):
        # Body part hit chances (weighted by size and vulnerability)
        self.hit_chances = {
            BodyPart.HEAD: 0.15,      # 15% - small but vulnerable
            BodyPart.TORSO: 0.40,     # 40% - largest target
            BodyPart.LEFT_ARM: 0.10,  # 10%
            BodyPart.RIGHT_ARM: 0.10, # 10%
            BodyPart.LEFT_LEG: 0.125, # 12.5%
            BodyPart.RIGHT_LEG: 0.125 # 12.5%
        }
    
    def select_hit_location(self, targeted: Optional[BodyPart] = None) -> BodyPart:
        """
        Select which body part is hit
        
        Args:
            targeted: Specific body part being aimed at (or None for random)
            
        Returns:
            Body part that was hit
        """
        if targeted:
            # 70% chance to hit targeted part, 30% miss and hit adjacent
            if random.random() < 0.7:
                return targeted
        
        # Random hit based on body part size
        roll = random.random()
        cumulative = 0.0
        
        for part, chance in self.hit_chances.items():
            cumulative += chance
            if roll <= cumulative:
                return part
        
        return BodyPart.TORSO  # Default
    
    def determine_wound_type(self, weapon_type: str, damage: int, 
                            body_part: BodyPart) -> Tuple[str, int]:
        """
        Determine wound type and severity based on weapon and damage
        
        Args:
            weapon_type: Type of weapon ("sword", "axe", "bow", etc.)
            damage: Damage dealt
            body_part: Part that was hit
            
        Returns:
            (wound_type, severity)
        """
        # Dismemberment weapons (high chance with heavy weapons)
        dismemberment_weapons = ["axe", "sword", "machete", "trident"]
        crushing_weapons = ["mace", "club", "rock"]
        piercing_weapons = ["spear", "knife", "arrow", "bolt"]
        
        # Base severity from damage
        if damage < 3:
            base_severity = 1  # Minor
        elif damage < 6:
            base_severity = 2  # Moderate
        elif damage < 10:
            base_severity = 3  # Severe
        elif damage < 15:
            base_severity = 4  # Critical
        else:
            base_severity = 5  # Potentially fatal/severing
        
        # Limbs can be severed at high damage
        if body_part in [BodyPart.LEFT_ARM, BodyPart.RIGHT_ARM, 
                         BodyPart.LEFT_LEG, BodyPart.RIGHT_LEG]:
            
            if weapon_type in dismemberment_weapons:
                if damage >= 15:
                    # Very high damage = guaranteed sever
                    return "severed", 5
                elif damage >= 12:
                    # High damage with cutting weapon = potential dismemberment
                    sever_chance = 0.4 + (damage - 12) * 0.15  # 40-85% based on damage
                    if random.random() < sever_chance:
                        return "severed", 5
        
        # Head wounds are especially dangerous
        if body_part == BodyPart.HEAD:
            if damage >= 10:
                return "skull_fracture", 5
            elif damage >= 6:
                return "concussion", 4
            else:
                return "cut", base_severity
        
        # Determine wound type by weapon
        if weapon_type in crushing_weapons:
            if base_severity >= 3:
                return "broken", base_severity
            else:
                return "bruise", base_severity
        
        elif weapon_type in piercing_weapons:
            return "stab", base_severity
        
        elif weapon_type in dismemberment_weapons:
            return "slash", base_severity
        
        else:
            return "cut", base_severity
    
    def create_wound(self, body_part: BodyPart, wound_type: str, 
                     severity: int, weapon_type: str) -> LimbWound:
        """
        Create a wound with bleeding severity classification
        
        Args:
            body_part: Part that was wounded
            wound_type: Type of wound
            severity: 1-5 severity
            weapon_type: Weapon that caused wound
            
        Returns:
            LimbWound object
        """
        # Calculate bleeding rate based on wound type and severity
        if wound_type == "severed":
            # Severed limbs are ALWAYS severe or fatal bleeding
            bleeding_rate = 15 + random.randint(0, 10)  # 15-25 HP/phase (FATAL)
            bleeding_severity = BleedingSeverity.FATAL
            # 50% chance of being untreatable (death in 1 phase)
            # Otherwise treatable but still fatal severity (death in 3 phases if not treated)
            is_fatal = random.random() < 0.5  # 50% untreatable
            infection_risk = 0.70
        elif wound_type in ["slash", "cut", "stab"]:
            base_bleeding = severity * 2
            variance = random.randint(-1, 2)
            bleeding_rate = max(1, base_bleeding + variance)
            
            # Classify bleeding severity
            if bleeding_rate <= 3:
                bleeding_severity = BleedingSeverity.MILD
                infection_risk = 0.15
                is_fatal = False
            elif bleeding_rate <= 7:
                bleeding_severity = BleedingSeverity.MODERATE
                infection_risk = 0.30
                is_fatal = False
            elif bleeding_rate <= 14:
                bleeding_severity = BleedingSeverity.SEVERE
                infection_risk = 0.50
                is_fatal = False
            else:  # 15+
                bleeding_severity = BleedingSeverity.FATAL
                infection_risk = 0.70
                is_fatal = random.random() < 0.3  # 30% chance of truly fatal (untreatable)
        elif wound_type == "broken":
            bleeding_rate = severity  # 1-5 HP/phase (internal bleeding)
            if bleeding_rate <= 3:
                bleeding_severity = BleedingSeverity.MILD
                infection_risk = 0.10
            else:
                bleeding_severity = BleedingSeverity.MODERATE
                infection_risk = 0.25
            is_fatal = False
        else:  # bruise
            bleeding_rate = 0
            bleeding_severity = BleedingSeverity.NONE
            infection_risk = 0.05
            is_fatal = False
        
        # Calculate pain level
        pain_level = severity * 2
        if body_part == BodyPart.HEAD:
            pain_level += 2  # Head wounds hurt more
        if wound_type == "severed":
            pain_level = 10  # Maximum pain
        
        return LimbWound(
            body_part=body_part,
            wound_type=wound_type,
            severity=severity,
            bleeding_rate=bleeding_rate,
            bleeding_severity=bleeding_severity,
            infection_risk=infection_risk,
            pain_level=min(10, pain_level),
            is_fatal_bleeding=is_fatal
        )
    
    def process_wound_effects(self, limb_state: LimbDamageState, 
                             phases_elapsed: int = 1) -> Dict[str, any]:
        """
        Process ongoing wound effects (bleeding, infection, healing)
        
        Args:
            limb_state: Tribute's limb damage state
            phases_elapsed: Number of phases elapsed
            
        Returns:
            Dictionary with effects applied
        """
        result = {
            'health_loss': 0,
            'new_infections': [],
            'healed_wounds': [],
            'death_from_bleeding': False,
            'death_from_infection': False,
            'fatal_bleeding_wounds': []  # Track untreatable fatal bleeding
        }
        
        wounds_to_remove = []
        
        for wound in limb_state.wounds:
            wound.phases_since_injury += phases_elapsed
            
            # Bleeding damage
            if wound.bleeding_rate > 0 and not wound.is_treated:
                result['health_loss'] += wound.bleeding_rate * phases_elapsed
                
                # Fatal bleeding - death within 1-3 phases depending on severity
                if wound.bleeding_severity == BleedingSeverity.FATAL:
                    if wound.is_fatal_bleeding:
                        # Truly fatal, untreatable bleeding
                        result['fatal_bleeding_wounds'].append(wound.body_part.value)
                        if wound.phases_since_injury >= 1:
                            result['death_from_bleeding'] = True
                    else:
                        # Severe but potentially treatable
                        if wound.phases_since_injury >= 3:
                            result['death_from_bleeding'] = True
                elif wound.bleeding_severity == BleedingSeverity.SEVERE:
                    # Severe bleeding - death in 5-8 phases if untreated
                    if wound.phases_since_injury >= 8:
                        result['death_from_bleeding'] = True
            
            # Infection risk
            if not wound.is_infected and not wound.is_treated:
                for _ in range(phases_elapsed):
                    if random.random() < wound.infection_risk:
                        wound.is_infected = True
                        result['new_infections'].append(wound.body_part.value)
                        # Update limb status
                        limb_state.set_limb_status(wound.body_part, LimbStatus.INFECTED)
                        break
            
            # Death from infection (untreated infected wounds)
            if wound.is_infected and not wound.is_treated:
                if wound.phases_since_injury >= 8:
                    result['death_from_infection'] = True
            
            # Natural healing for minor wounds
            if wound.severity <= 2 and not wound.is_infected:
                healing_threshold = 5 if wound.is_treated else 10
                if wound.phases_since_injury >= healing_threshold:
                    wounds_to_remove.append(wound)
                    result['healed_wounds'].append(wound.body_part.value)
        
        # Remove healed wounds
        for wound in wounds_to_remove:
            limb_state.wounds.remove(wound)
            
            # Update limb status if no more wounds on that part
            if not limb_state.get_wounds_on_part(wound.body_part):
                limb_state.set_limb_status(wound.body_part, LimbStatus.HEALTHY)
        
        return result
    
    def _get_medical_supply_effectiveness(self, supply: str, bleeding_severity: BleedingSeverity) -> float:
        """
        Get effectiveness bonus for medical supplies based on bleeding severity
        
        Medical Supply Effectiveness Guide:
        - Medical Kit: Best for all severities (sponsor gift quality)
        - Tourniquet: Essential for severe/fatal bleeding (stops arterial bleeding)
        - Bandage: Good for mild/moderate, can help severe
        - Cloth Strips: Improvised, works for mild/moderate
        - Herbs: Natural remedy, mild antiseptic and clotting
        - Moss: Wild item, basic clotting for mild wounds
        - Medicine/Antiseptic: Primarily for infection, minor bleeding help
        
        Args:
            supply: Type of medical supply
            bleeding_severity: Severity of bleeding
            
        Returns:
            Success chance bonus (0.0 to 0.35)
        """
        supply_lower = supply.lower().replace(" ", "_")
        
        # Medical Kit - comprehensive (sponsor gift quality)
        if supply_lower in ["medical_kit", "first_aid_kit", "medkit"]:
            return 0.30  # Excellent for all severities
        
        # Tourniquet - critical for severe bleeding (includes improvised)
        elif supply_lower in ["tourniquet", "belt", "rope", "string", "stick", "sticks", "vine", "wire"]:
            # Improvised tourniquets (string+stick) slightly less effective than proper ones
            is_improvised = supply_lower in ["string", "stick", "sticks", "vine", "wire"]
            effectiveness_modifier = 0.9 if is_improvised else 1.0
            
            if bleeding_severity == BleedingSeverity.FATAL:
                return 0.35 * effectiveness_modifier  # Most effective for fatal bleeding
            elif bleeding_severity == BleedingSeverity.SEVERE:
                return 0.30 * effectiveness_modifier  # Very effective for severe
            elif bleeding_severity == BleedingSeverity.MODERATE:
                return 0.15 * effectiveness_modifier  # Can help moderate
            else:
                return 0.05 * effectiveness_modifier  # Overkill for mild
        
        # Bandages - standard medical supply
        elif supply_lower in ["bandage", "bandages", "gauze"]:
            if bleeding_severity == BleedingSeverity.MILD:
                return 0.20  # Very effective for mild
            elif bleeding_severity == BleedingSeverity.MODERATE:
                return 0.18  # Good for moderate
            elif bleeding_severity == BleedingSeverity.SEVERE:
                return 0.12  # Can help severe
            else:
                return 0.05  # Limited use for fatal
        
        # Cloth strips - improvised bandages
        elif supply_lower in ["cloth", "cloth_strips", "torn_clothing", "shirt"]:
            if bleeding_severity == BleedingSeverity.MILD:
                return 0.15  # Works for mild
            elif bleeding_severity == BleedingSeverity.MODERATE:
                return 0.12  # Adequate for moderate
            elif bleeding_severity == BleedingSeverity.SEVERE:
                return 0.08  # Minimal help for severe
            else:
                return 0.03  # Almost useless for fatal
        
        # Herbs - natural clotting agents (wild find)
        elif supply_lower in ["herbs", "medicinal_herbs", "yarrow", "plantain"]:
            if bleeding_severity == BleedingSeverity.MILD:
                return 0.18  # Good for mild
            elif bleeding_severity == BleedingSeverity.MODERATE:
                return 0.14  # Decent for moderate
            else:
                return 0.06  # Limited for severe+
        
        # Moss - basic wild clotting (Hunger Games lore)
        elif supply_lower in ["moss", "leaf_pack", "leaves"]:
            if bleeding_severity == BleedingSeverity.MILD:
                return 0.12  # Works for mild
            elif bleeding_severity == BleedingSeverity.MODERATE:
                return 0.08  # Minimal for moderate
            else:
                return 0.02  # Almost nothing for severe+
        
        # Medicine/Antiseptic - primarily for infection
        elif supply_lower in ["medicine", "antiseptic", "alcohol", "pain_relief"]:
            return 0.08  # Minor help with bleeding, mainly for infection
        
        # Unknown/no supply
        else:
            return 0.0
        
        return result
    
    def treat_wound(self, wound: LimbWound, medical_skill: int, 
                   medical_supply: str) -> Dict[str, any]:
        """
        Attempt to treat a wound with bleeding severity consideration
        
        Args:
            wound: Wound to treat
            medical_skill: Treater's medical skill (1-10)
            medical_supply: Type of supply used (see get_medical_supply_effectiveness)
            
        Returns:
            Treatment result
        """
        result = {
            'success': False,
            'bleeding_stopped': False,
            'bleeding_reduced': False,
            'infection_cured': False,
            'limb_saved': False,
            'untreatable': False,
            'message': ''
        }
        
        # Check if wound is untreatable (fatal bleeding)
        if not wound.can_be_treated():
            result['untreatable'] = True
            result['message'] = f"Fatal bleeding from {wound.body_part.value} - wound is too severe to treat!"
            return result
        
        # Success chance based on skill, severity, and bleeding severity
        base_chance = 0.4 + (medical_skill / 10) * 0.4  # 40-80%
        severity_penalty = wound.severity * 0.1
        
        # Bleeding severity affects treatment difficulty
        if wound.bleeding_severity == BleedingSeverity.FATAL:
            severity_penalty += 0.3  # Very hard to treat
        elif wound.bleeding_severity == BleedingSeverity.SEVERE:
            severity_penalty += 0.2  # Hard to treat
        elif wound.bleeding_severity == BleedingSeverity.MODERATE:
            severity_penalty += 0.1  # Somewhat difficult
        
        success_chance = max(0.1, base_chance - severity_penalty)
        
        # Apply medical supply bonuses based on effectiveness
        supply_bonus = self._get_medical_supply_effectiveness(medical_supply, wound.bleeding_severity)
        success_chance += supply_bonus
        
        if random.random() < success_chance:
            result['success'] = True
            wound.is_treated = True
            
            # Stop or reduce bleeding based on severity
            if wound.bleeding_rate > 0:
                if wound.bleeding_severity == BleedingSeverity.FATAL:
                    # Can only reduce, not stop fatal bleeding
                    if wound.wound_type == "severed":
                        wound.bleeding_rate = max(5, wound.bleeding_rate // 3)
                        wound.bleeding_severity = BleedingSeverity.SEVERE
                        result['bleeding_reduced'] = True
                        result['message'] = f"Tourniquet applied - reduced fatal bleeding to severe"
                    else:
                        wound.bleeding_rate = max(8, wound.bleeding_rate // 2)
                        wound.bleeding_severity = BleedingSeverity.SEVERE
                        result['bleeding_reduced'] = True
                        result['message'] = "Fatal bleeding reduced to severe"
                
                elif wound.bleeding_severity == BleedingSeverity.SEVERE:
                    # Reduce to moderate
                    wound.bleeding_rate = max(4, wound.bleeding_rate // 2)
                    wound.bleeding_severity = BleedingSeverity.MODERATE
                    result['bleeding_reduced'] = True
                    result['message'] = "Severe bleeding reduced to moderate"
                
                elif wound.bleeding_severity == BleedingSeverity.MODERATE:
                    # Can stop moderate bleeding
                    wound.bleeding_rate = 0
                    wound.bleeding_severity = BleedingSeverity.MILD
                    result['bleeding_stopped'] = True
                    result['message'] = "Moderate bleeding stopped"
                
                elif wound.bleeding_severity == BleedingSeverity.MILD:
                    # Stop mild bleeding completely
                    wound.bleeding_rate = 0
                    wound.bleeding_severity = BleedingSeverity.NONE
                    result['bleeding_stopped'] = True
                    result['message'] = "Mild bleeding stopped"
            
            # Cure infection based on supply antiseptic properties
            if wound.is_infected:
                supply_lower = medical_supply.lower().replace(" ", "_")
                can_cure_infection = supply_lower in [
                    "medicine", "medical_kit", "first_aid_kit", "medkit",
                    "antiseptic", "alcohol", "herbs", "medicinal_herbs"
                ]
                if can_cure_infection:
                    wound.is_infected = False
                    result['infection_cured'] = True
                    if result['message']:
                        result['message'] += " and infection cured"
                    else:
                        result['message'] = "Infection cured"
            
            # For severed limbs, treatment prevents death but limb is lost
            if wound.wound_type == "severed":
                result['limb_saved'] = False
                if result['message']:
                    result['message'] += f" (severed {wound.body_part.value} cannot be reattached)"
                else:
                    result['message'] = f"Treated severed {wound.body_part.value}, but limb is lost"
        else:
            result['message'] = f"Failed to treat {wound.body_part.value} wound"
        
        return result


# Global singleton
_limb_system_instance = None

def get_limb_damage_system() -> LimbDamageSystem:
    """Get global limb damage system instance"""
    global _limb_system_instance
    if _limb_system_instance is None:
        _limb_system_instance = LimbDamageSystem()
    return _limb_system_instance
