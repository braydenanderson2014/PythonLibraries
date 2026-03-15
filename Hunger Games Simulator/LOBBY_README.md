# Hunger Games Lobby System

A real-time multiplayer lobby system for the Hunger Games Simulator using FastAPI and Socket.IO.

## Features

- **Real-time Lobby Management**: Players can join/leave lobbies with live updates
- **Ready System**: Players mark themselves as ready before starting
- **Host Controls**: Lobby host can start the game when all players are ready
- **Web Interface**: Browser-based lobby with live updates
- **Command-line Client**: Alternative client for testing/scripting
- **Game Integration**: Automatically launches simulator when game starts

## Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn python-socketio
```

### 2. Start the Lobby Server
```bash
python lobby_server.py
```

### 3. Open in Browser
Navigate to: http://localhost:8000

### 4. Alternative: Use Command-line Client
```bash
python lobby_client.py
```

## Architecture

### Server Components
- **FastAPI**: Web framework for HTTP endpoints
- **Socket.IO**: Real-time bidirectional communication
- **Lobby Manager**: Handles lobby state and player management
- **Game Integration**: Launches simulator in web mode

### Client Options
1. **Web Client**: Full browser interface with real-time updates
2. **Command-line Client**: Simple text-based client for testing

## API Events

### Server → Client
- `lobby_joined`: Player successfully joined a lobby
- `lobby_updated`: Lobby state changed (players, ready status)
- `game_started`: Game has begun
- `game_update`: Live game simulation updates

### Client → Server
- `join_lobby`: Join/create a lobby
- `toggle_ready`: Toggle ready status
- `start_game`: Start the game (host only)

## Game Integration

When a game starts:
1. Server launches the simulator in web mode
2. Simulator outputs to `data/web_output.json`
3. Server monitors the file and broadcasts updates to all players
4. Real-time game events are sent to all connected clients

## Configuration

The lobby system uses the existing `settings.json` file:

```json
{
  "web_settings": {
    "host": "localhost",
    "port": 8000,
    "max_connections": 100,
    "update_interval": 0.1
  }
}
```

## Testing

Run the test suite:
```bash
python test_lobby.py
```

This will:
- Start the lobby server
- Test web mode integration
- Verify output routing

## Development

### Adding New Features
- Lobby events: Add to `lobby_server.py` socket handlers
- Game integration: Modify the `run_game_simulation` function
- Client features: Update both web and command-line clients

### Scaling
For production use, consider:
- Database for persistent lobbies
- Redis for session management
- Load balancer for multiple server instances
- Authentication system

## Example Usage

### Web Client
1. Open http://localhost:8000
2. Enter your name
3. Wait for others to join
4. Click "Toggle Ready"
5. Host clicks "Start Game" when all ready

### Command-line Client
```python
from lobby_client import LobbyClient
import asyncio

async def main():
    client = LobbyClient()
    await client.connect()
    await client.join_lobby("PlayerName")
    await client.toggle_ready()
    # Game will start automatically when host initiates
```

## Troubleshooting

### Server Won't Start
- Ensure port 8000 is available
- Check that `static/` directory exists
- Verify all dependencies are installed

### Web Mode Not Working
- Check `data/web_output.json` permissions
- Ensure simulator can write to the file
- Verify settings.json has correct web configuration

### Connection Issues
- Check firewall settings
- Verify server is running on correct host/port
- Try localhost vs 127.0.0.1 vs 0.0.0.0</content>
<parameter name="filePath">/workspaces/SystemCommands/Hunger Games Simulator/LOBBY_README.md