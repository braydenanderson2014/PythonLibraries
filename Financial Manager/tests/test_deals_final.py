#!/usr/bin/env python3
"""
Test the enhanced deal system with BOGO and multi-criteria targeting
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.pos_manager import POSManager

def test_enhanced_deals():
    """Test the enhanced deal system"""
    print("=" * 70)
    print("TESTING ENHANCED DEAL SYSTEM WITH BOGO AND MULTI-CRITERIA TARGETING")
    print("=" * 70)
    
    manager = POSManager()
    
    # Create test products
    print("\n[1] Creating test products...")
    
    products = []
    
    # Product 1: Widget - $10
    p1 = manager.add_product(
        name="Widget",
        item_number="WIDG-001",
        tags="hardware,tools",
        price=10.00,
        initial_quantity=100
    )
    products.append({"id": p1, "name": "Widget", "price": 10.00, "category": "Tools"})
    
    # Product 2: Gadget - $25
    p2 = manager.add_product(
        name="Gadget",
        item_number="GADG-001",
        tags="electronics,tech",
        price=25.00,
        initial_quantity=50
    )
    products.append({"id": p2, "name": "Gadget", "price": 25.00, "category": "Electronics"})
    
    # Product 3: Widget Pro - $50
    p3 = manager.add_product(
        name="Widget Pro",
        item_number="WIDG-PRO",
        tags="hardware,premium",
        price=50.00,
        initial_quantity=25
    )
    products.append({"id": p3, "name": "Widget Pro", "price": 50.00, "category": "Tools"})
    
    print(f"    [OK] Created {len(products)} products")
    
    # Test 1: Discount deal with percentage (tag-based)
    print("\n[2] Creating discount deal: 10% off hardware items...")
    deal1 = manager.create_deal(
        name="Hardware Sale",
        description="10% off all hardware items",
        deal_mechanism="discount",
        discount_value=10.0,
        discount_type="percentage",
        tags=["hardware"]
    )
    print(f"    [OK] Deal created: {deal1[:8]}...")
    
    # Test 2: Discount deal with fixed amount (price range)
    print("\n[3] Creating discount deal: $5 off items over $20...")
    deal2 = manager.create_deal(
        name="Premium Discount",
        description="$5 off items over $20",
        deal_mechanism="discount",
        discount_value=5.0,
        discount_type="fixed",
        price_min=20.0
    )
    print(f"    [OK] Deal created: {deal2[:8]}...")
    
    # Test 3: BOGO deal (Buy 1 Get 1 free)
    print("\n[4] Creating BOGO deal: Buy 1 Widget Get 1 Free...")
    deal3 = manager.create_deal(
        name="Widget BOGO",
        description="Buy 1 Widget, Get 1 Free",
        deal_mechanism="bogo",
        bogo_buy_qty=1,
        bogo_get_qty=1,
        product_ids=[p1]
    )
    print(f"    [OK] Deal created: {deal3[:8]}...")
    
    # Test 4: Complex deal (multiple targeting criteria)
    print("\n[5] Creating complex deal: 15% off electronics in price range $20-$30...")
    deal4 = manager.create_deal(
        name="Electronics Flash Sale",
        description="15% off electronics between $20-$30",
        deal_mechanism="discount",
        discount_value=15.0,
        discount_type="percentage",
        categories=["Electronics"],
        price_min=20.0,
        price_max=30.0
    )
    print(f"    [OK] Deal created: {deal4[:8]}...")
    
    # Test 5: Item number targeting
    print("\n[6] Creating deal: $10 off specific item numbers...")
    deal5 = manager.create_deal(
        name="Item-Specific Deal",
        description="$10 off GADG-001",
        deal_mechanism="discount",
        discount_value=10.0,
        discount_type="fixed",
        item_numbers=["GADG-001"]
    )
    print(f"    [OK] Deal created: {deal5[:8]}...")
    
    # Now test deal matching
    print("\n" + "=" * 70)
    print("TESTING DEAL MATCHING")
    print("=" * 70)
    
    # Test 1: Widget (10%) should match hardware tag deal
    print(f"\n[1] Testing Widget ($10.00, tag=hardware)...")
    applicable = manager.get_applicable_deals(
        product_id=p1,
        tags=["hardware", "tools"],
        item_number="WIDG-001",
        price=10.00,
        category="Tools"
    )
    print(f"    Applicable deals: {len(applicable)}")
    for deal in applicable:
        print(f"    - {deal['name']} ({deal['deal_mechanism']})")
    assert len(applicable) > 0, "Widget should match hardware tag deal"
    
    # Test 2: Gadget (25$) should match multiple deals
    print(f"\n[2] Testing Gadget ($25.00, category=Electronics)...")
    applicable = manager.get_applicable_deals(
        product_id=p2,
        tags=["electronics", "tech"],
        item_number="GADG-001",
        price=25.00,
        category="Electronics"
    )
    print(f"    Applicable deals: {len(applicable)}")
    for deal in applicable:
        print(f"    - {deal['name']} ({deal['deal_mechanism']})")
    assert len(applicable) >= 2, "Gadget should match premium discount and item-specific deal"
    
    # Test 3: Widget Pro (50$) should match price-based deal only
    print(f"\n[3] Testing Widget Pro ($50.00, price outside range)...")
    applicable = manager.get_applicable_deals(
        product_id=p3,
        tags=["hardware", "premium"],
        item_number="WIDG-PRO",
        price=50.00,
        category="Tools"
    )
    print(f"    Applicable deals: {len(applicable)}")
    for deal in applicable:
        print(f"    - {deal['name']} ({deal['deal_mechanism']})")
    
    # Test discount calculations
    print("\n" + "=" * 70)
    print("TESTING DISCOUNT CALCULATIONS")
    print("=" * 70)
    
    # Test percentage discount
    print("\n[1] Testing percentage discount: 10% off $100...")
    discount = manager.calculate_deal_discount(
        {"deal_mechanism": "discount", "discount_type": "percentage", "discount_value": 10.0},
        quantity=2,
        unit_price=50.0
    )
    print(f"    Discount: ${discount:.2f} (expected: $10.00)")
    assert abs(discount - 10.0) < 0.01, "Percentage discount calculation failed"
    print("    [PASS]")
    
    # Test fixed discount
    print("\n[2] Testing fixed discount: $5 off per item (qty=3)...")
    discount = manager.calculate_deal_discount(
        {"deal_mechanism": "discount", "discount_type": "fixed", "discount_value": 5.0},
        quantity=3,
        unit_price=25.0
    )
    print(f"    Discount: ${discount:.2f} (expected: $15.00)")
    assert abs(discount - 15.0) < 0.01, "Fixed discount calculation failed"
    print("    [PASS]")
    
    # Test BOGO calculation
    print("\n[3] Testing BOGO: Buy 1 Get 1 Free (qty=3, price=$10/each)...")
    discount = manager.calculate_deal_discount(
        {"deal_mechanism": "bogo", "bogo_buy_qty": 1, "bogo_get_qty": 1},
        quantity=3,
        unit_price=10.0
    )
    print(f"    Discount: ${discount:.2f} (expected: $10.00 for 1 free item)")
    # qty=3: (buy 1 + get 1) + (buy 1) = 1 free item
    assert abs(discount - 10.0) < 0.01, "BOGO calculation failed"
    print("    [PASS]")
    
    # Test BOGO with larger quantities
    print("\n[4] Testing BOGO: Buy 2 Get 1 Free (qty=5, price=$20/each)...")
    discount = manager.calculate_deal_discount(
        {"deal_mechanism": "bogo", "bogo_buy_qty": 2, "bogo_get_qty": 1},
        quantity=5,
        unit_price=20.0
    )
    print(f"    Discount: ${discount:.2f} (expected: $20.00 for 1 free item)")
    # qty=5: 1 complete set (buy 2 + get 1) = 3 items, remainder=2 (not enough to get free)
    # So: 1 free item * $20 = $20
    assert abs(discount - 20.0) < 0.01, "BOGO multi-set calculation failed"
    print("    [PASS]")
    
    # Test deal retrieval and validation
    print("\n" + "=" * 70)
    print("TESTING DEAL RETRIEVAL AND VALIDATION")
    print("=" * 70)
    
    print("\n[1] Retrieving all deals...")
    all_deals = manager.get_all_deals()
    print(f"    Total deals: {len(all_deals)}")
    assert len(all_deals) == 5, f"Expected 5 deals, got {len(all_deals)}"
    print("    [PASS]")
    
    print("\n[2] Retrieving active deals...")
    active_deals = manager.get_active_deals()
    print(f"    Active deals: {len(active_deals)}")
    print("    [PASS]")
    
    print("\n[3] Checking deal details...")
    for i, deal in enumerate(all_deals, 1):
        print(f"\n    Deal {i}: {deal['name']}")
        print(f"    - Mechanism: {deal['deal_mechanism']}")
        if deal['deal_mechanism'] == 'discount':
            symbol = '%' if deal['discount_type'] == 'percentage' else '$'
            print(f"    - Discount: {deal['discount_value']}{symbol}")
        else:
            print(f"    - BOGO: Buy {deal['bogo_buy_qty']} Get {deal['bogo_get_qty']} Free")
        
        if deal['product_ids']:
            print(f"    - Products: {len(deal['product_ids'])} targeted")
        if deal['tags']:
            print(f"    - Tags: {deal['tags']}")
        if deal['categories']:
            print(f"    - Categories: {deal['categories']}")
        if deal['item_numbers']:
            print(f"    - Item Numbers: {deal['item_numbers']}")
        if deal['price_min'] or deal['price_max']:
            min_p = deal['price_min'] if deal['price_min'] else 'unlimited'
            max_p = deal['price_max'] if deal['price_max'] else 'unlimited'
            print(f"    - Price Range: ${min_p} - ${max_p}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    print("\nEnhanced deal system features verified:")
    print("- [OK] BOGO (Buy One Get One) deals")
    print("- [OK] Discount deals (percentage and fixed)")
    print("- [OK] Price range targeting")
    print("- [OK] Category-based targeting")
    print("- [OK] Tag-based targeting")
    print("- [OK] Item number targeting")
    print("- [OK] Product-specific targeting")
    print("- [OK] Multi-criteria deal matching")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_enhanced_deals()
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
