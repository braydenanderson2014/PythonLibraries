// Hunger Games Simulator - Game Page JavaScript

let gamePageInitialized = false;

// Wait for lobbyApp to be initialized before accessing socket
function waitForSocket(callback, timeout = 15000) {  // Increased from 10s to 15s
    const startTime = Date.now();
    let checkCount = 0;
    
    function checkSocket() {
        checkCount++;
        console.log(`[SOCKET_CHECK] Attempt ${checkCount}: lobbyApp=${!!window.lobbyApp}, socket=${!!window.lobbyApp?.socket}`);
        
        if (window.lobbyApp && window.lobbyApp.socket) {
            console.log('✅ Socket ready, initializing game');
            callback(window.lobbyApp.socket);
        } else if (Date.now() - startTime < timeout) {
            const elapsed = Date.now() - startTime;
            console.log(`⏳ Waiting for socket (${elapsed}ms)...`);
            setTimeout(checkSocket, 200);  // Check every 200ms instead of 100ms
        } else {
            console.error(`❌ Socket initialization timeout after ${Date.now() - startTime}ms`);
            console.error('lobbyApp:', window.lobbyApp);
            console.error('socket:', window.lobbyApp?.socket);
            // Don't redirect - this might be a timing issue in SPA mode
            // Instead, try one more time with a longer delay
            console.log('🔄 Retrying socket initialization...');
            setTimeout(() => {
                if (window.lobbyApp && window.lobbyApp.socket) {
                    console.log('✅ Socket became available on retry');
                    callback(window.lobbyApp.socket);
                } else {
                    console.error('❌ Socket still unavailable, redirecting to lobby');
                    window.location.href = '/';
                }
            }, 2000);
        }
    }
    
    checkSocket();
}

document.addEventListener('DOMContentLoaded', () => {
    // Don't initialize game page immediately
    // Instead, wait for the game_starting event to show the section
    // Then initialize when game section becomes visible
    console.log('Game page script loaded, waiting for game_starting event');
});

// Initialize game page when it's shown (called when game-starting event received)
// Can be called with socket directly OR will attempt to find it from window.lobbyApp
window.initializeGamePageWithSocket = function(socket) {
    if (gamePageInitialized) {
        console.log('Game page already initialized');
        return;
    }
    
    console.log('✅ [INIT] Socket passed directly, initializing game page');
    initializeGamePage(socket);
    gamePageInitialized = true;
};

// Fallback: try to find socket from window.lobbyApp (for compatibility)
window.initializeGamePageWhenReady = function() {
    if (gamePageInitialized) {
        console.log('Game page already initialized');
        return;
    }
    
    waitForSocket((socket) => {
        initializeGamePage(socket);
        gamePageInitialized = true;
    });
};

function initializeGamePage(socket) {

    // Get lobby ID from window (set by app.js when game_starting event received)
    const lobbyId = window.currentLobbyId;
    if (!lobbyId) {
        console.error('❌ No lobby ID found. Cannot initialize game page.');
        return;
    }
    console.log(`🎮 Initializing game page for lobby: ${lobbyId}`);

    // DOM elements
    const gameStatus = document.getElementById('game-status');
    const gameLog = document.getElementById('game-log');
    const actionButtons = document.getElementById('action-buttons');
    const leaveGameBtn = document.getElementById('leave-game-btn');

    let gameState = null;
    let currentPlayer = null;
    let lastUpdateTime = Date.now();
    let lobbyTimeoutInterval = null;
    let isPageHidden = false;

    // Track when page visibility changes (tab minimized, dev tools open, etc.)
    document.addEventListener('visibilitychange', () => {
        isPageHidden = document.hidden;
        if (!isPageHidden) {
            // Page became visible again, reset the update timer to avoid false timeouts
            lastUpdateTime = Date.now();
            console.log('📄 Page became visible again, timer reset');
        }
    });

    // Check for lobby timeout every 30 seconds
    function startLobbyTimeoutCheck() {
        if (lobbyTimeoutInterval) {
            clearInterval(lobbyTimeoutInterval);
        }
        lobbyTimeoutInterval = setInterval(checkLobbyTimeout, 30000); // Check every 30 seconds
    }

    function checkLobbyTimeout() {
        // Skip check if page is hidden (dev tools, minimized, etc.)
        if (isPageHidden) {
            console.log('📄 Page is hidden, skipping timeout check');
            return;
        }

        const now = Date.now();
        const timeSinceLastUpdate = now - lastUpdateTime;
        
        // Only redirect after VERY long period of no updates (5+ minutes)
        // This prevents false timeouts from dev tools or brief pauses
        if (timeSinceLastUpdate > 300000) {
            console.warn('⏱️ No game updates for 5+ minutes, performing active lobby health check');
            
            // Perform active health check via server endpoint
            fetch(`/api/lobby/${lobbyId}/status`)
                .then(response => {
                    if (response.status === 404) {
                        // Lobby no longer exists
                        console.error('❌ Lobby status: GONE - Redirecting to lobby selection');
                        window.location.href = '/';
                        return null;
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data) return;
                    
                    if (data.status === 'gone') {
                        console.error('❌ Lobby status: GONE - Redirecting to lobby selection');
                        window.location.href = '/';
                    } else if (data.status === 'alive') {
                        console.log(`✅ Lobby status: ALIVE (${data.game_status}, ${data.player_count} players)`);
                        // Lobby is still active, keep playing
                    } else if (data.status === 'error') {
                        console.warn(`⚠️ Lobby status: ERROR - ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('❌ Failed to check lobby status:', error);
                    // On network error, don't immediately disconnect
                    // The Socket.IO connection will handle real disconnects
                });
        }
    }

    function updateLastActivity() {
        lastUpdateTime = Date.now();
    }

    function stopLobbyTimeoutCheck() {
        if (lobbyTimeoutInterval) {
            clearInterval(lobbyTimeoutInterval);
            lobbyTimeoutInterval = null;
        }
    }

    // Start checking for lobby timeout when page loads
    startLobbyTimeoutCheck();
    
    // ALWAYS wait for DOM elements to be available before signaling server
    // This ensures #scoreboards-container, #tributes-container, etc. exist
    console.log('[CLIENT_READY] Checking readyState:', document.readyState);
    console.log('[CLIENT_READY] Waiting to ensure all DOM elements are ready...');
    
    // Use a simple, robust wait mechanism
    function waitForDOMElements() {
        const required = ['scoreboards-container', 'tributes-container', 'game-log'];
        const missing = required.filter(id => !document.getElementById(id));
        
        if (missing.length === 0) {
            // All elements found - safe to signal server
            console.log('✅ [CLIENT_READY] All DOM elements ready, signaling client_ready');
            socket.emit('client_ready');
        } else {
            // Elements not ready yet, wait and retry
            console.log(`⏳ [CLIENT_READY] Waiting for elements: ${missing.join(', ')}`);
            setTimeout(waitForDOMElements, 50);
        }
    }
    
    // Start waiting for DOM elements
    waitForDOMElements();

    let tributeStatsFetched = false;
    let lastDisplayedStats = null;
    let lastTributeUpdateTime = 0;
    const TRIBUTE_UPDATE_THROTTLE_MS = 500;  // Only update every 500ms max

    // Socket event handlers
    socket.on('game_state_update', (data) => {
        try {
            console.log('Game state update:', data);
            console.log('Current player from update:', data.current_player);
            console.log('Tribute data from update:', data.current_player?.tribute_data);
            console.log('Game state:', data.game_state);
            console.log('Game state players:', data.game_state?.players);
            console.log('Game state players length:', data.game_state?.players?.length);
            
            updateLastActivity();
            gameState = data.game_state;
            currentPlayer = data.current_player;

            updateGameDisplay();

            // Display the current player's tribute status using game state data
            if (currentPlayer) {
                console.log('✓ Displaying current player stats:', currentPlayer);
                displayCurrentPlayerStats(currentPlayer);
                // Also update live stats display if it exists
                setTimeout(() => {
                    updateLiveStatsDisplay();
                }, 100); // Small delay to ensure DOM is updated
            }

            // Display all tributes (remaining tributes from gameState)
            if (gameState && gameState.players && gameState.players.length > 0) {
                console.log('✓ Displaying all tributes from gameState:', gameState.players.length, 'tributes');
                // Log first tribute to verify data structure
                console.log('First tribute sample:', gameState.players[0]);
                // Use updateTributeScoreboards for the main tribute display
                const tributeMap = {};
                gameState.players.forEach((p, idx) => {
                    tributeMap[idx] = p;
                });
                updateTributeScoreboards(tributeMap);
            } else {
                console.log('✗ No tributes in gameState. gameState:', gameState);
            }
        } catch (error) {
            console.error('[ERROR] game_state_update handler failed:', error);
            console.error('Stack:', error.stack);
        }
    });

    socket.on('tribute_updated', (data) => {
        console.log('Tribute updated:', data);
        // Throttle updates to prevent constant re-rendering
        const now = Date.now();
        if (now - lastTributeUpdateTime < TRIBUTE_UPDATE_THROTTLE_MS) {
            console.log('Tribute update throttled - too soon after last update');
            return;
        }
        lastTributeUpdateTime = now;
        
        // Re-fetch tribute stats when they change
        if (currentPlayer && currentPlayer.id) {
            console.log('Fetching updated tribute stats');
            fetchPlayerTributeStats(currentPlayer.id);
        }
    });

    // Catch-all event listener to see what events we're receiving
    socket.onAny((eventName, data) => {
        if (eventName !== 'ping' && eventName !== 'pong') {
            console.log('🌐 SOCKET EVENT RECEIVED:', eventName, data);
            
            // Check if this is a timer update in disguise
            if (eventName === 'spectator_update' && data?.message?.message_type === 'cornucopia_timer_update') {
                console.log('🏺 FOUND TIMER UPDATE IN SPECTATOR EVENT!');
                const timerData = data.message.data;
                if (timerData) {
                    console.log('🏺 Processing timer data from spectator_update:', timerData);
                    updateCornucopiaTimer(timerData);
                }
            }
        }
    });

    socket.on('game_update', (data) => {
        console.log('Game update:', data);
        updateLastActivity();

        const message = data.message; // The actual Aurora Engine message
        console.log('🔍 Checking message_type:', message?.message_type);

        if (message.message_type === 'game_started') {
            console.log('🎮 Game started event received, creating timer...');
            
            // Update phase display if phase info is available
            if (message.data && message.data.phase_info) {
                updatePhaseDisplay(message.data.phase_info);
            }
            
            // Show game started message
            gameStatus.innerHTML = '<div class="game-starting">Game has started! The Cornucopia awaits... <button onclick="testCornucopiaTimer()" style="margin-left: 10px; padding: 5px 10px;">Test Timer</button></div>';
            addToGameLog('The Hunger Games have begun!', message.timestamp || data.timestamp);
            
            // Create popup cornucopia timer
            console.log('🏺 About to create cornucopia popup timer...');
            createCornucopiaPopupTimer();
        } else if (message.message_type === 'game_event') {
            // Handle game events (Arena Events, PvP Events, etc.)
            const eventData = message.data.event_data || message.data;
            const eventType = eventData.event_category || eventData.event_type || message.data.event_type;
            const description = eventData.description || 'Unknown event';
            const narrative = eventData.narrative;

            // Add to game log with timestamp from the message
            const timestamp = message.timestamp || data.timestamp;
            addToGameLog(`${eventType}: ${description}`, timestamp);
            if (narrative) {
                addToGameLog(narrative, timestamp);
            }

            // Handle specific event types
            if (eventType === 'PvP Events') {
                // PvP events might require player actions
                if (eventData.participants && eventData.participants.includes(currentPlayer?.id)) {
                    showActionButtons(['fight', 'flee', 'ally']);
                }
            }
        } else if (message.message_type === 'cornucopia_timer_update') {
            // Handle cornucopia timer updates
            console.log('🏺 CORNUCOPIA TIMER UPDATE in game_update:');
            console.log('🏺 Full message object:', JSON.stringify(message, null, 2));
            console.log('🏺 message.data:', JSON.stringify(message.data, null, 2));
            console.log('🏺 message.data.remaining_seconds:', message.data?.remaining_seconds);
            console.log('🏺 message.data.total_seconds:', message.data?.total_seconds);
            
            const timerData = message.data;
            if (timerData) {
                console.log('🏺 Processing timer data from game_update:', timerData);
                console.log('🏺 About to call updateCornucopiaTimer function...');
                try {
                    updateCornucopiaTimer(timerData);
                    console.log('🏺 ✅ updateCornucopiaTimer called successfully');
                } catch (error) {
                    console.error('🏺 ❌ Error calling updateCornucopiaTimer:', error);
                }
            } else {
                console.warn('🏺 No timer data found in cornucopia_timer_update message');
            }
        } else if (message.message_type === 'phase_timer_update') {
            // Handle phase timer updates (for all phases)
            console.log('⏱️ PHASE TIMER UPDATE in game_update:', message.data);
            const timerData = message.data;
            if (timerData && timerData.seconds_remaining !== undefined) {
                updatePhaseTimer(timerData);
            } else {
                console.warn('⏱️ No valid timer data in phase_timer_update message');
            }
        } else if (message.message_type === 'phase_changed') {
            // Handle phase changes
            const phaseInfo = message.data.phase_info;
            const timestamp = message.timestamp || data.timestamp;
            addToGameLog(`Phase changed to: ${phaseInfo.name}`, timestamp);
            
            // Update the header display
            updatePhaseDisplay(phaseInfo);
            
            // Update game overview if it exists
            const gameOverview = document.getElementById('game-overview');
            if (gameOverview) {
                gameOverview.innerHTML = `<div class="phase-change">Current Phase: ${phaseInfo.name}</div>`;
            }
        } else if (message.message_type === 'cornucopia_death') {
            // Handle individual cornucopia death events
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('💀 Cornucopia death event:', eventData);
            
            // Add dramatic death message to game log
            addToGameLog(`⚔️ ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
            // Scoreboard will update automatically via engine_status_update
            
        } else if (message.message_type === 'cornucopia_injury') {
            // Handle cornucopia injury events (non-fatal combat)
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🩹 Cornucopia injury event:', eventData);
            
            // Add injury message to game log
            addToGameLog(`⚔️ ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
        } else if (message.message_type === 'cornucopia_bloodbath') {
            // Handle cornucopia bloodbath summary
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🏺 Cornucopia bloodbath summary:', eventData);
            
            // Add bloodbath summary to game log
            addToGameLog(`🏺 ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
            // Scoreboard will update automatically via engine_status_update
            
        } else if (message.message_type === 'tribute_decisions_cornucopia') {
            // Handle grouped cornucopia rush decisions
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🏃‍♂️ Tributes rushing to cornucopia:', eventData);
            
            // Add grouped message to game log
            addToGameLog(`🏃‍♂️ ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
        } else if (message.message_type === 'tribute_decisions_flee') {
            // Handle grouped flee decisions
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🏃‍♀️ Tributes fleeing:', eventData);
            
            // Add grouped message to game log
            addToGameLog(`🏃 ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
        } else if (message.message_type === 'tribute_decision') {
            // Handle individual tribute decisions (legacy support)
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🤔 Tribute decision:', eventData);
            
            // Add decision to game log
            addToGameLog(`${eventData.tribute_name} ${eventData.decision === 'cornucopia' ? 'rushes toward the cornucopia' : 'flees into the forest'}`, timestamp);
            
        } else if (message.message_type === 'cornucopia_gong') {
            // Handle the gong sound event
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🔔 Cornucopia gong:', eventData);
            
            // Add dramatic gong message
            addToGameLog('🔔 THE GONG SOUNDS!', timestamp);
            if (eventData.narrative) {
                addToGameLog(eventData.narrative, timestamp);
            }
            
            // Trigger horn animation in timer popup
            const popupTimer = document.getElementById('cornucopia-popup-timer');
            if (popupTimer) {
                console.log('🔔 Triggering horn animation from game_update');
                showCornucopiaHorn(popupTimer);
            }
            
            // Show cornucopia decisions section
            showCornucopiaDecisions();
            
        } else if (message.message_type === 'early_step_off') {
            // Handle early step-off landmine death
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('💥 Early step-off:', eventData);
            
            // Add dramatic death message
            addToGameLog(`💥 ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
            // Scoreboard will update automatically via engine_status_update
            
        } else if (message.message_type === 'tributes_fled') {
            // Handle fled tributes summary
            const timestamp = message.timestamp || data.timestamp;
            const eventData = message.data;
            
            console.log('🏃 Tributes fled:', eventData);
            
            // Add flee message
            addToGameLog(`🏃 ${eventData.message}`, timestamp);
            addToGameLog(eventData.narrative, timestamp);
            
        } else if (message.message_type === 'input_response') {
            // Handle input responses
            const timestamp = message.timestamp || data.timestamp;
            if (message.data.success) {
                addToGameLog(`Action completed: ${message.data.command_type}`, timestamp);
            } else {
                addToGameLog(`Action failed: ${message.data.reason}`, timestamp);
            }
        }
    });

    socket.on('engine_status_update', (data) => {
        console.log('Engine status update:', data);
        updateLastActivity();
        
        const engineStatus = data.engine_status;
        if (engineStatus && engineStatus.status) {
            // Update phase display in header if phase info is available
            if (engineStatus.phase_info && engineStatus.phase_info.phase_info) {
                updatePhaseDisplay(engineStatus.phase_info.phase_info);
            }
            
            // Update status display with engine information
            const statusDiv = document.createElement('div');
            statusDiv.className = 'engine-status';
            statusDiv.innerHTML = `
                <small>Engine: ${engineStatus.status} | 
                Phase: ${engineStatus.phase_info ? engineStatus.phase_info.phase_info.name : 'Unknown'} | 
                Events: ${engineStatus.total_events}</small>
            `;
            
            // Update existing status or add new one
            if (gameOverview) {
                const existingStatus = gameOverview.querySelector('.engine-status');
                if (existingStatus) {
                    existingStatus.remove();
                }
                gameOverview.appendChild(statusDiv);
            }
        }

        // Update tribute scoreboards if available (this also updates currentPlayer stats)
        if (data.tribute_scoreboards) {
            console.log('📊 Received tribute scoreboards:', Object.keys(data.tribute_scoreboards).length, 'tributes');
            console.log('[DEBUG_STATS] All tribute IDs:', Object.keys(data.tribute_scoreboards));
            updateTributeScoreboards(data.tribute_scoreboards);
            
            // Also update currentPlayer stats from scoreboards if we have a player ID
            if (currentPlayer && currentPlayer.id) {
                console.log('[DEBUG_STATS] Looking for currentPlayer.id:', currentPlayer.id, 'in scoreboards');
                const playerStats = data.tribute_scoreboards[currentPlayer.id];
                if (playerStats) {
                    console.log('[ENGINE_UPDATE] ✓ Found stats for currentPlayer, updating');
                    currentPlayer.health = playerStats.health;
                    currentPlayer.hunger = playerStats.hunger;
                    currentPlayer.thirst = playerStats.thirst;
                    currentPlayer.fatigue = playerStats.fatigue;
                    currentPlayer.sanity = playerStats.sanity;
                    currentPlayer.status = playerStats.status;
                    
                    // Trigger live stats update
                    setTimeout(() => {
                        updateLiveStatsDisplay();
                    }, 100);
                } else {
                    console.error('[DEBUG_STATS] ✗ currentPlayer.id NOT FOUND in tribute_scoreboards!');
                    console.error('[DEBUG_STATS] currentPlayer.id type:', typeof currentPlayer.id);
                    console.error('[DEBUG_STATS] First scoreboard key type:', typeof Object.keys(data.tribute_scoreboards)[0]);
                }
            } else {
                console.error('[DEBUG_STATS] ✗ No currentPlayer or currentPlayer.id not set');
            }
        } else {
            console.warn('⚠️ No tribute_scoreboards in engine_status_update');
        }
    });

    // Cornucopia event handlers
    socket.on('cornucopia_countdown_start', (data) => {
        console.log('🏺 Cornucopia countdown started:', data);
        updateLastActivity();
        
        // Handle nested data structure - timer data could be in data.message.data or data.data
        const timerData = data.message?.data || data.data || data;
        
        showCornucopiaCountdown(timerData);
        addToGameLog(timerData.message || 'Cornucopia countdown started', data.timestamp);
        
        // Also create popup timer for better visibility
        createCornucopiaPopupTimer();
        // Initialize with countdown data
        if (timerData) {
            console.log('🏺 Initializing popup timer with data:', timerData);
            updateCornucopiaTimer(timerData);
        }
    });

    socket.on('cornucopia_timer_update', (data) => {
        console.log('🏺 RAW EVENT DATA:', JSON.stringify(data, null, 2));
        
        // Handle different data structures - the actual timer data is in data.message.data
        const timerData = data.message?.data || data.data || data;
        
        console.log('🏺 EXTRACTED TIMER DATA:', JSON.stringify(timerData, null, 2));
        console.log('🏺 REMAINING SECONDS CHECK:', {
            'timerData.remaining_seconds': timerData?.remaining_seconds,
            'timerData.countdown_seconds': timerData?.countdown_seconds,
            'timerData.total_seconds': timerData?.total_seconds
        });
        
        if (timerData) {
            updateCornucopiaTimer(timerData);
        } else {
            console.warn('🏺 No timer data received in cornucopia_timer_update event');
        }
    });

    socket.on('phase_timer_update', (data) => {
        console.log('⏱️ Phase timer update:', data);
        updateLastActivity();
        
        // Extract timer data from message structure
        const timerData = data.message?.data || data.data || data;
        
        if (timerData && timerData.seconds_remaining !== undefined) {
            updatePhaseTimer(timerData);
        } else {
            console.warn('⏱️ No valid timer data in phase_timer_update');
        }
    });

    socket.on('tribute_decision', (data) => {
        console.log('🤔 Tribute decision:', data);
        updateLastActivity();
        displayTributeDecision(data.data);
    });

    socket.on('cornucopia_bloodbath', (data) => {
        console.log('⚔️ Cornucopia bloodbath:', data);
        updateLastActivity();
        displayBloodbathResults(data.data);
        addToGameLog(data.data.message, data.timestamp);
    });

    socket.on('tributes_fled', (data) => {
        console.log('🏃 Tributes fled cornucopia:', data);
        updateLastActivity();
        addToGameLog(data.data.message, data.timestamp);
    });

    socket.on('early_step_off', (data) => {
        console.log('💥 Early step off detected:', data);
        updateLastActivity();
        addToGameLog('A tribute stepped off their platform early!', data.timestamp);
        if (data.data.death_occurred) {
            addToGameLog('💥 The mines exploded! A tribute has been killed.', data.timestamp);
        }
    });

    socket.on('animation_events', (data) => {
        console.log('Animation events:', data);
        
        // Handle animation events for visual effects
        if (data.events && data.events.length > 0) {
            data.events.forEach(event => {
                if (event.event_category) {
                    // Add visual indicator for different event types
                    const eventIndicator = document.createElement('div');
                    eventIndicator.className = `event-indicator ${event.event_category.toLowerCase().replace(' ', '-')}`;
                    eventIndicator.textContent = event.event_category;
                    eventIndicator.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #ff4444;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        z-index: 1000;
                        animation: fadeOut 3s forwards;
                    `;
                    
                    document.body.appendChild(eventIndicator);
                    
                    setTimeout(() => {
                        if (eventIndicator.parentNode) {
                            eventIndicator.remove();
                        }
                    }, 3000);
                }
            });
        }
    });

    // Socket connection handlers
    socket.on('connect', () => {
        console.log('Game page: Socket connected');
        updateLastActivity();
    });

    socket.on('disconnect', () => {
        console.log('Game page: Socket disconnected - lobby may be unavailable');
        // Redirect to main lobby after a short delay
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    });

    socket.on('error', (error) => {
        console.error('Socket error:', error);
    });

    socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
    });

    // UI event handlers
    window.performAction = function(action) {
        socket.emit('player_action', { action: action });
        actionButtons.innerHTML = '<div class="loading">Processing action...</div>';
    };

    window.returnToLobby = function() {
        socket.emit('return_to_lobby');
        window.lobbyApp.showSection('lobby-section');
    };

    window.leaveGame = function() {
        if (confirm('Are you sure you want to leave the game?')) {
            socket.emit('leave_game');
            window.lobbyApp.showSection('login-section');
        }
    };

    // Functions
    function updateGameDisplay() {
        if (!gameState) return;

        // Update current round display
        const roundDisplay = document.getElementById('current-round');
        if (roundDisplay) {
            roundDisplay.textContent = gameState.day || 1;
        }

        // Log game status for debugging
        const aliveCount = gameState.players ? gameState.players.filter(p => p.alive).length : 0;
        const totalCount = gameState.players ? gameState.players.length : 0;
        console.log(`Game Status - Day ${gameState.day}, ${aliveCount}/${totalCount} alive, Status: ${gameState.status}`);

        // Update action buttons based on game state
        if (gameState.status === 'waiting_for_actions' && actionButtons) {
            showActionButtons(['move', 'search', 'rest', 'craft']);
        } else if (actionButtons) {
            actionButtons.innerHTML = '<div class="waiting">Waiting for other players...</div>';
        }
    }

    function updateGameDisplayWithData(gameData) {
        if (!gameData) return;

        // Update game status with comprehensive data
        if (gameOverview) {
            gameOverview.innerHTML = `
                <div class="game-info">
                    <div><span>Day:</span> <strong>${gameData.day}</strong></div>
                    <div><span>Phase:</span> <strong>${gameData.phase}</strong></div>
                    <div><span>Turn:</span> <strong>${gameData.turn}</strong></div>
                    <div><span>Active Tributes:</span> <strong>${gameData.active_tributes_count}/${gameData.total_tributes}</strong></div>
                    <div><span>Status:</span> <strong>${gameData.game_status}</strong></div>
                </div>
            `;
        }

        // Update player stats with detailed tribute information
        let statsHtml = '<div class="tributes-overview">';
        statsHtml += '<h3>Active Tributes</h3>';
        
        gameData.active_tributes.forEach(tribute => {
            const healthColor = tribute.health > 70 ? 'green' : tribute.health > 30 ? 'yellow' : 'red';
            const statusIndicators = [];
            
            if (tribute.bleeding !== 'none') statusIndicators.push(`Bleeding: ${tribute.bleeding}`);
            if (tribute.infection) statusIndicators.push('Infected');
            if (tribute.is_sick) statusIndicators.push(`Sick: ${tribute.sickness_type}`);
            
            statsHtml += `
                <div class="tribute-card">
                    <div class="tribute-header">
                        <span class="tribute-name">${tribute.name}</span>
                        <span class="tribute-district">District ${tribute.district}</span>
                    </div>
                    <div class="tribute-stats">
                        <div class="stat-row">
                            <span class="stat-label">Health:</span>
                            <span class="stat-value health-${healthColor}">${tribute.health}/100</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Sanity:</span>
                            <span class="stat-value">${tribute.sanity}/100</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Food:</span>
                            <span class="stat-value">${tribute.food}/100</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Water:</span>
                            <span class="stat-value">${tribute.water}/100</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Weapons:</span>
                            <span class="stat-value">${tribute.weapons.join(', ') || 'None'}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Kills:</span>
                            <span class="stat-value">${tribute.kills.length}</span>
                        </div>
                        ${statusIndicators.length > 0 ? 
                            `<div class="stat-row status-indicators">
                                <span class="stat-label">Status:</span>
                                <span class="stat-value">${statusIndicators.join(', ')}</span>
                            </div>` : ''}
                    </div>
                </div>
            `;
        });
        
        statsHtml += '</div>';

        // Update action buttons - for simulation, just show status
        actionButtons.innerHTML = '<div class="simulation-status">Simulation running... Watch the game unfold!</div>';
    }

    function showActionButtons(actions) {
        if (!actions || actions.length === 0) {
            actionButtons.innerHTML = '<div class="waiting">No actions available</div>';
            return;
        }

        const buttons = actions.map(action => {
            const actionName = action.charAt(0).toUpperCase() + action.slice(1);
            return `<button onclick="performAction('${action}')" class="btn btn-action">${actionName}</button>`;
        }).join('');

        actionButtons.innerHTML = buttons;
    }

    function addToGameLog(message, timestamp) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        let time = '';
        if (timestamp) {
            try {
                // Try parsing as ISO string first
                const date = new Date(timestamp);
                if (!isNaN(date.getTime())) {
                    time = date.toLocaleTimeString();
                } else {
                    // Fallback for Unix timestamp
                    const unixDate = new Date(timestamp * 1000);
                    time = unixDate.toLocaleTimeString();
                }
            } catch (e) {
                time = 'Invalid Date';
            }
        }
        
        // Convert newlines to <br> tags for multi-line messages
        const formattedMessage = message.replace(/\n/g, '<br>');
        entry.innerHTML = `<span class="timestamp">[${time}]</span> ${formattedMessage}`;

        gameLog.appendChild(entry);
        gameLog.scrollTop = gameLog.scrollHeight;
    }

    function updateTributeScoreboards(scoreboards) {
        if (!scoreboards) {
            console.warn('❌ updateTributeScoreboards: No scoreboards data provided');
            return;
        }

        const container = document.getElementById('tributes-container');
        if (!container) {
            console.warn('❌ updateTributeScoreboards: tributes-container not found in DOM');
            return;
        }

        // Update current player data if available in scoreboards
        if (currentPlayer && currentPlayer.id && scoreboards[currentPlayer.id]) {
            const updatedPlayerData = scoreboards[currentPlayer.id];
            console.log('[LIVE_STATS] Updating currentPlayer from scoreboards:', updatedPlayerData);
            
            // Update currentPlayer with latest stats
            currentPlayer.health = updatedPlayerData.health;
            currentPlayer.hunger = updatedPlayerData.hunger;
            currentPlayer.thirst = updatedPlayerData.thirst;
            currentPlayer.fatigue = updatedPlayerData.fatigue;
            currentPlayer.sanity = updatedPlayerData.sanity;
            currentPlayer.status = updatedPlayerData.status;
            currentPlayer.inventory = updatedPlayerData.inventory;
            currentPlayer.weapons = updatedPlayerData.weapons;
            currentPlayer.food_supplies = updatedPlayerData.food_supplies;
            currentPlayer.water_supplies = updatedPlayerData.water_supplies;
            
            // Update live stats display if container exists
            console.log('[LIVE_STATS] Current player updated, refreshing live stats display');
            setTimeout(() => {
                updateLiveStatsDisplay();
            }, 50);
        }

        // Clear existing scoreboards
        container.innerHTML = '';

        // Sort tributes: alive first, then by district
        const sortedTributes = Object.values(scoreboards).sort((a, b) => {
            // Fix: Use status instead of alive
            const aAlive = a.status === 'alive';
            const bAlive = b.status === 'alive';
            if (aAlive && !bAlive) return -1;
            if (!aAlive && bAlive) return 1;
            const aDistrict = a.district || a.tribute_data?.district || 0;
            const bDistrict = b.district || b.tribute_data?.district || 0;
            return aDistrict - bDistrict;
        });

        console.log(`✅ Rendering ${sortedTributes.length} tribute scoreboard(s) in tributes-container`);

        sortedTributes.forEach(tribute => {
            const scoreboard = createTributeScoreboard(tribute);
            container.appendChild(scoreboard);
        });
    }

    function createTributeScoreboard(tribute) {
        const div = document.createElement('div');
        // Fix: Check if tribute.status is 'alive' properly
        const isAlive = tribute.status === 'alive';
        div.className = `tribute-scoreboard ${isAlive ? 'alive' : 'dead'}`;

        // Extract stats with defaults
        const health = tribute.health !== undefined ? tribute.health : 100;
        const sanity = tribute.sanity !== undefined ? tribute.sanity : 100;
        const hunger = tribute.hunger !== undefined ? tribute.hunger : 0;
        const thirst = tribute.thirst !== undefined ? tribute.thirst : 0;
        const fatigue = tribute.fatigue !== undefined ? tribute.fatigue : 0;
        const name = tribute.name || tribute.tribute_data?.name || 'Unknown';
        const district = tribute.district || tribute.tribute_data?.district || 'N/A';
        // Fix: Use tribute.status instead of tribute.alive
        const status = isAlive ? 'ALIVE' : 'DEAD';

        div.innerHTML = `
            <div class="tribute-scoreboard-header">
                <div class="tribute-name-district">
                    <span class="tribute-name">${name}</span>
                    <span class="tribute-district">D${district}</span>
                </div>
                <span class="tribute-status ${status.toLowerCase()}">${status}</span>
            </div>

            <div class="tribute-scoreboard-stats">
                <div class="stat-mini">
                    <label>HP</label>
                    <div class="stat-bar-mini">
                        <div class="stat-fill" style="width: ${health}%; background: #4CAF50;"></div>
                    </div>
                    <span>${health}</span>
                </div>

                <div class="stat-mini">
                    <label>Sanity</label>
                    <div class="stat-bar-mini">
                        <div class="stat-fill" style="width: ${sanity}%; background: #9C27B0;"></div>
                    </div>
                    <span>${sanity}</span>
                </div>

                <div class="stat-mini">
                    <label>Hunger</label>
                    <div class="stat-bar-mini">
                        <div class="stat-fill" style="width: ${hunger}%; background: #FF9800;"></div>
                    </div>
                    <span>${hunger}</span>
                </div>

                <div class="stat-mini">
                    <label>Thirst</label>
                    <div class="stat-bar-mini">
                        <div class="stat-fill" style="width: ${thirst}%; background: #2196F3;"></div>
                    </div>
                    <span>${thirst}</span>
                </div>
            </div>

            <div class="tribute-inventory">
                ${tribute.equipped_weapon ? `<div class="weapon">⚔️ ${tribute.equipped_weapon}</div>` : ''}
                ${tribute.inventory && tribute.inventory.length > 0 ?
                    `<div class="items">${tribute.inventory.slice(0, 3).map(i => `<span>${i}</span>`).join('')}${tribute.inventory.length > 3 ? `<span>+${tribute.inventory.length - 3}</span>` : ''}</div>` :
                    ''
                }
            </div>
        `;

        return div;
    }

    // Initialize game view
    if (window.lobbyApp.gameStarted) {
        socket.emit('request_game_state');
    }

    function displayCurrentPlayerStats(player) {
        console.log('[CURRENT_PLAYER_STATS] Displaying:', player);
        const scoreboardsContainer = document.getElementById('scoreboards-container');
        
        if (!scoreboardsContainer) {
            console.error('[CURRENT_PLAYER_STATS] ✗ scoreboards-container not found!');
            return;
        }

        if (!player) {
            console.error('[CURRENT_PLAYER_STATS] ✗ No player data');
            scoreboardsContainer.innerHTML = '<p>No player data available</p>';
            return;
        }

        // Get tribute info
        const tribute = player.tribute_data || player;
        const tributeName = tribute.name || player.name || 'Unknown';
        const tributeDistrict = tribute.district || 'N/A';
        const tributeAge = tribute.age || '?';
        const tributeGender = tribute.gender || '?';

        // Get stats
        const health = player.health !== undefined ? player.health : 100;
        const hunger = player.hunger !== undefined ? player.hunger : 0;
        const thirst = player.thirst !== undefined ? player.thirst : 0;
        const sanity = tribute.sanity !== undefined ? tribute.sanity : 100;
        const fatigue = tribute.fatigue !== undefined ? tribute.fatigue : 0;

        const statsHtml = `
            <div class="current-player-stats">
                <div class="player-header">
                    <h4>${tributeName}</h4>
                    <div class="player-info">
                        <span class="district">D${tributeDistrict}</span>
                        <span class="age-gender">${tributeAge}y, ${tributeGender}</span>
                    </div>
                </div>

                <div class="vital-stats">
                    <div class="stat-item">
                        <label>Health</label>
                        <div class="stat-bar">
                            <div class="stat-fill health-fill" style="width: ${health}%"></div>
                        </div>
                        <span class="stat-value">${health}/100</span>
                    </div>

                    <div class="stat-item">
                        <label>Sanity</label>
                        <div class="stat-bar">
                            <div class="stat-fill sanity-fill" style="width: ${sanity}%"></div>
                        </div>
                        <span class="stat-value">${sanity}/100</span>
                    </div>

                    <div class="stat-row-half">
                        <div class="stat-item">
                            <label>Hunger</label>
                            <div class="stat-bar">
                                <div class="stat-fill hunger-fill" style="width: ${hunger}%"></div>
                            </div>
                            <span class="stat-value">${hunger}/100</span>
                        </div>
                        <div class="stat-item">
                            <label>Thirst</label>
                            <div class="stat-bar">
                                <div class="stat-fill thirst-fill" style="width: ${thirst}%"></div>
                            </div>
                            <span class="stat-value">${thirst}/100</span>
                        </div>
                    </div>

                    <div class="stat-item">
                        <label>Fatigue</label>
                        <div class="stat-bar">
                            <div class="stat-fill fatigue-fill" style="width: ${fatigue}%"></div>
                        </div>
                        <span class="stat-value">${fatigue}/100</span>
                    </div>
                </div>

                <div class="inventory-section">
                    <h5>Inventory</h5>
                    ${player.inventory && player.inventory.length > 0 ?
                        `<div class="inventory-list">
                            ${player.inventory.map(item => `<span class="inventory-item">${item}</span>`).join('')}
                        </div>` :
                        '<p class="empty">No items</p>'
                    }
                </div>

                <div class="weapons-section">
                    <h5>Weapons</h5>
                    ${player.equipped_weapon ? `<div class="equipped-weapon">⚔️ ${player.equipped_weapon}</div>` : ''}
                    ${player.weapons && player.weapons.length > 0 ?
                        `<div class="weapons-list">
                            ${player.weapons.map(w => `<span class="weapon-item">${w}</span>`).join('')}
                        </div>` :
                        '<p class="empty">No weapons</p>'
                    }
                </div>
            </div>
        `;

        console.log('[CURRENT_PLAYER_STATS] ✓ Rendering player stats');
        scoreboardsContainer.innerHTML = statsHtml;
    }

    async function fetchPlayerTributeStats(playerId, retryCount = 0) {
        try {
            console.log('[FETCH_STATS] Fetching for player:', playerId, 'retry:', retryCount);
            const response = await fetch(`/api/tribute/${playerId}`);
            console.log('[FETCH_STATS] Response status:', response.status, 'ok:', response.ok);
            if (response.ok) {
                const tributeData = await response.json();
                console.log('[FETCH_STATS] ✅ Data received with skill_priority:', tributeData.skill_priority?.length, 'skills');
                console.log('[FETCH_STATS] Full data:', tributeData);
                displayPlayerTributeStats(tributeData);
            } else if (response.status === 404 && retryCount < 3) {
                console.log('[FETCH_STATS] ⚠️ Not found (404), retrying in 2 seconds...');
                setTimeout(() => fetchPlayerTributeStats(playerId, retryCount + 1), 2000);
            } else {
                console.error('[FETCH_STATS] ❌ Failed - status:', response.status);
                const errorText = await response.text();
                console.error('[FETCH_STATS] Error response:', errorText);
            }
        } catch (error) {
            console.error('[FETCH_STATS] ❌ Exception:', error);
            if (retryCount < 3) {
                console.log('[FETCH_STATS] Retrying in 2 seconds...');
                setTimeout(() => fetchPlayerTributeStats(playerId, retryCount + 1), 2000);
            }
        }
    }

    function displayPlayerTributeStats(data) {
        console.log('[DISPLAY_STATS] ⏱️ Called at', new Date().toLocaleTimeString());
        console.log('[DISPLAY_STATS] Data:', data);
        const scoreboardsContainer = document.getElementById('scoreboards-container');
        
        if (!scoreboardsContainer) {
            console.error('[DISPLAY_STATS] ✗ scoreboards-container not found!');
            return;
        }

        if (!data) {
            console.error('[DISPLAY_STATS] ✗ No data provided');
            scoreboardsContainer.innerHTML = '<p>No tribute data available</p>';
            return;
        }

        // Store/update currentPlayer with this data and ensure we have an ID
        if (!currentPlayer) {
            currentPlayer = {};
        }
        const oldId = currentPlayer.id;
        currentPlayer.id = data.id || data.tribute_id || currentPlayer.id;
        currentPlayer.name = data.name || currentPlayer.name;
        currentPlayer.district = data.district || currentPlayer.district;
        currentPlayer.tribute_data = data;
        
        console.log('[DISPLAY_STATS] currentPlayer.id updated:', {
            old: oldId,
            new: currentPlayer.id,
            type: typeof currentPlayer.id,
            source_data_id: data.id,
            source_tribute_id: data.tribute_id
        });

        // Extract data - handle both formats
        const tributeName = data.name || 'Unknown';
        const tributeDistrict = data.district || 1;
        const tributeAge = data.age || 16;
        const tributeGender = data.gender || 'Unknown';
        
        // Get skills - try multiple possible locations
        let ratings = {};
        if (data.final_ratings) {
            ratings = data.final_ratings;
        } else if (data.skills) {
            ratings = data.skills;
        }
        
        console.log('[DISPLAY_STATS] Rendering with', Object.keys(ratings).length, 'skills and', data.skill_priority?.length, 'priority skills');
        
        // Create tribute stats display - compact version for sidebar with LIVE STATS
        const statsHtml = `
            <div class="player-tribute-stats">
                <div class="tribute-header">
                    <h4>${tributeName}</h4>
                    <div class="tribute-info-compact">
                        <div>District ${tributeDistrict}</div>
                        <div>${tributeAge} yrs, ${tributeGender}</div>
                    </div>
                </div>
                
                <!-- LIVE GAME STATS SECTION -->
                <div class="live-stats-section">
                    <strong>Current Status:</strong>
                    <div id="live-stats-container">
                        <div class="loading-stats">Waiting for live stats...</div>
                    </div>
                </div>
                
                ${data.skill_priority && data.skill_priority.length > 0 ? `
                    <div class="skill-priority-section">
                        <strong>Skill Priority:</strong>
                        <div class="skill-priority-list">
                            ${data.skill_priority.map((skill, index) => {
                                const rating = ratings[skill] || 0;
                                const percentage = Math.min(100, (rating / 10) * 100);
                                return `
                                    <div class="priority-skill-item">
                                        <span class="priority-number">${index + 1}</span>
                                        <span class="priority-skill-name">${skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
                                        <div class="priority-skill-bar">
                                            <div class="priority-skill-fill" style="width: ${percentage}%"></div>
                                        </div>
                                        <span class="priority-skill-rating">${Math.max(1, Math.min(10, rating))}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="tribute-skills-compact">
                    <strong>All Skills:</strong>
                    ${Object.entries(ratings).length > 0 ?
                        Object.entries(ratings)
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 8)
                            .map(([skill, rating]) => {
                                const percentage = Math.min(100, (Math.max(0, rating) / 10) * 100);
                                return `
                                    <div class="skill-item-compact">
                                        <span class="skill-name">${skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
                                        <div class="skill-bar-compact">
                                            <div class="skill-fill-compact" style="width: ${percentage}%"></div>
                                        </div>
                                        <span class="skill-rating-compact">${Math.max(1, Math.min(10, rating))}</span>
                                    </div>
                                `;
                            }).join('') :
                        '<div>No skills data available</div>'
                    }
                </div>
                ${data.district_bonuses && Object.keys(data.district_bonuses).length > 0 ?
                    `<div class="district-bonuses-compact">
                        <strong>Bonuses:</strong>
                        ${Object.entries(data.district_bonuses)
                            .filter(([skill, bonus]) => bonus !== 0)
                            .map(([skill, bonus]) => `<span class="bonus ${bonus > 0 ? 'positive' : 'negative'}">${skill.substring(0, 3)}: ${bonus > 0 ? '+' : ''}${bonus}</span>`)
                            .join(', ')}
                    </div>` : ''}
            </div>
        `;

        console.log('[DISPLAY_STATS] ✓ Generated HTML, inserting into DOM');
        scoreboardsContainer.innerHTML = statsHtml;
        console.log('[DISPLAY_STATS] ✓ Successfully displayed tribute stats');
        
        // Update live stats after DOM is updated - use setTimeout to ensure container exists
        setTimeout(() => {
            updateLiveStatsDisplay();
        }, 50);
    }

    // New function to update the live stats section with current player game data
    function updateLiveStatsDisplay() {
        const liveStatsContainer = document.getElementById('live-stats-container');
        if (!liveStatsContainer) {
            console.warn('[LIVE_STATS] No live-stats-container found - player tribute stats may not be rendered yet');
            return;
        }

        if (!currentPlayer) {
            console.log('[LIVE_STATS] No current player data available');
            liveStatsContainer.innerHTML = '<div class="loading-stats">Waiting for live stats...</div>';
            return;
        }

        console.log('[LIVE_STATS] Updating with currentPlayer:', currentPlayer);

        // Extract live stats from current player
        const health = currentPlayer.health !== undefined ? currentPlayer.health : 100;
        const hunger = currentPlayer.hunger !== undefined ? currentPlayer.hunger : 0;
        const thirst = currentPlayer.thirst !== undefined ? currentPlayer.thirst : 0;
        const fatigue = currentPlayer.fatigue !== undefined ? currentPlayer.fatigue : 0;
        const sanity = currentPlayer.sanity !== undefined ? currentPlayer.sanity : 100;
        // Fix: Use currentPlayer.status instead of currentPlayer.alive
        const status = currentPlayer.status === 'alive' ? 'ALIVE' : 'DEAD';
        
        console.log('[LIVE_STATS] Stats - Health:', health, 'Status:', status, 'Hunger:', hunger, 'Thirst:', thirst);
        
        // Determine status class for coloring
        let statusClass = 'status-alive';
        // Fix: Use currentPlayer.status instead of currentPlayer.alive
        if (currentPlayer.status !== 'alive') {
            statusClass = 'status-dead';
        } else if (health < 25) {
            statusClass = 'status-critical';
        } else if (health < 50) {
            statusClass = 'status-injured';
        }

        const liveStatsHtml = `
            <div class="live-player-stats">
                <div class="status-indicator ${statusClass}">${status}</div>
                
                <div class="vital-stats-compact">
                    <div class="stat-item-live">
                        <label>Health</label>
                        <div class="stat-bar-live">
                            <div class="stat-fill-live health-fill" style="width: ${health}%"></div>
                        </div>
                        <span class="stat-value-live">${health}</span>
                    </div>

                    <div class="stat-item-live">
                        <label>Sanity</label>
                        <div class="stat-bar-live">
                            <div class="stat-fill-live sanity-fill" style="width: ${sanity}%"></div>
                        </div>
                        <span class="stat-value-live">${sanity}</span>
                    </div>

                    <div class="stat-row-live">
                        <div class="stat-item-live">
                            <label>Hunger</label>
                            <div class="stat-bar-live">
                                <div class="stat-fill-live hunger-fill" style="width: ${hunger}%"></div>
                            </div>
                            <span class="stat-value-live">${hunger}</span>
                        </div>
                        <div class="stat-item-live">
                            <label>Thirst</label>
                            <div class="stat-bar-live">
                                <div class="stat-fill-live thirst-fill" style="width: ${thirst}%"></div>
                            </div>
                            <span class="stat-value-live">${thirst}</span>
                        </div>
                    </div>

                    <div class="stat-item-live">
                        <label>Fatigue</label>
                        <div class="stat-bar-live">
                            <div class="stat-fill-live fatigue-fill" style="width: ${fatigue}%"></div>
                        </div>
                        <span class="stat-value-live">${fatigue}</span>
                    </div>
                </div>

                <div class="equipment-compact">
                    ${currentPlayer.equipped_weapon ? `<div class="equipped-weapon">⚔️ ${currentPlayer.equipped_weapon}</div>` : '<div class="no-weapon">🤏 Unarmed</div>'}
                    ${currentPlayer.inventory && currentPlayer.inventory.length > 0 ?
                        `<div class="inventory-items">📦 ${currentPlayer.inventory.slice(0, 3).join(', ')}${currentPlayer.inventory.length > 3 ? ` (+${currentPlayer.inventory.length - 3} more)` : ''}</div>` :
                        '<div class="no-items">📦 No items</div>'
                    }
                </div>
            </div>
        `;

        liveStatsContainer.innerHTML = liveStatsHtml;
        console.log('[LIVE_STATS] ✓ Updated live stats display');
    }

    // Display all tributes in the remaining tributes section
    function displayAllTributes(tributes, currentPlayerId) {
        console.log('[DISPLAY_TRIBUTES] Called with:', tributes?.length, 'tributes, current player:', currentPlayerId);
        const tributesContainer = document.getElementById('tributes-container');
        
        if (!tributesContainer) {
            console.error('[DISPLAY_TRIBUTES] ✗ Tributes container not found!');
            return;
        }

        if (!tributes || tributes.length === 0) {
            console.warn('[DISPLAY_TRIBUTES] No tributes to display');
            tributesContainer.innerHTML = '<p>No tributes available yet</p>';
            return;
        }

        console.log('[DISPLAY_TRIBUTES] Building cards for', tributes.length, 'tributes');

        // Create cards for all tributes
        const tributeCards = tributes.map((tribute, index) => {
            try {
                const isCurrent = tribute.id === currentPlayerId;
                // Fix: Use tribute.status instead of tribute.alive
                const isAlive = tribute.status === 'alive';
                const cardClass = `tribute-card ${isCurrent ? 'current-player' : ''} ${!isAlive ? 'dead-tribute' : 'alive-tribute'}`;
                
                // Get skills - handle both direct skills and nested tribute_data
                let tributeSkills = {};
                if (tribute.tribute_data && tribute.tribute_data.skills) {
                    tributeSkills = tribute.tribute_data.skills;
                } else if (tribute.skills) {
                    tributeSkills = tribute.skills;
                }

                const skillsHtml = tributeSkills && Object.keys(tributeSkills).length > 0 ?
                    Object.entries(tributeSkills)
                        .slice(0, 5)  // Show top 5 skills
                        .map(([skill, rating]) => {
                            const percentage = Math.min(100, (rating / 10) * 100);
                            return `
                                <div class="skill-bar">
                                    <span class="skill-label">${skill}</span>
                                    <div class="skill-gauge">
                                        <div class="skill-fill" style="width: ${percentage}%"></div>
                                    </div>
                                    <span class="skill-value">${rating}</span>
                                </div>
                            `;
                        }).join('') :
                    '<p class="no-skills">No skills recorded</p>';

                // Get tribute name and info - handle nested structure
                const tributeName = tribute.name || tribute.tribute_data?.name || 'Unknown';
                const tributeDistrict = tribute.district || tribute.tribute_data?.district || 'N/A';
                const tributeAge = tribute.age || tribute.tribute_data?.age || '?';
                const tributeGender = tribute.gender || tribute.tribute_data?.gender || '?';
                const statusBadge = isAlive ? 
                    '<span class="badge-status alive">ALIVE</span>' : 
                    '<span class="badge-status dead">DEAD</span>';

                console.log(`[DISPLAY_TRIBUTES] Card ${index}: ${tributeName} from District ${tributeDistrict} - ${isAlive ? 'ALIVE' : 'DEAD'}`);

                return `
                    <div class="${cardClass}">
                        <div class="tribute-card-header">
                            <h4 class="tribute-name">${tributeName}</h4>
                            <div class="tribute-badges">
                                ${isCurrent ? '<span class="badge-current">YOUR TRIBUTE</span>' : ''}
                                ${statusBadge}
                            </div>
                        </div>
                        <div class="tribute-card-info">
                            <div class="info-row">
                                <span class="label">District:</span>
                                <span class="value">${tributeDistrict}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Age:</span>
                                <span class="value">${tributeAge}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Gender:</span>
                                <span class="value">${tributeGender}</span>
                            </div>
                        </div>
                        <div class="tribute-card-skills">
                            <strong>Skills:</strong>
                            ${skillsHtml}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error(`[DISPLAY_TRIBUTES] Error building card ${index}:`, error);
                return `<div class="tribute-card error">Error displaying tribute</div>`;
            }
        }).join('');

        console.log('[DISPLAY_TRIBUTES] ✓ Generated', tributes.length, 'cards');
        tributesContainer.innerHTML = tributeCards;
        console.log('[DISPLAY_TRIBUTES] ✓ Cards inserted into DOM');
    }

    // Check if current user is the host/admin
    function isAdmin() {
        // This would need to be set from the server - check if currentPlayerId matches lobby host
        // For now, we'll add an admin check based on lobby data
        return window.lobbyApp && window.lobbyApp.isHost;
    }

    // Show admin controls if user is host
    function updateAdminControls() {
        const adminPanel = document.getElementById('admin-controls');
        if (adminPanel) {
            if (isAdmin()) {
                adminPanel.style.display = 'block';
            } else {
                adminPanel.style.display = 'none';
            }
        }
    }

    // Generate AI tributes for remaining districts (admin only)
    window.generateRemainingTributes = function() {
        const statusDiv = document.getElementById('admin-status');
        if (!statusDiv) return;

        statusDiv.className = 'admin-status';
        statusDiv.textContent = 'Generating AI tributes for remaining districts...';

        console.log('Requesting AI tribute generation for remaining districts');
        
        // Emit request to server to generate AI tributes for remaining districts
        socket.emit('generate_remaining_tributes', {}, (response) => {
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
    };

    // Generate a single random tribute (admin only)
    window.generateRandomTribute = function() {
        const statusDiv = document.getElementById('admin-status');
        if (!statusDiv) return;

        statusDiv.className = 'admin-status';
        statusDiv.textContent = 'Generating random tribute...';

        // Find first player without tribute
        const playerNeedingTribute = gameState?.players?.find(p => 
            !p.tribute_data || !p.tribute_data.name
        );

        if (!playerNeedingTribute) {
            statusDiv.className = 'admin-status success';
            statusDiv.textContent = '✓ All tributes already created!';
            return;
        }

        console.log(`Generating random tribute for player: ${playerNeedingTribute.id}`);
        
        socket.emit('generate_random_tribute', {
            player_id: playerNeedingTribute.id
        }, (response) => {
            if (response && response.success) {
                statusDiv.className = 'admin-status success';
                statusDiv.textContent = `✓ Generated tribute for ${response.tribute_name || 'new tribute'}!`;
            } else {
                statusDiv.className = 'admin-status error';
                statusDiv.textContent = `✗ Error: ${response?.message || 'Failed to generate tribute'}`;
            }
        });
    };

    // Show admin controls on page load
    updateAdminControls();

    // Listen for lobby updates to refresh admin controls
    socket.on('lobby_updated', () => {
        updateAdminControls();
    });

} // END OF initializeGamePage function

// ============================================================================
// CORNUCOPIA UI FUNCTIONS
// ============================================================================

function createCornucopiaPopupTimer() {
    console.log('🏺 Creating cornucopia popup timer...');
    
    // Check if timer already exists - don't create duplicates
    const existingTimer = document.getElementById('cornucopia-popup-timer');
    if (existingTimer) {
        console.log('🏺 Timer already exists, not creating duplicate');
        // Just make sure it's visible
        existingTimer.classList.add('show');
        return;
    }
    
    // Create popup timer overlay
    const timerPopup = document.createElement('div');
    timerPopup.id = 'cornucopia-popup-timer';
    timerPopup.className = 'cornucopia-popup-timer';
    timerPopup.innerHTML = `
        <div class="popup-timer-container">
            <div class="popup-timer-title">🏺 Cornucopia Countdown</div>
            <div class="popup-timer-display" id="popup-timer-display">--</div>
            <div class="popup-timer-message" id="popup-timer-message">Preparing countdown...</div>
            <div class="popup-timer-warning">⚠️ Do not step off your platform early!</div>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(timerPopup);
    console.log('🏺 Timer popup added to body');
    
    // Verify elements were created
    const verifyDisplay = document.getElementById('popup-timer-display');
    const verifyMessage = document.getElementById('popup-timer-message');
    const verifyTimer = document.getElementById('cornucopia-popup-timer');
    
    console.log('🏺 Verification after creation:');
    console.log('🏺 - Timer popup exists:', !!verifyTimer);
    console.log('🏺 - Display element exists:', !!verifyDisplay);
    console.log('🏺 - Message element exists:', !!verifyMessage);
    console.log('🏺 - Display element textContent:', verifyDisplay?.textContent);
    
    // Show with animation
    setTimeout(() => {
        timerPopup.classList.add('show');
        console.log('🏺 Timer popup should now be visible');
    }, 100);
    
    console.log('✅ Cornucopia popup timer created successfully');
}

// Global timer state for smooth countdown
let cornucopiaTimerState = {
    lastServerTime: null,
    lastUpdateTime: null,
    smoothInterval: null
};

function updateCornucopiaTimer(timerData) {
    console.log('🏺 UPDATE FUNCTION CALLED');
    console.log('🏺 timerData type:', typeof timerData);
    console.log('🏺 timerData keys:', Object.keys(timerData || {}));
    console.log('🏺 timerData.remaining_seconds (exact):', timerData?.remaining_seconds);
    
    // Store server update time for smooth countdown
    cornucopiaTimerState.lastServerTime = timerData?.remaining_seconds;
    cornucopiaTimerState.lastUpdateTime = Date.now();
    
    // Start smooth countdown if not already running
    if (!cornucopiaTimerState.smoothInterval && timerData?.remaining_seconds > 0) {
        startSmoothCountdown();
    }
    
    // Try to access the field in different ways
    let remainingSeconds = '--';
    
    console.log('🏺 Trying to extract remaining seconds...');
    console.log('🏺 Direct access test: timerData.remaining_seconds =', timerData.remaining_seconds);
    
    if (timerData && typeof timerData === 'object') {
        // Simple direct access - prioritize remaining_seconds since that's what the server sends
        if (timerData.remaining_seconds !== undefined && timerData.remaining_seconds !== null) {
            remainingSeconds = timerData.remaining_seconds;
            console.log('🏺 ✅ Using remaining_seconds:', remainingSeconds);
        } else if (timerData.countdown_seconds !== undefined && timerData.countdown_seconds !== null) {
            remainingSeconds = timerData.countdown_seconds;
            console.log('🏺 ✅ Using countdown_seconds:', remainingSeconds);
        } else if (timerData.total_seconds !== undefined && timerData.total_seconds !== null) {
            remainingSeconds = timerData.total_seconds;
            console.log('🏺 ✅ Using total_seconds:', remainingSeconds);
        } else {
            console.log('🏺 ❌ No valid time field found. Available fields:', Object.keys(timerData));
            console.log('🏺 Values check:');
            console.log('  - remaining_seconds:', timerData.remaining_seconds, '(type:', typeof timerData.remaining_seconds, ')');
            console.log('  - countdown_seconds:', timerData.countdown_seconds, '(type:', typeof timerData.countdown_seconds, ')');
            console.log('  - total_seconds:', timerData.total_seconds, '(type:', typeof timerData.total_seconds, ')');
        }
    } else {
        console.log('🏺 ❌ timerData is not a valid object:', timerData);
    }
    
    console.log('🏺 FINAL VALUE TO DISPLAY:', remainingSeconds);
    
    updateTimerDisplay(remainingSeconds, timerData.message);
    
    // Handle countdown completion
    if (remainingSeconds <= 0 || timerData.phase === 'completed' || timerData.phase === 'decision') {
        console.log('🏺 Countdown completed! Starting horn animation...');
        stopSmoothCountdown();
        const popupTimer = document.getElementById('cornucopia-popup-timer');
        if (popupTimer) {
            showCornucopiaHorn(popupTimer);
        }
    }
}

function startSmoothCountdown() {
    console.log('🏺 Starting smooth countdown animation');
    cornucopiaTimerState.smoothInterval = setInterval(() => {
        if (!cornucopiaTimerState.lastServerTime || !cornucopiaTimerState.lastUpdateTime) return;
        
        const elapsed = (Date.now() - cornucopiaTimerState.lastUpdateTime) / 1000;
        const smoothTime = Math.max(0, cornucopiaTimerState.lastServerTime - elapsed);
        
        // Only update if we have elements and time is reasonable
        if (smoothTime >= 0 && smoothTime !== cornucopiaTimerState.lastDisplayedTime) {
            updateTimerDisplay(Math.ceil(smoothTime), 'Countdown in progress...');
            cornucopiaTimerState.lastDisplayedTime = smoothTime;
        }
        
        // Stop if time reaches 0
        if (smoothTime <= 0) {
            stopSmoothCountdown();
        }
    }, 100); // Update every 100ms for smooth countdown
}

function stopSmoothCountdown() {
    if (cornucopiaTimerState.smoothInterval) {
        clearInterval(cornucopiaTimerState.smoothInterval);
        cornucopiaTimerState.smoothInterval = null;
        console.log('🏺 Stopped smooth countdown');
    }
}

function updateTimerDisplay(remainingSeconds, message) {
    // Check if timer popup exists
    const popupTimer = document.getElementById('cornucopia-popup-timer');
    const popupTimerDisplay = document.getElementById('popup-timer-display');
    const popupTimerMessage = document.getElementById('popup-timer-message');
    
    // If timer doesn't exist, create it first
    if (!popupTimer) {
        console.log('🏺 Timer popup not found, creating it...');
        createCornucopiaPopupTimer();
        // Small delay to ensure DOM is updated, then re-get elements
        setTimeout(() => {
            console.log('🏺 Retrying update after timer creation...');
            updateTimerDisplay(remainingSeconds, message);
        }, 200);
        return;
    }
    
    // Now update the existing timer
    if (popupTimerDisplay && popupTimerMessage && popupTimer) {
        console.log('🏺 About to update display with value:', remainingSeconds);
        
        // Update timer display
        popupTimerDisplay.textContent = remainingSeconds;
        popupTimerMessage.textContent = message || 'Countdown in progress...';
        
        console.log('🏺 ✅ Updated display! Current textContent:', popupTimerDisplay.textContent);
        
        // Apply visual effects based on remaining time
        popupTimerDisplay.className = 'popup-timer-display';
        popupTimer.className = 'cornucopia-popup-timer show'; // Reset classes
        
        if (remainingSeconds <= 10 && remainingSeconds > 0) {
            popupTimerDisplay.classList.add('countdown-critical');
            popupTimer.classList.add('critical');
        } else if (remainingSeconds <= 30 && remainingSeconds > 0) {
            popupTimerDisplay.classList.add('countdown-warning');
            popupTimer.classList.add('warning');
        }
    } else {
        console.warn('🏺 Timer popup elements not found after creation attempt');
        console.log('🏺 popupTimer:', !!popupTimer);
        console.log('🏺 popupTimerDisplay:', !!popupTimerDisplay);  
        console.log('🏺 popupTimerMessage:', !!popupTimerMessage);
    }
    
    // Update the main countdown timer in game log (if it exists)
    const timerElement = document.getElementById('countdown-timer');
    if (timerElement) {
        const remainingSeconds = timerData.remaining_seconds !== undefined ? timerData.remaining_seconds : 
                                timerData.countdown_seconds !== undefined ? timerData.countdown_seconds :
                                timerData.total_seconds !== undefined ? timerData.total_seconds : '--';
        timerElement.textContent = remainingSeconds;
        
        // Add visual effects based on time remaining
        if (remainingSeconds <= 10 && remainingSeconds > 0) {
            timerElement.classList.add('countdown-critical');
        } else if (remainingSeconds <= 30 && remainingSeconds > 0) {
            timerElement.classList.add('countdown-warning');
        }
    }
    
    // Update message in main timer
    const messageElement = document.querySelector('.countdown-message');
    if (messageElement) {
        messageElement.textContent = timerData.message || 'Countdown in progress...';
    }
}

function updatePhaseTimer(timerData) {
    console.log('⏱️ Updating phase timer:', timerData);
    
    // Get or create phase timer display
    let phaseTimerElement = document.getElementById('phase-timer-display');
    
    if (!phaseTimerElement) {
        // Create the phase timer display if it doesn't exist
        console.log('⏱️ Creating phase timer display element');
        
        // Find game overview or create container for phase timer
        const gameOverview = document.getElementById('game-overview');
        if (gameOverview) {
            const timerContainer = document.createElement('div');
            timerContainer.id = 'phase-timer-container';
            timerContainer.className = 'phase-timer-container';
            timerContainer.innerHTML = `
                <div class="phase-timer-title">${timerData.phase_name || 'Current Phase'}</div>
                <div id="phase-timer-display" class="phase-timer-display">${timerData.formatted_time || '--'}</div>
                <div class="phase-timer-info">Phase Duration: ${timerData.phase_duration || '--'} seconds</div>
            `;
            
            // Insert at top of game overview
            gameOverview.insertBefore(timerContainer, gameOverview.firstChild);
            phaseTimerElement = document.getElementById('phase-timer-display');
        } else {
            console.warn('⏱️ Could not find game-overview element to attach phase timer');
            return;
        }
    }
    
    // Update the timer display
    if (phaseTimerElement) {
        phaseTimerElement.textContent = timerData.formatted_time || '--';
        
        // Update phase name if container exists
        const titleElement = document.querySelector('.phase-timer-title');
        if (titleElement) {
            titleElement.textContent = timerData.phase_name || 'Current Phase';
        }
        
        // Apply visual effects based on remaining time
        const secondsRemaining = timerData.seconds_remaining;
        if (secondsRemaining !== undefined) {
            phaseTimerElement.className = 'phase-timer-display';
            
            // Warning states for last 5 minutes and last minute
            if (secondsRemaining <= 60 && secondsRemaining > 0) {
                phaseTimerElement.classList.add('timer-critical');
            } else if (secondsRemaining <= 300 && secondsRemaining > 0) {
                phaseTimerElement.classList.add('timer-warning');
            }
        }
        
        console.log('⏱️ Phase timer updated:', timerData.formatted_time);
    }
}

function showCornucopiaHorn(popupTimer) {
    console.log('🎺 Starting cornucopia horn animation');
    
    // Change timer to horn display
    const container = popupTimer.querySelector('.popup-timer-container');
    if (container) {
        container.innerHTML = `
            <div class="horn-animation">
                <div class="horn-icon">🎺</div>
                <div class="horn-title">THE GONG SOUNDS!</div>
                <div class="horn-message">Let the 75th Hunger Games begin!</div>
                <div class="horn-waves">
                    <div class="wave wave1"></div>
                    <div class="wave wave2"></div>
                    <div class="wave wave3"></div>
                </div>
            </div>
        `;
        
        // Add horn animation class
        popupTimer.classList.add('horn-active');
        
        // Play horn animation for 3 seconds then fade out
        setTimeout(() => {
            console.log('🎺 Horn animation complete, fading out timer');
            popupTimer.classList.add('fade-out');
            setTimeout(() => {
                popupTimer.remove();
                console.log('🎺 Timer popup removed, game continues');
            }, 1000); // 1 second fade out
        }, 3000); // 3 seconds of horn animation
    }
}

function showCornucopiaCountdown(countdownData) {
    const gameLog = document.getElementById('game-log');
    if (!gameLog) return;

    // Create countdown display
    const countdownDiv = document.createElement('div');
    countdownDiv.id = 'cornucopia-countdown';
    countdownDiv.className = 'cornucopia-countdown';
    countdownDiv.innerHTML = `
        <div class="countdown-container">
            <div class="countdown-title">🏺 Cornucopia Countdown</div>
            <div class="countdown-timer" id="countdown-timer">${countdownData.countdown_seconds}</div>
            <div class="countdown-message">${countdownData.message}</div>
            <div class="countdown-warning">⚠️ Do not step off your platform early!</div>
        </div>
    `;

    // Add countdown to top of game log
    gameLog.insertBefore(countdownDiv, gameLog.firstChild);
}

function showCornucopiaDecisions() {
    const gameStatus = document.getElementById('game-status');
    if (!gameStatus) return;

    const decisionsDiv = document.createElement('div');
    decisionsDiv.id = 'cornucopia-decisions';
    decisionsDiv.className = 'cornucopia-decisions';
    decisionsDiv.innerHTML = `
        <div class="decisions-container">
            <div class="decisions-title">🔔 The Gong Has Sounded!</div>
            <div class="decisions-message">Tributes are making their life-or-death choices...</div>
            <div class="decisions-list" id="decisions-list"></div>
        </div>
    `;

    gameStatus.innerHTML = '';
    gameStatus.appendChild(decisionsDiv);
}

function displayTributeDecision(decisionData) {
    const decisionsList = document.getElementById('decisions-list');
    if (!decisionsList) return;

    const decisionElement = document.createElement('div');
    decisionElement.className = `tribute-decision decision-${decisionData.decision}`;
    
    const icon = decisionData.decision === 'cornucopia' ? '⚔️' : '🏃';
    const action = decisionData.decision === 'cornucopia' ? 'rushes toward the Cornucopia' : 'flees into the arena';
    
    decisionElement.innerHTML = `
        <div class="decision-tribute">${icon} ${decisionData.tribute_name}</div>
        <div class="decision-action">${action}</div>
        <div class="decision-reasoning">${decisionData.reasoning}</div>
    `;

    decisionsList.appendChild(decisionElement);
}

function displayBloodbathResults(bloodbathData) {
    const gameStatus = document.getElementById('game-status');
    if (!gameStatus) return;

    const resultsDiv = document.createElement('div');
    resultsDiv.id = 'bloodbath-results';
    resultsDiv.className = 'bloodbath-results';
    resultsDiv.innerHTML = `
        <div class="bloodbath-container">
            <div class="bloodbath-title">⚔️ Cornucopia Bloodbath Results</div>
            <div class="bloodbath-stats">
                <div class="stat">
                    <span class="stat-label">Participants:</span>
                    <span class="stat-value">${bloodbathData.participants}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Casualties:</span>
                    <span class="stat-value casualties">${bloodbathData.casualties}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Supplies Claimed:</span>
                    <span class="stat-value supplies">${bloodbathData.supplies_claimed}</span>
                </div>
            </div>
            <div class="bloodbath-narrative">${bloodbathData.narrative}</div>
        </div>
    `;

    gameStatus.innerHTML = '';
    gameStatus.appendChild(resultsDiv);

    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (document.getElementById('bloodbath-results')) {
            gameStatus.innerHTML = '<div class="game-status">Cornucopia phase completed. The Games continue...</div>';
        }
    }, 10000);
}

// Update phase display in header
function updatePhaseDisplay(phaseInfo) {
    const phaseDisplay = document.getElementById('phase-display');
    if (!phaseDisplay) return;
    
    // Extract phase information
    const phaseName = phaseInfo.name || 'Unknown Phase';
    const phaseType = phaseInfo.type || '';
    const day = phaseInfo.day || 1;
    
    // Format the display based on phase type
    let displayText = '';
    
    if (phaseType === 'cornucopia') {
        displayText = 'Day 1 - Cornucopia';
    } else if (phaseType === 'day_phase') {
        displayText = `Day ${day} - ${phaseName}`;
    } else if (phaseType === 'night_phase') {
        displayText = `Day ${day} - ${phaseName}`;
    } else {
        // Fallback for any other phase type
        displayText = `Day ${day} - ${phaseName}`;
    }
    
    phaseDisplay.textContent = displayText;
    console.log('📅 Updated phase display:', displayText);
}

// Test function for cornucopia timer
function testCornucopiaTimer() {
    console.log('Testing cornucopia timer...');
    createCornucopiaPopupTimer();
    
    // Simulate countdown
    let seconds = 30;
    const interval = setInterval(() => {
        updateCornucopiaTimer({
            remaining_seconds: seconds,
            message: seconds > 10 ? 'Countdown in progress...' : 'PREPARE FOR THE GONG!'
        });
        
        seconds--;
        if (seconds < 0) {
            clearInterval(interval);
            updateCornucopiaTimer({
                remaining_seconds: 0,
                phase: 'completed',
                message: 'The gong sounds! Let the Games begin!'
            });
        }
    }, 1000);
}