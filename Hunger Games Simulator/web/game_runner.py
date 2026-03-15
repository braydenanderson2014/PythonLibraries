import sys
import os
import json
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

# Add the parent directory to the path so we can import from the main project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WebGameRunner:
    """Handles running Hunger Games simulations for the web interface."""

    def __init__(self):
        self.game_results = {}

    def prepare_tribute_data(self, tribute_jsons: List[Dict], output_file: str = "../data/tribute_upload.json") -> bool:
        """Prepare tribute data for the game by combining all uploaded JSONs."""
        try:
            # Combine all tribute JSONs into the expected format
            combined_data = {
                "description": "Web-uploaded tribute configurations",
                "version": "1.0",
                "global_settings": {
                    "enable_custom_tributes": True,
                    "relationship_influence": 1.0,
                    "bias_randomization": 0.0
                },
                "relationship_types": {},
                "custom_tributes": []
            }

            for tribute_entry in tribute_jsons:
                tribute_data = tribute_entry['data'].copy()
                # Ensure required fields are present
                if 'weapons' not in tribute_data:
                    tribute_data['weapons'] = ['Fists']
                if 'preferred_weapon' not in tribute_data:
                    tribute_data['preferred_weapon'] = 'Sword'
                if 'target_weapon' not in tribute_data:
                    tribute_data['target_weapon'] = None
                if 'health' not in tribute_data:
                    tribute_data['health'] = 100
                if 'sanity' not in tribute_data:
                    tribute_data['sanity'] = 100
                if 'speed' not in tribute_data:
                    tribute_data['speed'] = 5
                if 'has_camp' not in tribute_data:
                    tribute_data['has_camp'] = False
                if 'relationships' not in tribute_data:
                    tribute_data['relationships'] = {}

                combined_data['custom_tributes'].append(tribute_data)

            # Write to the tribute_upload.json file
            with open(output_file, 'w') as f:
                json.dump(combined_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error preparing tribute data: {e}")
            return False

    def prepare_pregame_data(self, alliances: List[Dict], targets: List[Dict], output_file: str = "../data/pregame_data.json") -> bool:
        """Prepare pre-game alliances and targets data for the simulation."""
        try:
            pregame_data = {
                "description": "Pre-game alliances and targets from web lobby",
                "version": "1.0",
                "alliances": alliances,
                "targets": targets,
                "generated_at": datetime.now().isoformat()
            }

            # Write to the pregame_data.json file
            with open(output_file, 'w') as f:
                json.dump(pregame_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error preparing pre-game data: {e}")
            return False

    def run_simulation(self, game_id: str, tribute_jsons: List[Dict]) -> Dict:
        """Run the Hunger Games simulation and return results."""
        try:
            # Prepare tribute data
            if not self.prepare_tribute_data(tribute_jsons):
                return {
                    'success': False,
                    'error': 'Failed to prepare tribute data'
                }

            # Run the actual simulation
            result = self._run_actual_simulation()

            self.game_results[game_id] = {
                'success': result['success'],
                'winner': result.get('winner', 'Unknown'),
                'stats': result.get('stats', {}),
                'completed_at': datetime.now()
            }

            return self.game_results[game_id]

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def run_simulation_streaming(self, game_id: str, tribute_jsons: List[Dict], game_settings: Dict, active_games_ref: Dict[str, dict], alliances: List[Dict] = None, targets: List[Dict] = None) -> Dict:
        """Run the Hunger Games simulation by monitoring the web output file."""
        try:
            # Prepare tribute data
            if not self.prepare_tribute_data(tribute_jsons):
                return {
                    'success': False,
                    'error': 'Failed to prepare tribute data'
                }

            # Prepare pre-game alliances and targets
            self.prepare_pregame_data(alliances or [], targets or [])

            # Clear any existing web output file
            web_output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'web_output.json')
            if os.path.exists(web_output_file):
                os.remove(web_output_file)

            # Run the simulation
            result = self._run_actual_simulation_streaming(game_id, game_settings, active_games_ref)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _run_actual_simulation(self) -> Dict:
        """Run the actual Hunger Games simulation by calling web_simulation.py."""
        try:
            # Get the path to the web_simulation.py file
            web_sim_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web_simulation.py')

            # Run the simulation
            result = subprocess.run([
                sys.executable, web_sim_path
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout

            if result.returncode == 0:
                # Parse the JSON output
                try:
                    # Find the JSON in the output (it should be at the end)
                    output_lines = result.stdout.strip().split('\n')
                    json_start = -1
                    for i, line in enumerate(output_lines):
                        if line.strip() == 'Simulation Results:':
                            json_start = i + 1
                            break

                    if json_start > 0 and json_start < len(output_lines):
                        json_output = '\n'.join(output_lines[json_start:])
                        parsed_result = json.loads(json_output)
                        return parsed_result
                    else:
                        # Fallback: try to parse the entire output as JSON
                        return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'winner': 'Unknown',
                        'stats': {'raw_output': result.stdout[-500:]}  # Last 500 chars
                    }
            else:
                return {
                    'success': False,
                    'error': f'Simulation failed: {result.stderr}'
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Simulation timed out after 5 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error running simulation: {str(e)}'
            }

    def _parse_simulation_output(self, output: str) -> Dict:
        """Parse the simulation output to extract winner and stats."""
        try:
            lines = output.split('\n')
            winner = "Unknown"
            stats = {}

            # Look for winner in the output
            for line in lines:
                line = line.strip()
                if 'winner' in line.lower() or 'victor' in line.lower():
                    # Try to extract the winner name
                    if ':' in line:
                        winner = line.split(':')[-1].strip()
                    else:
                        winner = line
                    break

            # Basic stats
            stats = {
                'total_tributes': 24,  # Default, could be improved
                'days_survived': 7,    # Default, could be improved
                'simulation_output': output[-1000:]  # Last 1000 chars for debugging
            }

            return {
                'success': True,
                'winner': winner,
                'stats': stats
            }

        except Exception as e:
            return {
                'success': True,  # Still consider it successful even if parsing fails
                'winner': 'Unknown',
                'stats': {'error': str(e)}
            }

    def _run_actual_simulation_streaming(self, game_id: str, game_settings: Dict, active_games_ref: Dict[str, dict]) -> Dict:
        """Run the actual Hunger Games simulation with file-based output monitoring."""
        try:
            # Get the path to the main.py file
            main_sim_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py')

            # Set environment variables for game settings
            env = os.environ.copy()
            env['HUNGER_GAMES_PHASE_DELAY'] = str(game_settings.get('phase_delay_seconds', 3))
            env['HUNGER_GAMES_PROGRESSION_MODE'] = game_settings.get('progression_mode', 'auto')

            # Get the main project directory (parent of web directory)
            main_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Run main.py normally (no --web flag)
            process = subprocess.Popen([
                sys.executable, main_sim_path
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=main_project_dir, env=env)

            # Monitor the web output file for updates
            web_output_file = os.path.join(main_project_dir, 'data', 'web_output.json')
            last_update_time = 0

            while process.poll() is None:  # While process is still running
                if os.path.exists(web_output_file):
                    try:
                        with open(web_output_file, 'r') as f:
                            data = json.load(f)

                        # Check if this is a new update
                        update_time = data.get('timestamp', 0)
                        if update_time > last_update_time:
                            last_update_time = update_time

                            # Update the game's output stream
                            if game_id in active_games_ref:
                                active_games_ref[game_id]['output_stream'].append({
                                    'timestamp': data['timestamp'],
                                    'message': data['message'],
                                    'status': data['status'],
                                    'game_data': data['game_data']
                                })

                                # Update game status
                                if data['status'] == 'completed':
                                    active_games_ref[game_id]['status'] = 'completed'
                                    active_games_ref[game_id]['results'] = data['game_data']
                                elif data['status'] == 'running':
                                    active_games_ref[game_id]['status'] = 'running'

                    except (json.JSONDecodeError, KeyError) as e:
                        # File might be partially written, skip this update
                        pass

                # Wait a bit before checking again
                import time
                time.sleep(0.5)

            # Wait for process to complete
            returncode = process.wait()

            if returncode == 0:
                return {
                    'success': True,
                    'message': 'Simulation completed successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Simulation failed with return code {returncode}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Simulation error: {str(e)}'
            }

    def get_game_result(self, game_id: str) -> Optional[Dict]:
        """Get the result of a completed game."""
        return self.game_results.get(game_id)

# Global instance
game_runner = WebGameRunner()