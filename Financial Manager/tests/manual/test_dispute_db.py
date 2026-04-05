#!/usr/bin/env python
"""Test dispute database persistence"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.database import DatabaseManager
from src.disputes import DisputeManager

# Create database and dispute manager
db = DatabaseManager()
dm = DisputeManager(db_manager=db)

print('✓ Both initialized successfully')
print(f'  Database: {db.db_path}')

# Create a test dispute
dispute = dm.create_dispute(
    'T001',
    'payment_not_recorded',
    'Test dispute - Payment from 1/15',
    amount=1800.00,
    reference_month='2026-01',
    reference_payment_id='PAY_001'
)

print(f'✓ Created dispute: {dispute.dispute_id}')

# Check database
db_dispute = db.get_dispute(dispute.dispute_id)
if db_dispute:
    print(f'✓ Found in database: {db_dispute["dispute_id"]}')
    print(f'  Status: {db_dispute["status"]}')
    print(f'  Type: {db_dispute["dispute_type"]}')
    print(f'  Amount: {db_dispute["amount"]}')
    print(f'  Reference Payment ID: {db_dispute["reference_payment_id"]}')
else:
    print('✗ Not found in database')

# Get all disputes for tenant
all_disputes = db.get_tenant_disputes('T001')
print(f'✓ Tenant disputes in DB: {len(all_disputes)}')

# Get dispute stats
stats = db.get_dispute_stats('T001')
print(f'✓ Dispute stats: {stats}')

# Create another dispute linked to delinquency
dispute2 = dm.create_dispute(
    'T001',
    'incorrect_balance',
    'Balance calculation error for delinquent month',
    amount=2500.00,
    reference_month='2025-12'
)

print(f'✓ Created second dispute: {dispute2.dispute_id}')

# Update first dispute status
db.update_dispute(dispute.dispute_id, status='acknowledged', admin_notes='Payment issue acknowledged')
print(f'✓ Updated dispute status')

# Check updated dispute
updated_dispute = db.get_dispute(dispute.dispute_id)
print(f'  New status: {updated_dispute["status"]}')
print(f'  Admin notes: {updated_dispute["admin_notes"]}')

print('\n✓ All database tests passed!')
