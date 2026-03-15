// Hunger Games Simulator - Spectator Page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const socket = window.lobbyApp.socket;

    // DOM elements (get them when needed since spectator-section might not be visible initially)
    const spectatorLog = document.getElementById('spectator-log');
    const leaveSpectatorBtn = document.getElementById('leave-spectator-btn');

    let gameState = null;
    let lastUpdateTime = Date.now();
    let spectatorTimeoutInterval = null;

    // Check for spectator timeout every 30 seconds
    function startSpectatorTimeoutCheck() {
        if (spectatorTimeoutInterval) {
            clearInterval(spectatorTimeoutInterval);
        }
        spectatorTimeoutInterval = setInterval(checkSpectatorTimeout, 30000);
    }

    function checkSpectatorTimeout() {
        const now = Date.now();
        const timeSinceLastUpdate = now - lastUpdateTime;
        
        // If no updates for 60 seconds, assume lobby is gone
        if (timeSinceLastUpdate > 60000) {
            console.log('No spectator updates received for 60 seconds, lobby may be unavailable');
            window.location.href = '/';
        }
    }

    function updateLastActivity() {
        lastUpdateTime = Date.now();
    }

    function stopSpectatorTimeoutCheck() {
        if (spectatorTimeoutInterval) {
            clearInterval(spectatorTimeoutInterval);
            spectatorTimeoutInterval = null;
        }
    }

    // Start checking for spectator timeout when page loads
    startSpectatorTimeoutCheck();

    // Socket event handlers
    socket.on('spectator_update', (data) => {
        console.log('Spectator update:', data);
        updateLastActivity();
        gameState = data.game_state;

        updateSpectatorDisplay();
    });

    socket.on('game_update', (data) => {
        console.log('Game update (spectator):', data);
        updateLastActivity();

        // Handle tribute stat updates
        if (data.message && data.message.type === 'tribute_stat_update') {
            handleTributeStatUpdate(data.message);
            return;
        }

        if (data.status === 'running' && data.message) {
            addToSpectatorLog(data.message, data.timestamp);
        } else if (data.status === 'completed') {
            const spectatorStats = document.getElementById('spectator-stats');
            if (spectatorStats) {
                spectatorStats.innerHTML = `<div class="game-completed">${data.message || 'Game completed!'}</div>`;
            }
            window.lobbyApp.showNotification('Game has ended!', 'success');
        } else if (data.status === 'error') {
            const spectatorStats = document.getElementById('spectator-stats');
            if (spectatorStats) {
                spectatorStats.innerHTML = `<div class="game-error">Error: ${data.message || 'Unknown error'}</div>`;
            }
            window.lobbyApp.showNotification('Game error occurred', 'error');
        }
    });

    // Socket connection handlers
    socket.on('connect', () => {
        console.log('Spectator page: Socket connected');
        updateLastActivity();
    });

    socket.on('disconnect', () => {
        console.log('Spectator page: Socket disconnected - lobby may be unavailable');
        // Redirect to main lobby after a short delay
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    });

    // UI event handlers
    window.leaveSpectator = function() {
        socket.emit('leave_spectator');
        window.lobbyApp.showSection('login-section');
    };

    // Functions
    function handleTributeStatUpdate(message) {
        console.log('Spectator handling tribute stat update:', message);
        
        const { tribute_id, stat, new_value, old_value, delta, cause } = message;
        
        // Update spectator display
        updateSpectatorTributeStats(tribute_id, stat, new_value, old_value, delta, cause);
        
        // Add to spectator log
        const statName = stat.charAt(0).toUpperCase() + stat.slice(1);
        const changeText = delta > 0 ? `+${delta}` : delta;
        const causeText = cause ? ` (${cause})` : '';
        addToSpectatorLog(`${tribute_id}: ${statName} ${old_value} → ${new_value} (${changeText})${causeText}`, new Date().toLocaleTimeString());
    }

    function updateSpectatorTributeStats(tributeId, stat, newValue, oldValue, delta, cause) {
        // Update the spectator stats display
        if (gameState && gameState.players) {
            const player = gameState.players.find(p => p.id === tributeId);
            if (player) {
                // Update the player's stat
                player[stat] = newValue;
                
                // Refresh the spectator display
                updateSpectatorDisplay();
            }
        }
    }

    function updateSpectatorDisplay() {
        if (!gameState) return;

        // Check if spectator stats element exists
        const spectatorStats = document.getElementById('spectator-stats');
        if (!spectatorStats) {
            console.log('Spectator stats element not found, skipping update');
            return;
        }

        // Update spectator stats in header
        const aliveCount = gameState.players.filter(p => p.alive).length;
        const totalCount = gameState.players.length;

        spectatorStats.innerHTML = `
            <div class="spectator-info">
                <div>Day: ${gameState.day}</div>
                <div>Alive: ${aliveCount}/${totalCount}</div>
                <div>Status: ${gameState.status}</div>
            </div>
        `;

        // Update all tributes in sidebar
        const spectatorTributesContainer = document.getElementById('spectator-tributes-container');
        if (spectatorTributesContainer) {
            spectatorTributesContainer.innerHTML = gameState.players.map(player =>
                `<div class="player-card spectator-player ${player.alive ? 'alive' : 'dead'}">
                    <div class="player-name">${player.name} ${player.alive ? '' : '(Dead)'}</div>
                    <div class="player-stats">
                        <div>Health: ${player.health}/100</div>
                        <div>District: ${player.district}</div>
                        ${player.alive ? `<div>Hunger: ${player.hunger}/100</div><div>Thirst: ${player.thirst}/100</div>` : ''}
                    </div>
                </div>`
            ).join('');
        }
    }

    function addToSpectatorLog(message, timestamp) {
        const spectatorLog = document.getElementById('spectator-log');
        if (!spectatorLog) return;

        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const time = timestamp ? new Date(timestamp * 1000).toLocaleTimeString() : '';
        entry.innerHTML = `<span class="timestamp">[${time}]</span> ${message}`;

        spectatorLog.appendChild(entry);
        spectatorLog.scrollTop = spectatorLog.scrollHeight;
    }
});