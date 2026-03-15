/**
 * API Client Module
 * Handles all API requests with authentication
 */

class APIClient {
    constructor(authManager) {
        this.auth = authManager;
    }
    
    /**
     * Make authenticated API request
     */
    async request(endpoint, method = 'GET', body = null) {
        if (!this.auth.isAuthenticated()) {
            throw new Error('Not authenticated. Please login first.');
        }
        
        const url = `${this.auth.apiUrl}${endpoint}`;
        const options = {
            method: method,
            headers: this.auth.getAuthHeader()
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.auth.logout();
                    throw new Error('Session expired. Please login again.');
                }
                throw new Error(data.message || `API error: ${response.status}`);
            }
            
            return {
                success: true,
                data: data,
                status: response.status
            };
        } catch (error) {
            console.error(`API request error (${endpoint}):`, error);
            return {
                success: false,
                error: error.message,
                endpoint: endpoint
            };
        }
    }
    
    // ========== TENANT ENDPOINTS ==========
    
    /**
     * Get all tenants
     */
    async getAllTenants() {
        return this.request('/api/tenants');
    }
    
    /**
     * Get specific tenant
     */
    async getTenant(tenantId) {
        return this.request(`/api/tenants/${tenantId}`);
    }
    
    /**
     * Get tenant payment summary
     */
    async getPaymentSummary(tenantId) {
        return this.request(`/api/tenants/${tenantId}/payment-summary`);
    }
    
    /**
     * Get tenant delinquency info
     */
    async getDelinquencyInfo(tenantId) {
        return this.request(`/api/tenants/${tenantId}/delinquency`);
    }
    
    /**
     * Get tenant monthly breakdown
     */
    async getMonthlyBreakdown(tenantId) {
        return this.request(`/api/tenants/${tenantId}/monthly-breakdown`);
    }
    
    /**
     * Export tenant data
     */
    async exportTenantData(tenantId) {
        return this.request(`/api/tenants/${tenantId}/export`);
    }
    
    // ========== DISPUTE ENDPOINTS ==========
    
    /**
     * Get all disputes
     */
    async getAllDisputes() {
        return this.request('/api/disputes');
    }
    
    /**
     * Get specific dispute
     */
    async getDispute(disputeId) {
        return this.request(`/api/disputes/${disputeId}`);
    }
    
    /**
     * Get tenant's disputes
     */
    async getTenantDisputes(tenantId) {
        return this.request(`/api/tenants/${tenantId}/disputes`);
    }
    
    /**
     * Create new dispute
     */
    async createDispute(tenantId, disputeData) {
        return this.request(
            `/api/tenants/${tenantId}/disputes`,
            'POST',
            disputeData
        );
    }
    
    /**
     * Update dispute status
     */
    async updateDisputeStatus(disputeId, status, adminNotes = '') {
        return this.request(
            `/api/disputes/${disputeId}/status`,
            'PUT',
            {
                status: status,
                admin_notes: adminNotes
            }
        );
    }
    
    // ========== INFO ENDPOINTS ==========
    
    /**
     * Get available dispute types
     */
    async getDisputeTypes() {
        return this.request('/api/info/dispute-types');
    }
    
    /**
     * Get available dispute statuses
     */
    async getDisputeStatuses() {
        return this.request('/api/info/dispute-statuses');
    }
    
    /**
     * Health check (no auth required, but included for completeness)
     */
    async health() {
        const url = `${this.auth.apiUrl}/api/health`;
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            return {
                success: response.ok,
                data: data,
                status: response.status
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Create global API client
const apiClient = new APIClient(authManager);
