"""Tracking workflow polish: reviewer→requester notifications, soft delete,
history filters, one-click preselect, and low-stock/expiry attention alerts.
"""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from stockT.models import KitType, NotificationLog, StockUsage

User = get_user_model()

pytestmark = pytest.mark.django_db


def submit_usage(client, kit_type, quantity, purpose='Build job'):
    return client.post('/tracking/', {
        'kit_type': kit_type.id,
        'quantity_used': str(quantity),
        'purpose': purpose,
        'feedback': 'ok',
    })


def make_usage(member, kit_type, workspace, quantity=10, status='pending'):
    return StockUsage.objects.create(
        user=member, clock_number=member.clock_number,
        kit_type=kit_type, kit_type_name=kit_type.name,
        quantity_used=quantity, status=status, workspace=workspace,
    )


# ---------------------------------------------------------------------------
# Requester notifications
# ---------------------------------------------------------------------------

class TestRequesterNotifications:
    def test_rejection_notifies_requester_with_notes(self, as_member, as_manager, member, kit_type, workspace):
        usage = make_usage(member, kit_type, workspace)
        as_manager.post(f'/tracking/review/{usage.id}/', {
            'action': 'reject', 'admin_notes': 'Use the spare roll instead.',
        })
        note = NotificationLog.objects.filter(
            notification_type='stock_usage_decision', sent_to=member,
        ).get()
        assert note.title == 'Stock usage rejected'
        assert 'Use the spare roll instead.' in note.message

    def test_approval_notifies_requester(self, as_member, as_manager, member, kit_type, kit, workspace):
        usage = make_usage(member, kit_type, workspace, quantity=10)
        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        note = NotificationLog.objects.filter(
            notification_type='stock_usage_decision', sent_to=member,
        ).get()
        assert note.title == 'Stock usage approved'
        assert 'stock has been updated' in note.message

    def test_no_decision_notification_before_review(self, as_member, member, kit_type, workspace):
        make_usage(member, kit_type, workspace)
        assert not NotificationLog.objects.filter(
            notification_type='stock_usage_decision',
        ).exists()


# ---------------------------------------------------------------------------
# Soft delete / audit trail
# ---------------------------------------------------------------------------

class TestSoftDelete:
    def test_manager_delete_is_soft_and_audited(self, as_manager, manager, member, kit_type, workspace):
        usage = make_usage(member, kit_type, workspace)
        response = as_manager.post(f'/tracking/delete/{usage.id}/')
        assert response.status_code == 302
        usage.refresh_from_db()  # row survives
        assert usage.deleted_at is not None
        assert usage.deleted_by_id == manager.id
        # Hidden from the history page…
        history = as_manager.get('/tracking/history/')
        assert not any(
            row.id == usage.id for row in history.context['usages']
        )
        # …and from the pending-review badge.
        dashboard = as_manager.get('/')
        assert dashboard.context['pending_stock_usage_count'] == 0

    def test_member_cannot_delete(self, as_member, member, kit_type, workspace):
        usage = make_usage(member, kit_type, workspace)
        as_member.post(f'/tracking/delete/{usage.id}/')
        usage.refresh_from_db()
        assert usage.deleted_at is None

    def test_deleted_usage_cannot_be_reviewed(self, as_manager, member, kit_type, workspace):
        usage = make_usage(member, kit_type, workspace)
        as_manager.post(f'/tracking/delete/{usage.id}/')
        response = as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})
        assert response.status_code == 404
        usage.refresh_from_db()
        assert usage.status == 'pending'


# ---------------------------------------------------------------------------
# History filters
# ---------------------------------------------------------------------------

class TestHistoryFilters:
    def test_invalid_status_filter_is_ignored(self, as_member, member, kit_type, workspace):
        make_usage(member, kit_type, workspace, status='pending')
        make_usage(member, kit_type, workspace, status='rejected')
        response = as_member.get('/tracking/history/', {'status': 'bogus'})
        assert response.status_code == 200
        assert len(response.context['usages']) == 2
        assert response.context['status_filter'] == ''

    def test_valid_status_filter_applies(self, as_member, member, kit_type, workspace):
        make_usage(member, kit_type, workspace, status='pending')
        make_usage(member, kit_type, workspace, status='rejected')
        response = as_member.get('/tracking/history/', {'status': 'rejected'})
        assert [row.status for row in response.context['usages']] == ['rejected']


# ---------------------------------------------------------------------------
# One-click "Track" preselect
# ---------------------------------------------------------------------------

class TestTrackPreselect:
    def test_kit_type_param_preselects_dropdown(self, as_member, kit_type):
        response = as_member.get(f'/tracking/?kit_type={kit_type.id}')
        assert response.status_code == 200
        assert response.context['form'].initial['kit_type'] == kit_type.id

    def test_legacy_kit_id_param_maps_to_type(self, as_member, kit, kit_type):
        response = as_member.get(f'/tracking/?kit_id={kit.id}')
        assert response.status_code == 200
        assert response.context['form'].initial['kit_type'] == kit_type.id

    def test_unknown_ids_are_ignored(self, as_member):
        response = as_member.get('/tracking/?kit_type=999999')
        assert response.status_code == 200
        assert 'kit_type' not in response.context['form'].initial


# ---------------------------------------------------------------------------
# Low-stock alerts
# ---------------------------------------------------------------------------

class TestLowStockAlerts:
    def test_approval_below_reorder_level_notifies_managers(
        self, as_manager, manager, owner, member, kit_type, kit, workspace,
    ):
        kit_type.reorder_level = 90  # 100 in stock, approval drops it to 80
        kit_type.save(update_fields=['reorder_level'])
        usage = make_usage(member, kit_type, workspace, quantity=20)

        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})

        alert = NotificationLog.objects.get(notification_type='low_stock')
        assert kit_type.name in alert.message
        assert alert.sent_to.filter(id=owner.id).exists()
        assert alert.sent_to.filter(id=manager.id).exists()
        assert not alert.sent_to.filter(id=member.id).exists()

    def test_approval_above_reorder_level_stays_silent(
        self, as_manager, member, kit_type, kit, workspace,
    ):
        kit_type.reorder_level = 50  # 80 left after approval — fine
        kit_type.save(update_fields=['reorder_level'])
        usage = make_usage(member, kit_type, workspace, quantity=20)

        as_manager.post(f'/tracking/review/{usage.id}/', {'action': 'approve'})

        assert not NotificationLog.objects.filter(notification_type='low_stock').exists()

    def test_submission_alone_never_alerts(self, as_member, member, kit_type, workspace):
        kit_type.reorder_level = 1
        kit_type.save(update_fields=['reorder_level'])
        submit_usage(as_member, kit_type, 5)
        assert not NotificationLog.objects.filter(notification_type='low_stock').exists()


# ---------------------------------------------------------------------------
# Dashboard "Needs attention" panel
# ---------------------------------------------------------------------------

class TestDashboardAttentionPanel:
    def test_low_stock_item_listed_for_managers(self, as_owner, kit_type, kit, workspace):
        kit_type.reorder_level = 90  # stock is 100 — not low yet
        kit_type.save(update_fields=['reorder_level'])
        response = as_owner.get('/')
        assert response.context['attention_low_stock'] == []

        kit_type.reorder_level = 150  # 100 in stock <= 150 → alert
        kit_type.save(update_fields=['reorder_level'])
        response = as_owner.get('/')
        rows = response.context['attention_low_stock']
        assert [row['name'] for row in rows] == [kit_type.name]
        assert rows[0]['total'] == 100
        assert 'Needs attention' in response.content.decode()

    def test_member_sees_no_attention_panel(self, as_member, kit_type, kit):
        kit_type.reorder_level = 1
        kit_type.save(update_fields=['reorder_level'])
        response = as_member.get('/')
        assert response.context['attention_low_stock'] == []
        assert response.context['attention_expiring'] == []
        assert 'Needs attention' not in response.content.decode()

    def test_expiring_and_expired_stock_listed(self, as_owner, kit, workspace, kit_type):
        today = timezone.localdate()
        kit.expiration_date = today + timedelta(days=10)
        kit.save(update_fields=['expiration_date'])
        response = as_owner.get('/')
        expiring = response.context['attention_expiring']
        assert [row.id for row in expiring] == [kit.id]

        kit.expiration_date = today + timedelta(days=90)  # too far out
        kit.save(update_fields=['expiration_date'])
        response = as_owner.get('/')
        assert response.context['attention_expiring'] == []

        kit.expiration_date = today - timedelta(days=3)  # already expired
        kit.save(update_fields=['expiration_date'])
        response = as_owner.get('/')
        assert [row.id for row in response.context['attention_expiring']] == [kit.id]


# ---------------------------------------------------------------------------
# Kit-type reorder management
# ---------------------------------------------------------------------------

class TestKitTypeReorderManagement:
    def test_manager_sets_reorder_level(self, as_manager, kit_type):
        response = as_manager.post('/kit-types/', {
            'action': 'set_reorder', 'kit_type_id': kit_type.id,
            'reorder_level': '25',
        })
        assert response.status_code == 302
        kit_type.refresh_from_db()
        assert kit_type.reorder_level == 25

    def test_manager_clears_reorder_level(self, as_manager, kit_type):
        kit_type.reorder_level = 10
        kit_type.save(update_fields=['reorder_level'])
        as_manager.post('/kit-types/', {
            'action': 'set_reorder', 'kit_type_id': kit_type.id,
            'reorder_level': '',
        })
        kit_type.refresh_from_db()
        assert kit_type.reorder_level is None

    def test_invalid_reorder_level_rejected(self, as_manager, kit_type):
        kit_type.reorder_level = 10
        kit_type.save(update_fields=['reorder_level'])
        response = as_manager.post('/kit-types/', {
            'action': 'set_reorder', 'kit_type_id': kit_type.id,
            'reorder_level': 'lots',
        })
        assert response.status_code == 302
        kit_type.refresh_from_db()
        assert kit_type.reorder_level == 10  # unchanged

    def test_add_form_accepts_reorder_level(self, as_manager, workspace):
        as_manager.post('/kit-types/', {
            'action': 'add', 'name': 'Clips', 'code': 'CLP1',
            'unit_of_measure': 'pieces', 'reorder_level': '40',
        })
        created = KitType.objects.get(code='CLP1')
        assert created.reorder_level == 40

    def test_member_cannot_manage_reorder_levels(self, as_member, kit_type):
        as_member.post('/kit-types/', {
            'action': 'set_reorder', 'kit_type_id': kit_type.id,
            'reorder_level': '99',
        })
        kit_type.refresh_from_db()
        assert kit_type.reorder_level is None
