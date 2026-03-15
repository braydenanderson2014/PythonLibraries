"""
Test suite for POS system
Tests database operations, manager functions, and business logic
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pos_database import POSDatabase
from src.pos_manager import POSManager


class TestPOSDatabase(unittest.TestCase):
    """Test POS database operations"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        self.db = POSDatabase(self.test_db_path)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_add_product(self):
        """Test adding a product"""
        product_id = self.db.add_product(
            name="Test Product",
            description="A test product",
            item_number="TEST-001",
            price=10.00,
            sale_price=8.00,
            purchase_price=5.00
        )
        
        self.assertIsNotNone(product_id)
        
        product = self.db.get_product(product_id)
        self.assertIsNotNone(product)
        self.assertEqual(product['name'], "Test Product")
        self.assertEqual(product['price'], 10.00)
        self.assertEqual(product['quantity_in_stock'], 0)
    
    def test_get_product_by_name(self):
        """Test getting product by name"""
        product_id = self.db.add_product(name="Named Product", price=20.00)
        
        product = self.db.get_product_by_name("Named Product")
        self.assertIsNotNone(product)
        self.assertEqual(product['product_id'], product_id)
    
    def test_update_product(self):
        """Test updating a product"""
        product_id = self.db.add_product(name="Original Name", price=10.00)
        
        self.db.update_product(product_id, price=15.00, name="Updated Name")
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['price'], 15.00)
        self.assertEqual(product['name'], "Updated Name")
    
    def test_inventory_update(self):
        """Test inventory updates"""
        product_id = self.db.add_product(name="Stock Item", price=10.00)
        
        # Add inventory
        self.db.update_inventory(product_id, 100, "initial_stock")
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 100)
        
        # Reduce inventory
        self.db.update_inventory(product_id, -30, "sale")
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 70)
    
    def test_inventory_cannot_go_negative(self):
        """Test that inventory cannot go negative"""
        product_id = self.db.add_product(name="Limited Stock", price=10.00)
        
        # Set inventory to 10
        self.db.update_inventory(product_id, 10, "initial_stock")
        
        # Try to remove 20 (should cap at 0)
        self.db.update_inventory(product_id, -20, "sale")
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 0)
    
    def test_record_sale(self):
        """Test recording a sale"""
        product_id = self.db.add_product(name="Sale Item", price=10.00)
        self.db.update_inventory(product_id, 100, "initial_stock")
        
        transaction_id = self.db.record_sale(
            product_id=product_id,
            quantity=5,
            unit_price=10.00,
            fees=1.00,
            customer_name="John Doe"
        )
        
        self.assertIsNotNone(transaction_id)
        
        transaction = self.db.get_transaction(transaction_id)
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction['quantity_sold'], 5)
        self.assertEqual(transaction['total_amount'], 51.00)  # 5*10 + 1
        
        # Check inventory was reduced
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 95)
    
    def test_sale_at_zero_inventory(self):
        """Test that we can sell at zero inventory (but stays at 0)"""
        product_id = self.db.add_product(name="Always Available", price=10.00)
        
        # Record sale without adding inventory
        transaction_id = self.db.record_sale(
            product_id=product_id,
            quantity=3,
            unit_price=10.00
        )
        
        self.assertIsNotNone(transaction_id)
        
        # Inventory should be 0, not -3
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 0)
    
    def test_refund_transaction(self):
        """Test refunding a transaction"""
        product_id = self.db.add_product(name="Refundable Item", price=10.00)
        self.db.update_inventory(product_id, 50, "initial_stock")
        
        # Record sale
        transaction_id = self.db.record_sale(
            product_id=product_id,
            quantity=5,
            unit_price=10.00
        )
        
        # Refund it
        refund_id = self.db.refund_transaction(transaction_id, "Changed mind")
        
        self.assertIsNotNone(refund_id)
        
        # Check original is marked refunded
        transaction = self.db.get_transaction(transaction_id)
        self.assertTrue(transaction['is_refunded'])
        self.assertEqual(transaction['refund_transaction_id'], refund_id)
        
        # Check inventory was restored
        product = self.db.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 50)
    
    def test_get_sales_summary(self):
        """Test getting sales summary"""
        product_id = self.db.add_product(name="Popular Item", price=10.00)
        self.db.update_inventory(product_id, 1000, "initial_stock")
        
        # Record multiple sales
        self.db.record_sale(product_id, 5, 10.00)
        self.db.record_sale(product_id, 3, 10.00)
        self.db.record_sale(product_id, 2, 10.00)
        
        summary = self.db.get_sales_summary(product_id)
        
        self.assertEqual(summary['total_transactions'], 3)
        self.assertEqual(summary['total_quantity'], 10)
        self.assertEqual(summary['total_revenue'], 100.00)


class TestPOSManager(unittest.TestCase):
    """Test POS manager operations"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        self.db = POSDatabase(self.test_db_path)
        self.manager = POSManager(self.db)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_add_product_with_validation(self):
        """Test adding product with validation"""
        product_id = self.manager.add_product(
            name="Validated Product",
            price=25.00,
            initial_quantity=50
        )
        
        self.assertIsNotNone(product_id)
        
        product = self.manager.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 50)
    
    def test_add_product_validation_fails(self):
        """Test that invalid product data raises errors"""
        with self.assertRaises(ValueError):
            self.manager.add_product(name="", price=10.00)  # Empty name
        
        with self.assertRaises(ValueError):
            self.manager.add_product(name="Invalid", price=-5.00)  # Negative price
    
    def test_process_sale(self):
        """Test processing a sale through manager"""
        product_id = self.manager.add_product(
            name="Sellable Item",
            price=15.00,
            initial_quantity=100
        )
        
        transaction_id, total = self.manager.process_sale(
            product_id=product_id,
            quantity=4,
            payment_method="cash",
            customer_name="Jane Doe"
        )
        
        self.assertIsNotNone(transaction_id)
        self.assertEqual(total, 60.00)
        
        product = self.manager.get_product(product_id)
        self.assertEqual(product['quantity_in_stock'], 96)
    
    def test_process_sale_uses_sale_price(self):
        """Test that sales use sale price if available"""
        product_id = self.manager.add_product(
            name="Discounted Item",
            price=20.00,
            sale_price=15.00,
            initial_quantity=50
        )
        
        _, total = self.manager.process_sale(
            product_id=product_id,
            quantity=2
        )
        
        self.assertEqual(total, 30.00)  # 2 * 15.00
    
    def test_process_sale_with_fees(self):
        """Test that fees are included in sale"""
        product_id = self.manager.add_product(
            name="Item with Fees",
            price=10.00,
            fees=2.50,
            initial_quantity=50
        )
        
        _, total = self.manager.process_sale(
            product_id=product_id,
            quantity=1
        )
        
        self.assertEqual(total, 12.50)  # 10.00 + 2.50
    
    def test_get_top_sellers(self):
        """Test getting top selling products"""
        # Create products
        product1_id = self.manager.add_product("Product A", item_number="PA001", price=10.00, initial_quantity=1000)
        product2_id = self.manager.add_product("Product B", item_number="PB001", price=20.00, initial_quantity=1000)
        product3_id = self.manager.add_product("Product C", item_number="PC001", price=15.00, initial_quantity=1000)
        
        # Record sales
        self.manager.process_sale(product1_id, 50)
        self.manager.process_sale(product2_id, 30)
        self.manager.process_sale(product3_id, 20)
        
        top_sellers = self.manager.get_top_sellers(3)
        
        self.assertEqual(len(top_sellers), 3)
        self.assertEqual(top_sellers[0]['name'], 'Product A')  # Most sold
        self.assertEqual(top_sellers[0]['quantity_sold'], 50)
    
    def test_get_low_stock_products(self):
        """Test identifying low stock products"""
        self.manager.add_product(
            "Low Stock Item",
            item_number="LOW001",
            price=10.00,
            initial_quantity=2,
            reorder_level=5
        )
        self.manager.add_product(
            "Adequate Stock Item",
            item_number="OK001",
            price=10.00,
            initial_quantity=50,
            reorder_level=5
        )
        
        low_stock = self.manager.get_low_stock_products()
        
        self.assertEqual(len(low_stock), 1)
        self.assertEqual(low_stock[0]['name'], 'Low Stock Item')
    
    def test_refund_sale_through_manager(self):
        """Test refunding a sale through manager"""
        product_id = self.manager.add_product(
            "Returnable Item",
            price=25.00,
            initial_quantity=100
        )
        
        transaction_id, _ = self.manager.process_sale(product_id, 5)
        
        product_before = self.manager.get_product(product_id)
        initial_quantity = product_before['quantity_in_stock']
        
        # Refund
        refund_id = self.manager.refund_sale(transaction_id, "Defective")
        
        self.assertIsNotNone(refund_id)
        
        product_after = self.manager.get_product(product_id)
        self.assertEqual(product_after['quantity_in_stock'], initial_quantity + 5)


class TestPOSIntegration(unittest.TestCase):
    """Integration tests for POS system"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        self.db = POSDatabase(self.test_db_path)
        self.manager = POSManager(self.db)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_complete_pos_workflow(self):
        """Test a complete POS workflow"""
        # 1. Add products
        coffee_id = self.manager.add_product(
            name="Coffee",
            description="Fresh brewed coffee",
            item_number="COFFEE-001",
            price=3.50,
            sale_price=3.00,
            purchase_price=1.50,
            fees=0.25,
            initial_quantity=100,
            reorder_level=20
        )
        
        tea_id = self.manager.add_product(
            name="Tea",
            description="Assorted tea",
            item_number="TEA-001",
            price=2.50,
            purchase_price=0.75,
            initial_quantity=75,
            reorder_level=10
        )
        
        # 2. Verify products exist
        products = self.manager.get_all_products()
        self.assertEqual(len(products), 2)
        
        # 3. Process multiple sales
        for i in range(5):
            self.manager.process_sale(coffee_id, 2, payment_method="cash", customer_name=f"Customer {i}")
            self.manager.process_sale(tea_id, 1, payment_method="card")
        
        # 4. Check inventory
        coffee = self.manager.get_product(coffee_id)
        tea = self.manager.get_product(tea_id)
        self.assertEqual(coffee['quantity_in_stock'], 90)  # 100 - (5*2)
        self.assertEqual(tea['quantity_in_stock'], 70)     # 75 - (5*1)
        
        # 5. Check sales summary
        summary = self.manager.get_sales_summary()
        self.assertEqual(summary['total_transactions'], 10)  # 5 coffee + 5 tea
        
        # 6. Get reports
        top_sellers = self.manager.get_top_sellers(2)
        self.assertEqual(len(top_sellers), 2)
        self.assertEqual(top_sellers[0]['name'], 'Coffee')  # More sold
        
        # 7. Adjust inventory (restock)
        self.manager.adjust_inventory(coffee_id, 50, "restock")
        coffee = self.manager.get_product(coffee_id)
        self.assertEqual(coffee['quantity_in_stock'], 140)
        
print("\n[PASS] Complete POS workflow test passed!")


if __name__ == '__main__':
    unittest.main()
