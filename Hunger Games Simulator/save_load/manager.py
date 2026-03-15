"""
Save/Load System for Hunger Games Simulator

Provides functionality to save and load game states mid-simulation,
allowing players to pause and resume games.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from core.game_state import GameState
from tributes.tribute import Tribute

class SaveLoadManager:
    """
    Manages saving and loading of game states with metadata.
    """

    def __init__(self, save_directory: str = 'saves'):
        self.save_directory = save_directory
        os.makedirs(save_directory, exist_ok=True)

    def save_game(self, game_state: GameState, slot_name: str = None,
                  description: str = "") -> str:
        """
        Save the current game state to a file.

        Args:
            game_state: The current GameState object
            slot_name: Optional name for the save slot
            description: Optional description of the save

        Returns:
            The filename of the saved game
        """
        if slot_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            slot_name = f"autosave_{timestamp}"

        filename = f"{slot_name}.json"
        filepath = os.path.join(self.save_directory, filename)

        # Create save data with metadata
        save_data = {
            'metadata': {
                'save_time': datetime.now().isoformat(),
                'description': description,
                'game_day': game_state.day,
                'game_phase': game_state.phase,
                'active_tributes': len(game_state.active_tributes),
                'eliminated_tributes': len(game_state.eliminated_tributes),
                'version': '1.0'
            },
            'game_state': {
                'active_tributes': [self._serialize_tribute(t) for t in game_state.active_tributes],
                'eliminated_tributes': [self._serialize_tribute(t) for t in game_state.eliminated_tributes],
                'day': game_state.day,
                'phase': game_state.phase,
                'current_phase': game_state.current_phase,
                'active_weather_events': game_state.active_weather_events,
                'active_danger_zones': game_state.active_danger_zones,
                'active_environmental_effects': game_state.active_environmental_effects
            }
        }

        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)

        return filename

    def load_game(self, filename: str) -> Optional[GameState]:
        """
        Load a game state from a file.

        Args:
            filename: The name of the save file

        Returns:
            GameState object if successful, None if failed
        """
        filepath = os.path.join(self.save_directory, filename)

        if not os.path.exists(filepath):
            print(f"Save file {filename} not found.")
            return None

        try:
            with open(filepath, 'r') as f:
                save_data = json.load(f)

            game_data = save_data['game_state']

            # Create new GameState
            game_state = GameState()

            # Restore basic state
            game_state.day = game_data['day']
            game_state.phase = game_data['phase']
            game_state.current_phase = game_data.get('current_phase', game_data['phase'])
            game_state.active_weather_events = game_data.get('active_weather_events', [])
            game_state.active_danger_zones = game_data.get('active_danger_zones', [])
            game_state.active_environmental_effects = game_data.get('active_environmental_effects', [])

            # Restore tributes
            game_state.active_tributes = [self._deserialize_tribute(t) for t in game_data['active_tributes']]
            game_state.eliminated_tributes = [self._deserialize_tribute(t) for t in game_data['eliminated_tributes']]

            return game_state

        except Exception as e:
            print(f"Error loading save file {filename}: {e}")
            return None

    def list_saves(self) -> List[Dict[str, str]]:
        """
        List all available save files with metadata.

        Returns:
            List of save file information
        """
        saves = []

        for filename in os.listdir(self.save_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(self.save_directory, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    metadata = data.get('metadata', {})
                    saves.append({
                        'filename': filename,
                        'description': metadata.get('description', ''),
                        'save_time': metadata.get('save_time', ''),
                        'game_day': metadata.get('game_day', 0),
                        'game_phase': metadata.get('game_phase', ''),
                        'active_tributes': metadata.get('active_tributes', 0)
                    })
                except:
                    # If we can't read the metadata, still include the file
                    saves.append({
                        'filename': filename,
                        'description': 'Corrupted save file',
                        'save_time': '',
                        'game_day': 0,
                        'game_phase': '',
                        'active_tributes': 0
                    })

        # Sort by save time (newest first)
        saves.sort(key=lambda x: x['save_time'], reverse=True)
        return saves

    def delete_save(self, filename: str) -> bool:
        """
        Delete a save file.

        Args:
            filename: Name of the save file to delete

        Returns:
            True if successful, False otherwise
        """
        filepath = os.path.join(self.save_directory, filename)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except:
                return False
        return False

    def _serialize_tribute(self, tribute: Tribute) -> Dict:
        """Convert a Tribute object to a serializable dictionary."""
        return {
            'name': tribute.name,
            'skills': tribute.skills,
            'weapons': tribute.weapons,
            'district': tribute.district,
            'gender': tribute.gender,
            'health': tribute.health,
            'sanity': tribute.sanity,
            'status': tribute.status,
            'kills': tribute.kills,
            'allies': tribute.allies,
            'trust': tribute.trust,
            'has_camp': tribute.has_camp,
            'speed': tribute.speed,
            'bleeding': tribute.bleeding,
            'infection': tribute.infection,
            'bleeding_days': tribute.bleeding_days,
            'total_bleeding_phases': tribute.total_bleeding_phases,
            'preferred_weapon': tribute.preferred_weapon,
            'target_weapon': tribute.target_weapon,
            'relationships': tribute.relationships,
            'weapon_durability': tribute.weapon_durability,
            'ammunition': tribute.ammunition,
            'food': tribute.food,
            'water': tribute.water,
            'shelter': tribute.shelter,
            'is_sick': tribute.is_sick,
            'sickness_type': tribute.sickness_type,
            'sickness_days': tribute.sickness_days,
            'sickness_curable': tribute.sickness_curable,
            'ongoing_effects': tribute.ongoing_effects,
            'traps': tribute.traps,
            'damage_sources': tribute.damage_sources,
            'starvation_timer': tribute.starvation_timer,
            'dehydration_timer': tribute.dehydration_timer
        }

    def _deserialize_tribute(self, data: Dict) -> Tribute:
        """Convert a dictionary back to a Tribute object."""
        tribute = Tribute(
            name=data['name'],
            district=data['district'],
            gender=data.get('gender', 'male'),
            skills=data['skills']
        )

        # Restore all attributes
        tribute.weapons = data['weapons']
        tribute.health = data['health']
        tribute.sanity = data['sanity']
        tribute.status = data['status']
        tribute.kills = data['kills']
        tribute.allies = data['allies']
        tribute.trust = data['trust']
        tribute.has_camp = data['has_camp']
        tribute.speed = data['speed']
        tribute.bleeding = data['bleeding']
        tribute.infection = data['infection']
        tribute.bleeding_days = data['bleeding_days']
        tribute.total_bleeding_phases = data['total_bleeding_phases']
        tribute.preferred_weapon = data['preferred_weapon']
        tribute.target_weapon = data['target_weapon']
        tribute.relationships = data['relationships']
        tribute.weapon_durability = data['weapon_durability']
        tribute.ammunition = data['ammunition']
        tribute.food = data['food']
        tribute.water = data['water']
        tribute.shelter = data['shelter']
        tribute.is_sick = data['is_sick']
        tribute.sickness_type = data['sickness_type']
        tribute.sickness_days = data['sickness_days']
        tribute.sickness_curable = data['sickness_curable']
        tribute.ongoing_effects = data['ongoing_effects']
        tribute.traps = data.get('traps', [])
        tribute.damage_sources = data.get('damage_sources', [])
        tribute.starvation_timer = data.get('starvation_timer', 0)
        tribute.dehydration_timer = data.get('dehydration_timer', 0)

        return tribute

    def quick_save(self, game_state: GameState) -> str:
        """Create a quick save with automatic naming."""
        return self.save_game(game_state, description="Quick save")

    def auto_save(self, game_state: GameState) -> str:
        """Create an automatic save at regular intervals."""
        return self.save_game(game_state, description="Auto save")