/**
 * Authentication Module
 * Handles login, token storage, and session management
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('apiToken');
        this.apiUrl = localStorage.getItem('apiUrl') || 'http://localhost:5000';
        this.username = localStorage.getItem('username');
        this.expiresAt = parseInt(localStorage.getItem('tokenExpiresAt') || '0');
        this.isAdmin = localStorage.getItem('isAdmin') === 'true';
        this.isTenant = localStorage.getItem('isTenant') === 'true';
    }
    
    /**
     * Check if user is currently logged in
     */
    isLoggedIn() {
        if (!this.token) return false;
        if (this.isTokenExpired()) {
            this.logout();
            return false;
        }
        return true;
    }

    /**
     * Check if the token expiration timestamp has passed
     */
    isTokenExpired() {
        if (!this.expiresAt) {
            return true;
        }
        return Date.now() >= this.expiresAt;
    }
    
    /**
     * Get the API URL for the current session
     */
    getApiUrl() {
        return this.apiUrl;
    }
    
    /**
     * Get current username
     */
    getUsername() {
        return this.username;
    }
    
    /**
     * Login with username and password
     */
    async login(username, password, apiUrl) {
        try {
            const response = await fetch(`${apiUrl}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }

            if (data.two_factor_required) {
                const code = window.prompt('Enter your 2FA code from your authenticator app:');
                if (!code) {
                    return {
                        success: false,
                        error: '2FA code entry was cancelled.'
                    };
                }

                const verifyResponse = await fetch(`${apiUrl}/api/auth/verify-2fa`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        challenge_id: data.challenge_id,
                        code: code.trim()
                    })
                });

                const verifyData = await verifyResponse.json();
                if (!verifyResponse.ok) {
                    throw new Error(verifyData.message || '2FA verification failed');
                }

                // Continue with verified payload as normal login data.
                Object.assign(data, verifyData);
            }
            
            if (!data.token) {
                throw new Error('No token received from server');
            }
            
            // Store credentials
            this.token = data.token;
            this.username = username;
            this.apiUrl = apiUrl;
            this.isAdmin = !!data.is_admin;
            this.isTenant = !!data.is_tenant;
            
            // Calculate expiration time
            const expiresInSeconds = data.session_expires_in_seconds || 3600;
            this.expiresAt = Date.now() + (expiresInSeconds * 1000);
            
            // Persist to localStorage
            localStorage.setItem('apiToken', this.token);
            localStorage.setItem('username', this.username);
            localStorage.setItem('apiUrl', this.apiUrl);
            localStorage.setItem('tokenExpiresAt', this.expiresAt.toString());
            localStorage.setItem('isAdmin', this.isAdmin ? 'true' : 'false');
            localStorage.setItem('isTenant', this.isTenant ? 'true' : 'false');
            
            return {
                success: true,
                message: 'Login successful',
                token: this.token,
                expiresIn: expiresInSeconds
            };
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Logout and clear session
     */
    async logout() {
        try {
            // Try to notify server
            if (this.token && this.apiUrl) {
                await fetch(`${this.apiUrl}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json'
                    }
                }).catch(() => {
                    // Logout from server failed, but clear local data anyway
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage
            localStorage.removeItem('apiToken');
            localStorage.removeItem('username');
            localStorage.removeItem('apiUrl');
            localStorage.removeItem('tokenExpiresAt');
            localStorage.removeItem('isAdmin');
            localStorage.removeItem('isTenant');
            
            this.token = null;
            this.username = null;
            this.expiresAt = 0;
            this.isAdmin = false;
            this.isTenant = false;
        }
    }
    
    /**
     * Check if token is valid and not expired
     */
    isAuthenticated() {
        if (!this.token) {
            return false;
        }
        
        // Check expiration
        if (this.expiresAt && Date.now() >= this.expiresAt) {
            this.logout();
            return false;
        }
        
        return true;
    }
    
    /**
     * Get authorization header
     */
    getAuthHeader() {
        if (!this.token) {
            throw new Error('No authentication token available');
        }
        
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
    
    /**
     * Verify token is still valid
     */
    async verifyToken() {
        try {
            const response = await fetch(`${this.apiUrl}/api/auth/verify`, {
                method: 'GET',
                headers: this.getAuthHeader()
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    return false;
                }
                throw new Error('Token verification failed');
            }

            const data = await response.json();
            this.username = data.username || this.username;
            this.isAdmin = !!data.is_admin;
            this.isTenant = !!data.is_tenant;
            localStorage.setItem('username', this.username || '');
            localStorage.setItem('isAdmin', this.isAdmin ? 'true' : 'false');
            localStorage.setItem('isTenant', this.isTenant ? 'true' : 'false');
            
            return true;
        } catch (error) {
            console.error('Token verification error:', error);
            this.logout();
            return false;
        }
    }
    
    /**
     * Get time until token expiration in seconds
     */
    getTimeUntilExpiration() {
        if (!this.expiresAt) {
            return -1;
        }
        
        const secondsRemaining = Math.floor((this.expiresAt - Date.now()) / 1000);
        return Math.max(0, secondsRemaining);
    }
    
    /**
     * Get formatted expiration time
     */
    getExpirationDisplay() {
        const seconds = this.getTimeUntilExpiration();
        
        if (seconds < 0) {
            return 'Expired';
        }
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    /**
     * Whether the logged-in account is a tenant account
     */
    isTenantAccount() {
        return !!this.isTenant;
    }

    /**
     * Whether the logged-in account is admin/landlord
     */
    isAdminAccount() {
        return !!this.isAdmin;
    }
}

// Create global auth manager
const authManager = new AuthManager();
