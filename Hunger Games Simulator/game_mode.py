#!/usr/bin/env python3
"""
Game Mode Manager for Hunger Games Simulator
Allows switching between console and web modes, and managing settings.
"""

import sys
import json
from utils.settings_manager import settings_manager
from utils.output_manager import output_manager

def print_usage():
    """Print usage information."""
    print("Hunger Games Simulator - Game Mode Manager")
    print("=" * 50)
    print("Usage: python game_mode.py [command] [options]")
    print()
    print("Commands:")
    print("  status          Show current game mode and settings")
    print("  set-mode MODE   Set game mode (console/web)")
    print("  set-setting KEY VALUE  Set a specific setting")
    print("  get-setting KEY        Get a specific setting")
    print("  reset-settings         Reset all settings to defaults")
    print("  test-output            Test output routing")
    print("  help                   Show this help")
    print()
    print("Examples:")
    print("  python game_mode.py set-mode web")
    print("  python game_mode.py set-setting tribute_settings.max_tributes 48")
    print("  python game_mode.py get-setting game_mode")
    print("  python game_mode.py test-output")

def show_status():
    """Show current status."""
    print("Current Game Mode:", settings_manager.get_game_mode().upper())
    print("Settings File:", settings_manager.settings_file)
    print()
    print("Key Settings:")
    print(f"  Max Tributes: {settings_manager.get_max_tributes()}")
    print(f"  Max Per District: {settings_manager.get_max_per_district()}")
    print(f"  Gender Balance: {settings_manager.enforce_gender_balance()}")
    print(f"  Base Phase Delay: {settings_manager.get_phase_delay('base_delay')}s")
    print(f"  Web Output File: {settings_manager.get_web_output_file()}")
    print(f"  Verbose Logging: {settings_manager.verbose_logging_enabled()}")

def set_game_mode(mode):
    """Set the game mode."""
    if mode not in ['console', 'web']:
        print(f"Error: Invalid mode '{mode}'. Must be 'console' or 'web'")
        return False

    settings_manager.set('game_mode', mode)
    print(f"Game mode set to: {mode.upper()}")
    return True

def set_setting(key, value):
    """Set a specific setting."""
    try:
        # Try to parse as JSON first (for complex values)
        parsed_value = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        # If not JSON, treat as string and try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            parsed_value = value.lower() == 'true'
        elif value.isdigit():
            parsed_value = int(value)
        elif value.replace('.', '').isdigit():
            parsed_value = float(value)
        else:
            parsed_value = value

    settings_manager.set(key, parsed_value)
    print(f"Setting '{key}' set to: {parsed_value}")

def get_setting(key):
    """Get a specific setting."""
    value = settings_manager.get(key)
    if value is not None:
        print(f"{key}: {value}")
    else:
        print(f"Setting '{key}' not found")

def reset_settings():
    """Reset all settings to defaults."""
    import os
    if os.path.exists(settings_manager.settings_file):
        os.remove(settings_manager.settings_file)
    # Reload settings (this will create defaults)
    settings_manager._load_settings()
    settings_manager.save_settings()
    print("Settings reset to defaults")

def test_output():
    """Test output routing."""
    print("Testing output routing...")
    print(f"Current mode: {settings_manager.get_game_mode().upper()}")

    output_manager.output_message("Test message 1")
    output_manager.output_message("Test message 2", {"test": "data"})
    output_manager.output_message("Test message 3")

    if settings_manager.is_web_mode():
        print(f"Check web output file: {settings_manager.get_web_output_file()}")

    print("Output test complete!")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == 'status':
        show_status()
    elif command == 'set-mode':
        if len(sys.argv) < 3:
            print("Error: Please specify mode (console/web)")
            return
        set_game_mode(sys.argv[2])
    elif command == 'set-setting':
        if len(sys.argv) < 4:
            print("Error: Please specify key and value")
            return
        set_setting(sys.argv[2], sys.argv[3])
    elif command == 'get-setting':
        if len(sys.argv) < 3:
            print("Error: Please specify key")
            return
        get_setting(sys.argv[2])
    elif command == 'reset-settings':
        reset_settings()
    elif command == 'test-output':
        test_output()
    elif command == 'help':
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == '__main__':
    main()