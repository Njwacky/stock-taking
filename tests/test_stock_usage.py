"""Stock usage: submit, review, and the approval signal that updates stock."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import Kit, NotificationLog, StockUsage

User = get_user_model()

pytestmark = pytest.mark.django_db


def submit_usage(client, kit_type, quantity):
    return client.post('/tracking/', {
        'kit_type': kit_type.id,
        'quantity_used': str(quantity),
        'purpose': 'Build job',
        'feedback': 'ok',
    })


class TestSubmission:
    def test_member_submits_pending_request(self, as_member, member, kit_type):
        response = submit_usage(as_member, kit_type, 10)
        assert response.status_code == 302
        usage = StockUsage.objects.get(user=member)
        assert usage.status == 'pending'
        assert usage.kit_type_name == kit_type.name

    def test_admins_notified_on_submission(self, as_member, owner, kit_type):
        submit_usage(as_member, kit_type, 10)
        assert NotificationLog.objects.filter(notification_type='stock_usage').exists()


class TestApprovalReducesStock:
    def test_partial_usage_reduces_kit_quantity(self, as_manager, member, kit_type, kit):
        """Regression: approval used to mark stock_deleted=True without touching stock."""
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=30, status='pending',
        )
        response = as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        assert response.status_code == 302
        kit.refresh_from_db()
        usage.refresh_from_db()
        assert kit.quantity == 70
        assert usage.status == 'completed'

    def test_full_usage_deletes_kit(self, as_manager, member, kit_type, kit):
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=100, status='pending',
        )
        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        assert not Kit.objects.filter(id=kit.id).exists()

    def test_usage_spans_multiple_kits(self, as_manager, member, kit_type):
        k1 = Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=20)
        k2 = Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=20)
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=30, status='pending',
        )
        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        remaining = sum(Kit.objects.filter(user=member, kit_type_fk=kit_type).values_list('quantity', flat=True))
        assert remaining == 10

    def test_explicit_kit_link_is_honoured(self, as_manager, member, kit_type):
        k1 = Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=50)
        k2 = Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=50)
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=10, status='pending', kit=k2,
        )
        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        k1.refresh_from_db()
        k2.refresh_from_db()
        assert k2.quantity == 40
        assert k1.quantity == 50


class TestRejection:
    def test_reject_keeps_stock_untouched(self, as_manager, member, kit_type, kit):
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=30, status='pending',
        )
        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'reject'})
        kit.refresh_from_db()
        usage.refresh_from_db()
        assert kit.quantity == 100
        assert usage.status == 'rejected'


class TestPermissions:
    def test_plain_member_cannot_review(self, as_member, member, kit_type):
        usage = StockUsage.objects.create(
            user=member, clock_number=member.clock_number,
            kit_type=kit_type, kit_type_name=kit_type.name,
            quantity_used=1, status='pending',
        )
        response = as_member.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        assert response.status_code == 302
        usage.refresh_from_db()
        assert usage.status == 'pending'

    def test_history_scoping(self, as_member, member, other_member, kit_type):
        StockUsage.objects.create(
            user=other_member, clock_number='1', kit_type=kit_type,
            kit_type_name=kit_type.name, quantity_used=1,
        )
        response = as_member.get('/tracking/history/')
        assert other_member.username not in response.content.decode()
