"""Password reset request flow: submit -> manager approves/rejects (was a dead end)."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import PasswordResetRequest

User = get_user_model()

pytestmark = pytest.mark.django_db


def submit_request(client, user):
    return client.post('/password-reset/request/', {
        'username': user.username, 'clock_number': user.clock_number,
    })


class TestRequestSubmission:
    def test_valid_request_recorded(self, client, member):
        response = submit_request(client, member)
        assert response.status_code == 302
        assert PasswordResetRequest.objects.filter(
            username=member.username, status='pending'
        ).exists()

    def test_wrong_clock_number_rejected(self, client, member):
        response = client.post('/password-reset/request/', {
            'username': member.username, 'clock_number': '0000',
        })
        assert response.status_code == 200
        assert not PasswordResetRequest.objects.exists()


class TestManagePageAccess:
    def test_manager_sees_page(self, as_manager, member):
        submit_request(as_manager, member)
        response = as_manager.get('/password-reset/manage/')
        assert response.status_code == 200
        assert member.username in response.content.decode()

    def test_plain_member_blocked(self, as_member):
        response = as_member.get('/password-reset/manage/')
        assert response.status_code == 302


class TestProcessing:
    def _pending(self, member):
        return PasswordResetRequest.objects.create(
            username=member.username, clock_number=member.clock_number, user=member,
        )

    def test_approve_sets_new_password(self, as_manager, member):
        request = self._pending(member)
        response = as_manager.post(f'/password-reset/process/{request.id}/', {
            'action': 'approve', 'new_password': 'T3mp!pass9', 'confirm_password': 'T3mp!pass9',
        })
        assert response.status_code == 302
        request.refresh_from_db()
        member.refresh_from_db()
        assert request.status == 'approved'
        assert request.processed_by is not None
        assert member.check_password('T3mp!pass9')

    def test_reject_keeps_password(self, as_manager, member):
        request = self._pending(member)
        as_manager.post(f'/password-reset/process/{request.id}/', {'action': 'reject'})
        request.refresh_from_db()
        member.refresh_from_db()
        assert request.status == 'rejected'
        assert not member.check_password('T3mp!pass9')

    def test_mismatched_password_stays_pending(self, as_manager, member):
        request = self._pending(member)
        as_manager.post(f'/password-reset/process/{request.id}/', {
            'action': 'approve', 'new_password': 'T3mp!pass9', 'confirm_password': 'nope',
        })
        request.refresh_from_db()
        assert request.status == 'pending'

    def test_double_process_ignored(self, as_manager, member):
        request = self._pending(member)
        as_manager.post(f'/password-reset/process/{request.id}/', {
            'action': 'approve', 'new_password': 'T3mp!pass9', 'confirm_password': 'T3mp!pass9',
        })
        response = as_manager.post(f'/password-reset/process/{request.id}/', {
            'action': 'approve', 'new_password': 'Other!pass1', 'confirm_password': 'Other!pass1',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.check_password('T3mp!pass9')

    def test_plain_member_cannot_process(self, as_member, member):
        request = self._pending(member)
        response = as_member.post(f'/password-reset/process/{request.id}/', {
            'action': 'approve', 'new_password': 'T3mp!pass9', 'confirm_password': 'T3mp!pass9',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert not member.check_password('T3mp!pass9')
