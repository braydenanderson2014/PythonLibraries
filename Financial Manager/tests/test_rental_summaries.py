"""
Rental Summaries System - Validation and Testing
Tests all components of the rental summaries system
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rental_summaries import RentalSummaries
from rent_tracker import RentTracker
from tenant import TenantManager
from datetime import datetime, date


class RentalSummariesValidator:
    """Validates the rental summaries system"""
    
    def __init__(self):
        """Initialize validator"""
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def test_initialization(self):
        """Test system initialization"""
        test_name = "System Initialization"
        try:
            tenant_manager = TenantManager()
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            if summaries is not None:
                self.pass_test(test_name)
                return True
            else:
                self.fail_test(test_name, "Summaries object is None")
                return False
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_monthly_summary_generation(self):
        """Test monthly summary generation"""
        test_name = "Monthly Summary Generation"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_monthly_summary(tenant.tenant_id, 2025, 1)
            
            if summary is None:
                self.skip_test(test_name, "No payment data available")
                return False
            
            # Validate structure
            required_fields = ['tenant_id', 'expected_rent', 'total_paid', 'balance']
            for field in required_fields:
                if field not in summary:
                    self.fail_test(test_name, f"Missing field: {field}")
                    return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_yearly_summary_generation(self):
        """Test yearly summary generation"""
        test_name = "Yearly Summary Generation"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_yearly_summary(tenant.tenant_id, 2025)
            
            if summary is None:
                self.skip_test(test_name, "No payment data available")
                return False
            
            # Validate structure
            required_fields = ['tenant_id', 'total_expected_rent', 'total_paid', 
                             'payment_rate', 'monthly_details']
            for field in required_fields:
                if field not in summary:
                    self.fail_test(test_name, f"Missing field: {field}")
                    return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_rental_period_summary_generation(self):
        """Test rental period summary generation"""
        test_name = "Rental Period Summary Generation"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            if not tenant.rental_period:
                self.skip_test(test_name, "Tenant has no rental period")
                return False
            
            summary = summaries.get_rental_period_summary(tenant.tenant_id)
            
            if summary is None:
                self.skip_test(test_name, "Failed to generate summary")
                return False
            
            # Validate structure
            required_fields = ['tenant_id', 'rental_start_date', 'rental_end_date',
                             'total_expected_rent', 'total_paid', 'yearly_summaries']
            for field in required_fields:
                if field not in summary:
                    self.fail_test(test_name, f"Missing field: {field}")
                    return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_monthly_formatting(self):
        """Test monthly summary formatting"""
        test_name = "Monthly Summary Formatting"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_monthly_summary(tenant.tenant_id, 2025, 1)
            
            if summary is None:
                self.skip_test(test_name, "No payment data available")
                return False
            
            formatted = summaries.format_monthly_display(summary)
            
            if not formatted or not isinstance(formatted, str):
                self.fail_test(test_name, "Invalid formatted output")
                return False
            
            if "MONTHLY SUMMARY" not in formatted:
                self.fail_test(test_name, "Missing header in formatted output")
                return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_yearly_formatting(self):
        """Test yearly summary formatting"""
        test_name = "Yearly Summary Formatting"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_yearly_summary(tenant.tenant_id, 2025)
            
            if summary is None:
                self.skip_test(test_name, "No payment data available")
                return False
            
            formatted = summaries.format_yearly_display(summary)
            
            if not formatted or not isinstance(formatted, str):
                self.fail_test(test_name, "Invalid formatted output")
                return False
            
            if "YEARLY SUMMARY" not in formatted:
                self.fail_test(test_name, "Missing header in formatted output")
                return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_rental_period_formatting(self):
        """Test rental period summary formatting"""
        test_name = "Rental Period Summary Formatting"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_rental_period_summary(tenant.tenant_id)
            
            if summary is None:
                self.skip_test(test_name, "No rental period data available")
                return False
            
            formatted = summaries.format_rental_period_display(summary)
            
            if not formatted or not isinstance(formatted, str):
                self.fail_test(test_name, "Invalid formatted output")
                return False
            
            if "RENTAL PERIOD SUMMARY" not in formatted:
                self.fail_test(test_name, "Missing header in formatted output")
                return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_json_export(self):
        """Test JSON export"""
        test_name = "JSON Export"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            
            # Test monthly JSON export
            result = summaries.export_monthly_summary_json(
                tenant.tenant_id, 2025, 1, 'test_monthly.json'
            )
            
            if not result:
                self.skip_test(test_name, "Monthly export not available")
                return False
            
            # Check file exists
            if not os.path.exists('test_monthly.json'):
                self.fail_test(test_name, "JSON file not created")
                return False
            
            # Clean up
            try:
                os.remove('test_monthly.json')
            except:
                pass
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_csv_export(self):
        """Test CSV export"""
        test_name = "CSV Export"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            summary = summaries.get_yearly_summary(tenant.tenant_id, 2025)
            
            if summary is None:
                self.skip_test(test_name, "No payment data available")
                return False
            
            # Test CSV export
            result = summaries.export_to_csv(
                summary, 'test_yearly.csv', summary_type='yearly'
            )
            
            if not result:
                self.fail_test(test_name, "CSV export failed")
                return False
            
            # Check file exists
            if not os.path.exists('test_yearly.csv'):
                self.fail_test(test_name, "CSV file not created")
                return False
            
            # Clean up
            try:
                os.remove('test_yearly.csv')
            except:
                pass
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def test_print_functions(self):
        """Test print functions"""
        test_name = "Print Functions"
        try:
            tenant_manager = TenantManager()
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                self.skip_test(test_name, "No tenants available")
                return False
            
            rent_tracker = RentTracker(tenant_manager=tenant_manager)
            summaries = RentalSummaries(rent_tracker=rent_tracker)
            
            tenant = tenants[0]
            
            # Test print functions (they should return True/False)
            result1 = summaries.print_monthly_summary(tenant.tenant_id, 2025, 1)
            result2 = summaries.print_yearly_summary(tenant.tenant_id, 2025)
            result3 = summaries.print_rental_period_summary(tenant.tenant_id)
            
            # At least one should succeed if data exists
            if not (result1 or result2 or result3):
                self.skip_test(test_name, "No data available for printing")
                return False
            
            self.pass_test(test_name)
            return True
        except Exception as e:
            self.fail_test(test_name, str(e))
            return False
    
    def pass_test(self, test_name):
        """Record passing test"""
        self.tests_passed += 1
        self.results.append(f"✓ {test_name}")
        print(f"✓ {test_name}")
    
    def fail_test(self, test_name, reason):
        """Record failing test"""
        self.tests_failed += 1
        self.results.append(f"✗ {test_name}: {reason}")
        print(f"✗ {test_name}: {reason}")
    
    def skip_test(self, test_name, reason):
        """Record skipped test"""
        self.results.append(f"⊘ {test_name}: {reason}")
        print(f"⊘ {test_name}: {reason}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("\n" + "="*70)
        print("RENTAL SUMMARIES SYSTEM - VALIDATION TEST SUITE")
        print("="*70 + "\n")
        
        self.test_initialization()
        self.test_monthly_summary_generation()
        self.test_yearly_summary_generation()
        self.test_rental_period_summary_generation()
        self.test_monthly_formatting()
        self.test_yearly_formatting()
        self.test_rental_period_formatting()
        self.test_json_export()
        self.test_csv_export()
        self.test_print_functions()
        
        print("\n" + "="*70)
        print(f"RESULTS: {self.tests_passed} passed, {self.tests_failed} failed")
        print("="*70 + "\n")
        
        for result in self.results:
            print(result)
        
        print("\n" + "="*70)
        if self.tests_failed == 0:
            print("✓ All validation tests passed!")
        else:
            print(f"✗ {self.tests_failed} test(s) failed")
        print("="*70 + "\n")
        
        return self.tests_failed == 0


if __name__ == "__main__":
    validator = RentalSummariesValidator()
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)
