import json
import random
from typing import List
from tributes.tribute import Tribute

class GameState:
    def __init__(self):
        self.active_tributes: List[Tribute] = []
        self.eliminated_tributes: List[Tribute] = []
        self.day: int = 1
        self.phase: str = 'morning'
        self.current_phase: str = 'morning'  # For time-based events
        self.pre_environmental_phase: str = 'morning'  # Phase before environmental phase
        # Environmental effects tracking
        self.active_weather_events: List[dict] = []
        self.active_danger_zones: List[dict] = []
        self.active_environmental_effects: List[dict] = []

    def save(self, filename='data/game_state.json'):
        def tribute_to_dict(tribute):
            """Convert tribute to dict, excluding non-serializable attributes."""
            tribute_dict = tribute.__dict__.copy()
            # Remove the behavior tree as it's not JSON serializable
            tribute_dict.pop('behavior_tree', None)
            return tribute_dict
        
        data = {
            'active': [tribute_to_dict(t) for t in self.active_tributes],
            'eliminated': [tribute_to_dict(t) for t in self.eliminated_tributes],
            'day': self.day,
            'phase': self.phase,
            'current_phase': self.current_phase,
            'pre_environmental_phase': self.pre_environmental_phase,
            'active_weather_events': self.active_weather_events,
            'active_danger_zones': self.active_danger_zones,
            'active_environmental_effects': self.active_environmental_effects
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, filename='data/game_state.json'):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.active_tributes = [Tribute(**t) for t in data['active']]
        self.eliminated_tributes = [Tribute(**t) for t in data['eliminated']]
        self.day = data['day']
        self.phase = data['phase']
        self.current_phase = data.get('current_phase', 'morning')
        self.pre_environmental_phase = data.get('pre_environmental_phase', 'morning')
        self.active_weather_events = data.get('active_weather_events', [])
        self.active_danger_zones = data.get('active_danger_zones', [])
        self.active_environmental_effects = data.get('active_environmental_effects', [])

    def advance_phase(self):
        """Advance to the next phase of the day."""
        # Check if we should insert an environmental phase (8% chance, but only if we have active effects)
        if random.random() < 0.08 and (self.active_weather_events or self.active_environmental_effects):
            # Save the current normal phase before inserting environmental phase
            self.pre_environmental_phase = self.phase
            # Insert environmental phase
            self.phase = 'environmental'
            self.current_phase = 'environmental'
            return
        
        # Normal phase advancement
        if self.phase == 'morning':
            self.phase = 'afternoon'
        elif self.phase == 'afternoon':
            self.phase = 'evening'
        elif self.phase == 'evening':
            self.phase = 'morning'
            self.day += 1
        elif self.phase == 'environmental':
            # After environmental phase, restore to the saved normal phase
            self.phase = self.pre_environmental_phase
            # Advance from the restored phase
            if self.phase == 'morning':
                self.phase = 'afternoon'
            elif self.phase == 'afternoon':
                self.phase = 'evening'
            elif self.phase == 'evening':
                self.phase = 'morning'
                self.day += 1
        self.current_phase = self.phase