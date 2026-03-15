#!/usr/bin/env python3
"""
Cornucopia Controller for Aurora Engine
Manages the countdown, tribute decisions, and cornucopia events.
"""

import json
import random
import time
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Add utils directory to path for cornucopia inventory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
try:
    from cornucopia_inventory import CornucopiaInventory
except ImportError:
    print("Warning: Could not import CornucopiaInventory, using fallback")
    CornucopiaInventory = None


class CornucopiaPhase(Enum):
    """Phases of the cornucopia event"""
    COUNTDOWN = "countdown"
    DECISION = "decision"
    BLOODBATH = "bloodbath"
    COMPLETED = "completed"


@dataclass
class TributeDecision:
    """Represents a tribute's cornucopia decision"""
    tribute_id: str
    decision: str  # "cornucopia", "flee", "early_step_off"
    reasoning: str
    risk_assessment: float
    confidence: float


@dataclass
class CornucopiaTimer:
    """Timer information for the UI"""
    total_seconds: int
    remaining_seconds: int
    phase: str  # String value of CornucopiaPhase enum for JSON serialization
    message: str


class CornucopiaController:
    """Controls the cornucopia countdown and bloodbath sequence"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cornucopia_settings = config.get("cornucopia_settings", {})
        
        # Timer state
        self.countdown_total = self.cornucopia_settings.get("countdown_seconds", 60)
        self.countdown_remaining = self.countdown_total
        self.current_phase = CornucopiaPhase.COUNTDOWN
        self.start_time = None
        
        # Tribute decisions
        self.tribute_decisions: Dict[str, TributeDecision] = {}
        self.cornucopia_participants: List[str] = []
        self.fled_tributes: List[str] = []
        self.exploded_tributes: List[str] = []
        
        # Early step-off tracking
        self.early_step_off_checked = False  # Only check once per game
        self.active_tributes: List[Dict[str, Any]] = []  # Store tribute references
        
        # Gong deduplication
        self.gong_sounded = False  # Prevent duplicate gong messages
        
        # Initialize cornucopia inventory system
        self.inventory = None
        if CornucopiaInventory:
            try:
                inventory_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cornucopia_inventory.json')
                self.inventory = CornucopiaInventory(inventory_path)
                print(f"[CORNUCOPIA] Initialized inventory system with {inventory_path}")
            except Exception as e:
                print(f"[CORNUCOPIA] Failed to initialize inventory: {e}")
                self.inventory = None
        
        # Results tracking
        self.bloodbath_results: Dict[str, Any] = {}
        self.supplies_distributed = False  # Flag to prevent premature distribution
        self.pending_supply_distribution: Dict[str, Any] = {}  # Store data for later distribution

    def start_countdown(self, tributes: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start the cornucopia countdown"""
        self.start_time = datetime.now()
        self.current_phase = CornucopiaPhase.COUNTDOWN
        self.countdown_remaining = self.countdown_total
        self.early_step_off_checked = False
        
        # Store tribute references for early step-off calculations
        if tributes:
            self.active_tributes = tributes
        
        return {
            "message_type": "cornucopia_countdown_start",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "countdown_seconds": self.countdown_total,
                "phase": self.current_phase.value,
                "message": f"Tributes, you have {self.countdown_total} seconds until the gong sounds. Good luck, and may the odds be ever in your favor!"
            }
        }

    def update_countdown(self) -> Optional[Dict[str, Any]]:
        """Update countdown timer and check for phase transitions"""
        if not self.start_time or self.current_phase == CornucopiaPhase.COMPLETED:
            return None
            
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.countdown_remaining = max(0, self.countdown_total - elapsed)
        
        # Check for early step-offs during countdown
        if self.current_phase == CornucopiaPhase.COUNTDOWN and self.countdown_remaining > 0:
            return self._check_early_step_offs()
        
        # Countdown finished - start decision phase
        elif self.current_phase == CornucopiaPhase.COUNTDOWN and self.countdown_remaining <= 0:
            # Only send gong message once
            if not self.gong_sounded:
                self.gong_sounded = True
                self.current_phase = CornucopiaPhase.DECISION
                return {
                    "message_type": "cornucopia_gong",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "phase": self.current_phase.value,
                        "message": "The gong sounds! Let the 75th Hunger Games begin!"
                    }
                }
            else:
                # Gong already sounded, just transition to decision phase silently
                self.current_phase = CornucopiaPhase.DECISION
                return None
            
        return None

    def get_timer_info(self) -> CornucopiaTimer:
        """Get current timer information for UI updates"""
        if self.current_phase == CornucopiaPhase.COUNTDOWN:
            message = f"Countdown: {int(self.countdown_remaining)}s remaining"
        elif self.current_phase == CornucopiaPhase.DECISION:
            message = "Tributes are making their decisions..."
        elif self.current_phase == CornucopiaPhase.BLOODBATH:
            message = "The cornucopia bloodbath has begun!"
        else:
            message = "Cornucopia phase completed"
            
        return CornucopiaTimer(
            total_seconds=self.countdown_total,
            remaining_seconds=int(self.countdown_remaining),
            phase=self.current_phase.value,  # Convert enum to string value
            message=message
        )

    def make_tribute_decisions(self, tributes: List[Dict[str, Any]], nemesis_engine=None) -> List[Dict[str, Any]]:
        """Have all tributes make their cornucopia decisions"""
        if self.current_phase != CornucopiaPhase.DECISION:
            return []
            
        cornucopia_tributes = []
        fled_tributes_list = []
        
        for tribute in tributes:
            decision = self._make_individual_decision(tribute, nemesis_engine)
            self.tribute_decisions[tribute["id"]] = decision
            
            tribute_name = tribute.get("name", "Unknown")
            
            if decision.decision == "cornucopia":
                self.cornucopia_participants.append(tribute)  # Store full tribute object
                cornucopia_tributes.append(tribute_name)
            elif decision.decision == "flee":
                self.fled_tributes.append(tribute)  # Store full tribute object
                fled_tributes_list.append(tribute_name)
        
        # Create grouped decision messages
        decisions = []
        
        if cornucopia_tributes:
            decisions.append({
                "message_type": "tribute_decisions_cornucopia",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "count": len(cornucopia_tributes),
                    "tributes": cornucopia_tributes,
                    "message": f"{len(cornucopia_tributes)} tributes rush toward the cornucopia",
                    "narrative": "The following tributes sprint toward the golden horn, eyes fixed on the glittering weapons and supplies:\n" + 
                                ", ".join(cornucopia_tributes)
                }
            })
        
        if fled_tributes_list:
            decisions.append({
                "message_type": "tribute_decisions_flee",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "count": len(fled_tributes_list),
                    "tributes": fled_tributes_list,
                    "message": f"{len(fled_tributes_list)} tributes flee into the arena",
                    "narrative": "The following tributes turn their backs on the cornucopia and sprint toward safety:\n" + 
                                ", ".join(fled_tributes_list)
                }
            })
        
        # Move to bloodbath phase
        self.current_phase = CornucopiaPhase.BLOODBATH
        return decisions

    def execute_bloodbath(self, tributes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the cornucopia bloodbath for participating tributes"""
        if self.current_phase != CornucopiaPhase.BLOODBATH:
            return []
            
        results = []
        
        # Handle cornucopia participants - now returns a list of events
        if self.cornucopia_participants:
            bloodbath_events = self._execute_cornucopia_combat()
            results.extend(bloodbath_events)
        
        # Fled tributes were already announced in the decision phase
        # No need to send another message here
        
        self.current_phase = CornucopiaPhase.COMPLETED
        return results

    def _check_early_step_offs(self) -> Optional[Dict[str, Any]]:
        """
        Check if any tribute steps off their platform early (1% chance per game).
        This check only happens once during the countdown period.
        """
        # Only check once per game
        if self.early_step_off_checked:
            return None
            
        self.early_step_off_checked = True
        
        # 1% chance per game (0.01) that someone steps off early
        game_step_off_chance = self.cornucopia_settings.get("game_early_step_off_chance", 0.01)
        
        if random.random() < game_step_off_chance:
            # Select a random tribute to step off early
            if not self.active_tributes:
                return None  # No tributes to select from
                
            victim = random.choice(self.active_tributes)
            victim_id = victim.get("id")
            victim_name = victim.get("name", "Unknown Tribute")
            
            # Track this tribute as having exploded
            if victim_id:
                self.exploded_tributes.append(victim_id)
            
            # Generate dramatic death message
            return {
                "message_type": "early_step_off",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "countdown_remaining": int(self.countdown_remaining),
                    "tribute_id": victim_id,
                    "tribute_name": victim_name,
                    "death_occurred": True,  # Always fatal
                    "message": f"{victim_name} steps off their platform too early!",
                    "narrative": f"The tension proves too much for {victim_name}. They step off their platform {int(self.countdown_remaining)} seconds before the gong. The landmine detonates instantly, ending their Games before they truly began.",
                    "cause_of_death": "landmine_detonation",
                    "intensity": "extreme"
                }
            }
        
        return None

    def _make_individual_decision(self, tribute: Dict[str, Any], nemesis_engine=None) -> TributeDecision:
        """Make cornucopia decision for individual tribute"""
        tribute_skills = tribute.get("skills", {})
        district = tribute.get("district", 1)
        
        # Base probabilities
        cornucopia_chance = self.cornucopia_settings.get("cornucopia_participation_rate", 0.4)
        
        # Adjust based on tribute characteristics
        decision_factors = self.cornucopia_settings.get("decision_factors", {})
        
        # Career tributes (Districts 1, 2, 4) prefer cornucopia
        if district in [1, 2, 4]:
            cornucopia_chance *= decision_factors.get("career_tribute_cornucopia_preference", 0.8)
        
        # District 12 tends to flee
        if district == 12:
            cornucopia_chance *= (1 - decision_factors.get("district_12_flee_preference", 0.8))
        
        # High combat skills prefer cornucopia
        combat_skills = (tribute_skills.get("strength", 5) + 
                        tribute_skills.get("agility", 5) + 
                        tribute_skills.get("hunting", 5)) / 3
        
        if combat_skills < 4:
            cornucopia_chance *= (1 - decision_factors.get("low_combat_skills_flee_preference", 0.7))
        elif combat_skills > 7:
            cornucopia_chance *= decision_factors.get("high_survival_skills_cornucopia_preference", 0.6)
        
        # Use Nemesis Engine if available
        if nemesis_engine:
            try:
                # Create game state for decision making
                game_state = {
                    "phase": "cornucopia_decision",
                    "available_actions": ["rush_cornucopia", "flee_arena"],
                    "risk_level": "very_high",
                    "supplies_available": True
                }
                
                decision_result = nemesis_engine.make_decision(tribute, game_state)
                if decision_result and hasattr(decision_result, 'action_type'):
                    if decision_result.action_type in ["combat", "aggressive", "resource_gathering"]:
                        cornucopia_chance *= 1.3
                    elif decision_result.action_type in ["survival", "evasive", "cautious"]:
                        cornucopia_chance *= 0.7
            except Exception as e:
                # Fallback to basic logic if Nemesis Engine fails
                pass
        
        # Make final decision
        if random.random() < cornucopia_chance:
            decision = "cornucopia"
            reasoning = f"Decided to risk the cornucopia for supplies (combat skills: {combat_skills:.1f})"
            risk_assessment = 0.7
        else:
            decision = "flee"
            reasoning = f"Chose to flee for safety (district {district}, combat skills: {combat_skills:.1f})"
            risk_assessment = 0.3
        
        return TributeDecision(
            tribute_id=tribute["id"],
            decision=decision,
            reasoning=reasoning,
            risk_assessment=risk_assessment,
            confidence=random.uniform(0.6, 0.9)
        )

    def _execute_cornucopia_combat(self) -> List[Dict[str, Any]]:
        """
        Execute combat between cornucopia participants.
        Returns a list of individual combat events plus a summary.
        """
        participants = len(self.cornucopia_participants)
        death_chance = self.cornucopia_settings.get("cornucopia_death_chance", 0.35)
        supply_chance = self.cornucopia_settings.get("supply_acquisition_chance", 0.7)
        
        # Determine casualties
        expected_deaths = int(participants * death_chance)
        actual_deaths = max(0, expected_deaths + random.randint(-1, 2))
        
        # Determine supply acquisition
        supplies_claimed = int(participants * supply_chance)
        
        events = []
        print(f"[CORNUCOPIA BLOODBATH] Generating {actual_deaths} death events for {participants} participants")
        
        # Generate individual death events
        available_tributes = list(self.cornucopia_participants)
        for i in range(actual_deaths):
            if len(available_tributes) < 2:
                break
                
            # Select victim and killer
            victim = random.choice(available_tributes)
            available_tributes.remove(victim)
            killer = random.choice([t for t in available_tributes if t != victim])
            
            victim_name = victim.get("name", "Unknown Tribute")
            killer_name = killer.get("name", "Unknown Tribute")
            
            # Combat event templates for cornucopia
            combat_templates = [
                f"{killer_name} grabs a {self._random_weapon()} and strikes down {victim_name} in the initial chaos.",
                f"As {victim_name} reaches for supplies, {killer_name} attacks from behind with a {self._random_weapon()}.",
                f"{killer_name} and {victim_name} clash violently over a backpack. {killer_name} emerges victorious.",
                f"In the frenzy at the cornucopia, {killer_name} overpowers {victim_name} with a {self._random_weapon()}.",
                f"{victim_name} is caught off-guard as {killer_name} launches a brutal attack with a {self._random_weapon()}.",
                f"The golden horn runs red as {killer_name} eliminates {victim_name} in the bloodbath.",
                f"{killer_name} shows no mercy, striking {victim_name} down as they scramble for supplies.",
                f"A desperate struggle ends with {killer_name} defeating {victim_name} at the cornucopia.",
                f"{victim_name} falls to {killer_name}'s {self._random_weapon()} in the opening moments.",
                f"The cornucopia claims another victim as {killer_name} kills {victim_name} over a cache of supplies."
            ]
            
            event = {
                "message_type": "cornucopia_death",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "victim_id": victim.get("id"),
                    "victim_name": victim_name,
                    "killer_id": killer.get("id"),
                    "killer_name": killer_name,
                    "message": f"{killer_name} kills {victim_name} at the cornucopia!",
                    "narrative": random.choice(combat_templates),
                    "intensity": "very_high",
                    "death_occurred": True,
                    "location": "cornucopia"
                }
            }
            events.append(event)
            print(f"[CORNUCOPIA BLOODBATH] Generated death event: {killer_name} killed {victim_name}")
        
        # Generate supply acquisition events (injuries/struggles without death)
        injury_count = min(3, participants - actual_deaths)  # Max 3 injury events
        for i in range(injury_count):
            if len(available_tributes) < 2:
                break
                
            tribute1 = random.choice(available_tributes)
            tribute2 = random.choice([t for t in available_tributes if t != tribute1])
            
            name1 = tribute1.get("name", "Unknown Tribute")
            name2 = tribute2.get("name", "Unknown Tribute")
            
            injury_templates = [
                f"{name1} and {name2} wrestle for a {self._random_supply()}, both sustaining injuries.",
                f"{name1} narrowly escapes {name2} with a {self._random_supply()}, bleeding but alive.",
                f"A violent struggle between {name1} and {name2} leaves both wounded but on their feet.",
                f"{name1} takes a glancing blow from {name2}'s {self._random_weapon()} while grabbing supplies."
            ]
            
            event = {
                "message_type": "cornucopia_injury",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "tribute1_id": tribute1.get("id"),
                    "tribute1_name": name1,
                    "tribute2_id": tribute2.get("id"),
                    "tribute2_name": name2,
                    "message": f"{name1} and {name2} clash at the cornucopia!",
                    "narrative": random.choice(injury_templates),
                    "intensity": "high",
                    "death_occurred": False,
                    "location": "cornucopia"
                }
            }
            events.append(event)
            print(f"[CORNUCOPIA BLOODBATH] Generated injury event: {name1} vs {name2}")
        
        # Add final summary message
        summary = {
            "message_type": "cornucopia_bloodbath",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "participants": participants,
                "casualties": actual_deaths,
                "injuries": injury_count,
                "supplies_claimed": supplies_claimed,
                "message": f"The cornucopia bloodbath ends with {actual_deaths} fallen tributes.",
                "narrative": f"When the chaos at the golden horn finally subsides, {actual_deaths} tributes lie motionless among the scattered supplies. {supplies_claimed} survivors retreat with their hard-won prizes, nursing their wounds.",
                "intensity": "very_high"
            }
        }
        events.append(summary)
        print(f"[CORNUCOPIA BLOODBATH] Generated final summary: {actual_deaths} deaths, {injury_count} injuries")
        
        return events
    
    def _random_weapon(self) -> str:
        """Return a random weapon name for narrative flavor"""
        weapons = ["knife", "sword", "spear", "machete", "axe", "mace", "trident", "bow", "sickle", "club"]
        return random.choice(weapons)
    
    def _random_supply(self) -> str:
        """Return a random supply item for narrative flavor"""
        supplies = ["backpack", "water bottle", "medical kit", "sleeping bag", "food pack", "rope", "matches", "tarp"]
        return random.choice(supplies)

    def _handle_fled_tributes(self) -> Dict[str, Any]:
        """Handle tributes who fled the cornucopia"""
        fled_count = len(self.fled_tributes)
        safety_bonus = self.cornucopia_settings.get("flee_safety_bonus", 0.9)
        
        return {
            "message_type": "tributes_fled",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "fled_count": fled_count,
                "safety_bonus": safety_bonus,
                "message": f"{fled_count} tributes chose discretion over valor and fled into the arena.",
                "narrative": f"As the gong sounds, {fled_count} tributes turn their backs on the cornucopia and sprint toward the forest, prioritizing survival over supplies.",
                "intensity": "medium"
            }
        }

    def is_completed(self) -> bool:
        """Check if cornucopia phase is completed"""
        return self.current_phase == CornucopiaPhase.COMPLETED

    def get_phase_status(self) -> str:
        """Get current phase status"""
        return self.current_phase.value
    
    def store_supply_distribution_data(self, tributes: List[Dict[str, Any]], supplies_claimed: int, participants: int):
        """
        Store supply distribution data for later processing.
        This prevents supplies from appearing before events are displayed.
        """
        self.pending_supply_distribution = {
            "tributes": tributes,
            "supplies_claimed": supplies_claimed,
            "participants": participants,
            "timestamp": datetime.now().isoformat()
        }
        print(f"[CORNUCOPIA] Stored supply distribution data: {supplies_claimed} supplies for {participants} participants")
    
    def get_pending_supply_distribution(self) -> Optional[Dict[str, Any]]:
        """
        Get pending supply distribution data and mark as distributed.
        Returns None if already distributed or no data available.
        """
        if self.supplies_distributed or not self.pending_supply_distribution:
            return None
        
        self.supplies_distributed = True
        return self.pending_supply_distribution