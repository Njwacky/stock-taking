"""
Shared fixtures for the stockT test suite.

Run with:  .venv/bin/pytest
"""
import itertools

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

_clock = itertools.count(10000)


def make_user(username, role='user', password='Pass!1234', **extra):
    """Create a user with a unique clock number and a known password."""
    extra.setdefault('clock_number', str(next(_clock)))
    return User.objects.create_user(
        username, f'{username}@example.com', password, role=role, **extra
    )


def make_admin(username='admin_user', **extra):
    extra.setdefault('clock_number', str(next(_clock)))
    return User.objects.create_superuser(
        username, f'{username}@example.com', 'Pass!1234', **extra
    )


@pytest.fixture
def owner(db):
    """Workspace owner (the first registrant): superuser + admin role."""
    return make_admin('owner')


@pytest.fixture
def manager(db):
    return make_user('manager', role='manager')


@pytest.fixture
def supervisor(db):
    return make_user('supervisor', role='supervisor')


@pytest.fixture
def member(db):
    return make_user('member')


@pytest.fixture
def other_member(db):
    return make_user('other_member')


@pytest.fixture
def kit_type(db):
    from stockT.models import KitType
    kt, _ = KitType.objects.get_or_create(
        code='TESTKIT', defaults={'name': 'Test Kit', 'unit_of_measure': 'pieces'}
    )
    return kt


@pytest.fixture
def kit(member, kit_type):
    from stockT.models import Kit
    return Kit.objects.create(
        user=member, kit_type_fk=kit_type, kit_type_string=kit_type.name[:20], quantity=100,
    )


@pytest.fixture
def as_owner(owner):
    from django.test import Client
    c = Client()
    c.force_login(owner)
    return c


@pytest.fixture
def as_manager(manager):
    from django.test import Client
    c = Client()
    c.force_login(manager)
    return c


@pytest.fixture
def as_member(member):
    from django.test import Client
    c = Client()
    c.force_login(member)
    return c


@pytest.fixture
def register_workspace(client):
    """POST the one-time workspace registration as the first user."""
    def _register(username='founder', clock_number='1001', password='F0under!pass'):
        response = client.post('/register/', {
            'username': username,
            'first_name': 'Work',
            'last_name': 'Space',
            'email': f'{username}@example.com',
            'clock_number': clock_number,
            'department': 'Ops',
            'phone_number': '0710000000',
            'password1': password,
            'password2': password,
        })
        return response
    return _register
