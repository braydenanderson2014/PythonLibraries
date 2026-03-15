import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ui')))


from account import AccountManager
from bank import Bank
from login import verify_user
from tenant import TenantManager
from rent_tracker import RentTracker
from uac import UACManager
from settings import SettingsController

TEST_USER = 'testuser'
TEST_PASS = 'testpass123'
TEST_DETAILS = {'email': 'test@example.com'}

TEST_TENANT_NAME = 'John Doe'
TEST_TENANT_PERIOD = ('2025-01-01', '2025-12-01')
TEST_TENANT_RENT = 1200.0
TEST_TENANT_DEPOSIT = 500.0

# Clean up any previous test data
account_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'accounts.json'))
bank_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'bank_data.json'))
tenant_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'tenants.json'))
for db in [account_db, bank_db, tenant_db]:
    if os.path.exists(db):
        os.remove(db)

def test_account_manager():
    am = AccountManager()
    # Create account
    acc = am.create_account(TEST_USER, TEST_PASS, **TEST_DETAILS)
    assert acc['username'] == TEST_USER
    assert am.verify_password(TEST_USER, TEST_PASS)
    # Get account by username
    acc2 = am.get_account(TEST_USER)
    assert acc2['account_id'] == acc['account_id']
    # Update account details
    am.update_account(TEST_USER, phone='1234567890')
    assert am.get_account(TEST_USER)['details']['phone'] == '1234567890'
    # Get account by ID
    acc3 = am.get_account_by_id(acc['account_id'])
    assert acc3['username'] == TEST_USER
    print('AccountManager tests passed.')

def test_bank():
    am = AccountManager()
    acc = am.get_account(TEST_USER)
    account_id = acc['account_id']
    bank = Bank()
    # Add transaction
    tx1 = bank.add_transaction(100.0, 'Deposit', account_id, type_='in', category='salary')
    assert tx1['amount'] == 100.0
    assert tx1['type'] == 'in'
    # Add another transaction
    tx2 = bank.add_transaction(50.0, 'Rent', account_id, type_='out', category='rent')
    assert tx2['type'] == 'out'
    # Update transaction by identifier
    tx2_id = tx2['identifier']
    bank.add_transaction(60.0, 'Updated Rent', account_id, identifier=tx2_id, type_='out', category='rent')
    tx2_updated = bank.get_transaction(tx2_id, account_id)
    assert tx2_updated['amount'] == 60.0
    assert tx2_updated['desc'] == 'Updated Rent'
    # List transactions for account
    txs = bank.list_transactions(account_id)
    assert len(txs) == 2
    # Search transactions
    results = bank.search_transactions(account=account_id, type='out')
    assert len(results) == 1 and results[0]['desc'] == 'Updated Rent'
    # Search by amount range
    results = bank.search_transactions(account=account_id, amount_range=(50, 120))
    assert len(results) == 2
    # Remove transaction
    bank.remove_transaction(tx2_id, account_id)
    txs = bank.list_transactions(account_id)
    assert len(txs) == 1
    print('Bank tests passed.')

def test_login():
    # Correct login
    assert verify_user(TEST_USER, TEST_PASS)
    # Incorrect password
    assert not verify_user(TEST_USER, 'wrongpass')
    # Nonexistent user
    assert not verify_user('nouser', 'nopass')
    print('Login tests passed.')

def test_tenant_manager():
    tm = TenantManager()
    # Set a test user for the tenant manager
    tm.set_current_user('test_user')
    tenant = tm.add_tenant(TEST_TENANT_NAME, TEST_TENANT_PERIOD, TEST_TENANT_RENT, TEST_TENANT_DEPOSIT, contact_info={'phone': '555-1234'})
    assert tenant.name == TEST_TENANT_NAME
    assert tenant.rent_amount == TEST_TENANT_RENT
    # Search by name
    results = tm.search_tenants(name=TEST_TENANT_NAME)
    print(f"Search results for name='{TEST_TENANT_NAME}':", [t.name for t in results])
    if len(results) != 1:
        print("DEBUG: TenantManager contents:", [t.to_dict() for t in tm.list_tenants()])
        print("DEBUG: Search criteria:", TEST_TENANT_NAME)
        print("DEBUG: Raw results:", results)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}. Results: {[t.name for t in results]}"
    # Update tenant
    tm.update_tenant(tenant.tenant_id, notes='VIP tenant')
    assert tm.get_tenant(tenant.tenant_id).notes.split('\n')[0] == 'VIP tenant'
    print('TenantManager tests passed.')

def test_rent_tracker_and_uac():
    tm = TenantManager()
    # Set test user and ensure we have a tenant
    tm.set_current_user('test_user')
    # Create a tenant if none exists
    if not tm.list_tenants():
        tm.add_tenant(TEST_TENANT_NAME, TEST_TENANT_PERIOD, TEST_TENANT_RENT, TEST_TENANT_DEPOSIT, contact_info={'phone': '555-1234'})
    tenant = tm.list_tenants()[0]
    rt = RentTracker(current_user_id='test_user')
    uac = UACManager()
    settings = SettingsController()
    # Set rent period
    assert rt.set_rent_period(tenant.tenant_id, TEST_TENANT_PERIOD[0], TEST_TENANT_PERIOD[1])
    # UAC: require password for rent change
    task = 'change_rent_details'
    assert not uac.is_authorized(TEST_USER, task)
    assert not uac.authorize(TEST_USER, 'wrongpass', task)
    assert uac.authorize(TEST_USER, TEST_PASS, task)
    assert uac.is_authorized(TEST_USER, task)
    # Change rent details (protected)
    try:
        rt.change_rent_details(tenant.tenant_id, TEST_USER, 'wrongpass', rent_amount=1300.0)
        assert False, 'Should not allow with wrong password'
    except PermissionError:
        pass
    rt.change_rent_details(tenant.tenant_id, TEST_USER, TEST_PASS, rent_amount=1300.0)
    tm.load()  # Reload tenant data after change
    assert tm.get_tenant(tenant.tenant_id).rent_amount == 1300.0
    # UAC token expires
    settings.set('uac_duration_seconds', 1)
    import time; time.sleep(2)
    assert not uac.is_authorized(TEST_USER, task)
    settings.set('uac_duration_seconds', 300)
    # Re-authorize for subsequent protected actions
    assert uac.authorize(TEST_USER, TEST_PASS, task)
    # Send income to financial tracker
    acc = AccountManager().get_account(TEST_USER)
    account_id = acc['account_id']
    tm.get_tenant(tenant.tenant_id).total_rent_paid = 1300.0
    tm.save()  # Save after updating total_rent_paid
    # Ensure RentTracker's tenant manager reloads latest data
    rt.tenant_manager.load()
    summary = rt.get_rent_summary_for_financial_tracker()
    assert summary['total_paid'] >= 1300.0
    assert summary['expected'] >= 1300.0
    # Compensate expected remaining
    rt.compensate_expected_remaining(tenant.tenant_id, 100.0)
    rt.tenant_manager.load()  # Reload after compensation
    assert rt.tenant_manager.get_tenant(tenant.tenant_id).total_rent_paid >= 1400.0
    print('RentTracker & UACManager tests passed.')

def test_settings_controller():
    settings = SettingsController()
    settings.set('uac_enabled', False)
    assert not settings.get('uac_enabled') == True
    settings.set('uac_enabled', True)
    assert settings.get('uac_enabled') == True
    print('SettingsController tests passed.')

def run_tests():
    test_account_manager()
    test_bank()
    test_login()
    test_tenant_manager()
    test_rent_tracker_and_uac()
    test_settings_controller()
    print('All tests passed.')

if __name__ == '__main__':
    run_tests()
