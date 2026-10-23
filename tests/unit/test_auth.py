"""Auth flows: logout (was broken), change own password, admin set password."""
import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, override_settings

from stockT.auth_backends import axes_client_ip

from tests.conftest import make_admin, make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestLoginCSRF:
    def test_login_form_token_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get('/login/')
        match = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            response.content,
        )

        assert response.status_code == 200
        assert match is not None

        response = client.post('/login/', {
            'username': 'unknown-user',
            'password': 'invalid',
            'csrfmiddlewaretoken': match.group(1).decode(),
        })

        assert response.status_code == 200
        assert b'Invalid username or password.' in response.content

    def test_login_is_locked_after_five_failed_attempts(self, client):
        for _ in range(4):
            response = client.post('/login/', {
                'username': 'guessed-account',
                'password': 'wrong-password',
            })
            assert response.status_code == 200

        response = client.post('/login/', {
            'username': 'guessed-account',
            'password': 'wrong-password',
        })
        assert response.status_code == 429
        assert b'Sign-in temporarily locked' in response.content
        assert b'15 minutes' in response.content

    def test_successful_login_clears_previous_failures(self, client):
        member = make_user('login_reset')
        for _ in range(4):
            client.post('/login/', {'username': member.username, 'password': 'incorrect'})

        response = client.post('/login/', {
            'username': member.username,
            'password': 'Pass!1234',
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_client_ip_uses_remote_addr_unless_proxy_is_trusted(self):
        request = RequestFactory().get(
            '/login/', HTTP_X_REAL_IP='198.51.100.99', REMOTE_ADDR='203.0.113.8',
        )
        with override_settings(TRUST_X_FORWARDED_FOR=False):
            assert axes_client_ip(request) == '203.0.113.8'
        with override_settings(TRUST_X_FORWARDED_FOR=True):
            assert axes_client_ip(request) == '198.51.100.99'


class TestLogout:
    def test_get_shows_confirmation(self, as_member):
        response = as_member.get('/logout/')
        assert response.status_code == 200
        assert 'log out' in response.content.decode().lower()

    def test_post_actually_logs_out(self, as_member, client):
        """Regression: the confirm page used to re-render without calling logout()."""
        response = as_member.post('/logout/')
        assert response.status_code == 302
        assert '/login' in response.url
        response = client.get('/profile/')
        assert response.status_code == 302
        assert '/login' in response.url


class TestChangePassword:
    def test_get_form(self, as_member):
        response = as_member.get('/change-password/')
        assert response.status_code == 200

    def test_requires_login(self, client):
        response = client.get('/change-password/')
        assert response.status_code == 302

    def test_change_with_wrong_old_password(self, as_member, member):
        response = as_member.post('/change-password/', {
            'old_password': 'wrong-pass', 'new_password1': 'N3w!pass99XY', 'new_password2': 'N3w!pass99XY',
        })
        assert response.status_code == 200  # form re-rendered with errors
        member.refresh_from_db()
        assert member.check_password('Pass!1234')

    def test_change_password_success(self, client, as_member, member):
        response = as_member.post('/change-password/', {
            'old_password': 'Pass!1234', 'new_password1': 'N3w!pass99XY', 'new_password2': 'N3w!pass99XY',
        })
        assert response.status_code == 302
        assert '/profile' in response.url
        assert client.login(username='member', password='N3w!pass99XY')
        assert not client.login(username='member', password='Pass!1234')


class TestAdminSetPassword:
    def test_admin_can_set_member_password(self, as_owner, owner, member):
        response = as_owner.post(f'/edit-user/{member.id}/set-password/', {
            'new_password': 'R3set!pass1XY', 'confirm_password': 'R3set!pass1XY',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.check_password('R3set!pass1XY')

    def test_manager_cannot_set_password(self, as_manager, manager, member):
        response = as_manager.post(f'/edit-user/{member.id}/set-password/', {
            'new_password': 'R3set!pass1XY', 'confirm_password': 'R3set!pass1XY',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert not member.check_password('R3set!pass1XY')

    def test_mismatched_passwords_rejected(self, as_owner, member):
        response = as_owner.post(f'/edit-user/{member.id}/set-password/', {
            'new_password': 'R3set!pass1XY', 'confirm_password': 'different',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert not member.check_password('R3set!pass1XY')

    def test_weak_password_rejected(self, as_owner, member):
        response = as_owner.post(f'/edit-user/{member.id}/set-password/', {
            'new_password': '123', 'confirm_password': '123',
        })
        member.refresh_from_db()
        assert not member.check_password('123')
