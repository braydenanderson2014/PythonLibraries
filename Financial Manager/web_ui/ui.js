/**
 * UI Controller Module
 * Handles all UI interactions and page rendering
 */

class UIController {
    constructor() {
        this.currentTenant = null;
        this.autoRefreshInterval = null;
        this.setupEventListeners();
        this.checkAuthStatus();
        this.loadSettings();
    }
    
    // ========== INITIALIZATION ==========
    
    setupEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        
        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
        
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.handleNavigation(e));
        });
        
        // Refresh buttons
        document.getElementById('refreshTenantsBtn').addEventListener('click', () => this.loadTenants());
        document.getElementById('refreshDisputesBtn').addEventListener('click', () => this.loadDisputes());
        
        // Settings
        document.getElementById('saveSettingsBtn').addEventListener('click', () => this.saveSettings());
        document.getElementById('darkMode').addEventListener('change', (e) => this.toggleDarkMode(e));
        
        // Copy token button
        document.getElementById('copyTokenBtn').addEventListener('click', () => this.copyTokenToClipboard());
        
        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (e) => {
            if (e.target.id === 'tenantModal') {
                this.closeModal();
            }
        });
    }
    
    checkAuthStatus() {
        if (authManager.isAuthenticated()) {
            this.showDashboard();
        } else {
            this.showLogin();
        }
    }
    
    loadSettings() {
        const autoRefresh = localStorage.getItem('autoRefresh') || '30';
        const darkMode = localStorage.getItem('darkMode') === 'true';
        
        document.getElementById('autoRefresh').value = autoRefresh;
        document.getElementById('darkMode').checked = darkMode;
        
        if (darkMode) {
            document.body.classList.add('dark-mode');
        }
        
        if (authManager.isAuthenticated()) {
            this.startAutoRefresh(parseInt(autoRefresh));
        }
    }
    
    // ========== AUTHENTICATION ==========
    
    async handleLogin(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const apiUrl = document.getElementById('apiUrl').value;
        
        const loginBtn = document.querySelector('.btn-login');
        const buttonText = document.getElementById('loginButtonText');
        const spinner = document.getElementById('loginSpinner');
        const errorDiv = document.getElementById('loginError');
        const successDiv = document.getElementById('loginSuccess');
        
        // Show loading state
        loginBtn.disabled = true;
        buttonText.classList.add('hidden');
        spinner.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        successDiv.classList.add('hidden');
        
        try {
            const result = await authManager.login(username, password, apiUrl);
            
            if (result.success) {
                successDiv.textContent = 'Login successful! Redirecting...';
                successDiv.classList.remove('hidden');
                
                // Reset form
                document.getElementById('loginForm').reset();
                
                // Show dashboard
                setTimeout(() => this.showDashboard(), 1500);
            } else {
                errorDiv.textContent = result.error || 'Login failed';
                errorDiv.classList.remove('hidden');
            }
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
        } finally {
            loginBtn.disabled = false;
            buttonText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    }
    
    async handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            await authManager.logout();
            this.stopAutoRefresh();
            this.showLogin();
        }
    }
    
    showLogin() {
        document.getElementById('loginPage').classList.add('active');
        document.getElementById('dashboardPage').classList.remove('active');
    }
    
    showDashboard() {
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('dashboardPage').classList.add('active');
        
        // Update user info
        document.getElementById('userInfo').textContent = `${authManager.username} | Token expires in: ${authManager.getExpirationDisplay()}`;
        
        // Load initial data
        this.loadTenants();
        this.loadDisputes();
        this.loadSystemInfo();
    }
    
    // ========== NAVIGATION ==========
    
    handleNavigation(event) {
        event.preventDefault();
        
        const page = event.target.dataset.page;
        
        // Update active link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        event.target.classList.add('active');
        
        // Update active section
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${page}Section`).classList.add('active');
        
        // Load data if needed
        if (page === 'tenants' && !this.tenantsCached) {
            this.loadTenants();
        } else if (page === 'disputes' && !this.disputesCached) {
            this.loadDisputes();
        } else if (page === 'info') {
            this.loadSystemInfo();
        }
    }
    
    // ========== TENANTS ==========
    
    async loadTenants() {
        const loadingDiv = document.getElementById('tenantsLoading');
        const errorDiv = document.getElementById('tenantsError');
        const listDiv = document.getElementById('tenantsList');
        
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        listDiv.innerHTML = '';
        
        try {
            const result = await apiClient.getAllTenants();
            
            if (!result.success) {
                throw new Error(result.error);
            }
            
            const tenants = result.data.tenants || [];
            
            if (tenants.length === 0) {
                listDiv.innerHTML = '<p class="empty-state">No tenants found</p>';
            } else {
                tenants.forEach(tenant => {
                    const card = this.createTenantCard(tenant);
                    listDiv.appendChild(card);
                });
            }
            
            this.tenantsCached = true;
        } catch (error) {
            errorDiv.textContent = `Error loading tenants: ${error.message}`;
            errorDiv.classList.remove('hidden');
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }
    
    createTenantCard(tenant) {
        const card = document.createElement('div');
        card.className = 'tenant-card';
        
        const status = tenant.payment_status ? tenant.payment_status.status : 'unknown';
        const statusClass = status === 'paid' ? 'status-paid' : status === 'delinquent' ? 'status-delinquent' : 'status-pending';
        
        const balance = tenant.payment_summary ? tenant.payment_summary.delinquency_balance : 0;
        const balance_formatted = typeof balance === 'number' ? balance.toFixed(2) : '0.00';
        
        card.innerHTML = `
            <div class="card-header">
                <h3>${tenant.name || 'Unknown Tenant'}</h3>
                <span class="status-badge ${statusClass}">${status}</span>
            </div>
            <div class="card-body">
                <div class="card-row">
                    <span class="label">ID:</span>
                    <span class="value">${tenant.tenant_id || 'N/A'}</span>
                </div>
                <div class="card-row">
                    <span class="label">Rent Amount:</span>
                    <span class="value">$${typeof tenant.rent_amount === 'number' ? tenant.rent_amount.toFixed(2) : '0.00'}</span>
                </div>
                <div class="card-row">
                    <span class="label">Delinquency:</span>
                    <span class="value ${balance > 0 ? 'error' : 'success'}">$${balance_formatted}</span>
                </div>
                ${tenant.contact_info ? `
                <div class="card-row">
                    <span class="label">Contact:</span>
                    <span class="value">${tenant.contact_info}</span>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <button class="btn btn-secondary btn-small" onclick="ui.viewTenantDetails('${tenant.tenant_id}')">
                    View Details
                </button>
            </div>
        `;
        
        return card;
    }
    
    async viewTenantDetails(tenantId) {
        const modal = document.getElementById('tenantModal');
        const content = document.getElementById('tenantDetailContent');
        
        content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading details...</p></div>';
        modal.classList.remove('hidden');
        
        try {
            const result = await apiClient.getTenant(tenantId);
            
            if (!result.success) {
                throw new Error(result.error);
            }
            
            const tenant = result.data.data || {};
            
            content.innerHTML = `
                <h2>${tenant.name}</h2>
                
                <div class="details-section">
                    <h3>Basic Information</h3>
                    <table class="details-table">
                        <tr><td>Tenant ID:</td><td>${tenant.tenant_id}</td></tr>
                        <tr><td>Name:</td><td>${tenant.name}</td></tr>
                        <tr><td>Contact:</td><td>${tenant.contact_info || 'N/A'}</td></tr>
                        <tr><td>Rental Period:</td><td>${tenant.rental_period || 'N/A'}</td></tr>
                    </table>
                </div>
                
                ${tenant.payment_summary ? `
                <div class="details-section">
                    <h3>Payment Summary</h3>
                    <table class="details-table">
                        <tr><td>Rent Amount:</td><td>$${(tenant.payment_summary.rent_amount || 0).toFixed(2)}</td></tr>
                        <tr><td>Total Paid:</td><td>$${(tenant.payment_summary.total_paid || 0).toFixed(2)}</td></tr>
                        <tr><td>Delinquency Balance:</td><td class="${tenant.payment_summary.delinquency_balance > 0 ? 'error' : 'success'}">$${(tenant.payment_summary.delinquency_balance || 0).toFixed(2)}</td></tr>
                        <tr><td>Status:</td><td>${tenant.payment_status ? tenant.payment_status.status : 'unknown'}</td></tr>
                    </table>
                </div>
                ` : ''}
                
                <div class="details-section">
                    <h3>Actions</h3>
                    <button class="btn btn-primary" onclick="ui.showCreateDisputeForm('${tenantId}')">
                        Create Dispute
                    </button>
                </div>
            `;
        } catch (error) {
            content.innerHTML = `<div class="error-message">${error.message}</div>`;
        }
    }
    
    // ========== DISPUTES ==========
    
    async loadDisputes() {
        const loadingDiv = document.getElementById('disputesLoading');
        const errorDiv = document.getElementById('disputesError');
        const listDiv = document.getElementById('disputesList');
        
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        listDiv.innerHTML = '';
        
        try {
            const result = await apiClient.getAllDisputes();
            
            if (!result.success) {
                throw new Error(result.error);
            }
            
            const disputes = result.data.disputes || [];
            
            if (disputes.length === 0) {
                listDiv.innerHTML = '<p class="empty-state">No disputes found</p>';
            } else {
                disputes.forEach(dispute => {
                    const row = this.createDisputeRow(dispute);
                    listDiv.appendChild(row);
                });
            }
            
            this.disputesCached = true;
        } catch (error) {
            errorDiv.textContent = `Error loading disputes: ${error.message}`;
            errorDiv.classList.remove('hidden');
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }
    
    createDisputeRow(dispute) {
        const row = document.createElement('div');
        row.className = 'dispute-row';
        
        const statusClass = `status-${dispute.status || 'unknown'}`;
        
        row.innerHTML = `
            <div class="dispute-col dispute-id">
                <strong>${dispute.dispute_id}</strong>
            </div>
            <div class="dispute-col dispute-tenant">
                ${dispute.tenant_id}
            </div>
            <div class="dispute-col dispute-type">
                ${(dispute.dispute_type || 'unknown').replace(/_/g, ' ')}
            </div>
            <div class="dispute-col dispute-amount">
                $${(dispute.amount || 0).toFixed(2)}
            </div>
            <div class="dispute-col dispute-status">
                <span class="status-badge ${statusClass}">${dispute.status || 'unknown'}</span>
            </div>
            <div class="dispute-col dispute-actions">
                <button class="btn btn-secondary btn-small" onclick="ui.viewDisputeDetails('${dispute.dispute_id}')">
                    View
                </button>
            </div>
        `;
        
        return row;
    }
    
    async viewDisputeDetails(disputeId) {
        const modal = document.getElementById('tenantModal');
        const content = document.getElementById('tenantDetailContent');
        
        content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading dispute...</p></div>';
        modal.classList.remove('hidden');
        
        try {
            const result = await apiClient.getDispute(disputeId);
            
            if (!result.success) {
                throw new Error(result.error);
            }
            
            const dispute = result.data.data || {};
            
            content.innerHTML = `
                <h2>Dispute ${dispute.dispute_id}</h2>
                
                <div class="details-section">
                    <h3>Dispute Information</h3>
                    <table class="details-table">
                        <tr><td>Dispute ID:</td><td>${dispute.dispute_id}</td></tr>
                        <tr><td>Tenant ID:</td><td>${dispute.tenant_id}</td></tr>
                        <tr><td>Type:</td><td>${(dispute.dispute_type || 'unknown').replace(/_/g, ' ')}</td></tr>
                        <tr><td>Amount:</td><td>$${(dispute.amount || 0).toFixed(2)}</td></tr>
                        <tr><td>Status:</td><td><span class="status-badge status-${dispute.status || 'unknown'}">${dispute.status || 'unknown'}</span></td></tr>
                        <tr><td>Description:</td><td>${dispute.description || 'N/A'}</td></tr>
                        <tr><td>Created:</td><td>${dispute.created_at || 'N/A'}</td></tr>
                    </table>
                </div>
                
                ${dispute.status !== 'resolved' ? `
                <div class="details-section">
                    <h3>Update Status</h3>
                    <select id="disputeStatusSelect" class="form-control">
                        <option value="">-- Select Status --</option>
                        <option value="acknowledged">Acknowledged</option>
                        <option value="pending_review">Pending Review</option>
                        <option value="resolved">Resolved</option>
                        <option value="rejected">Rejected</option>
                    </select>
                    <textarea id="adminNotes" class="form-control" placeholder="Admin notes..."></textarea>
                    <button class="btn btn-primary" onclick="ui.updateDisputeStatus('${dispute.dispute_id}')">
                        Update Status
                    </button>
                </div>
                ` : ''}
            `;
        } catch (error) {
            content.innerHTML = `<div class="error-message">${error.message}</div>`;
        }
    }
    
    async updateDisputeStatus(disputeId) {
        const status = document.getElementById('disputeStatusSelect').value;
        const notes = document.getElementById('adminNotes').value;
        
        if (!status) {
            alert('Please select a status');
            return;
        }
        
        try {
            const result = await apiClient.updateDisputeStatus(disputeId, status, notes);
            
            if (result.success) {
                alert('Dispute status updated successfully');
                this.closeModal();
                this.loadDisputes();
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
    
    // ========== SYSTEM INFO ==========
    
    async loadSystemInfo() {
        try {
            // Health check
            const health = await apiClient.health();
            const healthStatus = document.getElementById('healthStatus');
            
            if (health.success) {
                healthStatus.className = 'status healthy';
                healthStatus.textContent = '✓ Healthy';
            } else {
                healthStatus.className = 'status unhealthy';
                healthStatus.textContent = '✗ Unhealthy';
            }
            
            // Session token
            document.getElementById('sessionToken').textContent = authManager.token.substring(0, 20) + '...';
            
            // Dispute types
            const typesResult = await apiClient.getDisputeTypes();
            if (typesResult.success) {
                const typesList = document.getElementById('disputeTypesList');
                typesList.innerHTML = '';
                (typesResult.data.types || []).forEach(type => {
                    const li = document.createElement('li');
                    li.textContent = type.name;
                    typesList.appendChild(li);
                });
            }
            
            // Dispute statuses
            const statusesResult = await apiClient.getDisputeStatuses();
            if (statusesResult.success) {
                const statusesList = document.getElementById('disputeStatusesList');
                statusesList.innerHTML = '';
                (statusesResult.data.statuses || []).forEach(status => {
                    const li = document.createElement('li');
                    li.textContent = status.name;
                    statusesList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Error loading system info:', error);
        }
    }
    
    // ========== SETTINGS ==========
    
    saveSettings() {
        const autoRefresh = document.getElementById('autoRefresh').value;
        localStorage.setItem('autoRefresh', autoRefresh);
        
        this.startAutoRefresh(parseInt(autoRefresh));
        alert('Settings saved');
    }
    
    toggleDarkMode(event) {
        const isDark = event.target.checked;
        localStorage.setItem('darkMode', isDark);
        
        if (isDark) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
    
    // ========== AUTO-REFRESH ==========
    
    startAutoRefresh(seconds) {
        this.stopAutoRefresh();
        
        if (seconds > 0) {
            this.autoRefreshInterval = setInterval(() => {
                if (authManager.isAuthenticated()) {
                    this.loadTenants();
                    this.loadDisputes();
                }
            }, seconds * 1000);
        }
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    // ========== UTILITIES ==========
    
    copyTokenToClipboard() {
        const token = authManager.token;
        navigator.clipboard.writeText(token).then(() => {
            alert('Token copied to clipboard');
        });
    }
    
    closeModal() {
        document.getElementById('tenantModal').classList.add('hidden');
    }
    
    showCreateDisputeForm(tenantId) {
        const modal = document.getElementById('tenantModal');
        const content = document.getElementById('tenantDetailContent');
        
        content.innerHTML = `
            <h2>Create Dispute for Tenant ${tenantId}</h2>
            <form id="createDisputeForm">
                <div class="form-group">
                    <label for="disputeType">Dispute Type:</label>
                    <select id="disputeType" name="disputeType" required>
                        <option value="">-- Select Type --</option>
                        <option value="payment_not_recorded">Payment Not Recorded</option>
                        <option value="incorrect_balance">Incorrect Balance</option>
                        <option value="duplicate_charge">Duplicate Charge</option>
                        <option value="overpayment_not_credited">Overpayment Not Credited</option>
                        <option value="service_credit_error">Service Credit Error</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="description">Description:</label>
                    <textarea id="description" name="description" required></textarea>
                </div>
                
                <div class="form-group">
                    <label for="amount">Amount:</label>
                    <input type="number" id="amount" name="amount" step="0.01" required>
                </div>
                
                <div class="form-group">
                    <label for="referenceMonth">Reference Month (YYYY-MM):</label>
                    <input type="text" id="referenceMonth" name="referenceMonth" placeholder="2026-01">
                </div>
                
                <button type="submit" class="btn btn-primary">Create Dispute</button>
                <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Cancel</button>
            </form>
        `;
        
        modal.classList.remove('hidden');
        
        document.getElementById('createDisputeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const disputeType = document.getElementById('disputeType').value;
            const description = document.getElementById('description').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const referenceMonth = document.getElementById('referenceMonth').value;
            
            const disputeData = {
                dispute_type: disputeType,
                description: description,
                amount: amount
            };
            
            if (referenceMonth) {
                const [year, month] = referenceMonth.split('-');
                disputeData.reference_month = [parseInt(year), parseInt(month)];
            }
            
            try {
                const result = await apiClient.createDispute(tenantId, disputeData);
                
                if (result.success) {
                    alert('Dispute created successfully!');
                    this.closeModal();
                    this.loadDisputes();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
}

// Create global UI controller
const ui = new UIController();
