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
        
        logger.info("RentServer", "Initializing Rent Management Web Server with authentication")
        self._setup_routes()
        logger.info("RentServer", "Rent Management Server initialized successfully")
    
    def _setup_routes(self):
        """Setup all Flask routes"""
        
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
                
                if not result or not result.get('success'):
                    logger.warning("RentServer", f"Login failed for user: {data.get('username')}")
                    return jsonify({
                        'status': 'error',
                        'message': result.get('error', 'Authentication failed'),
                        'timestamp': datetime.now().isoformat()
                    }), 401
                
                logger.info("RentServer", f"User logged in: {data['username']}")
                return jsonify({
                    'status': 'success',
                    'token': result['token'],
                    'user_id': result['user_id'],
                    'username': result['username'],
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
        
        @self.app.route('/api/auth/verify', methods=['GET'])
        @require_auth
        def verify_token():
            """Verify current authentication token is valid"""
            return jsonify({
                'status': 'success',
                'user_id': request.current_user['user_id'],
                'username': request.current_user['username'],
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
                if not self.api:
                    return jsonify({
                        'status': 'error',
                        'message': 'API not initialized',
                        'timestamp': datetime.now().isoformat()
                    }), 503
                
                statuses = self.api.get_all_tenants_status()
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
                tenant_status = self.api.get_tenant_status(tenant_id)
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
                summary = self.api.get_payment_summary(tenant_id)
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
                delinquency = self.api.get_delinquency_info(tenant_id)
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
                breakdown = self.api.get_monthly_breakdown(tenant_id)
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
        
        @self.app.route('/api/tenants/<tenant_id>/export', methods=['GET'])
        @require_auth
        def export_tenant_data(tenant_id):
            """Export complete tenant data snapshot"""
            try:
                data = self.api.export_tenant_data(tenant_id)
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
                disputes = self.api.get_all_disputes()
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
                dispute = self.api.get_dispute(dispute_id)
                if not dispute:
                    return jsonify({
                        'status': 'error',
                        'message': f'Dispute {dispute_id} not found',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
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
                disputes = self.api.get_tenant_disputes(tenant_id)
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
                dispute = self.api.create_dispute(
                    tenant_id=tenant_id,
                    dispute_type=data.get('dispute_type'),
                    description=data.get('description'),
                    amount=data.get('amount'),
                    reference_month=reference_month,
                    evidence_notes=data.get('evidence_notes')
                )
                
                logger.info("RentServer", f"Dispute created: {dispute.dispute_id} for tenant {tenant_id}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Dispute created successfully',
                    'dispute': dispute.to_dict(),
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
                
                success = self.api.update_dispute_status(
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
                
                updated_dispute = self.api.get_dispute(dispute_id)
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
                dashboard_data = self.api.get_admin_dispute_dashboard()
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
                dispute_status = self.api.get_payment_dispute_display(payment_id)
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
                dispute_status = self.api.get_delinquency_dispute_display(tenant_id, year, month)
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
                summary = self.api.get_tenant_dispute_dashboard(tenant_id)
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
                data = request.get_json() or {}
                admin_notes = data.get('admin_notes', 'Upheld by admin')
                action = data.get('action', 'payment_corrected')
                
                result = self.api.uphold_dispute_admin(dispute_id, admin_notes, action)
                
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
                data = request.get_json() or {}
                admin_notes = data.get('admin_notes', 'Denied by admin')
                reason = data.get('reason', 'evidence_insufficient')
                
                result = self.api.deny_dispute_admin(dispute_id, admin_notes, reason)
                
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
                result = self.api.mark_dispute_for_review(dispute_id)
                
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
