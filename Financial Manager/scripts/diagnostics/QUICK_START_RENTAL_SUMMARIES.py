#!/usr/bin/env python3
"""
Rental Summaries System - Quick Start Checklist
Follow this checklist to get the system up and running
"""

import sys
import os

class QuickStartChecklist:
    """Interactive quick start checklist"""
    
    def __init__(self):
        self.items = [
            {
                'name': 'Files Installed',
                'steps': [
                    '✓ rental_summaries.py placed in src/',
                    '✓ rental_summaries_examples.py placed in src/',
                    '✓ rental_summaries_ui.py placed in src/',
                    '✓ test_rental_summaries.py placed in tests/',
                ]
            },
            {
                'name': 'Documentation Read',
                'steps': [
                    '✓ RENTAL_SUMMARIES_README.md - Overview',
                    '✓ RENTAL_SUMMARIES_QUICK_REF.md - Quick reference',
                    '✓ RENTAL_SUMMARIES_GUIDE.md - Full documentation',
                ]
            },
            {
                'name': 'System Testing',
                'steps': [
                    '✓ Run: python tests/test_rental_summaries.py',
                    '✓ Run: python src/rental_summaries_examples.py',
                    '✓ Verify test output shows passing tests',
                ]
            },
            {
                'name': 'Basic Usage',
                'steps': [
                    '✓ Create basic summary: summaries.get_rental_period_summary(tenant_id)',
                    '✓ Display summary: summaries.print_rental_period_summary(tenant_id)',
                    '✓ Export to JSON: summaries.export_rental_period_summary_json(tenant_id, "file.json")',
                ]
            },
            {
                'name': 'UI Integration (Optional)',
                'steps': [
                    '✓ Read RENTAL_SUMMARIES_INTEGRATION.md',
                    '✓ Add imports to main_window.py',
                    '✓ Initialize RentalSummariesWidget',
                    '✓ Add menu items for summaries',
                    '✓ Test with actual UI',
                ]
            },
            {
                'name': 'Batch Processing (Optional)',
                'steps': [
                    '✓ Review SummaryReportGenerator class',
                    '✓ Implement batch report generation',
                    '✓ Test with all tenants',
                    '✓ Set up automated scheduling if desired',
                ]
            },
            {
                'name': 'Production Deployment',
                'steps': [
                    '✓ All tests passing',
                    '✓ Documentation accessible to users',
                    '✓ Error handling verified',
                    '✓ Logging configured',
                    '✓ Deployment ready',
                ]
            },
        ]
    
    def print_checklist(self):
        """Print the complete checklist"""
        print("\n" + "="*70)
        print("RENTAL SUMMARIES SYSTEM - QUICK START CHECKLIST")
        print("="*70 + "\n")
        
        for i, section in enumerate(self.items, 1):
            print(f"{i}. {section['name'].upper()}")
            print("-" * 70)
            for step in section['steps']:
                print(f"   {step}")
            print()
    
    def print_quick_commands(self):
        """Print quick command reference"""
        print("="*70)
        print("QUICK COMMANDS")
        print("="*70 + "\n")
        
        commands = {
            'Test System': 'python tests/test_rental_summaries.py',
            'Run Examples': 'python src/rental_summaries_examples.py',
            'Quick Test Import': 'python -c "from src.rental_summaries import RentalSummaries; print(\'✓ Import successful\')"',
        }
        
        for name, cmd in commands.items():
            print(f"{name}:")
            print(f"  {cmd}\n")
    
    def print_quick_code(self):
        """Print quick code snippet"""
        print("="*70)
        print("QUICK CODE SNIPPET")
        print("="*70 + "\n")
        
        code = '''# Minimal working example
from src.rental_summaries import RentalSummaries
from src.rent_tracker import RentTracker
from src.tenant import TenantManager

# Initialize
tenant_manager = TenantManager()
rent_tracker = RentTracker(tenant_manager=tenant_manager)
summaries = RentalSummaries(rent_tracker=rent_tracker)

# Get first tenant
tenants = tenant_manager.list_tenants()
if tenants:
    tenant_id = tenants[0].tenant_id
    
    # Print rental period summary
    summaries.print_rental_period_summary(tenant_id)
    
    # Export to JSON
    summaries.export_rental_period_summary_json(
        tenant_id, 'tenant_report.json'
    )
    
    print("✓ Summary generated successfully!")
else:
    print("No tenants found")
'''
        print(code)
        print()
    
    def print_file_locations(self):
        """Print file locations"""
        print("="*70)
        print("FILE LOCATIONS")
        print("="*70 + "\n")
        
        files = {
            'Core Module': 'src/rental_summaries.py',
            'Examples': 'src/rental_summaries_examples.py',
            'UI Integration': 'src/rental_summaries_ui.py',
            'Tests': 'tests/test_rental_summaries.py',
            'Quick Reference': 'docs/RENTAL_SUMMARIES_QUICK_REF.md',
            'Full Guide': 'docs/RENTAL_SUMMARIES_GUIDE.md',
            'Implementation': 'docs/RENTAL_SUMMARIES_IMPLEMENTATION.md',
            'Integration': 'docs/RENTAL_SUMMARIES_INTEGRATION.md',
            'Overview': 'RENTAL_SUMMARIES_README.md',
        }
        
        for name, path in files.items():
            print(f"{name:<20} {path}")
        print()
    
    def print_support_resources(self):
        """Print support resources"""
        print("="*70)
        print("SUPPORT RESOURCES")
        print("="*70 + "\n")
        
        resources = {
            'Quick Answers': 'RENTAL_SUMMARIES_QUICK_REF.md',
            'Full Documentation': 'RENTAL_SUMMARIES_GUIDE.md',
            'How It Works': 'RENTAL_SUMMARIES_IMPLEMENTATION.md',
            'How to Integrate': 'RENTAL_SUMMARIES_INTEGRATION.md',
            'Working Examples': 'src/rental_summaries_examples.py',
            'Tests': 'tests/test_rental_summaries.py',
        }
        
        print("Start with:")
        print("  1. This checklist")
        print("  2. Quick Reference guide")
        print("  3. Run the examples\n")
        
        print("Then:")
        print("  4. Read the full guide")
        print("  5. Integrate into your application")
        print("  6. Deploy to production\n")
        
        print("Resources:")
        for name, path in resources.items():
            print(f"  • {name}: {path}")
        print()
    
    def print_common_tasks(self):
        """Print common tasks"""
        print("="*70)
        print("COMMON TASKS")
        print("="*70 + "\n")
        
        tasks = {
            'Display monthly summary': 'summaries.print_monthly_summary(tenant_id, 2025, 1)',
            'Display yearly summary': 'summaries.print_yearly_summary(tenant_id, 2025)',
            'Display full summary': 'summaries.print_rental_period_summary(tenant_id)',
            'Get summary as dict': 'summary = summaries.get_monthly_summary(tenant_id, 2025, 1)',
            'Export to JSON': 'summaries.export_monthly_summary_json(tenant_id, 2025, 1, "file.json")',
            'Export to CSV': 'summaries.export_to_csv(summary, "file.csv", "yearly")',
            'Process all tenants': 'for t in tenant_manager.list_tenants(): summaries.print_rental_period_summary(t.tenant_id)',
        }
        
        for task, code in tasks.items():
            print(f"{task}:")
            print(f"  {code}\n")


def main():
    """Run the quick start checklist"""
    checklist = QuickStartChecklist()
    
    print("\n")
    checklist.print_checklist()
    checklist.print_quick_commands()
    checklist.print_quick_code()
    checklist.print_file_locations()
    checklist.print_common_tasks()
    checklist.print_support_resources()
    
    print("="*70)
    print("START HERE:")
    print("="*70)
    print("\n1. Read: RENTAL_SUMMARIES_README.md")
    print("2. Read: RENTAL_SUMMARIES_QUICK_REF.md")
    print("3. Run:  python tests/test_rental_summaries.py")
    print("4. Run:  python src/rental_summaries_examples.py")
    print("5. Integrate using RENTAL_SUMMARIES_INTEGRATION.md\n")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
