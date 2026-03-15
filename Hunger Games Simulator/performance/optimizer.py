"""
Performance Optimization Module for Hunger Games Simulator

Provides caching, efficient data structures, and performance monitoring
to improve simulation speed and responsiveness.
"""

import time
from functools import lru_cache
from typing import Dict, List, Any, Optional
from collections import defaultdict
import weakref

class PerformanceMonitor:
    """
    Monitors performance metrics throughout the simulation.
    """

    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str):
        """End timing an operation and record the duration."""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation].append(duration)
            del self.start_times[operation]

    def get_average_time(self, operation: str) -> float:
        """Get the average time for an operation."""
        times = self.metrics[operation]
        return sum(times) / len(times) if times else 0.0

    def get_total_time(self, operation: str) -> float:
        """Get the total time spent on an operation."""
        return sum(self.metrics[operation])

    def get_operation_count(self, operation: str) -> int:
        """Get the number of times an operation was performed."""
        return len(self.metrics[operation])

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {}
        for operation, times in self.metrics.items():
            report[operation] = {
                'count': len(times),
                'total_time': sum(times),
                'average_time': sum(times) / len(times) if times else 0,
                'min_time': min(times) if times else 0,
                'max_time': max(times) if times else 0
            }
        return report

class CacheManager:
    """
    Manages various caches to improve performance.
    """

    def __init__(self):
        self.weapon_data_cache = {}
        self.message_cache = {}
        self.event_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    @lru_cache(maxsize=128)
    def get_weapon_data(self, weapon_name: str) -> Optional[Dict]:
        """Cache weapon data lookups."""
        if weapon_name in self.weapon_data_cache:
            self._cache_hits += 1
            return self.weapon_data_cache[weapon_name]

        # Load from file if not cached
        try:
            import json
            with open('data/weapons.json', 'r') as f:
                weapons_data = json.load(f)
                self.weapon_data_cache.update(weapons_data)
                self._cache_misses += 1
                return weapons_data.get(weapon_name)
        except:
            return None

    @lru_cache(maxsize=256)
    def get_message(self, category: str, key: str) -> str:
        """Cache message lookups."""
        cache_key = f"{category}:{key}"
        if cache_key in self.message_cache:
            self._cache_hits += 1
            return self.message_cache[cache_key]

        # Load from messages file if not cached
        try:
            import json
            with open('data/messages.json', 'r') as f:
                messages_data = json.load(f)
                # Flatten the messages for caching
                for cat, msgs in messages_data.items():
                    for k, v in msgs.items():
                        self.message_cache[f"{cat}:{k}"] = v
                self._cache_misses += 1
                return self.message_cache.get(cache_key, f"[{category}:{key}]")
        except:
            return f"[{category}:{key}]"

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def clear_cache(self):
        """Clear all caches."""
        self.weapon_data_cache.clear()
        self.message_cache.clear()
        self.event_cache.clear()
        self.get_weapon_data.cache_clear()
        self.get_message.cache_clear()

class EfficientDataStructures:
    """
    Provides efficient data structures for common operations.
    """

    def __init__(self):
        self.tribute_index = {}  # name -> tribute reference
        self.alliance_graph = defaultdict(set)  # tribute -> set of allies
        self.location_index = defaultdict(list)  # location -> list of tributes
        self.skill_index = defaultdict(lambda: defaultdict(list))  # skill -> value -> list of tributes

    def update_tribute_index(self, tributes: List):
        """Update the tribute index for fast lookups."""
        self.tribute_index.clear()
        for tribute in tributes:
            self.tribute_index[tribute.name] = tribute

    def update_alliance_graph(self, tributes: List):
        """Update the alliance graph for relationship queries."""
        self.alliance_graph.clear()
        for tribute in tributes:
            self.alliance_graph[tribute.name] = set(tribute.allies)

    def update_skill_index(self, tributes: List):
        """Update the skill index for efficient skill-based queries."""
        self.skill_index.clear()
        for tribute in tributes:
            for skill, value in tribute.skills.items():
                self.skill_index[skill][value].append(tribute.name)

    def find_tribute_by_name(self, name: str):
        """Fast tribute lookup by name."""
        return self.tribute_index.get(name)

    def get_allies(self, tribute_name: str) -> set:
        """Get all allies of a tribute."""
        return self.alliance_graph.get(tribute_name, set())

    def get_tributes_with_skill_above(self, skill: str, threshold: int) -> List[str]:
        """Get tributes with skill above threshold."""
        result = []
        for value in range(threshold + 1, 11):  # Skills range from 1-10
            result.extend(self.skill_index[skill].get(value, []))
        return result

    def get_mutual_allies(self, tribute1: str, tribute2: str) -> set:
        """Find mutual allies between two tributes."""
        allies1 = self.get_allies(tribute1)
        allies2 = self.get_allies(tribute2)
        return allies1.intersection(allies2)

class RelationshipOptimizer:
    """
    Optimizes relationship calculations and trust updates.
    """

    def __init__(self):
        self.trust_cache = {}  # (tribute1, tribute2) -> trust value
        self.relationship_cache = {}  # Cache for complex relationship calculations

    def update_trust_cache(self, tribute):
        """Update trust cache for a tribute."""
        for other_tribute, trust_value in tribute.trust.items():
            self.trust_cache[(tribute.name, other_tribute)] = trust_value
            self.trust_cache[(other_tribute, tribute.name)] = trust_value  # Bidirectional

    def get_trust(self, tribute1_name: str, tribute2_name: str) -> int:
        """Get trust value between two tributes."""
        return self.trust_cache.get((tribute1_name, tribute2_name), 50)  # Default neutral trust

    def calculate_relationship_score(self, tribute1, tribute2) -> float:
        """
        Calculate a comprehensive relationship score between two tributes.
        Cached for performance.
        """
        cache_key = (tribute1.name, tribute2.name)
        if cache_key in self.relationship_cache:
            return self.relationship_cache[cache_key]

        # Calculate score based on trust, alliances, shared kills, etc.
        score = 0.0

        # Trust component (0-100)
        trust = self.get_trust(tribute1.name, tribute2.name)
        score += (trust - 50) / 50 * 40  # -40 to +40

        # Alliance component
        if tribute2.name in tribute1.allies:
            score += 30
        if tribute1.name in tribute2.allies:
            score += 30

        # Shared enemies/kills component
        shared_kills = set(tribute1.kills).intersection(set(tribute2.kills))
        score += len(shared_kills) * 10

        # District relationship (same district = slight bonus)
        if tribute1.district == tribute2.district:
            score += 10

        self.relationship_cache[cache_key] = score
        return score

    def clear_cache(self):
        """Clear all caches when relationships change."""
        self.trust_cache.clear()
        self.relationship_cache.clear()