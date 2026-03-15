"""
Dispute Management System for Rent Tracker
Handles creation, tracking, and resolution of payment/rent disputes
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
import uuid
import json
import os
from assets.Logger import Logger

logger = Logger()


class DisputeStatus(Enum):
    """Dispute status enumeration"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


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
        dispute_type: str,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,
        created_by: Optional[str] = None,
        dispute_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        status: str = "open",
        admin_notes: Optional[str] = None,
        evidence_notes: Optional[str] = None
    ):
        self.dispute_id = dispute_id or f"DSP{str(uuid.uuid4())[:8].upper()}"
        self.tenant_id = tenant_id
        self.dispute_type = dispute_type
        self.description = description
        self.amount = amount
        self.reference_month = reference_month  # (year, month) tuple
        self.created_by = created_by or "tenant"
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.status = status
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
            'admin_notes': self.admin_notes,
            'evidence_notes': self.evidence_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dispute':
        """Create dispute from dictionary"""
        return cls(
            tenant_id=data['tenant_id'],
            dispute_type=data.get('type', 'other'),
            description=data.get('description', ''),
            amount=data.get('amount'),
            reference_month=data.get('reference_month'),
            created_by=data.get('created_by'),
            dispute_id=data.get('dispute_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'open'),
            admin_notes=data.get('admin_notes'),
            evidence_notes=data.get('evidence_notes')
        )


class DisputeManager:
    """Manages disputes for all tenants"""
    
    def __init__(self, data_dir: Optional[str] = None, db_manager=None):
        """
        Initialize dispute manager
        
        Args:
            data_dir: Directory to store dispute data (default: resources/)
            db_manager: DatabaseManager instance for database persistence
        """
        if data_dir is None:
            # Try to get from resources
            try:
                from AppPaths import AppPaths
                data_dir = AppPaths.get_resource_path('disputes.json')
                data_dir = os.path.dirname(data_dir)
            except:
                data_dir = os.path.join(os.path.dirname(__file__), '..', 'resources')
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.disputes_file = os.path.join(data_dir, 'disputes.json')
        self.disputes: Dict[str, List[Dispute]] = {}  # tenant_id -> disputes
        self.db = db_manager  # Optional database manager for persistence
        
        self._load_disputes()
        logger.info("DisputeManager", f"Dispute manager initialized with {len(self.disputes)} tenant(s)")
    
    def _load_disputes(self):
        """Load disputes from JSON file"""
        try:
            if os.path.exists(self.disputes_file):
                with open(self.disputes_file, 'r') as f:
                    data = json.load(f)
                    
                    for tenant_id, disputes_data in data.items():
                        self.disputes[tenant_id] = [
                            Dispute.from_dict(d) for d in disputes_data
                        ]
                
                logger.debug("DisputeManager", f"Loaded {sum(len(d) for d in self.disputes.values())} disputes")
            else:
                logger.debug("DisputeManager", "No disputes file found, starting fresh")
                self.disputes = {}
        except Exception as e:
            logger.error("DisputeManager", f"Failed to load disputes: {e}")
            self.disputes = {}
    
    def _save_disputes(self):
        """Save disputes to JSON file"""
        try:
            data = {
                tenant_id: [d.to_dict() for d in disputes]
                for tenant_id, disputes in self.disputes.items()
            }
            
            with open(self.disputes_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("DisputeManager", "Disputes saved successfully")
        except Exception as e:
            logger.error("DisputeManager", f"Failed to save disputes: {e}")
    
    def create_dispute(
        self,
        tenant_id: str,
        dispute_type: str,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,
        evidence_notes: Optional[str] = None,
        created_by: str = "tenant_web_ui",
        reference_payment_id: Optional[str] = None
    ) -> Dispute:
        """
        Create a new dispute
        
        Args:
            tenant_id: Tenant filing the dispute
            dispute_type: Type of dispute
            description: Description of the dispute
            amount: Amount in dispute
            reference_month: Reference month (year, month) tuple
            evidence_notes: Supporting evidence
            created_by: Who created the dispute
            reference_payment_id: ID of payment being disputed (optional)
        
        Returns:
            Created Dispute object
        """
        try:
            dispute = Dispute(
                tenant_id=tenant_id,
                dispute_type=dispute_type,
                description=description,
                amount=amount,
                reference_month=reference_month,
                created_by=created_by,
                evidence_notes=evidence_notes,
                status="open"
            )
            
            if tenant_id not in self.disputes:
                self.disputes[tenant_id] = []
            
            self.disputes[tenant_id].append(dispute)
            self._save_disputes()
            
            # Also save to database if available
            if self.db:
                try:
                    self.db.add_dispute(
                        dispute.dispute_id,
                        tenant_id,
                        dispute_type=dispute_type,
                        description=description,
                        amount=amount,
                        reference_month=reference_month,
                        evidence_notes=evidence_notes,
                        created_by=created_by,
                        reference_payment_id=reference_payment_id,
                        status="open"
                    )
                    logger.debug("DisputeManager", f"Dispute {dispute.dispute_id} synced to database")
                except Exception as e:
                    logger.warning("DisputeManager", f"Failed to sync dispute to database: {e}")
            
            logger.info("DisputeManager", f"Created dispute {dispute.dispute_id} for tenant {tenant_id}")
            return dispute
        except Exception as e:
            logger.error("DisputeManager", f"Failed to create dispute: {e}")
            raise
    
    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get a specific dispute by ID"""
        for tenant_id, disputes in self.disputes.items():
            for dispute in disputes:
                if dispute.dispute_id == dispute_id:
                    return dispute
        
        return None
    
    def get_tenant_disputes(self, tenant_id: str) -> List[Dispute]:
        """Get all disputes for a tenant"""
        return self.disputes.get(tenant_id, [])
    
    def get_all_disputes(self) -> List[Dispute]:
        """Get all disputes across all tenants"""
        all_disputes = []
        for disputes in self.disputes.values():
            all_disputes.extend(disputes)
        return all_disputes
    
    def update_dispute_status(
        self,
        dispute_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> bool:
        """
        Update dispute status
        
        Args:
            dispute_id: ID of dispute to update
            status: New status
            admin_notes: Admin notes
        
        Returns:
            True if updated, False if not found
        """
        dispute = self.get_dispute(dispute_id)
        if dispute:
            dispute.status = status
            dispute.updated_at = datetime.now().isoformat()
            if admin_notes:
                dispute.admin_notes = admin_notes
            
            self._save_disputes()
            
            # Also update in database if available
            if self.db:
                try:
                    self.db.update_dispute(
                        dispute_id,
                        status=status,
                        admin_notes=admin_notes
                    )
                    logger.debug("DisputeManager", f"Dispute {dispute_id} status updated in database")
                except Exception as e:
                    logger.warning("DisputeManager", f"Failed to update dispute status in database: {e}")
            
            logger.info("DisputeManager", f"Updated dispute {dispute_id} status to {status}")
            return True
        
        return False
    
    def get_dispute_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about disputes"""
        if tenant_id:
            disputes = self.get_tenant_disputes(tenant_id)
        else:
            disputes = self.get_all_disputes()
        
        stats = {
            'total': len(disputes),
            'by_status': {},
            'by_type': {},
            'total_amount': 0.0
        }
        
        for dispute in disputes:
            # Count by status
            status = dispute.status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Count by type
            d_type = dispute.dispute_type
            stats['by_type'][d_type] = stats['by_type'].get(d_type, 0) + 1
            
            # Sum amounts
            if dispute.amount:
                stats['total_amount'] += dispute.amount
        
        return stats
    
    def resolve_dispute(
        self,
        dispute_id: str,
        admin_notes: str
    ) -> bool:
        """Mark a dispute as resolved"""
        return self.update_dispute_status(
            dispute_id,
            "resolved",
            admin_notes
        )
    
    def reject_dispute(
        self,
        dispute_id: str,
        admin_notes: str
    ) -> bool:
        """Mark a dispute as rejected"""
        return self.update_dispute_status(
            dispute_id,
            "rejected",
            admin_notes
        )
    
    def acknowledge_dispute(self, dispute_id: str) -> bool:
        """Mark a dispute as acknowledged"""
        return self.update_dispute_status(
            dispute_id,
            "acknowledged"
        )
