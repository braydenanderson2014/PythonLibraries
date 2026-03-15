// Hunger Games Lobby - Main Application JavaScript

class LobbyApp {
    constructor() {
        this.socket = null;
        this.currentPlayerId = null;
        this.currentLobbyId = null;
        this.gameStarted = false;

        this.init();
    }

    init() {
        this.connectSocket();
        this.setupEventListeners();
        this.updateConnectionStatus('connecting');
    }

    connectSocket() {
        // Determine server URL based on current location
        let serverUrl = '';

        // Check if we're on localhost or a development environment
        if (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1' ||
            window.location.hostname === '') {
            // Development: connect to local Aurora Engine server
            serverUrl = 'http://localhost:8000';
        } else {
            // Production/Cloudflare Tunnel: connect to same host that served the page
            // Cloudflare Tunnel should forward WebSocket connections properly
            serverUrl = window.location.origin;
        }

        console.log('Connecting to server:', serverUrl);
        console.log('WebSocket URL will be:', serverUrl.replace(/^http/, 'ws') + '/socket.io/');

        this.socket = io(serverUrl, {
            // ALIGNED TRANSPORTS: Match server's polling-first priority for proxy stability
            // Server uses: ['polling', 'websocket']
            // This means server prefers polling, WebSocket is upgrade attempt
            transports: ['polling', 'websocket'],
            upgrade: true,
            rememberUpgrade: true,
            // CRITICAL: Timeout must allow for game phase transitions
            // Server uses: ping_timeout=20, ping_interval=8
            // Increased to 30s to allow for phase transitions and heavy processing
            timeout: 30000,  // 30 second connection timeout (allows for game processing)
            forceNew: false,
            reconnection: true,
            reconnectionAttempts: 15,  // More attempts for proxy stability
            reconnectionDelay: 500,
            reconnectionDelayMax: 5000,  // Exponential backoff up to 5 seconds
            maxReconnectionAttempts: 15,
            // REMOVED: User-Agent header causes "Refused to set unsafe header" errors in browsers
            // Browsers block setting User-Agent for security reasons
            // IMPORTANT: For Cloudflare Tunnel (non-localhost), disable WebSocket upgrade
            // This forces polling-only mode which is more stable through proxies
            // forcePolling=true prevents the upgrade attempt that often fails through tunnels
            forcePolling: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
            // Removed transportOptions with User-Agent headers - cause polling failures
            allowEIO3: true,
            withCredentials: true
        });

        this.socket.on('connect', () => {
            console.log('✅ Connected to server successfully');
            console.log('Socket ID:', this.socket.id);
            this.updateConnectionStatus('connected');
        });

        this.socket.on('disconnect', (reason) => {
            console.log('❌ Disconnected from server:', reason);
            this.updateConnectionStatus('disconnected');

            // Log additional context for Cloudflare Tunnel debugging
            if (reason === 'io server disconnect') {
                console.log('🔧 Server initiated disconnect - may be Cloudflare Tunnel related');
            } else if (reason === 'io client disconnect') {
                console.log('🔧 Client initiated disconnect');
            } else if (reason === 'ping timeout') {
                console.log('🔧 Ping timeout - connection may be unstable');
            } else if (reason === 'transport close') {
                console.log('🔧 Transport closed - WebSocket/polling issue');
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ Connection error:', error);
            console.error('Error details:', {
                message: error.message,
                description: error.description,
                context: error.context,
                type: error.type
            });
            this.updateConnectionStatus('disconnected');

            // Additional Cloudflare Tunnel debugging
            if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                console.log('🔧 Cloudflare Tunnel detected - connection errors are common, will retry with polling');
            }
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log('🔄 Reconnected to server after', attemptNumber, 'attempts');
            console.log('🔧 Transport used:', this.socket.io.engine.transport.name);
        });

        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log('🔄 Reconnection attempt', attemptNumber);
        });

        this.socket.on('reconnect_error', (error) => {
            console.error('❌ Reconnection error:', error);
        });

        // Monitor transport upgrades/downgrades
        this.socket.on('upgrade', (transport) => {
            console.log('⬆️ Transport upgraded to:', transport.name);
        });

        this.socket.on('upgradeError', (error) => {
            console.log('⬇️ Transport upgrade failed:', error);
        });

        // Add ping test for connection health
        this.socket.on('ping', () => {
            console.log('🏓 Received ping from server');
        });

        this.socket.on('pong', () => {
            console.log('🏓 Received pong from server');
        });

        // Debug info handler
        this.socket.on('debug_info', (data) => {
            console.log('🔍 Debug Info:', data);
            console.table(data.players);
        });

        // Game starting - transition to game section (SPA-style, no page reload)
        this.socket.on('game_starting', (data) => {
            console.log('🎬 Game starting event received:', data);
            const lobbyId = data.lobby_id;
            if (lobbyId) {
                console.log('Transitioning to game section for lobby:', lobbyId);
                // Store lobbyId for game page use
                window.currentLobbyId = lobbyId;
                // Show game section instead of redirecting (maintains socket connection)
                this.showSection('game-section');
                // Initialize game page now that it's visible
                // Pass socket directly to avoid timing issues with window.lobbyApp initialization
                if (window.initializeGamePageWithSocket) {
                    console.log('📱 Calling initializeGamePageWithSocket with socket');
                    window.initializeGamePageWithSocket(this.socket);
                } else if (window.initializeGamePageWhenReady) {
                    console.log('📱 Calling initializeGamePageWhenReady (fallback)');
                    window.initializeGamePageWhenReady();
                }
            }
        });
        this.connectionHealthCheck = setInterval(() => {
            if (this.socket.connected) {
                // Send periodic health check
                this.socket.emit('ping');
            } else if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                console.log('🔄 Connection health check: Socket not connected, Cloudflare Tunnel may need reconnection');
            }
        }, 30000); // Check every 30 seconds

        // Test connection with a ping after connection
        this.socket.on('connect', () => {
            console.log('✅ Connected to server successfully');
            console.log('Socket ID:', this.socket.id);
            this.updateConnectionStatus('connected');

            // Send a test ping to verify connection works
            setTimeout(() => {
                console.log('🏓 Sending test ping to server...');
                this.socket.emit('ping');
            }, 1000);
        });
    }

    setupEventListeners() {
        // Global event listeners will be set up in specific page scripts
    }

    updateConnectionStatus(status) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.className = `status ${status}`;
            statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    }

    showSection(sectionId) {
        // Hide all sections
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => section.style.display = 'none');

        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
    }

    formatPlayerName(player, isCurrentPlayer = false) {
        let name = player.name;
        if (isCurrentPlayer) {
            name += ' (You)';
        }
        return name;
    }

    formatPlayerStatus(player) {
        return player.tribute_ready ? 'Tribute Ready' : 'Creating Tribute';
    }

    createPlayerCard(player, isCurrentPlayer = false) {
        const card = document.createElement('div');
        card.className = `player-card ${player.tribute_ready ? 'tribute-ready' : 'creating-tribute'} ${isCurrentPlayer ? 'me' : ''}`;
        card.dataset.playerId = player.id;

        const badges = [];
        if (player.id === player.lobbyHostId) {
            badges.push('<span class="badge host">Host</span>');
        }
        if (player.tribute_ready) {
            badges.push('<span class="badge tribute-done">Tribute Done</span>');
        } else {
            badges.push('<span class="badge creating">Creating</span>');
        }
        if (isCurrentPlayer) {
            badges.push('<span class="badge you">You</span>');
        }

        let tributeInfo = '';
        if (player.tribute_data && player.tribute_data.name) {
            tributeInfo = `
                <div class="tribute-info">
                    <div class="tribute-name">${player.tribute_data.name}</div>
                    <div class="tribute-details">District ${player.tribute_data.district} • ${player.tribute_data.age} • ${player.tribute_data.gender}</div>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="player-name">${this.formatPlayerName(player, isCurrentPlayer)}</div>
            <div class="player-status">${this.formatPlayerStatus(player)}</div>
            ${tributeInfo}
            <div class="player-badges">${badges.join('')}</div>
        `;

        return card;
    }

    // Force reconnection for Cloudflare Tunnel issues
    forceReconnect() {
        console.log('🔄 Forcing reconnection...');
        if (this.socket) {
            this.socket.disconnect();
            setTimeout(() => {
                this.connectSocket();
            }, 1000);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Global functions for game control
window.startGame = function() {
    if (window.lobbyApp && window.lobbyApp.socket) {
        console.log('Sending start_game request to server');
        window.lobbyApp.socket.emit('start_game', {});
    } else {
        console.error('Socket not available for startGame');
    }
};

window.leaveLobby = function() {
    if (window.lobbyApp && window.lobbyApp.socket) {
        console.log('Leaving lobby');
        window.lobbyApp.socket.emit('leave_lobby', {});
        // Show lobby selection
        if (window.lobbyApp) {
            window.lobbyApp.showSection('lobby-selection-section');
        }
    }
};

window.leaveGame = function() {
    if (window.lobbyApp && window.lobbyApp.socket) {
        console.log('Leaving game');
        window.lobbyApp.socket.emit('leave_game', {});
        // Show lobby selection
        if (window.lobbyApp) {
            window.lobbyApp.showSection('lobby-selection-section');
        }
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.lobbyApp = new LobbyApp();
});

// Global functions for debugging Cloudflare Tunnel issues
window.forceReconnect = function() {
    if (window.lobbyApp) {
        window.lobbyApp.forceReconnect();
    }
};

window.getConnectionStatus = function() {
    if (window.lobbyApp && window.lobbyApp.socket) {
        return {
            connected: window.lobbyApp.socket.connected,
            transport: window.lobbyApp.socket.io?.engine?.transport?.name,
            socketId: window.lobbyApp.socket.id,
            hostname: window.location.hostname,
            isCloudflare: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
        };
    }
    return { error: 'Socket not initialized' };
};

console.log('🔧 Cloudflare Tunnel debugging functions available:');
console.log('  - forceReconnect() - Force socket reconnection');
console.log('  - getConnectionStatus() - Get current connection details');