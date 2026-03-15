"""
Enhanced Sponsor System for Hunger Games Simulator

This module provides a sophisticated sponsor gift system that considers
tribute performance, alliances, and strategic value when determining gifts.
"""

import random
import json
from typing import Dict, List, Optional, Tuple
from tributes.tribute import Tribute

class SponsorManager:
    """Manages sponsor gifts and decisions."""

    def __init__(self):
        self.sponsor_gifts = self._load_sponsor_gifts()
        self.sponsor_history: Dict[str, List[str]] = {}  # Track gifts given to each tribute

    def _load_sponsor_gifts(self) -> Dict[str, Dict[str, Any]]:
        """Load sponsor gift configurations."""
        return {
            "food": {
                "items": ["Fresh Bread", "Dried Fruit", "Energy Bar", "Canned Soup", "Chocolate"],
                "rarity": "common",
                "effect": {"food": [10, 20]},  # Reduced from [15, 30]
                "cost": 1
            },
            "water": {
                "items": ["Water Bottle", "Electrolyte Drink", "Canteen"],
                "rarity": "common",
                "effect": {"water": [10, 20]},  # Reduced from [15, 30]
                "cost": 1
            },
            "medicine": {
                "items": ["Painkillers", "Bandages", "Antiseptic", "First Aid Kit"],
                "rarity": "uncommon",
                "effect": {"health": [10, 25]},
                "cost": 2
            },
            "weapon": {
                "items": ["Knife", "Throwing Knife", "Poison", "Explosives"],
                "rarity": "rare",
                "effect": {"weapon": True},
                "cost": 3
            },
            "tool": {
                "items": ["Multi-tool", "Night Vision Goggles", "Tracker Jammer", "Parachute"],
                "rarity": "rare",
                "effect": {"tool": True},
                "cost": 3
            },
            "luxury": {
                "items": ["Warm Blanket", "Book", "Music Player", "Comfort Food"],
                "rarity": "legendary",
                "effect": {"sanity": [10, 20]},
                "cost": 4
            }
        }

    def evaluate_sponsor_interest(self, tribute: Tribute, game_state) -> float:
        """
        Evaluate how interesting a tribute is to sponsors.

        Factors:
        - Kills (most important)
        - Health (injured tributes get more attention)
        - Alliances (lone wolves vs team players)
        - District popularity
        - Recent activity
        """
        score = 0.0

        # Kills are the biggest factor
        score += tribute.kills * 2.0

        # Health - injured tributes get more sympathy gifts
        if tribute.health < 50:
            score += (50 - tribute.health) / 10.0
        elif tribute.health > 80:
            score -= 0.5  # Healthy tributes are "boring"

        # Alliance status
        active_allies = len([ally for ally in tribute.allies
                           if ally in [t.name for t in game_state.active_tributes]])
        if active_allies == 0:
            score += 1.0  # Lone wolves are interesting
        elif active_allies > 2:
            score += 0.5  # Team players get some support

        # District factor (some districts are more popular)
        district_popularity = {
            1: 1.2, 2: 1.1, 4: 1.1, 12: 1.3,  # Popular districts
            3: 0.8, 5: 0.9, 6: 0.9, 7: 0.9, 8: 0.8, 9: 0.8,
            10: 0.9, 11: 1.0
        }
        score *= district_popularity.get(tribute.district, 1.0)

        # Recent activity bonus
        if hasattr(tribute, 'last_action_time'):
            # More recent activity = higher score
            pass

        return max(0.1, score)  # Minimum interest

    def select_sponsor_gift(self, tribute: Tribute, game_state) -> Tuple[str, Dict[str, Any]]:
        """
        Select an appropriate sponsor gift for the tribute.

        Returns:
            (gift_type, gift_data)
        """
        interest_level = self.evaluate_sponsor_interest(tribute, game_state)

        # Determine gift rarity based on interest
        if interest_level > 3.0:
            gift_pool = ["food", "water", "medicine", "weapon", "tool", "luxury"]
            weights = [0.2, 0.2, 0.2, 0.15, 0.15, 0.1]
        elif interest_level > 1.5:
            gift_pool = ["food", "water", "medicine", "weapon", "tool"]
            weights = [0.25, 0.25, 0.2, 0.15, 0.15]
        else:
            gift_pool = ["food", "water", "medicine"]
            weights = [0.4, 0.4, 0.2]

        # Avoid giving the same type repeatedly
        recent_gifts = self.sponsor_history.get(tribute.name, [])[-3:]  # Last 3 gifts
        available_gifts = [g for g in gift_pool if g not in recent_gifts]

        if not available_gifts:
            available_gifts = gift_pool

        # Adjust weights based on tribute needs
        adjusted_weights = []
        for gift_type in available_gifts:
            weight = weights[gift_pool.index(gift_type)]

            # Boost weight for needed items
            if gift_type == "food" and tribute.food < 50:
                weight *= 2.0
            elif gift_type == "water" and tribute.water < 50:
                weight *= 2.0
            elif gift_type == "medicine" and tribute.health < 70:
                weight *= 2.0
            elif gift_type == "weapon" and len(tribute.weapons) < 2:
                weight *= 1.5

            adjusted_weights.append(weight)

        gift_type = random.choices(available_gifts, weights=adjusted_weights)[0]
        gift_data = self.sponsor_gifts[gift_type]

        # Select specific item
        item = random.choice(gift_data["items"])

        # Record the gift
        if tribute.name not in self.sponsor_history:
            self.sponsor_history[tribute.name] = []
        self.sponsor_history[tribute.name].append(gift_type)

        return gift_type, {
            "item": item,
            "effect": gift_data["effect"],
            "rarity": gift_data["rarity"],
            "cost": gift_data["cost"]
        }

    def can_afford_gift(self, gift_data: Dict[str, Any], sponsor_budget: int = 10) -> bool:
        """Check if sponsors can afford this gift."""
        return gift_data.get("cost", 1) <= sponsor_budget

    def get_sponsor_message(self, tribute: Tribute, gift_type: str, gift_data: Dict[str, Any]) -> str:
        """Generate a sponsor message."""
        item = gift_data["item"]
        rarity = gift_data["rarity"]

        messages = {
            "food": [
                f"{tribute.name} receives {item} from sponsors!",
                f"A drone drops {item} for {tribute.name}!",
                f"Sponsors send {tribute.name} some {item}!"
            ],
            "water": [
                f"{tribute.name} gets {item} from generous sponsors!",
                f"A sponsor gift of {item} arrives for {tribute.name}!",
                f"{tribute.name} receives hydration in the form of {item}!"
            ],
            "medicine": [
                f"{tribute.name} receives medical supplies: {item}!",
                f"Sponsors send {item} to help {tribute.name}!",
                f"A first aid package containing {item} arrives for {tribute.name}!"
            ],
            "weapon": [
                f"{tribute.name} receives a deadly {item} from sponsors!",
                f"Sponsors arm {tribute.name} with {item}!",
                f"A weapon crate containing {item} drops for {tribute.name}!"
            ],
            "tool": [
                f"{tribute.name} gets high-tech {item} from sponsors!",
                f"Sponsors provide {tribute.name} with {item}!",
                f"Advanced technology: {item} for {tribute.name}!"
            ],
            "luxury": [
                f"{tribute.name} receives luxury item: {item}!",
                f"Sponsors send comfort in the form of {item} to {tribute.name}!",
                f"A luxury gift of {item} arrives for {tribute.name}!"
            ]
        }

        return random.choice(messages.get(gift_type, [f"{tribute.name} receives a sponsor gift!"]))

# Global instance
sponsor_manager = SponsorManager()