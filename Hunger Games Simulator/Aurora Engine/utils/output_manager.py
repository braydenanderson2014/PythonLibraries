"""
Output Manager for Hunger Games Simulator
Handles routing output to console, web, or other destinations based on game mode.
"""

import json
import os
import time
from typing import Dict, Any, Optional
from utils.settings_manager import settings_manager

class OutputManager:
    """Manages output routing for different game modes."""

    def __init__(self):
        self.settings = settings_manager
        self.log_file = None
        self._latest_game_data = {}  # Cache for latest comprehensive game data
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging if enabled."""
        if self.settings.verbose_logging_enabled():
            log_file = self.settings.get_log_file()
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                self.log_file = open(log_file, 'a')
            except IOError as e:
                print(f"Warning: Could not open log file {log_file}: {e}")

    def output_message(self, message: str, game_data: Optional[Dict[str, Any]] = None) -> None:
        """Output a message based on the current game mode."""
        mode = self.settings.get_game_mode()

        # Cache game_data if provided (for comprehensive data)
        if game_data:
            self._latest_game_data = game_data.copy()

        if mode == 'web':
            # Use provided game_data, or fall back to cached data
            data_to_use = game_data if game_data else self._latest_game_data
            self._output_to_web(message, data_to_use)
        else:  # console mode
            self._output_to_console(message)

        # Also log if verbose logging is enabled
        if self.settings.verbose_logging_enabled() and self.log_file:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] {message}\n"
            try:
                self.log_file.write(log_entry)
                self.log_file.flush()
            except IOError:
                pass  # Silently fail if logging fails

    def _output_to_console(self, message: str) -> None:
        """Output message to console."""
        print(message)

    def _output_to_web(self, message: str, game_data: Optional[Dict[str, Any]] = None) -> None:
        """Output message to web/live game system."""
        output_file = self.settings.get_web_output_file()

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Create base output structure
        output = {
            'timestamp': time.time(),
            'message': message,
        }

        # If we have game_data, flatten it to top level for server compatibility
        if game_data:
            output.update(game_data)
        else:
            # Use cached data if available
            output.update(self._latest_game_data)

        print(f"DEBUG: Writing to web output: {message[:50]}... with keys: {list(output.keys())}")

        try:
            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2)
        except Exception as e:
            # Fallback to console if web output fails
            print(f"Warning: Could not write web output: {e}")
            print(message)

    def clear_web_output(self) -> None:
        """Clear the web output file."""
        if self.settings.is_web_mode():
            output_file = self.settings.get_web_output_file()
            try:
                if os.path.exists(output_file):
                    print(f"DEBUG: Clearing web output file: {output_file}")
                    os.remove(output_file)
                else:
                    print(f"DEBUG: Web output file does not exist: {output_file}")
            except Exception as e:
                print(f"Warning: Could not clear web output: {e}")

    def write_game_state(self, game_state_data: Dict[str, Any]) -> None:
        """Write complete game state for web consumption."""
        if self.settings.is_web_mode():
            output_file = self.settings.get_web_output_file()
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            output = {
                'timestamp': time.time(),
                'status': 'game_state',
            }
            # Flatten game_state_data to top level
            output.update(game_state_data)

            try:
                with open(output_file, 'w') as f:
                    json.dump(output, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not write game state: {e}")

    def close(self) -> None:
        """Clean up resources."""
        if self.log_file:
            try:
                self.log_file.close()
            except IOError:
                pass

# Global output manager instance
output_manager = OutputManager()