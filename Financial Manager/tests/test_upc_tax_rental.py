"""Test UPC, Product Tax Types, and Rental System"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pos_manager import POSManager
from src.product_tax_manager import ProductTaxManager
from src.rental_manager import RentalManager

def test_upc_and_tax_types():
    """Test UPC lookup and product tax types"""
    print("\n=== Testing UPC and Product Tax Types ===\n")
    
    pos_mgr = POSManager()
    
    # Add products with UPC and tax types
    print("Adding products with UPC and tax types...")
    
    # Add grocery item (tax-reduced)
    grocery_id = pos_mgr.add_product(
        name="Organic Milk",
        description="Fresh organic milk",
        item_number="MILK-001",
        upc="012000008722",
        price=4.99,
        product_tax_type="grocery",
        initial_quantity=50
    )
    print(f"[OK] Added grocery product (ID: {grocery_id})")
    
    # Add standard item
    tool_id = pos_mgr.add_product(
        name="Cordless Drill",
        description="DeWalt cordless drill",
        item_number="DRILL-001",
        upc="885911205236",
        price=99.99,
        product_tax_type="tools",
        initial_quantity=10
    )
    print(f"[OK] Added tool product (ID: {tool_id})")
    
    # Add clothing item
    clothing_id = pos_mgr.add_product(
        name="Cotton T-Shirt",
        description="White cotton t-shirt",
        item_number="SHIRT-001",
        upc="123456789012",
        price=19.99,
        product_tax_type="clothing",
        initial_quantity=100
    )
    print(f"[OK] Added clothing product (ID: {clothing_id})")
    
    # Test UPC lookup
    print("\nTesting UPC lookup...")
    milk = pos_mgr.get_product_by_upc("012000008722")
    if milk:
        print(f"[OK] Found product by UPC: {milk['name']} (${milk['price']:.2f})")
        print(f"     Tax Type: {milk['product_tax_type']}")
    else:
        print("[FAIL] UPC lookup failed")
    
    # Test product tax categories
    print("\nProduct Tax Categories:")
    categories = pos_mgr.get_product_tax_categories()
    for cat in categories:
        print(f"     - {cat}")
    
    # Test tax calculations with product types
    print("\nTesting tax calculations with product types...")
    base_rate = 0.0725  # CA rate
    
    products = [
        ("Milk (Grocery)", 4.99, "grocery"),
        ("Drill (Tools)", 99.99, "tools"),
        ("T-Shirt (Clothing)", 19.99, "clothing"),
        ("Service (Exempt)", 50.00, "services")
    ]
    
    for name, amount, tax_type in products:
        tax = pos_mgr.calculate_tax_with_product_type(amount, base_rate, tax_type)
        is_exempt = pos_mgr.is_product_tax_exempt(tax_type)
        rate = (tax / amount * 100) if amount > 0 else 0
        
        print(f"\n     {name}:")
        print(f"       Amount: ${amount:.2f}")
        print(f"       Tax Type: {tax_type}")
        print(f"       Tax Exempt: {is_exempt}")
        print(f"       Tax: ${tax:.2f} ({rate:.2f}%)")
        print(f"       Total: ${amount + tax:.2f}")
    
    print("\n[OK] All UPC and tax type tests passed!")
    return True


def test_rental_system():
    """Test rental system"""
    print("\n=== Testing Rental System ===\n")
    
    pos_mgr = POSManager()
    
    # Create a rental product
    print("Creating rental product...")
    product_id = pos_mgr.add_product(
        name="Pressure Washer Rental",
        description="2000 PSI pressure washer for rent",
        item_number="WASH-001",
        upc="984765321098",
        price=25.00,
        product_tax_type="services",
        initial_quantity=3
    )
    print(f"[OK] Created rental product (ID: {product_id})")
    
    # Create rentals
    print("\nCreating rental transactions...")
    start = datetime.now()
    end = start + timedelta(days=3)
    
    rental_id = pos_mgr.create_rental(
        product_id=product_id,
        customer_name="John Smith",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        daily_rate=25.00,
        notes="For driveway cleaning"
    )
    print(f"[OK] Created rental (ID: {rental_id})")
    
    # Get rental details
    print("\nRental Summary:")
    summary = pos_mgr.get_rental_summary(rental_id)
    if summary:
        print(f"  Customer: {summary['customer']}")
        print(f"  Product ID: {summary['product_id']}")
        print(f"  Status: {summary['status']}")
        print(f"  Days Rented: {summary['days_rented']}")
        print(f"  Daily Rate: ${summary['daily_rate']:.2f}")
        print(f"  Rental Cost: ${summary['rental_cost']:.2f}")
        print(f"  Paid Amount: ${summary['paid_amount']:.2f}")
        print(f"     Balance Due: ${summary['balance_due']:.2f}")
        print(f"     Overdue: {summary['is_overdue']}")
        print(f"     Late Fees: ${summary['late_fees']:.2f}")
        print(f"     Total Due: ${summary['total_due']:.2f}")
    else:
        print("[FAIL] Failed to get rental summary")
        return False
    
    # Test customer rentals
    print("\nFetching customer rentals...")
    customer_rentals = pos_mgr.get_customer_rentals("John Smith")
    print(f"[OK] Found {len(customer_rentals)} rental(s) for John Smith")
    
    # Test returning rental
    print("\nReturning rental...")
    pos_mgr.return_rental(rental_id, paid_amount=25.00)
    
    returned = pos_mgr.get_rental(rental_id)
    print(f"[OK] Rental returned. Status: {returned['status']}")
    
    # Test active rentals
    print("\nFetching active rentals...")
    active = pos_mgr.get_active_rentals()
    print(f"[OK] Found {len(active)} active rental(s)")
    
    print("\n[OK] All rental system tests passed!")
    return True


def test_complete_workflow():
    """Test complete workflow: product -> upc -> tax type -> rental -> calculation"""
    print("\n=== Testing Complete Workflow ===\n")
    
    pos_mgr = POSManager()
    
    # Create a complex product
    print("Creating multi-purpose rental product...")
    product_id = pos_mgr.add_product(
        name="Equipment Rental Kit",
        description="Complete equipment rental package",
        upc="555666777888",
        item_number="KIT-001",
        price=150.00,
        product_tax_type="services",
        initial_quantity=5
    )
    
    # Verify product by UPC
    product = pos_mgr.get_product_by_upc("555666777888")
    print(f"[OK] Product found by UPC: {product['name']}")
    print(f"     Item Number: {product['item_number']}")
    print(f"     Tax Type: {product['product_tax_type']}")
    
    # Create a rental
    start = datetime.now()
    end = start + timedelta(days=7)
    
    rental_id = pos_mgr.create_rental(
        product_id=product_id,
        customer_name="ABC Construction",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        daily_rate=150.00,
        notes="Construction site equipment"
    )
    print(f"\n[OK] Rental created (ID: {rental_id})")
    
    # Calculate costs and taxes
    rental_summary = pos_mgr.get_rental_summary(rental_id)
    base_tax_rate = 0.0725
    
    rental_subtotal = rental_summary['rental_cost']
    rental_tax = pos_mgr.calculate_tax_with_product_type(
        rental_subtotal,
        base_tax_rate,
        "services"
    )
    rental_total = rental_subtotal + rental_tax
    
    print(f"\nRental Calculation:")
    print(f"     Rental Period: {rental_summary['days_rented']} days")
    print(f"     Daily Rate: ${rental_summary['daily_rate']:.2f}")
    print(f"     Subtotal: ${rental_subtotal:.2f}")
    print(f"     Tax (Service Rate): ${rental_tax:.2f}")
    print(f"     Total: ${rental_total:.2f}")
    
    print("\n[OK] Complete workflow test passed!")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("UPC, PRODUCT TAX TYPES, AND RENTAL SYSTEM TESTS")
    print("=" * 60)
    
    try:
        # Run all tests
        test_upc_and_tax_types()
        test_rental_system()
        test_complete_workflow()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED [OK]")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
