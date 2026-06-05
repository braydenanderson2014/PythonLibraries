import os
import sys
import unittest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rent_tracker import RentTracker
from tenant import Tenant


class _TenantManagerStub:
    def save(self):
        return None


class RentTrackerDueDateOverrideTests(unittest.TestCase):
    def _build_tracker(self):
        tracker = RentTracker.__new__(RentTracker)
        tracker._sum_late_fee_charges_for_month = lambda *args, **kwargs: 0.0
        return tracker

    def test_first_month_due_date_respects_rental_start(self):
        tracker = self._build_tracker()
        tenant = Tenant(
            'December Start',
            ('2025-12-14', '2026-12-31'),
            1000.0,
            rent_due_date='1',
            payment_history=[
                {
                    'year': 2025,
                    'month': 12,
                    'amount': 1000.0,
                    'date': '2025-12-14',
                    'type': 'Cash',
                }
            ],
            user_id='test_user',
        )

        snapshot = tracker.get_month_payment_snapshot(tenant, 2025, 12)

        self.assertEqual(snapshot['due_date'].isoformat(), '2025-12-14')
        self.assertEqual(snapshot['display_status'], 'Paid in Full')
        self.assertFalse(snapshot['paid_late'])

    def test_monthly_due_day_override_changes_due_date(self):
        tracker = self._build_tracker()
        tenant = Tenant(
            'Monthly Due Override',
            ('2025-11-01', '2026-12-31'),
            1000.0,
            rent_due_date='1',
            monthly_due_day_overrides={'2025-12': 14},
            payment_history=[
                {
                    'year': 2025,
                    'month': 12,
                    'amount': 1000.0,
                    'date': '2025-12-14',
                    'type': 'Cash',
                }
            ],
            user_id='test_user',
        )

        snapshot = tracker.get_month_payment_snapshot(tenant, 2025, 12)

        self.assertEqual(snapshot['due_date'].isoformat(), '2025-12-14')
        self.assertEqual(snapshot['display_status'], 'Paid in Full')
        self.assertFalse(snapshot['paid_late'])

    def test_late_status_override_can_treat_paid_month_as_on_time(self):
        tracker = self._build_tracker()
        tenant = Tenant(
            'Late Status Override',
            ('2025-01-01', '2026-12-31'),
            1000.0,
            rent_due_date='1',
            monthly_late_status_overrides={'2025-12': 'on_time'},
            payment_history=[
                {
                    'year': 2025,
                    'month': 12,
                    'amount': 1000.0,
                    'date': '2025-12-14',
                    'type': 'Cash',
                }
            ],
            user_id='test_user',
        )

        snapshot = tracker.get_month_payment_snapshot(tenant, 2025, 12)

        self.assertEqual(snapshot['display_status'], 'Paid in Full')
        self.assertFalse(snapshot['paid_late'])
        self.assertEqual(snapshot['late_status_override'], 'on_time')

    def test_set_monthly_override_updates_amount_due_day_and_late_status(self):
        tracker = self._build_tracker()
        tracker.tenant_manager = _TenantManagerStub()

        tenant = Tenant(
            'Setter Test',
            ('2025-01-01', '2026-12-31'),
            1000.0,
            rent_due_date='1',
            user_id='test_user',
        )

        tracker.get_tenant_by_name = lambda tenant_name: tenant if tenant_name == tenant.name else None

        success = tracker.set_monthly_override(
            tenant.name,
            2025,
            12,
            850.0,
            notes='Partial first month',
            due_day_override=14,
            late_status_override='on_time',
        )

        self.assertTrue(success)
        self.assertEqual(tenant.monthly_exceptions['2025-12'], 850.0)
        self.assertEqual(tenant.monthly_due_day_overrides['2025-12'], 14)
        self.assertEqual(tenant.monthly_late_status_overrides['2025-12'], 'on_time')


if __name__ == '__main__':
    unittest.main()