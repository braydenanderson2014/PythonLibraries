"""
Rent Management Web Server
Flask-based REST API for rent management system.
Provides read-only access to tenant data and dispute management.
Integrates with existing RentTracker without modification.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Tuple, Dict, Any, Optional
from functools import wraps
import os
import sys
import threading
from datetime import datetime

# Add paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ui')))

from assets.Logger import Logger
from src.rent_api import RentStatusAPI, DisputeStatus, DisputeType
from src.rent_api_auth import SessionManager, RentAPIAuthenticator

logger = Logger()


def require_auth(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        token = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Missing or invalid authorization token',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # Verify token
        session = request.session_manager.verify_token(token)
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # Add session to request context
        request.current_user = session

        # Initialize request-scoped API context for authenticated user, except simple auth endpoints.
        if f.__name__ not in ('verify_token', 'logout'):
            try:
                request.current_api = request.server._ensure_user_api(session)
            except Exception as e:
                logger.error("RentServer", f"Failed to initialize API context for user {session.get('username')}: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to initialize user context: {e}',
                    'timestamp': datetime.now().isoformat()
                }), 503

        return f(*args, **kwargs)
    
    return decorated_function


class RentManagementServer:
    """Flask web server for rent management with dispute system and authentication"""
    
    def __init__(
        self,
        account_manager=None,
        rent_tracker=None,
        host: str = '0.0.0.0',
        port: int = 5000,
        debug: bool = False
    ):
        """
        Initialize rent management server
        
        Args:
            account_manager: AccountManager for user authentication
            rent_tracker: RentTracker instance (loaded after auth)
            host: Server host address
            port: Server port
            debug: Enable debug mode
        """
        self.account_manager = account_manager
        self.rent_tracker = rent_tracker
        self.api = None  # Created after authenticated user loads RentTracker
        self._api_by_user_id = {}
        self._tracker_by_user_id = {}
        self._api_lock = threading.Lock()
        self.host = host
        self.port = port
        self.debug = debug
        
        # Initialize session and auth managers
        self.session_manager = SessionManager(timeout_seconds=3600)
        self.authenticator = RentAPIAuthenticator(account_manager, self.session_manager)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False
        
        # Enable CORS
        CORS(self.app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        
        # Make session_manager available to request context
        @self.app.before_request
        def before_request():
            request.session_manager = self.session_manager
            request.authenticator = self.authenticator
            request.server = self

        logger.info("RentServer", "Initializing Rent Management Web Server with authentication")
        self._setup_routes()
        logger.info("RentServer", "Rent Management Server initialized successfully")

    def _ensure_user_api(self, session: Dict[str, Any]) -> RentStatusAPI:
        """Ensure a RentStatusAPI instance exists for the authenticated user."""
        user_id = session.get('user_id')
        username = session.get('username', 'unknown')
        principal = username or user_id

        if not user_id:
            raise ValueError("Missing user_id in authenticated session")

        with self._api_lock:
            existing_api = self._api_by_user_id.get(user_id)
            if existing_api:
                return existing_api

            # Lazy-create tracker/API for this authenticated user.
            # Use username when available because tenant assignments are commonly keyed by username.
            from src.rent_tracker import RentTracker
            tracker = RentTracker(current_user_id=principal)
            api = RentStatusAPI(tracker)

            self._tracker_by_user_id[user_id] = tracker
            self._api_by_user_id[user_id] = api

            # Keep legacy attribute populated for backward compatibility with any existing code paths.
            self.rent_tracker = tracker
            self.api = api

            logger.info("RentServer", f"Initialized RentStatusAPI for authenticated user: {username}")
            return api
    
    def _setup_routes(self):
        """Setup all Flask routes"""

        def require_landlord_access():
            """Tenant-only accounts cannot perform landlord/admin dispute actions."""
            if request.current_user.get('is_tenant', False):
                return jsonify({
                    'status': 'error',
                    'message': 'Tenant accounts do not have access to this landlord/admin endpoint.',
                    'timestamp': datetime.now().isoformat()
                }), 403
            return None

        def get_accessible_tenant_ids(api):
            """Resolve tenant IDs visible to the current authenticated user."""
            try:
                statuses = api.get_all_tenants_status() or []
                tenant_ids = []
                for item in statuses:
                    if isinstance(item, dict) and item.get('tenant_id'):
                        tenant_ids.append(item.get('tenant_id'))
                return set(tenant_ids)
            except Exception:
                return set()

        def require_tenant_membership(api, tenant_id):
            """Ensure tenant users can only access their own tenant records."""
            if not request.current_user.get('is_tenant', False):
                return None

            allowed = get_accessible_tenant_ids(api)
            if tenant_id not in allowed:
                return jsonify({
                    'status': 'error',
                    'message': 'Tenant account cannot access this tenant data.',
                    'timestamp': datetime.now().isoformat()
                }), 403
            return None
        
        # ========== AUTHENTICATION ENDPOINTS ==========
        
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """Login endpoint - returns authentication token"""
            try:
                data = request.get_json()
                
                if not data or 'username' not in data or 'password' not in data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing username or password',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # Authenticate user
                result = request.authenticator.authenticate_user(
                    data['username'],
                    data['password']
                )
                
                if not result or not isinstance(result, dict) or not result.get('success'):
                    logger.warning("RentServer", f"Login failed for user: {data.get('username')}")
                    error_message = 'Authentication failed'
                    if isinstance(result, dict):
                        error_message = result.get('error', error_message)
                    return jsonify({
                        'status': 'error',
                        'message': error_message,
                        'timestamp': datetime.now().isoformat()
                    }), 401

                if result.get('two_factor_required'):
                    return jsonify({
                        'status': 'success',
                        'two_factor_required': True,
                        'challenge_id': result['challenge_id'],
                        'username': result['username'],
                        'message': result.get('message', 'Two-factor authentication required'),
                        'challenge_expires_in_seconds': result.get('challenge_expires_in_seconds', 300),
                        'timestamp': datetime.now().isoformat()
                    }), 200
                
                logger.info("RentServer", f"User logged in: {data['username']}")
                return jsonify({
                    'status': 'success',
                    'token': result['token'],
                    'user_id': result['user_id'],
                    'username': result['username'],
                    'is_admin': result.get('is_admin', False),
                    'is_tenant': result.get('is_tenant', False),
                    'session_expires_in_seconds': result['session_expires_in_seconds'],
                    'timestamp': datetime.now().isoformat()
                }), 200
            
            except Exception as e:
                logger.error("RentServer", f"Login error: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/auth/verify-2fa', methods=['POST'])
        def verify_two_factor_login():
            """Verify second factor and issue API token"""
            try:
                data = request.get_json() or {}
                challenge_id = data.get('challenge_id')
                code = str(data.get('code', '')).strip()

                if not challenge_id or not code:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing challenge_id or code',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                result = request.authenticator.verify_2fa_and_create_session(challenge_id, code)
                if not result.get('success'):
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', '2FA verification failed'),
                        'timestamp': datetime.now().isoformat()
                    }), 401

                return jsonify({
                    'status': 'success',
                    'token': result['token'],
                    'user_id': result['user_id'],
                    'username': result['username'],
                    'is_admin': result.get('is_admin', False),
                    'is_tenant': result.get('is_tenant', False),
                    'session_expires_in_seconds': result['session_expires_in_seconds'],
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"2FA verification error: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/auth/setup-info', methods=['GET'])
        def get_setup_info():
            """Return public account setup details by setup token."""
            setup_token = request.args.get('token', '').strip()
            if not setup_token:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing setup token',
                    'timestamp': datetime.now().isoformat()
                }), 400

            if not hasattr(request.server.account_manager, 'get_setup_info'):
                return jsonify({
                    'status': 'error',
                    'message': 'Setup flow is not supported by current account manager',
                    'timestamp': datetime.now().isoformat()
                }), 501

            result = request.server.account_manager.get_setup_info(setup_token)
            if not result.get('success'):
                return jsonify({
                    'status': 'error',
                    'message': result.get('error', 'Invalid setup token'),
                    'timestamp': datetime.now().isoformat()
                }), 400

            return jsonify({
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }), 200

        @self.app.route('/api/auth/complete-setup', methods=['POST'])
        def complete_setup():
            """Finish account setup using a tokenized invite link."""
            try:
                data = request.get_json() or {}
                setup_token = str(data.get('token', '')).strip()
                password = str(data.get('password', ''))
                confirm_password = str(data.get('confirm_password', password))
                enable_two_factor = bool(data.get('enable_two_factor', False))

                if not setup_token or not password:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing token or password',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                if password != confirm_password:
                    return jsonify({
                        'status': 'error',
                        'message': 'Passwords do not match',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                if len(password) < 8:
                    return jsonify({
                        'status': 'error',
                        'message': 'Password must be at least 8 characters',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                if not hasattr(request.server.account_manager, 'complete_setup'):
                    return jsonify({
                        'status': 'error',
                        'message': 'Setup flow is not supported by current account manager',
                        'timestamp': datetime.now().isoformat()
                    }), 501

                result = request.server.account_manager.complete_setup(
                    setup_token,
                    password,
                    enable_two_factor=enable_two_factor
                )

                if not result.get('success'):
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', 'Failed to complete setup'),
                        'timestamp': datetime.now().isoformat()
                    }), 400

                response = {
                    'status': 'success',
                    'message': 'Account setup completed successfully',
                    'username': result.get('username'),
                    'timestamp': datetime.now().isoformat()
                }
                if result.get('two_factor_secret'):
                    response['two_factor_secret'] = result['two_factor_secret']
                    response['two_factor_uri'] = result.get('two_factor_uri')
                    response['two_factor_qr_url'] = result.get('two_factor_qr_url')
                return jsonify(response), 200

            except Exception as e:
                logger.error("RentServer", f"Complete setup error: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/auth/verify', methods=['GET'])
        @require_auth
        def verify_token():
            """Verify current authentication token is valid"""
            return jsonify({
                'status': 'success',
                'user_id': request.current_user['user_id'],
                'username': request.current_user['username'],
                'is_admin': request.current_user.get('is_admin', False),
                'is_tenant': request.current_user.get('is_tenant', False),
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        @require_auth
        def logout():
            """Logout - revoke authentication token"""
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                request.session_manager.revoke_token(token)
                logger.info("RentServer", f"User logged out: {request.current_user['username']}")
            
            return jsonify({
                'status': 'success',
                'message': 'Logged out successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # ========== HEALTH & STATUS ==========
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint (no auth required)"""
            return jsonify({
                'status': 'healthy',
                'service': 'rent-management-server',
                'requires_auth': True,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }), 200
        
        # ========== TENANT STATUS ENDPOINTS (All require auth) ==========
        
        @self.app.route('/api/tenants', methods=['GET'])
        @require_auth
        def get_all_tenants():
            """Get status for all tenants"""
            try:
                api = getattr(request, 'current_api', None)
                if not api:
                    return jsonify({
                        'status': 'error',
                        'message': 'API not initialized',
                        'timestamp': datetime.now().isoformat()
                    }), 503
                
                statuses = api.get_all_tenants_status()
                return jsonify({
                    'status': 'success',
                    'count': len(statuses),
                    'tenants': statuses,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching all tenants: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>', methods=['GET'])
        @require_auth
        def get_tenant(tenant_id):
            """Get comprehensive status for a specific tenant"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                tenant_status = api.get_tenant_status(tenant_id)
                if not tenant_status:
                    return jsonify({
                        'status': 'error',
                        'message': f'Tenant {tenant_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'data': tenant_status,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching tenant {tenant_id}: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/payment-summary', methods=['GET'])
        @require_auth
        def get_payment_summary(tenant_id):
            """Get payment summary for tenant"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                summary = api.get_payment_summary(tenant_id)
                if not summary:
                    return jsonify({
                        'status': 'error',
                        'message': f'Tenant {tenant_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'data': summary,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching payment summary: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/delinquency', methods=['GET'])
        @require_auth
        def get_delinquency(tenant_id):
            """Get delinquency information for tenant"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                delinquency = api.get_delinquency_info(tenant_id)
                if not delinquency:
                    return jsonify({
                        'status': 'error',
                        'message': f'Tenant {tenant_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'data': delinquency,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching delinquency info: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/monthly-breakdown', methods=['GET'])
        @require_auth
        def get_monthly_breakdown(tenant_id):
            """Get detailed monthly breakdown for tenant"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                breakdown = api.get_monthly_breakdown(tenant_id)
                if not breakdown:
                    return jsonify({
                        'status': 'error',
                        'message': f'Tenant {tenant_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'data': breakdown,
                    'count': len(breakdown),
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching monthly breakdown: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/tenants/<tenant_id>/payments', methods=['POST'])
        @require_auth
        def submit_payment(tenant_id):
            """Submit a payment for tenant (tenant submissions are pending approval)."""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                data = request.get_json() or {}
                amount = data.get('amount')
                if amount is None:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required field: amount',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                submitter_role = 'tenant' if request.current_user.get('is_tenant', False) else 'landlord'
                result = api.submit_payment(
                    tenant_id=tenant_id,
                    amount=amount,
                    payment_type=data.get('payment_type', 'Online'),
                    payment_date=data.get('payment_date'),
                    payment_month=data.get('payment_month'),
                    notes=data.get('notes'),
                    submitted_by=request.current_user.get('username'),
                    submitter_role=submitter_role
                )

                if result.get('error'):
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error'),
                        'timestamp': datetime.now().isoformat()
                    }), 400

                response_code = 202 if result.get('payment_status') == 'pending' else 201
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }), response_code
            except Exception as e:
                logger.error("RentServer", f"Error submitting payment: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/payments/pending', methods=['GET'])
        @require_auth
        def get_pending_payments():
            """Get pending payment submissions."""
            try:
                api = request.current_api
                tenant_ids = None
                if request.current_user.get('is_tenant', False):
                    tenant_ids = get_accessible_tenant_ids(api)

                pending = api.get_pending_payment_submissions(tenant_ids=tenant_ids)
                return jsonify({
                    'status': 'success',
                    'count': len(pending),
                    'payments': pending,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching pending payments: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/payments/pending/<action_id>/approve', methods=['POST'])
        @require_auth
        def approve_pending_payment(action_id):
            """Approve a tenant-submitted pending payment request."""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                result = api.approve_pending_payment(
                    action_id=action_id,
                    approved_by=request.current_user.get('username')
                )

                if result.get('error'):
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error'),
                        'timestamp': datetime.now().isoformat()
                    }), 400

                return jsonify({
                    'status': 'success',
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error approving pending payment: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/payments/pending/<action_id>/deny', methods=['POST'])
        @require_auth
        def deny_pending_payment(action_id):
            """Deny a tenant-submitted pending payment request."""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                data = request.get_json() or {}
                result = api.deny_pending_payment(
                    action_id=action_id,
                    denied_by=request.current_user.get('username'),
                    reason=data.get('reason', '')
                )

                if result.get('error'):
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error'),
                        'timestamp': datetime.now().isoformat()
                    }), 400

                return jsonify({
                    'status': 'success',
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error denying pending payment: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/export', methods=['GET'])
        @require_auth
        def export_tenant_data(tenant_id):
            """Export complete tenant data snapshot"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                data = api.export_tenant_data(tenant_id)
                return jsonify({
                    'status': 'success',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error exporting tenant data: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ========== DISPUTE ENDPOINTS ==========
        
        @self.app.route('/api/disputes', methods=['GET'])
        @require_auth
        def get_all_disputes():
            """Get all disputes across all tenants"""
            try:
                api = request.current_api
                if request.current_user.get('is_tenant', False):
                    disputes = []
                    for tenant_id in get_accessible_tenant_ids(api):
                        disputes.extend(api.get_tenant_disputes(tenant_id) or [])

                    # Deduplicate by dispute id to avoid accidental duplicates across joins.
                    deduped = {}
                    for dispute in disputes:
                        dispute_id = dispute.get('dispute_id') if isinstance(dispute, dict) else None
                        key = dispute_id or str(dispute)
                        deduped[key] = dispute
                    disputes = list(deduped.values())
                else:
                    disputes = api.get_all_disputes()

                return jsonify({
                    'status': 'success',
                    'count': len(disputes),
                    'disputes': disputes,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching all disputes: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/disputes/<dispute_id>', methods=['GET'])
        @require_auth
        def get_dispute(dispute_id):
            """Get specific dispute"""
            try:
                api = request.current_api
                dispute = api.get_dispute(dispute_id)
                if not dispute:
                    return jsonify({
                        'status': 'error',
                        'message': f'Dispute {dispute_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                if request.current_user.get('is_tenant', False):
                    tenant_id = dispute.get('tenant_id') if isinstance(dispute, dict) else None
                    allowed = get_accessible_tenant_ids(api)
                    if not tenant_id or tenant_id not in allowed:
                        return jsonify({
                            'status': 'error',
                            'message': 'Tenant account cannot access this dispute.',
                            'timestamp': datetime.now().isoformat()
                        }), 403

                return jsonify({
                    'status': 'success',
                    'data': dispute,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching dispute: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/disputes', methods=['GET'])
        @require_auth
        def get_tenant_disputes(tenant_id):
            """Get all disputes for a tenant"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                disputes = api.get_tenant_disputes(tenant_id)
                return jsonify({
                    'status': 'success',
                    'count': len(disputes),
                    'disputes': disputes,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching tenant disputes: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/disputes', methods=['POST'])
        @require_auth
        def create_dispute(tenant_id):
            """Create a new dispute (web UI tenant interface)"""
            try:
                api = request.current_api
                membership_error = require_tenant_membership(api, tenant_id)
                if membership_error:
                    return membership_error

                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'status': 'error',
                        'message': 'No JSON data provided',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # Validate required fields
                required_fields = ['dispute_type', 'description']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'status': 'error',
                            'message': f'Missing required field: {field}',
                            'timestamp': datetime.now().isoformat()
                        }), 400
                
                # Parse reference month if provided
                reference_month = None
                if 'reference_month' in data and data['reference_month']:
                    ref = data['reference_month']
                    if isinstance(ref, str):
                        parts = ref.split('-')
                        reference_month = (int(parts[0]), int(parts[1]))
                    elif isinstance(ref, list) and len(ref) == 2:
                        reference_month = tuple(ref)
                
                # Create dispute
                dispute = api.create_dispute(
                    tenant_id=tenant_id,
                    dispute_type=data.get('dispute_type'),
                    description=data.get('description'),
                    amount=data.get('amount'),
                    reference_month=reference_month,
                    evidence_notes=data.get('evidence_notes')
                )

                dispute_id = dispute.get('dispute_id') if isinstance(dispute, dict) else getattr(dispute, 'dispute_id', None)
                logger.info("RentServer", f"Dispute created: {dispute_id} for tenant {tenant_id}")
                dispute_payload = dispute if isinstance(dispute, dict) else dispute.to_dict()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Dispute created successfully',
                    'dispute': dispute_payload,
                    'timestamp': datetime.now().isoformat()
                }), 201
            except Exception as e:
                logger.error("RentServer", f"Error creating dispute: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/disputes/<dispute_id>/status', methods=['PUT'])
        @require_auth
        def update_dispute_status(dispute_id):
            """Update dispute status (admin endpoint)"""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                data = request.get_json()
                
                if not data or 'status' not in data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required field: status',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                admin_notes = data.get('admin_notes')
                
                # Validate status
                valid_statuses = [s.value for s in DisputeStatus]
                if data['status'] not in valid_statuses:
                    return jsonify({
                        'status': 'error',
                        'message': f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                success = api.update_dispute_status(
                    dispute_id=dispute_id,
                    status=data['status'],
                    admin_notes=admin_notes
                )
                
                if not success:
                    return jsonify({
                        'status': 'error',
                        'message': f'Dispute {dispute_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                updated_dispute = api.get_dispute(dispute_id)
                logger.info("RentServer", f"Dispute {dispute_id} status updated to {data['status']}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Dispute status updated',
                    'dispute': updated_dispute,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error updating dispute status: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ========== DISPUTE DISPLAY ENDPOINTS ==========
        
        @self.app.route('/api/disputes/admin/dashboard', methods=['GET'])
        @require_auth
        def get_admin_dispute_dashboard():
            """Get all disputes awaiting admin review"""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                dashboard_data = api.get_admin_dispute_dashboard()
                return jsonify({
                    'status': 'success',
                    'data': dashboard_data,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching dispute dashboard: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/payments/<payment_id>/disputes', methods=['GET'])
        @require_auth
        def get_payment_dispute_status(payment_id):
            """Get dispute status for a specific payment"""
            try:
                api = request.current_api
                dispute_status = api.get_payment_dispute_display(payment_id)
                return jsonify({
                    'status': 'success',
                    'data': dispute_status,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching payment dispute status: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/delinquencies/<int:year>/<int:month>/disputes', methods=['GET'])
        @require_auth
        def get_delinquency_dispute_status(tenant_id, year, month):
            """Get dispute status for a delinquent month"""
            try:
                api = request.current_api
                dispute_status = api.get_delinquency_dispute_display(tenant_id, year, month)
                return jsonify({
                    'status': 'success',
                    'data': dispute_status,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching delinquency dispute status: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tenants/<tenant_id>/dispute-summary', methods=['GET'])
        @require_auth
        def get_tenant_dispute_summary(tenant_id):
            """Get dispute summary for a specific tenant"""
            try:
                api = request.current_api
                summary = api.get_tenant_dispute_dashboard(tenant_id)
                return jsonify({
                    'status': 'success',
                    'data': summary,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logger.error("RentServer", f"Error fetching tenant dispute summary: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ========== DISPUTE ADMIN ACTION ENDPOINTS ==========
        
        @self.app.route('/api/disputes/<dispute_id>/uphold', methods=['POST'])
        @require_auth
        def uphold_dispute_admin(dispute_id):
            """Admin upholds a dispute"""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                data = request.get_json() or {}
                admin_notes = data.get('admin_notes', 'Upheld by admin')
                action = data.get('action', 'payment_corrected')
                
                result = api.uphold_dispute_admin(dispute_id, admin_notes, action)
                
                if result.get('success'):
                    logger.info("RentServer", f"Dispute {dispute_id} upheld")
                    return jsonify({
                        'status': 'success',
                        'message': 'Dispute upheld',
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', 'Failed to uphold dispute'),
                        'timestamp': datetime.now().isoformat()
                    }), 500
            except Exception as e:
                logger.error("RentServer", f"Error upholding dispute: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/disputes/<dispute_id>/deny', methods=['POST'])
        @require_auth
        def deny_dispute_admin(dispute_id):
            """Admin denies a dispute"""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                data = request.get_json() or {}
                admin_notes = data.get('admin_notes', 'Denied by admin')
                reason = data.get('reason', 'evidence_insufficient')
                
                result = api.deny_dispute_admin(dispute_id, admin_notes, reason)
                
                if result.get('success'):
                    logger.info("RentServer", f"Dispute {dispute_id} denied")
                    return jsonify({
                        'status': 'success',
                        'message': 'Dispute denied',
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', 'Failed to deny dispute'),
                        'timestamp': datetime.now().isoformat()
                    }), 500
            except Exception as e:
                logger.error("RentServer", f"Error denying dispute: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/disputes/<dispute_id>/review', methods=['POST'])
        @require_auth
        def mark_dispute_for_review(dispute_id):
            """Mark dispute as pending review"""
            try:
                access_error = require_landlord_access()
                if access_error:
                    return access_error

                api = request.current_api
                result = api.mark_dispute_for_review(dispute_id)
                
                if result.get('success'):
                    logger.info("RentServer", f"Dispute {dispute_id} marked for review")
                    return jsonify({
                        'status': 'success',
                        'message': 'Dispute marked for review',
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', 'Failed to mark dispute for review'),
                        'timestamp': datetime.now().isoformat()
                    }), 500
            except Exception as e:
                logger.error("RentServer", f"Error marking dispute for review: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ========== INFO ENDPOINTS ==========
        
        @self.app.route('/api/info/dispute-types', methods=['GET'])
        def get_dispute_types():
            """Get available dispute types"""
            types = [
                {'value': t.value, 'name': t.value.replace('_', ' ').title()}
                for t in DisputeType
            ]
            return jsonify({
                'status': 'success',
                'types': types,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/api/info/dispute-statuses', methods=['GET'])
        def get_dispute_statuses():
            """Get available dispute statuses"""
            statuses = [
                {'value': s.value, 'name': s.value.replace('_', ' ').title()}
                for s in DisputeStatus
            ]
            return jsonify({
                'status': 'success',
                'statuses': statuses,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # ========== ERROR HANDLERS ==========
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors"""
            return jsonify({
                'status': 'error',
                'message': 'Endpoint not found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors"""
            logger.error("RentServer", f"Internal server error: {error}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self):
        """Run the Flask server"""
        logger.info(
            "RentServer",
            f"Starting Rent Management Server on {self.host}:{self.port}"
        )
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False  # Disable reloader to avoid double initialization
        )
    
    def get_app(self):
        """Get Flask app for external use (testing, WSGI servers, etc.)"""
        return self.app


def create_server(account_manager, rent_tracker=None, host='0.0.0.0', port=5000, debug=False):
    """
    Factory function to create a rent management server
    
    Args:
        account_manager: AccountManager for authentication
        rent_tracker: RentTracker instance (optional, loaded after auth)
        host: Server host
        port: Server port
        debug: Debug mode
    
    Returns:
        RentManagementServer instance
    """
    server = RentManagementServer(account_manager, rent_tracker, host, port, debug)
    
    # If rent_tracker provided, initialize API
    if rent_tracker:
        server.api = RentStatusAPI(rent_tracker)
        logger.info("RentServer", "RentStatusAPI initialized with provided rent_tracker")
    
    return server
