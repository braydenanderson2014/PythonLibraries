#!/usr/bin/env python
"""Debug script to check rental summaries data"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.tenant import TenantManager
from src.rent_tracker import RentTracker
from src.rental_summaries import RentalSummaries

tm = TenantManager()
tm.load()

for t in tm.list_tenants()[:1]:  # Get first tenant only
    print(f'Tenant: {t.name}, ID: {t.tenant_id}')
    print(f'  Rent Amount: {t.rent_amount}')
    print(f'  Rental Period: {t.rental_period}')
    print(f'  Months to Charge: {len(t.months_to_charge) if hasattr(t, "months_to_charge") else "N/A"}')
    print(f'  Payment History Count: {len(t.payment_history) if hasattr(t, "payment_history") else "N/A"}')
    
    if hasattr(t, 'payment_history') and t.payment_history:
        print(f'\n  First 3 payments:')
        for i, p in enumerate(t.payment_history[:3]):
            print(f'    [{i}] {type(p).__name__}: {p}')
    
    print(f'\n  Months to charge (first 5):')
    if hasattr(t, 'months_to_charge'):
        for year, month in t.months_to_charge[:5]:
            print(f'    {year}-{month:02d}')
    
    print(f'\n  Testing RentalSummaries:')
    rt = RentTracker()
    summaries = RentalSummaries(rent_tracker=rt)
    
    # Test monthly summary for 2025-01
    monthly = summaries.get_monthly_summary(t.tenant_id, 2025, 1)
    print(f'\n  Monthly Summary (2025-01): {monthly}')
    
    # Test yearly summary for 2025
    yearly = summaries.get_yearly_summary(t.tenant_id, 2025)
    print(f'\n  Yearly Summary (2025): {yearly}')
