// Hunger Games Lobby - Lobby Page JavaScript

console.log('lobby.js loaded');

// Global error handler
window.addEventListener('error', (event) => {
    console.error('[GLOBAL ERROR]', event.error || event.message);
    console.error('Filename:', event.filename);
    console.error('Line:', event.lineno, 'Col:', event.colno);
    if (event.error && event.error.stack) {
        console.error('Stack:', event.error.stack);
    }
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    console.error('[UNHANDLED PROMISE REJECTION]', event.reason);
    if (event.reason && event.reason.stack) {
        console.error('Stack:', event.reason.stack);
    }
});

// ============================================================================
// GLOBAL UI FUNCTIONS - Available immediately for onclick handlers
// ============================================================================

window.showCreateLobbyForm = function() {
    const createLobbyForm = document.getElementById('create-lobby-form');
    const createLobbyBtn = document.getElementById('create-lobby-btn');
    const lobbyNameInput = document.getElementById('lobby-name');
    if (createLobbyForm) {
        createLobbyForm.style.display = 'block';
        createLobbyBtn.style.display = 'none';
        if (lobbyNameInput) lobbyNameInput.focus();
    }
};

window.hideCreateLobbyForm = function() {
    const createLobbyForm = document.getElementById('create-lobby-form');
    const createLobbyBtn = document.getElementById('create-lobby-btn');
    const lobbyNameInput = document.getElementById('lobby-name');
    if (createLobbyForm) {
        createLobbyForm.style.display = 'none';
        createLobbyBtn.style.display = 'inline-block';
        if (lobbyNameInput) lobbyNameInput.value = '';
    }
};

window.createLobby = function() {
    const adminName = document.getElementById('admin-name').value.trim();
    const lobbyName = document.getElementById('lobby-name').value.trim();
    const maxPlayersSelect = document.getElementById('max-players');
    const maxPlayers = maxPlayersSelect ? parseInt(maxPlayersSelect.value) : 24;
    const socket = window.lobbyApp.socket;

    if (!adminName) {
        window.lobbyApp.showNotification('Please enter your name', 'warning');
        return;
    }

    if (adminName.length > 20) {
        window.lobbyApp.showNotification('Your name is too long (max 20 characters)', 'warning');
        return;
    }

    if (!lobbyName) {
        window.lobbyApp.showNotification('Please enter a lobby name', 'warning');
        return;
    }

    if (lobbyName.length > 50) {
        window.lobbyApp.showNotification('Lobby name too long (max 50 characters)', 'warning');
        return;
    }

    socket.emit('create_lobby', {
        name: lobbyName,
        max_players: maxPlayers,
        player_name: adminName
    });

    window.hideCreateLobbyForm();
};

window.listLobbies = function() {
    const socket = window.lobbyApp ? window.lobbyApp.socket : null;
    if (!socket) {
        console.log('Socket not available yet, skipping listLobbies');
        return;
    }
    
    const lobbyList = document.getElementById('lobby-list');
    if (!lobbyList) return;

    console.log('listLobbies called - emitting list_lobbies event to server, socket connected:', socket.connected);
    lobbyList.innerHTML = '<div class="loading">Loading lobbies...</div>';
    socket.emit('list_lobbies');
    console.log('list_lobbies event emitted to server');
};

window.selectLobby = function(lobbyId, lobbyData) {
    const selectedLobbyName = document.getElementById('selected-lobby-name');
    const selectedLobbyDetails = document.getElementById('selected-lobby-details');
    
    if (!window.lobbyPageState) {
        window.lobbyPageState = {};
    }
    window.lobbyPageState.selectedLobbyId = lobbyId;
    window.lobbyPageState.selectedLobbyData = lobbyData;
    
    // Update URL to preserve state
    window.updatePageURL(`lobby:${lobbyId}`);

    if (selectedLobbyName) selectedLobbyName.textContent = lobbyData.name;
    if (selectedLobbyDetails) {
        selectedLobbyDetails.innerHTML = `
            <div>Players: ${lobbyData.player_count}/${lobbyData.max_players}</div>
            <div>Status: Waiting for players</div>
            <div>Created by ${lobbyData.host_name}${lobbyData.created_at ? ' - ' + new Date(lobbyData.created_at).toLocaleString() : ''}</div>
        `;
    }

    // Show/hide spectator button based on player count
    const spectatorBtn = document.getElementById('join-spectator-btn');
    if (spectatorBtn) {
        spectatorBtn.style.display = lobbyData.player_count > 0 ? 'inline-block' : 'none';
    }

    // Switch to login section
    if (window.lobbyApp) window.lobbyApp.showSection('login-section');
};

window.backToLobbySelection = function() {
    if (!window.lobbyPageState) {
        window.lobbyPageState = {};
    }
    window.lobbyPageState.selectedLobbyId = null;
    window.lobbyPageState.selectedLobbyData = null;
    
    // Update URL back to lobby selection
    window.updatePageURL('lobbies');
    
    if (window.lobbyApp) {
        window.lobbyApp.showSection('lobby-selection-section');
    }
    window.listLobbies();
};

// ============================================================================
// URL STATE MANAGEMENT - Preserve state in URL for session recovery
// ============================================================================

window.updatePageURL = function(state) {
    /**
     * Update the browser URL to reflect the current state
     * This allows session recovery on disconnect/reload
     */
    let newUrl = '/';
    
    if (state === 'lobbies') {
        newUrl = '/';
    } else if (state.startsWith('lobby:')) {
        const lobbyId = state.split(':')[1];
        newUrl = `/lobby/${lobbyId}`;
    } else if (state.startsWith('waiting:')) {
        const lobbyId = state.split(':')[1];
        newUrl = `/lobby/${lobbyId}/waiting`;
    }
    
    // Only update if URL actually changed to avoid excessive state entries
    if (window.location.pathname !== newUrl) {
        window.history.pushState({ state: state }, '', newUrl);
        console.log('[URL STATE] Updated URL to:', newUrl);
    }
};

window.restoreStateFromURL = function() {
    /**
     * Check current URL and return what state we should be in
     * Used on page load to restore disconnected sessions
     */
    const path = window.location.pathname;
    console.log('[URL STATE] Restoring state from URL:', path);
    
    if (path === '/') {
        return { type: 'lobbies' };
    } else if (path.startsWith('/lobby/')) {
        const parts = path.split('/');
        if (parts.length === 3 && parts[2]) {
            // /lobby/{lobbyId}
            const lobbyId = parts[2];
            return { type: 'lobby', lobbyId: lobbyId };
        } else if (parts.length === 4 && parts[3] === 'waiting') {
            // /lobby/{lobbyId}/waiting
            const lobbyId = parts[2];
            return { type: 'waiting', lobbyId: lobbyId };
        }
    }
    return { type: 'lobbies' };
};

window.handlePopState = function(event) {
    /**
     * Handle browser back/forward button
     */
    console.log('[URL STATE] popstate event:', event.state);
};

// Listen for back/forward navigation
window.addEventListener('popstate', window.handlePopState);

// ============================================================================
// MAIN INITIALIZATION
// ============================================================================

// Initialize global state
if (!window.lobbyPageState) {
    window.lobbyPageState = {
        selectedLobbyId: null,
        selectedLobbyData: null,
        isListingLobbies: false
    };
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('lobby.js DOMContentLoaded');
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
    const tributeSection = document.getElementById('tribute-section');
    const lobbySection = document.getElementById('lobby-section');
    const gameSection = document.getElementById('game-section');

    const playerNameInput = document.getElementById('player-name');
    const resumeCodeInput = document.getElementById('resume-code');
    const joinBtn = document.getElementById('join-btn');
    const startBtn = document.getElementById('start-btn');
    const leaveBtn = document.getElementById('leave-btn');

    const lobbyList = document.getElementById('lobby-list');
    const createLobbyBtn = document.getElementById('create-lobby-btn');
    const refreshLobbiesBtn = document.getElementById('refresh-lobbies-btn');
    const createLobbyForm = document.getElementById('create-lobby-form');
    const lobbyNameInput = document.getElementById('lobby-name');
    const maxPlayersSelect = document.getElementById('max-players');
    const selectedLobbyName = document.getElementById('selected-lobby-name');
    const selectedLobbyDetails = document.getElementById('selected-lobby-details');

    const tributeDistrictSelect = document.getElementById('tribute-district');
    const tributeGenderSelect = document.getElementById('tribute-gender');
    const tributeAgeInput = document.getElementById('tribute-age');
    const tributeNameInput = document.getElementById('tribute-name');
    const tributeWeaponSelect = document.getElementById('tribute-weapon');
    const tributeDoneBtn = document.getElementById('tribute-done-btn');
    const tributeNotDoneBtn = document.getElementById('tribute-not-done-btn');

    // Skill system elements
    const availableSkillsList = document.getElementById('available-skills');
    const skillOrderList = document.getElementById('skill-order-list');
    const skillRatingsPreview = document.getElementById('skill-ratings-preview');
    const districtBonusesDiv = document.getElementById('district-bonuses');

    const lobbyTitle = document.getElementById('lobby-title');
    const lobbyInfo = document.getElementById('lobby-info');
    const playersList = document.getElementById('players-list');
    const tributeStatus = document.getElementById('tribute-status');
    const tributeProgress = document.getElementById('tribute-progress');

    const gameStatus = document.getElementById('game-status');
    const gameLog = document.getElementById('game-log');

    let currentPlayerId = null;
    let currentLobbyId = null;
    let isHost = false;
    let currentTributeData = null;
    let draggedElement = null;
    let tributeStatsInterval = null;
    let districtConfig = null;
    let weaponsData = null;

    // Load district bonuses configuration
    async function loadDistrictConfig() {
        try {
            const response = await fetch('/api/district-bonuses');
            if (response.ok) {
                districtConfig = await response.json();
                console.log('District config loaded:', districtConfig);
                updateDistrictSelectOptions();
            }
        } catch (error) {
            console.error('Error loading district config:', error);
        }
    }

    // Load weapons configuration
    async function loadWeapons() {
        try {
            const response = await fetch('/api/weapons');
            if (response.ok) {
                const data = await response.json();
                weaponsData = data.weapons;
                console.log('Weapons loaded:', weaponsData);
                populateWeaponDropdown();
            }
        } catch (error) {
            console.error('Error loading weapons:', error);
        }
    }

    // Populate weapon dropdown
    function populateWeaponDropdown() {
        const weaponSelect = document.getElementById('tribute-weapon');
        if (!weaponSelect || !weaponsData) return;

        weaponSelect.innerHTML = '';
        
        // Convert weapons object to array and sort by name
        const weaponsList = Object.entries(weaponsData).map(([id, weapon]) => ({
            id,
            ...weapon
        })).sort((a, b) => a.name.localeCompare(b.name));

        weaponsList.forEach(weapon => {
            const option = document.createElement('option');
            option.value = weapon.id;
            option.textContent = `${weapon.name} (Damage: ${weapon.base_damage}, Type: ${weapon.weapon_type})`;
            weaponSelect.appendChild(option);
        });
        
        // Default to fists
        weaponSelect.value = 'fists';
    }

    // Socket event handlers
    socket.on('lobby_joined', (data) => {
        console.log('Joined lobby:', data);
        currentPlayerId = data.player_id;
        currentLobbyId = data.lobby_id;
        window.lobbyApp.currentPlayerId = currentPlayerId;
        window.lobbyApp.currentLobbyId = currentLobbyId;
        
        // Update URL to preserve state
        window.updatePageURL(`lobby:${currentLobbyId}`);

        // Switch to tribute creation view
        window.lobbyApp.showSection('tribute-section');

        // Update available districts immediately
        if (data.available_districts) {
            updateAvailableDistricts(data.available_districts);
        }

        // Load existing tribute data if any
        if (data.player && data.player.tribute_data) {
            loadTributeData(data.player.tribute_data);
        }

        // Initialize drag and drop after switching to tribute section
        setTimeout(() => {
            initializeDragAndDrop();
            updateSkillPreview();
        }, 100);

        // Show resume code if provided
        if (data.resume_code) {
            showResumeCode(data.resume_code);
        }
    });

    socket.on('lobby_updated', (data) => {
        try {
            const lobby = data.lobby;
            const availableDistricts = data.available_districts || [];

            // Update available districts in the tribute form
            updateAvailableDistricts(availableDistricts);

            // Check if we should be in waiting state (if we have a tribute ready)
            const currentPlayer = lobby.players[currentPlayerId];
            if (currentPlayer && currentPlayer.tribute_ready) {
                console.log('[URL STATE] Player tribute is ready, checking if we need to update URL');
                
                // If we're still in tribute section but our tribute is ready, switch to lobby
                const tributeSection = document.getElementById('tribute-section');
                if (tributeSection && tributeSection.style.display !== 'none') {
                    console.log('[URL STATE] Switching from tribute section to lobby section');
                    window.lobbyApp.showSection('lobby-section');
                }
                
                // ALWAYS update URL to waiting state when tribute is ready
                // Use lobby.id from server data (always accurate)
                const lobbyId = lobby.id || currentLobbyId;
                const currentPath = window.location.pathname;
                const expectedPath = `/lobby/${lobbyId}/waiting`;
                
                if (currentPath !== expectedPath) {
                    console.log('[URL STATE] Updating URL to waiting state for lobby:', lobbyId);
                    window.updatePageURL(`waiting:${lobbyId}`);
                } else {
                    console.log('[URL STATE] Already at correct waiting URL:', expectedPath);
                }
            } else {
                console.log('[URL STATE] Player tribute not ready yet');
            }

            updateLobby(lobby);
        } catch (error) {
            console.error('[ERROR] lobby_updated handler failed:', error);
            console.error('Stack:', error.stack);
        }
    });

    socket.on('lobby_closed', (data) => {
        console.log('Lobby closed:', data);
        window.lobbyApp.showNotification(data.reason || 'Lobby has been closed', 'error');
        resetToLogin();
    });

    socket.on('tribute_updated', (data) => {
        try {
            console.log('Tribute updated:', data);
            currentTributeData = data.tribute_data;
            window.lobbyApp.showNotification('Tribute updated successfully', 'success');
        } catch (error) {
            console.error('[ERROR] tribute_updated handler failed:', error);
        }
    });

    socket.on('game_starting', (data) => {
        try {
            console.log('Game starting event received:', data);
            console.log('Current location:', window.location.pathname);

            // Check if we're currently spectating (either on spectator page or spectator section visible)
            const isOnSpectatorPage = window.location.pathname.startsWith('/spectator');
            const spectatorSection = document.getElementById('spectator-section');
            const isSpectating = isOnSpectatorPage || (spectatorSection && spectatorSection.style.display !== 'none');
            console.log('Spectator check - isOnSpectatorPage:', isOnSpectatorPage, 'spectatorSection display:', spectatorSection ? spectatorSection.style.display : 'not found', 'isSpectating:', isSpectating);

            if (!isSpectating) {
                // DON'T do hard redirect - let app.js handle SPA navigation
                // Hard redirects disconnect the socket mid-game
                const lobbyId = data.lobby_id || (data.lobby && data.lobby.id) || currentLobbyId;
                console.log('Game starting - lobby ID:', lobbyId);
                console.log('✅ Allowing app.js to handle SPA navigation (no hard redirect)');
                // Let app.js handle the game page initialization via SPA
                // The game_starting event is also received there
            } else {
                console.log('Not redirecting - currently spectating');
            }
        } catch (error) {
            console.error('[ERROR] game_starting handler failed:', error);
            console.error('Stack:', error.stack);
        }
    });

    socket.on('game_started', (data) => {
        try {
            console.log('Game started event received:', data);
            console.log('Current location:', window.location.pathname);
            window.lobbyApp.gameStarted = true;

            // Stop tribute stats polling since game is starting
            stopTributeStatsPolling();

            // Fetch tribute stats if requested
            if (data.fetch_tribute_stats) {
                fetchTributeStats();
            }

            // Check if we're currently spectating (either on spectator page or spectator section visible)
            const isOnSpectatorPage = window.location.pathname.startsWith('/spectator');
            const spectatorSection = document.getElementById('spectator-section');
            const isSpectating = isOnSpectatorPage || (spectatorSection && spectatorSection.style.display !== 'none');
            console.log('Spectator check - isOnSpectatorPage:', isOnSpectatorPage, 'spectatorSection display:', spectatorSection ? spectatorSection.style.display : 'not found', 'isSpectating:', isSpectating);

            if (!isSpectating) {
                // DON'T do hard redirect - let app.js handle SPA navigation
                // Hard redirects disconnect the socket mid-game
                const lobbyId = data.lobby_id || (data.lobby && data.lobby.id);
                console.log('Game started - lobby ID:', lobbyId);
                console.log('✅ Allowing app.js to handle SPA navigation (no hard redirect)');
                // Let app.js handle the game page initialization via SPA
            } else {
                console.log('Not redirecting - currently spectating');
            }
        } catch (error) {
            console.error('[ERROR] game_started handler failed:', error);
            console.error('Stack:', error.stack);
        }
    });

    socket.on('game_start_failed', (data) => {
        console.log('Game start failed:', data);
        window.lobbyApp.showNotification(data.reason || 'Cannot start game', 'error');
    });

    socket.on('game_update', (data) => {
        console.log('Game update:', data);

        // Handle tribute stat updates
        if (data.message && data.message.type === 'tribute_stat_update') {
            handleTributeStatUpdate(data.message);
            return;
        }

        if (data.status === 'running' && data.message) {
            // Add to game log
            addToGameLog(data.message, data.timestamp);
        } else if (data.status === 'completed') {
            gameStatus.innerHTML = `<div class="game-completed">${data.message || 'Game completed!'}</div>`;
            window.lobbyApp.showNotification('Game has ended!', 'success');
        } else if (data.status === 'error') {
            gameStatus.innerHTML = `<div class="game-error">Error: ${data.message || 'Unknown error'}</div>`;
            if (spectatorSection && spectatorSection.style.display !== 'none') {
                document.getElementById('spectator-game-status').innerHTML = `<div class="game-error">Error: ${data.message || 'Unknown error'}</div>`;
            }
            window.lobbyApp.showNotification('Game error occurred', 'error');
        }
    });

    // Lobby management event handlers
    socket.on('lobby_list', (data) => {
        console.log('CLIENT: Received lobby_list event with raw data:', data);
        console.log('CLIENT: data.lobbies:', data.lobbies);
        console.log('CLIENT: typeof data.lobbies:', typeof data.lobbies);
        console.log('CLIENT: data.lobbies is array:', Array.isArray(data.lobbies));
        console.log('CLIENT: data.lobbies length:', data.lobbies ? data.lobbies.length : 'null/undefined');
        if (data.lobbies && data.lobbies.length > 0) {
            console.log('CLIENT: First lobby:', data.lobbies[0]);
        }
        window.lobbyPageState.isListingLobbies = false;
        updateLobbyList(data.lobbies);
    });

    socket.on('lobby_created', (data) => {
        console.log('Lobby created:', data);
        window.lobbyApp.showNotification(`Lobby "${data.lobby.name}" created successfully!`, 'success');

        // Since we're now automatically joined, update our state
        currentPlayerId = data.player_id;
        currentLobbyId = data.lobby_id;
        window.lobbyApp.currentPlayerId = currentPlayerId;
        window.lobbyApp.currentLobbyId = currentLobbyId;
        
        // Update URL to preserve state
        window.updatePageURL(`lobby:${currentLobbyId}`);

        // Switch to tribute creation view
        window.lobbyApp.showSection('tribute-section');

        // Update available districts immediately
        if (data.available_districts) {
            updateAvailableDistricts(data.available_districts);
        }

        // Load existing tribute data if any
        if (data.player && data.player.tribute_data) {
            loadTributeData(data.player.tribute_data);
        }

        // Initialize drag and drop after switching to tribute section
        setTimeout(() => {
            initializeDragAndDrop();
            updateSkillPreview();
        }, 100);

        // Show resume code if provided
        if (data.resume_code) {
            showResumeCode(data.resume_code);
        }
    });

    socket.on('lobby_join_failed', (data) => {
        console.log('Lobby join failed:', data);
        joinBtn.disabled = false;
        joinBtn.textContent = 'Join Lobby';
        window.lobbyApp.showNotification(data.reason || 'Failed to join lobby', 'error');
    });

    socket.on('error', (data) => {
        console.log('Socket error:', data);
        
        // Check if this is a "Lobby not found" error during recovery
        if (data.message && data.message.includes('Lobby not found')) {
            console.log('[RECOVERY] Lobby not found during recovery, resetting to lobby selection');
            window.lobbyApp.showNotification('Lobby no longer exists. Returning to lobby selection.', 'warning');
            
            // Reset state and go back to lobby selection
            currentPlayerId = null;
            currentLobbyId = null;
            window.lobbyPageState.selectedLobbyId = null;
            window.lobbyPageState.selectedLobbyData = null;
            window.lobbyApp.currentPlayerId = null;
            window.lobbyApp.currentLobbyId = null;
            
            // Update URL to lobby selection
            window.updatePageURL('lobbies');
            
            // Show lobby selection
            window.lobbyApp.showSection('lobby-selection-section');
            window.listLobbies();
            return;
        }
        
        // Re-enable join spectator button if it was disabled
        const joinSpectatorBtn = document.getElementById('join-spectator-btn');
        if (joinSpectatorBtn) {
            joinSpectatorBtn.disabled = false;
            joinSpectatorBtn.textContent = 'Join as Spectator';
        }
        window.lobbyApp.showNotification(data.message || 'An error occurred', 'error');
    });

    // Spectator event handlers
    socket.on('spectator_joined', (data) => {
        console.log('LOBBY.JS: Spectator joined:', data);
        currentPlayerId = data.player_id;
        currentLobbyId = data.lobby_id;
        // Note: Don't update currentPlayerName/currentLobbyId for spectators
        // as this would interfere with other tabs (like admin tabs)

        // Redirect to spectator page for this lobby
        console.log('LOBBY.JS: Redirecting spectator to spectator page');
        window.location.href = `/spectator/${data.lobby_id}`;
    });

    socket.on('spectator_update', (data) => {
        console.log('Spectator update:', data);

        // Check if this contains a cornucopia timer update
        if (data?.message?.message_type === 'cornucopia_timer_update') {
            console.log('🏺 CORNUCOPIA TIMER UPDATE found in spectator_update!', data.message.data);
            // Forward to game page if it exists
            if (typeof updateCornucopiaTimer === 'function') {
                updateCornucopiaTimer(data.message.data);
            }
            return; // Don't process as regular spectator update
        }

        // Only handle spectator updates if we're actually supposed to be spectating
        const isOnSpectatorPage = window.location.pathname.startsWith('/spectator');
        const spectatorSection = document.getElementById('spectator-section');

        if (isOnSpectatorPage || (spectatorSection && spectatorSection.style.display !== 'none')) {
            // We're in spectator mode, update the display
            updateSpectatorDisplay(data);
        } else {
            // We're not supposed to be spectating, ignore this event
            console.log('Ignoring spectator_update - not in spectator mode');
        }
    });

    // Modal event listeners
    document.querySelector('#resume-modal .modal-close').addEventListener('click', closeResumeModal);
    document.querySelector('#resume-modal .modal-footer .btn-primary').addEventListener('click', copyResumeCode);
    document.querySelector('#resume-modal .modal-footer .btn-secondary').addEventListener('click', closeResumeModal);

    // Spectator functions
    function updateSpectatorDisplay(data) {
        console.log('updateSpectatorDisplay called with:', data);
        // Handle both lobby data (waiting room) and game_state data (during game)
        const gameState = data.game_state || data; // data might be game_state directly or contain game_state
        const lobby = data.lobby || data; // data might be lobby directly

        // Check if spectator UI elements exist
        const spectatorRound = document.getElementById('spectator-round');
        const spectatorStatus = document.getElementById('spectator-game-status');
        const spectatorTributes = document.getElementById('spectator-tributes-container');

        console.log('Spectator UI elements found:', {
            spectatorRound: !!spectatorRound,
            spectatorStatus: !!spectatorStatus,
            spectatorTributes: !!spectatorTributes
        });

        if (!spectatorRound || !spectatorStatus || !spectatorTributes) {
            console.warn('Spectator UI elements not found, skipping update');
            return;
        }

        if (gameState && gameState.players) {
            // Game is running - show game state
            const aliveCount = gameState.players.filter(p => p.alive).length;
            const totalCount = gameState.players.length;

            // Update round
            spectatorRound.textContent = gameState.day || 1;

            // Update game status
            spectatorStatus.innerHTML = `
                <div class="spectator-info">
                    <div>Day: ${gameState.day || 1}</div>
                    <div>Alive: ${aliveCount}/${totalCount}</div>
                    <div>Status: ${gameState.status || 'Running'}</div>
                </div>
            `;

            // Update tributes
            spectatorTributes.innerHTML = gameState.players.map(player => `
                <div class="tribute-card ${player.alive ? '' : 'dead'}">
                    <div class="tribute-header">
                        <div class="tribute-name">${player.name}</div>
                        <div class="tribute-district">District ${player.district}</div>
                    </div>
                    <div class="tribute-stats">
                        <div class="stat-row">
                            <span class="stat-label">Health:</span>
                            <span class="stat-value ${getHealthClass(player.health)}">${player.health}/100</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Status:</span>
                            <span class="stat-value">${player.alive ? 'Alive' : 'Dead'}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } else if (lobby && lobby.players) {
            // Lobby waiting room - show player list
            spectatorRound.textContent = 'Waiting';

            spectatorStatus.innerHTML = `
                <div class="spectator-info">
                    <div>Status: Waiting for game to start</div>
                    <div>Players: ${Object.keys(lobby.players).length}</div>
                </div>
            `;

            // Show players who have created tributes
            const playersWithTributes = Object.values(lobby.players).filter(p => p.tribute_ready && p.tribute_data);
            spectatorTributes.innerHTML = playersWithTributes.map(player => `
                <div class="tribute-card">
                    <div class="tribute-header">
                        <div class="tribute-name">${player.tribute_data.name}</div>
                        <div class="tribute-district">District ${player.tribute_data.district}</div>
                    </div>
                    <div class="tribute-details">
                        <div>Player: ${player.name}</div>
                        <div>Age: ${player.tribute_data.age} • Gender: ${player.tribute_data.gender}</div>
                    </div>
                </div>
            `).join('');
        }
    }

    // Load district configuration and weapons on page load
    loadDistrictConfig();
    loadWeapons();

    function updateDistrictSelectOptions() {
        if (!districtConfig || !tributeDistrictSelect) return;

        // Clear existing options except the first one
        while (tributeDistrictSelect.options.length > 1) {
            tributeDistrictSelect.remove(1);
        }

        // Add district options with names
        for (let i = 1; i <= 12; i++) {
            const districtData = districtConfig.district_bonuses[i.toString()];
            const option = document.createElement('option');
            option.value = i;
            option.textContent = districtData ? `${i} - ${districtData.name}` : `District ${i}`;
            tributeDistrictSelect.appendChild(option);
        }
    }

    // UI event handlers
    window.joinLobby = function() {
        const playerName = playerNameInput.value.trim();
        const resumeCode = resumeCodeInput.value.trim().toUpperCase();

        if (!window.lobbyPageState.selectedLobbyId) {
            window.lobbyApp.showNotification('Please select a lobby first', 'warning');
            return;
        }

        if (!playerName && !resumeCode) {
            window.lobbyApp.showNotification('Please enter your name or resume code', 'warning');
            return;
        }

        if (playerName.length > 20) {
            window.lobbyApp.showNotification('Name too long (max 20 characters)', 'warning');
            return;
        }

        joinBtn.disabled = true;
        joinBtn.textContent = 'Joining...';

        if (resumeCode) {
            // Resume with code
            socket.emit('resume_lobby', {
                resume_code: resumeCode
            });
        } else {
            // Join as new player
            socket.emit('join_lobby', {
                lobby_id: window.lobbyPageState.selectedLobbyId,
                name: playerName
            });
        }
    };

    window.joinAsSpectator = function() {
        const lobbyId = currentLobbyId || window.lobbyPageState.selectedLobbyId;
        if (!lobbyId) {
            window.lobbyApp.showNotification('Please select a lobby first', 'warning');
            return;
        }

        // Disable button to prevent multiple clicks
        const joinSpectatorBtn = document.getElementById('join-spectator-btn');
        if (joinSpectatorBtn) {
            joinSpectatorBtn.disabled = true;
            joinSpectatorBtn.textContent = 'Joining as Spectator...';
        }

        // Emit join_as_spectator event to become a spectator of the selected/current lobby
        socket.emit('join_as_spectator', {
            lobby_id: lobbyId,
            name: currentPlayerName || 'Spectator'
        });
    };

    let lastTributeUpdateTime = 0;
    const TRIBUTE_UPDATE_THROTTLE_MS = 300; // Only send updates every 300ms max

    window.updateTribute = function() {
        // Rate limit tribute updates to prevent flooding the server
        const now = Date.now();
        if (now - lastTributeUpdateTime < TRIBUTE_UPDATE_THROTTLE_MS) {
            console.log('[THROTTLE] Skipping tribute update (too soon)');
            return;
        }
        lastTributeUpdateTime = now;

        try {
            // Get skill order from the skill order list
            const orderedSkills = skillOrderList.querySelectorAll('.skill-item');
            const skillOrder = Array.from(orderedSkills).map(item => item.dataset.skill);

            // Get preferred weapon
            const weaponSelect = document.getElementById('tribute-weapon');
            const preferredWeapon = weaponSelect ? weaponSelect.value || 'fists' : 'fists';

            // Send skill priority order to server - server will calculate ratings
            const tributeData = {
                name: tributeNameInput.value.trim(),
                district: parseInt(tributeDistrictSelect.value) || 1,
                gender: tributeGenderSelect.value,
                age: parseInt(tributeAgeInput.value) || 16,
                skill_priority: skillOrder,
                preferred_weapon: preferredWeapon
            };

            console.log('[UPDATE_TRIBUTE] Sending to server:', tributeData);
            socket.emit('update_tribute', { tribute_data: tributeData });

            // Also update player name to match tribute name
            const playerName = tributeNameInput.value.trim();
            if (playerName) {
                socket.emit('update_player_name', { name: playerName });
            }
        } catch (error) {
            console.error('[ERROR] updateTribute failed:', error);
            console.error('Stack:', error.stack);
        }
    };

    window.markTributeDone = function() {
        // First update tribute data
        updateTribute();

        // Then mark as done
        setTimeout(() => {
            socket.emit('tribute_done');
            tributeDoneBtn.disabled = true;
            tributeDoneBtn.textContent = 'Marked as Done';
            tributeNotDoneBtn.style.display = 'inline-block';
            
            // Start polling for tribute stats
            startTributeStatsPolling();
            
            // Switch to lobby section to see start button and other players
            window.lobbyApp.showSection('lobby-section');
        }, 500);
    };

    window.markTributeNotDone = function() {
        socket.emit('tribute_not_done');
        tributeDoneBtn.disabled = false;
        tributeDoneBtn.textContent = 'I\'m Done Creating My Tribute';
        tributeNotDoneBtn.style.display = 'none';

        // Stop polling for tribute stats
        stopTributeStatsPolling();

        // Switch back to tribute section to edit tribute
        window.lobbyApp.showSection('tribute-section');
    };

    window.editTribute = function() {
        // Mark tribute as not done (makes player not ready)
        markTributeNotDone();
    };

    // Tribute stats polling functions
    function startTributeStatsPolling() {
        if (tributeStatsInterval) {
            clearInterval(tributeStatsInterval);
        }
        tributeStatsInterval = setInterval(fetchTributeStats, 2000); // Poll every 2 seconds
        fetchTributeStats(); // Fetch immediately
    }

    function stopTributeStatsPolling() {
        if (tributeStatsInterval) {
            clearInterval(tributeStatsInterval);
            tributeStatsInterval = null;
        }
    }

    async function fetchTributeStats() {
        if (!currentPlayerId) return;

        try {
            // Check if we're spectating
            const currentSection = document.querySelector('.section:not([style*="display: none"])');
            const isSpectating = currentSection && currentSection.id === 'spectator-section';

            let response;
            if (isSpectating && currentLobbyId) {
                // Spectators get all tribute stats
                response = await fetch(`/api/tribute/spectator/${currentLobbyId}`);
            } else {
                // Regular players get only their own stats
                response = await fetch(`/api/tribute/${currentPlayerId}`);
            }

            if (response.ok) {
                const data = await response.json();
                updateTributeStatsDisplay(data);
            }
        } catch (error) {
            console.error('Error fetching tribute stats:', error);
        }
    }

    function updateTributeStatsDisplay(data) {
        // Check if this is spectator data (has tributes object) or single tribute data
        const isSpectatorData = data.tributes !== undefined;

        if (isSpectatorData) {
            // Handle spectator view - display all tributes
            updateSpectatorTributeStats(data.tributes);
        } else {
            // Handle single tribute view for players
            updateSingleTributeStats(data);
        }
    }

    function updateSingleTributeStats(data) {
        // Update district information
        if (data.district_name && data.district_description) {
            const districtInfoDiv = document.getElementById('district-info');
            if (districtInfoDiv) {
                districtInfoDiv.innerHTML = `
                    <div class="district-name">${data.district_name}</div>
                    <div class="district-description">${data.district_description}</div>
                `;
            }
        }

        // Update the skill ratings preview with final calculated stats
        if (data.final_ratings && skillRatingsPreview) {
            skillRatingsPreview.innerHTML = Object.entries(data.final_ratings)
                .map(([skill, rating]) => {
                    const baseRating = data.base_ratings ? data.base_ratings[skill] : rating;
                    const traitScore = data.trait_scores ? data.trait_scores[skill] : rating;
                    const traitInfo = districtConfig && districtConfig.trait_scoring[skill] ?
                        ` (${districtConfig.trait_scoring[skill].description})` : '';
                    return `
                        <div class="skill-rating-item">
                            <span class="skill-rating-name">${skill.charAt(0).toUpperCase() + skill.slice(1)}${traitInfo}</span>
                            <span class="skill-rating-value">${rating}/10</span>
                            <span class="base-rating">Base: ${baseRating}</span>
                            <span class="trait-score">Score: ${traitScore.toFixed(1)}</span>
                        </div>
                    `;
                })
                .join('');
        }

        if (data.district_bonuses && districtBonusesDiv) {
            const bonuses = Object.entries(data.district_bonuses)
                .filter(([skill, bonus]) => bonus !== 0)
                .map(([skill, bonus]) => `<div class="district-bonus ${bonus > 0 ? 'positive' : 'negative'}">${skill.charAt(0).toUpperCase() + skill.slice(1)}: ${bonus > 0 ? '+' : ''}${bonus}</div>`)
                .join('');
            districtBonusesDiv.innerHTML = bonuses || '<div class="no-bonuses">No district bonuses/penalties</div>';
        }
    }

    function updateSpectatorTributeStats(tributes) {
        // Find the spectator stats container
        let spectatorStatsContainer = document.getElementById('spectator-tribute-stats');
        if (!spectatorStatsContainer) {
            // Create container if it doesn't exist
            const spectatorSection = document.getElementById('spectator-section');
            if (spectatorSection) {
                spectatorStatsContainer = document.createElement('div');
                spectatorStatsContainer.id = 'spectator-tribute-stats';
                spectatorStatsContainer.className = 'spectator-tribute-stats';
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

    // Skill priority system functions - simplified drag-and-drop
    function initializeDragAndDrop() {
        // Make skills draggable
        document.querySelectorAll('.skill-item').forEach(item => {
            item.draggable = true;
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
        });

        // Make lists accept drops
        [availableSkillsList, skillOrderList].forEach(list => {
            list.addEventListener('dragover', handleDragOver);
            list.addEventListener('drop', handleDrop);
            list.addEventListener('dragenter', handleDragEnter);
            list.addEventListener('dragleave', handleDragLeave);
        });
    }

    function handleDragStart(e) {
        draggedElement = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        console.log('Started dragging:', draggedElement.textContent);
    }

    function handleDragEnd(e) {
        e.target.classList.remove('dragging');
        console.log('Drag ended');
        draggedElement = null;
        updateSkillPreview();
        updateTribute();
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();
    }

    function handleDragLeave(e) {
        e.preventDefault();
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        if (!draggedElement) {
            console.log('[DRAG] No dragged element');
            return;
        }

        // Get the list we're dropping into
        const targetList = e.currentTarget;
        if (!targetList || !targetList.classList.contains('skill-list')) {
            console.log('[DRAG] Target is not a skill-list');
            return;
        }

        const isDropOnOrderList = targetList === skillOrderList;
        console.log('[DRAG] Dropping into:', isDropOnOrderList ? 'skillOrderList' : 'availableSkillsList');

        // Get the skill data from the element being dragged
        const skillName = draggedElement.dataset.skill;
        const skillText = draggedElement.textContent.trim();
        const sourceList = draggedElement.parentElement;

        console.log(`[DRAG] Dragging skill: "${skillText}" (${skillName}) from ${sourceList === skillOrderList ? 'order' : 'available'} list`);

        // Check if this skill already exists in the target list (before we remove anything)
        const existingSkillInTarget = targetList.querySelector(`[data-skill="${skillName}"]`);
        const isReorderingInSameList = existingSkillInTarget && sourceList === targetList;

        // If reordering in the same list, remove the old one first so we can insert at new position
        if (isReorderingInSameList) {
            targetList.removeChild(draggedElement);
            console.log(`[DRAG] Removed from same list for reordering`);
        } else if (sourceList && sourceList !== targetList) {
            // Moving to different list - remove from source
            sourceList.removeChild(draggedElement);
            console.log(`[DRAG] Removed from source list`);
        }

        // Create a fresh element (avoid any state issues with the old element)
        const newSkillItem = document.createElement('div');
        newSkillItem.className = 'skill-item';
        newSkillItem.dataset.skill = skillName;
        newSkillItem.draggable = true;
        newSkillItem.textContent = skillText;
        newSkillItem.addEventListener('dragstart', handleDragStart);
        newSkillItem.addEventListener('dragend', handleDragEnd);

        // Find insertion point based on mouse Y position
        const currentItems = Array.from(targetList.querySelectorAll('.skill-item'));
        let insertBefore = null;
        
        if (currentItems.length > 0) {
            for (let item of currentItems) {
                const itemRect = item.getBoundingClientRect();
                const midpoint = itemRect.top + itemRect.height / 2;
                
                if (e.clientY < midpoint) {
                    insertBefore = item;
                    console.log(`[DRAG] Found insertion point before: ${item.textContent}`);
                    break;
                }
            }
        }

        // Insert at correct position
        if (insertBefore) {
            targetList.insertBefore(newSkillItem, insertBefore);
            console.log(`[DRAG] Inserted "${skillText}" before "${insertBefore.textContent}"`);
        } else {
            targetList.appendChild(newSkillItem);
            console.log(`[DRAG] Appended "${skillText}" to end of list`);
        }

        // Verify no duplicates in order list
        if (isDropOnOrderList) {
            const allSkills = Array.from(targetList.querySelectorAll('.skill-item')).map(el => el.dataset.skill);
            console.log(`[DRAG] Order list now contains: [${allSkills.join(', ')}]`);
            
            // Clean up any duplicates
            const seen = new Set();
            Array.from(targetList.querySelectorAll('.skill-item')).forEach(item => {
                if (seen.has(item.dataset.skill)) {
                    console.warn(`[DRAG] Removing duplicate: ${item.textContent}`);
                    targetList.removeChild(item);
                } else {
                    seen.add(item.dataset.skill);
                }
            });
        }

        // Update UI
        updatePlaceholderVisibility();
        updateSkillPreview();
        updateTribute();
    }

    function updatePlaceholderVisibility() {
        const placeholder = skillOrderList.querySelector('.skill-placeholder');
        const hasItems = skillOrderList.querySelectorAll('.skill-item').length > 0;

        if (placeholder) {
            placeholder.style.display = hasItems ? 'none' : 'block';
        }
    }

    function updateSkillPreview() {
        const orderedSkills = skillOrderList.querySelectorAll('.skill-item');
        const skillOrder = Array.from(orderedSkills).map(item => item.dataset.skill);

        skillRatingsPreview.innerHTML = '';
        districtBonusesDiv.innerHTML = '';

        const selectedDistrict = parseInt(tributeDistrictSelect.value) || 1;
        const districtModifiers = getDistrictModifiers(selectedDistrict);

        // Show district bonuses info
        districtBonusesDiv.innerHTML = `<h5>District ${selectedDistrict} Bonuses (Applied by Server):</h5>`;

        const bonusList = document.createElement('div');
        bonusList.className = 'bonus-list';

        Object.entries(districtModifiers).forEach(([skill, modifier]) => {
            if (modifier !== 0) {
                const bonusItem = document.createElement('div');
                bonusItem.className = `bonus-item ${modifier > 0 ? 'positive' : 'negative'}`;
                bonusItem.textContent = `${skill.charAt(0).toUpperCase() + skill.slice(1)}: ${modifier > 0 ? '+' : ''}${modifier}`;
                bonusList.appendChild(bonusItem);
            }
        });

        districtBonusesDiv.appendChild(bonusList);

        // Show BASE skill ratings (bonuses applied server-side)
        const allSkills = ['intelligence', 'hunting', 'strength', 'social', 'stealth', 'survival', 'agility', 'endurance', 'charisma', 'luck'];

        allSkills.forEach(skill => {
            const priorityIndex = skillOrder.indexOf(skill);
            let baseRating;

            if (priorityIndex !== -1) {
                // Prioritized skills: 10 down to 1 based on position
                baseRating = 10 - priorityIndex;
            } else {
                // Unprioritized skills: show as "random 1-5"
                baseRating = '?';  // Server will calculate this randomly
            }

            const ratingItem = document.createElement('div');
            ratingItem.className = 'skill-rating-item';
            const baseStr = typeof baseRating === 'number' ? `${baseRating}/10` : baseRating;
            ratingItem.innerHTML = `
                <span class="skill-rating-name">${skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
                <span class="skill-rating-value">${baseStr}</span>
                ${priorityIndex !== -1 ? `<span class="priority-indicator">(Priority #${priorityIndex + 1})</span>` : '<span class="unprioritized">(Random)</span>'}
            `;

            skillRatingsPreview.appendChild(ratingItem);
        });
    }

    function getDistrictModifiers(district) {
        // District-based skill modifiers (+/- values)
        const districtTraits = {
            1: { social: 2, charisma: 2, survival: -1, hunting: -1 }, // Luxury/Commerce
            2: { strength: 2, endurance: 2, stealth: -1, charisma: -1 }, // Masonry/Stone
            3: { intelligence: 2, agility: 1, strength: -1, endurance: -1 }, // Technology
            4: { agility: 2, hunting: 1, intelligence: -1, social: -1 }, // Fishing
            5: { intelligence: 2, endurance: 1, social: -1, charisma: -1 }, // Power
            6: { endurance: 2, strength: 1, intelligence: -1, agility: -1 }, // Transportation
            7: { strength: 2, endurance: 1, social: -1, charisma: -1 }, // Lumber
            8: { agility: 2, intelligence: 1, strength: -1, endurance: -1 }, // Textiles
            9: { endurance: 2, survival: 1, hunting: -1, intelligence: -1 }, // Grain
            10: { survival: 2, endurance: 1, charisma: -1, social: -1 }, // Livestock
            11: { survival: 2, strength: 1, intelligence: -1, charisma: -1 }, // Agriculture
            12: { endurance: 2, strength: 1, charisma: -1, social: -1 } // Coal Mining
        };

        return districtTraits[district] || {};
    }

    window.randomizeSkillOrder = function() {
        // Get all skills currently in the priority order list
        const currentSkills = Array.from(skillOrderList.querySelectorAll('.skill-item'));

        // If no skills in priority list, get all available skills and move them all to priority
        if (currentSkills.length === 0) {
            const availableSkills = Array.from(availableSkillsList.querySelectorAll('.skill-item'));
            availableSkills.forEach(skillElement => {
                const skillItem = document.createElement('div');
                skillItem.className = 'skill-item';
                skillItem.dataset.skill = skillElement.dataset.skill;
                skillItem.draggable = true;
                skillItem.textContent = skillElement.textContent;
                skillItem.addEventListener('dragstart', handleDragStart);
                skillItem.addEventListener('dragend', handleDragEnd);

                skillOrderList.appendChild(skillItem);
                skillElement.remove(); // Remove from available list
            });
            updatePlaceholderVisibility();
        }

        // Shuffle the skills currently in the priority order list
        const skillsToShuffle = Array.from(skillOrderList.querySelectorAll('.skill-item'));

        // Clear the priority list
        skillOrderList.innerHTML = '<div class="skill-placeholder">Drag skills here to set your priority order</div>';

        // Shuffle the skills array
        for (let i = skillsToShuffle.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [skillsToShuffle[i], skillsToShuffle[j]] = [skillsToShuffle[j], skillsToShuffle[i]];
        }

        // Add shuffled skills back to priority list
        skillsToShuffle.forEach(skillElement => {
            skillOrderList.appendChild(skillElement);
        });

        // Update UI
        updatePlaceholderVisibility();
        updateSkillPreview();
        updateTribute();
    };

    function showResumeCode(code) {
        document.getElementById('modal-resume-code').textContent = code;
        document.getElementById('resume-modal').style.display = 'block';
    }

    function closeResumeModal() {
        document.getElementById('resume-modal').style.display = 'none';
    }

    function copyResumeCode() {
        const codeElement = document.getElementById('modal-resume-code');
        if (!codeElement) return;

        const code = codeElement.textContent;

        navigator.clipboard.writeText(code).then(() => {
            window.lobbyApp.showNotification('Resume code copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = code;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            window.lobbyApp.showNotification('Resume code copied to clipboard!', 'success');
        });
    }

    window.copyResumeCode = copyResumeCode;

    window.startGame = function() {
        if (!isHost) {
            window.lobbyApp.showNotification('Only the host can start the game', 'warning');
            return;
        }

        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

        socket.emit('start_game');
    };

    window.leaveLobby = function() {
        if (confirm('Are you sure you want to leave the lobby?')) {
            socket.emit('leave_lobby');
            resetToLogin();
        }
    };

    // Helper functions
    function updateLobbyList(lobbies) {
        try {
            console.log('Updating lobby list with:', lobbies);
            console.log('lobbies is array:', Array.isArray(lobbies));
            console.log('lobbies length:', lobbies ? lobbies.length : 'null/undefined');

            if (!lobbyList) {
                console.error('lobbyList element not found!');
                return;
            }

            if (!lobbies || lobbies.length === 0) {
                console.log('No lobbies found, showing empty message');
                lobbyList.innerHTML = '<div class="no-lobbies">No lobbies available. Create one to get started!</div>';
                return;
            }

            console.log('Rendering', lobbies.length, 'lobbies');
            lobbyList.innerHTML = '';
            lobbies.forEach(lobby => {
                console.log('Rendering lobby:', lobby);
                const lobbyCard = document.createElement('div');
                lobbyCard.className = 'lobby-card';
                lobbyCard.onclick = () => selectLobby(lobby.id, lobby);
                lobbyCard.ondblclick = () => selectLobby(lobby.id, lobby); // Double-click also selects

                // Determine status and whether it's spectate-only
                let statusClass = 'waiting';
                let statusText = 'Waiting';
                let isSpectateOnly = lobby.spectate_only || lobby.game_started;

                if (isSpectateOnly) {
                    statusClass = 'in-progress';
                    statusText = 'In Progress (Spectate)';
                } else if (lobby.player_count >= lobby.max_players) {
                    statusClass = 'full';
                    statusText = 'Full';
                }

                // Store lobby data on the card for the join button
                lobbyCard.dataset.lobbyId = lobby.id;
                lobbyCard.dataset.lobbyData = JSON.stringify(lobby);

                // Show different button based on lobby state
                const buttonText = isSpectateOnly ? 'Spectate' : 'Join Lobby';
                const buttonClass = isSpectateOnly ? 'join-spectate-btn' : 'join-lobby-btn';

                lobbyCard.innerHTML = `
                    <div class="lobby-name">${lobby.name}</div>
                    <div class="lobby-details">
                        <div class="player-count">${lobby.player_count}/${lobby.max_players} players</div>
                        <div class="lobby-status ${statusClass}">${statusText}</div>
                    </div>
                    <div class="lobby-created">Created by ${lobby.host_name}${lobby.created_at ? ' - ' + new Date(lobby.created_at).toLocaleString() : ''}</div>
                    <div class="lobby-actions">
                        <button class="btn btn-primary btn-sm ${buttonClass}" data-lobby-id="${lobby.id}">${buttonText}</button>
                    </div>
                `;

                lobbyList.appendChild(lobbyCard);
            });

            // Add event listeners for join buttons (normal game)
            document.querySelectorAll('.join-lobby-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const lobbyId = btn.dataset.lobbyId;
                    const lobbyCard = btn.closest('.lobby-card');
                    const lobbyData = JSON.parse(lobbyCard.dataset.lobbyData);
                    selectLobby(lobbyId, lobbyData);
                });
            });

            // Add event listeners for spectate buttons
            document.querySelectorAll('.join-spectate-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const lobbyId = btn.dataset.lobbyId;
                    const lobbyCard = btn.closest('.lobby-card');
                    const lobbyData = JSON.parse(lobbyCard.dataset.lobbyData);
                    console.log('Spectating lobby:', lobbyId);
                    joinAsSpectator(lobbyData);
                });
            });
        } catch (error) {
            console.error('Error in updateLobbyList:', error);
        }
    }

    // Handle Enter key in name input
    playerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            joinLobby();
        }
    });

    // Auto-update tribute on input changes
    const tributeInputs = [
        tributeNameInput, tributeDistrictSelect, tributeGenderSelect, tributeAgeInput
    ];

    tributeInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', debounce(updateTribute, 1000));
        }
    });

    // Update skill preview when district changes
    tributeDistrictSelect.addEventListener('change', () => {
        updateSkillPreview();
        updateTribute();
    });

    // Test the district change functionality
    window.testDistrictChange = function(newDistrict) {
        console.log('Testing district change to:', newDistrict);
        tributeDistrictSelect.value = newDistrict;
        console.log('Set tributeDistrictSelect.value to:', tributeDistrictSelect.value);
        updateSkillPreview();
        console.log('Called updateSkillPreview');
    };

    // Force update district bonuses
    window.forceUpdateBonuses = function() {
        console.log('Force updating district bonuses');
        const selectedDistrict = parseInt(tributeDistrictSelect.value) || 1;
        const districtModifiers = getDistrictModifiers(selectedDistrict);
        districtBonusesDiv.innerHTML = `<h5>District ${selectedDistrict} Bonuses:</h5><div class="bonus-list"><div class="bonus-item positive">Test Bonus: +1</div></div>`;
        console.log('Set districtBonusesDiv.innerHTML');
    };

    // Skill range inputs (only if they exist on this page)
    const skillInputs = ['strength', 'agility', 'intelligence', 'charisma', 'survival', 'combat'];
    skillInputs.forEach(skill => {
        const input = document.getElementById(`skill-${skill}`);
        const valueSpan = document.getElementById(`${skill}-value`);

        if (input && valueSpan) {
            input.addEventListener('input', () => {
                valueSpan.textContent = input.value;
                updateTribute();
            });
        }
    });

    // Functions
    function updateLobby(lobby) {
        // Only update if we're in the lobby section
        const lobbySection = document.getElementById('lobby-section');
        if (lobbySection.style.display === 'none') {
            return;
        }

        lobbyTitle.textContent = `Lobby: ${lobby.name}`;
        lobbyInfo.innerHTML = `
            <div>Players: ${Object.keys(lobby.players).length}/24</div>
            <div>Status: ${lobby.game_started ? 'In Progress' : 'Creating Tributes'}</div>
        `;

        // Update players list
        playersList.innerHTML = '';
        const players = Object.values(lobby.players);

        players.forEach(player => {
            const isCurrentPlayer = player.id === currentPlayerId;
            const card = window.lobbyApp.createPlayerCard(player, isCurrentPlayer);
            playersList.appendChild(card);
        });

        // Update tribute status
        const totalPlayers = players.length;
        const donePlayers = players.filter(p => p.tribute_ready).length;

        // Show completed tributes
        let tributesHtml = '';
        if (donePlayers > 0) {
            tributesHtml = '<h3>Ready Tributes:</h3><div class="tributes-list">';
            players.filter(p => p.tribute_ready).forEach(player => {
                if (player.tribute_data) {
                    // Check if this is an AI player
                    const isAI = player.id.startsWith('ai_') || !player.connected;
                    const aiIndicator = isAI ? '<span class="ai-indicator">🤖 AI</span>' : '';
                    
                    tributesHtml += `
                        <div class="tribute-card ${isAI ? 'ai-tribute' : ''}">
                            <div class="tribute-name">${player.tribute_data.name} ${aiIndicator}</div>
                            <div class="tribute-details">
                                <span>District ${player.tribute_data.district}</span>
                                <span>${player.tribute_data.age} years old</span>
                                <span>${player.tribute_data.gender}</span>
                            </div>
                            <div class="tribute-player">${isAI ? 'Computer Player' : `Player: ${player.name}`}</div>
                        </div>
                    `;
                }
            });
            tributesHtml += '</div>';
        }

        tributeProgress.innerHTML = `
            ${tributesHtml}
            <div>Players Done: ${donePlayers}/${totalPlayers}</div>
            ${donePlayers >= 2 ? '<div class="ready-text">At least 2 players ready! Host can start the game.</div>' : '<div class="waiting-text">Waiting for at least 2 players to complete tribute creation...</div>'}
        `;

        // Update host status
        isHost = currentPlayerId === lobby.host_id;

        // Update buttons
        const enoughPlayersReady = donePlayers >= 2;
        const canStart = isHost && enoughPlayersReady && !lobby.game_started && players.length >= 2;

        startBtn.style.display = isHost ? 'inline-block' : 'none';
        startBtn.disabled = !canStart;
        startBtn.textContent = canStart ? 'Start Game' : 'Waiting for Tributes...';
        
        // Show/hide admin controls for host
        const adminControls = document.getElementById('admin-lobby-controls');
        if (adminControls) {
            adminControls.style.display = isHost ? 'block' : 'none';
        }
    }

    function loadTributeData(tributeData) {
        if (!tributeData) return;

        // Load tribute data into form
        if (tributeData.name) tributeNameInput.value = tributeData.name;
        if (tributeData.district) tributeDistrictSelect.value = tributeData.district;
        if (tributeData.gender) tributeGenderSelect.value = tributeData.gender;
        if (tributeData.age) tributeAgeInput.value = tributeData.age;

        // Load skills into priority system
        if (tributeData.skills) {
            // Clear current skill order list
            skillOrderList.innerHTML = '<div class="skill-placeholder">Drag skills here to set your priority order</div>';

            // Sort skills by rating (highest first) to determine priority order
            const skillEntries = Object.entries(tributeData.skills).sort((a, b) => b[1] - a[1]);

            // Add prioritized skills to order list (those with rating > 5, sorted by rating descending)
            skillEntries.forEach(([skill, rating]) => {
                // Include skills that were explicitly prioritized (rating > 5)
                if (rating > 5) {
                    const skillItem = document.createElement('div');
                    skillItem.className = 'skill-item';
                    skillItem.dataset.skill = skill;
                    skillItem.draggable = true;
                    skillItem.textContent = skill.charAt(0).toUpperCase() + skill.slice(1);
                    skillItem.addEventListener('dragstart', handleDragStart);
                    skillItem.addEventListener('dragend', handleDragEnd);

                    skillOrderList.appendChild(skillItem);

                    // Remove from available skills
                    const availableItem = availableSkillsList.querySelector(`[data-skill="${skill}"]`);
                    if (availableItem) {
                        availableItem.remove();
                    }
                }
            });

            updatePlaceholderVisibility();
            updateSkillPreview();
        }

        currentTributeData = tributeData;
    }

    function addToGameLog(message, timestamp) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const time = timestamp ? new Date(timestamp * 1000).toLocaleTimeString() : '';
        entry.innerHTML = `<span class="timestamp">[${time}]</span> ${message}`;

        gameLog.appendChild(entry);
        gameLog.scrollTop = gameLog.scrollHeight;

        // Also add to spectator log if it exists
        if (spectatorLog) {
            const spectatorEntry = entry.cloneNode(true);
            spectatorLog.appendChild(spectatorEntry);
            spectatorLog.scrollTop = spectatorLog.scrollHeight;
        }
    }

    function resetToLogin() {
        currentPlayerId = null;
        currentLobbyId = null;
        window.lobbyPageState.selectedLobbyId = null;
        window.lobbyPageState.selectedLobbyData = null;
        isHost = false;
        currentTributeData = null;
        window.lobbyApp.currentPlayerId = null;
        window.lobbyApp.currentLobbyId = null;
        window.lobbyApp.gameStarted = false;

        // Reset form
        playerNameInput.value = '';
        joinBtn.disabled = false;
        joinBtn.textContent = 'Join Lobby';

        // Clear logs
        gameLog.innerHTML = '';
        
        // Update URL back to lobby selection
        window.updatePageURL('lobbies');

        // Show lobby selection
        window.lobbyApp.showSection('lobby-selection-section');
        window.listLobbies();
    }

    function handleTributeStatUpdate(message) {
        console.log('Handling tribute stat update:', message);
        
        const { tribute_id, stat, new_value, old_value, delta, cause } = message;
        
        // Update tribute cards in the game overview
        updateTributeCard(tribute_id, stat, new_value, old_value, delta, cause);
        
        // Add to game log
        const statName = stat.charAt(0).toUpperCase() + stat.slice(1);
        const changeText = delta > 0 ? `+${delta}` : delta;
        const causeText = cause ? ` (${cause})` : '';
        addToGameLog(`${tribute_id}: ${statName} ${old_value} → ${new_value} (${changeText})${causeText}`, new Date().toLocaleTimeString());
    }

    function updateTributeCard(tributeId, stat, newValue, oldValue, delta, cause) {
        // Find the tribute card in the game overview
        const tributeCards = document.querySelectorAll('.tribute-card');
        for (const card of tributeCards) {
            const cardTributeId = card.dataset.tributeId;
            if (cardTributeId === tributeId) {
                // Update the stat display
                const statElement = card.querySelector(`.${stat}-value`);
                if (statElement) {
                    // Add visual feedback for the change
                    statElement.textContent = newValue;
                    statElement.classList.add('stat-changed');
                    
                    // Remove the class after animation
                    setTimeout(() => {
                        statElement.classList.remove('stat-changed');
                    }, 1000);
                    
                    // Add change indicator
                    const changeIndicator = card.querySelector('.stat-change-indicator') || document.createElement('div');
                    changeIndicator.className = 'stat-change-indicator';
                    changeIndicator.textContent = delta > 0 ? `+${delta}` : delta;
                    changeIndicator.style.color = delta > 0 ? '#4CAF50' : '#f44336';
                    
                    if (!card.querySelector('.stat-change-indicator')) {
                        statElement.parentNode.appendChild(changeIndicator);
                    }
                    
                    // Remove indicator after animation
                    setTimeout(() => {
                        if (changeIndicator.parentNode) {
                            changeIndicator.parentNode.removeChild(changeIndicator);
                        }
                    }, 2000);
                }
                
                // Update status if health changed significantly
                if (stat === 'health') {
                    updateTributeStatus(card, newValue);
                }
                
                break;
            }
        }
    }

    function updateTributeStatus(card, health) {
        const statusElement = card.querySelector('.tribute-status');
        if (statusElement) {
            let status = 'Alive';
            let statusClass = 'status-alive';
            
            if (health <= 0) {
                status = 'Dead';
                statusClass = 'status-dead';
            } else if (health < 30) {
                status = 'Critical';
                statusClass = 'status-critical';
            } else if (health < 60) {
                status = 'Injured';
                statusClass = 'status-injured';
            }
            
            statusElement.textContent = status;
            statusElement.className = `tribute-status ${statusClass}`;
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Auto-focus name input (when in login section)
    // playerNameInput.focus(); // Commented out since we start with lobby selection

    function updateAvailableDistricts(availableDistricts) {
        const districtSelect = document.getElementById('tribute-district');
        if (!districtSelect) return;

        // Store current selection
        const currentValue = districtSelect.value;

        // Clear existing options
        districtSelect.innerHTML = '';

        // Add available districts
        availableDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = `District ${district}`;
            districtSelect.appendChild(option);
        });

        // Try to restore previous selection if it's still available
        if (currentValue && availableDistricts.includes(parseInt(currentValue))) {
            districtSelect.value = currentValue;
        } else if (availableDistricts.length > 0) {
            // Select first available district
            districtSelect.value = availableDistricts[0];
        }

        console.log('Updated available districts:', availableDistricts);

        // Update skill preview with new district
        updateSkillPreview();
    }

    // Initialize by showing lobby selection
    function initializeLobbyPage() {
        console.log('initializeLobbyPage called, lobbyApp available:', !!window.lobbyApp);
        if (window.lobbyApp) {
            // Check URL to determine if we should restore a previous state
            const urlState = window.restoreStateFromURL();
            console.log('[URL STATE] Page load detected state from URL:', urlState);
            
            if (urlState.type === 'lobby' || urlState.type === 'waiting') {
                // We were previously in a lobby, attempt to rejoin
                console.log('[URL STATE] Restoring previous lobby state:', urlState);
                window.lobbyPageState.selectedLobbyId = urlState.lobbyId;
                
                // For now, we'll wait for socket connection and then let the server
                // re-establish the player session via player_id from the session/resume code
                // The lobby_joined or lobby_updated events will handle showing the right section
                
                // Show a loading message
                const lobbySelectionSection = document.getElementById('lobby-selection-section');
                if (lobbySelectionSection) {
                    lobbySelectionSection.innerHTML = '<div class="loading">Reconnecting to lobby...</div>';
                    window.lobbyApp.showSection('lobby-selection-section');
                }
            } else {
                // Normal initialization - show lobby selection
                console.log('Showing lobby selection section');
                window.lobbyApp.showSection('lobby-selection-section');
            }

            // Try to list lobbies immediately, and also listen for connect event
            function tryListLobbies() {
                console.log('Attempting to list lobbies, socket connected:', socket.connected, 'readyState:', socket.readyState);
                if (socket.connected) {
                    console.log('Socket connected, listing lobbies');
                    // Only list lobbies if we're in the lobby selection state
                    if (urlState.type !== 'lobby' && urlState.type !== 'waiting') {
                        listLobbies();
                    }
                } else {
                    console.log('Socket not connected yet, will retry...');
                    setTimeout(tryListLobbies, 500);
                }
            }

            // Listen for connect event in case socket connects later
            socket.once('connect', () => {
                console.log('Socket connected event fired, listing lobbies');
                // Only list lobbies if we're in the lobby selection state
                if (urlState.type !== 'lobby' && urlState.type !== 'waiting') {
                    listLobbies();
                }
            });

            // Try immediately
            console.log('Calling tryListLobbies() immediately');
            tryListLobbies();

            // Also try again after delays to ensure lobbies load
            setTimeout(() => {
                console.log('First retry: calling listLobbies() after 1 second');
                // Only list lobbies if we're in the lobby selection state
                if (urlState.type !== 'lobby' && urlState.type !== 'waiting') {
                    listLobbies();
                }
            }, 1000);

            setTimeout(() => {
                console.log('Second retry: calling listLobbies() after 3 seconds');
                // Only list lobbies if we're in the lobby selection state
                if (urlState.type !== 'lobby' && urlState.type !== 'waiting') {
                    listLobbies();
                }
            }, 3000);

            // Set up periodic refresh every 10 seconds to keep lobby list updated
            setInterval(() => {
                if (window.lobbyApp && window.lobbyApp.currentSection === 'lobby-selection-section' && urlState.type !== 'lobby' && urlState.type !== 'waiting') {
                    console.log('Periodic lobby refresh');
                    listLobbies();
                }
            }, 10000);
        } else {
            // Wait for lobbyApp to be available
            setTimeout(initializeLobbyPage, 100);
        }
    }

    // Initialize drag and drop for skill priorities
    initializeDragAndDrop();
    updateSkillPreview();

    initializeLobbyPage();
});

// ============================================================================
// ADMIN FUNCTIONS FOR LOBBY
// ============================================================================

window.generateRemainingTributesLobby = function() {
    const statusDiv = document.getElementById('admin-lobby-status');
    if (!statusDiv) return;

    statusDiv.className = 'admin-status';
    statusDiv.textContent = 'Generating AI tributes for remaining districts...';

    console.log('Requesting AI tribute generation for remaining districts from lobby');
    
    // Emit request to server to generate AI tributes for remaining districts
    if (window.lobbyApp && window.lobbyApp.socket) {
        window.lobbyApp.socket.emit('generate_remaining_tributes', {}, (response) => {
            if (response && response.success) {
                statusDiv.className = 'admin-status success';
                if (response.count > 0) {
                    statusDiv.textContent = `✓ Successfully generated ${response.count} AI tribute(s) for remaining districts!`;
                } else {
                    statusDiv.textContent = `✓ ${response.message}`;
                }
            } else {
                statusDiv.className = 'admin-status error';
                statusDiv.textContent = `✗ Error: ${response?.message || 'Failed to generate tributes'}`;
            }
            
            // Clear status after 5 seconds
            setTimeout(() => {
                statusDiv.textContent = '';
                statusDiv.className = 'admin-status';
            }, 5000);
        });
    } else {
        statusDiv.className = 'admin-status error';
        statusDiv.textContent = '✗ Not connected to server';
    }
};

window.viewAllTributes = function() {
    const statusDiv = document.getElementById('admin-lobby-status');
    if (!statusDiv) return;

    // Show a modal or expand the tributes display
    statusDiv.className = 'admin-status';
    statusDiv.textContent = 'Feature coming soon: View all created tributes';
    
    setTimeout(() => {
        statusDiv.textContent = '';
        statusDiv.className = 'admin-status';
    }, 3000);
};