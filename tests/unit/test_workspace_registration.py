"""Multi-workspace model: registration is always open, every user gets and
owns their own workspace, and data is scoped per workspace."""
import pytest
from django.contrib.auth import get_user_model

from tests.conftest import make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


def _post_register(client, username='newbie', clock_number='77000'):
    return client.post('/register/', {
        'username': username,
        'first_name': 'New',
        'last_name': 'User',
        'email': f'{username}@example.com',
        'clock_number': clock_number,
        'department': 'Ops',
        'phone_number': '0710000000',
        'password1': 'Str0ng!pass2026',
        'password2': 'Str0ng!pass2026',
    })


def test_register_page_always_open(client):
    """Registration is open on a fresh install…"""
    response = client.get('/register/')
    assert response.status_code == 200
    assert 'Create My Workspace' in response.content.decode()


def test_register_page_stays_open_with_existing_users(client):
    """…and stays open forever, even once users (and superusers) exist."""
    make_user('existing')
    User.objects.create_superuser('boss', 'boss@example.com', 'Pass!1234', clock_number='77111')
    response = client.get('/register/')
    assert response.status_code == 200


def test_registrant_gets_own_workspace_and_is_owner(client):
    response = _post_register(client)
    assert response.status_code == 302
    assert response.url == '/'

    user = User.objects.get(username='newbie')
    from stockT.models import Workspace, WorkspaceMember

    membership = WorkspaceMember.objects.get(user=user)
    assert membership.role == WorkspaceMember.ROLE_OWNER
    workspace = Workspace.objects.get(memberships__user=user)
    assert workspace.created_by == user


def test_workspace_is_seeded_with_kit_types(client):
    """New workspaces can add stock immediately (the flush-fresh-install fix)."""
    _post_register(client)
    user = User.objects.get(username='newbie')
    from stockT.models import KitType
    codes = set(KitType.objects.filter(workspace__memberships__user=user).values_list('code', flat=True))
    assert {'FEET', 'VHB18', 'RIV8'} <= codes


def test_registration_rejects_passwords_shorter_than_twelve_characters(client):
    response = client.post('/register/', {
        'username': 'short-password-user',
        'first_name': 'Short',
        'last_name': 'Password',
        'email': 'short@example.com',
        'clock_number': '77099',
        'department': 'Ops',
        'phone_number': '0710000000',
        'password1': 'Good!pass9',
        'password2': 'Good!pass9',
    })
    assert response.status_code == 200
    assert not User.objects.filter(username='short-password-user').exists()
    assert 'at least 12 characters' in response.content.decode()


def test_first_registrant_on_empty_install_is_ordinary_user(client):
    """Public registration never grants app-level administrative privileges."""
    _post_register(client)
    user = User.objects.get(username='newbie')
    assert user.is_superuser is False
    assert user.is_staff is False
    assert user.role == 'user'


def test_later_registrants_are_ordinary_users(client):
    _post_register(client, username='first', clock_number='77001')
    client.logout()
    _post_register(client, username='second', clock_number='77002')
    user = User.objects.get(username='second')
    assert user.is_superuser is False
    assert user.role == 'user'


def test_each_registrant_gets_a_separate_workspace(client):
    _post_register(client, username='alice', clock_number='77003')
    client.logout()
    _post_register(client, username='bob', clock_number='77004')

    alice = User.objects.get(username='alice')
    bob = User.objects.get(username='bob')
    assert alice.workspace_memberships.count() == 1
    assert bob.workspace_memberships.count() == 1
    assert alice.workspace_memberships.first().workspace_id != bob.workspace_memberships.first().workspace_id


def test_registration_never_closes(client):
    _post_register(client, username='first', clock_number='77005')
    client.logout()
    response = _post_register(client, username='intruder', clock_number='77006')
    assert response.status_code == 302
    assert User.objects.filter(username='intruder').exists()


def test_new_user_is_logged_in(client):
    _post_register(client)
    response = client.get('/profile/')
    assert response.status_code == 200
    assert 'newbie' in response.content.decode()


def test_nav_shows_register_for_anonymous(client):
    response = client.get('/')
    assert 'Register' in response.content.decode()


def test_authenticated_user_redirected_from_register(client):
    _post_register(client)
    response = client.get('/register/')
    assert response.status_code == 302


def test_cli_superuser_never_hits_dead_end(client):
    """`manage.py createsuperuser` then log in: a workspace is auto-provisioned
    and the stock pages work right away (previously the app locked up)."""
    from django.test import Client
    User.objects.create_superuser('cli_boss', 'cli@example.com', 'Pass!1234', clock_number='77007')
    c = Client()
    c.force_login(User.objects.get(username='cli_boss'))

    response = c.get('/add-items/')
    assert response.status_code == 200
    # starter kit types are present in the auto-provisioned workspace
    assert 'VHB Boss Tape 18mm' in response.content.decode()
