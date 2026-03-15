"""
Cornucopia Inventory Management System

This module manages the items available in the Cornucopia bloodbath,
providing a dynamic inventory system based on rarity and quantity settings.
"""

import json
import random
from typing import Dict, List, Any, Tuple

class CornucopiaInventory:
    """Manages Cornucopia inventory and item distribution."""

    def __init__(self, inventory_file: str = "data/cornucopia_inventory.json"):
        with open(inventory_file, 'r') as f:
            self.inventory_data = json.load(f)

        self.generated_inventory = None

    def generate_inventory(self, tribute_count: int) -> Dict[str, Any]:
        """
        Generate a random Cornucopia inventory based on tribute count.

        Args:
            tribute_count: Number of tributes (affects total items available)

        Returns:
            Dictionary containing available weapons, supplies, and ammunition
        """
        self.generated_inventory = {
            'weapons': [],
            'supplies': {},
            'ammunition': {}
        }

        # Generate weapons based on rarity and tribute count
        self._generate_weapons(tribute_count)

        # Generate supplies
        self._generate_supplies(tribute_count)

        # Generate ammunition
        self._generate_ammunition()

        return self.generated_inventory

    def _generate_weapons(self, tribute_count: int):
        """Generate weapons inventory."""
        multipliers = self.inventory_data['quantity_multipliers']['weapons']
        base_count = random.randint(multipliers['min'], multipliers['max'])

        # Scale with tribute count (more tributes = more weapons)
        total_weapons = int(base_count * (tribute_count / 24.0))  # 24 is baseline

        # Distribute by rarity
        rarity_weights = self.inventory_data['rarity_weights']

        for rarity, weapons in rarity_weights.items():
            if rarity == 'common':
                weight = 0.4
            elif rarity == 'uncommon':
                weight = 0.35
            elif rarity == 'rare':
                weight = 0.2
            else:  # legendary
                weight = 0.05

            rarity_count = int(total_weapons * weight)
            if rarity_count > 0:
                selected_weapons = random.choices(weapons, k=min(rarity_count, len(weapons)))
                self.generated_inventory['weapons'].extend(selected_weapons)

        # Ensure minimum weapons and shuffle
        min_weapons = max(10, tribute_count // 2)
        while len(self.generated_inventory['weapons']) < min_weapons:
            weapon = random.choice(self.inventory_data['weapons'])
            if weapon not in self.generated_inventory['weapons']:
                self.generated_inventory['weapons'].append(weapon)

        random.shuffle(self.generated_inventory['weapons'])

    def _generate_supplies(self, tribute_count: int):
        """Generate supplies inventory."""
        for supply_type, supply_data in self.inventory_data['supplies'].items():
            multipliers = self.inventory_data['quantity_multipliers'][supply_type]
            base_count = random.randint(multipliers['min'], multipliers['max'])

            # Scale with tribute count
            total_items = int(base_count * (tribute_count / 24.0))

            if total_items > 0:
                selected_items = random.choices(
                    supply_data['items'],
                    k=min(total_items, len(supply_data['items']))
                )

                self.generated_inventory['supplies'][supply_type] = {
                    'items': selected_items,
                    'quantity_range': supply_data['quantity_range'],
                    'effect': supply_data['effect']
                }

    def _generate_ammunition(self):
        """Generate ammunition for ranged weapons."""
        for ammo_type, ammo_data in self.inventory_data['ammunition'].items():
            # Generate ammunition for weapons that use this type
            quantity = random.randint(
                ammo_data['quantity_range'][0],
                ammo_data['quantity_range'][1]
            )

            self.generated_inventory['ammunition'][ammo_type] = quantity

    def get_available_weapons(self) -> List[str]:
        """Get list of available weapons."""
        return self.generated_inventory['weapons'].copy() if self.generated_inventory else []

    def get_available_supplies(self) -> Dict[str, Any]:
        """Get available supplies."""
        return self.generated_inventory['supplies'].copy() if self.generated_inventory else {}

    def remove_weapon(self, weapon: str) -> bool:
        """Remove a weapon from inventory. Returns True if successful."""
        if self.generated_inventory and weapon in self.generated_inventory['weapons']:
            self.generated_inventory['weapons'].remove(weapon)
            return True
        return False

    def get_supply_item(self, supply_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get a random supply item of the specified type.
        Returns (item_name, effect_data)
        """
        if (self.generated_inventory and
            supply_type in self.generated_inventory['supplies'] and
            self.generated_inventory['supplies'][supply_type]['items']):

            supplies = self.generated_inventory['supplies'][supply_type]
            item = random.choice(supplies['items'])
            supplies['items'].remove(item)  # Remove used item

            return item, supplies['effect']

        return None, {}

    def get_ammunition(self, ammo_type: str, amount: int) -> int:
        """Get ammunition of specified type and amount. Returns actual amount available."""
        if (self.generated_inventory and
            ammo_type in self.generated_inventory['ammunition']):

            available = self.generated_inventory['ammunition'][ammo_type]
            taken = min(amount, available)
            self.generated_inventory['ammunition'][ammo_type] -= taken
            return taken

        return 0

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get a summary of current inventory."""
        if not self.generated_inventory:
            return {}

        return {
            'weapons_count': len(self.generated_inventory['weapons']),
            'weapons_list': self.generated_inventory['weapons'][:5],  # First 5
            'supplies_count': sum(len(s.get('items', []))
                                 for s in self.generated_inventory['supplies'].values()),
            'ammunition_types': list(self.generated_inventory['ammunition'].keys())
        }

# Global instance
cornucopia_inventory = CornucopiaInventory()