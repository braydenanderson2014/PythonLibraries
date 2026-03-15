# Hunger Games Simulator - Settings & Game Mode System

This document explains how to use the new settings and game mode system for the Hunger Games Simulator.

## Overview

The simulator now supports two main modes:
- **Console Mode**: Outputs to terminal/console (default)
- **Web Mode**: Outputs to JSON files for web/live game consumption

Settings are controlled via a `settings.json` file and can be managed through the `game_mode.py` script.

## Game Modes

### Console Mode
- Default mode
- Outputs all game messages to the console
- Interactive prompts for tribute setup
- Full console output with delays between phases

### Web Mode
- Designed for web/live game integration
- Outputs game state to JSON files (`data/web_output.json`)
- Minimal console output (warnings/errors only)
- Fast phase transitions for real-time viewing

## Settings Configuration

The `settings.json` file controls all game parameters:

```json
{
  "game_mode": "console",
  "phase_delays": {
    "base_delay": 3.0,
    "morning": 1.0,
    "afternoon": 1.2,
    "evening": 1.5,
    "environmental": 2.0,
    "randomness": 0.25,
    "progression_factor": 0.05
  },
  "tribute_settings": {
    "max_tributes": 24,
    "max_per_district": 2,
    "enforce_gender_balance": true,
    "allow_custom_tributes": true,
    "districts": 12
  },
  "game_rules": {
    "context_filter_enabled": true,
    "work_friendly_mode": true,
    "auto_save_enabled": true,
    "sponsor_gifts_enabled": true,
    "alliances_enabled": true,
    "sanity_decay_enabled": true
  },
  "output_settings": {
    "web_output_file": "data/web_output.json",
    "log_file": "data/game_log.txt",
    "verbose_logging": false,
    "real_time_updates": true
  },
  "difficulty_settings": {
    "arena_event_frequency": 0.02,
    "resource_decay_rate": 1.0,
    "combat_lethality": 1.0,
    "environmental_harshness": 1.0
  },
  "web_settings": {
    "host": "localhost",
    "port": 8080,
    "max_connections": 100,
    "update_interval": 0.1
  }
}
```

## Using the Game Mode Manager

The `game_mode.py` script provides a command-line interface for managing settings and modes:

### Check Current Status
```bash
python game_mode.py status
```

### Switch Game Modes
```bash
# Switch to web mode
python game_mode.py set-mode web

# Switch to console mode
python game_mode.py set-mode console
```

### Modify Settings
```bash
# Set max tributes to 48
python game_mode.py set-setting tribute_settings.max_tributes 48

# Disable gender balance enforcement
python game_mode.py set-setting tribute_settings.enforce_gender_balance false

# Change base phase delay to 5 seconds
python game_mode.py set-setting phase_delays.base_delay 5.0
```

### Get Specific Settings
```bash
python game_mode.py get-setting game_mode
python game_mode.py get-setting tribute_settings.max_tributes
```

### Reset Settings
```bash
python game_mode.py reset-settings
```

### Test Output Routing
```bash
python game_mode.py test-output
```

## Web Mode Integration

When in web mode, the simulator outputs to `data/web_output.json` with this structure:

```json
{
  "timestamp": 1760375868.5946686,
  "status": "running",
  "message": "Game message here",
  "game_data": {
    "day": 1,
    "phase": "morning",
    "active_tributes": 24,
    // ... additional game state data
  }
}
```

Your web application can:
1. Monitor the JSON file for changes
2. Parse the `message` field for game events
3. Use `game_data` for real-time statistics
4. Handle different `status` values (running, completed, etc.)

## Running the Simulator

The simulator automatically uses the current settings:

```bash
# Run with current settings (console mode by default)
python main.py --tributes 24

# Run in fast mode (reduced delays)
python main.py --tributes 24 --fast
```

## Key Settings Explained

### Tribute Settings
- `max_tributes`: Maximum number of tributes (24 default)
- `max_per_district`: Maximum tributes per district (2 default)
- `enforce_gender_balance`: Ensure 1 male/1 female per district
- `districts`: Number of districts (12 default)

### Phase Delays
- `base_delay`: Base seconds between phases (3.0 default)
- `morning/afternoon/evening/environmental`: Multipliers for each phase
- `randomness`: Random variation in delays (±25% default)
- `progression_factor`: How much delays speed up as game progresses

### Game Rules
- `context_filter_enabled`: Enable work-friendly content filtering
- `sanity_decay_enabled`: Enable sanity decay over time
- `sponsor_gifts_enabled`: Allow sponsor gifts
- `alliances_enabled`: Allow tribute alliances

### Output Settings
- `verbose_logging`: Enable detailed logging to file
- `real_time_updates`: Enable real-time output updates

## Environment Variables (Legacy)

The system still supports some environment variables for backward compatibility:

- `HUNGER_GAMES_PROGRESSION_MODE`: Set to 'web' for web mode
- `HUNGER_GAMES_PHASE_DELAY`: Override base phase delay

However, it's recommended to use the settings file instead.