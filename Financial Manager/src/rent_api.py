"""
Rent Management API Layer
Provides a secondary data return system for the rent management system.
Maintains backward compatibility with existing UI while enabling remote data access.
Includes read-only status endpoints and dispute system.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from enum import Enum
import uuid


class DisputeStatus(Enum):
    """Dispute status enumeration"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


class DisputeType(Enum):
    """Types of disputes that can be filed"""
    PAYMENT_NOT_RECORDED = "payment_not_recorded"
    INCORRECT_BALANCE = "incorrect_balance"
    DUPLICATE_CHARGE = "duplicate_charge"
    OVERPAYMENT_NOT_CREDITED = "overpayment_not_credited"
    SERVICE_CREDIT_ERROR = "service_credit_error"
    OTHER = "other"


class Dispute:
    """Represents a payment/rent dispute"""
    
    def __init__(
        self,
        tenant_id: str,
        dispute_type: DisputeType,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,  # (year, month)
        created_by: Optional[str] = None,
        dispute_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        status: DisputeStatus = DisputeStatus.OPEN,
        admin_notes: Optional[str] = None,
        evidence_notes: Optional[str] = None
    ):
        self.dispute_id = dispute_id or str(uuid.uuid4())[:12]
        self.tenant_id = tenant_id
        self.dispute_type = dispute_type.value if isinstance(dispute_type, DisputeType) else dispute_type
        self.description = description
        self.amount = amount
        self.reference_month = reference_month  # (year, month) for date reference
        self.created_by = created_by or "tenant"
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.status = status.value if isinstance(status, DisputeStatus) else status
        self.admin_notes = admin_notes
        self.evidence_notes = evidence_notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dispute to dictionary"""
        return {
            'dispute_id': self.dispute_id,
            'tenant_id': self.tenant_id,
            'type': self.dispute_type,
            'description': self.description,
            'amount': self.amount,
            'reference_month': self.reference_month,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'admin_notes': admin_notes,
            'evidence_notes': self.evidence_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dispute':
        """Create dispute from dictionary"""
        return cls(
            tenant_id=data['tenant_id'],
            dispute_type=data.get('type', DisputeType.OTHER),
            description=data.get('description', ''),
            amount=data.get('amount'),
            reference_month=data.get('reference_month'),
            created_by=data.get('created_by'),
            dispute_id=data.get('dispute_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', DisputeStatus.OPEN),
            admin_notes=data.get('admin_notes'),
            evidence_notes=data.get('evidence_notes')
        )


class RentStatusAPI:
    """
    Read-only API for rent tracking data.
    Returns structured data compatible with web UI/remote access.
    Does not modify original rent_tracker behavior.
    """
    
    def __init__(self, rent_tracker):
        """
        Initialize API with rent tracker instance
        
        Args:
            rent_tracker: RentTracker instance from Financial Manager
        """
        self.rent_tracker = rent_tracker
        # Disputes are now managed by RentTracker's DisputeManager
        # We keep this for backward compatibility but it will use rent_tracker's disputes
        self.disputes: Dict[str, List[Dispute]] = {}
    
    # ========== TENANT STATUS ENDPOINTS ==========
    
    def get_tenant_status(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive read-only status for a tenant
        
        Returns:
            {
                'tenant_id': str,
                'name': str,
                'property': str,
                'contact_info': dict,
                'status': str (active/inactive/expired),
                'rental_period': dict,
                'rent_amount': float,
                'deposit_amount': float,
                'account_status': str,
                'payment_summary': {...},
                'delinquency_info': {...},
                'monthly_status': {...},
                'disputes': [...]
            }
        """
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return None
            
            return {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'contact_info': tenant.contact_info or {},
                'account_status': tenant.account_status,
                'rental_period': self._format_rental_period(tenant.rental_period),
                'rent_amount': tenant.rent_amount,
                'deposit_amount': tenant.deposit_amount,
                'rent_due_date': tenant.rent_due_date,
                'notes': tenant.notes,
                'payment_summary': self.get_payment_summary(tenant_id),
                'delinquency_info': self.get_delinquency_info(tenant_id),
                'monthly_status': self._format_monthly_status(tenant.monthly_status),
                'overpayment_credit': tenant.overpayment_credit,
                'service_credit': tenant.service_credit,
                'disputes': self.get_tenant_disputes(tenant_id),
                'last_modified': tenant.last_modified
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_all_tenants_status(self) -> List[Dict[str, Any]]:
        """Get status for all tenants"""
        statuses = []
        try:
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            for tenant in tenants:
                status = self.get_tenant_status(tenant.tenant_id)
                if status:
                    statuses.append(status)
        except Exception as e:
            return [{'error': str(e)}]
        
        return statuses
    
    def get_payment_summary(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get payment summary for a tenant
        
        Returns:
            {
                'total_rent_paid': float,
                'delinquency_balance': float,
                'overpayment_credit': float,
                'service_credit': float,
                'payment_count': int,
                'last_payment_date': str,
                'last_payment_amount': float
            }
        """
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return None
            
            last_payment = None
            if tenant.payment_history:
                last_payment = sorted(
                    tenant.payment_history,
                    key=lambda p: f"{p.get('year', 0)}-{p.get('month', 0):02d}",
                    reverse=True
                )[0]
            
            return {
                'total_rent_paid': tenant.total_rent_paid,
                'delinquency_balance': tenant.delinquency_balance,
                'overpayment_credit': tenant.overpayment_credit,
                'service_credit': tenant.service_credit,
                'payment_count': len(tenant.payment_history or []),
                'last_payment_date': last_payment.get('payment_date') if last_payment else None,
                'last_payment_amount': last_payment.get('amount') if last_payment else None,
                'delinquent_months': self._format_delinquent_months(tenant.delinquent_months)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_delinquency_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed delinquency information"""
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return None
            
            delinquent_details = []
            for year, month in tenant.delinquent_months:
                expected_rent = self.rent_tracker.get_effective_rent(tenant, year, month)
                delinquent_details.append({
                    'year': year,
                    'month': month,
                    'expected_rent': expected_rent,
                    'status': tenant.monthly_status.get(f"{year}-{month:02d}", "Unknown")
                })
            
            return {
                'is_delinquent': tenant.delinquency_balance > 0,
                'total_delinquency': tenant.delinquency_balance,
                'delinquent_month_count': len(tenant.delinquent_months),
                'delinquent_months_detail': delinquent_details,
                'requires_attention': len(delinquent_details) > 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_monthly_breakdown(self, tenant_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get detailed monthly breakdown for tenant
        
        Returns list of months with:
        {
            'year': int,
            'month': int,
            'month_key': str,
            'expected_rent': float,
            'paid_amount': float,
            'status': str,
            'payment_date': str (if paid)
        }
        """
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return None
            
            breakdown = []
            
            for year, month in tenant.months_to_charge:
                month_key = f"{year}-{month:02d}"
                expected_rent = self.rent_tracker.get_effective_rent(tenant, year, month)
                
                # Calculate paid amount for this month
                paid_amount = 0.0
                payment_date = None
                if tenant.payment_history:
                    for payment in tenant.payment_history:
                        if payment.get('year') == year and payment.get('month') == month:
                            if not payment.get('is_credit_usage', False):
                                paid_amount += payment.get('amount', 0)
                                if not payment_date:
                                    payment_date = payment.get('payment_date')
                
                breakdown.append({
                    'year': year,
                    'month': month,
                    'month_key': month_key,
                    'expected_rent': expected_rent,
                    'paid_amount': paid_amount,
                    'balance': expected_rent - paid_amount,
                    'status': tenant.monthly_status.get(month_key, 'Pending'),
                    'payment_date': payment_date
                })
            
            return breakdown
        except Exception as e:
            return [{'error': str(e)}]
    
    # ========== DISPUTE ENDPOINTS ==========
    
    def create_dispute(
        self,
        tenant_id: str,
        dispute_type: str,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,
        evidence_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new dispute (web UI tenant can file dispute)
        
        Args:
            tenant_id: Tenant filing the dispute
            dispute_type: DisputeType enum value as string
            description: Description of the dispute
            amount: Amount in dispute
            reference_month: (year, month) tuple
            evidence_notes: Any supporting evidence notes
        
        Returns:
            Dispute dictionary or None if failed
        """
        try:
            # Use rent_tracker's dispute manager
            if hasattr(self.rent_tracker, 'create_dispute'):
                return self.rent_tracker.create_dispute(
                    tenant_id=tenant_id,
                    dispute_type=dispute_type,
                    description=description,
                    amount=amount,
                    reference_month=reference_month,
                    evidence_notes=evidence_notes
                )
            else:
                raise Exception("RentTracker does not have dispute management")
        except Exception as e:
            raise Exception(f"Failed to create dispute: {e}")
    
    def get_tenant_disputes(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all disputes for a tenant"""
        try:
            if hasattr(self.rent_tracker, 'get_tenant_disputes'):
                return self.rent_tracker.get_tenant_disputes(tenant_id)
            else:
                # Fallback to internal disputes
                if tenant_id not in self.disputes:
                    return []
                return [d.to_dict() for d in self.disputes[tenant_id]]
        except Exception:
            return []
    
    def get_dispute(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Get specific dispute by ID"""
        try:
            if hasattr(self.rent_tracker, 'get_dispute'):
                return self.rent_tracker.get_dispute(dispute_id)
            else:
                # Fallback to internal disputes
                for tenant_id, disputes in self.disputes.items():
                    for dispute in disputes:
                        if dispute.dispute_id == dispute_id:
                            return dispute.to_dict()
                return None
        except Exception:
            return None
    
    def update_dispute_status(
        self,
        dispute_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update dispute status (admin endpoint)"""
        try:
            if hasattr(self.rent_tracker, 'update_dispute_status'):
                return self.rent_tracker.update_dispute_status(
                    dispute_id,
                    status,
                    admin_notes
                )
            else:
                # Fallback to internal disputes
                for tenant_id, disputes in self.disputes.items():
                    for dispute in disputes:
                        if dispute.dispute_id == dispute_id:
                            dispute.status = status
                            dispute.updated_at = datetime.now().isoformat()
                            if admin_notes:
                                dispute.admin_notes = admin_notes
                            return True
                return False
        except Exception:
            return False
    
    def get_all_disputes(self) -> List[Dict[str, Any]]:
        """Get all disputes across all tenants"""
        try:
            if hasattr(self.rent_tracker, 'get_all_disputes'):
                return self.rent_tracker.get_all_disputes()
            else:
                # Fallback to internal disputes
                all_disputes = []
                for tenant_id, disputes in self.disputes.items():
                    all_disputes.extend([d.to_dict() for d in disputes])
                return all_disputes
        except Exception:
            return []
    
    # ========== HELPER METHODS ==========
    
    def _format_rental_period(self, rental_period) -> Dict[str, str]:
        """Format rental period for API response"""
        if not rental_period:
            return {}
        
        try:
            if isinstance(rental_period, dict):
                return {
                    'start_date': str(rental_period.get('start_date', '')),
                    'end_date': str(rental_period.get('end_date', ''))
                }
            elif isinstance(rental_period, tuple) and len(rental_period) == 2:
                return {
                    'start_date': str(rental_period[0]),
                    'end_date': str(rental_period[1])
                }
        except:
            pass
        
        return {}
    
    def _format_monthly_status(self, monthly_status: Dict) -> Dict[str, str]:
        """Format monthly status for API response"""
        if not monthly_status:
            return {}
        
        formatted = {}
        for key, value in monthly_status.items():
            if isinstance(key, tuple):
                key = f"{key[0]}-{key[1]:02d}"
            
            if isinstance(value, dict):
                formatted[key] = value.get('status', str(value))
            else:
                formatted[key] = str(value)
        
        return formatted
    
    def _format_delinquent_months(self, delinquent_months: List) -> List[str]:
        """Format delinquent months for API response"""
        formatted = []
        for item in delinquent_months:
            if isinstance(item, tuple) and len(item) == 2:
                formatted.append(f"{item[0]}-{item[1]:02d}")
            else:
                formatted.append(str(item))
        
        return formatted
    
    def export_tenant_data(self, tenant_id: str) -> Dict[str, Any]:
        """
        Export all tenant data in a structured format for external use
        
        Returns complete read-only snapshot of tenant data
        """
        status = self.get_tenant_status(tenant_id)
        if not status:
            return {'error': 'Tenant not found'}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'tenant_status': status,
            'payment_summary': self.get_payment_summary(tenant_id),
            'monthly_breakdown': self.get_monthly_breakdown(tenant_id),
            'delinquency_info': self.get_delinquency_info(tenant_id),
            'disputes': self.get_tenant_disputes(tenant_id)
        }
    
    # ========== DISPUTE DISPLAY API METHODS ==========
    
    def get_payment_dispute_display(self, payment_id: str) -> Dict[str, Any]:
        """
        Get dispute display info for a payment (for UI)
        Shows if payment is disputed and why
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized'}
        
        return self.rent_tracker.get_payment_dispute_status(payment_id)
    
    def get_delinquency_dispute_display(self, tenant_id: str, year: int, month: int) -> Dict[str, Any]:
        """
        Get dispute display info for a delinquent month (for UI)
        Shows if delinquency is disputed
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized'}
        
        return self.rent_tracker.get_delinquency_dispute_status(tenant_id, year, month)
    
    def get_admin_dispute_dashboard(self) -> Dict[str, Any]:
        """
        Get all disputes awaiting admin review
        Used for admin dashboard to see what needs attention
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized', 'disputes': []}
        
        try:
            disputes = self.rent_tracker.get_disputes_awaiting_admin_review()
            
            # Group by status
            by_status = {}
            for dispute in disputes:
                status = dispute.get('status', 'unknown')
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(dispute)
            
            # Calculate totals
            return {
                'total_disputes': len(disputes),
                'disputes_by_status': by_status,
                'pending_review_count': len([d for d in disputes if d.get('status') == 'pending_review']),
                'open_count': len([d for d in disputes if d.get('status') == 'open']),
                'all_disputes': disputes,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'disputes': []}
    
    def get_tenant_dispute_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get dispute summary for a specific tenant (for tenant details view)
        Shows tenant's disputed payments and delinquent months
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized'}
        
        summary = self.rent_tracker.get_tenant_dispute_summary(tenant_id)
        
        # Enhance with tenant info
        status = self.get_tenant_status(tenant_id)
        
        return {
            'tenant_id': tenant_id,
            'tenant_name': status.get('tenant_name', 'Unknown') if status else 'Unknown',
            'dispute_summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    # ========== DISPUTE ADMIN ACTION API METHODS ==========
    
    def uphold_dispute_admin(self, dispute_id: str, admin_notes: str, action: str = "payment_corrected") -> Dict[str, Any]:
        """
        Admin upholds a dispute
        action: 'payment_corrected', 'balance_adjusted', 'delinquency_removed', etc.
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized', 'success': False}
        
        try:
            success = self.rent_tracker.uphold_dispute(dispute_id, admin_notes, action)
            return {
                'success': success,
                'dispute_id': dispute_id,
                'action': 'upheld',
                'admin_action': action,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'dispute_id': dispute_id}
    
    def deny_dispute_admin(self, dispute_id: str, admin_notes: str, reason: str = "evidence_insufficient") -> Dict[str, Any]:
        """
        Admin denies/rejects a dispute
        reason: 'evidence_insufficient', 'already_resolved', 'invalid_claim', etc.
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized', 'success': False}
        
        try:
            success = self.rent_tracker.deny_dispute(dispute_id, admin_notes, reason)
            return {
                'success': success,
                'dispute_id': dispute_id,
                'action': 'denied',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'dispute_id': dispute_id}
    
    def mark_dispute_for_review(self, dispute_id: str) -> Dict[str, Any]:
        """
        Admin marks a dispute as pending review
        """
        if not self.rent_tracker:
            return {'error': 'Rent tracker not initialized', 'success': False}
        
        try:
            success = self.rent_tracker.acknowledge_and_review_dispute(dispute_id)
            return {
                'success': success,
                'dispute_id': dispute_id,
                'status': 'pending_review',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'dispute_id': dispute_id}
