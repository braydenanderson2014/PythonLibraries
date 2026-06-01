import json
import os
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import src.banking_api as banking_api


class BankingApiPlaidFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, 'banking_api_config.json')
        self.linked_accounts_path = os.path.join(self.temp_dir.name, 'linked_bank_accounts.json')
        self.original_config_path = banking_api.BANKING_API_CONFIG_FILE
        self.original_linked_accounts_path = banking_api.LINKED_ACCOUNTS_FILE

        banking_api.BANKING_API_CONFIG_FILE = self.config_path
        banking_api.LINKED_ACCOUNTS_FILE = self.linked_accounts_path

        with open(self.config_path, 'w', encoding='utf-8') as handle:
            json.dump(
                {
                    'providers': {
                        'plaid': {
                            'enabled': True,
                            'client_id': 'client-id',
                            'secret': 'secret',
                            'environment': 'sandbox',
                            'client_name': 'Financial Manager',
                            'products': ['transactions'],
                            'country_codes': ['US'],
                            'language': 'en',
                            'redirect_uri': '',
                            'webhook': ''
                        },
                        'mock': {
                            'enabled': True,
                            'display_name': 'Demo Bank'
                        }
                    }
                },
                handle,
                indent=2
            )

    def tearDown(self):
        banking_api.BANKING_API_CONFIG_FILE = self.original_config_path
        banking_api.LINKED_ACCOUNTS_FILE = self.original_linked_accounts_path
        self.temp_dir.cleanup()

    def create_manager(self):
        return banking_api.BankingAPIManager(user_id='test-user')

    def test_link_account_accepts_public_token(self):
        manager = self.create_manager()
        plaid = manager.providers['plaid']

        plaid.exchange_public_token = lambda public_token: {
            'access_token': 'access-test-123',
            'item_id': 'item-test-123'
        }
        plaid.get_accounts = lambda access_token: [
            {
                'account_id': 'plaid-account-1',
                'name': 'Everyday Checking',
                'type': 'depository',
                'mask': '6789'
            }
        ]

        success = manager.link_account(
            provider_name='plaid',
            app_account_id='app-account-1',
            app_account_name='Primary Checking',
            public_token='public-test-123'
        )

        self.assertTrue(success)

        linked_accounts = manager.get_linked_accounts()
        self.assertEqual(len(linked_accounts), 1)
        self.assertEqual(linked_accounts[0]['access_token'], 'access-test-123')
        self.assertEqual(linked_accounts[0]['item_id'], 'item-test-123')
        self.assertEqual(linked_accounts[0]['provider_display_name'], 'Plaid')
        self.assertEqual(linked_accounts[0]['institution_name'], 'Plaid')

    def test_available_providers_include_demo_bank_label(self):
        manager = self.create_manager()
        providers = {
            provider['provider_name']: provider
            for provider in manager.get_available_providers()
        }

        self.assertEqual(providers['mock']['display_name'], 'Demo Bank')
        self.assertEqual(providers['plaid']['link_mode'], 'plaid_link')

    def test_create_plaid_link_token_uses_saved_config(self):
        manager = self.create_manager()
        captured = {}

        def fake_create_link_token(**kwargs):
            captured.update(kwargs)
            return 'link-token-123'

        manager.providers['plaid'].create_link_token = fake_create_link_token

        token = manager.create_plaid_link_token()

        self.assertEqual(token, 'link-token-123')
        self.assertEqual(captured['user_id'], 'test-user')
        self.assertEqual(captured['client_name'], 'Financial Manager')
        self.assertEqual(captured['products'], ['transactions'])
        self.assertEqual(captured['country_codes'], ['US'])
        self.assertEqual(captured['language'], 'en')


if __name__ == '__main__':
    unittest.main()