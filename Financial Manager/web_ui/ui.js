/**
 * UI Controller Module
 * Handles all UI interactions and page rendering
 */

class UIController {
    constructor() {
        this.currentTenant = null;
        this.tenantRecords = [];
        this.pendingPayments = [];
        this.selectedTenantId = null;
        this.roleMode = 'admin';
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
        document.getElementById('forceReauthBtn').addEventListener('click', () => this.handleForceReauth());
        
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.handleNavigation(e));
        });
        
        // Refresh buttons
        document.getElementById('refreshTenantsBtn').addEventListener('click', () => this.loadTenants());
        document.getElementById('refreshDisputesBtn').addEventListener('click', () => this.loadDisputes());

        // Tenant view tabs
        document.querySelectorAll('.tenant-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTenantTab(btn.dataset.tenantTab);
            });
        });
        
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

        // Force redirect to login when API client detects auth expiration.
        window.addEventListener('auth:required', (event) => {
            const reason = event?.detail?.reason || 'Authentication required. Please sign in again.';
            this.redirectToLogin(reason);
        });
    }
    
    async checkAuthStatus() {
        if (authManager.isAuthenticated()) {
            const valid = await authManager.verifyToken();
            if (!valid) {
                this.redirectToLogin('Session expired. Please sign in again.');
                return;
            }
            this.showDashboard();
        } else {
            this.redirectToLogin('Please sign in to continue.');
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

                // Move to dashboard promptly; long delays can feel like the redirect failed.
                setTimeout(() => {
                    try {
                        this.showDashboard();
                    } catch (navigationError) {
                        this.redirectToLogin(`Navigation failed: ${navigationError.message}`);
                    }
                }, 250);
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
            this.redirectToLogin('You have been logged out.');
        }
    }

    async handleForceReauth() {
        if (confirm('Force re-authentication now? This will clear your current session.')) {
            await authManager.logout();
            this.redirectToLogin('Session reset. Please sign in again.');
        }
    }
    
    showLogin() {
        document.getElementById('loginPage').classList.add('active');
        document.getElementById('dashboardPage').classList.remove('active');
    }

    redirectToLogin(message = '') {
        this.stopAutoRefresh();
        this.showLogin();

        const successDiv = document.getElementById('loginSuccess');
        const errorDiv = document.getElementById('loginError');
        successDiv.classList.add('hidden');

        if (message) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        } else {
            errorDiv.classList.add('hidden');
        }
    }
    
    showDashboard() {
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('dashboardPage').classList.add('active');

        this.configureRoleMode();
        
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

    formatContactInfo(contactInfo) {
        if (!contactInfo) {
            return 'N/A';
        }
        if (typeof contactInfo === 'string') {
            return contactInfo;
        }
        if (typeof contactInfo === 'object') {
            const pieces = [];
            const orderedKeys = ['name', 'email', 'phone', 'address'];
            orderedKeys.forEach(key => {
                if (contactInfo[key]) {
                    pieces.push(`${key}: ${contactInfo[key]}`);
                }
            });
            Object.keys(contactInfo).forEach(key => {
                if (!orderedKeys.includes(key) && contactInfo[key]) {
                    pieces.push(`${key}: ${contactInfo[key]}`);
                }
            });
            return pieces.length ? pieces.join(' | ') : 'N/A';
        }
        return String(contactInfo);
    }

    formatRentalPeriod(rentalPeriod) {
        if (!rentalPeriod) {
            return 'N/A';
        }
        if (typeof rentalPeriod === 'string') {
            return rentalPeriod;
        }
        if (Array.isArray(rentalPeriod) && rentalPeriod.length >= 2) {
            return `${rentalPeriod[0]} to ${rentalPeriod[1]}`;
        }
        if (typeof rentalPeriod === 'object') {
            const start = rentalPeriod.start_date || rentalPeriod.start || rentalPeriod.from;
            const end = rentalPeriod.end_date || rentalPeriod.end || rentalPeriod.to;
            if (start || end) {
                return `${start || 'N/A'} to ${end || 'N/A'}`;
            }

            // Fallback for unknown object shape without showing [object Object].
            const values = Object.values(rentalPeriod).filter(v => v !== null && v !== undefined && `${v}`.trim() !== '');
            if (values.length >= 2) {
                return `${values[0]} to ${values[1]}`;
            }
            if (values.length === 1) {
                return `${values[0]}`;
            }
            return JSON.stringify(rentalPeriod);
        }
        return String(rentalPeriod);
    }

    deriveAccountBalance(tenant, monthlyItems = []) {
        const summary = tenant.payment_summary || {};
        const delinquency = Number(summary.delinquency_balance || (tenant.delinquency_info || {}).total_delinquency || 0);
        const overpaymentCredit = Number(summary.overpayment_credit || tenant.overpayment_credit || 0);
        const serviceCredit = Number(summary.service_credit || tenant.service_credit || 0);

        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        const dueNowItems = (Array.isArray(monthlyItems) ? monthlyItems : []).filter(item => {
            const year = Number(item.year || 0);
            const month = Number(item.month || 0);
            if (!year || !month) {
                return true;
            }
            return year < currentYear || (year === currentYear && month <= currentMonth);
        });

        const breakdownDue = dueNowItems
            .map(item => Number(item.balance ?? (Number(item.expected_rent || 0) - Number(item.paid_amount || 0))))
            .reduce((acc, value) => acc + (value > 0 ? value : 0), 0);

        const baseDue = delinquency > 0 ? delinquency : breakdownDue;
        const balance = baseDue - overpaymentCredit - serviceCredit;
        return Number(balance.toFixed(2));
    }

    deriveStatusInfo(tenant, accountBalance) {
        if (accountBalance > 0.01) {
            return { label: 'Delinquent!', cssClass: 'status-delinquent' };
        }
        if (accountBalance < -0.01) {
            return { label: 'Credit', cssClass: 'status-paid' };
        }

        const accountStatus = (tenant.account_status || '').toLowerCase();
        if (accountStatus === 'inactive' || accountStatus === 'expired') {
            return { label: accountStatus, cssClass: 'status-pending' };
        }
        return { label: 'Current', cssClass: 'status-paid' };
    }

    getSignedAmountClass(amount, positiveIsBad = false) {
        const numeric = Number(amount || 0);
        if (numeric > 0.01) {
            return positiveIsBad ? 'tone-danger' : 'tone-success';
        }
        if (numeric < -0.01) {
            return positiveIsBad ? 'tone-success' : 'tone-danger';
        }
        return 'tone-muted';
    }

    getStatusToneClass(statusText) {
        const normalized = String(statusText || '').toLowerCase();
        if (!normalized) {
            return 'tone-muted';
        }
        if (normalized.includes('delinquent') || normalized.includes('rejected') || normalized.includes('failed') || normalized.includes('overdue')) {
            return 'tone-danger';
        }
        if (normalized.includes('unpaid')) {
            return 'tone-danger';
        }
        if (normalized.includes('pending') || normalized.includes('review') || normalized.includes('acknowledged')) {
            return 'tone-warning';
        }
        if (normalized.includes('partial')) {
            return 'tone-warning';
        }
        if (normalized.includes('not due')) {
            return 'tone-muted';
        }
        if (normalized.includes('paid') || normalized.includes('current') || normalized.includes('resolved') || normalized.includes('healthy')) {
            return 'tone-success';
        }
        if (normalized.includes('overpayment') || normalized.includes('credit')) {
            return 'tone-info';
        }
        return 'tone-info';
    }

    getPaidComparisonClass(expectedAmount, paidAmount, isDelinquent) {
        const expected = Number(expectedAmount || 0);
        const paid = Number(paidAmount || 0);
        const delta = paid - expected;

        if (delta < -0.01) {
            return isDelinquent ? 'tone-danger' : 'tone-warning';
        }
        if (delta > 0.01) {
            return 'tone-info';
        }
        return 'tone-success';
    }

    getNextPaymentInfo(monthlyItems = []) {
        if (!Array.isArray(monthlyItems) || monthlyItems.length === 0) {
            return {
                monthLabel: 'N/A',
                dueAmount: 0,
                status: 'No scheduled entries'
            };
        }

        const candidates = monthlyItems
            .map(item => {
                const expected = Number(item.expected_rent || 0);
                const paid = Number(item.paid_amount || 0);
                const balance = Number(item.balance ?? (expected - paid));
                return {
                    ...item,
                    expected,
                    paid,
                    balance,
                    key: `${item.year || 0}-${String(item.month || 0).padStart(2, '0')}`
                };
            })
            .sort((a, b) => a.key.localeCompare(b.key));

        const outstanding = candidates.find(item => item.balance > 0.01) || candidates[candidates.length - 1];
        const label = outstanding.month || outstanding.year
            ? `${outstanding.year || 'N/A'}-${String(outstanding.month || 'N/A').padStart(2, '0')}`
            : (outstanding.month_key || 'N/A');

        return {
            monthLabel: label,
            dueAmount: outstanding.balance,
            status: outstanding.status || 'Pending'
        };
    }

    configureRoleMode() {
        this.roleMode = authManager.isTenantAccount() ? 'tenant' : 'admin';

        const badge = document.getElementById('tenantModeBadge');
        const title = document.getElementById('tenantsSectionTitle');
        if (this.roleMode === 'tenant') {
            badge.textContent = 'Tenant Mode: showing your assigned tenancy information';
            badge.classList.remove('hidden', 'admin-mode');
            badge.classList.add('tenant-mode');
            title.textContent = 'My Tenancy';
        } else {
            badge.textContent = 'Admin/Landlord Mode: all available tenants and full detail view';
            badge.classList.remove('hidden', 'tenant-mode');
            badge.classList.add('admin-mode');
            title.textContent = 'Tenants';
        }
    }

    switchTenantTab(tabName) {
        document.querySelectorAll('.tenant-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tenantTab === tabName);
        });

        document.getElementById('tenantOverviewPanel').classList.toggle('active', tabName === 'overview');
        document.getElementById('tenantDetailsPanel').classList.toggle('active', tabName === 'details');
    }

    getDefaultPaymentMonth() {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    }

    normalizePaymentStatus(status, paidAmount) {
        if (Number(paidAmount || 0) > 0) {
            return 'completed';
        }
        const normalized = (status || '').toString().trim().toLowerCase();
        return normalized || 'pending';
    }

    deriveMonthlyPaymentStatus(item, delinquentMonthSet = new Set()) {
        const expected = Number(item?.expected_rent || 0);
        const paid = Number(item?.paid_amount || 0);
        const fallbackBalance = expected - paid;
        const balance = Number(item?.balance ?? fallbackBalance);
        const status = String(item?.status || '').trim().toLowerCase();
        const year = Number(item?.year || 0);
        const month = Number(item?.month || 0);
        const monthKey = item?.month_key || `${year}-${String(month).padStart(2, '0')}`;
        const isDelinquentMonth = delinquentMonthSet.has(monthKey);
        const epsilon = 0.01;

        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const isFutureMonth = year > currentYear || (year === currentYear && month > currentMonth);

        // Prefer explicit backend status values when they are specific and actionable.
        if (status.includes('rejected') || status.includes('failed')) {
            return 'failed';
        }
        if (status.includes('pending') || status.includes('review') || status.includes('approval')) {
            return 'pending';
        }

        if (paid > expected + epsilon && expected > 0) {
            return 'overpayment';
        }
        if (Math.abs(paid - expected) <= epsilon && expected > 0) {
            return 'paid';
        }

        if (paid <= epsilon) {
            if (isFutureMonth || expected <= epsilon) {
                return 'not due';
            }
            return (isDelinquentMonth || balance > epsilon) ? 'delinquent' : 'unpaid';
        }

        if (paid < expected - epsilon) {
            if (isFutureMonth && !isDelinquentMonth) {
                return 'partial (not due)';
            }
            return (isDelinquentMonth || balance > epsilon) ? 'delinquent' : 'partial';
        }

        if (status.includes('delinquent') || status.includes('overdue')) {
            return 'delinquent';
        }
        if (status.includes('not due')) {
            return 'not due';
        }
        if (status.includes('overpayment') || status.includes('credit')) {
            return 'overpayment';
        }
        if (status.includes('paid') || status.includes('completed')) {
            return 'paid';
        }

        return balance > epsilon ? 'delinquent' : 'paid';
    }

    renderPaymentChart(monthlyItems = []) {
        const container = document.getElementById('paymentChartContainer');
        if (!container) {
            return;
        }

        const statusFilter = document.getElementById('paymentChartStatusFilter')?.value || 'all';
        const rangeFilter = document.getElementById('paymentChartRangeFilter')?.value || '12';

        const sorted = [...(monthlyItems || [])].sort((a, b) => {
            const aKey = a.month_key || `${a.year || 0}-${String(a.month || 0).padStart(2, '0')}`;
            const bKey = b.month_key || `${b.year || 0}-${String(b.month || 0).padStart(2, '0')}`;
            return aKey.localeCompare(bKey);
        });

        let filtered = sorted.map(item => {
            const paid = Number(item.paid_amount || 0);
            const expected = Number(item.expected_rent || 0);
            return {
                ...item,
                paid,
                expected,
                normalizedStatus: this.normalizePaymentStatus(item.status, paid)
            };
        });

        if (statusFilter !== 'all') {
            filtered = filtered.filter(item => item.normalizedStatus === statusFilter);
        }

        if (rangeFilter !== 'all') {
            const count = Number(rangeFilter || 12);
            filtered = filtered.slice(Math.max(filtered.length - count, 0));
        }

        if (!filtered.length) {
            container.innerHTML = '<p class="empty-state">No payment rows match the current filters.</p>';
            return;
        }

        const maxAmount = Math.max(
            ...filtered.map(item => Math.max(item.expected, item.paid, 1)),
            1
        );

        const rowsHtml = filtered.map(item => {
            const monthLabel = item.month_key || `${item.year || 'N/A'}-${String(item.month || 'N/A').padStart(2, '0')}`;
            const paidWidth = Math.max(2, (item.paid / maxAmount) * 100);
            const expectedWidth = Math.max(2, (item.expected / maxAmount) * 100);
            const statusClass = this.getStatusToneClass(item.normalizedStatus);
            const dateLabel = item.payment_date || 'N/A';

            return `
                <div class="payment-chart-row">
                    <div class="payment-chart-meta">
                        <span><strong>${monthLabel}</strong></span>
                        <span class="${statusClass}">${item.normalizedStatus}</span>
                        <span>Date: ${dateLabel}</span>
                    </div>
                    <div class="payment-chart-bars">
                        <div class="payment-chart-bar expected" style="width: ${expectedWidth}%">Expected $${item.expected.toFixed(2)}</div>
                        <div class="payment-chart-bar paid" style="width: ${paidWidth}%">Paid $${item.paid.toFixed(2)}</div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="payment-chart-rows">${rowsHtml}</div>`;
    }

    bindPaymentChartControls(monthlyItems = []) {
        const statusSelect = document.getElementById('paymentChartStatusFilter');
        const rangeSelect = document.getElementById('paymentChartRangeFilter');
        if (!statusSelect || !rangeSelect) {
            return;
        }

        statusSelect.onchange = () => this.renderPaymentChart(monthlyItems);
        rangeSelect.onchange = () => this.renderPaymentChart(monthlyItems);
        this.renderPaymentChart(monthlyItems);
    }

    async submitTenantPayment(tenantId) {
        const amountInput = document.getElementById('paymentAmountInput');
        const typeInput = document.getElementById('paymentTypeInput');
        const monthInput = document.getElementById('paymentMonthInput');
        const dateInput = document.getElementById('paymentDateInput');
        const notesInput = document.getElementById('paymentNotesInput');
        const messageDiv = document.getElementById('submitPaymentMessage');

        const amount = Number(amountInput?.value || 0);
        if (!amount || amount <= 0) {
            messageDiv.textContent = 'Please enter a valid payment amount.';
            messageDiv.className = 'error-message';
            return;
        }

        const payload = {
            amount,
            payment_type: typeInput?.value || 'Cash',
            payment_month: monthInput?.value || '',
            payment_date: dateInput?.value || '',
            notes: notesInput?.value || ''
        };

        const result = await apiClient.submitTenantPayment(tenantId, payload);
        if (!result.success) {
            messageDiv.textContent = result.error || 'Failed to submit payment.';
            messageDiv.className = 'error-message';
            return;
        }

        const paymentStatus = result?.data?.data?.payment_status || 'completed';
        const successText = paymentStatus === 'pending'
            ? 'Payment submitted for admin approval.'
            : 'Payment recorded successfully.';

        messageDiv.textContent = successText;
        messageDiv.className = 'success-message';

        if (notesInput) {
            notesInput.value = '';
        }

        await this.loadTenants();
        await this.loadTenantDetails(tenantId);
        await this.loadDisputes();
    }
    
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
            this.tenantRecords = tenants;
            
            if (tenants.length === 0) {
                const emptyMessage = this.roleMode === 'tenant'
                    ? 'No tenancy has been assigned to this account yet.'
                    : 'No tenants found';
                listDiv.innerHTML = `<p class="empty-state">${emptyMessage}</p>`;
                document.getElementById('tenantDetailsPlaceholder').classList.remove('hidden');
                document.getElementById('tenantDetailsContent').classList.add('hidden');
            } else {
                tenants.forEach(tenant => {
                    const card = this.createTenantCard(tenant);
                    listDiv.appendChild(card);
                });

                if (this.roleMode === 'tenant') {
                    await this.selectTenantForDetails(tenants[0].tenant_id, true);
                } else if (this.selectedTenantId) {
                    await this.selectTenantForDetails(this.selectedTenantId, false);
                }
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
        card.dataset.tenantId = tenant.tenant_id || '';
        if (this.selectedTenantId && tenant.tenant_id === this.selectedTenantId) {
            card.classList.add('selected');
        }

        const accountBalance = this.deriveAccountBalance(tenant, []);
        const statusInfo = this.deriveStatusInfo(tenant, accountBalance);
        const balanceFormatted = Number(accountBalance || 0).toFixed(2);
        const rentalPeriod = this.formatRentalPeriod(tenant.rental_period);
        
        card.innerHTML = `
            <div class="card-header">
                <h3>${tenant.name || 'Unknown Tenant'}</h3>
                <span class="status-badge ${statusInfo.cssClass}">${statusInfo.label}</span>
            </div>
            <div class="card-body">
                <div class="card-row">
                    <span class="label">ID:</span>
                    <span class="value">${tenant.tenant_id || 'N/A'}</span>
                </div>
                <div class="card-row">
                    <span class="label">Rental Period:</span>
                    <span class="value">${rentalPeriod}</span>
                </div>
                <div class="card-row">
                    <span class="label">Rent Amount:</span>
                    <span class="value">$${typeof tenant.rent_amount === 'number' ? tenant.rent_amount.toFixed(2) : '0.00'}</span>
                </div>
                <div class="card-row">
                    <span class="label">Account Balance:</span>
                    <span class="value ${accountBalance > 0 ? 'error' : 'success'}">$${balanceFormatted}</span>
                </div>
                <div class="card-row">
                    <span class="label">Delinquency:</span>
                    <span class="value ${accountBalance > 0 ? 'error' : 'success'}">${accountBalance > 0 ? 'Delinquent!' : 'Current'}</span>
                </div>
                ${tenant.contact_info ? `
                <div class="card-row">
                    <span class="label">Contact:</span>
                    <span class="value">${this.formatContactInfo(tenant.contact_info)}</span>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <button class="btn btn-secondary btn-small" onclick="ui.selectTenantForDetails('${tenant.tenant_id}', true)">
                    Open Details Tab
                </button>
            </div>
        `;
        
        return card;
    }
    
    async selectTenantForDetails(tenantId, switchToDetails = true) {
        this.selectedTenantId = tenantId;
        if (switchToDetails) {
            this.switchTenantTab('details');
        }

        document.querySelectorAll('.tenant-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.tenantId === tenantId);
        });

        await this.loadTenantDetails(tenantId);
    }

    async loadTenantDetails(tenantId) {
        const placeholder = document.getElementById('tenantDetailsPlaceholder');
        const content = document.getElementById('tenantDetailsContent');

        placeholder.classList.add('hidden');
        content.classList.remove('hidden');
        content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading full tenant details...</p></div>';

        try {
            const [tenantResult, breakdownResult, disputesResult] = await Promise.all([
                apiClient.getTenant(tenantId),
                apiClient.getMonthlyBreakdown(tenantId),
                apiClient.getTenantDisputes(tenantId)
            ]);

            if (!tenantResult.success) {
                throw new Error(tenantResult.error || 'Failed to load tenant details');
            }

            const tenant = tenantResult.data.data || {};
            const monthlyItems = (breakdownResult.success ? (breakdownResult.data.data || []) : []);
            const disputes = (disputesResult.success ? (disputesResult.data.disputes || []) : []);
            const paymentSummary = tenant.payment_summary || {};
            const delinquencyInfo = tenant.delinquency_info || {};
            const nextPayment = this.getNextPaymentInfo(monthlyItems);
            const accountBalanceValue = this.deriveAccountBalance(tenant, monthlyItems);
            const statusInfo = this.deriveStatusInfo(tenant, accountBalanceValue);
            const delinquentMonthSet = new Set(
                (delinquencyInfo.delinquent_months_detail || []).map(item => {
                    const year = Number(item.year || 0);
                    const month = Number(item.month || 0);
                    return `${year}-${String(month).padStart(2, '0')}`;
                })
            );

            const paymentHistoryRows = monthlyItems
                .filter(item => Number(item.paid_amount || 0) > 0)
                .sort((a, b) => `${b.year}-${String(b.month).padStart(2, '0')}`.localeCompare(`${a.year}-${String(a.month).padStart(2, '0')}`))
                .slice(0, 24);

            const paymentHistoryHtml = paymentHistoryRows.length
                ? paymentHistoryRows.map(item => {
                    const monthLabel = `${item.year || 'N/A'}-${String(item.month || 'N/A').padStart(2, '0')}`;
                    const expected = Number(item.expected_rent || 0);
                    const paidAmount = Number(item.paid_amount || 0);
                    const isDelinquentMonth = delinquentMonthSet.has(monthLabel);
                    const paidClass = this.getPaidComparisonClass(expected, paidAmount, isDelinquentMonth);
                    const statusLabel = this.deriveMonthlyPaymentStatus(item, delinquentMonthSet);
                    const statusClass = this.getStatusToneClass(statusLabel);
                    return `
                        <div class="data-grid-row">
                            <div>${monthLabel}</div>
                            <div>$${expected.toFixed(2)}</div>
                            <div><span class="${paidClass}">$${paidAmount.toFixed(2)}</span></div>
                            <div>${item.payment_date || 'N/A'}</div>
                            <div><span class="${statusClass}">${statusLabel}</span></div>
                        </div>
                    `;
                }).join('')
                : '<div class="data-grid-empty">No payments recorded yet.</div>';

            const monthlyHtml = monthlyItems.length
                ? monthlyItems.map(item => {
                    const monthLabel = item.month_key || `${item.year || 'N/A'}-${String(item.month || 'N/A').padStart(2, '0')}`;
                    const expected = Number(item.expected_rent || 0);
                    const paid = Number(item.paid_amount || 0);
                    const balance = Number(item.balance ?? (expected - paid));
                    const isDelinquentMonth = delinquentMonthSet.has(monthLabel);
                    const paidClass = this.getPaidComparisonClass(expected, paid, isDelinquentMonth);
                    const statusLabel = this.deriveMonthlyPaymentStatus(item, delinquentMonthSet);
                    const statusClass = this.getStatusToneClass(statusLabel);
                    const balanceClass = this.getSignedAmountClass(balance, true);
                    return `
                        <div class="data-grid-row">
                            <div>${monthLabel}</div>
                            <div><span class="${statusClass}">${statusLabel}</span></div>
                            <div>$${expected.toFixed(2)}</div>
                            <div><span class="${paidClass}">$${paid.toFixed(2)}</span></div>
                            <div><span class="${balanceClass}">$${balance.toFixed(2)}</span></div>
                        </div>
                    `;
                }).join('')
                : '<div class="data-grid-empty">No monthly breakdown records.</div>';

            const disputesHtml = disputes.length
                ? disputes.map(d => `<tr><td>${d.dispute_id || 'N/A'}</td><td>${(d.dispute_type || 'unknown').replace(/_/g, ' ')}</td><td>${d.status || 'unknown'}</td><td>$${Number(d.amount || 0).toFixed(2)}</td></tr>`).join('')
                : '<tr><td colspan="4">No disputes for this tenant.</td></tr>';

            const contact = this.formatContactInfo(tenant.contact_info);
            const rentalPeriod = this.formatRentalPeriod(tenant.rental_period);
            const rentAmount = Number(paymentSummary.rent_amount || tenant.rent_amount || 0).toFixed(2);
            const paidAmount = Number(paymentSummary.total_rent_paid || paymentSummary.total_paid || 0).toFixed(2);
            const delinquencyBalance = Number(paymentSummary.delinquency_balance || delinquencyInfo.total_delinquency || 0).toFixed(2);
            const delinquentMonthCount = Number(delinquencyInfo.delinquent_month_count || 0);
            const accountBalance = Number(accountBalanceValue || 0).toFixed(2);
            const delinquencyClass = this.getSignedAmountClass(delinquencyBalance, true);
            const accountBalanceClass = this.getSignedAmountClass(accountBalance, true);
            const nextPaymentClass = this.getSignedAmountClass(nextPayment.dueAmount || 0, true);
            const statusToneClass = this.getStatusToneClass(statusInfo.label);

            content.innerHTML = `
                <h2>${tenant.name || 'Tenant Details'}</h2>
                <div class="details-section">
                    <h3>Profile</h3>
                    <table class="details-table">
                        <tr><td>Tenant ID</td><td>${tenant.tenant_id || 'N/A'}</td></tr>
                        <tr><td>Name</td><td>${tenant.name || 'N/A'}</td></tr>
                        <tr><td>Contact</td><td>${contact}</td></tr>
                        <tr><td>Rental Period</td><td>${rentalPeriod}</td></tr>
                    </table>
                </div>

                <div class="details-section">
                    <h3>Financial Summary</h3>
                    <table class="details-table">
                        <tr><td>Rent Amount</td><td>$${rentAmount}</td></tr>
                        <tr><td>Total Paid</td><td><span class="tone-success">$${paidAmount}</span></td></tr>
                        <tr><td>Delinquency Balance</td><td><span class="${delinquencyClass}">$${delinquencyBalance}</span></td></tr>
                        <tr><td>Account Balance (Due Now)</td><td><span class="${accountBalanceClass}">$${accountBalance}</span></td></tr>
                        <tr><td>Current Status</td><td><span class="${statusToneClass}">${statusInfo.label}</span></td></tr>
                        <tr><td>Next Payment Month</td><td>${nextPayment.monthLabel}</td></tr>
                        <tr><td>Next Payment Due</td><td><span class="${nextPaymentClass}">$${Number(nextPayment.dueAmount || 0).toFixed(2)}</span></td></tr>
                        <tr><td>Next Payment Status</td><td><span class="${this.getStatusToneClass(nextPayment.status)}">${nextPayment.status}</span></td></tr>
                        <tr><td>Delinquent Months</td><td><span class="${delinquentMonthCount > 0 ? 'tone-warning' : 'tone-success'}">${delinquentMonthCount}</span></td></tr>
                        <tr><td>Requires Attention</td><td><span class="${delinquencyInfo.requires_attention ? 'tone-warning' : 'tone-success'}">${delinquencyInfo.requires_attention ? 'Yes' : 'No'}</span></td></tr>
                    </table>
                </div>

                <div class="details-section">
                    <h3>Payment History</h3>
                    <div class="data-grid data-grid-payment-history">
                        <div class="data-grid-header">
                            <div>Month</div>
                            <div>Expected</div>
                            <div>Paid</div>
                            <div>Payment Date</div>
                            <div>Status</div>
                        </div>
                        ${paymentHistoryHtml}
                    </div>
                </div>

                <div class="details-section">
                    <h3>Payment Chart</h3>
                    <div class="inline-form-grid">
                        <select id="paymentChartStatusFilter" class="form-control">
                            <option value="all">All Statuses</option>
                            <option value="completed" selected>Completed</option>
                            <option value="pending">Pending</option>
                        </select>
                        <select id="paymentChartRangeFilter" class="form-control">
                            <option value="6">Last 6 Months</option>
                            <option value="12" selected>Last 12 Months</option>
                            <option value="24">Last 24 Months</option>
                            <option value="all">All Months</option>
                        </select>
                    </div>
                    <div id="paymentChartContainer"></div>
                </div>

                <div class="details-section">
                    <h3>Monthly Breakdown</h3>
                    <div class="data-grid data-grid-monthly-breakdown">
                        <div class="data-grid-header">
                            <div>Month</div>
                            <div>Status</div>
                            <div>Expected</div>
                            <div>Paid</div>
                            <div>Balance</div>
                        </div>
                        ${monthlyHtml}
                    </div>
                </div>

                <div class="details-section">
                    <h3>Submit Payment</h3>
                    <div id="submitPaymentMessage" class="hidden"></div>
                    <div class="inline-form-grid">
                        <input id="paymentAmountInput" class="form-control" type="number" step="0.01" min="0.01" placeholder="Amount" required>
                        <input id="paymentTypeInput" class="form-control" type="text" value="Cash" placeholder="Payment Type">
                        <input id="paymentMonthInput" class="form-control" type="text" value="${this.getDefaultPaymentMonth()}" placeholder="YYYY-MM">
                        <input id="paymentDateInput" class="form-control" type="date" value="${new Date().toISOString().split('T')[0]}">
                    </div>
                    <textarea id="paymentNotesInput" class="form-control" placeholder="Optional notes..."></textarea>
                    <button class="btn btn-primary" onclick="ui.submitTenantPayment('${tenantId}')">Submit Payment</button>
                    <p class="help-text">${this.roleMode === 'tenant' ? 'Tenant submissions are marked pending until admin approval.' : 'Landlord/admin submissions are recorded immediately.'}</p>
                </div>

                <div class="details-section">
                    <h3>Disputes</h3>
                    <table class="details-table">
                        <tr><td><strong>ID</strong></td><td><strong>Type</strong></td><td><strong>Status</strong></td><td><strong>Amount</strong></td></tr>
                        ${disputesHtml}
                    </table>
                </div>

                <div class="details-section">
                    <button class="btn btn-primary" onclick="ui.showCreateDisputeForm('${tenantId}')">Create Dispute</button>
                </div>
            `;

            this.bindPaymentChartControls(monthlyItems);
        } catch (error) {
            content.innerHTML = `<div class="error-message">Error loading tenant details: ${error.message}</div>`;
        }
    }

    async viewTenantDetails(tenantId) {
        // Backward-compatible alias used by legacy click handlers.
        await this.selectTenantForDetails(tenantId, true);
    }
    
    // ========== DISPUTES ==========
    
    async loadDisputes() {
        const loadingDiv = document.getElementById('disputesLoading');
        const errorDiv = document.getElementById('disputesError');
        const listDiv = document.getElementById('disputesList');
        const pendingPanel = document.getElementById('pendingPaymentsPanel');
        const pendingList = document.getElementById('pendingPaymentsList');
        
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        listDiv.innerHTML = '';

        if (this.roleMode === 'admin') {
            pendingPanel.classList.remove('hidden');
            pendingList.innerHTML = '<p class="empty-state">Loading pending payment submissions...</p>';
        } else {
            pendingPanel.classList.add('hidden');
            pendingList.innerHTML = '';
        }
        
        try {
            const requests = [apiClient.getAllDisputes()];
            if (this.roleMode === 'admin') {
                requests.push(apiClient.getPendingPayments());
            }

            const responses = await Promise.all(requests);
            const result = responses[0];
            
            if (!result.success) {
                throw new Error(result.error);
            }
            
            const disputes = result.data.disputes || [];
            
            if (disputes.length === 0) {
                const emptyText = this.roleMode === 'tenant'
                    ? 'No disputes found for your tenancy.'
                    : 'No disputes found';
                listDiv.innerHTML = `<p class="empty-state">${emptyText}</p>`;
            } else {
                disputes.forEach(dispute => {
                    const row = this.createDisputeRow(dispute);
                    listDiv.appendChild(row);
                });
            }

            if (this.roleMode === 'admin') {
                const pendingResult = responses[1];
                if (pendingResult && pendingResult.success) {
                    this.pendingPayments = pendingResult.data.payments || [];
                    this.renderPendingPayments();
                } else {
                    pendingList.innerHTML = `<div class="error-message">Failed to load pending payments: ${pendingResult?.error || 'Unknown error'}</div>`;
                }
            }
            
            this.disputesCached = true;
        } catch (error) {
            errorDiv.textContent = `Error loading disputes: ${error.message}`;
            errorDiv.classList.remove('hidden');
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }

    renderPendingPayments() {
        const pendingList = document.getElementById('pendingPaymentsList');
        const items = Array.isArray(this.pendingPayments) ? this.pendingPayments : [];

        if (!items.length) {
            pendingList.innerHTML = '<p class="empty-state">No pending payment submissions.</p>';
            return;
        }

        pendingList.innerHTML = items.map(item => {
            const amount = Number(item.amount || 0).toFixed(2);
            const paymentMonth = item.payment_month || 'N/A';
            const dateValue = item.payment_date || 'N/A';
            const submitter = item.submitted_by || 'unknown';
            const notes = item.notes ? `<div class="pending-payment-meta">Notes: ${item.notes}</div>` : '';

            return `
                <div class="pending-payment-card">
                    <div class="pending-payment-head">
                        <strong>${item.tenant_name || item.tenant_id}</strong>
                        <span class="tone-info">$${amount}</span>
                    </div>
                    <div class="pending-payment-meta">Month: ${paymentMonth} | Date: ${dateValue}</div>
                    <div class="pending-payment-meta">Type: ${item.payment_type || 'Online'} | Submitted by: ${submitter}</div>
                    ${notes}
                    <div class="pending-payment-actions">
                        <button class="btn btn-primary btn-small" onclick="ui.approvePendingPayment('${item.action_id}')">Approve</button>
                        <button class="btn btn-secondary btn-small" onclick="ui.denyPendingPayment('${item.action_id}')">Deny</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    async approvePendingPayment(actionId) {
        const result = await apiClient.approvePendingPayment(actionId);
        if (!result.success) {
            alert(`Failed to approve payment: ${result.error}`);
            return;
        }

        await this.loadDisputes();
        await this.loadTenants();
        if (this.selectedTenantId) {
            await this.loadTenantDetails(this.selectedTenantId);
        }
    }

    async denyPendingPayment(actionId) {
        const reason = prompt('Reason for denying this payment request (optional):', '') || '';
        const result = await apiClient.denyPendingPayment(actionId, reason);
        if (!result.success) {
            alert(`Failed to deny payment: ${result.error}`);
            return;
        }

        await this.loadDisputes();
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
window.ui = new UIController();
