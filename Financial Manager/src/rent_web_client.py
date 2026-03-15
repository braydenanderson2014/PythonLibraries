"""
Rent Management Web Client
Simple client library for interacting with the Rent Management Web Server
Use this for remote access to read-only rent data and dispute management
"""

import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class RentManagementClient:
    """Client for interacting with Rent Management Web Server"""
    
    def __init__(self, base_url: str = 'http://localhost:5000', timeout: int = 10):
        """
        Initialize client
        
        Args:
            base_url: Base URL of the Rent Management server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/json'}
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Tuple[bool, Any]:
        """
        Make HTTP request to server
        
        Returns:
            (success: bool, data: dict or error message)
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=self.timeout)
            else:
                return False, f"Unsupported method: {method}"
            
            # Check if request was successful
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    return False, error_data.get('message', f"HTTP {response.status_code}")
                except:
                    return False, f"HTTP {response.status_code}: {response.text}"
            
            try:
                return True, response.json()
            except:
                return True, response.text
        
        except requests.ConnectionError:
            return False, f"Connection error: Cannot connect to {self.base_url}"
        except requests.Timeout:
            return False, f"Request timeout after {self.timeout} seconds"
        except Exception as e:
            return False, str(e)
    
    # ========== HEALTH & STATUS ==========
    
    def health_check(self) -> bool:
        """Check if server is healthy"""
        success, data = self._make_request('GET', '/health')
        return success and data.get('status') == 'healthy'
    
    # ========== TENANT STATUS METHODS ==========
    
    def get_all_tenants(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get status for all tenants
        
        Returns:
            (success: bool, tenants: list)
        """
        success, response = self._make_request('GET', '/tenants')
        if success:
            return True, response.get('tenants', [])
        return False, [response]
    
    def get_tenant(self, tenant_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Get comprehensive status for a tenant
        
        Returns:
            (success: bool, tenant_data: dict or None)
        """
        success, response = self._make_request('GET', f'/tenants/{tenant_id}')
        if success:
            return True, response.get('data')
        return False, response
    
    def get_payment_summary(self, tenant_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Get payment summary for a tenant"""
        success, response = self._make_request('GET', f'/tenants/{tenant_id}/payment-summary')
        if success:
            return True, response.get('data')
        return False, response
    
    def get_delinquency_info(self, tenant_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Get delinquency information for a tenant"""
        success, response = self._make_request('GET', f'/tenants/{tenant_id}/delinquency')
        if success:
            return True, response.get('data')
        return False, response
    
    def get_monthly_breakdown(self, tenant_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get detailed monthly breakdown for a tenant"""
        success, response = self._make_request('GET', f'/tenants/{tenant_id}/monthly-breakdown')
        if success:
            return True, response.get('data', [])
        return False, [response]
    
    def export_tenant_data(self, tenant_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Export complete data snapshot for a tenant"""
        success, response = self._make_request('GET', f'/tenants/{tenant_id}/export')
        if success:
            return True, response.get('data')
        return False, response
    
    # ========== DISPUTE METHODS ==========
    
    def get_all_disputes(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get all disputes across all tenants"""
        success, response = self._make_request('GET', '/disputes')
        if success:
            return True, response.get('disputes', [])
        return False, [response]
    
    def get_dispute(self, dispute_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Get specific dispute details"""
        success, response = self._make_request('GET', f'/disputes/{dispute_id}')
        if success:
            return True, response.get('data')
        return False, response
    
    def get_tenant_disputes(self, tenant_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get all disputes for a specific tenant"""
        success, response = self._make_request('GET', f'/tenants/{tenant_id}/disputes')
        if success:
            return True, response.get('disputes', [])
        return False, [response]
    
    def create_dispute(
        self,
        tenant_id: str,
        dispute_type: str,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,
        evidence_notes: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Create a new dispute
        
        Args:
            tenant_id: Tenant ID filing the dispute
            dispute_type: Type of dispute (see get_dispute_types())
            description: Description of the dispute
            amount: Amount in dispute (optional)
            reference_month: (year, month) tuple (optional)
            evidence_notes: Supporting notes (optional)
        
        Returns:
            (success: bool, dispute: dict or error message)
        """
        data = {
            'dispute_type': dispute_type,
            'description': description
        }
        
        if amount is not None:
            data['amount'] = amount
        
        if reference_month:
            if isinstance(reference_month, (list, tuple)) and len(reference_month) == 2:
                data['reference_month'] = f"{reference_month[0]}-{reference_month[1]:02d}"
            else:
                data['reference_month'] = str(reference_month)
        
        if evidence_notes:
            data['evidence_notes'] = evidence_notes
        
        success, response = self._make_request('POST', f'/tenants/{tenant_id}/disputes', data=data)
        if success:
            return True, response.get('dispute')
        return False, response
    
    def update_dispute_status(
        self,
        dispute_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Update dispute status (admin operation)
        
        Args:
            dispute_id: Dispute ID to update
            status: New status (see get_dispute_statuses())
            admin_notes: Optional notes from admin
        
        Returns:
            (success: bool, updated_dispute: dict or error message)
        """
        data = {'status': status}
        if admin_notes:
            data['admin_notes'] = admin_notes
        
        success, response = self._make_request('PUT', f'/disputes/{dispute_id}/status', data=data)
        if success:
            return True, response.get('dispute')
        return False, response
    
    # ========== INFO METHODS ==========
    
    def get_dispute_types(self) -> Tuple[bool, List[Dict[str, str]]]:
        """Get available dispute types"""
        success, response = self._make_request('GET', '/info/dispute-types')
        if success:
            return True, response.get('types', [])
        return False, []
    
    def get_dispute_statuses(self) -> Tuple[bool, List[Dict[str, str]]]:
        """Get available dispute statuses"""
        success, response = self._make_request('GET', '/info/dispute-statuses')
        if success:
            return True, response.get('statuses', [])
        return False, []


def create_client(base_url: str = 'http://localhost:5000') -> RentManagementClient:
    """
    Factory function to create a client
    
    Args:
        base_url: Base URL of server
    
    Returns:
        RentManagementClient instance
    """
    return RentManagementClient(base_url)


# ========== EXAMPLE USAGE ==========

def example_usage():
    """Example of how to use the client"""
    
    # Create client
    client = create_client('http://localhost:5000')
    
    # Check server health
    if not client.health_check():
        print("Server is not responding!")
        return
    
    print("✓ Server is healthy\n")
    
    # Get all tenants
    print("=== ALL TENANTS ===")
    success, tenants = client.get_all_tenants()
    if success:
        for tenant in tenants:
            print(f"- {tenant['name']} (ID: {tenant['tenant_id']})")
            print(f"  Status: {tenant['account_status']}")
            print(f"  Rent: ${tenant['rent_amount']:.2f}")
    
    # Get specific tenant
    if tenants:
        tenant_id = tenants[0]['tenant_id']
        print(f"\n=== TENANT DETAILS: {tenant_id} ===")
        success, tenant = client.get_tenant(tenant_id)
        if success:
            print(f"Name: {tenant['name']}")
            print(f"Status: {tenant['account_status']}")
            print(f"Rent Amount: ${tenant['rent_amount']:.2f}")
            print(f"Delinquency Balance: ${tenant['payment_summary']['delinquency_balance']:.2f}")
            print(f"Overpayment Credit: ${tenant['payment_summary']['overpayment_credit']:.2f}")
        
        # Get monthly breakdown
        print(f"\n=== MONTHLY BREAKDOWN ===")
        success, breakdown = client.get_monthly_breakdown(tenant_id)
        if success:
            for month in breakdown[-3:]:  # Show last 3 months
                print(f"{month['month_key']}: Expected ${month['expected_rent']:.2f}, "
                      f"Paid ${month['paid_amount']:.2f}, Status: {month['status']}")
        
        # Get disputes
        print(f"\n=== DISPUTES ===")
        success, disputes = client.get_tenant_disputes(tenant_id)
        if success:
            if disputes:
                for dispute in disputes:
                    print(f"- {dispute['dispute_id']}: {dispute['type']} ({dispute['status']})")
                    print(f"  {dispute['description']}")
            else:
                print("No disputes found")
        
        # Create a dispute (example)
        print(f"\n=== CREATE DISPUTE ===")
        success, dispute = client.create_dispute(
            tenant_id=tenant_id,
            dispute_type='payment_not_recorded',
            description='Payment made on 2026-01-15 not showing in records',
            amount=1800.00,
            reference_month=(2026, 1),
            evidence_notes='Bank transfer receipt available'
        )
        if success:
            print(f"✓ Dispute created: {dispute['dispute_id']}")
            print(f"  Status: {dispute['status']}")


if __name__ == '__main__':
    print("Rent Management Web Client\n")
    example_usage()
