import json
import os
from typing import List, Dict, Optional
from tributes.tribute import Tribute

class CustomTributeManager:
    """Manages loading and handling custom tribute configurations and relationships."""

    def __init__(self, config_file: str = "data/tribute_upload.json"):
        self.config_file = config_file
        self.custom_config = None
        self.relationship_types = {}
        self.global_settings = {}

    def load_config(self) -> bool:
        """Load the custom tribute configuration file."""
        if not os.path.exists(self.config_file):
            return False

        try:
            with open(self.config_file, 'r') as f:
                self.custom_config = json.load(f)

            self.relationship_types = self.custom_config.get("relationship_types", {})
            self.global_settings = self.custom_config.get("global_settings", {})
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading custom tribute config: {e}")
            return False

    def has_custom_tributes(self) -> bool:
        """Check if custom tributes are available and enabled."""
        if not self.custom_config:
            return False
        return self.global_settings.get("enable_custom_tributes", False)

    def get_custom_tributes(self) -> List[Tribute]:
        """Load custom tributes from the configuration."""
        if not self.custom_config or not self.has_custom_tributes():
            return []

        custom_tributes = []
        
        # First pass: collect all tribute names for validation
        tribute_names = set()
        for tribute_data in self.custom_config.get("custom_tributes", []):
            name = tribute_data.get("name", "").strip()
            if name:
                tribute_names.add(name)
        
        # Second pass: create tributes and validate relationships
        for tribute_data in self.custom_config.get("custom_tributes", []):
            try:
                # Create tribute with custom data
                tribute = Tribute(
                    name=tribute_data["name"],
                    skills=tribute_data.get("skills", {}),
                    weapons=tribute_data.get("weapons", ["Fists"]),
                    district=tribute_data.get("district", 1),
                    gender=tribute_data.get("gender", "male"),
                    health=tribute_data.get("health", 100),
                    sanity=tribute_data.get("sanity", 100),
                    speed=tribute_data.get("speed", 5)
                )

                # Set weapon preferences
                if "preferred_weapon" in tribute_data:
                    tribute.set_preferred_weapon(tribute_data["preferred_weapon"])
                if "target_weapon" in tribute_data:
                    tribute.set_target_weapon(tribute_data["target_weapon"])

                # Set camp status
                tribute.has_camp = tribute_data.get("has_camp", False)

                # Load relationships with validation
                relationships = tribute_data.get("relationships", {})
                for other_name, rel_data in relationships.items():
                    if other_name in tribute_names:
                        tribute.add_relationship(
                            other_name,
                            rel_data["type"],
                            rel_data.get("bias_factor", 1.0),
                            rel_data.get("description", "")
                        )
                    else:
                        print(f"Warning: Tribute '{tribute.name}' has relationship with '{other_name}' who is not in the custom tribute configuration. Ignoring this relationship.")

                custom_tributes.append(tribute)
            except KeyError as e:
                print(f"Error loading custom tribute {tribute_data.get('name', 'Unknown')}: missing field {e}")
                continue

        return custom_tributes

    def get_relationship_bias(self, tribute1_name: str, tribute2_name: str, tribute1: Tribute) -> float:
        """Get the relationship bias between two tributes."""
        if not self.global_settings.get("relationship_influence", 1.0):
            return 1.0

        # Get bias from tribute1's perspective
        base_bias = tribute1.get_relationship_bias(tribute2_name)

        # Apply randomization if enabled
        randomization = self.global_settings.get("bias_randomization", 0.0)
        if randomization > 0:
            import random
            bias_multiplier = 1.0 + random.uniform(-randomization, randomization)
            base_bias *= bias_multiplier

        return max(0.1, base_bias)  # Ensure bias doesn't go too low

    def get_relationship_type_info(self, relationship_type: str) -> Dict:
        """Get information about a relationship type."""
        return self.relationship_types.get(relationship_type, {
            "description": "Unknown relationship type",
            "combat_bias": 1.0,
            "alliance_chance": 1.0,
            "attack_chance": 1.0
        })

    def get_custom_tribute_names(self) -> List[str]:
        """Get list of custom tribute names."""
        if not self.custom_config:
            return []
        return [t.get("name", "") for t in self.custom_config.get("custom_tributes", [])]

# Global instance for easy access
custom_tribute_manager = CustomTributeManager()