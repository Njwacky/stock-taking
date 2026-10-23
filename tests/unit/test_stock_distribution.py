"""Stock distribution portal: role access and password-confirmed assignment."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import Kit

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestAccess:
    def test_manager_allowed(self, as_manager):
        assert as_manager.get('/stock-distribution/').status_code == 200

    def test_supervisor_allowed(self, client, supervisor):
        client.force_login(supervisor)
        assert client.get('/stock-distribution/').status_code == 200

    def test_owner_allowed(self, as_owner):
        """Regression: admins used to be bounced out of the portal entirely."""
        assert as_owner.get('/stock-distribution/').status_code == 200

    def test_plain_member_redirected(self, as_member):
        response = as_member.get('/stock-distribution/')
        assert response.status_code == 302


class TestDistribution:
    def test_distribute_with_password(self, as_manager, manager, member, kit_type):
        response = as_manager.post('/stock-distribution/', {
            'recipient_user': member.id,
            'confirm_password': 'Pass!1234',
            f'kit_type_{kit_type.id}_qty': '12',
            f'kit_type_{kit_type.id}_condition': 'new',
        })
        assert response.status_code == 302
        kit = Kit.objects.get(user=member, created_by=manager)
        assert kit.quantity == 12

    def test_wrong_password_blocks(self, as_manager, manager, member, kit_type):
        response = as_manager.post('/stock-distribution/', {
            'recipient_user': member.id,
            'confirm_password': 'not-my-password',
            f'kit_type_{kit_type.id}_qty': '12',
        })
        assert response.status_code == 200
        assert not Kit.objects.filter(user=member).exists()

    def test_missing_inputs_rejected(self, as_manager, member, kit_type):
        response = as_manager.post('/stock-distribution/', {
            'recipient_user': member.id, 'confirm_password': '',
        })
        assert response.status_code == 200
        assert not Kit.objects.filter(user=member).exists()
