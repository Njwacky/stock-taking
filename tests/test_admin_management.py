"""Admin management: superuser-only create/promote/demote."""
import pytest
from django.contrib.auth import get_user_model

from tests.conftest import make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCreateAdmin:
    def test_superuser_creates_admin(self, as_owner):
        response = as_owner.post('/admin/create/', {
            'username': 'second_admin', 'email': 's@example.com',
            'clock_number': '55001', 'password': 'S3cond!admin',
        })
        assert response.status_code == 302
        user = User.objects.get(username='second_admin')
        assert user.role == 'admin'
        assert user.is_staff is True

    def test_manager_cannot_create_admin(self, as_manager):
        response = as_manager.post('/admin/create/', {
            'username': 'nope', 'password': 'N0pe!pass1', 'clock_number': '55002',
        })
        assert response.status_code == 302
        assert not User.objects.filter(username='nope').exists()

    def test_duplicate_username_rejected(self, as_owner, member):
        as_owner.post('/admin/create/', {
            'username': member.username, 'password': 'N0pe!pass1',
        })
        assert User.objects.filter(username=member.username).count() == 1


class TestPromoteDemote:
    def test_promote_to_admin(self, as_owner, member):
        response = as_owner.post(f'/admin/promote/{member.id}/')
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.role == 'admin'
        assert member.is_staff is True

    def test_demote_admin(self, as_owner):
        target = make_user('demote_me', role='admin', is_staff=True)
        response = as_owner.post(f'/admin/demote/{target.id}/')
        assert response.status_code == 302
        target.refresh_from_db()
        assert target.role == 'user'
        assert target.is_staff is False

    def test_cannot_demote_self(self, as_owner, owner):
        as_owner.post(f'/admin/demote/{owner.id}/')
        owner.refresh_from_db()
        assert owner.is_superuser is True

    def test_manager_cannot_promote(self, as_manager, member):
        as_manager.post(f'/admin/promote/{member.id}/')
        member.refresh_from_db()
        assert member.role == 'user'


class TestManageAdminsPage:
    def test_superuser_sees_page(self, as_owner):
        assert as_owner.get('/admin/manage/').status_code == 200

    def test_manager_blocked(self, as_manager):
        assert as_manager.get('/admin/manage/').status_code == 302
