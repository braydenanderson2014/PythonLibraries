"""
Logging and Analytics System for Hunger Games Simulator

Tracks game statistics, performance metrics, and provides detailed logging
for analysis and debugging.
"""

import json
import time
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
from core.game_state import GameState
from tributes.tribute import Tribute

class GameLogger:
    """
    Comprehensive logging system for the Hunger Games Simulator.
    Tracks events, statistics, and performance metrics.
    """

    def __init__(self):
        self.session_start = datetime.now()
        self.events: List[Dict[str, Any]] = []
        self.statistics = defaultdict(int)
        self.performance_metrics = {}
        self.tribute_stats = {}

    def log_event(self, event_type: str, data: Dict[str, Any], tribute: Tribute = None) -> None:
        """Log a game event with timestamp and context."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }

        if tribute:
            event['tribute'] = tribute.name
            event['district'] = tribute.district

        self.events.append(event)

        # Update statistics counters
        self.statistics[f'{event_type}_count'] += 1
        if tribute:
            self.statistics[f'{event_type}_{tribute.name}'] += 1

    def log_combat(self, attacker: Tribute, defender: Tribute, damage: int, result: str) -> None:
        """Log combat events."""
        self.log_event('combat', {
            'attacker': attacker.name,
            'defender': defender.name,
            'damage': damage,
            'result': result,
            'weapon': attacker.current_weapon,
            'attacker_health': attacker.health,
            'defender_health': defender.health
        })

    def log_elimination(self, tribute: Tribute, cause: str, killer: Tribute = None) -> None:
        """Log tribute elimination."""
        data = {
            'cause': cause,
            'day': self.get_current_day(),
            'phase': self.get_current_phase(),
            'survival_days': self.get_current_day()
        }

        if killer:
            data['killer'] = killer.name

        self.log_event('elimination', data, tribute)

    def log_resource_change(self, tribute: Tribute, resource: str, old_value: int, new_value: int) -> None:
        """Log resource changes."""
        self.log_event('resource_change', {
            'resource': resource,
            'old_value': old_value,
            'new_value': new_value,
            'change': new_value - old_value
        }, tribute)

    def log_alliance_change(self, tribute1: Tribute, tribute2: Tribute, action: str) -> None:
        """Log alliance formations or breakups."""
        self.log_event('alliance_change', {
            'tribute1': tribute1.name,
            'tribute2': tribute2.name,
            'action': action
        })

    def log_environmental_event(self, event_name: str, affected_tributes: List[Tribute]) -> None:
        """Log environmental events."""
        self.log_event('environmental', {
            'event_name': event_name,
            'affected_count': len(affected_tributes),
            'affected_tributes': [t.name for t in affected_tributes]
        })

    def update_tribute_stats(self, tribute: Tribute) -> None:
        """Update comprehensive statistics for a tribute."""
        self.tribute_stats[tribute.name] = {
            'district': tribute.district,
            'kills': len(tribute.kills),
            'health': tribute.health,
            'sanity': tribute.sanity,
            'weapons': list(tribute.weapons.keys()),
            'allies': tribute.allies.copy(),
            'food': tribute.food,
            'water': tribute.water,
            'shelter': tribute.shelter,
            'is_sick': tribute.is_sick,
            'sickness_type': tribute.sickness_type,
            'has_camp': tribute.has_camp,
            'bleeding': tribute.bleeding,
            'last_updated': datetime.now().isoformat()
        }

    def get_current_day(self) -> int:
        """Get current game day (would need game state reference)."""
        return getattr(self, '_current_day', 1)

    def get_current_phase(self) -> str:
        """Get current game phase."""
        return getattr(self, '_current_phase', 'morning')

    def set_game_context(self, day: int, phase: str) -> None:
        """Update current game context for logging."""
        self._current_day = day
        self._current_phase = phase

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive game report."""
        return {
            'session_info': {
                'start_time': self.session_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.session_start).total_seconds()
            },
            'statistics': dict(self.statistics),
            'total_events': len(self.events),
            'event_breakdown': self._get_event_breakdown(),
            'tribute_final_stats': self.tribute_stats,
            'performance_metrics': self.performance_metrics
        }

    def _get_event_breakdown(self) -> Dict[str, int]:
        """Get breakdown of events by type."""
        breakdown = defaultdict(int)
        for event in self.events:
            breakdown[event['type']] += 1
        return dict(breakdown)

    def save_log(self, filename: str = None) -> None:
        """Save the complete log to a file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/game_log_{timestamp}.json'

        # Ensure logs directory exists
        import os
        os.makedirs('logs', exist_ok=True)

        log_data = {
            'report': self.generate_report(),
            'events': self.events
        }

        with open(filename, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)

class GameAnalytics:
    """
    Analytics system for analyzing game patterns and statistics.
    """

    def __init__(self, logger: GameLogger):
        self.logger = logger

    def analyze_survival_factors(self) -> Dict[str, Any]:
        """Analyze what factors contribute to tribute survival."""
        # This would analyze correlations between skills, alliances, resources, etc.
        return {
            'skill_importance': self._analyze_skill_importance(),
            'alliance_impact': self._analyze_alliance_impact(),
            'resource_management': self._analyze_resource_management()
        }

    def analyze_combat_patterns(self) -> Dict[str, Any]:
        """Analyze combat patterns and effectiveness."""
        combat_events = [e for e in self.logger.events if e['type'] == 'combat']

        weapon_effectiveness = defaultdict(lambda: {'damage': 0, 'uses': 0})
        for event in combat_events:
            weapon = event['data']['weapon']
            weapon_effectiveness[weapon]['damage'] += event['data']['damage']
            weapon_effectiveness[weapon]['uses'] += 1

        # Calculate average damage per weapon
        for weapon, stats in weapon_effectiveness.items():
            if stats['uses'] > 0:
                stats['avg_damage'] = stats['damage'] / stats['uses']

        return {
            'total_combat_events': len(combat_events),
            'weapon_effectiveness': dict(weapon_effectiveness)
        }

    def analyze_elimination_patterns(self) -> Dict[str, Any]:
        """Analyze when and how tributes are eliminated."""
        eliminations = [e for e in self.logger.events if e['type'] == 'elimination']

        causes = defaultdict(int)
        days = defaultdict(int)

        for event in eliminations:
            causes[event['data']['cause']] += 1
            days[event['data']['day']] += 1

        return {
            'total_eliminations': len(eliminations),
            'causes': dict(causes),
            'elimination_days': dict(days)
        }

    def _analyze_skill_importance(self) -> Dict[str, float]:
        """Analyze which skills are most important for survival."""
        # Placeholder - would need more sophisticated analysis
        return {
            'strength': 0.8,
            'speed': 0.9,
            'intelligence': 0.7,
            'luck': 0.6
        }

    def _analyze_alliance_impact(self) -> Dict[str, float]:
        """Analyze the impact of alliances on survival."""
        # Placeholder
        return {
            'alliance_survival_rate': 0.75,
            'solo_survival_rate': 0.45
        }

    def _analyze_resource_management(self) -> Dict[str, Any]:
        """Analyze resource management effectiveness."""
        # Placeholder
        return {
            'food_importance': 0.85,
            'water_importance': 0.90,
            'shelter_importance': 0.70
        }