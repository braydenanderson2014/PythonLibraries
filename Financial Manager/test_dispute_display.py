#!/usr/bin/env python3
"""
Test script for dispute display and admin functionality
Tests the new methods for showing disputed items in RentTracker UI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ui'))

from assets.Logger import Logger
from src.rent_tracker import RentTracker
from src.rent_api import RentStatusAPI
from src.database import DatabaseManager

logger = Logger()

def test_dispute_display():
    """Test dispute display functionality"""
    print("\n" + "="*60)
    print("TESTING DISPUTE DISPLAY FUNCTIONALITY")
    print("="*60 + "\n")
    
    try:
        # Initialize rent tracker with a test user
        rent_tracker = RentTracker(current_user_id="test_user")
        api = RentStatusAPI(rent_tracker)
        
        print("1. RentTracker initialized")
        print("   ✓ Database and dispute manager ready\n")

        print("2. Adding test tenant...")
        rent_tracker.add_tenant("TST_DISP_001", "John Dispute", 1500.00)
        rent_tracker.add_payment("TST_DISP_001", 1500.00, "2025-01-15", "payment_1", "received")
        print("   ✓ Tenant and payment added\n")
        
        # Create a dispute for the payment
        print("3. Creating dispute for payment...")
        dispute_id = rent_tracker.create_dispute(
            tenant_id="TST_DISP_001",
            dispute_type="payment_not_recorded",
            description="Payment was made but not recorded in system",
            amount=1500.00,
            reference_payment_id="payment_1",
            evidence_notes="Receipt attached"
        )
        print(f"   ✓ Dispute created: {dispute_id}\n")
        
        # Test payment dispute status
        print("4. Testing get_payment_dispute_status()...")
        payment_status = rent_tracker.get_payment_dispute_status("payment_1")
        print(f"   Payment Dispute Status: {payment_status}")
        assert payment_status['is_disputed'], "Payment should be disputed"
        assert payment_status['dispute_count'] == 1, "Should have 1 dispute"
        print("   ✓ Payment dispute status correct\n")
        
        # Test API payment dispute display
        print("5. Testing API get_payment_dispute_display()...")
        api_status = api.get_payment_dispute_display("payment_1")
        print(f"   API Payment Status: {api_status}")
        assert api_status['is_disputed'], "API: Payment should be disputed"
        print("   ✓ API payment dispute display working\n")
        
        # Test tenant dispute summary
        print("6. Testing get_tenant_dispute_summary()...")
        summary = rent_tracker.get_tenant_dispute_summary("TST_DISP_001")
        print(f"   Dispute Summary:")
        print(f"   - Total Disputes: {summary['total_disputes']}")
        print(f"   - Open Disputes: {summary['open_disputes']}")
        print(f"   - Disputed Payments: {summary['disputed_payments']}")
        print(f"   - Awaiting Review: {summary['awaiting_review']}")
        assert summary['total_disputes'] == 1, "Should have 1 total dispute"
        print("   ✓ Tenant dispute summary working\n")
        
        # Test API tenant dispute dashboard
        print("7. Testing API get_tenant_dispute_dashboard()...")
        dashboard = api.get_tenant_dispute_dashboard("TST_DISP_001")
        print(f"   Dashboard Tenant: {dashboard['tenant_name']}")
        print(f"   Dashboard Disputes: {dashboard['dispute_summary']['total_disputes']}")
        assert dashboard['dispute_summary']['total_disputes'] == 1, "Dashboard should show 1 dispute"
        print("   ✓ API tenant dispute dashboard working\n")
        
        # Test get_disputes_awaiting_admin_review
        print("8. Testing get_disputes_awaiting_admin_review()...")
        awaiting = rent_tracker.get_disputes_awaiting_admin_review()
        print(f"   Disputes Awaiting Review: {len(awaiting)}")
        print(f"   Dispute ID: {awaiting[0].get('dispute_id')}")
        assert len(awaiting) >= 1, "Should have at least 1 dispute awaiting review"
        print("   ✓ Disputes awaiting review working\n")
        
        # Test API admin dashboard
        print("9. Testing API get_admin_dispute_dashboard()...")
        admin_dash = api.get_admin_dispute_dashboard()
        print(f"   Total Disputes: {admin_dash['total_disputes']}")
        print(f"   Pending Review: {admin_dash['pending_review_count']}")
        print(f"   Open Count: {admin_dash['open_count']}")
        assert admin_dash['total_disputes'] >= 1, "Dashboard should show disputes"
        print("   ✓ API admin dashboard working\n")
        
        # Test uphold_dispute
        print("10. Testing uphold_dispute()...")
        uphold_result = rent_tracker.uphold_dispute(
            dispute_id=dispute_id,
            admin_notes="Payment verified and recorded",
            action="payment_corrected"
        )
        print(f"   Uphold Result: {uphold_result}")
        assert uphold_result, "Uphold should succeed"
        
        # Check status after uphold
        dispute = rent_tracker.get_dispute(dispute_id)
        print(f"   Dispute Status After Uphold: {dispute.get('status')}")
        assert dispute.get('status') == 'resolved', "Dispute should be resolved"
        print("   ✓ Uphold dispute working\n")
        
        # Create another dispute for deny test
        print("11. Creating second dispute for deny test...")
        dispute_id_2 = rent_tracker.create_dispute(
            tenant_id="TST_DISP_001",
            dispute_type="incorrect_balance",
            description="Balance calculation is wrong",
            amount=500.00
        )
        print(f"    ✓ Second dispute created: {dispute_id_2}\n")
        
        # Test deny_dispute
        print("12. Testing deny_dispute()...")
        deny_result = rent_tracker.deny_dispute(
            dispute_id=dispute_id_2,
            admin_notes="Balance verified as correct",
            reason="evidence_insufficient"
        )
        print(f"    Deny Result: {deny_result}")
        assert deny_result, "Deny should succeed"
        
        # Check status after deny
        dispute2 = rent_tracker.get_dispute(dispute_id_2)
        print(f"    Dispute Status After Deny: {dispute2.get('status')}")
        assert dispute2.get('status') == 'rejected', "Dispute should be rejected"
        print("    ✓ Deny dispute working\n")
        
        # Test delinquency dispute
        print("13. Testing delinquency dispute...")
        # Mark a month as delinquent
        rent_tracker.mark_month_delinquent("TST_DISP_001", 2025, 2)
        
        # Create dispute for the delinquency
        dispute_id_3 = rent_tracker.create_dispute(
            tenant_id="TST_DISP_001",
            dispute_type="payment_not_recorded",
            description="Payment was made for Feb but marked as delinquent",
            reference_month=(2025, 2),
            amount=1500.00
        )
        print(f"    ✓ Delinquency dispute created: {dispute_id_3}\n")
        
        # Test get_delinquency_dispute_status
        print("14. Testing get_delinquency_dispute_status()...")
        delin_status = rent_tracker.get_delinquency_dispute_status("TST_DISP_001", 2025, 2)
        print(f"    Delinquency Dispute Status: {delin_status}")
        assert delin_status['is_disputed'], "Delinquency should be disputed"
        print("    ✓ Delinquency dispute status working\n")
        
        # Test API delinquency dispute
        print("15. Testing API get_delinquency_dispute_display()...")
        api_delin = api.get_delinquency_dispute_display("TST_DISP_001", 2025, 2)
        print(f"    API Delinquency Status: {api_delin}")
        assert api_delin['is_disputed'], "API should show delinquency disputed"
        print("    ✓ API delinquency dispute display working\n")
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nDispute display functionality is working correctly:")
        print("  ✓ Payment dispute status display")
        print("  ✓ Delinquency dispute status display")
        print("  ✓ Tenant dispute summary")
        print("  ✓ Admin dispute dashboard")
        print("  ✓ Uphold dispute action")
        print("  ✓ Deny dispute action")
        print("  ✓ API endpoints for all above")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_dispute_display()
    sys.exit(0 if success else 1)
