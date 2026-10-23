"""Workspace feature: creation, switching, members and data isolation."""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from tests.conftest import make_admin, make_user

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Creation & switching
# ---------------------------------------------------------------------------

class TestWorkspaceCreate:
    def test_user_creates_second_workspace(self, as_member, member):
        response = as_member.post('/workspace/create/', {'name': 'Side Project'}, follow=True)
        assert response.status_code == 200
        assert member.workspace_memberships.count() == 2
        assert 'Side Project' in response.content.decode()

    def test_creator_is_owner_of_new_workspace(self, as_member, member):
        as_member.post('/workspace/create/', {'name': 'Side Project'})
        roles = list(
            member.workspace_memberships.values_list('workspace__name', 'role')
        )
        assert ('Side Project', 'owner') in roles

    def test_new_workspace_starts_empty_and_can_be_configured(self, as_member, member):
        as_member.post('/workspace/create/', {'name': 'Side Project'})
        from stockT.models import KitType
        workspace = member.workspace_memberships.get(workspace__name='Side Project').workspace
        assert not KitType.objects.filter(workspace=workspace).exists()

        response = as_member.post('/kit-types/', {
            'action': 'add', 'name': 'Coffee beans', 'code': 'COFFEE', 'unit_of_measure': 'bags',
        })
        assert response.status_code == 302
        assert KitType.objects.filter(workspace=workspace, name='Coffee beans').exists()

    def test_name_required(self, as_member, member):
        as_member.post('/workspace/create/', {'name': '   '})
        assert member.workspace_memberships.count() == 1  # only the personal one


class TestWorkspaceSwitch:
    def test_switch_to_own_workspace(self, as_member, member, workspace):
        as_member.post('/workspace/create/', {'name': 'Side Project'})
        side = member.workspace_memberships.get(workspace__name='Side Project').workspace
        response = as_member.post('/workspace/switch/', {'workspace_id': side.id}, follow=True)
        assert response.status_code == 200
        # session now points at the switched workspace
        assert as_member.session['workspace_id'] == side.id

    def test_cannot_switch_to_foreign_workspace(self, as_member, member):
        stranger = make_user('stranger')
        from stockT.workspace import create_workspace
        foreign = create_workspace('Stranger WS', stranger)
        response = as_member.post('/workspace/switch/', {'workspace_id': foreign.id}, follow=True)
        assert response.status_code == 200
        assert as_member.session.get('workspace_id') != foreign.id


# ---------------------------------------------------------------------------
# Data isolation ("own your own apps")
# ---------------------------------------------------------------------------

class TestDataIsolation:
    def _make_kit_type(self, workspace, code, name='Iso Kit'):
        from stockT.models import KitType
        return KitType.objects.create(workspace=workspace, code=code, name=name)

    def test_kit_types_isolated_between_workspaces(self, as_member, member, workspace):
        self._make_kit_type(workspace, 'ISOTEST', name='Workspace A Only')
        as_member.post('/workspace/create/', {'name': 'B Workspace'})
        side = member.workspace_memberships.get(workspace__name='B Workspace').workspace
        self._make_kit_type(side, 'ISOB', name='Workspace B Only')

        # in workspace A
        as_member.post('/workspace/switch/', {'workspace_id': workspace.id})
        content = as_member.get('/add-items/').content.decode()
        assert 'Workspace A Only' in content
        assert 'Workspace B Only' not in content

        # switch to B
        as_member.post('/workspace/switch/', {'workspace_id': side.id})
        content = as_member.get('/add-items/').content.decode()
        assert 'Workspace B Only' in content
        assert 'Workspace A Only' not in content

    def test_kits_isolated_between_workspaces(self, as_member, member, workspace):
        from stockT.models import Kit
        kt = self._make_kit_type(workspace, 'ISOKIT')
        Kit.objects.create(user=member, kit_type_fk=kt, kit_type_string='Iso', quantity=5,
                           workspace=workspace)

        as_member.post('/workspace/create/', {'name': 'B Workspace'})
        side = member.workspace_memberships.get(workspace__name='B Workspace').workspace

        as_member.post('/workspace/switch/', {'workspace_id': side.id})
        content = as_member.get('/').content.decode()
        assert 'Iso Kit' not in content

    def test_usage_isolated_between_workspaces(self, as_member, member, workspace):
        from stockT.models import StockUsage
        StockUsage.objects.create(
            user=member, clock_number='1', kit_type_name='Iso Usage',
            quantity_used=3, workspace=workspace,
        )
        as_member.post('/workspace/create/', {'name': 'B Workspace'})
        side = member.workspace_memberships.get(workspace__name='B Workspace').workspace
        as_member.post('/workspace/switch/', {'workspace_id': side.id})
        content = as_member.get('/tracking/history/').content.decode()
        assert 'Iso Usage' not in content

    def test_orphaned_rows_are_not_treated_as_shared_across_workspaces(
        self, as_owner, owner, workspace,
    ):
        from stockT.models import Kit, KitType, StockUsage

        orphaned_type = KitType.objects.create(
            name='Unscoped legacy type', code='UNSCOPED', workspace=None,
        )
        orphaned_kit = Kit.objects.create(
            user=owner, kit_type_fk=orphaned_type, kit_type_string='Unscoped legacy type',
            quantity=17, workspace=None,
        )
        orphaned_usage = StockUsage.objects.create(
            user=owner, clock_number=owner.clock_number,
            kit_type=orphaned_type, kit_type_name='Unscoped legacy usage',
            quantity_used=2, workspace=None,
        )

        assert 'Unscoped legacy type' not in as_owner.get('/add-items/').content.decode()
        assert 'Unscoped legacy type' not in as_owner.get('/').content.decode()
        assert 'Unscoped legacy usage' not in as_owner.get('/tracking/history/').content.decode()
        response = as_owner.get(f'/get_user_kits/{owner.id}/')
        assert all(item['id'] != orphaned_kit.id for item in response.json()['kits'])
        assert Kit.objects.filter(pk=orphaned_kit.pk).exists()
        assert StockUsage.objects.filter(pk=orphaned_usage.pk).exists()
        with pytest.raises(CommandError, match='no workspace'):
            call_command('check_workspace_orphans')

    def test_manager_cannot_read_or_modify_another_workspaces_stock(
        self, as_owner, owner, workspace,
    ):
        from stockT.models import Kit, KitType
        from stockT.workspace import create_workspace

        foreign_workspace = create_workspace('Foreign Store', owner)
        foreign_type = KitType.objects.create(
            workspace=foreign_workspace, name='Foreign-only type', code='FOREIGN',
        )
        foreign_kit = Kit.objects.create(
            user=owner, kit_type_fk=foreign_type, kit_type_string=foreign_type.name,
            quantity=23, workspace=foreign_workspace,
        )

        response = as_owner.get(f'/get_user_kits/{owner.id}/')
        assert all(item['id'] != foreign_kit.id for item in response.json()['kits'])
        assert 'Foreign-only type' not in as_owner.get('/add-items/').content.decode()
        assert as_owner.post(
            f'/update_kit/{foreign_kit.id}/', {'quantity': '1'},
        ).status_code == 404
        assert as_owner.post(f'/delete_kit/{foreign_kit.id}/').status_code == 404
        foreign_kit.refresh_from_db()
        assert foreign_kit.quantity == 23

    def test_same_name_kit_type_allowed_in_two_workspaces(self, as_member, member, workspace):
        """Per-workspace uniqueness: 'Feets' can exist in every workspace."""
        from stockT.models import KitType
        as_member.post('/workspace/create/', {'name': 'B Workspace'})
        side = member.workspace_memberships.get(workspace__name='B Workspace').workspace
        KitType.objects.create(workspace=workspace, code='DUP', name='Dup Name')
        KitType.objects.create(workspace=side, code='DUP', name='Dup Name')
        assert KitType.objects.filter(code='DUP').count() == 2


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

class TestWorkspaceMembers:
    def test_owner_adds_member(self, as_owner, owner, workspace):
        newbie = make_user('newbie')
        response = as_owner.post('/workspace/members/add/', {
            'username': 'newbie', 'role': 'member',
        }, follow=True)
        assert response.status_code == 200
        assert workspace.memberships.filter(user=newbie).exists()

    def test_added_member_sees_shared_data(self, client, as_owner, owner, workspace):
        from stockT.models import KitType
        KitType.objects.create(workspace=workspace, code='SHARED', name='Shared Type')

        make_user('newbie')
        as_owner.post('/workspace/members/add/', {'username': 'newbie', 'role': 'member'})
        newbie = User.objects.get(username='newbie')

        from django.test import Client
        c = Client()
        c.force_login(newbie)
        # the shared workspace is the member's only/current one
        content = c.get('/add-items/').content.decode()
        assert 'Shared Type' in content

    def test_plain_member_cannot_add_members(self, as_member, member, workspace):
        newbie = make_user('newbie')
        response = as_member.post('/workspace/members/add/', {
            'username': 'newbie', 'role': 'member',
        }, follow=True)
        assert response.status_code == 200
        assert not workspace.memberships.filter(user=newbie).exists()

    def test_unknown_username_rejected(self, as_owner, owner, workspace):
        as_owner.post('/workspace/members/add/', {
            'username': 'ghost', 'role': 'member',
        }, follow=True)
        assert workspace.memberships.count() == 1  # just the owner

    def test_owner_cannot_be_removed(self, as_owner, owner, workspace):
        as_owner.post('/workspace/members/remove/', {'user_id': owner.id}, follow=True)
        assert workspace.memberships.filter(user=owner, role='owner').exists()

    def test_admin_removes_member(self, as_owner, owner, workspace):
        newbie = make_user('newbie')
        as_owner.post('/workspace/members/add/', {'username': 'newbie', 'role': 'member'})
        as_owner.post('/workspace/members/remove/', {'user_id': newbie.id}, follow=True)
        assert not workspace.memberships.filter(user=newbie).exists()

    def test_member_can_leave(self, as_member, member, workspace):
        as_member.post('/workspace/members/remove/', {'user_id': member.id}, follow=True)
        assert not workspace.memberships.filter(user=member, workspace=workspace).exists()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestWorkspaceSettings:
    def test_owner_renames_workspace(self, as_owner, owner, workspace):
        response = as_owner.post('/workspace/settings/', {
            'action': 'rename', 'name': 'Renamed WS',
        }, follow=True)
        assert response.status_code == 200
        workspace.refresh_from_db()
        assert workspace.name == 'Renamed WS'

    def test_plain_member_cannot_rename(self, as_member, member, workspace):
        as_member.post('/workspace/settings/', {
            'action': 'rename', 'name': 'Hijacked',
        }, follow=True)
        workspace.refresh_from_db()
        assert workspace.name == 'Test Workspace'

    def test_settings_page_lists_members(self, as_owner, owner, workspace):
        make_user('listed')
        as_owner.post('/workspace/members/add/', {'username': 'listed', 'role': 'member'})
        content = as_owner.get('/workspace/settings/').content.decode()
        assert 'listed' in content
        assert 'Owner' in content


class TestWorkspaceOwnerControls:
    def test_workspace_owner_sees_controls_for_the_active_workspace(
        self, as_member, member, other_member,
    ):
        from stockT.models import Kit, StockUsage

        as_member.post('/workspace/create/', {'name': 'Owned Store'})
        workspace = member.workspace_memberships.get(
            workspace__name='Owned Store',
        ).workspace
        assert not member.is_manager  # owner only in this workspace

        as_member.post('/workspace/members/add/', {
            'username': other_member.username,
            'role': 'member',
        })
        as_member.post('/kit-types/', {
            'action': 'add', 'name': 'Cable ties 200mm', 'code': 'CT200',
        })
        kit_type = workspace.kit_types.filter(is_active=True).first()
        Kit.objects.create(
            user=other_member,
            kit_type_fk=kit_type,
            kit_type_string=kit_type.name[:20],
            quantity=8,
            workspace=workspace,
        )
        StockUsage.objects.create(
            user=other_member,
            clock_number=other_member.clock_number,
            kit_type=kit_type,
            kit_type_name=kit_type.name,
            quantity_used=1,
            workspace=workspace,
        )

        dashboard = as_member.get('/').content.decode()
        assert 'Kit Types' in dashboard
        assert 'Manage Users' not in dashboard
        assert 'name="user"' in dashboard
        assert 'Delete Selected' in dashboard
        assert other_member.username in dashboard

        history = as_member.get('/tracking/history/').content.decode()
        assert 'Approve' in history
        assert 'Reject' in history

        tracking = as_member.get('/tracking/').content.decode()
        assert '1 pending' in tracking

        kit_types_page = as_member.get('/kit-types/')
        assert kit_types_page.status_code == 200
