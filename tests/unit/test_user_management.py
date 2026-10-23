"""User management: add people to the workspace, edit (no privilege escalation), delete."""
import pytest
from django.contrib.auth import get_user_model

from tests.conftest import make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


def add_user_payload(**overrides):
    payload = {
        'username': 'newbie',
        'first_name': 'New',
        'last_name': 'Person',
        'email': 'newbie@example.com',
        'clock_number': '77001',
        'department': 'Prod',
        'phone_number': '072',
        'role': 'user',
        'password1': 'N3wbie!pass2026',
        'password2': 'N3wbie!pass2026',
    }
    payload.update(overrides)
    return payload


class TestAddUser:
    def test_owner_adds_member_to_current_workspace(self, as_owner, workspace):
        response = as_owner.post('/manage-users/add/', add_user_payload())
        assert response.status_code == 302
        user = User.objects.get(username='newbie')
        assert user.role == 'user'
        assert user.is_superuser is False
        assert user.check_password('N3wbie!pass2026')
        membership = user.workspace_memberships.get(workspace=workspace)
        assert membership.role == 'member'
        assert user.workspace_memberships.count() == 1

    def test_member_is_added_to_the_selected_workspace(self, as_owner, owner, workspace):
        as_owner.post('/workspace/create/', {'name': 'Second Store'})
        selected = owner.workspace_memberships.get(
            workspace__name='Second Store',
        ).workspace

        response = as_owner.post('/manage-users/add/', add_user_payload())

        user = User.objects.get(username='newbie')
        assert response.status_code == 302
        assert user.workspace_memberships.filter(workspace=selected).exists()
        assert not user.workspace_memberships.filter(workspace=workspace).exists()

    def test_manager_cannot_add(self, as_manager):
        response = as_manager.post('/manage-users/add/', add_user_payload())
        assert response.status_code == 302
        assert not User.objects.filter(username='newbie').exists()

    def test_duplicate_username_rejected(self, as_owner, member):
        response = as_owner.post('/manage-users/add/', add_user_payload(username=member.username))
        assert response.status_code == 200
        assert User.objects.filter(username=member.username).count() == 1

    def test_duplicate_clock_number_rejected(self, as_owner, member):
        response = as_owner.post('/manage-users/add/', add_user_payload(clock_number=member.clock_number))
        assert not User.objects.filter(username='newbie').exists()


class TestEditUser:
    def test_manager_cannot_escalate_privileges(self, as_manager, manager, member):
        """Regression: managers used to be able to POST role=admin&is_staff=on."""
        response = as_manager.post(f'/edit-user/{member.id}/', {
            'username': member.username,
            'first_name': 'M',
            'last_name': 'E',
            'email': 'm@example.com',
            'clock_number': member.clock_number,
            'department': '',
            'phone_number': '',
            'role': 'admin',
            'is_active': 'on',
            'is_staff': 'on',
        })
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.role == 'user'
        assert member.is_staff is False

    def test_manager_can_edit_basic_fields(self, as_manager, member):
        as_manager.post(f'/edit-user/{member.id}/', {
            'username': member.username,
            'first_name': 'Renamed',
            'last_name': 'Person',
            'email': 'new@example.com',
            'clock_number': member.clock_number,
            'department': 'QA',
            'phone_number': '079',
            'role': 'user',
            'is_active': 'on',
        })
        member.refresh_from_db()
        assert member.first_name == 'Renamed'
        assert member.department == 'QA'

    def test_admin_can_change_role(self, as_owner, member):
        as_owner.post(f'/edit-user/{member.id}/', {
            'username': member.username,
            'first_name': 'M',
            'last_name': 'E',
            'email': 'm@example.com',
            'clock_number': member.clock_number,
            'department': '',
            'phone_number': '',
            'role': 'manager',
            'is_active': 'on',
        })
        member.refresh_from_db()
        assert member.role == 'manager'

    def test_self_role_change_blocked(self, as_owner, owner):
        response = as_owner.post(f'/edit-user/{owner.id}/', {
            'username': owner.username,
            'first_name': 'O',
            'last_name': 'W',
            'email': 'o@example.com',
            'clock_number': owner.clock_number,
            'department': '',
            'phone_number': '',
            'role': 'user',
            'is_active': 'on',
        })
        owner.refresh_from_db()
        assert owner.role == 'admin'


class TestActivateDeactivate:
    def test_deactivate_excludes_self(self, as_owner, owner, member):
        as_owner.post('/manage-users/', {'action': 'deactivate', 'user_ids': [owner.id, member.id]})
        owner.refresh_from_db()
        member.refresh_from_db()
        assert owner.is_active is True
        assert member.is_active is False

    def test_manager_cannot_deactivate(self, as_manager, member):
        as_manager.post('/manage-users/', {'action': 'deactivate', 'user_ids': [member.id]})
        member.refresh_from_db()
        assert member.is_active is True


class TestDeleteUser:
    def test_admin_deletes_member(self, as_owner, member):
        response = as_owner.post(f'/delete-user/{member.id}/')
        assert response.status_code == 302
        assert not User.objects.filter(id=member.id).exists()

    def test_cannot_delete_self(self, as_owner, owner):
        as_owner.post(f'/delete-user/{owner.id}/')
        assert User.objects.filter(id=owner.id).exists()

    def test_manager_cannot_delete(self, as_manager, member):
        as_manager.post(f'/delete-user/{member.id}/')
        assert User.objects.filter(id=member.id).exists()


class TestAdministratorAccountProtection:
    """Non-superusers must never be able to disable or delete a superadmin."""

    @pytest.fixture
    def role_admin(self, workspace):
        from tests.conftest import join_workspace

        user = make_user('role_admin', role='admin')
        user.is_staff = True
        user.save(update_fields=['is_staff'])
        join_workspace(workspace, user, 'admin')
        return user

    def test_manager_cannot_deactivate_superuser(self, as_manager, owner):
        as_manager.post(f'/edit-user/{owner.id}/', {
            'username': owner.username,
            'first_name': '',
            'last_name': '',
            'email': owner.email,
            'clock_number': owner.clock_number,
            'department': '',
            'phone_number': '',
        })
        owner.refresh_from_db()
        assert owner.is_active is True

    def test_role_admin_cannot_edit_superuser(self, client, role_admin, owner):
        client.force_login(role_admin)
        response = client.post(f'/edit-user/{owner.id}/', {
            'username': owner.username,
            'first_name': 'Hijacked',
            'last_name': '',
            'email': owner.email,
            'clock_number': owner.clock_number,
            'department': '',
            'phone_number': '',
            'role': 'user',
            'is_staff': 'on',
        })
        owner.refresh_from_db()
        assert response.status_code == 302
        assert owner.first_name != 'Hijacked'
        assert owner.is_active is True
        assert owner.is_superuser is True

    def test_role_admin_cannot_delete_superuser(self, client, role_admin, owner):
        client.force_login(role_admin)
        client.post(f'/delete-user/{owner.id}/')
        assert User.objects.filter(id=owner.id).exists()

    def test_bulk_deactivate_skips_superuser_for_role_admin(
        self, client, role_admin, owner, member,
    ):
        client.force_login(role_admin)
        client.post('/manage-users/', {
            'action': 'deactivate',
            'user_ids': [owner.id, member.id],
        })
        owner.refresh_from_db()
        member.refresh_from_db()
        assert owner.is_active is True
        assert member.is_active is False
