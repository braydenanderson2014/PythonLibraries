// Hunger Games Spectator Lobby - Spectator Page JavaScript

console.log('spectator_lobby.js loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('spectator_lobby.js DOMContentLoaded');
    const socket = window.lobbyApp.socket;

    // Debug socket connection
    console.log('Socket object:', socket);
    console.log('Socket connected on page load:', socket.connected);

    socket.on('connect', () => {
        console.log('Socket connected event fired');
    });

    socket.on('disconnect', () => {
        console.log('Socket disconnected event fired');
    });

    // DOM elements
    const loginSection = document.getElementById('login-section');
    const lobbySelectionSection = document.getElementById('lobby-selection-section');
    const spectatorSection = document.getElementById('spectator-section');

    const playerNameInput = document.getElementById('player-name');
    const joinSpectatorBtn = document.getElementById('join-spectator-btn');
    const refreshLobbiesBtn = document.getElementById('refresh-lobbies-btn');
    const selectedLobbyName = document.getElementById('selected-lobby-name');
    const selectedLobbyDetails = document.getElementById('selected-lobby-details');

    let currentPlayerId = null;
    let currentLobbyId = null;
    let selectedLobbyId = null;
    let selectedLobbyData = null;
    let isListingLobbies = false;

    // Socket event handlers
    socket.on('spectator_joined', (data) => {
        console.log('Spectator joined:', data);
        currentPlayerId = data.player_id;
        currentLobbyId = data.lobby_id;
        // Note: Don't set window.lobbyApp.currentPlayerId/currentLobbyId for spectators
        // as this would interfere with other tabs (like admin tabs)

        // Switch to spectator view
        window.lobbyApp.showSection('spectator-section');

        // Update spectator display with lobby info
        updateSpectatorDisplay(data.lobby);
    });

    socket.on('game_started', (data) => {
        console.log('Game started for spectator:', data);

        // Fetch all tribute stats for spectators
        if (data.fetch_tribute_stats && currentLobbyId) {
            fetchSpectatorTributeStats();
        }

        // Update spectator display to show game is in progress
        updateSpectatorGameStatus(true);
    });

    socket.on('lobby_list', (data) => {
        console.log('Received lobby_list event with raw data:', data);
        console.log('data.lobbies:', data.lobbies);
        console.log('typeof data.lobbies:', typeof data.lobbies);
        console.log('data.lobbies is array:', Array.isArray(data.lobbies));
        console.log('data.lobbies length:', data.lobbies ? data.lobbies.length : 'null/undefined');
        isListingLobbies = false;
        updateLobbyList(data.lobbies);
    });

    // Socket connection handlers
    socket.on('connect', () => {
        console.log('Spectator lobby: Socket connected');
    });

    socket.on('disconnect', () => {
        console.log('Spectator lobby: Socket disconnected');
        // If we were spectating a game, redirect to main lobby
        if (currentLobbyId) {
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
    });

    socket.on('lobby_closed', (data) => {
        console.log('Lobby closed:', data);
        window.lobbyApp.showNotification(data.reason || 'Lobby has been closed', 'error');
        resetToLobbySelection();
    });

    socket.on('error', (data) => {
        console.log('Error:', data);
        window.lobbyApp.showNotification(data.message || 'An error occurred', 'error');
    });

    socket.on('spectator_update', (data) => {
        console.log('Spectator update received:', data);
        updateSpectatorDisplay(data);
    });

    // UI event handlers
    window.joinAsSpectator = function() {
        const playerName = playerNameInput.value.trim();

        if (!selectedLobbyId) {
            window.lobbyApp.showNotification('Please select a lobby first', 'warning');
            return;
        }

        if (!playerName) {
            window.lobbyApp.showNotification('Please enter your name', 'warning');
            return;
        }

        if (playerName.length > 20) {
            window.lobbyApp.showNotification('Name too long (max 20 characters)', 'warning');
            return;
        }

        joinSpectatorBtn.disabled = true;
        joinSpectatorBtn.textContent = 'Joining as Spectator...';

        socket.emit('join_as_spectator', {
            lobby_id: selectedLobbyId,
            name: playerName
        });
    };

    window.backToLobbySelection = function() {
        window.lobbyApp.showSection('lobby-selection-section');
        selectedLobbyId = null;
        selectedLobbyData = null;
    };

    // Lobby selection functions
    function updateLobbyList(lobbies) {
        const lobbyList = document.getElementById('lobby-list');

        if (!Array.isArray(lobbies)) {
            console.error('lobbies is not an array:', lobbies);
            lobbyList.innerHTML = '<div class="error">Error loading lobbies</div>';
            return;
        }

        if (lobbies.length === 0) {
            lobbyList.innerHTML = '<div class="no-lobbies">No active lobbies available for spectating</div>';
            return;
        }

        lobbyList.innerHTML = lobbies.map(lobby => `
            <div class="lobby-item ${selectedLobbyId === lobby.id ? 'selected' : ''}" onclick="selectLobby('${lobby.id}', ${JSON.stringify(lobby).replace(/"/g, '&quot;')})">
                <div class="lobby-name">${lobby.name}</div>
                <div class="lobby-details">
                    Players: ${lobby.player_count}/${lobby.max_players} |
                    Host: ${lobby.host_name} |
                    Status: ${lobby.game_started ? 'In Game' : 'Waiting'}
                </div>
            </div>
        `).join('');
    }

    window.selectLobby = function(lobbyId, lobbyData) {
        selectedLobbyId = lobbyId;
        selectedLobbyData = lobbyData;

        // Update selected lobby info
        selectedLobbyName.textContent = lobbyData.name;
        selectedLobbyDetails.textContent = `Players: ${lobbyData.player_count}/${lobbyData.max_players} | Host: ${lobbyData.host_name} | Status: ${lobbyData.game_started ? 'In Game' : 'Waiting'}`;

        // Show login section
        window.lobbyApp.showSection('login-section');

        // Update lobby list to show selection
        updateLobbyList(document.querySelectorAll('.lobby-item').length ? Array.from(document.querySelectorAll('.lobby-item')).map(item => {
            const id = item.onclick.toString().match(/'([^']+)'/)[1];
            return { id, selected: id === lobbyId };
        }) : []);
    };

    window.listLobbies = function() {
        if (isListingLobbies) return;

        isListingLobbies = true;
        refreshLobbiesBtn.disabled = true;
        refreshLobbiesBtn.textContent = 'Loading...';

        socket.emit('list_lobbies');
    };

    // Initialize - try to list lobbies with retry logic
    function tryListLobbies() {
        console.log('Attempting to list lobbies, socket connected:', socket.connected);
        if (socket.connected) {
            console.log('Socket connected, listing lobbies');
            listLobbies();
        } else {
            console.log('Socket not connected yet, will retry...');
            setTimeout(tryListLobbies, 500);
        }
    }

    // Listen for connect event in case socket connects later
    socket.once('connect', () => {
        console.log('Socket connected event fired, listing lobbies');
        listLobbies();
    });

    // Try immediately
    console.log('Calling tryListLobbies() immediately');
    tryListLobbies();

    // Also try again after delays to ensure lobbies load
    setTimeout(() => {
        console.log('First retry: calling listLobbies() after 1 second');
        listLobbies();
    }, 1000);

    setTimeout(() => {
        console.log('Second retry: calling listLobbies() after 3 seconds');
        listLobbies();
    }, 3000);

    // Functions
    function updateSpectatorDisplay(lobby) {
        if (!lobby) return;

        // Update round (show as waiting or current round)
        const spectatorRound = document.getElementById('spectator-round');
        if (spectatorRound) {
            spectatorRound.textContent = lobby.game_started ? 'In Progress' : 'Waiting';
        }

        // Update game status
        const statusDiv = document.getElementById('spectator-game-status');
        if (statusDiv) {
            const aliveCount = lobby.players ? Object.values(lobby.players).filter(p => p.alive !== false).length : 0;
            const totalCount = lobby.players ? Object.keys(lobby.players).length : 0;

            statusDiv.innerHTML = `
                <div class="spectator-info">
                    <div>Lobby: ${lobby.name || 'Unknown'}</div>
                    <div>Alive: ${aliveCount}/${totalCount} tributes</div>
                    <div>Status: Game in progress</div>
                </div>
            `;
        } else {
            const playerCount = Object.keys(lobby.players || {}).length;
            const hostName = Object.values(lobby.players || {}).find(p => p.id === lobby.host_id)?.name || 'Unknown';

            statusDiv.innerHTML = `
                <div class="spectator-info">
                    <div>Lobby: ${lobby.name || 'Unknown'}</div>
                    <div>Players: ${playerCount}</div>
                    <div>Host: ${hostName}</div>
                    <div>Status: Waiting for Game to Start</div>
                </div>
            `;
        }

        // Update tributes
        const tributesContainer = document.getElementById('spectator-tributes-container');
        if (tributesContainer && lobby.players) {
            const players = Object.values(lobby.players);
            tributesContainer.innerHTML = players.map(player => `
                <div class="tribute-card ${player.id === lobby.host_id ? 'host-player' : ''}">
                    <div class="tribute-header">
                        <div class="tribute-name">${player.name}${player.id === lobby.host_id ? ' (Host)' : ''}</div>
                        <div class="tribute-district">District ${player.district || '?'}</div>
                    </div>
                    <div class="tribute-stats">
                        <div class="stat-row">
                            <span class="stat-label">Status:</span>
                            <span class="stat-value">${lobby.game_started ? (player.alive !== false ? 'Alive' : 'Dead') : (player.tribute_ready ? 'Ready' : 'Setting up')}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } else if (tributesContainer) {
            tributesContainer.innerHTML = '<div class="no-tributes">No players in lobby</div>';
        }
    }

    function resetToLobbySelection() {
        window.lobbyApp.showSection('lobby-selection-section');
        currentPlayerId = null;
        currentLobbyId = null;
        selectedLobbyId = null;
        selectedLobbyData = null;
        listLobbies();
    }

    async function fetchSpectatorTributeStats() {
        if (!currentLobbyId) return;

        try {
            const response = await fetch(`/api/tribute/spectator/${currentLobbyId}`);
            if (response.ok) {
                const data = await response.json();
                updateSpectatorTributeStats(data.tributes);
            }
        } catch (error) {
            console.error('Error fetching spectator tribute stats:', error);
        }
    }

    function updateSpectatorGameStatus(gameStarted) {
        const roundElement = document.getElementById('spectator-round');
        if (roundElement) {
            roundElement.textContent = gameStarted ? 'In Progress' : 'Waiting';
        }
    }

    function updateSpectatorTributeStats(tributes) {
        // Find or create the spectator stats container
        let spectatorStatsContainer = document.getElementById('spectator-tribute-stats');
        if (!spectatorStatsContainer) {
            const spectatorSection = document.getElementById('spectator-section');
            if (spectatorSection) {
                spectatorStatsContainer = document.createElement('div');
                spectatorStatsContainer.id = 'spectator-tribute-stats';
                spectatorStatsContainer.className = 'spectator-tribute-stats';
                // Insert at the top of the spectator section
                spectatorSection.insertBefore(spectatorStatsContainer, spectatorSection.firstChild);
            }
        }

        if (!spectatorStatsContainer) return;

        // Create HTML for all tributes
        const tributeCards = Object.values(tributes).map(tribute => {
            const skillsHtml = tribute.final_ratings ? Object.entries(tribute.final_ratings)
                .map(([skill, rating]) => `
                    <div class="spectator-skill">
                        <span class="skill-name">${skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
                        <span class="skill-rating">${rating}/10</span>
                    </div>
                `).join('') : '';

            return `
                <div class="spectator-tribute-card">
                    <div class="tribute-header">
                        <h3>${tribute.name}</h3>
                        <div class="tribute-info">
                            <span>District ${tribute.district}</span>
                            <span>${tribute.age} years old</span>
                            <span>${tribute.gender}</span>
                        </div>
                    </div>
                    <div class="tribute-skills">
                        ${skillsHtml}
                    </div>
                    ${tribute.district_bonuses && Object.keys(tribute.district_bonuses).length > 0 ?
                        `<div class="tribute-bonuses">
                            <strong>District Bonuses:</strong>
                            ${Object.entries(tribute.district_bonuses)
                                .filter(([skill, bonus]) => bonus !== 0)
                                .map(([skill, bonus]) => `<span class="bonus ${bonus > 0 ? 'positive' : 'negative'}">${skill}: ${bonus > 0 ? '+' : ''}${bonus}</span>`)
                                .join(', ')}
                        </div>` : ''}
                </div>
            `;
        }).join('');

        spectatorStatsContainer.innerHTML = `
            <h2>All Tribute Statistics</h2>
            <div class="spectator-tributes-grid">
                ${tributeCards}
            </div>
        `;
    }

    // Make functions global
    window.updateSpectatorDisplay = updateSpectatorDisplay;
    window.resetToLobbySelection = resetToLobbySelection;
    window.fetchSpectatorTributeStats = fetchSpectatorTributeStats;

    // Check for automatic joining on page load
    // Check URL parameters first, then template variables
    const urlParams = new URLSearchParams(window.location.search);
    const urlLobbyId = urlParams.get('lobby_id');
    
    // Check if lobby_id is provided as a template variable (from server)
    const templateLobbyId = window.spectatorLobbyId || 
                           document.body.getAttribute('data-lobby-id') || 
                           (window.lobbyData && window.lobbyData.lobby_id);
    
    const autoJoinLobbyId = urlLobbyId || templateLobbyId;
    
    if (autoJoinLobbyId) {
        console.log('Auto-joining spectator for lobby:', autoJoinLobbyId);
        // For spectator pages with lobby_id, just set the lobby ID and wait for updates
        // The spectator should already be joined from the lobby page
        currentLobbyId = autoJoinLobbyId;
        // Switch to spectator view immediately
        window.lobbyApp.showSection('spectator-section');
        // The spectator_update events will provide the game/lobby state
    } else {
        // No auto-join, show lobby selection
        listLobbies();
    }
});