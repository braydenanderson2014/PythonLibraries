#!/usr/bin/env python3
"""
Phase Controller for Aurora Engine
Manages game phases, determines allowed events, and handles Cornucopia logic.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PhaseInfo:
    """Information about a game phase"""
    name: str
    phase_type: str  # 'cornucopia', 'day_phase', 'night_phase', etc.
    day: int
    phase_number: int
    allowed_events: List[str]
    intensity: str = "medium"
    duration_minutes: int = 60
    is_special_phase: bool = False


class PhaseController:
    """Controls game phases and determines what events can occur"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.phases_config = self.config.get("phases", {})
        self.current_day = 1
        self.current_phase = 0
        self.game_started = False
        self.cornucopia_completed = False

    def start_game(self) -> Dict[str, Any]:
        """Initialize the game and return the first phase"""
        self.game_started = True
        self.current_day = 1
        self.current_phase = 0
        self.cornucopia_completed = False

        # First phase is always Cornucopia
        return self.get_current_phase_info()

    def advance_phase(self) -> Optional[Dict[str, Any]]:
        """Move to the next phase, return None if game is over"""
        if not self.game_started:
            return None

        # If Cornucopia hasn't happened yet, do it first
        if not self.cornucopia_completed:
            self.cornucopia_completed = True
            return self.get_current_phase_info()

        # Advance phase counter
        self.current_phase += 1

        # Check if we've completed all phases for the current day
        day_phases = self.phases_config.get("phases_per_day", 3)
        if self.current_phase >= day_phases:
            self.current_phase = 0
            self.current_day += 1

        # Check if game is over
        total_days = self.phases_config.get("total_days", 7)
        if self.current_day > total_days:
            return None

        return self.get_current_phase_info()

    def get_current_phase_info(self) -> Dict[str, Any]:
        """Get information about the current phase"""
        if not self.game_started:
            return None

        phase_info = self._get_phase_info()
        if phase_info is None:
            return None

        return {
            "phase_info": {
                "name": phase_info.name,
                "type": phase_info.phase_type,
                "day": phase_info.day,
                "phase_number": phase_info.phase_number,
                "allowed_events": phase_info.allowed_events,
                "intensity": phase_info.intensity,
                "duration_minutes": phase_info.duration_minutes,
                "is_special_phase": phase_info.is_special_phase
            },
            "game_state": {
                "current_day": self.current_day,
                "current_phase": self.current_phase,
                "total_days": self.phases_config.get("total_days", 7),
                "cornucopia_completed": self.cornucopia_completed,
                "game_over": self._is_game_over()
            }
        }

    def _get_phase_info(self) -> Optional[PhaseInfo]:
        """Internal method to get phase information"""
        if not self.cornucopia_completed:
            # Cornucopia phase
            cornucopia_config = self.phases_config.get("cornucopia_phase", {})
            return PhaseInfo(
                name=cornucopia_config.get("name", "Cornucopia"),
                phase_type="cornucopia",
                day=1,
                phase_number=0,
                allowed_events=cornucopia_config.get("allowed_events", ["Arena Events", "Combat Events"]),
                intensity="high",
                duration_minutes=cornucopia_config.get("duration_minutes", 30),
                is_special_phase=True
            )

        # Regular day phases
        day_phases = self.phases_config.get("day_phases", {})
        phase_key = str(self.current_phase + 1)  # phases are 1-indexed in config

        if phase_key not in day_phases:
            return None

        phase_config = day_phases[phase_key]
        return PhaseInfo(
            name=phase_config.get("name", f"Phase {self.current_phase + 1}"),
            phase_type="day_phase",
            day=self.current_day,
            phase_number=self.current_phase + 1,
            allowed_events=phase_config.get("allowed_events", ["Idle Events"]),
            intensity=phase_config.get("intensity", "medium"),
            duration_minutes=self.config.get("settings", {}).get("phase_duration_minutes", 60),
            is_special_phase=False
        )

    def _is_game_over(self) -> bool:
        """Check if the game has ended"""
        total_days = self.phases_config.get("total_days", 7)
        return self.current_day > total_days

    def get_allowed_events_for_current_phase(self) -> List[str]:
        """Get the list of allowed event types for the current phase"""
        phase_info = self._get_phase_info()
        if phase_info is None:
            return []
        return phase_info.allowed_events

    def is_event_allowed(self, event_type: str) -> bool:
        """Check if a specific event type is allowed in the current phase"""
        allowed_events = self.get_allowed_events_for_current_phase()
        return event_type in allowed_events

    def get_phase_duration(self) -> int:
        """Get the duration of the current phase in minutes"""
        phase_info = self._get_phase_info()
        if phase_info is None:
            return 0
        return phase_info.duration_minutes

    def get_game_progress(self) -> Dict[str, Any]:
        """Get overall game progress information"""
        total_days = self.phases_config.get("total_days", 7)
        total_phases = total_days * self.phases_config.get("phases_per_day", 3)

        completed_phases = (self.current_day - 1) * self.phases_config.get("phases_per_day", 3)
        if self.cornucopia_completed:
            completed_phases += self.current_phase

        return {
            "current_day": self.current_day,
            "current_phase": self.current_phase,
            "total_days": total_days,
            "completed_phases": completed_phases,
            "total_phases": total_phases,
            "progress_percentage": (completed_phases / total_phases) * 100 if total_phases > 0 else 0,
            "cornucopia_completed": self.cornucopia_completed,
            "game_over": self._is_game_over()
        }


# Example usage and testing
if __name__ == "__main__":
    controller = PhaseController()

    print("Starting Aurora Engine Phase Controller Test")
    print("=" * 50)

    # Start game
    phase_data = controller.start_game()
    print(f"Game started with phase: {phase_data['phase_info']['name']}")
    print(f"Allowed events: {phase_data['phase_info']['allowed_events']}")
    print()

    # Advance through phases
    while True:
        next_phase = controller.advance_phase()
        if next_phase is None:
            print("Game over!")
            break

        phase_info = next_phase['phase_info']
        game_state = next_phase['game_state']

        print(f"Day {game_state['current_day']}, Phase {phase_info['phase_number']}: {phase_info['name']}")
        print(f"  Type: {phase_info['phase_type']}")
        print(f"  Allowed events: {phase_info['allowed_events']}")
        print(f"  Intensity: {phase_info['intensity']}")
        print(f"  Duration: {phase_info['duration_minutes']} minutes")
        print(f"  Special phase: {phase_info['is_special_phase']}")
        print()

        # Stop after a few phases for testing
        if game_state['current_day'] > 1:
            break