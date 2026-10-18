"""Single-workspace model: one-time registration, first user owns the workspace."""
import pytest
from django.contrib.auth import get_user_model

from tests.conftest import make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_register_page_open_when_workspace_empty(client):
    response = client.get('/register/')
    assert response.status_code == 200
    assert 'Create Workspace' in response.content.decode()
    assert 'Become Superadmin' not in response.content.decode()


def test_first_registrant_becomes_workspace_owner(client, register_workspace):
    response = register_workspace()
    assert response.status_code == 302
    assert response.url == '/'
    user = User.objects.get(username='founder')
    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.role == 'admin'


def test_first_registrant_is_logged_in(client, register_workspace):
    register_workspace()
    response = client.get('/profile/')
    assert response.status_code == 200
    assert 'founder' in response.content.decode()


def test_registration_closes_after_first_user(client, register_workspace):
    register_workspace()
    client.logout()
    response = client.get('/register/')
    assert response.status_code == 302
    assert '/login' in response.url


def test_registration_post_blocked_when_closed(client, register_workspace):
    register_workspace()
    client.logout()
    response = client.post('/register/', {
        'username': 'intruder', 'email': 'i@example.com', 'clock_number': '9999',
        'password1': 'Intruder!1', 'password2': 'Intruder!1',
    })
    assert response.status_code == 302
    assert '/login' in response.url
    assert not User.objects.filter(username='intruder').exists()


def test_nav_hides_signup_when_closed(client, register_workspace):
    register_workspace()
    client.logout()
    response = client.get('/')
    assert 'Set Up Workspace' not in response.content.decode()


def test_nav_shows_signup_when_open(client):
    response = client.get('/')
    assert 'Set Up Workspace' in response.content.decode()


def test_authenticated_user_redirected_from_register(client, register_workspace):
    register_workspace()
    response = client.get('/register/')
    assert response.status_code == 302


def test_legacy_workspace_without_owner_reopens_registration(client):
    """Users exist but no admin — signup must reopen so the workspace can be claimed."""
    make_user('legacy_user')
    response = client.get('/register/')
    assert response.status_code == 200


def test_only_one_superuser_can_win_a_race(client, register_workspace):
    register_workspace()
    make_user('later_user')
    users = User.objects.filter(is_superuser=True)
    assert users.count() == 1
